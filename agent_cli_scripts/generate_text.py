from __future__ import annotations

import argparse

from common import (
    AgnesService,
    JsonArgumentParser,
    add_json_args,
    add_prompt_args,
    emit_error,
    emit_json,
    read_optional_file,
    read_prompt,
    write_text_output,
)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        operation="generate_text",
        description="Generate text with Agnes AI and print machine-readable JSON."
    )
    add_prompt_args(parser)
    parser.add_argument(
        "--system",
        default="You are a helpful AI assistant.",
        help="System prompt.",
    )
    parser.add_argument("--system-file", help="Read the system prompt from a file.")
    parser.add_argument("--image-url", help="Optional public image URL for vision input.")
    parser.add_argument("--model", help="Override the text model.")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument(
        "--enable-thinking",
        action="store_true",
        help="Send chat_template_kwargs.enable_thinking=true.",
    )
    parser.add_argument("--output", help="Optional file path for saving generated text.")
    add_json_args(parser)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        prompt = read_prompt(args)
        system = (
            read_optional_file(args.system_file, encoding=args.input_encoding)
            if args.system_file
            else args.system
        )
        payload = AgnesService().generate_text(
            prompt,
            system=system,
            image_url=args.image_url,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            enable_thinking=args.enable_thinking,
        )
        if args.output:
            output_path = write_text_output(args.output, payload["content"])
            payload["local_path"] = str(output_path)
        emit_json(payload, pretty=args.pretty)
    except Exception as exc:
        emit_error(
            "generate_text",
            exc,
            pretty=args.pretty,
            include_traceback=args.traceback,
        )


if __name__ == "__main__":
    main()
