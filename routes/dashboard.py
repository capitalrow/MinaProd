"""
Dashboard Routes for Mina Productivity Platform
Main dashboard with meetings, tasks, analytics overview.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Meeting, Task, Analytics, Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta


dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page with overview of meetings, tasks, and analytics."""
    # Get recent meetings
    recent_meetings = db.session.query(Meeting).filter_by(
        workspace_id=current_user.workspace_id
    ).order_by(desc(Meeting.created_at)).limit(5).all()
    
    # Get user's tasks
    user_tasks = db.session.query(Task).filter_by(
        assigned_to_id=current_user.id
    ).filter(Task.status.in_(['todo', 'in_progress'])).limit(10).all()
    
    # Get workspace statistics
    total_meetings = db.session.query(Meeting).filter_by(workspace_id=current_user.workspace_id).count()
    total_tasks = db.session.query(Task).join(Meeting).filter(
        Meeting.workspace_id == current_user.workspace_id
    ).count()
    completed_tasks = db.session.query(Task).join(Meeting).filter(
        Meeting.workspace_id == current_user.workspace_id,
        Task.status == 'completed'
    ).count()
    
    # Calculate task completion rate
    task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Get this week's meetings
    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    this_week_meetings = db.session.query(Meeting).filter_by(
        workspace_id=current_user.workspace_id
    ).filter(Meeting.created_at >= week_start).count()
    
    return render_template('dashboard/index.html',
                         recent_meetings=recent_meetings,
                         user_tasks=user_tasks,
                         stats={
                             'total_meetings': total_meetings,
                             'total_tasks': total_tasks,
                             'completed_tasks': completed_tasks,
                             'task_completion_rate': round(task_completion_rate, 1),
                             'this_week_meetings': this_week_meetings
                         })


@dashboard_bp.route('/meetings')
@login_required
def meetings():
    """Meetings overview page."""
    # Filter and pagination
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('search', '')
    
    # Base query
    query = db.session.query(Meeting).filter_by(workspace_id=current_user.workspace_id)
    
    # Apply filters
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if search_query:
        query = query.filter(Meeting.title.contains(search_query))
    
    # Paginate results
    meetings = db.paginate(
        query.order_by(desc(Meeting.created_at)),
        page=page, per_page=20, error_out=False
    )
    
    return render_template('dashboard/meetings.html',
                         meetings=meetings,
                         status_filter=status_filter,
                         search_query=search_query)


@dashboard_bp.route('/tasks')
@login_required
def tasks():
    """Tasks overview page with kanban board."""
    # Get tasks by status
    todo_tasks = db.session.query(Task).join(Meeting).filter(
        Meeting.workspace_id == current_user.workspace_id,
        Task.status == 'todo'
    ).order_by(Task.due_date.asc().nullslast(), Task.priority.desc()).all()
    
    in_progress_tasks = db.session.query(Task).join(Meeting).filter(
        Meeting.workspace_id == current_user.workspace_id,
        Task.status == 'in_progress'
    ).order_by(Task.due_date.asc().nullslast(), Task.priority.desc()).all()
    
    completed_tasks = db.session.query(Task).join(Meeting).filter(
        Meeting.workspace_id == current_user.workspace_id,
        Task.status == 'completed'
    ).order_by(desc(Task.completed_at)).limit(10).all()
    
    return render_template('dashboard/tasks.html',
                         todo_tasks=todo_tasks,
                         in_progress_tasks=in_progress_tasks,
                         completed_tasks=completed_tasks)


@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Analytics and insights page."""
    # Get recent analytics
    recent_analytics = db.session.query(Analytics).join(Meeting).filter(
        Meeting.workspace_id == current_user.workspace_id,
        Analytics.analysis_status == 'completed'
    ).order_by(desc(Analytics.created_at)).limit(10).all()
    
    # Calculate workspace averages
    avg_effectiveness = db.session.query(func.avg(Analytics.meeting_effectiveness_score)).join(Meeting).filter(
        Meeting.workspace_id == current_user.workspace_id,
        Analytics.meeting_effectiveness_score.isnot(None)
    ).scalar() or 0
    
    avg_engagement = db.session.query(func.avg(Analytics.overall_engagement_score)).join(Meeting).filter(
        Meeting.workspace_id == current_user.workspace_id,
        Analytics.overall_engagement_score.isnot(None)
    ).scalar() or 0
    
    avg_sentiment = db.session.query(func.avg(Analytics.overall_sentiment_score)).join(Meeting).filter(
        Meeting.workspace_id == current_user.workspace_id,
        Analytics.overall_sentiment_score.isnot(None)
    ).scalar() or 0
    
    return render_template('dashboard/analytics.html',
                         recent_analytics=recent_analytics,
                         workspace_averages={
                             'effectiveness': round(avg_effectiveness * 100, 1) if avg_effectiveness else 0,
                             'engagement': round(avg_engagement * 100, 1) if avg_engagement else 0,
                             'sentiment': round(avg_sentiment * 100, 1) if avg_sentiment else 0
                         })


@dashboard_bp.route('/api/recent-activity')
@login_required
def api_recent_activity():
    """API endpoint for recent activity feed."""
    # Get recent meetings
    recent_meetings = db.session.query(Meeting).filter_by(
        workspace_id=current_user.workspace_id
    ).order_by(desc(Meeting.created_at)).limit(5).all()
    
    # Get recent tasks
    recent_tasks = db.session.query(Task).join(Meeting).filter(
        Meeting.workspace_id == current_user.workspace_id
    ).order_by(desc(Task.created_at)).limit(5).all()
    
    # Combine and sort activities
    activities = []
    
    for meeting in recent_meetings:
        activities.append({
            'type': 'meeting',
            'id': meeting.id,
            'title': meeting.title,
            'timestamp': meeting.created_at,
            'status': meeting.status
        })
    
    for task in recent_tasks:
        activities.append({
            'type': 'task',
            'id': task.id,
            'title': task.title,
            'timestamp': task.created_at,
            'status': task.status,
            'priority': task.priority
        })
    
    # Sort by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({'activities': activities[:10]})


@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics."""
    # Meeting stats
    total_meetings = db.session.query(Meeting).filter_by(workspace_id=current_user.workspace_id).count()
    active_meetings = db.session.query(Meeting).filter_by(
        workspace_id=current_user.workspace_id,
        status='live'
    ).count()
    
    # Task stats
    total_tasks = db.session.query(Task).join(Meeting).filter(
        Meeting.workspace_id == current_user.workspace_id
    ).count()
    completed_tasks = db.session.query(Task).join(Meeting).filter(
        Meeting.workspace_id == current_user.workspace_id,
        Task.status == 'completed'
    ).count()
    overdue_tasks = db.session.query(Task).join(Meeting).filter(
        Meeting.workspace_id == current_user.workspace_id,
        Task.due_date < datetime.now().date(),
        Task.status.in_(['todo', 'in_progress'])
    ).count()
    
    # This week's activity
    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    this_week_meetings = db.session.query(Meeting).filter_by(
        workspace_id=current_user.workspace_id
    ).filter(Meeting.created_at >= week_start).count()
    
    this_week_tasks = db.session.query(Task).join(Meeting).filter(
        Meeting.workspace_id == current_user.workspace_id,
        Task.created_at >= week_start
    ).count()
    
    return jsonify({
        'meetings': {
            'total': total_meetings,
            'active': active_meetings,
            'this_week': this_week_meetings
        },
        'tasks': {
            'total': total_tasks,
            'completed': completed_tasks,
            'overdue': overdue_tasks,
            'this_week': this_week_tasks,
            'completion_rate': round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
        }
    })