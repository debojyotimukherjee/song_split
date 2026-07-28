const TRACK_ORDER = [
  "main_vocal",
  "backing_vocal",
  "drums",
  "bass",
  "guitar",
  "acoustic_guitar",
  "keys",
  "other",
];

const TRACK_LABELS = {
  main_vocal: "Main Vocal",
  backing_vocal: "Backing Vocal",
  drums: "Drums",
  bass: "Bass",
  guitar: "Guitar",
  acoustic_guitar: "Acoustic Guitar",
  keys: "Keys",
  other: "Other",
};

const TRACK_INSTRUMENTS = {
  main_vocal: "🎙️",
  backing_vocal: "🎤",
  drums: "🥁",
  bass: "🎸",
  guitar: "🎸",
  acoustic_guitar: "🪕",
  keys: "🎹",
  other: "🎷",
};

const EQ_BANDS = [
  { key: "low", label: "Low", type: "lowshelf", frequency: 120, q: 0.7 },
  { key: "mid", label: "Mid", type: "peaking", frequency: 1100, q: 0.95 },
  { key: "high", label: "High", type: "highshelf", frequency: 6200, q: 0.7 },
];

const SIDEBAR_WIDTH_STORAGE_KEY = "wannabeStemSidebarWidth";
const SIDEBAR_WIDTH_MIN = 260;
const SIDEBAR_WIDTH_MAX = 520;
const MIXER_MIN_WIDTH = 720;

const MIX_PRESETS = {
  main_vocal: { volume: 50, low: -1, mid: 2, high: 1, reverb: 62, compression: 64 },
  backing_vocal: { volume: 50, low: -2, mid: 1, high: 1, reverb: 66, compression: 58 },
  drums: { volume: 50, low: 2, mid: 0, high: 2, reverb: 54, compression: 60 },
  bass: { volume: 50, low: 3, mid: -2, high: 0, reverb: 50, compression: 56 },
  guitar: { volume: 50, low: -1, mid: 2, high: 2, reverb: 58, compression: 54 },
  acoustic_guitar: { volume: 50, low: 1, mid: 2, high: 3, reverb: 58, compression: 52 },
  keys: { volume: 50, low: -2, mid: 1, high: 3, reverb: 60, compression: 52 },
  other: { volume: 50, low: -1, mid: 0, high: 1, reverb: 58, compression: 52 },
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
  audioContext: null,
  masterInput: null,
  masterCompressor: null,
  masterGain: null,
  reverbImpulse: null,
  hdMaster: false,
  mixSettings: new Map(),
  loopStart: null,
  loopEnd: null,
  loopMode: "regular",
  practiceMuteTracks: new Set(),
  clickTimer: null,
  countInActive: false,
  playing: false,
  seeking: false,
  activeView: "track",
  activeChordIndex: -1,
  activeBarIndex: -1,
  splitTaskId: null,
  splitPollTimer: null,
  syncTimer: null,
  shiftedMixUrl: null,
  shiftedMixFilename: null,
};

const els = {
  tabs: document.querySelectorAll(".view-tab"),
  trackView: document.querySelector("#trackView"),
  chordView: document.querySelector("#chordView"),
  keyView: document.querySelector("#keyView"),
  editMixView: document.querySelector("#editMixView"),
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
  audioKeyStatus: document.querySelector("#audioKeyStatus"),
  renderShiftedButton: document.querySelector("#renderShiftedButton"),
  editMixDeck: document.querySelector("#editMixDeck"),
  hdMasterButton: document.querySelector("#hdMasterButton"),
  hdExportButton: document.querySelector("#hdExportButton"),
  saveMixButton: document.querySelector("#saveMixButton"),
  exportPreset: document.querySelector("#exportPreset"),
  exportFormat: document.querySelector("#exportFormat"),
  loopModeSelect: document.querySelector("#loopModeSelect"),
  setLoopStartButton: document.querySelector("#setLoopStartButton"),
  setLoopEndButton: document.querySelector("#setLoopEndButton"),
  clearLoopButton: document.querySelector("#clearLoopButton"),
  loopStatus: document.querySelector("#loopStatus"),
  globalLoopStatus: document.querySelector("#globalLoopStatus"),
  globalShiftedMixButton: document.querySelector("#globalShiftedMixButton"),
  globalShiftedMixText: document.querySelector("#globalShiftedMixText"),
  practiceMuteList: document.querySelector("#practiceMuteList"),
  countInToggle: document.querySelector("#countInToggle"),
  metronomeToggle: document.querySelector("#metronomeToggle"),
  mixStatus: document.querySelector("#mixStatus"),
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
  sidebarResizeHandle: document.querySelector("#sidebarResizeHandle"),
};

async function init() {
  restoreSidebarWidth();
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
  els.renderShiftedButton.addEventListener("click", renderShiftedMix);
  els.globalShiftedMixButton.addEventListener("click", openShiftedMix);
  els.hdMasterButton.addEventListener("click", toggleHdMaster);
  els.hdExportButton.addEventListener("click", renderHdMix);
  els.saveMixButton.addEventListener("click", saveMixSettings);
  els.loopModeSelect.addEventListener("change", () => setLoopMode(els.loopModeSelect.value));
  els.setLoopStartButton.addEventListener("click", setLoopStart);
  els.setLoopEndButton.addEventListener("click", setLoopEnd);
  els.clearLoopButton.addEventListener("click", clearLoop);
  els.metronomeToggle.addEventListener("change", () => {
    if (state.playing) startOrStopClick();
  });
  els.uploadButton.addEventListener("click", () => uploadSelectedFile("none"));
  els.splitButton.addEventListener("click", () => uploadSelectedFile("demucs"));
  els.cancelSplitButton.addEventListener("click", cancelCurrentSplit);
  els.sidebarResizeHandle?.addEventListener("pointerdown", startSidebarResize);
  els.sidebarResizeHandle?.addEventListener("keydown", adjustSidebarWidthWithKeyboard);
  window.addEventListener("resize", () => setSidebarWidth(currentSidebarWidth(), false));
}

function restoreSidebarWidth() {
  const savedWidth = Number(window.localStorage.getItem(SIDEBAR_WIDTH_STORAGE_KEY));
  setSidebarWidth(Number.isFinite(savedWidth) ? savedWidth : 320, false);
}

function setSidebarWidth(width, persist) {
  const maxForViewport = Math.max(SIDEBAR_WIDTH_MIN, Math.min(SIDEBAR_WIDTH_MAX, window.innerWidth - MIXER_MIN_WIDTH));
  const nextWidth = Math.max(SIDEBAR_WIDTH_MIN, Math.min(maxForViewport, Number(width) || 320));
  document.documentElement.style.setProperty("--sidebar-width", `${nextWidth}px`);
  if (els.sidebarResizeHandle) {
    els.sidebarResizeHandle.setAttribute("aria-valuemax", String(maxForViewport));
    els.sidebarResizeHandle.setAttribute("aria-valuenow", String(nextWidth));
    els.sidebarResizeHandle.setAttribute("title", `Left pane ${nextWidth}px`);
  }
  if (persist) {
    window.localStorage.setItem(SIDEBAR_WIDTH_STORAGE_KEY, String(nextWidth));
  }
}

function currentSidebarWidth() {
  const value = getComputedStyle(document.documentElement).getPropertyValue("--sidebar-width");
  return Number.parseInt(value, 10) || 320;
}

function startSidebarResize(event) {
  if (!els.sidebarResizeHandle) return;
  event.preventDefault();
  document.body.classList.add("sidebar-resizing");
  els.sidebarResizeHandle.setPointerCapture(event.pointerId);

  const move = (moveEvent) => setSidebarWidth(moveEvent.clientX, true);
  const stop = () => {
    document.body.classList.remove("sidebar-resizing");
    els.sidebarResizeHandle?.removeEventListener("pointermove", move);
    els.sidebarResizeHandle?.removeEventListener("pointerup", stop);
    els.sidebarResizeHandle?.removeEventListener("pointercancel", stop);
  };

  els.sidebarResizeHandle.addEventListener("pointermove", move);
  els.sidebarResizeHandle.addEventListener("pointerup", stop, { once: true });
  els.sidebarResizeHandle.addEventListener("pointercancel", stop, { once: true });
}

function adjustSidebarWidthWithKeyboard(event) {
  if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  const step = event.shiftKey ? 40 : 10;
  if (event.key === "Home") {
    setSidebarWidth(SIDEBAR_WIDTH_MIN, true);
  } else if (event.key === "End") {
    setSidebarWidth(SIDEBAR_WIDTH_MAX, true);
  } else {
    setSidebarWidth(currentSidebarWidth() + (event.key === "ArrowRight" ? step : -step), true);
  }
}

async function loadJobs() {
  const response = await fetch("/api/jobs");
  state.jobs = await response.json();
  els.jobSelect.innerHTML = "";

  if (!state.jobs.length) {
    els.jobSelect.innerHTML = "<option>No songs found</option>";
    els.jobMeta.textContent = "Split a song first.";
    els.tracks.innerHTML = '<div class="empty">No separated songs yet.</div>';
    els.editMixDeck.innerHTML = '<div class="empty">No separated songs yet.</div>';
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
  state.loopStart = null;
  state.loopEnd = null;
  state.loopMode = "regular";
  state.practiceMuteTracks = new Set();
  state.shiftedMixUrl = null;
  state.shiftedMixFilename = null;
  updateShiftedMixStatus("idle");
  renderTracks(state.job);
  await loadMixSettings();
  renderEditMix();
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
  updateAudioKeyStatus();
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
    updateAudioKeyStatus();
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
    const chord = displayChord(segment.chord);
    block.innerHTML = variant === "full"
      ? `<span>${escapeHtml(chord)}</span><small>${barLabel}</small>`
      : escapeHtml(chord);
    block.style.flexBasis = `${Math.max(3, ((segment.end - segment.start) / duration) * 100)}%`;
    block.title = `${chord} ${barLabel}`;
    block.addEventListener("click", () => seekAll(segment.start));
    block.addEventListener("dblclick", () => editChordSegment(index));
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
    const chord = displayChord(chordAtTime(midpoint)?.chord || chordAtTime(start)?.chord || "~");
    const item = document.createElement("button");
    item.className = "bar-card";
    item.type = "button";
    item.dataset.barIndex = String(index);
    item.innerHTML = `
      <strong>${escapeHtml(chord)}</strong>
      <span>${index + 1}</span>
    `;
    item.addEventListener("click", () => seekAll(start));
    item.addEventListener("dblclick", () => {
      const segmentIndex = state.chords.findIndex((segment) => midpoint >= segment.start && midpoint < segment.end);
      if (segmentIndex >= 0) editChordSegment(segmentIndex);
    });
    els.chordList.append(item);
  }
  updateLoopBarHighlights();
}

async function editChordSegment(index) {
  if (!state.job || !state.chords[index]) return;
  const current = state.chords[index].chord;
  const next = window.prompt("Correct chord", current);
  if (!next || next.trim() === current) return;
  const response = await fetch(`/api/jobs/${encodeURIComponent(state.job.job_id)}/chords/${index}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chord: next.trim() }),
  });
  if (!response.ok) {
    els.jobMeta.textContent = await response.text();
    return;
  }
  const analysis = await response.json();
  state.chords = analysis.segments || state.chords;
  renderChords();
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
        <button class="track-button mute" type="button">Mute</button>
        <button class="track-button solo" type="button">S</button>
        <input class="volume" type="range" min="0" max="2" step="0.01" value="1" aria-label="${TRACK_LABELS[name]} volume" />
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
      sourceNode: null,
      eqNodes: null,
      reverbNodes: null,
      compressionNode: null,
      gainNode: null,
    };
    ensureMixSettings(name);
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
      ensureMixSettings(name).volume = gainToVolumeLevel(track.volume);
      applyTrackMix();
      renderEditMix();
    });

    drawWaveform(row.querySelector("canvas"), audio.src, colorForTrack(name));
  }

  applyTrackMix();
  renderEditMix();
  renderPracticeMuteControls();
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
  await ensureAudioGraph();
  const time = master.currentTime;
  if (els.countInToggle.checked && !state.countInActive) {
    await playCountIn();
  }
  pauseAll(false);
  seekAll(time);
  syncTracksToMaster(time, 0);
  const playResults = await Promise.allSettled([...state.tracks.values()].map((track) => track.audio.play()));
  const hasPlayingTrack = playResults.some((result) => result.status === "fulfilled");
  if (!hasPlayingTrack) return;
  state.playing = true;
  els.playButton.textContent = "Pause";
  startSyncLoop();
  startOrStopClick();
}

function pauseAll(updateState = true) {
  for (const track of state.tracks.values()) {
    track.audio.pause();
    track.audio.playbackRate = state.playbackRate;
  }
  stopSyncLoop();
  stopClick();
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
  applyTrackMix();
}

function syncFromMaster(event) {
  const master = getMaster();
  if (!master || event.target !== master || state.seeking) return;
  const duration = getDuration();
  updateTimeDisplay(master.currentTime, duration);
  if (duration > 0) {
    els.seekBar.value = String(Math.round((master.currentTime / duration) * 1000));
  }
  applyTrackMix();
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
    if (state.loopMode === "regular" && hasActiveRange() && master.currentTime >= state.loopEnd) {
      seekAll(state.loopStart);
      return;
    }
    applyTrackMix();
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
  const masterTime = getMaster()?.currentTime || 0;
  const inPracticeZone = state.loopMode === "practice" && isPracticeZoneActiveAt(masterTime);
  for (const track of state.tracks.values()) {
    const practiceMuted = inPracticeZone && state.practiceMuteTracks.has(track.name);
    const audible = !(track.muted || practiceMuted || (hasSolo && !track.solo));
    if (track.gainNode) {
      track.audio.muted = false;
      track.audio.volume = 1;
      track.gainNode.gain.value = audible ? track.volume : 0;
    } else {
      track.audio.muted = !audible;
      track.audio.volume = track.volume;
    }
  }
}

function toggleTrackMute(trackName) {
  const track = state.tracks.get(trackName);
  if (!track) return;
  track.muted = !track.muted;
  track.row.querySelector(".mute")?.classList.toggle("active", track.muted);
  applyTrackMix();
  renderEditMix();
}

async function ensureAudioGraph() {
  if (!state.audioContext) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) {
      els.mixStatus.textContent = "EQ unavailable in this browser";
      return;
    }
    state.audioContext = new AudioContextClass();
    state.masterInput = state.audioContext.createGain();
    state.masterCompressor = state.audioContext.createDynamicsCompressor();
    state.masterCompressor.threshold.value = -18;
    state.masterCompressor.knee.value = 18;
    state.masterCompressor.ratio.value = 3.2;
    state.masterCompressor.attack.value = 0.006;
    state.masterCompressor.release.value = 0.18;
    state.masterGain = state.audioContext.createGain();
    state.masterGain.gain.value = 0.92;
    rebuildMasterChain();
  }

  if (state.audioContext.state === "suspended") {
    await state.audioContext.resume();
  }

  for (const track of state.tracks.values()) {
    connectTrackGraph(track);
  }
  applyEqToAllTracks();
  applyTrackMix();
  updateMixStatus();
}

function connectTrackGraph(track) {
  if (!state.audioContext || track.sourceNode) return;
  track.sourceNode = state.audioContext.createMediaElementSource(track.audio);
  const low = state.audioContext.createBiquadFilter();
  const mid = state.audioContext.createBiquadFilter();
  const high = state.audioContext.createBiquadFilter();
  const dryGain = state.audioContext.createGain();
  const convolver = state.audioContext.createConvolver();
  const wetGain = state.audioContext.createGain();
  const compressor = state.audioContext.createDynamicsCompressor();
  const gain = state.audioContext.createGain();

  const filters = { low, mid, high };
  for (const band of EQ_BANDS) {
    filters[band.key].type = band.type;
    filters[band.key].frequency.value = band.frequency;
    filters[band.key].Q.value = band.q;
  }

  track.sourceNode.connect(low);
  low.connect(mid);
  mid.connect(high);
  high.connect(dryGain);
  high.connect(convolver);
  convolver.connect(wetGain);
  dryGain.connect(gain);
  wetGain.connect(gain);
  gain.connect(compressor);
  compressor.connect(state.masterInput);
  track.eqNodes = filters;
  track.reverbNodes = { dryGain, convolver, wetGain };
  track.compressionNode = compressor;
  track.gainNode = gain;
  applyEqToTrack(track);
}

function rebuildMasterChain() {
  if (!state.masterInput || !state.masterGain || !state.audioContext) return;
  try {
    state.masterInput.disconnect();
    state.masterCompressor.disconnect();
    state.masterGain.disconnect();
  } catch {
    // Nodes may not be connected yet.
  }

  if (state.hdMaster) {
    state.masterInput.connect(state.masterCompressor);
    state.masterCompressor.connect(state.masterGain);
  } else {
    state.masterInput.connect(state.masterGain);
  }
  state.masterGain.connect(state.audioContext.destination);
}

function ensureMixSettings(trackName) {
  if (!state.mixSettings.has(trackName)) {
    state.mixSettings.set(trackName, { ...(MIX_PRESETS[trackName] || neutralMixSettings()) });
  }
  return state.mixSettings.get(trackName);
}

function neutralMixSettings() {
  return { volume: 50, low: 0, mid: 0, high: 0, reverb: 50, compression: 50 };
}

function normalizeVolumeLevel(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 50;
  return Math.max(0, Math.min(100, numeric));
}

function normalizeSavedVolumeLevel(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 50;
  if (numeric >= 0 && numeric <= 2) return gainToVolumeLevel(numeric);
  return normalizeVolumeLevel(numeric);
}

function volumeLevelToGain(level) {
  return Math.max(0, Math.min(2, normalizeVolumeLevel(level) / 50));
}

function gainToVolumeLevel(gain) {
  const numeric = Number(gain);
  if (!Number.isFinite(numeric)) return 50;
  return Math.max(0, Math.min(100, numeric * 50));
}

function applyEqToAllTracks() {
  for (const track of state.tracks.values()) {
    applyEqToTrack(track);
  }
}

function applyEqToTrack(track) {
  const settings = ensureMixSettings(track.name);
  settings.volume = normalizeVolumeLevel(settings.volume);
  track.volume = volumeLevelToGain(settings.volume);
  track.row.querySelector(".volume").value = String(track.volume);
  if (track.eqNodes) {
    for (const band of EQ_BANDS) {
      track.eqNodes[band.key].gain.value = Number(settings[band.key]) || 0;
    }
  }
  if (track.reverbNodes) {
    track.reverbNodes.convolver.buffer = state.reverbImpulse || createReverbImpulse();
    const wet = Math.max(0, Math.min(0.7, ((Number(settings.reverb) || 50) - 50) / 50 * 0.7));
    track.reverbNodes.wetGain.gain.value = wet;
    track.reverbNodes.dryGain.gain.value = Math.max(0.45, 1 - wet * 0.55);
  }
  if (track.compressionNode) {
    const amount = Math.max(0, Math.min(1, ((Number(settings.compression) || 50) - 50) / 50));
    track.compressionNode.threshold.value = -8 - amount * 28;
    track.compressionNode.knee.value = 24 - amount * 12;
    track.compressionNode.ratio.value = 1 + amount * 7;
    track.compressionNode.attack.value = 0.004 + amount * 0.006;
    track.compressionNode.release.value = 0.22 - amount * 0.12;
  }
}

function setEqValue(trackName, bandKey, value) {
  const settings = ensureMixSettings(trackName);
  const numeric = Number(value);
  const fallback = ["volume", "reverb", "compression"].includes(bandKey) ? 50 : 0;
  const safeValue = Number.isFinite(numeric) ? numeric : fallback;
  settings[bandKey] = ["volume", "reverb", "compression"].includes(bandKey)
    ? Math.max(0, Math.min(100, safeValue))
    : Math.max(-12, Math.min(12, safeValue));
  const track = state.tracks.get(trackName);
  if (track) {
    applyEqToTrack(track);
    applyTrackMix();
  }
}

function resetEq(trackName) {
  state.mixSettings.set(trackName, neutralMixSettings());
  const track = state.tracks.get(trackName);
  if (track) applyEqToTrack(track);
  applyTrackMix();
  renderEditMix();
}

function applyPreset(trackName) {
  state.mixSettings.set(trackName, { ...(MIX_PRESETS[trackName] || neutralMixSettings()) });
  const track = state.tracks.get(trackName);
  if (track) applyEqToTrack(track);
  applyTrackMix();
  renderEditMix();
}

function toggleHdMaster() {
  state.hdMaster = !state.hdMaster;
  rebuildMasterChain();
  updateMixStatus();
}

function updateMixStatus() {
  els.hdMasterButton.textContent = state.hdMaster ? "On" : "Off";
  els.hdMasterButton.setAttribute("aria-pressed", String(state.hdMaster));
  els.hdMasterButton.classList.toggle("active", state.hdMaster);
  els.mixStatus.textContent = state.hdMaster
    ? "Live HD master chain active"
    : "Live browser mix";
}

async function loadMixSettings() {
  if (!state.job) return;
  try {
    const response = await fetch(`/api/jobs/${encodeURIComponent(state.job.job_id)}/mix-settings`);
    if (!response.ok) return;
    const data = await response.json();
    const settings = data.settings || {};
    state.hdMaster = Boolean(settings.hdMaster);
    state.playbackRate = Number(settings.playbackRate) || state.playbackRate;
    els.tempoSlider.value = String(Math.round(state.playbackRate * 100));
    for (const [trackName, trackSettings] of Object.entries(settings.tracks || {})) {
      state.mixSettings.set(trackName, {
        ...ensureMixSettings(trackName),
        ...trackSettings,
      });
      state.mixSettings.get(trackName).volume = normalizeSavedVolumeLevel(trackSettings.volume);
      const track = state.tracks.get(trackName);
      if (track) {
        track.volume = volumeLevelToGain(state.mixSettings.get(trackName).volume);
        track.muted = Boolean(trackSettings.muted);
        track.solo = Boolean(trackSettings.solo);
        track.row.querySelector(".volume").value = String(track.volume);
        track.row.querySelector(".mute").classList.toggle("active", track.muted);
        track.row.querySelector(".solo").classList.toggle("active", track.solo);
      }
    }
    const practiceZone = settings.practiceZone || {};
    state.loopStart = parseOptionalTime(practiceZone.start);
    state.loopEnd = parseOptionalTime(practiceZone.end);
    state.loopMode = ["regular", "practice"].includes(practiceZone.mode) ? practiceZone.mode : "regular";
    els.loopModeSelect.value = state.loopMode;
    state.practiceMuteTracks = new Set((practiceZone.muteTracks || []).filter((name) => TRACK_ORDER.includes(name)));
    applyEqToAllTracks();
    applyTrackMix();
    updateMixStatus();
    updateLoopStatus();
    renderPracticeMuteControls();
    updateTempoReadout();
  } catch {
    // Saved mix settings are optional.
  }
}

async function saveMixSettings() {
  if (!state.job) return;
  const response = await fetch(`/api/jobs/${encodeURIComponent(state.job.job_id)}/mix-settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ settings: serializeMixSettings() }),
  });
  els.mixStatus.textContent = response.ok ? "Mix saved" : "Could not save mix";
}

function serializeMixSettings() {
  const tracks = {};
  for (const track of state.tracks.values()) {
    const settings = ensureMixSettings(track.name);
    settings.volume = normalizeVolumeLevel(settings.volume);
    tracks[track.name] = {
      ...settings,
      muted: track.muted,
      solo: track.solo,
    };
  }
  return {
    hdMaster: state.hdMaster,
    playbackRate: state.playbackRate,
    practiceZone: {
      mode: state.loopMode,
      start: state.loopStart,
      end: state.loopEnd,
      muteTracks: [...state.practiceMuteTracks],
    },
    tracks,
  };
}

async function renderHdMix(options = {}) {
  if (!state.job) return;
  const isShiftedRender = Boolean(options.shifted);
  els.hdExportButton.disabled = true;
  els.hdExportButton.textContent = "Rendering...";
  const format = els.exportFormat.value;
  const preset = els.exportPreset.value;
  els.mixStatus.textContent = preset === "stems_zip" ? "Preparing stems ZIP..." : `Rendering ${format.toUpperCase()}...`;
  if (isShiftedRender) updateShiftedMixStatus("rendering");
  try {
    const response = await fetch(`/api/jobs/${encodeURIComponent(state.job.job_id)}/exports/hd-mix`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildHdMixPayload()),
    });
    if (!response.ok) {
      const errorText = await response.text();
      els.mixStatus.textContent = errorText;
      if (isShiftedRender) updateShiftedMixStatus("error", errorText);
      return null;
    }
    const result = await response.json();
    els.mixStatus.innerHTML = `<a href="${escapeHtml(result.url)}" download>${escapeHtml(result.filename)}</a>`;
    if (isShiftedRender) updateShiftedMixStatus("ready", result.filename, result.url);
    return result;
  } catch {
    els.mixStatus.textContent = "HD render failed.";
    if (isShiftedRender) updateShiftedMixStatus("error", "Shifted mix failed");
    return null;
  } finally {
    els.hdExportButton.disabled = false;
    els.hdExportButton.textContent = "Render WAV";
  }
}

function buildHdMixPayload() {
  const hasSolo = [...state.tracks.values()].some((track) => track.solo);
  const tracks = {};
  for (const track of state.tracks.values()) {
    const eq = ensureMixSettings(track.name);
    tracks[track.name] = {
      volume: volumeLevelToGain(eq.volume),
      muted: track.muted || (hasSolo && !track.solo),
      low: eq.low,
      mid: eq.mid,
      high: eq.high,
      reverb: eq.reverb,
      compression: eq.compression,
    };
  }
  return {
    hd_master: state.hdMaster,
    semitones: transposeSemitones(),
    format: els.exportFormat.value,
    preset: els.exportPreset.value,
    tracks,
  };
}

async function renderShiftedMix() {
  if (!state.job) return;
  if (transposeSemitones() === 0) {
    updateShiftedMixStatus("error", "Choose a new key");
    els.audioKeyStatus.textContent = "Choose a different key first, then render the shifted mix.";
    return;
  }
  const previousPreset = els.exportPreset.value;
  const previousFormat = els.exportFormat.value;
  els.exportPreset.value = "full";
  els.exportFormat.value = "wav";
  await renderHdMix({ shifted: true });
  els.exportPreset.value = previousPreset;
  els.exportFormat.value = previousFormat;
}

function updateShiftedMixStatus(status, filename = null, url = null) {
  if (!els.globalShiftedMixButton || !els.globalShiftedMixText) return;
  els.globalShiftedMixButton.classList.remove("rendering", "ready", "error");
  if (status === "rendering") {
    state.shiftedMixUrl = null;
    state.shiftedMixFilename = null;
    els.globalShiftedMixButton.disabled = true;
    els.globalShiftedMixButton.classList.add("rendering");
    els.globalShiftedMixText.textContent = "Rendering shifted mix";
    return;
  }
  if (status === "ready") {
    state.shiftedMixUrl = url;
    state.shiftedMixFilename = filename;
    els.globalShiftedMixButton.disabled = false;
    els.globalShiftedMixButton.classList.add("ready");
    els.globalShiftedMixText.textContent = filename || "Shifted mix ready";
    return;
  }
  if (status === "error") {
    state.shiftedMixUrl = null;
    state.shiftedMixFilename = null;
    els.globalShiftedMixButton.disabled = true;
    els.globalShiftedMixButton.classList.add("error");
    els.globalShiftedMixText.textContent = filename || "Shifted mix failed";
    return;
  }
  state.shiftedMixUrl = null;
  state.shiftedMixFilename = null;
  els.globalShiftedMixButton.disabled = true;
  els.globalShiftedMixText.textContent = "No shifted mix";
}

function openShiftedMix() {
  if (!state.shiftedMixUrl) return;
  window.open(state.shiftedMixUrl, "_blank", "noopener");
}

function renderEditMix() {
  if (!els.editMixDeck) return;
  updateMixStatus();
  updateLoopStatus();
  renderPracticeMuteControls();
  els.editMixDeck.innerHTML = "";
  if (!state.job || !state.tracks.size) {
    els.editMixDeck.innerHTML = '<div class="empty">No separated songs yet.</div>';
    return;
  }

  for (const name of TRACK_ORDER) {
    const track = state.tracks.get(name);
    if (!track) continue;
    const settings = ensureMixSettings(name);
    const strip = document.createElement("article");
    strip.className = "mix-strip";
    strip.innerHTML = `
      <div class="mix-strip-title">
        <span class="instrument-badge" aria-label="${TRACK_LABELS[name]}" title="${TRACK_LABELS[name]}">${TRACK_INSTRUMENTS[name] || "🎚️"}</span>
        <strong>${TRACK_LABELS[name]}</strong>
      </div>
      <div class="eq-bank">
        <label class="eq-control volume-control">
          <span>Vol</span>
          <input type="range" min="0" max="100" step="1" value="${settings.volume ?? 50}" data-track="${name}" data-band="volume" />
          <strong>${formatPercent(settings.volume ?? 50)}</strong>
        </label>
        ${EQ_BANDS.map((band) => `
          <label class="eq-control">
            <span>${band.label}</span>
            <input type="range" min="-12" max="12" step="1" value="${settings[band.key]}" data-track="${name}" data-band="${band.key}" />
            <strong>${formatDb(settings[band.key])}</strong>
          </label>
        `).join("")}
        <label class="eq-control reverb-control">
          <span>Verb</span>
          <input type="range" min="0" max="100" step="1" value="${settings.reverb ?? 50}" data-track="${name}" data-band="reverb" />
          <strong>${formatPercent(settings.reverb ?? 50)}</strong>
        </label>
        <label class="eq-control compression-control">
          <span>Comp</span>
          <input type="range" min="0" max="100" step="1" value="${settings.compression ?? 50}" data-track="${name}" data-band="compression" />
          <strong>${formatPercent(settings.compression ?? 50)}</strong>
        </label>
      </div>
      <div class="mix-actions">
        <button class="track-button mix-mute-button ${track.muted ? "active" : ""}" type="button" data-mix-mute="${name}">Mute</button>
        <button class="secondary-button preset-button" type="button" data-preset="${name}">Preset</button>
        <button class="secondary-button reset-eq-button" type="button" data-reset="${name}">Flat</button>
      </div>
    `;
    els.editMixDeck.append(strip);
  }

  els.editMixDeck.querySelectorAll("[data-track][data-band]").forEach((slider) => {
    slider.addEventListener("input", (event) => {
      setEqValue(event.target.dataset.track, event.target.dataset.band, event.target.value);
      const valueText = ["volume", "reverb", "compression"].includes(event.target.dataset.band)
        ? formatPercent(event.target.value)
        : formatDb(event.target.value);
      event.target.closest(".eq-control")?.querySelector("strong").replaceChildren(valueText);
    });
  });
  els.editMixDeck.querySelectorAll("[data-mix-mute]").forEach((button) => {
    button.addEventListener("click", () => toggleTrackMute(button.dataset.mixMute));
  });
  els.editMixDeck.querySelectorAll("[data-preset]").forEach((button) => {
    button.addEventListener("click", () => applyPreset(button.dataset.preset));
  });
  els.editMixDeck.querySelectorAll("[data-reset]").forEach((button) => {
    button.addEventListener("click", () => resetEq(button.dataset.reset));
  });
}

function renderPracticeMuteControls() {
  if (!els.practiceMuteList) return;
  els.practiceMuteList.innerHTML = "";
  if (!state.job || !state.tracks.size) {
    els.practiceMuteList.innerHTML = '<span class="practice-zone-empty">Split a song first.</span>';
    return;
  }
  for (const name of TRACK_ORDER) {
    if (!state.tracks.has(name)) continue;
    const button = document.createElement("button");
    const active = state.practiceMuteTracks.has(name);
    button.className = `practice-mute-chip ${active ? "active" : ""}`;
    button.type = "button";
    button.setAttribute("aria-pressed", String(active));
    button.innerHTML = `
      <span class="instrument-badge" aria-label="${TRACK_LABELS[name]}" title="${TRACK_LABELS[name]}">${TRACK_INSTRUMENTS[name] || "🎚️"}</span>
      <strong>${TRACK_LABELS[name]}</strong>
    `;
    button.addEventListener("click", () => {
      if (state.practiceMuteTracks.has(name)) {
        state.practiceMuteTracks.delete(name);
      } else {
        state.practiceMuteTracks.add(name);
      }
      applyTrackMix();
      renderPracticeMuteControls();
    });
    els.practiceMuteList.append(button);
  }
}

function parseOptionalTime(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatDb(value) {
  const db = Number(value) || 0;
  if (db === 0) return "0 dB";
  return `${db > 0 ? "+" : ""}${db} dB`;
}

function formatPercent(value) {
  return `${Math.round(Number(value) || 0)}%`;
}

function setLoopStart() {
  state.loopStart = getMaster()?.currentTime || 0;
  if (state.loopEnd !== null && state.loopEnd <= state.loopStart) state.loopEnd = null;
  updateLoopStatus();
}

function setLoopEnd() {
  state.loopEnd = getMaster()?.currentTime || 0;
  if (state.loopStart === null || state.loopStart >= state.loopEnd) {
    state.loopStart = 0;
  }
  updateLoopStatus();
}

function clearLoop() {
  state.loopStart = null;
  state.loopEnd = null;
  updateLoopStatus();
  applyTrackMix();
}

function updateLoopStatus() {
  const running = hasActiveRange();
  const isPractice = state.loopMode === "practice";
  const activeLabel = isPractice ? "Practice Zone Active" : "Loop Running";
  const offLabel = isPractice ? "Practice Zone off" : "Loop off";
  const text = running
    ? `${activeLabel} ${formatTime(state.loopStart)} - ${formatTime(state.loopEnd)}`
    : offLabel;
  for (const node of [els.loopStatus, els.globalLoopStatus]) {
    if (!node) continue;
    node.classList.toggle("loop-running", running);
    node.textContent = text;
  }
  updateLoopBarHighlights();
}

function setLoopMode(mode) {
  state.loopMode = mode === "practice" ? "practice" : "regular";
  els.loopModeSelect.value = state.loopMode;
  updateLoopStatus();
  applyTrackMix();
  renderPracticeMuteControls();
}

function hasActiveRange() {
  return state.loopStart !== null && state.loopEnd !== null;
}

function isPracticeZoneActiveAt(time) {
  return hasActiveRange()
    && time >= state.loopStart
    && time < state.loopEnd;
}

function updateLoopBarHighlights() {
  const running = hasActiveRange();
  const tempo = state.tempo || normalizeTempo(null);
  document.querySelectorAll("[data-bar-index]").forEach((node) => {
    const index = Number(node.dataset.barIndex);
    const barStart = index * tempo.secondsPerBar;
    const barEnd = barStart + tempo.secondsPerBar;
    const inLoop = running && barEnd > state.loopStart && barStart < state.loopEnd;
    node.classList.toggle("loop-range", inLoop);
  });
}

async function playCountIn() {
  state.countInActive = true;
  const beats = 4;
  const interval = (60 / (state.tempo?.bpm || 120)) * 1000;
  for (let beat = 0; beat < beats; beat += 1) {
    playClick(beat === 0 ? 1320 : 920);
    await new Promise((resolve) => window.setTimeout(resolve, interval));
  }
  state.countInActive = false;
}

function startOrStopClick() {
  stopClick();
  if (!els.metronomeToggle.checked || !state.playing) return;
  const interval = (60 / (state.tempo?.bpm || 120)) * 1000 / state.playbackRate;
  playClick(1100);
  state.clickTimer = window.setInterval(() => {
    if (!state.playing || getMaster()?.paused || !els.metronomeToggle.checked) {
      stopClick();
      return;
    }
    playClick(880);
  }, interval);
}

function stopClick() {
  if (state.clickTimer) {
    window.clearInterval(state.clickTimer);
    state.clickTimer = null;
  }
}

function playClick(frequency) {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  const context = state.audioContext || (AudioContextClass ? new AudioContextClass() : null);
  if (!context) return;
  if (!state.audioContext) state.audioContext = context;
  const osc = context.createOscillator();
  const gain = context.createGain();
  osc.frequency.value = frequency;
  gain.gain.setValueAtTime(0.0001, context.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.38, context.currentTime + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + 0.08);
  osc.connect(gain);
  gain.connect(context.destination);
  osc.start();
  osc.stop(context.currentTime + 0.09);
}

function createReverbImpulse() {
  if (state.reverbImpulse || !state.audioContext) return state.reverbImpulse;
  const sampleRate = state.audioContext.sampleRate;
  const length = Math.round(sampleRate * 1.6);
  const impulse = state.audioContext.createBuffer(2, length, sampleRate);
  for (let channel = 0; channel < impulse.numberOfChannels; channel += 1) {
    const data = impulse.getChannelData(channel);
    for (let index = 0; index < length; index += 1) {
      const decay = Math.pow(1 - index / length, 2.4);
      data[index] = (Math.random() * 2 - 1) * decay;
    }
  }
  state.reverbImpulse = impulse;
  return impulse;
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
  if (state.playing) startOrStopClick();
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

  els.currentChord.textContent = activeSegment ? displayChord(activeSegment.chord) : "--";
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
  state.activeView = ["chord", "key", "edit"].includes(view) ? view : "track";
  els.tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.view === state.activeView);
  });
  els.trackView.classList.toggle("active", state.activeView === "track");
  els.chordView.classList.toggle("active", state.activeView === "chord");
  els.keyView.classList.toggle("active", state.activeView === "key");
  els.editMixView.classList.toggle("active", state.activeView === "edit");
  if (state.activeView === "edit") renderEditMix();
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
  updateAudioKeyStatus();
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

function updateAudioKeyStatus() {
  if (!els.audioKeyStatus) return;
  const semitones = transposeSemitones();
  els.audioKeyStatus.textContent = semitones === 0
    ? "Tracks are playing in the original recorded key."
    : `Chart is transposed ${formatSemitones(semitones)}; audio is still original until shifted tracks are rendered.`;
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

function displayChord(chord) {
  const normalized = String(chord || "").trim();
  if (!normalized || normalized === "N") return "~";
  return transposeChord(normalized);
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
  if (!window.confirm(`Remove "${songName}" from Wannabe Stem?`)) return;

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
    acoustic_guitar: "#ff8a3d",
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
