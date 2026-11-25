"""Uncertainty and paired comparison for eval runs.

The two configs of an issue are answered from one reading of it, so they are not independent:
resampling is by issue (a cluster bootstrap), never by case.

- ``bootstrap_intervals``: a percentile 95% interval for every rate metric of one run.
- ``compare``: two runs on the same cases. McNemar's exact test on the cases one run gets right
  and the other wrong, and a paired bootstrap interval for each metric's difference (a - b),
  resampling the same issues for both runs.
"""

import math
import random
from collections import defaultdict
from typing import Any

from dep_watch_agent.eval.metrics import RATE_METRICS, CaseResult, compute_metrics

DEFAULT_REPS = 1000
DEFAULT_SEED = 20261125


def bootstrap_intervals(
    results: list[CaseResult],
    *,
    reps: int = DEFAULT_REPS,
    seed: int = DEFAULT_SEED,
    level: float = 0.95,
) -> dict[str, list[float] | None]:
    """``{metric: [low, high]}`` for every rate metric; None for a metric that is undefined in
    too many resamples (more than half) to have an interval."""
    groups = _by_issue(results)
    keys = sorted(groups)
    rng = random.Random(seed)
    samples: dict[str, list[float]] = defaultdict(list)
    for _ in range(reps):
        drawn = [r for key in rng.choices(keys, k=len(keys)) for r in groups[key]]
        metrics = compute_metrics(drawn)
        for name in RATE_METRICS:
            if metrics[name] is not None:
                samples[name].append(metrics[name])
    return {name: _percentiles(samples[name], reps, level) for name in RATE_METRICS}


def compare(
    a: list[CaseResult],
    b: list[CaseResult],
    *,
    reps: int = DEFAULT_REPS,
    seed: int = DEFAULT_SEED,
    level: float = 0.95,
) -> dict[str, Any]:
    """Run ``a`` against run ``b`` on the cases both answered.

    ``mcnemar``: ``a_only`` cases only ``a`` got right, ``b_only`` only ``b``, and the exact
    two-sided p-value. ``difference``: per metric, ``a - b`` on all shared cases and its paired
    bootstrap interval.
    """
    by_id_b = {r.case_id: r for r in b}
    pairs = [(r, by_id_b[r.case_id]) for r in a if r.case_id in by_id_b]
    if not pairs:
        raise ValueError("the runs share no cases")
    shared_a = [x for x, _ in pairs]
    shared_b = [y for _, y in pairs]

    a_only = sum(x.correct and not y.correct for x, y in pairs)
    b_only = sum(y.correct and not x.correct for x, y in pairs)

    groups: dict[str, list[tuple[CaseResult, CaseResult]]] = defaultdict(list)
    for x, y in pairs:
        groups[x.issue_key].append((x, y))
    keys = sorted(groups)
    rng = random.Random(seed)
    samples: dict[str, list[float]] = defaultdict(list)
    for _ in range(reps):
        drawn = [pair for key in rng.choices(keys, k=len(keys)) for pair in groups[key]]
        ma = compute_metrics([x for x, _ in drawn])
        mb = compute_metrics([y for _, y in drawn])
        for name in RATE_METRICS:
            if ma[name] is not None and mb[name] is not None:
                samples[name].append(ma[name] - mb[name])

    full_a, full_b = compute_metrics(shared_a), compute_metrics(shared_b)
    difference = {}
    for name in RATE_METRICS:
        delta = (
            None if full_a[name] is None or full_b[name] is None else full_a[name] - full_b[name]
        )
        difference[name] = {
            "a": full_a[name],
            "b": full_b[name],
            "delta": delta,
            "ci95": _percentiles(samples[name], reps, level),
        }
    return {
        "cases": len(pairs),
        "issues": len(keys),
        "mcnemar": {"a_only": a_only, "b_only": b_only, "p_value": mcnemar_exact(a_only, b_only)},
        "difference": difference,
    }


def mcnemar_exact(a_only: int, b_only: int) -> float:
    """Exact two-sided McNemar p-value: under no difference, each discordant case is equally
    likely to favor either run, so the smaller count is Binomial(a_only + b_only, 1/2)."""
    n = a_only + b_only
    if n == 0:
        return 1.0
    k = min(a_only, b_only)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def _by_issue(results: list[CaseResult]) -> dict[str, list[CaseResult]]:
    groups: dict[str, list[CaseResult]] = defaultdict(list)
    for r in results:
        groups[r.issue_key].append(r)
    return groups


def _percentiles(values: list[float], reps: int, level: float) -> list[float] | None:
    if len(values) * 2 < reps:
        return None
    values = sorted(values)
    tail = (1 - level) / 2

    def at(q: float) -> float:
        return values[min(len(values) - 1, max(0, int(q * len(values))))]

    return [at(tail), at(1 - tail)]
