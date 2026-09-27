from datetime import UTC, datetime, timedelta, timezone

import pytest

from dep_watch_agent.jira.models import parse_issue
from dep_watch_agent.jira.store import load_watermark, upsert_issue
from dep_watch_agent.jira.sync import FIELDS, build_jql, sync_project
from tests.jira_factory import raw_comment, raw_issue


class FakeClient:
    def __init__(self, issues: list[dict], comments: dict[str, list[dict]] | None = None):
        self.issues = issues
        self.extra_comments = comments or {}
        self.queries: list[str] = []
        self.comment_requests: list[str] = []

    def search(self, jql, fields):
        assert fields == FIELDS
        self.queries.append(jql)
        yield from self.issues

    def comments(self, key):
        self.comment_requests.append(key)
        return self.extra_comments[key]


def clock(*times: datetime):
    it = iter(times)
    return lambda: next(it)


T0 = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
T1 = datetime(2026, 9, 2, 8, 30, tzinfo=UTC)


# --- JQL ---------------------------------------------------------------------


def test_build_jql_full():
    assert build_jql("KAFKA", None) == 'project = "KAFKA" ORDER BY created ASC, key ASC'


def test_build_jql_incremental_uses_utc_minutes():
    since = datetime(2026, 9, 1, 14, 5, 59, tzinfo=timezone(timedelta(hours=2)))
    assert build_jql("KAFKA", since) == (
        'project = "KAFKA" AND updated >= "2026-09-01 12:05" ORDER BY created ASC, key ASC'
    )


# --- sync against Postgres ------------------------------------------------------


def count(db, table: str) -> int:
    return db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def test_first_sync_is_full_and_saves_start_time(db):
    client = FakeClient([raw_issue(1, "KAFKA-1"), raw_issue(2, "KAFKA-2")])

    result = sync_project(db, client, now=clock(T0))

    assert result.issues_synced == 2
    assert result.since is None
    assert "updated >=" not in client.queries[0]
    assert load_watermark(db, "jira:KAFKA") == T0
    assert count(db, "jira_issues") == 2


def test_second_sync_is_incremental_with_overlap(db):
    sync_project(db, FakeClient([raw_issue(1, "KAFKA-1")]), now=clock(T0))

    client = FakeClient([])
    result = sync_project(db, client, now=clock(T1), overlap=timedelta(minutes=10))

    assert result.since == T0 - timedelta(minutes=10)
    assert 'updated >= "2026-09-01 11:50"' in client.queries[0]
    assert load_watermark(db, "jira:KAFKA") == T1


def test_full_flag_ignores_watermark(db):
    sync_project(db, FakeClient([]), now=clock(T0))
    client = FakeClient([])
    sync_project(db, client, full=True, now=clock(T1))
    assert "updated >=" not in client.queries[0]


def test_watermark_not_saved_if_sync_fails(db):
    class Boom(Exception):
        pass

    class FailingClient(FakeClient):
        def search(self, jql, fields):
            yield raw_issue(1, "KAFKA-1")
            raise Boom

    with pytest.raises(Boom):
        sync_project(db, FailingClient([]), now=clock(T0))

    assert load_watermark(db, "jira:KAFKA") is None
    # Issues synced before the failure are kept; the rerun upserts them again.
    assert count(db, "jira_issues") == 1


def test_watermarks_are_per_project(db):
    sync_project(db, FakeClient([]), "KAFKA", now=clock(T0))
    assert load_watermark(db, "jira:ZOOKEEPER") is None


def test_fetches_truncated_comments(db):
    full = [raw_comment(n, f"comment {n}") for n in range(1, 6)]
    issue = raw_issue(1, "KAFKA-1", comments=full[:2], comment_total=5)
    client = FakeClient([issue], comments={"KAFKA-1": full})

    sync_project(db, client, now=clock(T0))

    assert client.comment_requests == ["KAFKA-1"]
    assert count(db, "jira_comments") == 5


def test_does_not_fetch_complete_comments(db):
    issue = raw_issue(1, "KAFKA-1", comments=[raw_comment(1, "only")])
    client = FakeClient([issue])
    sync_project(db, client, now=clock(T0))
    assert client.comment_requests == []


def test_progress_callback(db):
    seen = []
    client = FakeClient([raw_issue(n, f"KAFKA-{n}") for n in range(1, 4)])
    sync_project(db, client, now=clock(T0), on_issue=seen.append)
    assert seen == [1, 2, 3]


# --- store ------------------------------------------------------------------------


def test_upsert_stores_everything(db, load_fixture):
    issue = parse_issue(load_fixture("jira/issue_bug_backported.json"))
    upsert_issue(db, issue)

    row = db.execute(
        "SELECT key, project, issue_type, resolution, raw->>'key' FROM jira_issues WHERE id = %s",
        (issue.id,),
    ).fetchone()
    assert row == ("KAFKA-16025", "KAFKA", "Bug", "Fixed", "KAFKA-16025")

    versions = db.execute(
        "SELECT kind, name FROM jira_issue_versions WHERE issue_id = %s ORDER BY kind, name",
        (issue.id,),
    ).fetchall()
    assert versions == [("affects", "3.4.0"), ("fix", "3.7.1"), ("fix", "3.8.0")]

    components = db.execute(
        "SELECT component FROM jira_issue_components WHERE issue_id = %s", (issue.id,)
    ).fetchall()
    assert components == [("streams",)]
    assert count(db, "jira_comments") == 3


def test_upsert_replaces_children(db):
    upsert_issue(
        db,
        parse_issue(
            raw_issue(
                1,
                "KAFKA-1",
                affects=["3.6.0"],
                fix=["3.7.0"],
                components=["streams", "clients"],
                comments=[raw_comment(10, "a"), raw_comment(11, "b")],
            )
        ),
    )
    upsert_issue(
        db,
        parse_issue(
            raw_issue(
                1,
                "KAFKA-1",
                summary="Renamed",
                affects=["3.6.0"],
                fix=["3.7.1", "3.8.0"],
                components=["streams"],
                comments=[raw_comment(11, "b edited")],
            )
        ),
    )

    assert db.execute("SELECT summary FROM jira_issues").fetchall() == [("Renamed",)]
    assert db.execute(
        "SELECT kind, name FROM jira_issue_versions ORDER BY kind, name"
    ).fetchall() == [("affects", "3.6.0"), ("fix", "3.7.1"), ("fix", "3.8.0")]
    assert db.execute("SELECT component FROM jira_issue_components").fetchall() == [("streams",)]
    assert db.execute("SELECT id, body FROM jira_comments").fetchall() == [(11, "b edited")]


def test_upsert_follows_key_change(db):
    # Moving an issue between projects changes its key but not its id.
    upsert_issue(db, parse_issue(raw_issue(1, "OLD-5")))
    upsert_issue(db, parse_issue(raw_issue(1, "KAFKA-99")))
    assert db.execute("SELECT id, key, project FROM jira_issues").fetchall() == [
        (1, "KAFKA-99", "KAFKA")
    ]


def test_resync_is_idempotent(db):
    issues = [raw_issue(1, "KAFKA-1", fix=["3.7.0"]), raw_issue(2, "KAFKA-2")]
    sync_project(db, FakeClient(issues), now=clock(T0))
    sync_project(db, FakeClient(issues), full=True, now=clock(T1))
    assert count(db, "jira_issues") == 2
    assert count(db, "jira_issue_versions") == 1
