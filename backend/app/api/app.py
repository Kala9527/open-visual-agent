from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routers import chat, config, health, images, openai_compat, sessions, videos
from backend.app.config import AgnesConfig
from backend.app.data import init_database


def create_app() -> FastAPI:
    app = FastAPI(
        title="Open Visual Agent API",
        version="0.2.0",
        description="FastAPI backend for AI image, video, prompt, and OpenAI-compatible creative workflows.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(config.router)
    app.include_router(chat.router)
    app.include_router(openai_compat.router)
    app.include_router(images.router)
    app.include_router(videos.router)
    app.include_router(sessions.router)

    @app.on_event("startup")
    def _startup() -> None:
        init_database(AgnesConfig.from_env().db_path)

    return app
