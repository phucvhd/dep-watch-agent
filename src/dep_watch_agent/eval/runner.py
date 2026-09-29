"""Run a system over the ground-truth dataset, locally or as a Langfuse experiment.

A system is anything with ``extract(IssueText) -> Extraction``. The runner, not the system,
turns extractions into answers with ``verdict.decide``, so every system is scored through the
same decision code. Each issue is extracted once and shared by its configs.
"""

from dataclasses import asdict
from typing import Any, Protocol

from dep_watch_agent.eval.dataset import Dataset, DatasetError, expected_answer, label_problems
from dep_watch_agent.eval.metrics import RATE_METRICS, CaseResult, compute_metrics
from dep_watch_agent.verdict import Decision, Extraction, IssueText, decide


class Extractor(Protocol):
    name: str

    def extract(self, issue: IssueText) -> Extraction: ...


def decision_output(decision: Decision) -> dict[str, Any]:
    return {
        "answer": decision.answer,
        "evidence": [asdict(e) for e in decision.used],
        "dropped": [{**asdict(d.evidence), "reason": d.reason} for d in decision.dropped],
        "evidence_total": decision.evidence_total,
        "citations_valid": decision.citations_valid,
    }


def run_local(
    dataset: Dataset, extractor: Extractor, *, provisional: bool = False
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

    extractions: dict[str, Extraction] = {}
    results = []
    for case in dataset.cases:
        issue = IssueText.from_dict(dataset.issues[case.issue_key])
        if case.issue_key not in extractions:
            extractions[case.issue_key] = extractor.extract(issue)
        decision = decide(issue, case.kafka_version, extractions[case.issue_key])
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
                kafka_version=case.kafka_version,
                expected=expected,
                answer=decision.answer,
                evidence_total=decision.evidence_total,
                citations_valid=decision.citations_valid,
                output=decision_output(decision),
            )
        )
    return results


def run_langfuse(
    client: Any,
    dataset_name: str,
    extractor: Extractor,
    *,
    run_name: str,
    metadata: dict[str, Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Run as a Langfuse experiment on the uploaded dataset. Returns (experiment, metrics).

    Per-case scores: ``correct`` and ``citation_validity``. Run-level scores: every metric in
    ``RATE_METRICS``.
    """
    from langfuse import Evaluation

    extractions: dict[str, Extraction] = {}
    results: list[CaseResult] = []

    def task(*, item: Any, **_: Any) -> dict[str, Any]:
        issue = IssueText.from_dict(item.input)
        key = item.metadata["issue_key"]
        if key not in extractions:
            extractions[key] = extractor.extract(issue)
        return decision_output(decide(issue, item.input["kafka_version"], extractions[key]))

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
                    kafka_version=r.item.input["kafka_version"],
                    expected=r.item.expected_output["answer"],
                    answer=r.output["answer"],
                    evidence_total=r.output["evidence_total"],
                    citations_valid=r.output["citations_valid"],
                    output=r.output,
                )
            )
        metrics = compute_metrics(results)
        return [
            Evaluation(name=name, value=metrics[name])
            for name in RATE_METRICS
            if metrics[name] is not None
        ]

    dataset = client.get_dataset(dataset_name)
    experiment = dataset.run_experiment(
        name=extractor.name,
        run_name=run_name,
        description=f"{extractor.name} on {dataset_name}",
        task=task,
        evaluators=[per_case],
        run_evaluators=[per_run],
        max_concurrency=1,
        metadata={"system": extractor.name, **(metadata or {})},
    )
    return experiment, compute_metrics(results)
