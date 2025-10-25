"""
Enterprise-Grade OpenAI Client Manager
Centralized, robust initialization and management of OpenAI clients

UPGRADE (Wave 0-10): Circuit breaker protection for all OpenAI API calls
"""

import os
import logging
from typing import Optional
from openai import OpenAI
from openai._exceptions import OpenAIError
from services.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpenError

logger = logging.getLogger(__name__)

# Circuit breaker for OpenAI transcription API
_openai_circuit_breaker = None

def get_openai_circuit_breaker() -> CircuitBreaker:
    """Get or create circuit breaker for OpenAI API calls."""
    global _openai_circuit_breaker
    if _openai_circuit_breaker is None:
        config = CircuitBreakerConfig(
            failure_threshold=3,    # Open after 3 consecutive failures
            recovery_timeout=30,    # Try recovery after 30s
            success_threshold=2,    # Close after 2 consecutive successes
            request_timeout=45      # 45s timeout for transcription
        )
        _openai_circuit_breaker = CircuitBreaker("openai_transcription", config)
        logger.info("🔒 OpenAI circuit breaker initialized")
    return _openai_circuit_breaker

class OpenAIClientManager:
    """Centralized OpenAI client management with robust error handling"""
    
    _instance: Optional['OpenAIClientManager'] = None
    _client: Optional[OpenAI] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._api_key = None
            self._initialization_error = None
            logger.info("OpenAI Client Manager initialized")
    
    def get_client(self, force_reinit: bool = False) -> Optional[OpenAI]:
        """
        Get OpenAI client with robust error handling
        
        Args:
            force_reinit: Force re-initialization even if client exists
            
        Returns:
            OpenAI client instance or None if initialization failed
        """
        if self._client is None or force_reinit:
            self._initialize_client()
        
        return self._client
    
    def _initialize_client(self) -> None:
        """Initialize OpenAI client with proper error handling"""
        try:
            # Get API key
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                self._initialization_error = "OPENAI_API_KEY environment variable not set"
                logger.warning(self._initialization_error)
                return
            
            # Store for validation
            self._api_key = api_key
            
            # Initialize client with clean parameters (no proxies or other legacy args)
            client_config = {
                "api_key": api_key,
            }
            
            # Add optional configurations if needed
            timeout = os.environ.get("OPENAI_TIMEOUT")
            if timeout:
                try:
                    client_config["timeout"] = float(timeout)
                except ValueError:
                    logger.warning(f"Invalid OPENAI_TIMEOUT value: {timeout}")
            
            max_retries = os.environ.get("OPENAI_MAX_RETRIES")
            if max_retries:
                try:
                    client_config["max_retries"] = int(max_retries)
                except ValueError:
                    logger.warning(f"Invalid OPENAI_MAX_RETRIES value: {max_retries}")
            
            # Initialize client with only clean, supported parameters
            self._client = OpenAI(**client_config)
            self._initialization_error = None
            
            logger.info("✅ OpenAI client initialized successfully")
            
        except Exception as e:
            self._initialization_error = str(e)
            self._client = None
            logger.error(f"❌ OpenAI client initialization failed: {e}")
    
    def is_available(self) -> bool:
        """Check if OpenAI client is available and working"""
        return self._client is not None and self._initialization_error is None
    
    def get_initialization_error(self) -> Optional[str]:
        """Get the last initialization error message"""
        return self._initialization_error
    
    def test_connection(self) -> tuple[bool, Optional[str]]:
        """
        Test OpenAI connection
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        client = self.get_client()
        if not client:
            return False, self._initialization_error
        
        try:
            # Simple test - try to list models (lightweight operation)
            models = client.models.list()
            if models:
                logger.info("✅ OpenAI connection test successful")
                return True, None
            else:
                return False, "No models returned from OpenAI API"
                
        except OpenAIError as e:
            error_msg = f"OpenAI API error: {e}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error testing OpenAI connection: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    async def transcribe_audio_async(self, audio_file, model: str = "whisper-1", **kwargs) -> Optional[str]:
        """
        Async transcribe audio with robust error handling + circuit breaker protection.
        
        Args:
            audio_file: Audio file object or path
            model: Whisper model to use
            **kwargs: Additional parameters for transcription
            
        Returns:
            Transcribed text or None if failed
        """
        client = self.get_client()
        if not client:
            logger.error("OpenAI client not available for transcription")
            return None
        
        # Get circuit breaker
        cb = get_openai_circuit_breaker()
        
        # Check if circuit is open
        if not cb.can_execute():
            state = cb.get_state()
            logger.warning(f"🚨 OpenAI circuit breaker is {state.value}, blocking async transcription request")
            return None
        
        try:
            # Clean kwargs to avoid unsupported parameters
            clean_kwargs = {
                "file": audio_file,
                "model": model,
            }
            
            # Add supported optional parameters
            if "language" in kwargs and kwargs["language"]:
                clean_kwargs["language"] = kwargs["language"]
            if "response_format" in kwargs:
                clean_kwargs["response_format"] = kwargs["response_format"]
            if "temperature" in kwargs:
                clean_kwargs["temperature"] = kwargs["temperature"]
            
            response = client.audio.transcriptions.create(**clean_kwargs)
            text = getattr(response, "text", "") or ""
            
            # Record success
            cb.record_success()
            return text
            
        except CircuitBreakerOpenError as e:
            logger.warning(f"🚨 Circuit breaker prevented async OpenAI call: {e}")
            return None
        except OpenAIError as e:
            logger.error(f"OpenAI async transcription error: {e}")
            # Record failure
            cb.record_failure(e)
            return None
        except Exception as e:
            logger.error(f"Unexpected async transcription error: {e}")
            # Record failure
            cb.record_failure(e)
            return None

    def transcribe_audio(self, audio_file, model: str = "whisper-1", **kwargs) -> Optional[str]:
        """
        Transcribe audio with robust error handling + circuit breaker protection.
        
        Args:
            audio_file: Audio file object or path
            model: Whisper model to use
            **kwargs: Additional parameters for transcription
            
        Returns:
            Transcribed text or None if failed
        """
        client = self.get_client()
        if not client:
            logger.error("OpenAI client not available for transcription")
            return None
        
        # Get circuit breaker
        cb = get_openai_circuit_breaker()
        
        # Check if circuit is open (service unavailable)
        if not cb.can_execute():
            state = cb.get_state()
            logger.warning(f"🚨 OpenAI circuit breaker is {state.value}, blocking transcription request")
            return None
        
        try:
            # Clean kwargs to avoid unsupported parameters
            clean_kwargs = {
                "file": audio_file,
                "model": model,
            }
            
            # Add supported optional parameters
            if "language" in kwargs and kwargs["language"]:
                clean_kwargs["language"] = kwargs["language"]
            if "response_format" in kwargs:
                clean_kwargs["response_format"] = kwargs["response_format"]
            if "temperature" in kwargs:
                clean_kwargs["temperature"] = kwargs["temperature"]
            
            response = client.audio.transcriptions.create(**clean_kwargs)
            text = getattr(response, "text", "") or ""
            
            # Record success
            cb.record_success()
            return text
            
        except CircuitBreakerOpenError as e:
            logger.warning(f"🚨 Circuit breaker prevented OpenAI call: {e}")
            return None
        except OpenAIError as e:
            logger.error(f"OpenAI transcription error: {e}")
            # Record failure to trigger circuit breaker
            cb.record_failure(e)
            return None
        except Exception as e:
            logger.error(f"Unexpected transcription error: {e}")
            # Record failure
            cb.record_failure(e)
            return None

# Global singleton instance
openai_manager = OpenAIClientManager()

def get_openai_client() -> Optional[OpenAI]:
    """Get OpenAI client instance - convenience function"""
    return openai_manager.get_client()

def test_openai_connection() -> tuple[bool, Optional[str]]:
    """Test OpenAI connection - convenience function"""
    return openai_manager.test_connection()

def get_openai_client_manager() -> OpenAIClientManager:
    """Get OpenAI client manager instance - convenience function"""
    return openai_manager