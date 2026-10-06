"""The FastAPI application.

``create_app`` takes every external dependency as an argument (database sessions, JIRA client,
Langfuse client, job registry, systems) so tests can replace them; by default they come from the
environment, as documented in ``.env.example``.
"""

import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, sessionmaker

from dep_watch_agent import __version__
from dep_watch_agent.api.deps import Settings
from dep_watch_agent.api.jobs import JobConflict, JobRegistry
from dep_watch_agent.api.routes import eval as eval_routes
from dep_watch_agent.api.routes import issues, ops, repo, scan, stats
from dep_watch_agent.api.schemas import JobOut
from dep_watch_agent.eval.dataset import DatasetError
from dep_watch_agent.systems import SystemRegistry, configured_systems


def create_app(
    *,
    settings: Settings | None = None,
    sessions: sessionmaker[Session] | None = None,
    jobs: JobRegistry | None = None,
    jira_client_factory: Callable[..., Any] | None = None,
    langfuse_factory: Callable[[], Any] | None = None,
    systems: SystemRegistry | None = None,
) -> FastAPI:
    load_dotenv()  # .env in the working directory; real environment variables win
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.migrate_on_startup:
            from dep_watch_agent.db import migrate

            migrate()
        yield

    app = FastAPI(
        title="DWatcher",
        description="Does an upstream issue affect the version I run?",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.sessions = sessions or _default_sessions()
    app.state.jobs = jobs or JobRegistry()
    app.state.jira_client_factory = jira_client_factory or _default_jira_client
    app.state.langfuse_factory = langfuse_factory or _default_langfuse
    app.state.systems = configured_systems() if systems is None else systems

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.exception_handler(JobConflict)
    async def job_conflict(request: Request, exc: JobConflict) -> JSONResponse:
        job = JobOut.model_validate(exc.existing)
        return JSONResponse(
            status_code=409, content={"detail": str(exc), "job": jsonable_encoder(job)}
        )

    @app.exception_handler(DatasetError)
    async def dataset_error(request: Request, exc: DatasetError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    app.include_router(ops.router)
    app.include_router(issues.router)
    app.include_router(scan.router)
    app.include_router(repo.router)
    app.include_router(stats.router)
    app.include_router(eval_routes.router)
    return app


def main() -> None:
    """Serve the API: ``uv run dep-watch-agent``. Host and port from ``DEP_WATCH_HOST`` and
    ``DEP_WATCH_PORT``."""
    import uvicorn

    load_dotenv()
    uvicorn.run(
        "dep_watch_agent.api.app:create_app",
        factory=True,
        host=os.environ.get("DEP_WATCH_HOST", "127.0.0.1"),
        port=int(os.environ.get("DEP_WATCH_PORT", "8000")),
    )


def _default_sessions() -> sessionmaker[Session]:
    from dep_watch_agent.db import session_factory

    return session_factory()


def _default_jira_client(**kwargs: Any) -> Any:
    from dep_watch_agent.jira.client import JiraClient

    return JiraClient(**kwargs)


def _default_langfuse() -> Any:
    from langfuse import Langfuse

    return Langfuse()
