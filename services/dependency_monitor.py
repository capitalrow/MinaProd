"""
🔗 External Dependency Health Monitor
Monitors health of external services like OpenAI API, database, Redis for 100% observability.
"""
import logging
import time
import requests
from typing import Dict, List, Optional, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import deque

logger = logging.getLogger(__name__)

class DependencyStatus(Enum):
    """Dependency health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy" 
    UNKNOWN = "unknown"

@dataclass
class DependencyCheck:
    """Individual dependency health check result"""
    name: str
    status: DependencyStatus
    response_time: float
    timestamp: float
    error_message: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

@dataclass
class DependencyHealth:
    """Overall dependency health"""
    name: str
    status: DependencyStatus
    success_rate: float
    average_response_time: float
    last_check: float
    consecutive_failures: int = 0
    total_checks: int = 0
    failed_checks: int = 0

class DependencyMonitor:
    """Monitor health of external dependencies"""
    
    def __init__(self):
        self.dependencies: Dict[str, DependencyHealth] = {}
        self.check_history: Dict[str, deque] = {}
        self.lock = threading.RLock()
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Define dependencies to monitor
        self.dependency_configs = {
            'openai_api': {
                'check_interval': 60,  # Check every minute
                'timeout': 10,
                'max_failures': 3,
                'check_function': self._check_openai_api
            },
            'database': {
                'check_interval': 30,  # Check every 30 seconds
                'timeout': 5,
                'max_failures': 2,
                'check_function': self._check_database
            },
            'redis': {
                'check_interval': 30,
                'timeout': 5,
                'max_failures': 2,
                'check_function': self._check_redis
            },
            'file_system': {
                'check_interval': 120,  # Check every 2 minutes
                'timeout': 5,
                'max_failures': 3,
                'check_function': self._check_file_system
            }
        }
        
        # Initialize dependency health tracking
        for name in self.dependency_configs:
            self.dependencies[name] = DependencyHealth(
                name=name,
                status=DependencyStatus.UNKNOWN,
                success_rate=100.0,
                average_response_time=0.0,
                last_check=0.0
            )
            self.check_history[name] = deque(maxlen=100)
        
        logger.info("🔗 Dependency monitor initialized")
    
    def start_monitoring(self):
        """Start continuous dependency monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("🔗 Dependency monitoring started")
    
    def stop_monitoring(self):
        """Stop dependency monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🔗 Dependency monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        last_checks = {name: 0 for name in self.dependency_configs}
        
        while self.monitoring_active:
            current_time = time.time()
            
            for name, config in self.dependency_configs.items():
                if current_time - last_checks[name] >= config['check_interval']:
                    try:
                        self._perform_health_check(name, config)
                        last_checks[name] = current_time
                    except Exception as e:
                        logger.error(f"❌ Error checking dependency {name}: {e}")
            
            time.sleep(5)  # Check every 5 seconds for due checks
    
    def _perform_health_check(self, name: str, config: Dict):
        """Perform health check for specific dependency"""
        start_time = time.time()
        
        try:
            # Call the check function
            check_function = config['check_function']
            result = check_function()
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            check = DependencyCheck(
                name=name,
                status=DependencyStatus.HEALTHY if result['success'] else DependencyStatus.UNHEALTHY,
                response_time=response_time,
                timestamp=time.time(),
                error_message=result.get('error'),
                metadata=result.get('metadata', {})
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            check = DependencyCheck(
                name=name,
                status=DependencyStatus.UNHEALTHY,
                response_time=response_time,
                timestamp=time.time(),
                error_message=str(e)
            )
        
        self._update_dependency_health(check)
    
    def _update_dependency_health(self, check: DependencyCheck):
        """Update dependency health based on check result"""
        with self.lock:
            name = check.name
            health = self.dependencies[name]
            
            # Add to history
            self.check_history[name].append(check)
            
            # Update counters
            health.total_checks += 1
            health.last_check = check.timestamp
            
            if check.status == DependencyStatus.HEALTHY:
                health.consecutive_failures = 0
            else:
                health.consecutive_failures += 1
                health.failed_checks += 1
            
            # Calculate success rate (last 100 checks)
            recent_checks = list(self.check_history[name])
            if recent_checks:
                successful_checks = sum(1 for c in recent_checks if c.status == DependencyStatus.HEALTHY)
                health.success_rate = (successful_checks / len(recent_checks)) * 100
                
                # Calculate average response time
                health.average_response_time = sum(c.response_time for c in recent_checks) / len(recent_checks)
            
            # Determine overall status
            config = self.dependency_configs[name]
            if health.consecutive_failures >= config['max_failures']:
                health.status = DependencyStatus.UNHEALTHY
            elif health.success_rate < 95:
                health.status = DependencyStatus.DEGRADED
            else:
                health.status = DependencyStatus.HEALTHY
            
            # Log status changes
            if check.status != DependencyStatus.HEALTHY:
                logger.warning(f"🔗 Dependency {name} check failed: {check.error_message}")
            elif health.consecutive_failures == 0 and health.status == DependencyStatus.HEALTHY:
                logger.info(f"🔗 Dependency {name} is healthy")
    
    def _check_openai_api(self) -> Dict:
        """Check OpenAI API health"""
        try:
            from services.openai_client_manager import get_openai_client_manager
            
            client_manager = get_openai_client_manager()
            client = client_manager.get_client()
            
            # Try a simple API call to check health
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            
            return {
                'success': True,
                'metadata': {
                    'model': 'gpt-3.5-turbo',
                    'api_version': 'v1'
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"OpenAI API error: {str(e)}"
            }
    
    def _check_database(self) -> Dict:
        """Check database connectivity"""
        try:
            from app import db
            from sqlalchemy import text
            
            # Simple database query
            result = db.session.execute(text('SELECT 1')).fetchone()
            
            return {
                'success': True,
                'metadata': {
                    'query': 'SELECT 1',
                    'result': str(result[0]) if result else None
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Database error: {str(e)}"
            }
    
    def _check_redis(self) -> Dict:
        """Check Redis connectivity"""
        try:
            # Try to import and ping Redis
            import redis
            
            # Use default Redis connection (adjust if needed)
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=5)
            result = r.ping()
            
            return {
                'success': result,
                'metadata': {
                    'ping_result': result
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Redis error: {str(e)}"
            }
    
    def _check_file_system(self) -> Dict:
        """Check file system health"""
        try:
            import os
            import tempfile
            
            # Test write/read to temp directory
            with tempfile.NamedTemporaryFile(mode='w', delete=True) as f:
                f.write("health_check")
                f.flush()
                
                # Check if file exists and is readable
                if os.path.exists(f.name):
                    with open(f.name, 'r') as read_f:
                        content = read_f.read()
                        success = content == "health_check"
                else:
                    success = False
            
            return {
                'success': success,
                'metadata': {
                    'temp_dir': tempfile.gettempdir()
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"File system error: {str(e)}"
            }
    
    def get_dependency_health(self, name: str) -> Optional[DependencyHealth]:
        """Get health status for specific dependency"""
        with self.lock:
            return self.dependencies.get(name)
    
    def get_all_dependencies(self) -> Dict[str, DependencyHealth]:
        """Get health status for all dependencies"""
        with self.lock:
            return self.dependencies.copy()
    
    def get_overall_health(self) -> Dict:
        """Get overall dependency health summary"""
        with self.lock:
            total_deps = len(self.dependencies)
            healthy_deps = sum(1 for dep in self.dependencies.values() if dep.status == DependencyStatus.HEALTHY)
            degraded_deps = sum(1 for dep in self.dependencies.values() if dep.status == DependencyStatus.DEGRADED)
            unhealthy_deps = sum(1 for dep in self.dependencies.values() if dep.status == DependencyStatus.UNHEALTHY)
            
            if unhealthy_deps > 0:
                overall_status = "critical"
            elif degraded_deps > 0:
                overall_status = "warning"
            else:
                overall_status = "healthy"
            
            return {
                'status': overall_status,
                'total_dependencies': total_deps,
                'healthy': healthy_deps,
                'degraded': degraded_deps,
                'unhealthy': unhealthy_deps,
                'health_score': (healthy_deps / total_deps * 100) if total_deps > 0 else 0,
                'dependencies': {name: dep.status.value for name, dep in self.dependencies.items()}
            }

# Global dependency monitor instance
_dependency_monitor = None

def get_dependency_monitor() -> DependencyMonitor:
    """Get global dependency monitor instance"""
    global _dependency_monitor
    if _dependency_monitor is None:
        _dependency_monitor = DependencyMonitor()
    return _dependency_monitor