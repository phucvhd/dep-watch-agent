"""Turn extracted, cited facts about an issue into a decision for one pinned version.

This is where "the LLM extracts facts, code decides" is enforced. Every system (see
``systems``) produces an ``Extraction``: version facts, each with a quote from the issue
text. Fix versions also arrive as structured input (``IssueText.fix_versions``, from
JIRA or git), as they do in production.

Evidence kinds, from strongest start-of-bug signal to fix:

- ``introduced``: the bug starts at this version ("regression in 3.6.0", "broken since 3.6.0")
- ``affects``: the bug was observed at this version ("reproduced on 3.6.0", a stack trace)
- ``unaffected``: the bug was absent at this version ("works on 3.5.2")
- ``fix``: the fix is in this release (text-stated; the given fix versions are added to these)

``decide``:

1. drops facts whose quote isn't in the issue text (no valid citation, no fact), whose quote
   doesn't contain the fact's version (the model inferred the version rather than read it),
   and versions that name a release line (``3.7``) rather than a release, in the dependency's
   version scheme;
2. **not affected** if the version contains a fix, by the version module's backport rules, or
   the text says this exact version is unaffected;
3. **affected** if the version is at or after a version where the bug exists (``affects`` or
   ``introduced``) and before a fix;
4. **not affected** if the version is below an ``introduced`` version: before the bug starts;
5. otherwise **insufficient_information**. In particular "seen on 3.6.0" says nothing about
   3.5.2: the reporter's version is not where the bug starts. Nor does "absent on 4.2.0" say
   anything about 3.9.1: an ``unaffected`` fact covers only its own version (rule 2), since
   "not a problem in 4.2.0" is as often said of a version past the bug as before it.

Extractions don't depend on the config version, so one extraction serves every config.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from dep_watch_agent.versions import (
    Applicability,
    Version,
    VersionParseError,
    VersionScheme,
    in_affected_range,
)

AFFECTED = "affected"
NOT_AFFECTED = "not_affected"
INSUFFICIENT_INFORMATION = "insufficient_information"
ANSWERS = (AFFECTED, NOT_AFFECTED, INSUFFICIENT_INFORMATION)

EvidenceKind = Literal["introduced", "affects", "unaffected", "fix"]
EVIDENCE_KINDS: tuple[str, ...] = ("introduced", "affects", "unaffected", "fix")


@dataclass(frozen=True)
class IssueText:
    """The only issue content a system may see: free text plus the given fix versions."""

    summary: str
    description: str
    comments: list[str] = field(default_factory=list)
    fix_versions: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IssueText":
        return cls(
            summary=data.get("summary") or "",
            description=data.get("description") or "",
            comments=list(data.get("comments") or []),
            fix_versions=list(data.get("fix_versions") or []),
        )

    def fields(self) -> list[str]:
        """The free-text fields quotes must come from."""
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


def decide(
    issue: IssueText, version: str, extraction: Extraction, scheme: VersionScheme
) -> Decision:
    """The answer for ``version``, a release in ``scheme``, the issue's dependency's scheme."""
    used: list[Evidence] = []
    dropped: list[DroppedEvidence] = []
    for ev in extraction.evidence:
        reason = _rejection(ev, issue, scheme)
        if reason:
            dropped.append(DroppedEvidence(ev, reason))
        else:
            used.append(ev)

    def versions(*kinds: str) -> list[Version]:
        return [scheme.parse(ev.version) for ev in used if ev.kind in kinds]

    target = scheme.parse(version)
    fixes = versions("fix") + [scheme.parse(v) for v in issue.fix_versions if scheme.is_release(v)]
    present = versions("affects", "introduced")
    introduced = versions("introduced")
    unaffected = versions("unaffected")

    if fixes and in_affected_range(target, [], fixes) is Applicability.NOT_AFFECTED:
        answer = NOT_AFFECTED
    elif target in unaffected and target not in present:
        answer = NOT_AFFECTED  # a statement about this exact version beats range inference
    elif present and in_affected_range(target, present, fixes) is Applicability.AFFECTED:
        answer = AFFECTED
    elif introduced and target < min(introduced):
        answer = NOT_AFFECTED
    else:
        answer = INSUFFICIENT_INFORMATION
    return Decision(answer, used, dropped)


def _rejection(ev: Evidence, issue: IssueText, scheme: VersionScheme) -> str | None:
    if ev.kind not in EVIDENCE_KINDS:
        return f"unknown kind {ev.kind!r}"
    if not quote_in_issue(ev.quote, issue):
        return "citation not found"
    try:
        scheme.parse(ev.version)
    except VersionParseError:
        return "not a version"
    if not scheme.is_release(ev.version):
        return "release line, not a release"
    if not version_in_quote(ev.version, ev.quote):
        return "version not in quote"
    return None


def version_in_quote(version: str, quote: str) -> bool:
    """True if ``quote`` names ``version`` itself: ``3.6.0`` in "kafka-raft-3.6.0.jar" or
    "{{3.6.0}}", but not in "13.6.0" or "3.6.01". A fact the quote doesn't name was inferred."""
    plain = version.strip().lstrip("vV")
    pattern = rf"(?<![\d.])[vV]?{re.escape(plain)}(?!\d|\.\d)"
    return re.search(pattern, quote) is not None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
