from __future__ import annotations

import argparse

from common import AgnesService, JsonArgumentParser, add_json_args, emit_error, emit_json


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        operation="video_status",
        description="Check an Agnes AI video task by task_id or video_id and print JSON."
    )
    ids = parser.add_mutually_exclusive_group(required=True)
    ids.add_argument("--task-id", help="Task id returned by generate_video.py.")
    ids.add_argument("--video-id", help="Video id returned by generate_video.py.")
    parser.add_argument("--model-name", help="Model name for video_id lookups.")
    parser.add_argument("--download", action="store_true", help="Download final video if available.")
    parser.add_argument("--include-raw", action="store_true", help="Include raw upstream JSON.")
    add_json_args(parser)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        payload = AgnesService().get_video_result(
            video_id=args.video_id,
            task_id=args.task_id,
            model_name=args.model_name,
            download=args.download,
            include_raw=args.include_raw,
        )
        emit_json(payload, pretty=args.pretty)
    except Exception as exc:
        emit_error(
            "video_status",
            exc,
            pretty=args.pretty,
            include_traceback=args.traceback,
        )


if __name__ == "__main__":
    main()
