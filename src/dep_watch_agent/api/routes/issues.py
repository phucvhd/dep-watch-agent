"""Synced JIRA data, and the check: does this issue affect my Kafka version?"""

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
    IssueSummary,
    KafkaVersion,
    ProjectKey,
)
from dep_watch_agent.check import IssueNotFound, check_issue, issue_url, load_issue
from dep_watch_agent.orm import (
    JiraIssueComponentRow,
    JiraIssueRow,
    JiraIssueVersionRow,
    JiraVersionRow,
)
from dep_watch_agent.verdict import is_release
from dep_watch_agent.versions import VersionParseError, parse_version

router = APIRouter(tags=["issues"])


@router.get("/issues", response_model=IssuePage)
def list_issues(
    session: SessionDep,
    project: ProjectKey = "KAFKA",
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
    return IssueDetail(
        **_summary(issue).model_dump(),
        project=issue.project,
        description=issue.description,
        labels=issue.labels,
        components=sorted(c.component for c in issue.components),
        affects_versions=sorted_versions(v.name for v in issue.versions if v.kind == "affects"),
        fix_versions=sorted_versions(v.name for v in issue.versions if v.kind == "fix"),
        comments=issue.comments,
    )


@router.get("/versions", response_model=list[KafkaVersion])
def list_versions(
    session: SessionDep, project: ProjectKey = "KAFKA", released: bool | None = None
) -> list[JiraVersionRow]:
    """Oldest first, ordered by the version module (3.9.0 before 3.10.0). Names that don't
    parse as versions come last."""
    stmt = select(JiraVersionRow).where(JiraVersionRow.project == project)
    if released is not None:
        stmt = stmt.where(JiraVersionRow.released.is_(released))
    rows = list(session.scalars(stmt))
    order = {name: i for i, name in enumerate(sorted_versions(r.name for r in rows))}
    return sorted(rows, key=lambda r: order[r.name])


@router.post("/check", response_model=CheckResponse, responses={404: {}, 422: {}, 503: {}})
def check(body: CheckRequest, session: SessionDep, systems: SystemsDep) -> CheckResponse:
    """Is ``kafka_version`` affected by the issue? Decided by code from cited facts; the answer
    may be ``insufficient_information``. 503 until a system is registered."""
    if not is_release(body.kafka_version):
        raise HTTPException(
            422, f"{body.kafka_version!r} is not a specific Kafka release, e.g. 3.6.1"
        )
    name = pick_system(systems, body.system)
    try:
        result = check_issue(session, body.issue_key, body.kafka_version, name, systems[name]())
    except IssueNotFound:
        raise HTTPException(404, f"issue {body.issue_key} not synced") from None

    decision = result.decision
    return CheckResponse(
        issue_key=result.issue.key,
        url=result.url,
        summary=result.issue.summary,
        kafka_version=result.kafka_version,
        answer=decision.answer,
        system=result.system,
        decided_by=result.decided_by,
        cached=result.cached,
        fix_versions=sorted_versions(result.issue_text.fix_versions),
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


def sorted_versions(names) -> list[str]:
    """Version order from the version module; unparseable names last, by name."""
    parsed, other = [], []
    for name in names:
        try:
            parsed.append((parse_version(name), name))
        except VersionParseError:
            other.append(name)
    return [name for _, name in sorted(parsed)] + sorted(other)
