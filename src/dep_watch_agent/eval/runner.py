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
    system_impl: Extractor | DirectSystem,
    *,
    system: str,
    run_name: str,
    metadata: dict[str, Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Run as a Langfuse experiment on the uploaded dataset. Returns (experiment, metrics).

    Per-case scores: ``correct`` and ``citation_validity``. Run-level scores: every metric in
    ``RATE_METRICS``.
    """
    from langfuse import Evaluation

    answer = CaseAnswerer(system_impl)
    results: list[CaseResult] = []

    def task(*, item: Any, **_: Any) -> dict[str, Any]:
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
                    output=r.output,
                    seconds=r.output.get("seconds", 0.0),
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
        name=system,
        run_name=run_name,
        description=f"{system} on {dataset_name}",
        task=task,
        evaluators=[per_case],
        run_evaluators=[per_run],
        max_concurrency=1,
        metadata={"system": system, **(metadata or {})},
    )
    return experiment, compute_metrics(results)
