import subprocess
import sys
import threading

import pytest
from alembic import command
from alembic.script import ScriptDirectory

from dep_watch_agent.db import (
    MIGRATION_LOCK_ID,
    alembic_config,
    current_revision,
    migrate,
    sqlalchemy_url,
)

APP_TABLES = {
    "jira_issues",
    "jira_issue_versions",
    "jira_issue_components",
    "jira_comments",
    "sync_state",
}


def script() -> ScriptDirectory:
    return ScriptDirectory.from_config(alembic_config())


def tables(conn) -> set[str]:
    return {
        r[0]
        for r in conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema()"
        )
    }


# --- revision graph -----------------------------------------------------------------


def test_single_head():
    # Two branches that each add a revision produce two heads; merge them before landing.
    assert len(script().get_heads()) == 1


# --- upgrade / downgrade ------------------------------------------------------------


def test_upgrade_to_head(db, schema):
    assert current_revision(schema.url, schema=schema.name) == script().get_current_head()
    assert APP_TABLES | {"alembic_version"} <= tables(db)


def test_upgrade_is_idempotent(db, schema):
    migrate(schema.url, schema=schema.name)
    assert current_revision(schema.url, schema=schema.name) == script().get_current_head()


def test_empty_schema_has_no_revision(schema):
    assert current_revision(schema.url, schema=schema.name) is None


def test_migrations_stay_in_target_schema(db, schema):
    # Nothing should leak into public when a schema is given.
    public = db.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = ANY(%s)",
        (list(APP_TABLES),),
    ).fetchone()[0]
    in_schema = db.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = %s AND table_name = ANY(%s)",
        (schema.name, list(APP_TABLES)),
    ).fetchone()[0]
    assert in_schema == len(APP_TABLES)
    # The dev DB may have its own tables in public; the point is we didn't create them here.
    assert public in (0, len(APP_TABLES))


def test_downgrade_to_base_removes_everything(db, schema):
    command.downgrade(alembic_config(schema.url, schema=schema.name), "base")
    assert tables(db) == {"alembic_version"}
    assert current_revision(schema.url, schema=schema.name) is None


def test_every_revision_round_trips(schema):
    """Stairway test: each revision upgrades, downgrades and upgrades again cleanly."""
    config = alembic_config(schema.url, schema=schema.name)
    revisions = list(reversed(list(script().walk_revisions())))
    for rev in revisions:
        command.upgrade(config, rev.revision)
        command.downgrade(config, rev.down_revision or "base")
        command.upgrade(config, rev.revision)
    assert current_revision(schema.url, schema=schema.name) == script().get_current_head()


# --- locking ---------------------------------------------------------------------


def test_migrate_waits_for_lock(schema):
    holder = schema.connect()
    holder.execute("SELECT pg_advisory_lock(%s)", (MIGRATION_LOCK_ID,))

    errors: list[BaseException] = []

    def run():
        try:
            migrate(schema.url, schema=schema.name)
        except BaseException as exc:  # noqa: BLE001 - surface to the main thread
            errors.append(exc)

    worker = threading.Thread(target=run)
    try:
        worker.start()
        worker.join(timeout=0.5)
        assert worker.is_alive(), "migrate ran while another session held the lock"
        assert current_revision(schema.url, schema=schema.name) is None
    finally:
        holder.execute("SELECT pg_advisory_unlock(%s)", (MIGRATION_LOCK_ID,))
        holder.close()

    worker.join(timeout=10)
    assert errors == []
    assert current_revision(schema.url, schema=schema.name) == script().get_current_head()


def test_concurrent_migrations_do_not_conflict(schema):
    # Separate processes, as in real deployments. Alembic keeps its migration context in
    # process-wide globals, so it cannot run several upgrades in threads of one process.
    code = (
        "import sys; from dep_watch_agent.db import migrate; "
        "migrate(sys.argv[1], schema=sys.argv[2])"
    )
    procs = [
        subprocess.Popen(
            [sys.executable, "-c", code, schema.url, schema.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(4)
    ]
    results = [p.communicate(timeout=60) for p in procs]

    assert [p.returncode for p in procs] == [0] * 4, [err for _, err in results]
    assert current_revision(schema.url, schema=schema.name) == script().get_current_head()


# --- URLs -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("postgresql://u:p@h:5433/d", "postgresql+psycopg://u:p@h:5433/d"),
        ("postgres://u:p@h/d", "postgresql+psycopg://u:p@h/d"),
        ("postgresql+psycopg://u:p@h/d", "postgresql+psycopg://u:p@h/d"),
    ],
)
def test_sqlalchemy_url(url, expected):
    assert sqlalchemy_url(url) == expected
