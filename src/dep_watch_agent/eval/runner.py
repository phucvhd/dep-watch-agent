"""Run a system over the ground-truth dataset, locally or as a Langfuse experiment.

Two kinds of system:

- an ``Extractor`` (``extract(IssueText) -> Extraction``): the runner, not the system, turns
  extractions into answers with ``verdict.decide``, so every extractor is scored through the
  same decision code. Each issue is extracted once and shared by its configs.
- a ``DirectSystem`` (``answer(IssueText, version) -> Decision``): the direct-verdict control,
  which answers each config itself and whose citation code only checks (``direct.py``).

Every case records the seconds its system spent on it (``CaseResult.seconds``).
"""

import time
from collections.abc import Callable
from dataclasses import asdict
from typing import Any, Protocol

from dep_watch_agent.eval.dataset import Dataset, DatasetError, expected_answer, label_problems
from dep_watch_agent.eval.metrics import RATE_METRICS, CaseResult, compute_metrics
from dep_watch_agent.verdict import Decision, Extraction, IssueText, decide
from dep_watch_agent.versions import KAFKA  # the ground truth is Kafka's


class Extractor(Protocol):
    """Turns issue text into cited facts. May also have a ``version`` string (everything that
    changes its output besides the text); only then are its extractions stored and reused
    (``extractions.py``)."""

    """Turns issue text into cited facts. Its name is the key it is registered under in
    ``systems.SYSTEMS``, so one class can back several systems (e.g. one per model)."""

    def extract(self, issue: IssueText) -> Extraction: ...


class DirectSystem(Protocol):
    """Answers one config of an issue itself, with its citation checked (``direct.py``)."""

    def answer(self, issue: IssueText, version: str) -> Decision: ...


def is_direct(system: Any) -> bool:
    return callable(getattr(system, "answer", None))


class CaseAnswerer:
    """Answers the configs of a run for one system, reading each issue once if the system is an
    extractor. Returns the decision, the seconds spent and the passages read (if selected)."""

    def __init__(self, system: Extractor | DirectSystem):
        self.system = system
        self._extractions: dict[str, Extraction] = {}

    def __call__(
        self, key: str, issue: IssueText, version: str
    ) -> tuple[Decision, float, list[str] | None]:
        start = time.perf_counter()
        if is_direct(self.system):
            decision = self.system.answer(issue, version)  # type: ignore[union-attr]
            return decision, time.perf_counter() - start, None
        seconds = 0.0
        if key not in self._extractions:
            self._extractions[key] = self.system.extract(issue)  # type: ignore[union-attr]
            seconds = time.perf_counter() - start
        extraction = self._extractions[key]
        return decide(issue, version, extraction, KAFKA), seconds, extraction.context


def decision_output(decision: Decision, context: list[str] | None = None) -> dict[str, Any]:
    output = {
        "answer": decision.answer,
        "evidence": [asdict(e) for e in decision.used],
        "dropped": [{**asdict(d.evidence), "reason": d.reason} for d in decision.dropped],
        "evidence_total": decision.evidence_total,
        "citations_valid": decision.citations_valid,
    }
    if context is not None:
        output["context"] = context
    return output


def run_local(
    dataset: Dataset, system: Extractor | DirectSystem, *, provisional: bool = False
) -> list[CaseResult]:
    """Score ``extractor`` on the dataset files.

    Needs complete labels, unless ``provisional``: then cases are scored against the JIRA
    metadata answer, which has no ``insufficient_information`` truth. Useful while developing,
    never as a reported result.
    """
    if not provisional:
        problems = label_problems(dataset)
        if problems:
            raise DatasetError(
                f"{len(problems)} labeling problem(s), first: {problems[0]}. "
                "Finish labeling or run as provisional."
            )

    answer = CaseAnswerer(system)
    results = []
    for case in dataset.cases:
        issue = IssueText.from_dict(dataset.issues[case.issue_key])
        decision, seconds, context = answer(case.issue_key, issue, case.version)
        expected = (
            case.metadata_answer
            if provisional
            else expected_answer(case, dataset.labels[case.case_id])
        )
        results.append(
            CaseResult(
                case_id=case.case_id,
                issue_key=case.issue_key,
                basis=case.basis,
                version=case.version,
                expected=expected,
                answer=decision.answer,
                evidence_total=decision.evidence_total,
                citations_valid=decision.citations_valid,
                output=decision_output(decision, context),
                seconds=seconds,
            )
        )
    return results


def item_version(item: Any) -> str:
    """The config version of a Langfuse dataset item. Items uploaded before the field was
    renamed carry it as ``kafka_version``."""
    return item.input.get("version") or item.input["kafka_version"]


def run_langfuse(
    client: Any,
    dataset_name: str,
    system_impl: Extractor | DirectSystem | None,
    *,
    system: str,
    run_name: str,
    metadata: dict[str, Any] | None = None,
    summarize: Callable[[list[CaseResult]], dict[str, Any]] | None = None,
    saved: dict[str, CaseResult] | None = None,
) -> tuple[Any, list[CaseResult], dict[str, Any]]:
    """Run as a Langfuse experiment on the uploaded dataset. Returns (experiment, case results,
    summary).

    Per-case scores: ``correct`` and ``citation_validity``. Run-level scores: everything
    ``summary_scores`` makes of the summary, which is ``summarize(results)`` (by default just
    ``{"metrics": compute_metrics(results)}``).

    With ``saved`` (case id -> result of a saved local run), nothing is asked of a system: each
    item's task returns the saved output, so a run already made locally becomes an experiment
    without calling the model again (a replay). Every item must be in ``saved``.
    """
    from langfuse import Evaluation

    if system_impl is None and saved is None:
        raise ValueError("give a system to run, or the saved results to replay")
    answer = CaseAnswerer(system_impl) if saved is None else None
    results: list[CaseResult] = []
    summary: dict[str, Any] = {}

    def task(*, item: Any, **_: Any) -> dict[str, Any]:
        if saved is not None:
            if item.id not in saved:
                raise DatasetError(f"{item.id} is in the Langfuse dataset but not the saved run")
            r = saved[item.id]
            return {**r.output, "seconds": r.seconds}
        issue = IssueText.from_dict(item.input)
        decision, seconds, context = answer(item.metadata["issue_key"], issue, item_version(item))
        return {**decision_output(decision, context), "seconds": seconds}

    def per_case(*, output: Any, expected_output: Any, **_: Any) -> list[Any]:
        scores = [
            Evaluation(name="correct", value=float(output["answer"] == expected_output["answer"]))
        ]
        if output["evidence_total"]:
            scores.append(
                Evaluation(
                    name="citation_validity",
                    value=output["citations_valid"] / output["evidence_total"],
                )
            )
        return scores

    def per_run(*, item_results: list[Any], **_: Any) -> list[Any]:
        for r in item_results:
            results.append(
                CaseResult(
                    case_id=r.item.id,
                    issue_key=r.item.metadata["issue_key"],
                    basis=r.item.metadata["basis"],
                    version=item_version(r.item),
                    expected=r.item.expected_output["answer"],
                    answer=r.output["answer"],
                    evidence_total=r.output["evidence_total"],
                    citations_valid=r.output["citations_valid"],
                    output={k: v for k, v in r.output.items() if k != "seconds"},
                    seconds=r.output.get("seconds", 0.0),
                )
            )
        summary.update(summarize(results) if summarize else {"metrics": compute_metrics(results)})
        return [Evaluation(**score) for score in summary_scores(summary)]

    dataset = client.get_dataset(dataset_name)
    experiment = dataset.run_experiment(
        name=system,
        run_name=run_name,
        description=f"{system} on {dataset_name}" + (" (replay of a local run)" if saved else ""),
        task=task,
        evaluators=[per_case],
        run_evaluators=[per_run],
        max_concurrency=1,
        metadata={"system": system, **({"replay": True} if saved else {}), **(metadata or {})},
    )
    return experiment, results, summary


def summary_scores(summary: dict[str, Any]) -> list[dict[str, Any]]:
    """The run-level Langfuse scores of a run summary (``metrics`` and, when present,
    ``intervals``, ``contamination`` and ``gate``), as ``Evaluation`` keyword arguments.

    - every rate metric with a value, its 95% bootstrap interval in the comment and metadata;
      ``macro_f1`` also carries the confusion matrix;
    - ``latency_p50_s``, ``latency_p95_s``;
    - ``macro_f1_before_release``, ``macro_f1_after_release`` (and accuracy), the release and
      issue counts in the comment;
    - ``gate_passed`` (boolean), the failing metrics in the comment;
    - ``faithfulness`` and ``context_recall``, once the run has been judged;
    - ``faithfulness_ragas``, once the RAGAS library has scored it.
    """
    metrics = summary["metrics"]
    intervals = summary.get("intervals") or {}
    scores = []
    for name in RATE_METRICS:
        if metrics.get(name) is None:
            continue
        score: dict[str, Any] = {"name": name, "value": metrics[name]}
        ci = intervals.get(name)
        if ci:
            score["comment"] = f"95% CI [{ci[0]:.3f}, {ci[1]:.3f}] (bootstrap over issues)"
            score["metadata"] = {"ci95": ci}
        if name == "macro_f1":
            score["metadata"] = {**score.get("metadata", {}), "confusion": metrics["confusion"]}
        scores.append(score)
    latency = metrics.get("latency")
    if latency:
        scores += [
            {"name": "latency_p50_s", "value": latency["p50_s"]},
            {"name": "latency_p95_s", "value": latency["p95_s"]},
        ]
    split = summary.get("contamination")
    if split:
        for side, label in (("before", "before_release"), ("after", "after_release")):
            part = split[side]
            comment = f"{part['issues']} issues created {side} {split['release']}"
            for name in ("macro_f1", "accuracy"):
                if part.get(name) is not None:
                    scores.append(
                        {"name": f"{name}_{label}", "value": part[name], "comment": comment}
                    )
    gate = summary.get("gate")
    if gate:
        failed = ", ".join(
            f"{f['metric']} {f['baseline']} -> {f['current']}" for f in gate["failures"]
        )
        scores.append(
            {
                "name": "gate_passed",
                "value": float(gate["passed"]),  # Langfuse booleans are 1 or 0
                "data_type": "BOOLEAN",
                "comment": f"against {gate['baseline_run']}, tolerance {gate['tolerance']}"
                + (f"; failed: {failed}" if failed else ""),
            }
        )
    judged = summary.get("faithfulness")
    if judged:
        if judged.get("faithfulness") is not None:
            scores.append(
                {
                    "name": "faithfulness",
                    "value": judged["faithfulness"],
                    "comment": f"judge {judged['judge']}, {judged['judged']} facts",
                    "metadata": {"by_kind": judged.get("by_kind", {})},
                }
            )
        recall = judged.get("context_recall")
        if recall:
            scores.append(
                {
                    "name": "context_recall",
                    "value": recall["recall"],
                    "comment": f"{recall['quotes']} labeled quotes in {recall['cases']} cases",
                }
            )
    ragas = summary.get("faithfulness_ragas")
    if ragas and ragas.get("faithfulness") is not None:
        agreed = ragas.get("agreement_with_inhouse")
        scores.append(
            {
                "name": "faithfulness_ragas",
                "value": ragas["faithfulness"],
                "comment": f"{ragas['library']}, judge {ragas['judge']}, mean over "
                f"{ragas['scored']} of {ragas['samples']} issues"
                + (
                    f"; differs from the in-house judge by {agreed['mean_abs_diff']:.2f}"
                    if agreed
                    else ""
                ),
                "metadata": {"agreement_with_inhouse": agreed},
            }
        )
    return scores
