"""Pick the issues that make up the ground-truth set.

Candidates are fixed bugs with both affected and fix versions in JIRA. The sample is
stratified on three properties so the set isn't dominated by easy cases:

- era: the newest fix version's major line (legacy <2.0, 2.x, 3.x+)
- backport: whether the fix landed on more than one release line
- mentions_version: whether the issue text names any known Kafka version at all

Sampling is deterministic for a given seed and candidate list. The result is committed to git,
so later changes to the database don't change an existing dataset.
"""

import random
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from dep_watch_agent.orm import JiraIssueRow, JiraVersionRow
from dep_watch_agent.versions import Version, VersionParseError, parse_version

JIRA_BROWSE_URL = "https://issues.apache.org/jira/browse/"

# Mirrors of GitHub PR review threads: half of all comment text, mostly code review noise.
EXCLUDED_COMMENT_AUTHORS = frozenset({"ASF GitHub Bot"})

DEFAULT_MAX_TEXT_CHARS = 40_000

# v1 (fix versions masked): backports matter because the fix side must come from the text.
STRATA_V1: dict[str, dict[object, float]] = {
    "era": {"legacy": 0.10, "2.x": 0.35, "3.x+": 0.55},
    "backport": {True: 0.30, False: 0.70},
    "mentions_version": {True: 0.50, False: 0.50},
}

# v2 (fix versions given): what the text must supply is where the bug starts. Only ~13% of
# issues say so, so that half is oversampled.
STRATA_V2: dict[str, dict[object, float]] = {
    "era": {"legacy": 0.10, "2.x": 0.35, "3.x+": 0.55},
    "start_language": {True: 0.50, False: 0.50},
    "mentions_version": {True: 0.50, False: 0.50},
}

DEFAULT_STRATA = STRATA_V2

_V = r"v?\d+\.\d+(?:\.\d+){0,2}"
# Language about where a bug starts or where it is absent. A sampling hint, not evidence.
START_LANGUAGE = re.compile(
    rf"(?:introduced\s+(?:in|by|with|since|as of)|regression\s+(?:in|since|from|introduced)|"
    rf"\bsince\s+(?:kafka\s+|version\s+|apache kafka\s+)?{_V}|"
    rf"works?\s+(?:fine|well|ok|correctly)?\s*(?:on|in|with)\s+(?:kafka\s+)?{_V}|"
    rf"did(?:n't| not)\s+(?:happen|occur|reproduce|see)|"
    rf"not\s+(?:affected|present|reproducible)\s+(?:in|on)|"
    rf"\b(?:prior to|before|until)\s+(?:kafka\s+|version\s+)?{_V}|"
    rf"started\s+(?:in|with|after|since))",
    re.IGNORECASE,
)

_VERSION_IN_TEXT = re.compile(r"(?<![\w.])v?\d+\.\d+(?:\.\d+){0,2}(?![\w.]*\d)")


@dataclass(frozen=True)
class IssueCandidate:
    key: str
    summary: str
    description: str
    comments: list[str]
    affects_versions: list[str]
    fix_versions: list[str]
    resolved_at: datetime | None
    versions_in_text: list[str]
    has_start_language: bool = False

    @property
    def url(self) -> str:
        return JIRA_BROWSE_URL + self.key

    @property
    def text_chars(self) -> int:
        return len(self.summary) + len(self.description) + sum(len(c) for c in self.comments)

    @property
    def strata(self) -> dict[str, object]:
        fixes = [parse_version(v) for v in self.fix_versions]
        newest = max(fixes)
        era = "legacy" if newest.release[0] < 2 else "2.x" if newest.release[0] == 2 else "3.x+"
        return {
            "era": era,
            "backport": len({f.line for f in fixes}) > 1,
            "mentions_version": bool(self.versions_in_text),
            "start_language": self.has_start_language,
        }


def known_versions(session: Session, project: str) -> set[Version]:
    """Every parseable version defined in the JIRA project, released or not."""
    names = session.scalars(select(JiraVersionRow.name).where(JiraVersionRow.project == project))
    known = set()
    for name in names:
        try:
            known.add(parse_version(name))
        except VersionParseError:
            continue
    return known


def released_versions(session: Session, project: str) -> list[Version]:
    """Released, non-pre-release versions, oldest first. Configs are drawn from these."""
    names = session.scalars(
        select(JiraVersionRow.name).where(
            JiraVersionRow.project == project, JiraVersionRow.released.is_(True)
        )
    )
    releases = []
    for name in names:
        try:
            v = parse_version(name)
        except VersionParseError:
            continue
        if not v.is_prerelease:
            releases.append(v)
    return sorted(releases)


def find_known_versions(text: str, known: set[Version]) -> list[str]:
    """Version-like strings in ``text`` that name a known Kafka version, in order of appearance.

    Only a labeling hint: "3.4" may be ZooKeeper, "2.12" is usually Scala and is dropped because
    no Kafka 2.12 exists.
    """
    found: list[str] = []
    for match in _VERSION_IN_TEXT.finditer(text):
        raw = match.group()
        try:
            v = parse_version(raw)
        except VersionParseError:
            continue
        if v in known and raw not in found:
            found.append(raw)
    return found


def load_candidates(
    session: Session,
    project: str = "KAFKA",
    *,
    max_text_chars: int = DEFAULT_MAX_TEXT_CHARS,
) -> list[IssueCandidate]:
    """Fixed bugs with affected and fix versions, all parseable, sorted by key."""
    known = known_versions(session, project)
    issues = session.scalars(
        select(JiraIssueRow)
        .where(
            JiraIssueRow.project == project,
            JiraIssueRow.issue_type == "Bug",
            JiraIssueRow.resolution == "Fixed",
        )
        .options(
            selectinload(JiraIssueRow.versions),
            selectinload(JiraIssueRow.comments),
        )
    )

    candidates = []
    for issue in issues:
        affects = sorted(v.name for v in issue.versions if v.kind == "affects")
        fixes = sorted(v.name for v in issue.versions if v.kind == "fix")
        if not affects or not fixes or not _all_parse(affects + fixes):
            continue
        comments = [
            c.body
            for c in issue.comments
            if c.author not in EXCLUDED_COMMENT_AUTHORS and c.body.strip()
        ]
        description = issue.description or ""
        text = "\n".join([issue.summary, description, *comments])
        candidate = IssueCandidate(
            key=issue.key,
            summary=issue.summary,
            description=description,
            comments=comments,
            affects_versions=affects,
            fix_versions=fixes,
            resolved_at=issue.resolved_at,
            versions_in_text=find_known_versions(text, known),
            has_start_language=bool(START_LANGUAGE.search(text)),
        )
        if candidate.text_chars <= max_text_chars:
            candidates.append(candidate)
    return sorted(candidates, key=lambda c: _key_sort(c.key))


def stratified_sample(
    candidates: list[IssueCandidate],
    size: int,
    *,
    seed: int,
    strata: dict[str, dict[object, float]] = DEFAULT_STRATA,
) -> list[IssueCandidate]:
    """Pick ``size`` candidates, filling each stratum's quota before relaxing.

    Candidates are shuffled with ``seed`` and taken greedily while every dimension's bucket is
    under quota. If some buckets can't be filled, the remainder is topped up in shuffled order.
    """
    if size > len(candidates):
        raise ValueError(f"asked for {size} issues but only {len(candidates)} candidates exist")

    quotas = {dim: _quota_counts(fractions, size) for dim, fractions in strata.items()}
    pool = list(candidates)
    random.Random(seed).shuffle(pool)

    chosen: list[IssueCandidate] = []
    filled: dict[str, Counter] = {dim: Counter() for dim in strata}
    for candidate in pool:
        if len(chosen) == size:
            break
        props = candidate.strata
        if all(filled[dim][props[dim]] < quotas[dim].get(props[dim], 0) for dim in strata):
            chosen.append(candidate)
            for dim in strata:
                filled[dim][props[dim]] += 1

    if len(chosen) < size:
        picked = {c.key for c in chosen}
        chosen.extend([c for c in pool if c.key not in picked][: size - len(chosen)])

    return sorted(chosen, key=lambda c: _key_sort(c.key))


def strata_counts(
    sample: list[IssueCandidate], dims: Iterable[str] = tuple(DEFAULT_STRATA)
) -> dict[str, dict[str, int]]:
    dims = set(dims)
    counts: dict[str, Counter] = {}
    for candidate in sample:
        for dim, value in candidate.strata.items():
            if dim in dims:
                counts.setdefault(dim, Counter())[str(value)] += 1
    return {dim: dict(sorted(c.items())) for dim, c in counts.items()}


def _quota_counts(fractions: dict[object, float], size: int) -> dict[object, int]:
    """Round fractions to counts that sum to ``size`` (largest remainder)."""
    raw = {bucket: f * size for bucket, f in fractions.items()}
    counts = {bucket: int(r) for bucket, r in raw.items()}
    leftover = size - sum(counts.values())
    for bucket in sorted(raw, key=lambda b: raw[b] - counts[b], reverse=True)[:leftover]:
        counts[bucket] += 1
    return counts


def _all_parse(names: list[str]) -> bool:
    try:
        for name in names:
            parse_version(name)
    except VersionParseError:
        return False
    return True


def _key_sort(key: str) -> tuple[str, int]:
    project, _, number = key.partition("-")
    return project, int(number) if number.isdigit() else 0
