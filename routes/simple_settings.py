"""
Simple Settings Page - No Authentication Required
Temporary solution until full authentication system is implemented
"""

from flask import Blueprint, render_template, request, jsonify
import logging

logger = logging.getLogger(__name__)

simple_settings_bp = Blueprint('simple_settings', __name__, url_prefix='/settings')


@simple_settings_bp.route('/')
def settings_dashboard():
    """
    Display the settings dashboard without authentication.
    """
    try:
        # Default settings for demo purposes
        default_settings = {
            'transcription': {
                'language': 'auto',
                'quality': 'high',
                'speaker_detection': True,
                'confidence_threshold': 0.8
            },
            'ui': {
                'theme': 'dark',
                'animations': True,
                'sidebar_collapsed': False
            },
            'audio': {
                'quality': 'high',
                'noise_reduction': True,
                'echo_cancellation': True
            },
            'privacy': {
                'data_retention_days': 365,
                'encrypt_storage': True
            }
        }
        
        logger.info("Loading simple settings dashboard")
        
        return render_template('settings/dashboard.html',
                             user_preferences=default_settings,
                             workspace_settings=None,
                             page_title="Settings")
    
    except Exception as e:
        logger.error(f"Error loading settings dashboard: {e}")
        return render_template('error.html', 
                             error_code=500, 
                             error_message="Settings temporarily unavailable"), 500


@simple_settings_bp.route('/api/preferences', methods=['GET'])
def get_preferences():
    """Get current preferences."""
    try:
        # Mock preferences for demo
        preferences = {
            'transcription': {
                'language': 'auto',
                'quality': 'high',
                'speaker_detection': True,
                'confidence_threshold': 0.8
            },
            'ui': {
                'theme': 'dark',
                'animations': True,
                'sidebar_collapsed': False
            }
        }
        
        return jsonify({
            'success': True,
            'preferences': preferences
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving preferences: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve preferences'
        }), 500


@simple_settings_bp.route('/api/preferences', methods=['POST'])
def update_preferences():
    """Update preferences (mock)."""
    try:
        data = request.get_json() or {}
        category = data.get('category')
        settings = data.get('settings', {})
        
        if not category:
            return jsonify({
                'success': False,
                'error': 'Category is required'
            }), 400
        
        logger.info(f"Mock update for {category} preferences: {settings}")
        
        return jsonify({
            'success': True,
            'message': f'{category.title()} preferences updated successfully',
            'category': category,
            'updated_settings': settings
        }), 200
    
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update preferences'
        }), 500