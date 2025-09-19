/* static/js/live.js
   Robust client: connects Socket.IO, records mic, streams chunks,
   shows level, and renders interim/final text.
*/
(() => {
  const $ = (sel) => document.querySelector(sel);
  const on = (el, ev, fn) => el.addEventListener(ev, fn);

  const ui = {
    conn: $('#conn'),
    levelTrack: $('#level i'),
    recChip: $('#rec'),
    recLabel: $('#recLabel'),
    btnStart: $('#btnStart'),
    btnStop:  $('#btnStop'),
    btnMute:  $('#btnMute'),
    log: $('#log'),
  };

  // ---- logging helpers ----
  function logLine(text, cls = 'sys') {
    const p = document.createElement('div');
    p.className = `line ${cls}`;
    p.textContent = text;
    ui.log.appendChild(p);
    ui.log.scrollTop = ui.log.scrollHeight;
  }
  const logSys = (t) => logLine(t, 'sys');
  const logErr = (t) => logLine(t, 'err');
  const logInterim = (t) => logLine(t, 'interim');
  const logFinal = (t) => logLine(t, 'final');

  // ---- Socket.IO connection ----
  let socket = null;
  function ensureSocket() {
    if (socket) return socket;

    if (typeof io === 'undefined') {
      logErr('Socket.IO client not available (io is undefined).');
      return null;
    }

    socket = io({
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 500,
      reconnectionDelayMax: 3000,
      timeout: 15000,
      withCredentials: false,
    });

    socket.on('connect', () => {
      ui.conn.textContent = 'Connected';
      ui.conn.style.background = '#15803d'; // green-700
      logSys(`[mina] socket connected id= ${socket.id}`);
      ui.btnStart.disabled = false;
    });

    socket.on('disconnect', (reason) => {
      ui.conn.textContent = 'Disconnected';
      ui.conn.style.background = '#7f1d1d'; // red-900
      logErr(`[mina] socket disconnected: ${reason}`);
      ui.btnStart.disabled = false;
      ui.btnStop.disabled = true;
    });

    socket.on('msg', (m) => logSys(m));
    socket.on('warn', (m) => logErr(m));
    socket.on('error', (m) => logErr(m));
    socket.on('interim', (d) => d?.text && logInterim(d.text));
    socket.on('final', (d) => d?.text && logFinal(d.text));

    return socket;
  }

  // ---- Audio recorder (MediaRecorder webm/opus) ----
  let mediaStream = null;
  let mediaRecorder = null;
  let isMuted = false;
  let levelNode = null;
  let audioCtx = null;
  let rafId = 0;

  function stopLevelMeter() {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = 0;
    if (audioCtx) try { audioCtx.close(); } catch {}
    audioCtx = null;
    levelNode = null;
    ui.levelTrack.style.transform = 'scaleX(0.05)';
  }

  async function startRecording() {
    const sock = ensureSocket();
    if (!sock || sock.disconnected) {
      logSys('Socket not connected yet; waiting…');
      return;
    }

    if (!mediaStream) {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          channelCount: 1,
          sampleRate: 48000
        },
        video: false
      });
    }

    // Level meter
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const src = audioCtx.createMediaStreamSource(mediaStream);
    levelNode = audioCtx.createAnalyser();
    levelNode.fftSize = 512;
    src.connect(levelNode);

    (function meter() {
      const buf = new Uint8Array(levelNode.frequencyBinCount);
      levelNode.getByteFrequencyData(buf);
      const max = Math.max(...buf) / 255; // 0..1
      const clamped = Math.max(0.05, Math.min(1, max));
      ui.levelTrack.style.transform = `scaleX(${clamped})`;
      rafId = requestAnimationFrame(meter);
    })();

    // MediaRecorder chunks
    const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm';

    mediaRecorder = new MediaRecorder(mediaStream, { mimeType: mime, audioBitsPerSecond: 128000 });

    mediaRecorder.onstart = () => {
      isMuted = ui.btnMute.getAttribute('aria-pressed') === 'true';
      ui.recLabel.textContent = 'Recording…';
      ui.btnStart.disabled = true;
      ui.btnStop.disabled = false;
      logSys('recording started');
      sock.emit('start', { mime, sampleRate: 48000 });
    };

    mediaRecorder.ondataavailable = (e) => {
      if (!e.data || e.data.size === 0 || isMuted) return;
      e.data.arrayBuffer().then((ab) => {
        // send as raw bytes; server can accept list/bytes either way
        sock.emit('audio_chunk', { chunk: Array.from(new Uint8Array(ab)) });
      }).catch((err) => logErr(`chunk error: ${err}`));
    };

    mediaRecorder.onstop = () => {
      sock.emit('stop');
      stopLevelMeter();
      ui.recLabel.textContent = 'Stopped';
      ui.btnStart.disabled = false;
      ui.btnStop.disabled = true;
      logSys('recording stopped');
    };

    mediaRecorder.start(250); // every 250ms
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
  }

  function toggleMute() {
    const pressed = ui.btnMute.getAttribute('aria-pressed') === 'true';
    const next = !pressed;
    ui.btnMute.setAttribute('aria-pressed', String(next));
    isMuted = next;
    ui.btnMute.textContent = next ? 'Unmute' : 'Mute';
  }

  // ---- Bind UI / hotkeys ----
  on(ui.btnStart, 'click', startRecording);
  on(ui.btnStop, 'click', stopRecording);
  on(ui.btnMute, 'click', toggleMute);

  on(window, 'keydown', (ev) => {
    if (ev.key.toLowerCase() === 'r') {
      if (mediaRecorder && mediaRecorder.state !== 'inactive') stopRecording();
      else startRecording();
    } else if (ev.key.toLowerCase() === 'm') {
      toggleMute();
    }
  });

  // Pre-connect socket asap
  ensureSocket();
})();