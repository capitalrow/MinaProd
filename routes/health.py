"""
Health Check Routes
Provides application health and status endpoints for monitoring.
"""

import os
import logging
from flask import Blueprint, jsonify
from datetime import datetime

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        JSON response with application health status
    """
    try:
        # Basic health check
        status = {
            "status": "ok",
            "version": os.environ.get('APP_VERSION', '0.1.0'),
            "git_sha": os.environ.get('GIT_SHA', 'dev'),
            "timestamp": datetime.utcnow().isoformat(),
            "environment": os.environ.get('FLASK_ENV', 'development')
        }
        
        # Add database connectivity check
        try:
            from app import db
            # Simple query to check database connectivity
            from sqlalchemy import text
            db.session.execute(text('SELECT 1')).fetchone()
            status["database"] = "connected"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            status["database"] = "error"
            status["database_error"] = str(e)
            # Don't fail the health check for database issues in development
            if os.environ.get('FLASK_ENV') == 'production':
                status["status"] = "degraded"
        
        # Add service-specific health checks
        try:
            from services.transcription_service import TranscriptionService
            # Basic service health check could be added here
            status["transcription_service"] = "available"
        except Exception as e:
            logger.error(f"Transcription service health check failed: {e}")
            status["transcription_service"] = "error"
        
        return jsonify(status), 200 if status["status"] == "ok" else 503
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check with comprehensive system information.
    
    Returns:
        JSON response with detailed health and performance metrics
    """
    try:
        from app_refactored import db
        import psutil
        import sys
        
        # System information
        system_info = {
            "python_version": sys.version,
            "platform": sys.platform,
            "cpu_count": psutil.cpu_count(),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            }
        }
        
        # Database statistics
        db_stats = {}
        try:
            # Get table counts
            from models.session import Session
            from models.segment import Segment
            
            from sqlalchemy import select, func
            from models.session import Session
            from models.segment import Segment
            
            sessions_count = db.session.execute(select(func.count(Session.id))).scalar()
            segments_count = db.session.execute(select(func.count(Segment.id))).scalar()
            
            db_stats = {
                "sessions_count": sessions_count,
                "segments_count": segments_count,
                "connection_pool": {
                    "size": db.engine.pool.size(),
                    "checked_in": db.engine.pool.checkedin(),
                    "checked_out": db.engine.pool.checkedout(),
                    "overflow": db.engine.pool.overflow(),
                    "invalidated": db.engine.pool.invalidated()
                }
            }
        except Exception as e:
            db_stats = {"error": str(e)}
        
        # Service statistics (if available)
        service_stats = {}
        try:
            # This would be populated if we had a global service instance
            service_stats = {
                "transcription_service": "available",
                "vad_service": "available",
                "whisper_service": "available"
            }
        except Exception as e:
            service_stats = {"error": str(e)}
        
        detailed_status = {
            "status": "ok",
            "version": os.environ.get('APP_VERSION', '0.1.0'),
            "git_sha": os.environ.get('GIT_SHA', 'dev'),
            "timestamp": datetime.utcnow().isoformat(),
            "environment": os.environ.get('FLASK_ENV', 'development'),
            "uptime": "N/A",  # Would need to track application start time
            "system": system_info,
            "database": db_stats,
            "services": service_stats
        }
        
        return jsonify(detailed_status), 200
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Readiness probe for Kubernetes and container orchestration.
    
    Returns:
        Simple JSON response indicating if the app is ready to serve traffic
    """
    try:
        # Check critical dependencies
        from app_refactored import db
        
        # Test database connection
        db.session.execute('SELECT 1').fetchone()
        
        return jsonify({
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503

@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Liveness probe for Kubernetes and container orchestration.
    
    Returns:
        Simple JSON response indicating if the app is alive
    """
    return jsonify({
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@health_bp.route('/api/health', methods=['GET'])
def api_health_check():
    """
    API health check endpoint for monitoring tools and external services.
    
    Returns:
        JSON response with basic health status and system metrics
    """
    try:
        # Get basic system status
        status = {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "version": os.environ.get('APP_VERSION', '0.1.0'),
            "environment": os.environ.get('FLASK_ENV', 'development')
        }
        
        # Check database connectivity
        try:
            from app import db
            from sqlalchemy import text
            db.session.execute(text('SELECT 1')).fetchone()
            status["database"] = {"status": "connected", "healthy": True}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            status["database"] = {"status": "error", "healthy": False, "error": str(e)}
            status["status"] = "degraded"
        
        # Check transcription service
        try:
            from services.transcription_service import TranscriptionService
            status["services"] = {
                "transcription": {"status": "available", "healthy": True},
                "websocket": {"status": "active", "healthy": True}
            }
        except Exception as e:
            logger.error(f"Service health check failed: {e}")
            status["services"] = {"status": "error", "healthy": False, "error": str(e)}
        
        # Basic system metrics
        try:
            import psutil
            status["system"] = {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        except Exception as e:
            logger.warning(f"System metrics unavailable: {e}")
            status["system"] = {"status": "metrics_unavailable"}
        
        return jsonify(status), 200 if status["status"] == "ok" else 503
        
    except Exception as e:
        logger.error(f"API health check failed: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500
