"""The RAGAS judge. ``samples`` and ``agreement`` need no RAGAS; the tests that run the library
skip unless it is installed:
``uv run --with ragas==0.4.4 python -m pytest tests/test_ragas_judge.py``."""

import time

import pytest

from dep_watch_agent.eval import ragas_judge
from dep_watch_agent.eval.metrics import CaseResult
from dep_watch_agent.verdict import AFFECTED


def result(key, case, output) -> CaseResult:
    return CaseResult(
        case_id=case,
        issue_key=key,
        basis="b",
        version="3.7.0",
        expected=AFFECTED,
        answer=AFFECTED,
        evidence_total=1,
        citations_valid=1,
        output=output,
    )


AFFECTS = {"version": "3.6.0", "kind": "affects", "quote": "We run 3.6.0."}
FIX = {"version": "3.7.1", "kind": "fix", "quote": "3.7.1"}
ISSUES = {
    "K": {"summary": "s", "description": "We run 3.6.0.", "fix_versions": ["3.7.1"]},
    "L": {"summary": "t", "description": "x" * 5000},
    "M": {"summary": "u", "description": "nothing kept"},
}
RESULTS = [
    # Both cases of K share one reading: their facts are pooled, the repeated one kept once.
    result("K", "K@a", {"evidence": [AFFECTS]}),
    result("K", "K@b", {"evidence": [AFFECTS, FIX]}),
    # L was read through retrieval: its passages are the context.
    result("L", "L@a", {"evidence": [{**AFFECTS, "kind": "introduced"}], "context": ["p1", "p2"]}),
    result("M", "M@a", {"evidence": []}),  # no kept facts: no sample
]


def test_one_sample_per_issue_with_kept_facts():
    out = ragas_judge.samples(RESULTS, ISSUES, max_context_chars=2000)
    assert [s.issue_key for s in out] == ["K", "L"]
    k, retrieved = out
    assert k.claims == (
        "Kafka 3.6.0 has the bug: it was seen, reproduced or logged on 3.6.0.",
        "The bug is fixed in Kafka 3.7.1.",
    )
    assert k.response == "\n".join(k.claims)
    # No retrieval: the issue's tagged text, cut to the limit.
    (text,) = k.contexts
    assert "<fix_versions>" in text and "We run 3.6.0." in text
    assert retrieved.contexts == ("p1", "p2")


def test_a_long_issue_read_whole_is_cut_to_the_limit():
    long = [result("L", "L@a", {"evidence": [AFFECTS]})]
    (sample,) = ragas_judge.samples(long, ISSUES, max_context_chars=2000)
    assert len(sample.contexts[0]) <= 2000


def test_agreement_compares_issue_scores():
    judgments = [
        {"issue_key": "K", "supported": True},
        {"issue_key": "K", "supported": False},
        {"issue_key": "L", "supported": True},
        {"issue_key": "N", "supported": None},  # invalid in-house judgment: left out
    ]
    agreed = ragas_judge.agreement({"K": 1.0, "L": 1.0, "M": None}, judgments)
    assert agreed["issues"] == 2
    assert agreed["ragas"] == 1.0
    assert agreed["inhouse"] == 0.75
    assert agreed["mean_abs_diff"] == 0.25
    assert agreed["same_all_supported"] == 0.5  # L agrees, K doesn't
    assert ragas_judge.agreement({"K": None}, judgments) is None


# --- with the RAGAS library --------------------------------------------------------------


@pytest.fixture
def fake_llm():
    """A judge that splits a response into its lines and supports a statement only if it names
    3.6.0, in RAGAS's own output models."""
    pytest.importorskip("ragas")
    from ragas.llms.base import InstructorBaseRagasLLM
    from ragas.metrics.collections.faithfulness.util import (
        NLIStatementOutput,
        StatementFaithfulnessAnswer,
        StatementGeneratorOutput,
    )

    class Fake(InstructorBaseRagasLLM):
        def __init__(self):
            self.prompts = []

        def generate(self, prompt, response_model):
            raise NotImplementedError

        async def agenerate(self, prompt, response_model):
            self.prompts.append(prompt)
            if "FAIL" in prompt:
                raise RuntimeError("invalid output")
            if response_model is StatementGeneratorOutput:
                lines = [c for c in RESPONSES if c in prompt]
                return StatementGeneratorOutput(statements=lines)
            statements = [c for c in RESPONSES if c in prompt]
            return NLIStatementOutput(
                statements=[
                    StatementFaithfulnessAnswer(statement=s, reason="r", verdict=int("3.6.0" in s))
                    for s in statements
                ]
            )

    return Fake()


RESPONSES = (
    "Kafka 3.6.0 has the bug: it was seen, reproduced or logged on 3.6.0.",
    "The bug is fixed in Kafka 3.7.1.",
    "The bug was introduced in Kafka 3.6.0: 3.6.0 is the first release that has it.",
)


def test_ragas_scores_each_issue_and_averages(fake_llm):
    scored = ragas_judge.score(RESULTS, ISSUES, fake_llm)
    assert scored["library"].startswith("ragas ")
    assert scored["by_issue"] == {"K": 0.5, "L": 1.0}
    assert (scored["samples"], scored["scored"], scored["faithfulness"]) == (2, 2, 0.75)
    assert len(fake_llm.prompts) == 4  # two calls per sample


def test_samples_are_spaced_to_a_requests_per_minute_cap(fake_llm):
    start = time.monotonic()
    ragas_judge.score(RESULTS, ISSUES, fake_llm, requests_per_minute=600)  # 0.2 s per sample
    assert time.monotonic() - start >= 0.2  # two samples: one gap between them


def test_an_issue_ragas_cant_score_is_left_out(fake_llm):
    failing = [*RESULTS, result("F", "F@a", {"evidence": [AFFECTS], "context": ["FAIL"]})]
    scored = ragas_judge.score(failing, ISSUES, fake_llm)
    assert scored["by_issue"]["F"] is None
    assert (scored["samples"], scored["scored"], scored["faithfulness"]) == (3, 2, 0.75)


def test_judge_needs_a_model_and_a_known_mode(monkeypatch):
    pytest.importorskip("ragas")
    monkeypatch.delenv("DEP_WATCH_RAGAS_MODEL", raising=False)
    with pytest.raises(ValueError, match="DEP_WATCH_RAGAS_MODEL"):
        ragas_judge.judge_from_env()
    monkeypatch.setenv("DEP_WATCH_RAGAS_MODEL", "gemma2-9b-it")
    monkeypatch.setenv("DEP_WATCH_RAGAS_MODE", "xml")
    with pytest.raises(ValueError, match="DEP_WATCH_RAGAS_MODE"):
        ragas_judge.judge_from_env()


def test_judge_talks_to_any_openai_compatible_api(monkeypatch):
    pytest.importorskip("ragas")
    monkeypatch.setenv("DEP_WATCH_RAGAS_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv(
        "DEP_WATCH_RAGAS_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    monkeypatch.setenv("DEP_WATCH_RAGAS_API_KEY", "test-key")
    monkeypatch.delenv("DEP_WATCH_RAGAS_MODE", raising=False)
    llm, model = ragas_judge.judge_from_env()  # builds the client; no request is made
    assert model == "gemini-2.5-flash"
    assert llm.model_args["temperature"] == 0.0
    assert "generativelanguage.googleapis.com" in str(llm.client.client.base_url)
