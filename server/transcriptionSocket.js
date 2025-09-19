/**
 * Socket.IO transcription engine using OpenAI Whisper (whisper-1).
 * Strategy: keep an ever-growing buffer; on each chunk, if not busy,
 * transcribe the FULL audio so far -> emit interim; on stop -> emit final.
 */
import { Server } from 'socket.io';
import axios from 'axios';
import FormData from 'form-data';

const OPENAI_URL = 'https://api.openai.com/v1/audio/transcriptions';
const MODEL = process.env.WHISPER_MODEL || 'whisper-1';
const LANGUAGE = process.env.LANGUAGE || 'en';

export default function attachTranscriptionSocket(httpServer) {
  const io = new Server(httpServer, {
    cors: { origin: '*' },
    transports: ['polling'], // Replit friendly
    allowEIO3: true
  });

  const ns = io.of('/transcribe');

  ns.on('connection', (socket) => {
    let chunks = [];
    let busy = false;
    let started = false;

    const log = (...a) => console.log('[mina]', ...a);
    const concat = () => Buffer.concat(chunks);

    const transcribeFull = async (final = false) => {
      busy = true;
      try {
        const buf = concat();
        if (!buf.length) {
          if (final) {
            // dual-emit for backward compatibility
            socket.emit('final', { text: '' });
            socket.emit('transcription', { text: '', final: true });
          }
          return;
        }

        const fd = new FormData();
        fd.append('model', MODEL);
        if (LANGUAGE) fd.append('language', LANGUAGE);
        fd.append('file', buf, { filename: 'audio.webm', contentType: 'audio/webm' });

        const { data } = await axios.post(OPENAI_URL, fd, {
          headers: { Authorization: `Bearer ${process.env.OPENAI_API_KEY}`, ...fd.getHeaders() },
          maxBodyLength: Infinity,
          timeout: 120000
        });

        const text = (data?.text || '').trim();

        if (final) {
          socket.emit('final', { text });                         // new canonical
          socket.emit('transcription', { text, final: true });    // legacy
        } else {
          socket.emit('interim', { text });                       // new canonical
          socket.emit('transcription', { text, final: false });   // legacy
        }
      } catch (e) {
        const msg = e?.response?.data?.error?.message || e.message || 'transcription_failed';
        socket.emit('error', { message: msg });
        log('transcribe error:', msg);
      } finally {
        busy = false;
      }
    };

    socket.emit('server-status', { ok: true });

    socket.on('start', () => {
      chunks = [];
      busy = false;
      started = true;
      log('🎙️ start');
    });

    socket.on('audio', (payload) => {
      if (!started) return;
      let buf = Buffer.isBuffer(payload)
        ? payload
        : payload?.buffer ? Buffer.from(payload.buffer)
        : null;
      if (!buf) return;
      chunks.push(buf);
      if (!busy) transcribeFull(false);
    });

    socket.on('stop', () => {
      if (!started) return;
      started = false;
      const wait = () => busy ? setTimeout(wait, 50) : transcribeFull(true);
      wait();
      log('⏹ stop');
    });

    socket.on('disconnect', () => {
      chunks = [];
      busy = false;
      started = false;
      log('🔌 disconnect');
    });
  });
}