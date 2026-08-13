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
from agnes_ai_generation.downloader import download_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate videos with Agnes AI.")
    parser.add_argument("--prompt", required=True, help="Video prompt.")
    parser.add_argument("--model", help="Override video model.")
    parser.add_argument("--image", help="Single public image URL for image-to-video.")
    parser.add_argument(
        "--extra-image",
        action="append",
        default=[],
        help="Reference image URL for multi-image/keyframe generation. Repeatable.",
    )
    parser.add_argument("--mode", choices=["ti2vid", "keyframes"], help="Optional generation mode.")
    parser.add_argument("--width", type=int, default=1152)
    parser.add_argument("--height", type=int, default=768)
    parser.add_argument("--num-frames", type=int, default=121)
    parser.add_argument("--frame-rate", type=int, default=24)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--negative-prompt")
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Create the video task only; do not wait for the final result.",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Do not download the final video file.",
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
        task = client.create_video_task(
            args.prompt,
            model=args.model,
            image=args.image,
            extra_images=args.extra_image,
            mode=args.mode,
            width=args.width,
            height=args.height,
            num_frames=args.num_frames,
            frame_rate=args.frame_rate,
            seed=args.seed,
            negative_prompt=args.negative_prompt,
        )
        console.print("Created video task:")
        console.print(json.dumps(task.raw, ensure_ascii=False, indent=2))

        if args.no_wait:
            console.print("\nVideo task was created. Run without --no-wait to poll and download the result.")
            return

        console.print("\nWaiting for video result...")
        result = client.wait_for_video(
            task,
            poll_seconds=args.poll_seconds,
            timeout_seconds=args.timeout_seconds,
        )
        console.print(json.dumps(result.raw, ensure_ascii=False, indent=2))

    if result.video_url:
        console.print(f"\nVideo URL: {result.video_url}", markup=False)
        if not args.no_download:
            output_path = download_file(
                result.video_url,
                config.output_dir / "videos",
                f"agnes_video_{datetime.now():%Y%m%d_%H%M%S}.mp4",
            )
            console.print(f"Downloaded: {output_path}", markup=False)
    else:
        console.print("\nNo video URL was returned.")


if __name__ == "__main__":
    main()
