"""
API endpoints for managing Copilot prompt templates.
Implements T3.3: Template library with system and user-defined templates.
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, CopilotTemplate

logger = logging.getLogger(__name__)

copilot_templates_bp = Blueprint('copilot_templates', __name__, url_prefix='/copilot/api/templates')


# ============================================
# System Templates (Pre-defined)
# ============================================

SYSTEM_TEMPLATES = [
    {
        'name': 'Summarize Meeting',
        'description': 'Get a comprehensive summary of a recent meeting',
        'prompt': 'Summarize the key points, decisions, and action items from [meeting name or "today\'s meeting"]',
        'category': 'meetings',
        'icon': 'document-text'
    },
    {
        'name': 'Extract Action Items',
        'description': 'List all action items and tasks',
        'prompt': 'Show me all action items from recent meetings with their assignees and due dates',
        'category': 'tasks',
        'icon': 'clipboard-list'
    },
    {
        'name': 'Draft Follow-up Email',
        'description': 'Create a follow-up email based on meeting notes',
        'prompt': 'Draft a follow-up email for [meeting] summarizing key decisions and next steps',
        'category': 'email',
        'icon': 'mail'
    },
    {
        'name': 'Weekly Summary',
        'description': 'Overview of this week\'s meetings and progress',
        'prompt': 'Summarize this week\'s meetings, key decisions, and overall progress',
        'category': 'analysis',
        'icon': 'calendar'
    },
    {
        'name': 'Risk Assessment',
        'description': 'Identify risks and concerns from meetings',
        'prompt': 'What are the main risks, blockers, or concerns mentioned in recent meetings?',
        'category': 'analysis',
        'icon': 'exclamation-triangle'
    },
    {
        'name': 'Decision Log',
        'description': 'List all decisions made in meetings',
        'prompt': 'Show me all decisions made in the last [week/month] with context',
        'category': 'meetings',
        'icon': 'lightbulb'
    },
    {
        'name': 'What\'s Due Today',
        'description': 'Show tasks due today',
        'prompt': 'What tasks and action items are due today?',
        'category': 'tasks',
        'icon': 'clock'
    },
    {
        'name': 'Meeting Prep',
        'description': 'Prepare for an upcoming meeting',
        'prompt': 'Help me prepare for [meeting name]. What were the outcomes of similar past meetings?',
        'category': 'meetings',
        'icon': 'presentation-chart-bar'
    }
]


@copilot_templates_bp.route('/', methods=['GET'])
@login_required
def get_templates():
    """
    Get all templates (system + user-defined) for current user.
    """
    try:
        category = request.args.get('category')
        favorites_only = request.args.get('favorites') == 'true'
        
        # Get user templates
        query = CopilotTemplate.query.filter(
            (CopilotTemplate.user_id == current_user.id) | (CopilotTemplate.is_system == True)
        )
        
        if category:
            query = query.filter_by(category=category)
        
        if favorites_only:
            query = query.filter_by(is_favorite=True)
        
        templates = query.order_by(
            CopilotTemplate.is_system.desc(),
            CopilotTemplate.usage_count.desc()
        ).all()
        
        return jsonify({
            'templates': [t.to_dict() for t in templates],
            'categories': ['general', 'meetings', 'tasks', 'analysis', 'email']
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        return jsonify({'error': 'Failed to fetch templates'}), 500


@copilot_templates_bp.route('/', methods=['POST'])
@login_required
def create_template():
    """
    Create a new user-defined template.
    """
    try:
        data = request.get_json()
        
        if not data.get('name') or not data.get('prompt'):
            return jsonify({'error': 'Name and prompt are required'}), 400
        
        template = CopilotTemplate(
            name=data['name'],
            description=data.get('description'),
            prompt=data['prompt'],
            category=data.get('category', 'general'),
            icon=data.get('icon'),
            user_id=current_user.id,
            is_system=False
        )
        
        db.session.add(template)
        db.session.commit()
        
        logger.info(f"User {current_user.id} created template: {template.name}")
        return jsonify(template.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating template: {e}")
        return jsonify({'error': 'Failed to create template'}), 500


@copilot_templates_bp.route('/<int:template_id>', methods=['PUT'])
@login_required
def update_template(template_id):
    """
    Update an existing user template.
    """
    try:
        template = CopilotTemplate.query.filter_by(
            id=template_id,
            user_id=current_user.id
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found or not owned by user'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            template.name = data['name']
        if 'description' in data:
            template.description = data['description']
        if 'prompt' in data:
            template.prompt = data['prompt']
        if 'category' in data:
            template.category = data['category']
        if 'icon' in data:
            template.icon = data['icon']
        if 'is_favorite' in data:
            template.is_favorite = data['is_favorite']
        
        template.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(template.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating template: {e}")
        return jsonify({'error': 'Failed to update template'}), 500


@copilot_templates_bp.route('/<int:template_id>', methods=['DELETE'])
@login_required
def delete_template(template_id):
    """
    Delete a user template.
    """
    try:
        template = CopilotTemplate.query.filter_by(
            id=template_id,
            user_id=current_user.id
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found or not owned by user'}), 404
        
        db.session.delete(template)
        db.session.commit()
        
        return jsonify({'message': 'Template deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting template: {e}")
        return jsonify({'error': 'Failed to delete template'}), 500


@copilot_templates_bp.route('/<int:template_id>/use', methods=['POST'])
@login_required
def use_template(template_id):
    """
    Mark a template as used (increment usage counter).
    """
    try:
        template = CopilotTemplate.query.filter(
            CopilotTemplate.id == template_id,
            (CopilotTemplate.user_id == current_user.id) | (CopilotTemplate.is_system == True)
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        template.increment_usage()
        db.session.commit()
        
        return jsonify({'message': 'Usage recorded', 'usage_count': template.usage_count}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error recording template usage: {e}")
        return jsonify({'error': 'Failed to record usage'}), 500


@copilot_templates_bp.route('/seed', methods=['POST'])
@login_required
def seed_system_templates():
    """
    Seed system templates (admin only or first-time setup).
    """
    try:
        # Check if system templates already exist
        existing_count = CopilotTemplate.query.filter_by(is_system=True).count()
        if existing_count > 0:
            return jsonify({'message': f'{existing_count} system templates already exist'}), 200
        
        # Create system templates
        for template_data in SYSTEM_TEMPLATES:
            template = CopilotTemplate(
                name=template_data['name'],
                description=template_data['description'],
                prompt=template_data['prompt'],
                category=template_data['category'],
                icon=template_data['icon'],
                is_system=True,
                user_id=None
            )
            db.session.add(template)
        
        db.session.commit()
        
        logger.info(f"Seeded {len(SYSTEM_TEMPLATES)} system templates")
        return jsonify({
            'message': f'Successfully seeded {len(SYSTEM_TEMPLATES)} system templates'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error seeding templates: {e}")
        return jsonify({'error': 'Failed to seed templates'}), 500
