# Wannabe Stem

Wannabe Stem is a local-first rehearsal app for musicians and bands. Drop in a song, split it into playable stems, slow it down, follow chords by bar, transpose the chart, loop hard sections, and build practice mixes on your own computer.

Built by Wannabe Weekenders for rehearsals that need a little less guesswork and a lot more playing.

## What You Need

- Docker Desktop for Mac or Windows.
- A reasonably modern computer with at least 8 GB of available memory.
- A few GB of free disk space for music models, uploaded songs, stems, and exports.

The app runs in Docker; you do not need to install Python, FFmpeg, Demucs, or music-analysis libraries on your computer.

## Docker Installation

Wannabe Stem runs with Docker so bandmates do not need to install Python, FFmpeg, Demucs, or any music-analysis libraries directly.

## Downloadable Bandmate Package

For non-technical bandmates, create a zip and upload that zip to Google Drive:

```bash
./scripts/make_release_package.sh
```

The script writes a file like:

```text
dist/Wannabe-Stem-20260727-1800.zip
```

Upload that zip to Google Drive. Bandmates should download it, unzip it, and double-click:

- Mac: **Start Wannabe Stem.command**
- Windows: **Start Wannabe Stem Windows.cmd**

They still need Docker Desktop installed and running first. The zip includes `BANDMATE_INSTALL.md` with simple Mac and Windows instructions.

### Mac

1. Install Docker Desktop for Mac from https://www.docker.com/products/docker-desktop/.
2. Open Docker Desktop once and leave it running.
3. Open Terminal.
4. Go to the Wannabe Stem folder:

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
5. Go to the Wannabe Stem folder. Example:

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

## What Wannabe Stem Creates

Upload an MP3, WAV, FLAC, or M4A and click **Split Tracks**. The app creates:

| Track | Notes |
|---|---|
| Main Vocal | Lead vocal from the vocal stem |
| Backing Vocal | Estimated harmony/double vocal track |
| Drums | Full drum kit |
| Bass | Cleaned bass stem with mud reduction |
| Guitar | Cleaned guitar stem |
| Acoustic Guitar | Estimated acoustic-focused guitar lane for strummed/acoustic parts |
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

Audio files and generated stems stay on the computer running Wannabe Stem. The optional song-information card can look up the artist and title inferred from the file name on Wikipedia; it does not upload audio.

## Limitations and Music Rights

Wannabe Stem is a rehearsal tool, not a replacement for original multitrack recordings.

- Stem separation, chord detection, key detection, bar positions, and BPM are estimates. Always trust your ears and correct the chart when needed.
- The Main Vocal, Drums, and Bass tracks are generally the most dependable. Backing Vocal, Acoustic Guitar, Keys, and instrument-specific estimates can contain bleed, artifacts, or missing parts.
- The experimental Keys and Acoustic Guitar lanes are intentionally labelled as estimates. They are useful starting points, not isolated studio tracks.
- Only process music you own or are authorized to use. You are responsible for respecting copyright, performer rights, and any distribution restrictions that apply to the source recording and exported stems.
- Do not present generated stems as official multitracks, and do not redistribute copyrighted source music or derived stems without permission.

## Privacy and Local Network Safety

Wannabe Stem is designed to run on your own computer. It does not provide accounts, login, or multi-user access controls.

- Keep the Docker port private to your own machine or a trusted home network.
- Do not expose port `8000` directly to the public internet.
- Anyone who can reach the app can upload audio or delete locally stored songs, so avoid using it on a shared or public network.
- To report a security issue privately, see [SECURITY.md](SECURITY.md).

## Getting Help and Contributing

- Report reproducible bugs or suggest improvements through [GitHub Issues](../../issues).
- Start a conversation or share workflow ideas in [GitHub Discussions](../../discussions), if enabled.
- Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.
- Include your operating system, Docker Desktop version, input format, a short log excerpt, and whether the problem is with splitting, playback, chords, or exporting. Please do not attach music you do not have permission to share.

## Open-Source Notices

Wannabe Stem is built on the work of the open-source music-information-retrieval community. See [NOTICE.md](NOTICE.md) for the principal libraries and projects used by the app, their licenses, and attribution notes.

## Releases

Stable releases are published on the repository's [Releases](../../releases) page. Each release includes a source ZIP for Mac and Windows users, release notes, and a SHA-256 checksum generated by `scripts/make_release_package.sh`. See [the release checklist](.github/RELEASE.md) if you are publishing a version.

## Command Line Tools

These are optional, but useful for troubleshooting or batch work:

```bash
# Separate a file into stems
INSTALL_DEMUCS=true docker compose run --rm worker separate data/inbox/your-song.mp3 --engine demucs

# Re-run stem cleanup/remapping without re-running the full model
INSTALL_DEMUCS=true docker compose run --rm worker remap data/jobs/<job_id>

# Re-run chord, key, and tempo detection
INSTALL_DEMUCS=true docker compose run --rm worker analyze-chords data/jobs/<job_id>

# List audio-separator/UVR models by stem name
docker compose exec api python -m app.cli list-audio-separator-models --filter Guitar --limit 10

# Re-run only the experimental audio-separator specialist pass on an existing job
docker compose exec api python -m app.cli enhance-audio-separator data/jobs/<job_id>
```

## Experimental Audio-Separator Backend

Wannabe Stem can optionally run `audio-separator` after Demucs as a specialist pass for Guitar, Acoustic Guitar, and Keys.

The current Docker Compose setup enables it by default:

```yaml
SONG_SPLIT_ENABLE_AUDIO_SEPARATOR: true
SONG_SPLIT_AUDIO_SEPARATOR_MODELS: htdemucs_6s.yaml
```

Important caveat: audio-separator's built-in models currently list `htdemucs_6s.yaml` as the main model with native `guitar` and `piano` stems. Its stronger UVR models are mostly vocal/instrumental or other/no-other models, so this backend is an experiment framework, not yet a guaranteed dedicated Keys or Acoustic Guitar model.

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
