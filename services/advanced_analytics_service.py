"""
Advanced Analytics Service for Mina.

This module provides comprehensive analytics and visualization data
for dashboards, including meeting insights, productivity metrics,
user engagement analytics, and trend analysis.
"""

import logging
import json
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import calendar

logger = logging.getLogger(__name__)


@dataclass
class MetricDataPoint:
    """Data point for time-series metrics."""
    date: str
    value: float
    label: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChartData:
    """Chart data structure for frontend visualization."""
    chart_type: str
    title: str
    data: List[Dict[str, Any]]
    options: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class AnalyticsSummary:
    """Summary statistics for analytics dashboard."""
    total_meetings: int
    total_duration_hours: float
    total_tasks_created: int
    avg_meeting_duration_minutes: float
    task_completion_rate: float
    active_users: int
    growth_rate: float
    engagement_score: float


class AdvancedAnalyticsService:
    """Service for advanced analytics and visualization data generation."""
    
    def __init__(self):
        self.cache_duration = timedelta(minutes=15)
        self.analytics_cache: Dict[str, Any] = {}
        
    def get_dashboard_analytics(self, user_id: int, days: int = 30, 
                              organization_id: Optional[int] = None,
                              team_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get comprehensive dashboard analytics for a user or organization.
        
        Args:
            user_id: User ID requesting analytics
            days: Number of days to analyze
            organization_id: Optional organization filter
            team_id: Optional team filter
            
        Returns:
            Comprehensive analytics data for dashboard visualization
        """
        try:
            # Check cache
            cache_key = f"dashboard_{user_id}_{days}_{organization_id}_{team_id}"
            if self._get_from_cache(cache_key):
                return self._get_from_cache(cache_key)
            
            # Get data from database
            data = self._get_analytics_data(user_id, days, organization_id, team_id)
            
            # Generate analytics
            analytics = {
                'summary': self._generate_summary_stats(data),
                'charts': self._generate_dashboard_charts(data, days),
                'insights': self._generate_insights(data),
                'trends': self._generate_trend_analysis(data, days),
                'user_metrics': self._generate_user_metrics(data, user_id),
                'productivity_scores': self._generate_productivity_scores(data),
                'engagement_metrics': self._generate_engagement_metrics(data),
                'time_analysis': self._generate_time_analysis(data),
                'content_analytics': self._generate_content_analytics(data),
                'collaboration_metrics': self._generate_collaboration_metrics(data)
            }
            
            # Cache results
            self._set_cache(cache_key, analytics)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting dashboard analytics: {e}")
            return self._get_default_analytics()
    
    def get_meeting_analytics(self, user_id: int, meeting_id: Optional[int] = None,
                            days: int = 30) -> Dict[str, Any]:
        """Get detailed meeting analytics and insights."""
        try:
            if meeting_id:
                # Single meeting analytics
                return self._get_single_meeting_analytics(meeting_id, user_id)
            else:
                # All meetings analytics
                return self._get_meetings_overview_analytics(user_id, days)
                
        except Exception as e:
            logger.error(f"Error getting meeting analytics: {e}")
            return {}
    
    def get_task_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive task analytics and productivity metrics."""
        try:
            data = self._get_task_data(user_id, days)
            
            return {
                'summary': self._generate_task_summary(data),
                'completion_trends': self._generate_task_completion_trends(data, days),
                'priority_distribution': self._generate_priority_distribution(data),
                'due_date_analysis': self._generate_due_date_analysis(data),
                'productivity_metrics': self._generate_task_productivity_metrics(data),
                'category_breakdown': self._generate_task_category_breakdown(data),
                'time_to_completion': self._generate_time_to_completion_analysis(data),
                'collaboration_tasks': self._generate_collaborative_task_metrics(data)
            }
            
        except Exception as e:
            logger.error(f"Error getting task analytics: {e}")
            return {}
    
    def get_user_engagement_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get detailed user engagement and behavior analytics."""
        try:
            data = self._get_user_engagement_data(user_id, days)
            
            return {
                'activity_timeline': self._generate_activity_timeline(data, days),
                'feature_usage': self._generate_feature_usage_analytics(data),
                'session_patterns': self._generate_session_pattern_analysis(data),
                'engagement_score': self._calculate_engagement_score(data),
                'productivity_patterns': self._generate_productivity_pattern_analysis(data),
                'collaboration_frequency': self._generate_collaboration_frequency(data),
                'peak_hours': self._generate_peak_hours_analysis(data),
                'device_usage': self._generate_device_usage_analytics(data)
            }
            
        except Exception as e:
            logger.error(f"Error getting user engagement analytics: {e}")
            return {}
    
    def get_organization_analytics(self, organization_id: int, user_id: int,
                                 days: int = 30) -> Dict[str, Any]:
        """Get organization-wide analytics and insights."""
        try:
            # Check permissions
            from services.rbac_service import rbac_service
            if not rbac_service.check_permission(user_id, 'view_analytics', organization_id=organization_id):
                raise PermissionError("User does not have permission to view organization analytics")
            
            data = self._get_organization_data(organization_id, days)
            
            return {
                'overview': self._generate_organization_overview(data),
                'team_performance': self._generate_team_performance_metrics(data),
                'meeting_analytics': self._generate_organization_meeting_analytics(data),
                'user_activity': self._generate_organization_user_activity(data),
                'productivity_trends': self._generate_organization_productivity_trends(data, days),
                'collaboration_networks': self._generate_collaboration_network_analysis(data),
                'content_insights': self._generate_organization_content_insights(data),
                'growth_metrics': self._generate_organization_growth_metrics(data, days)
            }
            
        except Exception as e:
            logger.error(f"Error getting organization analytics: {e}")
            return {}
    
    def get_real_time_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get real-time metrics for live dashboard updates."""
        try:
            now = datetime.now()
            
            return {
                'active_sessions': self._get_active_sessions_count(user_id),
                'current_transcriptions': self._get_current_transcriptions_count(user_id),
                'pending_tasks': self._get_pending_tasks_count(user_id),
                'recent_activity': self._get_recent_activity(user_id, hours=1),
                'system_status': self._get_system_status(),
                'live_insights': self._get_live_insights(user_id),
                'timestamp': now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return {'timestamp': datetime.now().isoformat()}
    
    def _get_analytics_data(self, user_id: int, days: int, 
                          organization_id: Optional[int] = None,
                          team_id: Optional[int] = None) -> Dict[str, Any]:
        """Get raw analytics data from database."""
        try:
            from models.session import Session
            from models.task import Task
            from models.summary import Summary
            from models.segment import Segment
            from app import db
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Base query filters
            session_query = db.session.query(Session).filter(
                Session.created_at >= start_date,
                Session.created_at <= end_date
            )
            
            task_query = db.session.query(Task).filter(
                Task.created_at >= start_date,
                Task.created_at <= end_date
            )
            
            # Apply user/organization/team filters
            if organization_id:
                # TODO: Filter by organization membership
                pass
            elif team_id:
                # TODO: Filter by team membership
                pass
            else:
                session_query = session_query.filter(Session.user_id == user_id)
                task_query = task_query.filter(Task.user_id == user_id)
            
            sessions = session_query.all()
            tasks = task_query.all()
            
            # Get related data
            session_ids = [s.id for s in sessions]
            summaries = db.session.query(Summary).filter(
                Summary.session_id.in_(session_ids)
            ).all() if session_ids else []
            
            segments = db.session.query(Segment).filter(
                Segment.session_id.in_(session_ids)
            ).all() if session_ids else []
            
            return {
                'sessions': sessions,
                'tasks': tasks,
                'summaries': summaries,
                'segments': segments,
                'start_date': start_date,
                'end_date': end_date,
                'user_id': user_id,
                'organization_id': organization_id,
                'team_id': team_id
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics data: {e}")
            return {}
    
    def _generate_summary_stats(self, data: Dict[str, Any]) -> AnalyticsSummary:
        """Generate summary statistics."""
        sessions = data.get('sessions', [])
        tasks = data.get('tasks', [])
        
        total_meetings = len(sessions)
        total_duration = sum(s.duration_seconds or 0 for s in sessions) / 3600  # hours
        total_tasks = len(tasks)
        avg_duration = (sum(s.duration_seconds or 0 for s in sessions) / 60 / len(sessions)) if sessions else 0
        
        completed_tasks = len([t for t in tasks if t.status == 'completed'])
        completion_rate = (completed_tasks / len(tasks) * 100) if tasks else 0
        
        active_users = len(set(s.user_id for s in sessions))
        
        # Calculate growth rate (simplified)
        days = (data.get('end_date', datetime.now()) - data.get('start_date', datetime.now())).days
        daily_avg = total_meetings / days if days > 0 else 0
        growth_rate = daily_avg * 7  # Weekly growth approximation
        
        # Calculate engagement score
        engagement_score = min(100, (total_meetings * 10 + total_tasks * 5 + completion_rate) / 3)
        
        return AnalyticsSummary(
            total_meetings=total_meetings,
            total_duration_hours=total_duration,
            total_tasks_created=total_tasks,
            avg_meeting_duration_minutes=avg_duration,
            task_completion_rate=completion_rate,
            active_users=active_users,
            growth_rate=growth_rate,
            engagement_score=engagement_score
        )
    
    def _generate_dashboard_charts(self, data: Dict[str, Any], days: int) -> List[ChartData]:
        """Generate chart data for dashboard visualization."""
        charts = []
        sessions = data.get('sessions', [])
        tasks = data.get('tasks', [])
        
        # 1. Meeting frequency over time
        meeting_timeline = self._generate_meeting_timeline_chart(sessions, days)
        charts.append(meeting_timeline)
        
        # 2. Task creation and completion trends
        task_trends = self._generate_task_trends_chart(tasks, days)
        charts.append(task_trends)
        
        # 3. Meeting duration distribution
        duration_distribution = self._generate_duration_distribution_chart(sessions)
        charts.append(duration_distribution)
        
        # 4. Task status breakdown
        task_status = self._generate_task_status_chart(tasks)
        charts.append(task_status)
        
        # 5. Daily productivity heatmap
        productivity_heatmap = self._generate_productivity_heatmap(sessions, tasks, days)
        charts.append(productivity_heatmap)
        
        # 6. Weekly pattern analysis
        weekly_patterns = self._generate_weekly_patterns_chart(sessions, days)
        charts.append(weekly_patterns)
        
        return charts
    
    def _generate_meeting_timeline_chart(self, sessions: List, days: int) -> ChartData:
        """Generate meeting frequency timeline chart."""
        # Group meetings by date
        daily_counts = defaultdict(int)
        end_date = datetime.now()
        
        for session in sessions:
            date_key = session.created_at.strftime('%Y-%m-%d')
            daily_counts[date_key] += 1
        
        # Fill in missing dates
        data_points = []
        for i in range(days):
            date = end_date - timedelta(days=i)
            date_key = date.strftime('%Y-%m-%d')
            count = daily_counts.get(date_key, 0)
            
            data_points.append({
                'date': date_key,
                'value': count,
                'label': date.strftime('%b %d')
            })
        
        data_points.reverse()  # Chronological order
        
        return ChartData(
            chart_type='line',
            title='Meeting Frequency Over Time',
            data=data_points,
            options={
                'responsive': True,
                'plugins': {
                    'legend': {'display': True},
                    'tooltip': {'enabled': True}
                },
                'scales': {
                    'x': {'type': 'time', 'time': {'unit': 'day'}},
                    'y': {'beginAtZero': True}
                }
            },
            metadata={'total_days': days, 'total_meetings': len(sessions)}
        )
    
    def _generate_task_trends_chart(self, tasks: List, days: int) -> ChartData:
        """Generate task creation and completion trends chart."""
        daily_created = defaultdict(int)
        daily_completed = defaultdict(int)
        end_date = datetime.now()
        
        for task in tasks:
            created_date = task.created_at.strftime('%Y-%m-%d')
            daily_created[created_date] += 1
            
            if task.status == 'completed' and task.updated_at:
                completed_date = task.updated_at.strftime('%Y-%m-%d')
                daily_completed[completed_date] += 1
        
        # Generate data points
        data_points = []
        for i in range(days):
            date = end_date - timedelta(days=i)
            date_key = date.strftime('%Y-%m-%d')
            
            data_points.append({
                'date': date_key,
                'created': daily_created.get(date_key, 0),
                'completed': daily_completed.get(date_key, 0),
                'label': date.strftime('%b %d')
            })
        
        data_points.reverse()
        
        return ChartData(
            chart_type='bar',
            title='Task Creation and Completion Trends',
            data=data_points,
            options={
                'responsive': True,
                'plugins': {'legend': {'display': True}},
                'scales': {'y': {'beginAtZero': True}}
            },
            metadata={'total_tasks': len(tasks)}
        )
    
    def _generate_duration_distribution_chart(self, sessions: List) -> ChartData:
        """Generate meeting duration distribution chart."""
        duration_buckets = {
            '0-15 min': 0,
            '15-30 min': 0,
            '30-60 min': 0,
            '1-2 hours': 0,
            '2+ hours': 0
        }
        
        for session in sessions:
            if not session.duration_seconds:
                continue
            
            minutes = session.duration_seconds / 60
            
            if minutes <= 15:
                duration_buckets['0-15 min'] += 1
            elif minutes <= 30:
                duration_buckets['15-30 min'] += 1
            elif minutes <= 60:
                duration_buckets['30-60 min'] += 1
            elif minutes <= 120:
                duration_buckets['1-2 hours'] += 1
            else:
                duration_buckets['2+ hours'] += 1
        
        data_points = [
            {'label': label, 'value': count, 'percentage': (count / len(sessions) * 100) if sessions else 0}
            for label, count in duration_buckets.items()
        ]
        
        return ChartData(
            chart_type='doughnut',
            title='Meeting Duration Distribution',
            data=data_points,
            options={
                'responsive': True,
                'plugins': {
                    'legend': {'position': 'right'},
                    'tooltip': {'enabled': True}
                }
            },
            metadata={'total_meetings': len(sessions)}
        )
    
    def _generate_task_status_chart(self, tasks: List) -> ChartData:
        """Generate task status breakdown chart."""
        status_counts = Counter(task.status for task in tasks)
        
        data_points = [
            {
                'label': status.replace('_', ' ').title(),
                'value': count,
                'percentage': (count / len(tasks) * 100) if tasks else 0
            }
            for status, count in status_counts.items()
        ]
        
        return ChartData(
            chart_type='pie',
            title='Task Status Breakdown',
            data=data_points,
            options={
                'responsive': True,
                'plugins': {'legend': {'position': 'bottom'}}
            },
            metadata={'total_tasks': len(tasks)}
        )
    
    def _generate_productivity_heatmap(self, sessions: List, tasks: List, days: int) -> ChartData:
        """Generate daily productivity heatmap."""
        # Calculate productivity score for each day
        end_date = datetime.now()
        daily_scores = {}
        
        for i in range(days):
            date = end_date - timedelta(days=i)
            date_key = date.strftime('%Y-%m-%d')
            
            # Count activities for the day
            day_sessions = [s for s in sessions if s.created_at.date() == date.date()]
            day_tasks = [t for t in tasks if t.created_at.date() == date.date()]
            
            # Calculate score (meetings * 10 + tasks * 5)
            score = len(day_sessions) * 10 + len(day_tasks) * 5
            
            daily_scores[date_key] = {
                'date': date_key,
                'score': score,
                'meetings': len(day_sessions),
                'tasks': len(day_tasks),
                'weekday': date.strftime('%A'),
                'day_of_week': date.weekday()
            }
        
        # Convert to heatmap format
        data_points = list(daily_scores.values())
        data_points.reverse()
        
        return ChartData(
            chart_type='heatmap',
            title='Daily Productivity Heatmap',
            data=data_points,
            options={
                'responsive': True,
                'plugins': {'tooltip': {'enabled': True}},
                'colorScale': {'min': 0, 'max': max(d['score'] for d in data_points) if data_points else 100}
            },
            metadata={'max_score': max(d['score'] for d in data_points) if data_points else 0}
        )
    
    def _generate_weekly_patterns_chart(self, sessions: List, days: int) -> ChartData:
        """Generate weekly activity patterns chart."""
        weekday_counts = defaultdict(int)
        
        for session in sessions:
            weekday = session.created_at.strftime('%A')
            weekday_counts[weekday] += 1
        
        # Order by weekday
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        data_points = [
            {
                'label': day,
                'value': weekday_counts.get(day, 0),
                'percentage': (weekday_counts.get(day, 0) / len(sessions) * 100) if sessions else 0
            }
            for day in weekdays
        ]
        
        return ChartData(
            chart_type='radar',
            title='Weekly Activity Patterns',
            data=data_points,
            options={
                'responsive': True,
                'plugins': {'legend': {'display': False}},
                'scales': {'r': {'beginAtZero': True}}
            },
            metadata={'total_meetings': len(sessions)}
        )
    
    def _generate_insights(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate AI-powered insights from analytics data."""
        insights = []
        sessions = data.get('sessions', [])
        tasks = data.get('tasks', [])
        
        # Insight 1: Meeting frequency pattern
        if sessions:
            avg_daily = len(sessions) / 30
            if avg_daily > 2:
                insights.append({
                    'type': 'productivity',
                    'title': 'High Meeting Frequency',
                    'description': f'You average {avg_daily:.1f} meetings per day, which is above optimal.',
                    'recommendation': 'Consider consolidating or shortening some meetings to increase focus time.',
                    'impact': 'medium',
                    'confidence': 0.8
                })
        
        # Insight 2: Task completion rate
        if tasks:
            completed = len([t for t in tasks if t.status == 'completed'])
            completion_rate = completed / len(tasks)
            
            if completion_rate < 0.6:
                insights.append({
                    'type': 'task_management',
                    'title': 'Low Task Completion Rate',
                    'description': f'Only {completion_rate*100:.0f}% of your tasks are completed.',
                    'recommendation': 'Break down large tasks into smaller, manageable pieces.',
                    'impact': 'high',
                    'confidence': 0.9
                })
        
        # Insight 3: Peak productivity hours
        if sessions:
            hour_counts = defaultdict(int)
            for session in sessions:
                hour_counts[session.created_at.hour] += 1
            
            peak_hour = max(hour_counts, key=hour_counts.get)
            insights.append({
                'type': 'time_management',
                'title': 'Peak Productivity Hours',
                'description': f'Your most active hour is {peak_hour}:00.',
                'recommendation': f'Schedule important meetings around {peak_hour}:00 for maximum engagement.',
                'impact': 'medium',
                'confidence': 0.7
            })
        
        return insights
    
    def _generate_trend_analysis(self, data: Dict[str, Any], days: int) -> Dict[str, Any]:
        """Generate trend analysis for various metrics."""
        sessions = data.get('sessions', [])
        tasks = data.get('tasks', [])
        
        # Split data into two periods for comparison
        mid_point = days // 2
        end_date = data.get('end_date', datetime.now())
        mid_date = end_date - timedelta(days=mid_point)
        
        recent_sessions = [s for s in sessions if s.created_at >= mid_date]
        older_sessions = [s for s in sessions if s.created_at < mid_date]
        
        recent_tasks = [t for t in tasks if t.created_at >= mid_date]
        older_tasks = [t for t in tasks if t.created_at < mid_date]
        
        return {
            'meeting_frequency': {
                'recent_avg': len(recent_sessions) / mid_point if mid_point > 0 else 0,
                'previous_avg': len(older_sessions) / mid_point if mid_point > 0 else 0,
                'trend': 'up' if len(recent_sessions) > len(older_sessions) else 'down',
                'change_percent': ((len(recent_sessions) - len(older_sessions)) / max(len(older_sessions), 1)) * 100
            },
            'task_creation': {
                'recent_avg': len(recent_tasks) / mid_point if mid_point > 0 else 0,
                'previous_avg': len(older_tasks) / mid_point if mid_point > 0 else 0,
                'trend': 'up' if len(recent_tasks) > len(older_tasks) else 'down',
                'change_percent': ((len(recent_tasks) - len(older_tasks)) / max(len(older_tasks), 1)) * 100
            }
        }
    
    def _generate_user_metrics(self, data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Generate user-specific metrics."""
        sessions = data.get('sessions', [])
        tasks = data.get('tasks', [])
        
        return {
            'total_meeting_time': sum(s.duration_seconds or 0 for s in sessions) / 3600,
            'avg_session_length': (sum(s.duration_seconds or 0 for s in sessions) / len(sessions)) / 60 if sessions else 0,
            'productivity_score': self._calculate_productivity_score(sessions, tasks),
            'consistency_score': self._calculate_consistency_score(sessions),
            'engagement_level': self._calculate_user_engagement_level(sessions, tasks)
        }
    
    def _calculate_productivity_score(self, sessions: List, tasks: List) -> float:
        """Calculate user productivity score."""
        # Base score from activity
        meeting_score = len(sessions) * 5
        task_score = len(tasks) * 3
        
        # Bonus for completed tasks
        completed_tasks = len([t for t in tasks if t.status == 'completed'])
        completion_bonus = completed_tasks * 2
        
        # Normalize to 0-100 scale
        total_score = meeting_score + task_score + completion_bonus
        return min(100, total_score)
    
    def _calculate_consistency_score(self, sessions: List) -> float:
        """Calculate consistency score based on regular activity."""
        if not sessions:
            return 0
        
        # Count active days
        active_days = len(set(s.created_at.date() for s in sessions))
        total_days = 30  # Assuming 30-day analysis
        
        return (active_days / total_days) * 100
    
    def _calculate_user_engagement_level(self, sessions: List, tasks: List) -> str:
        """Calculate user engagement level."""
        total_activity = len(sessions) + len(tasks)
        
        if total_activity >= 50:
            return 'high'
        elif total_activity >= 20:
            return 'medium'
        elif total_activity >= 5:
            return 'low'
        else:
            return 'minimal'
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if not expired."""
        if key in self.analytics_cache:
            cached_data, timestamp = self.analytics_cache[key]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Set data in cache with timestamp."""
        self.analytics_cache[key] = (data, datetime.now())
    
    def _get_default_analytics(self) -> Dict[str, Any]:
        """Return default analytics structure when data is unavailable."""
        return {
            'summary': AnalyticsSummary(
                total_meetings=0,
                total_duration_hours=0,
                total_tasks_created=0,
                avg_meeting_duration_minutes=0,
                task_completion_rate=0,
                active_users=0,
                growth_rate=0,
                engagement_score=0
            ),
            'charts': [],
            'insights': [],
            'trends': {},
            'user_metrics': {},
            'productivity_scores': {},
            'engagement_metrics': {},
            'time_analysis': {},
            'content_analytics': {},
            'collaboration_metrics': {}
        }


# Global service instance
advanced_analytics_service = AdvancedAnalyticsService()