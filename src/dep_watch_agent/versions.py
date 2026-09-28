"""Version parsing and comparison for Kafka releases.

This is the only place in the codebase where versions are compared. Everything else,
including the LangChain tools the agent calls, goes through these functions. Never compare
version strings directly and never ask the LLM to do it.

Kafka version scheme:

- Before 1.0, four numeric parts: ``0.10.2.1`` is patch 1 of the ``0.10.2`` release line.
- From 1.0 on, three numeric parts: ``3.7.1`` is patch 1 of the ``3.7`` release line.
- Shorter forms are padded with zeros, so ``3.7 == 3.7.0``.
- Optional pre-release tag: ``3.7.0-rc1``, ``3.7.0-SNAPSHOT``. A pre-release sorts before
  its release: ``3.6.2 < 3.7.0-rc0 < 3.7.0-rc1 < 3.7.0``.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from functools import total_ordering

# Lowest to highest. A final release ranks above every pre-release tag.
_PRE_RELEASE_RANK = {"snapshot": 0, "alpha": 1, "beta": 2, "rc": 3}
_RELEASE_RANK = len(_PRE_RELEASE_RANK)

_VERSION_RE = re.compile(
    r"v?(?P<release>\d+(?:\.\d+)+)"
    r"(?:[-.]?(?P<tag>alpha|beta|rc|snapshot)(?:[-.]?(?P<num>\d+))?)?",
    re.IGNORECASE,
)


class VersionParseError(ValueError):
    """Raised when a string is not a valid Kafka version."""


class Applicability(StrEnum):
    AFFECTED = "affected"
    NOT_AFFECTED = "not_affected"
    UNKNOWN = "unknown"


@total_ordering
@dataclass(frozen=True, repr=False)
class Version:
    release: tuple[int, ...]
    pre: tuple[str, int] | None = None
    raw: str = field(default="", compare=False)

    @property
    def line(self) -> tuple[int, ...]:
        """Release line this version belongs to: ``3.7.1 -> (3, 7)``, ``0.10.2.1 -> (0, 10, 2)``."""
        return self.release[:-1]

    @property
    def is_prerelease(self) -> bool:
        return self.pre is not None

    def _key(self) -> tuple[tuple[int, ...], int, int]:
        if self.pre is None:
            return self.release, _RELEASE_RANK, 0
        tag, num = self.pre
        return self.release, _PRE_RELEASE_RANK[tag], num

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._key() < other._key()

    def __str__(self) -> str:
        return self.raw

    def __repr__(self) -> str:
        return f"Version({self.raw!r})"


def parse_version(value: str | Version) -> Version:
    """Parse a Kafka version string. Raises ``VersionParseError`` rather than guessing."""
    if isinstance(value, Version):
        return value
    if not isinstance(value, str):
        raise VersionParseError(f"expected a version string, got {type(value).__name__}")

    raw = value.strip()
    match = _VERSION_RE.fullmatch(raw)
    if match is None:
        raise VersionParseError(f"not a valid version: {value!r}")

    parts = tuple(int(p) for p in match["release"].split("."))
    scheme_length = 4 if parts[0] == 0 else 3
    if len(parts) > scheme_length:
        raise VersionParseError(
            f"too many parts for a {parts[0]}.x version (max {scheme_length}): {value!r}"
        )
    release = parts + (0,) * (scheme_length - len(parts))

    pre = None
    if match["tag"] is not None:
        pre = (match["tag"].lower(), int(match["num"] or 0))

    return Version(release=release, pre=pre, raw=raw)


def compare_versions(a: str | Version, b: str | Version) -> int:
    """Return -1 if ``a < b``, 0 if equal, 1 if ``a > b``."""
    va, vb = parse_version(a), parse_version(b)
    return (va > vb) - (va < vb)


def in_affected_range(
    version: str | Version,
    affected_versions: Iterable[str | Version],
    fix_versions: Iterable[str | Version],
) -> Applicability:
    """Decide whether ``version`` has the bug, given JIRA's affects and fix versions.

    Rules, in order:

    1. ``version`` listed in ``affected_versions`` and not in ``fix_versions``: affected.
       Explicit evidence wins over the inference in rule 2. A version listed as both means the
       bug was found and fixed during that release's development, so the release itself
       shipped with the fix (rule 2 applies). 28% of fixed Kafka bugs look like this.
    2. ``version`` contains a fix: not affected. A fix covers later patches on its own release
       line (a 3.7.1 fix covers 3.7.2), and the highest fix version is assumed to be on trunk,
       so it also covers every version above it. Lines between fixes without their own fix
       version are not covered: fixed in 3.6.2 and 3.8.0 leaves 3.7.x affected.
    3. No affected versions recorded: unknown, since there is no evidence of when the bug
       started.
    4. ``version`` below the earliest affected version: not affected. JIRA's earliest affected
       version is taken as the start of the bug. The bug may be older than what the reporter
       saw, which is a known limitation of this rule.
    5. Otherwise: affected.
    """
    target = parse_version(version)
    affected = [parse_version(v) for v in affected_versions]
    fixes = [parse_version(v) for v in fix_versions]

    if target in affected and target not in fixes:
        return Applicability.AFFECTED
    if _contains_fix(target, fixes):
        return Applicability.NOT_AFFECTED
    if not affected:
        return Applicability.UNKNOWN
    if target < min(affected):
        return Applicability.NOT_AFFECTED
    return Applicability.AFFECTED


def _contains_fix(target: Version, fixes: list[Version]) -> bool:
    if not fixes:
        return False
    if any(fix.line == target.line and target >= fix for fix in fixes):
        return True
    return target >= max(fixes)
