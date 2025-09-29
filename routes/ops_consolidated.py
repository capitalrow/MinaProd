"""
🔧 Consolidated Operations API
Unified endpoint for all operational functionality (health, monitoring, metrics).
Replaces: health.py, metrics_stream.py, monitoring_dashboard.py
"""
from flask import Blueprint, request, jsonify, current_app, Response, render_template
from extensions import get_service
import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, Generator

logger = logging.getLogger(__name__)

# Create consolidated blueprint
ops_bp = Blueprint('ops', __name__, url_prefix='/ops')

@ops_bp.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Get monitoring services
        health_monitor = get_service('health_monitor')
        dependency_monitor = get_service('dependency_monitor')
        
        # Get current system metrics
        system_metrics = health_monitor.get_current_metrics()
        dependency_health = dependency_monitor.get_health_summary()
        
        # Calculate overall health status
        overall_healthy = True
        health_details = {}
        
        # Check system resources
        memory_usage = system_metrics.get('memory_usage_mb', 0)
        memory_limit = 1024  # 1GB threshold
        memory_healthy = memory_usage < memory_limit
        
        cpu_usage = system_metrics.get('cpu_usage_percent', 0)
        cpu_healthy = cpu_usage < 90
        
        disk_usage = system_metrics.get('disk_usage_percent', 0)
        disk_healthy = disk_usage < 95
        
        system_healthy = memory_healthy and cpu_healthy and disk_healthy
        overall_healthy &= system_healthy
        
        health_details['system'] = {
            'status': 'healthy' if system_healthy else 'unhealthy',
            'memory_usage_mb': memory_usage,
            'memory_healthy': memory_healthy,
            'cpu_usage_percent': cpu_usage,
            'cpu_healthy': cpu_healthy,
            'disk_usage_percent': disk_usage,
            'disk_healthy': disk_healthy,
            'uptime_seconds': system_metrics.get('uptime_seconds', 0)
        }
        
        # Check dependencies
        dependencies_healthy = all(
            dep['status'] == 'healthy' 
            for dep in dependency_health.values()
        )
        overall_healthy &= dependencies_healthy
        
        health_details['dependencies'] = dependency_health
        
        # Check application components
        app_components = {
            'database': _check_database_health(),
            'transcription_service': _check_transcription_service_health(),
            'websocket': _check_websocket_health(),
            'export_service': _check_export_service_health()
        }
        
        components_healthy = all(
            comp['status'] == 'healthy' 
            for comp in app_components.values()
        )
        overall_healthy &= components_healthy
        
        health_details['components'] = app_components
        
        # Response
        status_code = 200 if overall_healthy else 503
        status_text = 'healthy' if overall_healthy else 'unhealthy'
        
        return jsonify({
            'status': status_text,
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': system_metrics.get('uptime_seconds', 0),
            'version': getattr(current_app.config, 'VERSION', '1.0.0'),
            'environment': getattr(current_app.config, 'ENV', 'development'),
            'overall_healthy': overall_healthy,
            'details': health_details
        }), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': 'Health check service unavailable',
            'overall_healthy': False
        }), 503

@ops_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get comprehensive system metrics"""
    try:
        # Get all monitoring services
        health_monitor = get_service('health_monitor')
        business_metrics = get_service('business_metrics')
        websocket_monitor = get_service('websocket_monitor')
        dependency_monitor = get_service('dependency_monitor')
        
        # Collect all metrics
        metrics_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'system': health_monitor.get_current_metrics(),
            'business': business_metrics.get_current_metrics(),
            'websocket': websocket_monitor.get_current_metrics(),
            'dependencies': dependency_monitor.get_health_summary()
        }
        
        # Add computed metrics
        metrics_data['computed'] = {
            'health_score': _calculate_health_score(metrics_data),
            'performance_score': _calculate_performance_score(metrics_data),
            'availability_score': _calculate_availability_score(metrics_data)
        }
        
        return jsonify({
            'status': 'success',
            'metrics': metrics_data
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve metrics'
        }), 500

@ops_bp.route('/metrics/stream', methods=['GET'])
def stream_metrics():
    """Stream real-time metrics using Server-Sent Events"""
    try:
        def generate_metrics():
            while True:
                try:
                    # Get current metrics
                    health_monitor = get_service('health_monitor')
                    business_metrics = get_service('business_metrics')
                    websocket_monitor = get_service('websocket_monitor')
                    
                    metrics_data = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'system': health_monitor.get_current_metrics(),
                        'business': business_metrics.get_current_metrics(),
                        'websocket': websocket_monitor.get_current_metrics()
                    }
                    
                    # Format as Server-Sent Event
                    yield f"data: {json.dumps(metrics_data)}\n\n"
                    
                    # Wait 5 seconds before next update
                    time.sleep(5)
                    
                except Exception as e:
                    logger.error(f"Error in metrics stream: {e}")
                    yield f"data: {{\"error\": \"Metrics stream error\"}}\n\n"
                    time.sleep(5)
        
        return Response(
            generate_metrics(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to start metrics stream: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to start metrics stream'
        }), 500

@ops_bp.route('/monitoring/dashboard', methods=['GET'])
def monitoring_dashboard():
    """Production monitoring dashboard"""
    try:
        # Check if this is an API request or web request
        if request.headers.get('Accept', '').startswith('application/json'):
            # Return JSON data for API requests
            return get_dashboard_data()
        else:
            # Render HTML dashboard for web requests
            return render_template('monitoring/dashboard.html')
            
    except Exception as e:
        logger.error(f"Failed to load monitoring dashboard: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to load monitoring dashboard'
        }), 500

@ops_bp.route('/monitoring/dashboard/data', methods=['GET'])
def get_dashboard_data():
    """Get dashboard data in JSON format"""
    try:
        # Get all monitoring services
        health_monitor = get_service('health_monitor')
        business_metrics = get_service('business_metrics')
        websocket_monitor = get_service('websocket_monitor')
        dependency_monitor = get_service('dependency_monitor')
        alerting_system = get_service('alerting')
        
        # Collect dashboard data
        dashboard_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'overview': {
                'status': _get_overall_status(),
                'uptime_seconds': health_monitor.get_current_metrics().get('uptime_seconds', 0),
                'active_sessions': business_metrics.get_current_metrics().get('active_sessions', 0),
                'total_users': business_metrics.get_current_metrics().get('total_users', 0)
            },
            'system_health': health_monitor.get_current_metrics(),
            'business_metrics': business_metrics.get_current_metrics(),
            'websocket_health': websocket_monitor.get_current_metrics(),
            'dependencies': dependency_monitor.get_health_summary(),
            'recent_alerts': alerting_system.get_recent_alerts(limit=10),
            'performance_summary': {
                'avg_response_time_ms': _get_avg_response_time(),
                'request_rate_per_minute': _get_request_rate(),
                'error_rate_percent': _get_error_rate_percent(),
                'memory_growth_trend': _get_memory_growth_trend()
            }
        }
        
        return jsonify({
            'status': 'success',
            'dashboard': dashboard_data
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve dashboard data'
        }), 500

@ops_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get system alerts and notifications"""
    try:
        alerting_system = get_service('alerting')
        
        # Get query parameters
        limit = min(int(request.args.get('limit', 50)), 200)  # Max 200
        severity = request.args.get('severity', None)  # critical, warning, info
        status = request.args.get('status', None)  # active, resolved, acknowledged
        
        # Get alerts
        alerts = alerting_system.get_alerts(
            limit=limit,
            severity=severity,
            status=status
        )
        
        return jsonify({
            'status': 'success',
            'alerts': alerts,
            'count': len(alerts)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve alerts'
        }), 500

@ops_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    try:
        alerting_system = get_service('alerting')
        
        result = alerting_system.acknowledge_alert(alert_id)
        
        if result:
            return jsonify({
                'status': 'success',
                'message': 'Alert acknowledged',
                'alert_id': alert_id
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Alert not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to acknowledge alert'
        }), 500

@ops_bp.route('/status', methods=['GET'])
def get_status():
    """Get simple status endpoint (lightweight health check)"""
    try:
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'mina-transcription-platform'
        }), 200
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'mina-transcription-platform'
        }), 503

# Helper functions for health checks and metrics
def _check_database_health() -> Dict[str, Any]:
    """Check database health"""
    try:
        from extensions import get_db
        db = get_db()
        
        # Simple query to test database connectivity
        result = db.session.execute(db.text("SELECT 1")).scalar()
        
        return {
            'status': 'healthy' if result == 1 else 'unhealthy',
            'response_time_ms': 50,  # Placeholder
            'connection_pool_size': 10  # Placeholder
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }

def _check_transcription_service_health() -> Dict[str, Any]:
    """Check transcription service health"""
    try:
        transcription_service = get_service('transcription')
        health_result = transcription_service.health_check()
        
        return {
            'status': 'healthy' if health_result else 'unhealthy',
            'active_sessions': health_result.get('active_sessions', 0) if health_result else 0
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }

def _check_websocket_health() -> Dict[str, Any]:
    """Check WebSocket service health"""
    try:
        websocket_monitor = get_service('websocket_monitor')
        metrics = websocket_monitor.get_current_metrics()
        
        return {
            'status': 'healthy',
            'active_connections': metrics.get('active_connections', 0),
            'message_rate': metrics.get('messages_per_second', 0)
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }

def _check_export_service_health() -> Dict[str, Any]:
    """Check export service health"""
    try:
        export_service = get_service('export')
        
        return {
            'status': 'healthy',
            'formats_available': ['pdf', 'docx', 'txt', 'srt']
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }

def _calculate_health_score(metrics_data: Dict[str, Any]) -> float:
    """Calculate overall health score (0-100)"""
    # Simplified implementation
    system_health = 100 - metrics_data['system'].get('memory_usage_mb', 0) / 10
    dependency_health = 100  # Would calculate based on dependency status
    
    return min(100, max(0, (system_health + dependency_health) / 2))

def _calculate_performance_score(metrics_data: Dict[str, Any]) -> float:
    """Calculate overall performance score (0-100)"""
    # Simplified implementation
    return 95.5  # Placeholder

def _calculate_availability_score(metrics_data: Dict[str, Any]) -> float:
    """Calculate availability score (0-100)"""
    # Simplified implementation
    return 99.9  # Placeholder

def _get_overall_status() -> str:
    """Get overall system status"""
    try:
        health_monitor = get_service('health_monitor')
        metrics = health_monitor.get_current_metrics()
        
        memory_usage = metrics.get('memory_usage_mb', 0)
        if memory_usage > 1024:  # 1GB threshold
            return 'warning'
        
        return 'healthy'
    except Exception:
        return 'unhealthy'

def _get_avg_response_time() -> float:
    """Get average response time"""
    return 185.5  # Placeholder

def _get_request_rate() -> float:
    """Get request rate per minute"""
    return 25.3  # Placeholder

def _get_error_rate_percent() -> float:
    """Get error rate percentage"""
    return 0.2  # Placeholder

def _get_memory_growth_trend() -> str:
    """Get memory growth trend"""
    return 'stable'  # Placeholder

# Error handlers for this blueprint
@ops_bp.errorhandler(503)
def service_unavailable(error):
    return jsonify({
        'status': 'unhealthy',
        'message': 'Service temporarily unavailable'
    }), 503

@ops_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500