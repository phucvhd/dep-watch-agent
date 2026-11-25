"""Record saved local runs as Langfuse experiments without calling the model again, as
``POST /eval/runs/{dataset}/{run}/langfuse`` does. Each run is scored as a new one would be
(intervals, contamination split, gate) and keeps its judged faithfulness.

    uv run python scripts/eval/replay.py <run.json>...

Needs the Langfuse keys in ``.env`` and the dataset uploaded
(``POST /eval/datasets/{name}/upload``).
"""

import argparse
import json
import sys
from pathlib import Path

from langfuse import Langfuse

from dep_watch_agent.api.routes.eval import run_summary, save_run
from dep_watch_agent.eval.dataset import load_dataset
from dep_watch_agent.eval.metrics import CaseResult
from dep_watch_agent.eval.runner import run_langfuse

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("runs", type=Path, nargs="+", help="eval/runs/<dataset>/<run>.json")
    parser.add_argument("--datasets", type=Path, default=ROOT / "eval/datasets")
    parser.add_argument("--baselines", type=Path, default=ROOT / "eval/baselines")
    args = parser.parse_args(argv)

    client = Langfuse()
    for path in args.runs:
        run = json.loads(path.read_text())
        if run.get("provisional"):
            print(f"{path.name}: provisional, skipped (Langfuse holds labeled runs)", flush=True)
            continue
        data = load_dataset(args.datasets / run["dataset"])
        saved = {r["case_id"]: CaseResult(**r) for r in run["results"]}

        def summarize(results, run=run, data=data):
            summary = run_summary(
                data, results, run_name=run["run_name"], system=run["system"],
                model=run.get("model"), version=run.get("version"), provisional=False,
                baselines_dir=args.baselines,
            )  # fmt: skip
            if run.get("faithfulness"):  # scored on the same cases, so it still holds
                summary["faithfulness"] = run["faithfulness"]
            return summary

        _, results, summary = run_langfuse(
            client, data.name, None, system=run["system"], run_name=run["run_name"],
            metadata={"model": run.get("model"), "version": run.get("version")},
            summarize=summarize, saved=saved,
        )  # fmt: skip
        client.flush()
        save_run(path.parent.parent, {**run, **summary}, results, langfuse=True)
        m = summary["metrics"]
        print(
            f"{path.name}: macro_f1 {m['macro_f1']:.3f}, silent misses {m['silent_miss_rate']:.3f}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
