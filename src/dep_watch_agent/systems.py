"""The systems that can answer checks and be scored by the eval, by name.

A system is a factory for an extractor (``eval.runner.Extractor``) for a dependency: it turns
that dependency's issue text into cited version facts, reading with the prompt its adapter
names, and ``verdict.decide`` makes the decision; a direct-verdict system answers each version
itself and is for the eval only. Systems are compared with each other on the same metrics;
there is no fixed baseline. ``POST /check`` and ``POST /scan`` use the first extractor
registered.

The registry key is the system's only name (it goes into run names and Langfuse metadata), so
it is restricted to file-name characters.
"""

import os
import re
from collections.abc import Callable
from functools import cache

from dep_watch_agent.dependencies import Dependency
from dep_watch_agent.eval.runner import DirectSystem, Extractor

SystemFactory = Callable[[Dependency], Extractor | DirectSystem]
SystemRegistry = dict[str, SystemFactory]

SYSTEM_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


VARIANTS = ("zeroshot", "fewshot", "cot", "hybrid", "direct")


def configured_systems() -> SystemRegistry:
    """The LLM systems configured in the environment (see ``llm.chat.LLMConfig``), or none.

    One model, one system per variant in ``DEP_WATCH_LLM_VARIANTS`` (comma-separated, default
    ``zeroshot``), in that order:

    - ``zeroshot``: the dependency's extraction prompt. Named ``DEP_WATCH_LLM_SYSTEM``, by
      default the model id without its publisher, e.g. ``qwen3-4b-2507`` for
      ``qwen/qwen3-4b-2507``. Every other variant is that name plus ``-<variant>``.
    - ``fewshot``, ``cot``: the prompt with worked examples, or with step-by-step reasoning
      before the JSON (``llm.extractor.load_prompt``).
    - ``hybrid``: the zero-shot prompt over hybrid retrieval on long issues (``retrieval``);
      needs the database and an embedding model.
    - ``direct``: the direct-verdict control (``llm.direct``). It answers a version, not an
      issue, so it is for the eval only (``is_direct``); checks and scans skip it.
    """
    from dep_watch_agent.llm.chat import LLMConfig

    config = LLMConfig.from_env()
    if config is None:
        return {}
    name = os.environ.get("DEP_WATCH_LLM_SYSTEM") or system_name(config.model)
    if not SYSTEM_NAME_PATTERN.match(name):
        raise ValueError(f"DEP_WATCH_LLM_SYSTEM {name!r} must match {SYSTEM_NAME_PATTERN.pattern}")
    variants = [
        v.strip() for v in os.environ.get("DEP_WATCH_LLM_VARIANTS", "zeroshot").split(",") if v
    ]
    unknown = sorted(set(variants) - set(VARIANTS))
    if unknown or not variants:
        raise ValueError(f"DEP_WATCH_LLM_VARIANTS must name some of {VARIANTS}, got {unknown}")
    return {
        name if variant == "zeroshot" else f"{name}-{variant}": llm_system(config, variant)
        for variant in dict.fromkeys(variants)
    }


def is_direct(factory: SystemFactory) -> bool:
    """True for a direct-verdict system, which answers versions rather than extracting facts."""
    return getattr(factory, "direct", False)


def llm_system(config, variant: str) -> SystemFactory:
    """The factory of one variant of the LLM system over ``config`` (an ``LLMConfig``)."""
    from dataclasses import replace

    @cache  # one client per dependency and process; the system is stateless between issues
    def factory(dependency: Dependency):
        from dep_watch_agent.llm.chat import ChatFactModel
        from dep_watch_agent.llm.extractor import REASONING_TAG, LLMExtractor, load_prompt

        if dependency.adapter is None:
            raise ValueError(f"{dependency.name} is synced but not supported for checks")
        model_id = f"{config.model};output={config.output}"
        if config.reasoning_effort is not None:
            model_id += f";reasoning={config.reasoning_effort}"

        if variant == "direct":
            from dep_watch_agent.llm.direct import DIRECT_SCHEMA, LLMDirect

            prompt = load_prompt(
                dependency.adapter.prompt.replace("extract_facts", "direct_verdict")
            )
            model = ChatFactModel(
                config, prompt=prompt, schema=DIRECT_SCHEMA, run_name="direct_verdict"
            )
            return LLMDirect(model, prompt=prompt, model_id=model_id)

        prompt_variant = variant if variant in ("fewshot", "cot") else "zeroshot"
        prompt = load_prompt(dependency.adapter.prompt, prompt_variant)
        model_config = config
        if variant == "cot" and config.max_tokens is not None:
            # Room for the reasoning before the JSON.
            model_config = replace(config, max_tokens=max(config.max_tokens, 4096))
        model = ChatFactModel(
            model_config,
            prompt=prompt,
            reasoning_tag=REASONING_TAG if variant == "cot" else None,
        )
        extractor = LLMExtractor(model, prompt=prompt, model_id=model_id)
        if variant != "hybrid":
            return extractor

        from dep_watch_agent.retrieval import HybridExtractor, default_retriever

        budget = int(os.environ.get("DEP_WATCH_RETRIEVAL_BUDGET", "6000"))
        return HybridExtractor(extractor, default_retriever(), budget_chars=budget)

    factory.direct = variant == "direct"  # type: ignore[attr-defined]
    return factory


def system_name(model: str) -> str:
    """A registry name for a model id: ``qwen/qwen3-4b-2507`` -> ``qwen3-4b-2507``."""
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", model.rsplit("/", 1)[-1]).strip("-._")
    return name or "llm"
