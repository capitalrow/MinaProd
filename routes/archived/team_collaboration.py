"""
Team Collaboration and RBAC Routes for Mina.

This module handles API endpoints for role-based access control,
organization management, team collaboration, and user permissions.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from services.rbac_service import rbac_service

logger = logging.getLogger(__name__)

team_bp = Blueprint('team_collaboration', __name__, url_prefix='/team')


@team_bp.route('/api/organizations', methods=['GET'])
@login_required
def get_user_organizations():
    """
    Get all organizations the current user belongs to.
    
    Returns:
        JSON: List of user's organizations with membership details
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        organizations = rbac_service.get_user_organizations(current_user.id)
        
        return jsonify({
            'success': True,
            'organizations': organizations,
            'total_organizations': len(organizations)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting user organizations for {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get organizations: {str(e)}'
        }), 500


@team_bp.route('/api/organizations', methods=['POST'])
@login_required
def create_organization():
    """
    Create a new organization.
    
    Request Body:
        {
            "name": "Acme Corp",
            "slug": "acme-corp",
            "description": "A great company"
        }
    
    Returns:
        JSON: Created organization details
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        name = data.get('name', '').strip()
        slug = data.get('slug', '').strip()
        description = data.get('description', '').strip()
        
        # Validate required fields
        if not name:
            return jsonify({'success': False, 'error': 'Organization name is required'}), 400
        
        if not slug:
            return jsonify({'success': False, 'error': 'Organization slug is required'}), 400
        
        # Validate slug format (alphanumeric, dashes, underscores)
        import re
        if not re.match(r'^[a-zA-Z0-9-_]+$', slug):
            return jsonify({
                'success': False,
                'error': 'Slug can only contain letters, numbers, dashes, and underscores'
            }), 400
        
        # Create organization
        org_id = rbac_service.create_organization(
            name=name,
            slug=slug,
            created_by_user_id=current_user.id,
            description=description if description else None
        )
        
        if org_id:
            return jsonify({
                'success': True,
                'organization_id': org_id,
                'message': 'Organization created successfully'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create organization'
            }), 500
    
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating organization: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to create organization: {str(e)}'
        }), 500


@team_bp.route('/api/organizations/<int:organization_id>/teams', methods=['GET'])
@login_required
def get_organization_teams(organization_id: int):
    """
    Get all teams in an organization that the user has access to.
    
    Args:
        organization_id: Organization ID
    
    Returns:
        JSON: List of teams in the organization
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        # Check if user has permission to view teams in this organization
        if not rbac_service.check_permission(current_user.id, 'view_team', organization_id=organization_id):
            return jsonify({'success': False, 'error': 'Permission denied'}), 403
        
        teams = rbac_service.get_user_teams(current_user.id, organization_id=organization_id)
        
        return jsonify({
            'success': True,
            'teams': teams,
            'total_teams': len(teams),
            'organization_id': organization_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting teams for organization {organization_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get teams: {str(e)}'
        }), 500


@team_bp.route('/api/organizations/<int:organization_id>/teams', methods=['POST'])
@login_required
def create_team(organization_id: int):
    """
    Create a new team within an organization.
    
    Args:
        organization_id: Organization ID
    
    Request Body:
        {
            "name": "Development Team",
            "description": "Software development team",
            "type": "project",
            "is_private": false
        }
    
    Returns:
        JSON: Created team details
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        team_type = data.get('type', 'project')
        is_private = data.get('is_private', False)
        
        # Validate required fields
        if not name:
            return jsonify({'success': False, 'error': 'Team name is required'}), 400
        
        # Validate team type
        valid_types = ['department', 'project', 'cross_functional', 'temporary']
        if team_type not in valid_types:
            return jsonify({
                'success': False,
                'error': f'Invalid team type. Must be one of: {valid_types}'
            }), 400
        
        # Create team
        team_id = rbac_service.create_team(
            name=name,
            organization_id=organization_id,
            created_by_user_id=current_user.id,
            description=description if description else None,
            team_type=team_type
        )
        
        if team_id:
            return jsonify({
                'success': True,
                'team_id': team_id,
                'message': 'Team created successfully'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create team'
            }), 500
    
    except PermissionError:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    except Exception as e:
        logger.error(f"Error creating team in organization {organization_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to create team: {str(e)}'
        }), 500


@team_bp.route('/api/organizations/<int:organization_id>/invite', methods=['POST'])
@login_required
def invite_user_to_organization(organization_id: int):
    """
    Invite a user to join an organization.
    
    Args:
        organization_id: Organization ID
    
    Request Body:
        {
            "email": "user@example.com",
            "role": "member"
        }
    
    Returns:
        JSON: Invitation token and status
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        role = data.get('role', 'member')
        
        # Validate required fields
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Validate role
        valid_roles = ['organization_admin', 'team_admin', 'manager', 'member', 'guest']
        if role not in valid_roles:
            return jsonify({
                'success': False,
                'error': f'Invalid role. Must be one of: {valid_roles}'
            }), 400
        
        # Send invitation
        invitation_token = rbac_service.invite_user_to_organization(
            inviter_user_id=current_user.id,
            organization_id=organization_id,
            email=email,
            role=role
        )
        
        if invitation_token:
            return jsonify({
                'success': True,
                'invitation_token': invitation_token,
                'message': f'Invitation sent to {email}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send invitation'
            }), 500
    
    except PermissionError:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error inviting user to organization {organization_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to send invitation: {str(e)}'
        }), 500


@team_bp.route('/api/teams/<int:team_id>/invite', methods=['POST'])
@login_required
def invite_user_to_team(team_id: int):
    """
    Invite a user to join a team.
    
    Args:
        team_id: Team ID
    
    Request Body:
        {
            "email": "user@example.com",
            "role": "member"
        }
    
    Returns:
        JSON: Invitation token and status
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        role = data.get('role', 'member')
        
        # Validate required fields
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Validate role
        valid_roles = ['team_lead', 'admin', 'member', 'contributor', 'observer']
        if role not in valid_roles:
            return jsonify({
                'success': False,
                'error': f'Invalid role. Must be one of: {valid_roles}'
            }), 400
        
        # Send invitation
        invitation_token = rbac_service.invite_user_to_team(
            inviter_user_id=current_user.id,
            team_id=team_id,
            email=email,
            role=role
        )
        
        if invitation_token:
            return jsonify({
                'success': True,
                'invitation_token': invitation_token,
                'message': f'Invitation sent to {email}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send invitation'
            }), 500
    
    except PermissionError:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error inviting user to team {team_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to send invitation: {str(e)}'
        }), 500


@team_bp.route('/api/invitations/<invitation_token>/accept', methods=['POST'])
@login_required
def accept_invitation(invitation_token: str):
    """
    Accept an organization or team invitation.
    
    Args:
        invitation_token: Invitation token
    
    Returns:
        JSON: Acceptance status
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        success = rbac_service.accept_invitation(current_user.id, invitation_token)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Invitation accepted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to accept invitation'
            }), 400
    
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error accepting invitation {invitation_token}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to accept invitation: {str(e)}'
        }), 500


@team_bp.route('/api/user/roles', methods=['GET'])
@login_required
def get_user_roles():
    """
    Get all roles for the current user across organizations and teams.
    
    Returns:
        JSON: User's roles and permissions
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        roles = rbac_service.get_user_roles(current_user.id)
        
        return jsonify({
            'success': True,
            'roles': roles
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting user roles for {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get user roles: {str(e)}'
        }), 500


@team_bp.route('/api/user/permissions', methods=['POST'])
@login_required
def check_user_permission():
    """
    Check if the current user has a specific permission.
    
    Request Body:
        {
            "permission": "create_meeting",
            "organization_id": 1,
            "team_id": 2,
            "resource_id": 3
        }
    
    Returns:
        JSON: Permission check result
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        permission = data.get('permission')
        organization_id = data.get('organization_id')
        team_id = data.get('team_id')
        resource_id = data.get('resource_id')
        
        if not permission:
            return jsonify({'success': False, 'error': 'Permission name is required'}), 400
        
        # Check permission
        has_permission = rbac_service.check_permission(
            user_id=current_user.id,
            permission_name=permission,
            organization_id=organization_id,
            team_id=team_id,
            resource_id=resource_id
        )
        
        return jsonify({
            'success': True,
            'has_permission': has_permission,
            'permission': permission,
            'context': {
                'organization_id': organization_id,
                'team_id': team_id,
                'resource_id': resource_id
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error checking permission for user {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to check permission: {str(e)}'
        }), 500


@team_bp.route('/api/permissions', methods=['GET'])
@login_required
def get_available_permissions():
    """
    Get all available permissions in the system.
    
    Returns:
        JSON: List of available permissions grouped by category
    """
    try:
        # This would typically query the Permission model
        # For now, return a static list of permissions
        permissions_by_category = {
            'organization': [
                {'name': 'manage_organization', 'description': 'Manage organization settings and billing'},
                {'name': 'invite_user', 'description': 'Invite users to organization'},
                {'name': 'remove_user', 'description': 'Remove users from organization'},
                {'name': 'manage_roles', 'description': 'Manage user roles and permissions'}
            ],
            'team': [
                {'name': 'create_team', 'description': 'Create new teams'},
                {'name': 'manage_team', 'description': 'Manage team settings and members'},
                {'name': 'invite_team_member', 'description': 'Invite members to team'},
                {'name': 'remove_team_member', 'description': 'Remove members from team'}
            ],
            'meeting': [
                {'name': 'create_meeting', 'description': 'Create and start meetings'},
                {'name': 'edit_meeting', 'description': 'Edit meeting details and recordings'},
                {'name': 'delete_meeting', 'description': 'Delete meetings and recordings'},
                {'name': 'share_meeting', 'description': 'Share meetings with others'},
                {'name': 'view_meeting', 'description': 'View meetings and transcripts'}
            ],
            'task': [
                {'name': 'create_task', 'description': 'Create tasks from meetings'},
                {'name': 'edit_task', 'description': 'Edit and update tasks'},
                {'name': 'delete_task', 'description': 'Delete tasks'},
                {'name': 'assign_task', 'description': 'Assign tasks to team members'},
                {'name': 'view_task', 'description': 'View tasks and their details'}
            ],
            'analytics': [
                {'name': 'view_analytics', 'description': 'View analytics and insights'},
                {'name': 'export_data', 'description': 'Export meeting data and reports'}
            ],
            'settings': [
                {'name': 'manage_settings', 'description': 'Manage application settings'}
            ]
        }
        
        return jsonify({
            'success': True,
            'permissions': permissions_by_category
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting available permissions: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get permissions: {str(e)}'
        }), 500


@team_bp.route('/api/roles', methods=['GET'])
@login_required
def get_available_roles():
    """
    Get all available roles in the system.
    
    Returns:
        JSON: List of available roles with descriptions
    """
    try:
        roles = {
            'organization_roles': [
                {'name': 'super_admin', 'description': 'Full system access across all organizations'},
                {'name': 'organization_admin', 'description': 'Full access within the organization'},
                {'name': 'team_admin', 'description': 'Manage teams and team members'},
                {'name': 'manager', 'description': 'Manage meetings and tasks'},
                {'name': 'member', 'description': 'Standard user access'},
                {'name': 'guest', 'description': 'Limited read-only access'}
            ],
            'team_roles': [
                {'name': 'team_lead', 'description': 'Lead and manage the team'},
                {'name': 'admin', 'description': 'Administrative access within the team'},
                {'name': 'member', 'description': 'Active team member'},
                {'name': 'contributor', 'description': 'Contributes to team activities'},
                {'name': 'observer', 'description': 'Read-only access to team activities'}
            ]
        }
        
        return jsonify({
            'success': True,
            'roles': roles
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting available roles: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get roles: {str(e)}'
        }), 500


@team_bp.route('/api/initialize-permissions', methods=['POST'])
@login_required
def initialize_permissions():
    """
    Initialize default permissions and role mappings.
    This is typically called during system setup.
    
    Returns:
        JSON: Initialization status
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        # Check if user has super admin permissions
        # For now, allow any authenticated user to initialize (for testing)
        # In production, this should be restricted to super admins
        
        rbac_service.initialize_permissions()
        
        return jsonify({
            'success': True,
            'message': 'Permissions initialized successfully'
        }), 200
    
    except Exception as e:
        logger.error(f"Error initializing permissions: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to initialize permissions: {str(e)}'
        }), 500