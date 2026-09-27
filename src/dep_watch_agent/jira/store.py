"""Persist JIRA issues to Postgres. Every write is an idempotent upsert."""

from datetime import datetime

import psycopg
from psycopg.types.json import Jsonb

from dep_watch_agent.jira.models import JiraIssue


def upsert_issue(conn: psycopg.Connection, issue: JiraIssue) -> None:
    """Insert or replace an issue and its versions, components and comments."""
    with conn.transaction():
        conn.execute(
            """
            INSERT INTO jira_issues (
                id, key, project, summary, description, issue_type, status, resolution,
                priority, labels, created_at, updated_at, resolved_at, raw, synced_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (id) DO UPDATE SET
                key = EXCLUDED.key,
                project = EXCLUDED.project,
                summary = EXCLUDED.summary,
                description = EXCLUDED.description,
                issue_type = EXCLUDED.issue_type,
                status = EXCLUDED.status,
                resolution = EXCLUDED.resolution,
                priority = EXCLUDED.priority,
                labels = EXCLUDED.labels,
                created_at = EXCLUDED.created_at,
                updated_at = EXCLUDED.updated_at,
                resolved_at = EXCLUDED.resolved_at,
                raw = EXCLUDED.raw,
                synced_at = now()
            """,
            (
                issue.id,
                issue.key,
                issue.project,
                issue.summary,
                issue.description,
                issue.issue_type,
                issue.status,
                issue.resolution,
                issue.priority,
                issue.labels,
                issue.created_at,
                issue.updated_at,
                issue.resolved_at,
                Jsonb(issue.raw),
            ),
        )

        # Child rows are replaced wholesale so removed versions, components and deleted
        # comments disappear on re-sync.
        for table in ("jira_issue_versions", "jira_issue_components", "jira_comments"):
            conn.execute(f"DELETE FROM {table} WHERE issue_id = %s", (issue.id,))

        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO jira_issue_versions (issue_id, kind, name) VALUES (%s, %s, %s)",
                [(issue.id, "affects", v) for v in issue.affects_versions]
                + [(issue.id, "fix", v) for v in issue.fix_versions],
            )
            cur.executemany(
                "INSERT INTO jira_issue_components (issue_id, component) VALUES (%s, %s)",
                [(issue.id, c) for c in issue.components],
            )
            cur.executemany(
                """
                INSERT INTO jira_comments (id, issue_id, author, body, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    (c.id, issue.id, c.author, c.body, c.created_at, c.updated_at)
                    for c in issue.comments
                ],
            )


def load_watermark(conn: psycopg.Connection, source: str) -> datetime | None:
    row = conn.execute("SELECT watermark FROM sync_state WHERE source = %s", (source,)).fetchone()
    return row[0] if row else None


def save_watermark(conn: psycopg.Connection, source: str, watermark: datetime) -> None:
    with conn.transaction():
        conn.execute(
            """
            INSERT INTO sync_state (source, watermark) VALUES (%s, %s)
            ON CONFLICT (source) DO UPDATE SET watermark = EXCLUDED.watermark, updated_at = now()
            """,
            (source, watermark),
        )
