from __future__ import annotations

import subprocess
from pathlib import Path


FOCUS_STEMS_DIR = "stems_focus"
REBUILD_STEMS_DIR = "stems_rebuild"


def run_ffmpeg_filter(source_file: Path, output_file: Path, audio_filter: str) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source_file),
        "-af",
        audio_filter,
        str(output_file),
    ]
    subprocess.run(command, check=True)


def run_ffmpeg_mix(source_files: list[Path], output_file: Path, weights: list[float]) -> None:
    command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for source_file in source_files:
        command.extend(["-i", str(source_file)])

    labels = []
    filters = []
    for index, weight in enumerate(weights):
        label = f"a{index}"
        labels.append(f"[{label}]")
        filters.append(f"[{index}:a]volume={weight}[{label}]")

    filter_complex = ";".join(filters)
    filter_complex += (
        f";{''.join(labels)}amix=inputs={len(source_files)}:duration=first:normalize=0,"
        "alimiter=limit=0.98[out]"
    )
    command.extend(["-filter_complex", filter_complex, "-map", "[out]", str(output_file)])
    subprocess.run(command, check=True)

