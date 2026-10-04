"""Answer "does this issue affect my Kafka version?" for one synced issue.

The system sees exactly what it sees in the eval (design v2): the issue's free text, minus
comments from bots, plus the fix versions JIRA lists. JIRA's affected versions are not given;
where the bug starts has to come from the text. The decision is made by ``verdict.decide``.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from dep_watch_agent.eval.runner import Extractor
from dep_watch_agent.eval.sampling import EXCLUDED_COMMENT_AUTHORS, JIRA_BROWSE_URL
from dep_watch_agent.orm import JiraIssueRow
from dep_watch_agent.verdict import Decision, IssueText, decide


class IssueNotFound(LookupError):
    pass


@dataclass(frozen=True)
class CheckResult:
    issue: JiraIssueRow
    issue_text: IssueText
    kafka_version: str
    system: str
    decision: Decision

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


def check_issue(
    session: Session, key: str, kafka_version: str, extractor: Extractor
) -> CheckResult:
    """Decide whether ``kafka_version`` is affected by issue ``key``, with ``extractor``.

    ``kafka_version`` must already be validated as a release (``verdict.is_release``).
    """
    issue = load_issue(session, key)
    text = issue_text(issue)
    decision = decide(text, kafka_version, extractor.extract(text))
    return CheckResult(issue, text, kafka_version, extractor.name, decision)
