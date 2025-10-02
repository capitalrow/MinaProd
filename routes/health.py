"""
Health check endpoints for monitoring and load balancers.
"""
from flask import Blueprint, jsonify
from services.uptime_monitoring import uptime_monitor
import logging

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health_check():
    """
    Basic health check endpoint.
    Used by load balancers and uptime monitors.
    """
    try:
        health = uptime_monitor.get_health_status()
        
        status_code = 200 if health['status'] == 'healthy' else 503
        
        return jsonify({
            'status': health['status'],
            'uptime_seconds': health['uptime_seconds']
        }), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': 'Health check failed'
        }), 503


@health_bp.route('/health/detailed')
def detailed_health_check():
    """
    Detailed health check with component status.
    Used for debugging and monitoring dashboards.
    """
    try:
        health = uptime_monitor.get_health_status()
        return jsonify(health), 200
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@health_bp.route('/ping')
def ping():
    """Simple ping endpoint for basic connectivity check."""
    return jsonify({'status': 'ok'}), 200


@health_bp.route('/readiness')
def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration.
    Returns 200 when application is ready to serve traffic.
    """
    try:
        db_health = uptime_monitor.check_database_health()
        
        if db_health.get('connected'):
            return jsonify({'status': 'ready'}), 200
        else:
            return jsonify({'status': 'not_ready', 'reason': 'database_unavailable'}), 503
            
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({'status': 'not_ready', 'error': str(e)}), 503


@health_bp.route('/liveness')
def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration.
    Returns 200 if application process is alive.
    """
    return jsonify({'status': 'alive'}), 200
