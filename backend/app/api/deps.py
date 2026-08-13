from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException

from backend.app.config import AgentConfig, AgnesConfig, PROJECT_ROOT
from backend.app.data import SQLiteRepository
from backend.app.services.agent_service import SmartAssistantAgent
from backend.app.services.agnes_service import AgnesService, exception_payload, is_http_error
from backend.app.services.agnes_client import ImageUpstreamError


def display_path(path: Any) -> str:
    try:
        return str(Path(path).relative_to(PROJECT_ROOT))
    except (TypeError, ValueError):
        return str(path)


def get_agnes_config() -> AgnesConfig:
    return AgnesConfig.from_env()


def get_agent_config() -> AgentConfig:
    return AgentConfig.from_env()


def get_repository() -> SQLiteRepository:
    return SQLiteRepository(get_agnes_config().db_path)


def get_service() -> AgnesService:
    return AgnesService(get_agnes_config())


def get_agent() -> SmartAssistantAgent:
    agnes_config = get_agnes_config()
    return SmartAssistantAgent(
        agnes_config=agnes_config,
        agent_config=get_agent_config(),
        service=AgnesService(agnes_config),
    )


def raise_api_error(exc: Exception) -> None:
    payload = exception_payload(exc)
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=payload) from exc
    if isinstance(exc, ImageUpstreamError):
        raise HTTPException(status_code=exc.status_code, detail=payload) from exc
    if is_http_error(exc):
        raise HTTPException(status_code=payload.get("status_code") or 502, detail=payload) from exc
    raise HTTPException(status_code=500, detail=payload) from exc
