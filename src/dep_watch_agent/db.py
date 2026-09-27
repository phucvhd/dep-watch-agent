"""Postgres connection and schema migrations.

Migrations are plain SQL files in ``dep_watch_agent/migrations``, applied in filename order.
Each one runs in its own transaction and is recorded in ``schema_migrations`` with a SHA-256
checksum of its contents.

Rules the runner enforces:

- Applied migrations are immutable. If a file's checksum no longer matches the recorded one,
  ``migrate`` fails instead of silently ignoring the edit. Change the schema by adding a new
  file.
- Every recorded migration must still exist as a file. A missing one usually means the code
  is older than the database (e.g. an old branch checked out against a newer DB).
- Only one process migrates at a time. A session-level advisory lock serializes concurrent
  runs; the second waits, then finds nothing left to apply.
"""

import hashlib
import os
from importlib import resources
from importlib.resources.abc import Traversable

import psycopg

DEFAULT_DATABASE_URL = "postgresql://dep_watch:dep_watch@localhost:5433/dep_watch"

# Arbitrary constant identifying the migration lock among this app's advisory locks.
MIGRATION_LOCK_ID = 7_361_204_518


class MigrationError(RuntimeError):
    """The database's migration history disagrees with the migration files."""


def database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def connect(url: str | None = None) -> psycopg.Connection:
    """Open an autocommit connection. Group writes with ``conn.transaction()``."""
    return psycopg.connect(url or database_url(), autocommit=True)


def migrate(conn: psycopg.Connection, migrations: Traversable | None = None) -> list[str]:
    """Apply pending migrations. Returns the names of the ones applied."""
    if not conn.autocommit:
        raise ValueError("migrate needs an autocommit connection; use db.connect()")
    files = _migration_files(migrations or resources.files("dep_watch_agent.migrations"))

    conn.execute("SELECT pg_advisory_lock(%s)", (MIGRATION_LOCK_ID,))
    try:
        applied = _load_history(conn, files)
        _verify_history(applied, files)

        newly_applied = []
        for name, sql in files.items():
            if name in applied:
                continue
            with conn.transaction():
                conn.execute(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (name, checksum) VALUES (%s, %s)",
                    (name, _checksum(sql)),
                )
            newly_applied.append(name)
        return newly_applied
    finally:
        conn.execute("SELECT pg_advisory_unlock(%s)", (MIGRATION_LOCK_ID,))


def _migration_files(directory: Traversable) -> dict[str, str]:
    files = sorted(
        (f for f in directory.iterdir() if f.name.endswith(".sql")), key=lambda f: f.name
    )
    return {f.name: f.read_text() for f in files}


def _checksum(sql: str) -> str:
    return hashlib.sha256(sql.encode()).hexdigest()


def _load_history(conn: psycopg.Connection, files: dict[str, str]) -> dict[str, str]:
    """Return ``{name: checksum}`` for applied migrations, creating the table if needed."""
    with conn.transaction():
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name       text PRIMARY KEY,
                checksum   text NOT NULL,
                applied_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        # Databases migrated before checksums existed: add the column and trust the current
        # files for rows that have none.
        conn.execute("ALTER TABLE schema_migrations ADD COLUMN IF NOT EXISTS checksum text")
        rows = conn.execute("SELECT name FROM schema_migrations WHERE checksum IS NULL").fetchall()
        for (name,) in rows:
            if name in files:
                conn.execute(
                    "UPDATE schema_migrations SET checksum = %s WHERE name = %s",
                    (_checksum(files[name]), name),
                )
        # Any row still NULL has no file; _verify_history reports it as missing.
        if len(rows) == sum(name in files for (name,) in rows):
            conn.execute("ALTER TABLE schema_migrations ALTER COLUMN checksum SET NOT NULL")
        return dict(conn.execute("SELECT name, checksum FROM schema_migrations").fetchall())


def _verify_history(applied: dict[str, str], files: dict[str, str]) -> None:
    missing = sorted(set(applied) - set(files))
    if missing:
        raise MigrationError(
            f"database has migrations with no matching file: {', '.join(missing)}. "
            "Is the code older than the database?"
        )
    changed = sorted(
        name for name, checksum in applied.items() if _checksum(files[name]) != checksum
    )
    if changed:
        raise MigrationError(
            f"applied migrations were edited: {', '.join(changed)}. "
            "Revert the edit and add a new migration instead."
        )
