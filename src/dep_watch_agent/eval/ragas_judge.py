"""Faithfulness scored by the RAGAS library (``ragas.metrics.collections.Faithfulness``).

The in-house judge (``faithfulness.score``) follows RAGAS's definition with its own prompt; this
runs RAGAS itself, so the score is the one RAGAS reports and the two can be compared.

One RAGAS sample per issue: the response is the issue's kept facts as claims, one sentence each
("Kafka 3.6.0 has the bug: it was seen, reproduced or logged on 3.6.0."), and the retrieved
contexts are the passages the system read (a retrieval run) or the issue's text up to
``max_context_chars``. RAGAS splits the response into statements and checks each against the
context with its own prompts: two judge calls per sample. The run's faithfulness is the mean
over samples, as ``ragas.evaluate`` reports it; a sample RAGAS can't score (no statements, or
the judge's output stays invalid) is left out.

The judge is any OpenAI-compatible chat endpoint (``judge_from_env``): Groq, Gemini's OpenAI
endpoint, or LM Studio. As for the in-house judge, it is never the model under test.

RAGAS is not a project dependency: its ``instructor`` pins ``jiter<0.15``, which holds ``openai``
below the project's version. It runs in an overlay environment instead, which leaves the
project's packages as they are (``RAGAS`` is the version scored with):

    uv run --with ragas==0.4.4 python scripts/eval/ragas_judge.py <run.json>...
"""

import asyncio
import logging
import math
import os
from dataclasses import dataclass
from typing import Any

from dep_watch_agent.eval.faithfulness import MAX_CONTEXT_CHARS, claim
from dep_watch_agent.eval.metrics import CaseResult
from dep_watch_agent.llm.extractor import issue_chunks
from dep_watch_agent.verdict import IssueText

log = logging.getLogger(__name__)

RAGAS = "ragas==0.4.4"
QUESTION = "Which Kafka releases have this bug, according to its bug report?"
# instructor modes by name. md_json asks for JSON in the reply and needs no response_format
# support from the server, so it works on any chat endpoint; json uses response_format.
MODES = ("md_json", "json", "tools")


@dataclass(frozen=True)
class Sample:
    issue_key: str
    claims: tuple[str, ...]
    contexts: tuple[str, ...]

    @property
    def response(self) -> str:
        return "\n".join(self.claims)


def samples(
    results: list[CaseResult],
    issues: dict[str, dict[str, Any]],
    *,
    max_context_chars: int = MAX_CONTEXT_CHARS,
) -> list[Sample]:
    """One sample per issue with kept facts, in run order. The two cases of an issue share one
    reading, so their facts are pooled; a claim made twice is kept once."""
    claims: dict[str, dict[str, None]] = {}  # issue -> ordered set of claims
    contexts: dict[str, list[str] | None] = {}
    for r in results:
        for ev in r.output.get("evidence", []):
            claims.setdefault(r.issue_key, {})[claim(ev["kind"], ev["version"])] = None
            contexts.setdefault(r.issue_key, r.output.get("context"))
    out = []
    for key, issue_claims in claims.items():
        read = contexts[key]
        if not read:
            whole = issue_chunks(IssueText.from_dict(issues[key]), max_context_chars)[0]
            read = [whole[:max_context_chars]]  # the chunk's tags can run a little past it
        out.append(Sample(key, tuple(issue_claims), tuple(read)))
    return out


def score(
    results: list[CaseResult],
    issues: dict[str, dict[str, Any]],
    llm: Any,
    *,
    max_context_chars: int = MAX_CONTEXT_CHARS,
) -> dict[str, Any]:
    """RAGAS faithfulness of the run's kept facts: the mean over issues, and each issue's."""
    import ragas
    from ragas.metrics.collections import Faithfulness

    metric = Faithfulness(llm=llm)
    todo = samples(results, issues, max_context_chars=max_context_chars)

    async def run() -> dict[str, float | None]:
        by_issue: dict[str, float | None] = {}
        for sample in todo:  # one at a time: hosted free tiers limit requests per minute
            try:
                result = await metric.ascore(
                    user_input=QUESTION,
                    response=sample.response,
                    retrieved_contexts=list(sample.contexts),
                )
                value = None if math.isnan(result.value) else float(result.value)
            except Exception as exc:  # the judge's output stayed invalid, or the call failed
                log.warning("RAGAS could not score %s: %s", sample.issue_key, exc)
                value = None
            by_issue[sample.issue_key] = value
        return by_issue

    by_issue = asyncio.run(run())
    scored = [v for v in by_issue.values() if v is not None]
    return {
        "library": f"ragas {ragas.__version__}",
        "samples": len(todo),
        "scored": len(scored),
        "faithfulness": sum(scored) / len(scored) if scored else None,
        "by_issue": by_issue,
    }


def agreement(
    by_issue: dict[str, float | None], judgments: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """RAGAS against the in-house judge on the issues both scored: the in-house score of an
    issue is the share of its facts it found supported. None if they share no issue."""
    inhouse: dict[str, list[bool]] = {}
    for j in judgments:
        if j.get("supported") is not None:
            inhouse.setdefault(j["issue_key"], []).append(j["supported"])
    pairs = [
        (v, sum(inhouse[k]) / len(inhouse[k]))
        for k, v in by_issue.items()
        if v is not None and k in inhouse
    ]
    if not pairs:
        return None
    return {
        "issues": len(pairs),
        "ragas": sum(a for a, _ in pairs) / len(pairs),
        "inhouse": sum(b for _, b in pairs) / len(pairs),
        "mean_abs_diff": sum(abs(a - b) for a, b in pairs) / len(pairs),
        # Both call the issue fully supported, or both don't.
        "same_all_supported": sum((a == 1.0) == (b == 1.0) for a, b in pairs) / len(pairs),
    }


def judge_from_env() -> tuple[Any, str]:
    """The RAGAS judge and its model id, from the environment:

    - ``DEP_WATCH_RAGAS_MODEL`` (required), e.g. a Groq or Gemini model id;
    - ``DEP_WATCH_RAGAS_BASE_URL`` (default LM Studio, ``http://localhost:1234/v1``), e.g.
      ``https://api.groq.com/openai/v1`` or
      ``https://generativelanguage.googleapis.com/v1beta/openai/``;
    - ``DEP_WATCH_RAGAS_API_KEY``;
    - ``DEP_WATCH_RAGAS_MODE``: one of ``MODES`` (default ``md_json``);
    - ``DEP_WATCH_RAGAS_MAX_TOKENS`` (default 2048), ``DEP_WATCH_RAGAS_MAX_RETRIES`` (default 6,
      with backoff, for rate limits), ``DEP_WATCH_RAGAS_TIMEOUT`` (seconds, default 300),
      ``DEP_WATCH_RAGAS_REASONING_EFFORT`` (``none`` turns a local thinking model's reasoning
      off; unset sends nothing).
    """
    import instructor
    from openai import AsyncOpenAI
    from ragas.llms import llm_factory

    model = os.environ.get("DEP_WATCH_RAGAS_MODEL", "").strip()
    if not model:
        raise ValueError(
            "set DEP_WATCH_RAGAS_MODEL to the judge model (never the model under test)"
        )
    mode = os.environ.get("DEP_WATCH_RAGAS_MODE", "md_json").strip()
    if mode not in MODES:
        raise ValueError(f"DEP_WATCH_RAGAS_MODE must be one of {MODES}, got {mode!r}")
    client = AsyncOpenAI(
        base_url=os.environ.get("DEP_WATCH_RAGAS_BASE_URL", "http://localhost:1234/v1"),
        api_key=os.environ.get("DEP_WATCH_RAGAS_API_KEY") or "not-needed",
        max_retries=int(os.environ.get("DEP_WATCH_RAGAS_MAX_RETRIES", "6")),
        timeout=float(os.environ.get("DEP_WATCH_RAGAS_TIMEOUT", "300")),
    )
    extra: dict[str, Any] = {}
    if effort := os.environ.get("DEP_WATCH_RAGAS_REASONING_EFFORT", "").strip():
        extra["reasoning_effort"] = effort
    llm = llm_factory(
        model,
        provider="openai",
        client=client,
        # The OpenAI-compatible endpoint for every provider, Gemini's included; ragas would
        # otherwise route a "gemini-*" model through LiteLLM.
        adapter="instructor",
        mode={
            "md_json": instructor.Mode.MD_JSON,
            "json": instructor.Mode.JSON,
            "tools": instructor.Mode.TOOLS,
        }[mode],
        temperature=0.0,
        max_tokens=int(os.environ.get("DEP_WATCH_RAGAS_MAX_TOKENS", "2048")),
        **extra,
    )
    return llm, model
