"""jira issues

Revision ID: 502cd7866ccf
Revises:
Create Date: 2026-09-27 16:51:11.950426
"""

from collections.abc import Sequence

from alembic import op

revision: str = "502cd7866ccf"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Raw JIRA issues as synced. Keyed by JIRA's numeric id because keys change when an issue
    # moves between projects.
    op.execute(
        """
        CREATE TABLE jira_issues (
            id          bigint PRIMARY KEY,
            key         text NOT NULL UNIQUE,
            project     text NOT NULL,
            summary     text NOT NULL,
            description text,
            issue_type  text,
            status      text,
            resolution  text,
            priority    text,
            labels      text[] NOT NULL DEFAULT '{}',
            created_at  timestamptz NOT NULL,
            updated_at  timestamptz NOT NULL,
            resolved_at timestamptz,
            raw         jsonb NOT NULL,
            synced_at   timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX jira_issues_project_updated_idx ON jira_issues (project, updated_at)")

    # Version names are stored exactly as JIRA has them. Parsing and comparison happen in
    # dep_watch_agent.versions, never in SQL.
    op.execute(
        """
        CREATE TABLE jira_issue_versions (
            issue_id bigint NOT NULL REFERENCES jira_issues (id) ON DELETE CASCADE,
            kind     text NOT NULL CHECK (kind IN ('affects', 'fix')),
            name     text NOT NULL,
            PRIMARY KEY (issue_id, kind, name)
        )
        """
    )
    op.execute("CREATE INDEX jira_issue_versions_name_idx ON jira_issue_versions (name, kind)")

    op.execute(
        """
        CREATE TABLE jira_issue_components (
            issue_id  bigint NOT NULL REFERENCES jira_issues (id) ON DELETE CASCADE,
            component text NOT NULL,
            PRIMARY KEY (issue_id, component)
        )
        """
    )
    op.execute(
        "CREATE INDEX jira_issue_components_component_idx ON jira_issue_components (component)"
    )

    op.execute(
        """
        CREATE TABLE jira_comments (
            id         bigint PRIMARY KEY,
            issue_id   bigint NOT NULL REFERENCES jira_issues (id) ON DELETE CASCADE,
            author     text,
            body       text NOT NULL,
            created_at timestamptz NOT NULL,
            updated_at timestamptz NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX jira_comments_issue_idx ON jira_comments (issue_id)")

    # Incremental sync watermark per source, e.g. "jira:KAFKA".
    op.execute(
        """
        CREATE TABLE sync_state (
            source     text PRIMARY KEY,
            watermark  timestamptz NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE sync_state")
    op.execute("DROP TABLE jira_comments")
    op.execute("DROP TABLE jira_issue_components")
    op.execute("DROP TABLE jira_issue_versions")
    op.execute("DROP TABLE jira_issues")
