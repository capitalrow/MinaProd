(() => {
  const $ = (id) => document.getElementById(id);
  const dlog = (msg) => { $("debug").textContent += msg + "\n"; };

  const socket = io({ transports: ["websocket", "polling"] });
  let mediaRecorder, stream, chunks = [];

  socket.on("connect", () => {
    $("conn").textContent = "Connected";
    $("conn").className = "pill pill-ok";
    dlog("socket connected");
  });

  socket.on("server_status", (p) => dlog(p.message));

  $("btnStart").addEventListener("click", start);
  $("btnStop").addEventListener("click", stop);

  async function start() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      dlog("ERR mic: " + e.message);
      return;
    }

    const mime = "audio/webm;codecs=opus";
    mediaRecorder = new MediaRecorder(stream, { mimeType: mime });

    mediaRecorder.ondataavailable = (e) => {
      if (!e.data.size) return;
      chunks.push(e.data);
      e.data.arrayBuffer().then((buf) => {
        socket.emit("audio_chunk", buf);
      });
    };

    mediaRecorder.onstart = () => {
      $("btnStart").disabled = true;
      $("btnStop").disabled = false;
      dlog("MediaRecorder started");
    };

    mediaRecorder.onstop = () => {
      const full = new Blob(chunks, { type: mime });
      chunks = [];
      full.arrayBuffer().then((buf) => {
        socket.emit("audio_end", buf);
      });
      $("btnStart").disabled = false;
      $("btnStop").disabled = true;
      dlog("MediaRecorder stopped");
    };

    mediaRecorder.start(3000); // chunk every 3s
  }

  function stop() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
    }
  }

  let interimBuffer = "";
  socket.on("transcript", (p) => {
    interimBuffer += p.text + " ";
    $("interim").textContent = interimBuffer;
  });

  socket.on("transcript_final", (p) => {
    $("final").textContent = p.text;
    interimBuffer = "";
    $("interim").textContent = "";
  });
})();

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
