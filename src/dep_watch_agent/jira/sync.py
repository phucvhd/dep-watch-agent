"""Incremental sync of a JIRA project into Postgres.

How it stays correct:

- Results are ordered by ``created`` (which never changes), not ``updated``. If an issue is
  edited mid-sync it can newly match the filter and shift later pages, which causes a
  duplicate (harmless, upserts are idempotent) but never a skipped issue. Ordering by
  ``updated`` would move edited issues to the end and could skip others.
- The watermark saved is the time the run *started*, so anything edited during the run is
  picked up next time. It is only saved after the run completes; an interrupted run is
  simply redone.
- JQL date filters have minute precision and use the server's time zone, which is UTC for
  Apache JIRA. Each run looks back ``overlap`` before the watermark to absorb that rounding
  and any clock skew between this machine and the server.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import psycopg

from dep_watch_agent.jira.client import JiraClient
from dep_watch_agent.jira.models import comments_truncated, parse_issue
from dep_watch_agent.jira.store import load_watermark, save_watermark, upsert_issue

FIELDS = [
    "summary",
    "description",
    "status",
    "resolution",
    "issuetype",
    "priority",
    "components",
    "versions",
    "fixVersions",
    "labels",
    "created",
    "updated",
    "resolutiondate",
    "comment",
]

DEFAULT_OVERLAP = timedelta(minutes=10)


@dataclass(frozen=True)
class SyncResult:
    source: str
    since: datetime | None
    issues_synced: int
    watermark: datetime


def build_jql(project: str, since: datetime | None) -> str:
    clauses = [f'project = "{project}"']
    if since is not None:
        clauses.append(f'updated >= "{since.astimezone(UTC):%Y-%m-%d %H:%M}"')
    return " AND ".join(clauses) + " ORDER BY created ASC, key ASC"


def sync_project(
    conn: psycopg.Connection,
    client: JiraClient,
    project: str = "KAFKA",
    *,
    full: bool = False,
    overlap: timedelta = DEFAULT_OVERLAP,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    on_issue: Callable[[int], None] | None = None,
) -> SyncResult:
    """Sync issues updated since the last run, or every issue if ``full``."""
    source = f"jira:{project}"
    started_at = now()
    watermark = None if full else load_watermark(conn, source)
    since = watermark - overlap if watermark is not None else None

    count = 0
    for raw in client.search(build_jql(project, since), FIELDS):
        if comments_truncated(raw):
            raw["fields"]["comment"]["comments"] = client.comments(raw["key"])
        upsert_issue(conn, parse_issue(raw))
        count += 1
        if on_issue is not None:
            on_issue(count)

    save_watermark(conn, source, started_at)
    return SyncResult(source=source, since=since, issues_synced=count, watermark=started_at)
