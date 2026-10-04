from datetime import UTC, datetime

import pytest

from dep_watch_agent.jira.models import parse_issue
from dep_watch_agent.jira.store import upsert_issue
from dep_watch_agent.scan import scan_version
from dep_watch_agent.verdict import Evidence, Extraction, IssueText
from tests.jira_factory import raw_issue


class PhraseExtractor:
    """Cites a fact for each known phrase; records the issues it was asked about."""

    PHRASES = {"Regression in 3.9.0": ("3.9.0", "introduced")}

    def __init__(self, fail_on: str | None = None):
        self.seen: list[str] = []
        self.fail_on = fail_on

    def extract(self, issue: IssueText) -> Extraction:
        self.seen.append(issue.summary)
        if issue.summary == self.fail_on:
            raise ConnectionError("model server down")
        return Extraction(
            [
                Evidence(version, kind, text)
                for text in issue.fields()
                for phrase, (version, kind) in self.PHRASES.items()
                if phrase in text
            ]
        )


def issue(id, summary, *, updated, **kwargs):
    return raw_issue(id, f"KAFKA-{id}", summary=summary, updated=updated, **kwargs)


ISSUES = [
    # Fixed in 3.9.0's past: the fix versions settle it, no model call.
    issue(1, "old bug", updated="2026-09-01T00:00:00.000+0000", fix=["3.8.0"]),
    issue(
        2,
        "new regression",
        updated="2026-09-20T00:00:00.000+0000",
        description="Regression in 3.9.0: the consumer hangs.",
        fix=["4.2.0"],
    ),
    issue(
        3,
        "vague",
        updated="2026-09-25T00:00:00.000+0000",
        description="The broker logs a warning.",
        resolution=None,
    ),
    issue(4, "duplicate", updated="2026-09-26T00:00:00.000+0000", resolution={"name": "Duplicate"}),
    issue(
        5, "improvement", updated="2026-09-27T00:00:00.000+0000", issuetype={"name": "Improvement"}
    ),
    issue(6, "won't fix", updated="2026-09-02T00:00:00.000+0000", resolution={"name": "Won't Fix"}),
]


@pytest.fixture
def session(db):
    for raw in ISSUES:
        upsert_issue(db, parse_issue(raw))
    db.commit()
    return db


def test_scan_answers_every_candidate_in_report_order(session):
    extractor = PhraseExtractor()
    progress = []
    result = scan_version(session, "3.9.1", "phrases", extractor, on_issue=progress.append)

    answers = [(i.issue_key, i.answer, i.decided_by) for i in result.items]
    assert answers == [
        ("KAFKA-2", "affected", "phrases"),
        ("KAFKA-3", "insufficient_information", "phrases"),
        ("KAFKA-6", "insufficient_information", "phrases"),  # won't fix: the bug is real
        ("KAFKA-1", "not_affected", "fix_versions"),
    ]
    assert "old bug" not in extractor.seen  # decided by code, no model call
    assert result.candidates_total == 4  # no duplicate, no improvement
    assert result.counts == {"affected": 1, "not_affected": 1, "insufficient_information": 2}
    assert progress == [1, 2, 3, 4]

    regression = result.items[0]
    assert regression.url == "https://issues.apache.org/jira/browse/KAFKA-2"
    assert regression.evidence == [
        Evidence("3.9.0", "introduced", "Regression in 3.9.0: the consumer hangs.")
    ]
    assert regression.fix_versions == ["4.2.0"]


def test_scan_since_and_limit(session):
    since = datetime(2026, 9, 10, tzinfo=UTC)
    result = scan_version(session, "3.9.1", "phrases", PhraseExtractor(), since=since)
    assert {i.issue_key for i in result.items} == {"KAFKA-2", "KAFKA-3"}

    result = scan_version(session, "3.9.1", "phrases", PhraseExtractor(), limit=1)
    assert [i.issue_key for i in result.items] == ["KAFKA-3"]  # the newest
    assert result.candidates_total == 4


def test_a_failed_issue_is_reported_not_dropped(session):
    result = scan_version(session, "3.9.1", "phrases", PhraseExtractor(fail_on="vague"))
    failed = next(i for i in result.items if i.issue_key == "KAFKA-3")
    assert failed.answer == "insufficient_information"
    assert failed.error == "ConnectionError: model server down"
    assert result.errors == 1
    assert len(result.items) == 4  # the others are still answered
