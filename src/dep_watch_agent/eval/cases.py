"""Turn a sampled issue into eval cases: one affected config and one not-affected config.

The metadata answer comes from ``in_affected_range`` over JIRA's affects/fix versions, i.e.
the same rules the pipeline uses. Configs are always real released versions.

Negatives are chosen to be hard, because easy ones (a version years away from the bug) would
inflate every score. The kind is picked at random among those available, weighted towards the
first ones (``NEGATIVE_KIND_WEIGHTS``):

- ``fix_version``: the release that contains the fix
- ``later_patch``: a later patch on a line that got the fix, e.g. 3.7.2 when fixed in 3.7.1
- ``later_line``: the first release on a line newer than every fix
- ``before_affected``: the last release before the earliest affected version. Relies on JIRA's
  earliest affected version being where the bug started, the weakest of the rules.

Positives prefer versions JIRA lists as affected over versions inferred to be in range.
"""

import random
from dataclasses import dataclass

from dep_watch_agent.eval.sampling import IssueCandidate
from dep_watch_agent.versions import Applicability, Version, in_affected_range, parse_version

NEGATIVE_KIND_WEIGHTS = {
    "fix_version": 3,
    "later_patch": 2,
    "later_line": 1,
    "before_affected": 1,
}


@dataclass(frozen=True)
class Case:
    case_id: str
    issue_key: str
    version: str
    metadata_answer: str  # Applicability.AFFECTED or Applicability.NOT_AFFECTED
    basis: str  # listed_affected | inferred_affected | one of NEGATIVE_KIND_WEIGHTS
    affects_versions: list[str]
    fix_versions: list[str]


def make_cases(
    candidate: IssueCandidate, releases: list[Version], *, seed: int, design: str = "v2"
) -> tuple[Case, Case] | None:
    """Return (affected case, not-affected case), or None if either can't be built.

    ``v1``: negatives of every kind (fix versions are masked, so the fix side is tested too).
    ``v2``: negatives are always ``before_affected``. Fix versions are given to the system, so
    fix-side configs are decided by code and aren't worth a case.
    """
    rng = random.Random(f"{seed}:{candidate.key}")
    affects = [parse_version(v) for v in candidate.affects_versions]
    fixes = [parse_version(v) for v in candidate.fix_versions]

    positive = _pick_positive(releases, affects, fixes, rng)
    kinds = None if design == "v1" else {"before_affected"}
    negative = _pick_negative(releases, affects, fixes, rng, kinds=kinds)
    if positive is None or negative is None:
        return None

    def case(version: Version, answer: Applicability, basis: str) -> Case:
        return Case(
            case_id=f"{candidate.key}@{version}",
            issue_key=candidate.key,
            version=str(version),
            metadata_answer=answer.value,
            basis=basis,
            affects_versions=candidate.affects_versions,
            fix_versions=candidate.fix_versions,
        )

    return (
        case(positive[0], Applicability.AFFECTED, positive[1]),
        case(negative[0], Applicability.NOT_AFFECTED, negative[1]),
    )


def _pick_positive(
    releases: list[Version], affects: list[Version], fixes: list[Version], rng: random.Random
) -> tuple[Version, str] | None:
    affected = [
        r for r in releases if in_affected_range(r, affects, fixes) is Applicability.AFFECTED
    ]
    listed = [r for r in affected if r in affects]
    if listed:
        return rng.choice(listed), "listed_affected"
    if affected:
        return rng.choice(affected), "inferred_affected"
    return None


def _pick_negative(
    releases: list[Version],
    affects: list[Version],
    fixes: list[Version],
    rng: random.Random,
    *,
    kinds: set[str] | None = None,
) -> tuple[Version, str] | None:
    safe = [
        r for r in releases if in_affected_range(r, affects, fixes) is Applicability.NOT_AFFECTED
    ]
    newest_fix = max(fixes)
    fix_lines = {f.line for f in fixes}

    options: dict[str, Version] = {}
    fix_releases = [r for r in safe if r in fixes]
    if fix_releases:
        options["fix_version"] = rng.choice(fix_releases)
    later_patches = [
        r for r in safe if r not in fixes and any(r.line == f.line and r > f for f in fixes)
    ]
    if later_patches:
        options["later_patch"] = min(later_patches)
    later_lines = [r for r in safe if r > newest_fix and r.line not in fix_lines]
    if later_lines:
        options["later_line"] = min(later_lines)
    # Before the bug, and not merely a backport of the fix to an older line: that case would be
    # decided by the fix versions alone and wouldn't test whether the bug had started.
    before = [
        r
        for r in safe
        if r < min(affects) and in_affected_range(r, [], fixes) is not Applicability.NOT_AFFECTED
    ]
    if before:
        options["before_affected"] = max(before)

    if kinds is not None:
        options = {k: v for k, v in options.items() if k in kinds}
    if not options:
        return None
    kinds = sorted(options)
    kind = rng.choices(kinds, weights=[NEGATIVE_KIND_WEIGHTS[k] for k in kinds])[0]
    return options[kind], kind
