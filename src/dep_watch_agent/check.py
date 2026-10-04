"""Answer "does this issue affect my Kafka version?" for one synced issue.

The system sees exactly what it sees in the eval (design v2): the issue's free text, minus
comments from bots, plus the fix versions JIRA lists. JIRA's affected versions are not given;
where the bug starts has to come from the text. The decision is made by ``verdict.decide``.

Code goes first: if the given fix versions already put the version past the fix, the answer is
``not_affected`` and the system is not called. Otherwise the system's facts are stored
(``extractions.py``), so asking again, or about another version, reuses them.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from dep_watch_agent import extractions
from dep_watch_agent.eval.runner import Extractor
from dep_watch_agent.eval.sampling import EXCLUDED_COMMENT_AUTHORS, JIRA_BROWSE_URL
from dep_watch_agent.orm import JiraIssueRow
from dep_watch_agent.verdict import NOT_AFFECTED, Decision, Extraction, IssueText, decide


class IssueNotFound(LookupError):
    pass


@dataclass(frozen=True)
class CheckResult:
    issue: JiraIssueRow
    issue_text: IssueText
    kafka_version: str
    system: str
    decision: Decision
    decided_by: str  # FIX_VERSIONS, or the system's name
    cached: bool  # the system's facts were stored from an earlier run

    @property
    def url(self) -> str:
        return issue_url(self.issue.key)


def issue_url(key: str) -> str:
    return JIRA_BROWSE_URL + key


def load_issue(session: Session, key: str) -> JiraIssueRow:
    issue = session.scalars(
        select(JiraIssueRow)
        .where(JiraIssueRow.key == key)
        .options(
            selectinload(JiraIssueRow.versions),
            selectinload(JiraIssueRow.components),
            selectinload(JiraIssueRow.comments),
        )
    ).one_or_none()
    if issue is None:
        raise IssueNotFound(key)
    return issue


def issue_text(issue: JiraIssueRow) -> IssueText:
    """What a system may see of a synced issue."""
    return IssueText(
        summary=issue.summary,
        description=issue.description or "",
        comments=[
            c.body
            for c in issue.comments
            if c.author not in EXCLUDED_COMMENT_AUTHORS and c.body.strip()
        ],
        fix_versions=sorted(v.name for v in issue.versions if v.kind == "fix"),
    )


FIX_VERSIONS = "fix_versions"


@dataclass(frozen=True)
class Answered:
    decision: Decision
    decided_by: str  # FIX_VERSIONS, or the system's name
    cached: bool = False


def answer_issue(
    session: Session,
    issue_id: int,
    text: IssueText,
    kafka_version: str,
    system: str,
    extractor: Extractor,
) -> Answered:
    """The decision and what decided it: the fix versions alone, or ``system``'s facts (stored
    ones when the text, system and extractor version are unchanged)."""
    by_fixes = decide(text, kafka_version, Extraction([]))
    if by_fixes.answer == NOT_AFFECTED:
        return Answered(by_fixes, FIX_VERSIONS)
    extracted = extractions.extract(session, issue_id, text, system, extractor)
    return Answered(decide(text, kafka_version, extracted.extraction), system, extracted.cached)


def check_issue(
    session: Session, key: str, kafka_version: str, system: str, extractor: Extractor
) -> CheckResult:
    """Decide whether ``kafka_version`` is affected by issue ``key``, with ``extractor``
    (registered as ``system``).

    ``kafka_version`` must already be validated as a release (``verdict.is_release``).
    """
    issue = load_issue(session, key)
    text = issue_text(issue)
    answered = answer_issue(session, issue.id, text, kafka_version, system, extractor)
    return CheckResult(
        issue, text, kafka_version, system, answered.decision, answered.decided_by, answered.cached
    )
