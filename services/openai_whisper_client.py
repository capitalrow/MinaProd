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

    ext = _ext_from_mime(mime_hint or "audio/webm")
    fileobj = io.BytesIO(audio_bytes)
    fileobj.name = f"chunk.{ext}"

    attempt = 0
    while True:
        attempt += 1
        try:
            resp = client.audio.transcriptions.create(
                model=mdl,
                file=fileobj,  # correct for modern SDK
                language=language or os.getenv("LANGUAGE_HINT") or None,
            )
            return (getattr(resp, "text", "") or "").strip()
        except OpenAIError:
            if attempt >= max_retries:
                raise
            time.sleep(retry_backoff * attempt)
        except Exception:
            # Non-OpenAI exceptions: don't spin forever
            raise