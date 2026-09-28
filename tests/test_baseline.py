import pytest

from dep_watch_agent.baseline import RuleBasedExtractor
from dep_watch_agent.verdict import IssueText, quote_in_issue
from dep_watch_agent.versions import parse_version

KNOWN = {
    parse_version(v)
    for v in [
        "0.10.2.1", "2.0.0", "2.1.0", "2.3.0", "2.3.1", "2.4.0",
        "3.4.1", "3.6.0", "3.6.1", "3.7.0", "3.7.1", "3.8.0", "4.1.0",
    ]
}  # fmt: skip


def facts(text: str) -> list[tuple[str, str]]:
    extraction = RuleBasedExtractor(KNOWN).extract(IssueText(summary="", description=text))
    return [(e.kind, e.version) for e in extraction.evidence]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # fix cues, including lists after one cue
        ("Fixed in 3.7.1 and 3.8.0.", [("fix", "3.7.1"), ("fix", "3.8.0")]),
        ("This was merged to trunk and cherry-picked to 3.7.1", [("fix", "3.7.1")]),
        ("Backported to 3.6.1 as well.", [("fix", "3.6.1")]),
        ("The issue no longer happens in 3.8.0.", [("fix", "3.8.0")]),
        ("Fix Version: 3.8.0", [("fix", "3.8.0")]),
        # affects cues
        ("Affects version 3.6.0", [("affects", "3.6.0")]),
        ("Broken since 3.6.0.", [("affects", "3.6.0")]),
        ("Reproduced on 3.7.0 with 3 brokers", [("affects", "3.7.0")]),
        ("After upgrading to Kafka 3.4.1, the producer logs errors", [("affects", "3.4.1")]),
        ("We run Kafka Streams 4.1.0 with custom processors", [("affects", "4.1.0")]),
        ("3-broker cluster (running Apache Kafka 2.3.1)", [("affects", "2.3.1")]),
        ("There was a regression in 2.3.0 that made it slow", [("affects", "2.3.0")]),
        ("It is still present in 3.7.1.", [("affects", "3.7.1")]),
        ("Still not fixed in 3.7.1 for us.", [("affects", "3.7.1")]),
        ("at Foo.bar(Foo.java:12) ~[kafka-clients-3.7.0.jar:?]", [("affects", "3.7.0")]),
        ("kafka_2.13-3.6.0 $ bin/kafka-topics.sh", [("affects", "3.6.0")]),
        # upgrade source is not evidence, target is
        ("After upgrading from 2.3.0 to 2.4.0 the consumer hangs.", [("affects", "2.4.0")]),
        # neutral cues cancel
        ("It doesn't happen on 3.6.0.", []),
        ("Works fine on 3.6.0.", []),
        ("This is not fixed in 3.7.1.", []),
        # a cue far from the version, with real words between, doesn't count
        ("Moving this out to 2.1.0 since it is not ready for 2.0.0", []),
        # no cue, release lines, unknown versions, non-Kafka numbers
        ("See 3.7.0 for details", []),
        ("Merged to the 3.7 branch", []),
        ("Fixed in 9.9.9", []),
        ("latency went from 2.0 ms to 3.4 ms", []),
    ],
)
def test_cues(text, expected):
    assert facts(text) == expected


def test_quotes_are_the_source_sentence_and_always_valid():
    issue = IssueText(
        summary="Consumer hangs",
        description="We saw it on 3.6.0. Unrelated sentence.\nFixed in 3.7.1.",
        comments=["Also reproduced on 3.7.0 here."],
    )
    evidence = RuleBasedExtractor(KNOWN).extract(issue).evidence
    assert [e.quote for e in evidence] == [
        "We saw it on 3.6.0.",
        "Fixed in 3.7.1.",
        "Also reproduced on 3.7.0 here.",
    ]
    assert all(quote_in_issue(e.quote, issue) for e in evidence)


def test_duplicates_keep_first_quote():
    evidence = (
        RuleBasedExtractor(KNOWN)
        .extract(IssueText("Fixed in 3.7.1.", "Yes, fixed in 3.7.1 as said."))
        .evidence
    )
    assert [(e.version, e.quote) for e in evidence] == [("3.7.1", "Fixed in 3.7.1.")]


def test_same_version_can_be_both_kinds():
    assert facts("Reproduced on 3.7.1. Fixed in 3.7.1.") == [
        ("affects", "3.7.1"),
        ("fix", "3.7.1"),
    ]


def test_v_prefix_normalized():
    assert facts("Fixed in v3.7.1") == [("fix", "3.7.1")]
