"""Decide saved runs again with the current rules, without calling the model.

A run's file keeps every fact the model extracted for a case, kept (``evidence``) or dropped
with the reason (``dropped``). That is the extraction, so ``decide`` can be applied to it again:
a change to the decision rules (``verdict.DECIDE_RULES``) is measured on every saved run in
seconds, and compared case by case with the run as it was. Direct runs are left out: their
answer is the model's, and code only checks its citation.
"""

from dataclasses import replace
from typing import Any

from dep_watch_agent.eval.metrics import CaseResult
from dep_watch_agent.eval.runner import decision_output
from dep_watch_agent.verdict import Evidence, Extraction, IssueText, decide
from dep_watch_agent.versions import KAFKA

_DECISION_KEYS = (
    "answer", "evidence", "dropped", "evidence_total", "citations_valid", "context",
    "invalid_outputs",
)  # fmt: skip


def is_direct_run(run: dict[str, Any]) -> bool:
    return "parser=direct" in (run.get("version") or "")


def extraction_of(output: dict[str, Any]) -> Extraction:
    """The extraction a case was decided from: its kept and dropped facts, and the passages read."""
    facts = [*output.get("evidence", []), *output.get("dropped", [])]
    return Extraction(
        [Evidence(f["version"], f["kind"], f["quote"]) for f in facts],
        context=output.get("context"),
        invalid_outputs=output.get("invalid_outputs", 0),
    )


def redecide(results: list[CaseResult], issues: dict[str, dict[str, Any]]) -> list[CaseResult]:
    """Every case decided again from its saved extraction. The time spent reading and the
    invalid model output count are kept, and anything else the output recorded is carried over."""
    out = []
    for r in results:
        extraction = extraction_of(r.output)
        decision = decide(IssueText.from_dict(issues[r.issue_key]), r.version, extraction, KAFKA)
        output = {k: v for k, v in r.output.items() if k not in _DECISION_KEYS}
        output.update(decision_output(decision, extraction.context))
        out.append(
            replace(
                r,
                answer=decision.answer,
                evidence_total=decision.evidence_total,
                citations_valid=decision.citations_valid,
                output=output,
            )
        )
    return out
