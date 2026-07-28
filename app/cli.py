from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from app.audio.pipeline import enhance_existing_job_audio_separator, process_file, remap_existing_job
from app.audio.chords import analyze_job_chords
from app.core.config import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="weekend-stems")
    subparsers = parser.add_subparsers(dest="command", required=True)

    separate = subparsers.add_parser("separate", help="Create a job from an audio file.")
    separate.add_argument("input_file", help="Path to an MP3/WAV/FLAC/M4A file.")
    separate.add_argument(
        "--engine",
        choices=["none", "demucs"],
        default="none",
        help="Separation engine to run after normalization.",
    )
    separate.add_argument(
        "--job-id",
        help="Optional deterministic job id. Defaults to a slug plus timestamp.",
    )

    remap = subparsers.add_parser(
        "remap",
        help="Rebuild product stems from an existing Demucs job output.",
    )
    remap.add_argument("job_dir", help="Path to an existing job folder.")

    chords = subparsers.add_parser(
        "analyze-chords",
        help="Detect timestamped chords for an existing job.",
    )
    chords.add_argument("job_dir", help="Path to an existing job folder.")

    enhance = subparsers.add_parser(
        "enhance-audio-separator",
        help="Run the audio-separator specialist pass for an existing job.",
    )
    enhance.add_argument("job_dir", help="Path to an existing job folder.")

    list_uvr = subparsers.add_parser(
        "list-audio-separator-models",
        help="List available audio-separator models.",
    )
    list_uvr.add_argument("--filter", default=None, help="Optional stem/model filter, e.g. guitar or piano.")
    list_uvr.add_argument("--limit", default="10", help="Maximum number of models to show.")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = Settings.from_env()

    if args.command == "separate":
        manifest = process_file(
            input_file=Path(args.input_file),
            settings=settings,
            engine=args.engine,
            requested_job_id=args.job_id,
        )
        print(json.dumps(manifest.model_dump(mode="json"), indent=2))
    elif args.command == "remap":
        manifest = remap_existing_job(Path(args.job_dir), settings=settings)
        print(json.dumps(manifest.model_dump(mode="json"), indent=2))
    elif args.command == "analyze-chords":
        result = analyze_job_chords(Path(args.job_dir))
        print(json.dumps(result, indent=2))
    elif args.command == "enhance-audio-separator":
        manifest = enhance_existing_job_audio_separator(Path(args.job_dir), settings=settings)
        print(json.dumps(manifest.model_dump(mode="json"), indent=2))
    elif args.command == "list-audio-separator-models":
        command = ["audio-separator", "--list_models", "--list_limit", args.limit]
        if args.filter:
            command.extend(["--list_filter", args.filter])
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
