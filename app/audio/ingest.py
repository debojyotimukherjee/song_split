from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from app.core.manifests import AudioMetadata


SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ingest_file(input_file: Path, job_dir: Path) -> AudioMetadata:
    input_file = input_file.expanduser()
    if not input_file.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_file}")
    if input_file.suffix.lower() not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Unsupported audio format '{input_file.suffix}'. Supported: {supported}")

    input_dir = job_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    destination = input_dir / f"original{input_file.suffix.lower()}"
    shutil.copy2(input_file, destination)

    return AudioMetadata(
        filename=input_file.name,
        original_path=str(destination),
        file_sha256=sha256_file(destination),
        size_bytes=destination.stat().st_size,
    )

