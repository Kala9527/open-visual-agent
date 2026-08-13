from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from fastapi.concurrency import run_in_threadpool

from backend.app.api.deps import get_repository, get_service, raise_api_error
from backend.app.schemas.media import VideoCreateRequest


router = APIRouter(prefix="/v1/videos", tags=["videos"])


@router.post("")
async def create_video(request: VideoCreateRequest) -> dict[str, Any]:
    request_payload = request.model_dump()
    try:
        if request.wait:
            result = await run_in_threadpool(
                get_service().generate_video,
                request.prompt,
                wait=True,
                poll_seconds=request.poll_seconds,
                timeout_seconds=request.timeout_seconds,
                download=request.download,
                include_raw=request.include_raw,
                model=request.model,
                image=request.image,
                extra_images=request.extra_images,
                mode=request.mode,
                width=request.width,
                height=request.height,
                num_frames=request.num_frames,
                frame_rate=request.frame_rate,
                num_inference_steps=request.num_inference_steps,
                seed=request.seed,
                negative_prompt=request.negative_prompt,
            )
        else:
            result = await run_in_threadpool(
                get_service().create_video_task,
                request.prompt,
                model=request.model,
                image=request.image,
                extra_images=request.extra_images,
                mode=request.mode,
                width=request.width,
                height=request.height,
                num_frames=request.num_frames,
                frame_rate=request.frame_rate,
                num_inference_steps=request.num_inference_steps,
                seed=request.seed,
                negative_prompt=request.negative_prompt,
                include_raw=request.include_raw,
            )
    except Exception as exc:
        raise_api_error(exc)

    get_repository().save_video_task(result, request_payload)
    return result


@router.get("/{task_id}")
async def get_video(
    task_id: str,
    video_id: str | None = Query(default=None),
    model_name: str | None = Query(default=None),
    download: bool = Query(default=False),
    include_raw: bool = Query(default=False),
) -> dict[str, Any]:
    repository = get_repository()
    stored = repository.get_video_task(task_id) or {}
    resolved_video_id = video_id or stored.get("video_id")
    resolved_task_id = None if resolved_video_id else task_id
    try:
        result = await run_in_threadpool(
            get_service().get_video_result,
            video_id=resolved_video_id,
            task_id=resolved_task_id,
            model_name=model_name,
            download=download,
            include_raw=include_raw,
        )
        repository.update_video_result(task_id, result)
        return result
    except Exception as exc:
        raise_api_error(exc)


@router.get("/{task_id}/local")
def get_local_video_task(task_id: str) -> dict[str, Any]:
    stored = get_repository().get_video_task(task_id)
    return {"ok": bool(stored), "task": stored}
