# routes/websocket.py
import os
import io
import time
import json
import shutil
import tempfile
import threading
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, Dict

from flask import Blueprint, request
from flask_socketio import Namespace  # only for type hints/logical grouping
from werkzeug.utils import secure_filename

# ===== Blueprint (no HTTP routes here yet, but keeps parity with your app structure)
ws_bp = Blueprint("ws", __name__)

# ===== Environment/config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
INTERIM_SECONDS = float(os.getenv("INTERIM_SECONDS", "2.0"))  # cadence for real interims
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")       # change to your deployed name

# ===== Simple logger
def log(msg, **extra):
    line = f"[ws] {msg}"
    if extra:
        line += " " + json.dumps(extra, ensure_ascii=False)
    print(line, flush=True)

# ===== Session state
@dataclass
class SessionState:
    session_id: str
    mime: str = "audio/webm;codecs=opus"
    tmpdir: str = field(default_factory=lambda: tempfile.mkdtemp(prefix="mina_"))
    webm_path: str = ""
    wav_path: str = ""
    started_at: float = field(default_factory=time.time)
    last_emitted_text: str = ""   # to diff interims
    interim_thread: Optional[threading.Thread] = None
    stop_event: threading.Event = field(default_factory=threading.Event)
    bytes_written: int = 0

    def init_paths(self):
        # Rolling single file that grows as chunks arrive
        webm_file = secure_filename(f"{self.session_id}.webm")
        wav_file  = secure_filename(f"{self.session_id}.wav")
        self.webm_path = os.path.join(self.tmpdir, webm_file)
        self.wav_path  = os.path.join(self.tmpdir, wav_file)

    def cleanup(self):
        try:
            shutil.rmtree(self.tmpdir, ignore_errors=True)
        except Exception as e:
            log("cleanup_error", error=str(e))

_sessions: Dict[str, SessionState] = {}

# ====== OpenAI client (lazy import to avoid dependency when DRY_RUN)
def _openai_client():
    from openai import OpenAI
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=OPENAI_API_KEY)

def _ffmpeg_webm_to_wav(src_webm: str, dst_wav: str, sample_rate=16000):
    # -ac 1 mono, -ar 16k best for Whisper
    cmd = [
        "ffmpeg", "-y", "-i", src_webm,
        "-ac", "1", "-ar", str(sample_rate),
        "-f", "wav", dst_wav
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def _whisper_transcribe_file(path: str) -> str:
    client = _openai_client()
    # NOTE: Using classic transcription endpoint; adjust if you use a different SDK surface.
    with open(path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=f,
            response_format="text"
        )
    # SDK returns a plain string when response_format="text"
    return resp.strip() if isinstance(resp, str) else str(resp).strip()

def _interim_worker(socketio, sid: str, sess: SessionState):
    """Periodically convert the growing webm to wav, ask Whisper, and emit only new text."""
    log("interim_worker_start", session_id=sess.session_id)
    while not sess.stop_event.wait(INTERIM_SECONDS):
        try:
            if sess.bytes_written <= 0:
                continue
            _ffmpeg_webm_to_wav(sess.webm_path, sess.wav_path)
            full_text = _whisper_transcribe_file(sess.wav_path)
            if not full_text:
                continue
            # Emit only the delta since last emission
            if full_text.startswith(sess.last_emitted_text):
                delta = full_text[len(sess.last_emitted_text):].strip()
            else:
                # Whisper sometimes reformats punctuation; be pragmatic
                delta = full_text

            if delta:
                socketio.emit("interim", {"i": int((time.time()-sess.started_at)*1000), "text": delta}, to=sid)
                sess.last_emitted_text = full_text
                log("interim_emitted", session_id=sess.session_id, chars=len(delta))
        except Exception as e:
            log("interim_worker_error", error=str(e), session_id=sess.session_id)
            # don't crash loop; continue
    log("interim_worker_stop", session_id=sess.session_id)

# ===== Registration function (called from app_refactored after init_app)
def register_socketio_handlers(socketio):

    @socketio.on("connect")
    def on_connect():
        # NB: 'request.sid' is the Socket.IO session id
        socketio.emit("server_hello", {"msg": "hello from server", "ts": time.time()})
        log("client_connected", sid=request.sid)

    @socketio.on("disconnect")
    def on_disconnect():
        log("client_disconnected", sid=request.sid)

    @socketio.on("start")
    def on_start(data):
        sid = request.sid
        session_id = str(int(time.time() * 1000))
        mime = (data or {}).get("mime", "audio/webm;codecs=opus")

        sess = SessionState(session_id=session_id, mime=mime)
        sess.init_paths()
        _sessions[sid] = sess

        # create/truncate the rolling webm file
        open(sess.webm_path, "wb").close()
        sess.bytes_written = 0

        socketio.emit("msg", f"recording started {json.dumps({'mime': mime})}", to=sid)
        log("recording_started", sid=sid, session_id=session_id, mime=mime)

        if DRY_RUN:
            # In DRY_RUN we still want some interims so the UI proves out
            def _fake_interims():
                counter = 0
                while not sess.stop_event.wait(1.2):
                    counter += 1
                    txt = f"[Interim… {counter}]"
                    socketio.emit("interim", {"i": counter, "text": txt}, to=sid)
                    log("interim_emitted_dry", i=counter)
            t = threading.Thread(target=_fake_interims, daemon=True)
            t.start()
            sess.interim_thread = t
        else:
            # Start real interim worker
            t = threading.Thread(target=_interim_worker, args=(socketio, sid, sess), daemon=True)
            t.start()
            sess.interim_thread = t

    @socketio.on("audio_chunk")
    def on_audio_chunk(payload):
        sid = request.sid
        sess = _sessions.get(sid)
        if not sess:
            socketio.emit("warn", "chunk received before start; ignoring", to=sid)
            log("chunk_ignored_no_session", sid=sid)
            return

        # Two shapes supported:
        # 1) {chunk: Uint8Array} from client, already binary-packed by socket.io
        # 2) {audio_data_b64: "..."} older path
        chunk = None
        if "chunk" in payload and isinstance(payload["chunk"], (bytes, bytearray)):
            chunk = payload["chunk"]
        elif "chunk" in payload and isinstance(payload["chunk"], list):
            # socket.io sometimes gives list of ints; pack
            chunk = bytes(payload["chunk"])
        elif "audio_data_b64" in payload:
            import base64
            chunk = base64.b64decode(payload["audio_data_b64"])
        else:
            log("chunk_payload_unrecognized", keys=list(payload.keys()))
            return

        if not chunk:
            return

        # Append to rolling webm
        with open(sess.webm_path, "ab") as f:
            f.write(chunk)
        sess.bytes_written += len(chunk)

        # Cosmetic progress
        socketio.emit("msg", f"chunk -> {json.dumps({'size': len(chunk)})}", to=sid)

    @socketio.on("stop")
    def on_stop():
        sid = request.sid
        sess = _sessions.get(sid)
        if not sess:
            socketio.emit("warn", "stop without session", to=sid)
            return

        socketio.emit("msg", "recording stopped", to=sid)
        log("recording_stopped", sid=sid, session_id=sess.session_id)

        # halt interim thread
        sess.stop_event.set()
        if sess.interim_thread and sess.interim_thread.is_alive():
            sess.interim_thread.join(timeout=1.0)

        # Final transcription
        final_text = ""
        try:
            if DRY_RUN:
                final_text = "This is a DRY_RUN final transcript that proves the emit path is working."
            else:
                if sess.bytes_written > 0:
                    _ffmpeg_webm_to_wav(sess.webm_path, sess.wav_path)
                    final_text = _whisper_transcribe_file(sess.wav_path)
        except Exception as e:
            log("final_error", error=str(e), session_id=sess.session_id)

        final_text = (final_text or "").strip()
        if final_text:
            socketio.emit("final", {"i": int((time.time()-sess.started_at)*1000), "text": final_text}, to=sid)
            log("final_emitted", chars=len(final_text), session_id=sess.session_id)
        else:
            socketio.emit("warn", "No audio or transcription failed.", to=sid)

        # cleanup
        sess.cleanup()
        _sessions.pop(sid, None)

    log("routes.websocket loaded; handlers registered")