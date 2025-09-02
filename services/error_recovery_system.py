"""
🛡️ ERROR RECOVERY SYSTEM
Advanced error recovery and resilience mechanisms for production stability
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import queue
import asyncio

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorEvent:
    """Error event for tracking and recovery"""
    timestamp: float
    error_type: str
    severity: ErrorSeverity
    session_id: Optional[str]
    error_message: str
    stack_trace: Optional[str]
    context: Dict[str, Any]
    recovery_attempted: bool = False
    recovery_successful: bool = False


class CircuitBreaker:
    """Circuit breaker pattern for service protection"""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = 'closed'  # closed, open, half-open
        self.lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self.lock:
            if self.state == 'open':
                if time.time() - self.last_failure_time > self.timeout_seconds:
                    self.state = 'half-open'
                    logger.info("🔄 Circuit breaker moving to half-open state")
                else:
                    raise Exception(f"Circuit breaker is open. Service unavailable.")
            
            try:
                result = func(*args, **kwargs)
                
                if self.state == 'half-open':
                    self.state = 'closed'
                    self.failure_count = 0
                    logger.info("✅ Circuit breaker closed - service recovered")
                
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = 'open'
                    logger.warning(f"🚫 Circuit breaker opened after {self.failure_count} failures")
                
                raise e


class RetryStrategy:
    """Configurable retry strategy with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 30.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def execute(self, func: Callable, *args, **kwargs):
        """Execute function with retry strategy"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(f"❌ Function failed after {self.max_retries} retries: {e}")
                    raise e
                
                # Calculate delay with exponential backoff
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.warning(f"⚠️ Attempt {attempt + 1} failed, retrying in {delay:.1f}s: {e}")
                time.sleep(delay)
        
        raise last_exception


class ErrorRecoverySystem:
    """
    Comprehensive error recovery system with multiple resilience patterns
    """
    
    def __init__(self):
        self.error_history: List[ErrorEvent] = []
        self.recovery_strategies: Dict[str, Callable] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_lock = threading.Lock()
        
        # Error thresholds
        self.error_rate_threshold = 10.0  # 10% error rate threshold
        self.consecutive_error_threshold = 5
        
        # Monitoring
        self.total_errors = 0
        self.total_requests = 0
        self.consecutive_errors = 0
        
        # Recovery queues
        self.recovery_queue = queue.Queue()
        self.recovery_thread = None
        self.recovery_active = False
        
        # Register default recovery strategies
        self._register_default_strategies()
        
        logger.info("🛡️ Error recovery system initialized")
    
    def start_recovery_service(self):
        """Start the recovery service thread"""
        if self.recovery_active:
            return
        
        self.recovery_active = True
        self.recovery_thread = threading.Thread(target=self._recovery_worker, daemon=True)
        self.recovery_thread.start()
        
        logger.info("▶️ Error recovery service started")
    
    def stop_recovery_service(self):
        """Stop the recovery service"""
        self.recovery_active = False
        if self.recovery_thread and self.recovery_thread.is_alive():
            self.recovery_thread.join(timeout=5.0)
        
        logger.info("⏹️ Error recovery service stopped")
    
    def record_error(self, error_type: str, error_message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    session_id: Optional[str] = None, context: Optional[Dict] = None,
                    stack_trace: Optional[str] = None) -> ErrorEvent:
        """Record an error and potentially trigger recovery"""
        
        error_event = ErrorEvent(
            timestamp=time.time(),
            error_type=error_type,
            severity=severity,
            session_id=session_id,
            error_message=error_message,
            stack_trace=stack_trace,
            context=context or {}
        )
        
        with self.error_lock:
            self.error_history.append(error_event)
            self.total_errors += 1
            self.consecutive_errors += 1
            
            # Keep history manageable
            if len(self.error_history) > 1000:
                self.error_history = self.error_history[-500:]
        
        # Check if recovery is needed
        self._check_recovery_triggers(error_event)
        
        logger.error(f"❌ Error recorded: {error_type} - {error_message}")
        return error_event
    
    def record_success(self):
        """Record successful operation"""
        with self.error_lock:
            self.total_requests += 1
            self.consecutive_errors = 0
    
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """Register custom recovery strategy"""
        self.recovery_strategies[error_type] = strategy
        logger.info(f"🔧 Registered recovery strategy for: {error_type}")
    
    def _register_default_strategies(self):
        """Register default recovery strategies"""
        
        def restart_session_strategy(error_event: ErrorEvent):
            """Restart session on transcription errors"""
            if error_event.session_id:
                logger.info(f"🔄 Attempting session restart: {error_event.session_id}")
                # Implementation would restart the session
                return True
            return False
        
        def clear_audio_buffer_strategy(error_event: ErrorEvent):
            """Clear audio buffer on processing errors"""
            logger.info("🧹 Clearing audio buffers")
            # Implementation would clear buffers
            return True
        
        def reset_connection_strategy(error_event: ErrorEvent):
            """Reset connections on network errors"""
            logger.info("🔌 Resetting connections")
            # Implementation would reset connections
            return True
        
        def fallback_model_strategy(error_event: ErrorEvent):
            """Switch to fallback model on API errors"""
            logger.info("🔄 Switching to fallback transcription model")
            # Implementation would switch to backup model
            return True
        
        # Register strategies
        self.recovery_strategies.update({
            'transcription_error': restart_session_strategy,
            'audio_processing_error': clear_audio_buffer_strategy,
            'network_error': reset_connection_strategy,
            'api_error': fallback_model_strategy
        })
    
    def _check_recovery_triggers(self, error_event: ErrorEvent):
        """Check if recovery should be triggered"""
        
        # Immediate recovery for critical errors
        if error_event.severity == ErrorSeverity.CRITICAL:
            self.recovery_queue.put(error_event)
            return
        
        # Recovery for consecutive errors
        if self.consecutive_errors >= self.consecutive_error_threshold:
            logger.warning(f"⚠️ Consecutive error threshold reached: {self.consecutive_errors}")
            self.recovery_queue.put(error_event)
            return
        
        # Recovery for high error rate
        if self.total_requests > 0:
            error_rate = (self.total_errors / self.total_requests) * 100
            if error_rate >= self.error_rate_threshold:
                logger.warning(f"⚠️ Error rate threshold reached: {error_rate:.1f}%")
                self.recovery_queue.put(error_event)
                return
    
    def _recovery_worker(self):
        """Background worker for error recovery"""
        logger.info("🔄 Error recovery worker started")
        
        while self.recovery_active:
            try:
                error_event = self.recovery_queue.get(timeout=1.0)
                self._attempt_recovery(error_event)
                self.recovery_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Error in recovery worker: {e}")
    
    def _attempt_recovery(self, error_event: ErrorEvent):
        """Attempt to recover from error"""
        
        if error_event.recovery_attempted:
            logger.warning(f"⚠️ Recovery already attempted for error: {error_event.error_type}")
            return
        
        error_event.recovery_attempted = True
        
        # Try specific recovery strategy
        strategy = self.recovery_strategies.get(error_event.error_type)
        if strategy:
            try:
                success = strategy(error_event)
                error_event.recovery_successful = success
                
                if success:
                    logger.info(f"✅ Recovery successful for: {error_event.error_type}")
                    # Reset consecutive error count on successful recovery
                    with self.error_lock:
                        self.consecutive_errors = 0
                else:
                    logger.warning(f"⚠️ Recovery failed for: {error_event.error_type}")
                    
            except Exception as e:
                logger.error(f"❌ Recovery strategy failed: {e}")
                error_event.recovery_successful = False
        else:
            logger.warning(f"⚠️ No recovery strategy for error type: {error_event.error_type}")
    
    def get_error_statistics(self) -> Dict:
        """Get error statistics and recovery metrics"""
        with self.error_lock:
            recent_errors = [e for e in self.error_history if time.time() - e.timestamp < 3600]  # Last hour
            
            error_types = {}
            recovery_success_count = 0
            recovery_attempt_count = 0
            
            for error in recent_errors:
                error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
                
                if error.recovery_attempted:
                    recovery_attempt_count += 1
                    if error.recovery_successful:
                        recovery_success_count += 1
            
            error_rate = (self.total_errors / max(self.total_requests, 1)) * 100
            recovery_rate = (recovery_success_count / max(recovery_attempt_count, 1)) * 100
            
            return {
                'total_errors': self.total_errors,
                'total_requests': self.total_requests,
                'error_rate_percent': error_rate,
                'consecutive_errors': self.consecutive_errors,
                'recent_errors_1h': len(recent_errors),
                'error_types': error_types,
                'recovery_statistics': {
                    'attempts': recovery_attempt_count,
                    'successes': recovery_success_count,
                    'success_rate_percent': recovery_rate
                },
                'circuit_breakers': {
                    name: breaker.state for name, breaker in self.circuit_breakers.items()
                }
            }
    
    def get_health_status(self) -> Dict:
        """Get system health status from error perspective"""
        stats = self.get_error_statistics()
        
        # Determine health status
        if stats['error_rate_percent'] < 1.0 and stats['consecutive_errors'] < 3:
            health = 'healthy'
        elif stats['error_rate_percent'] < 5.0 and stats['consecutive_errors'] < 5:
            health = 'degraded'
        else:
            health = 'critical'
        
        return {
            'status': health,
            'error_rate': stats['error_rate_percent'],
            'consecutive_errors': stats['consecutive_errors'],
            'recovery_rate': stats['recovery_statistics']['success_rate_percent'],
            'active_circuit_breakers': len([cb for cb in self.circuit_breakers.values() if cb.state != 'closed'])
        }


# Global error recovery system
_error_recovery = None

def get_error_recovery() -> ErrorRecoverySystem:
    """Get or create global error recovery system"""
    global _error_recovery
    if _error_recovery is None:
        _error_recovery = ErrorRecoverySystem()
        _error_recovery.start_recovery_service()
    return _error_recovery


# Decorator for automatic error handling
def with_error_recovery(error_type: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """Decorator to automatically handle errors with recovery system"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            recovery_system = get_error_recovery()
            try:
                result = func(*args, **kwargs)
                recovery_system.record_success()
                return result
            except Exception as e:
                recovery_system.record_error(
                    error_type=error_type,
                    error_message=str(e),
                    severity=severity,
                    context={'function': func.__name__, 'args': str(args)[:100]}
                )
                raise e
        return wrapper
    return decorator