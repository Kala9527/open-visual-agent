from __future__ import annotations

import time
from typing import Any, Iterable

import httpx
from openai import OpenAI

from backend.app.config import AgnesConfig
from backend.app.domain_types import ChatMessage, ImageGenerationResult, VideoResult, VideoTask


class ImageUpstreamError(RuntimeError):
    def __init__(
        self,
        *,
        status_code: int,
        message: str,
        selected_model: str,
        endpoint: str,
        hint: str = "",
        upstream_error: Any | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.selected_model = selected_model
        self.endpoint = endpoint
        self.hint = hint
        self.upstream_error = upstream_error
        suffix = f" {hint}" if hint else ""
        super().__init__(f"Image upstream HTTP {status_code}: {message}{suffix}")


class AgnesAIClient:
    def __init__(self, config: AgnesConfig | None = None) -> None:
        self.config = config or AgnesConfig.from_env()
        self.http = httpx.Client(
            timeout=self.config.timeout_seconds,
        )
        self._text_openai: OpenAI | None = None

    def close(self) -> None:
        self.http.close()
        if self._text_openai is not None:
            self._text_openai.close()

    def __enter__(self) -> "AgnesAIClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _openai_for_text(self) -> OpenAI:
        if self._text_openai is None:
            self._text_openai = OpenAI(
                api_key=self.config.api_key_for("text"),
                base_url=self.config.api_base_url_for("text"),
                timeout=self.config.timeout_seconds,
            )
        return self._text_openai

    def _headers_for(self, capability: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key_for(capability)}",
            "Content-Type": "application/json",
        }

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = 0.7,
        max_tokens: int | None = 1024,
        stream: bool = False,
        enable_thinking: bool = False,
        extra_body: dict[str, Any] | None = None,
    ) -> str:
        body = dict(extra_body or {})
        if enable_thinking:
            body["chat_template_kwargs"] = {"enable_thinking": True}

        response = self._openai_for_text().chat.completions.create(
            model=model or self.config.model_for("text"),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            extra_body=body or None,
        )

        if stream:
            chunks: list[str] = []
            for chunk in response:
                delta = chunk.choices[0].delta.content or ""
                chunks.append(delta)
            return "".join(chunks)

        return response.choices[0].message.content or ""

    def image_content(self, prompt: str, image_url: str) -> list[dict[str, Any]]:
        return [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]

    def generate_image(
        self,
        prompt: str,
        *,
        model: str | None = None,
        size: str = "1024x1024",
        image_urls: Iterable[str] | None = None,
        response_format: str | None = None,
        return_base64: bool = False,
        n: int | None = None,
        quality: str | None = None,
        background: str | None = None,
        output_format: str | None = None,
        output_compression: int | None = None,
        moderation: str | None = None,
        user: str | None = None,
    ) -> ImageGenerationResult:
        images = list(image_urls or [])
        selected_model = model or self.config.model_for("image")
        payload: dict[str, Any] = {
            "model": selected_model,
            "prompt": prompt,
            "size": size,
        }
        if n is not None:
            payload["n"] = n
        if quality:
            payload["quality"] = quality
        if background:
            payload["background"] = background
        if output_format:
            payload["output_format"] = output_format
        if output_compression is not None:
            payload["output_compression"] = output_compression
        if moderation:
            payload["moderation"] = moderation
        if user:
            payload["user"] = user
        if images:
            payload["image"] = images
        selected_response_format = response_format
        if return_base64 and selected_response_format is None:
            selected_response_format = "b64_json"
        if selected_response_format and _supports_image_response_format(selected_model):
            payload["response_format"] = selected_response_format

        endpoint = f"{self.config.api_base_url_for('image')}/images/generations"
        response = self.http.post(
            endpoint,
            json=payload,
            headers=self._headers_for("image"),
        )
        if _should_retry_without_response_format(response, payload):
            retry_payload = dict(payload)
            retry_payload.pop("response_format", None)
            response = self.http.post(endpoint, json=retry_payload, headers=self._headers_for("image"))
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise _build_image_upstream_error(
                exc.response,
                selected_model=selected_model,
                endpoint=endpoint,
            ) from exc
        data = response.json()
        first = data["data"][0]
        return ImageGenerationResult(
            url=first.get("url"),
            b64_json=first.get("b64_json"),
            raw=data,
            model=selected_model,
        )

    def create_video_task(
        self,
        prompt: str,
        *,
        model: str | None = None,
        image: str | None = None,
        extra_images: Iterable[str] | None = None,
        mode: str | None = None,
        height: int | None = 768,
        width: int | None = 1152,
        num_frames: int = 121,
        frame_rate: int = 24,
        num_inference_steps: int | None = None,
        seed: int | None = None,
        negative_prompt: str | None = None,
    ) -> VideoTask:
        self._validate_video_frames(num_frames)

        payload: dict[str, Any] = {
            "model": model or self.config.model_for("video"),
            "prompt": prompt,
            "num_frames": num_frames,
            "frame_rate": frame_rate,
        }
        optional = {
            "image": image,
            "height": height,
            "width": width,
            "num_inference_steps": num_inference_steps,
            "seed": seed,
            "negative_prompt": negative_prompt,
        }
        payload.update({key: value for key, value in optional.items() if value is not None})

        extra = list(extra_images or [])
        if extra:
            payload["extra_body"] = {"image": extra}
            if mode:
                payload["extra_body"]["mode"] = mode
        elif mode:
            payload["mode"] = mode

        response = self.http.post(
            f"{self.config.api_base_url_for('video')}/videos",
            json=payload,
            headers=self._headers_for("video"),
        )
        response.raise_for_status()
        data = response.json()
        return VideoTask(
            task_id=data.get("task_id") or data.get("id"),
            video_id=data.get("video_id"),
            status=data.get("status"),
            raw=data,
        )

    def get_video_result(
        self,
        *,
        video_id: str | None = None,
        task_id: str | None = None,
        model_name: str | None = None,
    ) -> VideoResult:
        if video_id:
            params = {"video_id": video_id}
            if model_name:
                params["model_name"] = model_name
            response = self.http.get(
                f"{self.config.video_gateway_url}/agnesapi",
                params=params,
                headers=self._headers_for("video"),
            )
        elif task_id:
            response = self.http.get(
                f"{self.config.api_base_url_for('video')}/videos/{task_id}",
                headers=self._headers_for("video"),
            )
        else:
            raise ValueError("video_id or task_id is required.")

        response.raise_for_status()
        data = response.json()
        return self._parse_video_result(data)

    def wait_for_video(
        self,
        task: VideoTask,
        *,
        poll_seconds: int = 10,
        timeout_seconds: int = 1800,
    ) -> VideoResult:
        started_at = time.monotonic()
        last_result: VideoResult | None = None

        while time.monotonic() - started_at < timeout_seconds:
            last_result = self.get_video_result(
                video_id=task.video_id,
                task_id=task.task_id,
                model_name=self.config.model_for("video") if task.video_id else None,
            )
            if last_result.status in {"completed", "failed"}:
                return last_result
            time.sleep(poll_seconds)

        if last_result is not None:
            return last_result
        raise TimeoutError("Timed out before receiving a video task status.")

    @staticmethod
    def _parse_video_result(data: dict[str, Any]) -> VideoResult:
        video_url = (
            data.get("video_url")
            or data.get("url")
            or data.get("remixed_from_video_id")
            or data.get("output")
        )
        return VideoResult(
            status=data.get("status"),
            progress=data.get("progress"),
            video_url=video_url,
            error=data.get("error"),
            raw=data,
        )

    @staticmethod
    def _validate_video_frames(num_frames: int) -> None:
        if num_frames > 441:
            raise ValueError("num_frames must be <= 441.")
        if (num_frames - 1) % 8 != 0:
            raise ValueError("num_frames must follow the 8n + 1 rule, e.g. 81 or 121.")


def _supports_image_response_format(model: str) -> bool:
    normalized = model.lower()
    return not (
        normalized.startswith("gpt-image-")
        or normalized.startswith("agnes-")
        or "text-to-image" in normalized
    )


def _should_retry_without_response_format(response: httpx.Response, payload: dict[str, Any]) -> bool:
    if "response_format" not in payload or response.status_code < 400:
        return False
    text = response.text
    return "response_format" in text and (
        "UnsupportedParamsError" in text
        or "not supported" in text
        or "unsupported" in text.lower()
    )


def _build_image_upstream_error(
    response: httpx.Response,
    *,
    selected_model: str,
    endpoint: str,
) -> ImageUpstreamError:
    message, upstream_error = _extract_upstream_image_error(response)
    hint = _image_error_hint(str(message))
    return ImageUpstreamError(
        status_code=response.status_code,
        message=str(message),
        selected_model=selected_model,
        endpoint=endpoint,
        hint=hint,
        upstream_error=upstream_error,
    )


def _extract_upstream_image_error(response: httpx.Response) -> tuple[Any, Any]:
    try:
        data = response.json()
    except ValueError:
        return response.text[:1000], response.text[:1000]
    message = data
    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message") or error
        elif data.get("message"):
            message = data["message"]
    return message, data


def _image_error_hint(text: str) -> str:
    hint = ""
    if "requires an image model" in text:
        hint = (
            "The image provider did not recognize AGNES_IMAGE_MODEL as an image model. "
            "Set AGNES_IMAGE_MODEL to an image model supported and authorized by that provider."
        )
    elif "Image generation is not enabled" in text:
        hint = "The image provider recognized the model, but this API key/group is not authorized for image generation."
    return hint

