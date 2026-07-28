from __future__ import annotations

import re
import shutil
import subprocess
import time
from pathlib import Path
from threading import Event
from typing import Callable

from app.audio.instruments.acoustic_guitar import create_acoustic_guitar_stem
from app.audio.instruments.guitar import create_guitar_stem
from app.audio.instruments.keys import create_keys_stems
from app.audio.separate import SplitCancelled, TARGET_STEMS
from app.core.config import Settings
from app.core.manifests import StemManifest


SPECIALIST_STEMS = {"guitar", "acoustic_guitar", "keys"}


def apply_audio_separator_specialists(
    normalized_wav: Path,
    job_dir: Path,
    settings: Settings,
    manifests: list[StemManifest],
    cancel_event: Event | None = None,
    progress_callback: Callable[[int, str], None] | None = None,
) -> list[StemManifest]:
    if not settings.audio_separator_enabled:
        return manifests
    if not _audio_separator_available():
        return _with_warning(
            manifests,
            "audio-separator is enabled, but the package is not installed in this image.",
        )
    if not settings.audio_separator_models:
        return manifests

    raw_stems_dir = job_dir / "stems_raw"
    raw_stems_dir.mkdir(parents=True, exist_ok=True)
    candidate_files: dict[str, Path] = {}
    models_to_run = [
        model_filename
        for model_filename in settings.audio_separator_models
        if not _is_duplicate_demucs_model(model_filename, settings.model_name)
    ]
    if not models_to_run:
        return _with_warning(
            manifests,
            "audio-separator was enabled, but duplicate Demucs models were skipped.",
        )

    for index, model_filename in enumerate(models_to_run):
        _check_cancelled(cancel_event)
        if progress_callback:
            progress_callback(82 + index, f"Trying audio-separator model {model_filename}...")
        output_dir = job_dir / "working" / "audio_separator" / _safe_model_name(model_filename)
        output_dir.mkdir(parents=True, exist_ok=True)
        _run_audio_separator_model(normalized_wav, output_dir, model_filename, settings, cancel_event)
        candidate_files.update(_collect_candidate_files(output_dir))

    updated = {manifest.name: manifest for manifest in manifests}

    guitar_file = candidate_files.get("guitar")
    if guitar_file:
        shutil.copy2(guitar_file, raw_stems_dir / "audio_separator_guitar.wav")
        target_file = job_dir / "stems" / "guitar.wav"
        create_guitar_stem(guitar_file, target_file)
        updated["guitar"] = StemManifest(
            name="guitar",
            path=str(target_file),
            status="generated",
            source_stem="audio-separator:guitar",
            confidence=0.86,
            notes="Cleaned from an audio-separator/UVR guitar candidate.",
        )

        acoustic_file = job_dir / "stems" / "acoustic_guitar.wav"
        create_acoustic_guitar_stem(
            guitar_file,
            candidate_files.get("other") or raw_stems_dir / "other.wav",
            acoustic_file,
        )
        updated["acoustic_guitar"] = StemManifest(
            name="acoustic_guitar",
            path=str(acoustic_file),
            status="estimated",
            source_stem="audio-separator:guitar+other",
            confidence=0.68,
            notes="Estimated acoustic-focused lane from audio-separator guitar plus harmonic other content.",
        )

    piano_file = candidate_files.get("piano") or candidate_files.get("keys")
    if piano_file:
        shutil.copy2(piano_file, raw_stems_dir / "audio_separator_piano.wav")
        shutil.copy2(piano_file, raw_stems_dir / "piano.wav")
        keys_stems = create_keys_stems(job_dir)
        if keys_stems:
            for stem_info in keys_stems:
                updated[stem_info.name] = StemManifest(
                    name=stem_info.name,
                    path=str(stem_info.path),
                    status=stem_info.status,
                    source_stem="audio-separator:piano",
                    confidence=max(stem_info.confidence, 0.66),
                    notes=f"{stem_info.notes} Source piano candidate came from audio-separator/UVR.",
                )

    return [updated[name] for name in TARGET_STEMS if name in updated]


def _run_audio_separator_model(
    normalized_wav: Path,
    output_dir: Path,
    model_filename: str,
    settings: Settings,
    cancel_event: Event | None,
) -> None:
    settings.audio_separator_models_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "audio-separator",
        str(normalized_wav),
        "--model_filename",
        model_filename,
        "--model_file_dir",
        str(settings.audio_separator_models_dir),
        "--output_dir",
        str(output_dir),
        "--output_format",
        "WAV",
        "--sample_rate",
        "44100",
        "--normalization",
        "0.9",
    ]
    process = subprocess.Popen(command)
    started_at = time.monotonic()
    try:
        while process.poll() is None:
            _check_cancelled(cancel_event)
            if time.monotonic() - started_at > settings.audio_separator_timeout_seconds:
                process.terminate()
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                raise TimeoutError(
                    f"audio-separator model {model_filename} exceeded "
                    f"{settings.audio_separator_timeout_seconds} seconds."
                )
            time.sleep(1)
    except Exception:
        if process.poll() is None:
            process.terminate()
        raise
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command)


def _collect_candidate_files(output_dir: Path) -> dict[str, Path]:
    candidates: dict[str, Path] = {}
    for path in output_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".wav", ".flac", ".mp3"}:
            continue
        normalized_name = re.sub(r"[^a-z0-9]+", "_", path.stem.lower())
        for stem_name, tokens in {
            "guitar": ("guitar",),
            "piano": ("piano", "keys", "keyboards"),
            "other": ("other",),
        }.items():
            if stem_name not in candidates and any(token in normalized_name for token in tokens):
                candidates[stem_name] = path
    return candidates


def _with_warning(manifests: list[StemManifest], note: str) -> list[StemManifest]:
    return [
        manifest.model_copy(update={"notes": f"{manifest.notes or ''} {note}".strip()})
        if manifest.name in SPECIALIST_STEMS
        else manifest
        for manifest in manifests
    ]


def _audio_separator_available() -> bool:
    return shutil.which("audio-separator") is not None


def _safe_model_name(model_filename: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", model_filename).strip("._") or "model"


def _is_duplicate_demucs_model(model_filename: str, demucs_model_name: str) -> bool:
    normalized = model_filename.removesuffix(".yaml")
    return normalized == demucs_model_name


def _check_cancelled(cancel_event: Event | None) -> None:
    if cancel_event and cancel_event.is_set():
        raise SplitCancelled("Split was cancelled.")
