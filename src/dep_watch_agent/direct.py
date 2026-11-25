"""The direct-verdict control: the model answers for one version and cites one passage; code only
checks the citation (ALCE's one-pass answer-with-citations setting).

It is the comparison for RQ1. Everything ``verdict.decide`` does beyond checking quotes, the
version ordering, backports and the rule that the reporter's version is not where a bug starts,
is left to the model here.

``check_answer`` keeps an answer only if it is one of the three answers and, unless it abstains,
cites either a passage of the issue text (verbatim, whitespace aside) or one of the given fix
versions. An answer whose citation doesn't check out becomes ``insufficient_information``, as a
fact without a valid quote is dropped in ``decide``: an uncited claim is not an answer.
"""

from collections import Counter
from dataclasses import dataclass

from dep_watch_agent.verdict import (
    AFFECTED,
    ANSWERS,
    INSUFFICIENT_INFORMATION,
    NOT_AFFECTED,
    Decision,
    DroppedEvidence,
    Evidence,
    IssueText,
    quote_in_issue,
)

# The evidence kind a direct answer's citation is recorded as, so runs share an output format.
_KIND = {AFFECTED: "affects", NOT_AFFECTED: "unaffected"}


@dataclass(frozen=True)
class DirectAnswer:
    answer: str
    quote: str = ""


def check_answer(issue: IssueText, version: str, direct: DirectAnswer) -> Decision:
    if direct.answer == INSUFFICIENT_INFORMATION:
        return Decision(INSUFFICIENT_INFORMATION, [], [])
    kind = _KIND.get(direct.answer, direct.answer)
    cited = Evidence(version, kind, direct.quote)  # type: ignore[arg-type]
    if direct.answer not in ANSWERS:
        reason = f"unknown answer {direct.answer!r}"
    elif direct.quote.strip() in issue.fix_versions:
        return Decision(direct.answer, [Evidence(version, "fix", direct.quote.strip())], [])
    elif not quote_in_issue(direct.quote, issue):
        reason = "citation not found"
    else:
        return Decision(direct.answer, [cited], [])
    return Decision(INSUFFICIENT_INFORMATION, [], [DroppedEvidence(cited, reason)])


def combine(decisions: list[Decision]) -> Decision:
    """One decision from the chunks of a long issue: the answer every chunk that didn't abstain
    agrees on, else ``insufficient_information``. The citations of all chunks are kept."""
    used = [ev for d in decisions for ev in d.used]
    dropped = [ev for d in decisions for ev in d.dropped]
    answers = Counter(d.answer for d in decisions if d.answer != INSUFFICIENT_INFORMATION)
    answer = next(iter(answers)) if len(answers) == 1 else INSUFFICIENT_INFORMATION
    return Decision(answer, used, dropped)
