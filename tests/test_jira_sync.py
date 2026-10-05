from datetime import UTC, date, datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from dep_watch_agent.jira.models import parse_issue
from dep_watch_agent.jira.store import load_watermark, upsert_issue, upsert_versions
from dep_watch_agent.jira.sync import FIELDS, build_jql, sync_project
from dep_watch_agent.orm import (
    JiraCommentRow,
    JiraIssueComponentRow,
    JiraIssueRow,
    JiraIssueVersionRow,
    JiraVersionRow,
)
from tests.jira_factory import raw_comment, raw_issue


class FakeClient:
    def __init__(
        self,
        issues: list[dict],
        comments: dict[str, list[dict]] | None = None,
        versions: list[dict] | None = None,
    ):
        self.issues = issues
        self.extra_comments = comments or {}
        self.versions = versions or []
        self.queries: list[str] = []
        self.comment_requests: list[str] = []

    def project_versions(self, project):
        return self.versions

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


def count(session, model) -> int:
    return session.scalar(select(func.count()).select_from(model))


def test_first_sync_is_full_and_saves_start_time(db, schema):
    client = FakeClient([raw_issue(1, "KAFKA-1"), raw_issue(2, "KAFKA-2")])

    result = sync_project(db, client, "KAFKA", now=clock(T0))

    assert result.issues_synced == 2
    assert result.since is None
    assert "updated >=" not in client.queries[0]
    # Committed, not just visible in this session.
    with schema.session() as other:
        assert load_watermark(other, "jira:KAFKA") == T0
        assert count(other, JiraIssueRow) == 2


def test_second_sync_is_incremental_with_overlap(db):
    sync_project(db, FakeClient([raw_issue(1, "KAFKA-1")]), "KAFKA", now=clock(T0))

    client = FakeClient([])
    result = sync_project(db, client, "KAFKA", now=clock(T1), overlap=timedelta(minutes=10))

    assert result.since == T0 - timedelta(minutes=10)
    assert 'updated >= "2026-09-01 11:50"' in client.queries[0]
    assert load_watermark(db, "jira:KAFKA") == T1


def test_full_flag_ignores_watermark(db):
    sync_project(db, FakeClient([]), "KAFKA", now=clock(T0))
    client = FakeClient([])
    sync_project(db, client, "KAFKA", full=True, now=clock(T1))
    assert "updated >=" not in client.queries[0]


def test_watermark_not_saved_if_sync_fails(db, schema):
    class Boom(Exception):
        pass

    class FailingClient(FakeClient):
        def search(self, jql, fields):
            yield raw_issue(1, "KAFKA-1")
            raise Boom

    with pytest.raises(Boom):
        sync_project(db, FailingClient([]), "KAFKA", now=clock(T0))

    with schema.session() as other:
        assert load_watermark(other, "jira:KAFKA") is None
        # Issues synced before the failure are committed; the rerun upserts them again.
        assert count(other, JiraIssueRow) == 1


def test_watermarks_are_per_project(db):
    sync_project(db, FakeClient([]), "KAFKA", now=clock(T0))
    assert load_watermark(db, "jira:ZOOKEEPER") is None


def test_fetches_truncated_comments(db):
    full = [raw_comment(n, f"comment {n}") for n in range(1, 6)]
    issue = raw_issue(1, "KAFKA-1", comments=full[:2], comment_total=5)
    client = FakeClient([issue], comments={"KAFKA-1": full})

    sync_project(db, client, "KAFKA", now=clock(T0))

    assert client.comment_requests == ["KAFKA-1"]
    assert count(db, JiraCommentRow) == 5


def test_does_not_fetch_complete_comments(db):
    issue = raw_issue(1, "KAFKA-1", comments=[raw_comment(1, "only")])
    client = FakeClient([issue])
    sync_project(db, client, "KAFKA", now=clock(T0))
    assert client.comment_requests == []


def test_progress_callback(db):
    seen = []
    client = FakeClient([raw_issue(n, f"KAFKA-{n}") for n in range(1, 4)])
    sync_project(db, client, "KAFKA", now=clock(T0), on_issue=seen.append)
    assert seen == [1, 2, 3]


# --- store ------------------------------------------------------------------------


def versions_of(session, issue_id: int) -> list[tuple[str, str]]:
    return [
        tuple(r)
        for r in session.execute(
            select(JiraIssueVersionRow.kind, JiraIssueVersionRow.name)
            .where(JiraIssueVersionRow.issue_id == issue_id)
            .order_by(JiraIssueVersionRow.kind, JiraIssueVersionRow.name)
        )
    ]


def test_upsert_stores_everything(db, load_fixture):
    issue = parse_issue(load_fixture("jira/issue_bug_backported.json"))
    upsert_issue(db, issue)

    row = db.execute(
        select(
            JiraIssueRow.key,
            JiraIssueRow.project,
            JiraIssueRow.issue_type,
            JiraIssueRow.resolution,
            JiraIssueRow.raw["key"].astext,
        ).where(JiraIssueRow.id == issue.id)
    ).one()
    assert tuple(row) == ("KAFKA-16025", "KAFKA", "Bug", "Fixed", "KAFKA-16025")
    assert versions_of(db, issue.id) == [("affects", "3.4.0"), ("fix", "3.7.1"), ("fix", "3.8.0")]
    assert db.scalars(select(JiraIssueComponentRow.component)).all() == ["streams"]
    assert count(db, JiraCommentRow) == 3


def test_relationships_load_children(db, load_fixture):
    issue = parse_issue(load_fixture("jira/issue_bug_backported.json"))
    upsert_issue(db, issue)
    db.commit()

    row = db.get(JiraIssueRow, issue.id)
    assert sorted((v.kind, v.name) for v in row.versions) == [
        ("affects", "3.4.0"),
        ("fix", "3.7.1"),
        ("fix", "3.8.0"),
    ]
    assert [c.component for c in row.components] == ["streams"]
    assert [c.created_at for c in row.comments] == sorted(c.created_at for c in row.comments)
    assert row.comments[0].issue is row


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

    assert db.scalars(select(JiraIssueRow.summary)).all() == ["Renamed"]
    assert versions_of(db, 1) == [("affects", "3.6.0"), ("fix", "3.7.1"), ("fix", "3.8.0")]
    assert db.scalars(select(JiraIssueComponentRow.component)).all() == ["streams"]
    assert [tuple(r) for r in db.execute(select(JiraCommentRow.id, JiraCommentRow.body))] == [
        (11, "b edited")
    ]


def test_upsert_without_children(db):
    upsert_issue(db, parse_issue(raw_issue(1, "KAFKA-1")))
    assert count(db, JiraIssueRow) == 1
    assert count(db, JiraIssueVersionRow) == 0


def test_upsert_follows_key_change(db):
    # Moving an issue between projects changes its key but not its id.
    upsert_issue(db, parse_issue(raw_issue(1, "OLD-5")))
    upsert_issue(db, parse_issue(raw_issue(1, "KAFKA-99")))
    rows = db.execute(select(JiraIssueRow.id, JiraIssueRow.key, JiraIssueRow.project)).all()
    assert [tuple(r) for r in rows] == [(1, "KAFKA-99", "KAFKA")]


def test_resync_is_idempotent(db):
    issues = [raw_issue(1, "KAFKA-1", fix=["3.7.0"]), raw_issue(2, "KAFKA-2")]
    sync_project(db, FakeClient(issues), "KAFKA", now=clock(T0))
    sync_project(db, FakeClient(issues), "KAFKA", full=True, now=clock(T1))
    assert count(db, JiraIssueRow) == 2
    assert count(db, JiraIssueVersionRow) == 1


def raw_version(id: int, name: str, released: bool = True, date: str | None = "2024-01-01"):
    v = {"id": str(id), "name": name, "released": released, "archived": False}
    if date:
        v["releaseDate"] = date
    return v


def test_sync_stores_project_versions(db):
    client = FakeClient(
        [], versions=[raw_version(1, "3.7.0"), raw_version(2, "4.5.0", False, None)]
    )
    result = sync_project(db, client, "KAFKA", now=clock(T0))

    assert result.versions_synced == 2
    rows = db.execute(
        select(JiraVersionRow.name, JiraVersionRow.released, JiraVersionRow.release_date).order_by(
            JiraVersionRow.name
        )
    ).all()
    assert [tuple(r) for r in rows] == [
        ("3.7.0", True, date(2024, 1, 1)),
        ("4.5.0", False, None),
    ]


def test_upsert_versions_updates_release_state(db):
    upsert_versions(db, "KAFKA", [raw_version(1, "4.5.0", released=False, date=None)])
    upsert_versions(db, "KAFKA", [raw_version(1, "4.5.0", released=True, date="2026-10-01")])
    row = db.execute(select(JiraVersionRow.released, JiraVersionRow.release_date)).one()
    assert tuple(row) == (True, date(2026, 10, 1))
    assert upsert_versions(db, "KAFKA", []) == 0
