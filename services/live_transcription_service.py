"""
Live Transcription Service - Real-time OpenAI Whisper integration
Processes audio chunks and returns transcriptions in real-time
"""
import os
import logging
import tempfile
import time
from typing import Optional, Dict, Any
import openai
from pydub import AudioSegment
import io

logger = logging.getLogger(__name__)

class LiveTranscriptionService:
    """Service for real-time audio transcription using OpenAI Whisper"""
    
    def __init__(self):
        """Initialize the transcription service with OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = openai.OpenAI(api_key=api_key, timeout=10)
        logger.info("✅ Live Transcription Service initialized with OpenAI Whisper")
    
    def transcribe_audio_chunk(
        self, 
        audio_bytes: bytes, 
        mime_type: str = 'audio/webm',
        is_interim: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe an audio chunk using OpenAI Whisper API
        
        Args:
            audio_bytes: Raw audio data
            mime_type: MIME type of the audio (e.g., 'audio/webm', 'audio/wav')
            is_interim: Whether this is an interim transcription
            
        Returns:
            Dictionary with transcription results or None if failed
        """
        start_time = time.time()
        
        # Validate audio data
        if not audio_bytes or len(audio_bytes) < 1000:
            logger.debug(f"Audio chunk too small: {len(audio_bytes) if audio_bytes else 0} bytes")
            return None
        
        try:
            # Convert audio to WAV format for Whisper
            wav_audio = self._convert_to_wav(audio_bytes, mime_type)
            
            if not wav_audio or len(wav_audio) < 100:
                logger.warning("Audio conversion failed or produced empty result")
                return None
            
            # Create temporary file for Whisper API
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(wav_audio)
                temp_file_path = temp_file.name
            
            try:
                # Call OpenAI Whisper API
                with open(temp_file_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",
                        temperature=0.0,
                        prompt="High-quality meeting transcription with proper punctuation."
                    )
                
                # Extract transcription text
                text = response.text.strip() if hasattr(response, 'text') else ''
                
                if not text:
                    logger.debug("Empty transcription result from Whisper")
                    return None
                
                # Calculate confidence from segments if available
                confidence = 0.85  # Default confidence
                if hasattr(response, 'segments') and response.segments:
                    total_confidence = 0.0
                    confidence_count = 0
                    
                    for segment in response.segments:
                        if hasattr(segment, 'avg_logprob') and segment.avg_logprob is not None:
                            # Convert log probability to confidence
                            seg_confidence = max(0.0, min(1.0, (segment.avg_logprob + 1.0)))
                            total_confidence += seg_confidence
                            confidence_count += 1
                    
                    if confidence_count > 0:
                        confidence = total_confidence / confidence_count
                
                processing_time = (time.time() - start_time) * 1000
                
                logger.info(f"✅ Transcribed: '{text[:50]}...' (confidence: {confidence:.2f}, {processing_time:.0f}ms)")
                
                return {
                    'text': text,
                    'confidence': confidence,
                    'is_final': not is_interim,
                    'language': getattr(response, 'language', 'en'),
                    'duration': getattr(response, 'duration', 0.0),
                    'processing_time_ms': processing_time
                }
                
            finally:
                # Cleanup temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
        
        except openai.APIError as e:
            logger.error(f"❌ OpenAI API error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}", exc_info=True)
            return None
    
    def _convert_to_wav(self, audio_bytes: bytes, mime_type: str) -> Optional[bytes]:
        """
        Convert audio bytes to WAV format
        
        Args:
            audio_bytes: Raw audio data
            mime_type: MIME type of input audio
            
        Returns:
            WAV audio bytes or None if conversion failed
        """
        try:
            # Determine input format
            if 'webm' in mime_type.lower() or 'opus' in mime_type.lower():
                format_name = 'webm'
            elif 'wav' in mime_type.lower():
                # Already WAV, return as-is
                return audio_bytes
            elif 'mp4' in mime_type.lower() or 'm4a' in mime_type.lower():
                format_name = 'mp4'
            elif 'ogg' in mime_type.lower():
                format_name = 'ogg'
            else:
                logger.warning(f"Unknown audio format: {mime_type}, attempting as webm")
                format_name = 'webm'
            
            # Convert using pydub
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=format_name)
            
            # Convert to WAV format (16-bit PCM, mono, 16kHz for optimal Whisper performance)
            audio = audio.set_channels(1)  # Mono
            audio = audio.set_frame_rate(16000)  # 16kHz sample rate
            audio = audio.set_sample_width(2)  # 16-bit
            
            # Export to WAV bytes
            wav_buffer = io.BytesIO()
            audio.export(wav_buffer, format='wav')
            wav_bytes = wav_buffer.getvalue()
            
            logger.debug(f"Converted {len(audio_bytes)} bytes ({mime_type}) to {len(wav_bytes)} bytes WAV")
            return wav_bytes
            
        except Exception as e:
            logger.error(f"❌ Audio conversion failed: {e}")
            return None


# Global service instance
_live_transcription_service: Optional[LiveTranscriptionService] = None

def get_live_transcription_service() -> LiveTranscriptionService:
    """Get or create the global live transcription service instance"""
    global _live_transcription_service
    
    if _live_transcription_service is None:
        _live_transcription_service = LiveTranscriptionService()
    
    return _live_transcription_service
