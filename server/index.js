// server/index.js — dual-protocol shim + robust per-chunk queue (OpenAI Whisper)
import 'dotenv/config';
import express from 'express';
import http from 'http';
import path from 'path';
import { fileURLToPath } from 'url';
import cors from 'cors';
import { Server } from 'socket.io';
import axios from 'axios';
import FormData from 'form-data';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.join(__dirname, '..');

// ---------- Config
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || '';
if (!OPENAI_API_KEY) {
  console.error('❌ Missing OPENAI_API_KEY'); process.exit(1);
}
const PORT     = Number(process.env.PORT || 3000);
const MODEL    = process.env.WHISPER_MODEL || 'whisper-1';
const LANGUAGE = process.env.LANGUAGE || 'en';
const LOG_LEVEL = (process.env.LOG_LEVEL || 'debug').toLowerCase(); // info|debug
const DRY_RUN   = (process.env.DRY_RUN || 'false').toLowerCase() === 'true';
const OPENAI_URL = 'https://api.openai.com/v1/audio/transcriptions';

// ---------- Web app
const app = express();
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use('/static', express.static(path.join(ROOT, 'static')));
app.get('/live', (_, res) => res.sendFile(path.join(ROOT, 'templates', 'pages', 'live.html')));
app.get('/',     (_, res) => res.redirect('/live'));
app.get('/health', (_, res) => res.json({ ok: true, dryRun: DRY_RUN, model: MODEL }));

// ---------- Socket.IO
const server = http.createServer(app);
const io = new Server(server, {
  path: '/socket.io',
  cors: { origin: '*', methods: ['GET','POST'] },
  transports: ['polling','websocket'],
  allowEIO3: true,
});
io.engine.on('connection_error', (err) => {
  console.error('[mina] engine connection_error', { code: err.code, message: err.message, url: err.req?.url });
});

// ---------- Helpers
const dbg = (...a) => { if (LOG_LEVEL === 'debug') console.log(...a); };
async function transcribeBuffer(buf, label='chunk') {
  if (DRY_RUN) { await new Promise(r=>setTimeout(r,120)); return `[${label}] lorem ipsum`; }
  const fd = new FormData();
  fd.append('model', MODEL);
  if (LANGUAGE) fd.append('language', LANGUAGE);
  fd.append('file', buf, { filename: 'audio.webm', contentType: 'audio/webm' });
  const { data } = await axios.post(OPENAI_URL, fd, {
    headers: { Authorization: `Bearer ${OPENAI_API_KEY}`, ...fd.getHeaders() },
    maxBodyLength: Infinity, timeout: 120000,
  });
  return (data?.text || '').trim();
}

// ---------- Connection pipeline (per-client)
io.on('connection', (socket) => {
  // Session + state
  let sessionId = null;
  let started = false;
  let queue = [];        // { buf, idx }
  let pumping = false;
  let finalText = '';
  let seq = 0;

  const log = (...a) => console.log(`[mina#${socket.id}]`, ...a);

  socket.emit('server_hello', { ok: true, proto: 'dual', dryRun: DRY_RUN });
  log('🔌 client connected');

  // accept both join styles (legacy)
  socket.on('join_session', (p={}) => { sessionId = p.session_id || null; dbg(`[mina#${socket.id}] join_session`, sessionId); });
  // new start (from our new client)
  socket.on('start', () => {
    started = true; queue = []; pumping = false; finalText = ''; seq = 0;
    log('🎙️ START recording'); 
  });

  // legacy finalize -> treat as stop
  socket.on('finalize_session', () => {
    if (!started) return;
    log('🛑 finalize_session'); started = false; drainAndEmitFinal();
  });

  // new stop
  socket.on('stop', () => {
    if (!started) return;
    log('🛑 STOP requested'); started = false; drainAndEmitFinal();
  });

  // accept both payload forms
  function acceptChunk(payload) {
    if (!started) return;
    let buf = null;

    // Preferred: binary ArrayBuffer
    if (payload?.buffer) buf = Buffer.from(payload.buffer);
    // Compat: Uint8Array
    else if (payload?.chunk && payload.chunk.buffer) buf = Buffer.from(payload.chunk);
    // Legacy base64: { audio_data_b64: '...' }
    else if (payload?.audio_data_b64) {
      try { buf = Buffer.from(payload.audio_data_b64, 'base64'); }
      catch(_) { /* ignore */ }
    }

    if (!buf || !buf.length) return;

    seq += 1;
    dbg(`[mina#${socket.id}] ➕ chunk idx=${seq} size=${buf.length}`);
    queue.push({ buf, idx: seq });
    pump();
  }

  socket.on('audio', acceptChunk);        // new
  socket.on('audio_chunk', acceptChunk);  // legacy name

  async function pump() {
    if (pumping) return;
    pumping = true;
    try {
      while (queue.length) {
        const { buf, idx } = queue.shift();
        log('📤 sending CHUNK to Whisper', { idx, size: buf.length });
        try {
          const text = await transcribeBuffer(buf, `#${idx}`);
          dbg(`[mina#${socket.id}] 🟦 interim len=${text.length} idx=${idx}`);
          // Emit BOTH dialects so old/new UIs work
          socket.emit('interim',            { text });
          socket.emit('interim_transcript', { text });

          if (text) {
            if (finalText && !finalText.endsWith(' ')) finalText += ' ';
            finalText += text;
          }
        } catch (e) {
          const msg = e?.response?.data?.error?.message || e.message || 'transcription_failed';
          console.error('[mina] ❌ OpenAI error:', msg);
          socket.emit('socket_error', { message: msg });
          socket.emit('error',       { message: msg }); // legacy surface
        }
      }
    } finally {
      pumping = false;
    }
  }

  function drainAndEmitFinal() {
    const wait = () => {
      if (pumping || queue.length) return setTimeout(wait, 60);
      log('✅ FINAL text len=', finalText.length, 'session=', sessionId);
      // Emit BOTH dialects
      socket.emit('final',            { text: finalText });
      socket.emit('final_transcript', { text: finalText });
      // reset state
      queue = []; finalText = '';
    };
    wait();
  }

  socket.on('disconnect', (reason) => {
    log('🔌 disconnected', { reason, sessionId });
    // drop state; no final on abrupt disconnect
    started = false; queue = []; pumping = false; finalText = '';
  });
});

server.listen(PORT, () => {
  console.log(`🚀 Mina server http://localhost:${PORT}`);
  console.log(`   • Live UI: /live`);
  console.log(`   • Socket path: /socket.io`);
  console.log(`   • DRY_RUN=${DRY_RUN}  LOG_LEVEL=${LOG_LEVEL}`);
});