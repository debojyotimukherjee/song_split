from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import zipfile
from threading import Event, Lock, Thread
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.audio.chords import analyze_job_chords, read_chord_analysis
from app.audio.pipeline import process_file
from app.audio.separate import SplitCancelled
from app.core.config import Settings
from app.core.manifests import read_manifest, utc_now, write_manifest
from app.core.paths import make_job_id

app = FastAPI(title="Wannabe Stem API")


TaskState = Literal["queued", "running", "done", "failed", "cancelled"]


@dataclass
class SplitTask:
    task_id: str
    filename: str
    job_id: str | None = None
    state: TaskState = "queued"
    progress: int = 0
    message: str = "Queued"
    error: str | None = None
    cancel_event: Event = field(default_factory=Event)
    stage: str = "queued"
    stage_started_at: float | None = None
    estimated_stage_seconds: float | None = None


split_tasks: dict[str, SplitTask] = {}
split_tasks_lock = Lock()


class MixTrackSettings(BaseModel):
    volume: float = Field(default=1.0, ge=0.0, le=2.0)
    muted: bool = False
    low: float = Field(default=0.0, ge=-12.0, le=12.0)
    mid: float = Field(default=0.0, ge=-12.0, le=12.0)
    high: float = Field(default=0.0, ge=-12.0, le=12.0)
    reverb: float = Field(default=50.0, ge=0.0, le=100.0)
    compression: float = Field(default=50.0, ge=0.0, le=100.0)


class HdMixRequest(BaseModel):
    tracks: dict[str, MixTrackSettings] = Field(default_factory=dict)
    hd_master: bool = True
    semitones: int = Field(default=0, ge=-12, le=12)
    format: Literal["wav", "mp3"] = "wav"
    preset: Literal["full", "minus_vocals", "minus_guitar", "minus_keys", "stems_zip"] = "full"


class MixSettingsRequest(BaseModel):
    settings: dict = Field(default_factory=dict)


class ChordUpdateRequest(BaseModel):
    chord: str


class SectionsRequest(BaseModel):
    sections: list[dict] = Field(default_factory=list)

WEB_DIR = Path("web")
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="UI has not been built yet.")
    return FileResponse(index_path)


@app.get("/api/jobs")
def list_jobs() -> list[dict]:
    settings = Settings.from_env()
    if not settings.jobs_dir.exists():
        return []

    jobs = []
    for manifest_path in sorted(settings.jobs_dir.glob("*/manifest.json"), reverse=True):
        try:
            manifest = read_manifest(manifest_path.parent)
        except Exception:
            continue
        jobs.append(
            {
                "job_id": manifest.job_id,
                "filename": manifest.input.filename,
                "status": manifest.status,
                "updated_at": manifest.updated_at,
                "stems": [stem.model_dump(mode="json") for stem in manifest.stems],
            }
        )
    return jobs


@app.post("/api/splits")
def start_split(file: UploadFile = File(...)) -> dict:
    settings = Settings.from_env()
    settings.inbox_dir.mkdir(parents=True, exist_ok=True)
    upload_path = settings.inbox_dir / Path(file.filename or "upload.mp3").name

    with upload_path.open("wb") as handle:
        handle.write(file.file.read())

    job_id = make_job_id(upload_path)
    task = SplitTask(
        task_id=job_id,
        filename=Path(file.filename or upload_path.name).name,
        job_id=job_id,
    )
    with split_tasks_lock:
        split_tasks[task.task_id] = task

    thread = Thread(target=_run_split_task, args=(task.task_id, upload_path, settings), daemon=True)
    thread.start()
    return _task_payload(task)


@app.get("/api/splits/{task_id}")
def get_split_status(task_id: str) -> dict:
    task = _get_split_task(task_id)
    return _task_payload(task)


@app.get("/api/song-info")
def get_song_info(filename: str) -> dict:
    parsed = _parse_song_filename(filename)
    query = " ".join(part for part in (parsed["title"], parsed["artist"], "song") if part).strip()
    if not query:
        return _offline_song_info(parsed, "Song details will appear here when the file name has enough clues.")
    try:
        return _fetch_wikipedia_song_info(query, parsed)
    except Exception:
        return _offline_song_info(parsed, "Internet lookup is unavailable right now, but the split is still running normally.")


@app.post("/api/splits/{task_id}/cancel")
def cancel_split(task_id: str) -> dict:
    task = _get_split_task(task_id)
    if task.state in {"done", "failed", "cancelled"}:
        return _task_payload(task)
    task.cancel_event.set()
    task.state = "cancelled"
    task.message = "Cancelling split..."
    task.progress = min(task.progress, 95)
    return _task_payload(task)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    settings = Settings.from_env()
    manifest = _load_job_manifest(settings, job_id)
    return manifest.model_dump(mode="json")


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str) -> dict:
    settings = Settings.from_env()
    job_dir = _resolve_job_dir(settings, job_id)
    shutil.rmtree(job_dir)
    return {"deleted": True, "job_id": job_id}


@app.get("/api/jobs/{job_id}/chords")
def get_job_chords(job_id: str) -> dict:
    settings = Settings.from_env()
    job_dir = _resolve_job_dir(settings, job_id)
    try:
        return read_chord_analysis(job_dir)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Chord analysis not found.") from None


@app.post("/api/jobs/{job_id}/chords")
def create_job_chords(job_id: str) -> dict:
    settings = Settings.from_env()
    job_dir = _resolve_job_dir(settings, job_id)
    try:
        return analyze_job_chords(job_dir)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/jobs/{job_id}/audio/{collection}/{filename}")
def get_job_audio(job_id: str, collection: str, filename: str) -> FileResponse:
    if collection not in {"stems", "stems_raw", "stems_focus", "stems_rebuild"}:
        raise HTTPException(status_code=404, detail="Unknown audio collection.")
    if "/" in filename or not filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="Invalid audio filename.")

    settings = Settings.from_env()
    job_dir = _resolve_job_dir(settings, job_id)
    audio_path = job_dir / collection / filename
    if collection in {"stems_focus", "stems_rebuild"} and not audio_path.exists():
        audio_path = job_dir / "stems" / filename
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return FileResponse(audio_path, media_type="audio/wav")


@app.post("/api/jobs/{job_id}/exports/hd-mix")
def create_hd_mix(job_id: str, request: HdMixRequest) -> dict:
    settings = Settings.from_env()
    job_dir = _resolve_job_dir(settings, job_id)
    output_path = _render_stems_zip(job_dir) if request.preset == "stems_zip" else _render_hd_mix(job_dir, request)
    return {
        "filename": output_path.name,
        "url": f"/api/jobs/{job_id}/exports/{output_path.name}",
    }


@app.get("/api/jobs/{job_id}/exports/{filename}")
def get_job_export(job_id: str, filename: str) -> FileResponse:
    if "/" in filename or not filename.endswith((".wav", ".mp3", ".zip")):
        raise HTTPException(status_code=400, detail="Invalid export filename.")
    settings = Settings.from_env()
    job_dir = _resolve_job_dir(settings, job_id)
    export_path = job_dir / "exports" / filename
    if not export_path.exists():
        raise HTTPException(status_code=404, detail="Export not found.")
    media_type = "application/zip" if filename.endswith(".zip") else "audio/mpeg" if filename.endswith(".mp3") else "audio/wav"
    return FileResponse(export_path, media_type=media_type, filename=filename)


@app.get("/api/jobs/{job_id}/mix-settings")
def get_mix_settings(job_id: str) -> dict:
    settings = Settings.from_env()
    job_dir = _resolve_job_dir(settings, job_id)
    path = job_dir / "analysis" / "mix_settings.json"
    if not path.exists():
        return {"settings": {}}
    import json

    return {"settings": json.loads(path.read_text(encoding="utf-8"))}


@app.put("/api/jobs/{job_id}/mix-settings")
def save_mix_settings(job_id: str, request: MixSettingsRequest) -> dict:
    settings = Settings.from_env()
    job_dir = _resolve_job_dir(settings, job_id)
    path = job_dir / "analysis" / "mix_settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    import json

    path.write_text(json.dumps(request.settings, indent=2), encoding="utf-8")
    return {"saved": True}


@app.patch("/api/jobs/{job_id}/chords/{index}")
def update_chord_segment(job_id: str, index: int, request: ChordUpdateRequest) -> dict:
    settings = Settings.from_env()
    job_dir = _resolve_job_dir(settings, job_id)
    analysis = read_chord_analysis(job_dir)
    segments = analysis.get("segments") or []
    if index < 0 or index >= len(segments):
        raise HTTPException(status_code=404, detail="Chord segment not found.")
    segments[index]["chord"] = request.chord.strip() or segments[index].get("chord", "~")
    analysis["segments"] = segments
    analysis.setdefault("notes", []).append("Contains manual chord corrections.")
    analysis_dir = job_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    import json

    (analysis_dir / "chords.json").write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    return analysis


@app.get("/api/jobs/{job_id}/sections")
def get_sections(job_id: str) -> dict:
    settings = Settings.from_env()
    job_dir = _resolve_job_dir(settings, job_id)
    path = job_dir / "analysis" / "sections.json"
    if not path.exists():
        return {"sections": []}
    import json

    return {"sections": json.loads(path.read_text(encoding="utf-8"))}


@app.put("/api/jobs/{job_id}/sections")
def save_sections(job_id: str, request: SectionsRequest) -> dict:
    settings = Settings.from_env()
    job_dir = _resolve_job_dir(settings, job_id)
    path = job_dir / "analysis" / "sections.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    import json

    path.write_text(json.dumps(request.sections, indent=2), encoding="utf-8")
    return {"saved": True, "sections": request.sections}


@app.post("/jobs")
def create_job(file: UploadFile = File(...), engine: str = "none") -> dict:
    settings = Settings.from_env()
    settings.inbox_dir.mkdir(parents=True, exist_ok=True)
    upload_path = settings.inbox_dir / Path(file.filename or "upload.mp3").name

    with upload_path.open("wb") as handle:
        handle.write(file.file.read())

    try:
        manifest = process_file(upload_path, settings=settings, engine=engine)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return manifest.model_dump(mode="json")


def _run_split_task(task_id: str, upload_path: Path, settings: Settings) -> None:
    task = _get_split_task(task_id)

    def progress(percent: int, message: str) -> None:
        task.progress = max(task.progress, min(percent, 98))
        task.message = message
        _update_split_stage_estimate(task, settings)

    try:
        task.state = "running"
        task.progress = 5
        task.message = "Preparing song..."
        task.stage = "preparing"
        task.stage_started_at = time.monotonic()
        manifest = process_file(
            upload_path,
            settings=settings,
            engine="demucs",
            requested_job_id=task.job_id,
            progress_callback=progress,
            cancel_event=task.cancel_event,
        )
        if task.cancel_event.is_set():
            raise SplitCancelled("Split was cancelled.")
        task.progress = 88
        task.message = "Detecting chords and tempo..."
        task.stage = "chords"
        task.stage_started_at = time.monotonic()
        task.estimated_stage_seconds = None
        analyze_job_chords(settings.jobs_dir / manifest.job_id)
        task.state = "done"
        task.progress = 100
        task.message = "Split complete."
        task.stage = "done"
        task.job_id = manifest.job_id
    except SplitCancelled as exc:
        task.state = "cancelled"
        task.message = "Split cancelled."
        task.error = str(exc)
        _mark_manifest_status(settings, task.job_id, "cancelled", str(exc))
    except Exception as exc:
        task.state = "failed"
        task.message = "Split failed."
        task.error = str(exc)
        _mark_manifest_status(settings, task.job_id, "failed", str(exc))


def _mark_manifest_status(settings: Settings, job_id: str | None, status: str, warning: str) -> None:
    if not job_id:
        return
    job_dir = settings.jobs_dir / job_id
    try:
        manifest = read_manifest(job_dir)
    except Exception:
        return
    manifest.status = status
    manifest.updated_at = utc_now()
    manifest.warnings.append(warning)
    write_manifest(job_dir, manifest)


def _parse_song_filename(filename: str) -> dict[str, str]:
    stem = Path(filename or "").stem
    cleaned = re.sub(r"[_]+", " ", stem)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(
        r"\s*[\[(](official audio|official video|audio|video|lyrics?|remaster(?:ed)?|hd|hq)[\])]\s*",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -")
    artist = ""
    title = cleaned
    if " - " in cleaned:
        artist, title = [part.strip() for part in cleaned.split(" - ", 1)]
    return {"artist": artist, "title": title, "display": cleaned}


def _fetch_wikipedia_song_info(query: str, parsed: dict[str, str]) -> dict:
    params = urlencode(
        {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": "1",
            "prop": "extracts|pageimages|info",
            "exintro": "1",
            "explaintext": "1",
            "pithumbsize": "420",
            "inprop": "url",
            "format": "json",
        }
    )
    request = Request(
        f"https://en.wikipedia.org/w/api.php?{params}",
        headers={"User-Agent": "WannabeStem/0.1 local rehearsal app"},
    )
    with urlopen(request, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    pages = payload.get("query", {}).get("pages", {})
    if not pages:
        return _offline_song_info(parsed, "No artist/song article was found from the file name.")
    page = next(iter(pages.values()))
    extract = _short_extract(str(page.get("extract") or ""))
    return {
        "online": True,
        "source": "Wikipedia",
        "artist": parsed["artist"],
        "title": parsed["title"] or str(page.get("title") or parsed["display"]),
        "heading": str(page.get("title") or parsed["display"] or "Song notes"),
        "summary": extract or "Found a matching article, but it did not include a short summary.",
        "url": page.get("fullurl"),
        "image_url": page.get("thumbnail", {}).get("source"),
    }


def _short_extract(extract: str) -> str:
    extract = re.sub(r"\s+", " ", extract).strip()
    if len(extract) <= 420:
        return extract
    sentence_match = re.match(r"^(.{180,420}?[.!?])\s", extract)
    if sentence_match:
        return sentence_match.group(1)
    return f"{extract[:417].rstrip()}..."


def _offline_song_info(parsed: dict[str, str], summary: str) -> dict:
    return {
        "online": False,
        "source": "Local",
        "artist": parsed["artist"],
        "title": parsed["title"],
        "heading": parsed["display"] or "Song notes",
        "summary": summary,
        "url": None,
        "image_url": None,
    }


def _update_split_stage_estimate(task: SplitTask, settings: Settings) -> None:
    if "Demucs" not in task.message:
        if task.stage != "postprocess" and task.progress >= 82:
            task.stage = "postprocess"
            task.stage_started_at = time.monotonic()
            task.estimated_stage_seconds = None
        return

    if task.stage == "demucs":
        return

    task.stage = "demucs"
    task.stage_started_at = time.monotonic()
    task.estimated_stage_seconds = _estimate_demucs_seconds(settings, task.job_id)


def _estimate_demucs_seconds(settings: Settings, job_id: str | None) -> float:
    if not job_id:
        return 240.0
    normalized_path = settings.jobs_dir / job_id / "working" / "normalized.wav"
    duration = _audio_duration_seconds(normalized_path)
    if duration <= 0:
        return 240.0

    # On local Docker CPU runs, htdemucs_6s often lands around 0.7-1.0x song length.
    # Keep the estimate slightly conservative so the bar does not hit 82% too early.
    return max(120.0, min(900.0, duration * 0.9 + 45.0))


def _audio_duration_seconds(path: Path) -> float:
    if not path.exists():
        return 0.0
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return float(result.stdout.strip() or 0.0)
    except Exception:
        return 0.0


def _render_hd_mix(job_dir: Path, request: HdMixRequest) -> Path:
    track_files = _mix_track_files(job_dir)
    inputs: list[tuple[str, Path, MixTrackSettings]] = []
    for track_name, path in track_files.items():
        if not path.exists():
            continue
        track_settings = request.tracks.get(track_name, MixTrackSettings())
        if request.preset == "minus_vocals" and track_name in {"main_vocal", "backing_vocal"}:
            track_settings.muted = True
        elif request.preset == "minus_guitar" and track_name == "guitar":
            track_settings.muted = True
        elif request.preset == "minus_guitar" and track_name == "acoustic_guitar":
            track_settings.muted = True
        elif request.preset == "minus_keys" and track_name == "keys":
            track_settings.muted = True
        if track_settings.muted or track_settings.volume <= 0:
            continue
        inputs.append((track_name, path, track_settings))

    if not inputs:
        raise HTTPException(status_code=400, detail="No audible tracks available for HD mix.")

    exports_dir = job_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"{request.preset}_{request.semitones:+d}st"
    output_path = exports_dir / (f"hd_mix_{suffix}.mp3" if request.format == "mp3" else f"hd_mix_{suffix}_48k_24bit.wav")

    command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for _, path, _ in inputs:
        command.extend(["-i", str(path)])

    chains = []
    labels = []
    for index, (_, _, settings) in enumerate(inputs):
        label = f"a{index}"
        labels.append(f"[{label}]")
        filters = [
            "highpass=f=20",
            "lowpass=f=20000",
            f"equalizer=f=120:t=q:w=0.7:g={settings.low}",
            f"equalizer=f=1100:t=q:w=0.95:g={settings.mid}",
            f"equalizer=f=6200:t=q:w=0.7:g={settings.high}",
        ]
        if settings.reverb > 50:
            decay = round(min(0.72, max(0.0, (settings.reverb - 50) / 50 * 0.72)), 3)
            filters.append(f"aecho=0.82:0.88:55|118:{decay}|{round(decay * 0.68, 3)}")
        if settings.compression > 50:
            amount = min(1.0, max(0.0, (settings.compression - 50) / 50))
            threshold = round(0.18 - amount * 0.12, 3)
            ratio = round(2 + amount * 6, 2)
            filters.append(f"acompressor=threshold={threshold}:ratio={ratio}:attack=8:release=140:makeup=1")
        filters.append(f"volume={settings.volume}")
        if request.semitones:
            filters.extend(_pitch_shift_filters(request.semitones))
        chains.append(f"[{index}:a]{','.join(filters)}[{label}]")

    master_filters = [
        f"{''.join(labels)}amix=inputs={len(inputs)}:duration=longest:normalize=0"
    ]
    if request.hd_master:
        master_filters.extend(
            [
                "dynaudnorm=f=150:g=9:p=0.45",
                "loudnorm=I=-14:TP=-1.2:LRA=11",
                "alimiter=limit=0.98",
            ]
        )
    else:
        master_filters.append("alimiter=limit=0.98")
    master_filters.append("aresample=48000")
    chains.append(f"{','.join(master_filters)}[out]")

    command.extend(
        [
            "-filter_complex",
            ";".join(chains),
            "-map",
            "[out]",
        ]
    )
    if request.format == "mp3":
        command.extend(["-ar", "48000", "-codec:a", "libmp3lame", "-b:a", "320k", str(output_path)])
    else:
        command.extend(["-ar", "48000", "-c:a", "pcm_s24le", str(output_path)])
    subprocess.run(command, check=True)
    return output_path


def _pitch_shift_filters(semitones: int) -> list[str]:
    ratio = 2 ** (semitones / 12)
    tempo = 1 / ratio
    filters = [f"asetrate=48000*{ratio}", "aresample=48000"]
    if tempo < 0.5:
        filters.extend(["atempo=0.5", f"atempo={tempo / 0.5}"])
    elif tempo > 2:
        filters.extend(["atempo=2", f"atempo={tempo / 2}"])
    else:
        filters.append(f"atempo={tempo}")
    return filters


def _render_stems_zip(job_dir: Path) -> Path:
    exports_dir = job_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    output_path = exports_dir / "weekend_stems_tracks.zip"
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for track_name, path in _mix_track_files(job_dir).items():
            if path.exists():
                archive.write(path, arcname=f"{track_name}.wav")
    return output_path


def _mix_track_files(job_dir: Path) -> dict[str, Path]:
    return {
        "main_vocal": job_dir / "stems" / "main_vocal.wav",
        "backing_vocal": job_dir / "stems" / "backing_vocal.wav",
        "drums": job_dir / "stems" / "drums.wav",
        "bass": job_dir / "stems" / "bass.wav",
        "guitar": job_dir / "stems" / "guitar.wav",
        "acoustic_guitar": job_dir / "stems" / "acoustic_guitar.wav",
        "keys": _preferred_keys_path(job_dir),
        "other": job_dir / "stems" / "other.wav",
    }


def _preferred_keys_path(job_dir: Path) -> Path:
    rebuilt = job_dir / "stems_rebuild" / "keys.wav"
    return rebuilt if rebuilt.exists() else job_dir / "stems" / "keys.wav"


def _get_split_task(task_id: str) -> SplitTask:
    with split_tasks_lock:
        task = split_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Split task not found.")
    return task


def _task_payload(task: SplitTask) -> dict:
    progress, estimated, eta_seconds = _display_split_progress(task)
    return {
        "task_id": task.task_id,
        "job_id": task.job_id,
        "filename": task.filename,
        "state": task.state,
        "progress": progress,
        "actual_progress": task.progress,
        "progress_estimated": estimated,
        "eta_seconds": eta_seconds,
        "message": task.message,
        "error": task.error,
    }


def _display_split_progress(task: SplitTask) -> tuple[int, bool, int | None]:
    if (
        task.state != "running"
        or task.stage != "demucs"
        or task.stage_started_at is None
        or not task.estimated_stage_seconds
    ):
        return task.progress, False, None

    elapsed = max(0.0, time.monotonic() - task.stage_started_at)
    stage_ratio = min(0.985, elapsed / max(1.0, task.estimated_stage_seconds))
    estimated_progress = int(round(35 + stage_ratio * 47))
    progress = max(task.progress, min(81, estimated_progress))
    eta = max(0, int(round(task.estimated_stage_seconds - elapsed)))
    return progress, True, eta


def _resolve_job_dir(settings: Settings, job_id: str) -> Path:
    jobs_root = settings.jobs_dir.resolve()
    job_dir = (settings.jobs_dir / job_id).resolve()
    if jobs_root not in job_dir.parents:
        raise HTTPException(status_code=400, detail="Invalid job id.")
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job not found.")
    return job_dir


def _load_job_manifest(settings: Settings, job_id: str):
    return read_manifest(_resolve_job_dir(settings, job_id))
