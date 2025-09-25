import io
import os
from typing import Optional
from openai import OpenAI

# Override via env if you want (e.g., WHISPER_MODEL=whisper-1)
_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")

_client: Optional[OpenAI] = None


def _client_ok() -> Optional[OpenAI]:
    """
    Return an OpenAI client if OPENAI_API_KEY is set; else None.
    This lets the app behave gracefully if the key is missing.
    """
    global _client
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None
    if _client is None:
        _client = OpenAI(api_key=api_key)
    return _client


def _ext_from_mime(mime: str) -> str:
    if not mime:
        return "webm"
    m = mime.lower()
    if "ogg" in m:
        return "ogg"
    if "webm" in m:
        return "webm"
    if "wav" in m:
        return "wav"
    if "mp3" in m:
        return "mp3"
    return "webm"


def ping_openai() -> dict:
    """
    Lightweight credential/SDK check. Returns a dict safe to log/emit.
    """
    client = _client_ok()
    if not client:
        return {"ok": False, "reason": "missing_api_key"}
    try:
        _ = client.models.list()
        return {"ok": True, "model": _MODEL}
    except Exception as e:
        return {"ok": False, "reason": type(e).__name__, "detail": str(e)[:200]}


def transcribe_bytes(audio_bytes: bytes, mime_type: str) -> str:
    """
    Send a complete mini-file (e.g., ~1.2s webm/ogg chunk) to Whisper and return text.
    If no API key is present, returns an empty string instead of raising.
    """
    client = _client_ok()
    if not client:
        return ""

    ext = _ext_from_mime(mime_type or "webm")
    fname = f"chunk.{ext}"

    # New SDK path: pass a file-like object with .name set.
    fileobj = io.BytesIO(audio_bytes)
    fileobj.name = fname

    resp = client.audio.transcriptions.create(
        model=_MODEL,
        file=fileobj,
        # language=os.getenv("LANGUAGE_HINT") or None,  # optional
    )
    return (getattr(resp, "text", "") or "").strip()