from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


StemStatus = Literal["generated", "estimated", "unavailable"]
JobStatus = Literal["created", "normalized", "separated", "failed", "cancelled"]


class AudioMetadata(BaseModel):
    filename: str
    original_path: str
    file_sha256: str
    size_bytes: int


class StemManifest(BaseModel):
    name: str
    path: str | None = None
    status: StemStatus
    source_stem: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    notes: str | None = None


class JobManifest(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    input: AudioMetadata
    normalized_path: str | None = None
    model_name: str | None = None
    engine: str
    stems: list[StemManifest] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def write_manifest(job_dir: Path, manifest: JobManifest) -> None:
    job_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = job_dir / "manifest.json"
    manifest_path.write_text(
        manifest.model_dump_json(indent=2),
        encoding="utf-8",
    )


def read_manifest(job_dir: Path) -> JobManifest:
    manifest_path = job_dir / "manifest.json"
    return JobManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
