"""Decide saved runs again with the current decision rules, without calling the model, and
compare each with the run as it was (``dep_watch_agent.eval.redecide``).

    uv run python scripts/eval/redecide.py <run.json>... [--suffix S] [--no-save]

Each redecided run is saved beside its source as ``<run>-rules<N>`` (N is
``verdict.DECIDE_RULES``), so the comparison report can read it. Direct runs are skipped.
"""

import argparse
import json
import sys
from pathlib import Path

from dep_watch_agent.api.routes.eval import run_summary, save_run
from dep_watch_agent.eval.dataset import load_dataset
from dep_watch_agent.eval.metrics import CaseResult
from dep_watch_agent.eval.redecide import is_direct_run, redecide
from dep_watch_agent.eval.stats import compare
from dep_watch_agent.verdict import DECIDE_RULES

ROOT = Path(__file__).resolve().parents[2]
SHOWN = ("macro_f1", "recall", "precision", "silent_miss_rate", "false_alarm_rate")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("runs", type=Path, nargs="+", help="eval/runs/<dataset>/<run>.json")
    parser.add_argument("--datasets", type=Path, default=ROOT / "eval/datasets")
    parser.add_argument("--baselines", type=Path, default=ROOT / "eval/baselines")
    parser.add_argument("--suffix", default=f"-rules{DECIDE_RULES}", help="for the run names")
    parser.add_argument("--no-save", action="store_true", help="only print the comparison")
    args = parser.parse_args(argv)

    print(
        f"{'run':40} {'changed':>7} {'McNemar p':>9}  "
        + "  ".join(f"{m:>18}" for m in SHOWN)
        + "   (before -> after)"
    )
    for path in args.runs:
        run = json.loads(path.read_text())
        if is_direct_run(run):
            print(f"{run['run_name']:40} skipped: a direct run, answered by the model")
            continue
        data = load_dataset(args.datasets / run["dataset"])
        before = [CaseResult(**r) for r in run["results"]]
        after = redecide(before, data.issues)
        changed = sum(a.answer != b.answer for a, b in zip(after, before, strict=True))
        c = compare(after, before)
        cells = []
        for m in SHOWN:
            d = c["difference"][m]
            cells.append(
                "n/a".rjust(18) if d["delta"] is None else f"{d['b']:.3f} -> {d['a']:.3f}".rjust(18)
            )
        print(
            f"{run['run_name']:40} {changed:>7} {c['mcnemar']['p_value']:>9.3f}  "
            + "  ".join(cells),
            flush=True,
        )
        if args.no_save:
            continue
        summary = run_summary(
            data, after, run_name=run["run_name"] + args.suffix, system=run["system"],
            model=run.get("model"), version=run.get("version"), provisional=False,
            baselines_dir=args.baselines,
        )  # fmt: skip
        summary["redecided_from"] = {
            "run": run["run_name"],
            "decide_rules": run.get("decide_rules"),
        }
        save_run(path.parent.parent, summary, after, langfuse=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
