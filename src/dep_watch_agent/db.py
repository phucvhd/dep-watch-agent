"""Postgres connection and schema migrations.

Migrations are plain SQL files in ``dep_watch_agent/migrations``, applied in filename order.
Each one runs in its own transaction and is recorded in ``schema_migrations``.
"""

import os
from importlib import resources

import psycopg

DEFAULT_DATABASE_URL = "postgresql://dep_watch:dep_watch@localhost:5433/dep_watch"


def database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def connect(url: str | None = None) -> psycopg.Connection:
    """Open an autocommit connection. Group writes with ``conn.transaction()``."""
    return psycopg.connect(url or database_url(), autocommit=True)


def migrate(conn: psycopg.Connection) -> list[str]:
    """Apply pending migrations. Returns the names of the ones applied."""
    with conn.transaction():
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name       text PRIMARY KEY,
                applied_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        applied = {row[0] for row in conn.execute("SELECT name FROM schema_migrations")}

    files = sorted(
        (f for f in resources.files("dep_watch_agent.migrations").iterdir()),
        key=lambda f: f.name,
    )
    newly_applied = []
    for f in files:
        if not f.name.endswith(".sql") or f.name in applied:
            continue
        with conn.transaction():
            conn.execute(f.read_text())
            conn.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (f.name,))
        newly_applied.append(f.name)
    return newly_applied
