"""An LLM system: the model reads the issue text and returns cited version facts as JSON.

The model only extracts. ``verdict.decide`` checks every quote against the issue and makes the
decision. The model sits behind ``FactModel`` (a system prompt and a user message in, a JSON
object out), so tests use a fake and any OpenAI-compatible server can serve it (``chat.py``).

Long issues are split into chunks that each fit the model's context. Every chunk repeats the
summary and the fix versions, and the facts from all chunks are merged.
"""

import hashlib
import logging
from dataclasses import dataclass
from importlib import resources
from typing import Any, Protocol

from dep_watch_agent.verdict import Evidence, Extraction, IssueText

log = logging.getLogger(__name__)

PROMPT_NAME = "extract_facts"

FACTS_SCHEMA: dict[str, Any] = {
    "title": "facts",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "version": {"type": "string"},
                    "kind": {
                        "type": "string",
                        "enum": ["introduced", "affects", "unaffected", "fix"],
                    },
                    "quote": {"type": "string"},
                },
                "required": ["version", "kind", "quote"],
            },
        }
    },
    "required": ["evidence"],
}


class FactModel(Protocol):
    def __call__(self, system: str, user: str) -> Any:
        """Return the model's JSON object (``FACTS_SCHEMA``). May raise on a bad response."""
        ...


class InvalidOutput(ValueError):
    """The model's output doesn't have the shape of ``FACTS_SCHEMA``."""


@dataclass(frozen=True)
class Prompt:
    name: str
    text: str

    @property
    def version(self) -> str:
        """Content hash, so an eval run can be tied to the exact prompt it used."""
        return hashlib.sha256(self.text.encode()).hexdigest()[:12]


def load_prompt(name: str = PROMPT_NAME) -> Prompt:
    text = resources.files("dep_watch_agent.llm").joinpath("prompts", f"{name}.md").read_text()
    return Prompt(name, text)


class LLMExtractor:
    def __init__(
        self,
        model: FactModel,
        *,
        prompt: Prompt | None = None,
        chunk_chars: int = 30_000,
        max_chunks: int = 6,
        retries: int = 1,
    ):
        self.model = model
        self.prompt = prompt or load_prompt()
        self.chunk_chars = chunk_chars
        self.max_chunks = max_chunks
        self.retries = retries

    def extract(self, issue: IssueText) -> Extraction:
        chunks = issue_chunks(issue, self.chunk_chars)
        if len(chunks) > self.max_chunks:
            log.warning(
                "issue split into %d chunks; reading the first %d", len(chunks), self.max_chunks
            )
        evidence: list[Evidence] = []
        for chunk in chunks[: self.max_chunks]:
            for ev in self._extract_chunk(chunk):
                if ev not in evidence:
                    evidence.append(ev)
        return Extraction(evidence)

    def _extract_chunk(self, user: str) -> list[Evidence]:
        """Facts from one chunk. Output that stays invalid after the retries counts as no
        facts (the decision abstains); errors reaching the model are raised."""
        for attempt in range(self.retries + 1):
            try:
                return parse_facts(self.model(self.prompt.text, user))
            except InvalidOutput as exc:
                log.warning("invalid model output (attempt %d): %s", attempt + 1, exc)
        return []


def parse_facts(output: Any) -> list[Evidence]:
    """Facts from the model's JSON. Items with missing fields are skipped; an unknown ``kind``
    is kept so ``verdict.decide`` drops it with a reason."""
    if not isinstance(output, dict) or not isinstance(output.get("evidence"), list):
        raise InvalidOutput(f"expected {{'evidence': [...]}}, got {str(output)[:200]!r}")
    facts = []
    for item in output["evidence"]:
        if not isinstance(item, dict):
            continue
        values = [item.get(k) for k in ("version", "kind", "quote")]
        if all(isinstance(v, str) and v.strip() for v in values):
            version, kind, quote = (v.strip() for v in values)
            facts.append(Evidence(version, kind, quote))  # type: ignore[arg-type]
    return facts


def issue_chunks(issue: IssueText, max_chars: int) -> list[str]:
    """The user messages for one issue. Fields are tagged so the model can quote inside one
    field; a field longer than a chunk is split on line breaks."""
    header = [
        _tag("fix_versions", ", ".join(issue.fix_versions) or "none"),
        _tag("summary", issue.summary),
    ]
    budget = max(max_chars - sum(len(h) for h in header), 1_000)
    fields = [("description", issue.description)] + [("comment", c) for c in issue.comments]
    pieces = [
        _tag(name, part) for name, text in fields if text.strip() for part in _split(text, budget)
    ]

    chunks: list[list[str]] = [[]]
    size = 0
    for piece in pieces:
        if chunks[-1] and size + len(piece) > budget:
            chunks.append([])
            size = 0
        chunks[-1].append(piece)
        size += len(piece)
    return ["\n\n".join(header + chunk) for chunk in chunks]


def _tag(name: str, text: str) -> str:
    return f"<{name}>\n{text.strip()}\n</{name}>"


def _split(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts: list[str] = []
    current = ""
    for line in text.splitlines(keepends=True):
        while len(line) > max_chars:  # one enormous line, e.g. a minified log
            parts.append(current + line[: max_chars - len(current)])
            line = line[max_chars - len(current) :]
            current = ""
        if len(current) + len(line) > max_chars:
            parts.append(current)
            current = ""
        current += line
    if current:
        parts.append(current)
    return parts
