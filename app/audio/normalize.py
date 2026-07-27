from __future__ import annotations

import subprocess
from pathlib import Path


def normalize_to_wav(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-ar",
        "44100",
        "-ac",
        "2",
        str(destination),
    ]
    subprocess.run(command, check=True)

