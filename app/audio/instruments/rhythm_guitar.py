from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.audio.instruments.common import FOCUS_STEMS_DIR, run_ffmpeg_filter
from app.audio.instruments.guitar_separation import GuitarSplitResult, separate_lead_rhythm, write_wav


@dataclass
class RhythmGuitarStemInfo:
    name: str
    path: Path
    status: str
    confidence: float
    notes: str


def create_rhythm_guitar_stem(
    job_dir: Path, split_result: GuitarSplitResult | None = None
) -> RhythmGuitarStemInfo | None:
    raw_guitar = job_dir / "stems_raw" / "guitar.wav"
    if not raw_guitar.exists():
        return None

    result = split_result or separate_lead_rhythm(raw_guitar)

    split_dir = job_dir / "working" / "guitar_split"
    rhythm_raw = split_dir / "rhythm_raw.wav"
    write_wav(rhythm_raw, result.rhythm, result.sample_rate)

    stems_dir = job_dir / "stems"
    focus_dir = job_dir / FOCUS_STEMS_DIR
    stems_dir.mkdir(parents=True, exist_ok=True)
    focus_dir.mkdir(parents=True, exist_ok=True)

    rhythm_target = stems_dir / "rhythm_guitar.wav"
    run_ffmpeg_filter(rhythm_raw, rhythm_target, _rhythm_guitar_filter())
    run_ffmpeg_filter(rhythm_raw, focus_dir / "rhythm_guitar.wav", _rhythm_guitar_focus_filter())

    return RhythmGuitarStemInfo(
        name="rhythm_guitar",
        path=rhythm_target,
        status="estimated",
        confidence=_confidence_for(result),
        notes=f"{result.notes} EQ-shaped by the rhythm guitar module after separation.",
    )


def _confidence_for(result: GuitarSplitResult) -> float:
    if result.method != "ica":
        return 0.4
    separation_strength = max(0.0, 1.0 - result.channel_correlation)
    return round(min(0.82, 0.5 + separation_strength * 0.4), 2)


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
