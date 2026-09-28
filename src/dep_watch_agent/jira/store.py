"""Persist JIRA issues to Postgres. Every write is an idempotent upsert.

These functions don't commit; the caller owns the transaction.
"""

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from dep_watch_agent.jira.models import JiraIssue
from dep_watch_agent.orm import (
    JiraCommentRow,
    JiraIssueComponentRow,
    JiraIssueRow,
    JiraIssueVersionRow,
    SyncStateRow,
)


def upsert_issue(session: Session, issue: JiraIssue) -> None:
    """Insert or replace an issue and its versions, components and comments."""
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
    session.execute(
        stmt.on_conflict_do_update(
            index_elements=[JiraIssueRow.id],
            set_={**{k: stmt.excluded[k] for k in values if k != "id"}, "synced_at": func.now()},
        )
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
