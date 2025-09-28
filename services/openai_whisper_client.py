# services/openai_whisper_client.py
import io
import os
import time
from typing import Optional, Tuple

from openai import OpenAI
from openai._exceptions import OpenAIError

_CLIENT: Optional[OpenAI] = None

def _client() -> OpenAI:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = OpenAI()  # reads OPENAI_API_KEY from env
    return _CLIENT

# Map the mime that comes from MediaRecorder to extensions Whisper accepts
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
    # fallbacks
    "webm": "webm",
    "ogg": "ogg",
    "mp3": "mp3",
    "wav": "wav",
    "flac": "flac",
    "m4a": "m4a",
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
    Send a self-contained audio file (e.g., a small webm blob) to Whisper and return text.
    This is used for both interim (small) chunks and the final full buffer.
    """
    if not audio_bytes:
        return ""

    client = _client()
    model = model or os.getenv("WHISPER_MODEL", "whisper-1")
    filename, mime = _filename_and_mime(mime_hint)
    file_tuple = (filename, io.BytesIO(audio_bytes), mime)

    attempt = 0
    while True:
        attempt += 1
        try:
            # Only pass language if it's actually a string
            create_kwargs = {
                "file": file_tuple,
                "model": model,
            }
            lang = language or os.getenv("LANGUAGE_HINT")
            if lang:
                create_kwargs["language"] = lang
            
            resp = client.audio.transcriptions.create(**create_kwargs)
            return getattr(resp, "text", "") or ""
        except OpenAIError as e:
            if attempt >= max_retries:
                raise
            time.sleep(retry_backoff * attempt)
            