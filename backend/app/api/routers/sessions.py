from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from backend.app.api.deps import get_repository


router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


@router.get("")
def list_sessions(limit: int = Query(default=50, ge=1, le=200)) -> dict[str, Any]:
    return {"sessions": get_repository().list_sessions(limit)}


@router.get("/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "messages": [message.model_dump() for message in get_repository().get_messages(session_id)],
    }


@router.delete("/{session_id}")
def clear_session(session_id: str) -> dict[str, Any]:
    get_repository().clear_session(session_id)
    return {"ok": True, "session_id": session_id}
