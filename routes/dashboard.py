"""
Dashboard Routes for Mina Productivity Platform
Main dashboard with meetings, tasks, analytics overview.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Meeting, Task, Analytics, Session, Marker
from sqlalchemy import desc, func, and_
from datetime import datetime, timedelta, date

try:
    from services.uptime_monitoring import uptime_monitor
    from services.performance_monitoring import performance_monitor
    monitoring_available = True
except ImportError:
    monitoring_available = False


dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page with overview of meetings, tasks, and analytics."""
    # Check if user has a workspace, if not create one
    if not current_user.workspace_id:
        from models import Workspace
        try:
            workspace_name = f"{current_user.first_name}'s Workspace" if current_user.first_name else f"{current_user.username}'s Workspace"
            workspace = Workspace(
                name=workspace_name,
                slug=Workspace.generate_slug(workspace_name),
                owner_id=current_user.id
            )
            db.session.add(workspace)
            db.session.flush()
            current_user.workspace_id = workspace.id
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            import logging
            logging.error(f"Failed to create workspace for user {current_user.id}: {e}")
            # Continue with None workspace - show empty dashboard
    
    # Get recent meetings (handle None workspace)
    if current_user.workspace_id:
        recent_meetings = db.session.query(Meeting).filter_by(
            workspace_id=current_user.workspace_id
        ).order_by(desc(Meeting.created_at)).limit(5).all()
    else:
        recent_meetings = []
    
    # Get user's tasks
    user_tasks = db.session.query(Task).filter_by(
        assigned_to_id=current_user.id
    ).filter(Task.status.in_(['todo', 'in_progress'])).limit(10).all()
    
    # Get workspace statistics
    if current_user.workspace_id:
        total_meetings = db.session.query(Meeting).filter_by(workspace_id=current_user.workspace_id).count()
        total_tasks = db.session.query(Task).join(Meeting).filter(
            Meeting.workspace_id == current_user.workspace_id
        ).count()
        completed_tasks = db.session.query(Task).join(Meeting).filter(
            Meeting.workspace_id == current_user.workspace_id,
            Task.status == 'completed'
        ).count()
    else:
        total_meetings = 0
        total_tasks = 0
        completed_tasks = 0
    
    # Calculate task completion rate
    task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Get this week's meetings
    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    if current_user.workspace_id:
        this_week_meetings = db.session.query(Meeting).filter_by(
            workspace_id=current_user.workspace_id
        ).filter(Meeting.created_at >= week_start).count()
    else:
        this_week_meetings = 0
    
    # Get today's meetings (meetings created today or scheduled for today)
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    if current_user.workspace_id:
        todays_meetings = db.session.query(Meeting).filter_by(
            workspace_id=current_user.workspace_id
        ).filter(
            and_(
                Meeting.created_at >= today_start,
                Meeting.created_at < today_end
            )
        ).order_by(desc(Meeting.created_at)).all()
    else:
        todays_meetings = []
    
    # Get follow-up items from recent meetings (last 7 days)
    recent_cutoff = datetime.now() - timedelta(days=7)
    
    # Get recent markers (decisions, todos, risks)
    recent_markers = db.session.query(Marker).filter_by(
        user_id=current_user.id
    ).filter(Marker.created_at >= recent_cutoff).order_by(desc(Marker.created_at)).limit(5).all()
    
    # Get urgent tasks (high priority or due soon)
    urgent_tasks = db.session.query(Task).filter_by(
        assigned_to_id=current_user.id
    ).filter(
        Task.status.in_(['todo', 'in_progress'])
    ).order_by(desc(Task.priority), Task.due_date).limit(5).all()
    
    # Create follow-up items combining markers and urgent tasks
    follow_up_items = []
    
    # Add markers as follow-up items
    for marker in recent_markers:
        content_preview = str(marker.content)[:50] + ('...' if len(str(marker.content)) > 50 else '')
        follow_up_items.append({
            'type': 'marker',
            'subtype': marker.type,
            'title': f"{marker.type.title()}: {content_preview}",
            'content': marker.content,
            'timestamp': marker.created_at,
            'speaker': marker.speaker,
            'session_id': marker.session_id,
            'id': marker.id
        })
    
    # Add urgent tasks as follow-up items
    for task in urgent_tasks:
        follow_up_items.append({
            'type': 'task',
            'subtype': task.priority,
            'title': task.title,
            'content': task.description or '',
            'timestamp': task.created_at,
            'due_date': task.due_date,
            'status': task.status,
            'id': task.id
        })
    
    # Sort follow-up items by timestamp (newest first)
    follow_up_items.sort(key=lambda x: x['timestamp'], reverse=True)
    follow_up_items = follow_up_items[:8]  # Limit to 8 items
    
    return render_template('dashboard/index.html',
                         recent_meetings=recent_meetings,
                         user_tasks=user_tasks,
                         todays_meetings=todays_meetings,
                         follow_up_items=follow_up_items,
                         stats={
                             'total_meetings': total_meetings,
                             'total_tasks': total_tasks,
                             'completed_tasks': completed_tasks,
                             'task_completion_rate': round(task_completion_rate, 1),
                             'this_week_meetings': this_week_meetings,
                             'todays_meetings': len(todays_meetings)
                         })


@dashboard_bp.route('/meetings')
@login_required
def meetings():
    """Meetings overview page."""
    # Check if user has workspace, if not show empty state
    if not current_user.workspace_id:
        return render_template('dashboard/meetings.html',
                             meetings=[],
                             status_filter='all',
                             search_query='',
                             empty_state=True)
    
    # Filter and pagination
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('search', '')
    
    # Build query
    query = db.select(Meeting).filter_by(workspace_id=current_user.workspace_id)
    
    # Apply filters
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if search_query:
        query = query.filter(Meeting.title.contains(search_query))
    
    # Order by created_at descending
    query = query.order_by(desc(Meeting.created_at))
    
    # Paginate results
    meetings = db.paginate(query, page=page, per_page=20, error_out=False)
    
    return render_template('dashboard/meetings.html',
                         meetings=meetings,
                         status_filter=status_filter,
                         search_query=search_query,
                         empty_state=False)


@dashboard_bp.route('/meeting/<int:meeting_id>')
@login_required
def meeting_detail(meeting_id):
    """Three-pane meeting detail view with transcript, summary, and tasks."""
    # Get meeting details
    meeting = db.session.query(Meeting).filter_by(
        id=meeting_id,
        workspace_id=current_user.workspace_id
    ).first()
    
    if not meeting:
        return render_template('errors/404.html'), 404
    
    # Get meeting transcript segments (if available from session)
    from models import Session, Segment
    session = None
    segments = []
    
    if meeting.session_id:
        session = db.session.query(Session).filter_by(external_id=meeting.session_id).first()
        if session:
            segments = db.session.query(Segment).filter_by(
                session_id=session.id
            ).order_by(Segment.start_ms.asc()).all()
    
    # Get meeting tasks
    meeting_tasks = db.session.query(Task).filter_by(
        meeting_id=meeting.id
    ).order_by(Task.created_at.desc()).all()
    
    # Get meeting markers
    meeting_markers = []
    if meeting.session_id:
        meeting_markers = db.session.query(Marker).filter_by(
            session_id=meeting.session_id
        ).order_by(Marker.timestamp.asc()).all()
    
    # Generate AI summary (placeholder - would be from actual AI service)
    summary_data = {
        'key_points': [
            'Meeting started with review of quarterly goals',
            'Discussed upcoming product launch timeline',
            'Identified three main blockers requiring immediate attention',
            'Agreed on next steps for team coordination'
        ],
        'decisions': [marker for marker in meeting_markers if getattr(marker, 'type', None) == 'decision'],
        'action_items': [marker for marker in meeting_markers if getattr(marker, 'type', None) == 'todo'],
        'risks_concerns': [marker for marker in meeting_markers if getattr(marker, 'type', None) == 'risk'],
        'participants': ['Speaker 1', 'Speaker 2'],  # Placeholder - segments don't have speaker info
        'duration': calculate_meeting_duration(segments),
        'word_count': sum(len(segment.text.split()) for segment in segments if segment.text)
    }
    
    return render_template('dashboard/meeting_detail.html',
                         meeting=meeting,
                         session=session,
                         segments=segments,
                         tasks=meeting_tasks,
                         markers=meeting_markers,
                         summary=summary_data)


def calculate_meeting_duration(segments):
    """Calculate total meeting duration from segments."""
    if not segments:
        return "0 minutes"
    
    # Use start_ms and end_ms from segments
    start_ms = segments[0].start_ms if segments and segments[0].start_ms else None
    end_ms = segments[-1].end_ms if segments and segments[-1].end_ms else None
    
    if start_ms is not None and end_ms is not None:
        duration_ms = end_ms - start_ms
        duration_minutes = int(duration_ms / (1000 * 60))
        
        if duration_minutes < 60:
            return f"{duration_minutes} minutes"
        else:
            hours = duration_minutes // 60
            minutes = duration_minutes % 60
            return f"{hours}h {minutes}m"
    
    return "Unknown duration"


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


@dashboard_bp.route('/ops/metrics')
def ops_metrics():
    """Operational metrics dashboard endpoint."""
    if not monitoring_available:
        return jsonify({'error': 'Monitoring services not available'}), 503
    
    try:
        health = uptime_monitor.get_health_status()
        perf_stats = performance_monitor.get_stats()
        
        return jsonify({
            'health': health,
            'performance': perf_stats,
            'timestamp': health['timestamp']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500