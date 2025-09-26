# services/openai_whisper_client.py
# Full drop-in: fixes the "proxies" TypeError by supplying our own httpx client
# and keeps the modern Whisper usage (file=fileobj). Includes health check + retries.

import io
import os
import time
from typing import Optional, Dict, List

import httpx
from openai import OpenAI
from openai._exceptions import OpenAIError


_CLIENT: Optional[OpenAI] = None

# Audio buffer storage for assembling complete WebM files
_AUDIO_BUFFERS: Dict[str, List[bytes]] = {}
_BUFFER_MAX_SIZE = 10  # Maximum chunks to buffer before transcribing


def _make_http_client() -> httpx.Client:
    """
    Build an httpx client that **ignores environment proxies** so OpenAI
    never attempts to pass unsupported 'proxies=' to httpx.
    """
    return httpx.Client(
        timeout=30.0,
        http2=True,
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        verify=True,
        trust_env=False,  # <-- critical: do not load HTTP(S)_PROXY from env
    )


def _client() -> OpenAI:
    """
    Lazily construct the OpenAI client with our httpx.Client injected.
    Avoids the 'proxies' kwarg crash regardless of httpx/openai versions.
    """
    global _CLIENT
    if _CLIENT is None:
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if not api_key:
            # Defer raising; upstream callers use health check or handle empty returns.
            raise RuntimeError("Missing OPENAI_API_KEY")
        _CLIENT = OpenAI(
            api_key=api_key,
            http_client=_make_http_client(),  # <-- bypasses SDK's default client creation
        )
    return _CLIENT


def _ext_from_mime(m: Optional[str]) -> str:
    if not m:
        return "webm"
    m = m.lower()
    if "ogg" in m:
        return "ogg"
    if "webm" in m:
        return "webm"
    if "wav" in m:
        return "wav"
    if "mp3" in m:
        return "mp3"
    return "webm"


def check_openai() -> dict:
    """
    Lightweight health check used by the websocket join handler.
    """
    try:
        c = _client()
    except Exception as e:
        return {"ok": False, "reason": type(e).__name__, "detail": str(e)[:200]}
    try:
        _ = c.models.list()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "reason": type(e).__name__, "detail": str(e)[:200]}


def buffer_audio_chunk(
    session_id: str,
    audio_bytes: bytes,
    is_final: bool = False
) -> Optional[bytes]:
    """
    Buffer audio chunks for a session and return complete WebM when ready.
    
    Args:
        session_id: Unique session identifier
        audio_bytes: Raw audio chunk from MediaRecorder
        is_final: True when recording is finished
    
    Returns:
        Complete WebM bytes when buffer is full or session is final, None otherwise
    """
    global _AUDIO_BUFFERS
    
    # Initialize buffer for new session
    if session_id not in _AUDIO_BUFFERS:
        _AUDIO_BUFFERS[session_id] = []
    
    # Add chunk to buffer
    _AUDIO_BUFFERS[session_id].append(audio_bytes)
    
    # Check if we should process the buffer
    buffer = _AUDIO_BUFFERS[session_id]
    should_process = is_final or len(buffer) >= _BUFFER_MAX_SIZE
    
    if should_process:
        # Combine all chunks into complete WebM
        complete_audio = b''.join(buffer)
        
        # Clear buffer if final, otherwise keep recent chunks for context
        if is_final:
            del _AUDIO_BUFFERS[session_id]
        else:
            # Keep last few chunks for continuity
            _AUDIO_BUFFERS[session_id] = buffer[-3:]
        
        print(f"[DEBUG] Assembled complete WebM: {len(complete_audio)} bytes from {len(buffer)} chunks")
        return complete_audio
    
    return None


def transcribe_bytes(
    audio_bytes: bytes,
    mime_hint: Optional[str] = None,
    language: Optional[str] = None,
    model: Optional[str] = None,
    max_retries: int = 2,
    retry_backoff: float = 0.6,
) -> str:
    """
    Send a self-contained audio blob (e.g., 1.2s webm) to Whisper and return text.

    Uses the new OpenAI Python SDK signature: pass a file-like object to `file=`.
    """
    if not audio_bytes:
        return ""

    client = _client()
    mdl = model or os.getenv("WHISPER_MODEL", "whisper-1")

    # LIVE TRANSCRIPTION: Using assembled complete WebM files via buffering system
    print(f"[DEBUG] Transcribing complete audio: {len(audio_bytes)} bytes, mime_hint: {mime_hint}")
    
    # Check if this looks like actual WebM data by examining first few bytes
    if len(audio_bytes) > 0:
        first_bytes = audio_bytes[:8].hex() if len(audio_bytes) >= 8 else audio_bytes.hex()
        print(f"[DEBUG] First bytes: {first_bytes}")

    # Build fileobj for OpenAI
    ext = _ext_from_mime(mime_hint)
    fileobj = io.BytesIO(audio_bytes)
    fileobj.name = f"audio.{ext}"

    attempt = 0
    while True:
        attempt += 1
        try:
            # Build params conditionally to avoid type issues
            params = {"model": mdl, "file": fileobj}
            lang = language or os.getenv("LANGUAGE_HINT")
            if lang:
                params["language"] = lang
            
            resp = client.audio.transcriptions.create(**params)
            return (getattr(resp, "text", "") or "").strip()
        except OpenAIError:
            if attempt >= max_retries:
                raise
            time.sleep(retry_backoff * attempt)
        except Exception as e:
            # Non-OpenAI exceptions: don't spin forever  
            print(f"[DEBUG] Transcription failed with error: {e}")
            print(f"[DEBUG] Audio data size: {len(audio_bytes)}")
            raise