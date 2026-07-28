from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from app.core.manifests import read_manifest


SAMPLE_RATE = 22_050
FRAME_SIZE = 8192
HOP_SIZE = 2048
PITCH_NAMES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
NO_CHORD = "~"
ACCOMPANIMENT_STEMS = (
    ("guitar", 1.15),
    ("keys", 0.95),
    ("other", 0.42),
    ("bass", 0.32),
)

MAJOR_TEMPLATE = np.array([1.0, 0.0, 0.15, 0.0, 0.75, 0.1, 0.0, 0.8, 0.0, 0.15, 0.0, 0.0])
MINOR_TEMPLATE = np.array([1.0, 0.0, 0.15, 0.75, 0.0, 0.1, 0.0, 0.8, 0.0, 0.15, 0.0, 0.0])
DOM7_TEMPLATE = np.array([1.0, 0.0, 0.12, 0.0, 0.72, 0.1, 0.0, 0.78, 0.0, 0.1, 0.5, 0.0])
MIN7_TEMPLATE = np.array([1.0, 0.0, 0.12, 0.72, 0.0, 0.1, 0.0, 0.78, 0.0, 0.1, 0.5, 0.0])
SUS4_TEMPLATE = np.array([1.0, 0.0, 0.12, 0.0, 0.08, 0.68, 0.0, 0.78, 0.0, 0.1, 0.0, 0.0])
SUS2_TEMPLATE = np.array([1.0, 0.0, 0.62, 0.0, 0.08, 0.1, 0.0, 0.78, 0.0, 0.1, 0.0, 0.0])
POWER_TEMPLATE = np.array([1.0, 0.0, 0.08, 0.0, 0.08, 0.08, 0.0, 0.92, 0.0, 0.08, 0.0, 0.0])
EXTENDED_CHORD_TEMPLATES = (
    ("", MAJOR_TEMPLATE),
    ("m", MINOR_TEMPLATE),
    ("7", DOM7_TEMPLATE),
    ("m7", MIN7_TEMPLATE),
    ("sus4", SUS4_TEMPLATE),
    ("sus2", SUS2_TEMPLATE),
    ("5", POWER_TEMPLATE),
)
CHORD_TEMPLATES = (("", MAJOR_TEMPLATE), ("m", MINOR_TEMPLATE))
MAJOR_KEY_PROFILE = np.array([1.0, 0.18, 0.72, 0.18, 0.82, 0.68, 0.22, 0.9, 0.18, 0.76, 0.2, 0.68])
MINOR_KEY_PROFILE = np.array([1.0, 0.18, 0.68, 0.82, 0.18, 0.72, 0.2, 0.88, 0.78, 0.2, 0.68, 0.22])


def analyze_job_chords(job_dir: Path) -> dict[str, Any]:
    manifest = read_manifest(job_dir)
    if not manifest.normalized_path:
        raise ValueError("Job has no normalized WAV to analyze.")

    audio, source = _decode_analysis_audio(job_dir, Path(manifest.normalized_path))
    if audio.size == 0:
        raise ValueError("No audio samples decoded for chord analysis.")

    bass_audio = _decode_optional_stem(job_dir / "stems" / "bass.wav")
    chroma, times, tempo, method = _analyze_harmony_features(audio)
    bass_chroma = _aligned_analysis_chroma(bass_audio, len(times), method) if bass_audio is not None else None
    segments = _estimate_bar_chord_segments(chroma, bass_chroma, times, len(audio) / SAMPLE_RATE, tempo)
    result = {
        "job_id": manifest.job_id,
        "source": source,
        "method": method,
        "sample_rate": SAMPLE_RATE,
        "tempo": tempo,
        "segments": segments,
        "notes": [
            "Stem-aware local chord detection from accompaniment tracks using a dedicated CQT audio-analysis path when available.",
            "Tempo and bar numbers assume a steady 4/4 pulse.",
            "Accuracy is approximate; manual correction support is still a good future feature.",
        ],
    }

    analysis_dir = job_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "chords.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def read_chord_analysis(job_dir: Path) -> dict[str, Any]:
    path = job_dir / "analysis" / "chords.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _decode_audio(path: Path) -> np.ndarray:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-ac",
        "1",
        "-ar",
        str(SAMPLE_RATE),
        "-f",
        "f32le",
        "-",
    ]
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE)
    return np.frombuffer(result.stdout, dtype=np.float32)


def _decode_analysis_audio(job_dir: Path, fallback_path: Path) -> tuple[np.ndarray, str]:
    weighted_stems = []
    for stem_name, weight in ACCOMPANIMENT_STEMS:
        audio = _decode_optional_stem(job_dir / "stems" / f"{stem_name}.wav")
        if audio is None:
            continue
        rms = float(np.sqrt(np.mean(np.square(audio))) + 1e-9)
        weighted_stems.append((stem_name, (audio / rms) * weight))

    if not weighted_stems:
        return _decode_audio(fallback_path), "normalized.wav"

    length = min(audio.size for _, audio in weighted_stems)
    mix = np.zeros(length, dtype=np.float32)
    for _, audio in weighted_stems:
        mix += audio[:length].astype(np.float32)
    peak = float(np.max(np.abs(mix)) + 1e-9)
    source_names = "+".join(stem_name for stem_name, _ in weighted_stems)
    return (mix / peak).astype(np.float32), f"stems:{source_names}"


def _decode_optional_stem(path: Path) -> np.ndarray | None:
    if not path.exists():
        return None
    try:
        audio = _decode_audio(path)
    except subprocess.CalledProcessError:
        return None
    if audio.size == 0:
        return None
    return audio


def _analyze_harmony_features(audio: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, Any], str]:
    try:
        return _librosa_harmony_features(audio)
    except Exception:
        chroma, times = _compute_chroma(audio)
        return chroma, times, _estimate_tempo(audio), "stem-aware-bar-chroma-v3"


def _aligned_analysis_chroma(audio: np.ndarray, frame_count: int, method: str) -> np.ndarray:
    if method.startswith("librosa"):
        try:
            chroma, _ = _librosa_chroma(audio)
        except Exception:
            return _aligned_chroma(audio, frame_count)
    else:
        chroma, _ = _compute_chroma(audio)
    return _fit_chroma_length(chroma, frame_count)


def _librosa_harmony_features(audio: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, Any], str]:
    import librosa

    mono = np.asarray(audio, dtype=np.float32)
    harmonic = librosa.effects.harmonic(mono, margin=8)
    chroma, times = _librosa_chroma(harmonic)
    tempo = _estimate_tempo(mono)
    return chroma, times, tempo, "librosa-cqt-chords-v1"


def _librosa_chroma(audio: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    import librosa

    chroma = librosa.feature.chroma_cqt(
        y=np.asarray(audio, dtype=np.float32),
        sr=SAMPLE_RATE,
        hop_length=HOP_SIZE,
        bins_per_octave=36,
        n_chroma=12,
        threshold=0.08,
    )
    chroma = np.asarray(chroma.T, dtype=np.float64)
    chroma = np.power(np.maximum(chroma, 0.0), 0.72)
    norms = np.linalg.norm(chroma, axis=1, keepdims=True)
    chroma = np.divide(chroma, norms, out=np.zeros_like(chroma), where=norms > 0)
    times = librosa.frames_to_time(np.arange(chroma.shape[0]), sr=SAMPLE_RATE, hop_length=HOP_SIZE)
    return chroma, times


def _librosa_tempo(audio: np.ndarray) -> dict[str, Any]:
    import librosa

    onset = librosa.onset.onset_strength(y=np.asarray(audio, dtype=np.float32), sr=SAMPLE_RATE, hop_length=HOP_SIZE)
    tempo = librosa.feature.tempo(onset_envelope=onset, sr=SAMPLE_RATE, hop_length=HOP_SIZE)
    bpm = float(np.ravel(tempo)[0]) if np.size(tempo) else 120.0
    return _tempo_result(bpm, 0.85)


def _fit_chroma_length(chroma: np.ndarray, frame_count: int) -> np.ndarray:
    if chroma.shape[0] == frame_count:
        return chroma
    if chroma.shape[0] > frame_count:
        return chroma[:frame_count]
    padding = np.repeat(chroma[-1:, :], frame_count - chroma.shape[0], axis=0)
    return np.vstack([chroma, padding])


def _compute_chroma(audio: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if audio.size < FRAME_SIZE:
        audio = np.pad(audio, (0, FRAME_SIZE - audio.size))

    window = np.hanning(FRAME_SIZE).astype(np.float32)
    freqs = np.fft.rfftfreq(FRAME_SIZE, d=1 / SAMPLE_RATE)
    pitch_bins = _pitch_class_bins(freqs)
    usable = pitch_bins >= 0
    weights = _frequency_weights(freqs)
    frames = []
    times = []

    for start in range(0, audio.size - FRAME_SIZE + 1, HOP_SIZE):
        frame = audio[start : start + FRAME_SIZE] * window
        spectrum = np.log1p(np.abs(np.fft.rfft(frame)) * 12.0) * weights
        chroma = np.zeros(12, dtype=np.float64)
        np.add.at(chroma, pitch_bins[usable], spectrum[usable])
        chroma = _reduce_overtone_bias(chroma)
        norm = np.linalg.norm(chroma)
        if norm > 0:
            chroma = chroma / norm
        frames.append(chroma)
        times.append(start / SAMPLE_RATE)

    return np.vstack(frames), np.array(times)


def _aligned_chroma(audio: np.ndarray, frame_count: int) -> np.ndarray:
    chroma, _ = _compute_chroma(audio)
    return _fit_chroma_length(chroma, frame_count)


def _estimate_tempo(audio: np.ndarray) -> dict[str, Any]:
    frame_size = 1024
    hop_size = 512
    if audio.size < frame_size * 4:
        return _tempo_result(120.0, 0.0)

    mono = np.asarray(audio, dtype=np.float32)
    frames = []
    previous = np.zeros(frame_size // 2 + 1, dtype=np.float64)
    window = np.hanning(frame_size).astype(np.float32)

    for start in range(0, mono.size - frame_size + 1, hop_size):
        spectrum = np.abs(np.fft.rfft(mono[start : start + frame_size] * window))
        flux = float(np.maximum(spectrum - previous, 0).sum())
        frames.append(flux)
        previous = spectrum

    envelope = np.asarray(frames, dtype=np.float64)
    if envelope.size < 16 or float(envelope.max()) <= 0:
        return _tempo_result(120.0, 0.0)

    envelope = envelope - envelope.mean()
    envelope = envelope / (envelope.std() + 1e-9)
    autocorr = np.correlate(envelope, envelope, mode="full")[envelope.size - 1 :]
    autocorr[0] = 0

    min_bpm = 70
    max_bpm = 180
    min_lag = max(1, round((60 * SAMPLE_RATE) / (max_bpm * hop_size)))
    max_lag = min(autocorr.size - 1, round((60 * SAMPLE_RATE) / (min_bpm * hop_size)))
    if max_lag <= min_lag:
        return _tempo_result(120.0, 0.0)

    lag_window = autocorr[min_lag : max_lag + 1]
    lag = int(np.argmax(lag_window) + min_lag)
    bpm = (60 * SAMPLE_RATE) / (lag * hop_size)
    confidence = float(np.clip(autocorr[lag] / (np.max(lag_window) + 1e-9), 0.0, 1.0))
    return _tempo_result(bpm, confidence)


def _tempo_result(bpm: float, confidence: float) -> dict[str, Any]:
    normalized_bpm = float(bpm)
    while normalized_bpm < 100:
        normalized_bpm *= 2
    while normalized_bpm > 190:
        normalized_bpm /= 2
    rounded_bpm = round(normalized_bpm, 1)
    beats_per_bar = 4
    return {
        "bpm": rounded_bpm,
        "confidence": round(float(confidence), 3),
        "time_signature": "4/4",
        "beats_per_bar": beats_per_bar,
        "seconds_per_bar": round((60 / rounded_bpm) * beats_per_bar, 3),
    }


def _pitch_class_bins(freqs: np.ndarray) -> np.ndarray:
    bins = np.full(freqs.shape, -1, dtype=np.int16)
    mask = (freqs >= 70.0) & (freqs <= 1450.0)
    midi = np.rint(69 + 12 * np.log2(freqs[mask] / 440.0)).astype(np.int16)
    bins[mask] = midi % 12
    return bins


def _frequency_weights(freqs: np.ndarray) -> np.ndarray:
    weights = np.zeros(freqs.shape, dtype=np.float64)
    mask = (freqs >= 70.0) & (freqs <= 1450.0)
    weights[mask] = 1.0
    weights *= np.where(freqs > 900.0, 0.55, 1.0)
    weights *= np.where(freqs < 95.0, 0.65, 1.0)
    return weights


def _reduce_overtone_bias(chroma: np.ndarray) -> np.ndarray:
    cleaned = chroma.astype(np.float64).copy()
    for pitch_class in range(12):
        overtone_leak = (
            0.18 * chroma[(pitch_class + 7) % 12]
            + 0.12 * chroma[(pitch_class + 4) % 12]
            + 0.08 * chroma[(pitch_class + 10) % 12]
        )
        cleaned[pitch_class] = max(0.0, cleaned[pitch_class] - overtone_leak)
    return cleaned


def _estimate_bar_chord_segments(
    chroma: np.ndarray,
    bass_chroma: np.ndarray | None,
    times: np.ndarray,
    duration: float,
    tempo: dict[str, Any],
) -> list[dict[str, Any]]:
    seconds_per_bar = float(tempo.get("seconds_per_bar") or 2.0)
    bar_count = max(1, math.ceil(duration / seconds_per_bar))
    raw_segments = []

    for bar_index in range(bar_count):
        start = bar_index * seconds_per_bar
        end = min(duration, (bar_index + 1) * seconds_per_bar)
        frame_mask = (times >= start) & (times < end)
        if not np.any(frame_mask):
            frame_mask[np.argmin(np.abs(times - start))] = True
        segment_chroma = chroma[frame_mask].mean(axis=0)
        segment_bass = bass_chroma[frame_mask].mean(axis=0) if bass_chroma is not None else None
        chord, confidence, scores = _match_chord(segment_chroma, segment_bass)
        chord = _with_bass_note(chord, segment_bass)
        raw_segments.append(
            {
                "start": round(start, 3),
                "end": round(end, 3),
                "chord": chord,
                "confidence": round(confidence, 3),
                "_scores": scores,
            }
        )

    key_context = _estimate_key_context(raw_segments)
    smoothed = _smooth_bar_segments(raw_segments, key_context)
    for segment in smoothed:
        segment.pop("_scores", None)
    return _merge_segments(smoothed, duration)


def _match_chord(chroma: np.ndarray, bass_chroma: np.ndarray | None = None) -> tuple[str, float, dict[str, float]]:
    if float(np.sum(chroma)) < 0.01:
        return NO_CHORD, 0.0, {}

    best_name = NO_CHORD
    best_score = -math.inf
    runner_up = -math.inf
    scores: dict[str, float] = {}
    for root in range(12):
        for suffix, template in CHORD_TEMPLATES:
            shifted = np.roll(template, root)
            shifted = shifted / np.linalg.norm(shifted)
            score = float(np.dot(chroma, shifted))
            if bass_chroma is not None:
                score += 0.13 * float(bass_chroma[root])
                score += 0.04 * float(bass_chroma[(root + 7) % 12])
            if suffix in {"5", "sus2", "sus4"}:
                score -= 0.025
            name = f"{PITCH_NAMES[root]}{suffix}"
            scores[name] = score
            if score > best_score:
                runner_up = best_score
                best_score = score
                best_name = name
            elif score > runner_up:
                runner_up = score

    confidence = max(0.0, min(1.0, best_score - max(0.0, runner_up) + 0.45))
    best_name = _resolve_ambiguous_third(best_name, scores, confidence)
    return best_name, confidence, scores


def _resolve_ambiguous_third(chord: str, scores: dict[str, float], confidence: float) -> str:
    if confidence > 0.55 or not chord.endswith("m"):
        return chord
    major_chord = chord[:-1]
    if confidence < 0.52:
        return major_chord
    minor_score = scores.get(chord)
    major_score = scores.get(major_chord)
    if minor_score is None or major_score is None:
        return chord
    if major_score >= minor_score - 0.055:
        return major_chord
    return chord


def _with_bass_note(chord: str, bass_chroma: np.ndarray | None) -> str:
    if bass_chroma is None or chord == NO_CHORD or "/" in chord:
        return chord
    root = _chord_root(chord)
    if root is None:
        return chord
    bass_root = int(np.argmax(bass_chroma))
    interval = (bass_root - root) % 12
    if interval not in {3, 4, 7, 9, 10, 11}:
        return chord
    bass_strength = float(bass_chroma[bass_root])
    root_strength = float(bass_chroma[root])
    if bass_root != root and bass_strength > 0.3 and bass_strength >= root_strength * 1.2:
        return f"{chord}/{PITCH_NAMES[bass_root]}"
    return chord


def _estimate_key_context(segments: list[dict[str, Any]]) -> dict[str, Any]:
    key_chroma = np.zeros(12, dtype=np.float64)
    for segment in segments:
        for chord, score in segment.get("_scores", {}).items():
            root = _chord_root(chord)
            if root is not None:
                key_chroma[root] += max(0.0, score)
    norm = np.linalg.norm(key_chroma)
    if norm > 0:
        key_chroma = key_chroma / norm

    best_root = 0
    best_mode = "major"
    best_score = -math.inf
    for root in range(12):
        major_score = float(np.dot(key_chroma, np.roll(MAJOR_KEY_PROFILE, root)))
        minor_score = float(np.dot(key_chroma, np.roll(MINOR_KEY_PROFILE, root)))
        if major_score > best_score:
            best_root = root
            best_mode = "major"
            best_score = major_score
        if minor_score > best_score:
            best_root = root
            best_mode = "minor"
            best_score = minor_score
    return {"root": best_root, "mode": best_mode}


def _smooth_bar_segments(segments: list[dict[str, Any]], key_context: dict[str, Any]) -> list[dict[str, Any]]:
    smoothed = [dict(segment) for segment in segments]

    for segment in smoothed:
        current_chord = segment["chord"]
        diatonic = _best_diatonic_alternative(segment.get("_scores", {}), key_context)
        if (
            diatonic
            and diatonic != current_chord
            and segment["confidence"] < 0.49
            and not _is_diatonic_chord(current_chord, key_context)
            and segment.get("_scores", {}).get(diatonic, -math.inf)
            >= segment.get("_scores", {}).get(current_chord, -math.inf) - 0.018
        ):
            segment["chord"] = diatonic
            segment["confidence"] = round(max(segment["confidence"], 0.52), 3)

    for index in range(1, len(smoothed) - 1):
        previous_chord = smoothed[index - 1]["chord"]
        current = smoothed[index]
        next_chord = smoothed[index + 1]["chord"]
        if previous_chord == next_chord and current["chord"] != previous_chord and current["confidence"] < 0.58:
            current["chord"] = previous_chord
            current["confidence"] = round((current["confidence"] + smoothed[index - 1]["confidence"]) / 2, 3)

    for index in range(1, len(smoothed)):
        previous = smoothed[index - 1]
        current = smoothed[index]
        previous_score = current.get("_scores", {}).get(previous["chord"])
        current_score = current.get("_scores", {}).get(current["chord"])
        if previous_score is None or current_score is None:
            continue
        if current["chord"] != previous["chord"] and current["confidence"] < 0.53 and previous_score >= current_score - 0.04:
            current["chord"] = previous["chord"]
            current["confidence"] = round(max(current["confidence"], previous["confidence"] * 0.92), 3)

    return smoothed


def _best_diatonic_alternative(scores: dict[str, float], key_context: dict[str, Any]) -> str | None:
    root = int(key_context.get("root", 0))
    mode = key_context.get("mode", "major")
    if mode == "minor":
        degrees = {0: "m", 2: "", 3: "", 5: "m", 7: "m", 8: "", 10: ""}
    else:
        degrees = {0: "", 2: "m", 4: "m", 5: "", 7: "", 9: "m", 11: "m"}
    candidates = []
    for interval, suffix in degrees.items():
        chord_root = (root + interval) % 12
        candidates.append(f"{PITCH_NAMES[chord_root]}{suffix}")
    present = [(name, scores[name]) for name in candidates if name in scores]
    if not present:
        return None
    return max(present, key=lambda item: item[1])[0]


def _is_diatonic_chord(chord: str, key_context: dict[str, Any]) -> bool:
    root = _chord_root(chord)
    if root is None:
        return False
    key_root = int(key_context.get("root", 0))
    mode = key_context.get("mode", "major")
    major_roots = {0, 2, 4, 5, 7, 9, 11}
    minor_roots = {0, 2, 3, 5, 7, 8, 10}
    return ((root - key_root) % 12) in (minor_roots if mode == "minor" else major_roots)


def _chord_root(chord: str) -> int | None:
    for index, name in sorted(enumerate(PITCH_NAMES), key=lambda item: len(item[1]), reverse=True):
        if chord.startswith(name):
            return index
    return None


def _merge_segments(segments: list[dict[str, Any]], duration: float) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for segment in segments:
        if merged and merged[-1]["chord"] == segment["chord"]:
            merged[-1]["end"] = segment["end"]
            merged[-1]["confidence"] = round(
                (merged[-1]["confidence"] + segment["confidence"]) / 2,
                3,
            )
        else:
            merged.append(segment)

    if merged:
        merged[-1]["end"] = round(duration, 3)
    return merged
