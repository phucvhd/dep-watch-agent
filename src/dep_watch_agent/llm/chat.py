"""``FactModel`` over an OpenAI-compatible chat server (LM Studio, vLLM, Ollama, llama.cpp), via
LangChain. Calls are traced to Langfuse when its keys are set in the environment.

Two ways to get JSON (``DEP_WATCH_LLM_OUTPUT``):

- ``text`` (default): the model answers in text and the JSON object is parsed out of it
  (code fences allowed). Reasoning models need this: constrained decoding skips their thinking,
  and gemma-4-e4b then returns ``{"evidence": []}`` for every issue (6 tokens, no reasoning),
  while unconstrained it finds the facts.
- ``json_schema``: the server constrains decoding to ``FACTS_SCHEMA``. For models that don't
  reason before answering.

Either way ``extractor.parse_facts`` validates the shape, and invalid output is retried.

LM Studio answers with whatever model is loaded when the requested one isn't, and its facts would
be stored under this system's name. ``_answered_by`` refuses such a reply; it is switched off for
now (see the commented lines in ``ChatFactModel.__init__``).
"""

import os
from dataclasses import dataclass
from typing import Any

from dep_watch_agent.llm.extractor import FACTS_SCHEMA, InvalidOutput, Prompt

OUTPUT_MODES = ("text", "json_schema")


@dataclass(frozen=True)
class LLMConfig:
    base_url: str
    model: str
    api_key: str = "not-needed"
    timeout: float = 600.0
    temperature: float = 0.0
    output: str = "text"  # one of OUTPUT_MODES

    @classmethod
    def from_env(cls) -> "LLMConfig | None":
        """``DEP_WATCH_LLM_MODEL`` (required), ``DEP_WATCH_LLM_BASE_URL``,
        ``DEP_WATCH_LLM_API_KEY``, ``DEP_WATCH_LLM_TIMEOUT``, ``DEP_WATCH_LLM_OUTPUT``. None if
        no model is set."""
        model = os.environ.get("DEP_WATCH_LLM_MODEL", "").strip()
        if not model:
            return None
        return cls(
            base_url=os.environ.get("DEP_WATCH_LLM_BASE_URL", "http://localhost:1234/v1"),
            model=model,
            api_key=os.environ.get("DEP_WATCH_LLM_API_KEY", "not-needed"),
            timeout=float(os.environ.get("DEP_WATCH_LLM_TIMEOUT", "600")),
            output=os.environ.get("DEP_WATCH_LLM_OUTPUT", "text"),
        )

    def __post_init__(self) -> None:
        if self.output not in OUTPUT_MODES:
            raise ValueError(
                f"DEP_WATCH_LLM_OUTPUT must be one of {OUTPUT_MODES}, got {self.output!r}"
            )


class WrongModel(RuntimeError):
    """The server answered with another model than the configured one."""


class ChatFactModel:
    def __init__(self, config: LLMConfig, *, prompt: Prompt | None = None):
        # from langchain_core.runnables import RunnableLambda
        from langchain_openai import ChatOpenAI

        chat = ChatOpenAI(
            base_url=config.base_url,
            model=config.model,
            api_key=config.api_key,
            temperature=config.temperature,
            timeout=config.timeout,
            max_retries=1,
        )
        self.config = config
        if config.output == "json_schema":
            self._runnable = chat.with_structured_output(
                FACTS_SCHEMA, method="json_schema", strict=True
            )
            # Refuse a reply from another model (switched off for now):
            # self._runnable = chat.with_structured_output(
            #     FACTS_SCHEMA, method="json_schema", strict=True, include_raw=True
            # ) | RunnableLambda(self._structured)
        else:
            from langchain_core.output_parsers import JsonOutputParser

            self._runnable = chat | JsonOutputParser()
            # Refuse a reply from another model (switched off for now):
            # self._runnable = chat | RunnableLambda(self._answered_by) | JsonOutputParser()
        self._metadata = {"model": config.model, "output": config.output}
        if prompt is not None:
            self._metadata |= {"prompt": prompt.name, "prompt_version": prompt.version}
        self._callbacks = _langfuse_callbacks()

    def __call__(self, system: str, user: str) -> Any:
        from langchain_core.exceptions import OutputParserException
        from langchain_core.messages import HumanMessage, SystemMessage

        try:
            return self._runnable.invoke(
                [SystemMessage(system), HumanMessage(user)],
                config={
                    "callbacks": self._callbacks,
                    "run_name": "extract_facts",
                    "metadata": self._metadata,
                },
            )
        except OutputParserException as exc:
            raise InvalidOutput(str(exc)[:500]) from exc

    def _answered_by(self, message: Any) -> Any:
        """The reply, if the configured model wrote it. A server that doesn't name its model
        can't be checked."""
        served = message.response_metadata.get("model_name")
        if served and served != self.config.model:
            raise WrongModel(
                f"asked for {self.config.model!r} but {served!r} answered: load it on the "
                "server or set DEP_WATCH_LLM_MODEL to the model being served"
            )
        return message

    def _structured(self, output: dict[str, Any]) -> Any:
        from langchain_core.exceptions import OutputParserException

        self._answered_by(output["raw"])
        if output["parsing_error"] is not None:
            raise OutputParserException(str(output["parsing_error"]))
        return output["parsed"]


def _langfuse_callbacks() -> list[Any]:
    if not (os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY")):
        return []
    from langfuse.langchain import CallbackHandler

    return [CallbackHandler()]
