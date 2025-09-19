// static/js/recording_wiring.js
(() => {
  let socket;
  const SESSION_ID = String(Date.now());
  let stream = null, mediaRecorder = null, starting = false;
  let audioCtx, analyser, dataArray, rafId = null;

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

  function transports() {
    const force = !!(window.MINA && window.MINA.FORCE_POLLING);
    return force ? ["polling"] : ["websocket","polling"];
  }

  function initSocket() {
    if (socket && socket.connected) return;

    const path = (window.MINA && window.MINA.SOCKETIO_PATH) || "/socket.io";
    const force = !!(window.MINA && window.MINA.FORCE_POLLING);

    socket = io(window.location.origin, {
      path,
      transports: transports(),
      upgrade: !force,
      reconnection: true,
      reconnectionAttempts: 30,
      reconnectionDelay: 500,
      timeout: 10000,
    });

    socket.on("connect", () => {
      ui.ws.textContent = "Connected";
      log("socket connected", { id: socket.id, transport: socket.io.engine.transport.name });
      socket.emit("join_session", { session_id: SESSION_ID });
    });
    socket.on("disconnect", (r) => { ui.ws.textContent = "Disconnected"; log("socket disconnected", r); });
    socket.on("connect_error", (e) => { ui.ws.textContent = "Conn error"; log("connect_error", e?.message || e); });

    socket.on("server_hello", (m) => log("server_hello", m));
    socket.on("ack", () => {});
    socket.on("error", (e) => log("socket error", e));
    socket.on("socket_error", (e) => log("transcription error", e));
    socket.on("debug", (m) => log("DEBUG", m?.message || m));

    socket.on("interim_transcript", (p) => { ui.interim.textContent = p?.text || ""; });
    socket.on("final_transcript", (p) => {
      const t = (p?.text || "").trim();
      if (!t) return;
      const prior = ui.final.textContent.trim();
      ui.final.textContent = (prior ? prior + " " : "") + t;
      ui.interim.textContent = "";
    });
  }

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
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const v = (dataArray[i] - 128) / 128;
        sum += v*v;
      }
      const rms = Math.sqrt(sum / dataArray.length);
      const pct = Math.min(100, Math.max(0, Math.round(rms * 140)));
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

  async function startRecording() {
    if (starting || (mediaRecorder && mediaRecorder.state === "recording")) return;
    starting = true;

    initSocket();
    if (!socket || !socket.connected) log("socket not connected yet (will buffer events)");

    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      starting = false;
      ui.mic.textContent = "Mic denied";
      log("❌ microphone permission denied", e);
      return;
    }

    ui.mic.textContent = "Recording…";

    let mime = "audio/webm;codecs=opus";
    if (!MediaRecorder.isTypeSupported(mime)) {
      if (MediaRecorder.isTypeSupported("audio/webm")) mime = "audio/webm";
      else if (MediaRecorder.isTypeSupported("audio/ogg;codecs=opus")) mime = "audio/ogg;codecs=opus";
      else mime = "";
    }

    mediaRecorder = new MediaRecorder(stream, { mimeType: mime, audioBitsPerSecond: 128000 });

    mediaRecorder.ondataavailable = async (e) => {
      if (!e.data || e.data.size === 0) return;
      try {
        const buf = await e.data.arrayBuffer();
        const b64 = btoa(String.fromCharCode(...new Uint8Array(buf)));
        socket.emit("audio_chunk", {
          session_id: SESSION_ID,
          audio_data_b64: b64,
          mime: e.data.type || mime || "audio/webm",
          duration_ms: 0
        });
        log("chunk ->", { size: e.data.size });
      } catch (err) {
        log("chunk encode error", err);
      }
    };

    mediaRecorder.onstop = () => {
      stopMeter();
      ui.mic.textContent = "Stopped";
      socket.emit("finalize_session", {
        session_id: SESSION_ID,
        mime: mediaRecorder.mimeType || mime || "audio/webm"
      });
      try { stream.getTracks().forEach(t => t.stop()); } catch {}
      stream = null;
      log("recording stopped");
      starting = false;
    };

    mediaRecorder.start(1200); // ~1.2s slices -> matches server cadence
    startMeter();
    log("recording started", { mime });
    starting = false;
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
  }

  ui.start?.addEventListener("click", startRecording);
  ui.stop?.addEventListener("click", stopRecording);
  initSocket();
})();