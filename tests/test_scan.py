from datetime import UTC, datetime

import pytest

from dep_watch_agent.dependencies import DEPENDENCIES
from dep_watch_agent.jira.models import parse_issue
from dep_watch_agent.jira.store import upsert_issue
from dep_watch_agent.scan import Backlog, backlog, candidates_query, scan_version
from dep_watch_agent.verdict import Evidence, Extraction, IssueText
from tests.jira_factory import raw_issue

KAFKA = DEPENDENCIES[0]


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
    result = scan_version(session, KAFKA, "3.9.1", "phrases", extractor, on_issue=progress.append)

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
    result = scan_version(session, KAFKA, "3.9.1", "phrases", PhraseExtractor(), since=since)
    assert {i.issue_key for i in result.items} == {"KAFKA-2", "KAFKA-3"}

    result = scan_version(session, KAFKA, "3.9.1", "phrases", PhraseExtractor(), limit=1)
    assert [i.issue_key for i in result.items] == ["KAFKA-3"]  # the newest
    assert result.candidates_total == 4


def test_a_failed_issue_is_reported_not_dropped(session):
    result = scan_version(session, KAFKA, "3.9.1", "phrases", PhraseExtractor(fail_on="vague"))
    failed = next(i for i in result.items if i.issue_key == "KAFKA-3")
    assert failed.answer == "insufficient_information"
    assert failed.error == "phrases could not read the issue: model server down"
    assert result.errors == 1
    assert len(result.items) == 4  # the others are still answered


class VersionedPhraseExtractor(PhraseExtractor):
    version = "v1"


def test_rescans_and_other_versions_reuse_stored_facts(session):
    first = scan_version(session, KAFKA, "3.9.1", "phrases", VersionedPhraseExtractor())
    assert first.cached == 0

    extractor = VersionedPhraseExtractor()
    again = scan_version(session, KAFKA, "3.9.1", "phrases", extractor)
    assert extractor.seen == []  # no model call
    assert again.cached == 3  # every issue the fix versions don't settle
    assert [(i.issue_key, i.answer) for i in again.items] == [
        (i.issue_key, i.answer) for i in first.items
    ]

    # Another version is answered from the same facts.
    upgrade = scan_version(session, KAFKA, "3.8.0", "phrases", extractor)
    assert extractor.seen == []
    regression = next(i for i in upgrade.items if i.issue_key == "KAFKA-2")
    assert regression.answer == "not_affected"  # 3.8.0 is before "Regression in 3.9.0"
    assert regression.cached is True


def test_backlog_counts_what_a_scan_would_read(session):
    extractor = VersionedPhraseExtractor()
    # Four candidates: KAFKA-1's fix versions settle it; the other three need the model.
    assert backlog(session, KAFKA, "3.9.1", "phrases", extractor) == Backlog(4, 1, 0, 3)

    scan_version(session, KAFKA, "3.9.1", "phrases", extractor, limit=2)  # reads KAFKA-3, KAFKA-2
    assert backlog(session, KAFKA, "3.9.1", "phrases", extractor) == Backlog(4, 1, 2, 1)
    assert extractor.seen == ["vague", "new regression"]  # counting never calls the model

    # Stored facts answer any version, but at 3.7.0 KAFKA-1's fix (3.8.0) no longer settles it,
    # and it was never read.
    assert backlog(session, KAFKA, "3.7.0", "phrases", extractor) == Backlog(4, 0, 2, 2)

    since = datetime(2026, 9, 10, tzinfo=UTC)
    assert backlog(session, KAFKA, "3.9.1", "phrases", extractor, since=since) == Backlog(
        2, 0, 2, 0
    )


def test_backlog_without_a_system_counts_only_what_code_settles(session):
    assert backlog(session, KAFKA, "3.9.1", None, None) == Backlog(4, 1, 0, 3)


def test_spark_candidates_leave_out_bugs_only_a_subproject_has(db):
    spark = next(d for d in DEPENDENCIES if d.id == "spark")
    for raw in [
        raw_issue(11, "SPARK-11", fix=["kubernetes-operator-1.0.0"]),  # the operator's bug
        raw_issue(12, "SPARK-12", affects=["4.0.0"], fix=["connect-swift-0.8.0"]),  # Spark's too
        raw_issue(13, "SPARK-13", fix=["3.5.2"]),
        raw_issue(14, "SPARK-14", resolution=None),  # no versions yet: kept
    ]:
        upsert_issue(db, parse_issue(raw))
    db.commit()
    keys = {issue.key for issue in db.scalars(candidates_query(spark, None))}
    assert keys == {"SPARK-12", "SPARK-13", "SPARK-14"}
