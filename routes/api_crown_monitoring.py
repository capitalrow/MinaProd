"""
API Endpoints for CROWN+ Event Sequencing Monitoring

Provides API access to:
- Background task status
- Event metrics and health
- Dashboard refresh monitoring
"""

import logging
from flask import Blueprint, jsonify, request
from services.post_transcription_orchestrator import PostTranscriptionOrchestrator
from services.event_monitoring import get_dashboard_metrics, get_pipeline_health

logger = logging.getLogger(__name__)

crown_monitoring_bp = Blueprint('crown_monitoring', __name__)


@crown_monitoring_bp.route('/api/crown/task/<task_id>', methods=['GET'])
def get_task_status(task_id: str):
    """
    Get status of a background post-transcription task.
    
    Returns:
        200: Task status found
        404: Task not found
    """
    try:
        orchestrator = PostTranscriptionOrchestrator()
        status = orchestrator.get_task_status(task_id)
        
        if not status:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error retrieving task status: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@crown_monitoring_bp.route('/api/crown/metrics/dashboard-refresh', methods=['GET'])
def get_dashboard_refresh_metrics():
    """
    Get dashboard refresh event metrics.
    
    Query params:
        hours: Look back window in hours (default: 24)
        
    Returns:
        200: Metrics data
    """
    try:
        hours = int(request.args.get('hours', 24))
        
        if hours < 1 or hours > 168:  # Max 7 days
            return jsonify({'error': 'hours must be between 1 and 168'}), 400
        
        metrics = get_dashboard_metrics(hours=hours)
        
        return jsonify(metrics), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid hours parameter'}), 400
    except Exception as e:
        logger.error(f"Error retrieving dashboard metrics: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@crown_monitoring_bp.route('/api/crown/health', methods=['GET'])
def get_pipeline_health_report():
    """
    Get overall CROWN+ pipeline health report.
    
    Returns:
        200: Health report with metrics for all stages
    """
    try:
        health_report = get_pipeline_health()
        
        return jsonify(health_report), 200
        
    except Exception as e:
        logger.error(f"Error generating health report: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@crown_monitoring_bp.route('/api/crown/metrics/events', methods=['GET'])
def get_event_metrics():
    """
    Get aggregated metrics for all event types.
    
    Query params:
        hours: Look back window in hours (default: 24)
        event_type: Specific event type to query (optional)
        
    Returns:
        200: Event metrics data
    """
    try:
        from services.event_monitoring import event_monitoring_service
        
        hours = int(request.args.get('hours', 24))
        event_type = request.args.get('event_type')
        
        if hours < 1 or hours > 168:
            return jsonify({'error': 'hours must be between 1 and 168'}), 400
        
        metrics = event_monitoring_service.get_event_metrics(event_type=event_type, hours=hours)
        
        # Convert to JSON-serializable format
        result = {}
        for event_type_str, metric in metrics.items():
            result[event_type_str] = {
                'total_count': metric.total_count,
                'success_count': metric.success_count,
                'failure_count': metric.failure_count,
                'success_rate': round(metric.success_rate, 2),
                'failure_rate': round(metric.failure_rate, 2),
                'avg_duration_ms': round(metric.avg_duration_ms, 2),
                'min_duration_ms': round(metric.min_duration_ms, 2) if metric.min_duration_ms != float('inf') else 0,
                'max_duration_ms': round(metric.max_duration_ms, 2),
                'last_execution': metric.last_execution.isoformat() if metric.last_execution else None
            }
        
        return jsonify({
            'time_window_hours': hours,
            'event_type_filter': event_type,
            'metrics': result
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid parameter'}), 400
    except Exception as e:
        logger.error(f"Error retrieving event metrics: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
