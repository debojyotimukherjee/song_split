# Weekend Stems

Local-first music stem separation for Wannabe Weekenders rehearsals, designed to grow into a Moises-like mixer interface.

## Current Shape

- `data/inbox/`: input files dropped in for processing.
- `data/jobs/`: generated job folders, normalized audio, stems, exports, and manifests.
- `data/models/`: model cache/downloads.
- `app/`: Python backend, CLI, and processing pipeline.

## Docker Quick Start

Build the light image, without Demucs:

```bash
docker compose build
```

Run ingest/normalization against the sample MP3:

```bash
docker compose run --rm worker separate data/inbox/sample-500kb.mp3 --engine none
```

Build with Demucs installed:

```bash
INSTALL_DEMUCS=true docker compose build
```

Run separation with Demucs:

```bash
INSTALL_DEMUCS=true docker compose run --rm worker separate data/inbox/sample-500kb.mp3 --engine demucs
```

Rebuild product stems from an existing Demucs job, including estimated Guitar 1/2 and Keys 1/2 pan splits:

```bash
INSTALL_DEMUCS=true docker compose run --rm worker remap data/jobs/<job_id>
```

Start the API:

```bash
docker compose up api
```

Open the local Weekend Stems UI:

```text
http://localhost:8000
```

Generated files appear locally under:

```text
data/jobs/<job_id>/
```
