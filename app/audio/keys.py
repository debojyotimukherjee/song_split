from __future__ import annotations

import subprocess
from pathlib import Path


FOCUS_STEMS_DIR = "stems_focus"
REBUILD_STEMS_DIR = "stems_rebuild"


def create_keys_focus_stem(job_dir: Path) -> bool:
    raw_stems_dir = job_dir / "stems_raw"
    piano_file = raw_stems_dir / "piano.wav"
    if not piano_file.exists():
        return False

    output_dir = job_dir / FOCUS_STEMS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    keys_filter = ",".join(
        [
            "highpass=f=130",
            "lowpass=f=11500",
            "equalizer=f=220:t=q:w=1.0:g=-3.5",
            "equalizer=f=360:t=q:w=1.1:g=-5.0",
            "equalizer=f=720:t=q:w=1.2:g=-2.0",
            "equalizer=f=1900:t=q:w=0.9:g=2.4",
            "equalizer=f=3400:t=q:w=0.8:g=3.4",
            "equalizer=f=6800:t=q:w=0.8:g=2.2",
            "dynaudnorm=f=150:g=9:p=0.55",
            "alimiter=limit=0.98",
        ]
    )
    _run_ffmpeg_filter(piano_file, output_dir / "keys.wav", keys_filter)
    return True


def create_keys_rebuild_stem(job_dir: Path) -> bool:
    raw_stems_dir = job_dir / "stems_raw"
    piano_file = raw_stems_dir / "piano.wav"
    other_file = raw_stems_dir / "other.wav"
    if not piano_file.exists():
        return False

    output_dir = job_dir / REBUILD_STEMS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "keys.wav"

    if not other_file.exists():
        _run_ffmpeg_filter(piano_file, output_file, _keys_rebuild_single_filter())
        return True

    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(piano_file),
        "-i",
        str(other_file),
        "-filter_complex",
        _keys_rebuild_mix_filter(),
        "-map",
        "[out]",
        str(output_file),
    ]
    subprocess.run(command, check=True)
    return True


def _keys_rebuild_single_filter() -> str:
    return ",".join(
        [
            "highpass=f=150",
            "lowpass=f=10500",
            "equalizer=f=260:t=q:w=1.0:g=-4.5",
            "equalizer=f=430:t=q:w=1.0:g=-5.5",
            "equalizer=f=850:t=q:w=1.2:g=-2.0",
            "equalizer=f=2100:t=q:w=0.9:g=2.8",
            "equalizer=f=3600:t=q:w=0.75:g=4.0",
            "equalizer=f=7200:t=q:w=0.8:g=2.4",
            "dynaudnorm=f=120:g=11:p=0.62",
            "alimiter=limit=0.98",
        ]
    )


def _keys_rebuild_mix_filter() -> str:
    piano_chain = ",".join(
        [
            "highpass=f=150",
            "lowpass=f=10500",
            "equalizer=f=260:t=q:w=1.0:g=-4.5",
            "equalizer=f=430:t=q:w=1.0:g=-5.5",
            "equalizer=f=850:t=q:w=1.2:g=-2.0",
            "equalizer=f=2100:t=q:w=0.9:g=2.8",
            "equalizer=f=3600:t=q:w=0.75:g=4.0",
            "equalizer=f=7200:t=q:w=0.8:g=2.4",
            "volume=0.9",
        ]
    )
    harmonic_other_chain = ",".join(
        [
            "highpass=f=210",
            "lowpass=f=9000",
            "equalizer=f=280:t=q:w=1.0:g=-8.0",
            "equalizer=f=520:t=q:w=1.0:g=-5.0",
            "equalizer=f=1200:t=q:w=0.9:g=1.4",
            "equalizer=f=2600:t=q:w=0.8:g=3.2",
            "equalizer=f=5200:t=q:w=0.8:g=2.6",
            "afftdn=nf=-28",
            "volume=0.36",
        ]
    )
    return (
        f"[0:a]{piano_chain}[piano];"
        f"[1:a]{harmonic_other_chain}[otherkeys];"
        "[piano][otherkeys]amix=inputs=2:duration=first:normalize=0,"
        "dynaudnorm=f=120:g=10:p=0.58,"
        "alimiter=limit=0.98[out]"
    )


def _run_ffmpeg_filter(source_file: Path, output_file: Path, audio_filter: str) -> None:
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
