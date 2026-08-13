from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from backend.app.config import AgnesConfig
from backend.app.domain_types import VideoTask
from backend.app.services.agnes_client import AgnesAIClient, ImageUpstreamError
from backend.app.services.downloader import download_file, save_b64_image, unique_path


def exception_payload(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, ImageUpstreamError):
        return {
            "kind": exc.__class__.__name__,
            "message": exc.message,
            "status_code": exc.status_code,
            "selected_model": exc.selected_model,
            "endpoint": exc.endpoint,
            "hint": exc.hint,
            "upstream_error": exc.upstream_error,
        }

    status_code = None
    response = getattr(exc, "response", None)
    if response is not None:
        status_code = getattr(response, "status_code", None)
    return {
        "kind": exc.__class__.__name__,
        "message": str(exc),
        "status_code": status_code,
    }


class AgnesService:
    def __init__(self, config: AgnesConfig | None = None) -> None:
        self.config = config or AgnesConfig.from_env()

    def generate_text(
        self,
        prompt: str,
        *,
        system: str = "You are a helpful AI assistant.",
        image_url: str | None = None,
        model: str | None = None,
        temperature: float | None = 0.7,
        max_tokens: int | None = 1024,
        enable_thinking: bool = False,
    ) -> dict[str, Any]:
        with AgnesAIClient(self.config) as client:
            user_content = client.image_content(prompt, image_url) if image_url else prompt
            content = client.chat(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                enable_thinking=enable_thinking,
            )
        return {
            "ok": True,
            "type": "text",
            "content": content,
            "model": model or self.config.model_for("text"),
        }

    def generate_image(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        model: str | None = None,
        image_urls: list[str] | None = None,
        return_base64: bool = False,
        download: bool = True,
        include_raw: bool = False,
        n: int | None = None,
        response_format: str | None = None,
        quality: str | None = None,
        background: str | None = None,
        output_format: str | None = None,
        output_compression: int | None = None,
        moderation: str | None = None,
        user: str | None = None,
    ) -> dict[str, Any]:
        with AgnesAIClient(self.config) as client:
            result = client.generate_image(
                prompt,
                model=model,
                size=size,
                image_urls=image_urls,
                response_format=response_format or ("b64_json" if return_base64 else "url"),
                return_base64=return_base64,
                n=n,
                quality=quality,
                background=background,
                output_format=output_format,
                output_compression=output_compression,
                moderation=moderation,
                user=user,
            )

        local_path: Path | None = None
        if result.url and download:
            local_path = download_file(
                result.url,
                self.config.output_dir / "images",
                f"agnes_image_{datetime.now():%Y%m%d_%H%M%S}.png",
            )
        elif result.b64_json:
            local_path = unique_path(
                self.config.output_dir / "images" / f"agnes_image_{datetime.now():%Y%m%d_%H%M%S}.png"
            )
            save_b64_image(result.b64_json, local_path)

        payload: dict[str, Any] = {
            "ok": True,
            "type": "image",
            "created": result.raw.get("created") if isinstance(result.raw, dict) else int(datetime.now().timestamp()),
            "data": result.raw.get("data") if isinstance(result.raw, dict) else [],
            "url": result.url,
            "local_path": str(local_path) if local_path else None,
            "has_b64_json": bool(result.b64_json),
            "model": result.model or model or self.config.model_for("image"),
        }
        if include_raw:
            payload["raw"] = result.raw
        return payload

    def create_video_task(
        self,
        prompt: str,
        *,
        model: str | None = None,
        image: str | None = None,
        extra_images: list[str] | None = None,
        mode: str | None = None,
        width: int = 1152,
        height: int = 768,
        num_frames: int = 121,
        frame_rate: int = 24,
        num_inference_steps: int | None = None,
        seed: int | None = None,
        negative_prompt: str | None = None,
        include_raw: bool = False,
    ) -> dict[str, Any]:
        with AgnesAIClient(self.config) as client:
            task = client.create_video_task(
                prompt,
                model=model,
                image=image,
                extra_images=extra_images,
                mode=mode,
                width=width,
                height=height,
                num_frames=num_frames,
                frame_rate=frame_rate,
                num_inference_steps=num_inference_steps,
                seed=seed,
                negative_prompt=negative_prompt,
            )
        payload: dict[str, Any] = {
            "ok": True,
            "type": "video_task",
            "task_id": task.task_id,
            "video_id": task.video_id,
            "status": task.status,
            "model": model or self.config.model_for("video"),
        }
        if include_raw:
            payload["raw"] = task.raw
        return payload

    def get_video_result(
        self,
        *,
        video_id: str | None = None,
        task_id: str | None = None,
        model_name: str | None = None,
        download: bool = False,
        include_raw: bool = False,
    ) -> dict[str, Any]:
        with AgnesAIClient(self.config) as client:
            result = client.get_video_result(
                video_id=video_id,
                task_id=task_id,
                model_name=model_name,
            )

        local_path: Path | None = None
        if result.video_url and download:
            local_path = download_file(
                result.video_url,
                self.config.output_dir / "videos",
                f"agnes_video_{datetime.now():%Y%m%d_%H%M%S}.mp4",
            )

        payload: dict[str, Any] = {
            "ok": True,
            "type": "video_result",
            "status": result.status,
            "progress": result.progress,
            "video_url": result.video_url,
            "local_path": str(local_path) if local_path else None,
            "error": result.error,
            "terminal": result.status in {"completed", "failed"},
        }
        if include_raw:
            payload["raw"] = result.raw
        return payload

    def generate_video(
        self,
        prompt: str,
        *,
        wait: bool = False,
        poll_seconds: int = 10,
        timeout_seconds: int = 1800,
        download: bool = False,
        include_raw: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        with AgnesAIClient(self.config) as client:
            created_task = client.create_video_task(prompt, **kwargs)

        task: dict[str, Any] = {
            "ok": True,
            "type": "video_task",
            "task_id": created_task.task_id,
            "video_id": created_task.video_id,
            "status": created_task.status,
            "model": kwargs.get("model") or self.config.model_for("video"),
        }
        if include_raw:
            task["raw"] = created_task.raw

        if not wait:
            return {
                "ok": True,
                "type": "video",
                "task": task,
                "result": None,
                "timed_out": False,
            }

        with AgnesAIClient(self.config) as client:
            result = client.wait_for_video(
                VideoTask(
                    task_id=created_task.task_id,
                    video_id=created_task.video_id,
                    status=created_task.status,
                    raw=created_task.raw,
                ),
                poll_seconds=poll_seconds,
                timeout_seconds=timeout_seconds,
            )

        local_path: Path | None = None
        if result.video_url and download:
            local_path = download_file(
                result.video_url,
                self.config.output_dir / "videos",
                f"agnes_video_{datetime.now():%Y%m%d_%H%M%S}.mp4",
            )
        result_payload: dict[str, Any] = {
            "ok": True,
            "type": "video_result",
            "status": result.status,
            "progress": result.progress,
            "video_url": result.video_url,
            "local_path": str(local_path) if local_path else None,
            "error": result.error,
            "terminal": result.status in {"completed", "failed"},
        }
        if include_raw:
            result_payload["raw"] = result.raw
        return {
            "ok": True,
            "type": "video",
            "task": task,
            "result": result_payload,
            "timed_out": False,
            "video_url": result.video_url,
            "local_path": str(local_path) if local_path else None,
        }


def is_http_error(exc: Exception) -> bool:
    return isinstance(
        exc,
        (
            ImageUpstreamError,
            httpx.HTTPStatusError,
            httpx.TimeoutException,
            httpx.RequestError,
        ),
    )
