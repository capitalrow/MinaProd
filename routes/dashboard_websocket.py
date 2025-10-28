"""
Dashboard WebSocket Namespace - CROWN⁴ Real-time Synchronization

Handles real-time updates for:
- New meeting creation (session_update:created)
- Dashboard statistics refresh
- Idle background sync (checksum validation)
- Filter changes
- Archive operations
"""

import logging
from flask import request
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from services.event_broadcaster import event_broadcaster

logger = logging.getLogger(__name__)


def register_dashboard_namespace(socketio):
    """
    Register Dashboard WebSocket namespace handlers.
    
    Namespace: /dashboard
    Events:
    - connect: Client connects to dashboard
    - disconnect: Client disconnects
    - join_workspace: Join workspace-specific room
    - leave_workspace: Leave workspace room
    - request_sync: Request dashboard sync
    """
    
    @socketio.on('connect', namespace='/dashboard')
    def handle_dashboard_connect():
        """Handle client connection to dashboard namespace."""
        try:
            client_id = request.sid
            logger.info(f"Dashboard client connected: {client_id}")
            
            # Send acknowledgment
            emit('connected', {
                'message': 'Connected to dashboard namespace',
                'client_id': client_id,
                'namespace': '/dashboard'
            })
            
        except Exception as e:
            logger.error(f"Dashboard connect error: {e}", exc_info=True)
    
    @socketio.on('disconnect', namespace='/dashboard')
    def handle_dashboard_disconnect():
        """Handle client disconnection from dashboard namespace."""
        try:
            client_id = request.sid
            logger.info(f"Dashboard client disconnected: {client_id}")
            
        except Exception as e:
            logger.error(f"Dashboard disconnect error: {e}", exc_info=True)
    
    @socketio.on('join_workspace', namespace='/dashboard')
    def handle_join_workspace(data):
        """
        Join workspace-specific room for isolated broadcasts.
        
        Args:
            data: {'workspace_id': int}
        """
        try:
            workspace_id = data.get('workspace_id')
            if not workspace_id:
                emit('error', {'message': 'workspace_id required'})
                return
            
            room = f"workspace_{workspace_id}"
            join_room(room)
            
            logger.info(f"Client {request.sid} joined dashboard room: {room}")
            
            emit('joined_workspace', {
                'workspace_id': workspace_id,
                'room': room,
                'message': f'Joined workspace {workspace_id}'
            })
            
        except Exception as e:
            logger.error(f"Join workspace error: {e}", exc_info=True)
            emit('error', {'message': 'Failed to join workspace'})
    
    @socketio.on('leave_workspace', namespace='/dashboard')
    def handle_leave_workspace(data):
        """
        Leave workspace-specific room.
        
        Args:
            data: {'workspace_id': int}
        """
        try:
            workspace_id = data.get('workspace_id')
            if not workspace_id:
                emit('error', {'message': 'workspace_id required'})
                return
            
            room = f"workspace_{workspace_id}"
            leave_room(room)
            
            logger.info(f"Client {request.sid} left dashboard room: {room}")
            
            emit('left_workspace', {
                'workspace_id': workspace_id,
                'room': room,
                'message': f'Left workspace {workspace_id}'
            })
            
        except Exception as e:
            logger.error(f"Leave workspace error: {e}", exc_info=True)
            emit('error', {'message': 'Failed to leave workspace'})
    
    @socketio.on('request_sync', namespace='/dashboard')
    def handle_request_sync(data):
        """
        Handle client request for dashboard sync.
        
        Args:
            data: {'workspace_id': int, 'client_checksum': str}
        """
        try:
            workspace_id = data.get('workspace_id')
            client_checksum = data.get('client_checksum')
            
            logger.debug(f"Dashboard sync requested for workspace {workspace_id}")
            
            # TODO: Implement checksum validation and delta sync in Phase 3
            emit('sync_response', {
                'workspace_id': workspace_id,
                'sync_required': False,  # Placeholder
                'message': 'Sync check completed'
            })
            
        except Exception as e:
            logger.error(f"Request sync error: {e}", exc_info=True)
            emit('error', {'message': 'Failed to process sync request'})
    
    @socketio.on('request_event_replay', namespace='/dashboard')
    def handle_request_event_replay(data):
        """
        CROWN⁴ Event Replay - Replay missed events for reconnecting clients.
        
        Critical for offline resilience: When a client reconnects after being offline,
        they request all events since their last_sequence_num to catch up to current state.
        
        Args:
            data: {
                'workspace_id': int,
                'last_sequence_num': int,
                'namespace': str,
                'is_initial_sync': bool
            }
        """
        try:
            from models import db
            from models.event_ledger import EventLedger, EventStatus
            from sqlalchemy import select
            
            workspace_id = data.get('workspace_id')
            last_sequence_num = data.get('last_sequence_num', 0)
            is_initial_sync = data.get('is_initial_sync', False)
            
            logger.info(
                f"Event replay requested: workspace={workspace_id}, "
                f"last_seq={last_sequence_num}, initial_sync={is_initial_sync}"
            )
            
            # CRITICAL SECURITY: Query events ONLY for the requesting workspace
            # Filter events that belong to this workspace by checking payload
            all_events = db.session.scalars(
                select(EventLedger)
                .where(EventLedger.status == EventStatus.COMPLETED)
                .where(EventLedger.sequence_num > last_sequence_num)
                .order_by(EventLedger.sequence_num)
            ).all()
            
            # Filter events to only those belonging to the requested workspace
            # CRITICAL: Prevent cross-workspace data leaks
            events = []
            for event in all_events:
                # Check if event payload contains workspace_id matching the request
                if event.payload and isinstance(event.payload, dict):
                    event_workspace_id = event.payload.get('workspace_id')
                    if event_workspace_id == workspace_id:
                        events.append(event)
                # Include workspace-agnostic system events (e.g., dashboard_bootstrap)
                # but only if they don't leak data from other workspaces
                elif event.event_type.value in ['dashboard_bootstrap', 'dashboard_idle_sync']:
                    events.append(event)
            
            # NOTE: No hard limit - client must receive ALL missed events to stay in sync
            # If there are thousands of events, consider implementing pagination
            if len(events) > 500:
                logger.warning(
                    f"Large event replay: {len(events)} events for workspace {workspace_id}. "
                    "Consider implementing pagination for better performance."
                )
            
            # Convert events to dictionaries for JSON serialization
            events_data = []
            for event in events:
                events_data.append({
                    'event_id': event.id,
                    'event_type': event.event_type.value,
                    'event_name': event.event_name,
                    'sequence_num': event.sequence_num,
                    'last_applied': event.last_applied_id,
                    'timestamp': event.created_at.isoformat() if event.created_at else None,
                    'data': event.payload or {},
                    'checksum': event.checksum
                })
            
            logger.info(
                f"Replaying {len(events_data)} events for workspace {workspace_id} "
                f"(seq {last_sequence_num} → {events[-1].sequence_num if events else last_sequence_num})"
            )
            
            # Send replayed events to client
            emit('event_replay', {
                'events': events_data,
                'workspace_id': workspace_id,
                'last_sequence_num': events[-1].sequence_num if events else last_sequence_num,
                'is_initial_sync': is_initial_sync,
                'count': len(events_data)
            })
            
        except Exception as e:
            logger.error(f"Event replay error: {e}", exc_info=True)
            emit('error', {'message': 'Failed to replay events'})
    
    logger.info("✅ Dashboard WebSocket namespace registered (/dashboard)")
