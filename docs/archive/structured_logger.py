#!/usr/bin/env python3
"""
Structured JSON Logger with Request ID and Session ID tracking
Provides comprehensive logging for the transcription pipeline
"""

import json
import time
import uuid
import logging
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager

class StructuredLogger:
    """Structured JSON logger with request/session tracking"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.local = threading.local()
        
    def set_context(self, request_id: str = None, session_id: str = None, **kwargs):
        """Set logging context for current thread"""
        if not hasattr(self.local, 'context'):
            self.local.context = {}
        
        if request_id:
            self.local.context['request_id'] = request_id
        if session_id:
            self.local.context['session_id'] = session_id
        
        # Add any additional context
        self.local.context.update(kwargs)
    
    @contextmanager
    def context(self, **kwargs):
        """Context manager for temporary logging context"""
        old_context = getattr(self.local, 'context', {}).copy()
        self.set_context(**kwargs)
        try:
            yield
        finally:
            self.local.context = old_context
    
    def _format_log(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """Format log entry as structured JSON"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            'logger': self.logger.name
        }
        
        # Add thread context if available
        if hasattr(self.local, 'context'):
            log_entry.update(self.local.context)
        
        # Add any additional fields
        log_entry.update(kwargs)
        
        return log_entry
    
    def info(self, message: str, **kwargs):
        """Log info message with structured format"""
        log_data = self._format_log('INFO', message, **kwargs)
        self.logger.info(json.dumps(log_data))
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured format"""
        log_data = self._format_log('WARNING', message, **kwargs)
        self.logger.warning(json.dumps(log_data))
    
    def error(self, message: str, **kwargs):
        """Log error message with structured format"""
        log_data = self._format_log('ERROR', message, **kwargs)
        self.logger.error(json.dumps(log_data))
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured format"""
        log_data = self._format_log('DEBUG', message, **kwargs)
        self.logger.debug(json.dumps(log_data))
    
    def audit(self, action: str, result: str, **kwargs):
        """Log audit event with structured format"""
        log_data = self._format_log('AUDIT', f"Action: {action}, Result: {result}", 
                                   action=action, result=result, **kwargs)
        self.logger.info(json.dumps(log_data))
    
    def metric(self, metric_name: str, value: float, unit: str = None, **kwargs):
        """Log metric with structured format"""
        log_data = self._format_log('METRIC', f"Metric: {metric_name} = {value}", 
                                   metric_name=metric_name, metric_value=value, 
                                   metric_unit=unit, **kwargs)
        self.logger.info(json.dumps(log_data))

# Create structured loggers for different components
transcription_logger = StructuredLogger('transcription')
websocket_logger = StructuredLogger('websocket')  
quality_logger = StructuredLogger('quality')
pipeline_logger = StructuredLogger('pipeline')

def generate_request_id() -> str:
    """Generate unique request ID"""
    return str(uuid.uuid4())[:8]

def log_performance(func):
    """Decorator to log function performance"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        request_id = generate_request_id()
        
        transcription_logger.set_context(request_id=request_id)
        transcription_logger.info(f"Starting {func.__name__}", function=func.__name__)
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            transcription_logger.metric(f"{func.__name__}_duration", duration, "seconds")
            transcription_logger.info(f"Completed {func.__name__}", function=func.__name__, success=True)
            return result
        except Exception as e:
            duration = time.time() - start_time
            transcription_logger.error(f"Failed {func.__name__}: {str(e)}", 
                                     function=func.__name__, error=str(e), duration=duration)
            raise
    
    return wrapper