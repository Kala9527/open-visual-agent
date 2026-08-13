from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agnes_ai_generation import AgnesAIClient, AgnesConfig
from agnes_ai_generation.downloader import download_file, save_b64_image, unique_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate images with Agnes AI.")
    parser.add_argument("--prompt", required=True, help="Image prompt.")
    parser.add_argument("--size", default="1024x768", help="Image size, e.g. 1024x768.")
    parser.add_argument("--model", help="Override image model.")
    parser.add_argument(
        "--image",
        action="append",
        default=[],
        help="Optional public image URL or data URI for image-to-image. Repeatable.",
    )
    parser.add_argument(
        "--base64",
        action="store_true",
        help="Ask for base64 output instead of URL output.",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Do not download image files returned as URLs.",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    console = Console()
    config = AgnesConfig.from_env()

    with AgnesAIClient(config) as client:
        result = client.generate_image(
            args.prompt,
            model=args.model,
            size=args.size,
            image_urls=args.image,
            response_format="b64_json" if args.base64 else "url",
            return_base64=args.base64,
        )

    if result.url:
        console.print(f"Image URL: {result.url}", markup=False)
        if not args.no_download:
            output_path = download_file(
                result.url,
                config.output_dir / "images",
                f"agnes_image_{datetime.now():%Y%m%d_%H%M%S}.png",
            )
            console.print(f"Downloaded: {output_path}", markup=False)
    elif result.b64_json:
        output_path = unique_path(
            config.output_dir / "images" / f"agnes_image_{datetime.now():%Y%m%d_%H%M%S}.png"
        )
        save_b64_image(result.b64_json, output_path)
        console.print(f"Saved base64 image: {output_path}", markup=False)
    else:
        console.print("No image URL or base64 image was returned.")


if __name__ == "__main__":
    main()
