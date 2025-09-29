"""
Comprehensive error handling service for production readiness
"""
import logging
import traceback
import time
import gc
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union
from datetime import datetime

from flask import jsonify, request
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling with memory leak prevention and resource cleanup"""
    
    def __init__(self):
        self.error_counts = {}
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
    
    def handle_database_error(self, error: Exception, db_session, operation: str = "database operation") -> Dict[str, Any]:
        """Handle database errors with automatic rollback and logging"""
        try:
            # Always rollback on database errors
            db_session.rollback()
            logger.error(f"Database error during {operation}: {error}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            return {
                "success": False,
                "error": f"Database error during {operation}",
                "error_type": "database_error",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as rollback_error:
            logger.critical(f"Failed to rollback database transaction: {rollback_error}")
            return {
                "success": False,
                "error": "Critical database error - transaction rollback failed",
                "error_type": "critical_database_error",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def handle_websocket_error(self, error: Exception, session_id: str, cleanup_resources: Optional[Callable] = None) -> Dict[str, Any]:
        """Handle WebSocket errors with resource cleanup"""
        try:
            # Execute cleanup function if provided
            if cleanup_resources:
                cleanup_resources(session_id)
            
            logger.error(f"WebSocket error for session {session_id}: {error}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            return {
                "error": True,
                "message": "WebSocket connection error",
                "error_type": "websocket_error",
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as cleanup_error:
            logger.critical(f"Failed to cleanup WebSocket resources for session {session_id}: {cleanup_error}")
            return {
                "error": True,
                "message": "Critical WebSocket error - resource cleanup failed",
                "error_type": "critical_websocket_error",
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def handle_api_error(self, error: Exception, endpoint: str = "unknown", user_id: Optional[str] = None) -> tuple:
        """Handle API errors with proper HTTP status codes and logging"""
        try:
            # Log error with context
            error_context = {
                "endpoint": endpoint,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "user_agent": request.headers.get('User-Agent', 'unknown') if request else 'unknown',
                "ip_address": request.remote_addr if request else 'unknown'
            }
            
            logger.error(f"API error at {endpoint}: {error}")
            logger.error(f"Error context: {error_context}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Determine appropriate HTTP status code
            if isinstance(error, HTTPException):
                status_code = error.code
                error_message = str(error.description)
            elif "authentication" in str(error).lower() or "unauthorized" in str(error).lower():
                status_code = 401
                error_message = "Authentication required"
            elif "permission" in str(error).lower() or "forbidden" in str(error).lower():
                status_code = 403
                error_message = "Access forbidden"
            elif "not found" in str(error).lower():
                status_code = 404
                error_message = "Resource not found"
            elif "validation" in str(error).lower() or "invalid" in str(error).lower():
                status_code = 400
                error_message = "Invalid request data"
            else:
                status_code = 500
                error_message = "Internal server error"
            
            response_data = {
                "success": False,
                "error": error_message,
                "error_type": "api_error",
                "endpoint": endpoint,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Track error frequency for monitoring
            self._track_error(endpoint, error)
            
            return jsonify(response_data), status_code
            
        except Exception as handler_error:
            logger.critical(f"Error handler itself failed: {handler_error}")
            return jsonify({
                "success": False,
                "error": "Critical system error",
                "error_type": "handler_error",
                "timestamp": datetime.utcnow().isoformat()
            }), 500
    
    def handle_external_service_error(self, error: Exception, service_name: str, operation: str = "") -> Dict[str, Any]:
        """Handle external service errors (OpenAI, Redis, etc.) with circuit breaker logic"""
        try:
            error_key = f"{service_name}_{operation}"
            current_time = time.time()
            
            # Track error frequency for circuit breaker
            if error_key not in self.error_counts:
                self.error_counts[error_key] = {"count": 0, "last_error": 0}
            
            self.error_counts[error_key]["count"] += 1
            self.error_counts[error_key]["last_error"] = current_time
            
            logger.error(f"External service error - {service_name} ({operation}): {error}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Determine if circuit should be opened (too many errors)
            error_count = self.error_counts[error_key]["count"]
            time_window = current_time - self.error_counts[error_key].get("first_error", current_time)
            
            circuit_open = error_count > 5 and time_window < 300  # 5 errors in 5 minutes
            
            return {
                "success": False,
                "error": f"External service error: {service_name}",
                "service": service_name,
                "operation": operation,
                "circuit_open": circuit_open,
                "error_count": error_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as handler_error:
            logger.critical(f"External service error handler failed: {handler_error}")
            return {
                "success": False,
                "error": "Critical external service error handler failure",
                "service": service_name,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _track_error(self, endpoint: str, error: Exception):
        """Track error frequencies for monitoring and alerting"""
        current_time = time.time()
        
        if endpoint not in self.error_counts:
            self.error_counts[endpoint] = {"count": 0, "last_error": 0}
        
        self.error_counts[endpoint]["count"] += 1
        self.error_counts[endpoint]["last_error"] = current_time
        
        # Cleanup old error counts periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_error_counts(current_time)
            self.last_cleanup = current_time
    
    def _cleanup_error_counts(self, current_time: float):
        """Clean up old error count entries to prevent memory leaks"""
        cutoff_time = current_time - 3600  # Keep errors for 1 hour
        
        endpoints_to_remove = []
        for endpoint, error_data in self.error_counts.items():
            if error_data["last_error"] < cutoff_time:
                endpoints_to_remove.append(endpoint)
        
        for endpoint in endpoints_to_remove:
            del self.error_counts[endpoint]
        
        # Force garbage collection
        if endpoints_to_remove:
            gc.collect()
            logger.info(f"Cleaned up {len(endpoints_to_remove)} old error count entries")

# Global error handler instance
error_handler = ErrorHandler()

def with_error_handling(operation_name: str = "", cleanup_func: Optional[Callable] = None):
    """Decorator for comprehensive error handling with resource cleanup"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as error:
                # Execute cleanup if provided
                if cleanup_func:
                    try:
                        cleanup_func(*args, **kwargs)
                    except Exception as cleanup_error:
                        logger.error(f"Cleanup function failed in {operation_name}: {cleanup_error}")
                
                # Log the error with full context
                logger.error(f"Error in {operation_name or func.__name__}: {error}")
                logger.error(f"Stack trace: {traceback.format_exc()}")
                
                # Re-raise the error for proper handling upstream
                raise
        return wrapper
    return decorator

def with_database_error_handling(db_session, operation_name: str = ""):
    """Decorator for database operations with automatic rollback"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as error:
                # Handle database error with rollback
                error_response = error_handler.handle_database_error(error, db_session, operation_name or func.__name__)
                
                # Return error response instead of raising exception
                return error_response
        return wrapper
    return decorator