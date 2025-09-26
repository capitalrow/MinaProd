import io
import os
from typing import Optional
from openai import OpenAI

_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")

_client = None
def _client_ok() -> Optional[OpenAI]:
    global _client
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    if _client is None:
        _client = OpenAI(api_key=api_key)
    return _client

def _ext_from_mime(mime: str) -> str:
    if not mime:
        return "webm"
    m = mime.lower()
    if "ogg" in m: return "ogg"
    if "webm" in m: return "webm"
    if "wav" in m: return "wav"
    if "mp3" in m: return "mp3"
    return "webm"

def transcribe_bytes(audio_bytes: bytes, mime_type: str) -> str:
    """
    Returns text from OpenAI Whisper when API key present,
    otherwise returns '' (no mock text).
    """
    client = _client_ok()
    if not client:
        # No API key -> do nothing (empty string)
        return ""
    ext = _ext_from_mime(mime_type)
    fname = f"chunk.{ext}"
    fileobj = io.BytesIO(audio_bytes)
    fileobj.name = fname  # OpenAI SDK expects a "name"
    resp = client.audio.transcriptions.create(
        model=_MODEL,
        file=(fname, fileobj, mime_type or "application/octet-stream"),
        # You can pass language or prompt here if you like:
        # language="en"
    )
    # OpenAI Python SDK returns .text for Whisper
    return (getattr(resp, "text", "") or "").strip()