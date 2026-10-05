"""Ground-truth dataset files, human labels, and upload to Langfuse.

A dataset is a directory committed to git::

    manifest.json   how it was sampled (seed, strata, counts)
    issues.jsonl    masked issue text: exactly what the model sees, no structured fields
    cases.jsonl     (issue, config version) pairs with the answer from JIRA metadata
    labels.csv      filled in by a person: can the answer be found in the text?
    review.md       the same text as issues.jsonl, formatted for reading while labeling

A case's expected answer is its metadata answer if the labeler marked it answerable from the
text, and ``insufficient_information`` otherwise.
"""

import csv
import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from sqlalchemy.orm import Session

from dep_watch_agent.eval.cases import Case, make_cases
from dep_watch_agent.eval.sampling import (
    DEFAULT_MAX_TEXT_CHARS,
    EXCLUDED_COMMENT_AUTHORS,
    STRATA_V1,
    STRATA_V2,
    IssueCandidate,
    load_candidates,
    released_versions,
    strata_counts,
    stratified_sample,
)
from dep_watch_agent.verdict import INSUFFICIENT_INFORMATION

ANSWERABLE_VALUES = ("yes", "no")

LABEL_FIELDS = [
    "case_id",
    "issue_key",
    "url",
    "version",
    "metadata_answer",
    "basis",
    "affects_versions",
    "fix_versions",
    "known_versions_in_text",
    "answerable_from_text",
    "notes",
]


DESIGNS = {
    "v1": "Text only; fix versions masked. Superseded: the text rarely names the fix release.",
    "v2": (
        "Fix versions given as structured input, as in production; affected versions masked. "
        "Negatives are configs before the bug starts, so the text must say where it starts."
    ),
}


class DatasetError(Exception):
    pass


def _design(manifest: dict[str, Any]) -> str:
    return manifest.get("design", {}).get("version", "v1")


@dataclass(frozen=True)
class Dataset:
    directory: Path
    manifest: dict[str, Any]
    issues: dict[str, dict[str, Any]]
    cases: list[Case]
    labels: dict[str, dict[str, str]]

    @property
    def name(self) -> str:
        return self.manifest["name"]


# --- sampling ----------------------------------------------------------------------------


def sample_dataset(
    session: Session,
    name: str,
    *,
    size: int,
    seed: int,
    project: str = "KAFKA",
    max_text_chars: int = DEFAULT_MAX_TEXT_CHARS,
    design: str = "v2",
    now: datetime | None = None,
) -> tuple[dict[str, Any], list[IssueCandidate], list[Case]]:
    """Sample issues and build their cases. Returns (manifest, sample, cases).

    ``design`` is ``v2`` (fix versions given to the system, see DESIGNS) or ``v1`` (text only).
    """
    if design not in DESIGNS:
        raise DatasetError(f"unknown design {design!r}; expected one of {sorted(DESIGNS)}")
    strata = STRATA_V2 if design == "v2" else STRATA_V1
    releases = released_versions(session, project)
    if not releases:
        raise DatasetError(f"no released {project} versions in the database; sync JIRA first")

    candidates = load_candidates(session, project, max_text_chars=max_text_chars)
    built = {c.key: make_cases(c, releases, seed=seed, design=design) for c in candidates}
    viable = [c for c in candidates if built[c.key] is not None]

    sample = stratified_sample(viable, size, seed=seed, strata=strata)
    cases = [case for c in sample for case in built[c.key]]
    manifest = {
        "name": name,
        "project": project,
        "seed": seed,
        "size": size,
        "design": {"version": design, "description": DESIGNS[design]},
        "created_at": (now or datetime.now(UTC)).isoformat(),
        "max_text_chars": max_text_chars,
        "excluded_comment_authors": sorted(EXCLUDED_COMMENT_AUTHORS),
        "candidates": len(candidates),
        "viable_candidates": len(viable),
        "strata_targets": {
            dim: {str(k): v for k, v in fractions.items()} for dim, fractions in strata.items()
        },
        "strata_counts": strata_counts(sample, strata),
        "case_basis_counts": dict(sorted(Counter(c.basis for c in cases).items())),
    }
    return manifest, sample, cases


# --- writing ----------------------------------------------------------------------------


def write_dataset(
    directory: Path,
    manifest: dict[str, Any],
    sample: list[IssueCandidate],
    cases: list[Case],
    *,
    force: bool = False,
) -> None:
    """Write a new dataset. Refuses to overwrite an existing one unless ``force``."""
    if directory.exists() and any(directory.iterdir()) and not force:
        raise DatasetError(
            f"{directory} already exists; it may contain labels. Use a new name or --force."
        )
    directory.mkdir(parents=True, exist_ok=True)

    by_key = {c.key: c for c in sample}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    given_fixes = _design(manifest) == "v2"
    _write_jsonl(directory / "issues.jsonl", (_issue_record(c, given_fixes) for c in sample))
    _write_jsonl(directory / "cases.jsonl", (asdict(c) for c in cases))

    with (directory / "labels.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LABEL_FIELDS)
        writer.writeheader()
        for case in cases:
            issue = by_key[case.issue_key]
            writer.writerow(
                {
                    "case_id": case.case_id,
                    "issue_key": case.issue_key,
                    "url": issue.url,
                    "version": case.version,
                    "metadata_answer": case.metadata_answer,
                    "basis": case.basis,
                    "affects_versions": " ".join(case.affects_versions),
                    "fix_versions": " ".join(case.fix_versions),
                    "known_versions_in_text": " ".join(issue.versions_in_text),
                    "answerable_from_text": "",
                    "notes": "",
                }
            )

    (directory / "review.md").write_text(_review_markdown(manifest, sample, cases))


def _issue_record(candidate: IssueCandidate, given_fixes: bool) -> dict[str, Any]:
    record = {
        "issue_key": candidate.key,
        "url": candidate.url,
        "summary": candidate.summary,
        "description": candidate.description,
        "comments": candidate.comments,
    }
    if given_fixes:
        record["fix_versions"] = candidate.fix_versions
    return record


def _review_markdown(
    manifest: dict[str, Any], sample: list[IssueCandidate], cases: list[Case]
) -> str:
    by_issue: dict[str, list[Case]] = {}
    for case in cases:
        by_issue.setdefault(case.issue_key, []).append(case)

    v2 = _design(manifest) == "v2"
    question = (
        [
            "The fix versions are GIVEN (the system sees them). For each case, decide whether",
            "the text below plus the given fix versions say enough to conclude the metadata",
            "answer for that config version: for `affected`, that the bug exists at or before",
            "the config and isn't fixed by it; for `not_affected` (`before_affected`), that the",
            'bug did not exist yet at the config ("introduced in", "works on"). "Seen on',
            '3.6.0" alone says nothing about 3.5.2.',
        ]
        if v2
        else [
            "For each case, decide whether the text below (and only this text) says enough to",
            "conclude the metadata answer for that config version.",
        ]
    )
    lines = [
        f"# {manifest['name']}: labeling review",
        "",
        *question,
        "",
        "Record `yes` or `no` in the `answerable_from_text` column of labels.csv, with a short",
        "note when it's borderline.",
        "",
    ]
    for issue in sample:
        lines += [f"## {issue.key}: {issue.summary}", "", issue.url, ""]
        if v2:
            lines.append(f"Given fix versions: {', '.join(issue.fix_versions)}")
            lines.append(
                f"JIRA affects (masked from the system): {', '.join(issue.affects_versions)}"
            )
        else:
            lines.append(
                f"JIRA metadata: affects {', '.join(issue.affects_versions)}; "
                f"fixed in {', '.join(issue.fix_versions)}"
            )
        lines.append("")
        for case in by_issue.get(issue.key, []):
            lines.append(
                f"- `{case.case_id}`: config {case.version}, metadata answer "
                f"**{case.metadata_answer}** ({case.basis})"
            )
        hint = ", ".join(issue.versions_in_text) or "none"
        lines += ["", f"Known Kafka versions mentioned in text: {hint}", ""]
        lines += ["### Description", "", "~~~~", issue.description or "(empty)", "~~~~", ""]
        if issue.comments:
            lines += [f"### Comments ({len(issue.comments)})", ""]
            for i, body in enumerate(issue.comments, 1):
                lines += [f"{i}.", "", "~~~~", body, "~~~~", ""]
        lines += ["---", ""]
    return "\n".join(lines)


# --- reading and validation ---------------------------------------------------------------


def load_dataset(directory: Path) -> Dataset:
    if not (directory / "manifest.json").exists():
        raise DatasetError(f"no dataset at {directory}")
    manifest = json.loads((directory / "manifest.json").read_text())
    issues = {r["issue_key"]: r for r in _read_jsonl(directory / "issues.jsonl")}
    cases = [Case(**r) for r in _read_jsonl(directory / "cases.jsonl")]
    with (directory / "labels.csv").open(newline="") as f:
        labels = {row["case_id"]: row for row in csv.DictReader(f)}
    return Dataset(directory, manifest, issues, cases, labels)


def label_problems(dataset: Dataset) -> list[str]:
    """Everything that stops the labels from being used. Empty means ready to upload."""
    problems = []
    case_ids = {c.case_id for c in dataset.cases}
    for case_id in sorted(set(dataset.labels) - case_ids):
        problems.append(f"{case_id}: in labels.csv but not a case")
    for case in dataset.cases:
        label = dataset.labels.get(case.case_id)
        if label is None:
            problems.append(f"{case.case_id}: missing from labels.csv")
            continue
        value = label.get("answerable_from_text", "").strip().lower()
        if not value:
            problems.append(f"{case.case_id}: not labeled")
        elif value not in ANSWERABLE_VALUES:
            problems.append(
                f"{case.case_id}: answerable_from_text must be yes or no, got {value!r}"
            )
    return problems


def label_progress(dataset: Dataset) -> tuple[int, int]:
    """(labeled cases, total cases)."""
    labeled = sum(
        1
        for c in dataset.cases
        if dataset.labels.get(c.case_id, {}).get("answerable_from_text", "").strip()
    )
    return labeled, len(dataset.cases)


def expected_answer(case: Case, label: dict[str, str]) -> str:
    answerable = label["answerable_from_text"].strip().lower() == "yes"
    return case.metadata_answer if answerable else INSUFFICIENT_INFORMATION


# --- Langfuse ------------------------------------------------------------------------------


class LangfuseDatasets(Protocol):
    def create_dataset(self, *, name: str, description: str | None, metadata: Any) -> Any: ...

    def create_dataset_item(
        self,
        *,
        dataset_name: str,
        id: str,
        input: Any,
        expected_output: Any,
        metadata: Any,
    ) -> Any: ...


def langfuse_items(dataset: Dataset) -> list[dict[str, Any]]:
    """Dataset items. ``input`` is all the model may see; answers stay in ``expected_output``
    and ``metadata``."""
    problems = label_problems(dataset)
    if problems:
        raise DatasetError(f"{len(problems)} labeling problem(s), first: {problems[0]}")

    items = []
    for case in dataset.cases:
        issue = dataset.issues[case.issue_key]
        label = dataset.labels[case.case_id]
        items.append(
            {
                "id": case.case_id,
                "input": {
                    "summary": issue["summary"],
                    "description": issue["description"],
                    "comments": issue["comments"],
                    **({"fix_versions": issue["fix_versions"]} if "fix_versions" in issue else {}),
                    "version": case.version,
                },
                "expected_output": {"answer": expected_answer(case, label)},
                "metadata": {
                    "issue_key": case.issue_key,
                    "url": issue["url"],
                    "metadata_answer": case.metadata_answer,
                    "basis": case.basis,
                    "affects_versions": case.affects_versions,
                    "fix_versions": case.fix_versions,
                    "answerable_from_text": label["answerable_from_text"].strip().lower(),
                    "notes": label.get("notes", ""),
                },
            }
        )
    return items


def upload(dataset: Dataset, client: LangfuseDatasets) -> int:
    """Create or update the Langfuse dataset. Items are keyed by case id, so re-uploading
    updates them instead of adding duplicates. Returns the number of items."""
    items = langfuse_items(dataset)
    client.create_dataset(
        name=dataset.name,
        description=DESIGNS[_design(dataset.manifest)],
        metadata={k: v for k, v in dataset.manifest.items() if k != "name"},
    )
    for item in items:
        client.create_dataset_item(dataset_name=dataset.name, **item)
    return len(items)


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    with path.open("w") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]
