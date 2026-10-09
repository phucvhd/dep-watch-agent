"""Which synced issues affect one pinned version? The alerting flow, end to end.

Tier 1 (SQL, no LLM): bugs whose resolution doesn't say they weren't real, and that aren't only
a subproject's (``Adapter.subprojects``), optionally only those updated since a date (this
week's issues), newest first. Then each issue is answered by
``check.answer_issue``: code first from the fix versions, the system's cited facts otherwise.
Every issue gets one of the three answers; one that fails (e.g. the model server is down) is
reported with its error and answered ``insufficient_information``, so a scan never drops an
issue silently.
"""

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import and_, exists, func, not_, or_, select
from sqlalchemy.orm import Session, selectinload

from dep_watch_agent import extractions
from dep_watch_agent.check import Answered, answer_issue, issue_text, issue_url
from dep_watch_agent.dependencies import Dependency
from dep_watch_agent.eval.runner import Extractor
from dep_watch_agent.extractions import ExtractionFailed
from dep_watch_agent.orm import JiraIssueRow, JiraIssueVersionRow
from dep_watch_agent.verdict import (
    AFFECTED,
    ANSWERS,
    INSUFFICIENT_INFORMATION,
    NOT_AFFECTED,
    Decision,
    DroppedEvidence,
    Evidence,
    Extraction,
    decide,
)

BUG_TYPES = ("Bug",)
# Resolutions saying there was no bug of its own to be affected by. "Won't Fix" and the like
# stay: the bug is real and may never be fixed.
NOT_A_BUG_RESOLUTIONS = (
    "Duplicate",
    "Not A Problem",
    "Invalid",
    "Cannot Reproduce",
    "Not A Bug",
    "Information Provided",
    "Incomplete",
    "Works for Me",
)
# Answers in report order: what needs action first.
REPORT_ORDER = {AFFECTED: 0, INSUFFICIENT_INFORMATION: 1}


@dataclass(frozen=True)
class ScanItem:
    issue_key: str
    url: str
    summary: str
    status: str | None
    resolution: str | None
    updated_at: datetime
    fix_versions: list[str]
    answer: str
    decided_by: str
    evidence: list[Evidence] = field(default_factory=list)
    dropped: list[DroppedEvidence] = field(default_factory=list)
    cached: bool = False
    error: str | None = None


@dataclass(frozen=True)
class ScanResult:
    version: str
    system: str
    since: datetime | None
    candidates_total: int
    items: list[ScanItem]

    @property
    def counts(self) -> dict[str, int]:
        counter = Counter(item.answer for item in self.items)
        return {answer: counter[answer] for answer in ANSWERS}

    @property
    def errors(self) -> int:
        return sum(item.error is not None for item in self.items)

    @property
    def cached(self) -> int:
        return sum(item.cached for item in self.items)


def candidates_query(dependency: Dependency, since: datetime | None):
    stmt = select(JiraIssueRow).where(
        JiraIssueRow.project == dependency.project,
        JiraIssueRow.issue_type.in_(BUG_TYPES),
        or_(
            JiraIssueRow.resolution.is_(None),
            JiraIssueRow.resolution.not_in(NOT_A_BUG_RESOLUTIONS),
        ),
    )
    subprojects = dependency.adapter.subprojects if dependency.adapter else ()
    if subprojects:
        # Versions, and none of them the dependency's own: another product's bug. An issue
        # without versions stays (unreleased fixes, open bugs).
        of_issue = JiraIssueVersionRow.issue_id == JiraIssueRow.id
        theirs = or_(*(JiraIssueVersionRow.name.startswith(p) for p in subprojects))
        stmt = stmt.where(
            not_(
                and_(
                    exists().where(of_issue, theirs),
                    ~exists().where(of_issue, not_(theirs)),
                )
            )
        )
    if since is not None:
        stmt = stmt.where(JiraIssueRow.updated_at >= since)
    return stmt


def scan_version(
    session: Session,
    dependency: Dependency,
    version: str,
    system: str,
    extractor: Extractor,
    *,
    since: datetime | None = None,
    limit: int | None = None,
    on_issue: Callable[[int], None] | None = None,
) -> ScanResult:
    """Answer every candidate issue of ``dependency`` (newest first, at most ``limit``) for
    ``version``, which must already be validated (``check.answerable``)."""
    stmt = candidates_query(dependency, since)
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    issues = session.scalars(
        stmt.order_by(JiraIssueRow.updated_at.desc(), JiraIssueRow.id.desc())
        .limit(limit)
        .options(selectinload(JiraIssueRow.versions), selectinload(JiraIssueRow.comments))
    ).all()

    items = []
    for done, issue in enumerate(issues, 1):
        text = issue_text(issue)
        # Read before answering: storing a new extraction commits, which expires the rows.
        fields = {
            "issue_key": issue.key,
            "url": issue_url(issue.key),
            "summary": issue.summary,
            "status": issue.status,
            "resolution": issue.resolution,
            "updated_at": issue.updated_at,
            "fix_versions": text.fix_versions,
        }
        try:
            answered = answer_issue(
                session, issue.id, text, version, dependency.scheme, system, extractor
            )
            assert answered is not None  # read=True always answers
            error = None
        except Exception as exc:  # one failed issue must not lose the others
            session.rollback()
            answered = Answered(Decision(INSUFFICIENT_INFORMATION, [], []), system)
            error = (
                str(exc) if isinstance(exc, ExtractionFailed) else f"{type(exc).__name__}: {exc}"
            )
        decision = answered.decision
        items.append(
            ScanItem(
                **fields,
                answer=decision.answer,
                decided_by=answered.decided_by,
                evidence=decision.used,
                dropped=decision.dropped,
                cached=answered.cached,
                error=error,
            )
        )
        if on_issue:
            on_issue(done)

    items.sort(key=lambda i: REPORT_ORDER.get(i.answer, 2))  # stable: newest first within
    return ScanResult(version, system, since, total, items)


@dataclass(frozen=True)
class Backlog:
    """What a scan of ``version`` would find, by what answers each candidate."""

    candidates: int
    settled: int  # the fix versions answer it: no model call
    checked: int  # the system's facts are stored for its current text
    unchecked: int  # a scan would have the system read it


def backlog(
    session: Session,
    dependency: Dependency,
    version: str,
    system: str | None,
    extractor: Extractor | None,
    *,
    since: datetime | None = None,
) -> Backlog:
    """Count the candidates a scan would answer, without calling the system: those the fix
    versions settle, those with stored facts, and the rest, which would each take a model call.
    ``version`` must already be validated (``check.answerable``)."""
    issues = session.scalars(
        candidates_query(dependency, since).options(
            selectinload(JiraIssueRow.versions), selectinload(JiraIssueRow.comments)
        )
    ).all()
    stored = (
        extractions.stored_texts(session, [i.id for i in issues], system, extractor)
        if system and extractor
        else set()
    )
    settled = checked = 0
    for issue in issues:
        text = issue_text(issue)
        if decide(text, version, Extraction([]), dependency.scheme).answer == NOT_AFFECTED:
            settled += 1
        elif (issue.id, extractions.text_hash(text)) in stored:
            checked += 1
    return Backlog(len(issues), settled, checked, len(issues) - settled - checked)
