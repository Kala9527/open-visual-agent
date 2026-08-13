from __future__ import annotations

import argparse

from common import (
    AgnesService,
    JsonArgumentParser,
    add_json_args,
    add_prompt_args,
    emit_error,
    emit_json,
    read_prompt,
)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        operation="generate_image",
        description="Generate images with Agnes AI and print machine-readable JSON."
    )
    add_prompt_args(parser)
    parser.add_argument("--size", default="1024x1024", help="Image size, e.g. 1024x1024.")
    parser.add_argument("--model", help="Override the image model.")
    parser.add_argument(
        "--image",
        "--image-url",
        dest="image_urls",
        action="append",
        default=[],
        help="Optional public image URL or data URI for image-to-image. Repeatable.",
    )
    parser.add_argument(
        "--return-base64",
        action="store_true",
        help="Ask for base64 output instead of URL output.",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Do not download returned image URLs.",
    )
    parser.add_argument("--n", type=int, help="Number of images if supported upstream.")
    parser.add_argument("--response-format", choices=["url", "b64_json"])
    parser.add_argument("--quality", help="Quality value if supported upstream.")
    parser.add_argument("--background", help="Background value if supported upstream.")
    parser.add_argument("--output-format", help="Output image format if supported upstream.")
    parser.add_argument("--output-compression", type=int, help="Compression 0-100 if supported.")
    parser.add_argument("--moderation", help="Moderation mode if supported upstream.")
    parser.add_argument("--user", help="End-user identifier sent upstream if supported.")
    parser.add_argument("--include-raw", action="store_true", help="Include raw upstream JSON.")
    add_json_args(parser)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        payload = AgnesService().generate_image(
            read_prompt(args),
            size=args.size,
            model=args.model,
            image_urls=args.image_urls,
            return_base64=args.return_base64,
            download=not args.no_download,
            include_raw=args.include_raw,
            n=args.n,
            response_format=args.response_format,
            quality=args.quality,
            background=args.background,
            output_format=args.output_format,
            output_compression=args.output_compression,
            moderation=args.moderation,
            user=args.user,
        )
        emit_json(payload, pretty=args.pretty)
    except Exception as exc:
        emit_error(
            "generate_image",
            exc,
            pretty=args.pretty,
            include_traceback=args.traceback,
        )


if __name__ == "__main__":
    main()
