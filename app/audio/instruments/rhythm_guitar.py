from __future__ import annotations

from pathlib import Path

from app.audio.instruments.common import FOCUS_STEMS_DIR, run_ffmpeg_filter


def create_rhythm_guitar_stem(job_dir: Path) -> bool:
    raw_guitar = job_dir / "stems_raw" / "guitar.wav"
    if not raw_guitar.exists():
        return False

    stems_dir = job_dir / "stems"
    stems_dir.mkdir(parents=True, exist_ok=True)
    run_ffmpeg_filter(raw_guitar, stems_dir / "rhythm_guitar.wav", _rhythm_guitar_filter())

    focus_dir = job_dir / FOCUS_STEMS_DIR
    focus_dir.mkdir(parents=True, exist_ok=True)
    run_ffmpeg_filter(raw_guitar, focus_dir / "rhythm_guitar.wav", _rhythm_guitar_focus_filter())
    return True


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
