# Weekend Stems

Weekend Stems is a local rehearsal app for Wannabe Weekenders. Drop in a song, split it into playable stems, slow it down, follow chords by bar, transpose the chart, loop hard sections, and build practice mixes without uploading your music anywhere.

## Docker Installation

Weekend Stems runs with Docker so bandmates do not need to install Python, FFmpeg, Demucs, or any music-analysis libraries directly.

### Mac

1. Install Docker Desktop for Mac from https://www.docker.com/products/docker-desktop/.
2. Open Docker Desktop once and leave it running.
3. Open Terminal.
4. Go to the Weekend Stems folder:

```bash
cd /Users/debo/Documents/song_split
```

5. Build the app with the separation engine:

```bash
INSTALL_DEMUCS=true docker compose build
```

6. Start the app:

```bash
INSTALL_DEMUCS=true docker compose up api
```

7. Open http://localhost:8000 in Chrome, Edge, or Safari.

### Windows

1. Install Docker Desktop for Windows from https://www.docker.com/products/docker-desktop/.
2. During install, allow Docker to use WSL 2 if it asks.
3. Open Docker Desktop once and leave it running.
4. Open PowerShell.
5. Go to the Weekend Stems folder. Example:

```powershell
cd C:\Users\YourName\Documents\song_split
```

6. Build the app with the separation engine:

```powershell
$env:INSTALL_DEMUCS="true"; docker compose build
```

7. Start the app:

```powershell
$env:INSTALL_DEMUCS="true"; docker compose up api
```

8. Open http://localhost:8000 in Chrome or Edge.

### Stop the App

Press `Ctrl+C` in the terminal running Docker, or run:

```bash
docker compose down
```

## What Weekend Stems Creates

Upload an MP3, WAV, FLAC, or M4A and click **Split Tracks**. The app creates:

| Track | Notes |
|---|---|
| Main Vocal | Lead vocal from the vocal stem |
| Backing Vocal | Estimated harmony/double vocal track |
| Drums | Full drum kit |
| Bass | Cleaned bass stem with mud reduction |
| Guitar | Cleaned guitar stem |
| Keys | Rebuilt keys/piano stem with guitar bleed suppression |
| Other | Sax, strings, synths, percussion, accordion, and anything not captured above |

Each track is labeled as generated or estimated so you know which stems are stronger and which are approximate.

## Main Features

- **Songs sidebar**: select processed songs, upload new songs, split tracks, cancel a split, watch progress, or remove a song.
- **Track View**: play synchronized stems with waveform lanes, volume, mute, and solo controls.
- **Chord View**: shows the song as bars, four bars per row, with the current bar moving as the song plays.
- **Chord correction**: double-click a chord/bar to manually correct it.
- **Song Key**: detects the song key and lets you transpose the displayed chord chart.
- **Shifted audio render**: render a transposed mix when you want the audio to match the selected key.
- **Tempo control**: slow down or speed up playback for practice while preserving pitch.
- **Count-in and click**: optional count-in and metronome click while the song is playing.
- **Regular Loop**: mark a start and end range, then repeat that range for focused practice.
- **Practice Zone**: use the same start/end range without looping; selected tracks mute only inside that zone, then the full mix resumes after it.
- **Edit Mix**: per-track EQ, reverb, compression, mute, preset, and flat reset controls.
- **HD Mix**: enable the master chain and render WAV or MP3 exports.
- **Export presets**: full mix, minus vocals, minus guitar, minus keys, or a ZIP of stems.

## Regular Loop vs Practice Zone

In **Edit Mix**, choose **Range Mode**:

- **Regular Loop**: `Start Range` and `End Range` create a true loop. Playback jumps back to the start when it reaches the end.
- **Practice Zone**: `Start Range` and `End Range` create a non-looping practice range. Pick tracks under **Practice Zone Mute** and those tracks mute only while playback is inside the range.

The active range is shown in green on the chord bars.

## Where Files Are Stored

All files stay local in the `data/` folder beside this README:

```text
data/
├── inbox/      uploaded source files
├── jobs/       one folder per processed song
│   └── <song_id>/
│       ├── analysis/       chords, tempo, key, mix settings
│       ├── exports/        rendered mixes and ZIPs
│       ├── stems/          final playable stems
│       ├── stems_raw/      raw model output
│       ├── stems_focus/    alternate focused stems
│       └── stems_rebuild/  rebuilt keys stem
└── models/     cached separation models
```

Nothing is uploaded to a cloud service by Weekend Stems.

## Command Line Tools

These are optional, but useful for troubleshooting or batch work:

```bash
# Separate a file into stems
INSTALL_DEMUCS=true docker compose run --rm worker separate data/inbox/your-song.mp3 --engine demucs

# Re-run stem cleanup/remapping without re-running the full model
INSTALL_DEMUCS=true docker compose run --rm worker remap data/jobs/<job_id>

# Re-run chord, key, and tempo detection
INSTALL_DEMUCS=true docker compose run --rm worker analyze-chords data/jobs/<job_id>
```

## Troubleshooting

**Docker is not running**

Open Docker Desktop first, wait until it says it is running, then try the command again.

**First split is slow**

The first run downloads the separation model and can take a while. Later runs reuse the cached model in `data/models/`.

**"Demucs is not installed in this container"**

Rebuild with `INSTALL_DEMUCS=true`.

```bash
INSTALL_DEMUCS=true docker compose build
```

**Port 8000 is already in use**

Stop the other app using port 8000, or edit `docker-compose.yml` and change:

```yaml
ports:
  - "8000:8000"
```

to something like:

```yaml
ports:
  - "8080:8000"
```

Then open http://localhost:8080.

**Changes are not showing up**

The app code is baked into the Docker image. Rebuild and restart:

```bash
docker compose down
INSTALL_DEMUCS=true docker compose up -d --build api
```

**Clean slate**

This deletes uploaded songs, processed stems, exports, and cached models:

```bash
docker compose down
rm -rf data/inbox/* data/jobs/* data/models/*
INSTALL_DEMUCS=true docker compose build --no-cache
INSTALL_DEMUCS=true docker compose up api
```
