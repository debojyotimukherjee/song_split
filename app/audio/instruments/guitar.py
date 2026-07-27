from __future__ import annotations

from pathlib import Path

from app.audio.instruments.common import FOCUS_STEMS_DIR, run_ffmpeg_filter


def create_guitar_stems(job_dir: Path) -> bool:
    raw_stems_dir = job_dir / "stems_raw"
    guitar_file = raw_stems_dir / "guitar.wav"
    if not guitar_file.exists():
        return False

    stems_dir = job_dir / "stems"
    stems_dir.mkdir(parents=True, exist_ok=True)
    run_ffmpeg_filter(guitar_file, stems_dir / "lead_guitar.wav", _lead_guitar_filter())
    run_ffmpeg_filter(guitar_file, stems_dir / "rhythm_guitar.wav", _rhythm_guitar_filter())

    output_dir = job_dir / FOCUS_STEMS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    run_ffmpeg_filter(guitar_file, output_dir / "lead_guitar.wav", _lead_guitar_focus_filter())
    run_ffmpeg_filter(guitar_file, output_dir / "rhythm_guitar.wav", _rhythm_guitar_focus_filter())
    return True


def _lead_guitar_filter() -> str:
    return ",".join(
        [
            "highpass=f=170",
            "lowpass=f=10500",
            "equalizer=f=450:t=q:w=1.1:g=-2.2",
            "equalizer=f=1600:t=q:w=0.9:g=2.4",
            "equalizer=f=3200:t=q:w=0.8:g=3.2",
            "equalizer=f=6200:t=q:w=0.9:g=1.6",
            "alimiter=limit=0.98",
        ]
    )


def _rhythm_guitar_filter() -> str:
    return ",".join(
        [
            "highpass=f=95",
            "lowpass=f=7800",
            "equalizer=f=220:t=q:w=1.0:g=1.8",
            "equalizer=f=420:t=q:w=1.1:g=1.2",
            "equalizer=f=2500:t=q:w=1.0:g=-1.8",
            "equalizer=f=5200:t=q:w=0.9:g=-1.5",
            "alimiter=limit=0.98",
        ]
    )


def _lead_guitar_focus_filter() -> str:
    return ",".join(
        [
            "highpass=f=220",
            "lowpass=f=11000",
            "equalizer=f=500:t=q:w=1.0:g=-3.0",
            "equalizer=f=1800:t=q:w=0.85:g=3.0",
            "equalizer=f=3600:t=q:w=0.75:g=4.0",
            "equalizer=f=7000:t=q:w=0.85:g=2.0",
            "dynaudnorm=f=140:g=8:p=0.45",
            "alimiter=limit=0.98",
        ]
    )


def _rhythm_guitar_focus_filter() -> str:
    return ",".join(
        [
            "highpass=f=110",
            "lowpass=f=7200",
            "equalizer=f=240:t=q:w=1.0:g=2.2",
            "equalizer=f=480:t=q:w=1.1:g=1.5",
            "equalizer=f=1800:t=q:w=1.1:g=-1.4",
            "equalizer=f=3200:t=q:w=0.9:g=-2.0",
            "dynaudnorm=f=160:g=7:p=0.4",
            "alimiter=limit=0.98",
        ]
    )
