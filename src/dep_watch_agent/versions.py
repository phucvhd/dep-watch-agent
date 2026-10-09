"""Version parsing and comparison for upstream releases.

This is the only place in the codebase where versions are compared. Everything else,
including the LangChain tools the agent calls, goes through these functions. Never compare
version strings directly and never ask the LLM to do it.

A ``VersionScheme`` says how many numeric parts a dependency's releases have; each dependency
names its own (``dependencies.py``). Every scheme shares the rest:

- Shorter forms are padded with zeros, so ``3.7 == 3.7.0``. A padded form names a release
  line, not a release (``VersionScheme.is_release``).
- The last part is the patch: ``3.7.1`` is patch 1 of the ``3.7`` release line.
- Optional pre-release tag: ``3.7.0-rc1``, ``3.7.0-SNAPSHOT``, Spark's ``4.0.0-preview2``. A
  pre-release sorts before its release: ``3.6.2 < 3.7.0-rc0 < 3.7.0-rc1 < 3.7.0``, and a
  preview before the release candidates: ``4.0.0-preview2 < 4.0.0-rc1``.

Kafka's scheme (``KAFKA``): four parts before 1.0 (``0.10.2.1`` is patch 1 of the ``0.10.2``
line), three from 1.0 on. Its first releases were written shorter, and JIRA keeps those names:
``0.6`` and ``0.7``, then ``0.7.1`` to ``0.8.1``, then ``0.8.1.1``; four parts only from
``0.8.2.0``. Those are on ``x.y`` lines (``0.8.1`` and ``0.8.1.1`` patch the ``0.8`` line),
and are padded to four parts like every 0.x version, so they compare correctly.
``THREE_PART``: three parts throughout (Spark's ``0.9.1``).

Versions are only compared within one scheme: a dependency's versions with each other.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from functools import total_ordering

# Lowest to highest. A final release ranks above every pre-release tag.
_PRE_RELEASE_RANK = {"snapshot": 0, "alpha": 1, "beta": 2, "preview": 3, "rc": 4}
_RELEASE_RANK = len(_PRE_RELEASE_RANK)

_VERSION_RE = re.compile(
    r"v?(?P<release>\d+(?:\.\d+)+)"
    r"(?:[-.]?(?P<tag>alpha|beta|preview|rc|snapshot)(?:[-.]?(?P<num>\d+))?)?",
    re.IGNORECASE,
)


class VersionParseError(ValueError):
    """Raised when a string is not a valid version in the scheme asked for."""


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
    # Parts naming the release line, when the scheme says it isn't all but the last (an early
    # release: Kafka's 0.7.2 and 0.8.1.1 are on the 0.7 and 0.8 lines).
    line_parts: int | None = field(default=None, compare=False)

    @property
    def line(self) -> tuple[int, ...]:
        """Release line this version belongs to: ``3.7.1 -> (3, 7)``, ``0.10.2.1 -> (0, 10, 2)``."""
        if self.line_parts is not None:
            return self.release[: self.line_parts]
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


@dataclass(frozen=True)
class VersionScheme:
    """How a dependency numbers its releases: the parts of a release, before and from 1.0.

    ``early`` lists releases written with fewer parts, oldest first, as ``(below, parts)``: a
    version below ``below`` is a release when written with at least ``parts`` parts.
    """

    name: str
    parts: int = 3
    parts_before_1: int = 3
    early: tuple[tuple[tuple[int, ...], int], ...] = ()

    def _early_parts(self, release: tuple[int, ...]) -> int | None:
        return next((parts for below, parts in self.early if release < below), None)

    def parse(self, value: str | Version) -> Version:
        """Parse a version string. Raises ``VersionParseError`` rather than guessing."""
        if isinstance(value, Version):
            return value
        if not isinstance(value, str):
            raise VersionParseError(f"expected a version string, got {type(value).__name__}")

        raw = value.strip()
        match = _VERSION_RE.fullmatch(raw)
        if match is None:
            raise VersionParseError(f"not a valid version: {value!r}")

        parts = tuple(int(p) for p in match["release"].split("."))
        length = self.parts_before_1 if parts[0] == 0 else self.parts
        if len(parts) > length:
            raise VersionParseError(
                f"too many parts for a {parts[0]}.x {self.name} version (max {length}): {value!r}"
            )
        release = parts + (0,) * (length - len(parts))

        pre = None
        if match["tag"] is not None:
            pre = (match["tag"].lower(), int(match["num"] or 0))

        # Early releases are on x.y lines, as releases from 1.0 are: 0.8.1.1 patches the 0.8 line.
        line_parts = self.parts - 1 if self._early_parts(release) is not None else None
        return Version(release=release, pre=pre, raw=raw, line_parts=line_parts)

    def is_release(self, value: str) -> bool:
        """True for a specific release (``3.7.0``), false for a line (``3.7``) or a string that
        isn't a version at all."""
        try:
            parsed = self.parse(value)
        except VersionParseError:
            return False
        given = len(value.strip().lstrip("vV").split("-")[0].split("."))
        early = self._early_parts(parsed.release)
        if early is not None:
            return given >= early
        return given == len(parsed.release)


KAFKA = VersionScheme("Kafka", parts=3, parts_before_1=4, early=(((0, 7, 1), 2), ((0, 8, 2), 3)))
THREE_PART = VersionScheme("three-part")


def parse_version(value: str | Version, scheme: VersionScheme = KAFKA) -> Version:
    """``scheme.parse``. The default is Kafka's, the scheme of the eval's ground truth; code that
    answers for a dependency passes that dependency's scheme."""
    return scheme.parse(value)


def compare_versions(a: str | Version, b: str | Version, scheme: VersionScheme = KAFKA) -> int:
    """Return -1 if ``a < b``, 0 if equal, 1 if ``a > b``."""
    va, vb = scheme.parse(a), scheme.parse(b)
    return (va > vb) - (va < vb)


def in_affected_range(
    version: str | Version,
    affected_versions: Iterable[str | Version],
    fix_versions: Iterable[str | Version],
    scheme: VersionScheme = KAFKA,
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
    target = scheme.parse(version)
    affected = [scheme.parse(v) for v in affected_versions]
    fixes = [scheme.parse(v) for v in fix_versions]

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
