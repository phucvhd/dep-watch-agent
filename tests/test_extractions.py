import pytest
from sqlalchemy import func, select

from dep_watch_agent import extractions
from dep_watch_agent.jira.models import parse_issue
from dep_watch_agent.jira.store import upsert_issue
from dep_watch_agent.orm import ExtractionRow
from dep_watch_agent.verdict import Evidence, Extraction, IssueText
from tests.jira_factory import raw_issue

TEXT = IssueText("Hang", "Regression in 3.6.0: the consumer hangs.", ["Works on 3.5.2."], ["3.9.0"])
FACT = Evidence("3.6.0", "introduced", "Regression in 3.6.0: the consumer hangs.")


class CountingExtractor:
    def __init__(self, version: str | None = "v1", fail: bool = False):
        if version is not None:
            self.version = version
        self.calls = 0
        self.fail = fail

    def extract(self, issue: IssueText) -> Extraction:
        self.calls += 1
        if self.fail:
            raise ConnectionError("model server down")
        return Extraction([FACT])


@pytest.fixture
def issue_id(db):
    upsert_issue(db, parse_issue(raw_issue(1, "KAFKA-1")))
    db.commit()
    return 1


def stored(db) -> int:
    return db.scalar(select(func.count()).select_from(ExtractionRow))


def test_an_extraction_is_stored_and_reused(db, issue_id):
    extractor = CountingExtractor()
    first = extractions.extract(db, issue_id, TEXT, "sys", extractor)
    second = extractions.extract(db, issue_id, TEXT, "sys", extractor)

    assert (first.cached, second.cached) == (False, True)
    assert first.extraction == second.extraction == Extraction([FACT])
    assert extractor.calls == 1
    row = db.scalars(select(ExtractionRow)).one()
    assert (row.system, row.extractor_version) == ("sys", "v1")
    assert row.evidence == [{"version": "3.6.0", "kind": "introduced", "quote": FACT.quote}]


@pytest.mark.parametrize(
    "change",
    [
        {
            "text": IssueText(
                "Hang", TEXT.description, [*TEXT.comments, "Seen on 3.7.0."], ["3.9.0"]
            )
        },
        {"text": IssueText("Hang", TEXT.description, TEXT.comments, ["3.9.0", "3.8.1"])},
        {"system": "other"},
        {"version": "v2"},  # a new model or prompt
    ],
    ids=["new comment", "new fix version", "other system", "new extractor version"],
)
def test_a_change_the_system_would_see_extracts_again(db, issue_id, change):
    extractions.extract(db, issue_id, TEXT, "sys", CountingExtractor())
    extractor = CountingExtractor(change.get("version", "v1"))
    again = extractions.extract(
        db, issue_id, change.get("text", TEXT), change.get("system", "sys"), extractor
    )
    assert (again.cached, extractor.calls) == (False, 1)
    assert stored(db) == 2  # the old extraction stays as history


def test_extractors_without_a_version_are_never_stored(db, issue_id):
    extractor = CountingExtractor(version=None)
    for _ in range(2):
        assert extractions.extract(db, issue_id, TEXT, "sys", extractor).cached is False
    assert (extractor.calls, stored(db)) == (2, 0)


def test_a_failed_extraction_is_not_stored(db, issue_id):
    with pytest.raises(extractions.ExtractionFailed, match="sys could not read the issue"):
        extractions.extract(db, issue_id, TEXT, "sys", CountingExtractor(fail=True))
    assert stored(db) == 0


def test_text_hash_covers_only_what_the_system_sees():
    same = IssueText("Hang", TEXT.description, list(TEXT.comments), list(TEXT.fix_versions))
    assert extractions.text_hash(same) == extractions.text_hash(TEXT)
    assert len(extractions.text_hash(TEXT)) == 64
    other = IssueText("Hang!", TEXT.description, TEXT.comments, TEXT.fix_versions)
    assert extractions.text_hash(other) != extractions.text_hash(TEXT)


def test_refresh_reads_again_and_replaces_the_stored_facts(db, issue_id):
    extractions.extract(db, issue_id, TEXT, "sys", CountingExtractor())

    class Different(CountingExtractor):
        def extract(self, issue: IssueText) -> Extraction:
            self.calls += 1
            return Extraction([])

    extractor = Different()
    again = extractions.extract(db, issue_id, TEXT, "sys", extractor, refresh=True)
    assert (again.cached, extractor.calls) == (False, 1)
    assert stored(db) == 1  # replaced, not added
    assert extractions.stored(db, issue_id, TEXT, "sys", extractor) == Extraction([])
