"""
Role-Based Access Control (RBAC) Service for Mina.

This module provides comprehensive role-based access control functionality
including permission checking, role management, and team collaboration features.
"""

import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from sqlalchemy import and_, or_

logger = logging.getLogger(__name__)


class RBACService:
    """Service for managing role-based access control and team collaboration."""
    
    def __init__(self):
        self.permission_cache: Dict[str, Dict[str, Any]] = {}
        self.role_hierarchy = {
            'super_admin': ['organization_admin', 'team_admin', 'manager', 'member', 'guest'],
            'organization_admin': ['team_admin', 'manager', 'member', 'guest'],
            'team_admin': ['manager', 'member', 'guest'],
            'manager': ['member', 'guest'],
            'member': ['guest'],
            'guest': []
        }
    
    def check_permission(self, user_id: int, permission_name: str, 
                        organization_id: Optional[int] = None, 
                        team_id: Optional[int] = None,
                        resource_id: Optional[int] = None) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user_id: User ID to check
            permission_name: Name of the permission to check
            organization_id: Optional organization context
            team_id: Optional team context
            resource_id: Optional resource ID for resource-specific permissions
            
        Returns:
            Boolean indicating if user has permission
        """
        try:
            from models.organization import (
                OrganizationMembership, TeamMembership, Permission, RolePermission
            )
            from app import db
            
            # Get user's organization role
            org_membership = None
            if organization_id:
                org_membership = db.session.query(OrganizationMembership).filter_by(
                    user_id=user_id,
                    organization_id=organization_id,
                    is_active=True
                ).first()
            
            # Get user's team role
            team_membership = None
            if team_id:
                team_membership = db.session.query(TeamMembership).filter_by(
                    user_id=user_id,
                    team_id=team_id,
                    is_active=True
                ).first()
            
            # Get permission
            permission = db.session.query(Permission).filter_by(name=permission_name).first()
            if not permission:
                logger.warning(f"Permission '{permission_name}' not found")
                return False
            
            # Check super admin (has all permissions)
            if org_membership and org_membership.role.value == 'super_admin':
                return True
            
            # Check role-based permissions
            roles_to_check = []
            
            # Add organization role
            if org_membership:
                roles_to_check.append(org_membership.role.value)
                # Add inherited roles
                roles_to_check.extend(self.role_hierarchy.get(org_membership.role.value, []))
            
            # Add team role
            if team_membership:
                team_role = f"team_{team_membership.role.value}"
                roles_to_check.append(team_role)
            
            # Check if any role has the permission
            for role in roles_to_check:
                role_permission = db.session.query(RolePermission).filter(
                    and_(
                        RolePermission.role == role,
                        RolePermission.permission_id == permission.id,
                        RolePermission.granted == True,
                        or_(
                            RolePermission.organization_id == organization_id,
                            RolePermission.organization_id.is_(None)
                        ),
                        or_(
                            RolePermission.team_id == team_id,
                            RolePermission.team_id.is_(None)
                        )
                    )
                ).first()
                
                if role_permission:
                    return True
            
            # Check resource-specific permissions if resource_id provided
            if resource_id:
                return self._check_resource_permission(
                    user_id, permission_name, resource_id, organization_id, team_id
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking permission {permission_name} for user {user_id}: {e}")
            return False
    
    def get_user_roles(self, user_id: int) -> Dict[str, Any]:
        """Get all roles for a user across organizations and teams."""
        try:
            from models.organization import OrganizationMembership, TeamMembership
            from app import db
            
            # Get organization memberships
            org_memberships = db.session.query(OrganizationMembership).filter_by(
                user_id=user_id, is_active=True
            ).all()
            
            # Get team memberships
            team_memberships = db.session.query(TeamMembership).filter_by(
                user_id=user_id, is_active=True
            ).all()
            
            return {
                'organization_roles': [
                    {
                        'organization_id': mem.organization_id,
                        'role': mem.role.value,
                        'joined_at': mem.joined_at.isoformat() if mem.joined_at else None
                    }
                    for mem in org_memberships
                ],
                'team_roles': [
                    {
                        'team_id': mem.team_id,
                        'role': mem.role.value,
                        'joined_at': mem.joined_at.isoformat() if mem.joined_at else None
                    }
                    for mem in team_memberships
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting user roles for {user_id}: {e}")
            return {'organization_roles': [], 'team_roles': []}
    
    def create_organization(self, name: str, slug: str, created_by_user_id: int, 
                          description: Optional[str] = None) -> Optional[int]:
        """Create a new organization and make the creator an admin."""
        try:
            from models.organization import Organization, OrganizationMembership, UserRole
            from app import db
            
            # Check if slug is unique
            existing = db.session.query(Organization).filter_by(slug=slug).first()
            if existing:
                raise ValueError(f"Organization slug '{slug}' already exists")
            
            # Create organization
            org = Organization(
                name=name,
                slug=slug,
                description=description
            )
            db.session.add(org)
            db.session.flush()  # Get the ID
            
            # Create admin membership for creator
            membership = OrganizationMembership(
                user_id=created_by_user_id,
                organization_id=org.id,
                role=UserRole.ORGANIZATION_ADMIN,
                is_active=True,
                joined_at=datetime.utcnow()
            )
            db.session.add(membership)
            db.session.commit()
            
            logger.info(f"Created organization '{name}' with ID {org.id}")
            return org.id
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating organization: {e}")
            return None
    
    def create_team(self, name: str, organization_id: int, created_by_user_id: int,
                   description: Optional[str] = None, team_type: str = 'project') -> Optional[int]:
        """Create a new team within an organization."""
        try:
            from models.organization import Team, TeamMembership, TeamType, TeamRole
            from app import db
            
            # Verify user has permission to create teams in this organization
            if not self.check_permission(created_by_user_id, 'create_team', organization_id=organization_id):
                raise PermissionError("User does not have permission to create teams")
            
            # Create team
            team = Team(
                name=name,
                organization_id=organization_id,
                created_by_user_id=created_by_user_id,
                description=description,
                type=TeamType(team_type)
            )
            db.session.add(team)
            db.session.flush()
            
            # Create team lead membership for creator
            membership = TeamMembership(
                user_id=created_by_user_id,
                team_id=team.id,
                role=TeamRole.TEAM_LEAD,
                is_active=True,
                joined_at=datetime.utcnow()
            )
            db.session.add(membership)
            db.session.commit()
            
            logger.info(f"Created team '{name}' with ID {team.id}")
            return team.id
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating team: {e}")
            return None
    
    def invite_user_to_organization(self, inviter_user_id: int, organization_id: int,
                                  email: str, role: str = 'member') -> Optional[str]:
        """Invite a user to join an organization."""
        try:
            from models.organization import OrganizationMembership, UserRole
            from models.user import User
            from app import db
            
            # Check inviter permissions
            if not self.check_permission(inviter_user_id, 'invite_user', organization_id=organization_id):
                raise PermissionError("User does not have permission to invite users")
            
            # Check if user already exists
            user = db.session.query(User).filter_by(email=email).first()
            
            # Generate invitation token
            token = self._generate_invitation_token()
            expires_at = datetime.utcnow() + timedelta(days=7)
            
            if user:
                # Check if user is already a member
                existing_membership = db.session.query(OrganizationMembership).filter_by(
                    user_id=user.id,
                    organization_id=organization_id
                ).first()
                
                if existing_membership and existing_membership.is_active:
                    raise ValueError("User is already a member of this organization")
                
                # Create or update membership
                if existing_membership:
                    existing_membership.role = UserRole(role)
                    existing_membership.is_active = False  # Will be activated when accepted
                    existing_membership.invitation_token = token
                    existing_membership.invitation_expires_at = expires_at
                    existing_membership.invited_by_user_id = inviter_user_id
                else:
                    membership = OrganizationMembership(
                        user_id=user.id,
                        organization_id=organization_id,
                        role=UserRole(role),
                        is_active=False,
                        invitation_token=token,
                        invitation_expires_at=expires_at,
                        invited_by_user_id=inviter_user_id
                    )
                    db.session.add(membership)
            else:
                # Create pending membership for email
                membership = OrganizationMembership(
                    organization_id=organization_id,
                    role=UserRole(role),
                    is_active=False,
                    invitation_token=token,
                    invitation_expires_at=expires_at,
                    invited_by_user_id=inviter_user_id
                )
                db.session.add(membership)
            
            db.session.commit()
            
            # TODO: Send invitation email
            logger.info(f"Invited user {email} to organization {organization_id}")
            return token
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error inviting user to organization: {e}")
            return None
    
    def invite_user_to_team(self, inviter_user_id: int, team_id: int,
                          email: str, role: str = 'member') -> Optional[str]:
        """Invite a user to join a team."""
        try:
            from models.organization import TeamMembership, TeamRole, Team
            from models.user import User
            from app import db
            
            # Get team to check organization
            team = db.session.query(Team).filter_by(id=team_id).first()
            if not team:
                raise ValueError("Team not found")
            
            # Check inviter permissions
            if not self.check_permission(inviter_user_id, 'invite_team_member', 
                                       organization_id=team.organization_id, team_id=team_id):
                raise PermissionError("User does not have permission to invite team members")
            
            # Check if user already exists
            user = db.session.query(User).filter_by(email=email).first()
            
            # Generate invitation token
            token = self._generate_invitation_token()
            expires_at = datetime.utcnow() + timedelta(days=7)
            
            if user:
                # Check if user is already a team member
                existing_membership = db.session.query(TeamMembership).filter_by(
                    user_id=user.id,
                    team_id=team_id
                ).first()
                
                if existing_membership and existing_membership.is_active:
                    raise ValueError("User is already a member of this team")
                
                # Create or update membership
                if existing_membership:
                    existing_membership.role = TeamRole(role)
                    existing_membership.is_active = False
                    existing_membership.invitation_token = token
                    existing_membership.invitation_expires_at = expires_at
                    existing_membership.invited_by_user_id = inviter_user_id
                else:
                    membership = TeamMembership(
                        user_id=user.id,
                        team_id=team_id,
                        role=TeamRole(role),
                        is_active=False,
                        invitation_token=token,
                        invitation_expires_at=expires_at,
                        invited_by_user_id=inviter_user_id
                    )
                    db.session.add(membership)
            else:
                # Create pending membership for email
                membership = TeamMembership(
                    team_id=team_id,
                    role=TeamRole(role),
                    is_active=False,
                    invitation_token=token,
                    invitation_expires_at=expires_at,
                    invited_by_user_id=inviter_user_id
                )
                db.session.add(membership)
            
            db.session.commit()
            
            # TODO: Send invitation email
            logger.info(f"Invited user {email} to team {team_id}")
            return token
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error inviting user to team: {e}")
            return None
    
    def accept_invitation(self, user_id: int, invitation_token: str) -> bool:
        """Accept an organization or team invitation."""
        try:
            from models.organization import OrganizationMembership, TeamMembership
            from app import db
            
            # Check organization invitation
            org_membership = db.session.query(OrganizationMembership).filter_by(
                invitation_token=invitation_token
            ).first()
            
            if org_membership:
                if org_membership.invitation_expires_at < datetime.utcnow():
                    raise ValueError("Invitation has expired")
                
                org_membership.user_id = user_id
                org_membership.is_active = True
                org_membership.joined_at = datetime.utcnow()
                org_membership.invitation_token = None
                org_membership.invitation_expires_at = None
                
                db.session.commit()
                logger.info(f"User {user_id} accepted organization invitation")
                return True
            
            # Check team invitation
            team_membership = db.session.query(TeamMembership).filter_by(
                invitation_token=invitation_token
            ).first()
            
            if team_membership:
                if team_membership.invitation_expires_at < datetime.utcnow():
                    raise ValueError("Invitation has expired")
                
                team_membership.user_id = user_id
                team_membership.is_active = True
                team_membership.joined_at = datetime.utcnow()
                team_membership.invitation_token = None
                team_membership.invitation_expires_at = None
                
                db.session.commit()
                logger.info(f"User {user_id} accepted team invitation")
                return True
            
            raise ValueError("Invalid invitation token")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error accepting invitation: {e}")
            return False
    
    def get_user_organizations(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all organizations a user belongs to."""
        try:
            from models.organization import Organization, OrganizationMembership
            from app import db
            
            query = db.session.query(Organization, OrganizationMembership).join(
                OrganizationMembership
            ).filter(
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.is_active == True
            )
            
            results = []
            for org, membership in query.all():
                org_dict = org.to_dict()
                org_dict['membership'] = membership.to_dict()
                results.append(org_dict)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting user organizations for {user_id}: {e}")
            return []
    
    def get_user_teams(self, user_id: int, organization_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all teams a user belongs to, optionally filtered by organization."""
        try:
            from models.organization import Team, TeamMembership
            from app import db
            
            query = db.session.query(Team, TeamMembership).join(
                TeamMembership
            ).filter(
                TeamMembership.user_id == user_id,
                TeamMembership.is_active == True
            )
            
            if organization_id:
                query = query.filter(Team.organization_id == organization_id)
            
            results = []
            for team, membership in query.all():
                team_dict = team.to_dict()
                team_dict['membership'] = membership.to_dict()
                results.append(team_dict)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting user teams for {user_id}: {e}")
            return []
    
    def initialize_permissions(self):
        """Initialize default permissions in the database."""
        try:
            from models.organization import Permission, RolePermission
            from app import db
            
            # Define default permissions
            default_permissions = [
                # Organization permissions
                ('manage_organization', 'Manage organization settings and billing', 'organization'),
                ('invite_user', 'Invite users to organization', 'organization'),
                ('remove_user', 'Remove users from organization', 'organization'),
                ('manage_roles', 'Manage user roles and permissions', 'organization'),
                
                # Team permissions
                ('create_team', 'Create new teams', 'team'),
                ('manage_team', 'Manage team settings and members', 'team'),
                ('invite_team_member', 'Invite members to team', 'team'),
                ('remove_team_member', 'Remove members from team', 'team'),
                
                # Meeting permissions
                ('create_meeting', 'Create and start meetings', 'meeting'),
                ('edit_meeting', 'Edit meeting details and recordings', 'meeting'),
                ('delete_meeting', 'Delete meetings and recordings', 'meeting'),
                ('share_meeting', 'Share meetings with others', 'meeting'),
                ('view_meeting', 'View meetings and transcripts', 'meeting'),
                
                # Task permissions
                ('create_task', 'Create tasks from meetings', 'task'),
                ('edit_task', 'Edit and update tasks', 'task'),
                ('delete_task', 'Delete tasks', 'task'),
                ('assign_task', 'Assign tasks to team members', 'task'),
                ('view_task', 'View tasks and their details', 'task'),
                
                # Analytics permissions
                ('view_analytics', 'View analytics and insights', 'analytics'),
                ('export_data', 'Export meeting data and reports', 'analytics'),
                
                # Settings permissions
                ('manage_settings', 'Manage application settings', 'settings'),
            ]
            
            # Create permissions if they don't exist
            for name, description, category in default_permissions:
                existing = db.session.query(Permission).filter_by(name=name).first()
                if not existing:
                    permission = Permission(
                        name=name,
                        description=description,
                        category=category
                    )
                    db.session.add(permission)
            
            db.session.commit()
            
            # Define default role permissions
            self._initialize_role_permissions()
            
            logger.info("Permissions initialized successfully")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error initializing permissions: {e}")
    
    def _initialize_role_permissions(self):
        """Initialize default role-permission mappings."""
        try:
            from models.organization import Permission, RolePermission
            from app import db
            
            # Get all permissions
            permissions = {p.name: p.id for p in db.session.query(Permission).all()}
            
            # Define role-permission mappings
            role_permissions = {
                'super_admin': list(permissions.keys()),  # All permissions
                'organization_admin': [
                    'manage_organization', 'invite_user', 'remove_user', 'manage_roles',
                    'create_team', 'manage_team', 'invite_team_member', 'remove_team_member',
                    'create_meeting', 'edit_meeting', 'delete_meeting', 'share_meeting', 'view_meeting',
                    'create_task', 'edit_task', 'delete_task', 'assign_task', 'view_task',
                    'view_analytics', 'export_data', 'manage_settings'
                ],
                'team_admin': [
                    'manage_team', 'invite_team_member', 'remove_team_member',
                    'create_meeting', 'edit_meeting', 'share_meeting', 'view_meeting',
                    'create_task', 'edit_task', 'assign_task', 'view_task',
                    'view_analytics'
                ],
                'manager': [
                    'create_meeting', 'edit_meeting', 'share_meeting', 'view_meeting',
                    'create_task', 'edit_task', 'assign_task', 'view_task',
                    'view_analytics'
                ],
                'member': [
                    'create_meeting', 'view_meeting', 'create_task', 'edit_task', 'view_task'
                ],
                'guest': [
                    'view_meeting', 'view_task'
                ],
                # Team-specific roles
                'team_team_lead': [
                    'manage_team', 'invite_team_member',
                    'create_meeting', 'edit_meeting', 'share_meeting', 'view_meeting',
                    'create_task', 'edit_task', 'assign_task', 'view_task'
                ],
                'team_admin': [
                    'invite_team_member', 'create_meeting', 'edit_meeting', 'share_meeting', 'view_meeting',
                    'create_task', 'edit_task', 'assign_task', 'view_task'
                ],
                'team_member': [
                    'create_meeting', 'view_meeting', 'create_task', 'edit_task', 'view_task'
                ],
                'team_contributor': [
                    'view_meeting', 'create_task', 'edit_task', 'view_task'
                ],
                'team_observer': [
                    'view_meeting', 'view_task'
                ]
            }
            
            # Create role permissions
            for role, permission_names in role_permissions.items():
                for permission_name in permission_names:
                    if permission_name in permissions:
                        # Check if already exists
                        existing = db.session.query(RolePermission).filter_by(
                            role=role,
                            permission_id=permissions[permission_name]
                        ).first()
                        
                        if not existing:
                            role_perm = RolePermission(
                                role=role,
                                permission_id=permissions[permission_name],
                                granted=True
                            )
                            db.session.add(role_perm)
            
            db.session.commit()
            logger.info("Role permissions initialized successfully")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error initializing role permissions: {e}")
    
    def _check_resource_permission(self, user_id: int, permission_name: str, 
                                 resource_id: int, organization_id: Optional[int] = None,
                                 team_id: Optional[int] = None) -> bool:
        """Check resource-specific permissions (e.g., meeting ownership)."""
        try:
            # Check if user owns the resource
            if permission_name in ['edit_meeting', 'delete_meeting']:
                from models.session import Session
                from app import db
                
                session = db.session.query(Session).filter_by(id=resource_id, user_id=user_id).first()
                if session:
                    return True
            
            elif permission_name in ['edit_task', 'delete_task']:
                from models.task import Task
                from app import db
                
                task = db.session.query(Task).filter_by(id=resource_id, user_id=user_id).first()
                if task:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking resource permission: {e}")
            return False
    
    def _generate_invitation_token(self) -> str:
        """Generate a secure invitation token."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))


# Global service instance
rbac_service = RBACService()