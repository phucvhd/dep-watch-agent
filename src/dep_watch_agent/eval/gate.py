"""Regression gate: a run fails when a metric moves the wrong way past a tolerance, compared with
the accepted baseline of the same system on the same dataset.

Baselines are committed under ``eval/baselines/<dataset>/<system>.json`` (``accept``): the
metrics of the run that was accepted, its name and the tolerance. Every saved run is checked
against its system's baseline if there is one; there is no CI, so the gate runs where the eval
runs, and from the command line for a saved run:

    uv run python -m dep_watch_agent.eval.gate eval/runs/<dataset>/<run>.json [--accept]

which exits 1 when the gate fails.
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dep_watch_agent.eval.metrics import LOWER_IS_BETTER

GATED_METRICS = (
    "macro_f1",
    "recall",
    "abstention_recall",
    "citation_validity",
    "false_alarm_rate",
    "silent_miss_rate",
)
DEFAULT_TOLERANCE = 0.02
DEFAULT_BASELINES_DIR = Path("eval/baselines")


def baseline_path(baselines_dir: Path, dataset: str, system: str) -> Path:
    return baselines_dir / dataset / f"{system}.json"


def read_baseline(baselines_dir: Path, dataset: str, system: str) -> dict[str, Any] | None:
    path = baseline_path(baselines_dir, dataset, system)
    return json.loads(path.read_text()) if path.is_file() else None


def accept(
    baselines_dir: Path, run: dict[str, Any], *, tolerance: float = DEFAULT_TOLERANCE
) -> Path:
    """Make ``run`` (a saved run's payload) the baseline of its system on its dataset."""
    if run.get("provisional"):
        raise ValueError("a provisional run can't be a baseline")
    path = baseline_path(baselines_dir, run["dataset"], run["system"])
    path.parent.mkdir(parents=True, exist_ok=True)
    baseline = {
        "run_name": run["run_name"],
        "accepted_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "tolerance": tolerance,
        "metrics": {name: run["metrics"].get(name) for name in GATED_METRICS},
    }
    path.write_text(json.dumps(baseline, indent=2) + "\n")
    return path


def check(metrics: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    """Compare a run's metrics with a baseline. A metric fails when it is worse by more than the
    tolerance (lower for most, higher for the error rates in ``LOWER_IS_BETTER``), or when it
    had a value in the baseline and has none now."""
    tolerance = baseline.get("tolerance", DEFAULT_TOLERANCE)
    failures = []
    for name in GATED_METRICS:
        before, now = baseline["metrics"].get(name), metrics.get(name)
        if before is None:
            continue
        if now is None:
            failures.append({"metric": name, "baseline": before, "current": None, "change": None})
            continue
        worse = (now - before) if name in LOWER_IS_BETTER else (before - now)
        if worse > tolerance + 1e-12:
            failures.append(
                {"metric": name, "baseline": before, "current": now, "change": now - before}
            )
    return {
        "baseline_run": baseline["run_name"],
        "tolerance": tolerance,
        "passed": not failures,
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("run", type=Path, help="a saved run, eval/runs/<dataset>/<run>.json")
    parser.add_argument("--baselines", type=Path, default=DEFAULT_BASELINES_DIR)
    parser.add_argument("--accept", action="store_true", help="make this run the baseline")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    args = parser.parse_args(argv)

    run = json.loads(args.run.read_text())
    if args.accept:
        print(f"baseline written: {accept(args.baselines, run, tolerance=args.tolerance)}")
        return 0
    baseline = read_baseline(args.baselines, run["dataset"], run["system"])
    if baseline is None:
        print(f"no baseline for {run['system']} on {run['dataset']}; nothing to gate")
        return 0
    result = check(run["metrics"], baseline)
    for f in result["failures"]:
        print(f"FAIL {f['metric']}: {f['baseline']} -> {f['current']}")
    print(f"gate {'passed' if result['passed'] else 'failed'} against {result['baseline_run']}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
