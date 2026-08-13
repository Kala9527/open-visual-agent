from __future__ import annotations

from typing import Any

from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "service": "open-visual-agent-api"}
