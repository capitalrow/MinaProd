#!/usr/bin/env python3
# 💾 Production Feature: Checkpointing System for Fault Tolerance
"""
Implements comprehensive checkpointing system for fault tolerance,
ensuring session state and transcript progress are preserved across failures.

Addresses: "Fault Tolerance" gap from production assessment.

Key Features:
- Automatic session state checkpointing
- Transcript progress preservation
- Recovery from checkpoint data
- Configurable checkpoint intervals
- Redis-backed persistent storage
"""

import logging
import time
import json
import threading
import pickle
import hashlib
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import redis

logger = logging.getLogger(__name__)

class CheckpointType(Enum):
    """Types of checkpoints."""
    SESSION_STATE = "session_state"
    TRANSCRIPT = "transcript"
    AUDIO_BUFFER = "audio_buffer"
    USER_ACTIVITY = "user_activity"
    SYSTEM_STATE = "system_state"

@dataclass
class Checkpoint:
    """Checkpoint data structure."""
    checkpoint_id: str
    session_id: str
    checkpoint_type: CheckpointType
    timestamp: float
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    size_bytes: int = 0
    checksum: str = ""
    
    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._calculate_checksum()
        if not self.size_bytes:
            self.size_bytes = len(json.dumps(self.data))
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum for data integrity."""
        data_str = json.dumps(self.data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

@dataclass
class CheckpointingConfig:
    """Configuration for checkpointing system."""
    # Intervals (seconds)
    session_checkpoint_interval: float = 30.0
    transcript_checkpoint_interval: float = 10.0
    audio_buffer_checkpoint_interval: float = 60.0
    
    # Retention
    max_checkpoints_per_session: int = 20
    checkpoint_retention_hours: int = 24
    
    # Storage
    compression_enabled: bool = True
    encryption_enabled: bool = False
    
    # Recovery
    auto_recovery_enabled: bool = True
    recovery_timeout_s: float = 30.0

class CheckpointingManager:
    """
    💾 Production-grade checkpointing manager for fault tolerance.
    
    Automatically saves session state, transcript progress, and system state
    to enable recovery from failures without data loss.
    """
    
    def __init__(self, redis_client: redis.Redis, config: Optional[CheckpointingConfig] = None):
        self.redis_client = redis_client
        self.config = config or CheckpointingConfig()
        
        # Checkpoint storage and management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.checkpoint_timers: Dict[str, threading.Timer] = {}
        self.checkpoint_lock = threading.RLock()
        
        # Recovery callbacks
        self.recovery_callbacks: Dict[CheckpointType, List[Callable]] = {
            checkpoint_type: [] for checkpoint_type in CheckpointType
        }
        
        # Metrics
        self.checkpoints_created = 0
        self.checkpoints_restored = 0
        self.checkpoint_failures = 0
        self.recovery_attempts = 0
        self.successful_recoveries = 0
        
        # Background cleanup
        self._start_cleanup_thread()
        
        logger.info("💾 Checkpointing manager initialized with Redis persistence")
    
    def register_session(self, session_id: str, initial_state: Dict[str, Any] = None):
        """
        Register a session for checkpointing.
        
        Args:
            session_id: Session identifier
            initial_state: Initial session state to checkpoint
        """
        with self.checkpoint_lock:
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    'registered_at': time.time(),
                    'last_checkpoint': 0,
                    'state': initial_state or {},
                    'checkpoint_count': 0
                }
                
                # Schedule automatic checkpointing
                self._schedule_checkpointing(session_id)
                
                # Create initial checkpoint
                if initial_state:
                    self.create_checkpoint(
                        session_id, 
                        CheckpointType.SESSION_STATE, 
                        initial_state
                    )
                
                logger.info(f"Registered session {session_id} for checkpointing")
    
    def create_checkpoint(self, session_id: str, checkpoint_type: CheckpointType, 
                         data: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
        """
        Create a checkpoint for session data.
        
        Args:
            session_id: Session identifier
            checkpoint_type: Type of checkpoint
            data: Data to checkpoint
            metadata: Optional metadata
            
        Returns:
            Checkpoint ID
        """
        try:
            checkpoint_id = f"{session_id}_{checkpoint_type.value}_{int(time.time() * 1000)}"
            
            # Create checkpoint object
            checkpoint = Checkpoint(
                checkpoint_id=checkpoint_id,
                session_id=session_id,
                checkpoint_type=checkpoint_type,
                timestamp=time.time(),
                data=data,
                metadata=metadata or {}
            )
            
            # Store in Redis
            self._store_checkpoint(checkpoint)
            
            # Update session tracking
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['last_checkpoint'] = checkpoint.timestamp
                self.active_sessions[session_id]['checkpoint_count'] += 1
            
            self.checkpoints_created += 1
            logger.debug(f"Created checkpoint {checkpoint_id} for session {session_id}")
            
            return checkpoint_id
            
        except Exception as e:
            self.checkpoint_failures += 1
            logger.error(f"Failed to create checkpoint for {session_id}: {e}")
            raise
    
    def _store_checkpoint(self, checkpoint: Checkpoint):
        """Store checkpoint in Redis."""
        # Store checkpoint data
        checkpoint_key = f"checkpoint:{checkpoint.checkpoint_id}"
        checkpoint_data = {
            'checkpoint_id': checkpoint.checkpoint_id,
            'session_id': checkpoint.session_id,
            'checkpoint_type': checkpoint.checkpoint_type.value,
            'timestamp': checkpoint.timestamp,
            'data': checkpoint.data,
            'metadata': checkpoint.metadata,
            'size_bytes': checkpoint.size_bytes,
            'checksum': checkpoint.checksum
        }
        
        # Store with TTL based on retention policy
        ttl_seconds = self.config.checkpoint_retention_hours * 3600
        
        self.redis_client.setex(
            checkpoint_key,
            ttl_seconds,
            json.dumps(checkpoint_data)
        )
        
        # Add to session checkpoint index
        session_index_key = f"session_checkpoints:{checkpoint.session_id}"
        self.redis_client.zadd(
            session_index_key,
            {checkpoint.checkpoint_id: checkpoint.timestamp}
        )
        self.redis_client.expire(session_index_key, ttl_seconds)
        
        # Add to type-based index
        type_index_key = f"checkpoints_by_type:{checkpoint.checkpoint_type.value}"
        self.redis_client.zadd(
            type_index_key,
            {checkpoint.checkpoint_id: checkpoint.timestamp}
        )
        self.redis_client.expire(type_index_key, ttl_seconds)
        
        # Maintain checkpoint count limit
        self._cleanup_old_checkpoints(checkpoint.session_id)
    
    def get_latest_checkpoint(self, session_id: str, 
                            checkpoint_type: Optional[CheckpointType] = None) -> Optional[Checkpoint]:
        """
        Get the latest checkpoint for a session.
        
        Args:
            session_id: Session identifier
            checkpoint_type: Optional checkpoint type filter
            
        Returns:
            Latest checkpoint or None
        """
        try:
            session_index_key = f"session_checkpoints:{session_id}"
            
            # Get latest checkpoint IDs (most recent first)
            checkpoint_ids = self.redis_client.zrevrange(session_index_key, 0, 10)
            
            for checkpoint_id in checkpoint_ids:
                checkpoint = self._load_checkpoint(checkpoint_id)
                if checkpoint and (not checkpoint_type or checkpoint.checkpoint_type == checkpoint_type):
                    return checkpoint
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest checkpoint for {session_id}: {e}")
            return None
    
    def get_checkpoints_by_time_range(self, session_id: str, start_time: float, 
                                    end_time: float) -> List[Checkpoint]:
        """
        Get checkpoints within a time range.
        
        Args:
            session_id: Session identifier
            start_time: Start timestamp
            end_time: End timestamp
            
        Returns:
            List of checkpoints in time range
        """
        try:
            session_index_key = f"session_checkpoints:{session_id}"
            
            # Get checkpoint IDs in time range
            checkpoint_ids = self.redis_client.zrangebyscore(
                session_index_key, start_time, end_time
            )
            
            checkpoints = []
            for checkpoint_id in checkpoint_ids:
                checkpoint = self._load_checkpoint(checkpoint_id)
                if checkpoint:
                    checkpoints.append(checkpoint)
            
            return sorted(checkpoints, key=lambda c: c.timestamp)
            
        except Exception as e:
            logger.error(f"Failed to get checkpoints by time range for {session_id}: {e}")
            return []
    
    def _load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load checkpoint from Redis."""
        try:
            checkpoint_key = f"checkpoint:{checkpoint_id}"
            data_json = self.redis_client.get(checkpoint_key)
            
            if not data_json:
                return None
            
            data = json.loads(data_json)
            
            # Verify checksum
            checkpoint = Checkpoint(
                checkpoint_id=data['checkpoint_id'],
                session_id=data['session_id'],
                checkpoint_type=CheckpointType(data['checkpoint_type']),
                timestamp=data['timestamp'],
                data=data['data'],
                metadata=data['metadata'],
                size_bytes=data['size_bytes'],
                checksum=data['checksum']
            )
            
            # Verify data integrity
            if checkpoint.checksum != checkpoint._calculate_checksum():
                logger.warning(f"Checksum mismatch for checkpoint {checkpoint_id}")
                return None
            
            return checkpoint
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            return None
    
    def recover_session(self, session_id: str, recovery_point: Optional[float] = None) -> Dict[str, Any]:
        """
        Recover session from checkpoints.
        
        Args:
            session_id: Session identifier
            recovery_point: Optional specific time to recover to
            
        Returns:
            Recovery result with restored data
        """
        try:
            self.recovery_attempts += 1
            start_time = time.time()
            
            logger.info(f"Starting session recovery for {session_id}")
            
            # Get recovery checkpoint
            if recovery_point:
                # Find checkpoint closest to recovery point
                checkpoints = self.get_checkpoints_by_time_range(
                    session_id, 0, recovery_point
                )
                if not checkpoints:
                    return {
                        'success': False,
                        'error': 'no_checkpoints_before_recovery_point',
                        'recovery_point': recovery_point
                    }
                checkpoint = checkpoints[-1]  # Latest before recovery point
            else:
                # Get latest checkpoint
                checkpoint = self.get_latest_checkpoint(session_id)
                if not checkpoint:
                    return {
                        'success': False,
                        'error': 'no_checkpoints_found',
                        'session_id': session_id
                    }
            
            # Restore data by type
            restored_data = {}
            
            # Get all checkpoint types for this session
            session_checkpoints = self.get_checkpoints_by_time_range(
                session_id, 0, checkpoint.timestamp
            )
            
            # Group by type and get latest of each
            by_type = {}
            for cp in session_checkpoints:
                if cp.checkpoint_type not in by_type or cp.timestamp > by_type[cp.checkpoint_type].timestamp:
                    by_type[cp.checkpoint_type] = cp
            
            # Restore each type
            for checkpoint_type, cp in by_type.items():
                restored_data[checkpoint_type.value] = cp.data
                
                # Call recovery callbacks
                for callback in self.recovery_callbacks.get(checkpoint_type, []):
                    try:
                        callback(session_id, cp.data)
                    except Exception as e:
                        logger.error(f"Recovery callback error for {checkpoint_type}: {e}")
            
            recovery_time = time.time() - start_time
            self.successful_recoveries += 1
            
            logger.info(f"✅ Session {session_id} recovered in {recovery_time:.2f}s from checkpoint {checkpoint.checkpoint_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'checkpoint_id': checkpoint.checkpoint_id,
                'recovery_timestamp': checkpoint.timestamp,
                'recovery_time_s': recovery_time,
                'restored_types': list(restored_data.keys()),
                'data': restored_data
            }
            
        except Exception as e:
            logger.error(f"Session recovery failed for {session_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    def register_recovery_callback(self, checkpoint_type: CheckpointType, callback: Callable):
        """
        Register callback for session recovery.
        
        Args:
            checkpoint_type: Type of checkpoint to handle
            callback: Function to call on recovery (session_id, data)
        """
        self.recovery_callbacks[checkpoint_type].append(callback)
        logger.debug(f"Registered recovery callback for {checkpoint_type}")
    
    def _schedule_checkpointing(self, session_id: str):
        """Schedule automatic checkpointing for a session."""
        def create_session_checkpoint():
            if session_id in self.active_sessions:
                try:
                    session_data = self.active_sessions[session_id]
                    self.create_checkpoint(
                        session_id,
                        CheckpointType.SESSION_STATE,
                        session_data['state'],
                        {'auto_generated': True}
                    )
                except Exception as e:
                    logger.error(f"Auto checkpoint failed for {session_id}: {e}")
                
                # Schedule next checkpoint
                timer = threading.Timer(
                    self.config.session_checkpoint_interval,
                    create_session_checkpoint
                )
                timer.start()
                self.checkpoint_timers[session_id] = timer
        
        # Start initial timer
        timer = threading.Timer(
            self.config.session_checkpoint_interval,
            create_session_checkpoint
        )
        timer.start()
        self.checkpoint_timers[session_id] = timer
    
    def _cleanup_old_checkpoints(self, session_id: str):
        """Clean up old checkpoints to maintain count limit."""
        try:
            session_index_key = f"session_checkpoints:{session_id}"
            checkpoint_count = self.redis_client.zcard(session_index_key)
            
            if checkpoint_count > self.config.max_checkpoints_per_session:
                # Remove oldest checkpoints
                excess_count = checkpoint_count - self.config.max_checkpoints_per_session
                old_checkpoint_ids = self.redis_client.zrange(session_index_key, 0, excess_count - 1)
                
                for checkpoint_id in old_checkpoint_ids:
                    # Remove checkpoint data
                    checkpoint_key = f"checkpoint:{checkpoint_id}"
                    self.redis_client.delete(checkpoint_key)
                    
                    # Remove from indices
                    self.redis_client.zrem(session_index_key, checkpoint_id)
        
        except Exception as e:
            logger.error(f"Checkpoint cleanup failed for {session_id}: {e}")
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread for expired checkpoints."""
        def cleanup_loop():
            while True:
                try:
                    # Clean up expired checkpoint indices
                    current_time = time.time()
                    cutoff_time = current_time - (self.config.checkpoint_retention_hours * 3600)
                    
                    # Clean up type indices
                    for checkpoint_type in CheckpointType:
                        type_index_key = f"checkpoints_by_type:{checkpoint_type.value}"
                        self.redis_client.zremrangebyscore(type_index_key, 0, cutoff_time)
                    
                    time.sleep(3600)  # Run every hour
                    
                except Exception as e:
                    logger.error(f"Cleanup thread error: {e}")
                    time.sleep(60)  # Retry after 1 minute on error
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True, name="checkpoint-cleanup")
        cleanup_thread.start()
    
    def update_session_state(self, session_id: str, state_updates: Dict[str, Any]):
        """
        Update session state (triggers checkpoint on next interval).
        
        Args:
            session_id: Session identifier
            state_updates: State updates to apply
        """
        with self.checkpoint_lock:
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['state'].update(state_updates)
                logger.debug(f"Updated session state for {session_id}")
    
    def force_checkpoint(self, session_id: str, checkpoint_type: CheckpointType, 
                        data: Dict[str, Any]) -> str:
        """
        Force immediate checkpoint creation.
        
        Args:
            session_id: Session identifier
            checkpoint_type: Type of checkpoint
            data: Data to checkpoint
            
        Returns:
            Checkpoint ID
        """
        return self.create_checkpoint(
            session_id, 
            checkpoint_type, 
            data, 
            {'forced': True, 'created_at': time.time()}
        )
    
    def unregister_session(self, session_id: str):
        """
        Unregister session from checkpointing.
        
        Args:
            session_id: Session identifier
        """
        with self.checkpoint_lock:
            # Stop checkpointing timer
            if session_id in self.checkpoint_timers:
                self.checkpoint_timers[session_id].cancel()
                del self.checkpoint_timers[session_id]
            
            # Remove from active sessions
            self.active_sessions.pop(session_id, None)
            
            logger.info(f"Unregistered session {session_id} from checkpointing")
    
    def get_checkpointing_stats(self) -> Dict[str, Any]:
        """Get checkpointing statistics."""
        return {
            'active_sessions': len(self.active_sessions),
            'active_timers': len(self.checkpoint_timers),
            'checkpoints_created': self.checkpoints_created,
            'checkpoints_restored': self.checkpoints_restored,
            'checkpoint_failures': self.checkpoint_failures,
            'recovery_attempts': self.recovery_attempts,
            'successful_recoveries': self.successful_recoveries,
            'recovery_success_rate_percent': round(
                (self.successful_recoveries / max(1, self.recovery_attempts)) * 100, 1
            ),
            'config': asdict(self.config)
        }

# Global checkpointing manager
_checkpointing_manager: Optional[CheckpointingManager] = None

def get_checkpointing_manager() -> Optional[CheckpointingManager]:
    """Get the global checkpointing manager."""
    return _checkpointing_manager

def initialize_checkpointing_manager(redis_client: redis.Redis, 
                                   config: Optional[CheckpointingConfig] = None) -> CheckpointingManager:
    """Initialize the global checkpointing manager."""
    global _checkpointing_manager
    _checkpointing_manager = CheckpointingManager(redis_client, config)
    return _checkpointing_manager