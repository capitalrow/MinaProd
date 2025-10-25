"""
Row-Level Security Context Middleware

This middleware sets the current user ID in Postgres session context before each
request, enabling Row-Level Security (RLS) policies to enforce data isolation.

HOW IT WORKS:
1. Before each request, check if user is authenticated
2. If authenticated, set app.current_user_id in Postgres
3. RLS policies use this value to filter queries automatically
4. Users only see their own data (defense-in-depth security)

USAGE:
    from middleware.rls_context import set_rls_context
    
    def create_app():
        app = Flask(__name__)
        # ... app setup ...
        
        # Enable RLS context middleware
        set_rls_context(app)
        
        # ... rest of app setup ...
"""

import logging
from flask import g
from flask_login import current_user
from sqlalchemy import text

logger = logging.getLogger(__name__)


def set_rls_context(app):
    """
    Enable RLS context setting for all requests.
    
    This middleware executes before every request and sets the
    app.current_user_id Postgres variable based on the authenticated user.
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def set_postgres_rls_context():
        """Set current user ID in Postgres context for RLS policies."""
        
        # Import here to avoid circular dependency
        from models import db
        
        try:
            if current_user.is_authenticated:
                # Set current user ID for RLS policies
                db.session.execute(
                    text("SET LOCAL app.current_user_id = :user_id"),
                    {"user_id": current_user.id}
                )
                
                logger.debug(f"🔒 RLS context set: user_id={current_user.id}")
            else:
                # For unauthenticated requests, unset the variable
                # This allows anonymous sessions to be visible
                db.session.execute(text("SET LOCAL app.current_user_id = NULL"))
                logger.debug("🔓 RLS context cleared (anonymous request)")
                
        except Exception as e:
            # Log warning but don't fail the request
            # RLS is defense-in-depth, application auth is primary
            logger.warning(f"⚠️ Failed to set RLS context: {e}")
    
    logger.info("✅ RLS context middleware enabled")


def bypass_rls_for_admin(user_id: int) -> bool:
    """
    Check if user should bypass RLS policies (admin users).
    
    This function is used internally by Postgres RLS helper functions.
    The application doesn't need to call this directly.
    
    Args:
        user_id: User ID to check
        
    Returns:
        True if user is admin, False otherwise
    """
    from models import db, User
    
    try:
        user = db.session.get(User, user_id)
        return user and user.role == 'admin'
    except Exception:
        return False


def set_rls_context_for_background_task(user_id: int):
    """
    Manually set RLS context for background tasks (Celery, APScheduler).
    
    Background tasks don't have Flask request context, so they must
    manually set the RLS context before database operations.
    
    Usage:
        from middleware.rls_context import set_rls_context_for_background_task
        
        @celery.task
        def process_session(session_id, user_id):
            # Set RLS context before querying
            set_rls_context_for_background_task(user_id)
            
            session = Session.query.get(session_id)
            # ... process session ...
    
    Args:
        user_id: User ID to set as current context
    """
    from models import db
    
    try:
        db.session.execute(
            text("SET LOCAL app.current_user_id = :user_id"),
            {"user_id": user_id}
        )
        logger.debug(f"🔒 RLS context set for background task: user_id={user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to set RLS context for background task: {e}")
        raise


def disable_rls_for_migration():
    """
    Temporarily disable RLS for database migrations or admin operations.
    
    DANGER: Only use this for migrations or admin operations where you need
    to access/modify data across all users.
    
    Usage:
        from middleware.rls_context import disable_rls_for_migration
        
        # In migration or admin script
        disable_rls_for_migration()
        
        # Perform cross-user operations
        all_sessions = Session.query.all()  # See all users' sessions
        
        # RLS will be re-enabled on next request
    """
    from models import db
    
    try:
        # Unset the user context (bypasses RLS)
        db.session.execute(text("SET LOCAL app.current_user_id = NULL"))
        
        # Or use superuser role if available
        # db.session.execute(text("SET ROLE postgres"))
        
        logger.warning("⚠️ RLS temporarily disabled for admin operation")
    except Exception as e:
        logger.error(f"❌ Failed to disable RLS: {e}")
        raise
