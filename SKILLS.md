# Project Skills

This file defines the working skills the Wannabe Stem agent should use while building the local stem separation and rehearsal system. It is a project-level operating guide, not a packaged Codex skill.

## 1. Docker-First Local App

Use when changing setup, dependencies, runtime commands, or packaging.

Responsibilities:

- Keep Docker as the default install path for Mac and Windows users.
- Avoid requiring users to install Python, FFmpeg, Demucs, or audio libraries directly.
- Keep `INSTALL_DEMUCS=true` documented for full separation builds.
- Make startup simple enough for non-technical bandmates.
- Preserve all audio processing locally.

Done when:

- `docker compose up api` starts the browser app.
- The README includes copy/paste commands.
- First-run model download behavior is documented.

## 2. Audio Ingestion

Use when adding or changing file upload, metadata extraction, import behavior, or format conversion.

Responsibilities:

- Accept MP3 first, plus WAV/FLAC/M4A.
- Preserve the original file unchanged.
- Convert input to normalized WAV for processing.
- Capture duration, sample rate, channel count, loudness, and source metadata.
- Reject unsupported or corrupt files with actionable errors.

Done when:

- Uploading a song creates a durable job folder.
- `manifest.json` contains input metadata.
- The normalized WAV aligns with the source duration.

## 3. Source Separation

Use when integrating or changing the model runner.

Responsibilities:

- Provide a stable interface for model backends.
- Use one dependable local separation path before adding experiments.
- Keep model downloads/cache under `data/models/`.
- Write raw model stems before product-level remapping.
- Report progress and errors clearly.
- Support cancellation for long-running splits.

Done when:

- One command can process a normalized WAV into raw model stems.
- The runner records model name, settings, device, and elapsed time.
- Failed jobs can be retried without re-uploading the source.

## 4. Stem Mapping

Use when translating model-native stems into user-facing Wannabe Stem tracks.

Responsibilities:

- Map native stems to Main Vocal, Backing Vocal, Drums, Bass, Guitar, Acoustic Guitar, Keys, and Other.
- Keep one dependable Guitar track and one dependable Keys track unless a new model proves better.
- Mark estimated or derived stems with status, confidence, and notes.
- Keep stems time-aligned and equal length.
- Avoid pretending heuristic separation is more precise than it is.

Done when:

- Every user-facing track has a manifest entry.
- Missing or estimated tracks are visible in metadata and UI.
- Raw stems remain available for debugging or future remapping.

## 5. Instrument-Specific Cleanup

Use when improving Bass, Guitar, Acoustic Guitar, Keys, Drums, Other, or vocal-derived stems.

Responsibilities:

- Keep instrument cleanup in `app/audio/instruments/`.
- Bass should reduce rumble and low-mid mud while preserving punch.
- Guitar should improve focus/presence without over-splitting into fake parts.
- Acoustic Guitar should live in its own module and may blend raw guitar with harmonic content from other for strummed/acoustic-heavy songs.
- Keys should prefer the rebuilt keys path and suppress guitar bleed where possible.
- Other should remain a useful catch-all for instruments not otherwise separated.
- Keep raw, focus, and rebuild outputs clearly named.
- `audio-separator` may be used as an experimental specialist pass, but verify model output stems first with `list-audio-separator-models`; do not assume a dedicated Guitar or Keys model exists just because the package is installed.

Done when:

- The UI plays the preferred final stem path.
- Alternate/debug stems are preserved in job folders.
- Notes explain whether a track is generated, cleaned, rebuilt, or estimated.

## 6. Chord, Tempo, and Key Analysis

Use when changing chord detection, bar layout, tempo, or transposition.

Responsibilities:

- Prefer accompaniment-aware analysis over full-mix-only detection.
- Detect chords by bar and show four bars per row.
- Support slash chords such as `D/A` when bass evidence is useful.
- Detect estimated song key and allow chart transposition.
- Preserve manual chord corrections.
- Keep audio key shifting as an explicit rendered mix, not an invisible live promise.

Done when:

- Chord View follows playback across the whole song.
- Current bar/chord updates while the song plays.
- Manual chord fixes persist.
- Transposed charts update consistently.

## 7. Job Orchestration

Use when building status updates, retries, cancellation, cleanup, or song removal.

Responsibilities:

- Represent each song as a durable job.
- Keep state transitions explicit.
- Show progress for long-running separation.
- Support canceling active splits.
- Make song deletion safe and intentional.
- Keep logs and generated files tied to job IDs.

Done when:

- The app recovers job state after restart.
- Users can see queued/running/failed/complete states.
- Removing a song deletes its local job files.

## 8. Mixer UI

Use when changing the browser interface.

Responsibilities:

- Keep the red/black Wannabe Stem visual theme.
- Prefer instrument icons and compact controls over explanatory text.
- Show synchronized stem lanes with waveform previews.
- Support play/pause/stop/seek, mute, solo, volume, and tempo.
- Keep Bass, Guitar, and Keys visually close when possible.
- Make unavailable, estimated, or generated stems clear.

Done when:

- All audible stems start in sync and stay synced.
- Mute, solo, volume, and tempo work during playback.
- The UI remains usable on laptop-sized screens.

## 9. Practice Tools

Use when changing loops, click/count-in, or section-based practice behavior.

Responsibilities:

- Regular Loop should repeat the selected start/end range.
- Practice Zone should use the selected range without looping.
- Practice Zone mutes selected tracks only while playback is inside the range.
- The full normal mix should return outside the Practice Zone.
- Active ranges should be highlighted green in Chord View.
- Count-in and click should sound only during playback.

Done when:

- Regular Loop and Practice Zone are separate selectable modes.
- Switching modes does not lose the selected range.
- Loop/mute behavior follows the same playhead on all tabs.

## 10. Edit Mix and Export

Use when changing EQ, reverb, compression, HD master, or downloads.

Responsibilities:

- Provide per-track EQ, reverb, compression, mute, preset, and flat reset controls.
- Make controls affect playback live where the browser audio graph supports it.
- Save mix settings per song.
- Render HD mix exports with selected preset and format.
- Support full mix, minus vocals, minus guitar, minus keys, and stems ZIP.
- Prevent clipping where practical.

Done when:

- Edit Mix changes are audible during playback.
- Saved settings reload with the song.
- Exported files are written under the job's `exports/` folder.

## 11. Quality Evaluation

Use when validating model output or comparing separation approaches.

Responsibilities:

- Maintain short legal test clips.
- Compare runtime, artifacts, bleed, sync, and musician usefulness.
- Track model/settings changes in repeatable notes.
- Trust listening tests and rehearsal usefulness, not only numeric metrics.

Done when:

- Each experiment has input, settings, outputs, and notes.
- Regressions can be spotted with a small repeatable test set.

## 12. Research Discipline

Use when adding new models, dependencies, or algorithms.

Responsibilities:

- Prefer maintained libraries and local model formats.
- Verify licensing before bundling models or sample audio.
- Keep experimental code separate from the stable runner.
- Record why a model was accepted, rejected, or deferred.
- Avoid adding heavyweight dependencies unless they clearly improve the rehearsal experience.

Done when:

- The stable path remains simple.
- Experiments do not break current UI workflows.
- Licensing and model source are documented before release.
