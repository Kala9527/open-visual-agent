from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from backend.app.schemas.chat import ChatMessage

from .database import connect, init_database


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._lock = Lock()
        init_database(db_path)

    def ensure_session(self, session_id: str | None = None, scenario: str | None = None) -> str:
        sid = session_id or uuid4().hex
        now = utc_now()
        with self._lock, connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO chat_sessions(id, scenario, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    scenario = COALESCE(excluded.scenario, chat_sessions.scenario),
                    updated_at = excluded.updated_at
                """,
                (sid, scenario, now, now),
            )
        return sid

    def get_messages(self, session_id: str) -> list[ChatMessage]:
        with self._lock, connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT role, content_json
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY position ASC, id ASC
                """,
                (session_id,),
            ).fetchall()
        return [
            ChatMessage(role=row["role"], content=json.loads(row["content_json"]))
            for row in rows
        ]

    def append_messages(self, session_id: str, *messages: ChatMessage) -> None:
        if not messages:
            return
        now = utc_now()
        with self._lock, connect(self.db_path) as connection:
            current_position = connection.execute(
                "SELECT COALESCE(MAX(position), -1) AS max_position FROM chat_messages WHERE session_id = ?",
                (session_id,),
            ).fetchone()["max_position"]
            for offset, message in enumerate(messages, start=1):
                connection.execute(
                    """
                    INSERT INTO chat_messages(session_id, role, content_json, position, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        message.role,
                        json.dumps(message.content, ensure_ascii=False),
                        current_position + offset,
                        now,
                    ),
                )
            connection.execute(
                "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )

    def clear_session(self, session_id: str) -> None:
        with self._lock, connect(self.db_path) as connection:
            connection.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))

    def list_sessions(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock, connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT s.id, s.scenario, s.created_at, s.updated_at, COUNT(m.id) AS message_count
                FROM chat_sessions s
                LEFT JOIN chat_messages m ON m.session_id = s.id
                GROUP BY s.id
                ORDER BY s.updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_video_task(self, payload: dict[str, Any], request: dict[str, Any] | None = None) -> None:
        task_id = payload.get("task_id") or payload.get("task", {}).get("task_id")
        if not task_id:
            return
        task = payload.get("task") if isinstance(payload.get("task"), dict) else payload
        now = utc_now()
        with self._lock, connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO video_tasks(
                    task_id, video_id, status, prompt, model, request_json, raw_json,
                    result_json, video_url, local_path, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    video_id = COALESCE(excluded.video_id, video_tasks.video_id),
                    status = COALESCE(excluded.status, video_tasks.status),
                    request_json = excluded.request_json,
                    raw_json = excluded.raw_json,
                    result_json = excluded.result_json,
                    video_url = COALESCE(excluded.video_url, video_tasks.video_url),
                    local_path = COALESCE(excluded.local_path, video_tasks.local_path),
                    updated_at = excluded.updated_at
                """,
                (
                    task_id,
                    task.get("video_id"),
                    task.get("status"),
                    (request or {}).get("prompt") or payload.get("prompt"),
                    task.get("model") or (request or {}).get("model"),
                    json.dumps(request or {}, ensure_ascii=False),
                    json.dumps(task.get("raw", payload), ensure_ascii=False, default=str),
                    json.dumps(payload.get("result") or {}, ensure_ascii=False, default=str),
                    payload.get("video_url"),
                    payload.get("local_path"),
                    now,
                    now,
                ),
            )

    def update_video_result(self, task_id: str, payload: dict[str, Any]) -> None:
        now = utc_now()
        with self._lock, connect(self.db_path) as connection:
            connection.execute(
                """
                UPDATE video_tasks
                SET status = ?, result_json = ?, video_url = ?, local_path = ?, updated_at = ?
                WHERE task_id = ?
                """,
                (
                    payload.get("status"),
                    json.dumps(payload, ensure_ascii=False, default=str),
                    payload.get("video_url"),
                    payload.get("local_path"),
                    now,
                    task_id,
                ),
            )

    def get_video_task(self, task_id: str) -> dict[str, Any] | None:
        with self._lock, connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM video_tasks WHERE task_id = ?",
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        data = dict(row)
        for key in ("request_json", "raw_json", "result_json", "metadata_json"):
            if key in data and data[key]:
                try:
                    data[key] = json.loads(data[key])
                except json.JSONDecodeError:
                    pass
        return data

    def save_media_output(self, media_type: str, payload: dict[str, Any], prompt: str | None = None) -> None:
        now = utc_now()
        with self._lock, connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO media_outputs(media_type, prompt, remote_url, local_path, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    media_type,
                    prompt,
                    payload.get("url") or payload.get("video_url"),
                    payload.get("local_path"),
                    json.dumps(payload, ensure_ascii=False, default=str),
                    now,
                ),
            )
