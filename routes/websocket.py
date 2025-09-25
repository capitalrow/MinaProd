# routes/websocket.py
# Drop-in replacement: preserves your blueprint export and improves error detail.
import base64
import binascii
import logging
import time
from collections import defaultdict
from typing import Dict, Optional

from flask import Blueprint
from flask_socketio import emit

# Locate the shared Socket.IO instance from app.py
try:
    from app import socketio  # type: ignore
except Exception:
    try:
        # sometimes the project exposes it via a different module during dev
        from app_refactored import socketio  # type: ignore
    except Exception as e:
        raise RuntimeError("SocketIO instance not found") from e

from services.openai_whisper_client import transcribe_bytes, check_openai

logger = logging.getLogger(__name__)
ws_bp = Blueprint("ws", __name__)

# Per-session state (dev-grade, in-memory)
_BUFFERS: Dict[str, bytearray] = defaultdict(bytearray)
_LAST_EMIT_AT: Dict[str, float] = {}
_LAST_INTERIM_TEXT: Dict[str, str] = {}

# Tunables — keep your previous cadence to avoid regressions
_MIN_MS_BETWEEN_INTERIM = 1200.0     # ~1.2s cadence (matches MediaRecorder.start(1200))
_MAX_B64_SIZE = 1024 * 1024 * 6      # 6 MB safety guard


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

    # One-time health hint for the client
    health = check_openai()
    if not health.get("ok"):
        emit("socket_error", {"message": "OpenAI not ready", "detail": health})

    emit("server_hello", {"msg": "connected", "t": int(_now_ms())})
    logger.info("[ws] join_session %s", session_id)

@socketio.on("audio_chunk")
def on_audio_chunk(data):
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

    # Append so finalize has the full buffer
    _BUFFERS[session_id].extend(chunk)

    # Throttle interim
    now = _now_ms()
    if now - (_LAST_EMIT_AT.get(session_id, 0) or 0) < _MIN_MS_BETWEEN_INTERIM:
        emit("ack", {"ok": True})
        return

    try:
        text = transcribe_bytes(chunk, mime_hint=mime)
    except Exception as e:
        logger.warning("[ws] interim transcription error: %s", e)
        emit("socket_error", {"message": "Transcription error (interim).", "detail": str(e)[:200]})
        emit("ack", {"ok": False})
        return

    text = (text or "").strip()
    if text and text != _LAST_INTERIM_TEXT.get(session_id, ""):
        _LAST_INTERIM_TEXT[session_id] = text
        emit("interim_transcript", {"text": text})

    _LAST_EMIT_AT[session_id] = now
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
        logger.error("[ws] final transcription error: %s", e)
        emit("error", {"message": "Transcription failed (final).", "detail": str(e)[:200]})
        return

    emit("final_transcript", {"text": (final_text or '').strip()})

    # clear session memory
    _BUFFERS.pop(session_id, None)
    _LAST_EMIT_AT.pop(session_id, None)
    _LAST_INTERIM_TEXT.pop(session_id, None)