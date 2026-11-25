"""Score variants of one model on a dataset and save each run locally, as ``POST /eval/runs``
does with ``"langfuse": false``. ``replay.py`` records the saved runs as Langfuse experiments.

    uv run python scripts/eval/run_variants.py <model id> <variant>[,<variant>...]
        [--dataset DIR] [--limit N] [--suffix S]

The model is the one served at ``DEP_WATCH_LLM_BASE_URL`` (LM Studio); ``run_matrix.sh`` loads
it. Runs are saved to ``DEP_WATCH_RUNS_DIR`` (default ``eval/runs``) and checked against their
system's baseline in ``eval/baselines`` when it has one.
"""

import argparse
import logging
import os
import sys
import time
from dataclasses import replace
from pathlib import Path

from dep_watch_agent.api.routes.eval import EVAL_DEPENDENCY, run_summary, save_run
from dep_watch_agent.eval.dataset import Dataset, load_dataset
from dep_watch_agent.eval.metrics import format_metrics
from dep_watch_agent.eval.runner import run_local
from dep_watch_agent.systems import VARIANTS, configured_systems

ROOT = Path(__file__).resolve().parents[2]


def first_issues(dataset: Dataset, n: int) -> Dataset:
    """The cases of the dataset's first ``n`` issues, with their labels: a smoke test."""
    keys = list(dict.fromkeys(c.issue_key for c in dataset.cases))[:n]
    cases = [c for c in dataset.cases if c.issue_key in keys]
    return replace(
        dataset, cases=cases, labels={c.case_id: dataset.labels[c.case_id] for c in cases}
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("model", help="model id as served, e.g. qwen/qwen3-4b-2507")
    parser.add_argument("variants", help="comma-separated: " + ", ".join(VARIANTS))
    parser.add_argument(
        "--dataset", type=Path, default=ROOT / "eval/datasets/kafka-ground-truth-v2"
    )
    parser.add_argument("--limit", type=int, help="only the first N issues (a smoke test)")
    parser.add_argument("--suffix", default="", help="appended to every run name")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")

    # The systems registry reads the model and its variants from the environment.
    os.environ["DEP_WATCH_LLM_MODEL"] = args.model
    os.environ["DEP_WATCH_LLM_VARIANTS"] = args.variants
    os.environ.pop("DEP_WATCH_LLM_SYSTEM", None)
    runs_dir = Path(os.environ.get("DEP_WATCH_RUNS_DIR", ROOT / "eval/runs"))
    dataset = load_dataset(args.dataset)
    if args.limit:
        dataset = first_issues(dataset, args.limit)

    for name, factory in configured_systems().items():
        system = factory(EVAL_DEPENDENCY)
        run_name = name + args.suffix
        start = time.time()
        print(f"== {run_name} started {time.strftime('%H:%M:%S')}", flush=True)
        results = run_local(dataset, system)
        summary = run_summary(
            dataset,
            results,
            run_name=run_name,
            system=name,
            model=getattr(system, "model_id", None),
            version=getattr(system, "version", None),
            provisional=False,
            baselines_dir=ROOT / "eval/baselines",
        )
        out = save_run(runs_dir, summary, results, langfuse=False)
        print(format_metrics(summary["metrics"]), flush=True)
        print(f"== {run_name} done in {time.time() - start:.0f}s -> {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
