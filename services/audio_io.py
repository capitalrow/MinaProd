# services/audio_io.py
import base64
import binascii
import os

# Hard caps (tune via env if you like)
MAX_AUDIO_B64_LEN = int(os.environ.get('MAX_AUDIO_B64_LEN', 256 * 1024))  # ~256 KB per message BEFORE base64
MAX_CHUNKS_PER_MINUTE = int(os.environ.get('MAX_CHUNKS_PER_MINUTE', 600))  # safety valve (~10/sec)

class AudioChunkTooLarge(Exception): 
    """Raised when audio chunk exceeds size limits."""
    pass

class AudioChunkDecodeError(Exception): 
    """Raised when audio chunk cannot be decoded."""
    pass

def decode_audio_b64(b64_str: str) -> bytes:
    """
    Safely decode base64 audio data with size validation.
    
    Args:
        b64_str: Base64 encoded audio data
        
    Returns:
        Raw audio bytes
        
    Raises:
        AudioChunkTooLarge: If data exceeds size limits
        AudioChunkDecodeError: If data cannot be decoded
    """
    if not b64_str:
        return b""
    
    # Fast length check (base64 expands by ~4/3); reject obvious oversize
    max_b64_len = int(MAX_AUDIO_B64_LEN * 4 / 3) + 32
    if len(b64_str) > max_b64_len:
        raise AudioChunkTooLarge(f"b64 length {len(b64_str)} exceeds limit {max_b64_len}")
    
    try:
        return base64.b64decode(b64_str, validate=True)
    except (binascii.Error, ValueError) as e:
        raise AudioChunkDecodeError(f"Invalid base64 audio data: {e}")

def validate_audio_size(audio_bytes: bytes) -> None:
    """
    Validate decoded audio size.
    
    Args:
        audio_bytes: Raw audio data
        
    Raises:
        AudioChunkTooLarge: If audio exceeds size limits
    """
    if len(audio_bytes) > MAX_AUDIO_B64_LEN:
        raise AudioChunkTooLarge(f"Audio size {len(audio_bytes)} exceeds limit {MAX_AUDIO_B64_LEN}")