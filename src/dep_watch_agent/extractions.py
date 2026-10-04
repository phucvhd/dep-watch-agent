"""Stored extractions: run a system on an issue once, answer any Kafka version from its facts.

An extraction is reused when the issue text the system sees, the system and its
``extractor.version`` are all unchanged. A system without a ``version`` attribute (e.g. a test
fake) is never stored, since nothing would tell its stored facts apart from new ones.
"""

import hashlib
import json
import time
from dataclasses import asdict, dataclass

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from dep_watch_agent.eval.runner import Extractor
from dep_watch_agent.orm import ExtractionRow
from dep_watch_agent.verdict import Evidence, Extraction, IssueText


@dataclass(frozen=True)
class Extracted:
    extraction: Extraction
    cached: bool


def text_hash(text: IssueText) -> str:
    """Hash of exactly what the system sees, so edits that don't reach it (status, assignee,
    a bot comment) keep the stored facts valid."""
    canonical = json.dumps(asdict(text), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def extract(
    session: Session, issue_id: int, text: IssueText, system: str, extractor: Extractor
) -> Extracted:
    """The stored extraction for this text, system and version, or a new one, stored and
    committed so a long scan keeps what it has paid for."""
    version = getattr(extractor, "version", None)
    if version is None:
        return Extracted(extractor.extract(text), cached=False)

    key = {
        "issue_id": issue_id,
        "system": system,
        "extractor_version": version,
        "text_hash": text_hash(text),
    }
    row = session.scalars(select(ExtractionRow).filter_by(**key)).one_or_none()
    if row is not None:
        return Extracted(Extraction([Evidence(**e) for e in row.evidence]), cached=True)

    start = time.monotonic()
    extraction = extractor.extract(text)
    duration_ms = int((time.monotonic() - start) * 1000)
    evidence = [asdict(e) for e in extraction.evidence]
    # Two requests may extract the same issue at once; the first to commit wins.
    session.execute(
        insert(ExtractionRow)
        .values(**key, evidence=evidence, duration_ms=duration_ms)
        .on_conflict_do_nothing()
    )
    session.commit()
    return Extracted(extraction, cached=False)
