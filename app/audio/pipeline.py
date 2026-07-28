from __future__ import annotations

from pathlib import Path
from threading import Event
from typing import Callable

from app.audio.audio_separator_backend import apply_audio_separator_specialists
from app.audio.ingest import ingest_file
from app.audio.normalize import normalize_to_wav
from app.audio.separate import SplitCancelled, map_demucs_output, run_demucs, unavailable_stems
from app.core.config import Settings
from app.core.manifests import JobManifest, read_manifest, utc_now, write_manifest
from app.core.paths import make_job_id


def process_file(
    input_file: Path,
    settings: Settings,
    engine: str,
    requested_job_id: str | None = None,
    progress_callback: Callable[[int, str], None] | None = None,
    cancel_event: Event | None = None,
) -> JobManifest:
    settings.jobs_dir.mkdir(parents=True, exist_ok=True)
    job_id = make_job_id(input_file, requested_job_id)
    job_dir = settings.jobs_dir / job_id

    created_at = utc_now()
    input_metadata = ingest_file(input_file, job_dir)
    manifest = JobManifest(
        job_id=job_id,
        status="created",
        created_at=created_at,
        updated_at=created_at,
        input=input_metadata,
        engine=engine,
        model_name=settings.model_name if engine == "demucs" else None,
    )
    write_manifest(job_dir, manifest)

    _check_cancelled(cancel_event)
    if progress_callback:
        progress_callback(12, "Normalizing audio...")
    normalized_path = job_dir / "working" / "normalized.wav"
    normalize_to_wav(Path(input_metadata.original_path), normalized_path)
    manifest.status = "normalized"
    manifest.normalized_path = str(normalized_path)
    manifest.updated_at = utc_now()
    write_manifest(job_dir, manifest)

    _check_cancelled(cancel_event)
    if engine == "none":
        manifest.stems = unavailable_stems("Separation was skipped with --engine none.")
        manifest.warnings.append("Separation skipped; only ingest and normalization were run.")
    elif engine == "demucs":
        manifest.stems = run_demucs(
            normalized_path,
            job_dir,
            settings.model_name,
            cancel_event=cancel_event,
            progress_callback=progress_callback,
        )
        _check_cancelled(cancel_event)
        manifest.stems = apply_audio_separator_specialists(
            normalized_path,
            job_dir,
            settings,
            manifest.stems,
            cancel_event=cancel_event,
            progress_callback=progress_callback,
        )
        manifest.status = "separated"
    else:
        raise ValueError(f"Unknown separation engine: {engine}")

    manifest.updated_at = utc_now()
    write_manifest(job_dir, manifest)
    return manifest


def _check_cancelled(cancel_event: Event | None) -> None:
    if cancel_event and cancel_event.is_set():
        raise SplitCancelled("Split was cancelled.")


def remap_existing_job(job_dir: Path, settings: Settings) -> JobManifest:
    manifest = read_manifest(job_dir)
    if not manifest.normalized_path:
        raise ValueError(f"Job has no normalized path: {job_dir}")

    model_output_dir = (
        job_dir
        / "working"
        / "demucs"
        / (manifest.model_name or settings.model_name)
        / Path(manifest.normalized_path).stem
    )
    manifest.stems = map_demucs_output(model_output_dir, job_dir)
    manifest.status = "separated"
    manifest.updated_at = utc_now()
    manifest.warnings = [
        warning
        for warning in manifest.warnings
        if warning != "Guitar and keys split with estimated pan-biased second-stage mapping."
    ]
    write_manifest(job_dir, manifest)
    return manifest


def enhance_existing_job_audio_separator(job_dir: Path, settings: Settings) -> JobManifest:
    manifest = read_manifest(job_dir)
    if not manifest.normalized_path:
        raise ValueError(f"Job has no normalized path: {job_dir}")
    manifest.stems = apply_audio_separator_specialists(
        Path(manifest.normalized_path),
        job_dir,
        settings,
        manifest.stems,
    )
    manifest.status = "separated"
    manifest.updated_at = utc_now()
    manifest.warnings = [
        warning
        for warning in manifest.warnings
        if not warning.startswith("audio-separator")
    ]
    if settings.audio_separator_enabled:
        manifest.warnings.append(
            "audio-separator specialist pass enabled for guitar/acoustic guitar/keys."
        )
    write_manifest(job_dir, manifest)
    return manifest
