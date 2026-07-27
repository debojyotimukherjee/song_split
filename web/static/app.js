const TRACK_ORDER = [
  "main_vocal",
  "backing_vocal",
  "drums",
  "bass",
  "guitar",
  "keys",
  "other",
];

const TRACK_LABELS = {
  main_vocal: "Main Vocal",
  backing_vocal: "Backing Vocal",
  drums: "Drums",
  bass: "Bass",
  guitar: "Guitar",
  keys: "Keys",
  other: "Other",
};

const TRACK_INSTRUMENTS = {
  main_vocal: "🎙️",
  backing_vocal: "🎤",
  drums: "🥁",
  bass: "🎸",
  guitar: "🎸",
  keys: "🎹",
  other: "🎷",
};

const KEY_OPTIONS = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"];
const NOTE_TO_PC = {
  C: 0,
  "B#": 0,
  "C#": 1,
  Db: 1,
  D: 2,
  "D#": 3,
  Eb: 3,
  E: 4,
  Fb: 4,
  "E#": 5,
  F: 5,
  "F#": 6,
  Gb: 6,
  G: 7,
  "G#": 8,
  Ab: 8,
  A: 9,
  "A#": 10,
  Bb: 10,
  B: 11,
  Cb: 11,
};

const state = {
  jobs: [],
  job: null,
  tracks: new Map(),
  chords: [],
  tempo: null,
  detectedKey: null,
  targetKey: null,
  playbackRate: 1,
  playing: false,
  seeking: false,
  activeView: "track",
  activeChordIndex: -1,
  activeBarIndex: -1,
  splitTaskId: null,
  splitPollTimer: null,
  syncTimer: null,
};

const els = {
  tabs: document.querySelectorAll(".view-tab"),
  trackView: document.querySelector("#trackView"),
  chordView: document.querySelector("#chordView"),
  keyView: document.querySelector("#keyView"),
  jobSelect: document.querySelector("#jobSelect"),
  deleteSongButton: document.querySelector("#deleteSongButton"),
  jobMeta: document.querySelector("#jobMeta"),
  tracks: document.querySelector("#tracks"),
  chordTimeline: document.querySelector("#chordTimeline"),
  fullChordTimeline: document.querySelector("#fullChordTimeline"),
  chordList: document.querySelector("#chordList"),
  currentChord: document.querySelector("#currentChord"),
  chordViewBar: document.querySelector("#chordViewBar"),
  chordViewTempo: document.querySelector("#chordViewTempo"),
  detectedKey: document.querySelector("#detectedKey"),
  targetKey: document.querySelector("#targetKey"),
  transposeSummary: document.querySelector("#transposeSummary"),
  resetKeyButton: document.querySelector("#resetKeyButton"),
  playButton: document.querySelector("#playButton"),
  stopButton: document.querySelector("#stopButton"),
  currentTime: document.querySelector("#currentTime"),
  duration: document.querySelector("#duration"),
  seekBar: document.querySelector("#seekBar"),
  tempoSlider: document.querySelector("#tempoSlider"),
  tempoValue: document.querySelector("#tempoValue"),
  fileInput: document.querySelector("#fileInput"),
  uploadButton: document.querySelector("#uploadButton"),
  splitButton: document.querySelector("#splitButton"),
  cancelSplitButton: document.querySelector("#cancelSplitButton"),
  splitProgressPanel: document.querySelector("#splitProgressPanel"),
  splitProgressBar: document.querySelector("#splitProgressBar"),
  splitProgressMessage: document.querySelector("#splitProgressMessage"),
  splitProgressValue: document.querySelector("#splitProgressValue"),
};

async function init() {
  renderKeyOptions();
  bindEvents();
  await loadJobs();
}

function bindEvents() {
  els.tabs.forEach((tab) => {
    tab.addEventListener("click", () => setActiveView(tab.dataset.view));
  });
  els.jobSelect.addEventListener("change", () => selectJob(els.jobSelect.value));
  els.deleteSongButton.addEventListener("click", deleteSelectedSong);
  els.playButton.addEventListener("click", togglePlayback);
  els.stopButton.addEventListener("click", stopPlayback);
  els.seekBar.addEventListener("input", () => {
    state.seeking = true;
    const duration = getDuration();
    updateTimeDisplay((Number(els.seekBar.value) / 1000) * duration, duration);
  });
  els.seekBar.addEventListener("change", () => {
    const duration = getDuration();
    seekAll((Number(els.seekBar.value) / 1000) * duration);
    state.seeking = false;
  });
  els.tempoSlider.addEventListener("input", () => {
    setPlaybackRate(Number(els.tempoSlider.value) / 100);
  });
  els.targetKey.addEventListener("change", () => setTargetKey(els.targetKey.value));
  els.resetKeyButton.addEventListener("click", () => setTargetKey(state.detectedKey || "C"));
  els.uploadButton.addEventListener("click", () => uploadSelectedFile("none"));
  els.splitButton.addEventListener("click", () => uploadSelectedFile("demucs"));
  els.cancelSplitButton.addEventListener("click", cancelCurrentSplit);
}

async function loadJobs() {
  const response = await fetch("/api/jobs");
  state.jobs = await response.json();
  els.jobSelect.innerHTML = "";

  if (!state.jobs.length) {
    els.jobSelect.innerHTML = "<option>No songs found</option>";
    els.jobMeta.textContent = "Split a song first.";
    els.tracks.innerHTML = '<div class="empty">No separated songs yet.</div>';
    els.deleteSongButton.disabled = true;
    return;
  }

  els.deleteSongButton.disabled = false;

  for (const job of state.jobs) {
    const option = document.createElement("option");
    option.value = job.job_id;
    option.textContent = `${job.filename} - ${job.status}`;
    els.jobSelect.append(option);
  }

  await selectJob(state.jobs[0].job_id);
}

async function selectJob(jobId) {
  stopPlayback();
  const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}`);
  state.job = await response.json();
  els.jobMeta.innerHTML = `
    <strong>${escapeHtml(state.job.input.filename)}</strong><br />
    Song ID: ${escapeHtml(state.job.job_id)}<br />
    Status: ${escapeHtml(state.job.status)}<br />
    Updated: ${new Date(state.job.updated_at).toLocaleString()}
  `;
  renderTracks(state.job);
  await loadChords(state.job.job_id);
}

async function loadChords(jobId) {
  state.chords = [];
  state.tempo = null;
  state.detectedKey = null;
  state.targetKey = null;
  state.activeChordIndex = -1;
  state.activeBarIndex = -1;
  els.chordTimeline.textContent = "No chord analysis yet";
  els.fullChordTimeline.textContent = "No chord analysis yet";
  els.chordList.innerHTML = "";
  els.currentChord.textContent = "--";
  els.chordViewBar.textContent = "Bar 1";
  updateTempoReadout();
  updateKeyReadout();
  try {
    const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/chords`);
    if (!response.ok) return;
    const analysis = await response.json();
    state.tempo = normalizeTempo(analysis.tempo);
    state.chords = analysis.segments || [];
    state.detectedKey = detectSongKey(state.chords);
    state.targetKey = state.detectedKey;
    updateTempoReadout();
    updateKeyReadout();
    renderChords();
  } catch {
    els.chordTimeline.textContent = "No chord analysis yet";
  }
}

function renderChords() {
  const duration = Math.max(getDuration(), state.chords.at(-1)?.end || 0);
  if (!state.chords.length || duration <= 0) {
    els.chordTimeline.textContent = "No chord analysis yet";
    els.fullChordTimeline.textContent = "No chord analysis yet";
    els.chordList.innerHTML = "";
    els.currentChord.textContent = "--";
    els.chordViewBar.textContent = "Bar 1";
    return;
  }

  renderChordTimeline(els.chordTimeline, duration, "compact");
  renderChordTimeline(els.fullChordTimeline, duration, "full");
  renderBarChart(duration);
  updateChordHighlight(getMaster()?.currentTime || 0, true);
}

function renderChordTimeline(container, duration, variant) {
  container.innerHTML = "";
  state.chords.forEach((segment, index) => {
    const block = document.createElement("button");
    block.className = `chord-block ${variant}`;
    block.type = "button";
    block.dataset.chordIndex = String(index);
    const barLabel = formatBarRange(segment);
    const chord = transposeChord(segment.chord);
    block.innerHTML = variant === "full"
      ? `<span>${escapeHtml(chord)}</span><small>${barLabel}</small>`
      : escapeHtml(chord);
    block.style.flexBasis = `${Math.max(3, ((segment.end - segment.start) / duration) * 100)}%`;
    block.title = `${chord} ${barLabel}`;
    block.addEventListener("click", () => seekAll(segment.start));
    container.append(block);
  });
}

function renderBarChart(duration) {
  els.chordList.innerHTML = "";
  const tempo = state.tempo || normalizeTempo(null);
  const barCount = Math.max(1, Math.ceil(duration / tempo.secondsPerBar));
  for (let index = 0; index < barCount; index += 1) {
    const start = index * tempo.secondsPerBar;
    const midpoint = start + tempo.secondsPerBar / 2;
    const chord = transposeChord(chordAtTime(midpoint)?.chord || chordAtTime(start)?.chord || "N");
    const item = document.createElement("button");
    item.className = "bar-card";
    item.type = "button";
    item.dataset.barIndex = String(index);
    item.innerHTML = `
      <strong>${escapeHtml(chord)}</strong>
      <span>${index + 1}</span>
    `;
    item.addEventListener("click", () => seekAll(start));
    els.chordList.append(item);
  }
}

function renderTracks(job) {
  state.tracks.clear();
  els.tracks.innerHTML = "";

  for (const name of TRACK_ORDER) {
    const stem = job.stems.find((item) => item.name === name);
    const row = document.createElement("article");
    row.className = "track";

    if (!stem || stem.status === "unavailable") {
      row.innerHTML = `
        <div class="track-title">
          <span class="track-name"><span class="instrument-badge" aria-label="${TRACK_LABELS[name]}" title="${TRACK_LABELS[name]}">${TRACK_INSTRUMENTS[name] || "🎚️"}</span>${TRACK_LABELS[name]}</span>
          <span class="track-status">Unavailable</span>
        </div>
        <div class="wave-wrap"><canvas class="waveform" width="900" height="80"></canvas><span class="playhead"></span></div>
        <div class="track-controls"></div>
      `;
      els.tracks.append(row);
      drawEmptyWave(row.querySelector("canvas"));
      continue;
    }

    const audio = document.createElement("audio");
    audio.preload = "auto";
    audio.src = audioUrl(job.job_id, name);
    audio.playbackRate = state.playbackRate;
    audio.preservesPitch = true;
    audio.mozPreservesPitch = true;
    audio.webkitPreservesPitch = true;
    audio.addEventListener("timeupdate", syncFromMaster);
    audio.addEventListener("loadedmetadata", syncFromMaster);

    row.innerHTML = `
      <div class="track-title">
        <span class="track-name"><span class="instrument-badge" aria-label="${TRACK_LABELS[name]}" title="${TRACK_LABELS[name]}">${TRACK_INSTRUMENTS[name] || "🎚️"}</span>${TRACK_LABELS[name]}</span>
        <span class="track-status ${stem.status}">${stem.status}</span>
      </div>
      <div class="wave-wrap"><canvas class="waveform" width="900" height="80"></canvas><span class="playhead"></span></div>
      <div class="track-controls">
        <button class="track-button mute" type="button">M</button>
        <button class="track-button solo" type="button">S</button>
        <input class="volume" type="range" min="0" max="1" step="0.01" value="1" aria-label="${TRACK_LABELS[name]} volume" />
      </div>
    `;

    row.append(audio);
    els.tracks.append(row);

    const track = {
      name,
      audio,
      muted: false,
      solo: false,
      volume: 1,
      row,
    };
    state.tracks.set(name, track);

    row.querySelector(".mute").addEventListener("click", () => {
      track.muted = !track.muted;
      row.querySelector(".mute").classList.toggle("active", track.muted);
      applyTrackMix();
    });
    row.querySelector(".solo").addEventListener("click", () => {
      track.solo = !track.solo;
      row.querySelector(".solo").classList.toggle("active", track.solo);
      applyTrackMix();
    });
    row.querySelector(".volume").addEventListener("input", (event) => {
      track.volume = Number(event.target.value);
      applyTrackMix();
    });

    drawWaveform(row.querySelector("canvas"), audio.src, colorForTrack(name));
  }

  applyTrackMix();
}

function audioUrl(jobId, trackName) {
  if (trackName === "keys") {
    return `/api/jobs/${encodeURIComponent(jobId)}/audio/stems_rebuild/keys.wav`;
  }
  return `/api/jobs/${encodeURIComponent(jobId)}/audio/stems/${trackName}.wav`;
}

function getMaster() {
  return [...state.tracks.values()][0]?.audio ?? null;
}

async function togglePlayback() {
  const master = getMaster();
  if (!master) return;

  if (state.playing) {
    pauseAll();
    return;
  }

  await ensureTracksReady();
  const time = master.currentTime;
  pauseAll(false);
  seekAll(time);
  syncTracksToMaster(time, 0);
  const playResults = await Promise.allSettled([...state.tracks.values()].map((track) => track.audio.play()));
  const hasPlayingTrack = playResults.some((result) => result.status === "fulfilled");
  if (!hasPlayingTrack) return;
  state.playing = true;
  els.playButton.textContent = "Pause";
  startSyncLoop();
}

function pauseAll(updateState = true) {
  for (const track of state.tracks.values()) {
    track.audio.pause();
    track.audio.playbackRate = state.playbackRate;
  }
  stopSyncLoop();
  if (updateState) {
    state.playing = false;
    els.playButton.textContent = "Play";
  }
}

function stopPlayback() {
  pauseAll();
  seekAll(0);
}

function seekAll(time) {
  for (const track of state.tracks.values()) {
    setTrackTime(track, time);
  }
  updateTimeDisplay(time, getDuration());
}

function syncFromMaster(event) {
  const master = getMaster();
  if (!master || event.target !== master || state.seeking) return;
  const duration = getDuration();
  updateTimeDisplay(master.currentTime, duration);
  if (duration > 0) {
    els.seekBar.value = String(Math.round((master.currentTime / duration) * 1000));
  }
  syncTracksToMaster(master.currentTime, 0.08);
}

function startSyncLoop() {
  stopSyncLoop();
  state.syncTimer = window.setInterval(() => {
    const master = getMaster();
    if (!master || master.paused || state.seeking) return;
    const duration = getDuration();
    updateTimeDisplay(master.currentTime, duration);
    if (duration > 0) {
      els.seekBar.value = String(Math.round((master.currentTime / duration) * 1000));
    }
    syncTracksToMaster(master.currentTime, 0.06);
  }, 180);
}

function stopSyncLoop() {
  if (state.syncTimer) {
    window.clearInterval(state.syncTimer);
    state.syncTimer = null;
  }
}

function syncTracksToMaster(masterTime, tolerance) {
  const master = getMaster();
  for (const track of state.tracks.values()) {
    if (track.audio === master) continue;
    const drift = track.audio.currentTime - masterTime;
    if (Math.abs(drift) > tolerance) {
      setTrackTime(track, masterTime);
    }
    track.audio.playbackRate = state.playbackRate;
    if (state.playing && master && !master.paused && track.audio.paused) {
      track.audio.play().catch(() => {});
    }
  }
}

function setTrackTime(track, time) {
  try {
    const duration = Number.isFinite(track.audio.duration) ? track.audio.duration : time;
    track.audio.currentTime = Math.max(0, Math.min(time, duration));
  } catch {
    // Some browsers reject currentTime before metadata is ready; the sync loop will retry.
  }
}

async function ensureTracksReady() {
  await Promise.all([...state.tracks.values()].map((track) => {
    if (track.audio.readyState >= 1) return Promise.resolve();
    return new Promise((resolve) => {
      const done = () => {
        track.audio.removeEventListener("loadedmetadata", done);
        track.audio.removeEventListener("error", done);
        resolve();
      };
      track.audio.addEventListener("loadedmetadata", done, { once: true });
      track.audio.addEventListener("error", done, { once: true });
      track.audio.load();
    });
  }));
}

function applyTrackMix() {
  const hasSolo = [...state.tracks.values()].some((track) => track.solo);
  for (const track of state.tracks.values()) {
    track.audio.muted = track.muted || (hasSolo && !track.solo);
    track.audio.volume = track.volume;
  }
}

function setPlaybackRate(rate) {
  state.playbackRate = Math.min(1.25, Math.max(0.5, rate || 1));
  els.tempoValue.textContent = `${Math.round(state.playbackRate * 100)}%`;
  for (const track of state.tracks.values()) {
    track.audio.playbackRate = state.playbackRate;
    track.audio.preservesPitch = true;
    track.audio.mozPreservesPitch = true;
    track.audio.webkitPreservesPitch = true;
  }
  updateTempoReadout();
}

function getDuration() {
  return getMaster()?.duration || 0;
}

function updateTimeDisplay(current, duration) {
  els.currentTime.textContent = formatTime(current || 0);
  els.duration.textContent = formatTime(duration || 0);
  const progress = duration > 0 ? Math.max(0, Math.min(100, (current / duration) * 100)) : 0;
  document.documentElement.style.setProperty("--playhead", `${progress}%`);
  els.chordViewBar.textContent = formatBar(current || 0);
  updateChordHighlight(current || 0, false);
}

function updateChordHighlight(time, forceScroll) {
  const activeIndex = state.chords.findIndex((segment) => time >= segment.start && time < segment.end);
  const activeSegment = state.chords[activeIndex];
  const activeBarIndex = barForTime(time) - 1;

  els.currentChord.textContent = activeSegment ? transposeChord(activeSegment.chord) : "--";
  els.chordViewBar.textContent = formatBar(time);

  document.querySelectorAll("[data-chord-index]").forEach((node) => {
    node.classList.toggle("active", Number(node.dataset.chordIndex) === activeIndex);
  });
  document.querySelectorAll("[data-bar-index]").forEach((node) => {
    node.classList.toggle("active", Number(node.dataset.barIndex) === activeBarIndex);
  });

  if (activeIndex < 0) {
    state.activeChordIndex = -1;
    state.activeBarIndex = -1;
    return;
  }

  const changed = activeIndex !== state.activeChordIndex || activeBarIndex !== state.activeBarIndex;
  state.activeChordIndex = activeIndex;
  state.activeBarIndex = activeBarIndex;
  if (!changed && !forceScroll) return;

  const compactBlock = els.chordTimeline.querySelector(`[data-chord-index="${activeIndex}"]`);
  compactBlock?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });

  if (state.activeView === "chord" || forceScroll) {
    const fullBlock = els.fullChordTimeline.querySelector(`[data-chord-index="${activeIndex}"]`);
    const card = els.chordList.querySelector(`[data-bar-index="${activeBarIndex}"]`);
    fullBlock?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
    card?.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
  }
}

function setActiveView(view) {
  state.activeView = ["chord", "key"].includes(view) ? view : "track";
  els.tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.view === state.activeView);
  });
  els.trackView.classList.toggle("active", state.activeView === "track");
  els.chordView.classList.toggle("active", state.activeView === "chord");
  els.keyView.classList.toggle("active", state.activeView === "key");
  updateChordHighlight(getMaster()?.currentTime || 0, true);
}

function normalizeTempo(tempo) {
  const bpm = Number(tempo?.bpm);
  const beatsPerBar = Number(tempo?.beats_per_bar) || 4;
  if (!Number.isFinite(bpm) || bpm <= 0) {
    return {
      bpm: 120,
      beatsPerBar,
      secondsPerBar: 2,
      timeSignature: "4/4",
      confidence: 0,
    };
  }
  return {
    bpm,
    beatsPerBar,
    secondsPerBar: Number(tempo?.seconds_per_bar) || (60 / bpm) * beatsPerBar,
    timeSignature: tempo?.time_signature || "4/4",
    confidence: Number(tempo?.confidence) || 0,
  };
}

function updateTempoReadout() {
  const tempo = state.tempo || normalizeTempo(null);
  const practiceBpm = Math.round(tempo.bpm * state.playbackRate);
  els.chordViewTempo.textContent = `${practiceBpm} BPM`;
  els.tempoValue.textContent = `${Math.round(state.playbackRate * 100)}%`;
  els.tempoSlider.title = `Original ${Math.round(tempo.bpm)} BPM, practice ${practiceBpm} BPM`;
}

function renderKeyOptions() {
  els.targetKey.innerHTML = "";
  for (const key of KEY_OPTIONS) {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = key;
    els.targetKey.append(option);
  }
}

function setTargetKey(key) {
  state.targetKey = KEY_OPTIONS.includes(key) ? key : state.detectedKey;
  updateKeyReadout();
  renderChords();
}

function updateKeyReadout() {
  const detected = state.detectedKey || "--";
  const target = state.targetKey || state.detectedKey || "C";
  const semitones = transposeSemitones();
  els.detectedKey.textContent = detected;
  els.targetKey.value = KEY_OPTIONS.includes(target) ? target : "C";
  els.transposeSummary.textContent = semitones === 0
    ? `Showing original key: ${detected}`
    : `Showing ${target}, transposed ${formatSemitones(semitones)} from ${detected}`;
}

function detectSongKey(chords) {
  const scores = new Array(12).fill(0);
  for (const segment of chords) {
    const parsed = parseChord(segment.chord);
    if (!parsed) continue;
    const duration = Math.max(0.25, (segment.end || 0) - (segment.start || 0));
    scores[parsed.pc] += duration;
    scores[(parsed.pc + (parsed.minor ? 3 : 9)) % 12] += duration * 0.25;
  }
  const best = scores.reduce((bestIndex, score, index) => score > scores[bestIndex] ? index : bestIndex, 0);
  return KEY_OPTIONS[best];
}

function transposeChord(chord) {
  const parsed = parseChord(chord);
  if (!parsed) return chord;
  const root = KEY_OPTIONS[(parsed.pc + transposeSemitones() + 12) % 12];
  return `${root}${parsed.suffix}`;
}

function transposeSemitones() {
  const from = NOTE_TO_PC[state.detectedKey] ?? 0;
  const to = NOTE_TO_PC[state.targetKey || state.detectedKey] ?? from;
  return ((to - from + 18) % 12) - 6;
}

function parseChord(chord) {
  const match = String(chord || "").match(/^([A-G](?:#|b)?)(.*)$/);
  if (!match || !(match[1] in NOTE_TO_PC)) return null;
  return {
    pc: NOTE_TO_PC[match[1]],
    suffix: match[2] || "",
    minor: match[2]?.startsWith("m") && !match[2]?.startsWith("maj"),
  };
}

function formatSemitones(semitones) {
  const direction = semitones > 0 ? "up" : "down";
  const amount = Math.abs(semitones);
  return `${direction} ${amount} semitone${amount === 1 ? "" : "s"}`;
}

function barForTime(seconds) {
  const tempo = state.tempo || normalizeTempo(null);
  return Math.max(1, Math.floor((seconds || 0) / tempo.secondsPerBar) + 1);
}

function chordAtTime(seconds) {
  return state.chords.find((segment) => seconds >= segment.start && seconds < segment.end) || state.chords.at(-1);
}

function formatBar(seconds) {
  return `Bar ${barForTime(seconds)}`;
}

function formatBarRange(segment) {
  const startBar = barForTime(segment.start);
  const endBar = barForTime(Math.max(segment.start, segment.end - 0.001));
  return startBar === endBar ? `Bar ${startBar}` : `Bars ${startBar}-${endBar}`;
}

async function uploadSelectedFile(engine) {
  const file = els.fileInput.files?.[0];
  if (!file) {
    els.jobMeta.textContent = "Choose a file first.";
    return;
  }
  const form = new FormData();
  form.append("file", file);
  setUploadBusy(true, engine === "demucs");
  els.jobMeta.textContent = engine === "demucs"
    ? "Starting split..."
    : "Uploading song...";
  try {
    if (engine === "demucs") {
      const response = await fetch("/api/splits", { method: "POST", body: form });
      if (!response.ok) {
        els.jobMeta.textContent = await response.text();
        return;
      }
      const task = await response.json();
      state.splitTaskId = task.task_id;
      updateSplitProgress(task);
      pollSplitProgress();
      return;
    }

    const response = await fetch(`/jobs?engine=${encodeURIComponent(engine)}`, { method: "POST", body: form });
    if (!response.ok) {
      els.jobMeta.textContent = await response.text();
      return;
    }
    const job = await response.json();
    await loadJobs();
    if (job.job_id) await selectJob(job.job_id);
  } finally {
    if (engine !== "demucs") setUploadBusy(false, false);
  }
}

async function deleteSelectedSong() {
  if (!state.job) return;
  const songName = state.job.input?.filename || state.job.job_id;
  if (!window.confirm(`Remove "${songName}" from Weekend Stems?`)) return;

  pauseAll();
  els.deleteSongButton.disabled = true;
  els.jobMeta.textContent = "Removing song...";
  const response = await fetch(`/api/jobs/${encodeURIComponent(state.job.job_id)}`, { method: "DELETE" });
  if (!response.ok) {
    els.jobMeta.textContent = await response.text();
    els.deleteSongButton.disabled = false;
    return;
  }

  state.job = null;
  state.tracks.clear();
  state.chords = [];
  els.tracks.innerHTML = "";
  els.chordTimeline.textContent = "No chord analysis yet";
  els.fullChordTimeline.textContent = "No chord analysis yet";
  els.chordList.innerHTML = "";
  await loadJobs();
}

function setUploadBusy(isBusy, showProgress) {
  els.uploadButton.disabled = isBusy;
  els.splitButton.disabled = isBusy;
  els.fileInput.disabled = isBusy;
  els.deleteSongButton.disabled = isBusy || !state.job;
  els.splitButton.textContent = isBusy ? "Working..." : "Split Tracks";
  els.splitProgressPanel.hidden = !showProgress;
  els.cancelSplitButton.disabled = !isBusy;
  if (!showProgress) updateSplitProgress({ progress: 0, message: "Preparing song..." });
}

async function pollSplitProgress() {
  if (!state.splitTaskId) return;
  const response = await fetch(`/api/splits/${encodeURIComponent(state.splitTaskId)}`);
  if (!response.ok) {
    setUploadBusy(false, false);
    els.jobMeta.textContent = "Could not read split progress.";
    return;
  }

  const task = await response.json();
  updateSplitProgress(task);

  if (task.state === "done") {
    clearSplitPollTimer();
    state.splitTaskId = null;
    setUploadBusy(false, false);
    els.jobMeta.textContent = "Split complete.";
    await loadJobs();
    if (task.job_id) await selectJob(task.job_id);
    return;
  }

  if (task.state === "failed" || task.state === "cancelled") {
    clearSplitPollTimer();
    state.splitTaskId = null;
    setUploadBusy(false, false);
    els.jobMeta.textContent = task.error || task.message || "Split stopped.";
    await loadJobs();
    return;
  }

  state.splitPollTimer = window.setTimeout(pollSplitProgress, 1500);
}

async function cancelCurrentSplit() {
  if (!state.splitTaskId) return;
  els.cancelSplitButton.disabled = true;
  els.splitProgressMessage.textContent = "Cancelling split...";
  await fetch(`/api/splits/${encodeURIComponent(state.splitTaskId)}/cancel`, { method: "POST" });
  pollSplitProgress();
}

function clearSplitPollTimer() {
  if (state.splitPollTimer) {
    window.clearTimeout(state.splitPollTimer);
    state.splitPollTimer = null;
  }
}

function updateSplitProgress(task) {
  const progress = Math.max(0, Math.min(100, Number(task.progress) || 0));
  els.splitProgressBar.value = progress;
  els.splitProgressValue.textContent = `${Math.round(progress)}%`;
  els.splitProgressMessage.textContent = task.message || "Working...";
}

async function drawWaveform(canvas, url, color) {
  const ctx = canvas.getContext("2d");
  drawEmptyWave(canvas);
  try {
    const response = await fetch(url);
    const buffer = await response.arrayBuffer();
    const audioContext = new AudioContext();
    const audioBuffer = await audioContext.decodeAudioData(buffer);
    const data = audioBuffer.getChannelData(0);
    const width = canvas.width;
    const height = canvas.height;
    const step = Math.ceil(data.length / width);

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#090707";
    ctx.fillRect(0, 0, width, height);
    ctx.fillStyle = color;

    for (let x = 0; x < width; x += 1) {
      let min = 1;
      let max = -1;
      const start = x * step;
      for (let i = 0; i < step && start + i < data.length; i += 1) {
        const sample = data[start + i];
        if (sample < min) min = sample;
        if (sample > max) max = sample;
      }
      const y1 = ((1 + min) * height) / 2;
      const y2 = ((1 + max) * height) / 2;
      ctx.fillRect(x, y1, 1, Math.max(1, y2 - y1));
    }
    audioContext.close();
  } catch {
    drawEmptyWave(canvas);
  }
}

function drawEmptyWave(canvas) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#090707";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "#3a2323";
  ctx.beginPath();
  ctx.moveTo(0, canvas.height / 2);
  ctx.lineTo(canvas.width, canvas.height / 2);
  ctx.stroke();
}

function colorForTrack(name) {
  const colors = {
    main_vocal: "#ff4059",
    backing_vocal: "#ff7888",
    drums: "#e00024",
    bass: "#ffb000",
    guitar: "#ff5a1f",
    keys: "#c81dff",
    other: "#ffcf5a",
  };
  return colors[name] || "#ff4059";
}

function formatTime(seconds) {
  const safe = Math.max(0, Math.floor(seconds || 0));
  const mins = Math.floor(safe / 60);
  const secs = safe % 60;
  return `${mins}:${String(secs).padStart(2, "0")}`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

init();
