import hashlib
import threading

import psycopg
import pytest

from dep_watch_agent.db import MIGRATION_LOCK_ID, MigrationError, migrate
from tests.conftest import connect_to_schema, db_url_for_tests


def write(directory, name: str, sql: str) -> None:
    (directory / name).write_text(sql)


def tables(conn) -> set[str]:
    return {
        r[0]
        for r in conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema()"
        )
    }


def history(conn) -> list[str]:
    return [r[0] for r in conn.execute("SELECT name FROM schema_migrations ORDER BY name")]


def current_schema(conn) -> str:
    return conn.execute("SELECT current_schema()").fetchone()[0]


# --- packaged migrations -----------------------------------------------------------


def test_migrate_is_idempotent(db):
    # The fixture already migrated; a second run applies nothing.
    assert migrate(db) == []
    assert history(db) == ["001_jira_issues.sql"]


def test_expected_tables_exist(db):
    assert {
        "schema_migrations",
        "jira_issues",
        "jira_issue_versions",
        "jira_issue_components",
        "jira_comments",
        "sync_state",
    } <= tables(db)


def test_records_sha256_checksum(empty_db, tmp_path):
    write(tmp_path, "001_a.sql", "CREATE TABLE a (id int);")
    migrate(empty_db, tmp_path)
    (checksum,) = empty_db.execute("SELECT checksum FROM schema_migrations").fetchone()
    assert checksum == hashlib.sha256(b"CREATE TABLE a (id int);").hexdigest()


# --- ordering and failures ------------------------------------------------------


def test_applies_in_filename_order(empty_db, tmp_path):
    write(tmp_path, "002_b.sql", "ALTER TABLE a ADD COLUMN b int;")
    write(tmp_path, "001_a.sql", "CREATE TABLE a (id int);")
    write(tmp_path, "README.md", "not a migration")

    assert migrate(empty_db, tmp_path) == ["001_a.sql", "002_b.sql"]
    assert history(empty_db) == ["001_a.sql", "002_b.sql"]


def test_applies_only_new_migrations(empty_db, tmp_path):
    write(tmp_path, "001_a.sql", "CREATE TABLE a (id int);")
    migrate(empty_db, tmp_path)
    write(tmp_path, "002_b.sql", "CREATE TABLE b (id int);")
    assert migrate(empty_db, tmp_path) == ["002_b.sql"]


def test_failed_migration_rolls_back_and_is_not_recorded(empty_db, tmp_path):
    write(tmp_path, "001_a.sql", "CREATE TABLE a (id int);")
    write(tmp_path, "002_bad.sql", "CREATE TABLE half (id int); SELECT * FROM nope;")

    with pytest.raises(psycopg.errors.UndefinedTable):
        migrate(empty_db, tmp_path)

    assert history(empty_db) == ["001_a.sql"]
    assert "half" not in tables(empty_db)


# --- immutability checks -----------------------------------------------------------


def test_edited_migration_is_rejected(empty_db, tmp_path):
    write(tmp_path, "001_a.sql", "CREATE TABLE a (id int);")
    migrate(empty_db, tmp_path)

    write(tmp_path, "001_a.sql", "CREATE TABLE a (id int, extra text);")
    write(tmp_path, "002_b.sql", "CREATE TABLE b (id int);")
    with pytest.raises(MigrationError, match="001_a.sql"):
        migrate(empty_db, tmp_path)

    # Nothing further is applied once the history is inconsistent.
    assert history(empty_db) == ["001_a.sql"]
    assert "b" not in tables(empty_db)


def test_whitespace_edit_is_still_an_edit(empty_db, tmp_path):
    write(tmp_path, "001_a.sql", "CREATE TABLE a (id int);")
    migrate(empty_db, tmp_path)
    write(tmp_path, "001_a.sql", "CREATE TABLE a (id int);\n")
    with pytest.raises(MigrationError, match="edited"):
        migrate(empty_db, tmp_path)


def test_missing_migration_file_is_rejected(empty_db, tmp_path):
    write(tmp_path, "001_a.sql", "CREATE TABLE a (id int);")
    write(tmp_path, "002_b.sql", "CREATE TABLE b (id int);")
    migrate(empty_db, tmp_path)

    (tmp_path / "002_b.sql").unlink()
    with pytest.raises(MigrationError, match="002_b.sql"):
        migrate(empty_db, tmp_path)


# --- databases migrated before checksums existed --------------------------------


def create_legacy_history(conn, *names: str) -> None:
    conn.execute(
        """
        CREATE TABLE schema_migrations (
            name       text PRIMARY KEY,
            applied_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    for name in names:
        conn.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (name,))


def test_legacy_history_is_backfilled(empty_db, tmp_path):
    write(tmp_path, "001_a.sql", "CREATE TABLE a (id int);")
    create_legacy_history(empty_db, "001_a.sql")

    assert migrate(empty_db, tmp_path) == []

    (checksum,) = empty_db.execute("SELECT checksum FROM schema_migrations").fetchone()
    assert checksum == hashlib.sha256(b"CREATE TABLE a (id int);").hexdigest()
    (nullable,) = empty_db.execute(
        """
        SELECT is_nullable FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'schema_migrations' AND column_name = 'checksum'
        """
    ).fetchone()
    assert nullable == "NO"

    # Once backfilled, edits are caught like any other.
    write(tmp_path, "001_a.sql", "CREATE TABLE a (id bigint);")
    with pytest.raises(MigrationError, match="edited"):
        migrate(empty_db, tmp_path)


def test_legacy_history_with_missing_file_reports_it(empty_db, tmp_path):
    write(tmp_path, "001_a.sql", "CREATE TABLE a (id int);")
    create_legacy_history(empty_db, "001_a.sql", "002_gone.sql")

    with pytest.raises(MigrationError, match="002_gone.sql"):
        migrate(empty_db, tmp_path)


# --- locking ---------------------------------------------------------------------


def test_concurrent_migrate_waits_for_lock(empty_db, tmp_path):
    write(tmp_path, "001_a.sql", "CREATE TABLE a (id int);")
    holder = connect_to_schema(current_schema(empty_db))
    holder.execute("SELECT pg_advisory_lock(%s)", (MIGRATION_LOCK_ID,))

    result: list[list[str]] = []
    worker = threading.Thread(target=lambda: result.append(migrate(empty_db, tmp_path)))
    try:
        worker.start()
        worker.join(timeout=0.5)
        assert worker.is_alive(), "migrate ran while another session held the lock"
        assert result == []
    finally:
        holder.execute("SELECT pg_advisory_unlock(%s)", (MIGRATION_LOCK_ID,))
        holder.close()

    worker.join(timeout=5)
    assert result == [["001_a.sql"]]


def test_second_runner_applies_nothing(empty_db, tmp_path):
    write(tmp_path, "001_a.sql", "CREATE TABLE a (id int);")
    other = connect_to_schema(current_schema(empty_db))
    try:
        assert migrate(empty_db, tmp_path) == ["001_a.sql"]
        assert migrate(other, tmp_path) == []
    finally:
        other.close()


def test_lock_released_after_failure(empty_db, tmp_path):
    write(tmp_path, "001_bad.sql", "SELECT * FROM nope;")
    with pytest.raises(psycopg.errors.UndefinedTable):
        migrate(empty_db, tmp_path)

    probe = psycopg.connect(db_url_for_tests(), autocommit=True)
    try:
        (acquired,) = probe.execute(
            "SELECT pg_try_advisory_lock(%s)", (MIGRATION_LOCK_ID,)
        ).fetchone()
        assert acquired
        probe.execute("SELECT pg_advisory_unlock(%s)", (MIGRATION_LOCK_ID,))
    finally:
        probe.close()


def test_requires_autocommit_connection(tmp_path):
    try:
        conn = psycopg.connect(db_url_for_tests())
    except psycopg.OperationalError:
        pytest.skip("Postgres not reachable")
    try:
        with pytest.raises(ValueError, match="autocommit"):
            migrate(conn, tmp_path)
    finally:
        conn.close()
