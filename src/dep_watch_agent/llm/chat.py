"""``FactModel`` over a chat model, via LangChain. Calls are traced to Langfuse when its keys are
set in the environment.

Two providers (``DEP_WATCH_LLM_PROVIDER``):

- ``openai`` (default): any OpenAI-compatible chat server (LM Studio, vLLM, Ollama, llama.cpp,
  Groq), at ``DEP_WATCH_LLM_BASE_URL``.
- ``bedrock``: Amazon Bedrock's Converse API. Credentials come from the standard AWS chain (an
  SSO profile on a laptop, the instance role on EC2), never from an API key in the environment;
  the region from ``AWS_REGION`` / ``AWS_DEFAULT_REGION``. ``DEP_WATCH_LLM_MODEL`` is a Bedrock
  model id or inference profile id.

Two ways to get JSON (``DEP_WATCH_LLM_OUTPUT``):

- ``text`` (default): the model answers in text and the JSON object is parsed out of it
  (code fences allowed). Reasoning models need this: constrained decoding skips their thinking,
  and gemma-4-e4b then returns ``{"evidence": []}`` for every issue (6 tokens, no reasoning),
  while unconstrained it finds the facts.
- ``json_schema``: the server constrains decoding to ``FACTS_SCHEMA``. For models that don't
  reason before answering.

Either way ``extractor.parse_facts`` validates the shape, and invalid output is retried. A prompt
that asks for reasoning before the JSON (chain of thought) names the tag it goes in
(``reasoning_tag``), and the tagged text is removed before parsing.

The same model serves the direct-verdict control with another schema (``llm.direct``).

LM Studio answers with whatever model is loaded when the requested one isn't, and its facts would
be stored under this system's name. ``_answered_by`` refuses such a reply; it is switched off for
now (see the commented lines in ``ChatFactModel.__init__``).
"""

import os
from dataclasses import dataclass
from typing import Any

from dep_watch_agent.llm.extractor import FACTS_SCHEMA, InvalidOutput, Prompt

OUTPUT_MODES = ("text", "json_schema")
PROVIDERS = ("openai", "bedrock")


@dataclass(frozen=True)
class LLMConfig:
    base_url: str
    model: str
    api_key: str = "not-needed"
    timeout: float = 600.0
    temperature: float = 0.0
    output: str = "text"  # one of OUTPUT_MODES
    provider: str = "openai"  # one of PROVIDERS
    # Cap on generated tokens: without it a model that falls into a repetition loop
    # generates until the context is full and the call times out. A truncated reply
    # fails to parse and counts as invalid output (retried, then no facts).
    max_tokens: int | None = 2048
    # Sent as the OpenAI ``reasoning_effort``; "none" turns a thinking model's reasoning off
    # (LM Studio honors it for Qwen3.5, whose thinking otherwise fills ``max_tokens``). None
    # sends nothing, leaving the model's default.
    reasoning_effort: str | None = None

    @classmethod
    def from_env(cls) -> "LLMConfig | None":
        """``DEP_WATCH_LLM_MODEL`` (required), ``DEP_WATCH_LLM_BASE_URL``,
        ``DEP_WATCH_LLM_API_KEY``, ``DEP_WATCH_LLM_TIMEOUT``, ``DEP_WATCH_LLM_OUTPUT``,
        ``DEP_WATCH_LLM_MAX_TOKENS`` (0 for no cap), ``DEP_WATCH_LLM_PROVIDER``,
        ``DEP_WATCH_LLM_REASONING_EFFORT``. None if no model is set."""
        model = os.environ.get("DEP_WATCH_LLM_MODEL", "").strip()
        if not model:
            return None
        return cls(
            base_url=os.environ.get("DEP_WATCH_LLM_BASE_URL", "http://localhost:1234/v1"),
            model=model,
            api_key=os.environ.get("DEP_WATCH_LLM_API_KEY", "not-needed"),
            timeout=float(os.environ.get("DEP_WATCH_LLM_TIMEOUT", "600")),
            output=os.environ.get("DEP_WATCH_LLM_OUTPUT", "text"),
            max_tokens=int(os.environ.get("DEP_WATCH_LLM_MAX_TOKENS", "2048")) or None,
            provider=os.environ.get("DEP_WATCH_LLM_PROVIDER", "openai"),
            reasoning_effort=os.environ.get("DEP_WATCH_LLM_REASONING_EFFORT", "").strip() or None,
        )

    def __post_init__(self) -> None:
        if self.output not in OUTPUT_MODES:
            raise ValueError(
                f"DEP_WATCH_LLM_OUTPUT must be one of {OUTPUT_MODES}, got {self.output!r}"
            )
        if self.provider not in PROVIDERS:
            raise ValueError(
                f"DEP_WATCH_LLM_PROVIDER must be one of {PROVIDERS}, got {self.provider!r}"
            )
        if self.provider == "bedrock" and self.output != "text":
            # Converse has no OpenAI-style json_schema response format; LangChain would fall
            # back to tool calling, a different path from the one the eval measured.
            raise ValueError("DEP_WATCH_LLM_PROVIDER=bedrock supports DEP_WATCH_LLM_OUTPUT=text")
        if self.provider == "bedrock" and self.reasoning_effort is not None:
            raise ValueError("DEP_WATCH_LLM_REASONING_EFFORT is for the openai provider")


class WrongModel(RuntimeError):
    """The server answered with another model than the configured one."""


def _chat_model(config: LLMConfig) -> Any:
    """The LangChain chat model for ``config.provider``. Building it makes no request."""
    if config.provider == "bedrock":
        from botocore.config import Config
        from langchain_aws import ChatBedrockConverse

        return ChatBedrockConverse(
            model=config.model,
            region_name=os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION"),
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            # One retry, like the OpenAI client; botocore counts the first attempt.
            config=Config(read_timeout=config.timeout, retries={"max_attempts": 2}),
        )

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        base_url=config.base_url,
        model=config.model,
        api_key=config.api_key,
        temperature=config.temperature,
        timeout=config.timeout,
        max_tokens=config.max_tokens,
        max_retries=1,
        reasoning_effort=config.reasoning_effort,
    )


class ChatFactModel:
    def __init__(
        self,
        config: LLMConfig,
        *,
        prompt: Prompt | None = None,
        schema: dict[str, Any] = FACTS_SCHEMA,
        reasoning_tag: str | None = None,
        run_name: str = "extract_facts",
    ):
        from langchain_core.runnables import RunnableLambda

        chat = _chat_model(config)
        self.config = config
        self.run_name = run_name
        if config.output == "json_schema":
            if reasoning_tag:
                raise ValueError("a reasoning prompt needs DEP_WATCH_LLM_OUTPUT=text")
            self._runnable = chat.with_structured_output(schema, method="json_schema", strict=True)
            # Refuse a reply from another model (switched off for now):
            # self._runnable = chat.with_structured_output(
            #     FACTS_SCHEMA, method="json_schema", strict=True, include_raw=True
            # ) | RunnableLambda(self._structured)
        else:
            from langchain_core.output_parsers import JsonOutputParser

            if reasoning_tag:
                strip = RunnableLambda(lambda message: strip_tagged(message, reasoning_tag))
                self._runnable = chat | strip | JsonOutputParser()
            else:
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
                    "run_name": self.run_name,
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


def strip_tagged(message: Any, tag: str) -> str:
    """The reply's text without its ``<tag>...</tag>`` blocks. An unclosed block (a reply cut
    off while reasoning) leaves nothing to parse, which counts as invalid output."""
    import re

    text = message.content if hasattr(message, "content") else str(message)
    if isinstance(text, list):  # content blocks
        text = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in text)
    text = re.sub(rf"<{tag}>.*?</{tag}>", "", text, flags=re.DOTALL)
    return re.sub(rf"<{tag}>.*", "", text, flags=re.DOTALL).strip()


def _langfuse_callbacks() -> list[Any]:
    if not (os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY")):
        return []
    from langfuse.langchain import CallbackHandler

    return [CallbackHandler()]
