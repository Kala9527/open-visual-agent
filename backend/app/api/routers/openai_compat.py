from __future__ import annotations

import json
import time
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError

from backend.app.api.deps import get_agnes_config, get_repository
from backend.app.schemas.chat import ChatMessage
from backend.app.schemas.openai_compat import OpenAIChatCompletionRequest


router = APIRouter(prefix="/v1", tags=["openai-compatible"])
UPSTREAM_EMPTY_LENGTH_RETRY_MAX_TOKENS = 1024


def _stringify_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                elif "text" in item:
                    parts.append(str(item["text"]))
                elif item.get("type") == "image_url":
                    image = item.get("image_url", {})
                    if isinstance(image, dict):
                        parts.append(f"[image_url: {image.get('url', '')}]")
                    else:
                        parts.append(f"[image_url: {image}]")
                else:
                    parts.append(json.dumps(item, ensure_ascii=False))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    return json.dumps(content, ensure_ascii=False)


def _normalize_messages(request: OpenAIChatCompletionRequest) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for message in request.messages:
        role = message.role
        if role not in {"system", "developer", "user", "assistant", "tool", "function"}:
            continue
        content = _stringify_content(message.content)
        metadata_parts: list[str] = []
        if message.tool_calls:
            metadata_parts.append(f"tool_calls={json.dumps(message.tool_calls, ensure_ascii=False)}")
        if message.function_call:
            metadata_parts.append(f"function_call={json.dumps(message.function_call, ensure_ascii=False)}")
        if message.refusal:
            metadata_parts.append(f"refusal={message.refusal}")
        if metadata_parts:
            content = "\n".join(part for part in [content, *metadata_parts] if part)

        if role == "developer":
            normalized.append({"role": "system", "content": content})
            continue
        if role in {"tool", "function"}:
            name = message.name or message.tool_call_id or role
            normalized.append({"role": "user", "content": f"[{role}:{name}]\n{content}"})
        else:
            normalized.append({"role": role, "content": content})
    if not normalized:
        raise ValueError("messages is required")
    if not any(item["role"] == "user" for item in normalized):
        raise ValueError("at least one user message is required")
    return normalized


def _to_upstream_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    system_parts = [item["content"] for item in messages if item["role"] == "system" and item.get("content")]
    conversation: list[dict[str, str]] = []
    for item in messages:
        role = item["role"]
        if role == "system":
            continue
        conversation.append({"role": role, "content": str(item.get("content", ""))})

    upstream: list[dict[str, Any]] = []
    if system_parts:
        upstream.append({"role": "system", "content": "\n".join(system_parts)})
    upstream.append(
        {
            "role": "user",
            "content": (
                "The following JSON array contains a multi-turn conversation. "
                "Answer the latest user message using the full context. "
                "Do not repeat the conversation history.\n\n"
                + json.dumps(conversation, ensure_ascii=False)
            ),
        }
    )
    return upstream


def _completion_payload(
    *,
    request_id: str,
    model: str,
    answer: str,
    prompt_tokens: int = 0,
) -> dict[str, Any]:
    completion_tokens = max(1, len(answer) // 4)
    return {
        "id": request_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def _chunk_payload(request_id: str, model: str, delta: str, finish_reason: str | None = None) -> dict[str, Any]:
    choice: dict[str, Any] = {
        "index": 0,
        "delta": {"content": delta} if delta else {},
        "finish_reason": finish_reason,
    }
    return {
        "id": request_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [choice],
    }


def _sse_line(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=True)}\n\n"


async def _run_completion(
    request: OpenAIChatCompletionRequest,
    messages: list[dict[str, Any]] | None = None,
) -> tuple[str, str, list[dict[str, Any]]]:
    config = get_agnes_config()
    upstream_model = config.model_for("text")
    response_model = request.model or upstream_model
    messages = messages or _normalize_messages(request)
    upstream_messages = _to_upstream_messages(messages)
    try:
        answer = await run_in_threadpool(
            _chat_once,
            upstream_messages,
            upstream_model,
            request.temperature,
            request.max_tokens if request.max_tokens is not None else request.max_completion_tokens,
        )
    except Exception as exc:
        answer = f"Upstream model request failed: {exc}"

    if not answer:
        answer = "I could not generate a valid response. Please provide more context and try again."
    _persist_compat_session(messages, answer)
    return answer, response_model, messages


def _chat_once(
    messages: list[dict[str, Any]],
    model: str,
    temperature: float | None,
    max_tokens: int | None,
) -> str:
    config = get_agnes_config()
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    headers = {
        "Authorization": f"Bearer {config.api_key_for('text')}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=config.timeout_seconds, headers=headers) as client:
        response = client.post(f"{config.api_base_url_for('text')}/chat/completions", json=payload)

    text = response.text
    parsed = _parse_possible_json_prefix(text)
    if response.status_code >= 400:
        if parsed and "choices" in parsed:
            return _extract_completion_content(parsed).strip()
        error_message = _extract_error_message(parsed, text)
        raise RuntimeError(f"HTTP {response.status_code}: {error_message}")

    if parsed is None:
        raise RuntimeError(f"Invalid upstream response: {text[:500]}")
    answer = _extract_completion_content(parsed).strip()
    if not answer and _extract_finish_reason(parsed) == "length" and max_tokens is not None:
        retry_payload = dict(payload)
        retry_payload["max_tokens"] = max(max_tokens, UPSTREAM_EMPTY_LENGTH_RETRY_MAX_TOKENS)
        with httpx.Client(timeout=config.timeout_seconds, headers=headers) as client:
            response = client.post(f"{config.api_base_url_for('text')}/chat/completions", json=retry_payload)

        text = response.text
        parsed = _parse_possible_json_prefix(text)
        if response.status_code >= 400:
            if parsed and "choices" in parsed:
                return _extract_completion_content(parsed).strip()
            error_message = _extract_error_message(parsed, text)
            raise RuntimeError(f"HTTP {response.status_code}: {error_message}")
        if parsed is None:
            raise RuntimeError(f"Invalid upstream response: {text[:500]}")
        answer = _extract_completion_content(parsed).strip()
    return answer


def _parse_possible_json_prefix(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None
    decoder = json.JSONDecoder()
    try:
        parsed, _index = decoder.raw_decode(stripped)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _extract_completion_content(payload: dict[str, Any]) -> str:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return ""
    return _stringify_content(content)


def _extract_finish_reason(payload: dict[str, Any]) -> str | None:
    try:
        finish_reason = payload["choices"][0].get("finish_reason")
    except (KeyError, IndexError, TypeError, AttributeError):
        return None
    return str(finish_reason) if finish_reason is not None else None


def _extract_error_message(payload: dict[str, Any] | None, raw_text: str) -> str:
    if payload:
        error = payload.get("error")
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])
        if payload.get("message"):
            return str(payload["message"])
    return raw_text[:1000]


def _persist_compat_session(messages: list[dict[str, Any]], answer: str) -> None:
    try:
        repository = get_repository()
        session_id = repository.ensure_session(None, "openai_compat")
        stored_messages = [
            ChatMessage(role=item["role"], content=item.get("content", ""))
            for item in messages
            if item["role"] in {"system", "user", "assistant", "tool"}
        ]
        stored_messages.append(ChatMessage(role="assistant", content=answer))
        repository.append_messages(session_id, *stored_messages)
    except Exception:
        # Compatibility requests should not fail only because optional auditing failed.
        return


def _openai_error_response(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "message": message,
                "type": "invalid_request_error",
            }
        },
    )


def _validation_message(exc: ValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return str(exc)
    first = errors[0]
    location = ".".join(str(part) for part in first.get("loc", ()))
    message = first.get("msg", "Invalid request")
    return f"{location}: {message}" if location else str(message)


def _usage_payload(prompt_tokens: int, answer: str) -> dict[str, int]:
    completion_tokens = max(1, len(answer) // 4)
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }


def _should_stream_usage(request: OpenAIChatCompletionRequest) -> bool:
    options = request.stream_options or {}
    return bool(options.get("include_usage"))


@router.post("/chat/completions")
async def create_chat_completion(http_request: Request) -> Any:
    try:
        raw_payload = await http_request.json()
    except Exception as exc:
        return _openai_error_response(f"Invalid JSON request body: {exc}")

    try:
        request = OpenAIChatCompletionRequest.model_validate(raw_payload)
    except ValidationError as exc:
        return _openai_error_response(_validation_message(exc))

    try:
        normalized_messages = _normalize_messages(request)
    except ValueError as exc:
        return _openai_error_response(str(exc))

    request_id = f"chatcmpl-{uuid4().hex}"
    if request.stream:
        async def stream_events():
            try:
                answer, model, messages = await _run_completion(request, normalized_messages)
                prompt_tokens = sum(max(1, len(str(message.get("content", ""))) // 4) for message in messages)
                yield _sse_line(
                    {
                        "id": request_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"role": "assistant"},
                                "finish_reason": None,
                            }
                        ],
                    }
                )
                if answer:
                    yield _sse_line(_chunk_payload(request_id, model, answer))
                yield _sse_line(_chunk_payload(request_id, model, "", "stop"))
                if _should_stream_usage(request):
                    yield _sse_line(
                        {
                            "id": request_id,
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [],
                            "usage": _usage_payload(prompt_tokens, answer),
                        }
                    )
                yield "data: [DONE]\n\n"
            except Exception as exc:
                message = str(exc)
                model = request.model or get_agnes_config().model_for("text")
                yield _sse_line(
                    {
                        "id": request_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"role": "assistant"},
                                "finish_reason": None,
                            }
                        ],
                    }
                )
                yield _sse_line(_chunk_payload(request_id, model, f"Upstream model request failed: {message}"))
                yield _sse_line(_chunk_payload(request_id, model, "", "stop"))
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            stream_events(),
            media_type="text/event-stream; charset=utf-8",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    answer, model, messages = await _run_completion(request, normalized_messages)
    prompt_tokens = sum(max(1, len(str(message.get("content", ""))) // 4) for message in messages)
    return _completion_payload(
        request_id=request_id,
        model=model,
        answer=answer,
        prompt_tokens=prompt_tokens,
    )


@router.get("/models")
def list_models() -> dict[str, Any]:
    config = get_agnes_config()
    now = int(time.time())
    models = [
        model
        for model in (config.text_model, config.image_model, config.video_model)
        if model
    ]
    return {
        "object": "list",
        "data": [
            {"id": model, "object": "model", "created": now, "owned_by": "smart-assistant"}
            for model in models
        ],
    }
