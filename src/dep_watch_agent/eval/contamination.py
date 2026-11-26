"""Contamination split: open models are trained on public JIRA text, so a run is also scored
separately on the issues created before and after the model was released.

Issues created after the release can't have been in its training data; a system that does much
better on the older issues may be recalling them. The release date is the date the model's
weights were first published (its Hugging Face repository's creation date), an upper bound on
its training cutoff. ``DEP_WATCH_LLM_RELEASE_DATE`` (YYYY-MM-DD) overrides it, for a model not
listed here.

Issue creation dates are kept beside the dataset in ``issue_dates.json`` (``write_issue_dates``),
not in ``issues.jsonl``, which holds exactly what the model sees.
"""

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from dep_watch_agent.eval.metrics import CaseResult, compute_metrics

ISSUE_DATES_FILE = "issue_dates.json"

# Model id (as served, publisher optional) -> first publication of its weights on Hugging Face.
MODEL_RELEASES: dict[str, date] = {
    "qwen3-4b-2507": date(2025, 8, 5),  # Qwen/Qwen3-4B-Instruct-2507
    "qwen3-4b-instruct-2507": date(2025, 8, 5),
    "qwen3.5-9b": date(2026, 2, 27),  # Qwen/Qwen3.5-9B
    "gemma-4-e4b": date(2026, 3, 2),  # google/gemma-4-E4B-it
    "gemma-4-e4b-it": date(2026, 3, 2),
    "llama-3.1-8b-instruct": date(2024, 7, 18),  # meta-llama/Llama-3.1-8B-Instruct
    "meta-llama-3.1-8b-instruct": date(2024, 7, 18),
}


def model_release(model: str) -> date | None:
    override = os.environ.get("DEP_WATCH_LLM_RELEASE_DATE", "").strip()
    if override:
        return date.fromisoformat(override)
    name = model.split(";", 1)[0].rsplit("/", 1)[-1].lower()
    return MODEL_RELEASES.get(name)


def write_issue_dates(directory: Path, session: Session) -> int:
    """Write ``issue_dates.json`` for the dataset in ``directory`` from the synced issues.
    Returns how many issues got a date."""
    from dep_watch_agent.eval.dataset import load_dataset
    from dep_watch_agent.orm import JiraIssueRow

    dataset = load_dataset(directory)
    rows = session.execute(
        select(JiraIssueRow.key, JiraIssueRow.created_at).where(
            JiraIssueRow.key.in_(list(dataset.issues))
        )
    ).all()
    dates = {key: created.date().isoformat() for key, created in sorted(rows)}
    (directory / ISSUE_DATES_FILE).write_text(json.dumps(dates, indent=2) + "\n")
    return len(dates)


def read_issue_dates(directory: Path) -> dict[str, date] | None:
    path = directory / ISSUE_DATES_FILE
    if not path.is_file():
        return None
    return {k: date.fromisoformat(v) for k, v in json.loads(path.read_text()).items()}


def split(results: list[CaseResult], issue_dates: dict[str, date], release: date) -> dict[str, Any]:
    """Metrics on the cases of issues created before ``release`` and on or after it. Cases of
    issues without a date are counted in neither."""
    before = [
        r for r in results if r.issue_key in issue_dates and issue_dates[r.issue_key] < release
    ]
    after = [
        r for r in results if r.issue_key in issue_dates and issue_dates[r.issue_key] >= release
    ]
    return {
        "release": release.isoformat(),
        "before": {"issues": len({r.issue_key for r in before}), **compute_metrics(before)},
        "after": {"issues": len({r.issue_key for r in after}), **compute_metrics(after)},
    }
