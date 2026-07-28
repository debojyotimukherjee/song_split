from __future__ import annotations

import subprocess
from pathlib import Path


def create_acoustic_guitar_stem(guitar_file: Path, other_file: Path | None, output_file: Path) -> None:
    """Build a practice-focused acoustic guitar lane.

    Demucs can place acoustic strumming in either the guitar stem or the catch-all
    other stem. This blend keeps the dependable raw guitar source, then lightly
    folds in harmonic/string content from other when it exists.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if other_file and other_file.exists():
        command = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(guitar_file),
            "-i",
            str(other_file),
            "-filter_complex",
            (
                "[0:a]highpass=f=65,lowpass=f=14500,"
                "equalizer=f=180:t=q:w=0.9:g=1.1,"
                "equalizer=f=750:t=q:w=1.0:g=1.4,"
                "equalizer=f=2800:t=q:w=0.8:g=2.4,"
                "equalizer=f=7200:t=q:w=0.8:g=1.7,"
                "volume=0.92[g];"
                "[1:a]highpass=f=120,lowpass=f=12500,"
                "equalizer=f=700:t=q:w=1.0:g=1.0,"
                "equalizer=f=3400:t=q:w=0.9:g=2.2,"
                "volume=0.38[o];"
                "[g][o]amix=inputs=2:duration=first:normalize=0,"
                "alimiter=limit=0.98[out]"
            ),
            "-map",
            "[out]",
            str(output_file),
        ]
    else:
        command = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(guitar_file),
            "-af",
            (
                "highpass=f=65,lowpass=f=14500,"
                "equalizer=f=180:t=q:w=0.9:g=1.1,"
                "equalizer=f=750:t=q:w=1.0:g=1.4,"
                "equalizer=f=2800:t=q:w=0.8:g=2.4,"
                "equalizer=f=7200:t=q:w=0.8:g=1.7,"
                "alimiter=limit=0.98"
            ),
            str(output_file),
        ]
    subprocess.run(command, check=True)
