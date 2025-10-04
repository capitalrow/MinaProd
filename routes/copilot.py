"""
AI Copilot routes for Mina.

This module provides the AI Copilot functionality described in the handbook:
- Separate chat tab for natural language queries
- Meeting-aware Q&A with citations
- Task management through chat interface
- Action buttons for common operations
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user

logger = logging.getLogger(__name__)

copilot_bp = Blueprint('copilot', __name__, url_prefix='/copilot')


@copilot_bp.route('/')
@login_required 
def copilot_dashboard():
    """
    Display the AI Copilot interface.
    
    Returns:
        Rendered copilot chat interface
    """
    try:
        logger.debug(f"Loading AI Copilot for user {current_user.id}")
        return render_template('copilot/chat.html', 
                             page_title="AI Copilot")
    except Exception as e:
        logger.error(f"Error loading AI Copilot: {e}")
        flash('Failed to load AI Copilot. Please try again.', 'error')
        return redirect(url_for('dashboard.index'))


@copilot_bp.route('/api/chat', methods=['POST'])
@login_required
def chat_with_copilot():
    """
    Process chat messages with AI Copilot.
    
    Request Body:
        {
            "message": "What did we decide about the Q3 budget?",
            "context": "meeting_id_optional"
        }
    
    Returns:
        JSON: Copilot response with citations and action buttons
    """
    try:
        data = request.get_json() or {}
        message = data.get('message', '').strip()
        context = data.get('context')
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        # Process the message with AI
        response = _process_copilot_message(message, context, current_user.id)
        
        return jsonify({
            'success': True,
            'response': response
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing copilot message: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process message'
        }), 500


@copilot_bp.route('/api/execute-action', methods=['POST'])
@login_required
def execute_copilot_action():
    """
    Execute actions suggested by the Copilot.
    
    Request Body:
        {
            "action": "create_task|mark_done|delete_task|add_to_calendar|export",
            "parameters": {...}
        }
    
    Returns:
        JSON: Success/error response
    """
    try:
        data = request.get_json() or {}
        action = data.get('action')
        parameters = data.get('parameters', {})
        
        if not action:
            return jsonify({
                'success': False,
                'error': 'Action is required'
            }), 400
        
        # Execute the action
        result = _execute_copilot_action(action, parameters, current_user.id)
        
        return jsonify({
            'success': True,
            'result': result
        }), 200
    
    except Exception as e:
        logger.error(f"Error executing copilot action: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to execute action'
        }), 500


@copilot_bp.route('/api/quick-queries', methods=['GET'])
@login_required
def get_quick_queries():
    """
    Get suggested quick queries for the user.
    
    Returns:
        JSON: List of suggested queries
    """
    try:
        queries = [
            "What's due today?",
            "What are my overdue tasks?",
            "Summarize yesterday's meetings",
            "What decisions were made this week?",
            "Show me all risks from recent meetings",
            "What tasks did I create last week?",
            "Which meetings had the most action items?",
            "What topics came up most in my meetings?"
        ]
        
        return jsonify({
            'success': True,
            'queries': queries
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting quick queries: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get quick queries'
        }), 500


def _process_copilot_message(message: str, context: Optional[str], user_id: int) -> Dict[str, Any]:
    """
    Process a message using AI and meeting context.
    
    Args:
        message: User's natural language query
        context: Optional meeting ID for context
        user_id: ID of the current user
    
    Returns:
        Dict containing AI response, citations, and action buttons
    """
    try:
        from services.openai_client_manager import get_openai_client
        from models import Meeting, Task, Segment, db as models_db
        
        # Get relevant meetings and tasks for context
        recent_meetings = models_db.session.query(Meeting)\
            .filter_by(user_id=user_id)\
            .order_by(Meeting.created_at.desc())\
            .limit(10).all()
        
        recent_tasks = models_db.session.query(Task)\
            .filter_by(assigned_to=user_id)\
            .order_by(Task.created_at.desc())\
            .limit(20).all()
        
        # Build context for AI
        meeting_context = []
        for meeting in recent_meetings:
            # Get segments through the session relationship
            segments = []
            if meeting.session:
                segments = models_db.session.query(Segment)\
                    .filter_by(session_id=meeting.session.id)\
                    .order_by(Segment.created_at)\
                    .all()
            
            transcript = " ".join([seg.text for seg in segments if seg.text])
            meeting_context.append({
                'id': meeting.id,
                'title': meeting.title,
                'date': meeting.created_at.isoformat(),
                'transcript': transcript[:1000] + "..." if len(transcript) > 1000 else transcript
            })
        
        task_context = []
        for task in recent_tasks:
            task_context.append({
                'id': task.id,
                'title': task.title,
                'status': task.status,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'meeting_id': task.meeting_id
            })
        
        # Prepare AI prompt
        system_prompt = """You are Mina's AI Copilot. You help users understand their meetings, manage tasks, and find information. 

You have access to:
- Recent meeting transcripts and summaries
- Task lists and status
- Meeting decisions and action items

Always:
- Provide specific, actionable responses
- Include citations to meetings or tasks when possible
- Suggest relevant actions users can take
- Be concise but helpful

Available actions you can suggest:
- create_task: Create a new task
- mark_done: Mark a task as complete  
- delete_task: Remove a task
- add_to_calendar: Add item to calendar
- export: Export to Slack/Notion/etc
"""
        
        user_prompt = f"""
Query: {message}

Recent Meetings:
{json.dumps(meeting_context, indent=2)}

Recent Tasks: 
{json.dumps(task_context, indent=2)}

Please provide a helpful response with specific information and suggest any relevant actions.
"""
        
        # Call OpenAI
        client = get_openai_client()
        if not client:
            return {
                'text': "AI service is not configured. Please check your API key settings.",
                'citations': [],
                'suggested_actions': [],
                'timestamp': datetime.now().isoformat()
            }
            
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content or ""
        
        # Parse response for action suggestions
        actions = _extract_suggested_actions(ai_response, message)
        citations = _extract_citations(ai_response, meeting_context, task_context)
        
        return {
            'text': ai_response,
            'citations': citations,
            'suggested_actions': actions,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing copilot message: {e}")
        return {
            'text': "I'm having trouble processing your request right now. Please try again.",
            'citations': [],
            'suggested_actions': [],
            'timestamp': datetime.now().isoformat()
        }


def _extract_suggested_actions(response: str, original_query: str) -> List[Dict[str, Any]]:
    """Extract suggested actions from AI response."""
    actions = []
    
    # Simple heuristics for action suggestions
    if "overdue" in original_query.lower() or "due" in original_query.lower():
        actions.append({
            'type': 'mark_done',
            'label': 'Mark task as done',
            'icon': 'check-circle'
        })
    
    if "create" in original_query.lower() or "add" in original_query.lower():
        actions.append({
            'type': 'create_task',
            'label': 'Create new task',
            'icon': 'plus-circle'
        })
    
    if "calendar" in original_query.lower() or "schedule" in original_query.lower():
        actions.append({
            'type': 'add_to_calendar',
            'label': 'Add to calendar',
            'icon': 'calendar'
        })
    
    return actions


def _extract_citations(response: str, meetings: List[Dict], tasks: List[Dict]) -> List[Dict[str, Any]]:
    """Extract citations from AI response based on mentioned meetings/tasks."""
    citations = []
    
    # Simple citation extraction based on content matches
    for meeting in meetings:
        if meeting['title'].lower() in response.lower():
            citations.append({
                'type': 'meeting',
                'id': meeting['id'],
                'title': meeting['title'],
                'date': meeting['date']
            })
    
    for task in tasks:
        if task['title'].lower() in response.lower():
            citations.append({
                'type': 'task',
                'id': task['id'],
                'title': task['title'],
                'status': task['status']
            })
    
    return citations


def _execute_copilot_action(action: str, parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """Execute an action suggested by the Copilot."""
    try:
        from models import Task, db as models_db
        
        if action == 'create_task':
            title = parameters.get('title')
            description = parameters.get('description', '')
            due_date = parameters.get('due_date')
            
            if not title:
                return {'error': 'Task title is required'}
            
            task = Task(
                title=title,
                description=description,
                assigned_to=user_id,
                status='pending',
                due_date=datetime.fromisoformat(due_date) if due_date else None
            )
            models_db.session.add(task)
            models_db.session.commit()
            
            return {'task_id': task.id, 'message': f'Created task: {title}'}
        
        elif action == 'mark_done':
            task_id = parameters.get('task_id')
            if not task_id:
                return {'error': 'Task ID is required'}
            
            task = models_db.session.query(Task).filter_by(id=task_id, assigned_to=user_id).first()
            if not task:
                return {'error': 'Task not found'}
            
            task.status = 'completed'
            task.completed_at = datetime.now()
            models_db.session.commit()
            
            return {'message': f'Marked task as done: {task.title}'}
        
        elif action == 'delete_task':
            task_id = parameters.get('task_id')
            if not task_id:
                return {'error': 'Task ID is required'}
            
            task = models_db.session.query(Task).filter_by(id=task_id, assigned_to=user_id).first()
            if not task:
                return {'error': 'Task not found'}
            
            task_title = task.title
            models_db.session.delete(task)
            models_db.session.commit()
            
            return {'message': f'Deleted task: {task_title}'}
        
        else:
            return {'error': f'Unknown action: {action}'}
    
    except Exception as e:
        logger.error(f"Error executing action {action}: {e}")
        return {'error': 'Failed to execute action'}