"""Health, background jobs, and JIRA sync."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from dep_watch_agent import __version__
from dep_watch_agent.api.deps import (
    JiraClientFactoryDep,
    JobsDep,
    SessionDep,
    SessionsDep,
    SystemsDep,
)
from dep_watch_agent.api.schemas import (
    DependencyOut,
    Health,
    JobOut,
    ProjectKey,
    SyncRequest,
    SyncRun,
    SyncState,
)
from dep_watch_agent.dependencies import DEPENDENCIES
from dep_watch_agent.orm import JiraIssueRow, SyncRunRow, SyncStateRow

router = APIRouter()


@router.get("/health", response_model=Health, tags=["ops"])
def health(session: SessionDep) -> Health:
    from alembic.runtime.migration import MigrationContext

    revision = MigrationContext.configure(session.connection()).get_current_revision()
    return Health(status="ok", version=__version__, db_revision=revision)


@router.get("/dependencies", response_model=list[DependencyOut], tags=["ops"])
def list_dependencies(session: SessionDep) -> list[DependencyOut]:
    """The catalog of sources, in a fixed order, each marked if it has been added (synced)."""
    added = added_projects(session)
    return [
        DependencyOut(
            id=d.id,
            name=d.name,
            project=d.project,
            tracker_url=d.tracker_url,
            watchable=d.watchable,
            added=d.project in added,
        )
        for d in DEPENDENCIES
    ]


def added_projects(session) -> set[str]:
    """Projects with synced issues. A sync commits issue by issue, so a first sync counts as
    soon as its first issue is in."""
    return set(session.scalars(select(JiraIssueRow.project).distinct()))


@router.get("/systems", response_model=list[str], tags=["ops"])
def list_systems(systems: SystemsDep) -> list[str]:
    """Registered systems, the default (used when a request names none) first. Empty when no
    model is configured; ``/check`` and ``/scan`` then return 503."""
    return list(systems)


@router.get("/jobs", response_model=list[JobOut], tags=["jobs"])
def list_jobs(jobs: JobsDep, kind: str | None = None):
    """Jobs since the server started, newest first."""
    return jobs.list(kind)


@router.get("/jobs/{job_id}", response_model=JobOut, responses={404: {}}, tags=["jobs"])
def get_job(job_id: str, jobs: JobsDep):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(404, f"no job {job_id}; jobs are forgotten on restart")
    return job


@router.post(
    "/sync/jira",
    response_model=JobOut,
    status_code=status.HTTP_202_ACCEPTED,
    responses={409: {"description": "A sync of this project is already running"}},
    tags=["sync"],
)
def start_jira_sync(
    body: SyncRequest, jobs: JobsDep, sessions: SessionsDep, jira_client: JiraClientFactoryDep
):
    """Sync issues updated since the last run (or all, with ``full``). Poll ``/jobs/{id}``;
    ``progress`` counts issues synced so far."""
    from dep_watch_agent.jira.sync import sync_project

    def run(progress):
        with sessions() as session, jira_client(request_delay=body.request_delay) as client:
            result = sync_project(session, client, body.project, full=body.full, on_issue=progress)
        return {
            "source": result.source,
            "since": result.since.isoformat() if result.since else None,
            "issues_synced": result.issues_synced,
            "new_issues": result.new_issues,
            "versions_synced": result.versions_synced,
            "watermark": result.watermark.isoformat(),
        }

    return jobs.submit("sync-jira", run, key=f"sync:{body.project}", params=body.model_dump())


@router.get("/sync/runs", response_model=list[SyncRun], tags=["sync"])
def sync_runs(
    session: SessionDep, project: ProjectKey, limit: Annotated[int, Query(ge=1, le=200)] = 20
):
    """The project's syncs, newest first: finished and failed ones, with what each fetched."""
    return session.scalars(
        select(SyncRunRow)
        .where(SyncRunRow.source == f"jira:{project}")
        .order_by(SyncRunRow.started_at.desc(), SyncRunRow.id.desc())
        .limit(limit)
    ).all()


@router.get("/sync/state", response_model=list[SyncState], tags=["sync"])
def sync_state(session: SessionDep):
    """Watermark per source: everything updated before it has been synced."""
    return session.scalars(select(SyncStateRow).order_by(SyncStateRow.source)).all()
