from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from threading import Event
from typing import Callable

from app.audio.instruments.bass import create_bass_stem
from app.audio.instruments.drums import create_drums_stem
from app.audio.instruments.guitar import create_guitar_stems
from app.audio.instruments.keys import create_keys_focus_stem, create_keys_rebuild_stem
from app.audio.instruments.other import create_other_stem
from app.audio.instruments.vocals import create_backing_vocal_estimate
from app.core.manifests import StemManifest


TARGET_STEMS = [
    "main_vocal",
    "backing_vocal",
    "drums",
    "bass",
    "lead_guitar",
    "rhythm_guitar",
    "keys",
    "other",
]

DEMUX_SOURCE_STEMS = ("vocals", "drums", "bass", "guitar", "piano", "other")
DIRECT_DEMUX_TO_TARGET = {
    "vocals": "main_vocal",
    "piano": "keys",
}


class SplitCancelled(RuntimeError):
    pass


def unavailable_stems(notes: str) -> list[StemManifest]:
    return [
        StemManifest(
            name=name,
            status="unavailable",
            confidence=0.0,
            notes=notes,
        )
        for name in TARGET_STEMS
    ]


def run_demucs(
    normalized_wav: Path,
    job_dir: Path,
    model_name: str,
    cancel_event: Event | None = None,
    progress_callback: Callable[[int, str], None] | None = None,
) -> list[StemManifest]:
    if not _demucs_available():
        raise RuntimeError(
            "Demucs is not installed in this container. Rebuild with "
            "`INSTALL_DEMUCS=true docker compose build`."
        )

    raw_dir = job_dir / "working" / "demucs"
    stems_dir = job_dir / "stems"
    raw_dir.mkdir(parents=True, exist_ok=True)
    stems_dir.mkdir(parents=True, exist_ok=True)

    command = [
        "python",
        "-m",
        "demucs.separate",
        "-n",
        model_name,
        "--out",
        str(raw_dir),
        str(normalized_wav),
    ]
    _check_cancelled(cancel_event)
    if progress_callback:
        progress_callback(35, "Separating stems with Demucs...")
    process = subprocess.Popen(command)
    try:
        while process.poll() is None:
            if cancel_event and cancel_event.is_set():
                process.terminate()
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                raise SplitCancelled("Split was cancelled.")
    except Exception:
        if process.poll() is None:
            process.terminate()
        raise
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command)

    model_output_dir = raw_dir / model_name / normalized_wav.stem
    if progress_callback:
        progress_callback(82, "Preparing track files...")
    _check_cancelled(cancel_event)
    return map_demucs_output(model_output_dir, job_dir)


def map_demucs_output(model_output_dir: Path, job_dir: Path) -> list[StemManifest]:
    if not model_output_dir.exists():
        raise FileNotFoundError(f"Demucs output folder does not exist: {model_output_dir}")

    stems_dir = job_dir / "stems"
    raw_stems_dir = job_dir / "stems_raw"
    stems_dir.mkdir(parents=True, exist_ok=True)
    raw_stems_dir.mkdir(parents=True, exist_ok=True)

    manifests: list[StemManifest] = []
    mapped_targets: set[str] = set()

    for source_stem in DEMUX_SOURCE_STEMS:
        source_file = model_output_dir / f"{source_stem}.wav"
        if not source_file.exists():
            continue
        shutil.copy2(source_file, raw_stems_dir / f"{source_stem}.wav")

    for source_stem, target_stem in DIRECT_DEMUX_TO_TARGET.items():
        source_file = raw_stems_dir / f"{source_stem}.wav"
        if not source_file.exists():
            continue
        target_file = stems_dir / f"{target_stem}.wav"
        shutil.copy2(source_file, target_file)
        manifests.append(
            StemManifest(
                name=target_stem,
                path=str(target_file),
                status="generated",
                source_stem=source_stem,
                confidence=0.9,
            )
        )
        mapped_targets.add(target_stem)

    vocals_file = raw_stems_dir / "vocals.wav"
    if vocals_file.exists():
        backing_vocal_file = stems_dir / "backing_vocal.wav"
        create_backing_vocal_estimate(vocals_file, backing_vocal_file)
        manifests.append(
            StemManifest(
                name="backing_vocal",
                path=str(backing_vocal_file),
                status="estimated",
                source_stem="vocals",
                confidence=0.45,
                notes=(
                    "Estimated from the raw Demucs vocal stem using a side/wide vocal "
                    "extraction. This can catch doubled vocals, harmonies, and reverb, "
                    "but it is not a true lead/backing vocal model split."
                ),
            )
        )
        mapped_targets.add("backing_vocal")

    drums_file = raw_stems_dir / "drums.wav"
    if drums_file.exists():
        target_file = stems_dir / "drums.wav"
        create_drums_stem(drums_file, target_file)
        manifests.append(
            StemManifest(
                name="drums",
                path=str(target_file),
                status="generated",
                source_stem="drums",
                confidence=0.9,
            )
        )
        mapped_targets.add("drums")

    bass_file = raw_stems_dir / "bass.wav"
    if bass_file.exists():
        target_file = stems_dir / "bass.wav"
        create_bass_stem(bass_file, target_file)
        manifests.append(
            StemManifest(
                name="bass",
                path=str(target_file),
                status="generated",
                source_stem="bass",
                confidence=0.85,
                notes=(
                    "Cleaned from the raw Demucs bass stem with rumble removal, "
                    "low-mid mud reduction, and upper bleed filtering. Raw bass is "
                    "preserved in stems_raw/bass.wav."
                ),
            )
        )
        mapped_targets.add("bass")

    if create_guitar_stems(job_dir):
        for name, confidence, notes in (
            (
                "lead_guitar",
                0.62,
                "Estimated from Demucs guitar with a lead-focused filter; no keys or piano are blended in.",
            ),
            (
                "rhythm_guitar",
                0.62,
                "Estimated from Demucs guitar with a rhythm-focused filter; no keys or piano are blended in.",
            ),
        ):
            target_file = stems_dir / f"{name}.wav"
            manifests.append(
                StemManifest(
                    name=name,
                    path=str(target_file),
                    status="estimated",
                    source_stem="guitar",
                    confidence=confidence,
                    notes=notes,
                )
            )
            mapped_targets.add(name)

    other_file = raw_stems_dir / "other.wav"
    if other_file.exists():
        target_file = stems_dir / "other.wav"
        create_other_stem(other_file, target_file)
        manifests.append(
            StemManifest(
                name="other",
                path=str(target_file),
                status="generated",
                source_stem="other",
                confidence=0.9,
            )
        )
        mapped_targets.add("other")

    create_keys_focus_stem(job_dir)
    create_keys_rebuild_stem(job_dir)

    for target in TARGET_STEMS:
        if target not in mapped_targets:
            manifests.append(
                StemManifest(
                    name=target,
                    status="unavailable",
                    confidence=0.0,
                    notes="No reliable direct model output for this target stem yet.",
                )
            )

    return sorted(manifests, key=lambda item: TARGET_STEMS.index(item.name))


def _check_cancelled(cancel_event: Event | None) -> None:
    if cancel_event and cancel_event.is_set():
        raise SplitCancelled("Split was cancelled.")


def _demucs_available() -> bool:
    result = subprocess.run(
        ["python", "-c", "import demucs"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0
