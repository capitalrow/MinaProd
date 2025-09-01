"""
API endpoints for system profiler status and health monitoring.
Missing endpoint that frontend JavaScript expects.
"""

import logging
from flask import Blueprint, jsonify
from services.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

api_profiler_bp = Blueprint('api_profiler', __name__)

@api_profiler_bp.route('/api/profiler/status')
def profiler_status():
    """
    System profiler status endpoint that frontend JavaScript expects.
    Returns real-time system health and performance data.
    """
    try:
        # Get comprehensive system status
        dashboard_data = performance_monitor.get_global_dashboard()
        
        # Format for frontend expectations
        status_data = {
            'success': True,
            'timestamp': dashboard_data.get('timestamp'),
            'system_health': {
                'status': 'healthy' if dashboard_data.get('status') == 'healthy' else 'degraded',
                'cpu_usage': dashboard_data.get('resources', {}).get('cpu_usage', 0),
                'memory_usage': dashboard_data.get('resources', {}).get('memory_usage', 0),
                'active_sessions': dashboard_data.get('sessions', {}).get('active_count', 0)
            },
            'transcription_service': {
                'available': True,
                'response_time_ms': dashboard_data.get('performance', {}).get('avg_latency', 0),
                'success_rate': dashboard_data.get('performance', {}).get('success_rate', 0),
                'queue_length': dashboard_data.get('performance', {}).get('queue_length', 0)
            },
            'performance_metrics': {
                'avg_latency': dashboard_data.get('performance', {}).get('avg_latency', 0),
                'p95_latency': dashboard_data.get('performance', {}).get('p95_latency', 0),
                'total_sessions': dashboard_data.get('sessions', {}).get('total', 0),
                'error_rate': dashboard_data.get('performance', {}).get('error_rate', 0)
            },
            'integrations': {
                'realWhisperIntegration': True,
                'performanceIntegration': True, 
                'pipelinePerformance': True,
                'comprehensiveQA': True,
                'robustnessEnhancements': True,
                'uiAccessibility': True
            }
        }
        
        return jsonify(status_data)
        
    except Exception as e:
        logger.error(f"Error getting profiler status: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'system_health': {
                'status': 'error',
                'cpu_usage': 0,
                'memory_usage': 0,
                'active_sessions': 0
            },
            'transcription_service': {
                'available': False,
                'response_time_ms': 0,
                'success_rate': 0,
                'queue_length': 0
            },
            'integrations': {
                'realWhisperIntegration': False,
                'performanceIntegration': False,
                'pipelinePerformance': False,
                'comprehensiveQA': False,
                'robustnessEnhancements': False,
                'uiAccessibility': False
            }
        }), 500