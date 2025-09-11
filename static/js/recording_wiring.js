// static/js/recording_wiring.js
(() => {
  let socket;
  const SESSION_ID = String(Date.now());
  let stream, mediaRecorder;
  let audioCtx, analyser, dataArray, rafId = null;

  // UI helpers
  const $ = sel => document.querySelector(sel);
  const log = (...a) => {
    const s = a.map(x => (typeof x === "object" ? JSON.stringify(x) : String(x))).join(" ");
    console.log("[mina]", s);
    const dbg = $("#debug");
    if (dbg) { const p = document.createElement("div"); p.textContent = s; dbg.appendChild(p); dbg.scrollTop = dbg.scrollHeight; }
  };

  const ui = {
    start: $("#startRecordingBtn"),
    stop:  $("#stopRecordingBtn"),
    ws:    $("#wsStatus"),
    mic:   $("#micStatus"),
    meter: $("#meterFill"),
    interim: $("#interimText"),
    final: $("#finalText"),
    sess: $("#sess"),
  };
  if (ui.sess) ui.sess.textContent = SESSION_ID;

  // ---- Socket.IO (polling only is fine on Replit)
  function initSocket() {
    if (socket && socket.connected) return;

    socket = io(window.location.origin, {
      path: "/socket.io",
      transports: ["polling"],
      upgrade: false,
      reconnection: true,
      reconnectionAttempts: 30,
      reconnectionDelay: 500,
      timeout: 10000,
    });

    socket.on("connect", () => {
      ui.ws.textContent = "Connected";
      log("socket connected id=", socket.id, "transport=", socket.io.engine.transport.name);
      socket.emit("join_session", { session_id: SESSION_ID });
    });
    socket.on("disconnect", (r) => { ui.ws.textContent = "Disconnected"; log("socket disconnected", r); });
    socket.on("connect_error", (e) => { ui.ws.textContent = "Conn error"; log("connect_error", e?.message || e); });

    socket.on("server_hello", (m) => log("server_hello", m));
    socket.on("ack", () => { /* rtt tracking if needed */ });

    socket.on("error", (e) => log("socket error", e));
    socket.on("socket_error", (e) => log("transcription error", e));

    socket.on("interim_transcript", (p) => {
      ui.interim.textContent = p?.text || "";
    });

    socket.on("final_transcript", (p) => {
      const t = (p?.text || "").trim();
      if (!t) return;
      const prior = ui.final.textContent.trim();
      ui.final.textContent = (prior ? prior + " " : "") + t;
      ui.interim.textContent = "";
    });
  }

  // ---- Audio meter
  function startMeter() {
    if (!stream) return;
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const src = audioCtx.createMediaStreamSource(stream);
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 512;
    dataArray = new Uint8Array(analyser.frequencyBinCount);
    src.connect(analyser);

    const tick = () => {
      analyser.getByteTimeDomainData(dataArray);
      // RMS-like level
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const v = (dataArray[i] - 128) / 128;
        sum += v*v;
      }
      const rms = Math.sqrt(sum / dataArray.length);
      const pct = Math.min(100, Math.max(0, Math.round(rms * 140))); // 0..~140%
      if (ui.meter) ui.meter.style.width = pct + "%";
      rafId = requestAnimationFrame(tick);
    };
    tick();
  }
  function stopMeter() {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = null;
    try { audioCtx && audioCtx.close(); } catch {}
    audioCtx = null; analyser = null; dataArray = null;
    if (ui.meter) ui.meter.style.width = "0%";
  }

  // ---- Recording
  async function startRecording() {
    initSocket();
    if (!socket || !socket.connected) {
      log("socket not connected yet");
    }

    // Ask mic
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    ui.mic.textContent = "Recording…";

    // Try webm/opus (widest support); fall back if needed
    let mime = "audio/webm;codecs=opus";
    if (!MediaRecorder.isTypeSupported(mime)) {
      if (MediaRecorder.isTypeSupported("audio/webm")) mime = "audio/webm";
      else if (MediaRecorder.isTypeSupported("audio/ogg;codecs=opus")) mime = "audio/ogg;codecs=opus";
      else mime = ""; // let browser decide
    }

    mediaRecorder = new MediaRecorder(stream, { mimeType: mime, audioBitsPerSecond: 128000 });

    mediaRecorder.ondataavailable = async (e) => {
      if (!e.data || e.data.size === 0) return;
      // Convert Blob -> base64
      const buf = await e.data.arrayBuffer();
      const b64 = btoa(String.fromCharCode(...new Uint8Array(buf)));
      socket.emit("audio_chunk", {
        session_id: SESSION_ID,
        audio_data_b64: b64,
        mime: e.data.type || mime || "audio/webm",
        duration_ms: 0
      });
    };

    mediaRecorder.onstop = () => {
      stopMeter();
      ui.mic.textContent = "Stopped";
      // ask server to finalize (full pass)
      socket.emit("finalize_session", { session_id: SESSION_ID, mime: mediaRecorder.mimeType || mime || "audio/webm" });
      try { stream.getTracks().forEach(t => t.stop()); } catch {}
      stream = null;
    };

    // Emit blobs every ~1.2s (balanced latency/cost)
    mediaRecorder.start(1200);
    startMeter();
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
  }

  // ---- Wire UI
  ui.start?.addEventListener("click", startRecording);
  ui.stop?.addEventListener("click", stopRecording);

  // connect early so join_session is ready before recording
  initSocket();
})();
