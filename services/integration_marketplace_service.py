"""
Integration Marketplace Service for Mina.

This module provides comprehensive integration capabilities with popular
productivity tools like Slack, Jira, Notion, and other third-party services
to create a seamless workflow ecosystem.
"""

import logging
import json
import secrets
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import requests

logger = logging.getLogger(__name__)


class IntegrationType(Enum):
    """Types of integrations available."""
    MESSAGING = "messaging"  # Slack, Microsoft Teams
    PROJECT_MANAGEMENT = "project_management"  # Jira, Asana, Trello
    DOCUMENTATION = "documentation"  # Notion, Confluence
    CALENDAR = "calendar"  # Google Calendar, Outlook
    CRM = "crm"  # Salesforce, HubSpot
    STORAGE = "storage"  # Google Drive, Dropbox
    AUTOMATION = "automation"  # Zapier, Make
    EMAIL = "email"  # Gmail, Outlook


class IntegrationStatus(Enum):
    """Integration connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    EXPIRED = "expired"


@dataclass
class Integration:
    """Integration definition and metadata."""
    id: str
    name: str
    description: str
    provider: str
    type: IntegrationType
    icon_url: str
    website_url: str
    is_official: bool
    supported_features: List[str]
    setup_complexity: str  # 'easy', 'medium', 'advanced'
    pricing_model: str  # 'free', 'freemium', 'paid'
    popularity_score: int
    last_updated: datetime
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'provider': self.provider,
            'type': self.type.value,
            'icon_url': self.icon_url,
            'website_url': self.website_url,
            'is_official': self.is_official,
            'supported_features': self.supported_features,
            'setup_complexity': self.setup_complexity,
            'pricing_model': self.pricing_model,
            'popularity_score': self.popularity_score,
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class UserIntegration:
    """User's integration connection."""
    id: str
    user_id: int
    integration_id: str
    status: IntegrationStatus
    config: Dict[str, Any]
    credentials: Dict[str, Any]  # Encrypted
    last_sync: Optional[datetime]
    sync_frequency: str  # 'real_time', 'hourly', 'daily'
    enabled_features: List[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self, include_credentials: bool = False):
        """Convert to dictionary, optionally including credentials."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'integration_id': self.integration_id,
            'status': self.status.value,
            'config': self.config,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'sync_frequency': self.sync_frequency,
            'enabled_features': self.enabled_features,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_credentials:
            data['credentials'] = self.credentials
        
        return data


class IntegrationMarketplaceService:
    """Service for managing integrations and marketplace functionality."""
    
    def __init__(self):
        self.integrations_registry: Dict[str, Integration] = {}
        self.user_integrations: Dict[str, UserIntegration] = {}
        self._initialize_integrations()
    
    def get_marketplace_integrations(self, category: Optional[str] = None,
                                   search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available integrations from the marketplace."""
        try:
            integrations = list(self.integrations_registry.values())
            
            # Filter by category
            if category:
                try:
                    integration_type = IntegrationType(category)
                    integrations = [i for i in integrations if i.type == integration_type]
                except ValueError:
                    pass
            
            # Filter by search query
            if search_query:
                query_lower = search_query.lower()
                integrations = [
                    i for i in integrations
                    if query_lower in i.name.lower() 
                    or query_lower in i.description.lower()
                    or query_lower in i.provider.lower()
                ]
            
            # Sort by popularity and official status
            integrations.sort(key=lambda x: (x.is_official, x.popularity_score), reverse=True)
            
            return [integration.to_dict() for integration in integrations]
            
        except Exception as e:
            logger.error(f"Error getting marketplace integrations: {e}")
            return []
    
    def get_user_integrations(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's connected integrations."""
        try:
            user_integrations = [
                integration for integration in self.user_integrations.values()
                if integration.user_id == user_id
            ]
            
            # Enrich with integration metadata
            enriched_integrations = []
            for user_integration in user_integrations:
                integration_meta = self.integrations_registry.get(user_integration.integration_id)
                if integration_meta:
                    data = user_integration.to_dict()
                    data['integration'] = integration_meta.to_dict()
                    enriched_integrations.append(data)
            
            return enriched_integrations
            
        except Exception as e:
            logger.error(f"Error getting user integrations for {user_id}: {e}")
            return []
    
    def connect_integration(self, user_id: int, integration_id: str,
                          config: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Initiate connection to an integration."""
        try:
            # Check if integration exists
            if integration_id not in self.integrations_registry:
                return False, "Integration not found"
            
            integration = self.integrations_registry[integration_id]
            
            # Check if user already has this integration
            existing = self._get_user_integration(user_id, integration_id)
            if existing and existing.status in [IntegrationStatus.CONNECTED, IntegrationStatus.CONNECTING]:
                return False, "Integration already connected or connecting"
            
            # Create user integration
            user_integration_id = f"{user_id}_{integration_id}_{secrets.token_hex(8)}"
            user_integration = UserIntegration(
                id=user_integration_id,
                user_id=user_id,
                integration_id=integration_id,
                status=IntegrationStatus.CONNECTING,
                config=config or {},
                credentials={},
                last_sync=None,
                sync_frequency='real_time',
                enabled_features=integration.supported_features,
                error_message=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Store user integration
            self.user_integrations[user_integration_id] = user_integration
            
            # Initiate OAuth flow or connection process
            auth_url = self._initiate_integration_auth(integration, user_integration)
            
            return True, auth_url
            
        except Exception as e:
            logger.error(f"Error connecting integration {integration_id} for user {user_id}: {e}")
            return False, f"Connection failed: {str(e)}"
    
    def disconnect_integration(self, user_id: int, user_integration_id: str) -> bool:
        """Disconnect a user's integration."""
        try:
            user_integration = self.user_integrations.get(user_integration_id)
            
            if not user_integration or user_integration.user_id != user_id:
                return False
            
            # Revoke credentials with the provider
            self._revoke_integration_credentials(user_integration)
            
            # Update status
            user_integration.status = IntegrationStatus.DISCONNECTED
            user_integration.credentials = {}
            user_integration.error_message = None
            user_integration.updated_at = datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting integration {user_integration_id}: {e}")
            return False
    
    def sync_integration(self, user_id: int, user_integration_id: str) -> bool:
        """Manually trigger sync for an integration."""
        try:
            user_integration = self.user_integrations.get(user_integration_id)
            
            if not user_integration or user_integration.user_id != user_id:
                return False
            
            if user_integration.status != IntegrationStatus.CONNECTED:
                return False
            
            # Perform sync based on integration type
            success = self._perform_integration_sync(user_integration)
            
            if success:
                user_integration.last_sync = datetime.now()
                user_integration.error_message = None
            else:
                user_integration.error_message = "Sync failed"
            
            user_integration.updated_at = datetime.now()
            
            return success
            
        except Exception as e:
            logger.error(f"Error syncing integration {user_integration_id}: {e}")
            return False
    
    def send_to_integration(self, user_id: int, integration_id: str,
                          action: str, data: Dict[str, Any]) -> bool:
        """Send data to an integration (e.g., post to Slack, create Jira ticket)."""
        try:
            user_integration = self._get_user_integration(user_id, integration_id)
            
            if not user_integration or user_integration.status != IntegrationStatus.CONNECTED:
                return False
            
            integration = self.integrations_registry.get(integration_id)
            if not integration:
                return False
            
            # Route to appropriate integration handler
            if integration_id == 'slack':
                return self._send_to_slack(user_integration, action, data)
            elif integration_id == 'jira':
                return self._send_to_jira(user_integration, action, data)
            elif integration_id == 'notion':
                return self._send_to_notion(user_integration, action, data)
            else:
                logger.warning(f"No handler for integration {integration_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error sending to integration {integration_id}: {e}")
            return False
    
    def get_integration_analytics(self, user_id: int) -> Dict[str, Any]:
        """Get analytics about user's integration usage."""
        try:
            user_integrations = [
                integration for integration in self.user_integrations.values()
                if integration.user_id == user_id
            ]
            
            total_integrations = len(user_integrations)
            connected_integrations = len([
                i for i in user_integrations 
                if i.status == IntegrationStatus.CONNECTED
            ])
            
            # Calculate usage statistics
            sync_stats = {}
            for integration in user_integrations:
                if integration.last_sync:
                    days_since_sync = (datetime.now() - integration.last_sync).days
                    sync_stats[integration.integration_id] = days_since_sync
            
            return {
                'total_integrations': total_integrations,
                'connected_integrations': connected_integrations,
                'connection_rate': (connected_integrations / total_integrations * 100) if total_integrations > 0 else 0,
                'most_used_types': self._get_most_used_integration_types(user_integrations),
                'sync_health': sync_stats,
                'recent_activity': self._get_recent_integration_activity(user_integrations)
            }
            
        except Exception as e:
            logger.error(f"Error getting integration analytics for {user_id}: {e}")
            return {}
    
    def _initialize_integrations(self):
        """Initialize the integrations registry with available integrations."""
        integrations = [
            # Slack Integration
            Integration(
                id='slack',
                name='Slack',
                description='Send meeting summaries and task notifications to Slack channels. Get real-time updates and collaborate seamlessly.',
                provider='Slack Technologies',
                type=IntegrationType.MESSAGING,
                icon_url='/static/images/integrations/slack.svg',
                website_url='https://slack.com',
                is_official=True,
                supported_features=[
                    'send_meeting_summaries',
                    'task_notifications',
                    'real_time_updates',
                    'channel_integration',
                    'direct_messages',
                    'slash_commands'
                ],
                setup_complexity='easy',
                pricing_model='freemium',
                popularity_score=95,
                last_updated=datetime.now()
            ),
            
            # Jira Integration
            Integration(
                id='jira',
                name='Jira',
                description='Create Jira tickets from meeting action items. Link tasks to issues and track progress across your development workflow.',
                provider='Atlassian',
                type=IntegrationType.PROJECT_MANAGEMENT,
                icon_url='/static/images/integrations/jira.svg',
                website_url='https://atlassian.com/software/jira',
                is_official=True,
                supported_features=[
                    'create_tickets',
                    'link_tasks',
                    'status_sync',
                    'comments_sync',
                    'priority_mapping',
                    'custom_fields'
                ],
                setup_complexity='medium',
                pricing_model='paid',
                popularity_score=88,
                last_updated=datetime.now()
            ),
            
            # Notion Integration
            Integration(
                id='notion',
                name='Notion',
                description='Export meeting summaries to Notion pages. Sync with databases and create a knowledge base from your meetings.',
                provider='Notion Labs',
                type=IntegrationType.DOCUMENTATION,
                icon_url='/static/images/integrations/notion.svg',
                website_url='https://notion.so',
                is_official=True,
                supported_features=[
                    'export_summaries',
                    'database_sync',
                    'page_creation',
                    'template_support',
                    'collaborative_editing',
                    'search_integration'
                ],
                setup_complexity='medium',
                pricing_model='freemium',
                popularity_score=85,
                last_updated=datetime.now()
            ),
            
            # Microsoft Teams Integration
            Integration(
                id='microsoft_teams',
                name='Microsoft Teams',
                description='Integrate with Microsoft Teams for seamless collaboration. Send summaries and updates directly to Teams channels.',
                provider='Microsoft',
                type=IntegrationType.MESSAGING,
                icon_url='/static/images/integrations/teams.svg',
                website_url='https://teams.microsoft.com',
                is_official=True,
                supported_features=[
                    'channel_messages',
                    'meeting_summaries',
                    'task_notifications',
                    'bot_integration',
                    'adaptive_cards'
                ],
                setup_complexity='medium',
                pricing_model='freemium',
                popularity_score=82,
                last_updated=datetime.now()
            ),
            
            # Asana Integration
            Integration(
                id='asana',
                name='Asana',
                description='Create tasks and projects in Asana from meeting action items. Track progress and manage deadlines.',
                provider='Asana',
                type=IntegrationType.PROJECT_MANAGEMENT,
                icon_url='/static/images/integrations/asana.svg',
                website_url='https://asana.com',
                is_official=True,
                supported_features=[
                    'create_tasks',
                    'project_management',
                    'deadline_sync',
                    'team_collaboration',
                    'status_updates'
                ],
                setup_complexity='easy',
                pricing_model='freemium',
                popularity_score=78,
                last_updated=datetime.now()
            ),
            
            # Trello Integration
            Integration(
                id='trello',
                name='Trello',
                description='Add meeting action items as Trello cards. Organize tasks on boards and track progress visually.',
                provider='Atlassian',
                type=IntegrationType.PROJECT_MANAGEMENT,
                icon_url='/static/images/integrations/trello.svg',
                website_url='https://trello.com',
                is_official=True,
                supported_features=[
                    'create_cards',
                    'board_integration',
                    'checklist_sync',
                    'due_date_sync',
                    'label_management'
                ],
                setup_complexity='easy',
                pricing_model='freemium',
                popularity_score=75,
                last_updated=datetime.now()
            ),
            
            # Google Drive Integration
            Integration(
                id='google_drive',
                name='Google Drive',
                description='Save meeting recordings and summaries to Google Drive. Organize files and share with team members.',
                provider='Google',
                type=IntegrationType.STORAGE,
                icon_url='/static/images/integrations/google_drive.svg',
                website_url='https://drive.google.com',
                is_official=True,
                supported_features=[
                    'file_storage',
                    'auto_organization',
                    'sharing_controls',
                    'folder_structure',
                    'version_history'
                ],
                setup_complexity='easy',
                pricing_model='freemium',
                popularity_score=90,
                last_updated=datetime.now()
            ),
            
            # Zapier Integration
            Integration(
                id='zapier',
                name='Zapier',
                description='Connect Mina to 5000+ apps with Zapier. Create custom automation workflows triggered by meeting events.',
                provider='Zapier',
                type=IntegrationType.AUTOMATION,
                icon_url='/static/images/integrations/zapier.svg',
                website_url='https://zapier.com',
                is_official=True,
                supported_features=[
                    'workflow_automation',
                    'trigger_events',
                    'custom_actions',
                    'multi_step_zaps',
                    'conditional_logic'
                ],
                setup_complexity='advanced',
                pricing_model='freemium',
                popularity_score=80,
                last_updated=datetime.now()
            )
        ]
        
        # Store in registry
        for integration in integrations:
            self.integrations_registry[integration.id] = integration
    
    def _get_user_integration(self, user_id: int, integration_id: str) -> Optional[UserIntegration]:
        """Get user's integration by integration_id."""
        for user_integration in self.user_integrations.values():
            if (user_integration.user_id == user_id and 
                user_integration.integration_id == integration_id):
                return user_integration
        return None
    
    def _initiate_integration_auth(self, integration: Integration, 
                                 user_integration: UserIntegration) -> str:
        """Initiate OAuth authentication flow for integration."""
        try:
            # Generate state parameter for OAuth
            state = secrets.token_urlsafe(32)
            
            # Store state in user integration config
            user_integration.config['oauth_state'] = state
            
            # Return mock OAuth URL - in real implementation, this would be the actual OAuth URL
            oauth_urls = {
                'slack': f'https://slack.com/oauth/v2/authorize?client_id=SLACK_CLIENT_ID&scope=chat:write,channels:read&state={state}&redirect_uri=https://mina.app/auth/slack/callback',
                'jira': f'https://auth.atlassian.com/authorize?audience=api.atlassian.com&client_id=JIRA_CLIENT_ID&scope=read:jira-work&state={state}&redirect_uri=https://mina.app/auth/jira/callback',
                'notion': f'https://api.notion.com/v1/oauth/authorize?client_id=NOTION_CLIENT_ID&response_type=code&owner=user&state={state}&redirect_uri=https://mina.app/auth/notion/callback',
                'microsoft_teams': f'https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=TEAMS_CLIENT_ID&scope=https://graph.microsoft.com/Chat.ReadWrite&state={state}&redirect_uri=https://mina.app/auth/teams/callback'
            }
            
            return oauth_urls.get(integration.id, f'https://mina.app/integrations/{integration.id}/setup?state={state}')
            
        except Exception as e:
            logger.error(f"Error initiating auth for {integration.id}: {e}")
            return f'https://mina.app/integrations/{integration.id}/setup'
    
    def _revoke_integration_credentials(self, user_integration: UserIntegration):
        """Revoke integration credentials with the provider."""
        try:
            # In real implementation, this would make API calls to revoke tokens
            logger.info(f"Revoking credentials for integration {user_integration.integration_id}")
        except Exception as e:
            logger.error(f"Error revoking credentials: {e}")
    
    def _perform_integration_sync(self, user_integration: UserIntegration) -> bool:
        """Perform sync operation for an integration."""
        try:
            integration_id = user_integration.integration_id
            
            # Mock sync operations
            if integration_id == 'slack':
                return self._sync_slack(user_integration)
            elif integration_id == 'jira':
                return self._sync_jira(user_integration)
            elif integration_id == 'notion':
                return self._sync_notion(user_integration)
            else:
                logger.info(f"Sync completed for {integration_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error syncing integration {user_integration.integration_id}: {e}")
            return False
    
    def _send_to_slack(self, user_integration: UserIntegration, action: str, data: Dict[str, Any]) -> bool:
        """Send data to Slack."""
        try:
            if action == 'meeting_summary':
                # Mock sending meeting summary to Slack
                channel = data.get('channel', '#general')
                summary = data.get('summary', '')
                logger.info(f"Sending meeting summary to Slack channel {channel}")
                return True
            elif action == 'task_notification':
                # Mock sending task notification to Slack
                user = data.get('user', '@channel')
                task = data.get('task', '')
                logger.info(f"Sending task notification to {user}: {task}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error sending to Slack: {e}")
            return False
    
    def _send_to_jira(self, user_integration: UserIntegration, action: str, data: Dict[str, Any]) -> bool:
        """Send data to Jira."""
        try:
            if action == 'create_ticket':
                # Mock creating Jira ticket
                project = data.get('project', 'PROJ')
                summary = data.get('summary', '')
                description = data.get('description', '')
                logger.info(f"Creating Jira ticket in {project}: {summary}")
                return True
            elif action == 'update_ticket':
                # Mock updating Jira ticket
                ticket_id = data.get('ticket_id', '')
                status = data.get('status', '')
                logger.info(f"Updating Jira ticket {ticket_id} to {status}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error sending to Jira: {e}")
            return False
    
    def _send_to_notion(self, user_integration: UserIntegration, action: str, data: Dict[str, Any]) -> bool:
        """Send data to Notion."""
        try:
            if action == 'create_page':
                # Mock creating Notion page
                title = data.get('title', '')
                content = data.get('content', '')
                logger.info(f"Creating Notion page: {title}")
                return True
            elif action == 'update_database':
                # Mock updating Notion database
                database_id = data.get('database_id', '')
                properties = data.get('properties', {})
                logger.info(f"Updating Notion database {database_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error sending to Notion: {e}")
            return False
    
    def _sync_slack(self, user_integration: UserIntegration) -> bool:
        """Sync with Slack (fetch channels, users, etc.)."""
        logger.info("Syncing with Slack")
        return True
    
    def _sync_jira(self, user_integration: UserIntegration) -> bool:
        """Sync with Jira (fetch projects, issue types, etc.)."""
        logger.info("Syncing with Jira")
        return True
    
    def _sync_notion(self, user_integration: UserIntegration) -> bool:
        """Sync with Notion (fetch pages, databases, etc.)."""
        logger.info("Syncing with Notion")
        return True
    
    def _get_most_used_integration_types(self, user_integrations: List[UserIntegration]) -> List[str]:
        """Get most used integration types."""
        type_counts = {}
        for integration in user_integrations:
            if integration.status == IntegrationStatus.CONNECTED:
                integration_meta = self.integrations_registry.get(integration.integration_id)
                if integration_meta:
                    type_name = integration_meta.type.value
                    type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return sorted(type_counts.keys(), key=lambda x: type_counts[x], reverse=True)
    
    def _get_recent_integration_activity(self, user_integrations: List[UserIntegration]) -> List[Dict[str, Any]]:
        """Get recent integration activity."""
        activities = []
        for integration in user_integrations:
            if integration.last_sync:
                activities.append({
                    'integration_id': integration.integration_id,
                    'activity': 'sync',
                    'timestamp': integration.last_sync.isoformat(),
                    'status': 'success'
                })
        
        # Sort by timestamp, most recent first
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:10]  # Return last 10 activities


# Global service instance
integration_marketplace_service = IntegrationMarketplaceService()