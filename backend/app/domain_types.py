from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ChatMessage = dict[str, Any]


@dataclass(frozen=True)
class ImageGenerationResult:
    url: str | None
    b64_json: str | None
    raw: Any
    model: str | None = None


@dataclass(frozen=True)
class VideoTask:
    task_id: str | None
    video_id: str | None
    status: str | None
    raw: dict[str, Any]


@dataclass(frozen=True)
class VideoResult:
    status: str | None
    progress: int | None
    video_url: str | None
    error: Any
    raw: dict[str, Any]
