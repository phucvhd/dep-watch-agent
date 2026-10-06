"""Upgrade (or downgrade) diagnosis: what changes for a dependency between two versions.

Each candidate issue (the scan's Tier 1: bugs that aren't "not a bug") is answered for both
versions by ``verdict.decide``, from the same facts, and code compares the two answers:

- ``fixed``: affected now, not affected at the target: a bug you have that the move fixes.
- ``fix_included``: not affected at the target, not known either way now. Usually the fix
  versions settle the target with no model call, while the text doesn't say where the bug
  starts.
- ``new_risk``: not affected now, affected at the target.
- ``exposed``: not affected now, but the target can't be ruled out. On a downgrade these are
  mostly the fixes you would give up: the fix versions settle the current version, while the
  text rarely says where the bug starts.
- ``remains``: affected at the target, and affected (or not known otherwise) now.
- ``inconclusive``: the target's answer is ``insufficient_information``, and so was or is
  the current one.
- ``unchanged``: not affected at either version; counted, not listed.

Nothing new decides anything: the per-version answers are what the eval measures, and the
comparison is deterministic. Facts come from stored extractions; an issue without them is
answered by its fix versions alone and counted as not checked, unless ``read`` lets the system
read it. ``read_order`` decides which issues those are: first those the target's fix versions
don't settle (they may affect the target), then the rest; within each, issues that aren't
about tests, build or docs, those JIRA reports between the two versions or that were reported
recently enough to be new, then by priority. These are Tier 1 hints for what to read first,
never evidence for an answer, and nothing is left out: unread issues are counted.
"""

import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from dep_watch_agent import extractions
from dep_watch_agent.check import issue_text, issue_url
from dep_watch_agent.dependencies import Dependency
from dep_watch_agent.eval.runner import Extractor
from dep_watch_agent.extractions import ExtractionFailed
from dep_watch_agent.orm import JiraIssueRow, JiraVersionRow
from dep_watch_agent.scan import candidates_query
from dep_watch_agent.verdict import (
    AFFECTED,
    INSUFFICIENT_INFORMATION,
    NOT_AFFECTED,
    DroppedEvidence,
    Evidence,
    Extraction,
    IssueText,
    decide,
)
from dep_watch_agent.versions import Version, VersionParseError, VersionScheme

FIXED = "fixed"
FIX_INCLUDED = "fix_included"
NEW_RISK = "new_risk"
EXPOSED = "exposed"
REMAINS = "remains"
INCONCLUSIVE = "inconclusive"
UNCHANGED = "unchanged"
CHANGES = (NEW_RISK, REMAINS, EXPOSED, FIXED, INCONCLUSIVE, FIX_INCLUDED, UNCHANGED)
# Listed in this order: the bugs at the target, then the bugs you have now that it fixes.
REPORT_ORDER = {c: i for i, c in enumerate(CHANGES[:-1])}

# Read-order hints. A bug that starts after the current version can't have been reported long
# before it: trunk runs about one release cycle ahead of a release.
TRUNK_LEAD = timedelta(days=183)
PRIORITY_RANK = {"Blocker": 0, "Critical": 1, "Major": 2, "Minor": 3, "Trivial": 4}
NOT_PRODUCT = {"unit tests", "system tests", "build", "docs", "documentation", "website"}
FLAKY = re.compile(r"^\s*flaky\b", re.IGNORECASE)


def change(current: str, target: str) -> str:
    """How an issue's answer changes from the current version to the target."""
    if target == NOT_AFFECTED:
        if current == NOT_AFFECTED:
            return UNCHANGED
        return FIXED if current == AFFECTED else FIX_INCLUDED
    if target == AFFECTED:
        return NEW_RISK if current == NOT_AFFECTED else REMAINS
    return EXPOSED if current == NOT_AFFECTED else INCONCLUSIVE


@dataclass(frozen=True)
class UpgradeItem:
    issue_key: str
    url: str
    summary: str
    status: str | None
    resolution: str | None
    updated_at: datetime
    fix_versions: list[str]
    current: str  # the answer at the current version
    target: str  # the answer at the target version
    change: str
    decided_by: str  # the system's name when its facts were used, else "fix_versions"
    cached: bool = False
    evidence: list[Evidence] = field(default_factory=list)
    dropped: list[DroppedEvidence] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class UpgradeResult:
    from_version: str
    to_version: str
    direction: str  # "upgrade" or "downgrade"
    system: str | None
    candidates: int
    releases_between: int  # released versions after the lower one, up to the higher one
    unchecked: int  # inconclusive at the target and never read: a model call would answer it
    read: int  # issues the system read in this run
    items: list[UpgradeItem]  # every change but unchanged, in report order
    unchanged: int

    @property
    def counts(self) -> dict[str, int]:
        counter = Counter(item.change for item in self.items)
        return {c: counter[c] for c in CHANGES if c != UNCHANGED} | {UNCHANGED: self.unchanged}

    @property
    def errors(self) -> int:
        return sum(item.error is not None for item in self.items)


def diagnose(
    session: Session,
    dependency: Dependency,
    from_version: str,
    to_version: str,
    system: str | None,
    extractor: Extractor | None,
    *,
    read: int = 0,
    on_issue: Callable[[int], None] | None = None,
) -> UpgradeResult:
    """Compare every candidate's answer at ``from_version`` and ``to_version`` (both validated
    with ``check.answerable``). Reads at most ``read`` issues without stored facts, first those
    the JIRA affects versions place between the two versions."""
    scheme = dependency.scheme
    current, target = scheme.parse(from_version), scheme.parse(to_version)
    low, high = sorted((current, target))
    issues = session.scalars(
        candidates_query(dependency.project, None)
        .order_by(JiraIssueRow.updated_at.desc(), JiraIssueRow.id.desc())
        .options(
            selectinload(JiraIssueRow.versions),
            selectinload(JiraIssueRow.comments),
            selectinload(JiraIssueRow.components),
        )
    ).all()
    texts = {issue.id: issue_text(issue) for issue in issues}
    stored = (
        extractions.stored_texts(session, [i.id for i in issues], system, extractor)
        if system and extractor
        else set()
    )

    def by_fixes(issue: JiraIssueRow, version: str) -> bool:
        return decide(texts[issue.id], version, Extraction([]), scheme).answer == NOT_AFFECTED

    to_read: set[int] = set()
    if read and system and extractor:
        # Reading can't change an answer both versions' fix versions settle.
        unread = [
            i
            for i in issues
            if (i.id, extractions.text_hash(texts[i.id])) not in stored
            and not (by_fixes(i, from_version) and by_fixes(i, to_version))
        ]
        since = _release_date(session, dependency, low)
        unread.sort(
            key=lambda i: read_order(
                i,
                target_settled=by_fixes(i, to_version),
                low=low,
                high=high,
                scheme=scheme,
                recent_since=since - TRUNK_LEAD if since else None,
            )
        )  # stable: newest first within a tie
        to_read = {i.id for i in unread[:read]}

    items, unchanged, unchecked, done = [], 0, 0, 0
    for issue in issues:
        text = texts[issue.id]
        fields = _fields(issue, text)  # read first: storing an extraction expires the rows
        facts, cached, error = None, False, None
        if (issue.id, extractions.text_hash(text)) in stored:
            facts = extractions.stored(session, issue.id, text, system, extractor)
            cached = True
        elif issue.id in to_read:
            try:
                facts = extractions.extract(session, issue.id, text, system, extractor).extraction
            except ExtractionFailed as exc:
                session.rollback()
                error = str(exc)
            done += 1
            if on_issue:
                on_issue(done)
        item = _item(fields, text, from_version, to_version, scheme, facts, system, cached, error)
        if item.change == UNCHANGED:
            unchanged += 1
            continue
        if facts is None and error is None and item.change == INCONCLUSIVE:
            unchecked += 1  # never read: only counted, every one would say the same
            continue
        items.append(item)

    items.sort(key=lambda i: REPORT_ORDER[i.change])  # stable: newest first within
    releases = _releases_between(session, dependency, low, high)
    return UpgradeResult(
        from_version=from_version,
        to_version=to_version,
        direction="upgrade" if current < target else "downgrade",
        system=system,
        candidates=len(issues),
        releases_between=releases,
        unchecked=unchecked,
        read=done,
        items=items,
        unchanged=unchanged,
    )


def _fields(issue: JiraIssueRow, text: IssueText) -> dict:
    return {
        "issue_key": issue.key,
        "url": issue_url(issue.key),
        "summary": issue.summary,
        "status": issue.status,
        "resolution": issue.resolution,
        "updated_at": issue.updated_at,
        "fix_versions": text.fix_versions,
    }


def _item(
    fields: dict,
    text: IssueText,
    from_version: str,
    to_version: str,
    scheme: VersionScheme,
    facts: Extraction | None,
    system: str | None,
    cached: bool,
    error: str | None,
) -> UpgradeItem:
    """Both answers from the same facts; with a failed read, the target can't be told."""
    extraction = facts or Extraction([])
    at_current = decide(text, from_version, extraction, scheme)
    at_target = decide(text, to_version, extraction, scheme)
    target = INSUFFICIENT_INFORMATION if error else at_target.answer
    return UpgradeItem(
        **fields,
        current=at_current.answer,
        target=target,
        change=change(at_current.answer, target),
        decided_by=system if facts is not None and system else "fix_versions",
        cached=cached,
        evidence=at_target.used,
        dropped=at_target.dropped,
        error=error,
    )


def read_order(
    issue: JiraIssueRow,
    *,
    target_settled: bool,
    low: Version,
    high: Version,
    scheme: VersionScheme,
    recent_since: date | None,
) -> tuple:
    """Sort key for what to read first (lower first). Reading an issue whose target answer the
    fix versions already settle only tells whether you have the bug now, so those go last."""
    components = {c.component.strip().lower() for c in issue.components}
    not_product = bool(
        FLAKY.match(issue.summary)
        or "flaky-test" in (issue.labels or [])
        or (components and components <= NOT_PRODUCT)
    )
    recent = recent_since is not None and issue.created_at.date() >= recent_since
    return (
        target_settled,
        not_product,
        not (_reported_between(issue, low, high, scheme) or recent),
        PRIORITY_RANK.get(issue.priority or "", len(PRIORITY_RANK)),
    )


def _release_date(session: Session, dependency: Dependency, version: Version) -> date | None:
    """When ``version`` was released, from JIRA's version list."""
    rows = session.execute(
        select(JiraVersionRow.name, JiraVersionRow.release_date).where(
            JiraVersionRow.project == dependency.project,
            JiraVersionRow.release_date.is_not(None),
        )
    )
    for name, released in rows:
        try:
            if dependency.scheme.parse(name) == version:
                return released
        except VersionParseError:
            continue
    return None


def _reported_between(
    issue: JiraIssueRow, low: Version, high: Version, scheme: VersionScheme
) -> bool:
    """JIRA lists an affects version between the two: worth reading first."""
    for v in issue.versions:
        if v.kind != "affects":
            continue
        try:
            if low <= scheme.parse(v.name) <= high:
                return True
        except VersionParseError:
            continue
    return False


def _releases_between(session: Session, dependency: Dependency, low: Version, high: Version) -> int:
    names = session.scalars(
        select(JiraVersionRow.name).where(
            JiraVersionRow.project == dependency.project, JiraVersionRow.released.is_(True)
        )
    )
    count = 0
    for name in names:
        if not dependency.scheme.is_release(name):
            continue
        if low < dependency.scheme.parse(name) <= high:
            count += 1
    return count
