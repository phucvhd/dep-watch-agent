from types import SimpleNamespace

import pytest

from dep_watch_agent.eval.dataset import DatasetError, langfuse_items, load_dataset
from dep_watch_agent.eval.metrics import CaseResult, compute_metrics, format_metrics
from dep_watch_agent.eval.runner import run_langfuse, run_local
from dep_watch_agent.verdict import (
    AFFECTED,
    INSUFFICIENT_INFORMATION,
    NOT_AFFECTED,
    Evidence,
    Extraction,
    IssueText,
)
from tests.eval_factory import ALL_YES, fill_labels

# --- metrics ------------------------------------------------------------------------------


def result(expected, answer, basis="b", total=1, valid=1) -> CaseResult:
    return CaseResult(
        case_id=f"c{id(object())}",
        issue_key="KAFKA-1",
        basis=basis,
        kafka_version="3.7.0",
        expected=expected,
        answer=answer,
        evidence_total=total,
        citations_valid=valid,
        output={},
    )


def test_metric_definitions():
    results = [
        result(AFFECTED, AFFECTED),  # TP
        result(AFFECTED, AFFECTED),  # TP
        result(AFFECTED, INSUFFICIENT_INFORMATION),  # missed
        result(NOT_AFFECTED, AFFECTED, basis="fix_version"),  # false alarm
        result(NOT_AFFECTED, NOT_AFFECTED, basis="fix_version"),
        result(INSUFFICIENT_INFORMATION, AFFECTED, total=2, valid=1),  # unsupported alert
        result(INSUFFICIENT_INFORMATION, INSUFFICIENT_INFORMATION, total=0, valid=0),
        result(INSUFFICIENT_INFORMATION, INSUFFICIENT_INFORMATION, total=0, valid=0),
    ]
    m = compute_metrics(results)
    assert m["n"] == 8
    assert m["accuracy"] == 5 / 8
    assert m["precision"] == 2 / 4
    assert m["recall"] == 2 / 3
    assert m["false_alarm_rate"] == 2 / 5  # both non-affected rows answered affected
    assert m["abstention_rate"] == 3 / 8
    assert m["abstention_recall"] == 2 / 3
    assert m["citation_validity"] == 6 / 7
    assert m["always_abstain_accuracy"] == 3 / 8
    # F1 = 2TP / (2TP + FP + FN) per answer
    assert m["f1_by_answer"] == {
        AFFECTED: 4 / 7,  # TP 2, FP 2, FN 1
        NOT_AFFECTED: 2 / 3,  # TP 1, FP 0, FN 1
        INSUFFICIENT_INFORMATION: 4 / 6,  # TP 2, FP 1, FN 1
    }
    assert m["f1"] == 4 / 7
    assert m["macro_f1"] == pytest.approx((4 / 7 + 2 / 3 + 4 / 6) / 3)
    assert m["confusion"][NOT_AFFECTED][AFFECTED] == 1
    assert m["accuracy_by_basis"] == {"b": 4 / 6, "fix_version": 1 / 2}


def test_zero_denominators_are_none_not_zero():
    m = compute_metrics([result(NOT_AFFECTED, INSUFFICIENT_INFORMATION, total=0, valid=0)])
    assert m["precision"] is None  # never answered affected
    assert m["recall"] is None  # nothing expected affected
    assert m["abstention_recall"] is None
    assert m["citation_validity"] is None
    assert m["f1"] is None  # affected never expected nor answered
    assert m["f1_by_answer"][NOT_AFFECTED] == 0.0  # expected, never given
    assert m["macro_f1"] == 0.0  # mean over the two answers that occur
    assert "n/a" in format_metrics(m)
    assert "(always abstain)" in format_metrics(m)


# --- local runs ------------------------------------------------------------------------


class CountingExtractor:
    """Says every issue is affected from 3.7.0 (quoting the description) and fixed in 3.7.1
    (quoting the first comment)."""

    def __init__(self):
        self.calls = []

    def extract(self, issue: IssueText) -> Extraction:
        self.calls.append(issue.summary)
        return Extraction(
            [
                Evidence("3.7.0", "affects", issue.description),
                Evidence("3.7.1", "fix", issue.comments[0]),
            ]
        )


def test_local_run_requires_labels(written):
    with pytest.raises(DatasetError, match="provisional"):
        run_local(load_dataset(written), CountingExtractor())


def test_provisional_run_scores_against_metadata(written):
    extractor = CountingExtractor()
    results = run_local(load_dataset(written), extractor, provisional=True)

    assert [(r.case_id, r.expected, r.answer) for r in results] == [
        ("KAFKA-1@3.7.0", AFFECTED, AFFECTED),
        ("KAFKA-1@3.7.1", NOT_AFFECTED, NOT_AFFECTED),
        ("KAFKA-2@3.7.0", AFFECTED, AFFECTED),
        ("KAFKA-2@3.7.1", NOT_AFFECTED, NOT_AFFECTED),
    ]
    assert extractor.calls == ["KAFKA-1 summary", "KAFKA-2 summary"]  # once per issue
    assert results[0].output["evidence"][0]["version"] == "3.7.0"


def test_labeled_run_uses_expected_answers(written):
    fill_labels(written, {**ALL_YES, "KAFKA-2@3.7.1": "no"})
    results = run_local(load_dataset(written), CountingExtractor())
    by_id = {r.case_id: r for r in results}
    assert by_id["KAFKA-2@3.7.1"].expected == INSUFFICIENT_INFORMATION
    assert not by_id["KAFKA-2@3.7.1"].correct


def test_runner_enforces_citations(written):
    class Fabricator:
        def extract(self, issue):
            return Extraction([Evidence("3.7.0", "affects", "a quote that is not in the issue")])

    results = run_local(load_dataset(written), Fabricator(), provisional=True)
    assert {r.answer for r in results} == {INSUFFICIENT_INFORMATION}
    assert compute_metrics(results)["citation_validity"] == 0.0


# --- Langfuse runs ---------------------------------------------------------------------


class FakeDataset:
    """Calls task and evaluators the way Langfuse's run_experiment does."""

    def __init__(self, items):
        self.items = items
        self.runs = []

    def run_experiment(self, *, name, run_name, description, task, evaluators, run_evaluators,
                       max_concurrency, metadata):  # fmt: skip
        item_results = []
        item_scores = {}
        for item in self.items:
            output = task(item=item)
            scores = []
            for evaluate in evaluators:
                scores += evaluate(
                    input=item.input,
                    output=output,
                    expected_output=item.expected_output,
                    metadata=item.metadata,
                )
            item_scores[item.id] = {s.name: s.value for s in scores}
            item_results.append(SimpleNamespace(item=item, output=output, evaluations=scores))
        run_scores = {s.name: s.value for e in run_evaluators for s in e(item_results=item_results)}
        self.runs.append(
            {"name": name, "run_name": run_name, "metadata": metadata,
             "item_scores": item_scores, "run_scores": run_scores}
        )  # fmt: skip
        return self.runs[-1]


class FakeLangfuse:
    def __init__(self, dataset):
        self.dataset = dataset

    def get_dataset(self, name):
        return self.dataset


def test_langfuse_run_scores_items_and_run(written):
    fill_labels(written, {**ALL_YES, "KAFKA-2@3.7.1": "no"})
    items = [SimpleNamespace(**i) for i in langfuse_items(load_dataset(written))]
    fake = FakeDataset(items)
    extractor = CountingExtractor()

    run, metrics = run_langfuse(
        FakeLangfuse(fake), "test-set", extractor, system="counting", run_name="r1"
    )

    assert run["name"] == "counting"
    assert run["run_name"] == "r1"
    assert run["metadata"] == {"system": "counting"}
    assert run["item_scores"]["KAFKA-1@3.7.0"] == {"correct": 1.0, "citation_validity": 1.0}
    assert run["item_scores"]["KAFKA-2@3.7.1"]["correct"] == 0.0  # expected abstention
    assert run["run_scores"]["accuracy"] == 3 / 4
    assert "abstention_recall" in run["run_scores"]
    assert metrics["accuracy"] == 3 / 4
    assert len(extractor.calls) == 2  # cached per issue


def test_langfuse_run_skips_undefined_metrics(written):
    fill_labels(written, ALL_YES)  # nothing expected to abstain
    items = [SimpleNamespace(**i) for i in langfuse_items(load_dataset(written))]
    fake = FakeDataset(items)
    run_langfuse(
        FakeLangfuse(fake), "test-set", CountingExtractor(), system="counting", run_name="r1"
    )
    assert "abstention_recall" not in fake.runs[0]["run_scores"]
