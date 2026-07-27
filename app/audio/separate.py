from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from threading import Event
from typing import Callable

from app.audio.keys import FOCUS_STEMS_DIR, create_keys_focus_stem, create_keys_rebuild_stem
from app.core.manifests import StemManifest


TARGET_STEMS = [
    "main_vocal",
    "backing_vocal",
    "drums",
    "bass",
    "guitar",
    "keys",
    "other",
]

DEMUX_SOURCE_STEMS = ("vocals", "drums", "bass", "guitar", "piano", "other")
DIRECT_DEMUX_TO_TARGET = {
    "vocals": "main_vocal",
    "drums": "drums",
    "guitar": "guitar",
    "piano": "keys",
    "other": "other",
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
        _create_backing_vocal_estimate(vocals_file, backing_vocal_file)
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

    bass_file = raw_stems_dir / "bass.wav"
    if bass_file.exists():
        target_file = stems_dir / "bass.wav"
        _create_clean_bass(bass_file, target_file)
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

    create_guitar_focus_stem(job_dir)
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


def create_guitar_focus_stem(job_dir: Path) -> bool:
    raw_stems_dir = job_dir / "stems_raw"
    guitar_file = raw_stems_dir / "guitar.wav"
    if not guitar_file.exists():
        return False

    source_files = [guitar_file]
    weights = [1.0]
    other_file = raw_stems_dir / "other.wav"
    piano_file = raw_stems_dir / "piano.wav"
    if other_file.exists():
        source_files.append(other_file)
        weights.append(0.42)
    if piano_file.exists():
        source_files.append(piano_file)
        weights.append(0.18)

    output_dir = job_dir / FOCUS_STEMS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg_mix(source_files, output_dir / "guitar.wav", weights)
    return True


def _create_clean_bass(source_file: Path, output_file: Path) -> None:
    bass_filter = ",".join(
        [
            "highpass=f=35",
            "lowpass=f=4200",
            "equalizer=f=220:t=q:w=1.2:g=-4",
            "equalizer=f=320:t=q:w=1.0:g=-2.5",
            "alimiter=limit=0.98",
        ]
    )
    _run_ffmpeg_filter(source_file, output_file, bass_filter)


def _create_backing_vocal_estimate(source_file: Path, output_file: Path) -> None:
    backing_filter = ",".join(
        [
            "pan=stereo|c0=0.55*c0-0.35*c1|c1=0.55*c1-0.35*c0",
            "highpass=f=120",
            "lowpass=f=9000",
            "alimiter=limit=0.95",
        ]
    )
    _run_ffmpeg_filter(source_file, output_file, backing_filter)


def _run_ffmpeg_filter(source_file: Path, output_file: Path, audio_filter: str) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source_file),
        "-af",
        audio_filter,
        str(output_file),
    ]
    subprocess.run(command, check=True)


def _run_ffmpeg_mix(source_files: list[Path], output_file: Path, weights: list[float]) -> None:
    command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for source_file in source_files:
        command.extend(["-i", str(source_file)])

    labels = []
    filters = []
    for index, weight in enumerate(weights):
        label = f"a{index}"
        labels.append(f"[{label}]")
        filters.append(f"[{index}:a]volume={weight}[{label}]")

    filter_complex = ";".join(filters)
    filter_complex += (
        f";{''.join(labels)}amix=inputs={len(source_files)}:duration=first:normalize=0,"
        "alimiter=limit=0.98[out]"
    )
    command.extend(["-filter_complex", filter_complex, "-map", "[out]", str(output_file)])
    subprocess.run(command, check=True)


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
