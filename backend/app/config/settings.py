from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AGENT_IDENTITY = "open_visual_agent"
DEFAULT_AGENT_SYSTEM_PROMPT = """You are Open Visual Agent, a practical creative AI copilot.
Help users turn product, marketing, and content ideas into precise prompts, visual briefs, image requests,
video tasks, and implementation steps. Be concise, concrete, and useful. When a tool call is useful,
confirm the minimum required inputs, then explain what output the user should expect."""
DEFAULT_SKILLS_DOC_PATHS = ("README.md", "prompts/visual-growth-pack.md")


def _load_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv()


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _resolve_project_path(value: str) -> Path:
    path = Path(value.strip())
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _parse_path_list(value: str | None, default: tuple[str, ...]) -> tuple[Path, ...]:
    raw_items = value.split(";") if value else default
    return tuple(_resolve_project_path(item) for item in raw_items if item.strip())


def _load_prompt_from_file(path_value: str | None) -> str | None:
    if not path_value:
        return None
    prompt_path = _resolve_project_path(path_value)
    if not prompt_path.exists():
        raise ValueError(f"Agent prompt file was not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _normalize_base_url(value: str) -> str:
    return value.strip().rstrip("/")


def _is_missing_secret(value: str) -> bool:
    normalized = value.strip()
    return not normalized or normalized in {
        "YOUR_API_KEY",
        "YOUR_SHARED_API_KEY",
        "YOUR_TEXT_PROVIDER_API_KEY",
        "YOUR_IMAGE_PROVIDER_API_KEY",
        "YOUR_VIDEO_PROVIDER_API_KEY",
    }


@dataclass(frozen=True)
class AgnesConfig:
    platform_url: str = "https://platform.agnes-ai.com/"
    text_api_key: str = ""
    text_api_base_url: str = ""
    text_model: str = ""
    image_api_key: str = ""
    image_api_base_url: str = ""
    image_model: str = ""
    video_api_key: str = ""
    video_api_base_url: str = ""
    video_status_base_url: str | None = None
    video_model: str = ""
    timeout_seconds: float = 360.0
    output_dir: Path = PROJECT_ROOT / "outputs"
    db_path: Path = PROJECT_ROOT / "backend" / "app" / "data" / "open_visual_agent.sqlite3"

    @classmethod
    def from_env(cls) -> "AgnesConfig":
        _load_env()

        output_dir = _resolve_project_path(os.getenv("AGNES_OUTPUT_DIR", "outputs"))
        db_path = _resolve_project_path(
            os.getenv("AGNES_DB_PATH", "backend/app/data/open_visual_agent.sqlite3")
        )

        return cls(
            platform_url=os.getenv("AGNES_PLATFORM_URL", cls.platform_url),
            text_api_key=_env("AGNES_TEXT_API_KEY"),
            text_api_base_url=_normalize_base_url(_env("AGNES_TEXT_API_BASE_URL")),
            text_model=_env("AGNES_TEXT_MODEL"),
            image_api_key=_env("AGNES_IMAGE_API_KEY"),
            image_api_base_url=_normalize_base_url(_env("AGNES_IMAGE_API_BASE_URL")),
            image_model=_env("AGNES_IMAGE_MODEL"),
            video_api_key=_env("AGNES_VIDEO_API_KEY"),
            video_api_base_url=_normalize_base_url(_env("AGNES_VIDEO_API_BASE_URL")),
            video_status_base_url=_normalize_base_url(_env("AGNES_VIDEO_STATUS_BASE_URL")) or None,
            video_model=_env("AGNES_VIDEO_MODEL"),
            timeout_seconds=float(os.getenv("AGNES_TIMEOUT_SECONDS", str(cls.timeout_seconds))),
            output_dir=output_dir,
            db_path=db_path,
        )

    @property
    def video_gateway_url(self) -> str:
        return (self.video_status_base_url or self.api_base_url_for("video").removesuffix("/v1")).rstrip("/")

    def api_key_for(self, capability: str) -> str:
        env_name = f"AGNES_{capability.upper()}_API_KEY"
        value = getattr(self, f"{capability}_api_key", "")
        if _is_missing_secret(value):
            raise ValueError(f"{env_name} is missing. Edit .env and set the {capability} provider API key.")
        return value

    def api_base_url_for(self, capability: str) -> str:
        env_name = f"AGNES_{capability.upper()}_API_BASE_URL"
        value = getattr(self, f"{capability}_api_base_url", "").strip().rstrip("/")
        if not value:
            raise ValueError(f"{env_name} is missing. Edit .env and set the {capability} provider base URL.")
        return value

    def model_for(self, capability: str) -> str:
        env_name = f"AGNES_{capability.upper()}_MODEL"
        value = getattr(self, f"{capability}_model", "").strip()
        if not value:
            raise ValueError(f"{env_name} is missing. Edit .env and set the {capability} model.")
        return value


@dataclass(frozen=True)
class AgentScenario:
    name: str
    description: str
    system_prompt: str
    skills_doc_paths: tuple[Path, ...] = ()


def _default_scenarios(skills_doc_paths: tuple[Path, ...]) -> dict[str, AgentScenario]:
    return {
        "default": AgentScenario(
            name="default",
            description="General creative copilot for prompt writing, planning, and tool orchestration.",
            system_prompt=DEFAULT_AGENT_SYSTEM_PROMPT,
            skills_doc_paths=skills_doc_paths,
        ),
        "growth_marketer": AgentScenario(
            name="growth_marketer",
            description="Turns products into launch visuals, thumbnails, short-form concepts, and campaign prompts.",
            system_prompt=(
                DEFAULT_AGENT_SYSTEM_PROMPT
                + "\nAct like a practical growth marketer. Suggest assets that can ship today, avoid vague strategy, "
                "and turn every recommendation into a concrete prompt or checklist."
            ),
            skills_doc_paths=skills_doc_paths,
        ),
        "creative_director": AgentScenario(
            name="creative_director",
            description="Creates image and video briefs with visual style, composition, camera, lighting, and constraints.",
            system_prompt=(
                DEFAULT_AGENT_SYSTEM_PROMPT
                + "\nAct like a creative director. Produce crisp briefs with subject, composition, lighting, mood, "
                "camera, aspect ratio, negative constraints, and iteration notes."
            ),
            skills_doc_paths=skills_doc_paths,
        ),
        "developer_advocate": AgentScenario(
            name="developer_advocate",
            description="Explains API usage, CLI workflows, docs, demos, and contribution-ready examples.",
            system_prompt=(
                DEFAULT_AGENT_SYSTEM_PROMPT
                + "\nAct like a developer advocate. Make examples copy-pasteable and explain deployment tradeoffs "
                "without hiding required environment variables."
            ),
            skills_doc_paths=skills_doc_paths,
        ),
    }


@dataclass(frozen=True)
class AgentConfig:
    identity: str
    default_scenario: str
    system_prompt: str
    skills_doc_paths: tuple[Path, ...]
    enable_tools: bool
    scenarios: Mapping[str, AgentScenario]

    @classmethod
    def from_env(cls) -> "AgentConfig":
        _load_env()

        skills_doc_paths = _parse_path_list(
            os.getenv("AGENT_SKILLS_DOC_PATHS"),
            DEFAULT_SKILLS_DOC_PATHS,
        )
        prompt = (
            os.getenv("AGENT_SYSTEM_PROMPT", "").strip()
            or _load_prompt_from_file(os.getenv("AGENT_SYSTEM_PROMPT_FILE"))
            or DEFAULT_AGENT_SYSTEM_PROMPT
        )
        scenarios = _default_scenarios(skills_doc_paths)
        scenarios["default"] = AgentScenario(
            name="default",
            description=scenarios["default"].description,
            system_prompt=prompt,
            skills_doc_paths=skills_doc_paths,
        )

        return cls(
            identity=os.getenv("AGENT_IDENTITY", DEFAULT_AGENT_IDENTITY).strip()
            or DEFAULT_AGENT_IDENTITY,
            default_scenario=os.getenv("AGENT_DEFAULT_SCENARIO", "growth_marketer").strip()
            or "growth_marketer",
            system_prompt=prompt,
            skills_doc_paths=skills_doc_paths,
            enable_tools=_parse_bool(os.getenv("AGENT_ENABLE_TOOLS"), True),
            scenarios=scenarios,
        )

    def get_scenario(self, scenario: str | None = None) -> AgentScenario:
        name = (scenario or self.default_scenario or "default").strip()
        return self.scenarios.get(name) or self.scenarios["default"]
