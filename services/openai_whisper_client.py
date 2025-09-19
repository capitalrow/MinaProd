# services/openai_whisper_client.py – resilient Whisper client (v1 SDK safe)
import io
import os
import time
from typing import Optional, Tuple

from openai import OpenAI

_CLIENT: Optional[OpenAI] = None

def _client() -> OpenAI:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = OpenAI()  # reads OPENAI_API_KEY
    return _CLIENT

_EXT_FROM_MIME = {
    "audio/webm": "webm",
    "audio/webm;codecs=opus": "webm",
    "audio/ogg": "ogg",
    "audio/ogg;codecs=opus": "ogg",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/flac": "flac",
    "audio/mp4": "m4a",
    "audio/aac": "m4a",
    "webm": "webm", "ogg": "ogg", "mp3": "mp3", "wav": "wav", "flac": "flac", "m4a": "m4a",
}

def _filename_and_mime(mime_hint: Optional[str]) -> Tuple[str, str]:
    mime = (mime_hint or "").split(";")[0].strip().lower()
    ext = _EXT_FROM_MIME.get(mime) or "webm"
    if mime not in _EXT_FROM_MIME:
        mime = "audio/webm"
    return (f"chunk.{ext}", mime)

def transcribe_bytes(
    audio_bytes: bytes,
    mime_hint: Optional[str] = None,
    language: Optional[str] = None,
    model: Optional[str] = None,
    max_retries: int = 3,
    retry_backoff: float = 0.8,
) -> str:
    """
    Blocking Whisper call with retries.
    IMPORTANT: OpenAI v1 expects a file-like with a .name; do NOT pass a (filename, file, mime) tuple.
    """
    if not audio_bytes:
        return ""
    client = _client()
    model = model or os.getenv("WHISPER_MODEL", "whisper-1")
    language = language or os.getenv("LANGUAGE_HINT") or None
    filename, _mime = _filename_and_mime(mime_hint)

    bio = io.BytesIO(audio_bytes)
    bio.name = filename  # v1 SDK inspects .name for file extension

    attempt = 0
    while True:
        attempt += 1
        try:
            resp = client.audio.transcriptions.create(
                file=bio,
                model=model,
                language=language,
            )
            return getattr(resp, "text", "") or ""
        except Exception:
            if attempt >= max_retries:
                raise
            # rewind buffer for retry
            try:
                bio.seek(0)
            except Exception:
                bio = io.BytesIO(audio_bytes); bio.name = filename
            time.sleep(retry_backoff * attempt)