"""
Product team analytics dashboard.
Shows product usage metrics, engagement, retention, conversion funnels.
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from services.product_analytics import product_analytics
from models import db, AnalyticsEvent
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

product_dashboard_bp = Blueprint('product_dashboard', __name__, url_prefix='/product')


@product_dashboard_bp.route('/analytics')
@login_required
def analytics_dashboard():
    """Product analytics dashboard page."""
    return render_template('product/analytics.html')


@product_dashboard_bp.route('/api/metrics')
@login_required
def metrics_api():
    """
    API endpoint for product metrics.
    Returns activation, engagement, retention, and conversion data.
    """
    try:
        days = request.args.get('days', 30, type=int)
        
        # Activation rate
        activation_rate = product_analytics.get_activation_rate(days=7)
        
        # Conversion funnel
        funnel = product_analytics.get_conversion_funnel()
        
        # Retention cohorts
        retention_day_1 = product_analytics.get_retention_cohort(cohort_days=1)
        retention_day_7 = product_analytics.get_retention_cohort(cohort_days=7)
        retention_day_30 = product_analytics.get_retention_cohort(cohort_days=30)
        
        # Daily active users
        dau = get_daily_active_users(days=days)
        
        # Weekly active users
        wau = get_weekly_active_users(days=days)
        
        # Most used features
        top_events = get_top_events(days=days, limit=10)
        
        return jsonify({
            'activation': {
                'rate': round(activation_rate * 100, 1),
                'period_days': 7
            },
            'engagement': {
                'dau': dau,
                'wau': wau,
                'dau_wau_ratio': round((dau / wau * 100), 1) if wau > 0 else 0
            },
            'retention': {
                'day_1': retention_day_1,
                'day_7': retention_day_7,
                'day_30': retention_day_30
            },
            'conversion': funnel,
            'feature_usage': top_events
        }), 200
        
    except Exception as e:
        logger.error(f"Product metrics API failed: {e}")
        return jsonify({'error': str(e)}), 500


@product_dashboard_bp.route('/api/user-engagement/<int:user_id>')
@login_required
def user_engagement(user_id):
    """Get engagement score for specific user."""
    try:
        days = request.args.get('days', 30, type=int)
        score = product_analytics.get_engagement_score(user_id, days=days)
        
        # Get user's recent events
        cutoff = datetime.utcnow() - timedelta(days=days)
        events = db.session.query(
            AnalyticsEvent.event_name,
            func.count(AnalyticsEvent.id).label('count')
        ).filter(
            AnalyticsEvent.user_id == user_id,
            AnalyticsEvent.timestamp >= cutoff
        ).group_by(AnalyticsEvent.event_name).all()
        
        event_breakdown = {e.event_name: e.count for e in events}
        
        return jsonify({
            'user_id': user_id,
            'engagement_score': score,
            'period_days': days,
            'event_breakdown': event_breakdown
        }), 200
        
    except Exception as e:
        logger.error(f"User engagement API failed: {e}")
        return jsonify({'error': str(e)}), 500


@product_dashboard_bp.route('/api/cohort-retention')
@login_required
def cohort_retention_api():
    """
    Cohort retention table.
    Shows retention for cohorts from last 12 weeks.
    """
    try:
        cohorts = []
        
        # Get retention for last 12 weeks
        for week in range(12):
            days_ago = week * 7
            cohort = product_analytics.get_retention_cohort(cohort_days=days_ago)
            
            if cohort.get('cohort_size', 0) > 0:
                cohorts.append(cohort)
        
        return jsonify({'cohorts': cohorts}), 200
        
    except Exception as e:
        logger.error(f"Cohort retention API failed: {e}")
        return jsonify({'error': str(e)}), 500


@product_dashboard_bp.route('/api/feature-adoption')
@login_required
def feature_adoption():
    """
    Feature adoption metrics.
    Shows what percentage of users have used each feature.
    """
    try:
        days = request.args.get('days', 30, type=int)
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Total active users in period
        total_users = db.session.query(
            func.count(func.distinct(AnalyticsEvent.user_id))
        ).filter(AnalyticsEvent.timestamp >= cutoff).scalar() or 1
        
        # Users per feature
        feature_adoption = db.session.query(
            AnalyticsEvent.event_name,
            func.count(func.distinct(AnalyticsEvent.user_id)).label('users')
        ).filter(
            AnalyticsEvent.timestamp >= cutoff
        ).group_by(AnalyticsEvent.event_name).all()
        
        features = [
            {
                'feature': f.event_name,
                'users': f.users,
                'adoption_rate': round(f.users / total_users * 100, 1)
            }
            for f in feature_adoption
        ]
        
        # Sort by adoption rate
        features.sort(key=lambda x: x['adoption_rate'], reverse=True)
        
        return jsonify({
            'total_active_users': total_users,
            'period_days': days,
            'features': features
        }), 200
        
    except Exception as e:
        logger.error(f"Feature adoption API failed: {e}")
        return jsonify({'error': str(e)}), 500


def get_daily_active_users(days: int = 30) -> int:
    """Get count of daily active users."""
    try:
        cutoff = datetime.utcnow() - timedelta(days=1)
        
        dau = db.session.query(
            func.count(func.distinct(AnalyticsEvent.user_id))
        ).filter(AnalyticsEvent.timestamp >= cutoff).scalar() or 0
        
        return dau
        
    except Exception as e:
        logger.error(f"Failed to get DAU: {e}")
        return 0


def get_weekly_active_users(days: int = 30) -> int:
    """Get count of weekly active users."""
    try:
        cutoff = datetime.utcnow() - timedelta(days=7)
        
        wau = db.session.query(
            func.count(func.distinct(AnalyticsEvent.user_id))
        ).filter(AnalyticsEvent.timestamp >= cutoff).scalar() or 0
        
        return wau
        
    except Exception as e:
        logger.error(f"Failed to get WAU: {e}")
        return 0


def get_top_events(days: int = 30, limit: int = 10) -> list:
    """Get most frequent events."""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        top = db.session.query(
            AnalyticsEvent.event_name,
            func.count(AnalyticsEvent.id).label('count')
        ).filter(
            AnalyticsEvent.timestamp >= cutoff
        ).group_by(AnalyticsEvent.event_name).order_by(
            desc('count')
        ).limit(limit).all()
        
        return [
            {'event': e.event_name, 'count': e.count}
            for e in top
        ]
        
    except Exception as e:
        logger.error(f"Failed to get top events: {e}")
        return []
