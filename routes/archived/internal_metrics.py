"""
🎯 OBSERVER INTERNAL API - Metrics Endpoint for Comprehensive Observability

This module implements internal API endpoints for accessing system performance 
and linguistic quality metrics, as requested in OBSERVER-SYS and OBSERVER-LING.

These endpoints are internal-only and not exposed to end users.
"""

from flask import Blueprint, jsonify
from services.observer import observer_service
import logging

logger = logging.getLogger(__name__)

internal_metrics_bp = Blueprint('internal_metrics', __name__, url_prefix='/internal/metrics')


@internal_metrics_bp.route('/session/<session_id>', methods=['GET'])
def get_session_metrics(session_id: str):
    """
    🎯 OBSERVER-SYS & OBSERVER-LING: Get comprehensive metrics for a session.
    
    Returns structured JSON with:
    - System performance metrics: latency, throughput, resource usage
    - Linguistic quality metrics: WER, confidence, transcript refinement
    - Session summary: chunk counts, errors, duration
    
    This endpoint is for internal monitoring and analysis only.
    
    TODO: OBSERVER-DASHBOARD-PIN - Once Mina app is stable, expose these metrics 
    in Founder Dashboard for visibility.
    """
    try:
        metrics = observer_service.get_session_metrics(session_id)
        
        if 'error' in metrics:
            return jsonify({'error': metrics['error']}), 404
            
        return jsonify({
            'status': 'success',
            'data': metrics,
            'meta': {
                'endpoint': 'internal_metrics.get_session_metrics',
                'version': '1.0.0',
                'description': 'Comprehensive observability metrics for live transcription'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"🎯 OBSERVER API ERROR: Failed to get session metrics: {e}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@internal_metrics_bp.route('/session/<session_id>/compute', methods=['POST'])
def compute_session_metrics(session_id: str):
    """
    🎯 OBSERVER: Force computation of session-level metrics.
    
    Useful for on-demand metric aggregation and analysis.
    Internal endpoint for system administration and debugging.
    """
    try:
        aggregated = observer_service.compute_session_metrics(session_id)
        
        if not aggregated:
            return jsonify({'error': 'No metrics computed or session not found'}), 404
            
        return jsonify({
            'status': 'success',
            'message': f'Session metrics computed for {session_id}',
            'computed_metrics': aggregated
        }), 200
        
    except Exception as e:
        logger.error(f"🎯 OBSERVER API ERROR: Failed to compute session metrics: {e}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@internal_metrics_bp.route('/health', methods=['GET'])
def metrics_health_check():
    """
    🎯 OBSERVER: Health check for the observability system.
    
    Returns status of metrics collection, storage, and API availability.
    """
    try:
        health_status = {
            'observer_service': 'active',
            'metrics_storage': 'available',
            'api_status': 'operational',
            'timestamp': observer_service.storage_path.exists(),
            'features': {
                'system_performance_tracking': True,
                'linguistic_quality_analysis': True,
                'real_time_metrics': True,
                'dashboard_integration_ready': False  # TODO: Set to True when dashboard is ready
            }
        }
        
        return jsonify({
            'status': 'healthy',
            'data': health_status
        }), 200
        
    except Exception as e:
        logger.error(f"🎯 OBSERVER API ERROR: Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


# 🎯 OBSERVER-DASHBOARD-PIN: Future dashboard integration endpoints
# TODO: Once Mina app is stable, add these endpoints for Founder Dashboard:
#
# @internal_metrics_bp.route('/dashboard/summary', methods=['GET'])
# def get_dashboard_summary():
#     """Aggregated metrics summary for founder dashboard."""
#     pass
#
# @internal_metrics_bp.route('/dashboard/trends', methods=['GET']) 
# def get_performance_trends():
#     """Performance trends over time for dashboard charts."""
#     pass
#
# @internal_metrics_bp.route('/dashboard/alerts', methods=['GET'])
# def get_quality_alerts():
#     """Quality degradation alerts for dashboard notifications."""
#     pass