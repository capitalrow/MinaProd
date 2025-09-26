"""
Tasks API Routes
REST API endpoints for task management, CRUD operations, and status updates.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Task, Meeting, User
from datetime import datetime, date
from sqlalchemy import func, and_, or_


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
        query = Task.query.join(Meeting).filter(
            Meeting.workspace_id == current_user.workspace_id
        )
        
        # Apply filters
        if status:
            query = query.filter(Task.status == status)
        
        if priority:
            query = query.filter(Task.priority == priority)
        
        if assigned_to:
            if assigned_to == 'me':
                query = query.filter(Task.assigned_to_id == current_user.id)
            elif assigned_to == 'unassigned':
                query = query.filter(Task.assigned_to_id.is_(None))
            else:
                query = query.filter(Task.assigned_to_id == int(assigned_to))
        
        if meeting_id:
            query = query.filter(Task.meeting_id == meeting_id)
        
        if search:
            query = query.filter(
                or_(
                    Task.title.contains(search),
                    Task.description.contains(search)
                )
            )
        
        # Due date filters
        if due_date_filter:
            today = date.today()
            if due_date_filter == 'today':
                query = query.filter(Task.due_date == today)
            elif due_date_filter == 'overdue':
                query = query.filter(
                    and_(
                        Task.due_date < today,
                        Task.status.in_(['todo', 'in_progress'])
                    )
                )
            elif due_date_filter == 'this_week':
                week_end = today + timedelta(days=7-today.weekday())
                query = query.filter(
                    and_(
                        Task.due_date >= today,
                        Task.due_date <= week_end
                    )
                )
        
        # Order by priority and due date
        query = query.order_by(
            Task.priority.desc(),
            Task.due_date.asc().nullslast(),
            Task.created_at.desc()
        )
        
        # Paginate
        tasks = query.paginate(page=page, per_page=per_page, error_out=False)
        
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
        task = Task.query.join(Meeting).filter(
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
        
        if not data.get('meeting_id'):
            return jsonify({'success': False, 'message': 'Meeting ID is required'}), 400
        
        # Verify meeting exists and belongs to user's workspace
        meeting = Meeting.query.filter_by(
            id=data['meeting_id'],
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
            assignee = User.query.filter_by(
                id=assigned_to_id,
                workspace_id=current_user.workspace_id
            ).first()
            if not assignee:
                return jsonify({'success': False, 'message': 'Invalid assignee'}), 400
        
        task = Task(
            title=data['title'].strip(),
            description=data.get('description', '').strip() or None,
            meeting_id=data['meeting_id'],
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
        task = Task.query.join(Meeting).filter(
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
                    task.completed_by_id = current_user.id
                elif new_status != 'completed' and old_status == 'completed':
                    task.completed_at = None
                    task.completed_by_id = None
        
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
                assignee = User.query.filter_by(
                    id=assigned_to_id,
                    workspace_id=current_user.workspace_id
                ).first()
                if not assignee:
                    return jsonify({'success': False, 'message': 'Invalid assignee'}), 400
            task.assigned_to_id = assigned_to_id
        
        task.updated_at = datetime.now()
        db.session.commit()
        
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
        task = Task.query.join(Meeting).filter(
            Task.id == task_id,
            Meeting.workspace_id == current_user.workspace_id
        ).first()
        
        if not task:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        db.session.delete(task)
        db.session.commit()
        
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
        task = Task.query.join(Meeting).filter(
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
            task.completed_by_id = current_user.id
        elif new_status != 'completed' and old_status == 'completed':
            task.completed_at = None
            task.completed_by_id = None
        
        task.updated_at = datetime.now()
        db.session.commit()
        
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
        tasks = Task.query.join(Meeting).filter(
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
                    task.completed_by_id = current_user.id
                elif new_status != 'completed' and old_status == 'completed':
                    task.completed_at = None
                    task.completed_by_id = None
            
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
        
        query = Task.query.join(Meeting).filter(
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
        total_tasks = Task.query.join(Meeting).filter(
            Meeting.workspace_id == workspace_id
        ).count()
        
        completed_tasks = Task.query.join(Meeting).filter(
            Meeting.workspace_id == workspace_id,
            Task.status == 'completed'
        ).count()
        
        overdue_tasks = Task.query.join(Meeting).filter(
            Meeting.workspace_id == workspace_id,
            Task.due_date < date.today(),
            Task.status.in_(['todo', 'in_progress'])
        ).count()
        
        my_tasks = Task.query.join(Meeting).filter(
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
        overdue_tasks = Task.query.join(Meeting).filter(
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