#!/usr/bin/env python3
"""
🐛 Production Feature: Centralized Error Tracking & Monitoring

Implements comprehensive error tracking, aggregation, and alerting system
for production environments. Provides detailed error context, stack traces,
and automated error analysis.

Key Features:
- Centralized error collection and storage
- Error aggregation and deduplication
- Performance impact tracking
- Automated error alerting
- Error trend analysis
- Integration with logging and monitoring
"""

import logging
import json
import traceback
import sys
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
import hashlib
import threading
from urllib.parse import urlparse
import os

logger = logging.getLogger(__name__)

@dataclass
class ErrorContext:
    """Error context information."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    url: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    additional_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}

@dataclass
class ErrorEvent:
    """Individual error event."""
    id: str
    error_hash: str
    timestamp: datetime
    level: str  # ERROR, WARNING, CRITICAL
    message: str
    exception_type: str
    stack_trace: List[str]
    file_path: str
    line_number: int
    function_name: str
    context: ErrorContext
    environment: str
    release_version: Optional[str] = None
    tags: Dict[str, str] = None
    fingerprint: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.fingerprint is None:
            self.fingerprint = []

@dataclass
class ErrorGroup:
    """Grouped error events."""
    error_hash: str
    first_seen: datetime
    last_seen: datetime
    count: int
    level: str
    title: str
    message: str
    exception_type: str
    file_path: str
    function_name: str
    environment: str
    is_resolved: bool = False
    assigned_to: Optional[str] = None
    release_version: Optional[str] = None

class CentralizedErrorTracker:
    """
    🐛 Production-grade centralized error tracking system.
    
    Captures, aggregates, and analyzes errors across the entire application
    providing comprehensive error monitoring and alerting.
    """
    
    def __init__(self):
        self.error_events = []
        self.error_groups = {}
        self.error_counts = defaultdict(int)
        self.alert_thresholds = {
            'error_rate_per_minute': 10,
            'critical_error_threshold': 1,
            'new_error_alert': True
        }
        
        # Thread-safe storage
        self._lock = threading.RLock()
        
        # Environment detection
        self.environment = os.environ.get('ENVIRONMENT', 'development')
        self.release_version = os.environ.get('RELEASE_VERSION', 'unknown')
        
        # Hook into Python's exception handling
        self._setup_global_exception_handler()
        
        logger.info("🐛 Centralized Error Tracker initialized")
    
    def _setup_global_exception_handler(self):
        """Set up global exception handler for uncaught exceptions."""
        original_excepthook = sys.excepthook
        
        def custom_excepthook(exc_type, exc_value, exc_traceback):
            if exc_type == KeyboardInterrupt:
                # Don't capture keyboard interrupts
                original_excepthook(exc_type, exc_value, exc_traceback)
                return
            
            # Capture the exception
            self.capture_exception(
                exc_value,
                level="CRITICAL",
                context=ErrorContext(additional_data={"uncaught": True})
            )
            
            # Call original handler
            original_excepthook(exc_type, exc_value, exc_traceback)
        
        sys.excepthook = custom_excepthook
    
    def capture_exception(self, exception: Exception, level: str = "ERROR",
                         context: Optional[ErrorContext] = None,
                         tags: Optional[Dict[str, str]] = None) -> str:
        """Capture exception with full context."""
        try:
            with self._lock:
                # Generate error ID
                error_id = self._generate_error_id()
                
                # Extract exception details
                exc_type = type(exception).__name__
                exc_message = str(exception)
                
                # Get stack trace
                if hasattr(exception, '__traceback__') and exception.__traceback__:
                    tb = exception.__traceback__
                else:
                    tb = sys.exc_info()[2]
                
                stack_trace = []
                file_path = "unknown"
                line_number = 0
                function_name = "unknown"
                
                if tb:
                    stack_trace = traceback.format_tb(tb)
                    # Get the last frame for file/line info
                    last_frame = tb
                    while last_frame.tb_next:
                        last_frame = last_frame.tb_next
                    
                    file_path = last_frame.tb_frame.f_code.co_filename
                    line_number = last_frame.tb_lineno
                    function_name = last_frame.tb_frame.f_code.co_name
                
                # Generate error hash for grouping
                error_hash = self._generate_error_hash(exc_type, exc_message, file_path, function_name)
                
                # Create error event
                error_event = ErrorEvent(
                    id=error_id,
                    error_hash=error_hash,
                    timestamp=datetime.utcnow(),
                    level=level,
                    message=exc_message,
                    exception_type=exc_type,
                    stack_trace=stack_trace,
                    file_path=file_path,
                    line_number=line_number,
                    function_name=function_name,
                    context=context or ErrorContext(),
                    environment=self.environment,
                    release_version=self.release_version,
                    tags=tags or {}
                )
                
                # Store error event
                self.error_events.append(error_event)
                self.error_counts[error_hash] += 1
                
                # Update or create error group
                self._update_error_group(error_event)
                
                # Check alert thresholds
                self._check_alert_thresholds(error_event)
                
                logger.error(f"🐛 Error captured: {error_id} - {exc_type}: {exc_message}")
                return error_id
                
        except Exception as e:
            # Don't let error tracking itself cause errors
            logger.error(f"Failed to capture exception: {e}")
            return "capture_failed"
    
    def capture_message(self, message: str, level: str = "INFO",
                       context: Optional[ErrorContext] = None,
                       tags: Optional[Dict[str, str]] = None) -> str:
        """Capture custom message/log entry."""
        try:
            with self._lock:
                error_id = self._generate_error_id()
                
                # Get caller information
                frame = sys._getframe(1)
                file_path = frame.f_code.co_filename
                line_number = frame.f_lineno
                function_name = frame.f_code.co_name
                
                error_hash = self._generate_error_hash("CustomMessage", message, file_path, function_name)
                
                error_event = ErrorEvent(
                    id=error_id,
                    error_hash=error_hash,
                    timestamp=datetime.utcnow(),
                    level=level,
                    message=message,
                    exception_type="CustomMessage",
                    stack_trace=[],
                    file_path=file_path,
                    line_number=line_number,
                    function_name=function_name,
                    context=context or ErrorContext(),
                    environment=self.environment,
                    release_version=self.release_version,
                    tags=tags or {}
                )
                
                self.error_events.append(error_event)
                self.error_counts[error_hash] += 1
                self._update_error_group(error_event)
                
                logger.info(f"📝 Message captured: {error_id} - {level}: {message}")
                return error_id
                
        except Exception as e:
            logger.error(f"Failed to capture message: {e}")
            return "capture_failed"
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _generate_error_hash(self, exc_type: str, message: str, 
                           file_path: str, function_name: str) -> str:
        """Generate hash for error grouping."""
        # Create fingerprint for grouping similar errors
        fingerprint_data = f"{exc_type}:{file_path}:{function_name}"
        
        # Normalize message (remove variable parts)
        normalized_message = self._normalize_error_message(message)
        fingerprint_data += f":{normalized_message}"
        
        return hashlib.md5(fingerprint_data.encode()).hexdigest()[:16]
    
    def _normalize_error_message(self, message: str) -> str:
        """Normalize error message for better grouping."""
        # Remove common variable parts
        import re
        
        # Remove numbers, IDs, timestamps
        normalized = re.sub(r'\b\d+\b', 'N', message)
        normalized = re.sub(r'\b[a-f0-9]{8,}\b', 'ID', normalized)
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}.*?Z?', 'TIMESTAMP', normalized)
        
        return normalized.lower()
    
    def _update_error_group(self, error_event: ErrorEvent):
        """Update or create error group."""
        error_hash = error_event.error_hash
        
        if error_hash in self.error_groups:
            # Update existing group
            group = self.error_groups[error_hash]
            group.last_seen = error_event.timestamp
            group.count += 1
            
            # Escalate level if needed
            if error_event.level == "CRITICAL" and group.level != "CRITICAL":
                group.level = "CRITICAL"
            elif error_event.level == "ERROR" and group.level == "WARNING":
                group.level = "ERROR"
        else:
            # Create new group
            group = ErrorGroup(
                error_hash=error_hash,
                first_seen=error_event.timestamp,
                last_seen=error_event.timestamp,
                count=1,
                level=error_event.level,
                title=f"{error_event.exception_type} in {error_event.function_name}",
                message=error_event.message,
                exception_type=error_event.exception_type,
                file_path=error_event.file_path,
                function_name=error_event.function_name,
                environment=error_event.environment,
                release_version=error_event.release_version
            )
            
            self.error_groups[error_hash] = group
            
            # Alert on new error
            if self.alert_thresholds.get('new_error_alert', False):
                self._send_new_error_alert(group)
    
    def _check_alert_thresholds(self, error_event: ErrorEvent):
        """Check if error event should trigger alerts."""
        # Critical error alert
        if error_event.level == "CRITICAL" and self.alert_thresholds.get('critical_error_threshold', 1) <= 1:
            self._send_critical_error_alert(error_event)
        
        # Error rate alert
        now = datetime.utcnow()
        recent_cutoff = now - timedelta(minutes=1)
        recent_errors = [e for e in self.error_events if e.timestamp > recent_cutoff]
        
        if len(recent_errors) > self.alert_thresholds.get('error_rate_per_minute', 10):
            self._send_error_rate_alert(len(recent_errors))
    
    def _send_new_error_alert(self, error_group: ErrorGroup):
        """Send alert for new error."""
        logger.warning(f"🚨 NEW ERROR ALERT: {error_group.title}")
        # In production: integrate with Slack, email, PagerDuty, etc.
    
    def _send_critical_error_alert(self, error_event: ErrorEvent):
        """Send alert for critical error."""
        logger.error(f"🔥 CRITICAL ERROR ALERT: {error_event.exception_type} - {error_event.message}")
        # In production: immediate notification to on-call
    
    def _send_error_rate_alert(self, error_count: int):
        """Send alert for high error rate."""
        logger.warning(f"📈 HIGH ERROR RATE: {error_count} errors in last minute")
        # In production: send to monitoring team
    
    def get_error_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for specified time period."""
        try:
            with self._lock:
                cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                recent_errors = [e for e in self.error_events if e.timestamp > cutoff_time]
                
                if not recent_errors:
                    return {
                        "total_errors": 0,
                        "error_rate": 0,
                        "by_level": {},
                        "by_type": {},
                        "by_environment": {},
                        "top_errors": []
                    }
                
                # Group by level
                by_level = defaultdict(int)
                for error in recent_errors:
                    by_level[error.level] += 1
                
                # Group by type
                by_type = defaultdict(int)
                for error in recent_errors:
                    by_type[error.exception_type] += 1
                
                # Group by environment
                by_environment = defaultdict(int)
                for error in recent_errors:
                    by_environment[error.environment] += 1
                
                # Top error groups
                group_counts = defaultdict(int)
                for error in recent_errors:
                    group_counts[error.error_hash] += 1
                
                top_error_hashes = sorted(group_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                top_errors = []
                for error_hash, count in top_error_hashes:
                    if error_hash in self.error_groups:
                        group = self.error_groups[error_hash]
                        top_errors.append({
                            "title": group.title,
                            "count": count,
                            "level": group.level,
                            "last_seen": group.last_seen.isoformat()
                        })
                
                return {
                    "period_hours": hours,
                    "total_errors": len(recent_errors),
                    "error_rate": len(recent_errors) / hours,  # Errors per hour
                    "by_level": dict(by_level),
                    "by_type": dict(by_type),
                    "by_environment": dict(by_environment),
                    "top_errors": top_errors,
                    "unique_errors": len(set(e.error_hash for e in recent_errors))
                }
                
        except Exception as e:
            logger.error(f"Failed to get error stats: {e}")
            return {"error": "Failed to calculate stats"}
    
    def get_error_group(self, error_hash: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about error group."""
        try:
            with self._lock:
                if error_hash not in self.error_groups:
                    return None
                
                group = self.error_groups[error_hash]
                events = [e for e in self.error_events if e.error_hash == error_hash]
                
                # Sample recent events
                recent_events = sorted(events, key=lambda e: e.timestamp, reverse=True)[:10]
                
                return {
                    "group": asdict(group),
                    "recent_events": [asdict(e) for e in recent_events],
                    "total_events": len(events),
                    "first_occurrence": group.first_seen.isoformat(),
                    "last_occurrence": group.last_seen.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get error group: {e}")
            return None
    
    def resolve_error_group(self, error_hash: str, assigned_to: str = "system") -> bool:
        """Mark error group as resolved."""
        try:
            with self._lock:
                if error_hash in self.error_groups:
                    group = self.error_groups[error_hash]
                    group.is_resolved = True
                    group.assigned_to = assigned_to
                    
                    logger.info(f"✅ Error group resolved: {group.title}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to resolve error group: {e}")
            return False
    
    def export_errors(self, filename: str = "error_export.json", hours: int = 24):
        """Export errors to JSON file."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_errors = [e for e in self.error_events if e.timestamp > cutoff_time]
            
            export_data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "period_hours": hours,
                "total_errors": len(recent_errors),
                "errors": [asdict(e) for e in recent_errors],
                "error_groups": [asdict(g) for g in self.error_groups.values()],
                "statistics": self.get_error_stats(hours)
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"📁 Errors exported to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to export errors: {e}")

# Decorator for automatic error capture
def capture_errors(level: str = "ERROR", tags: Optional[Dict[str, str]] = None):
    """Decorator to automatically capture exceptions from functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get error tracker instance (assume it's globally available)
                error_tracker = getattr(wrapper, '_error_tracker', None)
                if error_tracker:
                    error_tracker.capture_exception(e, level=level, tags=tags)
                raise  # Re-raise the exception
        
        return wrapper
    return decorator

# Global error tracker instance
error_tracker = None

def init_error_tracking() -> CentralizedErrorTracker:
    """Initialize global error tracking."""
    global error_tracker
    error_tracker = CentralizedErrorTracker()
    
    # Integrate with Flask if available
    try:
        from flask import Flask, request, g
        
        def setup_flask_integration(app: Flask):
            @app.before_request
            def before_request():
                g.request_id = error_tracker._generate_error_id()
            
            @app.errorhandler(Exception)
            def handle_exception(e):
                # Capture exception with request context
                context = ErrorContext(
                    request_id=getattr(g, 'request_id', None),
                    url=request.url if request else None,
                    user_agent=request.headers.get('User-Agent') if request else None,
                    ip_address=request.headers.get('X-Forwarded-For', request.remote_addr) if request else None
                )
                
                error_tracker.capture_exception(e, context=context)
                
                # Re-raise to let Flask handle normally
                raise
        
        # Store setup function for later use
        error_tracker.setup_flask_integration = setup_flask_integration
        
    except ImportError:
        pass
    
    logger.info("🐛 Global error tracking initialized")
    return error_tracker

if __name__ == "__main__":
    # CLI interface for error tracking
    import argparse
    
    parser = argparse.ArgumentParser(description="Centralized Error Tracking")
    parser.add_argument("--stats", type=int, default=24, help="Get stats for N hours")
    parser.add_argument("--export", type=int, default=24, help="Export errors for N hours")
    parser.add_argument("--group", type=str, help="Get error group details")
    parser.add_argument("--resolve", type=str, help="Resolve error group")
    
    args = parser.parse_args()
    
    tracker = init_error_tracking()
    
    if args.stats:
        stats = tracker.get_error_stats(args.stats)
        print(json.dumps(stats, indent=2))
    
    elif args.export:
        tracker.export_errors(hours=args.export)
        print(f"Errors exported for last {args.export} hours")
    
    elif args.group:
        group_info = tracker.get_error_group(args.group)
        if group_info:
            print(json.dumps(group_info, indent=2, default=str))
        else:
            print("Error group not found")
    
    elif args.resolve:
        success = tracker.resolve_error_group(args.resolve)
        print(f"Resolution {'successful' if success else 'failed'}")
    
    else:
        parser.print_help()