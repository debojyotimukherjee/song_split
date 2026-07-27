# Weekend Stems Agent

## Mission

Build Weekend Stems: a local-first music stem separation system for Wannabe Weekenders. A user should be able to drop an MP3 file into the app, wait for processing, and receive synchronized audio tracks that can be played, muted, soloed, mixed, and exported.

The product direction is similar to Moises in spirit, but scoped first as a local desktop/web app for personal music practice, transcription, rehearsal, remix sketching, and arrangement study.

## Target Stems

Desired user-facing tracks:

- Main Vocal
- Backing Vocal
- Drums
- Bass
- Guitar 1
- Guitar 2
- Keys 1
- Keys 2
- Other

Important modeling note: most mature local open-source music source separation models natively produce 4 to 6 stems, commonly vocals, drums, bass, guitar, piano/keys, and other. The named target tracks should be treated as a product goal reached in stages:

1. MVP: produce reliable core stems.
2. Expansion: split guitar/piano/keys further when confidence is high.
3. Advanced: separate main vs backing vocals and Guitar 1 vs Guitar 2 using specialized models, heuristics, or user-assisted labeling.

## Recommended MVP

Start with six internal stems:

- vocals
- drums
- bass
- guitar
- keys or piano
- other

Then expose the desired eight-track layout with clear fallbacks:

- Main Vocal: generated from vocals, later refined with lead-vocal separation.
- Backing Vocal: estimated from vocals with a side/wide extraction in the MVP; later refined with lead/backing vocal separation.
- Drums: generated directly.
- Bass: generated directly.
- Guitar 1: generated from guitar.
- Guitar 2: optional duplicate/refinement lane in MVP; later split by timbre/pan/frequency.
- Keys 1: generated from piano/keys.
- Keys 2: optional duplicate/refinement lane in MVP; later split by timbre/pan/frequency.
- Other: generated from the model's catch-all `other` stem for sax, accordion, percussion, strings, synths, and anything not captured by named tracks.

## Local Architecture

The system should be designed as a pipeline:

1. Ingest: accept MP3/WAV/FLAC/M4A from a watched folder or browser drop zone.
2. Normalize: convert to a stable internal WAV format, preserve original metadata, and calculate duration/sample rate/channels.
3. Separate: run a local source-separation engine.
4. Post-process: loudness normalize, trim/pad stems to exact alignment, detect silence, and write metadata.
5. Package: create per-stem WAV/MP3 exports and a project manifest.
6. Review: provide a mixer UI for playback, mute/solo, volume, waveform preview, and export.

## Model Strategy

Use a pluggable model runner so the project can swap engines without rewriting the app.

Initial candidates:

- Demucs `htdemucs_6s`: good first baseline for local six-stem separation.
- ONNX-based Demucs exports: useful for packaging and avoiding a full PyTorch runtime.
- UVR-style model ensembles: useful later for higher-quality vocals and backing-vocal experiments.

Keep the first version boring and dependable: one model runner, one queue, one output format, predictable job folders.

## Suggested Folder Structure

```text
song_split/
├── AGENT.md
├── SKILLS.md
├── README.md
├── pyproject.toml
├── .env.example
├── app/
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/
│   │   └── schemas/
│   ├── core/
│   │   ├── config.py
│   │   ├── jobs.py
│   │   ├── manifests.py
│   │   └── paths.py
│   ├── audio/
│   │   ├── ingest.py
│   │   ├── normalize.py
│   │   ├── separate.py
│   │   ├── postprocess.py
│   │   └── export.py
│   ├── models/
│   │   ├── base.py
│   │   ├── demucs_runner.py
│   │   └── onnx_runner.py
│   └── workers/
│       └── queue.py
├── web/
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── audio/
│   │   └── styles/
│   └── public/
├── data/
│   ├── inbox/
│   ├── jobs/
│   ├── models/
│   └── exports/
├── scripts/
│   ├── dev_backend.sh
│   ├── dev_frontend.sh
│   └── smoke_test_separation.sh
├── tests/
│   ├── unit/
│   └── integration/
└── docs/
    ├── architecture.md
    ├── stem-taxonomy.md
    └── model-notes.md
```

## Data Layout

Each processed song should get one job folder:

```text
data/jobs/<job_id>/
├── input/
│   └── original.mp3
├── working/
│   └── normalized.wav
├── stems/
│   ├── main_vocal.wav
│   ├── backing_vocal.wav
│   ├── drums.wav
│   ├── bass.wav
│   ├── guitar.wav
│   ├── keys.wav
│   └── other.wav
├── exports/
│   ├── stems.zip
│   └── mix.wav
└── manifest.json
```

The manifest should record input filename, duration, sample rate, model name/version, processing settings, generated stems, confidence/status per target stem, and any warnings.

## Implementation Principles

- Keep all audio local by default.
- Never overwrite source uploads.
- Make every processing step resumable.
- Track model/version/settings in the manifest for reproducibility.
- Prefer WAV internally; export MP3 only as a delivery option.
- Design for long-running jobs with progress events.
- Treat advanced stems as confidence-scored outputs, not guaranteed truth.

## First Build Milestones

1. CLI proof of concept: separate one MP3 into six stems.
2. Job manifest: persist job status and output paths.
3. Local API: upload/drop file and poll processing status.
4. Mixer UI: play stems in sync with mute/solo/volume.
5. Export: download individual stems and zip.
6. Advanced splitting experiments: main/backing vocal, guitar 1/2, keys 1/2.
