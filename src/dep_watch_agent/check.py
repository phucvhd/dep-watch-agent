"""Answer "does this issue affect the version I run?" for one synced issue.

The system sees exactly what it sees in the eval (design v2): the issue's free text, minus
comments from bots, plus the fix versions JIRA lists. JIRA's affected versions are not given;
where the bug starts has to come from the text. The decision is made by ``verdict.decide``.

Code goes first: if the given fix versions already put the version past the fix, the answer is
``not_affected`` and the system is not called. Otherwise the system's facts are stored
(``extractions.py``), so asking again, or about another version, reuses them.

Versions are read in the scheme of the issue's dependency, found from its project.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from dep_watch_agent import extractions
from dep_watch_agent.dependencies import Dependency, dependency_for_project
from dep_watch_agent.eval.runner import Extractor
from dep_watch_agent.eval.sampling import EXCLUDED_COMMENT_AUTHORS, JIRA_BROWSE_URL
from dep_watch_agent.orm import JiraIssueRow
from dep_watch_agent.verdict import NOT_AFFECTED, Decision, Extraction, IssueText, decide
from dep_watch_agent.versions import VersionScheme


class IssueNotFound(LookupError):
    pass


class NotAnswerable(ValueError):
    """The project's dependency isn't answered for a version, or ``version`` isn't one of its
    releases."""


def answerable(project: str, version: str) -> Dependency:
    """The dependency to answer ``version`` of ``project`` for. Raises ``NotAnswerable``."""
    dependency = dependency_for_project(project)
    if dependency is None:
        raise NotAnswerable(f"no dependency is synced from project {project}")
    if not dependency.watchable:
        raise NotAnswerable(f"{dependency.name} issues are synced, not answered for a version")
    if not dependency.scheme.is_release(version):
        raise NotAnswerable(
            f"{version!r} is not a specific {dependency.name} release "
            "(a release line such as 3.7 is not one)"
        )
    return dependency


@dataclass(frozen=True)
class CheckResult:
    issue: JiraIssueRow
    issue_text: IssueText
    version: str
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
    version: str,
    scheme: VersionScheme,
    system: str,
    extractor: Extractor,
    *,
    read: bool = True,
) -> Answered | None:
    """The decision and what decided it: the fix versions alone, or ``system``'s facts (stored
    ones when the text, system and extractor version are unchanged). With ``read=False`` the
    system is never called: None when neither settles it."""
    by_fixes = decide(text, version, Extraction([]), scheme)
    if by_fixes.answer == NOT_AFFECTED:
        return Answered(by_fixes, FIX_VERSIONS)
    if not read:
        known = extractions.stored(session, issue_id, text, system, extractor)
        if known is None:
            return None
        return Answered(decide(text, version, known, scheme), system, cached=True)
    extracted = extractions.extract(session, issue_id, text, system, extractor)
    return Answered(decide(text, version, extracted.extraction, scheme), system, extracted.cached)


def check_issue(
    session: Session,
    key: str,
    version: str,
    system: str | None,
    extractor: Extractor | None,
    *,
    read: bool = True,
) -> CheckResult | None:
    """Decide whether ``version`` is affected by issue ``key``, with ``extractor`` (registered
    as ``system``). With ``read=False``, None if that would take a model call. With no
    extractor, only the fix versions can answer; None if they don't.

    Raises ``IssueNotFound``, and ``NotAnswerable`` when the issue's dependency isn't answered
    or ``version`` isn't one of its releases.
    """
    issue = load_issue(session, key)
    scheme = answerable(issue.project, version).scheme
    text = issue_text(issue)
    answered: Answered | None
    if system is None or extractor is None:
        by_fixes = decide(text, version, Extraction([]), scheme)
        answered = Answered(by_fixes, FIX_VERSIONS) if by_fixes.answer == NOT_AFFECTED else None
    else:
        answered = answer_issue(
            session, issue.id, text, version, scheme, system, extractor, read=read
        )
    if answered is None:
        return None
    return CheckResult(
        issue, text, version, system or "", answered.decision, answered.decided_by, answered.cached
    )
