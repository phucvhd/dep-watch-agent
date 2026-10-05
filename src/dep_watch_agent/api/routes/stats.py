"""Numbers for the charts: issues over time and how long the model takes to read one."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from dep_watch_agent.api.deps import SessionDep
from dep_watch_agent.api.schemas import (
    MonthCount,
    ProjectKey,
    ReadingTime,
    ReadingTimeBin,
    SourceCount,
)
from dep_watch_agent.dependencies import DEPENDENCIES
from dep_watch_agent.orm import ExtractionRow, JiraIssueRow, SyncStateRow

router = APIRouter(tags=["stats"])

READING_BIN_SECONDS = 15
READING_BINS = 8  # 0-15 s ... 105-120 s, and the last bin holds everything slower


@router.get("/stats/sources", response_model=list[SourceCount])
def sources(session: SessionDep) -> list[SourceCount]:
    """Synced issues per dependency, in DEPENDENCIES order: where the issues come from."""
    projects = [d.project for d in DEPENDENCIES]
    is_bug = JiraIssueRow.issue_type == "Bug"
    rows = session.execute(
        select(
            JiraIssueRow.project,
            func.count(),
            func.count().filter(is_bug),
            func.count().filter(is_bug, JiraIssueRow.resolution.is_(None)),
        )
        .where(JiraIssueRow.project.in_(projects))
        .group_by(JiraIssueRow.project)
    )
    counts = {project: (issues, bugs, open_bugs) for project, issues, bugs, open_bugs in rows}
    watermarks = dict(session.execute(select(SyncStateRow.source, SyncStateRow.watermark)).all())
    return [
        SourceCount(
            dependency=d.id,
            name=d.name,
            project=d.project,
            issues=counts.get(d.project, (0, 0, 0))[0],
            bugs=counts.get(d.project, (0, 0, 0))[1],
            open_bugs=counts.get(d.project, (0, 0, 0))[2],
            synced_at=watermarks.get(f"jira:{d.project}"),
        )
        for d in DEPENDENCIES
    ]


@router.get("/stats/issues/monthly", response_model=list[MonthCount])
def monthly(
    session: SessionDep,
    project: ProjectKey,
    months: Annotated[int, Query(ge=1, le=120)] = 24,
    now: Annotated[datetime | None, Query(include_in_schema=False)] = None,
) -> list[MonthCount]:
    """Bugs filed and bugs fixed per calendar month (UTC), oldest first, the last ``months``
    months including the current one. Months with none are included as zero."""
    end = now or datetime.now(UTC)
    start_index = end.year * 12 + end.month - 1 - (months - 1)
    labels = [f"{i // 12:04d}-{i % 12 + 1:02d}" for i in range(start_index, start_index + months)]
    start = datetime(start_index // 12, start_index % 12 + 1, 1, tzinfo=UTC)

    def per_month(column, *conditions) -> dict[str, int]:
        month = func.to_char(func.date_trunc("month", func.timezone("UTC", column)), "YYYY-MM")
        rows = session.execute(
            select(month, func.count())
            .where(
                JiraIssueRow.project == project,
                JiraIssueRow.issue_type == "Bug",
                column >= start,
                *conditions,
            )
            .group_by(month)
        )
        return dict(rows.all())

    filed = per_month(JiraIssueRow.created_at)
    fixed = per_month(JiraIssueRow.resolved_at, JiraIssueRow.resolution == "Fixed")
    return [MonthCount(month=m, filed=filed.get(m, 0), fixed=fixed.get(m, 0)) for m in labels]


@router.get("/stats/reading", response_model=ReadingTime)
def reading_time(session: SessionDep, project: ProjectKey) -> ReadingTime:
    """How long reading one issue took the model, over the stored extractions."""
    durations = sorted(
        session.scalars(
            select(ExtractionRow.duration_ms)
            .join(JiraIssueRow, JiraIssueRow.id == ExtractionRow.issue_id)
            .where(JiraIssueRow.project == project)
        )
    )
    counts = [0] * READING_BINS
    for ms in durations:
        counts[min(int(ms / 1000 // READING_BIN_SECONDS), READING_BINS - 1)] += 1
    bins = [
        ReadingTimeBin(
            from_s=i * READING_BIN_SECONDS,
            to_s=None if i == READING_BINS - 1 else (i + 1) * READING_BIN_SECONDS,
            count=c,
        )
        for i, c in enumerate(counts)
    ]

    def quantile(q: float) -> int | None:
        return durations[min(len(durations) - 1, int(q * len(durations)))] if durations else None

    return ReadingTime(
        count=len(durations), median_ms=quantile(0.5), p90_ms=quantile(0.9), bins=bins
    )
