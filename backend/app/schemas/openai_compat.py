from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class OpenAIChatMessage(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: Literal["system", "developer", "user", "assistant", "tool", "function"]
    content: Any = ""
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    function_call: dict[str, Any] | None = None
    refusal: str | None = None


class OpenAIChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str | None = None
    messages: list[OpenAIChatMessage] = Field(default_factory=list)
    temperature: float | None = 0.7
    max_tokens: int | None = 1024
    max_completion_tokens: int | None = None
    stream: bool = False
    user: str | None = None

    # Accepted for OpenAI-compatible gateway tolerance. The current backend
    # ignores these unless later mapped to tool-enabled agent behavior.
    top_p: float | None = None
    n: int | None = None
    stop: str | list[str] | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: Any | None = None
    response_format: dict[str, Any] | None = None
    stream_options: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    store: bool | None = None
    reasoning_effort: str | None = None
    parallel_tool_calls: bool | None = None
    seed: int | None = None
    logprobs: bool | None = None
    top_logprobs: int | None = None
    logit_bias: dict[str, Any] | None = None
    modalities: list[str] | None = None


class OpenAIModel(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "smart-assistant"
