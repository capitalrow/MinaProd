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
            "context": "meeting_id_optional",
            "session_id": "optional_session_id"
        }
    
    Returns:
        JSON: Copilot response with citations and action buttons
    """
    try:
        data = request.get_json() or {}
        message = data.get('message', '').strip()
        context = data.get('context')
        session_id = data.get('session_id')  # For conversation continuity
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        # Process the message with AI
        response = _process_copilot_message(message, context, current_user.id, session_id)
        
        return jsonify({
            'success': True,
            'response': response
        }), 200
    
    except Exception as e:
        import traceback
        logger.error(f"Error processing copilot message: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
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


def _process_copilot_message(message: str, context: Optional[str], user_id: int, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a message using AI and meeting context with conversation history.
    
    Args:
        message: User's natural language query
        context: Optional meeting ID for context
        user_id: ID of the current user
        session_id: Optional session ID for conversation continuity
    
    Returns:
        Dict containing AI response, citations, and action buttons
    """
    try:
        from services.openai_client_manager import get_openai_client
        from models import Meeting, Task, Segment, CopilotConversation, db as models_db
        
        # Generate session_id if not provided
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        # Get current user to access workspace_id and preferences
        from models import User
        user = models_db.session.get(User, user_id)
        if not user or not user.workspace_id:
            return {
                'text': "Unable to access your workspace. Please try logging in again.",
                'citations': [],
                'suggested_actions': [],
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
        
        # Load user preferences if available
        user_preferences = {}
        if user.preferences:
            try:
                user_preferences = json.loads(user.preferences)
            except:
                pass
        
        # Load recent conversation history for context continuity (last 10 messages in this session)
        conversation_history = models_db.session.query(CopilotConversation)\
            .filter_by(user_id=user_id, session_id=session_id)\
            .order_by(CopilotConversation.created_at.desc())\
            .limit(10).all()
        conversation_history.reverse()  # Oldest first for chronological order
        
        # Get relevant meetings and tasks for context
        recent_meetings = models_db.session.query(Meeting)\
            .filter_by(workspace_id=user.workspace_id)\
            .order_by(Meeting.created_at.desc())\
            .limit(10).all()
        
        recent_tasks = models_db.session.query(Task)\
            .filter_by(assigned_to_id=user_id)\
            .order_by(Task.created_at.desc())\
            .limit(20).all()
        
        # Build context for AI with insights
        from models import Summary
        meeting_context = []
        for meeting in recent_meetings:
            meeting_data = {
                'id': meeting.id,
                'title': meeting.title,
                'date': meeting.created_at.isoformat(),
                'status': meeting.status
            }
            
            # Add AI insights if available from Summary
            if meeting.session:
                summary = models_db.session.query(Summary)\
                    .filter_by(session_id=meeting.session.id)\
                    .first()
                
                if summary:
                    # Add summary text
                    if summary.brief_summary:
                        meeting_data['summary'] = summary.brief_summary
                    elif summary.summary_md:
                        meeting_data['summary'] = summary.summary_md[:300]  # Truncate if needed
                    
                    # Add actions (top 3)
                    if summary.actions:
                        meeting_data['actions'] = summary.actions[:3] if isinstance(summary.actions, list) else []
                    
                    # Add decisions (top 2)
                    if summary.decisions:
                        meeting_data['decisions'] = summary.decisions[:2] if isinstance(summary.decisions, list) else []
                else:
                    # Fallback to transcript snippet if no summary
                    segments = models_db.session.query(Segment)\
                        .filter_by(session_id=meeting.session.id)\
                        .order_by(Segment.created_at)\
                        .limit(10).all()  # Just first 10 segments for context
                    
                    transcript = " ".join([seg.text for seg in segments if seg.text])
                    if transcript:
                        meeting_data['transcript_snippet'] = transcript[:500] + "..." if len(transcript) > 500 else transcript
            
            meeting_context.append(meeting_data)
        
        task_context = []
        for task in recent_tasks:
            task_data = {
                'id': task.id,
                'title': task.title,
                'status': task.status,
                'priority': task.priority if hasattr(task, 'priority') else 'medium',
                'due_date': task.due_date.isoformat() if task.due_date else None
            }
            if task.description:
                task_data['description'] = task.description[:200]  # Brief description
            if task.meeting_id:
                task_data['meeting_id'] = task.meeting_id
            task_context.append(task_data)
        
        # Prepare AI prompt with user preferences awareness
        system_prompt = """You are Mina's AI Copilot. You help users understand their meetings, manage tasks, and find information. 

You have access to:
- Recent meeting transcripts and summaries
- Task lists and status
- Meeting decisions and action items
- Conversation history for context continuity
- User preferences and work patterns

Always:
- Provide specific, actionable responses
- Include citations to meetings or tasks when possible
- Suggest relevant actions users can take
- Be concise but helpful
- Remember context from earlier in the conversation

Available actions you can suggest:
- create_task: Create a new task
- mark_done: Mark a task as complete  
- delete_task: Remove a task
- add_to_calendar: Add item to calendar
- export: Export to Slack/Notion/etc
"""
        
        # Add user preferences to system prompt if available
        if user_preferences:
            pref_lines = []
            if user_preferences.get('timezone'):
                pref_lines.append(f"- User timezone: {user_preferences['timezone']}")
            if user_preferences.get('work_hours'):
                pref_lines.append(f"- Work hours: {user_preferences['work_hours']}")
            if user_preferences.get('communication_style'):
                pref_lines.append(f"- Communication style: {user_preferences['communication_style']}")
            
            if pref_lines:
                system_prompt += "\n\nUser Preferences:\n" + "\n".join(pref_lines)
        
        # Build context string with token management
        context_parts = []
        context_parts.append(f"User Query: {message}\n")
        
        if meeting_context:
            context_parts.append(f"\nRecent Meetings ({len(meeting_context)}):")
            for m in meeting_context[:5]:  # Limit to 5 most recent
                context_parts.append(f"- {m['title']} ({m['date']})")
                if 'summary' in m:
                    context_parts.append(f"  Summary: {m['summary'][:200]}")
                if 'actions' in m and m['actions']:
                    action_list = [str(a.get('task', a)) if isinstance(a, dict) else str(a) for a in m['actions'][:3]]
                    context_parts.append(f"  Actions: {', '.join(action_list)}")
                if 'decisions' in m and m['decisions']:
                    decision_list = [str(d.get('decision', d)) if isinstance(d, dict) else str(d) for d in m['decisions'][:2]]
                    context_parts.append(f"  Decisions: {', '.join(decision_list)}")
                if 'transcript_snippet' in m:
                    context_parts.append(f"  Context: {m['transcript_snippet'][:150]}...")
        
        if task_context:
            context_parts.append(f"\n\nRecent Tasks ({len(task_context)}):")
            for t in task_context[:10]:  # Limit to 10 most recent
                due_status = f" (Due: {t['due_date']})" if t['due_date'] else ""
                context_parts.append(f"- [{t['status']}] {t['title']}{due_status}")
                if 'description' in t:
                    context_parts.append(f"  {t['description'][:100]}")
        
        user_prompt = "\n".join(context_parts) + "\n\nPlease provide a helpful, specific response based on this context. Include citations to meetings or tasks when relevant, and suggest actionable next steps."
        
        # Call OpenAI with conversation history
        client = get_openai_client()
        if not client:
            return {
                'text': "AI service is not configured. Please check your API key settings.",
                'citations': [],
                'suggested_actions': [],
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
        
        # Build messages array with conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history for context
        for conv in conversation_history:
            messages.append({
                "role": conv.role,
                "content": conv.message
            })
        
        # Add current user message
        messages.append({"role": "user", "content": user_prompt})
            
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=800,  # Increased for better responses
            temperature=0.7,
            presence_penalty=0.1,  # Encourage diverse responses
            frequency_penalty=0.1  # Reduce repetition
        )
        
        ai_response = response.choices[0].message.content or ""
        
        # Parse response for action suggestions and follow-up questions
        actions = _extract_suggested_actions(ai_response, message)
        citations = _extract_citations(ai_response, meeting_context, task_context)
        follow_up_questions = _generate_follow_up_questions(message, ai_response, meeting_context, task_context)
        
        # Save conversation to database for future context
        try:
            # Save user message
            user_conv = CopilotConversation(
                user_id=user_id,
                role='user',
                message=message,
                session_id=session_id,
                context_filter=context,
                prompt_tokens=response.usage.prompt_tokens if hasattr(response, 'usage') else None,
                completion_tokens=0
            )
            models_db.session.add(user_conv)
            
            # Save assistant response
            assistant_conv = CopilotConversation(
                user_id=user_id,
                role='assistant',
                message=ai_response,
                session_id=session_id,
                context_filter=context,
                prompt_tokens=0,
                completion_tokens=response.usage.completion_tokens if hasattr(response, 'usage') else None
            )
            models_db.session.add(assistant_conv)
            models_db.session.commit()
            
            logger.debug(f"Saved conversation for user {user_id}, session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save conversation history: {e}")
            # Don't fail the response if saving fails
            models_db.session.rollback()
        
        return {
            'text': ai_response,
            'citations': citations,
            'suggested_actions': actions,
            'follow_up_questions': follow_up_questions,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Error in _process_copilot_message: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            'text': "I'm having trouble processing your request right now. Please try again.",
            'citations': [],
            'suggested_actions': [],
            'follow_up_questions': [],
            'session_id': session_id if 'session_id' in locals() else None,
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


def _generate_follow_up_questions(original_query: str, ai_response: str, meetings: List[Dict], tasks: List[Dict]) -> List[str]:
    """
    Generate contextual follow-up questions based on the conversation.
    
    Args:
        original_query: The user's original question
        ai_response: The AI's response
        meetings: List of meeting context
        tasks: List of task context
    
    Returns:
        List of 3-5 suggested follow-up questions
    """
    follow_ups = []
    query_lower = original_query.lower()
    response_lower = ai_response.lower()
    
    # Question generation based on query type
    
    # Meeting-related queries
    if any(word in query_lower for word in ['meeting', 'discussed', 'decision', 'agenda']):
        if 'decision' in response_lower or 'decided' in response_lower:
            follow_ups.append("What were the alternatives considered?")
        if len(meetings) > 0:
            follow_ups.append("Who were the key participants in these discussions?")
            follow_ups.append("Are there any follow-up meetings scheduled?")
        if 'action' in response_lower or 'task' in response_lower:
            follow_ups.append("What are the timelines for these action items?")
    
    # Task-related queries
    elif any(word in query_lower for word in ['task', 'due', 'overdue', 'action']):
        if 'overdue' in response_lower or 'late' in response_lower:
            follow_ups.append("Which tasks are highest priority?")
            follow_ups.append("Are there any blockers preventing completion?")
        if len(tasks) > 0:
            follow_ups.append("Show me tasks by priority")
            follow_ups.append("What tasks are due this week?")
        follow_ups.append("Can you create a summary of pending tasks?")
    
    # Summary/overview queries
    elif any(word in query_lower for word in ['summary', 'overview', 'status', 'progress']):
        follow_ups.append("What are the main risks or concerns?")
        follow_ups.append("Are we on track with our goals?")
        if len(meetings) > 1:
            follow_ups.append("How does this compare to last week?")
        follow_ups.append("What should I focus on next?")
    
    # Time-based queries
    elif any(word in query_lower for word in ['today', 'week', 'yesterday', 'month']):
        follow_ups.append("What's coming up tomorrow?")
        follow_ups.append("Show me last week's highlights")
        follow_ups.append("What are this month's key achievements?")
    
    # Risk/blocker queries
    elif any(word in query_lower for word in ['risk', 'blocker', 'issue', 'problem']):
        follow_ups.append("What mitigation strategies were discussed?")
        follow_ups.append("Who is responsible for resolving these?")
        follow_ups.append("Are there any dependencies?")
    
    # General fallback questions
    else:
        if meetings:
            follow_ups.append("Tell me more about recent meetings")
        if tasks:
            follow_ups.append("What tasks need my attention?")
        follow_ups.append("Summarize this week's progress")
        follow_ups.append("What decisions were made recently?")
    
    # Limit to 5 questions and ensure no duplicates
    follow_ups = list(dict.fromkeys(follow_ups))[:5]
    
    # If we have less than 3, add generic useful questions
    if len(follow_ups) < 3:
        generic_questions = [
            "What are the key takeaways?",
            "Who should I follow up with?",
            "Are there any pending approvals?",
            "Show me related action items",
            "What's the status of ongoing projects?"
        ]
        for q in generic_questions:
            if q not in follow_ups and len(follow_ups) < 5:
                follow_ups.append(q)
    
    return follow_ups


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
                assigned_to_id=user_id,
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
            
            task = models_db.session.query(Task).filter_by(id=task_id, assigned_to_id=user_id).first()
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
            
            task = models_db.session.query(Task).filter_by(id=task_id, assigned_to_id=user_id).first()
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