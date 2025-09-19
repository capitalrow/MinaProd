# 🛡️ **FIX PACK 3: Reliability and Resilience Components**

import time
import json
import redis
import threading
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from collections import deque, defaultdict
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open" 
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker pattern implementation for service protection."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30, 
                 monitoring_period: int = 10):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.monitoring_period = monitoring_period
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.successful_calls = 0
        
        self.call_history = deque(maxlen=100)
        self.lock = threading.RLock()
    
    async def execute(self, func: Callable, *args, **kwargs):
        """Execute a function with circuit breaker protection."""
        with self.lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info("Circuit breaker moved to HALF_OPEN state")
                else:
                    raise Exception("Circuit breaker is OPEN - service unavailable")
        
        start_time = time.time()
        try:
            result = await func(*args, **kwargs) if hasattr(func, '__call__') else func
            self._record_success(start_time)
            return result
        except Exception as e:
            self._record_failure(start_time, str(e))
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _record_success(self, start_time: float):
        """Record successful call."""
        with self.lock:
            self.call_history.append({
                'success': True,
                'timestamp': time.time(),
                'duration': time.time() - start_time
            })
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.successful_calls += 1
                if self.successful_calls >= 3:  # Reset after 3 successful calls
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.successful_calls = 0
                    logger.info("Circuit breaker CLOSED - service recovered")
    
    def _record_failure(self, start_time: float, error: str):
        """Record failed call."""
        with self.lock:
            self.call_history.append({
                'success': False,
                'timestamp': time.time(),
                'duration': time.time() - start_time,
                'error': error
            })
            
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.error(f"Circuit breaker OPENED due to {self.failure_count} failures")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        recent_calls = [call for call in self.call_history 
                       if time.time() - call['timestamp'] < self.monitoring_period]
        
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_rate': sum(1 for call in recent_calls if call['success']) / len(recent_calls) if recent_calls else 0,
            'recent_calls': len(recent_calls),
            'last_failure_time': self.last_failure_time,
            'time_since_last_failure': time.time() - self.last_failure_time if self.last_failure_time else None
        }

class SessionPersistenceManager:
    """Redis-backed session persistence with redundancy."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        try:
            self.redis_client = redis.from_url(redis_url)
            self.redis_available = True
        except:
            self.redis_client = None
            self.redis_available = False
            logger.warning("Redis not available, using local cache only")
        
        self.local_cache = {}
        self.persistence_interval = 10  # seconds
        self.ttl = 3600  # 1 hour
        
        # Start background persistence thread
        self._start_persistence_thread()
    
    def persist_session_state(self, session_id: str, state: Dict[str, Any]):
        """Persist session state with triple redundancy."""
        serialized_state = json.dumps(state, default=str)
        
        try:
            # Primary: Redis
            if self.redis_available:
                self.redis_client.setex(
                    f"session:{session_id}", 
                    self.ttl,
                    serialized_state
                )
            
            # Secondary: Local cache
            self.local_cache[session_id] = {
                'state': state,
                'timestamp': time.time(),
                'serialized': serialized_state
            }
            
            # Tertiary: Database backup (implement based on your DB)
            self._backup_to_database(session_id, state)
            
        except Exception as e:
            logger.error(f"Session persistence failed for {session_id}: {e}")
            # Ensure local cache backup at minimum
            self.local_cache[session_id] = {
                'state': state,
                'timestamp': time.time(),
                'serialized': serialized_state
            }
    
    def restore_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Restore session state from available sources."""
        # Try Redis first
        if self.redis_available:
            try:
                cached_state = self.redis_client.get(f"session:{session_id}")
                if cached_state:
                    return json.loads(cached_state.decode('utf-8'))
            except Exception as e:
                logger.error(f"Redis restore failed for {session_id}: {e}")
        
        # Try local cache
        if session_id in self.local_cache:
            cache_entry = self.local_cache[session_id]
            # Check if not too old (2 hours max)
            if time.time() - cache_entry['timestamp'] < 7200:
                return cache_entry['state']
        
        # Try database backup
        return self._restore_from_database(session_id)
    
    def _backup_to_database(self, session_id: str, state: Dict[str, Any]):
        """Backup session state to database."""
        try:
            from app_refactored import db
            from models.session import Session
            
            # Update existing session or create backup entry
            session = Session.query.filter_by(external_id=session_id).first()
            if session:
                session.backup_state = json.dumps(state, default=str)
                session.backup_timestamp = time.time()
                db.session.commit()
        except Exception as e:
            logger.error(f"Database backup failed for {session_id}: {e}")
    
    def _restore_from_database(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Restore session state from database backup."""
        try:
            from models.session import Session
            
            session = Session.query.filter_by(external_id=session_id).first()
            if session and hasattr(session, 'backup_state') and session.backup_state:
                return json.loads(session.backup_state)
        except Exception as e:
            logger.error(f"Database restore failed for {session_id}: {e}")
        
        return None
    
    def _start_persistence_thread(self):
        """Start background thread for periodic persistence."""
        def persistence_worker():
            while True:
                try:
                    # Clean up old local cache entries
                    current_time = time.time()
                    expired_sessions = []
                    
                    for session_id, cache_entry in self.local_cache.items():
                        if current_time - cache_entry['timestamp'] > 7200:  # 2 hours
                            expired_sessions.append(session_id)
                    
                    for session_id in expired_sessions:
                        del self.local_cache[session_id]
                    
                    if expired_sessions:
                        logger.info(f"Cleaned up {len(expired_sessions)} expired cache entries")
                    
                    time.sleep(self.persistence_interval)
                except Exception as e:
                    logger.error(f"Persistence worker error: {e}")
                    time.sleep(self.persistence_interval)
        
        thread = threading.Thread(target=persistence_worker, daemon=True)
        thread.start()

class HealthMonitor:
    """Comprehensive health monitoring system."""
    
    def __init__(self):
        self.health_checks = {}
        self.health_history = defaultdict(lambda: deque(maxlen=100))
        self.alert_thresholds = {}
        self.alert_callbacks = []
        
    def register_health_check(self, name: str, check_func: Callable, 
                            threshold: float = 0.8, interval: int = 10):
        """Register a health check function."""
        self.health_checks[name] = {
            'function': check_func,
            'interval': interval,
            'last_check': 0,
            'enabled': True
        }
        self.alert_thresholds[name] = threshold
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks and return results."""
        current_time = time.time()
        health_results = {}
        
        for name, check_config in self.health_checks.items():
            if not check_config['enabled']:
                continue
                
            # Check if it's time to run this health check
            if current_time - check_config['last_check'] < check_config['interval']:
                continue
            
            try:
                result = check_config['function']()
                health_results[name] = {
                    'status': 'healthy' if result.get('healthy', False) else 'unhealthy',
                    'value': result.get('value', 0),
                    'details': result.get('details', {}),
                    'timestamp': current_time
                }
                
                # Record in history
                self.health_history[name].append(health_results[name])
                
                # Check alert threshold
                if result.get('value', 1) < self.alert_thresholds[name]:
                    self._trigger_alert(name, health_results[name])
                
                check_config['last_check'] = current_time
                
            except Exception as e:
                health_results[name] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': current_time
                }
                self.health_history[name].append(health_results[name])
        
        return health_results
    
    def _trigger_alert(self, check_name: str, result: Dict[str, Any]):
        """Trigger alert for failed health check."""
        alert_data = {
            'check_name': check_name,
            'status': result['status'],
            'value': result.get('value', 0),
            'threshold': self.alert_thresholds[check_name],
            'details': result.get('details', {}),
            'timestamp': result['timestamp']
        }
        
        logger.warning(f"Health check alert: {check_name} - {alert_data}")
        
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def add_alert_callback(self, callback: Callable):
        """Add callback function for health alerts."""
        self.alert_callbacks.append(callback)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary."""
        current_time = time.time()
        summary = {}
        
        for name, history in self.health_history.items():
            if not history:
                continue
                
            recent_checks = [check for check in history 
                           if current_time - check['timestamp'] < 300]  # Last 5 minutes
            
            if recent_checks:
                healthy_count = sum(1 for check in recent_checks 
                                  if check['status'] == 'healthy')
                
                summary[name] = {
                    'current_status': history[-1]['status'],
                    'health_rate': healthy_count / len(recent_checks),
                    'recent_checks': len(recent_checks),
                    'last_check': history[-1]['timestamp'],
                    'threshold': self.alert_thresholds[name]
                }
        
        return {
            'checks': summary,
            'overall_health': min((check.get('health_rate', 0) for check in summary.values()), default=1.0),
            'timestamp': current_time
        }