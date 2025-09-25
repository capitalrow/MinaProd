// static/js/recording_wiring.js
// Full drop-in client aligned to templates/live.html IDs, with detailed error surfacing.
(() => {
  let socket;
  const SESSION_ID = String(Date.now());
  let stream = null, mediaRecorder = null;
  let audioCtx = null, analyser = null, dataArray = null, rafId = null;

  // ---------- UI helpers ----------
  const $ = (sel) => document.querySelector(sel);
  const ui = {
    start: $("#startRecordingBtn"),
    stop: $("#stopRecordingBtn"),
    ws: $("#wsStatus"),
    mic: $("#micStatus"),
    sess: $("#sess"),
    meter: $("#meter"),
    meterFill: $("#meterFill"),
    interim: $("#interimText"),
    final: $("#finalText"),
    debug: $("#debug"),
  };

  const log = (...a) => {
    const s = a.map(x => (typeof x === "object" ? JSON.stringify(x) : String(x))).join(" ");
    console.log("[mina]", s);
    if (ui.debug) {
      const p = document.createElement("div");
      p.textContent = s;
      ui.debug.appendChild(p);
      ui.debug.scrollTop = ui.debug.scrollHeight;
    }
  };

  function setWs(status) { if (ui.ws) ui.ws.textContent = status; }
  function setMic(status) { if (ui.mic) ui.mic.textContent = status; }
  function setSess(id) { if (ui.sess) ui.sess.textContent = id; }
  function setInterim(t) { if (ui.interim) ui.interim.textContent = t; }
  function setFinal(t) { if (ui.final) ui.final.textContent = t; }

  // ---------- Meter ----------
  function startMeter(stream) {
    if (!window.AudioContext) return;
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaStreamSource(stream);
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 512;
    const bufferLen = analyser.frequencyBinCount;
    dataArray = new Uint8Array(bufferLen);
    source.connect(analyser);

    const draw = () => {
      analyser.getByteTimeDomainData(dataArray);
      let peak = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const v = Math.abs(dataArray[i] - 128);
        if (v > peak) peak = v;
      }
      const pct = Math.min(100, Math.round((peak / 128) * 100));
      if (ui.meterFill) ui.meterFill.style.width = pct + "%";
      rafId = requestAnimationFrame(draw);
    };
    draw();
  }

  function stopMeter() {
    if (rafId) cancelAnimationFrame(rafId), rafId = null;
    if (audioCtx) { try { audioCtx.close(); } catch {} audioCtx = null; }
    analyser = null; dataArray = null;
    if (ui.meterFill) ui.meterFill.style.width = "0%";
  }

  // ---------- Socket.IO ----------
  function initSocket() {
    if (socket) return socket;
    // Keep your original transport settings (avoid regressions on Replit)
    socket = io({
      path: "/socket.io",
      transports: ["polling"],
      upgrade: false,
      reconnection: true,
      reconnectionAttempts: 30,
      reconnectionDelay: 500,
      timeout: 10000,
    });

    socket.on("connect", () => {
      setWs("Connected");
      log("socket connected id=", socket.id, "transport=", socket.io.engine.transport.name);
      socket.emit("join_session", { session_id: SESSION_ID });
    });
    socket.on("disconnect", (r) => { setWs("Disconnected"); log("socket disconnected", r); });
    socket.on("connect_error", (e) => { setWs("Conn error"); log("connect_error", e?.message || e); });

    socket.on("server_hello", (m) => log("server_hello", m));
    socket.on("ack", () => { /* for RTT if needed */ });

    // Enhanced error surfacing (details go to Interim panel as requested)
    socket.on("error", (e) => {
      log("socket error", e);
      if (e && e.detail) setInterim("[server] " + (e.detail || e.message || "error"));
    });
    socket.on("socket_error", (e) => {
      log("transcription error", e);
      if (e && e.detail) setInterim("[transcription] " + (e.detail || e.message || "error"));
    });

    socket.on("interim_transcript", (p) => {
      setInterim(p?.text || "");
    });

    socket.on("final_transcript", (p) => {
      const t = (p?.text || "").trim();
      if (!t) return;
      const prior = (ui.final?.textContent || "").trim();
      // append with spacing for readability
      setFinal(prior ? (prior + (prior.endsWith(".") ? " " : ". ") + t) : t);
    });

    return socket;
  }

  // ---------- Recording ----------
  async function startRecording() {
    initSocket();
    if (!socket || !socket.connected) {
      log("socket not connected yet");
    }

    // Ask mic
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      log("getUserMedia failure", err);
      setInterim("[mic] " + (err?.message || "Microphone access failed"));
      return;
    }
    setMic("Recording…");

    // Prefer webm/opus, fall back as needed
    let mime = "audio/webm;codecs=opus";
    if (!MediaRecorder.isTypeSupported(mime)) {
      if (MediaRecorder.isTypeSupported("audio/webm")) mime = "audio/webm";
      else if (MediaRecorder.isTypeSupported("audio/ogg;codecs=opus")) mime = "audio/ogg;codecs=opus";
      else mime = ""; // let browser decide
    }

    try {
      mediaRecorder = new MediaRecorder(stream, { mimeType: mime, audioBitsPerSecond: 128000 });
    } catch (err) {
      log("MediaRecorder init failed", err);
      setInterim("[recorder] " + (err?.message || "Failed to initialize MediaRecorder"));
      return;
    }

    // Meter & reset panels
    startMeter(stream);
    setInterim("");
    setFinal("");
    setSess(SESSION_ID);

    mediaRecorder.ondataavailable = async (e) => {
      try {
        if (!e.data || e.data.size === 0) return;
        // Blob -> base64
        const buf = await e.data.arrayBuffer();
        const b64 = btoa(String.fromCharCode(...new Uint8Array(buf)));
        socket.emit("audio_chunk", {
          session_id: SESSION_ID,
          audio_data_b64: b64,
          mime: e.data.type || mime || "audio/webm",
          duration_ms: 0
        });
      } catch (err) {
        log("chunk send failed", err);
      }
    };

    mediaRecorder.onstop = () => {
      stopMeter();
      setMic("Stopped");
      // Ask server to finalize after the last ondataavailable
      setTimeout(() => {
        socket.emit("finalize_session", {
          session_id: SESSION_ID,
          mime: mediaRecorder?.mimeType || mime || "audio/webm"
        });
      }, 300);
      try { stream.getTracks().forEach(t => t.stop()); } catch {}
      stream = null;
    };

    mediaRecorder.start(1200); // request 1.2s chunks
    log("MediaRecorder started", mime || "(browser default)");
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
  }

  // ---------- Wire UI ----------
  ui.start?.addEventListener("click", startRecording);
  ui.stop?.addEventListener("click", stopRecording);

  // Connect early so join_session is ready before recording
  initSocket();
  setSess(SESSION_ID);
  setWs(socket?.connected ? "Connected" : "Disconnected");
  setMic("Idle");
})();