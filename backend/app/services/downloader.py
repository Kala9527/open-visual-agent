from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import httpx


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_b64_image(b64_json: str, output_path: Path) -> Path:
    ensure_dir(output_path.parent)
    output_path.write_bytes(base64.b64decode(b64_json))
    return output_path


def download_file(url: str, output_dir: Path, fallback_name: str) -> Path:
    ensure_dir(output_dir)
    parsed = urlparse(url)
    name = Path(parsed.path).name or fallback_name
    if "." not in name:
        content_type = _head_content_type(url)
        suffix = mimetypes.guess_extension(content_type or "") or ""
        name = f"{name}{suffix}" if suffix else fallback_name

    output_path = unique_path(output_dir / name)
    with httpx.stream("GET", url, follow_redirects=True, timeout=360) as response:
        response.raise_for_status()
        with output_path.open("wb") as file:
            for chunk in response.iter_bytes():
                file.write(chunk)
    return output_path


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    index = 1
    while True:
        candidate = parent / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def _head_content_type(url: str) -> str | None:
    try:
        response = httpx.head(url, follow_redirects=True, timeout=30)
        response.raise_for_status()
        return response.headers.get("content-type")
    except httpx.HTTPError:
        return None
