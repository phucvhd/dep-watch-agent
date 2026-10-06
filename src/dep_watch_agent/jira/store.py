"""Persist JIRA issues to Postgres. Every write is an idempotent upsert.

These functions don't commit; the caller owns the transaction.
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import delete, func, literal_column, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from dep_watch_agent.jira.models import JiraIssue
from dep_watch_agent.orm import (
    JiraCommentRow,
    JiraIssueComponentRow,
    JiraIssueRow,
    JiraIssueVersionRow,
    JiraVersionRow,
    SyncRunRow,
    SyncStateRow,
)


def upsert_issue(session: Session, issue: JiraIssue) -> bool:
    """Insert or replace an issue and its versions, components and comments. True if the issue
    is new to the database."""
    values = {
        "id": issue.id,
        "key": issue.key,
        "project": issue.project,
        "summary": issue.summary,
        "description": issue.description,
        "issue_type": issue.issue_type,
        "status": issue.status,
        "resolution": issue.resolution,
        "priority": issue.priority,
        "labels": issue.labels,
        "created_at": issue.created_at,
        "updated_at": issue.updated_at,
        "resolved_at": issue.resolved_at,
        "raw": issue.raw,
    }
    stmt = insert(JiraIssueRow).values(values)  # synced_at defaults to now() on insert
    # xmax is 0 only on a row this statement inserted; an updated row carries the updater's id.
    inserted = session.scalar(
        stmt.on_conflict_do_update(
            index_elements=[JiraIssueRow.id],
            set_={**{k: stmt.excluded[k] for k in values if k != "id"}, "synced_at": func.now()},
        ).returning(literal_column("xmax = 0"))
    )

    # Child rows are replaced wholesale so removed versions, components and deleted comments
    # disappear on re-sync.
    for child in (JiraIssueVersionRow, JiraIssueComponentRow, JiraCommentRow):
        session.execute(delete(child).where(child.issue_id == issue.id))

    versions = [
        {"issue_id": issue.id, "kind": kind, "name": name}
        for kind, names in (("affects", issue.affects_versions), ("fix", issue.fix_versions))
        for name in names
    ]
    components = [{"issue_id": issue.id, "component": c} for c in issue.components]
    comments = [
        {
            "id": c.id,
            "issue_id": issue.id,
            "author": c.author,
            "body": c.body,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in issue.comments
    ]
    for model, rows in (
        (JiraIssueVersionRow, versions),
        (JiraIssueComponentRow, components),
        (JiraCommentRow, comments),
    ):
        if rows:
            session.execute(insert(model), rows)
    return bool(inserted)


def upsert_versions(session: Session, project: str, versions: list[dict[str, Any]]) -> int:
    """Insert or update a project's versions from the JIRA API. Returns how many."""
    rows = [
        {
            "id": int(v["id"]),
            "project": project,
            "name": v["name"],
            "released": bool(v.get("released", False)),
            "archived": bool(v.get("archived", False)),
            "release_date": date.fromisoformat(v["releaseDate"]) if v.get("releaseDate") else None,
        }
        for v in versions
    ]
    if not rows:
        return 0
    stmt = insert(JiraVersionRow)
    session.execute(
        stmt.on_conflict_do_update(
            index_elements=[JiraVersionRow.id],
            set_={
                k: stmt.excluded[k]
                for k in ("project", "name", "released", "archived", "release_date")
            },
        ),
        rows,
    )
    return len(rows)


def load_watermark(session: Session, source: str) -> datetime | None:
    # A column query, not session.get(): the identity map would return a cached row that
    # save_watermark's upsert doesn't update.
    return session.scalar(select(SyncStateRow.watermark).where(SyncStateRow.source == source))


def save_watermark(session: Session, source: str, watermark: datetime) -> None:
    stmt = insert(SyncStateRow).values(source=source, watermark=watermark)
    session.execute(
        stmt.on_conflict_do_update(
            index_elements=[SyncStateRow.source],
            set_={"watermark": stmt.excluded.watermark, "updated_at": func.now()},
        )
    )


def record_sync_run(session: Session, **values: Any) -> None:
    session.add(SyncRunRow(**values))
