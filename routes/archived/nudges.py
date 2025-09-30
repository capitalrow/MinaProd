"""
Smart Nudges and Follow-up Suggestions Routes for Mina.

This module handles API endpoints for smart nudges, follow-up suggestions,
and user behavior tracking for productivity enhancements.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from services.smart_nudges_service import smart_nudges_service, NudgeChannel, Priority

logger = logging.getLogger(__name__)

nudges_bp = Blueprint('nudges', __name__, url_prefix='/nudges')


@nudges_bp.route('/api/generate', methods=['POST'])
@login_required
def generate_nudges():
    """
    Generate smart nudges for the current user.
    
    Request Body:
        {
            "refresh": false
        }
    
    Returns:
        JSON: List of smart nudges
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json() or {}
        refresh = data.get('refresh', False)
        
        # Clear cache if refresh is requested
        if refresh and current_user.id in smart_nudges_service.nudges_cache:
            del smart_nudges_service.nudges_cache[current_user.id]
        
        # Generate nudges
        nudges = smart_nudges_service.generate_nudges(current_user.id)
        
        # Convert nudges to JSON-serializable format
        nudges_data = []
        for nudge in nudges:
            nudges_data.append({
                'id': nudge.id,
                'type': nudge.type.value,
                'priority': nudge.priority.value,
                'title': nudge.title,
                'message': nudge.message,
                'action_text': nudge.action_text,
                'action_url': nudge.action_url,
                'context': nudge.context,
                'related_entities': nudge.related_entities,
                'suggested_channels': [ch.value for ch in nudge.suggested_channels],
                'created_at': nudge.created_at.isoformat(),
                'expires_at': nudge.expires_at.isoformat() if nudge.expires_at else None,
                'dismissed': nudge.dismissed,
                'acted_upon': nudge.acted_upon
            })
        
        return jsonify({
            'success': True,
            'nudges': nudges_data,
            'total_nudges': len(nudges_data),
            'user_id': current_user.id
        }), 200
    
    except Exception as e:
        logger.error(f"Error generating nudges for user {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to generate nudges: {str(e)}'
        }), 500


@nudges_bp.route('/api/active', methods=['GET'])
@login_required
def get_active_nudges():
    """
    Get active nudges for the current user.
    
    Query Parameters:
        channel: Optional channel filter (in_app, email, push, slack)
    
    Returns:
        JSON: List of active nudges
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        channel_param = request.args.get('channel')
        channel = None
        
        if channel_param:
            try:
                channel = NudgeChannel(channel_param)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid channel. Must be one of: {[ch.value for ch in NudgeChannel]}'
                }), 400
        
        # Get active nudges
        active_nudges = smart_nudges_service.get_active_nudges(current_user.id, channel)
        
        # Convert to JSON format
        nudges_data = []
        for nudge in active_nudges:
            nudges_data.append({
                'id': nudge.id,
                'type': nudge.type.value,
                'priority': nudge.priority.value,
                'title': nudge.title,
                'message': nudge.message,
                'action_text': nudge.action_text,
                'action_url': nudge.action_url,
                'context': nudge.context,
                'related_entities': nudge.related_entities,
                'suggested_channels': [ch.value for ch in nudge.suggested_channels],
                'created_at': nudge.created_at.isoformat(),
                'expires_at': nudge.expires_at.isoformat() if nudge.expires_at else None
            })
        
        return jsonify({
            'success': True,
            'nudges': nudges_data,
            'total_active': len(nudges_data),
            'channel_filter': channel_param
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting active nudges for user {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get active nudges: {str(e)}'
        }), 500


@nudges_bp.route('/api/nudges/<nudge_id>/dismiss', methods=['POST'])
@login_required
def dismiss_nudge(nudge_id: str):
    """
    Dismiss a specific nudge.
    
    Args:
        nudge_id: ID of the nudge to dismiss
    
    Returns:
        JSON: Success status
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        success = smart_nudges_service.dismiss_nudge(current_user.id, nudge_id)
        
        if success:
            # Update user patterns
            smart_nudges_service.update_user_patterns(current_user.id, 'dismiss_nudge')
            
            return jsonify({
                'success': True,
                'message': 'Nudge dismissed successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Nudge not found'
            }), 404
    
    except Exception as e:
        logger.error(f"Error dismissing nudge {nudge_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to dismiss nudge: {str(e)}'
        }), 500


@nudges_bp.route('/api/nudges/<nudge_id>/act', methods=['POST'])
@login_required
def act_on_nudge(nudge_id: str):
    """
    Mark a nudge as acted upon.
    
    Args:
        nudge_id: ID of the nudge acted upon
    
    Returns:
        JSON: Success status
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        success = smart_nudges_service.mark_nudge_acted(current_user.id, nudge_id)
        
        if success:
            # Update user patterns
            smart_nudges_service.update_user_patterns(current_user.id, 'act_on_nudge')
            
            return jsonify({
                'success': True,
                'message': 'Nudge marked as acted upon'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Nudge not found'
            }), 404
    
    except Exception as e:
        logger.error(f"Error marking nudge {nudge_id} as acted upon: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to mark nudge as acted upon: {str(e)}'
        }), 500


@nudges_bp.route('/api/follow-up-suggestions/<int:meeting_id>', methods=['GET'])
@login_required
def get_follow_up_suggestions(meeting_id: int):
    """
    Get follow-up suggestions for a specific meeting.
    
    Args:
        meeting_id: ID of the meeting/session
    
    Returns:
        JSON: List of follow-up suggestions
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        # Generate follow-up suggestions
        suggestions = smart_nudges_service.generate_follow_up_suggestions(meeting_id)
        
        # Convert to JSON format
        suggestions_data = []
        for suggestion in suggestions:
            suggestions_data.append({
                'id': suggestion.id,
                'title': suggestion.title,
                'description': suggestion.description,
                'suggested_action': suggestion.suggested_action,
                'context': suggestion.context,
                'confidence': suggestion.confidence,
                'related_meeting_id': suggestion.related_meeting_id,
                'related_entities': suggestion.related_entities,
                'suggested_due_date': suggestion.suggested_due_date.isoformat() if suggestion.suggested_due_date else None,
                'priority': suggestion.priority.value,
                'category': suggestion.category,
                'created_at': suggestion.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'suggestions': suggestions_data,
            'total_suggestions': len(suggestions_data),
            'meeting_id': meeting_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting follow-up suggestions for meeting {meeting_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get follow-up suggestions: {str(e)}'
        }), 500


@nudges_bp.route('/api/follow-up-suggestions', methods=['GET'])
@login_required
def get_all_follow_up_suggestions():
    """
    Get all follow-up suggestions for the current user.
    
    Query Parameters:
        category: Optional category filter
        priority: Optional priority filter
    
    Returns:
        JSON: List of follow-up suggestions
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        category_filter = request.args.get('category')
        priority_filter = request.args.get('priority')
        
        # Get all suggestions for the user
        all_suggestions = smart_nudges_service.follow_up_suggestions.get(current_user.id, [])
        
        # Apply filters
        filtered_suggestions = all_suggestions
        
        if category_filter:
            filtered_suggestions = [s for s in filtered_suggestions if s.category == category_filter]
        
        if priority_filter:
            try:
                priority_enum = Priority(priority_filter)
                filtered_suggestions = [s for s in filtered_suggestions if s.priority == priority_enum]
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid priority. Must be one of: {[p.value for p in Priority]}'
                }), 400
        
        # Convert to JSON format
        suggestions_data = []
        for suggestion in filtered_suggestions:
            suggestions_data.append({
                'id': suggestion.id,
                'title': suggestion.title,
                'description': suggestion.description,
                'suggested_action': suggestion.suggested_action,
                'context': suggestion.context,
                'confidence': suggestion.confidence,
                'related_meeting_id': suggestion.related_meeting_id,
                'related_entities': suggestion.related_entities,
                'suggested_due_date': suggestion.suggested_due_date.isoformat() if suggestion.suggested_due_date else None,
                'priority': suggestion.priority.value,
                'category': suggestion.category,
                'created_at': suggestion.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'suggestions': suggestions_data,
            'total_suggestions': len(suggestions_data),
            'filters': {
                'category': category_filter,
                'priority': priority_filter
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting follow-up suggestions for user {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get follow-up suggestions: {str(e)}'
        }), 500


@nudges_bp.route('/api/user-patterns', methods=['GET'])
@login_required
def get_user_patterns():
    """
    Get user behavior patterns.
    
    Returns:
        JSON: User behavior patterns
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        patterns = smart_nudges_service.user_patterns.get(current_user.id)
        
        if patterns:
            patterns_data = {
                'user_id': patterns.user_id,
                'preferred_nudge_times': patterns.preferred_nudge_times,
                'preferred_channels': [ch.value for ch in patterns.preferred_channels],
                'response_rate_by_type': patterns.response_rate_by_type,
                'avg_response_time_hours': patterns.avg_response_time_hours,
                'activity_patterns': patterns.activity_patterns,
                'last_updated': patterns.last_updated.isoformat() if patterns.last_updated else None
            }
        else:
            patterns_data = {
                'user_id': current_user.id,
                'preferred_nudge_times': [9, 14, 17],  # Default times
                'preferred_channels': ['in_app'],
                'response_rate_by_type': {},
                'avg_response_time_hours': 2.0,
                'activity_patterns': {},
                'last_updated': None
            }
        
        return jsonify({
            'success': True,
            'patterns': patterns_data
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting user patterns for user {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get user patterns: {str(e)}'
        }), 500


@nudges_bp.route('/api/user-patterns', methods=['PUT'])
@login_required
def update_user_patterns():
    """
    Update user behavior patterns.
    
    Request Body:
        {
            "preferred_nudge_times": [9, 14, 17],
            "preferred_channels": ["in_app", "email"]
        }
    
    Returns:
        JSON: Success status
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate and update patterns
        preferred_times = data.get('preferred_nudge_times', [])
        preferred_channels = data.get('preferred_channels', [])
        
        # Validate times (0-23)
        if preferred_times and not all(0 <= t <= 23 for t in preferred_times):
            return jsonify({
                'success': False,
                'error': 'preferred_nudge_times must be hours between 0 and 23'
            }), 400
        
        # Validate channels
        if preferred_channels:
            try:
                channel_enums = [NudgeChannel(ch) for ch in preferred_channels]
            except ValueError as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid channel: {str(e)}'
                }), 400
        
        # Update or create user patterns
        from services.smart_nudges_service import UserBehaviorPattern
        
        if current_user.id in smart_nudges_service.user_patterns:
            patterns = smart_nudges_service.user_patterns[current_user.id]
            if preferred_times:
                patterns.preferred_nudge_times = preferred_times
            if preferred_channels:
                patterns.preferred_channels = channel_enums
            patterns.last_updated = datetime.now()
        else:
            patterns = UserBehaviorPattern(
                user_id=current_user.id,
                preferred_nudge_times=preferred_times or [9, 14, 17],
                preferred_channels=channel_enums if preferred_channels else [NudgeChannel.IN_APP],
                response_rate_by_type={},
                avg_response_time_hours=2.0,
                activity_patterns={}
            )
            smart_nudges_service.user_patterns[current_user.id] = patterns
        
        return jsonify({
            'success': True,
            'message': 'User patterns updated successfully'
        }), 200
    
    except Exception as e:
        logger.error(f"Error updating user patterns for user {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to update user patterns: {str(e)}'
        }), 500


@nudges_bp.route('/api/nudge-types', methods=['GET'])
@login_required
def get_nudge_types():
    """
    Get available nudge types and their descriptions.
    
    Returns:
        JSON: Nudge types with descriptions
    """
    try:
        nudge_types = {
            'overdue_task': {
                'name': 'Overdue Task',
                'description': 'Tasks that are past their due date',
                'priority': 'urgent'
            },
            'upcoming_deadline': {
                'name': 'Upcoming Deadline',
                'description': 'Tasks with approaching deadlines',
                'priority': 'high'
            },
            'missing_follow_up': {
                'name': 'Missing Follow-up',
                'description': 'Meetings without follow-up actions',
                'priority': 'medium'
            },
            'inactive_project': {
                'name': 'Inactive Project',
                'description': 'Projects without recent activity',
                'priority': 'low'
            },
            'meeting_preparation': {
                'name': 'Meeting Preparation',
                'description': 'Reminders to prepare for upcoming meetings',
                'priority': 'medium'
            },
            'action_review': {
                'name': 'Action Review',
                'description': 'Periodic review of completed actions',
                'priority': 'low'
            },
            'decision_confirmation': {
                'name': 'Decision Confirmation',
                'description': 'Confirmation of important decisions made',
                'priority': 'medium'
            },
            'collaboration_reminder': {
                'name': 'Collaboration Reminder',
                'description': 'Reminders about team collaboration opportunities',
                'priority': 'low'
            }
        }
        
        return jsonify({
            'success': True,
            'nudge_types': nudge_types
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting nudge types: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get nudge types: {str(e)}'
        }), 500