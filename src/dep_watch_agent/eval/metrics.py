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
- abstention_rate: share of all cases answered ``insufficient_information``.
- abstention_recall: of the cases expected ``insufficient_information``, how many were
  answered that way. None until the dataset is labeled (metadata answers never abstain).
- citation_validity: share of extracted facts whose quote exists in the issue text.
- always_abstain_accuracy: the accuracy of a system that answers ``insufficient_information``
  to everything, i.e. the share of cases expected to abstain. Not a score of the system; the
  floor its accuracy must beat to mean anything.

A metric whose denominator is zero is None rather than 0 or 1, so it can't be mistaken for a
result.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from dep_watch_agent.verdict import AFFECTED, ANSWERS, INSUFFICIENT_INFORMATION

RATE_METRICS = (
    "accuracy",
    "macro_f1",
    "f1",
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
    return "\n".join(lines)


def _f1(confusion: dict[str, Counter], answer: str) -> float | None:
    tp = confusion[answer][answer]
    fp = sum(confusion[e][answer] for e in ANSWERS if e != answer)
    fn = sum(confusion[answer][a] for a in ANSWERS if a != answer)
    return _ratio(2 * tp, 2 * tp + fp + fn)


def _ratio(numerator: float, denominator: int) -> float | None:
    return numerator / denominator if denominator else None
