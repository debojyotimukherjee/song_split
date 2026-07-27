from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.audio.instruments.common import FOCUS_STEMS_DIR, run_ffmpeg_filter
from app.audio.instruments.guitar_separation import GuitarSplitResult, separate_lead_rhythm, write_wav


@dataclass
class LeadGuitarStemInfo:
    name: str
    path: Path
    status: str
    confidence: float
    notes: str


def create_lead_guitar_stem(job_dir: Path, split_result: GuitarSplitResult | None = None) -> LeadGuitarStemInfo | None:
    raw_guitar = job_dir / "stems_raw" / "guitar.wav"
    if not raw_guitar.exists():
        return None

    result = split_result or separate_lead_rhythm(raw_guitar)

    split_dir = job_dir / "working" / "guitar_split"
    lead_raw = split_dir / "lead_raw.wav"
    write_wav(lead_raw, result.lead, result.sample_rate)

    stems_dir = job_dir / "stems"
    focus_dir = job_dir / FOCUS_STEMS_DIR
    stems_dir.mkdir(parents=True, exist_ok=True)
    focus_dir.mkdir(parents=True, exist_ok=True)

    lead_target = stems_dir / "lead_guitar.wav"
    run_ffmpeg_filter(lead_raw, lead_target, _lead_guitar_filter())
    run_ffmpeg_filter(lead_raw, focus_dir / "lead_guitar.wav", _lead_guitar_focus_filter())

    return LeadGuitarStemInfo(
        name="lead_guitar",
        path=lead_target,
        status="estimated",
        confidence=_confidence_for(result),
        notes=f"{result.notes} EQ-shaped by the lead guitar module after separation.",
    )


def _confidence_for(result: GuitarSplitResult) -> float:
    if result.method != "ica":
        return 0.4
    separation_strength = max(0.0, 1.0 - result.channel_correlation)
    return round(min(0.82, 0.5 + separation_strength * 0.4), 2)


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
