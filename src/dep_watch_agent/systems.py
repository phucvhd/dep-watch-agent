"""The systems that can answer checks and be scored by the eval, by name.

A system is a factory for an extractor (``eval.runner.Extractor``) for a dependency: it turns
that dependency's issue text into cited version facts, reading with the prompt its adapter
names, and ``verdict.decide`` makes the decision. Systems are compared with each
other on the same metrics; there is no fixed baseline. ``POST /check`` and ``POST /scan`` use
the first one registered.

The registry key is the system's only name (it goes into run names and Langfuse metadata), so
it is restricted to file-name characters.
"""

import os
import re
from collections.abc import Callable
from functools import cache

from dep_watch_agent.dependencies import Dependency
from dep_watch_agent.eval.runner import Extractor

SystemFactory = Callable[[Dependency], Extractor]
SystemRegistry = dict[str, SystemFactory]

SYSTEM_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def configured_systems() -> SystemRegistry:
    """The LLM system configured in the environment (see ``llm.chat.LLMConfig``), or none.

    Its name is ``DEP_WATCH_LLM_SYSTEM``, by default the model id without its publisher, e.g.
    ``gemma-4-e4b`` for ``google/gemma-4-e4b``.
    """
    from dep_watch_agent.llm.chat import LLMConfig

    config = LLMConfig.from_env()
    if config is None:
        return {}
    name = os.environ.get("DEP_WATCH_LLM_SYSTEM") or system_name(config.model)
    if not SYSTEM_NAME_PATTERN.match(name):
        raise ValueError(f"DEP_WATCH_LLM_SYSTEM {name!r} must match {SYSTEM_NAME_PATTERN.pattern}")

    @cache  # one client per dependency and process; the extractor is stateless between issues
    def factory(dependency: Dependency) -> Extractor:
        from dep_watch_agent.llm.chat import ChatFactModel
        from dep_watch_agent.llm.extractor import LLMExtractor, load_prompt

        if dependency.adapter is None:
            raise ValueError(f"{dependency.name} is synced but not supported for checks")
        prompt = load_prompt(dependency.adapter.prompt)
        return LLMExtractor(
            ChatFactModel(config, prompt=prompt),
            prompt=prompt,
            model_id=f"{config.model};output={config.output}",
        )

    return {name: factory}


def system_name(model: str) -> str:
    """A registry name for a model id: ``google/gemma-4-e4b`` -> ``gemma-4-e4b``."""
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", model.rsplit("/", 1)[-1]).strip("-._")
    return name or "llm"
