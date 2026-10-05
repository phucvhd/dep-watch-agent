"""Builders for eval dataset tests."""

import csv

from dep_watch_agent.eval.cases import Case
from dep_watch_agent.eval.dataset import write_dataset
from dep_watch_agent.eval.sampling import IssueCandidate

MANIFEST = {"name": "test-set", "seed": 1}


def issue(key: str) -> IssueCandidate:
    return IssueCandidate(
        key=key,
        summary=f"{key} summary",
        description="Consumer hangs after upgrade to 3.7.0",
        comments=["Fixed in trunk and 3.7.1", "Backported to 3.7"],
        affects_versions=["3.7.0"],
        fix_versions=["3.7.1", "3.8.0"],
        resolved_at=None,
        versions_in_text=["3.7.0"],
    )


def cases_for(key: str) -> list[Case]:
    common = {"issue_key": key, "affects_versions": ["3.7.0"], "fix_versions": ["3.7.1", "3.8.0"]}
    return [
        Case(f"{key}@3.7.0", version="3.7.0", metadata_answer="affected",
             basis="listed_affected", **common),
        Case(f"{key}@3.7.1", version="3.7.1", metadata_answer="not_affected",
             basis="fix_version", **common),
    ]  # fmt: skip


def fill_labels(directory, answers: dict[str, str], notes: dict[str, str] | None = None):
    path = directory / "labels.csv"
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0])
    for row in rows:
        if row["case_id"] in answers:
            row["answerable_from_text"] = answers[row["case_id"]]
        row["notes"] = (notes or {}).get(row["case_id"], row["notes"])
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


ALL_YES = {
    "KAFKA-1@3.7.0": "yes",
    "KAFKA-1@3.7.1": "yes",
    "KAFKA-2@3.7.0": "yes",
    "KAFKA-2@3.7.1": "yes",
}


def write_test_dataset(directory):
    sample = [issue("KAFKA-1"), issue("KAFKA-2")]
    cases = cases_for("KAFKA-1") + cases_for("KAFKA-2")
    write_dataset(directory, MANIFEST, sample, cases)
    return directory
