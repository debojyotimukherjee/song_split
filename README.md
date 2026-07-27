# Weekend Stems

Turn a song into separate tracks you can mute, solo, mix, and slow down for practice — vocals, drums, bass, guitar, keys, and more. Built for band rehearsal prep, runs entirely on your own machine (nothing is uploaded anywhere), and is driven by Docker so there's nothing else to install.

## What you get

Drop in an MP3 (or WAV/FLAC/M4A), and Weekend Stems splits it into:

| Track | What it is |
|---|---|
| Main Vocal | Lead vocal |
| Backing Vocal | Harmonies/doubles, estimated from the vocal track |
| Drums | Full drum kit |
| Bass | Bass guitar |
| Guitar | All guitars, cleaned up |
| Keys | Piano/keys, with bleed from other instruments suppressed |
| Other | Everything else (sax, strings, synths, etc.) |

It also detects chords, tempo, and the song's key, and lets you change the playback pitch to a different key or slow the whole song down without changing pitch — handy for learning a part before rehearsal.

Every track is labeled as **generated** (directly from the separation model) or **estimated** (derived/approximated, lower confidence) so you always know how much to trust what you're hearing.

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- A few GB of free disk space (the separation model and audio files add up).
- Internet access the first time you run it, to download the separation model (a few hundred MB, one-time — cached locally after that).

## Quick start

Open a terminal in this folder and run:

```bash
INSTALL_DEMUCS=true docker compose build
INSTALL_DEMUCS=true docker compose up api
```

Then open **http://localhost:8000** in your browser. Upload a song, hit **Split Tracks**, and wait — the first split is slower because it's downloading the model; after that it's much quicker.

To stop the app, press `Ctrl+C` in that terminal, or run `docker compose down` from another one.

> `INSTALL_DEMUCS=true` builds the full image with the separation engine. Leaving it off (`docker compose build` / `docker compose up api`) builds a lighter image that can ingest and normalize audio but can't actually separate tracks — mainly useful for quickly checking the app boots.

## Using the app

- **Songs** (left sidebar): pick a previously processed song, or upload a new one and click **Split Tracks**. **Upload only** just stores the file without processing it.
- **Track view**: each stem gets its own row with mute, solo, and volume. Bass, Guitar, and Keys have a mode switch (e.g. Clean vs Raw) if you want to compare the cleaned-up track against the model's untouched output.
- **Chord view / Song Key**: shows detected chords and lets you transpose the on-screen chart to a different key without changing the audio.
- **Tempo slider**: play the song slower for practice, without changing pitch.
- **Remove Song**: deletes a processed song and all its files.

## Where your files go

Everything lives in the `data/` folder next to this README, on your own disk — nothing leaves your machine:

```text
data/
├── inbox/    uploaded source files
├── jobs/     one folder per processed song (stems, exports, manifest.json)
└── models/   cached separation model (downloaded once)
```

## Command line (optional)

For running things outside the browser, e.g. batch-processing files:

```bash
# Separate a file into stems
INSTALL_DEMUCS=true docker compose run --rm worker separate data/inbox/your-song.mp3 --engine demucs

# Re-run track cleanup on an already-separated song (no need to re-run the model)
INSTALL_DEMUCS=true docker compose run --rm worker remap data/jobs/<job_id>

# Re-run chord/key/tempo detection on an already-separated song
INSTALL_DEMUCS=true docker compose run --rm worker analyze-chords data/jobs/<job_id>
```

## Troubleshooting

**Something's misbehaving and you want a clean slate:**

```bash
docker compose down
rm -rf data/inbox/* data/jobs/* data/models/*
INSTALL_DEMUCS=true docker compose build --no-cache
INSTALL_DEMUCS=true docker compose up api
```

This clears all processed songs and the cached model (it'll re-download on the next split) and rebuilds the image from scratch.

**"Demucs is not installed in this container"** — you built or ran without `INSTALL_DEMUCS=true`. Rebuild with it set.

**Port 8000 already in use** — something else on your machine is using that port. Stop it, or edit the `ports:` line in `docker-compose.yml` to map a different port (e.g. `"8080:8000"`), then open that port in your browser instead.

**Code changes not showing up** — the app's code is baked into the Docker image, not live-reloaded. After changing anything under `app/` or `web/`, rebuild with `docker compose build` before restarting.
