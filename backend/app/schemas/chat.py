from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: Any


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str | None = None
    scenario: str | None = None
    history: list[ChatMessage] = Field(default_factory=list)
    use_tools: bool = True


class ChatResponse(BaseModel):
    ok: bool
    session_id: str
    scenario: str
    answer: str
    messages: list[ChatMessage] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)
