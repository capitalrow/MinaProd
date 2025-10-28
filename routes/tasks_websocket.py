"""
Tasks WebSocket Namespace - CROWN⁴ Real-time Task Updates

Handles real-time updates for:
- Task status changes (pending → in_progress → completed)
- Task creation from meetings
- Task assignments
- Task priority updates
"""

import logging
from flask import request
from flask_socketio import emit, join_room, leave_room
from services.event_broadcaster import event_broadcaster

logger = logging.getLogger(__name__)


def register_tasks_namespace(socketio):
    """
    Register Tasks WebSocket namespace handlers.
    
    Namespace: /tasks
    Events:
    - connect: Client connects
    - disconnect: Client disconnects
    - join_workspace: Join workspace room for task updates
    - subscribe_meeting: Subscribe to task updates for specific meeting
    """
    
    @socketio.on('connect', namespace='/tasks')
    def handle_tasks_connect():
        """Handle client connection to tasks namespace."""
        try:
            client_id = request.sid
            logger.info(f"Tasks client connected: {client_id}")
            
            emit('connected', {
                'message': 'Connected to tasks namespace',
                'client_id': client_id,
                'namespace': '/tasks'
            })
            
        except Exception as e:
            logger.error(f"Tasks connect error: {e}", exc_info=True)
    
    @socketio.on('disconnect', namespace='/tasks')
    def handle_tasks_disconnect():
        """Handle client disconnection from tasks namespace."""
        try:
            client_id = request.sid
            logger.info(f"Tasks client disconnected: {client_id}")
            
        except Exception as e:
            logger.error(f"Tasks disconnect error: {e}", exc_info=True)
    
    @socketio.on('join_workspace', namespace='/tasks')
    def handle_join_workspace(data):
        """
        Join workspace room for task updates.
        
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
            
            logger.info(f"Client {request.sid} joined tasks room: {room}")
            
            emit('joined_workspace', {
                'workspace_id': workspace_id,
                'room': room
            })
            
        except Exception as e:
            logger.error(f"Join workspace error: {e}", exc_info=True)
            emit('error', {'message': 'Failed to join workspace'})
    
    @socketio.on('subscribe_meeting', namespace='/tasks')
    def handle_subscribe_meeting(data):
        """
        Subscribe to task updates for specific meeting.
        
        Args:
            data: {'meeting_id': int}
        """
        try:
            meeting_id = data.get('meeting_id')
            if not meeting_id:
                emit('error', {'message': 'meeting_id required'})
                return
            
            room = f"meeting_{meeting_id}"
            join_room(room)
            
            logger.info(f"Client {request.sid} subscribed to meeting {meeting_id} tasks")
            
            emit('subscribed_meeting', {
                'meeting_id': meeting_id,
                'room': room
            })
            
        except Exception as e:
            logger.error(f"Subscribe meeting error: {e}", exc_info=True)
            emit('error', {'message': 'Failed to subscribe to meeting'})
    
    logger.info("✅ Tasks WebSocket namespace registered (/tasks)")
