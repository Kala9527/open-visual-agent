from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agnes_ai_generation import AgnesAIClient, AgnesConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start a multi-turn Agnes AI chat.")
    parser.add_argument(
        "--system",
        default="You are a helpful AI assistant. Answer in Chinese by default.",
        help="System prompt.",
    )
    parser.add_argument("--model", help="Override text model.")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-tokens", type=int, default=1024)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    console = Console()
    config = AgnesConfig.from_env()
    messages = [{"role": "system", "content": args.system}]

    console.print("[bold]Agnes AI chat started.[/bold] Type exit, quit, or blank line to stop.")
    with AgnesAIClient(config) as client:
        while True:
            user_input = console.input("\n[bold cyan]You> [/bold cyan]").strip()
            if user_input.lower() in {"", "exit", "quit"}:
                break
            messages.append({"role": "user", "content": user_input})
            answer = client.chat(
                messages,
                model=args.model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            )
            messages.append({"role": "assistant", "content": answer})
            console.print("[bold green]Agnes>[/bold green]")
            console.print(answer, markup=False)

    output_path = config.output_dir / f"chat_transcript_{datetime.now():%Y%m%d_%H%M%S}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(messages, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    console.print(f"\nSaved transcript: {output_path}")


if __name__ == "__main__":
    main()
