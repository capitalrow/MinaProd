#!/usr/bin/env python3
"""
ROBUSTNESS ENHANCEMENTS FOR MINA TRANSCRIPTION PIPELINE
Implements circuit breakers, connection management, and structured logging
"""

import logging
import time
import json
import threading
import hashlib
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """
    Circuit breaker pattern implementation for preventing cascade failures.
    """
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        with self.lock:
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                    logger.info("🔄 Circuit breaker: Attempting reset")
                else:
                    raise Exception(f"Circuit breaker OPEN - service unavailable")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time > self.timeout_seconds
    
    def _on_success(self):
        """Handle successful operation."""
        if self.state == 'HALF_OPEN':
            self.state = 'CLOSED'
            self.failure_count = 0
            logger.info("✅ Circuit breaker: Reset to CLOSED")
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(f"🚨 Circuit breaker: OPEN after {self.failure_count} failures")

class ConnectionManager:
    """
    Manages WebSocket connections to prevent duplicates and handle reconnection.
    """
    
    def __init__(self):
        self.active_connections = {}
        self.connection_history = deque(maxlen=1000)
        self.lock = threading.Lock()
    
    def register_connection(self, session_id: str, connection_id: str) -> bool:
        """
        Register a new connection, preventing duplicates.
        Returns True if connection is allowed, False if duplicate.
        """
        with self.lock:
            # Check for existing connection
            if session_id in self.active_connections:
                existing_conn = self.active_connections[session_id]
                logger.warning(f"🔄 Duplicate connection attempt for session {session_id}")
                
                # Allow if enough time passed (connection might be stale)
                if time.time() - existing_conn['timestamp'] > 30:  # 30 seconds
                    logger.info(f"⏰ Replacing stale connection for session {session_id}")
                    self._close_connection(session_id)
                else:
                    logger.warning(f"🚨 Rejecting duplicate connection for active session {session_id}")
                    return False
            
            # Register new connection
            self.active_connections[session_id] = {
                'connection_id': connection_id,
                'timestamp': time.time(),
                'session_id': session_id
            }
            
            self.connection_history.append({
                'action': 'connected',
                'session_id': session_id,
                'connection_id': connection_id,
                'timestamp': time.time()
            })
            
            logger.info(f"✅ Connection registered: {session_id} -> {connection_id}")
            return True
    
    def _close_connection(self, session_id: str):
        """Close and cleanup connection."""
        if session_id in self.active_connections:
            conn_data = self.active_connections[session_id]
            del self.active_connections[session_id]
            
            self.connection_history.append({
                'action': 'disconnected',
                'session_id': session_id,
                'connection_id': conn_data['connection_id'],
                'timestamp': time.time()
            })
            
            logger.info(f"🔌 Connection closed: {session_id}")
    
    def disconnect(self, session_id: str):
        """Handle connection disconnect."""
        with self.lock:
            self._close_connection(session_id)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        with self.lock:
            return {
                'active_connections': len(self.active_connections),
                'connection_sessions': list(self.active_connections.keys()),
                'recent_activity': list(self.connection_history)[-10:]
            }

class StructuredLogger:
    """
    Structured logging with request IDs and session tracking.
    """
    
    def __init__(self):
        self.request_context = threading.local()
        
    def set_request_context(self, session_id: str, request_id: str = None):
        """Set context for current request."""
        if request_id is None:
            request_id = str(uuid.uuid4())[:8]
        
        self.request_context.session_id = session_id
        self.request_context.request_id = request_id
        self.request_context.start_time = time.time()
    
    def log_structured(self, level: str, message: str, **kwargs):
        """Log with structured data including context."""
        try:
            context = {
                'session_id': getattr(self.request_context, 'session_id', 'unknown'),
                'request_id': getattr(self.request_context, 'request_id', 'unknown'),
                'timestamp': time.time(),
                'processing_time_ms': (time.time() - getattr(self.request_context, 'start_time', time.time())) * 1000
            }
            
            # Merge context with additional data
            log_data = {**context, **kwargs}
            
            # Format structured log message
            structured_msg = f"[{context['session_id']}:{context['request_id']}] {message}"
            if kwargs:
                structured_msg += f" | Data: {json.dumps(log_data, default=str)}"
            
            # Log at appropriate level
            getattr(logger, level.lower())(structured_msg)
            
        except Exception as e:
            logger.error(f"Structured logging error: {e}")
            # Fallback to basic logging
            logger.log(getattr(logging, level.upper()), message)

class SessionPersistence:
    """
    Session persistence and recovery for handling network interruptions.
    """
    
    def __init__(self):
        self.session_store = {}
        self.session_timeouts = {}
        self.cleanup_interval = 300  # 5 minutes
        self.lock = threading.Lock()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_sessions, daemon=True)
        self.cleanup_thread.start()
    
    def save_session_state(self, session_id: str, state_data: Dict[str, Any]):
        """Save session state for recovery."""
        with self.lock:
            self.session_store[session_id] = {
                'state': state_data,
                'timestamp': time.time(),
                'last_activity': time.time()
            }
            
            # Set session timeout
            self.session_timeouts[session_id] = time.time() + 3600  # 1 hour timeout
    
    def restore_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Restore session state after reconnection."""
        with self.lock:
            if session_id in self.session_store:
                session_data = self.session_store[session_id]
                
                # Update last activity
                session_data['last_activity'] = time.time()
                
                logger.info(f"♻️ Session state restored: {session_id}")
                return session_data['state']
            
            return None
    
    def _cleanup_expired_sessions(self):
        """Background cleanup of expired sessions."""
        while True:
            try:
                current_time = time.time()
                
                with self.lock:
                    expired_sessions = []
                    for session_id, timeout_time in self.session_timeouts.items():
                        if current_time > timeout_time:
                            expired_sessions.append(session_id)
                    
                    for session_id in expired_sessions:
                        if session_id in self.session_store:
                            del self.session_store[session_id]
                        if session_id in self.session_timeouts:
                            del self.session_timeouts[session_id]
                        
                        logger.info(f"🗑️ Expired session cleaned up: {session_id}")
                
                time.sleep(self.cleanup_interval)
                
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
                time.sleep(60)  # Wait before retrying

class RobustnessOrchestrator:
    """
    Main orchestrator for all robustness enhancements.
    """
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        self.connection_manager = ConnectionManager()
        self.structured_logger = StructuredLogger()
        self.session_persistence = SessionPersistence()
        
        self.is_active = False
        
    def activate_robustness_features(self):
        """Activate all robustness features."""
        self.is_active = True
        logger.info("🛡️ Robustness features activated:")
        logger.info("  ✅ Circuit breaker pattern")
        logger.info("  ✅ Connection deduplication")
        logger.info("  ✅ Structured logging with request IDs")
        logger.info("  ✅ Session persistence and recovery")
        
    def execute_with_protection(self, func, session_id: str, *args, **kwargs):
        """Execute function with full robustness protection."""
        if not self.is_active:
            return func(*args, **kwargs)
        
        # Set logging context
        request_id = str(uuid.uuid4())[:8]
        self.structured_logger.set_request_context(session_id, request_id)
        
        try:
            # Execute with circuit breaker protection
            result = self.circuit_breaker.call(func, *args, **kwargs)
            
            self.structured_logger.log_structured('info', f"Operation successful: {func.__name__}", 
                                                result_type=type(result).__name__)
            
            return result
            
        except Exception as e:
            self.structured_logger.log_structured('error', f"Operation failed: {func.__name__}", 
                                                error=str(e), error_type=type(e).__name__)
            raise e
    
    def handle_connection(self, session_id: str, connection_id: str = None) -> bool:
        """Handle new connection with duplicate prevention."""
        if connection_id is None:
            connection_id = str(uuid.uuid4())[:8]
        
        return self.connection_manager.register_connection(session_id, connection_id)
    
    def save_session(self, session_id: str, state: Dict[str, Any]):
        """Save session state for recovery."""
        self.session_persistence.save_session_state(session_id, state)
    
    def restore_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Restore session state."""
        return self.session_persistence.restore_session_state(session_id)
    
    def get_robustness_status(self) -> Dict[str, Any]:
        """Get comprehensive robustness status."""
        return {
            'circuit_breaker': {
                'state': self.circuit_breaker.state,
                'failure_count': self.circuit_breaker.failure_count,
                'last_failure': self.circuit_breaker.last_failure_time
            },
            'connections': self.connection_manager.get_connection_stats(),
            'session_persistence': {
                'active_sessions': len(self.session_persistence.session_store),
                'pending_timeouts': len(self.session_persistence.session_timeouts)
            },
            'overall_status': 'ACTIVE' if self.is_active else 'INACTIVE'
        }

# Global robustness orchestrator
robustness_orchestrator = RobustnessOrchestrator()

def activate_robustness_enhancements():
    """Activate all robustness enhancements."""
    robustness_orchestrator.activate_robustness_features()
    return True

def get_robustness_status():
    """Get current robustness status."""
    return robustness_orchestrator.get_robustness_status()

if __name__ == "__main__":
    # Test robustness features
    activate_robustness_enhancements()
    status = get_robustness_status()
    print(json.dumps(status, indent=2))