"""
Integration Marketplace Routes for Mina.

This module handles API endpoints for the integration marketplace,
managing connections to third-party services like Slack, Jira, Notion,
and providing a comprehensive ecosystem for productivity integrations.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from services.integration_marketplace_service import integration_marketplace_service

logger = logging.getLogger(__name__)

integrations_bp = Blueprint('integrations', __name__, url_prefix='/integrations')


@integrations_bp.route('/api/marketplace', methods=['GET'])
@login_required
def get_marketplace():
    """
    Get available integrations from the marketplace.
    
    Query Parameters:
        category: Filter by integration category
        search: Search query for integration name/description
    
    Returns:
        JSON: List of available integrations
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        category = request.args.get('category')
        search_query = request.args.get('search')
        
        integrations = integration_marketplace_service.get_marketplace_integrations(
            category=category,
            search_query=search_query
        )
        
        return jsonify({
            'success': True,
            'integrations': integrations,
            'total_integrations': len(integrations),
            'filters': {
                'category': category,
                'search': search_query
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting marketplace integrations: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get marketplace integrations: {str(e)}'
        }), 500


@integrations_bp.route('/api/user-integrations', methods=['GET'])
@login_required
def get_user_integrations():
    """
    Get user's connected integrations.
    
    Returns:
        JSON: List of user's integrations with status and configuration
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        integrations = integration_marketplace_service.get_user_integrations(current_user.id)
        
        return jsonify({
            'success': True,
            'integrations': integrations,
            'total_integrations': len(integrations)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting user integrations for {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get user integrations: {str(e)}'
        }), 500


@integrations_bp.route('/api/connect/<integration_id>', methods=['POST'])
@login_required
def connect_integration(integration_id: str):
    """
    Connect to an integration.
    
    Args:
        integration_id: ID of the integration to connect
    
    Request Body:
        {
            "config": {
                "channel": "#general",
                "project_key": "PROJ"
            }
        }
    
    Returns:
        JSON: Connection status and OAuth URL if needed
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json() or {}
        config = data.get('config', {})
        
        success, result = integration_marketplace_service.connect_integration(
            user_id=current_user.id,
            integration_id=integration_id,
            config=config
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Integration connection initiated',
                'auth_url': result,
                'requires_oauth': result.startswith('http')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 400
    
    except Exception as e:
        logger.error(f"Error connecting integration {integration_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to connect integration: {str(e)}'
        }), 500


@integrations_bp.route('/api/disconnect/<user_integration_id>', methods=['POST'])
@login_required
def disconnect_integration(user_integration_id: str):
    """
    Disconnect a user's integration.
    
    Args:
        user_integration_id: ID of the user integration to disconnect
    
    Returns:
        JSON: Disconnection status
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        success = integration_marketplace_service.disconnect_integration(
            user_id=current_user.id,
            user_integration_id=user_integration_id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Integration disconnected successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to disconnect integration'
            }), 400
    
    except Exception as e:
        logger.error(f"Error disconnecting integration {user_integration_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to disconnect integration: {str(e)}'
        }), 500


@integrations_bp.route('/api/sync/<user_integration_id>', methods=['POST'])
@login_required
def sync_integration(user_integration_id: str):
    """
    Manually trigger sync for an integration.
    
    Args:
        user_integration_id: ID of the user integration to sync
    
    Returns:
        JSON: Sync status
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        success = integration_marketplace_service.sync_integration(
            user_id=current_user.id,
            user_integration_id=user_integration_id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Integration synced successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to sync integration'
            }), 400
    
    except Exception as e:
        logger.error(f"Error syncing integration {user_integration_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to sync integration: {str(e)}'
        }), 500


@integrations_bp.route('/api/send/<integration_id>', methods=['POST'])
@login_required
def send_to_integration(integration_id: str):
    """
    Send data to an integration.
    
    Args:
        integration_id: ID of the integration
    
    Request Body:
        {
            "action": "meeting_summary",
            "data": {
                "channel": "#general",
                "summary": "Meeting summary text",
                "title": "Weekly Team Meeting"
            }
        }
    
    Returns:
        JSON: Send status
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        action = data.get('action')
        payload = data.get('data', {})
        
        if not action:
            return jsonify({'success': False, 'error': 'Action is required'}), 400
        
        success = integration_marketplace_service.send_to_integration(
            user_id=current_user.id,
            integration_id=integration_id,
            action=action,
            data=payload
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Data sent to {integration_id} successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to send data to {integration_id}'
            }), 400
    
    except Exception as e:
        logger.error(f"Error sending to integration {integration_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to send to integration: {str(e)}'
        }), 500


@integrations_bp.route('/api/analytics', methods=['GET'])
@login_required
def get_integration_analytics():
    """
    Get analytics about user's integration usage.
    
    Returns:
        JSON: Integration usage analytics
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        analytics = integration_marketplace_service.get_integration_analytics(current_user.id)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting integration analytics for {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get integration analytics: {str(e)}'
        }), 500


@integrations_bp.route('/api/categories', methods=['GET'])
@login_required
def get_integration_categories():
    """
    Get available integration categories.
    
    Returns:
        JSON: List of integration categories with descriptions
    """
    try:
        categories = [
            {
                'id': 'messaging',
                'name': 'Messaging & Communication',
                'description': 'Slack, Microsoft Teams, Discord',
                'icon': 'message-circle',
                'count': 3
            },
            {
                'id': 'project_management',
                'name': 'Project Management',
                'description': 'Jira, Asana, Trello, Linear',
                'icon': 'clipboard',
                'count': 4
            },
            {
                'id': 'documentation',
                'name': 'Documentation',
                'description': 'Notion, Confluence, GitBook',
                'icon': 'book',
                'count': 3
            },
            {
                'id': 'calendar',
                'name': 'Calendar & Scheduling',
                'description': 'Google Calendar, Outlook, Calendly',
                'icon': 'calendar',
                'count': 3
            },
            {
                'id': 'storage',
                'name': 'Cloud Storage',
                'description': 'Google Drive, Dropbox, OneDrive',
                'icon': 'cloud',
                'count': 3
            },
            {
                'id': 'automation',
                'name': 'Automation',
                'description': 'Zapier, Make, IFTTT',
                'icon': 'zap',
                'count': 3
            },
            {
                'id': 'crm',
                'name': 'CRM & Sales',
                'description': 'Salesforce, HubSpot, Pipedrive',
                'icon': 'users',
                'count': 3
            },
            {
                'id': 'email',
                'name': 'Email',
                'description': 'Gmail, Outlook, SendGrid',
                'icon': 'mail',
                'count': 3
            }
        ]
        
        return jsonify({
            'success': True,
            'categories': categories
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting integration categories: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get integration categories: {str(e)}'
        }), 500


@integrations_bp.route('/api/featured', methods=['GET'])
@login_required
def get_featured_integrations():
    """
    Get featured/recommended integrations.
    
    Returns:
        JSON: List of featured integrations
    """
    try:
        # Get all integrations and filter for featured ones
        all_integrations = integration_marketplace_service.get_marketplace_integrations()
        
        # Featured integrations (high popularity, official)
        featured = [
            integration for integration in all_integrations
            if integration.get('is_official') and integration.get('popularity_score', 0) >= 80
        ]
        
        # Sort by popularity score
        featured.sort(key=lambda x: x.get('popularity_score', 0), reverse=True)
        
        # Return top 6 featured integrations
        featured = featured[:6]
        
        return jsonify({
            'success': True,
            'featured_integrations': featured,
            'total_featured': len(featured)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting featured integrations: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get featured integrations: {str(e)}'
        }), 500


@integrations_bp.route('/api/templates', methods=['GET'])
@login_required
def get_integration_templates():
    """
    Get pre-configured integration templates.
    
    Query Parameters:
        use_case: Filter by use case
    
    Returns:
        JSON: List of integration templates
    """
    try:
        use_case = request.args.get('use_case')
        
        templates = [
            {
                'id': 'dev_team_starter',
                'name': 'Development Team Starter',
                'description': 'Perfect setup for software development teams',
                'use_case': 'development',
                'integrations': ['slack', 'jira', 'github', 'notion'],
                'estimated_setup_time': '15 minutes',
                'popularity': 95
            },
            {
                'id': 'marketing_team',
                'name': 'Marketing Team Essentials',
                'description': 'Essential integrations for marketing teams',
                'use_case': 'marketing',
                'integrations': ['slack', 'asana', 'google_drive', 'hubspot'],
                'estimated_setup_time': '10 minutes',
                'popularity': 88
            },
            {
                'id': 'remote_team',
                'name': 'Remote Team Collaboration',
                'description': 'Enhanced collaboration for remote teams',
                'use_case': 'remote_work',
                'integrations': ['microsoft_teams', 'notion', 'google_calendar', 'zoom'],
                'estimated_setup_time': '20 minutes',
                'popularity': 92
            },
            {
                'id': 'startup_basic',
                'name': 'Startup Basic Package',
                'description': 'Essential tools for growing startups',
                'use_case': 'startup',
                'integrations': ['slack', 'trello', 'google_drive'],
                'estimated_setup_time': '8 minutes',
                'popularity': 85
            },
            {
                'id': 'enterprise_suite',
                'name': 'Enterprise Suite',
                'description': 'Comprehensive integrations for large organizations',
                'use_case': 'enterprise',
                'integrations': ['microsoft_teams', 'jira', 'confluence', 'salesforce', 'zapier'],
                'estimated_setup_time': '45 minutes',
                'popularity': 78
            }
        ]
        
        # Filter by use case if provided
        if use_case:
            templates = [t for t in templates if t['use_case'] == use_case]
        
        # Sort by popularity
        templates.sort(key=lambda x: x['popularity'], reverse=True)
        
        return jsonify({
            'success': True,
            'templates': templates,
            'total_templates': len(templates),
            'filter': {'use_case': use_case}
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting integration templates: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get integration templates: {str(e)}'
        }), 500


@integrations_bp.route('/api/setup-template', methods=['POST'])
@login_required
def setup_integration_template():
    """
    Set up multiple integrations from a template.
    
    Request Body:
        {
            "template_id": "dev_team_starter",
            "custom_config": {
                "slack_channel": "#dev-team",
                "jira_project": "DEV"
            }
        }
    
    Returns:
        JSON: Setup status and next steps
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        template_id = data.get('template_id')
        custom_config = data.get('custom_config', {})
        
        if not template_id:
            return jsonify({'success': False, 'error': 'Template ID is required'}), 400
        
        # Mock template setup - in real implementation, this would:
        # 1. Get template configuration
        # 2. Initiate connections for each integration
        # 3. Apply custom configuration
        # 4. Return setup progress and next steps
        
        setup_results = {
            'template_id': template_id,
            'total_integrations': 4,
            'initiated_connections': 4,
            'completed_connections': 0,
            'next_steps': [
                {
                    'integration': 'slack',
                    'action': 'Complete OAuth authorization',
                    'url': 'https://slack.com/oauth/authorize?...',
                    'status': 'pending'
                },
                {
                    'integration': 'jira',
                    'action': 'Complete OAuth authorization',
                    'url': 'https://auth.atlassian.com/authorize?...',
                    'status': 'pending'
                }
            ],
            'estimated_completion_time': '15 minutes'
        }
        
        return jsonify({
            'success': True,
            'message': 'Template setup initiated',
            'results': setup_results
        }), 200
    
    except Exception as e:
        logger.error(f"Error setting up integration template: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to setup template: {str(e)}'
        }), 500


@integrations_bp.route('/api/webhooks/<integration_id>', methods=['POST'])
def handle_integration_webhook(integration_id: str):
    """
    Handle incoming webhooks from integrations.
    
    Args:
        integration_id: ID of the integration sending the webhook
    
    Returns:
        JSON: Webhook processing status
    """
    try:
        # Verify webhook signature if applicable
        signature = request.headers.get('X-Hub-Signature-256')
        
        # Get webhook payload
        payload = request.get_json()
        
        # Log webhook for debugging
        logger.info(f"Received webhook from {integration_id}: {payload}")
        
        # Process webhook based on integration type
        if integration_id == 'slack':
            # Handle Slack events (mentions, slash commands, etc.)
            event_type = payload.get('type')
            if event_type == 'url_verification':
                return jsonify({'challenge': payload.get('challenge')}), 200
        
        elif integration_id == 'jira':
            # Handle Jira events (issue updates, etc.)
            webhook_event = payload.get('webhookEvent')
            logger.info(f"Jira webhook event: {webhook_event}")
        
        elif integration_id == 'github':
            # Handle GitHub events (commits, PRs, etc.)
            event_type = request.headers.get('X-GitHub-Event')
            logger.info(f"GitHub webhook event: {event_type}")
        
        return jsonify({
            'success': True,
            'message': 'Webhook processed successfully'
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing webhook from {integration_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to process webhook: {str(e)}'
        }), 500