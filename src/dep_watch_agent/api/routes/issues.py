"""Synced JIRA data, and the check: does this issue affect the version I run?"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from dep_watch_agent.api.deps import SessionDep, SystemsDep, pick_system
from dep_watch_agent.api.schemas import (
    CheckRequest,
    CheckResponse,
    DroppedEvidenceOut,
    EvidenceOut,
    IssueDetail,
    IssuePage,
    IssueStats,
    IssueSummary,
    ProjectKey,
    ReleaseVersion,
    StoredAnswer,
)
from dep_watch_agent.check import (
    CheckResult,
    IssueNotFound,
    NotAnswerable,
    check_issue,
    issue_url,
    load_issue,
)
from dep_watch_agent.dependencies import scheme_for_project
from dep_watch_agent.orm import (
    ExtractionRow,
    JiraIssueComponentRow,
    JiraIssueRow,
    JiraIssueVersionRow,
    JiraVersionRow,
)
from dep_watch_agent.versions import VersionParseError, VersionScheme

router = APIRouter(tags=["issues"])


@router.get("/issues", response_model=IssuePage)
def list_issues(
    session: SessionDep,
    project: ProjectKey,
    q: Annotated[str | None, Query(description="Issue key, or text in the summary")] = None,
    issue_type: str | None = None,
    status: str | None = None,
    resolution: str | None = None,
    component: str | None = None,
    affects_version: str | None = None,
    fix_version: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> IssuePage:
    """Newest first. Version filters match a version name exactly; they don't compare versions."""
    stmt = select(JiraIssueRow).where(JiraIssueRow.project == project)
    if q:
        stmt = stmt.where(
            (JiraIssueRow.key == q.strip().upper())
            | JiraIssueRow.summary.icontains(q, autoescape=True)
        )
    for column, value in (
        (JiraIssueRow.issue_type, issue_type),
        (JiraIssueRow.status, status),
        (JiraIssueRow.resolution, resolution),
    ):
        if value:
            stmt = stmt.where(column == value)
    if component:
        stmt = stmt.where(JiraIssueRow.components.any(JiraIssueComponentRow.component == component))
    for kind, name in (("affects", affects_version), ("fix", fix_version)):
        if name:
            stmt = stmt.where(
                JiraIssueRow.versions.any(
                    (JiraIssueVersionRow.kind == kind) & (JiraIssueVersionRow.name == name)
                )
            )

    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = session.scalars(
        stmt.order_by(JiraIssueRow.created_at.desc(), JiraIssueRow.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return IssuePage(total=total, limit=limit, offset=offset, items=[_summary(row) for row in rows])


@router.get("/issues/{key}", response_model=IssueDetail, responses={404: {}})
def get_issue(key: str, session: SessionDep) -> IssueDetail:
    try:
        issue = load_issue(session, key)
    except IssueNotFound:
        raise HTTPException(404, f"issue {key} not synced") from None
    scheme = scheme_for_project(issue.project)
    return IssueDetail(
        **_summary(issue).model_dump(),
        project=issue.project,
        description=issue.description,
        labels=issue.labels,
        components=sorted(c.component for c in issue.components),
        affects_versions=sorted_versions(
            (v.name for v in issue.versions if v.kind == "affects"), scheme
        ),
        fix_versions=sorted_versions((v.name for v in issue.versions if v.kind == "fix"), scheme),
        comments=issue.comments,
    )


@router.get("/versions", response_model=list[ReleaseVersion])
def list_versions(
    session: SessionDep, project: ProjectKey, released: bool | None = None
) -> list[JiraVersionRow]:
    """Oldest first, ordered by the version module in the project's scheme (3.9.0 before
    3.10.0). Names that don't parse as versions come last."""
    stmt = select(JiraVersionRow).where(JiraVersionRow.project == project)
    if released is not None:
        stmt = stmt.where(JiraVersionRow.released.is_(released))
    rows = list(session.scalars(stmt))
    names = sorted_versions((r.name for r in rows), scheme_for_project(project))
    order = {name: i for i, name in enumerate(names)}
    return sorted(rows, key=lambda r: order[r.name])


@router.post("/check", response_model=CheckResponse, responses={404: {}, 422: {}, 503: {}})
def check(body: CheckRequest, session: SessionDep, systems: SystemsDep) -> CheckResponse:
    """Is ``version`` affected by the issue? Decided by code from cited facts; the answer may be
    ``insufficient_information``. 422 when the issue's dependency isn't answered or the version
    isn't one of its releases; 503 until a system is registered."""
    name = pick_system(systems, body.system)
    try:
        result = check_issue(session, body.issue_key, body.version, name, systems[name]())
    except IssueNotFound:
        raise HTTPException(404, f"issue {body.issue_key} not synced") from None
    except NotAnswerable as exc:
        raise HTTPException(422, str(exc)) from None
    assert result is not None  # read=True always answers
    return check_response(result)


@router.get("/issues/{key}/answer", response_model=StoredAnswer, responses={404: {}, 422: {}})
def stored_answer(
    key: str,
    session: SessionDep,
    systems: SystemsDep,
    version: Annotated[str, Query(examples=["3.9.1"])],
    system: str | None = None,
) -> StoredAnswer:
    """The answer for ``version`` if it needs no model call: the fix versions settle it, or the
    system's facts for this issue are stored. Otherwise ``answered`` is false and ``POST /check``
    reads the issue."""
    name = pick_system(systems, system) if systems else None
    try:
        result = check_issue(
            session, key, version, name, systems[name]() if name else None, read=False
        )
    except IssueNotFound:
        raise HTTPException(404, f"issue {key} not synced") from None
    except NotAnswerable as exc:
        raise HTTPException(422, str(exc)) from None
    if result is None:
        return StoredAnswer(answered=False, system=name)
    return StoredAnswer(answered=True, system=name, result=check_response(result))


@router.get("/stats/issues", response_model=IssueStats)
def issue_stats(session: SessionDep, project: ProjectKey) -> IssueStats:
    """Counts over the synced issues, for the top of the issues page."""
    issues = select(JiraIssueRow).where(JiraIssueRow.project == project).subquery()
    total = session.scalar(select(func.count()).select_from(issues)) or 0
    bugs = select(JiraIssueRow).where(
        JiraIssueRow.project == project, JiraIssueRow.issue_type == "Bug"
    )
    bug_count = session.scalar(select(func.count()).select_from(bugs.subquery())) or 0
    open_bugs = (
        session.scalar(
            select(func.count()).select_from(
                bugs.where(JiraIssueRow.resolution.is_(None)).subquery()
            )
        )
        or 0
    )
    fixed_bugs = (
        session.scalar(
            select(func.count()).select_from(
                bugs.where(JiraIssueRow.resolution == "Fixed").subquery()
            )
        )
        or 0
    )
    newest = session.scalar(
        select(func.max(JiraIssueRow.updated_at)).where(JiraIssueRow.project == project)
    )
    read = (
        session.scalar(
            select(func.count(func.distinct(ExtractionRow.issue_id)))
            .join(JiraIssueRow, JiraIssueRow.id == ExtractionRow.issue_id)
            .where(JiraIssueRow.project == project)
        )
        or 0
    )
    return IssueStats(
        total=total,
        bugs=bug_count,
        open_bugs=open_bugs,
        fixed_bugs=fixed_bugs,
        read=read,
        newest=newest,
    )


def check_response(result: CheckResult) -> CheckResponse:
    decision = result.decision
    return CheckResponse(
        issue_key=result.issue.key,
        url=result.url,
        summary=result.issue.summary,
        version=result.version,
        answer=decision.answer,
        system=result.system,
        decided_by=result.decided_by,
        cached=result.cached,
        fix_versions=sorted_versions(
            result.issue_text.fix_versions, scheme_for_project(result.issue.project)
        ),
        evidence=evidence_out(decision.used),
        dropped=dropped_out(decision.dropped),
    )


def evidence_out(used) -> list[EvidenceOut]:
    return [EvidenceOut(version=e.version, kind=e.kind, quote=e.quote) for e in used]


def dropped_out(dropped) -> list[DroppedEvidenceOut]:
    return [
        DroppedEvidenceOut(
            version=d.evidence.version,
            kind=d.evidence.kind,
            quote=d.evidence.quote,
            reason=d.reason,
        )
        for d in dropped
    ]


def _summary(row: JiraIssueRow) -> IssueSummary:
    return IssueSummary(
        key=row.key,
        url=issue_url(row.key),
        summary=row.summary,
        issue_type=row.issue_type,
        status=row.status,
        resolution=row.resolution,
        priority=row.priority,
        created_at=row.created_at,
        updated_at=row.updated_at,
        resolved_at=row.resolved_at,
    )


def sorted_versions(names, scheme: VersionScheme) -> list[str]:
    """Version order from the version module; unparseable names last, by name."""
    parsed, other = [], []
    for name in names:
        try:
            parsed.append((scheme.parse(name), name))
        except VersionParseError:
            other.append(name)
    return [name for _, name in sorted(parsed)] + sorted(other)
