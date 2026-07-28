# Wannabe Stem Agent

## Mission

Build Wannabe Stem: a local-first music practice system for Wannabe Weekenders. A non-technical bandmate should be able to run it with Docker, open a browser, upload a song, split it into useful tracks, and practice with chords, loops, tempo, key, and mix controls.

The product is Moises-like in spirit, but intentionally local and band-rehearsal focused. Nothing should require uploading a song to a cloud service.

## Current Product Direction

Wannabe Stem should prioritize dependable, musician-useful tracks over speculative over-separation. Earlier experiments with Guitar 1/Guitar 2 and Keys 1/Keys 2 caused bleed and mushy results, so the current user-facing track list is:

- Main Vocal
- Backing Vocal
- Drums
- Bass
- Guitar
- Acoustic Guitar
- Keys
- Other

`Other` is important. It should catch sax, accordion, strings, synths, extra percussion, and anything not reliably represented by the named tracks.

## Stem Quality Strategy

Use local Demucs-style separation as the baseline and keep instrument-specific cleanup modules separate:

- Bass: clean low-end, reduce low-mid mud, preserve focus.
- Guitar: one cleaned guitar stem is preferred over unreliable lead/rhythm splits.
- Acoustic Guitar: separate module derived from raw guitar plus harmonic content from other, for acoustic-heavy songs where strumming is not captured in Guitar.
- Keys: use the rebuilt keys path when available, with guitar bleed suppression.
- Backing Vocal: estimated from the vocal stem and clearly labeled as lower confidence.
- Other: keep the model catch-all available and audible.

Treat all derived stems as confidence-scored outputs. Do not pretend a heuristic split is ground truth.

## Local Architecture

The system is a Dockerized local app with a FastAPI backend, static browser UI, and CLI worker commands.

Pipeline:

1. Ingest: accept MP3/WAV/FLAC/M4A from browser upload.
2. Normalize: convert to stable internal WAV and capture metadata.
3. Separate: run local separation engine when built with `INSTALL_DEMUCS=true`.
4. Remap: convert raw model outputs into Wannabe Stem tracks.
5. Post-process: run instrument-specific cleanup/rebuild modules.
6. Analyze: detect chords, bars, tempo, and estimated key.
7. Review: browser mixer with synchronized playback.
8. Export: render HD mixes, key-shifted mixes, and stems ZIPs.

## UI Direction

The UI should feel like a rehearsal tool, not a marketing page. Keep the red/black Wannabe Stem theme, icon-forward instrument controls, and the four main views:

- Track View: synchronized waveform rows with mute, solo, and volume.
- Chord View: bar-based chord chart, four bars per row, current bar tracking playback.
- Song Key: detected key plus chart transposition and shifted mix rendering.
- Edit Mix: per-track EQ, reverb, compression, mute, HD master, exports, loop, and Practice Zone.

Practice tools:

- Regular Loop repeats a selected start/end range.
- Practice Zone uses the same range without looping; selected tracks mute only inside that range.
- Count-in and click should only sound during playback.
- Active ranges should be visible in green on chord bars.

## Suggested Folder Structure

```text
song_split/
├── AGENT.md
├── SKILLS.md
├── README.md
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements/
│   ├── base.txt
│   └── separation.txt
├── app/
│   ├── api/
│   │   └── main.py
│   ├── audio/
│   │   ├── chords.py
│   │   ├── ingest.py
│   │   ├── pipeline.py
│   │   ├── separate.py
│   │   └── instruments/
│   │       ├── bass.py
│   │       ├── bleed.py
│   │       ├── common.py
│   │       ├── drums.py
│   │       ├── guitar.py
│   │       ├── keys.py
│   │       └── other.py
│   ├── cli.py
│   └── core/
│       ├── config.py
│       ├── jobs.py
│       ├── manifests.py
│       └── paths.py
├── web/
│   ├── index.html
│   └── static/
│       ├── app.js
│       └── styles.css
└── data/
    ├── inbox/
    ├── jobs/
    └── models/
```

## Data Layout

Each processed song gets one job folder:

```text
data/jobs/<job_id>/
├── input/
│   └── original.<ext>
├── working/
│   └── normalized.wav
├── analysis/
│   ├── chords.json
│   └── mix_settings.json
├── stems/
│   ├── main_vocal.wav
│   ├── backing_vocal.wav
│   ├── drums.wav
│   ├── bass.wav
│   ├── guitar.wav
│   ├── acoustic_guitar.wav
│   ├── keys.wav
│   └── other.wav
├── stems_raw/
├── stems_focus/
├── stems_rebuild/
├── exports/
└── manifest.json
```

The manifest should record input filename, duration, sample rate, model name/version, processing settings, generated stems, confidence/status per target stem, and warnings.

## Implementation Principles

- Keep all audio local by default.
- Prefer Docker-first workflows for non-technical users.
- Never overwrite source uploads.
- Make long-running jobs visible, cancellable, and recoverable.
- Track model/version/settings in manifests for reproducibility.
- Prefer WAV internally; export MP3 only as a delivery option.
- Keep stems synchronized by duration and playback position.
- Favor one reliable musician-useful track over multiple confusing approximations.
- Keep experimental model work separate from the stable app path.

## Current Milestones

Completed or in progress:

1. Dockerized local API and worker.
2. Browser upload and split workflow with progress/cancel.
3. Core stem mapping: Main Vocal, Backing Vocal, Drums, Bass, Guitar, Keys, Other.
4. Instrument-specific cleanup modules for bass, guitar, acoustic guitar, keys, drums, and other.
5. Chord, tempo, bar, and key analysis.
6. Track View, Chord View, Song Key, and Edit Mix UI.
7. Regular Loop and Practice Zone.
8. HD mix and export presets.

Next likely areas:

1. Improve keys quality with a dedicated model or stronger reconstruction path.
2. Make install/start friendlier for non-technical bandmates.
3. Add more repeatable audio quality test clips and comparison notes.
