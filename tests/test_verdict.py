import pytest

from dep_watch_agent.verdict import (
    AFFECTED,
    INSUFFICIENT_INFORMATION,
    NOT_AFFECTED,
    Evidence,
    Extraction,
    IssueText,
    decide,
    is_release,
    quote_in_issue,
)

ISSUE = IssueText(
    summary="Consumer hangs after rebalance",
    description="Seen on 3.6.0 and 3.6.1.\nStack trace:\n  at   Foo.bar(Foo.java:12)",
    comments=["Fixed in 3.7.1 and 3.8.0.", "Merged to 3.6 branch."],
)

AFFECTS_360 = Evidence("3.6.0", "affects", "Seen on 3.6.0 and 3.6.1.")
FIX_371 = Evidence("3.7.1", "fix", "Fixed in 3.7.1 and 3.8.0.")
FIX_380 = Evidence("3.8.0", "fix", "Fixed in 3.7.1 and 3.8.0.")


def run(version, *evidence):
    return decide(ISSUE, version, Extraction(list(evidence)))


@pytest.mark.parametrize(
    ("version", "answer"),
    [
        ("3.5.0", NOT_AFFECTED),  # before the earliest affected version
        ("3.6.0", AFFECTED),
        ("3.7.0", AFFECTED),
        ("3.7.1", NOT_AFFECTED),
        ("3.10.0", NOT_AFFECTED),
    ],
)
def test_decides_with_the_version_module(version, answer):
    assert run(version, AFFECTS_360, FIX_371, FIX_380).answer == answer


def test_no_evidence_is_insufficient():
    assert run("3.7.0").answer == INSUFFICIENT_INFORMATION


def test_unknown_start_is_insufficient():
    # Only a fix version is known and 3.7.0 is below it: no evidence the bug existed there.
    assert run("3.7.0", FIX_371).answer == INSUFFICIENT_INFORMATION
    assert run("3.7.1", FIX_371).answer == NOT_AFFECTED


def test_fabricated_quote_is_dropped():
    fake = Evidence("3.9.0", "fix", "Fixed in 3.9.0.")
    decision = run("3.9.0", AFFECTS_360, fake)
    assert decision.answer == AFFECTED  # decided without the fabricated fix
    assert [d.reason for d in decision.dropped] == ["citation not found"]
    assert decision.evidence_total == 2
    assert decision.citations_valid == 1


def test_only_invalid_citations_means_abstain():
    decision = run("3.6.0", Evidence("3.6.0", "affects", "this sentence is not in the issue"))
    assert decision.answer == INSUFFICIENT_INFORMATION
    assert decision.used == []


def test_release_line_is_dropped():
    decision = run("3.6.5", AFFECTS_360, Evidence("3.6", "fix", "Merged to 3.6 branch."))
    assert decision.answer == AFFECTED  # "3.6" must not become a fix in 3.6.0
    assert [d.reason for d in decision.dropped] == ["release line, not a release"]
    assert decision.citations_valid == 2  # the quote itself was valid


def test_non_version_and_bad_kind_dropped():
    decision = run(
        "3.6.0",
        Evidence("latest", "fix", "Fixed in 3.7.1 and 3.8.0."),
        Evidence("3.6.0", "maybe", "Seen on 3.6.0 and 3.6.1."),  # type: ignore[arg-type]
    )
    assert decision.answer == INSUFFICIENT_INFORMATION
    assert sorted(d.reason for d in decision.dropped) == ["not a version", "unknown kind 'maybe'"]


def test_quote_matching_ignores_whitespace_but_not_words():
    assert quote_in_issue("Stack trace: at Foo.bar(Foo.java:12)", ISSUE)
    assert quote_in_issue("  Fixed in 3.7.1   and 3.8.0. ", ISSUE)
    assert not quote_in_issue("Fixed in 3.7.2", ISSUE)
    assert not quote_in_issue("   ", ISSUE)
    # Quotes can't span fields.
    assert not quote_in_issue("Fixed in 3.7.1 and 3.8.0. Merged to 3.6 branch.", ISSUE)


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("3.7.0", True),
        ("v3.7.0", True),
        ("3.7.0-rc1", True),
        ("0.10.2.1", True),
        ("3.7", False),
        ("0.10.2", False),
        ("nope", False),
    ],
)
def test_is_release(version, expected):
    assert is_release(version) is expected


def test_issue_text_from_dict_tolerates_missing_fields():
    issue = IssueText.from_dict({"summary": "s", "description": None})
    assert issue.fields() == ["s", ""]
