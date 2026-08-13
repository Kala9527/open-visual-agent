from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ImageGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    prompt: str = Field(..., min_length=1)
    size: str = "1024x1024"
    model: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    return_base64: bool = False
    download: bool = True
    include_raw: bool = False
    n: int | None = Field(default=None, gt=0)
    response_format: Literal["url", "b64_json"] | None = None
    quality: str | None = None
    background: str | None = None
    output_format: str | None = None
    output_compression: int | None = Field(default=None, ge=0, le=100)
    moderation: str | None = None
    user: str | None = None

    @field_validator("size")
    @classmethod
    def validate_size(cls, value: str) -> str:
        if value.lower() == "auto":
            return value
        parts = value.lower().split("x")
        if len(parts) != 2 or not all(part.isdigit() and int(part) > 0 for part in parts):
            raise ValueError("size must be auto or use the WIDTHxHEIGHT format, e.g. 1024x1024.")
        return value


class VideoCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: str | None = None
    image: str | None = None
    extra_images: list[str] = Field(default_factory=list)
    mode: Literal["ti2vid", "keyframes"] | None = None
    width: int = Field(1152, gt=0)
    height: int = Field(768, gt=0)
    num_frames: int = Field(121, gt=0, le=441)
    frame_rate: int = Field(24, gt=0)
    num_inference_steps: int | None = Field(default=None, gt=0)
    seed: int | None = None
    negative_prompt: str | None = None
    wait: bool = False
    poll_seconds: int = Field(10, gt=0)
    timeout_seconds: int = Field(1800, gt=0)
    download: bool = False
    include_raw: bool = False

    @field_validator("num_frames")
    @classmethod
    def validate_frames(cls, value: int) -> int:
        if (value - 1) % 8 != 0:
            raise ValueError("num_frames must follow the 8n + 1 rule, e.g. 81 or 121.")
        return value


class VideoResultRequest(BaseModel):
    video_id: str | None = None
    task_id: str | None = None
    model_name: str | None = None
    download: bool = False
    include_raw: bool = False

    @model_validator(mode="after")
    def validate_identifier(self) -> "VideoResultRequest":
        if not self.video_id and not self.task_id:
            raise ValueError("video_id or task_id is required.")
        return self
