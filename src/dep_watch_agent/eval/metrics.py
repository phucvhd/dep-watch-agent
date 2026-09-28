"""Eval metrics. The positive class is "affected", i.e. an alert.

- accuracy: answer == expected, over all cases.
- precision: of the cases answered ``affected``, how many were expected ``affected``.
- recall: of the cases expected ``affected``, how many were answered ``affected``.
- false_alarm_rate: of the cases not expected ``affected`` (``not_affected`` or
  ``insufficient_information``), how many were answered ``affected``. An alert the text doesn't
  support counts as a false alarm.
- abstention_rate: share of all cases answered ``insufficient_information``.
- abstention_recall: of the cases expected ``insufficient_information``, how many were
  answered that way. None until the dataset is labeled (metadata answers never abstain).
- citation_validity: share of extracted facts whose quote exists in the issue text.

A metric whose denominator is zero is None rather than 0 or 1, so it can't be mistaken for a
result.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from dep_watch_agent.verdict import AFFECTED, ANSWERS, INSUFFICIENT_INFORMATION

RATE_METRICS = (
    "accuracy",
    "precision",
    "recall",
    "false_alarm_rate",
    "abstention_rate",
    "abstention_recall",
    "citation_validity",
)


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    issue_key: str
    basis: str
    kafka_version: str
    expected: str
    answer: str
    evidence_total: int
    citations_valid: int
    output: dict[str, Any]

    @property
    def correct(self) -> bool:
        return self.answer == self.expected


def compute_metrics(results: list[CaseResult]) -> dict[str, Any]:
    n = len(results)
    answered_affected = [r for r in results if r.answer == AFFECTED]
    expected_affected = [r for r in results if r.expected == AFFECTED]
    expected_other = [r for r in results if r.expected != AFFECTED]
    expected_insufficient = [r for r in results if r.expected == INSUFFICIENT_INFORMATION]

    confusion: dict[str, Counter] = {e: Counter() for e in ANSWERS}
    by_basis: dict[str, list[CaseResult]] = defaultdict(list)
    for r in results:
        confusion[r.expected][r.answer] += 1
        by_basis[r.basis].append(r)

    return {
        "n": n,
        "accuracy": _ratio(sum(r.correct for r in results), n),
        "precision": _ratio(
            sum(r.expected == AFFECTED for r in answered_affected), len(answered_affected)
        ),
        "recall": _ratio(
            sum(r.answer == AFFECTED for r in expected_affected), len(expected_affected)
        ),
        "false_alarm_rate": _ratio(
            sum(r.answer == AFFECTED for r in expected_other), len(expected_other)
        ),
        "abstention_rate": _ratio(sum(r.answer == INSUFFICIENT_INFORMATION for r in results), n),
        "abstention_recall": _ratio(
            sum(r.answer == INSUFFICIENT_INFORMATION for r in expected_insufficient),
            len(expected_insufficient),
        ),
        "citation_validity": _ratio(
            sum(r.citations_valid for r in results), sum(r.evidence_total for r in results)
        ),
        "confusion": {e: {a: confusion[e][a] for a in ANSWERS} for e in ANSWERS},
        "accuracy_by_basis": {
            basis: _ratio(sum(r.correct for r in rs), len(rs))
            for basis, rs in sorted(by_basis.items())
        },
    }


def format_metrics(metrics: dict[str, Any]) -> str:
    lines = [f"cases: {metrics['n']}"]
    for name in RATE_METRICS:
        value = metrics[name]
        lines.append(f"  {name:<18} {'n/a' if value is None else f'{value:.3f}'}")
    lines.append("  confusion (rows expected, columns answered):")
    lines.append(f"    {'':<26}" + "".join(f"{a:>26}" for a in ANSWERS))
    for expected, row in metrics["confusion"].items():
        lines.append(f"    {expected:<26}" + "".join(f"{row[a]:>26}" for a in ANSWERS))
    lines.append("  accuracy by case basis:")
    for basis, value in metrics["accuracy_by_basis"].items():
        lines.append(f"    {basis:<20} {'n/a' if value is None else f'{value:.3f}'}")
    return "\n".join(lines)


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None
