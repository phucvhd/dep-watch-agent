"""Ground-truth datasets and eval runs.

Datasets are directories committed to git (see ``eval.dataset``); labeling is still done by
editing ``labels.csv``. These endpoints sample, check, upload and score them.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from fastapi import Path as PathParam

from dep_watch_agent.api.deps import (
    JobsDep,
    LangfuseFactoryDep,
    SessionDep,
    SessionsDep,
    SettingsDep,
)
from dep_watch_agent.api.schemas import (
    FILE_NAME_PATTERN,
    DatasetStatus,
    DatasetSummary,
    EvalRun,
    EvalRunRequest,
    EvalRunSummary,
    JobOut,
    SampleRequest,
    SampleResponse,
    UploadResponse,
)
from dep_watch_agent.eval import dataset as ds

router = APIRouter(prefix="/eval", tags=["eval"])

Name = Annotated[str, PathParam(pattern=FILE_NAME_PATTERN)]


@router.get("/datasets", response_model=list[DatasetSummary])
def list_datasets(settings: SettingsDep) -> list[DatasetSummary]:
    summaries = []
    for manifest in sorted(settings.datasets_dir.glob("*/manifest.json")):
        dataset = ds.load_dataset(manifest.parent)
        labeled, total = ds.label_progress(dataset)
        design = dataset.manifest.get("design", {}).get("version", "v1")
        summaries.append(
            DatasetSummary(name=dataset.name, design=design, labeled=labeled, total=total)
        )
    return summaries


@router.post(
    "/datasets",
    response_model=SampleResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "The dataset exists and force is false"}},
)
def sample_dataset(body: SampleRequest, session: SessionDep, settings: SettingsDep):
    """Sample issues and write a new dataset with an empty ``labels.csv``."""
    directory = settings.datasets_dir / body.name
    if directory.exists() and not body.force:
        raise HTTPException(409, f"dataset {body.name} exists; its labels would be lost")
    manifest, sample, cases = ds.sample_dataset(
        session, body.name, size=body.size, seed=body.seed, design=body.design
    )
    ds.write_dataset(directory, manifest, sample, cases, force=body.force)
    return SampleResponse(
        name=body.name,
        issues=len(sample),
        cases=len(cases),
        strata_counts=manifest["strata_counts"],
        case_basis_counts=manifest["case_basis_counts"],
    )


@router.get("/datasets/{name}/status", response_model=DatasetStatus, responses={404: {}})
def dataset_status(name: Name, settings: SettingsDep) -> DatasetStatus:
    """Labeling progress and problems."""
    dataset = _load(settings.datasets_dir, name)
    labeled, total = ds.label_progress(dataset)
    problems = ds.label_problems(dataset)
    return DatasetStatus(
        name=dataset.name,
        labeled=labeled,
        total=total,
        problems=[p for p in problems if not p.endswith("not labeled")],
        ready=not problems,
    )


@router.post("/datasets/{name}/upload", response_model=UploadResponse, responses={404: {}})
def upload_dataset(name: Name, settings: SettingsDep, langfuse: LangfuseFactoryDep):
    """Upload a fully labeled dataset to Langfuse."""
    dataset = _load(settings.datasets_dir, name)
    client = langfuse()
    count = ds.upload(dataset, client)
    client.flush()
    return UploadResponse(name=dataset.name, uploaded=count)


@router.post(
    "/runs", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED, responses={404: {}}
)
def start_run(
    body: EvalRunRequest,
    jobs: JobsDep,
    sessions: SessionsDep,
    settings: SettingsDep,
    langfuse: LangfuseFactoryDep,
):
    """Score a system on the dataset. Poll ``/jobs/{id}``; the result has the metrics, and local
    runs are saved under ``/eval/runs``."""
    if body.langfuse and body.provisional:
        raise HTTPException(400, "provisional runs are local only; Langfuse holds labeled data")
    dataset = None if body.langfuse else _load(settings.datasets_dir, body.dataset)
    if dataset is not None and not body.provisional:
        problems = ds.label_problems(dataset)
        if problems:
            raise HTTPException(
                400,
                f"{len(problems)} labeling problem(s), first: {problems[0]}. "
                "Finish labeling or set provisional.",
            )
    run_name = body.run_name or f"{body.system}-{datetime.now(UTC):%Y%m%dT%H%M%SZ}"

    def run(progress):
        from dep_watch_agent.baseline import RuleBasedExtractor
        from dep_watch_agent.eval.metrics import compute_metrics
        from dep_watch_agent.eval.runner import run_langfuse, run_local
        from dep_watch_agent.eval.sampling import known_versions

        with sessions() as session:
            extractor = RuleBasedExtractor(known_versions(session, "KAFKA"))

        if dataset is None:
            client = langfuse()
            _, metrics = run_langfuse(client, body.dataset, extractor, run_name=run_name)
            client.flush()
            return {"run_name": run_name, "system": extractor.name, "metrics": metrics}

        results = run_local(dataset, extractor, provisional=body.provisional)
        payload = {
            "run_name": run_name,
            "system": extractor.name,
            "dataset": body.dataset,
            "provisional": body.provisional,
            "metrics": compute_metrics(results),
            "results": [r.__dict__ for r in results],
        }
        out = settings.runs_dir / body.dataset / f"{run_name}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2) + "\n")
        return {key: payload[key] for key in ("run_name", "system", "metrics")}

    params = {**body.model_dump(), "run_name": run_name}
    return jobs.submit("eval-run", run, params=params)


@router.get("/runs", response_model=list[EvalRunSummary])
def list_runs(
    settings: SettingsDep,
    dataset: Annotated[str | None, Query(pattern=FILE_NAME_PATTERN)] = None,
) -> list[dict]:
    """Saved local runs, newest first."""
    paths = settings.runs_dir.glob(f"{dataset}/*.json" if dataset else "*/*.json")
    runs = sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)
    return [_read_run(p) for p in runs]


@router.get("/runs/{dataset}/{run_name}", response_model=EvalRun, responses={404: {}})
def get_run(dataset: Name, run_name: Name, settings: SettingsDep) -> dict:
    path = settings.runs_dir / dataset / f"{run_name}.json"
    if not path.is_file():
        raise HTTPException(404, f"no run {run_name} on {dataset}")
    return _read_run(path)


def _load(datasets_dir: Path, name: str) -> ds.Dataset:
    directory = datasets_dir / name
    if not (directory / "manifest.json").exists():
        raise HTTPException(404, f"no dataset {name}")
    return ds.load_dataset(directory)


def _read_run(path: Path) -> dict:
    return json.loads(path.read_text())
