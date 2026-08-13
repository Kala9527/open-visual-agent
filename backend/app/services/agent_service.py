from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from backend.app.config import AgentConfig, AgnesConfig
from backend.app.schemas.chat import ChatMessage
from backend.app.services.agnes_service import AgnesService
from backend.app.services.langchain_tools import build_langchain_tools


class SmartAssistantAgent:
    def __init__(
        self,
        agnes_config: AgnesConfig | None = None,
        agent_config: AgentConfig | None = None,
        service: AgnesService | None = None,
    ) -> None:
        self.agnes_config = agnes_config or AgnesConfig.from_env()
        self.agent_config = agent_config or AgentConfig.from_env()
        self.service = service or AgnesService(self.agnes_config)
        self.tools = build_langchain_tools(self.service)
        self.model = ChatOpenAI(
            api_key=self.agnes_config.api_key_for("text"),
            base_url=self.agnes_config.api_base_url_for("text"),
            model=self.agnes_config.model_for("text"),
            timeout=self.agnes_config.timeout_seconds,
        )

    def run(
        self,
        message: str,
        *,
        scenario: str | None = None,
        history: list[ChatMessage] | None = None,
        use_tools: bool | None = None,
    ) -> dict[str, Any]:
        selected = self.agent_config.get_scenario(scenario)
        system_prompt = self._build_system_prompt(selected.system_prompt, selected.skills_doc_paths)
        lc_history = self._to_langchain_messages(history or [])
        lc_messages = [*lc_history, HumanMessage(content=message)]
        allow_tools = self.agent_config.enable_tools if use_tools is None else use_tools

        if allow_tools:
            try:
                agent = create_agent(
                    model=self.model,
                    tools=self.tools,
                    system_prompt=system_prompt,
                )
                state = agent.invoke({"messages": self._to_agent_payload(lc_messages)})
                final_messages = state.get("messages", [])
                return {
                    "ok": True,
                    "scenario": selected.name,
                    "answer": self._last_ai_content(final_messages),
                    "messages": self._to_schema_messages(final_messages),
                    "tool_calls": self._extract_tool_calls(final_messages),
                    "raw": {"mode": "agent"},
                }
            except Exception as exc:
                fallback = self._direct_invoke(system_prompt, lc_messages, selected.name)
                fallback["raw"] = {
                    "mode": "direct_fallback",
                    "agent_error": f"{exc.__class__.__name__}: {exc}",
                }
                return fallback

        return self._direct_invoke(system_prompt, lc_messages, selected.name)

    def _direct_invoke(
        self,
        system_prompt: str,
        messages: list[BaseMessage],
        scenario: str,
    ) -> dict[str, Any]:
        response = self.model.invoke([SystemMessage(content=system_prompt), *messages])
        return {
            "ok": True,
            "scenario": scenario,
            "answer": str(response.content or ""),
            "messages": self._to_schema_messages([*messages, response]),
            "tool_calls": [],
            "raw": {"mode": "direct"},
        }

    @staticmethod
    def _build_system_prompt(prompt: str, skills_doc_paths: tuple[Any, ...]) -> str:
        if not skills_doc_paths:
            return prompt
        rendered_paths = "\n".join(f"- {path}" for path in skills_doc_paths)
        return f"{prompt}\n\n可参考的 skills/说明文档路径：\n{rendered_paths}"

    @staticmethod
    def _to_langchain_messages(messages: list[ChatMessage]) -> list[BaseMessage]:
        converted: list[BaseMessage] = []
        for item in messages:
            if item.role == "system":
                converted.append(SystemMessage(content=str(item.content)))
            elif item.role == "assistant":
                converted.append(AIMessage(content=str(item.content)))
            elif item.role == "user":
                converted.append(HumanMessage(content=str(item.content)))
        return converted

    @staticmethod
    def _to_agent_payload(messages: list[BaseMessage]) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        for item in messages:
            role = "user"
            if item.type == "ai":
                role = "assistant"
            elif item.type == "system":
                role = "system"
            payload.append({"role": role, "content": item.content})
        return payload

    @staticmethod
    def _last_ai_content(messages: list[Any]) -> str:
        for item in reversed(messages):
            content = getattr(item, "content", None)
            if getattr(item, "type", None) in {"ai", "assistant"} and content:
                return str(content)
            if isinstance(item, dict) and item.get("role") == "assistant":
                return str(item.get("content", ""))
        return ""

    @staticmethod
    def _to_schema_messages(messages: list[Any]) -> list[ChatMessage]:
        rendered: list[ChatMessage] = []
        for item in messages:
            if isinstance(item, dict):
                role = item.get("role", "assistant")
                if role in {"system", "user", "assistant", "tool"}:
                    rendered.append(ChatMessage(role=role, content=item.get("content", "")))
                continue
            msg_type = getattr(item, "type", "")
            role = {"human": "user", "ai": "assistant", "system": "system", "tool": "tool"}.get(
                msg_type,
                "assistant",
            )
            rendered.append(ChatMessage(role=role, content=getattr(item, "content", "")))
        return rendered

    @staticmethod
    def _extract_tool_calls(messages: list[Any]) -> list[dict[str, Any]]:
        calls: list[dict[str, Any]] = []
        for item in messages:
            tool_calls = getattr(item, "tool_calls", None)
            if tool_calls:
                calls.extend(tool_calls)
        return calls
