(() => {
  const $ = (id) => document.getElementById(id);
  const dlog = (msg) => { $("debug").textContent += msg + "\n"; };

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

    // iOS Safari MediaRecorder MIME fallback
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