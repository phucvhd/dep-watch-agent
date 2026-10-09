import pytest

from dep_watch_agent.verdict import (
    AFFECTED,
    INSUFFICIENT_INFORMATION,
    NOT_AFFECTED,
    Evidence,
    Extraction,
    IssueText,
    decide,
    quote_in_issue,
    version_in_quote,
)
from dep_watch_agent.versions import KAFKA, THREE_PART

ISSUE = IssueText(
    summary="Consumer hangs after rebalance",
    description="Seen on 3.6.0 and 3.6.1.\nStack trace:\n  at   Foo.bar(Foo.java:12)",
    comments=["Fixed in 3.7.1 and 3.8.0.", "Merged to 3.6 branch."],
)

AFFECTS_360 = Evidence("3.6.0", "affects", "Seen on 3.6.0 and 3.6.1.")
FIX_371 = Evidence("3.7.1", "fix", "Fixed in 3.7.1 and 3.8.0.")
FIX_380 = Evidence("3.8.0", "fix", "Fixed in 3.7.1 and 3.8.0.")


def run(version, *evidence):
    return decide(ISSUE, version, Extraction(list(evidence)), KAFKA)


@pytest.mark.parametrize(
    ("version", "answer"),
    [
        # "seen on 3.6.0" says nothing about 3.5.0: the reporter's version isn't the start
        ("3.5.0", INSUFFICIENT_INFORMATION),
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
        ("0.8.0", True),  # an early Kafka release, written with three parts
        ("nope", False),
    ],
)
def test_is_release(version, expected):
    assert KAFKA.is_release(version) is expected


def test_issue_text_from_dict_tolerates_missing_fields():
    issue = IssueText.from_dict({"summary": "s", "description": None})
    assert issue.fields() == ["s", ""]


# --- start-of-bug evidence and given fix versions ----------------------------------------

START_ISSUE = IssueText(
    summary="Fetch sessions leak",
    description="This regression was introduced in 3.6.0. It works fine on 3.5.2.",
    comments=["Reproduced on 3.6.1."],
    fix_versions=["3.7.1", "3.8.0"],
)
INTRODUCED_360 = Evidence("3.6.0", "introduced", "This regression was introduced in 3.6.0.")
UNAFFECTED_352 = Evidence("3.5.2", "unaffected", "It works fine on 3.5.2.")
AFFECTS_361 = Evidence("3.6.1", "affects", "Reproduced on 3.6.1.")


def start_run(version, *evidence, issue=START_ISSUE):
    return decide(issue, version, Extraction(list(evidence)), KAFKA).answer


@pytest.mark.parametrize(
    ("version", "answer"),
    [
        ("3.5.0", NOT_AFFECTED),  # before the bug was introduced
        ("3.5.2", NOT_AFFECTED),
        ("3.6.0", AFFECTED),
        ("3.7.0", AFFECTED),
        ("3.7.1", NOT_AFFECTED),  # given fix version
        ("3.9.0", NOT_AFFECTED),
    ],
)
def test_introduced_sets_where_the_bug_starts(version, answer):
    assert start_run(version, INTRODUCED_360) == answer


def test_unaffected_covers_only_that_version():
    assert start_run("3.5.2", AFFECTS_361, UNAFFECTED_352) == NOT_AFFECTED
    # "Works on 3.5.2" says nothing about 3.4.0: only "introduced" marks where the bug starts.
    assert start_run("3.4.0", AFFECTS_361, UNAFFECTED_352) == INSUFFICIENT_INFORMATION
    # Between "works on 3.5.2" and "seen on 3.6.1": unknown.
    assert start_run("3.6.0", AFFECTS_361, UNAFFECTED_352) == INSUFFICIENT_INFORMATION
    assert start_run("3.6.1", AFFECTS_361, UNAFFECTED_352) == AFFECTED
    # With the start stated, versions before it are settled.
    assert start_run("3.4.0", INTRODUCED_360, UNAFFECTED_352) == NOT_AFFECTED


def test_absent_on_a_later_version_says_nothing_about_earlier_ones():
    # KAFKA-20003: "not causing a real problem in 4.2.0" was read as every version up to 4.2.0
    # being unaffected, a silent miss for 3.9.1.
    issue = IssueText("s", "This issue is not causing a real problem in 4.2.0.")
    absent = Evidence("4.2.0", "unaffected", "This issue is not causing a real problem in 4.2.0.")
    assert start_run("3.9.1", absent, issue=issue) == INSUFFICIENT_INFORMATION
    assert start_run("4.2.0", absent, issue=issue) == NOT_AFFECTED


def test_observed_only_is_insufficient_below_it():
    assert start_run("3.6.0", AFFECTS_361) == INSUFFICIENT_INFORMATION
    assert start_run("3.7.0", AFFECTS_361) == AFFECTED


def test_given_fix_versions_decide_without_text_evidence():
    # No extracted facts at all: the given fix versions still settle the fix side.
    assert start_run("3.7.1") == NOT_AFFECTED
    assert start_run("3.7.2") == NOT_AFFECTED  # later patch on a fixed line
    assert start_run("3.9.0") == NOT_AFFECTED
    assert start_run("3.7.0") == INSUFFICIENT_INFORMATION


def test_explicit_unaffected_version_beats_range():
    issue = IssueText("s", "Seen on 3.5.0. Works on 3.6.0 again.", fix_versions=[])
    evidence = [
        Evidence("3.5.0", "affects", "Seen on 3.5.0."),
        Evidence("3.6.0", "unaffected", "Works on 3.6.0 again."),
    ]
    assert start_run("3.6.0", *evidence, issue=issue) == NOT_AFFECTED


def test_release_lines_in_given_fix_versions_are_ignored():
    issue = IssueText("s", "Reproduced on 3.6.1.", fix_versions=["3.7"])
    assert start_run("3.7.0", AFFECTS_361, issue=issue) == AFFECTED


def test_a_fact_whose_quote_does_not_name_its_version_is_dropped():
    # KAFKA-14102: a stack trace line cited as evidence for 3.0.1; KAFKA-20770: "introduced by
    # KIP-1023" cited as "introduced 4.3.0".
    issue = IssueText(
        "s",
        "Caused by: java.lang.IllegalArgumentException: Callback handler must be castable.\n"
        "Identified while comparing the implementations introduced by KIP-1023.",
    )
    decision = decide(
        issue,
        "3.9.1",
        Extraction(
            [
                Evidence("3.0.1", "affects", "Caused by: java.lang.IllegalArgumentException"),
                Evidence("4.3.0", "introduced", "the implementations introduced by KIP-1023."),
            ]
        ),
        KAFKA,
    )
    assert decision.answer == INSUFFICIENT_INFORMATION  # was affected and not_affected
    assert [d.reason for d in decision.dropped] == ["version not in quote"] * 2
    assert decision.citations_valid == 2  # the quotes exist; they just don't name the version


@pytest.mark.parametrize(
    ("version", "quote", "named"),
    [
        ("3.6.0", "Seen on 3.6.0.", True),
        ("3.6.0", "Kafka Version: {{3.6.0}}", True),
        ("3.6.0", "at kafka-raft-3.6.0.jar", True),
        ("3.6.0", "upgraded to v3.6.0 today", True),
        ("0.10.2.0", "版本 kafka_2.11-0.10.2.0 中", True),
        ("v3.6.0", "Seen on 3.6.0", True),
        ("3.6.0", "Seen on 13.6.0", False),
        ("3.6.0", "Seen on 3.6.01", False),
        ("3.6.0", "Seen on 3.6.0.1", False),
        ("3.6.0", "Seen on the 3.6 line", False),
    ],
)
def test_version_in_quote(version, quote, named):
    assert version_in_quote(version, quote) is named


def test_fix_versions_are_not_quotable_text():
    issue = IssueText("s", "d", fix_versions=["3.7.1"])
    assert not quote_in_issue("3.7.1", issue)


def test_issue_text_reads_given_fix_versions():
    issue = IssueText.from_dict({"summary": "s", "description": "d", "fix_versions": ["3.7.1"]})
    assert issue.fix_versions == ["3.7.1"]


def test_early_kafka_fix_versions_count():
    # JIRA writes Kafka's early releases short: a fix in 0.8.1 used to be dropped as a line.
    issue = IssueText("s", "Seen on 0.8.0.", fix_versions=["0.8.1"])
    assert decide(issue, "0.8.1.1", Extraction([]), KAFKA).answer == NOT_AFFECTED
    seen = Extraction([Evidence("0.8.0", "affects", "Seen on 0.8.0.")])
    assert decide(issue, "0.8.0", seen, KAFKA).answer == AFFECTED


def test_a_subproject_fix_version_does_not_settle_spark():
    # Spark's JIRA lists the Kubernetes Operator's releases too: its 1.0.0 is not Spark's.
    issue = IssueText(summary="s", description="d", fix_versions=["kubernetes-operator-1.0.0"])
    assert decide(issue, "3.5.1", Extraction([]), THREE_PART).answer == INSUFFICIENT_INFORMATION
    fixed = IssueText(summary="s", description="d", fix_versions=["3.5.2", "connect-rust-4.2.0"])
    assert decide(fixed, "3.5.2", Extraction([]), THREE_PART).answer == NOT_AFFECTED
