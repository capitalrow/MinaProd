"""
📊 Consolidated Analytics API  
Unified endpoint consolidating all analytics functionality to eliminate duplication.
Replaces: api_analytics.py, api_generate_insights.py, api_profiler.py, api_performance.py
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from extensions import get_service, get_db
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Create consolidated blueprint
analytics_api_bp = Blueprint('analytics_api', __name__, url_prefix='/api/analytics')

@analytics_api_bp.route('/overview', methods=['GET'])
@login_required
def get_analytics_overview():
    """Get analytics overview dashboard data"""
    try:
        # Get query parameters
        period = request.args.get('period', '30d')  # 7d, 30d, 90d, 1y
        include_trends = request.args.get('include_trends', 'true').lower() == 'true'
        
        business_metrics = get_service('business_metrics')
        db = get_db()
        
        # Calculate date range
        end_date = datetime.utcnow()
        if period == '7d':
            start_date = end_date - timedelta(days=7)
        elif period == '30d':
            start_date = end_date - timedelta(days=30)
        elif period == '90d':
            start_date = end_date - timedelta(days=90)
        elif period == '1y':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get user's sessions statistics
        from models.session import Session
        
        query = db.session.query(Session).filter(
            Session.user_id == current_user.id,
            Session.created_at >= start_date,
            Session.created_at <= end_date
        )
        
        total_sessions = query.count()
        completed_sessions = query.filter(Session.status == 'completed').count()
        active_sessions = query.filter(Session.status == 'active').count()
        
        # Calculate totals
        total_duration = db.session.query(
            db.func.sum(Session.duration_seconds)
        ).filter(
            Session.user_id == current_user.id,
            Session.created_at >= start_date,
            Session.status == 'completed'
        ).scalar() or 0
        
        total_segments = db.session.query(
            db.func.sum(Session.segments_count)
        ).filter(
            Session.user_id == current_user.id,
            Session.created_at >= start_date
        ).scalar() or 0
        
        avg_confidence = db.session.query(
            db.func.avg(Session.confidence_avg)
        ).filter(
            Session.user_id == current_user.id,
            Session.created_at >= start_date,
            Session.confidence_avg.isnot(None)
        ).scalar() or 0
        
        overview_data = {
            'period': period,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'summary': {
                'total_sessions': total_sessions,
                'completed_sessions': completed_sessions,
                'active_sessions': active_sessions,
                'completion_rate': (completed_sessions / max(total_sessions, 1)) * 100,
                'total_duration_seconds': int(total_duration),
                'total_segments': int(total_segments),
                'avg_confidence': round(float(avg_confidence), 3),
                'avg_session_duration': int(total_duration / max(completed_sessions, 1))
            }
        }
        
        # Add trends if requested
        if include_trends:
            overview_data['trends'] = _calculate_trends(
                user_id=current_user.id,
                start_date=start_date,
                end_date=end_date,
                period=period
            )
        
        return jsonify({
            'status': 'success',
            'analytics': overview_data
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get analytics overview: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve analytics overview'
        }), 500

@analytics_api_bp.route('/performance', methods=['GET'])
@login_required
def get_performance_analytics():
    """Get performance analytics and metrics"""
    try:
        period = request.args.get('period', '7d')
        metric_type = request.args.get('metric', 'all')  # latency, accuracy, throughput, all
        
        # Get health monitor service
        health_monitor = get_service('health_monitor')
        dependency_monitor = get_service('dependency_monitor')
        
        # Get system performance metrics
        system_metrics = health_monitor.get_current_metrics()
        dependency_health = dependency_monitor.get_health_summary()
        
        # Get transcription performance metrics
        performance_data = {
            'period': period,
            'system_health': {
                'memory_usage_mb': system_metrics.get('memory_usage_mb', 0),
                'cpu_usage_percent': system_metrics.get('cpu_usage_percent', 0),
                'disk_usage_percent': system_metrics.get('disk_usage_percent', 0),
                'network_active': system_metrics.get('network_active', False),
                'uptime_seconds': system_metrics.get('uptime_seconds', 0)
            },
            'dependencies': dependency_health,
            'transcription_performance': {
                'avg_processing_time_ms': _get_avg_processing_time(current_user.id, period),
                'avg_confidence_score': _get_avg_confidence(current_user.id, period),
                'error_rate_percent': _get_error_rate(current_user.id, period),
                'throughput_segments_per_hour': _get_throughput(current_user.id, period)
            }
        }
        
        # Filter by metric type if specified
        if metric_type != 'all':
            if metric_type == 'latency':
                performance_data = {
                    'transcription_performance': {
                        'avg_processing_time_ms': performance_data['transcription_performance']['avg_processing_time_ms']
                    }
                }
            elif metric_type == 'accuracy':
                performance_data = {
                    'transcription_performance': {
                        'avg_confidence_score': performance_data['transcription_performance']['avg_confidence_score']
                    }
                }
            elif metric_type == 'throughput':
                performance_data = {
                    'transcription_performance': {
                        'throughput_segments_per_hour': performance_data['transcription_performance']['throughput_segments_per_hour']
                    }
                }
        
        return jsonify({
            'status': 'success',
            'performance': performance_data
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get performance analytics: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve performance analytics'
        }), 500

@analytics_api_bp.route('/insights', methods=['POST'])
@login_required
def generate_insights():
    """Generate AI insights from user's meeting data"""
    try:
        data = request.get_json() or {}
        
        # Get parameters
        session_ids = data.get('session_ids', [])
        insight_type = data.get('type', 'summary')  # summary, trends, recommendations
        period = data.get('period', '30d')
        
        if not session_ids:
            # Get recent sessions if none specified
            db = get_db()
            from models.session import Session
            
            recent_sessions = db.session.query(Session).filter(
                Session.user_id == current_user.id,
                Session.status == 'completed'
            ).order_by(Session.created_at.desc()).limit(10).all()
            
            session_ids = [s.session_id for s in recent_sessions]
        
        if not session_ids:
            return jsonify({
                'status': 'error',
                'message': 'No sessions available for insights generation'
            }), 400
        
        # Generate insights using AI service
        openai_client = get_service('openai_client')
        
        insights_data = _generate_ai_insights(
            session_ids=session_ids,
            insight_type=insight_type,
            openai_client=openai_client
        )
        
        return jsonify({
            'status': 'success',
            'insights': insights_data,
            'generated_at': datetime.utcnow().isoformat(),
            'session_count': len(session_ids)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to generate insights: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate insights'
        }), 500

@analytics_api_bp.route('/usage', methods=['GET'])
@login_required
def get_usage_analytics():
    """Get usage analytics and patterns"""
    try:
        period = request.args.get('period', '30d')
        granularity = request.args.get('granularity', 'daily')  # hourly, daily, weekly
        
        # Calculate date range
        end_date = datetime.utcnow()
        if period == '7d':
            start_date = end_date - timedelta(days=7)
        elif period == '30d':
            start_date = end_date - timedelta(days=30)
        elif period == '90d':
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        db = get_db()
        from models.session import Session
        
        # Get usage patterns
        usage_data = {
            'period': period,
            'granularity': granularity,
            'usage_by_time': _get_usage_by_time(
                user_id=current_user.id,
                start_date=start_date,
                end_date=end_date,
                granularity=granularity
            ),
            'usage_by_day_of_week': _get_usage_by_day_of_week(
                user_id=current_user.id,
                start_date=start_date,
                end_date=end_date
            ),
            'usage_by_hour': _get_usage_by_hour(
                user_id=current_user.id,
                start_date=start_date,
                end_date=end_date
            ),
            'language_distribution': _get_language_distribution(
                user_id=current_user.id,
                start_date=start_date,
                end_date=end_date
            ),
            'session_duration_distribution': _get_duration_distribution(
                user_id=current_user.id,
                start_date=start_date,
                end_date=end_date
            )
        }
        
        return jsonify({
            'status': 'success',
            'usage_analytics': usage_data
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get usage analytics: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve usage analytics'
        }), 500

@analytics_api_bp.route('/export', methods=['POST'])
@login_required
def export_analytics():
    """Export analytics data in various formats"""
    try:
        data = request.get_json() or {}
        
        export_format = data.get('format', 'json')  # json, csv, pdf
        export_type = data.get('type', 'overview')  # overview, performance, usage, insights
        period = data.get('period', '30d')
        
        # Get the requested analytics data
        if export_type == 'overview':
            analytics_data = _get_overview_for_export(current_user.id, period)
        elif export_type == 'performance':
            analytics_data = _get_performance_for_export(current_user.id, period)
        elif export_type == 'usage':
            analytics_data = _get_usage_for_export(current_user.id, period)
        else:
            analytics_data = _get_overview_for_export(current_user.id, period)
        
        # Format the export
        if export_format == 'json':
            return jsonify({
                'status': 'success',
                'export_data': analytics_data,
                'format': export_format,
                'exported_at': datetime.utcnow().isoformat()
            }), 200
        elif export_format == 'csv':
            csv_data = _format_as_csv(analytics_data)
            return csv_data, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=analytics_{export_type}_{period}.csv'
            }
        elif export_format == 'pdf':
            pdf_data = _format_as_pdf(analytics_data, export_type)
            return pdf_data, 200, {
                'Content-Type': 'application/pdf',
                'Content-Disposition': f'attachment; filename=analytics_{export_type}_{period}.pdf'
            }
        else:
            return jsonify({
                'status': 'error',
                'message': 'Unsupported export format'
            }), 400
        
    except Exception as e:
        logger.error(f"Failed to export analytics: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to export analytics'
        }), 500

# Helper functions for analytics calculations
def _calculate_trends(user_id: str, start_date: datetime, end_date: datetime, period: str) -> Dict[str, Any]:
    """Calculate trend data for the analytics overview"""
    # This is a simplified implementation - in production you'd want more sophisticated trending
    db = get_db()
    from models.session import Session
    
    # Calculate period splits for comparison
    period_duration = end_date - start_date
    mid_date = start_date + (period_duration / 2)
    
    # First half metrics
    first_half = db.session.query(Session).filter(
        Session.user_id == user_id,
        Session.created_at >= start_date,
        Session.created_at < mid_date
    ).count()
    
    # Second half metrics  
    second_half = db.session.query(Session).filter(
        Session.user_id == user_id,
        Session.created_at >= mid_date,
        Session.created_at <= end_date
    ).count()
    
    # Calculate trend
    if first_half > 0:
        trend_percent = ((second_half - first_half) / first_half) * 100
    else:
        trend_percent = 100 if second_half > 0 else 0
    
    return {
        'sessions_trend': {
            'direction': 'up' if trend_percent > 0 else 'down' if trend_percent < 0 else 'stable',
            'percentage': abs(round(trend_percent, 1)),
            'first_half_count': first_half,
            'second_half_count': second_half
        }
    }

def _get_avg_processing_time(user_id: str, period: str) -> float:
    """Get average processing time for user's sessions"""
    # Placeholder implementation - would calculate from processing metrics
    return 250.5  # milliseconds

def _get_avg_confidence(user_id: str, period: str) -> float:
    """Get average confidence score for user's sessions"""
    db = get_db()
    from models.session import Session
    
    end_date = datetime.utcnow()
    if period == '7d':
        start_date = end_date - timedelta(days=7)
    elif period == '30d':
        start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=7)
    
    avg_confidence = db.session.query(
        db.func.avg(Session.confidence_avg)
    ).filter(
        Session.user_id == user_id,
        Session.created_at >= start_date,
        Session.confidence_avg.isnot(None)
    ).scalar()
    
    return round(float(avg_confidence or 0), 3)

def _get_error_rate(user_id: str, period: str) -> float:
    """Get error rate percentage for user's sessions"""
    # Placeholder implementation - would calculate from error metrics
    return 1.2  # percent

def _get_throughput(user_id: str, period: str) -> float:
    """Get throughput in segments per hour"""
    # Placeholder implementation - would calculate from segment counts
    return 450.0  # segments per hour

def _generate_ai_insights(session_ids: List[str], insight_type: str, openai_client) -> Dict[str, Any]:
    """Generate AI insights from session data"""
    # Placeholder implementation - would use OpenAI to generate insights
    return {
        'insight_type': insight_type,
        'summary': 'AI-generated insights would appear here based on session analysis',
        'key_findings': [
            'Users tend to have longer meetings in the afternoon',
            'Average confidence scores are highest for English sessions',
            'Most productive meeting times are between 10 AM and 2 PM'
        ],
        'recommendations': [
            'Consider scheduling important meetings during peak confidence hours',
            'Enable speaker diarization for better multi-participant tracking'
        ]
    }

def _get_usage_by_time(user_id: str, start_date: datetime, end_date: datetime, granularity: str) -> List[Dict]:
    """Get usage patterns by time period"""
    # Placeholder implementation
    return [
        {'period': '2024-09-29', 'sessions': 5, 'duration': 1800},
        {'period': '2024-09-28', 'sessions': 3, 'duration': 1200},
        {'period': '2024-09-27', 'sessions': 7, 'duration': 2400}
    ]

def _get_usage_by_day_of_week(user_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
    """Get usage patterns by day of week"""
    # Placeholder implementation
    return [
        {'day': 'Monday', 'sessions': 12, 'avg_duration': 1500},
        {'day': 'Tuesday', 'sessions': 15, 'avg_duration': 1600},
        {'day': 'Wednesday', 'sessions': 18, 'avg_duration': 1400},
        {'day': 'Thursday', 'sessions': 16, 'avg_duration': 1550},
        {'day': 'Friday', 'sessions': 10, 'avg_duration': 1300}
    ]

def _get_usage_by_hour(user_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
    """Get usage patterns by hour of day"""
    # Placeholder implementation
    return [
        {'hour': 9, 'sessions': 5},
        {'hour': 10, 'sessions': 12},
        {'hour': 11, 'sessions': 15},
        {'hour': 14, 'sessions': 18},
        {'hour': 15, 'sessions': 14},
        {'hour': 16, 'sessions': 8}
    ]

def _get_language_distribution(user_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
    """Get language usage distribution"""
    # Placeholder implementation
    return [
        {'language': 'English', 'sessions': 45, 'percentage': 75.0},
        {'language': 'Spanish', 'sessions': 10, 'percentage': 16.7},
        {'language': 'French', 'sessions': 5, 'percentage': 8.3}
    ]

def _get_duration_distribution(user_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
    """Get session duration distribution"""
    # Placeholder implementation
    return [
        {'range': '0-15 min', 'sessions': 20, 'percentage': 33.3},
        {'range': '15-30 min', 'sessions': 25, 'percentage': 41.7},
        {'range': '30-60 min', 'sessions': 12, 'percentage': 20.0},
        {'range': '60+ min', 'sessions': 3, 'percentage': 5.0}
    ]

def _get_overview_for_export(user_id: str, period: str) -> Dict[str, Any]:
    """Get overview data formatted for export"""
    # Placeholder implementation
    return {'overview': 'export data'}

def _get_performance_for_export(user_id: str, period: str) -> Dict[str, Any]:
    """Get performance data formatted for export"""
    # Placeholder implementation
    return {'performance': 'export data'}

def _get_usage_for_export(user_id: str, period: str) -> Dict[str, Any]:
    """Get usage data formatted for export"""
    # Placeholder implementation
    return {'usage': 'export data'}

def _format_as_csv(data: Dict[str, Any]) -> str:
    """Format analytics data as CSV"""
    # Placeholder implementation
    return "data,value\nplaceholder,123\n"

def _format_as_pdf(data: Dict[str, Any], export_type: str) -> bytes:
    """Format analytics data as PDF"""
    # Placeholder implementation
    return b"PDF placeholder content"

# Error handlers for this blueprint
@analytics_api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'status': 'error',
        'message': 'Bad request'
    }), 400

@analytics_api_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'status': 'error',
        'message': 'Authentication required'
    }), 401

@analytics_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500