import pytest

from dep_watch_agent.direct import DirectAnswer, check_answer, combine
from dep_watch_agent.eval.dataset import load_dataset
from dep_watch_agent.eval.runner import is_direct, run_local
from dep_watch_agent.llm.direct import LLMDirect, parse_direct
from dep_watch_agent.llm.extractor import InvalidOutput, load_prompt
from dep_watch_agent.verdict import AFFECTED, INSUFFICIENT_INFORMATION, NOT_AFFECTED, IssueText

ISSUE = IssueText(
    summary="Consumer hangs",
    description="We run 3.6.0 and   see this.",
    comments=["Fixed in trunk."],
    fix_versions=["3.7.1"],
)


def test_a_cited_answer_is_kept():
    d = check_answer(ISSUE, "3.6.0", DirectAnswer(AFFECTED, "We run 3.6.0 and see this."))
    assert d.answer == AFFECTED
    assert [(e.version, e.kind) for e in d.used] == [("3.6.0", "affects")]
    assert d.citations_valid == 1


def test_a_fix_version_is_a_citation():
    d = check_answer(ISSUE, "3.8.0", DirectAnswer(NOT_AFFECTED, "3.7.1"))
    assert (d.answer, d.used[0].kind) == (NOT_AFFECTED, "fix")


@pytest.mark.parametrize(
    ("direct", "reason"),
    [
        (DirectAnswer(AFFECTED, "We run 3.5.0."), "citation not found"),
        (DirectAnswer(AFFECTED, ""), "citation not found"),
        (DirectAnswer("maybe", "We run 3.6.0"), "unknown answer 'maybe'"),
    ],
)
def test_an_uncited_answer_abstains(direct, reason):
    d = check_answer(ISSUE, "3.6.0", direct)
    assert d.answer == INSUFFICIENT_INFORMATION
    assert [x.reason for x in d.dropped] == [reason]


def test_abstaining_needs_no_citation():
    d = check_answer(ISSUE, "3.6.0", DirectAnswer(INSUFFICIENT_INFORMATION))
    assert (d.answer, d.evidence_total) == (INSUFFICIENT_INFORMATION, 0)


def test_chunks_must_agree():
    yes = check_answer(ISSUE, "3.6.0", DirectAnswer(AFFECTED, "We run 3.6.0"))
    no = check_answer(ISSUE, "3.6.0", DirectAnswer(NOT_AFFECTED, "Fixed in trunk."))
    none = check_answer(ISSUE, "3.6.0", DirectAnswer(INSUFFICIENT_INFORMATION))
    assert combine([yes, none]).answer == AFFECTED
    assert combine([yes, no]).answer == INSUFFICIENT_INFORMATION
    assert len(combine([yes, no]).used) == 2


def test_parse_direct():
    assert parse_direct({"answer": " affected ", "quote": " q "}) == DirectAnswer(AFFECTED, "q")
    assert parse_direct({"answer": "affected"}) == DirectAnswer(AFFECTED, "")
    with pytest.raises(InvalidOutput):
        parse_direct({"evidence": []})


class FakeModel:
    def __init__(self, replies):
        self.replies = list(replies)
        self.users = []

    def __call__(self, system, user):
        self.users.append(user)
        return self.replies.pop(0)


def test_llm_direct_asks_about_the_version():
    model = FakeModel([{"answer": "affected", "quote": "We run 3.6.0 and see this."}])
    system = LLMDirect(model, prompt=load_prompt("direct_verdict"))
    assert system.answer(ISSUE, "3.6.0").answer == AFFECTED
    assert model.users[0].endswith("<version>\n3.6.0\n</version>")
    assert "parser=direct-1" in system.version
    assert is_direct(system)


def test_invalid_output_is_retried_then_abstains():
    model = FakeModel(["junk", "junk"])
    system = LLMDirect(model, prompt=load_prompt("direct_verdict"))
    assert system.answer(ISSUE, "3.6.0").answer == INSUFFICIENT_INFORMATION
    assert len(model.users) == 2


def test_runner_asks_a_direct_system_per_case(written):
    class Always:
        def __init__(self):
            self.asked = []

        def answer(self, issue, version):
            self.asked.append(version)
            return check_answer(issue, version, DirectAnswer(AFFECTED, issue.description))

    system = Always()
    results = run_local(load_dataset(written), system, provisional=True)
    assert system.asked == ["3.7.0", "3.7.1", "3.7.0", "3.7.1"]
    assert [r.answer for r in results] == [AFFECTED] * 4
    assert all(r.seconds >= 0 for r in results)
