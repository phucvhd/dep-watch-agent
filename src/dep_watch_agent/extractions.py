"""Stored extractions: run a system on an issue once, answer any version from its facts.

An extraction is reused when the issue text the system sees, the system and its
``extractor.version`` are all unchanged. A system without a ``version`` attribute (e.g. a test
fake) is never stored, since nothing would tell its stored facts apart from new ones.

A re-check (``refresh``) reads the issue again and replaces the stored facts: the model is not
deterministic, and a reader who doubts a stored answer can ask for a fresh one.
"""

import hashlib
import json
import time
from dataclasses import asdict, dataclass

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from dep_watch_agent.eval.runner import Extractor
from dep_watch_agent.orm import ExtractionRow
from dep_watch_agent.verdict import Evidence, Extraction, IssueText


class ExtractionFailed(RuntimeError):
    """The system couldn't read the issue: its model server is down, or its output was invalid.
    Nothing is stored."""


@dataclass(frozen=True)
class Extracted:
    extraction: Extraction
    cached: bool


def text_hash(text: IssueText) -> str:
    """Hash of exactly what the system sees, so edits that don't reach it (status, assignee,
    a bot comment) keep the stored facts valid."""
    canonical = json.dumps(asdict(text), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _key(issue_id: int, text: IssueText, system: str, version: str) -> dict:
    return {
        "issue_id": issue_id,
        "system": system,
        "extractor_version": version,
        "text_hash": text_hash(text),
    }


def stored(
    session: Session, issue_id: int, text: IssueText, system: str, extractor: Extractor
) -> Extraction | None:
    """The stored extraction for this text, system and version, without calling the system."""
    version = getattr(extractor, "version", None)
    if version is None:
        return None
    key = _key(issue_id, text, system, version)
    row = session.scalars(select(ExtractionRow).filter_by(**key)).one_or_none()
    return Extraction([Evidence(**e) for e in row.evidence]) if row else None


def stored_texts(
    session: Session, issue_ids: list[int], system: str, extractor: Extractor
) -> set[tuple[int, str]]:
    """``(issue_id, text_hash)`` of every stored extraction among ``issue_ids`` for this system
    and version: one query for a whole scan's worth of issues."""
    version = getattr(extractor, "version", None)
    if version is None or not issue_ids:
        return set()
    rows = session.execute(
        select(ExtractionRow.issue_id, ExtractionRow.text_hash).where(
            ExtractionRow.issue_id.in_(issue_ids),
            ExtractionRow.system == system,
            ExtractionRow.extractor_version == version,
        )
    )
    return {(issue_id, digest) for issue_id, digest in rows}


def extract(
    session: Session,
    issue_id: int,
    text: IssueText,
    system: str,
    extractor: Extractor,
    *,
    refresh: bool = False,
) -> Extracted:
    """The stored extraction for this text, system and version, or a new one, stored and
    committed so a long scan keeps what it has paid for. With ``refresh``, always a new one,
    replacing what was stored."""
    version = getattr(extractor, "version", None)
    if version is None:
        return Extracted(_read(extractor, text, system), cached=False)

    if not refresh:
        known = stored(session, issue_id, text, system, extractor)
        if known is not None:
            return Extracted(known, cached=True)
    key = _key(issue_id, text, system, version)

    start = time.monotonic()
    extraction = _read(extractor, text, system)
    duration_ms = int((time.monotonic() - start) * 1000)
    evidence = [asdict(e) for e in extraction.evidence]
    stmt = insert(ExtractionRow).values(**key, evidence=evidence, duration_ms=duration_ms)
    if refresh:
        stmt = stmt.on_conflict_do_update(
            index_elements=list(key),
            set_={"evidence": evidence, "duration_ms": duration_ms, "created_at": func.now()},
        )
    else:  # two requests may extract the same issue at once; the first to commit wins
        stmt = stmt.on_conflict_do_nothing()
    session.execute(stmt)
    session.commit()
    return Extracted(extraction, cached=False)


def _read(extractor: Extractor, text: IssueText, system: str) -> Extraction:
    try:
        return extractor.extract(text)
    except Exception as exc:
        raise ExtractionFailed(f"{system} could not read the issue: {exc}") from exc
