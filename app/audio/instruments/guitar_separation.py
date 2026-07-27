from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf


CORRELATION_FALLBACK_THRESHOLD = 0.985


@dataclass
class GuitarSplitResult:
    lead: np.ndarray
    rhythm: np.ndarray
    sample_rate: int
    method: str  # "ica" or "eq-duplicate"
    channel_correlation: float
    notes: str


def separate_lead_rhythm(raw_guitar_path: Path) -> GuitarSplitResult:
    """Split a stereo Demucs 'guitar' stem into lead/rhythm parts.

    No pretrained model splits lead vs rhythm guitar (it's a musical role, not a
    timbre class), so this uses stereo FastICA blind-source separation instead:
    if the two guitars are mixed with different pan/level, they form a linear
    instantaneous mixture that ICA can invert. If the channels are too similar
    to separate (e.g. a single hard-panned guitar, or a mono source), this falls
    back to returning the same audio twice, same as before.
    """
    audio, sample_rate = sf.read(str(raw_guitar_path), dtype="float32", always_2d=True)

    if audio.shape[1] < 2:
        return _fallback(
            audio,
            sample_rate,
            "Guitar stem is mono, so there is no stereo pan difference for blind-source separation to use.",
        )

    left, right = audio[:, 0], audio[:, 1]
    correlation = _channel_correlation(left, right)

    if correlation > CORRELATION_FALLBACK_THRESHOLD:
        return _fallback(
            audio,
            sample_rate,
            f"Left/right channels are {correlation:.3f} correlated (essentially the same pan position), "
            "so there isn't enough stereo difference for blind-source separation to isolate two guitars.",
        )

    try:
        lead_signal, rhythm_signal = _ica_split(left, right, sample_rate)
    except Exception as exc:  # defensive: never let a bad take crash the whole job
        return _fallback(
            audio,
            sample_rate,
            f"FastICA separation failed ({exc}); falling back to EQ-based duplication.",
        )

    return GuitarSplitResult(
        lead=_normalize_peak(lead_signal),
        rhythm=_normalize_peak(rhythm_signal),
        sample_rate=sample_rate,
        method="ica",
        channel_correlation=correlation,
        notes=(
            "Separated with stereo FastICA blind-source separation on the Demucs guitar stem, using the "
            "left/right mix-position difference between the two guitar parts. Lead/rhythm labels were "
            "assigned from onset density and percussive-energy ratio, not a trained classifier, so the "
            "labeling can occasionally be swapped."
        ),
    )


def _fallback(audio: np.ndarray, sample_rate: int, reason: str) -> GuitarSplitResult:
    stereo = audio if audio.shape[1] >= 2 else np.repeat(audio, 2, axis=1)
    return GuitarSplitResult(
        lead=stereo.copy(),
        rhythm=stereo.copy(),
        sample_rate=sample_rate,
        method="eq-duplicate",
        channel_correlation=1.0,
        notes=f"{reason} Both tracks come from the same guitar audio, distinguished only by EQ shaping.",
    )


def _channel_correlation(left: np.ndarray, right: np.ndarray) -> float:
    length = min(left.size, right.size)
    if length == 0:
        return 1.0
    left_centered = left[:length] - left[:length].mean()
    right_centered = right[:length] - right[:length].mean()
    denom = np.sqrt(np.sum(left_centered**2) * np.sum(right_centered**2))
    if denom < 1e-9:
        return 1.0
    return float(np.clip(np.sum(left_centered * right_centered) / denom, -1.0, 1.0))


def _ica_split(left: np.ndarray, right: np.ndarray, sample_rate: int) -> tuple[np.ndarray, np.ndarray]:
    from sklearn.decomposition import FastICA

    length = min(left.size, right.size)
    mixed = np.column_stack([left[:length], right[:length]]).astype(np.float64)

    ica = FastICA(n_components=2, whiten="unit-variance", max_iter=500, random_state=0)
    sources = ica.fit_transform(mixed)

    score_a = _rhythm_score(sources[:, 0], sample_rate)
    score_b = _rhythm_score(sources[:, 1], sample_rate)
    rhythm_idx = 0 if score_a >= score_b else 1
    lead_idx = 1 - rhythm_idx

    lead_only = sources.copy()
    lead_only[:, rhythm_idx] = 0.0
    rhythm_only = sources.copy()
    rhythm_only[:, lead_idx] = 0.0

    # inverse_transform projects the isolated component back through the estimated
    # mixing matrix (and undoes ICA's centering), so each output keeps that source's
    # original stereo pan position instead of collapsing to mono.
    lead_signal = ica.inverse_transform(lead_only).astype(np.float32)
    rhythm_signal = ica.inverse_transform(rhythm_only).astype(np.float32)
    return lead_signal, rhythm_signal


def _rhythm_score(signal: np.ndarray, sample_rate: int) -> float:
    """Higher score => more likely the strummed/rhythm part (dense onsets, percussive energy)."""
    try:
        import librosa

        mono = signal.astype(np.float32)
        onset_env = librosa.onset.onset_strength(y=mono, sr=sample_rate)
        onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sample_rate)
        duration = max(1.0, mono.size / sample_rate)
        onset_rate = len(onsets) / duration

        harmonic, percussive = librosa.effects.hpss(mono, margin=(1.0, 3.0))
        harmonic_energy = float(np.sum(harmonic**2))
        percussive_energy = float(np.sum(percussive**2))
        percussive_ratio = percussive_energy / max(1e-9, harmonic_energy + percussive_energy)
        return onset_rate / 6.0 + percussive_ratio
    except Exception:
        return _crude_transient_density(signal)


def _crude_transient_density(signal: np.ndarray, frame: int = 2048) -> float:
    if signal.size < frame * 2:
        return 0.0
    usable = signal[: (signal.size // frame) * frame].reshape(-1, frame)
    rms = np.sqrt(np.mean(usable**2, axis=1))
    diffs = np.diff(rms)
    return float(np.mean(np.maximum(diffs, 0.0)))


def _normalize_peak(stereo: np.ndarray, target: float = 0.95) -> np.ndarray:
    peak = float(np.max(np.abs(stereo)) + 1e-9)
    if peak <= target:
        return stereo.astype(np.float32)
    return (stereo * (target / peak)).astype(np.float32)


def write_wav(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), np.clip(audio, -1.0, 1.0), sample_rate, subtype="PCM_16")
