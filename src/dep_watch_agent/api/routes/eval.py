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
    SettingsDep,
    SystemsDep,
    pick_system,
)
from dep_watch_agent.api.schemas import (
    FILE_NAME_PATTERN,
    BaselineOut,
    DatasetStatus,
    DatasetSummary,
    EvalComparison,
    EvalRun,
    EvalRunRequest,
    EvalRunSummary,
    IssueDatesOut,
    JobOut,
    SampleRequest,
    SampleResponse,
    UploadResponse,
)
from dep_watch_agent.dependencies import DEPENDENCIES
from dep_watch_agent.eval import contamination, gate
from dep_watch_agent.eval import dataset as ds

EVAL_DEPENDENCY = next(d for d in DEPENDENCIES if d.id == "kafka")  # the ground truth is Kafka's

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
    "/runs",
    response_model=JobOut,
    status_code=status.HTTP_202_ACCEPTED,
    responses={404: {}, 422: {}},
)
def start_run(
    body: EvalRunRequest,
    jobs: JobsDep,
    settings: SettingsDep,
    langfuse: LangfuseFactoryDep,
    systems: SystemsDep,
):
    """Score a system on the dataset. Poll ``/jobs/{id}``; the result has the metrics, and local
    runs are saved under ``/eval/runs``."""
    pick_system(systems, body.system, direct_ok=True)
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
        from dep_watch_agent.eval.runner import run_langfuse, run_local

        system = systems[body.system](EVAL_DEPENDENCY)
        model = getattr(system, "model_id", None)

        if dataset is None:
            client = langfuse()
            _, metrics = run_langfuse(
                client,
                body.dataset,
                system,
                system=body.system,
                run_name=run_name,
                metadata={"model": model, "version": getattr(system, "version", None)},
            )
            client.flush()
            return {"run_name": run_name, "system": body.system, "metrics": metrics}

        results = run_local(dataset, system, provisional=body.provisional)
        payload = run_payload(
            dataset, results, run_name=run_name, system=body.system, model=model,
            version=getattr(system, "version", None), provisional=body.provisional,
        )  # fmt: skip
        if not body.provisional:
            baseline = gate.read_baseline(settings.baselines_dir, body.dataset, body.system)
            if baseline is not None:
                payload["gate"] = gate.check(payload["metrics"], baseline)
        out = settings.runs_dir / body.dataset / f"{run_name}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2) + "\n")
        return {key: payload[key] for key in ("run_name", "system", "metrics") + _OPTIONAL
                if key in payload}  # fmt: skip

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
    return _read_run(_run_path(settings.runs_dir, dataset, run_name))


_OPTIONAL = ("intervals", "contamination", "gate")


def run_payload(
    dataset: ds.Dataset,
    results: list,
    *,
    run_name: str,
    system: str,
    model: str | None,
    version: str | None,
    provisional: bool,
) -> dict:
    """A local run as saved: metrics with bootstrap intervals, the contamination split when the
    dataset has issue dates and the model's release is known, and every case's result."""
    from dep_watch_agent.eval.metrics import compute_metrics
    from dep_watch_agent.eval.stats import bootstrap_intervals

    payload = {
        "run_name": run_name,
        "system": system,
        "dataset": dataset.name,
        "model": model,
        "version": version,
        "provisional": provisional,
        "metrics": compute_metrics(results),
        "intervals": bootstrap_intervals(results),
    }
    dates = contamination.read_issue_dates(dataset.directory)
    release = contamination.model_release(model or system)
    if dates and release:
        payload["contamination"] = contamination.split(results, dates, release)
    payload["results"] = [r.__dict__ for r in results]
    return payload


@router.get("/compare", response_model=EvalComparison, responses={404: {}, 422: {}})
def compare_runs(
    settings: SettingsDep,
    dataset: Annotated[str, Query(pattern=FILE_NAME_PATTERN)],
    a: Annotated[str, Query(pattern=FILE_NAME_PATTERN, description="Run name")],
    b: Annotated[str, Query(pattern=FILE_NAME_PATTERN, description="Run name to compare with")],
) -> dict:
    """Two saved runs on the same cases: McNemar's exact test on correctness and a paired
    bootstrap interval for each metric's difference (a - b)."""
    from dep_watch_agent.eval.stats import compare

    ra, rb = (_case_results(settings.runs_dir, dataset, name) for name in (a, b))
    try:
        return {"a": a, "b": b, **compare(ra, rb)}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post(
    "/runs/{dataset}/{run_name}/baseline",
    response_model=BaselineOut,
    responses={400: {}, 404: {}},
)
def accept_baseline(
    dataset: Name,
    run_name: Name,
    settings: SettingsDep,
    tolerance: Annotated[float, Query(ge=0, le=1)] = gate.DEFAULT_TOLERANCE,
) -> dict:
    """Make a saved run the regression-gate baseline of its system on its dataset. Later runs of
    the system fail the gate when a gated metric is worse by more than ``tolerance``."""
    run = _read_run(_run_path(settings.runs_dir, dataset, run_name))
    try:
        path = gate.accept(settings.baselines_dir, run, tolerance=tolerance)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"system": run["system"], "dataset": dataset, **json.loads(path.read_text())}


@router.post(
    "/runs/{dataset}/{run_name}/faithfulness",
    response_model=JobOut,
    status_code=status.HTTP_202_ACCEPTED,
    responses={400: {}, 404: {}},
)
def start_faithfulness(dataset: Name, run_name: Name, jobs: JobsDep, settings: SettingsDep):
    """Score a saved run's facts with the judge model (``DEP_WATCH_JUDGE_MODEL``) and, for a
    retrieval run, the recall of the labeled quotes in the passages read. Saved into the run."""
    from dep_watch_agent.eval import faithfulness as fa
    from dep_watch_agent.llm.extractor import load_prompt

    path = _run_path(settings.runs_dir, dataset, run_name)
    run = _read_run(path)
    data = _load(settings.datasets_dir, dataset)
    try:
        judge, judge_model = fa.judge_from_env()
        fa.check_judge(judge_model, run.get("model") or run["system"])
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    def score(progress):
        from dep_watch_agent.eval.metrics import CaseResult

        results = [CaseResult(**r) for r in run["results"]]
        scored = fa.score(results, data.issues, judge, load_prompt("judge_faithfulness").text)
        run["faithfulness"] = {
            "judge": judge_model,
            **scored,
            "context_recall": fa.context_recall(results, fa.read_label_evidence(data.directory)),
        }
        path.write_text(json.dumps(run, indent=2) + "\n")
        return {k: v for k, v in run["faithfulness"].items() if k != "judgments"}

    return jobs.submit("eval-faithfulness", score, params={"dataset": dataset, "run": run_name})


@router.post("/datasets/{name}/dates", response_model=IssueDatesOut, responses={404: {}})
def write_dates(name: Name, session: SessionDep, settings: SettingsDep) -> dict:
    """Write the dataset's issue creation dates (``issue_dates.json``) from the synced issues,
    for the contamination split."""
    directory = _load(settings.datasets_dir, name).directory
    return {"name": name, "issues": contamination.write_issue_dates(directory, session)}


def _run_path(runs_dir: Path, dataset: str, run_name: str) -> Path:
    path = runs_dir / dataset / f"{run_name}.json"
    if not path.is_file():
        raise HTTPException(404, f"no run {run_name} on {dataset}")
    return path


def _case_results(runs_dir: Path, dataset: str, run_name: str) -> list:
    from dep_watch_agent.eval.metrics import CaseResult

    run = _read_run(_run_path(runs_dir, dataset, run_name))
    return [CaseResult(**r) for r in run["results"]]


def _load(datasets_dir: Path, name: str) -> ds.Dataset:
    directory = datasets_dir / name
    if not (directory / "manifest.json").exists():
        raise HTTPException(404, f"no dataset {name}")
    return ds.load_dataset(directory)


def _read_run(path: Path) -> dict:
    return json.loads(path.read_text())
