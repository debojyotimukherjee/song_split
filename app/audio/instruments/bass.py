from __future__ import annotations

from pathlib import Path

from app.audio.instruments.common import run_ffmpeg_filter


def create_bass_stem(source_file: Path, output_file: Path) -> None:
    bass_filter = ",".join(
        [
            "highpass=f=35",
            "lowpass=f=4200",
            "equalizer=f=220:t=q:w=1.2:g=-4",
            "equalizer=f=320:t=q:w=1.0:g=-2.5",
            "alimiter=limit=0.98",
        ]
    )
    run_ffmpeg_filter(source_file, output_file, bass_filter)

