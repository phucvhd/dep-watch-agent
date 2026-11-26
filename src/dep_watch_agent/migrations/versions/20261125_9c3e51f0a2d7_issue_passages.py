"""issue passages

Revision ID: 9c3e51f0a2d7
Revises: 41a29d4127bb
Create Date: 2026-11-25 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from dep_watch_agent.orm import Vector

revision: str = "9c3e51f0a2d7"
down_revision: str | Sequence[str] | None = "41a29d4127bb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # pgvector lives in public, shared by every schema; it is left in place on downgrade.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public")
    op.create_table(
        "issue_passages",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("issue_key", sa.Text(), nullable=False),
        sa.Column("embed_model", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("field", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("text_hash", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issue_key", "embed_model", "position"),
    )
    op.create_index(
        "ix_issue_passages_issue_key_embed_model",
        "issue_passages",
        ["issue_key", "embed_model"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_issue_passages_issue_key_embed_model", table_name="issue_passages")
    op.drop_table("issue_passages")
