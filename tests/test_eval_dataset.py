import csv
import json

import pytest

from dep_watch_agent.cli import main
from dep_watch_agent.eval.cases import Case
from dep_watch_agent.eval.dataset import (
    INSUFFICIENT_INFORMATION,
    DatasetError,
    expected_answer,
    label_problems,
    label_progress,
    langfuse_items,
    load_dataset,
    sample_dataset,
    upload,
    write_dataset,
)
from dep_watch_agent.eval.sampling import IssueCandidate
from dep_watch_agent.jira.models import parse_issue
from dep_watch_agent.jira.store import upsert_issue, upsert_versions
from tests.jira_factory import raw_comment, raw_issue

MANIFEST = {"name": "test-set", "seed": 1}


def issue(key: str) -> IssueCandidate:
    return IssueCandidate(
        key=key,
        summary=f"{key} summary",
        description="Consumer hangs after upgrade to 3.7.0",
        comments=["Fixed in trunk", "Backported to 3.7"],
        affects_versions=["3.7.0"],
        fix_versions=["3.7.1", "3.8.0"],
        resolved_at=None,
        versions_in_text=["3.7.0"],
    )


def cases_for(key: str) -> list[Case]:
    common = {"issue_key": key, "affects_versions": ["3.7.0"], "fix_versions": ["3.7.1", "3.8.0"]}
    return [
        Case(f"{key}@3.7.0", kafka_version="3.7.0", metadata_answer="affected",
             basis="listed_affected", **common),
        Case(f"{key}@3.7.1", kafka_version="3.7.1", metadata_answer="not_affected",
             basis="fix_version", **common),
    ]  # fmt: skip


@pytest.fixture
def written(tmp_path):
    directory = tmp_path / "test-set"
    sample = [issue("KAFKA-1"), issue("KAFKA-2")]
    cases = cases_for("KAFKA-1") + cases_for("KAFKA-2")
    write_dataset(directory, MANIFEST, sample, cases)
    return directory


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


# --- files ------------------------------------------------------------------------------


def test_writes_all_files(written):
    assert sorted(p.name for p in written.iterdir()) == [
        "cases.jsonl",
        "issues.jsonl",
        "labels.csv",
        "manifest.json",
        "review.md",
    ]


def test_issue_file_is_masked(written):
    # Only free text reaches the model: no versions, components or other structured fields.
    records = [json.loads(line) for line in (written / "issues.jsonl").read_text().splitlines()]
    assert {tuple(sorted(r)) for r in records} == {
        ("comments", "description", "issue_key", "summary", "url")
    }


def test_round_trip(written):
    ds = load_dataset(written)
    assert ds.name == "test-set"
    assert [c.case_id for c in ds.cases] == [
        "KAFKA-1@3.7.0",
        "KAFKA-1@3.7.1",
        "KAFKA-2@3.7.0",
        "KAFKA-2@3.7.1",
    ]
    assert ds.cases[0] == cases_for("KAFKA-1")[0]
    assert ds.issues["KAFKA-1"]["comments"] == ["Fixed in trunk", "Backported to 3.7"]


def test_labels_csv_prefilled_for_the_labeler(written):
    with (written / "labels.csv").open(newline="") as f:
        row = next(csv.DictReader(f))
    assert row["url"] == "https://issues.apache.org/jira/browse/KAFKA-1"
    assert row["fix_versions"] == "3.7.1 3.8.0"
    assert row["known_versions_in_text"] == "3.7.0"
    assert row["answerable_from_text"] == ""


def test_review_shows_exactly_the_model_text(written):
    review = (written / "review.md").read_text()
    assert "## KAFKA-1: KAFKA-1 summary" in review
    assert "Consumer hangs after upgrade to 3.7.0" in review
    assert "Backported to 3.7" in review
    assert "`KAFKA-1@3.7.1`: config 3.7.1, metadata answer **not_affected** (fix_version)" in review


def test_refuses_to_overwrite(written):
    with pytest.raises(DatasetError, match="already exists"):
        write_dataset(written, MANIFEST, [issue("KAFKA-1")], cases_for("KAFKA-1"))
    write_dataset(written, MANIFEST, [issue("KAFKA-1")], cases_for("KAFKA-1"), force=True)
    assert len(load_dataset(written).cases) == 2


def test_load_missing_dataset(tmp_path):
    with pytest.raises(DatasetError, match="no dataset"):
        load_dataset(tmp_path / "nope")


# --- labels ------------------------------------------------------------------------------


def test_unlabeled_dataset_has_problems(written):
    ds = load_dataset(written)
    assert label_progress(ds) == (0, 4)
    assert len(label_problems(ds)) == 4


def test_invalid_and_unknown_labels_reported(written):
    fill_labels(written, {**ALL_YES, "KAFKA-1@3.7.0": "maybe"})
    with (written / "labels.csv").open("a", newline="") as f:
        f.write("KAFKA-9@1.0.0,,,,,,,,,yes,\n")
    problems = label_problems(load_dataset(written))
    assert any("KAFKA-1@3.7.0: answerable_from_text must be yes or no" in p for p in problems)
    assert any("KAFKA-9@1.0.0: in labels.csv but not a case" in p for p in problems)


def test_labels_are_case_insensitive(written):
    fill_labels(written, {k: "YES " for k in ALL_YES})
    assert label_problems(load_dataset(written)) == []


def test_expected_answer():
    positive, negative = cases_for("KAFKA-1")
    assert expected_answer(positive, {"answerable_from_text": "yes"}) == "affected"
    assert expected_answer(negative, {"answerable_from_text": "yes"}) == "not_affected"
    assert expected_answer(negative, {"answerable_from_text": "no"}) == INSUFFICIENT_INFORMATION


# --- Langfuse ------------------------------------------------------------------------------


class FakeLangfuse:
    def __init__(self):
        self.datasets = []
        self.items = {}

    def create_dataset(self, *, name, description, metadata):
        self.datasets.append({"name": name, "description": description, "metadata": metadata})

    def create_dataset_item(self, *, dataset_name, id, input, expected_output, metadata):
        self.items[(dataset_name, id)] = {
            "input": input,
            "expected_output": expected_output,
            "metadata": metadata,
        }


def test_items_refused_until_fully_labeled(written):
    fill_labels(written, {"KAFKA-1@3.7.0": "yes"})
    with pytest.raises(DatasetError, match="3 labeling problem"):
        langfuse_items(load_dataset(written))


def test_item_input_is_only_text_and_config(written):
    fill_labels(written, {**ALL_YES, "KAFKA-2@3.7.1": "no"}, notes={"KAFKA-2@3.7.1": "vague"})
    items = {i["id"]: i for i in langfuse_items(load_dataset(written))}

    item = items["KAFKA-2@3.7.1"]
    assert sorted(item["input"]) == ["comments", "description", "kafka_version", "summary"]
    assert item["input"]["kafka_version"] == "3.7.1"
    assert item["expected_output"] == {"answer": INSUFFICIENT_INFORMATION}
    assert item["metadata"]["metadata_answer"] == "not_affected"
    assert item["metadata"]["fix_versions"] == ["3.7.1", "3.8.0"]
    assert item["metadata"]["notes"] == "vague"
    assert items["KAFKA-1@3.7.0"]["expected_output"] == {"answer": "affected"}


def test_upload_is_idempotent(written):
    fill_labels(written, ALL_YES)
    ds = load_dataset(written)
    client = FakeLangfuse()

    assert upload(ds, client) == 4
    assert upload(ds, client) == 4

    assert len(client.items) == 4  # keyed by case id, so no duplicates
    assert client.datasets[0]["name"] == "test-set"
    assert client.datasets[0]["metadata"] == {"seed": 1}


# --- sampling from Postgres and the CLI ---------------------------------------------------


def seed_db(db, n_issues: int = 6):
    upsert_versions(
        db,
        "KAFKA",
        [
            {"id": str(i), "name": name, "released": True, "archived": False}
            for i, name in enumerate(["3.5.0", "3.6.0", "3.7.0", "3.7.1", "3.8.0", "3.9.0"], 1)
        ],
    )
    for n in range(1, n_issues + 1):
        raw = raw_issue(
            n,
            f"KAFKA-{n}",
            affects=["3.6.0"],
            fix=["3.7.1", "3.8.0"] if n % 2 else ["3.8.0"],
            comments=[raw_comment(n, f"Reproduced on 3.6.0 (#{n})")],
        )
        upsert_issue(db, parse_issue(raw))
    db.commit()


def test_sample_dataset_end_to_end(db, tmp_path):
    seed_db(db)
    manifest, sample, cases = sample_dataset(db, "e2e", size=4, seed=5)

    assert len(sample) == 4
    assert len(cases) == 8
    assert manifest["candidates"] == manifest["viable_candidates"] == 6
    assert sum(manifest["case_basis_counts"].values()) == 8

    write_dataset(tmp_path / "e2e", manifest, sample, cases)
    ds = load_dataset(tmp_path / "e2e")
    assert {c.issue_key for c in ds.cases} == {c.key for c in sample}


def test_sample_dataset_needs_versions(db):
    with pytest.raises(DatasetError, match="no released KAFKA versions"):
        sample_dataset(db, "x", size=1, seed=1)


def test_cli_status(written, capsys):
    args = ["eval", "status", "--name", "test-set", "--dir", str(written.parent)]
    assert main(args) == 1
    assert "0/4 cases labeled" in capsys.readouterr().out

    fill_labels(written, ALL_YES)
    assert main(args) == 0
    assert "4/4 cases labeled" in capsys.readouterr().out


def test_cli_reports_missing_dataset(tmp_path, capsys):
    assert main(["eval", "status", "--dir", str(tmp_path)]) == 1
    assert "no dataset" in capsys.readouterr().err
