from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from app.core.manifests import read_manifest


SAMPLE_RATE = 22_050
HOP_SIZE = 2048
NO_CHORD = "~"
PITCH_NAMES_SHARP = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
PITCH_NAMES_FLAT = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
NOTE_TO_PC = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}
SLASH_INTERVALS = {
    "3": 4,
    "b3": 3,
    "5": 7,
    "b5": 6,
    "#5": 8,
}
MAJOR_KEY_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_KEY_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def analyze_job_chords(job_dir: Path) -> dict[str, Any]:
    manifest = read_manifest(job_dir)
    if not manifest.normalized_path:
        raise ValueError("Job has no normalized WAV to analyze.")

    source_path = Path(manifest.normalized_path)
    chord_rows = _predict_accordoai(source_path)
    duration = _duration_from_rows(chord_rows)
    tempo = _estimate_tempo(source_path)
    key = _estimate_key(source_path, chord_rows)
    spelling_mode = str(key.get("mode") or _infer_spelling_mode(chord_rows)) if key else _infer_spelling_mode(chord_rows)
    segments = _bar_segments_from_accordoai_rows(chord_rows, duration, spelling_mode, tempo)

    result = {
        "job_id": manifest.job_id,
        "source": "normalized.wav",
        "method": "accordoai-0.2.7",
        "sample_rate": SAMPLE_RATE,
        "key": key,
        "spelling": {
            "mode_context": spelling_mode,
            "accidentals": "sharps" if spelling_mode == "major" else "flats",
        },
        "tempo": tempo,
        "segments": segments,
        "notes": [
            "Chord detection is provided by accordoai's bundled deep-learning model.",
            "Song key is estimated with pymusickit's Krumhansl-Schmuckler key finder.",
            "Tempo and bar numbers assume a steady 4/4 pulse.",
        ],
    }

    analysis_dir = job_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "chords.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def read_chord_analysis(job_dir: Path) -> dict[str, Any]:
    path = job_dir / "analysis" / "chords.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _predict_accordoai(source_path: Path) -> list[dict[str, Any]]:
    try:
        from accordoai import ChordPredictor
        from accordoai import predictor as accordo_predictor
    except ImportError as exc:
        raise RuntimeError(
            "accordoai is not installed in this image. Rebuild the Docker image with chord requirements."
        ) from exc

    # accordoai keeps predictions in module globals; clear them so repeated songs do not leak into each other.
    for name in (
        "predictions_root",
        "predictions_bass",
        "predictions_triad",
        "predictions_fourth",
        "predicted_chord_vector",
    ):
        value = getattr(accordo_predictor, name, None)
        if hasattr(value, "clear"):
            value.clear()

    predictor = ChordPredictor()
    prediction = predictor.predict_chords(str(source_path))
    if prediction is None:
        raise RuntimeError("accordoai did not return chord predictions.")
    if not hasattr(prediction, "to_dict"):
        raise RuntimeError("accordoai returned an unsupported prediction format.")
    return prediction.to_dict("records")


def _bar_segments_from_accordoai_rows(
    rows: list[dict[str, Any]],
    duration: float,
    spelling_mode: str,
    tempo: dict[str, Any],
) -> list[dict[str, Any]]:
    if duration <= 0:
        return []

    seconds_per_bar = float(tempo.get("seconds_per_bar") or 3.0)
    bar_count = max(1, int(np.ceil(duration / seconds_per_bar)))
    normalized_rows = [
        (
            float(row.get("timestep") or 0.0),
            _normalize_accordoai_label(str(row.get("chord_label") or NO_CHORD), spelling_mode),
        )
        for row in rows
    ]
    raw_segments: list[dict[str, Any]] = []
    for bar_index in range(bar_count):
        start = bar_index * seconds_per_bar
        end = min(duration, (bar_index + 1) * seconds_per_bar)
        chords = [chord for time_value, chord in normalized_rows if start <= time_value < end]
        chord = _most_common_chord(chords)
        confidence = 0.72 if chord != NO_CHORD else 0.0
        raw_segments.append(
            {
                "start": round(start, 3),
                "end": round(end, 3),
                "chord": chord,
                "confidence": confidence,
            }
        )

    return _merge_adjacent_segments(raw_segments, duration)


def _segment(start: float, end: float, chord: str) -> dict[str, Any]:
    return {
        "start": round(max(0.0, start), 3),
        "end": round(max(start, end), 3),
        "chord": chord,
        "confidence": 0.72 if chord != NO_CHORD else 0.0,
    }


def _merge_adjacent_segments(segments: list[dict[str, Any]], duration: float) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for segment in segments:
        if merged and merged[-1]["chord"] == segment["chord"]:
            merged[-1]["end"] = segment["end"]
        else:
            merged.append(dict(segment))

    if merged:
        merged[0]["start"] = 0.0
        merged[-1]["end"] = round(duration, 3)
    return merged


def _most_common_chord(chords: list[str]) -> str:
    if not chords:
        return NO_CHORD
    counts: dict[str, int] = {}
    for chord in chords:
        counts[chord] = counts.get(chord, 0) + 1
    non_silent = {chord: count for chord, count in counts.items() if chord != NO_CHORD}
    if non_silent:
        return max(non_silent.items(), key=lambda item: item[1])[0]
    return NO_CHORD


def _normalize_accordoai_label(label: str, spelling_mode: str) -> str:
    label = label.strip()
    if not label or label in {"N", "X", NO_CHORD}:
        return NO_CHORD

    root, separator, rest = label.partition(":")
    root = _normalize_note(root, spelling_mode)
    if not root:
        return NO_CHORD

    quality = rest if separator else ""
    slash = ""
    if "/" in quality:
        quality, slash = quality.split("/", 1)

    suffix = {
        "": "",
        "maj": "",
        "Major": "",
        "min": "m",
        "Minor": "m",
        "7": "7",
        "maj7": "maj7",
        "min7": "m7",
        "maj6": "6",
        "minmaj7": "mMaj7",
        "dim": "dim",
        "dim7": "dim7",
        "aug": "aug",
        "sus2": "sus2",
        "sus4": "sus4",
    }.get(quality, quality)

    chord = f"{root}{suffix}"
    bass = _bass_note_from_interval(root, slash, spelling_mode)
    if bass and bass != root:
        chord = f"{chord}/{bass}"
    return chord


def _normalize_note(note: str, spelling_mode: str) -> str | None:
    note = note.strip()
    if note not in NOTE_TO_PC:
        return None
    return _pitch_names(spelling_mode)[NOTE_TO_PC[note]]


def _bass_note_from_interval(root: str, interval: str, spelling_mode: str) -> str | None:
    if not interval:
        return None
    if interval in NOTE_TO_PC:
        return _pitch_names(spelling_mode)[NOTE_TO_PC[interval]]
    if interval not in SLASH_INTERVALS:
        return None
    return _pitch_names(spelling_mode)[(NOTE_TO_PC[root] + SLASH_INTERVALS[interval]) % 12]


def _pitch_names(spelling_mode: str) -> tuple[str, ...]:
    return PITCH_NAMES_SHARP if spelling_mode == "major" else PITCH_NAMES_FLAT


def _infer_spelling_mode(rows: list[dict[str, Any]]) -> str:
    major_weight = 0.0
    minor_weight = 0.0
    for row in rows:
        label = str(row.get("chord_label") or "")
        if label in {"", "N", "X"}:
            continue
        if ":min" in label:
            minor_weight += 1.0
        elif ":maj" in label or ":7" in label or ":" not in label:
            major_weight += 1.0
    return "minor" if minor_weight > major_weight else "major"


def _duration_from_rows(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    last = float(rows[-1].get("timestep") or 0.0)
    return round(last + (HOP_SIZE / SAMPLE_RATE), 3)


def _estimate_tempo(path: Path) -> dict[str, Any]:
    try:
        import librosa

        audio, sample_rate = librosa.load(path, sr=SAMPLE_RATE, mono=True)
        bpm = _librosa_tempo(audio, sample_rate, HOP_SIZE)
        fine_bpm = _librosa_tempo(audio, sample_rate, 512)
        if bpm > 155 and 135 <= fine_bpm <= 155:
            bpm = fine_bpm
        confidence = 0.75
    except Exception:
        bpm = 120.0
        confidence = 0.0
    return _tempo_result(bpm, confidence)


def _librosa_tempo(audio: np.ndarray, sample_rate: int, hop_length: int) -> float:
    import librosa

    onset = librosa.onset.onset_strength(y=audio, sr=sample_rate, hop_length=hop_length)
    tempo = librosa.feature.tempo(onset_envelope=onset, sr=sample_rate, hop_length=hop_length)
    return float(np.ravel(tempo)[0]) if np.size(tempo) else 120.0


def _estimate_key(path: Path, chord_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    try:
        from pymusickit.key_finder import KeyFinder

        key_finder = KeyFinder(str(path))
        primary, primary_corr = key_finder.get_primary_key_corr()
        alternate, alternate_corr = key_finder.get_secondary_key_corr()
        tonic, mode = _parse_pymusickit_key(primary)
        if tonic is None or mode is None:
            return None
        tonic = _normalize_note(tonic, mode) or tonic
        confidence = _key_confidence(primary_corr, alternate_corr)
        key = {
            "tonic": tonic,
            "mode": mode,
            "label": f"{tonic} {'major' if mode == 'major' else 'minor'}",
            "confidence": round(confidence, 3),
            "method": "pymusickit-krumhansl-schmuckler",
            "correlation": round(float(primary_corr), 3),
            "alternate": _format_alternate_key(alternate, alternate_corr),
        }
        return _apply_chord_mode_context(key, chord_rows)
    except Exception:
        return None


def _apply_chord_mode_context(key: dict[str, Any], chord_rows: list[dict[str, Any]]) -> dict[str, Any]:
    alternate = key.get("alternate")
    if not isinstance(alternate, dict):
        return key
    if alternate.get("tonic") != key.get("tonic") or alternate.get("mode") == key.get("mode"):
        return key

    primary_score = _scale_fit_score(chord_rows, str(key["tonic"]), str(key["mode"]))
    alternate_score = _scale_fit_score(chord_rows, str(alternate["tonic"]), str(alternate["mode"]))
    if alternate_score <= primary_score + 0.12:
        return key

    original = {
        "tonic": key["tonic"],
        "mode": key["mode"],
        "label": key["label"],
        "correlation": key["correlation"],
        "scale_fit": round(primary_score, 3),
    }
    tonic = str(alternate["tonic"])
    mode = str(alternate["mode"])
    adjusted = dict(key)
    adjusted.update(
        {
            "tonic": tonic,
            "mode": mode,
            "label": f"{tonic} {'major' if mode == 'major' else 'minor'}",
            "confidence": round(max(0.55, float(key.get("confidence") or 0.0) - 0.12), 3),
            "correlation": alternate["correlation"],
            "chord_context_adjusted": True,
            "scale_fit": round(alternate_score, 3),
            "alternate": original,
        }
    )
    return adjusted


def _scale_fit_score(chord_rows: list[dict[str, Any]], tonic: str, mode: str) -> float:
    tonic_pc = NOTE_TO_PC.get(tonic)
    if tonic_pc is None:
        return 0.0
    scale_intervals = (0, 2, 4, 5, 7, 9, 11) if mode == "major" else (0, 2, 3, 5, 7, 8, 10)
    scale_pcs = {(tonic_pc + interval) % 12 for interval in scale_intervals}
    root_counts: dict[int, int] = {}
    for row in chord_rows:
        root_pc = _accordoai_root_pc(str(row.get("chord_label") or ""))
        if root_pc is None:
            continue
        root_counts[root_pc] = root_counts.get(root_pc, 0) + 1
    total = sum(root_counts.values())
    if total == 0:
        return 0.0
    fit = sum(count for pc, count in root_counts.items() if pc in scale_pcs)
    tonic_weight = root_counts.get(tonic_pc, 0) / total
    return (fit / total) + (tonic_weight * 0.08)


def _accordoai_root_pc(label: str) -> int | None:
    label = label.strip()
    if not label or label in {"N", "X", NO_CHORD}:
        return None
    root = label.split(":", 1)[0]
    return NOTE_TO_PC.get(root)


def _parse_pymusickit_key(label: str | None) -> tuple[str | None, str | None]:
    parts = str(label or "").strip().split()
    if len(parts) < 2:
        return None, None
    tonic = parts[0]
    mode = parts[1].lower()
    if mode not in {"major", "minor"}:
        return None, None
    return tonic, mode


def _key_confidence(primary_corr: float | None, alternate_corr: float | None) -> float:
    primary = float(primary_corr or 0.0)
    alternate = float(alternate_corr or 0.0)
    return float(np.clip((primary + 1.0) / 2.0 + max(0.0, primary - alternate) * 0.35, 0.0, 1.0))


def _format_alternate_key(label: str | None, correlation: float | None) -> dict[str, Any] | None:
    tonic, mode = _parse_pymusickit_key(label)
    if tonic is None or mode is None or correlation is None:
        return None
    tonic = _normalize_note(tonic, mode) or tonic
    return {
        "tonic": tonic,
        "mode": mode,
        "label": f"{tonic} {'major' if mode == 'major' else 'minor'}",
        "correlation": round(float(correlation), 3),
    }


def _tempo_result(bpm: float, confidence: float) -> dict[str, Any]:
    normalized_bpm = float(bpm)
    while normalized_bpm < 55:
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
