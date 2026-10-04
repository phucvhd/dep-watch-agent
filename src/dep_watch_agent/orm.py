"""SQLAlchemy models: the single definition of the database schema.

Alembic autogenerates migrations from ``Base.metadata``, and the test suite runs
``alembic check`` so these models can't drift from the migrations.

Version names are plain text columns. Parsing and comparison happen in
``dep_watch_agent.versions``, never in SQL.
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

Timestamp = DateTime(timezone=True)


class Base(DeclarativeBase):
    pass


class JiraIssueRow(Base):
    """A JIRA issue as synced. Keyed by JIRA's numeric id because keys change when an issue
    moves between projects."""

    __tablename__ = "jira_issues"
    __table_args__ = (Index("jira_issues_project_updated_idx", "project", "updated_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    key: Mapped[str] = mapped_column(Text, unique=True)
    project: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    issue_type: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text)
    resolution: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str | None] = mapped_column(Text)
    labels: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=text("'{}'"))
    created_at: Mapped[datetime] = mapped_column(Timestamp)
    updated_at: Mapped[datetime] = mapped_column(Timestamp)
    resolved_at: Mapped[datetime | None] = mapped_column(Timestamp)
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB)
    synced_at: Mapped[datetime] = mapped_column(Timestamp, server_default=func.now())

    versions: Mapped[list["JiraIssueVersionRow"]] = relationship(
        back_populates="issue", passive_deletes=True
    )
    components: Mapped[list["JiraIssueComponentRow"]] = relationship(
        back_populates="issue", passive_deletes=True
    )
    comments: Mapped[list["JiraCommentRow"]] = relationship(
        back_populates="issue", passive_deletes=True, order_by="JiraCommentRow.created_at"
    )


class JiraIssueVersionRow(Base):
    __tablename__ = "jira_issue_versions"
    __table_args__ = (
        CheckConstraint("kind IN ('affects', 'fix')", name="jira_issue_versions_kind_check"),
        Index("jira_issue_versions_name_idx", "name", "kind"),
    )

    issue_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("jira_issues.id", ondelete="CASCADE"), primary_key=True
    )
    kind: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, primary_key=True)

    issue: Mapped[JiraIssueRow] = relationship(back_populates="versions")


class JiraIssueComponentRow(Base):
    __tablename__ = "jira_issue_components"
    __table_args__ = (Index("jira_issue_components_component_idx", "component"),)

    issue_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("jira_issues.id", ondelete="CASCADE"), primary_key=True
    )
    component: Mapped[str] = mapped_column(Text, primary_key=True)

    issue: Mapped[JiraIssueRow] = relationship(back_populates="components")


class JiraCommentRow(Base):
    __tablename__ = "jira_comments"
    __table_args__ = (Index("jira_comments_issue_idx", "issue_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    issue_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("jira_issues.id", ondelete="CASCADE")
    )
    author: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(Timestamp)
    updated_at: Mapped[datetime] = mapped_column(Timestamp)

    issue: Mapped[JiraIssueRow] = relationship(back_populates="comments")


class JiraVersionRow(Base):
    """A version defined in a JIRA project, released or not."""

    __tablename__ = "jira_versions"
    __table_args__ = (UniqueConstraint("project", "name"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    project: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    released: Mapped[bool] = mapped_column(Boolean)
    archived: Mapped[bool] = mapped_column(Boolean)
    release_date: Mapped[date | None] = mapped_column(Date)


class SyncStateRow(Base):
    """Incremental sync watermark per source, e.g. ``jira:KAFKA``."""

    __tablename__ = "sync_state"

    source: Mapped[str] = mapped_column(Text, primary_key=True)
    watermark: Mapped[datetime] = mapped_column(Timestamp)
    updated_at: Mapped[datetime] = mapped_column(Timestamp, server_default=func.now())


class ExtractionRow(Base):
    """Cited version facts a system extracted from an issue's text (``verdict.Extraction``).

    Facts don't depend on the Kafka version asked about, so one extraction answers every
    version, and model calls are only repeated when something they depend on changes: the
    text the system sees (``text_hash``), the system, or its configuration
    (``extractor_version``: model, prompt, chunking). Older rows stay as history.
    """

    __tablename__ = "extractions"
    __table_args__ = (UniqueConstraint("issue_id", "system", "extractor_version", "text_hash"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    issue_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("jira_issues.id", ondelete="CASCADE")
    )
    system: Mapped[str] = mapped_column(Text)
    extractor_version: Mapped[str] = mapped_column(Text)
    text_hash: Mapped[str] = mapped_column(Text)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    duration_ms: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(Timestamp, server_default=func.now())
