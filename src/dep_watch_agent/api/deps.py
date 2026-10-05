"""Settings and per-request dependencies, all hung off ``app.state`` so tests can swap them."""

import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session, sessionmaker

from dep_watch_agent.api.jobs import JobRegistry
from dep_watch_agent.systems import SystemRegistry

DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://localhost:3000"


@dataclass(frozen=True)
class Settings:
    datasets_dir: Path = Path("eval/datasets")
    runs_dir: Path = Path("eval/runs")
    cors_origins: list[str] = field(default_factory=list)
    migrate_on_startup: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        origins = os.environ.get("DEP_WATCH_CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
        return cls(
            datasets_dir=Path(os.environ.get("DEP_WATCH_DATASETS_DIR", "eval/datasets")),
            runs_dir=Path(os.environ.get("DEP_WATCH_RUNS_DIR", "eval/runs")),
            cors_origins=[o.strip() for o in origins.split(",") if o.strip()],
            migrate_on_startup=os.environ.get("DEP_WATCH_MIGRATE_ON_STARTUP", "1") != "0",
        )


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_sessions(request: Request) -> sessionmaker[Session]:
    return request.app.state.sessions


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.sessions() as session:
        yield session


def get_jobs(request: Request) -> JobRegistry:
    return request.app.state.jobs


def get_jira_client_factory(request: Request) -> Callable[..., Any]:
    return request.app.state.jira_client_factory


def get_langfuse_factory(request: Request) -> Callable[[], Any]:
    return request.app.state.langfuse_factory


def get_systems(request: Request) -> SystemRegistry:
    return request.app.state.systems


def pick_system(systems: SystemRegistry, name: str | None) -> str:
    """The requested system's name, or the first registered one. 503 if none is registered,
    422 if the name is unknown."""
    if not systems:
        raise HTTPException(503, "no system registered; set DEP_WATCH_LLM_MODEL (see .env.example)")
    name = name or next(iter(systems))
    if name not in systems:
        raise HTTPException(422, f"unknown system {name!r}; registered: {sorted(systems)}")
    return name


SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[Session, Depends(get_session)]
SessionsDep = Annotated[sessionmaker[Session], Depends(get_sessions)]
JobsDep = Annotated[JobRegistry, Depends(get_jobs)]
JiraClientFactoryDep = Annotated[Callable[..., Any], Depends(get_jira_client_factory)]
LangfuseFactoryDep = Annotated[Callable[[], Any], Depends(get_langfuse_factory)]
SystemsDep = Annotated[SystemRegistry, Depends(get_systems)]
