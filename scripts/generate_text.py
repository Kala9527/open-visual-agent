from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agnes_ai_generation import AgnesAIClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate text with Agnes AI.")
    parser.add_argument("--prompt", required=True, help="User prompt.")
    parser.add_argument(
        "--system",
        default="You are a helpful AI assistant.",
        help="System prompt.",
    )
    parser.add_argument("--image-url", help="Optional public image URL for vision input.")
    parser.add_argument("--model", help="Override text model.")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--stream", action="store_true", help="Stream response.")
    parser.add_argument(
        "--enable-thinking",
        action="store_true",
        help="Send chat_template_kwargs.enable_thinking=true.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    console = Console()

    with AgnesAIClient() as client:
        user_content = (
            client.image_content(args.prompt, args.image_url)
            if args.image_url
            else args.prompt
        )
        messages = [
            {"role": "system", "content": args.system},
            {"role": "user", "content": user_content},
        ]
        result = client.chat(
            messages,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            stream=args.stream,
            enable_thinking=args.enable_thinking,
        )

    if not args.stream:
        console.print(result, markup=False)


if __name__ == "__main__":
    main()
