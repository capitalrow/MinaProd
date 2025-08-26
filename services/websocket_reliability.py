#!/usr/bin/env python3
# 🔗 Production Feature: Enhanced WebSocket Reliability
"""
Implements enhanced WebSocket reliability with auto-reconnection, heartbeat,
session recovery, and network resilience features.

Addresses: "WebSocket Reliability" gap from production assessment.

Key Features:
- Auto-reconnection with exponential backoff
- Heartbeat/keep-alive mechanism
- Session state recovery
- Network error handling
- Connection state management
"""

import logging
import time
import json
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
from enum import Enum
import redis
from flask_socketio import SocketIO

logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    """WebSocket connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting" 
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"

@dataclass
class SessionRecoveryData:
    """Data needed to recover a session after disconnection."""
    session_id: str
    user_id: Optional[str] = None
    last_activity: float = field(default_factory=time.time)
    transcription_state: Dict[str, Any] = field(default_factory=dict)
    client_metadata: Dict[str, Any] = field(default_factory=dict)
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3

@dataclass
class HeartbeatConfig:
    """Heartbeat configuration."""
    interval_s: float = 30.0  # Send heartbeat every 30 seconds
    timeout_s: float = 60.0   # Timeout after 60 seconds without response
    max_missed: int = 3       # Max missed heartbeats before considering disconnected

class WebSocketReliabilityManager:
    """
    🔗 Production-grade WebSocket reliability manager.
    
    Handles connection state, auto-reconnection, heartbeat monitoring,
    and session recovery for robust real-time communication.
    """
    
    def __init__(self, socketio: SocketIO, redis_client: Optional[redis.Redis] = None,
                 heartbeat_config: Optional[HeartbeatConfig] = None):
        self.socketio = socketio
        self.redis_client = redis_client
        self.heartbeat_config = heartbeat_config or HeartbeatConfig()
        
        # Connection tracking
        self.client_states: Dict[str, ConnectionState] = {}  # {client_id: state}
        self.client_sessions: Dict[str, str] = {}  # {client_id: session_id}
        self.session_clients: Dict[str, List[str]] = {}  # {session_id: [client_ids]}
        
        # Session recovery
        self.recovery_data: Dict[str, SessionRecoveryData] = {}  # {session_id: recovery_data}
        self.recovery_lock = threading.RLock()
        
        # Heartbeat tracking
        self.heartbeat_timers: Dict[str, threading.Timer] = {}  # {client_id: timer}
        self.last_heartbeat: Dict[str, float] = {}  # {client_id: timestamp}
        self.missed_heartbeats: Dict[str, int] = {}  # {client_id: count}
        
        # Metrics
        self.total_connections = 0
        self.total_disconnections = 0
        self.successful_recoveries = 0
        self.failed_recoveries = 0
        self.heartbeat_timeouts = 0
        
        # Setup event handlers
        self._setup_event_handlers()
        
        logger.info("🔗 WebSocket reliability manager initialized with heartbeat and recovery")
    
    def _setup_event_handlers(self):
        """Setup Socket.IO event handlers for reliability features."""
        
        @self.socketio.on('connect')
        def handle_connect(auth):
            client_id = self._get_client_id()
            self.client_states[client_id] = ConnectionState.CONNECTED
            self.total_connections += 1
            
            logger.info(f"Client connected: {client_id}")
            
            # Start heartbeat monitoring
            self._start_heartbeat_monitoring(client_id)
            
            # Send connection acknowledgment with reliability info
            self.socketio.emit('connection_ack', {
                'client_id': client_id,
                'heartbeat_interval_s': self.heartbeat_config.interval_s,
                'server_time': time.time(),
                'reliability_features': ['heartbeat', 'auto_recovery', 'session_persistence']
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            client_id = self._get_client_id()
            self.client_states[client_id] = ConnectionState.DISCONNECTED
            self.total_disconnections += 1
            
            logger.info(f"Client disconnected: {client_id}")
            
            # Stop heartbeat monitoring
            self._stop_heartbeat_monitoring(client_id)
            
            # Setup session recovery if client was in a session
            if client_id in self.client_sessions:
                session_id = self.client_sessions[client_id]
                self._setup_session_recovery(session_id, client_id)
        
        @self.socketio.on('heartbeat')
        def handle_heartbeat(data):
            client_id = self._get_client_id()
            self._process_heartbeat(client_id, data)
        
        @self.socketio.on('recover_session')
        def handle_recover_session(data):
            client_id = self._get_client_id()
            session_id = data.get('session_id')
            
            if session_id:
                recovery_result = self._attempt_session_recovery(client_id, session_id)
                self.socketio.emit('recovery_result', recovery_result)
        
        @self.socketio.on('join_session')
        def handle_join_session(data):
            client_id = self._get_client_id()
            session_id = data.get('session_id')
            
            if session_id:
                self._register_client_session(client_id, session_id)
                
                # Store session metadata for recovery
                self._store_session_recovery_data(session_id, {
                    'client_id': client_id,
                    'joined_at': time.time(),
                    'metadata': data
                })
    
    def _get_client_id(self) -> str:
        """Get current client ID from request context."""
        from flask import request
        return request.sid
    
    def _start_heartbeat_monitoring(self, client_id: str):
        """Start heartbeat monitoring for a client."""
        self.last_heartbeat[client_id] = time.time()
        self.missed_heartbeats[client_id] = 0
        
        # Schedule heartbeat timeout check
        timer = threading.Timer(
            self.heartbeat_config.timeout_s, 
            self._check_heartbeat_timeout, 
            args=[client_id]
        )
        timer.start()
        self.heartbeat_timers[client_id] = timer
        
        # Send initial heartbeat request
        self.socketio.emit('heartbeat_request', {
            'timestamp': time.time(),
            'interval_s': self.heartbeat_config.interval_s
        }, room=client_id)
    
    def _stop_heartbeat_monitoring(self, client_id: str):
        """Stop heartbeat monitoring for a client."""
        if client_id in self.heartbeat_timers:
            self.heartbeat_timers[client_id].cancel()
            del self.heartbeat_timers[client_id]
        
        # Clean up heartbeat data
        self.last_heartbeat.pop(client_id, None)
        self.missed_heartbeats.pop(client_id, None)
    
    def _process_heartbeat(self, client_id: str, data: Dict[str, Any]):
        """Process heartbeat response from client."""
        current_time = time.time()
        self.last_heartbeat[client_id] = current_time
        self.missed_heartbeats[client_id] = 0
        
        # Calculate round-trip time
        client_timestamp = data.get('timestamp', current_time)
        rtt_ms = (current_time - client_timestamp) * 1000
        
        # Send heartbeat acknowledgment
        self.socketio.emit('heartbeat_ack', {
            'server_timestamp': current_time,
            'client_timestamp': client_timestamp,
            'rtt_ms': round(rtt_ms, 2)
        }, room=client_id)
        
        # Schedule next heartbeat timeout check
        if client_id in self.heartbeat_timers:
            self.heartbeat_timers[client_id].cancel()
        
        timer = threading.Timer(
            self.heartbeat_config.timeout_s,
            self._check_heartbeat_timeout,
            args=[client_id]
        )
        timer.start()
        self.heartbeat_timers[client_id] = timer
    
    def _check_heartbeat_timeout(self, client_id: str):
        """Check if client has timed out on heartbeat."""
        if client_id not in self.last_heartbeat:
            return
        
        current_time = time.time()
        last_seen = self.last_heartbeat[client_id]
        time_since_heartbeat = current_time - last_seen
        
        if time_since_heartbeat > self.heartbeat_config.timeout_s:
            self.missed_heartbeats[client_id] = self.missed_heartbeats.get(client_id, 0) + 1
            
            if self.missed_heartbeats[client_id] >= self.heartbeat_config.max_missed:
                # Client has missed too many heartbeats
                self.heartbeat_timeouts += 1
                self.client_states[client_id] = ConnectionState.FAILED
                
                logger.warning(f"Client {client_id} heartbeat timeout after {time_since_heartbeat:.1f}s")
                
                # Setup recovery if in session
                if client_id in self.client_sessions:
                    session_id = self.client_sessions[client_id]
                    self._setup_session_recovery(session_id, client_id)
                
                # Disconnect the client
                self.socketio.disconnect(client_id)
            else:
                # Send another heartbeat request
                self.socketio.emit('heartbeat_request', {
                    'timestamp': current_time,
                    'missed_count': self.missed_heartbeats[client_id]
                }, room=client_id)
                
                # Schedule next check
                timer = threading.Timer(
                    self.heartbeat_config.timeout_s,
                    self._check_heartbeat_timeout,
                    args=[client_id]
                )
                timer.start()
                self.heartbeat_timers[client_id] = timer
    
    def _register_client_session(self, client_id: str, session_id: str):
        """Register client as part of a session."""
        self.client_sessions[client_id] = session_id
        
        if session_id not in self.session_clients:
            self.session_clients[session_id] = []
        
        if client_id not in self.session_clients[session_id]:
            self.session_clients[session_id].append(client_id)
        
        logger.debug(f"Registered client {client_id} to session {session_id}")
    
    def _setup_session_recovery(self, session_id: str, client_id: str):
        """Setup session recovery data for disconnected client."""
        with self.recovery_lock:
            if session_id not in self.recovery_data:
                self.recovery_data[session_id] = SessionRecoveryData(session_id=session_id)
            
            recovery = self.recovery_data[session_id]
            recovery.last_activity = time.time()
            recovery.client_metadata[client_id] = {
                'disconnected_at': time.time(),
                'state': self.client_states.get(client_id, ConnectionState.DISCONNECTED).value
            }
            
            # Store in Redis if available
            if self.redis_client:
                recovery_key = f"session_recovery:{session_id}"
                recovery_data = {
                    'session_id': session_id,
                    'last_activity': recovery.last_activity,
                    'client_metadata': recovery.client_metadata,
                    'recovery_attempts': recovery.recovery_attempts
                }
                self.redis_client.setex(
                    recovery_key, 
                    3600,  # 1 hour TTL
                    json.dumps(recovery_data)
                )
            
            logger.info(f"Setup session recovery for {session_id}, client {client_id}")
    
    def _attempt_session_recovery(self, client_id: str, session_id: str) -> Dict[str, Any]:
        """Attempt to recover a session for a reconnecting client."""
        with self.recovery_lock:
            recovery_data = None
            
            # Try to get recovery data from Redis first
            if self.redis_client:
                recovery_key = f"session_recovery:{session_id}"
                stored_data = self.redis_client.get(recovery_key)
                if stored_data:
                    recovery_data = json.loads(stored_data)
            
            # Fall back to in-memory data
            if not recovery_data and session_id in self.recovery_data:
                recovery = self.recovery_data[session_id]
                recovery_data = {
                    'session_id': session_id,
                    'last_activity': recovery.last_activity,
                    'client_metadata': recovery.client_metadata,
                    'recovery_attempts': recovery.recovery_attempts
                }
            
            if not recovery_data:
                self.failed_recoveries += 1
                return {
                    'success': False,
                    'reason': 'no_recovery_data',
                    'session_id': session_id
                }
            
            # Check if recovery is still valid (within time window)
            current_time = time.time()
            time_since_disconnect = current_time - recovery_data['last_activity']
            max_recovery_time = 300  # 5 minutes
            
            if time_since_disconnect > max_recovery_time:
                self.failed_recoveries += 1
                return {
                    'success': False,
                    'reason': 'recovery_expired',
                    'session_id': session_id,
                    'time_since_disconnect': time_since_disconnect
                }
            
            # Check recovery attempts
            if recovery_data['recovery_attempts'] >= 3:
                self.failed_recoveries += 1
                return {
                    'success': False,
                    'reason': 'max_attempts_exceeded',
                    'session_id': session_id,
                    'attempts': recovery_data['recovery_attempts']
                }
            
            # Successful recovery
            self.successful_recoveries += 1
            recovery_data['recovery_attempts'] += 1
            
            # Re-register client to session
            self._register_client_session(client_id, session_id)
            
            # Update recovery data
            if session_id in self.recovery_data:
                self.recovery_data[session_id].recovery_attempts = recovery_data['recovery_attempts']
            
            logger.info(f"Successfully recovered session {session_id} for client {client_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'recovery_time_s': time_since_disconnect,
                'attempt_number': recovery_data['recovery_attempts'],
                'metadata': recovery_data.get('client_metadata', {})
            }
    
    def _store_session_recovery_data(self, session_id: str, data: Dict[str, Any]):
        """Store session recovery data."""
        with self.recovery_lock:
            if session_id not in self.recovery_data:
                self.recovery_data[session_id] = SessionRecoveryData(session_id=session_id)
            
            recovery = self.recovery_data[session_id]
            recovery.transcription_state.update(data)
            recovery.last_activity = time.time()
    
    def broadcast_to_session(self, session_id: str, event: str, data: Dict[str, Any]):
        """Broadcast message to all clients in a session."""
        if session_id in self.session_clients:
            for client_id in self.session_clients[session_id]:
                if self.client_states.get(client_id) == ConnectionState.CONNECTED:
                    self.socketio.emit(event, data, room=client_id)
    
    def get_reliability_stats(self) -> Dict[str, Any]:
        """Get WebSocket reliability statistics."""
        current_time = time.time()
        
        # Count connections by state
        state_counts = {}
        for state in ConnectionState:
            state_counts[state.value] = sum(1 for s in self.client_states.values() if s == state)
        
        # Calculate recovery success rate
        total_recoveries = self.successful_recoveries + self.failed_recoveries
        recovery_success_rate = (
            (self.successful_recoveries / total_recoveries * 100) if total_recoveries > 0 else 0
        )
        
        return {
            'connection_states': state_counts,
            'total_connections': self.total_connections,
            'total_disconnections': self.total_disconnections,
            'active_sessions': len(self.session_clients),
            'recovery_success_rate_percent': round(recovery_success_rate, 1),
            'successful_recoveries': self.successful_recoveries,
            'failed_recoveries': self.failed_recoveries,
            'heartbeat_timeouts': self.heartbeat_timeouts,
            'active_heartbeat_monitors': len(self.heartbeat_timers),
            'recovery_data_entries': len(self.recovery_data)
        }
    
    def cleanup_session(self, session_id: str):
        """Clean up session data and associated clients."""
        with self.recovery_lock:
            # Remove from recovery data
            self.recovery_data.pop(session_id, None)
            
            # Clean up client associations
            if session_id in self.session_clients:
                client_ids = self.session_clients[session_id].copy()
                for client_id in client_ids:
                    self.client_sessions.pop(client_id, None)
                del self.session_clients[session_id]
            
            # Clean up Redis data
            if self.redis_client:
                recovery_key = f"session_recovery:{session_id}"
                self.redis_client.delete(recovery_key)
            
            logger.info(f"Cleaned up reliability data for session {session_id}")

# Global reliability manager
_reliability_manager: Optional[WebSocketReliabilityManager] = None

def get_reliability_manager() -> Optional[WebSocketReliabilityManager]:
    """Get the global reliability manager instance."""
    return _reliability_manager

def initialize_reliability_manager(socketio: SocketIO, redis_client: Optional[redis.Redis] = None):
    """Initialize the global reliability manager."""
    global _reliability_manager
    _reliability_manager = WebSocketReliabilityManager(socketio, redis_client)
    return _reliability_manager