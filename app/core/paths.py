from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "song"


def make_job_id(input_file: Path, requested_job_id: str | None = None) -> str:
    if requested_job_id:
        return slugify(requested_job_id)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{timestamp}-{slugify(input_file.stem)}"

