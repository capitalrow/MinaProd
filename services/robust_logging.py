#!/usr/bin/env python3
"""
🛡️ Robust Logging & Error Handling System
Enterprise-grade logging with structured session tracking
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import traceback
from functools import wraps

class StructuredLogger:
    """Enhanced logging with session context and structured data"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.session_context = {}
        
    def set_session_context(self, session_id: str, context: Dict[str, Any]):
        """Set session-specific logging context"""
        self.session_context[session_id] = {
            **context,
            "start_time": time.time(),
            "created_at": datetime.now().isoformat()
        }
    
    def log_transcription_event(self, session_id: str, event_type: str, 
                               data: Dict[str, Any], level: str = "info"):
        """Log structured transcription event"""
        log_data = {
            "event_type": event_type,
            "session_id": session_id,
            "timestamp": time.time(),
            "data": data,
            "context": self.session_context.get(session_id, {})
        }
        
        message = f"[{session_id}] {event_type}: {json.dumps(data, default=str)}"
        
        if level == "error":
            self.logger.error(message, extra=log_data)
        elif level == "warning":
            self.logger.warning(message, extra=log_data)
        else:
            self.logger.info(message, extra=log_data)
    
    def log_performance_metrics(self, session_id: str, metrics: Dict[str, Any]):
        """Log performance metrics with context"""
        self.log_transcription_event(
            session_id, "performance_metrics", metrics, "info"
        )
    
    def log_error(self, session_id: str, error: Exception, context: Dict[str, Any] = None):
        """Log error with full traceback and context"""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        self.log_transcription_event(
            session_id, "error", error_data, "error"
        )

def with_retry_logic(max_retries: int = 3, backoff_factor: float = 1.5):
    """Decorator for exponential backoff retry logic"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        delay = backoff_factor ** attempt
                        logging.warning(
                            f"Retry attempt {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after {delay:.1f}s delay: {e}"
                        )
                        time.sleep(delay)
                    else:
                        logging.error(
                            f"All retry attempts failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        return wrapper
    return decorator

# Global structured logger
transcription_logger = StructuredLogger("transcription")