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
        operation="generate_video",
        description="Create an Agnes AI video task, optionally wait for completion, and print JSON."
    )
    add_prompt_args(parser)
    parser.add_argument("--model", help="Override the video model.")
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
    parser.add_argument("--num-inference-steps", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--negative-prompt")
    parser.add_argument("--wait", action="store_true", help="Poll until the task reaches a result.")
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--download", action="store_true", help="Download the final video if available.")
    parser.add_argument("--include-raw", action="store_true", help="Include raw upstream JSON.")
    add_json_args(parser)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        payload = AgnesService().generate_video(
            read_prompt(args),
            wait=args.wait,
            poll_seconds=args.poll_seconds,
            timeout_seconds=args.timeout_seconds,
            download=args.download,
            include_raw=args.include_raw,
            model=args.model,
            image=args.image,
            extra_images=args.extra_image,
            mode=args.mode,
            width=args.width,
            height=args.height,
            num_frames=args.num_frames,
            frame_rate=args.frame_rate,
            num_inference_steps=args.num_inference_steps,
            seed=args.seed,
            negative_prompt=args.negative_prompt,
        )
        emit_json(payload, pretty=args.pretty)
    except Exception as exc:
        emit_error(
            "generate_video",
            exc,
            pretty=args.pretty,
            include_traceback=args.traceback,
        )


if __name__ == "__main__":
    main()
