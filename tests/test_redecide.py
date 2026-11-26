from dep_watch_agent.eval.metrics import CaseResult
from dep_watch_agent.eval.redecide import extraction_of, is_direct_run, redecide
from dep_watch_agent.verdict import AFFECTED, INSUFFICIENT_INFORMATION, Evidence

ISSUES = {
    "K": {
        "summary": "Offset syncs published on every commit",
        "description": "Since 3.5 this behaviour changed. We run 3.6.0 and see this.",
        "fix_versions": ["3.7.1"],
    }
}
SINCE = {"version": "3.5", "kind": "introduced", "quote": "Since 3.5 this behaviour changed."}


def case(version, output, expected=AFFECTED) -> CaseResult:
    return CaseResult(
        case_id=f"K@{version}",
        issue_key="K",
        basis="b",
        version=version,
        expected=expected,
        answer=output["answer"],
        evidence_total=len(output["evidence"]) + len(output["dropped"]),
        citations_valid=1,
        output=output,
        seconds=2.5,
    )


SAVED = {
    "answer": INSUFFICIENT_INFORMATION,
    "evidence": [],
    "dropped": [{**SINCE, "reason": "release line, not a release"}],
    "evidence_total": 1,
    "citations_valid": 1,
    "context": ["Since 3.5 this behaviour changed."],
    "invalid_outputs": 1,
}


def test_the_extraction_is_the_kept_and_dropped_facts():
    extraction = extraction_of({**SAVED, "evidence": [{**SINCE, "version": "3.6.0"}]})
    assert extraction.evidence == [
        Evidence("3.6.0", "introduced", SINCE["quote"]),
        Evidence("3.5", "introduced", SINCE["quote"]),
    ]
    assert extraction.context == SAVED["context"]


def test_a_case_is_decided_again_from_its_saved_facts():
    (after,) = redecide([case("3.6.0", SAVED)], ISSUES)
    assert after.answer == AFFECTED  # "since 3.5" now starts the bug at 3.5.0
    assert after.output["evidence"] == [SINCE]
    assert after.output["dropped"] == []
    assert after.output["context"] == SAVED["context"]
    assert after.output["invalid_outputs"] == 1  # carried over
    assert (after.seconds, after.citations_valid, after.evidence_total) == (2.5, 1, 1)


def test_direct_runs_are_told_apart_by_their_parser():
    assert is_direct_run({"version": "model=m;prompt=direct_verdict@1;parser=direct-1"})
    assert not is_direct_run({"version": "model=m;prompt=extract_facts@1;parser=3"})
    assert not is_direct_run({})
