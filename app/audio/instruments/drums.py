from __future__ import annotations

import shutil
from pathlib import Path


def create_drums_stem(source_file: Path, output_file: Path) -> None:
    shutil.copy2(source_file, output_file)

