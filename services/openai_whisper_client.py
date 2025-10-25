# services/openai_whisper_client.py
# UPGRADE (Wave 0-10): Circuit breaker protection for OpenAI Whisper API calls
import io
import os
import time
import logging
from typing import Optional, Tuple

from openai import OpenAI
from openai._exceptions import OpenAIError

# Import circuit breaker from openai_client_manager (shared instance)
from services.openai_client_manager import get_openai_circuit_breaker

logger = logging.getLogger(__name__)

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
    
    UPGRADE (Wave 0-10): Circuit breaker protection added
    """
    if not audio_bytes:
        return ""

    client = _client()
    model = model or os.getenv("WHISPER_MODEL", "whisper-1")
    filename, mime = _filename_and_mime(mime_hint)
    file_tuple = (filename, io.BytesIO(audio_bytes), mime)
    
    # Get circuit breaker (shared with openai_client_manager)
    cb = get_openai_circuit_breaker()
    
    # Check if circuit is open (service unavailable)
    if not cb.can_execute():
        state = cb.get_state()
        logger.warning(f"🚨 OpenAI circuit breaker is {state.value}, blocking transcribe_bytes request")
        return ""  # Return empty string on circuit open

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
            text = getattr(resp, "text", "") or ""
            
            # Record success in circuit breaker
            cb.record_success()
            return text
            
        except OpenAIError as e:
            logger.error(f"OpenAI error on attempt {attempt}/{max_retries}: {e}")
            
            # Record failure in circuit breaker
            cb.record_failure(e)
            
            if attempt >= max_retries:
                raise
            time.sleep(retry_backoff * attempt)
            