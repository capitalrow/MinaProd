# utils/db_helpers.py
"""
Database utility functions for preventing memory leaks in SocketIO handlers.
Critical for resolving memory growth issues in production.
"""

import logging
from functools import wraps
from models import db

logger = logging.getLogger(__name__)

def socketio_db_cleanup(func):
    """
    Critical decorator to prevent database session leaks in SocketIO handlers.
    
    SocketIO handlers run outside Flask request context, so database sessions
    are not automatically cleaned up, causing memory leaks. This decorator
    ensures sessions are always removed after event handlers complete.
    
    Usage:
        @socketio.on('event')
        @socketio_db_cleanup
        def handler(data):
            # Database operations
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"SocketIO handler {func.__name__} error: {e}")
            raise
        finally:
            # Critical: Always remove database sessions to prevent memory leaks
            try:
                db.session.remove()
            except Exception as cleanup_error:
                logger.warning(f"Database session cleanup warning in {func.__name__}: {cleanup_error}")
    
    return wrapper