import itertools
from collections import Counter

import pytest

from dep_watch_agent.eval.cases import make_cases
from dep_watch_agent.eval.sampling import IssueCandidate
from dep_watch_agent.versions import Applicability, in_affected_range, parse_version

RELEASES = [
    parse_version(v)
    for v in [
        "3.5.0", "3.5.1", "3.5.2",
        "3.6.0", "3.6.1", "3.6.2",
        "3.7.0", "3.7.1", "3.7.2",
        "3.8.0", "3.8.1",
        "3.9.0",
        "4.0.0",
    ]
]  # fmt: skip


def candidate(key="KAFKA-1", affects=("3.6.0",), fixes=("3.8.0",)) -> IssueCandidate:
    return IssueCandidate(
        key=key,
        summary="s",
        description="d",
        comments=[],
        affects_versions=list(affects),
        fix_versions=list(fixes),
        resolved_at=None,
        versions_in_text=[],
    )


def build(c: IssueCandidate, seed: int = 1):
    return make_cases(c, RELEASES, seed=seed)


def rule(case) -> Applicability:
    return in_affected_range(case.kafka_version, case.affects_versions, case.fix_versions)


def test_positive_and_negative_follow_the_rules():
    positive, negative = build(candidate())
    assert positive.metadata_answer == "affected"
    assert negative.metadata_answer == "not_affected"
    assert rule(positive) is Applicability.AFFECTED
    assert rule(negative) is Applicability.NOT_AFFECTED


def test_positive_prefers_listed_affected_version():
    positive, _ = build(candidate(affects=("3.6.1",), fixes=("3.8.0",)))
    assert positive.kafka_version == "3.6.1"
    assert positive.basis == "listed_affected"


def test_positive_falls_back_to_inferred_when_listed_version_unreleased():
    # 3.6.3 was never released; 3.7.x is affected by inference.
    positive, _ = build(candidate(affects=("3.6.3",), fixes=("3.8.0",)))
    assert positive.basis == "inferred_affected"
    assert rule(positive) is Applicability.AFFECTED


def test_no_cases_when_no_release_was_affected():
    # Found and fixed during 3.7.0 development: no shipped release had the bug.
    assert build(candidate(affects=("3.7.0",), fixes=("3.7.0",))) is None


def test_no_cases_without_a_safe_release():
    # Affected from the first release onwards and never fixed in a release.
    assert build(candidate(affects=("3.5.0",), fixes=("4.1.0",))) is None


@pytest.mark.parametrize(
    ("kind", "expected_version"),
    [
        ("later_patch", "3.7.2"),  # first patch after the 3.7.1 backport
        ("later_line", "3.9.0"),  # first release on a line newer than every fix
        ("before_affected", "3.5.2"),  # last release before the bug
    ],
)
def test_negative_kinds_pick_the_hardest_version(kind, expected_version):
    c = candidate(affects=("3.6.0",), fixes=("3.6.2", "3.7.1", "3.8.0"))
    found = {}
    for seed in range(200):
        _, negative = build(c, seed)
        found.setdefault(negative.basis, set()).add(negative.kafka_version)
    assert found[kind] == {expected_version}


def test_fix_version_negative_is_a_listed_fix():
    c = candidate(affects=("3.6.0",), fixes=("3.6.2", "3.7.1", "3.8.0"))
    fix_negatives = {
        n.kafka_version for n in (build(c, s)[1] for s in range(200)) if n.basis == "fix_version"
    }
    assert fix_negatives == {"3.6.2", "3.7.1", "3.8.0"}


def test_negative_kinds_are_weighted_towards_fix_versions():
    c = candidate(affects=("3.6.0",), fixes=("3.6.2", "3.7.1", "3.8.0"))
    kinds = Counter(build(c, s)[1].basis for s in range(2000))
    assert kinds["fix_version"] > kinds["later_patch"] > kinds["later_line"]
    assert set(kinds) == {"fix_version", "later_patch", "later_line", "before_affected"}


def test_deterministic_per_seed_and_key():
    c = candidate(affects=("3.6.0",), fixes=("3.6.2", "3.7.1", "3.8.0"))
    assert build(c, 7) == build(c, 7)
    # Different issues get independent draws under the same seed.
    other = candidate(key="KAFKA-2", affects=("3.6.0",), fixes=("3.6.2", "3.7.1", "3.8.0"))
    draws = {build(c, s)[1].kafka_version != build(other, s)[1].kafka_version for s in range(50)}
    assert draws == {True, False}


def test_case_fields():
    positive, negative = build(candidate(key="KAFKA-42"))
    assert positive.case_id == f"KAFKA-42@{positive.kafka_version}"
    assert positive.issue_key == negative.issue_key == "KAFKA-42"
    assert positive.affects_versions == ["3.6.0"]
    assert positive.fix_versions == ["3.8.0"]
    assert positive.case_id != negative.case_id


def test_every_generated_case_agrees_with_the_version_module():
    """Property check over many affects/fix combinations."""
    names = [str(r) for r in RELEASES] + ["3.6.3", "4.1.0"]
    built = 0
    for affects, fixes in itertools.product(
        itertools.combinations(names, 1), itertools.combinations(names, 2)
    ):
        cases = build(candidate(affects=affects, fixes=fixes))
        if cases is None:
            continue
        built += 1
        positive, negative = cases
        assert rule(positive) is Applicability.AFFECTED, positive
        assert rule(negative) is Applicability.NOT_AFFECTED, negative
        assert parse_version(positive.kafka_version) in RELEASES
        assert parse_version(negative.kafka_version) in RELEASES
    assert built > 100
