from datetime import UTC, datetime

from dep_watch_agent.jira.models import comments_truncated, parse_issue, parse_timestamp
from tests.jira_factory import raw_comment, raw_issue


def test_parse_real_issue(load_fixture):
    raw = load_fixture("jira/issue_bug_backported.json")
    issue = parse_issue(raw)

    assert issue.key == "KAFKA-16025"
    assert issue.id == int(raw["id"])
    assert issue.project == "KAFKA"
    assert issue.issue_type == "Bug"
    assert issue.resolution == "Fixed"
    assert issue.affects_versions == ["3.4.0"]
    assert issue.fix_versions == ["3.7.1", "3.8.0"]
    assert issue.components == ["streams"]
    assert len(issue.comments) == 3
    assert all(c.body for c in issue.comments)
    assert issue.created_at.tzinfo is not None
    assert issue.resolved_at is not None
    assert issue.raw is raw


def test_version_names_kept_verbatim():
    # No parsing here: "0.10.2.1" and "3.10.0" go to the database exactly as JIRA has them.
    issue = parse_issue(raw_issue(1, "KAFKA-1", affects=["3.10.0", "0.10.2.1"], fix=["3.9.0"]))
    assert issue.affects_versions == ["0.10.2.1", "3.10.0"]
    assert issue.fix_versions == ["3.9.0"]


def test_duplicate_names_collapsed():
    issue = parse_issue(raw_issue(1, "KAFKA-1", components=["streams", "streams"]))
    assert issue.components == ["streams"]


def test_missing_optional_fields():
    raw = raw_issue(1, "KAFKA-1", resolution=None, priority=None, resolutiondate=None)
    raw["fields"]["description"] = None
    del raw["fields"]["comment"]
    issue = parse_issue(raw)
    assert issue.resolution is None
    assert issue.priority is None
    assert issue.resolved_at is None
    assert issue.description is None
    assert issue.comments == []


def test_comment_without_author():
    comment = raw_comment(10, "hello")
    del comment["author"]
    issue = parse_issue(raw_issue(1, "KAFKA-1", comments=[comment]))
    assert issue.comments[0].author is None
    assert issue.comments[0].body == "hello"


def test_parse_timestamp():
    assert parse_timestamp("2026-09-27T16:38:55.000+0000") == datetime(
        2026, 9, 27, 16, 38, 55, tzinfo=UTC
    )


def test_comments_truncated():
    assert not comments_truncated(raw_issue(1, "KAFKA-1", comments=[raw_comment(1, "a")]))
    assert comments_truncated(
        raw_issue(1, "KAFKA-1", comments=[raw_comment(1, "a")], comment_total=5)
    )
