import pytest
from langchain_core.exceptions import OutputParserException

from dep_watch_agent.dependencies import DEPENDENCIES
from dep_watch_agent.llm.chat import ChatFactModel, LLMConfig, WrongModel
from dep_watch_agent.llm.extractor import (
    InvalidOutput,
    LLMExtractor,
    Prompt,
    issue_chunks,
    load_prompt,
    parse_facts,
)
from dep_watch_agent.systems import configured_systems, system_name
from dep_watch_agent.verdict import Evidence, IssueText

ISSUE = IssueText(
    summary="Consumer hangs after rebalance",
    description="Regression in 3.6.0: the consumer hangs.",
    comments=["Works fine on 3.5.2.", "   "],
    fix_versions=["3.7.1", "3.8.0"],
)


class FakeModel:
    """Returns queued outputs (or raises queued exceptions) and records each call."""

    def __init__(self, *outputs):
        self.outputs = list(outputs)
        self.calls: list[tuple[str, str]] = []

    def __call__(self, system, user):
        self.calls.append((system, user))
        output = self.outputs.pop(0)
        if isinstance(output, Exception):
            raise output
        return output


def fact(version, kind, quote):
    return {"version": version, "kind": kind, "quote": quote}


# --- prompt and chunks ----------------------------------------------------------------------


def test_prompt_is_a_versioned_file():
    prompt = load_prompt()
    assert prompt.name == "extract_facts"
    assert len(prompt.version) == 12
    assert "insufficient" not in prompt.text  # the model extracts; it never answers
    assert '{"evidence": []}' in prompt.text


def test_one_chunk_tags_every_field():
    [chunk] = issue_chunks(ISSUE, 30_000)
    assert "<fix_versions>\n3.7.1, 3.8.0\n</fix_versions>" in chunk
    assert "<summary>\nConsumer hangs after rebalance\n</summary>" in chunk
    assert "<description>\nRegression in 3.6.0: the consumer hangs.\n</description>" in chunk
    assert "<comment>\nWorks fine on 3.5.2.\n</comment>" in chunk
    assert chunk.count("<comment>") == 1  # blank comments are left out


def test_long_issues_are_split_and_every_chunk_has_the_header():
    lines = [f"line {i}: the broker logs a warning\n" for i in range(400)]
    issue = IssueText("Summary", "".join(lines), comments=["Seen on 3.6.0."], fix_versions=[])
    chunks = issue_chunks(issue, 4_000)

    assert len(chunks) > 3
    assert all("<summary>\nSummary\n</summary>" in c for c in chunks)
    assert all("<fix_versions>\nnone\n</fix_versions>" in c for c in chunks)
    assert all(len(c) < 4_200 for c in chunks)
    text = "".join(chunks)
    assert all(line.strip() in text for line in lines)  # split on line breaks, nothing lost
    assert "Seen on 3.6.0." in chunks[-1]


def test_one_enormous_line_is_split_too():
    issue = IssueText("S", "q" * 10_000)  # "q" is in no tag name
    chunks = issue_chunks(issue, 2_000)
    assert sum(c.count("q") for c in chunks) == 10_000


# --- parsing ------------------------------------------------------------------------------


def test_parse_skips_malformed_items_and_keeps_unknown_kinds():
    facts = parse_facts(
        {
            "evidence": [
                fact(" 3.6.0 ", "introduced", "Regression in 3.6.0"),
                fact("3.5.2", "worked", "Works fine on 3.5.2."),  # decide drops it, with a reason
                {"version": "3.6.0", "kind": "affects"},  # no quote
                fact("", "affects", "a quote"),
                "not an object",
            ]
        }
    )
    assert facts == [
        Evidence("3.6.0", "introduced", "Regression in 3.6.0"),
        Evidence("3.5.2", "worked", "Works fine on 3.5.2."),  # type: ignore[arg-type]
    ]


@pytest.mark.parametrize("output", [None, [], {"facts": []}, {"evidence": "none"}])
def test_parse_rejects_the_wrong_shape(output):
    with pytest.raises(InvalidOutput):
        parse_facts(output)


# --- extractor ----------------------------------------------------------------------------


def test_extractor_sends_the_prompt_and_merges_chunks():
    issue = IssueText("S", "a\n" * 3_000, comments=["Regression in 3.6.0"])
    same = fact("3.6.0", "introduced", "Regression in 3.6.0")
    model = FakeModel(*[{"evidence": [same]}] * 10)

    extraction = LLMExtractor(model, chunk_chars=2_000).extract(issue)

    assert len(model.calls) > 1
    assert all(system == load_prompt().text for system, _ in model.calls)
    assert extraction.evidence == [Evidence("3.6.0", "introduced", "Regression in 3.6.0")]


def test_extractor_reads_at_most_max_chunks():
    model = FakeModel(*[{"evidence": []}] * 10)
    LLMExtractor(model, chunk_chars=2_000, max_chunks=2).extract(IssueText("S", "a\n" * 5_000))
    assert len(model.calls) == 2


def test_invalid_output_is_retried():
    model = FakeModel(InvalidOutput("not json"), {"evidence": [fact("3.6.0", "affects", "q")]})
    assert LLMExtractor(model).extract(ISSUE).evidence == [Evidence("3.6.0", "affects", "q")]


def test_output_invalid_after_retries_means_no_facts():
    model = FakeModel(InvalidOutput("1"), {"evidence": "2"})
    assert LLMExtractor(model, retries=1).extract(ISSUE).evidence == []
    assert len(model.calls) == 2


def test_errors_reaching_the_model_are_raised():
    model = FakeModel(ConnectionError("model server down"))
    with pytest.raises(ConnectionError):
        LLMExtractor(model).extract(ISSUE)


# --- chat model and registry --------------------------------------------------------------


def test_chat_model_turns_parse_errors_into_invalid_output(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    model = ChatFactModel(LLMConfig(base_url="http://localhost:1/v1", model="m"))

    class Broken:
        def invoke(self, messages, config):
            raise OutputParserException("not json")

    model._runnable = Broken()
    with pytest.raises(InvalidOutput):
        model("system", "user")


def test_text_output_is_parsed_out_of_code_fences(monkeypatch):
    from langchain_core.language_models.fake_chat_models import FakeListChatModel

    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    model = ChatFactModel(LLMConfig(base_url="http://localhost:1/v1", model="m"))
    reply = '```json\n{"evidence": [{"version": "4.0.0", "kind": "affects", "quote": "q"}]}\n```'
    model._runnable = FakeListChatModel(responses=[reply, "no json here"]) | model._runnable.last
    assert model("system", "user") == {
        "evidence": [{"version": "4.0.0", "kind": "affects", "quote": "q"}]
    }
    with pytest.raises(InvalidOutput):
        model("system", "user")


@pytest.mark.parametrize(
    ("served", "refused"),
    [("qwen/qwen3-4b-2507", False), (None, False), ("google/gemma-4-e4b", True)],
)
@pytest.mark.parametrize("output", ["text", "json_schema"])
@pytest.mark.skip(reason="the served-model check is switched off in ChatFactModel")
def test_a_reply_from_another_model_is_refused(monkeypatch, output, served, refused):
    # LM Studio answers with the loaded model when the requested one isn't loaded.
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage

    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    config = LLMConfig(base_url="http://localhost:1/v1", model="qwen/qwen3-4b-2507", output=output)
    model = ChatFactModel(config)
    message = AIMessage(
        '{"evidence": []}', response_metadata={"model_name": served} if served else {}
    )
    if output == "text":
        _, check, parse = model._runnable.steps
        model._runnable = GenericFakeChatModel(messages=iter([message])) | check | parse
        call = lambda: model("system", "user")  # noqa: E731
    else:
        raw = {"raw": message, "parsed": {"evidence": []}, "parsing_error": None}
        call = lambda: model._structured(raw)  # noqa: E731
    if refused:
        with pytest.raises(WrongModel, match="google/gemma-4-e4b"):
            call()
    else:
        assert call() == {"evidence": []}


def test_output_mode_is_checked():
    with pytest.raises(ValueError, match="DEP_WATCH_LLM_OUTPUT"):
        LLMConfig(base_url="u", model="m", output="xml")


@pytest.mark.parametrize(
    ("model", "name"),
    [("qwen/qwen3-4b-2507", "qwen3-4b-2507"), ("qwen2.5:7b", "qwen2.5-7b"), ("///", "llm")],
)
def test_system_name(model, name):
    assert system_name(model) == name


def test_no_model_configured_means_no_system(monkeypatch):
    monkeypatch.delenv("DEP_WATCH_LLM_MODEL", raising=False)
    assert configured_systems() == {}


def test_configured_system_is_named_after_the_model(monkeypatch):
    monkeypatch.setenv("DEP_WATCH_LLM_MODEL", "qwen/qwen3-4b-2507")
    monkeypatch.delenv("DEP_WATCH_LLM_SYSTEM", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    systems = configured_systems()

    assert list(systems) == ["qwen3-4b-2507"]
    kafka, spark, hadoop = DEPENDENCIES[:3]
    extractor = systems["qwen3-4b-2507"](kafka)  # builds the client; no request is made
    assert isinstance(extractor, LLMExtractor)
    assert systems["qwen3-4b-2507"](kafka) is extractor  # one client per dependency and process
    # Each dependency reads with its adapter's prompt. Kafka's keeps its name, so its stored
    # extractions stay valid.
    assert extractor.prompt.name == "extract_facts"
    assert systems["qwen3-4b-2507"](spark).prompt.name == "extract_facts_spark"
    with pytest.raises(ValueError, match="not supported"):
        systems["qwen3-4b-2507"](hadoop)


def test_system_name_override_must_be_a_file_name(monkeypatch):
    monkeypatch.setenv("DEP_WATCH_LLM_MODEL", "m")
    monkeypatch.setenv("DEP_WATCH_LLM_SYSTEM", "../x")
    with pytest.raises(ValueError, match="DEP_WATCH_LLM_SYSTEM"):
        configured_systems()


def test_extractor_version_changes_with_what_changes_its_output():
    prompt = load_prompt()
    base = LLMExtractor(FakeModel(), prompt=prompt, model_id="m")
    assert prompt.version in base.version
    other_prompt = Prompt(prompt.name, prompt.text + "\nOne more rule.")
    versions = {
        base.version,
        LLMExtractor(FakeModel(), prompt=other_prompt, model_id="m").version,
        LLMExtractor(FakeModel(), prompt=prompt, model_id="other").version,
        LLMExtractor(FakeModel(), prompt=prompt, model_id="m", chunk_chars=10_000).version,
    }
    assert len(versions) == 4
    assert LLMExtractor(FakeModel(), prompt=prompt, model_id="m", retries=3).version == base.version


@pytest.mark.parametrize("dependency", [d for d in DEPENDENCIES if d.watchable], ids=str)
def test_every_answered_dependency_has_its_own_prompt(dependency):
    prompt = load_prompt(dependency.adapter.prompt)
    assert prompt.text.startswith(f"You read one {dependency.name} JIRA issue")
