from dep_watch_agent.db import migrate


def test_migrate_is_idempotent(db):
    # The fixture already migrated; a second run applies nothing.
    assert migrate(db) == []
    names = [r[0] for r in db.execute("SELECT name FROM schema_migrations ORDER BY name")]
    assert names == ["001_jira_issues.sql"]


def test_expected_tables_exist(db):
    tables = {
        r[0]
        for r in db.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema()"
        )
    }
    assert {
        "schema_migrations",
        "jira_issues",
        "jira_issue_versions",
        "jira_issue_components",
        "jira_comments",
        "sync_state",
    } <= tables
