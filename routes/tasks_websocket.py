"""
Tasks WebSocket Namespace - CROWN⁴.5 Real-time Task Updates

Handles all 20 CROWN⁴.5 task events with vector clock support,
deduplication, and optimistic UI updates.

Supported Events (Full Matrix):
1. tasks_bootstrap - Initial load
2. tasks_ws_subscribe - Subscribe to updates  
3. task_nlp:proposed - AI-proposed task
4. task_create:manual - Manual creation
5. task_create:nlp_accept - Accept NLP proposal
6. task_update:title - Update title
7. task_update:status_toggle - Toggle status
8. task_update:priority - Update priority
9. task_update:due - Update due date
10. task_update:assign - Assign participant
11. task_update:labels - Update labels
12. task_snooze - Snooze task
13. task_merge - Merge duplicates
14. task_link:jump_to_span - Jump to transcript
15. filter_apply - Apply filters
16. tasks_refresh - Manual refresh
17. tasks_idle_sync - Background sync
18. tasks_offline_queue:replay - Offline queue replay
19. task_delete - Delete task
20. tasks_multiselect:bulk - Bulk operations
"""

import logging
import asyncio
from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from services.event_broadcaster import event_broadcaster
from services.task_event_handler import task_event_handler

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
    
    # CROWN⁴.5 Event Matrix Handlers
    
    @socketio.on('task_event', namespace='/tasks')
    async def handle_task_event(data):
        """
        Universal handler for all 20 CROWN⁴.5 task events.
        
        Args:
            data: {
                'event_type': str,  # e.g., 'task_create:manual'
                'payload': dict,    # Event-specific data
                'vector_clock': dict (optional),  # Vector clock for offline support
                'trace_id': str (optional)  # Trace ID for telemetry
            }
        """
        try:
            event_type = data.get('event_type')
            payload = data.get('payload', {})
            
            if not event_type:
                await socketio.emit('error', {'message': 'event_type required'}, namespace='/tasks')
                return
            
            # Get user ID (from authenticated session)
            user_id = payload.get('user_id') or (current_user.id if current_user.is_authenticated else None)
            session_id = payload.get('session_id')
            
            if not user_id:
                await socketio.emit('error', {'message': 'user_id required'}, namespace='/tasks')
                return
            
            # Add vector clock to payload if provided
            if 'vector_clock' in data:
                payload['vector_clock'] = data['vector_clock']
            
            # Process event (now properly awaited in async context)
            result = await task_event_handler.handle_event(
                event_type=event_type,
                payload=payload,
                user_id=user_id,
                session_id=session_id
            )
            
            # Emit result back to client (async)
            await socketio.emit('task_event_result', {
                'event_type': event_type,
                'result': result,
                'trace_id': data.get('trace_id')
            }, namespace='/tasks')
            
            # Broadcast to workspace room if successful
            if result.get('success'):
                workspace_id = payload.get('workspace_id')
                if workspace_id:
                    await socketio.emit('task_updated', {
                        'event_type': event_type,
                        'data': result
                    }, room=f"workspace_{workspace_id}", namespace='/tasks')
            
        except Exception as e:
            logger.error(f"Task event error: {e}", exc_info=True)
            await socketio.emit('error', {
                'message': 'Failed to process task event',
                'error': str(e)
            }, namespace='/tasks')
    
    # Individual event handlers for backward compatibility
    
    @socketio.on('tasks_bootstrap', namespace='/tasks')
    async def handle_tasks_bootstrap(data):
        """Bootstrap handler - loads initial tasks."""
        data['event_type'] = 'tasks_bootstrap'
        return await handle_task_event(data)
    
    @socketio.on('task_create', namespace='/tasks')
    async def handle_task_create(data):
        """Task creation handler."""
        data['event_type'] = 'task_create:manual'
        return await handle_task_event(data)
    
    @socketio.on('task_update', namespace='/tasks')
    async def handle_task_update(data):
        """Task update handler - routes to specific update type."""
        update_type = data.get('update_type', 'title')
        data['event_type'] = f'task_update:{update_type}'
        return await handle_task_event(data)
    
    @socketio.on('task_delete', namespace='/tasks')
    async def handle_task_delete(data):
        """Task deletion handler."""
        data['event_type'] = 'task_delete'
        return await handle_task_event(data)
    
    @socketio.on('offline_queue:save', namespace='/tasks')
    async def handle_offline_queue_save(data):
        """
        Save frontend's offline queue to server for backup.
        Allows recovery if browser cache is cleared.
        """
        from app import db
        from models.offline_queue import OfflineQueue
        from datetime import datetime
        
        try:
            if not current_user.is_authenticated:
                await socketio.emit('error', {'message': 'Authentication required'}, namespace='/tasks')
                return
            
            user_id = current_user.id
            session_id = data.get('session_id')
            queue_data = data.get('queue_data', [])
            
            existing = OfflineQueue.query.filter_by(
                user_id=user_id,
                session_id=session_id
            ).first()
            
            if existing:
                existing.queue_data = queue_data
                existing.updated_at = datetime.utcnow()
            else:
                existing = OfflineQueue(
                    user_id=user_id,
                    session_id=session_id,
                    queue_data=queue_data
                )
                db.session.add(existing)
            
            db.session.commit()
            
            await socketio.emit('offline_queue:saved', {
                'success': True,
                'queue_id': existing.id,
                'updated_at': existing.updated_at.isoformat()
            }, namespace='/tasks')
            
            logger.info(f"Offline queue saved for user {user_id}, session {session_id}")
            
        except Exception as e:
            logger.error(f"Offline queue save failed: {e}", exc_info=True)
            db.session.rollback()
            await socketio.emit('error', {
                'message': 'Failed to save offline queue',
                'error': str(e)
            }, namespace='/tasks')
    
    @socketio.on('offline_queue:retrieve', namespace='/tasks')
    async def handle_offline_queue_retrieve(data):
        """
        Retrieve saved offline queue from server.
        Used for recovery after browser cache loss.
        """
        from models.offline_queue import OfflineQueue
        
        try:
            if not current_user.is_authenticated:
                await socketio.emit('error', {'message': 'Authentication required'}, namespace='/tasks')
                return
            
            user_id = current_user.id
            session_id = data.get('session_id')
            
            queue = OfflineQueue.query.filter_by(
                user_id=user_id,
                session_id=session_id
            ).first()
            
            if queue:
                await socketio.emit('offline_queue:retrieved', {
                    'success': True,
                    'queue_data': queue.queue_data,
                    'updated_at': queue.updated_at.isoformat()
                }, namespace='/tasks')
                logger.info(f"Offline queue retrieved for user {user_id}, session {session_id}")
            else:
                await socketio.emit('offline_queue:retrieved', {
                    'success': True,
                    'queue_data': [],
                    'message': 'No saved queue found'
                }, namespace='/tasks')
                
        except Exception as e:
            logger.error(f"Offline queue retrieve failed: {e}", exc_info=True)
            await socketio.emit('error', {
                'message': 'Failed to retrieve offline queue',
                'error': str(e)
            }, namespace='/tasks')
    
    @socketio.on('offline_queue:clear', namespace='/tasks')
    async def handle_offline_queue_clear(data):
        """
        Clear saved offline queue from server.
        Called after successful replay to clean up.
        """
        from app import db
        from models.offline_queue import OfflineQueue
        
        try:
            if not current_user.is_authenticated:
                await socketio.emit('error', {'message': 'Authentication required'}, namespace='/tasks')
                return
            
            user_id = current_user.id
            session_id = data.get('session_id')
            
            deleted = OfflineQueue.query.filter_by(
                user_id=user_id,
                session_id=session_id
            ).delete()
            
            db.session.commit()
            
            await socketio.emit('offline_queue:cleared', {
                'success': True,
                'deleted_count': deleted
            }, namespace='/tasks')
            
            logger.info(f"Offline queue cleared for user {user_id}, session {session_id}: {deleted} entries")
            
        except Exception as e:
            logger.error(f"Offline queue clear failed: {e}", exc_info=True)
            db.session.rollback()
            await socketio.emit('error', {
                'message': 'Failed to clear offline queue',
                'error': str(e)
            }, namespace='/tasks')
    
    logger.info("✅ Tasks WebSocket namespace registered (/tasks)")
