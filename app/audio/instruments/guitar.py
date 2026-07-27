from __future__ import annotations

from pathlib import Path

from app.audio.instruments.common import FOCUS_STEMS_DIR, run_ffmpeg_mix


def create_guitar_focus_stem(job_dir: Path) -> bool:
    raw_stems_dir = job_dir / "stems_raw"
    guitar_file = raw_stems_dir / "guitar.wav"
    if not guitar_file.exists():
        return False

    source_files = [guitar_file]
    weights = [1.0]
    other_file = raw_stems_dir / "other.wav"
    piano_file = raw_stems_dir / "piano.wav"
    if other_file.exists():
        source_files.append(other_file)
        weights.append(0.42)
    if piano_file.exists():
        source_files.append(piano_file)
        weights.append(0.18)

    output_dir = job_dir / FOCUS_STEMS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    run_ffmpeg_mix(source_files, output_dir / "guitar.wav", weights)
    return True

