from collections import Counter

import pytest

from dep_watch_agent.eval.sampling import (
    START_LANGUAGE,
    STRATA_V1,
    STRATA_V2,
    IssueCandidate,
    _quota_counts,
    find_known_versions,
    load_candidates,
    released_versions,
    stratified_sample,
)
from dep_watch_agent.jira.models import parse_issue
from dep_watch_agent.jira.store import upsert_issue, upsert_versions
from dep_watch_agent.versions import parse_version
from tests.jira_factory import raw_comment, raw_issue

KNOWN = {parse_version(v) for v in ["2.8.0", "3.4.0", "3.7.0", "3.7.1", "3.10.0", "0.10.2.1"]}


# --- version mentions ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Broken since 3.7.0, still broken in 3.7.1.", ["3.7.0", "3.7.1"]),
        ("We run 3.7 in prod", ["3.7"]),  # 3.7 == 3.7.0
        ("Upgraded to 3.10.0", ["3.10.0"]),
        ("old cluster on 0.10.2.1", ["0.10.2.1"]),
        ("Scala 2.12 and Java 1.8", []),  # not Kafka versions
        ("broker at 192.168.1.1", []),
        ("kafka_2.13-3.7.0.tgz", ["3.7.0"]),
        ("3.7.0 then 3.7.0 again", ["3.7.0"]),
        ("see 3.7.1-rc2", ["3.7.1"]),
        ("version 3.7.0.1", []),
        ("nothing here", []),
    ],
)
def test_find_known_versions(text, expected):
    assert find_known_versions(text, KNOWN) == expected


# --- strata ---------------------------------------------------------------------


def candidate(
    key: str, fixes=("3.8.0",), mentions=False, affects=("3.6.0",), start=False
) -> IssueCandidate:
    return IssueCandidate(
        key=key,
        summary="s",
        description="d",
        comments=[],
        affects_versions=list(affects),
        fix_versions=list(fixes),
        resolved_at=None,
        versions_in_text=["3.6.0"] if mentions else [],
        has_start_language=start,
    )


@pytest.mark.parametrize(
    ("fixes", "era", "backport"),
    [
        (("1.1.0",), "legacy", False),
        (("0.10.2.1", "0.11.0.0"), "legacy", True),
        (("2.8.1",), "2.x", False),
        (("2.8.2", "3.0.0"), "3.x+", True),
        (("3.7.1", "3.7.2"), "3.x+", False),  # same line twice is not a backport
        (("4.0.0",), "3.x+", False),
    ],
)
def test_strata(fixes, era, backport):
    props = candidate("KAFKA-1", fixes=fixes).strata
    assert props["era"] == era
    assert props["backport"] is backport


def test_quota_counts_sum_to_size():
    for size in (1, 7, 10, 99, 100, 101):
        counts = _quota_counts({"a": 0.10, "b": 0.35, "c": 0.55}, size)
        assert sum(counts.values()) == size


def pool(n_per_bucket: int = 40, start: bool = False) -> list[IssueCandidate]:
    shapes = [
        ("1.1.0",),
        ("2.8.1",),
        ("2.8.2", "3.0.0"),
        ("3.8.0",),
        ("3.7.1", "3.8.0"),
    ]
    out = []
    n = 0
    for fixes in shapes:
        for mentions in (True, False):
            for _ in range(n_per_bucket):
                n += 1
                out.append(
                    candidate(
                        f"KAFKA-{n}", fixes=fixes, mentions=mentions, start=start or n % 2 == 0
                    )
                )
    return out


def test_v1_sample_meets_quotas_when_pool_allows():
    sample = stratified_sample(pool(), 100, seed=1, strata=STRATA_V1)
    assert len(sample) == 100
    assert len({c.key for c in sample}) == 100
    counts = {dim: Counter(c.strata[dim] for c in sample) for dim in ("era", "backport")}
    mentions = Counter(c.strata["mentions_version"] for c in sample)
    assert counts["era"] == {"legacy": 10, "2.x": 35, "3.x+": 55}
    assert counts["backport"] == {True: 30, False: 70}
    assert mentions == {True: 50, False: 50}


def test_v2_sample_balances_start_language():
    sample = stratified_sample(pool(), 100, seed=1, strata=STRATA_V2)
    assert Counter(c.strata["start_language"] for c in sample) == {True: 50, False: 50}
    assert Counter(c.strata["mentions_version"] for c in sample) == {True: 50, False: 50}
    assert Counter(c.strata["era"] for c in sample) == {"legacy": 10, "2.x": 35, "3.x+": 55}


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("This regression was introduced in 3.6.0", True),
        ("Broken since 3.6.0", True),
        ("It works fine on 3.5.2", True),
        ("This didn't happen before the upgrade", True),
        ("Not reproducible in older versions", True),
        ("Reproduced on 3.6.0", False),
        ("Fixed in 3.7.1", False),
    ],
)
def test_start_language_hint(text, expected):
    assert bool(START_LANGUAGE.search(text)) is expected


def test_sample_is_deterministic_and_sorted():
    a = stratified_sample(pool(), 50, seed=3)
    b = stratified_sample(pool(), 50, seed=3)
    assert [c.key for c in a] == [c.key for c in b]
    assert [c.key for c in a] == sorted((c.key for c in a), key=lambda k: int(k.split("-")[1]))
    assert [c.key for c in a] != [c.key for c in stratified_sample(pool(), 50, seed=4)]


def test_sample_tops_up_when_a_stratum_is_scarce():
    # No legacy issues at all: their 10% is filled from the rest.
    scarce = [c for c in pool() if c.strata["era"] != "legacy"]
    sample = stratified_sample(scarce, 100, seed=1)
    assert len(sample) == 100


def test_sample_larger_than_pool_raises():
    with pytest.raises(ValueError, match="only 3 candidates"):
        stratified_sample(pool()[:3], 10, seed=1)


# --- loading from Postgres -------------------------------------------------------------


def seed_versions(db, names_released: dict[str, bool]):
    upsert_versions(
        db,
        "KAFKA",
        [
            {"id": str(i), "name": name, "released": released, "archived": False}
            for i, (name, released) in enumerate(names_released.items(), 1)
        ],
    )


def test_released_versions_sorted_numerically(db):
    seed_versions(db, {"3.9.0": True, "3.10.0": True, "3.2.0": True, "4.5.0": False})
    assert [str(v) for v in released_versions(db, "KAFKA")] == ["3.2.0", "3.9.0", "3.10.0"]


def test_load_candidates_filters(db):
    seed_versions(db, {"3.6.0": True, "3.8.0": True})
    issues = [
        raw_issue(1, "KAFKA-1", affects=["3.6.0"], fix=["3.8.0"]),  # kept
        raw_issue(2, "KAFKA-2", affects=[], fix=["3.8.0"]),  # no affected version
        raw_issue(3, "KAFKA-3", affects=["3.6.0"], fix=[]),  # not fixed in a version
        raw_issue(4, "KAFKA-4", affects=["3.6.0"], fix=["3.8.0"], issuetype={"name": "Task"}),
        raw_issue(5, "KAFKA-5", affects=["3.6.0"], fix=["3.8.0"], resolution={"name": "Won't Fix"}),
        raw_issue(6, "KAFKA-6", affects=["streams-1.0"], fix=["3.8.0"]),  # unparseable
        raw_issue(7, "KAFKA-7", affects=["3.6.0"], fix=["3.8.0"], summary="x" * 50),  # too long
    ]
    for raw in issues:
        upsert_issue(db, parse_issue(raw))

    keys = [c.key for c in load_candidates(db, max_text_chars=60)]
    assert keys == ["KAFKA-1"]


def test_load_candidates_drops_bot_comments_and_finds_versions(db):
    seed_versions(db, {"3.6.0": True, "3.8.0": True})
    bot = raw_comment(2, "Mirrored PR review mentioning 3.8.0")
    bot["author"] = {"name": "githubbot", "displayName": "ASF GitHub Bot"}
    raw = raw_issue(
        1,
        "KAFKA-1",
        affects=["3.6.0"],
        fix=["3.8.0"],
        comments=[raw_comment(1, "Seen on 3.6.0 too"), bot, raw_comment(3, "   ")],
    )
    upsert_issue(db, parse_issue(raw))

    (c,) = load_candidates(db)
    assert c.comments == ["Seen on 3.6.0 too"]
    assert c.versions_in_text == ["3.6.0"]
    assert c.url == "https://issues.apache.org/jira/browse/KAFKA-1"


def test_load_candidates_sorted_by_issue_number(db):
    for n in (10, 9, 100):
        upsert_issue(db, parse_issue(raw_issue(n, f"KAFKA-{n}", affects=["3.6.0"], fix=["3.8.0"])))
    assert [c.key for c in load_candidates(db)] == ["KAFKA-9", "KAFKA-10", "KAFKA-100"]
