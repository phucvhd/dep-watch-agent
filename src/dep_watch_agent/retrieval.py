"""Hybrid retrieval inside one issue, for RQ3: on a long thread, read only the passages most
likely to state a version fact instead of the whole text.

An issue's free-text fields are split into passages (paragraphs, long ones split on lines),
each embedded once and stored in ``issue_passages`` with pgvector. Passages are ranked two
ways in PostgreSQL and the rankings fused by reciprocal rank (``RRF_K``):

- dense: cosine distance to a fixed question about versions (Qwen3-Embedding's query
  instruction format), so "since we moved to the new release" still ranks;
- lexical: ``ts_rank`` against version-statement words and every release named in the issue
  or its fix versions. Embeddings of ``3.10.0`` and ``3.9.0`` are nearly identical; exact
  identifiers need lexical matching.

``HybridExtractor`` reads an issue whole when it fits ``budget_chars``, as the plain extractor
does; a longer one is read as its summary, fix versions and the best passages that fit the
budget, in their original order. Each passage is a substring of one field, so quotes from it
pass the citation check like any other. The passages read are kept on the extraction
(``Extraction.context``) for scoring the retrieval.

The extraction is version-independent like every other, so the lexical query names every
release in the issue, not the one asked about.
"""

import hashlib
import os
import re
from dataclasses import dataclass
from typing import Protocol

import httpx
from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session, sessionmaker

from dep_watch_agent.llm.extractor import LLMExtractor, _tag
from dep_watch_agent.orm import IssuePassageRow
from dep_watch_agent.verdict import Extraction, IssueText

RRF_K = 60
PASSAGE_CHARS = 800
RETRIEVAL_VERSION = 1

DENSE_QUERY = (
    "Instruct: Given a software bug report, retrieve the passages that say which release the "
    "bug started in, was seen in, was absent from, or was fixed in\n"
    "Query: Which versions have this bug, since when, and where is it fixed?"
)
LEXICAL_WORDS = (
    "regression introduced since upgrade upgrading upgraded downgrade downgraded affected "
    "affects broken broke reproduced reproduce works worked fixed fix release version"
).split()

_RELEASE = re.compile(r"(?<![\w.])v?(\d+\.\d+(?:\.\d+){0,2})(?![\w]|\.\d)")


@dataclass(frozen=True)
class Passage:
    position: int
    field: str  # description or comment
    body: str


def passages(issue: IssueText, max_chars: int = PASSAGE_CHARS) -> list[Passage]:
    """The issue's description and comments as passages: paragraphs, split on lines (and a
    very long line into pieces) to at most ``max_chars``. The summary is always read, so it is
    not a passage."""
    out: list[Passage] = []
    fields = [("description", issue.description)] + [("comment", c) for c in issue.comments]
    for name, body in fields:
        for paragraph in re.split(r"\n\s*\n", body):
            for piece in _pieces(paragraph, max_chars):
                if piece.strip():
                    out.append(Passage(len(out), name, piece.strip()))
    return out


def _pieces(paragraph: str, max_chars: int) -> list[str]:
    if len(paragraph) <= max_chars:
        return [paragraph]
    pieces, current = [], ""
    for line in paragraph.splitlines(keepends=True):
        while len(line) > max_chars:
            pieces.append(current)
            pieces.append(line[:max_chars])
            line, current = line[max_chars:], ""
        if len(current) + len(line) > max_chars:
            pieces.append(current)
            current = ""
        current += line
    pieces.append(current)
    return [p for p in pieces if p]


def releases_named(issue: IssueText) -> list[str]:
    """Every release-like token in the issue's text and fix versions, in order of appearance."""
    found: list[str] = []
    for value in [*issue.fields(), *issue.fix_versions]:
        for match in _RELEASE.finditer(value):
            if match.group(1) not in found:
                found.append(match.group(1))
    return found


def lexical_query(issue: IssueText) -> str:
    """A ``to_tsquery`` OR-query of the version-statement words and the issue's releases. Every
    term is letters, digits and dots only, so the string is safe to pass to ``to_tsquery``."""
    terms = LEXICAL_WORDS + releases_named(issue)
    return " | ".join(t for t in terms if re.fullmatch(r"[A-Za-z0-9.]+", t))


class Embedder(Protocol):
    model: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIEmbedder:
    """Embeddings from an OpenAI-compatible ``/embeddings`` endpoint (LM Studio, vLLM, Ollama)."""

    def __init__(self, model: str, base_url: str, api_key: str = "not-needed", timeout=120.0):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "OpenAIEmbedder":
        """``DEP_WATCH_EMBED_MODEL`` (default Qwen3-Embedding-0.6B's LM Studio id),
        ``DEP_WATCH_EMBED_BASE_URL`` (default ``DEP_WATCH_LLM_BASE_URL``)."""
        base = os.environ.get("DEP_WATCH_LLM_BASE_URL", "http://localhost:1234/v1")
        return cls(
            model=os.environ.get("DEP_WATCH_EMBED_MODEL", "text-embedding-qwen3-embedding-0.6b"),
            base_url=os.environ.get("DEP_WATCH_EMBED_BASE_URL", base),
            api_key=os.environ.get("DEP_WATCH_LLM_API_KEY", "not-needed"),
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), 32):
            response = httpx.post(
                f"{self.base_url}/embeddings",
                json={"model": self.model, "input": texts[start : start + 32]},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = sorted(response.json()["data"], key=lambda d: d["index"])
            vectors.extend(d["embedding"] for d in data)
        return vectors


@dataclass(frozen=True)
class Ranked:
    passage: Passage
    score: float


class HybridRetriever:
    def __init__(self, sessions: sessionmaker[Session], embedder: Embedder):
        self.sessions = sessions
        self.embedder = embedder
        self._query_vector: list[float] | None = None

    def rank(self, key: str, issue: IssueText) -> list[Ranked]:
        """The issue's passages, best first."""
        items = passages(issue)
        if not items:
            return []
        with self.sessions() as session:
            self._store(session, key, items)
            rows = session.execute(
                text(_RANK_SQL),
                {
                    "key": key,
                    "model": self.embedder.model,
                    "query": _vector_literal(self._query()),
                    "tsquery": lexical_query(issue),
                    "k": RRF_K,
                },
            ).all()
            session.commit()
        by_position = {p.position: p for p in items}
        return [Ranked(by_position[position], float(score)) for position, score in rows]

    def _query(self) -> list[float]:
        if self._query_vector is None:
            self._query_vector = self.embedder.embed([DENSE_QUERY])[0]
        return self._query_vector

    def _store(self, session: Session, key: str, items: list[Passage]) -> None:
        """Embed and store the passages unless the stored ones are the same text."""
        hashes = {p.position: _hash(p.body) for p in items}
        stored = dict(
            session.execute(
                select(IssuePassageRow.position, IssuePassageRow.text_hash).filter_by(
                    issue_key=key, embed_model=self.embedder.model
                )
            ).all()
        )
        if stored == hashes:
            return
        session.execute(
            delete(IssuePassageRow).filter_by(issue_key=key, embed_model=self.embedder.model)
        )
        vectors = self.embedder.embed([p.body for p in items])
        session.add_all(
            IssuePassageRow(
                issue_key=key,
                embed_model=self.embedder.model,
                position=p.position,
                field=p.field,
                body=p.body,
                text_hash=hashes[p.position],
                embedding=vector,
            )
            for p, vector in zip(items, vectors, strict=True)
        )
        session.flush()


# Reciprocal rank fusion of the dense and lexical rankings of one issue's passages. A passage
# that matches no lexical term has only its dense rank. OPERATOR(public.<=>) because the session
# may be pinned to a schema without public on its path.
_RANK_SQL = """
WITH p AS (
    SELECT position, body, embedding FROM issue_passages
    WHERE issue_key = :key AND embed_model = :model
),
dense AS (
    SELECT position,
           row_number() OVER (
               ORDER BY embedding OPERATOR(public.<=>) CAST(:query AS public.vector), position
           ) AS r
    FROM p
),
lexical AS (
    SELECT position,
           row_number() OVER (
               ORDER BY ts_rank(to_tsvector('english', body), to_tsquery('english', :tsquery))
                        DESC, position
           ) AS r
    FROM p
    WHERE to_tsvector('english', body) @@ to_tsquery('english', :tsquery)
)
SELECT p.position,
       COALESCE(1.0 / (:k + dense.r), 0) + COALESCE(1.0 / (:k + lexical.r), 0) AS score
FROM p
LEFT JOIN dense USING (position)
LEFT JOIN lexical USING (position)
ORDER BY score DESC, p.position
"""


def select_within(ranked: list[Ranked], budget: int) -> list[Passage]:
    """The best passages whose bodies fit ``budget`` characters together, in issue order. A
    passage too big for what is left is skipped for smaller ones further down."""
    chosen: list[Passage] = []
    left = budget
    for r in ranked:
        if len(r.passage.body) <= left:
            chosen.append(r.passage)
            left -= len(r.passage.body)
    return sorted(chosen, key=lambda p: p.position)


def text_chars(issue: IssueText) -> int:
    return sum(len(f) for f in issue.fields())


class HybridExtractor:
    """``LLMExtractor`` that reads a long issue through hybrid retrieval. Passages are stored
    under a hash of the issue's text, so an edited issue is split and embedded again."""

    def __init__(
        self, base: LLMExtractor, retriever: HybridRetriever, *, budget_chars: int = 6_000
    ):
        self.base = base
        self.retriever = retriever
        self.budget_chars = budget_chars

    @property
    def model_id(self) -> str:
        return self.base.model_id

    @property
    def version(self) -> str:
        return (
            f"{self.base.version};retrieval=hybrid-{RETRIEVAL_VERSION}"
            f"@{self.retriever.embedder.model};budget={self.budget_chars};rrf={RRF_K}"
        )

    def extract(self, issue: IssueText) -> Extraction:
        if text_chars(issue) <= self.budget_chars:
            return self.base.extract(issue)
        key = "text:" + _hash("\n".join(issue.fields()))
        chosen = select_within(self.retriever.rank(key, issue), self.budget_chars)
        user = "\n\n".join(
            [
                _tag("fix_versions", ", ".join(issue.fix_versions) or "none"),
                _tag("summary", issue.summary),
                *(_tag(p.field, p.body) for p in chosen),
            ]
        )
        facts = self.base._extract_chunk(user)
        evidence = []
        for ev in facts or []:
            if ev not in evidence:
                evidence.append(ev)
        return Extraction(
            evidence,
            context=[issue.summary, *(p.body for p in chosen)],
            invalid_outputs=int(facts is None),
        )


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in vector) + "]"


def default_retriever() -> HybridRetriever:
    from dep_watch_agent.db import create_db_engine, session_factory

    return HybridRetriever(session_factory(create_db_engine()), OpenAIEmbedder.from_env())
