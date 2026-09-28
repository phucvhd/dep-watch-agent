import pytest

from dep_watch_agent.versions import (
    Applicability,
    Version,
    VersionParseError,
    compare_versions,
    in_affected_range,
    parse_version,
)

AFFECTED = Applicability.AFFECTED
NOT_AFFECTED = Applicability.NOT_AFFECTED
UNKNOWN = Applicability.UNKNOWN


# --- parsing -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "release", "pre"),
    [
        ("3.9.0", (3, 9, 0), None),
        ("3.10.0", (3, 10, 0), None),
        ("4.0.0", (4, 0, 0), None),
        ("0.10.2.1", (0, 10, 2, 1), None),
        ("0.8.2.2", (0, 8, 2, 2), None),
        # Short forms are padded to the scheme length.
        ("3.7", (3, 7, 0), None),
        ("0.10", (0, 10, 0, 0), None),
        ("0.10.2", (0, 10, 2, 0), None),
        # Pre-release tags.
        ("3.7.0-rc1", (3, 7, 0), ("rc", 1)),
        ("3.7.0-rc0", (3, 7, 0), ("rc", 0)),
        ("3.7.0-RC2", (3, 7, 0), ("rc", 2)),
        ("3.7.0rc1", (3, 7, 0), ("rc", 1)),
        ("3.7.0-rc.1", (3, 7, 0), ("rc", 1)),
        ("3.7.0-alpha1", (3, 7, 0), ("alpha", 1)),
        ("3.7.0-beta", (3, 7, 0), ("beta", 0)),
        ("3.7.0-SNAPSHOT", (3, 7, 0), ("snapshot", 0)),
        # Tolerated decoration.
        ("  3.9.0 ", (3, 9, 0), None),
        ("v3.9.0", (3, 9, 0), None),
    ],
)
def test_parse(raw, release, pre):
    v = parse_version(raw)
    assert v.release == release
    assert v.pre == pre


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "3",
        "abc",
        "3.x",
        "3.9.0.",
        ".3.9.0",
        "3..9",
        "3.9.0-foo",
        "3.9.0 rc1",
        "3.9.0.1",  # four parts only exist for 0.x releases
        "0.10.2.1.1",
        "-3.9.0",
        "future",
        "trunk",
    ],
)
def test_parse_rejects_invalid(raw):
    with pytest.raises(VersionParseError):
        parse_version(raw)


def test_parse_error_is_value_error():
    with pytest.raises(ValueError):
        parse_version("nope")


def test_parse_rejects_non_string():
    with pytest.raises(VersionParseError):
        parse_version(390)  # type: ignore[arg-type]


def test_parse_accepts_version_instance():
    v = parse_version("3.9.0")
    assert parse_version(v) is v


def test_str_keeps_raw_input():
    assert str(parse_version("3.7")) == "3.7"
    assert str(parse_version(" 3.7.0-rc1 ")) == "3.7.0-rc1"


@pytest.mark.parametrize(
    ("raw", "line"),
    [
        ("3.7.1", (3, 7)),
        ("3.7", (3, 7)),
        ("3.7.0-rc1", (3, 7)),
        ("1.0.2", (1, 0)),
        ("0.10.2.1", (0, 10, 2)),
        ("0.10.1.0", (0, 10, 1)),
        ("0.11.0.3", (0, 11, 0)),
    ],
)
def test_release_line(raw, line):
    assert parse_version(raw).line == line


def test_is_prerelease():
    assert parse_version("3.7.0-rc1").is_prerelease
    assert not parse_version("3.7.0").is_prerelease


# --- comparison: known traps --------------------------------------------------


@pytest.mark.parametrize(
    ("lower", "higher"),
    [
        # Lexical comparison gets every one of these wrong.
        ("3.9.0", "3.10.0"),
        ("2.8.9", "2.8.10"),
        ("0.9.0.0", "0.10.0.0"),
        ("0.10.2.1", "0.10.2.10"),
        ("3.9.9", "3.10.0"),
        ("9.0.0", "10.0.0"),
        # Plain ordering.
        ("3.7.0", "3.7.1"),
        ("3.7.1", "3.8.0"),
        ("0.11.0.3", "1.0.0"),
        ("2.8.2", "3.0.0"),
        # Pre-release sorts before its release, after the previous release.
        ("3.7.0-rc1", "3.7.0"),
        ("3.6.2", "3.7.0-rc0"),
        ("3.7.0-rc0", "3.7.0-rc1"),
        ("3.7.0-rc2", "3.7.0-rc10"),
        ("3.7.0-alpha1", "3.7.0-beta1"),
        ("3.7.0-beta1", "3.7.0-rc1"),
        ("3.7.0-SNAPSHOT", "3.7.0-alpha1"),
        ("3.7.0-rc9", "3.7.0"),
    ],
)
def test_ordering(lower, higher):
    assert compare_versions(lower, higher) == -1
    assert compare_versions(higher, lower) == 1
    assert parse_version(lower) < parse_version(higher)
    assert parse_version(higher) > parse_version(lower)


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("3.9.0", "3.9.0"),
        ("3.7", "3.7.0"),
        ("0.10.2", "0.10.2.0"),
        ("v3.9.0", "3.9.0"),
        ("3.7.0-RC1", "3.7.0-rc1"),
        ("3.7.0-rc", "3.7.0-rc0"),
    ],
)
def test_equality(a, b):
    assert compare_versions(a, b) == 0
    assert parse_version(a) == parse_version(b)
    assert hash(parse_version(a)) == hash(parse_version(b))


def test_sorting_is_numeric():
    raw = ["3.10.0", "3.9.0", "3.7.0-rc1", "2.8.10", "3.7.0", "2.8.9", "0.10.2.1", "1.0.0"]
    assert [str(v) for v in sorted(parse_version(r) for r in raw)] == [
        "0.10.2.1",
        "1.0.0",
        "2.8.9",
        "2.8.10",
        "3.7.0-rc1",
        "3.7.0",
        "3.9.0",
        "3.10.0",
    ]


def test_compare_rejects_invalid():
    with pytest.raises(VersionParseError):
        compare_versions("3.9.0", "latest")


def test_version_not_comparable_to_string():
    with pytest.raises(TypeError):
        _ = parse_version("3.9.0") < "3.10.0"  # type: ignore[operator]
    assert parse_version("3.9.0") != "3.9.0"


# --- affected range -----------------------------------------------------------


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("3.5.0", NOT_AFFECTED),  # before the earliest known affected version
        ("3.6.0", AFFECTED),
        ("3.6.1", AFFECTED),
        ("3.7.0", AFFECTED),
        ("3.8.0", AFFECTED),  # later line, no fix anywhere yet
        ("3.10.0", AFFECTED),
    ],
)
def test_unresolved_issue(version, expected):
    assert in_affected_range(version, affected_versions=["3.6.0"], fix_versions=[]) == expected


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("3.7.0", AFFECTED),
        ("3.7.2", AFFECTED),
        ("3.8.0-rc1", AFFECTED),  # pre-release of the fix version still has the bug
        ("3.8.0", NOT_AFFECTED),
        ("3.8.1", NOT_AFFECTED),
        ("3.9.0", NOT_AFFECTED),
        ("3.10.0", NOT_AFFECTED),
        ("4.0.0", NOT_AFFECTED),
    ],
)
def test_single_fix_version(version, expected):
    assert in_affected_range(version, affected_versions=["3.7.0"], fix_versions=["3.8.0"]) == (
        expected
    )


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        # Fixed on trunk (3.8.0) and backported to 3.6.2 and 3.7.1; 3.5 got no backport.
        ("3.5.0", AFFECTED),
        ("3.5.2", AFFECTED),
        ("3.6.0", AFFECTED),
        ("3.6.1", AFFECTED),
        ("3.6.2", NOT_AFFECTED),
        ("3.6.3", NOT_AFFECTED),
        ("3.7.0", AFFECTED),
        ("3.7.1", NOT_AFFECTED),
        ("3.7.2", NOT_AFFECTED),
        ("3.8.0", NOT_AFFECTED),
        ("3.9.0", NOT_AFFECTED),
        ("3.4.0", NOT_AFFECTED),  # before the earliest known affected version
    ],
)
def test_backported_fix(version, expected):
    result = in_affected_range(
        version,
        affected_versions=["3.5.0", "3.7.0"],
        fix_versions=["3.6.2", "3.7.1", "3.8.0"],
    )
    assert result == expected


def test_backport_does_not_fix_skipped_line():
    # Fixed in 3.6.2 and 3.8.0, never backported to 3.7.
    kwargs = {"affected_versions": ["3.6.0"], "fix_versions": ["3.6.2", "3.8.0"]}
    assert in_affected_range("3.6.2", **kwargs) == NOT_AFFECTED
    assert in_affected_range("3.7.0", **kwargs) == AFFECTED
    assert in_affected_range("3.7.5", **kwargs) == AFFECTED
    assert in_affected_range("3.8.0", **kwargs) == NOT_AFFECTED


def test_fix_order_does_not_matter():
    a = in_affected_range("3.7.0", ["3.5.0"], ["3.8.0", "3.6.2", "3.7.1"])
    b = in_affected_range("3.7.0", ["3.5.0"], ["3.6.2", "3.7.1", "3.8.0"])
    assert a == b == AFFECTED


def test_trap_versions_in_range():
    # 3.10.0 is after the 3.9.0 fix; lexical comparison would call it affected.
    assert in_affected_range("3.10.0", ["3.8.0"], ["3.9.0"]) == NOT_AFFECTED
    # 2.8.10 is after the 2.8.9 backport.
    assert in_affected_range("2.8.10", ["2.8.0"], ["2.8.9", "3.0.0"]) == NOT_AFFECTED
    assert in_affected_range("2.8.8", ["2.8.0"], ["2.8.9", "3.0.0"]) == AFFECTED


def test_pre_one_zero_release_lines():
    # 0.10.1 and 0.10.2 are separate release lines.
    kwargs = {"affected_versions": ["0.10.1.0"], "fix_versions": ["0.10.1.1", "0.10.2.0"]}
    assert in_affected_range("0.10.1.0", **kwargs) == AFFECTED
    assert in_affected_range("0.10.1.1", **kwargs) == NOT_AFFECTED
    assert in_affected_range("0.10.2.0", **kwargs) == NOT_AFFECTED
    assert in_affected_range("0.11.0.0", **kwargs) == NOT_AFFECTED
    assert in_affected_range("0.10.0.1", **kwargs) == NOT_AFFECTED


def test_crosses_zero_to_one():
    kwargs = {"affected_versions": ["0.11.0.0"], "fix_versions": ["0.11.0.2", "1.0.1"]}
    assert in_affected_range("0.11.0.1", **kwargs) == AFFECTED
    assert in_affected_range("0.11.0.2", **kwargs) == NOT_AFFECTED
    assert in_affected_range("1.0.0", **kwargs) == AFFECTED
    assert in_affected_range("1.0.1", **kwargs) == NOT_AFFECTED
    assert in_affected_range("2.0.0", **kwargs) == NOT_AFFECTED


def test_explicit_affected_overrides_inferred_fix():
    # JIRA says 3.9.0 is affected even though the only fix listed is on an older line.
    # Explicit evidence wins over the "later lines inherit the fix" inference.
    assert in_affected_range("3.9.0", ["3.9.0"], ["3.8.1"]) == AFFECTED
    assert in_affected_range("3.9.1", ["3.9.0"], ["3.8.1"]) == NOT_AFFECTED


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("2.3.1", NOT_AFFECTED),  # before the bug
        ("2.4.0", NOT_AFFECTED),  # found and fixed before 2.4.0 shipped
        ("2.4.1", NOT_AFFECTED),
        ("2.5.0", NOT_AFFECTED),
    ],
)
def test_found_and_fixed_in_same_release(version, expected):
    # JIRA lists the version as both affected and fixed: the bug only existed in unreleased
    # code, so no release is affected.
    assert in_affected_range(version, ["2.4.0"], ["2.4.0"]) == expected


def test_same_release_fix_with_earlier_affected_versions():
    # Reported on 2.3.0, also seen in 2.4.0 pre-release builds, fixed before 2.4.0 shipped.
    kwargs = {"affected_versions": ["2.3.0", "2.4.0"], "fix_versions": ["2.3.1", "2.4.0"]}
    assert in_affected_range("2.3.0", **kwargs) == AFFECTED
    assert in_affected_range("2.3.1", **kwargs) == NOT_AFFECTED
    assert in_affected_range("2.4.0", **kwargs) == NOT_AFFECTED


def test_explicit_affected_matches_padded_forms():
    assert in_affected_range("3.9.0", ["3.9"], ["3.8.1"]) == AFFECTED


def test_unknown_when_no_affected_versions_and_not_fixed():
    assert in_affected_range("3.7.0", [], ["3.8.0"]) == UNKNOWN
    assert in_affected_range("3.7.0", [], []) == UNKNOWN


def test_fixed_even_without_affected_versions():
    assert in_affected_range("3.8.0", [], ["3.8.0"]) == NOT_AFFECTED
    assert in_affected_range("3.9.0", [], ["3.8.0"]) == NOT_AFFECTED


def test_accepts_version_instances():
    v = parse_version("3.7.0")
    assert in_affected_range(v, [parse_version("3.6.0")], [parse_version("3.8.0")]) == AFFECTED


def test_accepts_tuples():
    assert in_affected_range("3.7.0", ("3.6.0",), ("3.8.0",)) == AFFECTED


def test_range_rejects_invalid_versions():
    with pytest.raises(VersionParseError):
        in_affected_range("latest", ["3.6.0"], ["3.8.0"])
    with pytest.raises(VersionParseError):
        in_affected_range("3.7.0", ["3.6.0"], ["future"])
    with pytest.raises(VersionParseError):
        in_affected_range("3.7.0", ["nope"], ["3.8.0"])


def test_applicability_values_are_stable_strings():
    # These values end up in the database and in Langfuse scores.
    assert AFFECTED == "affected"
    assert NOT_AFFECTED == "not_affected"
    assert UNKNOWN == "unknown"


def test_version_is_hashable_and_immutable():
    v = parse_version("3.9.0")
    assert {v, parse_version("3.9")} == {v}
    with pytest.raises(AttributeError):
        v.release = (4, 0, 0)  # type: ignore[misc]


def test_version_repr():
    assert repr(parse_version("3.7.0-rc1")) == "Version('3.7.0-rc1')"


def test_version_type():
    assert isinstance(parse_version("3.9.0"), Version)
