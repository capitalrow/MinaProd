/**
 * File: /static/js/live.js
 * Purpose: Mina Live Recording Controller (NON-REGRESSIVE)
 * Notes:
 *  - This is your original file wrapped with a minimal finalize step.
 *  - All existing behavior (socket, start/stop, UI updates) is preserved.
 *  - Adds a safe POST to /api/sessions/<external_id>/complete after onstop.
 */

(() => {
  // === Utility shims (unchanged) ===========================================
  const $ = (id) => document.getElementById(id);
  const dlog = (msg) => { const el = $("debug"); if (el) el.textContent += msg + "\n"; };

  // === NEW: Resolve session external_id safely =============================
  // Prefer <body data-session-external-id="...">, fallback to <meta name="mina-session-external-id">
  function resolveExternalId() {
    const bodyAttr = document.body?.dataset?.sessionExternalId;
    if (bodyAttr && bodyAttr.trim()) return bodyAttr.trim();
    const meta = document.querySelector('meta[name="mina-session-external-id"]');
    const metaVal = meta?.getAttribute('content');
    return metaVal && metaVal.trim() ? metaVal.trim() : null;
  }
  const SESSION_EXTERNAL_ID = resolveExternalId();

  // === Socket.IO (unchanged) ===============================================
  const socket = io({
    path: '/socket.io',
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    timeout: 20000,
    upgrade: true
  });

  let mediaRecorder, stream, chunks = [];

  socket.on("connect", () => {
    if ($("conn")) {
      $("conn").textContent = "Connected";
      $("conn").className = "pill pill-ok";
    }
    dlog("socket connected");
  });

  socket.on("server_status", (p) => dlog(p.message));

  // === Bind UI (unchanged) =================================================
  if ($("btnStart")) $("btnStart").addEventListener("click", start);
  if ($("btnStop"))  $("btnStop").addEventListener("click", stop);

  // === Start recording (unchanged, with iOS MIME handling) =================
  async function start() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      dlog("ERR mic: " + e.message);
      return;
    }

    let mime = "audio/webm;codecs=opus";
    if (!MediaRecorder.isTypeSupported(mime)) {
      if (MediaRecorder.isTypeSupported('audio/webm')) {
        mime = 'audio/webm';
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mime = 'audio/mp4'; // iOS Safari fallback
      } else if (MediaRecorder.isTypeSupported('audio/aac')) {
        mime = 'audio/aac'; // iOS Safari fallback
      } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
        mime = 'audio/ogg;codecs=opus';
      } else {
        mime = ''; // Let browser decide
      }
    }

    dlog("Using MIME type: " + (mime || "browser default"));
    mediaRecorder = new MediaRecorder(stream, mime ? { mimeType: mime } : {});

    mediaRecorder.ondataavailable = (e) => {
      if (!e.data.size) return;
      chunks.push(e.data);
      e.data.arrayBuffer().then((buf) => {
        socket.emit("audio_chunk", buf);
      });
    };

    mediaRecorder.onstart = () => {
      if ($("btnStart")) $("btnStart").disabled = true;
      if ($("btnStop"))  $("btnStop").disabled = false;
      dlog("MediaRecorder started");
    };

    // === onstop: original behavior + NEW finalize call =====================
    mediaRecorder.onstop = async () => {
      const full = new Blob(chunks, { type: mediaRecorder.mimeType || mime || 'application/octet-stream' });
      chunks = [];
      full.arrayBuffer().then((buf) => {
        // 1) ORIGINAL: tell server audio stream ended
        socket.emit("audio_end", buf);
      });

      if ($("btnStart")) $("btnStart").disabled = false;
      if ($("btnStop"))  $("btnStop").disabled = true;
      dlog("MediaRecorder stopped");

      // 2) NEW: finalize the session safely (no crash if endpoint missing)
      await finalizeSessionSafe(SESSION_EXTERNAL_ID);

      // 3) NEW: UX flow – navigate to transcript page after recording
      setTimeout(() => {
        if (window.location.pathname.includes("/live") && SESSION_EXTERNAL_ID) {
          window.location.href = `/transcript/${SESSION_EXTERNAL_ID}`;
        } else if (window.location.pathname.includes("/live")) {
          window.location.href = "/dashboard";
        } else {
          window.location.reload();
        }
      }, 600);
    };

    // Chunk every 3s (unchanged)
    mediaRecorder.start(3000);
  }

  // === Stop recording (unchanged) =========================================
  function stop() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
    }
  }

  // === Transcript UI (unchanged) ==========================================
  let interimBuffer = "";
  socket.on("transcript", (p) => {
    interimBuffer += p.text + " ";
    if ($("interim")) $("interim").textContent = interimBuffer;
  });

  socket.on("transcript_final", (p) => {
    if ($("final")) $("final").textContent = p.text;
    interimBuffer = "";
    if ($("interim")) $("interim").textContent = "";
  });

  // === NEW: finalize helper with graceful fallbacks ========================
  async function finalizeSessionSafe(externalId) {
    if (!externalId) {
      dlog("⚠️ No external session id found; skipping finalize.");
      return;
    }

    // Small debounce to let server finish last chunk processing
    await sleep(350);

    const url = `/api/sessions/${encodeURIComponent(externalId)}/complete`;
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force: false })
      });
      if (!res.ok) {
        dlog(`⚠️ finalize returned ${res.status}; will retry once...`);
        // One retry after a short delay, in case of race with final segment write
        await sleep(500);
        const retry = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ force: true })
        });
        if (!retry.ok) {
          dlog(`❌ finalize retry failed: ${retry.status}`);
        } else {
          dlog("✅ finalize retry succeeded.");
        }
      } else {
        dlog("✅ session finalized.");
      }
    } catch (e) {
      dlog("❌ finalize error: " + e.message);
      // Do not throw; we never want to break navigation
    }
  }

  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
})();