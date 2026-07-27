from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf


def reduce_spectral_bleed(
    target_path: Path,
    interferer_paths: list[Path],
    output_path: Path,
    strength: float = 1.3,
    floor: float = 0.15,
    n_fft: int = 4096,
    hop_length: int = 1024,
) -> bool:
    """Suppress time/frequency content in `target` that another stem ("interferer")
    dominates. This is what catches cross-instrument bleed (e.g. guitar leaking
    into a piano/keys stem) that a same-stem EQ pass can't fix, since leaked
    energy sits in the same EQ bands as the real instrument.

    For every STFT bin, compares how loud the target is against how loud the
    interferer is at that same moment/frequency, and builds a soft mask from the
    ratio (a Wiener-style mask, the same idea used for noise reduction, but with
    another separated stem standing in for the noise profile instead of a
    silence-based noise print). A floor keeps the mask from fully gating out the
    target, since Demucs' own stems aren't perfectly clean either.

    Returns False (leaving the caller to fall back to a plain copy) if the
    target or every interferer is missing.
    """
    import librosa

    if not target_path.exists():
        return False
    existing_interferers = [path for path in interferer_paths if path.exists()]
    if not existing_interferers:
        return False

    target_audio, sample_rate = sf.read(str(target_path), dtype="float32", always_2d=True)

    interferer_audio: np.ndarray | None = None
    for path in existing_interferers:
        audio, interferer_sr = sf.read(str(path), dtype="float32", always_2d=True)
        if interferer_sr != sample_rate:
            continue
        interferer_audio = audio.astype(np.float64) if interferer_audio is None else _sum_stereo(interferer_audio, audio)

    if interferer_audio is None:
        return False

    channels = target_audio.shape[1]
    cleaned = np.zeros_like(target_audio)
    for channel_index in range(channels):
        interferer_channel = interferer_audio[:, min(channel_index, interferer_audio.shape[1] - 1)]
        cleaned[:, channel_index] = _mask_channel(
            target_audio[:, channel_index],
            interferer_channel,
            strength,
            floor,
            n_fft,
            hop_length,
        )

    peak = float(np.max(np.abs(cleaned)) + 1e-9)
    if peak > 0.98:
        cleaned = cleaned * (0.95 / peak)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), cleaned.astype(np.float32), sample_rate, subtype="PCM_16")
    return True


def _sum_stereo(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    length = max(a.shape[0], b.shape[0])
    channels = max(a.shape[1], b.shape[1])
    out = np.zeros((length, channels), dtype=np.float64)
    out[: a.shape[0], : a.shape[1]] += a
    out[: b.shape[0], : b.shape[1]] += b
    return out


def _mask_channel(
    target: np.ndarray,
    interferer: np.ndarray,
    strength: float,
    floor: float,
    n_fft: int,
    hop_length: int,
) -> np.ndarray:
    import librosa

    length = min(target.size, interferer.size)
    if length == 0:
        return target

    target = target[:length].astype(np.float32)
    interferer = interferer[:length].astype(np.float32)

    target_stft = librosa.stft(target, n_fft=n_fft, hop_length=hop_length)
    interferer_stft = librosa.stft(interferer, n_fft=n_fft, hop_length=hop_length)

    target_mag = np.abs(target_stft)
    interferer_mag = np.abs(interferer_stft)

    denom = target_mag + interferer_mag + 1e-9
    mask = target_mag / denom
    mask = np.power(np.clip(mask, 0.0, 1.0), max(0.1, strength))
    mask = np.clip(mask, floor, 1.0)

    cleaned_stft = target_stft * mask
    cleaned = librosa.istft(cleaned_stft, hop_length=hop_length, length=length)
    return cleaned.astype(np.float32)
