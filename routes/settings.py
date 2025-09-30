"""
Settings management routes for Mina.

This module handles user settings, preferences, and configuration management.
"""

import json
import logging
from typing import Dict, Any, Optional

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user

from models.user import User
from models.workspace import Workspace

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('/')
@login_required
def settings_dashboard():
    """
    Display the main settings dashboard.
    
    Returns:
        Rendered settings template with current user preferences
    """
    logger.info(f"🔍 Settings dashboard accessed - User authenticated: {current_user.is_authenticated}")
    
    try:
        from app import db
        
        # Type check current_user
        if not current_user.is_authenticated:
            logger.warning(f"⚠️ User not authenticated, redirecting to login")
            return redirect(url_for('auth.login'))
        
        logger.info(f"✅ Loading settings for user {current_user.id} ({current_user.username})")
        
        # Get current user preferences  
        user_preferences = _get_user_preferences(current_user)
        logger.debug(f"📝 User preferences loaded: {list(user_preferences.keys())}")
        
        # Get workspace settings if user has access
        workspace_settings = _get_workspace_settings(current_user)
        
        logger.info(f"✅ Rendering settings dashboard template")
        
        return render_template('settings/dashboard.html',
                             user_preferences=user_preferences,
                             workspace_settings=workspace_settings,
                             page_title="Settings")
    
    except Exception as e:
        logger.error(f"❌ Error loading settings dashboard: {e}", exc_info=True)
        flash('Failed to load settings. Please try again.', 'error')
        logger.error(f"🔄 Redirecting to dashboard due to error")
        return redirect(url_for('dashboard.index'))


@settings_bp.route('/api/preferences', methods=['GET'])
@login_required
def get_preferences():
    """
    Get user preferences as JSON.
    
    Returns:
        JSON: Current user preferences
    """
    try:
        from app import db
        
        # Type check current_user
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
            
        preferences = _get_user_preferences(current_user)
        
        return jsonify({
            'success': True,
            'preferences': preferences
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving preferences for user {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve preferences'
        }), 500


@settings_bp.route('/api/preferences', methods=['POST'])
@login_required
def update_preferences():
    """
    Update user preferences.
    
    Request Body:
        {
            "category": "transcription|summary|tasks|audio|privacy|integrations|general",
            "settings": {
                "key": "value",
                ...
            }
        }
    
    Returns:
        JSON: Success/error response
    """
    try:
        data = request.get_json() or {}
        category = data.get('category')
        settings = data.get('settings', {})
        
        if not category:
            return jsonify({
                'success': False,
                'error': 'Category is required'
            }), 400
        
        # Validate category
        valid_categories = [
            'transcription', 'summary', 'tasks', 'audio', 
            'privacy', 'integrations', 'general', 'ui'
        ]
        
        if category not in valid_categories:
            return jsonify({
                'success': False,
                'error': f'Invalid category. Must be one of: {", ".join(valid_categories)}'
            }), 400
        
        from app import db
        
        # Type check current_user
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Get current preferences
        current_preferences = _get_user_preferences(current_user)
        
        # Update the specific category
        current_preferences[category] = {
            **current_preferences.get(category, {}),
            **settings
        }
        
        # Save to database
        current_user.preferences = json.dumps(current_preferences)
        db.session.commit()
        
        logger.info(f"Updated {category} preferences for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': f'{category.title()} preferences updated successfully',
            'category': category,
            'updated_settings': settings
        }), 200
    
    except Exception as e:
        logger.error(f"Error updating preferences for user {current_user.id}: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update preferences'
        }), 500


@settings_bp.route('/api/preferences/reset', methods=['POST'])
@login_required
def reset_preferences():
    """
    Reset user preferences to defaults.
    
    Request Body:
        {
            "category": "category_name" (optional - if not provided, resets all)
        }
    
    Returns:
        JSON: Success/error response
    """
    try:
        data = request.get_json() or {}
        category = data.get('category')
        
        # Get default preferences
        default_preferences = _get_default_preferences()
        
        from app import db
        
        # Type check current_user
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        if category:
            # Reset specific category
            current_preferences = _get_user_preferences(current_user)
            current_preferences[category] = default_preferences.get(category, {})
            preferences_to_save = current_preferences
            message = f'{category.title()} preferences reset to defaults'
        else:
            # Reset all preferences
            preferences_to_save = default_preferences
            message = 'All preferences reset to defaults'
        
        # Save to database
        current_user.preferences = json.dumps(preferences_to_save)
        db.session.commit()
        
        logger.info(f"Reset preferences for user {current_user.id}: {category or 'all'}")
        
        return jsonify({
            'success': True,
            'message': message,
            'preferences': preferences_to_save
        }), 200
    
    except Exception as e:
        logger.error(f"Error resetting preferences for user {current_user.id}: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to reset preferences'
        }), 500


@settings_bp.route('/api/export', methods=['GET'])
@login_required
def export_settings():
    """
    Export user settings as JSON file.
    
    Returns:
        JSON: User settings for export
    """
    try:
        from app import db
        
        # Type check current_user
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
            
        preferences = _get_user_preferences(current_user)
        
        export_data = {
            'user_id': current_user.id,
            'username': current_user.username,
            'export_timestamp': db.func.now(),
            'preferences': preferences,
            'version': '1.0'
        }
        
        logger.info(f"Exported settings for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'data': export_data
        }), 200
    
    except Exception as e:
        logger.error(f"Error exporting settings for user {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to export settings'
        }), 500


def _get_user_preferences(user: User) -> Dict[str, Any]:
    """
    Get user preferences with defaults for missing values.
    
    Args:
        user: User object
        
    Returns:
        Dictionary of user preferences with defaults
    """
    try:
        if user.preferences:
            preferences = json.loads(user.preferences)
        else:
            preferences = {}
        
        # Merge with defaults to ensure all categories exist
        default_preferences = _get_default_preferences()
        
        for category, defaults in default_preferences.items():
            if category not in preferences:
                preferences[category] = defaults
            else:
                # Merge with defaults to ensure all keys exist
                preferences[category] = {**defaults, **preferences[category]}
        
        return preferences
    
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Invalid preferences JSON for user {user.id}: {e}")
        return _get_default_preferences()


def _get_workspace_settings(user: User) -> Optional[Dict[str, Any]]:
    """
    Get workspace settings for the user.
    
    Args:
        user: User object
        
    Returns:
        Dictionary of workspace settings or None
    """
    try:
        # For now, return None as workspace functionality is not fully implemented
        # In the future, this would query the user's workspace
        return None
    
    except Exception as e:
        logger.warning(f"Error retrieving workspace settings for user {user.id}: {e}")
        return None


def _get_default_preferences() -> Dict[str, Any]:
    """
    Get default user preferences.
    
    Returns:
        Dictionary of default preferences organized by category
    """
    return {
        'transcription': {
            'language': 'auto',
            'quality': 'high',
            'speaker_detection': True,
            'confidence_threshold': 0.8,
            'punctuation': True,
            'profanity_filter': False,
            'auto_save': True,
            'real_time_display': True
        },
        'summary': {
            'default_level': 'standard',
            'default_style': 'executive',
            'auto_generate': True,
            'auto_generate_delay': 30,  # seconds after session ends
            'include_actions': True,
            'include_decisions': True,
            'include_risks': True,
            'email_summary': False
        },
        'tasks': {
            'default_priority': 'medium',
            'auto_assign': False,
            'due_date_suggestions': True,
            'notification_reminders': True,
            'calendar_integration': False,
            'task_categories': ['action', 'follow-up', 'research', 'decision']
        },
        'audio': {
            'quality': 'high',
            'noise_reduction': True,
            'echo_cancellation': True,
            'auto_gain_control': True,
            'voice_activity_detection': True,
            'buffer_size': 'medium',
            'format': 'webm'
        },
        'privacy': {
            'data_retention_days': 365,
            'share_analytics': False,
            'recording_consent': True,
            'delete_on_export': False,
            'encrypt_storage': True,
            'anonymous_usage_stats': True
        },
        'integrations': {
            'google_calendar': False,
            'outlook_calendar': False,
            'slack_notifications': False,
            'teams_integration': False,
            'notion_sync': False,
            'linear_tasks': False,
            'jira_integration': False
        },
        'ui': {
            'theme': 'dark',
            'sidebar_collapsed': False,
            'auto_refresh': True,
            'keyboard_shortcuts': True,
            'tooltips': True,
            'animations': True,
            'compact_mode': False,
            'language': 'en'
        },
        'general': {
            'timezone': 'auto',
            'date_format': 'MM/DD/YYYY',
            'time_format': '12h',
            'first_day_of_week': 'monday',
            'notifications': True,
            'email_notifications': True,
            'browser_notifications': True
        }
    }