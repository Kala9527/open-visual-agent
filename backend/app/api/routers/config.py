from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.app.api.deps import display_path, get_agent_config, get_agnes_config


router = APIRouter(prefix="/v1/config", tags=["config"])


@router.get("/scenarios")
def list_scenarios() -> dict[str, Any]:
    config = get_agent_config()
    return {
        "identity": config.identity,
        "default_scenario": config.default_scenario,
        "skills_doc_paths": [display_path(path) for path in config.skills_doc_paths],
        "scenarios": {
            name: {
                "name": scenario.name,
                "description": scenario.description,
                "skills_doc_paths": [display_path(path) for path in scenario.skills_doc_paths],
            }
            for name, scenario in config.scenarios.items()
        },
    }


@router.get("/runtime")
def runtime_config() -> dict[str, Any]:
    agnes = get_agnes_config()
    agent = get_agent_config()
    return {
        "text_api_base_url": agnes.text_api_base_url,
        "text_model": agnes.text_model,
        "image_api_base_url": agnes.image_api_base_url,
        "image_model": agnes.image_model,
        "video_api_base_url": agnes.video_api_base_url,
        "video_status_base_url": agnes.video_status_base_url,
        "video_model": agnes.video_model,
        "output_dir": display_path(agnes.output_dir),
        "db_path": display_path(agnes.db_path),
        "agent_identity": agent.identity,
        "default_scenario": agent.default_scenario,
    }
