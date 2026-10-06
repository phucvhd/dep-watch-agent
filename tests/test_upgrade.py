import pytest

from dep_watch_agent.dependencies import DEPENDENCIES
from dep_watch_agent.jira.models import parse_issue
from dep_watch_agent.jira.store import upsert_issue
from dep_watch_agent.upgrade import (
    EXPOSED,
    FIXED,
    INCONCLUSIVE,
    NEW_RISK,
    REMAINS,
    UNCHANGED,
    change,
    diagnose,
)
from dep_watch_agent.verdict import Evidence, Extraction, IssueText
from tests.jira_factory import raw_issue

KAFKA = DEPENDENCIES[0]


class PhraseExtractor:
    """Cites a fact for each known phrase; records the issues it read."""

    version = "v1"
    PHRASES = {
        "Regression in 3.9.0": ("3.9.0", "introduced"),
        "Seen on 3.7.0": ("3.7.0", "affects"),
    }

    def __init__(self, fail: bool = False):
        self.seen: list[str] = []
        self.fail = fail

    def extract(self, issue: IssueText) -> Extraction:
        self.seen.append(issue.summary)
        if self.fail:
            raise ConnectionError("model server down")
        return Extraction(
            [
                Evidence(version, kind, text)
                for text in issue.fields()
                for phrase, (version, kind) in self.PHRASES.items()
                if phrase in text
            ]
        )


def issue(id, summary, **kwargs):
    return raw_issue(id, f"KAFKA-{id}", summary=summary, **kwargs)


ISSUES = [
    issue(1, "fixed between", fix=["3.8.0"]),
    issue(2, "regression", description="Regression in 3.9.0: hangs.", fix=["4.2.0"]),
    issue(3, "old", fix=["3.5.0"]),
    issue(4, "vague", description="The broker logs a warning.", resolution=None),
    issue(5, "seen early", description="Seen on 3.7.0 in production.", resolution=None),
    issue(6, "hint", description="Something odd.", resolution=None, affects=["3.9.0"]),
]


@pytest.fixture
def session(db):
    for raw in ISSUES:
        upsert_issue(db, parse_issue(raw))
    db.commit()
    return db


@pytest.mark.parametrize(
    ("current", "target", "expected"),
    [
        ("affected", "not_affected", FIXED),
        ("insufficient_information", "not_affected", FIXED),
        ("not_affected", "not_affected", UNCHANGED),
        ("not_affected", "affected", NEW_RISK),
        ("affected", "affected", REMAINS),
        ("insufficient_information", "affected", REMAINS),
        ("not_affected", "insufficient_information", EXPOSED),
        ("affected", "insufficient_information", INCONCLUSIVE),
    ],
)
def test_change(current, target, expected):
    assert change(current, target) == expected


def by_key(result):
    return {item.issue_key: item for item in result.items}


def test_upgrade_without_reading_uses_fix_versions_only(session):
    extractor = PhraseExtractor()
    result = diagnose(session, KAFKA, "3.7.0", "3.9.1", "phrases", extractor)
    items = by_key(result)

    assert result.direction == "upgrade"
    assert extractor.seen == []  # nothing stored, nothing read
    assert (items["KAFKA-1"].change, items["KAFKA-1"].decided_by) == (FIXED, "fix_versions")
    assert result.unchanged == 1  # KAFKA-3, fixed before both
    assert result.unchecked == 4  # the rest: never read, only counted
    assert result.counts[FIXED] == 1


def test_a_downgrade_lists_the_fixes_given_up(session):
    result = diagnose(session, KAFKA, "3.9.1", "3.7.0", "phrases", PhraseExtractor())
    assert result.direction == "downgrade"
    assert by_key(result)["KAFKA-1"].change == EXPOSED  # 3.8.0's fix is lost


def test_reading_classifies_from_the_same_facts(session):
    extractor = PhraseExtractor()
    result = diagnose(session, KAFKA, "3.8.0", "3.9.1", "phrases", extractor, read=10)
    items = by_key(result)

    assert items["KAFKA-2"].change == NEW_RISK  # before "Regression in 3.9.0", then in it
    assert (items["KAFKA-2"].current, items["KAFKA-2"].target) == ("not_affected", "affected")
    assert items["KAFKA-5"].change == REMAINS  # seen on 3.7.0, no fix
    assert items["KAFKA-4"].change == INCONCLUSIVE
    assert result.read == len(extractor.seen) == 4  # not KAFKA-1 or KAFKA-3: fix versions settle
    assert result.unchecked == 0

    # Stored now: another run reads nothing and answers the same.
    again = PhraseExtractor()
    rerun = diagnose(session, KAFKA, "3.8.0", "3.9.1", "phrases", again)
    assert again.seen == []
    assert by_key(rerun)["KAFKA-2"].cached is True
    assert by_key(rerun)["KAFKA-2"].change == NEW_RISK


def test_issues_reported_between_the_versions_are_read_first(session):
    extractor = PhraseExtractor()
    diagnose(session, KAFKA, "3.8.0", "3.9.1", "phrases", extractor, read=1)
    assert extractor.seen == ["hint"]  # JIRA lists 3.9.0 as affected: read before the rest


def test_a_failed_read_is_reported_not_dropped(session):
    result = diagnose(session, KAFKA, "3.8.0", "3.9.1", "phrases", PhraseExtractor(True), read=1)
    failed = by_key(result)["KAFKA-6"]
    assert failed.change == INCONCLUSIVE
    assert failed.error == "phrases could not read the issue: model server down"
    assert result.errors == 1


def test_without_a_system_only_fix_versions_answer(session):
    result = diagnose(session, KAFKA, "3.7.0", "3.9.1", None, None, read=10)
    assert result.read == 0
    assert result.counts[FIXED] == 1
