"""Error analysis and the comparison report over saved runs.

``error_kind`` names why a case went wrong from its saved output, so failures can be counted
by cause rather than read one by one. ``markdown_report`` puts several runs on one dataset side
by side: metrics with bootstrap intervals, paired tests against a reference run, error kinds,
the long-issue subset (where retrieval applies) and the contamination split.

    uv run python -m dep_watch_agent.eval.analysis <dataset dir> <run.json>... [--reference N]
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from dep_watch_agent.eval.contamination import model_release, read_issue_dates, split
from dep_watch_agent.eval.dataset import Dataset, load_dataset
from dep_watch_agent.eval.metrics import RATE_METRICS, CaseResult, compute_metrics
from dep_watch_agent.eval.stats import bootstrap_intervals, compare
from dep_watch_agent.retrieval import text_chars
from dep_watch_agent.verdict import AFFECTED, INSUFFICIENT_INFORMATION, NOT_AFFECTED, IssueText

START_KINDS = ("affects", "introduced")


def error_kind(r: CaseResult) -> str | None:
    """Why the case is wrong, from its output; None if it is right."""
    if r.correct:
        return None
    out = r.output
    used = out.get("evidence", [])
    dropped = out.get("dropped", [])
    reasons = sorted({d["reason"] for d in dropped})
    if r.expected == AFFECTED and r.answer == INSUFFICIENT_INFORMATION:
        if not used and not dropped:
            return "missed: no facts extracted"
        if not any(e["kind"] in START_KINDS for e in used):
            if dropped:
                return f"missed: facts dropped ({', '.join(reasons)})"
            return "missed: no affects/introduced fact"
        return "missed: bug-present fact not at or before the version"
    if r.expected == NOT_AFFECTED and r.answer == INSUFFICIENT_INFORMATION:
        if dropped:
            return f"missed all-clear: facts dropped ({', '.join(reasons)})"
        return "missed all-clear: no introduced/unaffected fact for the version"
    if r.answer == NOT_AFFECTED:
        return (
            "silent miss: wrong all-clear"
            if r.expected == AFFECTED
            else "unsupported all-clear: text has no answer"
        )
    if r.answer == AFFECTED:
        return (
            "false alarm: version is before the bug or fixed"
            if r.expected == NOT_AFFECTED
            else "unsupported alert: text has no answer"
        )
    return "other"


def error_kinds(results: list[CaseResult]) -> dict[str, int]:
    counts = Counter(k for r in results if (k := error_kind(r)))
    return dict(counts.most_common())


def load_run(path: Path) -> dict[str, Any]:
    run = json.loads(path.read_text())
    run["case_results"] = [CaseResult(**r) for r in run["results"]]
    return run


def long_issues(dataset: Dataset, chars: int) -> set[str]:
    return {
        key for key, data in dataset.issues.items() if text_chars(IssueText.from_dict(data)) > chars
    }


def _fmt(value: Any) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def _interval(ci: list[float] | None) -> str:
    return "" if ci is None else f" [{ci[0]:.2f}, {ci[1]:.2f}]"


def markdown_report(
    dataset: Dataset,
    runs: list[dict[str, Any]],
    *,
    reference: int = 0,
    long_chars: int = 6_000,
    reps: int = 1000,
) -> str:
    names = [r["run_name"] for r in runs]
    lines = [f"# Eval report: {dataset.name}", ""]
    lines += [f"Runs: {', '.join(f'`{n}`' for n in names)}. Reference: `{names[reference]}`.", ""]

    lines += ["## Metrics (95% bootstrap interval over issues)", ""]
    shown = ["macro_f1", *[m for m in RATE_METRICS if m != "macro_f1"]]
    lines += ["| metric | " + " | ".join(names) + " |", "|---|" + "---|" * len(runs)]
    intervals = [bootstrap_intervals(r["case_results"], reps=reps) for r in runs]
    for metric in shown:
        cells = [
            _fmt(r["metrics"][metric]) + _interval(ci[metric])
            for r, ci in zip(runs, intervals, strict=True)
        ]
        lines.append(f"| {metric} | " + " | ".join(cells) + " |")
    latencies = [r["metrics"].get("latency") for r in runs]
    lines.append(
        "| latency p50 / p95 per issue (s) | "
        + " | ".join(
            "n/a" if not lat else f"{lat['p50_s']:.1f} / {lat['p95_s']:.1f}" for lat in latencies
        )
        + " |"
    )
    lines.append("")

    lines += [f"## Paired comparison with `{names[reference]}`", ""]
    lines += [
        "McNemar's exact test on correctness; differences are run minus reference, with a "
        "paired bootstrap interval.",
        "",
        "| run | only run right | only reference right | McNemar p | Δ macro-F1 | "
        "Δ silent-miss rate |",
        "|---|---|---|---|---|---|",
    ]
    ref = runs[reference]["case_results"]
    for i, run in enumerate(runs):
        if i == reference:
            continue
        c = compare(run["case_results"], ref, reps=reps)
        d_f1, d_sm = c["difference"]["macro_f1"], c["difference"]["silent_miss_rate"]
        lines.append(
            f"| {run['run_name']} | {c['mcnemar']['a_only']} | {c['mcnemar']['b_only']} | "
            f"{c['mcnemar']['p_value']:.3f} | {_fmt(d_f1['delta'])}{_interval(d_f1['ci95'])} | "
            f"{_fmt(d_sm['delta'])}{_interval(d_sm['ci95'])} |"
        )
    lines.append("")

    lines += ["## Confusion (rows expected, columns answered)", ""]
    for run in runs:
        conf = run["metrics"]["confusion"]
        answers = list(conf)
        lines += [f"`{run['run_name']}`", "", "| | " + " | ".join(answers) + " |"]
        lines.append("|---|" + "---|" * len(answers))
        for expected, row in conf.items():
            lines.append(f"| {expected} | " + " | ".join(str(row[a]) for a in answers) + " |")
        lines.append("")

    lines += ["## Error kinds", ""]
    kinds = [error_kinds(r["case_results"]) for r in runs]
    every = sorted(
        {k for ks in kinds for k in ks}, key=lambda k: -sum(ks.get(k, 0) for ks in kinds)
    )
    lines += ["| error | " + " | ".join(names) + " |", "|---|" + "---|" * len(runs)]
    for kind in every:
        lines.append(f"| {kind} | " + " | ".join(str(ks.get(kind, 0)) for ks in kinds) + " |")
    lines.append("")

    long_keys = long_issues(dataset, long_chars)
    lines += [
        f"## Long issues (over {long_chars:,} characters: {len(long_keys)} issues)",
        "",
        "Where hybrid retrieval reads a selection instead of the whole thread.",
        "",
        "| metric | " + " | ".join(names) + " |",
        "|---|" + "---|" * len(runs),
    ]
    subsets = [
        compute_metrics([r for r in run["case_results"] if r.issue_key in long_keys])
        for run in runs
    ]
    for metric in ("n", "accuracy", "macro_f1", "recall", "silent_miss_rate"):
        cells = [str(m[metric]) if metric == "n" else _fmt(m[metric]) for m in subsets]
        lines.append(f"| {metric} | " + " | ".join(cells) + " |")
    lines.append("")

    dates = read_issue_dates(dataset.directory)
    lines += ["## Contamination split", ""]
    if dates is None:
        lines += ["No `issue_dates.json` for this dataset.", ""]
    else:
        lines += [
            "Issues created before vs on or after the model's release (first publication of "
            "its weights).",
            "",
            "| run | release | issues before / after | macro-F1 before | macro-F1 after | "
            "accuracy before | accuracy after |",
            "|---|---|---|---|---|---|---|",
        ]
        for run in runs:
            release = model_release(run.get("model") or run["system"])
            if release is None:
                lines.append(f"| {run['run_name']} | unknown | | | | | |")
                continue
            s = split(run["case_results"], dates, release)
            b, a = s["before"], s["after"]
            lines.append(
                f"| {run['run_name']} | {s['release']} | {b['issues']} / {a['issues']} | "
                f"{_fmt(b['macro_f1'])} | {_fmt(a['macro_f1'])} | {_fmt(b['accuracy'])} | "
                f"{_fmt(a['accuracy'])} |"
            )
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare saved eval runs as a Markdown report.")
    parser.add_argument("dataset", type=Path, help="the dataset directory")
    parser.add_argument("runs", type=Path, nargs="+", help="saved runs, eval/runs/<ds>/<run>.json")
    parser.add_argument("--reference", type=int, default=0, help="index of the reference run")
    parser.add_argument("--long-chars", type=int, default=6_000)
    parser.add_argument("--out", type=Path, help="write here instead of stdout")
    args = parser.parse_args(argv)
    report = markdown_report(
        load_dataset(args.dataset),
        [load_run(p) for p in args.runs],
        reference=args.reference,
        long_chars=args.long_chars,
    )
    if args.out:
        args.out.write_text(report + "\n")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
