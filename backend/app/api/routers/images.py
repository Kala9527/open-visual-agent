from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from backend.app.api.deps import get_repository, get_service, raise_api_error
from backend.app.schemas.media import ImageGenerationRequest


router = APIRouter(prefix="/v1/images", tags=["images"])


@router.post("/generations")
async def generate_image(request: ImageGenerationRequest) -> dict[str, Any]:
    try:
        result = await run_in_threadpool(
            get_service().generate_image,
            request.prompt,
            size=request.size,
            model=request.model,
            image_urls=request.image_urls,
            return_base64=request.return_base64,
            download=request.download,
            include_raw=request.include_raw,
            n=request.n,
            response_format=request.response_format,
            quality=request.quality,
            background=request.background,
            output_format=request.output_format,
            output_compression=request.output_compression,
            moderation=request.moderation,
            user=request.user,
        )
        get_repository().save_media_output("image", result, request.prompt)
        return result
    except Exception as exc:
        raise_api_error(exc)
