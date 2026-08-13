from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolError(BaseModel):
    kind: str
    message: str
    status_code: int | None = None


class GenericToolResponse(BaseModel):
    ok: bool
    type: str
    error: ToolError | None = None
    data: dict[str, Any] = Field(default_factory=dict)
