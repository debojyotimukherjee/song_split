from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    model_name: str = "htdemucs_6s"
    audio_separator_enabled: bool = False
    audio_separator_models: tuple[str, ...] = ()
    audio_separator_timeout_seconds: int = 900

    @property
    def inbox_dir(self) -> Path:
        return self.data_dir / "inbox"

    @property
    def jobs_dir(self) -> Path:
        return self.data_dir / "jobs"

    @property
    def models_dir(self) -> Path:
        return self.data_dir / "models"

    @property
    def audio_separator_models_dir(self) -> Path:
        return self.models_dir / "audio-separator"

    @classmethod
    def from_env(cls) -> "Settings":
        data_dir = Path(os.getenv("SONG_SPLIT_DATA_DIR", "data"))
        model_name = os.getenv("SONG_SPLIT_MODEL_NAME", "htdemucs_6s")
        audio_separator_enabled = os.getenv("SONG_SPLIT_ENABLE_AUDIO_SEPARATOR", "false").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        audio_separator_models = tuple(
            model.strip()
            for model in os.getenv("SONG_SPLIT_AUDIO_SEPARATOR_MODELS", "").split(",")
            if model.strip()
        )
        audio_separator_timeout_seconds = int(os.getenv("SONG_SPLIT_AUDIO_SEPARATOR_TIMEOUT_SECONDS", "900"))
        return cls(
            data_dir=data_dir,
            model_name=model_name,
            audio_separator_enabled=audio_separator_enabled,
            audio_separator_models=audio_separator_models,
            audio_separator_timeout_seconds=audio_separator_timeout_seconds,
        )
