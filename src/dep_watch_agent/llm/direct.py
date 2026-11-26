"""The direct-verdict control over an LLM: the model is asked for the answer for one version, with
a citation, and ``direct.check_answer`` only checks the citation.

One model call per config (and chunk), where an extractor makes one per issue. Long issues are
read in the same chunks as by the extractor; ``direct.combine`` merges the chunks' answers.
"""

import logging
from typing import Any

from dep_watch_agent.direct import DirectAnswer, check_answer, combine
from dep_watch_agent.llm.extractor import FactModel, InvalidOutput, Prompt, _tag, issue_chunks
from dep_watch_agent.verdict import ANSWERS, INSUFFICIENT_INFORMATION, Decision, IssueText

log = logging.getLogger(__name__)

DIRECT_PROMPT_NAME = "direct_verdict"
DIRECT_PARSER_VERSION = 1

DIRECT_SCHEMA: dict[str, Any] = {
    "title": "verdict",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "answer": {"type": "string", "enum": list(ANSWERS)},
        "quote": {"type": "string"},
    },
    "required": ["answer", "quote"],
}


class LLMDirect:
    def __init__(
        self,
        model: FactModel,
        *,
        prompt: Prompt,
        chunk_chars: int = 30_000,
        max_chunks: int = 6,
        retries: int = 1,
        model_id: str = "unknown",
    ):
        self.model = model
        self.prompt = prompt
        self.chunk_chars = chunk_chars
        self.max_chunks = max_chunks
        self.retries = retries
        self.model_id = model_id

    @property
    def version(self) -> str:
        return (
            f"model={self.model_id};prompt={self.prompt.name}@{self.prompt.version};"
            f"chunks={self.chunk_chars}x{self.max_chunks};parser=direct-{DIRECT_PARSER_VERSION}"
        )

    def answer(self, issue: IssueText, version: str) -> Decision:
        chunks = issue_chunks(issue, self.chunk_chars)[: self.max_chunks]
        question = _tag("version", version)
        return combine(
            [check_answer(issue, version, self._ask(f"{c}\n\n{question}")) for c in chunks]
        )

    def _ask(self, user: str) -> DirectAnswer:
        """The model's answer for one chunk. Output that stays invalid after the retries is an
        abstention; errors reaching the model are raised."""
        for attempt in range(self.retries + 1):
            try:
                return parse_direct(self.model(self.prompt.text, user))
            except InvalidOutput as exc:
                log.warning("invalid model output (attempt %d): %s", attempt + 1, exc)
        return DirectAnswer(INSUFFICIENT_INFORMATION)


def parse_direct(output: Any) -> DirectAnswer:
    """``{"answer", "quote"}``. An answer that isn't one of the three is kept, so
    ``check_answer`` records it as dropped."""
    if not isinstance(output, dict) or not isinstance(output.get("answer"), str):
        raise InvalidOutput(f"expected {{'answer': ..., 'quote': ...}}, got {str(output)[:200]!r}")
    quote = output.get("quote")
    return DirectAnswer(output["answer"].strip(), quote.strip() if isinstance(quote, str) else "")
