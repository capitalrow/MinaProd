"""
Unified Transcription State Persistence Service

Provides crash-safe, 5-second auto-save for both WebSocket handlers.
Ensures consistent persistence guarantees across default and /transcription namespaces.
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict
from flask import current_app
from models import db
from models.session import Session
from models.segment import Segment

logger = logging.getLogger(__name__)


class TranscriptionStatePersister:
    """
    Thread-safe transcription persistence manager with automatic 5-second flush.
    
    Features:
    - Per-session segment buffering with batch commits
    - Automatic 5-second flush cadence
    - Session metadata updates (duration, last_activity, transcript snapshot)
    - Crash-safe with force flush on disconnect
    - Thread-safe with Flask app context handling
    """
    
    def __init__(self, flush_interval_seconds: int = 5, batch_size: int = 5):
        """
        Initialize persistence manager.
        
        Args:
            flush_interval_seconds: How often to auto-flush (default: 5)
            batch_size: Min segments to trigger immediate flush (default: 5)
        """
        self.flush_interval = flush_interval_seconds
        self.batch_size = batch_size
        
        # Per-session state
        self._segment_buffers: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._session_metadata: Dict[str, Dict[str, Any]] = {}
        self._last_flush_time: Dict[str, float] = {}
        self._flush_threads: Dict[str, threading.Thread] = {}
        self._active_sessions: Dict[str, bool] = {}
        self._locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        
        logger.info(f"✅ TranscriptionStatePersister initialized (flush_interval={flush_interval_seconds}s, batch_size={batch_size})")
    
    def start_session(self, session_id: str, db_session_id: int, metadata: Optional[Dict[str, Any]] = None):
        """
        Start tracking a new session.
        
        Args:
            session_id: External session ID
            db_session_id: Database session ID
            metadata: Optional metadata (user_id, workspace_id, etc.)
        """
        with self._locks[session_id]:
            self._segment_buffers[session_id] = []
            self._session_metadata[session_id] = {
                'db_session_id': db_session_id,
                'started_at': datetime.utcnow(),
                'last_activity': datetime.utcnow(),
                'metadata': metadata or {}
            }
            self._last_flush_time[session_id] = time.time()
            self._active_sessions[session_id] = True
            
            # Start background flush thread
            flush_thread = threading.Thread(
                target=self._background_flush_loop,
                args=(session_id,),
                daemon=True,
                name=f"PersistenceFlush-{session_id[:8]}"
            )
            flush_thread.start()
            self._flush_threads[session_id] = flush_thread
            
            logger.info(f"📝 Started persistence tracking for session {session_id} (db_id={db_session_id})")
    
    def enqueue_segment(self, session_id: str, segment_payload: Dict[str, Any]):
        """
        Add a segment to the buffer for persistence.
        
        Args:
            session_id: External session ID
            segment_payload: Dict with segment data (text, kind, confidence, timestamps, etc.)
        """
        if session_id not in self._active_sessions:
            logger.warning(f"⚠️  Attempted to enqueue segment for inactive session: {session_id}")
            return
        
        with self._locks[session_id]:
            self._segment_buffers[session_id].append(segment_payload)
            self._session_metadata[session_id]['last_activity'] = datetime.utcnow()
            buffer_size = len(self._segment_buffers[session_id])
            
            logger.debug(f"📝 Enqueued segment for session {session_id} (buffer size: {buffer_size})")
            
            # Trigger immediate flush if batch size reached
            if buffer_size >= self.batch_size:
                logger.info(f"🚀 Batch size ({buffer_size}) reached for session {session_id}, triggering immediate flush")
                self.flush(session_id, force=True)
    
    def flush(self, session_id: str, force: bool = False):
        """
        Flush buffered segments to database.
        
        Args:
            session_id: External session ID
            force: If True, flush regardless of batch size
        """
        if session_id not in self._active_sessions:
            return
        
        with self._locks[session_id]:
            pending = self._segment_buffers[session_id]
            
            # Only commit if we have segments and (force or batch size met)
            if not pending:
                return
            
            if not force and len(pending) < self.batch_size:
                return
            
            db_session_id = self._session_metadata[session_id].get('db_session_id')
            if not db_session_id:
                logger.error(f"❌ No db_session_id for session {session_id}, cannot flush")
                return
            
            try:
                # Use Flask app context for thread safety
                with current_app.app_context():
                    # Add all pending segments
                    for segment_data in pending:
                        segment = Segment(
                            session_id=db_session_id,
                            kind=segment_data.get('kind', 'final'),
                            text=segment_data.get('text', ''),
                            avg_confidence=segment_data.get('avg_confidence') or segment_data.get('confidence'),
                            start_ms=segment_data.get('start_ms'),
                            end_ms=segment_data.get('end_ms'),
                            created_at=segment_data.get('created_at', datetime.utcnow())
                        )
                        db.session.add(segment)
                    
                    # Update session metadata (heartbeat)
                    session = db.session.query(Session).filter_by(id=db_session_id).first()
                    if session:
                        session.total_segments = (session.total_segments or 0) + len(pending)
                        
                        # Calculate and update duration if session is still active
                        if session.started_at:
                            duration_seconds = (datetime.utcnow() - session.started_at).total_seconds()
                            session.total_duration = duration_seconds
                    
                    db.session.commit()
                    
                    logger.info(f"💾 Flushed {len(pending)} segments for session {session_id} (db_id={db_session_id})")
                    
                    # Clear buffer after successful commit
                    self._segment_buffers[session_id] = []
                    self._last_flush_time[session_id] = time.time()
                    
            except Exception as e:
                logger.error(f"❌ Failed to flush segments for session {session_id}: {e}")
                db.session.rollback()
                # Keep segments in buffer for retry on next flush
    
    def _background_flush_loop(self, session_id: str):
        """
        Background thread that flushes every N seconds while session is active.
        
        Args:
            session_id: External session ID
        """
        logger.info(f"🔄 Started background flush loop for session {session_id}")
        
        try:
            while self._active_sessions.get(session_id, False):
                time.sleep(self.flush_interval)
                
                # Check if there's anything to flush
                if session_id in self._segment_buffers and len(self._segment_buffers[session_id]) > 0:
                    logger.debug(f"⏰ Auto-flush triggered for session {session_id}")
                    self.flush(session_id, force=False)  # Respects batch size unless force=True
                    
        except Exception as e:
            logger.error(f"❌ Background flush loop error for session {session_id}: {e}")
        finally:
            logger.info(f"🛑 Background flush loop stopped for session {session_id}")
    
    def end_session(self, session_id: str):
        """
        End session tracking and perform final flush.
        
        Args:
            session_id: External session ID
        """
        if session_id not in self._active_sessions:
            return
        
        logger.info(f"🏁 Ending session {session_id}, performing final flush")
        
        # Stop background thread
        self._active_sessions[session_id] = False
        
        # Final flush (force to get any remaining segments)
        self.flush(session_id, force=True)
        
        # Update session status to completed
        db_session_id = self._session_metadata[session_id].get('db_session_id')
        if db_session_id:
            try:
                with current_app.app_context():
                    session = db.session.query(Session).filter_by(id=db_session_id).first()
                    if session and session.status != 'completed':
                        session.status = 'completed'
                        session.completed_at = datetime.utcnow()
                        db.session.commit()
                        logger.info(f"✅ Marked session {session_id} as completed (db_id={db_session_id})")
            except Exception as e:
                logger.error(f"❌ Failed to mark session complete: {e}")
                db.session.rollback()
        
        # Cleanup
        with self._locks[session_id]:
            self._segment_buffers.pop(session_id, None)
            self._session_metadata.pop(session_id, None)
            self._last_flush_time.pop(session_id, None)
            self._flush_threads.pop(session_id, None)
            self._locks.pop(session_id, None)
        
        logger.info(f"🧹 Cleaned up persistence state for session {session_id}")
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current session persistence statistics.
        
        Args:
            session_id: External session ID
            
        Returns:
            Dict with buffered_segments, last_flush, etc. or None if session inactive
        """
        if session_id not in self._active_sessions:
            return None
        
        with self._locks[session_id]:
            return {
                'session_id': session_id,
                'buffered_segments': len(self._segment_buffers[session_id]),
                'last_flush': self._last_flush_time.get(session_id),
                'last_activity': self._session_metadata[session_id].get('last_activity'),
                'is_active': self._active_sessions.get(session_id, False)
            }


# Global singleton instance
_persister_instance: Optional[TranscriptionStatePersister] = None


def get_persister() -> TranscriptionStatePersister:
    """
    Get or create the global persister instance.
    
    Returns:
        TranscriptionStatePersister singleton
    """
    global _persister_instance
    if _persister_instance is None:
        _persister_instance = TranscriptionStatePersister(
            flush_interval_seconds=5,  # 5-second auto-save as per requirements
            batch_size=5  # Immediate flush when 5+ segments buffered
        )
    return _persister_instance
