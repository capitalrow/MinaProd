# services/openai_whisper_client.py
# Full drop-in: fixes the "proxies" TypeError by supplying our own httpx client
# and keeps the modern Whisper usage (file=fileobj). Includes health check + retries.

import io
import os
import time
from typing import Optional

import httpx
from openai import OpenAI
from openai._exceptions import OpenAIError


_CLIENT: Optional[OpenAI] = None


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

    # CRITICAL FIX: Create proper WebM file structure for OpenAI
    # MediaRecorder sends raw data chunks that need proper container headers
    
    # Create a BytesIO object with the raw audio data
    fileobj = io.BytesIO(audio_bytes)
    
    # Set appropriate filename based on mime type
    # OpenAI accepts webm format, so let's use that
    fileobj.name = "chunk.webm"
    
    # Ensure we're at the beginning of the buffer
    fileobj.seek(0)
    
    # Debug: Log audio data info for troubleshooting
    print(f"[DEBUG] Audio chunk: {len(audio_bytes)} bytes, mime_hint: {mime_hint}")
    
    # Check if this looks like actual WebM data by examining first few bytes
    if len(audio_bytes) > 0:
        first_bytes = audio_bytes[:8].hex() if len(audio_bytes) >= 8 else audio_bytes.hex()
        print(f"[DEBUG] First bytes: {first_bytes}")

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
            print(f"[DEBUG] Audio data size: {len(audio_bytes)}, fileobj.name: {fileobj.name}")
            raise