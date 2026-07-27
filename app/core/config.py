from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    model_name: str = "htdemucs_6s"

    @property
    def inbox_dir(self) -> Path:
        return self.data_dir / "inbox"

    @property
    def jobs_dir(self) -> Path:
        return self.data_dir / "jobs"

    @property
    def models_dir(self) -> Path:
        return self.data_dir / "models"

    @classmethod
    def from_env(cls) -> "Settings":
        data_dir = Path(os.getenv("SONG_SPLIT_DATA_DIR", "data"))
        model_name = os.getenv("SONG_SPLIT_MODEL_NAME", "htdemucs_6s")
        return cls(data_dir=data_dir, model_name=model_name)

