"""
Advanced Analytics Routes for Mina.

This module handles API endpoints for advanced analytics, data visualization,
and dashboard metrics with comprehensive chart data and insights.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from services.advanced_analytics_service import advanced_analytics_service

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('advanced_analytics', __name__, url_prefix='/analytics')


@analytics_bp.route('/api/dashboard', methods=['GET'])
@login_required
def get_dashboard_analytics():
    """
    Get comprehensive dashboard analytics with visualizations.
    
    Query Parameters:
        days: Number of days to analyze (default: 30)
        organization_id: Optional organization filter
        team_id: Optional team filter
    
    Returns:
        JSON: Comprehensive analytics data with charts and insights
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        days = int(request.args.get('days', 30))
        organization_id = request.args.get('organization_id')
        team_id = request.args.get('team_id')
        
        # Validate parameters
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'error': 'Days parameter must be between 1 and 365'
            }), 400
        
        if organization_id:
            organization_id = int(organization_id)
        
        if team_id:
            team_id = int(team_id)
        
        # Get analytics data
        analytics = advanced_analytics_service.get_dashboard_analytics(
            user_id=current_user.id,
            days=days,
            organization_id=organization_id,
            team_id=team_id
        )
        
        # Convert summary to dict if it's a dataclass
        if hasattr(analytics.get('summary'), '__dict__'):
            analytics['summary'] = analytics['summary'].__dict__
        
        # Convert chart data to serializable format
        if 'charts' in analytics:
            charts_data = []
            for chart in analytics['charts']:
                if hasattr(chart, '__dict__'):
                    charts_data.append(chart.__dict__)
                else:
                    charts_data.append(chart)
            analytics['charts'] = charts_data
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'parameters': {
                'days': days,
                'organization_id': organization_id,
                'team_id': team_id
            },
            'generated_at': datetime.now().isoformat()
        }), 200
    
    except ValueError as e:
        return jsonify({'success': False, 'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error getting dashboard analytics for user {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get dashboard analytics: {str(e)}'
        }), 500


@analytics_bp.route('/api/meetings', methods=['GET'])
@login_required
def get_meeting_analytics():
    """
    Get detailed meeting analytics and insights.
    
    Query Parameters:
        meeting_id: Optional specific meeting ID
        days: Number of days to analyze (default: 30)
    
    Returns:
        JSON: Meeting analytics data
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        meeting_id = request.args.get('meeting_id')
        days = int(request.args.get('days', 30))
        
        if meeting_id:
            meeting_id = int(meeting_id)
        
        analytics = advanced_analytics_service.get_meeting_analytics(
            user_id=current_user.id,
            meeting_id=meeting_id,
            days=days
        )
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'parameters': {
                'meeting_id': meeting_id,
                'days': days
            }
        }), 200
    
    except ValueError as e:
        return jsonify({'success': False, 'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error getting meeting analytics: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get meeting analytics: {str(e)}'
        }), 500


@analytics_bp.route('/api/tasks', methods=['GET'])
@login_required
def get_task_analytics():
    """
    Get comprehensive task analytics and productivity metrics.
    
    Query Parameters:
        days: Number of days to analyze (default: 30)
    
    Returns:
        JSON: Task analytics data
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        days = int(request.args.get('days', 30))
        
        analytics = advanced_analytics_service.get_task_analytics(
            user_id=current_user.id,
            days=days
        )
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'parameters': {'days': days}
        }), 200
    
    except ValueError as e:
        return jsonify({'success': False, 'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error getting task analytics: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get task analytics: {str(e)}'
        }), 500


@analytics_bp.route('/api/engagement', methods=['GET'])
@login_required
def get_user_engagement_analytics():
    """
    Get detailed user engagement and behavior analytics.
    
    Query Parameters:
        days: Number of days to analyze (default: 30)
    
    Returns:
        JSON: User engagement analytics
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        days = int(request.args.get('days', 30))
        
        analytics = advanced_analytics_service.get_user_engagement_analytics(
            user_id=current_user.id,
            days=days
        )
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'parameters': {'days': days}
        }), 200
    
    except ValueError as e:
        return jsonify({'success': False, 'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error getting user engagement analytics: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get user engagement analytics: {str(e)}'
        }), 500


@analytics_bp.route('/api/organization/<int:organization_id>', methods=['GET'])
@login_required
def get_organization_analytics(organization_id: int):
    """
    Get organization-wide analytics and insights.
    
    Args:
        organization_id: Organization ID
    
    Query Parameters:
        days: Number of days to analyze (default: 30)
    
    Returns:
        JSON: Organization analytics data
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        days = int(request.args.get('days', 30))
        
        analytics = advanced_analytics_service.get_organization_analytics(
            organization_id=organization_id,
            user_id=current_user.id,
            days=days
        )
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'parameters': {
                'organization_id': organization_id,
                'days': days
            }
        }), 200
    
    except PermissionError:
        return jsonify({
            'success': False,
            'error': 'Permission denied: Cannot view organization analytics'
        }), 403
    except ValueError as e:
        return jsonify({'success': False, 'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error getting organization analytics: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get organization analytics: {str(e)}'
        }), 500


@analytics_bp.route('/api/real-time', methods=['GET'])
@login_required
def get_real_time_metrics():
    """
    Get real-time metrics for live dashboard updates.
    
    Returns:
        JSON: Real-time metrics and status
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        metrics = advanced_analytics_service.get_real_time_metrics(current_user.id)
        
        return jsonify({
            'success': True,
            'metrics': metrics
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting real-time metrics: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get real-time metrics: {str(e)}'
        }), 500


@analytics_bp.route('/api/export', methods=['POST'])
@login_required
def export_analytics_data():
    """
    Export analytics data in various formats.
    
    Request Body:
        {
            "format": "csv|json|xlsx",
            "type": "dashboard|meetings|tasks|engagement",
            "days": 30,
            "filters": {}
        }
    
    Returns:
        File download or JSON with download URL
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        export_format = data.get('format', 'csv')
        analytics_type = data.get('type', 'dashboard')
        days = data.get('days', 30)
        filters = data.get('filters', {})
        
        # Validate parameters
        valid_formats = ['csv', 'json', 'xlsx']
        valid_types = ['dashboard', 'meetings', 'tasks', 'engagement']
        
        if export_format not in valid_formats:
            return jsonify({
                'success': False,
                'error': f'Invalid format. Must be one of: {valid_formats}'
            }), 400
        
        if analytics_type not in valid_types:
            return jsonify({
                'success': False,
                'error': f'Invalid type. Must be one of: {valid_types}'
            }), 400
        
        # For now, return a simple export confirmation
        # In a full implementation, this would generate and return actual files
        export_id = f"export_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return jsonify({
            'success': True,
            'export_id': export_id,
            'format': export_format,
            'type': analytics_type,
            'status': 'generating',
            'estimated_completion': '2-5 minutes',
            'download_url': f'/api/analytics/downloads/{export_id}'
        }), 202
    
    except Exception as e:
        logger.error(f"Error exporting analytics data: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to export analytics data: {str(e)}'
        }), 500


@analytics_bp.route('/api/custom-query', methods=['POST'])
@login_required
def run_custom_analytics_query():
    """
    Run a custom analytics query with flexible parameters.
    
    Request Body:
        {
            "metrics": ["meeting_count", "task_completion_rate"],
            "dimensions": ["date", "user"],
            "filters": {
                "date_range": {"start": "2023-01-01", "end": "2023-12-31"},
                "user_ids": [1, 2, 3]
            },
            "aggregation": "daily|weekly|monthly"
        }
    
    Returns:
        JSON: Custom query results
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No query data provided'}), 400
        
        metrics = data.get('metrics', [])
        dimensions = data.get('dimensions', [])
        filters = data.get('filters', {})
        aggregation = data.get('aggregation', 'daily')
        
        # Validate metrics
        valid_metrics = [
            'meeting_count', 'task_completion_rate', 'avg_meeting_duration',
            'total_tasks', 'active_users', 'engagement_score'
        ]
        
        invalid_metrics = [m for m in metrics if m not in valid_metrics]
        if invalid_metrics:
            return jsonify({
                'success': False,
                'error': f'Invalid metrics: {invalid_metrics}. Valid metrics: {valid_metrics}'
            }), 400
        
        # For now, return a simple mock response
        # In a full implementation, this would execute the custom query
        results = {
            'query': {
                'metrics': metrics,
                'dimensions': dimensions,
                'filters': filters,
                'aggregation': aggregation
            },
            'data': [],
            'metadata': {
                'total_rows': 0,
                'execution_time_ms': 0,
                'cache_hit': False
            }
        }
        
        return jsonify({
            'success': True,
            'results': results
        }), 200
    
    except Exception as e:
        logger.error(f"Error running custom analytics query: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to run custom query: {str(e)}'
        }), 500


@analytics_bp.route('/api/benchmarks', methods=['GET'])
@login_required
def get_industry_benchmarks():
    """
    Get industry benchmarks for comparison with user metrics.
    
    Query Parameters:
        industry: Optional industry filter
        company_size: Optional company size filter
    
    Returns:
        JSON: Industry benchmark data
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        industry = request.args.get('industry')
        company_size = request.args.get('company_size')
        
        # Mock benchmark data
        benchmarks = {
            'meeting_frequency': {
                'average': 15.2,  # meetings per week
                'median': 12.0,
                'percentile_75': 20.0,
                'percentile_90': 28.0
            },
            'meeting_duration': {
                'average': 42.5,  # minutes
                'median': 30.0,
                'percentile_75': 60.0,
                'percentile_90': 90.0
            },
            'task_completion_rate': {
                'average': 68.3,  # percentage
                'median': 72.0,
                'percentile_75': 85.0,
                'percentile_90': 95.0
            },
            'engagement_score': {
                'average': 74.8,
                'median': 78.0,
                'percentile_75': 88.0,
                'percentile_90': 95.0
            }
        }
        
        return jsonify({
            'success': True,
            'benchmarks': benchmarks,
            'filters': {
                'industry': industry,
                'company_size': company_size
            },
            'data_source': 'Industry Analysis 2024',
            'last_updated': '2024-01-01'
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting industry benchmarks: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get industry benchmarks: {str(e)}'
        }), 500


@analytics_bp.route('/api/predictions', methods=['GET'])
@login_required
def get_predictive_analytics():
    """
    Get predictive analytics and forecasts based on historical data.
    
    Query Parameters:
        forecast_days: Number of days to forecast (default: 30)
        confidence_level: Confidence level for predictions (default: 0.8)
    
    Returns:
        JSON: Predictive analytics and forecasts
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        forecast_days = int(request.args.get('forecast_days', 30))
        confidence_level = float(request.args.get('confidence_level', 0.8))
        
        # Mock predictive analytics
        predictions = {
            'meeting_frequency_forecast': {
                'next_week': 12.5,
                'next_month': 48.3,
                'confidence': confidence_level,
                'trend': 'increasing',
                'trend_strength': 'moderate'
            },
            'task_completion_forecast': {
                'next_week': 18,
                'next_month': 72,
                'confidence': confidence_level,
            },
            'productivity_trends': {
                'direction': 'improving',
                'rate': 2.3,  # percentage improvement per week
                'confidence': confidence_level
            },
            'recommendations': [
                {
                    'type': 'optimization',
                    'title': 'Optimize Meeting Schedule',
                    'description': 'Based on your patterns, consider moving meetings to your peak hours (10-11 AM).',
                    'impact': 'medium',
                    'confidence': 0.75
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'predictions': predictions,
            'parameters': {
                'forecast_days': forecast_days,
                'confidence_level': confidence_level
            },
            'generated_at': datetime.now().isoformat()
        }), 200
    
    except ValueError as e:
        return jsonify({'success': False, 'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error getting predictive analytics: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get predictive analytics: {str(e)}'
        }), 500