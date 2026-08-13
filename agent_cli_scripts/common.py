from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent


def _prepend_import_path(path: Path) -> None:
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)


_prepend_import_path(PROJECT_ROOT)
_prepend_import_path(PROJECT_ROOT / "src")

from backend.app.services.agnes_service import AgnesService, exception_payload  # noqa: E402


class JsonArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args: Any, operation: str, **kwargs: Any) -> None:
        self.operation = operation
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> None:
        payload = {
            "ok": False,
            "type": "error",
            "operation": self.operation,
            "error": {
                "kind": "ArgumentError",
                "message": message,
                "status_code": None,
            },
            "usage": self.format_usage().strip(),
        }
        pretty = "--pretty" in sys.argv[1:]
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None))
        sys.stdout.write("\n")
        raise SystemExit(2)


def add_json_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument(
        "--traceback",
        action="store_true",
        help="Include a Python traceback in error JSON.",
    )


def add_prompt_args(parser: argparse.ArgumentParser) -> None:
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--prompt", help="Prompt text.")
    source.add_argument("--prompt-file", help="Read prompt text from a file.")
    source.add_argument("--stdin", action="store_true", help="Read prompt text from stdin.")
    parser.add_argument(
        "--input-encoding",
        default="utf-8",
        help="Encoding for prompt/system files.",
    )


def read_prompt(args: argparse.Namespace) -> str:
    return read_text_source(
        value=getattr(args, "prompt", None),
        file_value=getattr(args, "prompt_file", None),
        from_stdin=getattr(args, "stdin", False),
        encoding=getattr(args, "input_encoding", "utf-8"),
        label="prompt",
    )


def read_text_source(
    *,
    value: str | None,
    file_value: str | None,
    from_stdin: bool,
    encoding: str,
    label: str,
) -> str:
    if file_value:
        text = resolve_cli_path(file_value).read_text(encoding=encoding)
    elif from_stdin:
        text = sys.stdin.read()
    else:
        text = value or ""

    if not text.strip():
        raise ValueError(f"{label} is empty.")
    return text


def read_optional_file(path_value: str | None, *, encoding: str) -> str | None:
    if not path_value:
        return None
    return resolve_cli_path(path_value).read_text(encoding=encoding)


def resolve_cli_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return Path.cwd() / path


def write_text_output(path_value: str, content: str, *, encoding: str = "utf-8") -> Path:
    path = resolve_cli_path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)
    return path


def emit_json(payload: dict[str, Any], *, pretty: bool, exit_code: int = 0) -> None:
    indent = 2 if pretty else None
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=indent, default=str))
    sys.stdout.write("\n")
    raise SystemExit(exit_code)


def emit_error(
    operation: str,
    exc: Exception,
    *,
    pretty: bool,
    include_traceback: bool,
) -> None:
    payload: dict[str, Any] = {
        "ok": False,
        "type": "error",
        "operation": operation,
        "error": exception_payload(exc),
    }
    if include_traceback:
        payload["traceback"] = traceback.format_exc()
    emit_json(payload, pretty=pretty, exit_code=1)
