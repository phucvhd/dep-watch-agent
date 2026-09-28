"""Turn extracted, cited facts about an issue into a decision for one Kafka version.

This is where "the LLM extracts facts, code decides" is enforced. Every system (the rule-based
baseline, the LLM pipeline) produces an ``Extraction``: version facts, each with a quote from
the issue. ``decide`` then:

1. drops facts whose quote doesn't appear in the issue text (no valid citation, no fact),
2. drops versions that aren't a specific release (``3.7`` names a release line, not a release;
   treating it as ``3.7.0`` would invent a fact),
3. decides with ``in_affected_range`` from the version module. ``unknown``, or no usable facts
   at all, becomes ``insufficient_information``.

Extractions don't depend on the config version, so one extraction serves every config.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from dep_watch_agent.versions import (
    Applicability,
    VersionParseError,
    in_affected_range,
    parse_version,
)

AFFECTED = "affected"
NOT_AFFECTED = "not_affected"
INSUFFICIENT_INFORMATION = "insufficient_information"
ANSWERS = (AFFECTED, NOT_AFFECTED, INSUFFICIENT_INFORMATION)

EvidenceKind = Literal["affects", "fix"]


@dataclass(frozen=True)
class IssueText:
    """The only issue content a system may see."""

    summary: str
    description: str
    comments: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IssueText":
        return cls(
            summary=data.get("summary") or "",
            description=data.get("description") or "",
            comments=list(data.get("comments") or []),
        )

    def fields(self) -> list[str]:
        return [self.summary, self.description, *self.comments]


@dataclass(frozen=True)
class Evidence:
    version: str
    kind: EvidenceKind
    quote: str


@dataclass(frozen=True)
class Extraction:
    evidence: list[Evidence]


@dataclass(frozen=True)
class DroppedEvidence:
    evidence: Evidence
    reason: str


@dataclass(frozen=True)
class Decision:
    answer: str
    used: list[Evidence]
    dropped: list[DroppedEvidence]

    @property
    def evidence_total(self) -> int:
        return len(self.used) + len(self.dropped)

    @property
    def citations_valid(self) -> int:
        """How many facts had a quote that exists in the issue."""
        return self.evidence_total - sum(d.reason == "citation not found" for d in self.dropped)


def quote_in_issue(quote: str, issue: IssueText) -> bool:
    """True if ``quote`` appears in one of the issue's fields, ignoring whitespace differences."""
    needle = _normalize(quote)
    return bool(needle) and any(needle in _normalize(text) for text in issue.fields())


def decide(issue: IssueText, kafka_version: str, extraction: Extraction) -> Decision:
    used: list[Evidence] = []
    dropped: list[DroppedEvidence] = []
    for ev in extraction.evidence:
        reason = _rejection(ev, issue)
        if reason:
            dropped.append(DroppedEvidence(ev, reason))
        else:
            used.append(ev)

    if not used:
        return Decision(INSUFFICIENT_INFORMATION, used, dropped)

    result = in_affected_range(
        kafka_version,
        [ev.version for ev in used if ev.kind == "affects"],
        [ev.version for ev in used if ev.kind == "fix"],
    )
    answer = {
        Applicability.AFFECTED: AFFECTED,
        Applicability.NOT_AFFECTED: NOT_AFFECTED,
        Applicability.UNKNOWN: INSUFFICIENT_INFORMATION,
    }[result]
    return Decision(answer, used, dropped)


def is_release(version: str) -> bool:
    """True for a specific release (``3.7.0``, ``0.10.2.1``), false for a line (``3.7``)."""
    try:
        parsed = parse_version(version)
    except VersionParseError:
        return False
    given = version.strip().lstrip("vV").split("-")[0].split(".")
    return len(given) == len(parsed.release)


def _rejection(ev: Evidence, issue: IssueText) -> str | None:
    if ev.kind not in ("affects", "fix"):
        return f"unknown kind {ev.kind!r}"
    if not quote_in_issue(ev.quote, issue):
        return "citation not found"
    try:
        parse_version(ev.version)
    except VersionParseError:
        return "not a version"
    if not is_release(ev.version):
        return "release line, not a release"
    return None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
