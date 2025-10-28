"""
Tasks API Routes
REST API endpoints for task management, CRUD operations, and status updates.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Task, Meeting, User, Session, Workspace
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_, select
# server/routes/api_tasks.py
import logging
from app import db
from models.summary import Summary
from services.event_broadcaster import EventBroadcaster

logger = logging.getLogger(__name__)
event_broadcaster = EventBroadcaster()

api_tasks_bp = Blueprint('api_tasks', __name__, url_prefix='/api/tasks')


@api_tasks_bp.route('/', methods=['GET'])
@login_required
def list_tasks():
    """Get tasks for current user's workspace with filtering and pagination."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        status = request.args.get('status', None)
        priority = request.args.get('priority', None)
        assigned_to = request.args.get('assigned_to', None)
        meeting_id = request.args.get('meeting_id', None, type=int)
        search = request.args.get('search', None)
        due_date_filter = request.args.get('due_date', None)  # today, overdue, this_week
        
        # Base query - tasks from meetings in user's workspace
        stmt = select(Task).join(Meeting).where(
            Meeting.workspace_id == current_user.workspace_id
        )
        
        # Apply filters
        if status:
            stmt = stmt.where(Task.status == status)
        
        if priority:
            stmt = stmt.where(Task.priority == priority)
        
        if assigned_to:
            if assigned_to == 'me':
                stmt = stmt.where(Task.assigned_to_id == current_user.id)
            elif assigned_to == 'unassigned':
                stmt = stmt.where(Task.assigned_to_id.is_(None))
            else:
                stmt = stmt.where(Task.assigned_to_id == int(assigned_to))
        
        if meeting_id:
            stmt = stmt.where(Task.meeting_id == meeting_id)
        
        if search:
            stmt = stmt.where(
                or_(
                    Task.title.contains(search),
                    Task.description.contains(search)
                )
            )
        
        # Due date filters
        if due_date_filter:
            today = date.today()
            if due_date_filter == 'today':
                stmt = stmt.where(Task.due_date == today)
            elif due_date_filter == 'overdue':
                stmt = stmt.where(
                    and_(
                        Task.due_date < today,
                        Task.status.in_(['todo', 'in_progress'])
                    )
                )
            elif due_date_filter == 'this_week':
                week_end = today + timedelta(days=7-today.weekday())
                stmt = stmt.where(
                    and_(
                        Task.due_date >= today,
                        Task.due_date <= week_end
                    )
                )
        
        # Order by priority and due date
        stmt = stmt.order_by(
            Task.priority.desc(),
            Task.due_date.asc().nullslast(),
            Task.created_at.desc()
        )
        
        # Paginate
        tasks = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'tasks': [task.to_dict() for task in tasks.items],
            'pagination': {
                'page': tasks.page,
                'pages': tasks.pages,
                'per_page': tasks.per_page,
                'total': tasks.total,
                'has_next': tasks.has_next,
                'has_prev': tasks.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_tasks_bp.route('/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    """Get detailed task information."""
    try:
        task = db.session.query(Task).join(Meeting).filter(
            Task.id == task_id,
            Meeting.workspace_id == current_user.workspace_id
        ).first()
        
        if not task:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        return jsonify({
            'success': True,
            'task': task.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_tasks_bp.route('/', methods=['POST'])
@login_required
def create_task():
    """Create a new task."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'success': False, 'message': 'Title is required'}), 400
        
        # Verify meeting exists and belongs to user's workspace (optional)
        meeting = None
        meeting_id = data.get('meeting_id')
        if meeting_id:
            meeting = db.session.query(Meeting).filter_by(
                id=meeting_id,
                workspace_id=current_user.workspace_id
            ).first()
            
            if not meeting:
                return jsonify({'success': False, 'message': 'Invalid meeting ID'}), 400
        
        # Parse due date if provided
        due_date = None
        if data.get('due_date'):
            try:
                due_date = date.fromisoformat(data['due_date'])
            except ValueError:
                return jsonify({'success': False, 'message': 'Invalid due date format. Use YYYY-MM-DD'}), 400
        
        # Validate assigned_to_id if provided
        assigned_to_id = data.get('assigned_to_id')
        if assigned_to_id:
            assignee = db.session.query(User).filter_by(
                id=assigned_to_id,
                workspace_id=current_user.workspace_id
            ).first()
            if not assignee:
                return jsonify({'success': False, 'message': 'Invalid assignee'}), 400
        
        task = Task(
            title=data['title'].strip(),
            description=data.get('description', '').strip() or None,
            meeting_id=meeting.id if meeting else None,
            priority=data.get('priority', 'medium'),
            category=data.get('category', '').strip() or None,
            due_date=due_date,
            assigned_to_id=assigned_to_id,
            status='todo',
            created_by_id=current_user.id,
            extracted_by_ai=False
        )
        
        db.session.add(task)
        db.session.commit()
        
        # Broadcast task_update event (always broadcast, even without meeting)
        task_dict = task.to_dict()
        task_dict['action'] = 'created'
        task_dict['meeting_title'] = meeting.title if meeting else None
        event_broadcaster.broadcast_task_update(
            task_id=task.id,
            task_data=task_dict,
            meeting_id=meeting.id if meeting else None,
            workspace_id=current_user.workspace_id
        )
        
        return jsonify({
            'success': True,
            'message': 'Task created successfully',
            'task': task.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@api_tasks_bp.route('/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    """Update task information."""
    try:
        task = db.session.query(Task).join(Meeting).filter(
            Task.id == task_id,
            Meeting.workspace_id == current_user.workspace_id
        ).first()
        
        if not task:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        data = request.get_json()
        old_status = task.status
        
        # Update fields
        if 'title' in data:
            task.title = data['title'].strip()
        
        if 'description' in data:
            task.description = data['description'].strip() or None
        
        if 'priority' in data:
            task.priority = data['priority']
        
        if 'category' in data:
            task.category = data['category'].strip() or None
        
        if 'status' in data:
            new_status = data['status']
            if new_status != old_status:
                task.status = new_status
                
                # Update completion timestamp
                if new_status == 'completed' and old_status != 'completed':
                    task.completed_at = datetime.now()
                elif new_status != 'completed' and old_status == 'completed':
                    task.completed_at = None
        
        if 'due_date' in data:
            if data['due_date']:
                try:
                    task.due_date = date.fromisoformat(data['due_date'])
                except ValueError:
                    return jsonify({'success': False, 'message': 'Invalid due date format'}), 400
            else:
                task.due_date = None
        
        if 'assigned_to_id' in data:
            assigned_to_id = data['assigned_to_id']
            if assigned_to_id:
                assignee = db.session.query(User).filter_by(
                    id=assigned_to_id,
                    workspace_id=current_user.workspace_id
                ).first()
                if not assignee:
                    return jsonify({'success': False, 'message': 'Invalid assignee'}), 400
            task.assigned_to_id = assigned_to_id
        
        task.updated_at = datetime.now()
        db.session.commit()
        
        # Broadcast task_update event (always broadcast, even without meeting)
        meeting = task.meeting
        action = 'completed' if task.status == 'completed' and old_status != 'completed' else 'updated'
        task_dict = task.to_dict()
        task_dict['action'] = action
        task_dict['meeting_title'] = meeting.title if meeting else None
        
        event_broadcaster.broadcast_task_update(
            task_id=task.id,
            task_data=task_dict,
            meeting_id=meeting.id if meeting else None,
            workspace_id=current_user.workspace_id
        )
        
        return jsonify({
            'success': True,
            'message': 'Task updated successfully',
            'task': task.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@api_tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """Delete a task."""
    try:
        task = db.session.query(Task).join(Meeting).filter(
            Task.id == task_id,
            Meeting.workspace_id == current_user.workspace_id
        ).first()
        
        if not task:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        # Store task info before deletion
        task_id = task.id
        task_dict = task.to_dict()
        task_dict['action'] = 'deleted'
        meeting = task.meeting
        meeting_title = meeting.title if meeting else 'Unknown'
        meeting_id = meeting.id if meeting else None
        task_dict['meeting_title'] = meeting_title
        workspace_id = current_user.workspace_id
        
        db.session.delete(task)
        db.session.commit()
        
        # Broadcast task_update event (always broadcast, even without meeting)
        event_broadcaster.broadcast_task_update(
            task_id=task_id,
            task_data=task_dict,
            meeting_id=meeting_id,
            workspace_id=workspace_id
        )
        
        return jsonify({
            'success': True,
            'message': 'Task deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@api_tasks_bp.route('/<int:task_id>/status', methods=['PUT'])
@login_required
def update_task_status(task_id):
    """Update only the status of a task (for quick status changes)."""
    try:
        task = db.session.query(Task).join(Meeting).filter(
            Task.id == task_id,
            Meeting.workspace_id == current_user.workspace_id
        ).first()
        
        if not task:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'success': False, 'message': 'Status is required'}), 400
        
        if new_status not in ['todo', 'in_progress', 'completed', 'cancelled']:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        old_status = task.status
        task.status = new_status
        
        # Update completion fields
        if new_status == 'completed' and old_status != 'completed':
            task.completed_at = datetime.now()
        elif new_status != 'completed' and old_status == 'completed':
            task.completed_at = None
        
        task.updated_at = datetime.now()
        db.session.commit()
        
        # Broadcast task_update event (always broadcast, even without meeting)
        meeting = task.meeting
        action = 'completed' if new_status == 'completed' and old_status != 'completed' else 'updated'
        task_dict = task.to_dict()
        task_dict['action'] = action
        task_dict['meeting_title'] = meeting.title if meeting else None
        
        event_broadcaster.broadcast_task_update(
            task_id=task.id,
            task_data=task_dict,
            meeting_id=meeting.id if meeting else None,
            workspace_id=current_user.workspace_id
        )
        
        return jsonify({
            'success': True,
            'message': 'Task status updated successfully',
            'task': task.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@api_tasks_bp.route('/bulk-update', methods=['PUT'])
@login_required
def bulk_update_tasks():
    """Update multiple tasks at once."""
    try:
        data = request.get_json()
        task_ids = data.get('task_ids', [])
        updates = data.get('updates', {})
        
        if not task_ids:
            return jsonify({'success': False, 'message': 'Task IDs are required'}), 400
        
        # Get tasks that belong to user's workspace
        tasks = db.session.query(Task).join(Meeting).filter(
            Task.id.in_(task_ids),
            Meeting.workspace_id == current_user.workspace_id
        ).all()
        
        updated_count = 0
        for task in tasks:
            if 'status' in updates:
                new_status = updates['status']
                old_status = task.status
                task.status = new_status
                
                # Handle completion logic
                if new_status == 'completed' and old_status != 'completed':
                    task.completed_at = datetime.now()
                elif new_status != 'completed' and old_status == 'completed':
                    task.completed_at = None
            
            if 'priority' in updates:
                task.priority = updates['priority']
            
            if 'assigned_to_id' in updates:
                task.assigned_to_id = updates['assigned_to_id']
            
            task.updated_at = datetime.now()
            updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Updated {updated_count} tasks successfully',
            'updated_count': updated_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@api_tasks_bp.route('/my-tasks', methods=['GET'])
@login_required
def get_my_tasks():
    """Get tasks assigned to current user."""
    try:
        status = request.args.get('status', None)
        
        query = db.session.query(Task).join(Meeting).filter(
            Task.assigned_to_id == current_user.id,
            Meeting.workspace_id == current_user.workspace_id
        )
        
        if status:
            query = query.filter(Task.status == status)
        
        tasks = query.order_by(
            Task.priority.desc(),
            Task.due_date.asc().nullslast(),
            Task.created_at.desc()
        ).all()
        
        # Group by status for dashboard
        task_groups = {
            'todo': [],
            'in_progress': [],
            'completed': []
        }
        
        for task in tasks:
            if task.status in task_groups:
                task_groups[task.status].append(task.to_dict())
        
        return jsonify({
            'success': True,
            'tasks': task_groups,
            'total_assigned': len(tasks)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_tasks_bp.route('/stats', methods=['GET'])
@login_required
def get_task_stats():
    """Get task statistics for current workspace."""
    try:
        workspace_id = current_user.workspace_id
        
        # Basic counts
        total_tasks = db.session.query(Task).join(Meeting).filter(
            Meeting.workspace_id == workspace_id
        ).count()
        
        completed_tasks = db.session.query(Task).join(Meeting).filter(
            Meeting.workspace_id == workspace_id,
            Task.status == 'completed'
        ).count()
        
        overdue_tasks = db.session.query(Task).join(Meeting).filter(
            Meeting.workspace_id == workspace_id,
            Task.due_date < date.today(),
            Task.status.in_(['todo', 'in_progress'])
        ).count()
        
        my_tasks = db.session.query(Task).join(Meeting).filter(
            Meeting.workspace_id == workspace_id,
            Task.assigned_to_id == current_user.id,
            Task.status.in_(['todo', 'in_progress'])
        ).count()
        
        # Tasks by status
        status_counts = db.session.query(
            Task.status,
            func.count(Task.id).label('count')
        ).join(Meeting).filter(
            Meeting.workspace_id == workspace_id
        ).group_by(Task.status).all()
        
        status_distribution = {status: count for status, count in status_counts}
        
        # Tasks by priority
        priority_counts = db.session.query(
            Task.priority,
            func.count(Task.id).label('count')
        ).join(Meeting).filter(
            Meeting.workspace_id == workspace_id
        ).group_by(Task.priority).all()
        
        priority_distribution = {priority: count for priority, count in priority_counts}
        
        return jsonify({
            'success': True,
            'stats': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'overdue_tasks': overdue_tasks,
                'my_active_tasks': my_tasks,
                'completion_rate': round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0,
                'status_distribution': status_distribution,
                'priority_distribution': priority_distribution
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_tasks_bp.route('/overdue', methods=['GET'])
@login_required
def get_overdue_tasks():
    """Get overdue tasks for current workspace."""
    try:
        overdue_tasks = db.session.query(Task).join(Meeting).filter(
            Meeting.workspace_id == current_user.workspace_id,
            Task.due_date < date.today(),
            Task.status.in_(['todo', 'in_progress'])
        ).order_by(Task.due_date.asc()).all()
        
        return jsonify({
            'success': True,
            'overdue_tasks': [task.to_dict() for task in overdue_tasks],
            'count': len(overdue_tasks)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_tasks_bp.route('/create', methods=['POST'])
def create_live_task():
    """Create a task from highlighted text in live transcription (no authentication required for live sessions)."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'success': False, 'message': 'Title is required'}), 400
        
        if not data.get('session_id'):
            return jsonify({'success': False, 'message': 'Session ID is required'}), 400
        
        # Find or create a session record
        session_external_id = data['session_id']
        session = db.session.query(Session).filter_by(external_id=session_external_id).first()
        
        if not session:
            # Create a new session record for this live transcription
            # Note: No user_id/workspace_id for anonymous live sessions
            session = Session(
                external_id=session_external_id,
                title=f"Live Transcription - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                status="active",
                started_at=datetime.utcnow()
            )
            db.session.add(session)
            db.session.flush()  # Get the session ID
        
        # Create or find a meeting record linked to this session
        meeting = db.session.query(Meeting).filter(Meeting.session.has(id=session.id)).first()
        
        if not meeting:
            # Get default workspace for anonymous sessions
            default_workspace = db.session.query(Workspace).first()
            workspace_id = default_workspace.id if default_workspace else 1
            
            # Get default user for anonymous sessions  
            default_user = db.session.query(User).first()
            user_id = default_user.id if default_user else None
            
            # Create a meeting record
            meeting = Meeting(
                title=f"Live Meeting - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                status="in_progress",
                workspace_id=workspace_id,
                organizer_id=user_id if user_id else 1,  # Required field
                created_at=datetime.utcnow()
            )
            db.session.add(meeting)
            db.session.flush()  # Get the meeting ID
            
            # Link session to meeting (correct direction)
            session.meeting_id = meeting.id
            db.session.flush()
        
        # Parse due date from natural language if provided
        due_date = None
        due_date_text = data.get('due_date_text', '').strip()
        if due_date_text:
            due_date = parse_natural_due_date(due_date_text)
        
        # Create the task
        # Store context and assignee in extraction_context for live sessions
        extraction_ctx = {}
        if data.get('context'):
            extraction_ctx['source_text'] = data.get('context', '')
        if data.get('assignee'):
            extraction_ctx['assignee_name'] = data.get('assignee', '').strip()
        
        task = Task(
            title=data['title'].strip(),
            description=data.get('description', '').strip() or None,
            meeting_id=meeting.id,
            priority=data.get('priority', 'medium'),
            category='live_transcription',
            due_date=due_date,
            status='todo',
            created_by_id=None,  # No user authentication for live sessions
            extracted_by_ai=False,
            extraction_context=extraction_ctx if extraction_ctx else None
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task created successfully',
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'priority': task.priority,
                'status': task.status,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'extraction_context': task.extraction_context,
                'created_at': task.created_at.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

def parse_natural_due_date(due_date_text):
    """Parse natural language due dates like 'tomorrow', 'next week', 'friday'."""
    try:
        text = due_date_text.lower().strip()
        today = date.today()
        
        if text in ['today']:
            return today
        elif text in ['tomorrow']:
            return today + timedelta(days=1)
        elif text in ['next week']:
            days_ahead = 7 - today.weekday()
            return today + timedelta(days=days_ahead)
        elif text in ['end of week', 'friday']:
            days_ahead = 4 - today.weekday()  # Friday is day 4
            if days_ahead < 0:  # If Friday has passed, get next Friday
                days_ahead += 7
            return today + timedelta(days=days_ahead)
        elif text in ['monday']:
            days_ahead = 0 - today.weekday()
            if days_ahead <= 0:  # If Monday has passed, get next Monday
                days_ahead += 7
            return today + timedelta(days=days_ahead)
        elif text in ['next month']:
            if today.month == 12:
                return date(today.year + 1, 1, today.day)
            else:
                return date(today.year, today.month + 1, today.day)
        
        # Try to parse as ISO date
        try:
            return date.fromisoformat(text)
        except ValueError:
            pass
            
        # Default to one week from now if we can't parse
        return today + timedelta(days=7)
        
    except Exception:
        # If all parsing fails, default to one week from now
        return date.today() + timedelta(days=7)

@api_tasks_bp.route('', methods=['GET'])
def get_all_tasks():
    """
    List all action items across sessions.
    Query params:
      - session_id: (optional) filter by session
      - completed: (optional) "true"/"false" to filter by completion status
    """
    session_filter = request.args.get('session_id', type=int)
    completed_filter = request.args.get('completed')
    try:
        stmt = select(Summary).filter(Summary.actions != None)
        if session_filter:
            stmt = stmt.filter(Summary.session_id == session_filter)
        summaries = db.session.execute(stmt).scalars().all()
        tasks = []
        for summary in summaries:
            if not summary.actions: 
                continue
            for idx, task in enumerate(summary.actions):
                # Apply completion filter if provided
                if completed_filter is not None:
                    want_completed = completed_filter.lower() in ['1', 'true', 'yes']
                    if task.get('completed', False) != want_completed:
                        continue
                tasks.append({
                    "session_id": summary.session_id,
                    "task_index": idx,
                    "text": task.get("text"),
                    "owner": task.get("owner"),
                    "due": task.get("due"),
                    "completed": task.get("completed", False)
                })
        return jsonify({"success": True, "tasks": tasks}), 200
    except Exception as e:
        logger.error(f"Error retrieving tasks: {e}")
        return jsonify({"success": False, "error": "Failed to retrieve tasks"}), 500

@api_tasks_bp.route('/<int:session_id>/<int:task_index>', methods=['PUT'])
def update_summary_task(session_id, task_index):
    """
    Update a specific task identified by session ID and index.
    Allows marking complete or editing fields (same JSON format as summary route).
    """
    data = request.get_json(force=True)
    if not data:
        return jsonify({"success": False, "error": "No update data provided"}), 400
    try:
        stmt = select(Summary).filter(Summary.session_id == session_id).order_by(Summary.created_at.desc())
        summary = db.session.execute(stmt).scalar_one_or_none()
        if not summary or not summary.actions or task_index >= len(summary.actions):
            return jsonify({"success": False, "error": "Task not found"}), 404
        task = summary.actions[task_index]
        if 'text' in data: task['text'] = data['text']
        if 'owner' in data: task['owner'] = data['owner']
        if 'due' in data: task['due'] = data['due']
        if 'completed' in data: task['completed'] = bool(data['completed'])
        summary.actions = summary.actions
        db.session.commit()
        logger.info(f"Task updated for session {session_id}, index {task_index}: {data}")
        return jsonify({"success": True, "task": task}), 200
    except Exception as e:
        logger.error(f"Error updating task {task_index} in session {session_id}: {e}")
        db.session.rollback()
        return jsonify({"success": False, "error": "Failed to update task"}), 500
        