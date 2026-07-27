from __future__ import annotations

from pathlib import Path

from app.audio.instruments.common import run_ffmpeg_filter


def create_backing_vocal_estimate(source_file: Path, output_file: Path) -> None:
    backing_filter = ",".join(
        [
            "pan=stereo|c0=0.55*c0-0.35*c1|c1=0.55*c1-0.35*c0",
            "highpass=f=120",
            "lowpass=f=9000",
            "alimiter=limit=0.95",
        ]
    )
    run_ffmpeg_filter(source_file, output_file, backing_filter)

