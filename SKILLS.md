# Project Skills

This file defines the working skills the Weekend Stems agent should use while building the local stem separation system. It is a project-level operating guide, not a packaged Codex skill.

## 1. Audio Ingestion

Use when adding or changing file upload, watched-folder import, metadata extraction, or format conversion.

Responsibilities:

- Accept MP3 first, then WAV/FLAC/M4A.
- Preserve the original file unchanged.
- Convert input to a normalized WAV for processing.
- Capture duration, sample rate, channel count, loudness, and file hash.
- Reject unsupported or corrupt files with actionable errors.

Done when:

- A dropped MP3 creates a job folder.
- `manifest.json` contains input metadata.
- The normalized WAV is aligned with the source duration.

## 2. Source Separation

Use when integrating or changing the model runner.

Responsibilities:

- Provide a stable interface for model backends.
- Start with one dependable local model path.
- Keep model downloads/cache under `data/models/`.
- Write raw model stems before any product-level remapping.
- Report progress and errors clearly.

Done when:

- One command can process a normalized WAV into core stems.
- The runner records model name, version, device, settings, and elapsed time.
- Failed jobs can be retried without re-uploading the source.

## 3. Stem Mapping

Use when translating model-native stems into the product's target tracks.

Responsibilities:

- Map native stems to Main Vocal, Backing Vocal, Drums, Bass, Guitar 1, Guitar 2, Keys 1, Keys 2, and Other.
- Mark estimated or placeholder stems with status and confidence.
- Keep stems time-aligned and equal length.
- Avoid pretending advanced separations are more precise than they are.

Done when:

- Every target track has a manifest entry.
- Missing or estimated tracks are visible in metadata.
- The UI can distinguish generated, estimated, and unavailable stems.

## 4. Audio Post-Processing

Use when improving generated audio quality or export consistency.

Responsibilities:

- Trim or pad stems to exact duration.
- Prevent clipping.
- Optionally loudness-normalize previews and exports.
- Detect near-silent stems.
- Build instrumental or custom mixes from selected stems.

Done when:

- Stems start together and stay synchronized.
- Exports do not clip unexpectedly.
- Silence or low-confidence outputs are labeled.

## 5. Job Orchestration

Use when building the processing queue, status updates, retries, cancellation, or cleanup.

Responsibilities:

- Represent each song as a durable job.
- Keep state transitions explicit.
- Support progress events for long-running separation.
- Make cleanup safe and intentional.
- Keep logs tied to job IDs.

Done when:

- The app can recover job state after restart.
- Users can see queued/running/failed/complete states.
- A failed processing step gives enough detail to debug.

## 6. Mixer UI

Use when building the browser or desktop interface.

Responsibilities:

- Provide drag-and-drop import.
- Show job progress.
- Display synchronized stem lanes.
- Support play/pause/seek, mute, solo, volume, and export.
- Make unavailable or estimated stems visually clear.

Done when:

- All audible stems start in sync.
- Mute/solo/volume works without breaking transport.
- Users can export individual stems or a zip.

## 7. Quality Evaluation

Use when validating model output or comparing separation approaches.

Responsibilities:

- Maintain short test clips that are legal to use.
- Compare runtime, artifacts, bleed, and stem usefulness.
- Track model settings in repeatable notes.
- Prefer musician-useful evaluation over only numeric metrics.

Done when:

- Each model experiment has input, settings, outputs, and notes.
- Regressions can be spotted with a small repeatable test set.

## 8. Research Discipline

Use when adding new models, dependencies, or algorithms.

Responsibilities:

- Prefer maintained libraries and model formats that can run locally.
- Verify licensing before bundling models or sample audio.
- Keep experimental code separate from the stable runner.
- Record why a model was accepted, rejected, or deferred.

Done when:

- The stable path stays simple.
- Experiments do not break MVP workflows.
- Licensing and model source are documented before release.
