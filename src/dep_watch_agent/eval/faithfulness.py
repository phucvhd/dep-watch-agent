"""Faithfulness of a run's facts to the text the system read, scored by a judge model.

This follows RAGAS's faithfulness: the share of an answer's claims that the retrieved context
supports, each claim checked by an LLM judge. Here the claims are already atomic, one per
fact a system extracted and ``decide`` kept ("Kafka 3.6.0 has the bug"), so RAGAS's
claim-splitting step is not needed. The context is the passages the system read for a
retrieval run (``output["context"]``), else the issue's whole text. A kept fact's quote is
always verbatim in the issue; faithfulness asks whether it says what the fact claims.

The judge is never the model under test (``JudgeIsModelUnderTest``): a model grading its own
reading would share its blind spots. ``DEP_WATCH_JUDGE_MODEL`` names it, served like the
systems' model (``DEP_WATCH_JUDGE_BASE_URL``, default ``DEP_WATCH_LLM_BASE_URL``).

``context_recall`` needs no judge: for a retrieval run, the share of the labeled evidence
quotes (``label_evidence.jsonl``) that are inside the passages read, over the cases that have
any. It measures whether retrieval kept the decisive sentence.
"""

import json
import logging
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Protocol

from dep_watch_agent.eval.metrics import CaseResult
from dep_watch_agent.llm.extractor import InvalidOutput, _tag, issue_chunks
from dep_watch_agent.verdict import IssueText

log = logging.getLogger(__name__)

JUDGE_SCHEMA: dict[str, Any] = {
    "title": "judgment",
    "type": "object",
    "additionalProperties": False,
    "properties": {"supported": {"type": "boolean"}},
    "required": ["supported"],
}

CLAIMS = {
    "introduced": "The bug was introduced in Kafka {v}: {v} is the first release that has it.",
    "affects": "Kafka {v} has the bug: it was seen, reproduced or logged on {v}.",
    "unaffected": "Kafka {v} does not have the bug.",
    "fix": "The bug is fixed in Kafka {v}.",
}
MAX_CONTEXT_CHARS = 30_000


class JudgeIsModelUnderTest(ValueError):
    pass


class Judge(Protocol):
    def __call__(self, system: str, user: str) -> Any: ...


def claim(kind: str, version: str) -> str:
    return CLAIMS.get(kind, "Kafka {v}: " + kind).format(v=version)


def _same_model(a: str, b: str) -> bool:
    def norm(m: str) -> str:
        return m.split(";", 1)[0].rsplit("/", 1)[-1].lower()

    return norm(a) == norm(b)


def check_judge(judge_model: str, run_model: str | None) -> None:
    if run_model and _same_model(judge_model, run_model):
        raise JudgeIsModelUnderTest(f"{judge_model} would judge its own run; use another model")


def score(
    results: list[CaseResult],
    issues: dict[str, dict[str, Any]],
    judge: Judge,
    prompt: str,
    *,
    retries: int = 1,
) -> dict[str, Any]:
    """Judge every distinct kept fact of the run once. Returns the faithfulness, per kind, and
    the judgments. A judgment that stays invalid after the retries is left out of the score."""
    seen: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for r in results:
        context = r.output.get("context")
        for ev in r.output.get("evidence", []):
            key = (r.issue_key, ev["version"], ev["kind"], ev["quote"])
            if key not in seen:
                seen[key] = {"context": context, "evidence": ev, "issue_key": r.issue_key}

    judgments = []
    for (issue_key, version, kind, _), item in seen.items():
        context = item["context"] or _whole_text(IssueText.from_dict(issues[issue_key]))
        user = _tag("context", "\n\n".join(context) if isinstance(context, list) else context)
        user = f"{user[:MAX_CONTEXT_CHARS]}\n\n{_tag('statement', claim(kind, version))}"
        supported = _ask(judge, prompt, user, retries)
        judgments.append({**item["evidence"], "issue_key": issue_key, "supported": supported})

    judged = [j for j in judgments if j["supported"] is not None]
    by_kind: dict[str, list[bool]] = defaultdict(list)
    for j in judged:
        by_kind[j["kind"]].append(j["supported"])
    return {
        "facts": len(judgments),
        "judged": len(judged),
        "faithfulness": sum(j["supported"] for j in judged) / len(judged) if judged else None,
        "by_kind": {k: sum(v) / len(v) for k, v in sorted(by_kind.items())},
        "judgments": judgments,
    }


def _ask(judge: Judge, prompt: str, user: str, retries: int) -> bool | None:
    for attempt in range(retries + 1):
        try:
            output = judge(prompt, user)
            if isinstance(output, dict) and isinstance(output.get("supported"), bool):
                return output["supported"]
            raise InvalidOutput(f"expected {{'supported': bool}}, got {str(output)[:200]!r}")
        except InvalidOutput as exc:
            log.warning("invalid judge output (attempt %d): %s", attempt + 1, exc)
    return None


def _whole_text(issue: IssueText) -> str:
    return issue_chunks(issue, MAX_CONTEXT_CHARS)[0]


def read_label_evidence(directory: Path) -> dict[str, list[str]]:
    path = directory / "label_evidence.jsonl"
    if not path.is_file():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            record = json.loads(line)
            out[record["case_id"]] = [
                q["quote"] if isinstance(q, dict) else q for q in record.get("quotes", [])
            ]
    return out


def context_recall(results: list[CaseResult], gold: dict[str, list[str]]) -> dict[str, Any] | None:
    """Over the cases read through retrieval that have labeled quotes: the share of those quotes
    inside the passages read. None if no such case."""
    found = total = 0
    cases = 0
    for r in results:
        context = r.output.get("context")
        quotes = gold.get(r.case_id) or []
        if context is None or not quotes:
            continue
        cases += 1
        read = _norm("\n".join(context))
        for quote in quotes:
            total += 1
            found += _norm(quote) in read
    if not total:
        return None
    return {"cases": cases, "quotes": total, "recall": found / total}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def judge_from_env() -> tuple[Any, str]:
    """The judge model from ``DEP_WATCH_JUDGE_MODEL``, and its id."""
    from dataclasses import replace

    from dep_watch_agent.llm.chat import ChatFactModel, LLMConfig

    model = os.environ.get("DEP_WATCH_JUDGE_MODEL", "").strip()
    if not model:
        raise ValueError(
            "set DEP_WATCH_JUDGE_MODEL to the judge model (never the model under test)"
        )
    base = LLMConfig.from_env() or LLMConfig(base_url="http://localhost:1234/v1", model=model)
    config = replace(
        base,
        model=model,
        base_url=os.environ.get("DEP_WATCH_JUDGE_BASE_URL", base.base_url),
        output="text",
        # Room for a reasoning judge to think before its one-field answer.
        max_tokens=int(os.environ.get("DEP_WATCH_JUDGE_MAX_TOKENS", "2048")) or None,
        reasoning_effort=os.environ.get("DEP_WATCH_JUDGE_REASONING_EFFORT", "").strip() or None,
    )
    return ChatFactModel(config, schema=JUDGE_SCHEMA, run_name="judge_faithfulness"), model
