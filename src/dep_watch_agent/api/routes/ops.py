"""Health, background jobs, and JIRA sync."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from dep_watch_agent import __version__
from dep_watch_agent.api.deps import JiraClientFactoryDep, JobsDep, SessionDep, SessionsDep
from dep_watch_agent.api.schemas import Health, JobOut, SyncRequest, SyncState
from dep_watch_agent.orm import SyncStateRow

router = APIRouter()


@router.get("/health", response_model=Health, tags=["ops"])
def health(session: SessionDep) -> Health:
    from alembic.runtime.migration import MigrationContext

    revision = MigrationContext.configure(session.connection()).get_current_revision()
    return Health(status="ok", version=__version__, db_revision=revision)


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
            "versions_synced": result.versions_synced,
            "watermark": result.watermark.isoformat(),
        }

    return jobs.submit("sync-jira", run, key=f"sync:{body.project}", params=body.model_dump())


@router.get("/sync/state", response_model=list[SyncState], tags=["sync"])
def sync_state(session: SessionDep):
    """Watermark per source: everything updated before it has been synced."""
    return session.scalars(select(SyncStateRow).order_by(SyncStateRow.source)).all()
