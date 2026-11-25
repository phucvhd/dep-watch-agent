import json
from datetime import date

import pytest

from dep_watch_agent.eval import analysis, contamination, faithfulness, gate
from dep_watch_agent.eval.metrics import CaseResult, compute_metrics, format_metrics
from dep_watch_agent.eval.stats import bootstrap_intervals, compare, mcnemar_exact
from dep_watch_agent.verdict import AFFECTED, INSUFFICIENT_INFORMATION, NOT_AFFECTED


def result(expected, answer, key="KAFKA-1", case=None, seconds=0.0, output=None) -> CaseResult:
    return CaseResult(
        case_id=case or f"{key}@{id(object())}",
        issue_key=key,
        basis="b",
        version="3.7.0",
        expected=expected,
        answer=answer,
        evidence_total=0,
        citations_valid=0,
        output=output or {},
        seconds=seconds,
    )


# --- metrics -----------------------------------------------------------------------------


def test_silent_miss_rate_is_an_unsupported_all_clear():
    m = compute_metrics(
        [
            result(AFFECTED, NOT_AFFECTED),  # silent miss
            result(AFFECTED, AFFECTED),
            result(INSUFFICIENT_INFORMATION, NOT_AFFECTED),  # unsupported all-clear
            result(INSUFFICIENT_INFORMATION, INSUFFICIENT_INFORMATION),
            result(NOT_AFFECTED, NOT_AFFECTED),  # not in the denominator
        ]
    )
    assert m["silent_miss_rate"] == 2 / 4


def test_latency_is_per_issue():
    m = compute_metrics(
        [
            result(AFFECTED, AFFECTED, key="A", seconds=3.0),
            result(AFFECTED, AFFECTED, key="A", seconds=0.0),  # reused the reading
            result(AFFECTED, AFFECTED, key="B", seconds=1.0),
        ]
    )
    assert m["latency"] == {"issues": 2, "mean_s": 2.0, "p50_s": 1.0, "p95_s": 3.0, "total_s": 4.0}
    assert "latency per issue" in format_metrics(m)
    assert compute_metrics([result(AFFECTED, AFFECTED)])["latency"] is None


# --- stats -------------------------------------------------------------------------------


def test_mcnemar_exact():
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(5, 5) == 1.0
    assert mcnemar_exact(0, 6) == pytest.approx(2 / 64)
    assert mcnemar_exact(1, 9) == pytest.approx(2 * 11 / 1024)


def many(n_issues: int, right: int) -> list[CaseResult]:
    """Two cases per issue; the first ``right`` issues answered correctly."""
    out = []
    for i in range(n_issues):
        answer = AFFECTED if i < right else INSUFFICIENT_INFORMATION
        for j in range(2):
            out.append(result(AFFECTED, answer, key=f"K-{i}", case=f"K-{i}@{j}"))
    return out


def test_bootstrap_interval_brackets_the_estimate_and_is_reproducible():
    results = many(40, 20)
    ci = bootstrap_intervals(results, reps=300)
    low, high = ci["accuracy"]
    assert low < 0.5 < high
    assert ci == bootstrap_intervals(results, reps=300)
    assert ci["precision"] == [1.0, 1.0]
    assert ci["abstention_recall"] is None  # nothing expected to abstain


def test_compare_pairs_cases_by_id():
    a, b = many(40, 30), many(40, 10)
    c = compare(a, b, reps=300)
    assert (c["cases"], c["issues"]) == (80, 40)
    assert c["mcnemar"]["a_only"] == 40 and c["mcnemar"]["b_only"] == 0
    assert c["mcnemar"]["p_value"] < 1e-6
    diff = c["difference"]["accuracy"]
    assert diff["delta"] == pytest.approx(0.5)
    assert diff["ci95"][0] > 0
    with pytest.raises(ValueError):
        compare(a, [result(AFFECTED, AFFECTED, case="other")])


# --- gate --------------------------------------------------------------------------------


def run(metrics: dict, **fields) -> dict:
    return {"run_name": "r1", "system": "s", "dataset": "d", "metrics": metrics, **fields}


def test_gate_fails_on_a_drop_past_the_tolerance(tmp_path):
    path = gate.accept(tmp_path, run({"macro_f1": 0.6, "silent_miss_rate": 0.05}), tolerance=0.02)
    baseline = json.loads(path.read_text())
    assert path == tmp_path / "d" / "s.json"

    assert gate.check({"macro_f1": 0.59, "silent_miss_rate": 0.06}, baseline)["passed"]
    worse = gate.check({"macro_f1": 0.55, "silent_miss_rate": 0.10}, baseline)
    assert not worse["passed"]
    assert [f["metric"] for f in worse["failures"]] == ["macro_f1", "silent_miss_rate"]
    assert not gate.check({"macro_f1": None, "silent_miss_rate": 0.0}, baseline)["passed"]
    with pytest.raises(ValueError):
        gate.accept(tmp_path, run({}, provisional=True))


def test_gate_command_exit_codes(tmp_path):
    saved = tmp_path / "r1.json"
    saved.write_text(json.dumps(run({"macro_f1": 0.6})))
    args = [str(saved), "--baselines", str(tmp_path / "b")]
    assert gate.main(args) == 0  # no baseline yet
    assert gate.main([*args, "--accept"]) == 0
    saved.write_text(json.dumps(run({"macro_f1": 0.5})))
    assert gate.main(args) == 1


# --- contamination -----------------------------------------------------------------------


def test_contamination_split_by_issue_date():
    results = [
        result(AFFECTED, AFFECTED, key="OLD"),
        result(AFFECTED, INSUFFICIENT_INFORMATION, key="NEW"),
        result(AFFECTED, AFFECTED, key="UNDATED"),
    ]
    dates = {"OLD": date(2024, 1, 1), "NEW": date(2025, 9, 1)}
    s = contamination.split(results, dates, date(2025, 8, 5))
    assert (s["before"]["issues"], s["before"]["accuracy"]) == (1, 1.0)
    assert (s["after"]["issues"], s["after"]["accuracy"]) == (1, 0.0)


def test_model_release(monkeypatch):
    monkeypatch.delenv("DEP_WATCH_LLM_RELEASE_DATE", raising=False)
    assert contamination.model_release("qwen/qwen3-4b-2507;output=text") == date(2025, 8, 5)
    assert contamination.model_release("unknown-model") is None
    monkeypatch.setenv("DEP_WATCH_LLM_RELEASE_DATE", "2026-01-02")
    assert contamination.model_release("unknown-model") == date(2026, 1, 2)


# --- analysis ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("expected", "answer", "output", "kind"),
    [
        (AFFECTED, AFFECTED, {}, None),
        (AFFECTED, INSUFFICIENT_INFORMATION, {}, "missed: no facts extracted"),
        (
            AFFECTED,
            INSUFFICIENT_INFORMATION,
            {"dropped": [{"reason": "citation not found"}]},
            "missed: facts dropped (citation not found)",
        ),
        (
            AFFECTED,
            INSUFFICIENT_INFORMATION,
            {"evidence": [{"kind": "fix"}]},
            "missed: no affects/introduced fact",
        ),
        (AFFECTED, NOT_AFFECTED, {}, "silent miss: wrong all-clear"),
        (INSUFFICIENT_INFORMATION, AFFECTED, {}, "unsupported alert: text has no answer"),
        (NOT_AFFECTED, AFFECTED, {}, "false alarm: version is before the bug or fixed"),
    ],
)
def test_error_kind(expected, answer, output, kind):
    assert analysis.error_kind(result(expected, answer, output=output)) == kind


def test_markdown_report(written, tmp_path):
    from dep_watch_agent.eval.dataset import load_dataset

    dataset = load_dataset(written)
    cases = [c.case_id for c in dataset.cases]
    runs = []
    for name, answer in (("ref", AFFECTED), ("other", INSUFFICIENT_INFORMATION)):
        results = [
            result(AFFECTED, answer, key=c.split("@")[0], case=c, seconds=1.0) for c in cases
        ]
        runs.append(
            {
                "run_name": name,
                "system": "qwen3-4b-2507",
                "metrics": compute_metrics(results),
                "case_results": results,
            }
        )
    (written / contamination.ISSUE_DATES_FILE).write_text(
        json.dumps({"KAFKA-1": "2024-01-01", "KAFKA-2": "2026-01-01"})
    )
    report = analysis.markdown_report(dataset, runs, reps=50)
    assert "| other | 0 | 4 |" in report
    assert "missed: no facts extracted" in report
    assert "2025-08-05 | 1 / 1" in report


# --- faithfulness ------------------------------------------------------------------------


def test_faithfulness_judges_each_fact_once():
    ev = {"version": "3.6.0", "kind": "affects", "quote": "We run 3.6.0."}
    out = {"evidence": [ev], "context": ["We run 3.6.0."]}
    results = [
        result(AFFECTED, AFFECTED, key="K", case="K@a", output=out),
        result(AFFECTED, AFFECTED, key="K", case="K@b", output=out),
        result(
            AFFECTED,
            AFFECTED,
            key="L",
            case="L@a",
            output={"evidence": [{**ev, "kind": "introduced"}]},
        ),
    ]
    issues = {"L": {"summary": "s", "description": "We run 3.6.0."}}
    asked = []

    def judge(system, user):
        asked.append(user)
        return {"supported": "has the bug" in user}

    scored = faithfulness.score(results, issues, judge, "prompt")
    assert (scored["facts"], scored["judged"], scored["faithfulness"]) == (2, 2, 0.5)
    assert scored["by_kind"] == {"affects": 1.0, "introduced": 0.0}
    assert "<context>\nWe run 3.6.0.\n</context>" in asked[0]
    assert "<description>" in asked[1]  # no retrieval: the whole issue


def test_faithfulness_skips_invalid_judgments():
    out = {"evidence": [{"version": "1.0.0", "kind": "fix", "quote": "q"}], "context": ["q"]}
    scored = faithfulness.score(
        [result(AFFECTED, AFFECTED, output=out)], {}, lambda s, u: "nonsense", "p"
    )
    assert (scored["facts"], scored["judged"], scored["faithfulness"]) == (1, 0, None)


def test_judge_is_never_the_model_under_test():
    with pytest.raises(faithfulness.JudgeIsModelUnderTest):
        faithfulness.check_judge("qwen/qwen3-4b-2507", "qwen/qwen3-4b-2507;output=text")
    faithfulness.check_judge("qwen/qwen3.5-9b", "qwen/qwen3-4b-2507;output=text")


def test_context_recall():
    results = [
        result(AFFECTED, AFFECTED, case="a", output={"context": ["We run  3.6.0 here."]}),
        result(AFFECTED, AFFECTED, case="b", output={"context": ["nothing"]}),
        result(AFFECTED, AFFECTED, case="c", output={}),  # read whole: not counted
    ]
    gold = {"a": ["We run 3.6.0 here."], "b": ["Seen on 2.8.0."], "c": ["x"]}
    assert faithfulness.context_recall(results, gold) == {"cases": 2, "quotes": 2, "recall": 0.5}
    assert faithfulness.context_recall(results, {}) is None
