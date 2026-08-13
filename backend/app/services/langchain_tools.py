from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, model_validator

from backend.app.services.agnes_service import AgnesService, exception_payload


class TextToolInput(BaseModel):
    prompt: str = Field(..., min_length=1)
    system: str = "You are a helpful AI assistant."
    image_url: str | None = None
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1024
    enable_thinking: bool = False


class ImageToolInput(BaseModel):
    prompt: str = Field(..., min_length=1)
    size: str = "1024x768"
    model: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    return_base64: bool = False
    download: bool = True
    include_raw: bool = False


class VideoCreateToolInput(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: str | None = None
    image: str | None = None
    extra_images: list[str] = Field(default_factory=list)
    mode: Literal["ti2vid", "keyframes"] | None = None
    width: int = 1152
    height: int = 768
    num_frames: int = 121
    frame_rate: int = 24
    num_inference_steps: int | None = None
    seed: int | None = None
    negative_prompt: str | None = None
    include_raw: bool = False


class VideoResultToolInput(BaseModel):
    video_id: str | None = None
    task_id: str | None = None
    model_name: str | None = None
    download: bool = False
    include_raw: bool = False

    @model_validator(mode="after")
    def validate_identifier(self) -> "VideoResultToolInput":
        if not self.video_id and not self.task_id:
            raise ValueError("video_id or task_id is required.")
        return self


class VideoGenerateToolInput(VideoCreateToolInput):
    wait: bool = False
    poll_seconds: int = 10
    timeout_seconds: int = 1800
    download: bool = False


def _json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)


def _safe_call(tool_type: str, func: Any, **kwargs: Any) -> str:
    try:
        return _json(func(**kwargs))
    except Exception as exc:
        return _json({"ok": False, "type": tool_type, "error": exception_payload(exc)})


def build_langchain_tools(service: AgnesService | None = None) -> list[StructuredTool]:
    service = service or AgnesService()

    def agnes_generate_text(**kwargs: Any) -> str:
        return _safe_call("text", service.generate_text, **kwargs)

    def agnes_generate_image(**kwargs: Any) -> str:
        return _safe_call("image", service.generate_image, **kwargs)

    def agnes_create_video_task(**kwargs: Any) -> str:
        return _safe_call("video_task", service.create_video_task, **kwargs)

    def agnes_get_video_result(**kwargs: Any) -> str:
        return _safe_call("video_result", service.get_video_result, **kwargs)

    def agnes_generate_video(**kwargs: Any) -> str:
        return _safe_call("video", service.generate_video, **kwargs)

    return [
        StructuredTool.from_function(
            func=agnes_generate_text,
            name="agnes_generate_text",
            description="Generate text or understand a public image URL with Agnes AI.",
            args_schema=TextToolInput,
        ),
        StructuredTool.from_function(
            func=agnes_generate_image,
            name="agnes_generate_image",
            description="Generate an image or image variation with Agnes AI.",
            args_schema=ImageToolInput,
        ),
        StructuredTool.from_function(
            func=agnes_create_video_task,
            name="agnes_create_video_task",
            description="Create an Agnes AI video generation task without waiting.",
            args_schema=VideoCreateToolInput,
        ),
        StructuredTool.from_function(
            func=agnes_get_video_result,
            name="agnes_get_video_result",
            description="Check an Agnes AI video generation task by task_id or video_id.",
            args_schema=VideoResultToolInput,
        ),
        StructuredTool.from_function(
            func=agnes_generate_video,
            name="agnes_generate_video",
            description="Create a video generation task and optionally wait for the result.",
            args_schema=VideoGenerateToolInput,
        ),
    ]
