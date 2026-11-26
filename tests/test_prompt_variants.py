import pytest
from langchain_core.messages import AIMessage

from dep_watch_agent.dependencies import DEPENDENCIES
from dep_watch_agent.llm.chat import strip_tagged
from dep_watch_agent.llm.extractor import (
    ANSWER_FORMAT_MARKER,
    PromptNotFound,
    load_prompt,
)
from dep_watch_agent.systems import configured_systems, is_direct

KAFKA = next(d for d in DEPENDENCIES if d.id == "kafka")
SPARK = next(d for d in DEPENDENCIES if d.id == "spark")


def test_zero_shot_prompt_is_unchanged_by_variants():
    plain = load_prompt("extract_facts")
    assert (plain.name, load_prompt("extract_facts", "zeroshot")) == ("extract_facts", plain)


def test_few_shot_appends_examples():
    plain, few = load_prompt("extract_facts"), load_prompt("extract_facts", "fewshot")
    assert few.name == "extract_facts+fewshot"
    assert few.text.startswith(plain.text.rstrip())
    assert "Worked examples" in few.text and few.version != plain.version


def test_cot_replaces_the_answer_format():
    cot = load_prompt("extract_facts", "cot")
    assert cot.text.count(ANSWER_FORMAT_MARKER) == 0
    assert "<reasoning>" in cot.text


def test_missing_variant_files_are_errors():
    with pytest.raises(PromptNotFound):
        load_prompt("extract_facts_spark", "fewshot")
    with pytest.raises(ValueError):
        load_prompt("extract_facts", "tot")


def test_strip_tagged():
    reply = AIMessage('<reasoning>\n3.6.0 is "affects"\n</reasoning>\n{"evidence": []}')
    assert strip_tagged(reply, "reasoning") == '{"evidence": []}'
    assert strip_tagged(AIMessage("<reasoning>cut off"), "reasoning") == ""


def test_variants_are_registered_by_name(monkeypatch):
    monkeypatch.setenv("DEP_WATCH_LLM_MODEL", "qwen/qwen3-4b-2507")
    monkeypatch.delenv("DEP_WATCH_LLM_SYSTEM", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.setenv("DEP_WATCH_LLM_VARIANTS", "zeroshot,fewshot,cot,direct")
    systems = configured_systems()
    assert list(systems) == [
        "qwen3-4b-2507",
        "qwen3-4b-2507-fewshot",
        "qwen3-4b-2507-cot",
        "qwen3-4b-2507-direct",
    ]
    assert [is_direct(f) for f in systems.values()] == [False, False, False, True]

    cot = systems["qwen3-4b-2507-cot"](KAFKA)
    assert cot.prompt.name == "extract_facts+cot"
    assert cot.model.config.max_tokens == 4096
    assert systems["qwen3-4b-2507-direct"](KAFKA).prompt.name == "direct_verdict"
    with pytest.raises(PromptNotFound):
        systems["qwen3-4b-2507-fewshot"](SPARK)


def test_default_is_zero_shot_only(monkeypatch):
    monkeypatch.setenv("DEP_WATCH_LLM_MODEL", "qwen/qwen3-4b-2507")
    monkeypatch.delenv("DEP_WATCH_LLM_VARIANTS", raising=False)
    monkeypatch.delenv("DEP_WATCH_LLM_SYSTEM", raising=False)
    assert list(configured_systems()) == ["qwen3-4b-2507"]
    monkeypatch.setenv("DEP_WATCH_LLM_VARIANTS", "zeroshot,beam")
    with pytest.raises(ValueError, match="beam"):
        configured_systems()
