"""
Performance API endpoints for real-time monitoring and QA metrics
"""

from flask import Blueprint, jsonify, request
from services.performance_monitor import performance_monitor
from services.qa_pipeline import qa_pipeline
import logging

logger = logging.getLogger(__name__)
api_performance = Blueprint('api_performance', __name__)

@api_performance.route('/api/performance/dashboard')
def performance_dashboard():
    """Real-time performance dashboard data."""
    try:
        dashboard_data = performance_monitor.get_global_dashboard()
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
    except Exception as e:
        logger.error(f"Error getting performance dashboard: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_performance.route('/api/performance/session/<session_id>')
def session_performance(session_id):
    """Get performance metrics for specific session."""
    try:
        session_data = performance_monitor.get_session_report(session_id)
        return jsonify({
            'success': True,
            'data': session_data
        })
    except Exception as e:
        logger.error(f"Error getting session performance: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_performance.route('/api/qa/session/<session_id>')
def session_qa_metrics(session_id):
    """Get QA metrics for active session."""
    try:
        qa_metrics = qa_pipeline.get_realtime_metrics(session_id)
        return jsonify({
            'success': True,
            'data': qa_metrics
        })
    except Exception as e:
        logger.error(f"Error getting QA metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_performance.route('/api/qa/finalize/<session_id>', methods=['POST'])
def finalize_session_qa(session_id):
    """Finalize QA analysis for completed session."""
    try:
        reference_transcript = request.json.get('reference_transcript') if request.json else None
        qa_report = qa_pipeline.finalize_session_qa(session_id, reference_transcript)
        return jsonify({
            'success': True,
            'data': qa_report
        })
    except Exception as e:
        logger.error(f"Error finalizing QA: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_performance.route('/api/health')
def health_check():
    """Comprehensive health check endpoint."""
    try:
        dashboard = performance_monitor.get_global_dashboard()
        alerts = dashboard.get('alerts', [])
        
        # Determine overall health
        critical_alerts = [a for a in alerts if a.get('level') == 'critical']
        warning_alerts = [a for a in alerts if a.get('level') == 'warning']
        
        health_status = 'healthy'
        if critical_alerts:
            health_status = 'critical'
        elif warning_alerts:
            health_status = 'warning'
            
        return jsonify({
            'status': health_status,
            'alerts': alerts,
            'metrics': {
                'avg_latency_ms': dashboard['overview']['avg_latency_ms'],
                'active_sessions': dashboard['overview']['active_sessions'],
                'memory_usage': dashboard['overview']['system_memory_usage'],
                'cpu_usage': dashboard['overview']['system_cpu_usage']
            },
            'timestamp': dashboard['timestamp']
        })
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500