from __future__ import annotations

from pathlib import Path

from app.audio.instruments.common import run_ffmpeg_filter


def create_guitar_stem(source_file: Path, output_file: Path) -> None:
    """Clean up the raw Demucs guitar stem: trim rumble/hiss and add a touch of
    presence. This is a single, reliably-generated track (no lead/rhythm split) --
    splitting one guitar stem into "lead" and "rhythm" turned out to only work
    when the two parts happen to be panned differently in the mix, and silently
    fell back to duplicating the same audio otherwise. For a rehearsal reference
    track, one dependable Guitar stem beats two that might secretly be identical.
    """
    guitar_filter = ",".join(
        [
            "highpass=f=90",
            "lowpass=f=11000",
            "equalizer=f=250:t=q:w=1.1:g=-1.6",
            "equalizer=f=500:t=q:w=1.0:g=-1.2",
            "equalizer=f=2200:t=q:w=0.9:g=1.6",
            "equalizer=f=4200:t=q:w=0.8:g=1.8",
            "alimiter=limit=0.98",
        ]
    )
    run_ffmpeg_filter(source_file, output_file, guitar_filter)
