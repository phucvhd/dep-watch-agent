"""Eval metrics. The positive class is "affected", i.e. an alert.

- accuracy: answer == expected, over all cases.
- precision: of the cases answered ``affected``, how many were expected ``affected``.
- recall: of the cases expected ``affected``, how many were answered ``affected``.
- f1: harmonic mean of precision and recall for ``affected``.
- macro_f1: the mean of the per-answer F1 (``f1_by_answer``) over the three answers, so each
  answer counts equally however many cases expect it. Per answer, F1 is
  ``2TP / (2TP + FP + FN)``: 0 when the answer is never right, None when no case expects or
  gives it (left out of the mean).
- false_alarm_rate: of the cases not expected ``affected`` (``not_affected`` or
  ``insufficient_information``), how many were answered ``affected``. An alert the text doesn't
  support counts as a false alarm.
- silent_miss_rate: of the cases not expected ``not_affected`` (``affected`` or
  ``insufficient_information``), how many were answered ``not_affected``: an all-clear the text
  doesn't support, the error an operator never hears about. The mirror of the false alarm.
- abstention_rate: share of all cases answered ``insufficient_information``.
- abstention_recall: of the cases expected ``insufficient_information``, how many were
  answered that way. None until the dataset is labeled (metadata answers never abstain).
- citation_validity: share of extracted facts whose quote exists in the issue text.
- latency: seconds the system spent per issue (its calls for every config of the issue), as
  mean, p50, p95 and total. None for runs saved before it was measured.
- always_abstain_accuracy: the accuracy of a system that answers ``insufficient_information``
  to everything, i.e. the share of cases expected to abstain. Not a score of the system; the
  floor its accuracy must beat to mean anything.

A metric whose denominator is zero is None rather than 0 or 1, so it can't be mistaken for a
result.
"""

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from dep_watch_agent.verdict import AFFECTED, ANSWERS, INSUFFICIENT_INFORMATION, NOT_AFFECTED

RATE_METRICS = (
    "accuracy",
    "macro_f1",
    "f1",
    "precision",
    "recall",
    "false_alarm_rate",
    "silent_miss_rate",
    "abstention_rate",
    "abstention_recall",
    "citation_validity",
)
# Rate metrics where lower is better; for every other one higher is better.
LOWER_IS_BETTER = frozenset({"false_alarm_rate", "silent_miss_rate"})


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    issue_key: str
    basis: str
    version: str
    expected: str
    answer: str
    evidence_total: int
    citations_valid: int
    output: dict[str, Any]
    seconds: float = 0.0  # time spent answering this case; 0 when it reused its issue's reading

    @property
    def correct(self) -> bool:
        return self.answer == self.expected


def compute_metrics(results: list[CaseResult]) -> dict[str, Any]:
    n = len(results)
    answered_affected = [r for r in results if r.answer == AFFECTED]
    expected_affected = [r for r in results if r.expected == AFFECTED]
    expected_other = [r for r in results if r.expected != AFFECTED]
    expected_not_clear = [r for r in results if r.expected != NOT_AFFECTED]
    expected_insufficient = [r for r in results if r.expected == INSUFFICIENT_INFORMATION]

    confusion: dict[str, Counter] = {e: Counter() for e in ANSWERS}
    by_basis: dict[str, list[CaseResult]] = defaultdict(list)
    for r in results:
        confusion[r.expected][r.answer] += 1
        by_basis[r.basis].append(r)

    f1_by_answer = {a: _f1(confusion, a) for a in ANSWERS}
    defined_f1 = [f for f in f1_by_answer.values() if f is not None]

    return {
        "n": n,
        "accuracy": _ratio(sum(r.correct for r in results), n),
        "macro_f1": _ratio(sum(defined_f1), len(defined_f1)),
        "f1": f1_by_answer[AFFECTED],
        "precision": _ratio(
            sum(r.expected == AFFECTED for r in answered_affected), len(answered_affected)
        ),
        "recall": _ratio(
            sum(r.answer == AFFECTED for r in expected_affected), len(expected_affected)
        ),
        "false_alarm_rate": _ratio(
            sum(r.answer == AFFECTED for r in expected_other), len(expected_other)
        ),
        "silent_miss_rate": _ratio(
            sum(r.answer == NOT_AFFECTED for r in expected_not_clear), len(expected_not_clear)
        ),
        "abstention_rate": _ratio(sum(r.answer == INSUFFICIENT_INFORMATION for r in results), n),
        "abstention_recall": _ratio(
            sum(r.answer == INSUFFICIENT_INFORMATION for r in expected_insufficient),
            len(expected_insufficient),
        ),
        "citation_validity": _ratio(
            sum(r.citations_valid for r in results), sum(r.evidence_total for r in results)
        ),
        "always_abstain_accuracy": _ratio(len(expected_insufficient), n),
        "confusion": {e: {a: confusion[e][a] for a in ANSWERS} for e in ANSWERS},
        "f1_by_answer": f1_by_answer,
        "accuracy_by_basis": {
            basis: _ratio(sum(r.correct for r in rs), len(rs))
            for basis, rs in sorted(by_basis.items())
        },
        "latency": latency(results),
    }


def latency(results: list[CaseResult]) -> dict[str, float] | None:
    """Seconds per issue: mean, p50, p95 (nearest rank) and total. None if nothing was timed."""
    per_issue: dict[str, float] = defaultdict(float)
    for r in results:
        per_issue[r.issue_key] += r.seconds
    times = sorted(per_issue.values())
    if not times or not any(times):
        return None

    def rank(q: float) -> float:
        return times[min(len(times) - 1, max(0, math.ceil(q * len(times)) - 1))]

    return {
        "issues": len(times),
        "mean_s": sum(times) / len(times),
        "p50_s": rank(0.5),
        "p95_s": rank(0.95),
        "total_s": sum(times),
    }


def format_metrics(metrics: dict[str, Any]) -> str:
    lines = [f"cases: {metrics['n']}"]
    for name in RATE_METRICS:
        value = metrics[name]
        lines.append(f"  {name:<18} {'n/a' if value is None else f'{value:.3f}'}")
    floor = metrics["always_abstain_accuracy"]
    lines.append(
        f"  {'(always abstain)':<18} {'n/a' if floor is None else f'{floor:.3f}'}"
        "  <- accuracy of answering insufficient_information to everything"
    )
    lines.append("  confusion (rows expected, columns answered):")
    lines.append(f"    {'':<26}" + "".join(f"{a:>26}" for a in ANSWERS))
    for expected, row in metrics["confusion"].items():
        lines.append(f"    {expected:<26}" + "".join(f"{row[a]:>26}" for a in ANSWERS))
    lines.append("  f1 by answer:")
    for answer, value in metrics["f1_by_answer"].items():
        lines.append(f"    {answer:<26} {'n/a' if value is None else f'{value:.3f}'}")
    lines.append("  accuracy by case basis:")
    for basis, value in metrics["accuracy_by_basis"].items():
        lines.append(f"    {basis:<20} {'n/a' if value is None else f'{value:.3f}'}")
    if metrics.get("latency"):
        lat = metrics["latency"]
        lines.append(
            f"  latency per issue: mean {lat['mean_s']:.1f}s, p50 {lat['p50_s']:.1f}s, "
            f"p95 {lat['p95_s']:.1f}s, total {lat['total_s']:.0f}s"
        )
    return "\n".join(lines)


def _f1(confusion: dict[str, Counter], answer: str) -> float | None:
    tp = confusion[answer][answer]
    fp = sum(confusion[e][answer] for e in ANSWERS if e != answer)
    fn = sum(confusion[answer][a] for a in ANSWERS if a != answer)
    return _ratio(2 * tp, 2 * tp + fp + fn)


def _ratio(numerator: float, denominator: int) -> float | None:
    return numerator / denominator if denominator else None
