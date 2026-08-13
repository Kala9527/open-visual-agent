from __future__ import annotations

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from backend.app.api.deps import get_agent, get_repository, raise_api_error
from backend.app.schemas.chat import ChatMessage, ChatRequest, ChatResponse


router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    repository = get_repository()
    session_id = repository.ensure_session(request.session_id, request.scenario)
    history = [*repository.get_messages(session_id), *request.history]
    try:
        result = await run_in_threadpool(
            get_agent().run,
            request.message,
            scenario=request.scenario,
            history=history,
            use_tools=request.use_tools,
        )
    except Exception as exc:
        raise_api_error(exc)

    repository.append_messages(
        session_id,
        ChatMessage(role="user", content=request.message),
        ChatMessage(role="assistant", content=result["answer"]),
    )
    return ChatResponse(
        ok=True,
        session_id=session_id,
        scenario=result.get("scenario") or request.scenario or "default",
        answer=result["answer"],
        messages=repository.get_messages(session_id),
        tool_calls=result.get("tool_calls", []),
        raw=result.get("raw", {}),
    )


@router.post("/agent/run", response_model=ChatResponse)
async def agent_run(request: ChatRequest) -> ChatResponse:
    return await chat(request)
