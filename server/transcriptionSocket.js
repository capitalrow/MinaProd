/**
 * Socket.IO transcription engine using OpenAI Whisper (whisper-1).
 * Strategy: keep an ever-growing in-memory buffer; on each chunk, if not busy,
 * transcribe the FULL audio so far -> emit partial; on stop -> emit final.
 * This avoids cut-offs & missed words while keeping updates frequent.
 */
import { Server } from 'socket.io';
import axios from 'axios';
import FormData from 'form-data';

const OPENAI_URL = 'https://api.openai.com/v1/audio/transcriptions';
const MODEL = 'whisper-1';
const LANGUAGE = 'en'; // set to undefined to auto-detect

export default function attachTranscriptionSocket(httpServer) {
  const io = new Server(httpServer, {
    cors: { origin: '*'},
    // Polling works fine if WS can't upgrade (as you saw). Keep both on.
    allowEIO3: true
  });

  io.on('connection', (socket) => {
    // per-connection state
    let chunks = [];               // raw Buffer[] of webm/opus blobs
    let busy = false;              // true while a transcription request is running
    let lastTranscribedBytes = 0;  // size snapshot of last transcription
    let sessionId = Date.now().toString();

    socket.emit('server-status', { ok: true, sessionId });

    const log = (...a) => console.log(`[#${sessionId}]`, ...a);

    // sanity helper
    const concat = () => Buffer.concat(chunks);

    // One-shot transcription of the *entire* buffer
    const transcribeFull = async (final = false) => {
      busy = true;
      try {
        const buf = concat();
        if (!buf.length) {
          if (final) socket.emit('transcription', { text: '', final: true });
          return;
        }

        const fd = new FormData();
        fd.append('model', MODEL);
        if (LANGUAGE) fd.append('language', LANGUAGE);
        // filename & contentType matter for ffmpeg probing
        fd.append('file', buf, { filename: 'audio.webm', contentType: 'audio/webm' });

        const { data } = await axios.post(OPENAI_URL, fd, {
          headers: {
            Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
            ...fd.getHeaders()
          },
          maxBodyLength: Infinity,
          timeout: 120000
        });

        const text = (data?.text ?? '').trim();
        socket.emit('transcription', { text, final });
        log(final ? '✅ final bytes=' : '🕒 partial bytes=', buf.length, 'textLen=', text.length);
      } catch (err) {
        const msg = err?.response?.data || err?.message || 'transcription failed';
        log('❌ whisper error:', msg);
        socket.emit('transcription', { error: 'Transcription failed. Retrying on next chunk.' });
      } finally {
        lastTranscribedBytes = concat().length;
        busy = false;

        // If more audio arrived while we were busy, immediately run again (partial)
        if (!final && concat().length > lastTranscribedBytes) {
          // micro-queue to yield back to event loop
          setTimeout(() => { if (!busy) transcribeFull(false); }, 0);
        }
      }
    };

    // Client events
    socket.on('start-recording', () => {
      chunks = [];
      busy = false;
      lastTranscribedBytes = 0;
      sessionId = Date.now().toString();
      log('🎙️ start');
      socket.emit('session', { id: sessionId });
    });

    // Note: Socket.IO delivers Blobs as Buffer on Node automatically.
    socket.on('audio-chunk', (payload) => {
      // payload can be Buffer or {buffer:ArrayBuffer}
      let buf;
      if (Buffer.isBuffer(payload)) buf = payload;
      else if (payload?.buffer) buf = Buffer.from(payload.buffer);
      else return;

      chunks.push(buf);

      // throttle: only kick a transcription if not already busy
      if (!busy) transcribeFull(false);
    });

    socket.on('stop-recording', async () => {
      log('🏁 stop');
      // do a last pass as final
      if (busy) {
        // wait until current pass finishes, then run final
        const check = () => busy ? setTimeout(check, 50) : transcribeFull(true);
        check();
      } else {
        transcribeFull(true);
      }
    });

    socket.on('disconnect', () => {
      log('🔌 disconnect; clearing buffers.');
      chunks = [];
      busy = false;
    });
  });
}