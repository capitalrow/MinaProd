# routes/websocket.py
import base64
import binascii
import logging
import time
import uuid
from collections import defaultdict
from typing import Dict, Optional
from datetime import datetime

from flask import Blueprint
from flask_socketio import emit

# Import the socketio instance from the consolidated app
from app import socketio

# Import database models for persistence
from models import db, Session, Segment

from services.openai_whisper_client import transcribe_bytes

logger = logging.getLogger(__name__)
ws_bp = Blueprint("ws", __name__)

# Per-session state (dev-grade, in-memory for audio buffering)
_BUFFERS: Dict[str, bytearray] = defaultdict(bytearray)
_LAST_EMIT_AT: Dict[str, float] = {}
_LAST_INTERIM_TEXT: Dict[str, str] = {}

# Tunables
_MIN_MS_BETWEEN_INTERIM = 400.0      # Real-time feel: ~400ms cadence  
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
    
    # Create or get existing session in database
    try:
        session = db.session.query(Session).filter_by(external_id=session_id).first()
        if not session:
            session = Session(
                external_id=session_id,
                title="Live Transcription Session",
                status="active",
                started_at=datetime.utcnow()
            )
            db.session.add(session)
            db.session.commit()
            logger.info(f"[ws] Created new session in DB: {session_id}")
        else:
            logger.info(f"[ws] Using existing session: {session_id}")
    except Exception as e:
        logger.error(f"[ws] Database error creating session: {e}")
        # Continue with in-memory only
    
    # init/clear in-memory buffers
    _BUFFERS[session_id] = bytearray()
    _LAST_EMIT_AT[session_id] = 0
    _LAST_INTERIM_TEXT[session_id] = ""
    emit("server_hello", {"msg": "connected", "t": int(_now_ms())})
    logger.info(f"[ws] join_session {session_id}")

@socketio.on("audio_chunk")  
def on_audio_chunk(data):
    """
    data: { session_id, audio_data, settings }
    Frontend sends audio_data as array of bytes from MediaRecorder.
    """
    session_id = (data or {}).get("session_id")
    if not session_id:
        emit("error", {"message": "Missing session_id in audio_chunk"})
        return

    # Get settings from frontend
    settings = (data or {}).get("settings", {})
    mime_type = settings.get("mimeType", "audio/webm")
    
    # Handle audio data - frontend sends as array of bytes
    audio_data = (data or {}).get("audio_data")
    if not audio_data:
        emit("error", {"message": "Missing audio_data in audio_chunk"})
        return
    
    try:
        # Convert array of bytes to bytes object
        if isinstance(audio_data, list):
            chunk = bytes(audio_data)
        elif isinstance(audio_data, str):
            # Fallback: try base64 decode
            chunk = _decode_b64(audio_data)
        else:
            chunk = bytes(audio_data)
    except (ValueError, TypeError) as e:
        emit("error", {"message": f"bad_audio: {e}"})
        return

    if not chunk:
        return

    # Append to full buffer for the eventual final pass
    _BUFFERS[session_id].extend(chunk)

    # Only process if we have meaningful audio data (> 200 bytes for real-time feel)
    if len(chunk) < 200:
        emit("ack", {"ok": True})
        return
    
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
        text = transcribe_bytes(window_bytes, mime_hint=mime_type)
    except Exception as e:
        logger.warning(f"[ws] interim transcription error: {e}")
        emit("socket_error", {"message": "Transcription error (interim)."})
        return

    text = (text or "").strip()
    if text and text != _LAST_INTERIM_TEXT.get(session_id, ""):
        _LAST_INTERIM_TEXT[session_id] = text
        # Emit transcription_result that frontend expects
        emit("transcription_result", {
            "text": text,
            "is_final": False,
            "confidence": 0.8,  # Default confidence for interim
            "session_id": session_id,
            "timestamp": int(_now_ms())
        })

    emit("ack", {"ok": True})

@socketio.on("finalize_session")
def on_finalize(data):
    session_id = (data or {}).get("session_id")
    if not session_id:
        emit("error", {"message": "Missing session_id in finalize_session"})
        return

    # Get settings from frontend
    settings = (data or {}).get("settings", {})
    mime_type = settings.get("mimeType", "audio/webm")
    full_audio = bytes(_BUFFERS.get(session_id, b""))
    if not full_audio:
        emit("final_transcript", {"text": ""})
        return

    try:
        final_text = transcribe_bytes(full_audio, mime_hint=mime_type)
    except Exception as e:
        logger.error(f"[ws] final transcription error: {e}")
        emit("error", {"message": "Transcription failed (final)."})
        return

    final_text = (final_text or "").strip()
    
    # Save final segment to database
    try:
        session = db.session.query(Session).filter_by(external_id=session_id).first()
        if session and final_text:
            segment = Segment(
                session_id=session.id,
                text=final_text,
                start_time=0,  # Could be calculated from audio duration
                end_time=len(full_audio) / 16000,  # Rough estimate
                confidence=0.9,  # Default confidence
                is_final=True,
                segment_type="final"
            )
            db.session.add(segment)
            
            # Update session status
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            session.total_segments = 1
            session.total_duration = len(full_audio) / 16000
            
            db.session.commit()
            logger.info(f"[ws] Saved final segment to DB for session: {session_id}")
    except Exception as e:
        logger.error(f"[ws] Database error saving segment: {e}")

    # Emit transcription_result that frontend expects
    emit("transcription_result", {
        "text": final_text,
        "is_final": True,
        "confidence": 0.9,  # Higher confidence for final
        "session_id": session_id,
        "timestamp": int(_now_ms())
    })
    
    # clear session memory
    _BUFFERS.pop(session_id, None)
    _LAST_EMIT_AT.pop(session_id, None)
    _LAST_INTERIM_TEXT.pop(session_id, None)
    