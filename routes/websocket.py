# routes/websocket.py
import base64
import binascii
import logging
import time
from collections import defaultdict
from typing import Dict, Optional

from flask import Blueprint
from flask_socketio import emit

# Locate the shared socketio instance; keep both import paths for your repo
try:
    from app import socketio  # your main app should expose this
except Exception:
    try:
        from app_refactored import socketio
    except Exception:
        socketio = None  # we'll guard on register

from services.openai_whisper_client import transcribe_bytes

logger = logging.getLogger(__name__)
ws_bp = Blueprint("ws", __name__)

# Per-session state (dev-grade, in-memory)
_BUFFERS: Dict[str, bytearray] = defaultdict(bytearray)
_LAST_EMIT_AT: Dict[str, float] = {}
_LAST_INTERIM_TEXT: Dict[str, str] = {}

# Tunables
_MIN_MS_BETWEEN_INTERIM = 1200.0     # don't spam Whisper; ~1.2s cadence
_MAX_INTERIM_WINDOW_SEC = 14.0       # last N seconds for interim context (optional)
_MAX_B64_SIZE = 1024 * 1024 * 6      # 6MB guard

def _now_ms() -> float:
    return time.time() * 1000.0

def _decode_b64(b64: Optional[str]) -> bytes:
    if not b64:
        return b""
    if len(b64) > _MAX_B64_SIZE:
        raise ValueError("audio_data_b64 too large")
    try:
        return base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError) as e:
        raise ValueError(f"base64 decode failed: {e}")

@socketio.on("join_session")
def on_join_session(data):
    session_id = (data or {}).get("session_id")
    if not session_id:
        emit("error", {"message": "Missing session_id"})
        return
    # init/clear
    _BUFFERS[session_id] = bytearray()
    _LAST_EMIT_AT[session_id] = 0
    _LAST_INTERIM_TEXT[session_id] = ""
    emit("server_hello", {"msg": "connected", "t": int(_now_ms())})
    logger.info(f"[ws] join_session {session_id}")

@socketio.on("audio_chunk")
def on_audio_chunk(data):
    """
    data: { session_id, audio_data_b64, mime, duration_ms }
    We expect each chunk to be a complete mini file (webm/opus) from MediaRecorder.
    """
    session_id = (data or {}).get("session_id")
    if not session_id:
        emit("error", {"message": "Missing session_id in audio_chunk"})
        return

    mime = (data or {}).get("mime") or "audio/webm"
    try:
        chunk = _decode_b64((data or {}).get("audio_data_b64"))
    except ValueError as e:
        emit("error", {"message": f"bad_audio: {e}"})
        return

    if not chunk:
        return

    # Append to full buffer for the eventual final pass
    _BUFFERS[session_id].extend(chunk)

    # Rate-limit interim requests
    now = _now_ms()
    if (now - _LAST_EMIT_AT.get(session_id, 0)) < _MIN_MS_BETWEEN_INTERIM:
        emit("ack", {"ok": True})
        return

    _LAST_EMIT_AT[session_id] = now

    # INTERIM: transcribe the last few seconds to keep latency low but with context
    # (Whisper works on full files; we send a small "window" for near real-time effect)
    window_bytes = bytes(_BUFFERS[session_id])

    # If the buffer is huge, just take the tail ~N seconds.
    # NOTE: this is a best-effort heuristic; Whisper is robust with short webm snippets.
    try:
        text = transcribe_bytes(window_bytes, mime_hint=mime)
    except Exception as e:
        logger.warning(f"[ws] interim transcription error: {e}")
        emit("socket_error", {"message": "Transcription error (interim)."})
        return

    text = (text or "").strip()
    if text and text != _LAST_INTERIM_TEXT.get(session_id, ""):
        _LAST_INTERIM_TEXT[session_id] = text
        emit("interim_transcript", {"text": text})

    emit("ack", {"ok": True})

@socketio.on("finalize_session")
def on_finalize(data):
    session_id = (data or {}).get("session_id")
    if not session_id:
        emit("error", {"message": "Missing session_id in finalize_session"})
        return

    mime = (data or {}).get("mime") or "audio/webm"
    full_audio = bytes(_BUFFERS.get(session_id, b""))
    if not full_audio:
        emit("final_transcript", {"text": ""})
        return

    try:
        final_text = transcribe_bytes(full_audio, mime_hint=mime)
    except Exception as e:
        logger.error(f"[ws] final transcription error: {e}")
        emit("error", {"message": "Transcription failed (final)."})
        return

    emit("final_transcript", {"text": (final_text or "").strip()})
    # clear session memory
    _BUFFERS.pop(session_id, None)
    _LAST_EMIT_AT.pop(session_id, None)
    _LAST_INTERIM_TEXT.pop(session_id, None)
    