# services/enhanced_session_manager.py
"""
ENHANCED SESSION MANAGER
Comprehensive session management with persistence, recovery, export capabilities,
performance optimization, and real-time collaboration features.
"""

import logging
import json
import time
import uuid
import threading
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import pickle
import gzip
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SessionMetadata:
    """Comprehensive session metadata"""
    session_id: str
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str] = None
    session_name: str = ""
    total_duration: float = 0.0
    audio_processed_bytes: int = 0
    transcription_word_count: int = 0
    speaker_count: int = 0
    average_confidence: float = 0.0
    language: str = "en"
    quality_score: float = 0.0
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    export_formats: List[str] = field(default_factory=list)
    
@dataclass
class SessionState:
    """Enhanced session state with comprehensive tracking"""
    metadata: SessionMetadata
    transcription_segments: List[Dict[str, Any]] = field(default_factory=list)
    speaker_profiles: Dict[str, Any] = field(default_factory=dict)
    audio_metrics_history: List[Dict[str, Any]] = field(default_factory=list)
    processing_events: List[Dict[str, Any]] = field(default_factory=list)
    error_log: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'metadata': asdict(self.metadata),
            'transcription_segments': self.transcription_segments,
            'speaker_profiles': self.speaker_profiles,
            'audio_metrics_history': self.audio_metrics_history[-1000:],  # Keep last 1000
            'processing_events': self.processing_events[-500:],  # Keep last 500
            'error_log': self.error_log[-100:],  # Keep last 100
            'performance_metrics': self.performance_metrics,
            'checkpoints': self.checkpoints[-10:]  # Keep last 10
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """Create from dictionary"""
        metadata_dict = data.get('metadata', {})
        if 'created_at' in metadata_dict and isinstance(metadata_dict['created_at'], str):
            metadata_dict['created_at'] = datetime.fromisoformat(metadata_dict['created_at'])
        if 'updated_at' in metadata_dict and isinstance(metadata_dict['updated_at'], str):
            metadata_dict['updated_at'] = datetime.fromisoformat(metadata_dict['updated_at'])
            
        metadata = SessionMetadata(**metadata_dict)
        
        return cls(
            metadata=metadata,
            transcription_segments=data.get('transcription_segments', []),
            speaker_profiles=data.get('speaker_profiles', {}),
            audio_metrics_history=data.get('audio_metrics_history', []),
            processing_events=data.get('processing_events', []),
            error_log=data.get('error_log', []),
            performance_metrics=data.get('performance_metrics', {}),
            checkpoints=data.get('checkpoints', [])
        )

class SessionPersistenceManager:
    """Advanced session persistence with compression and recovery"""
    
    def __init__(self, storage_path: str = "sessions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Compression settings
        self.enable_compression = True
        self.compression_level = 6
        
        # Recovery settings
        self.auto_backup_interval = 300  # 5 minutes
        self.max_backups_per_session = 5
        
        logger.info(f"📁 Session persistence manager initialized: {self.storage_path}")
    
    def save_session(self, session_state: SessionState) -> bool:
        """Save session with compression and backup"""
        try:
            session_id = session_state.metadata.session_id
            session_path = self.storage_path / f"{session_id}.session"
            backup_path = self.storage_path / "backups" / session_id
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Update metadata
            session_state.metadata.updated_at = datetime.now()
            
            # Prepare data
            session_data = session_state.to_dict()
            serialized_data = json.dumps(session_data, default=str, indent=2)
            
            # Save with compression
            if self.enable_compression:
                compressed_data = gzip.compress(serialized_data.encode('utf-8'), compresslevel=self.compression_level)
                with open(session_path.with_suffix('.session.gz'), 'wb') as f:
                    f.write(compressed_data)
            else:
                with open(session_path, 'w', encoding='utf-8') as f:
                    f.write(serialized_data)
            
            # Create backup
            self._create_backup(session_state, backup_path)
            
            logger.debug(f"💾 Session saved: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Session save failed: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[SessionState]:
        """Load session with automatic recovery if needed"""
        try:
            session_path = self.storage_path / f"{session_id}.session"
            compressed_path = session_path.with_suffix('.session.gz')
            
            # Try compressed version first
            if compressed_path.exists():
                with open(compressed_path, 'rb') as f:
                    compressed_data = f.read()
                    session_data = json.loads(gzip.decompress(compressed_data).decode('utf-8'))
            elif session_path.exists():
                with open(session_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
            else:
                # Try recovery from backup
                return self._recover_from_backup(session_id)
            
            session_state = SessionState.from_dict(session_data)
            logger.debug(f"📂 Session loaded: {session_id}")
            return session_state
            
        except Exception as e:
            logger.error(f"❌ Session load failed: {e}")
            # Try recovery
            return self._recover_from_backup(session_id)
    
    def _create_backup(self, session_state: SessionState, backup_path: Path):
        """Create timestamped backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_path / f"backup_{timestamp}.json.gz"
            
            session_data = session_state.to_dict()
            serialized_data = json.dumps(session_data, default=str)
            compressed_data = gzip.compress(serialized_data.encode('utf-8'))
            
            with open(backup_file, 'wb') as f:
                f.write(compressed_data)
            
            # Clean up old backups
            self._cleanup_old_backups(backup_path)
            
        except Exception as e:
            logger.warning(f"⚠️ Backup creation failed: {e}")
    
    def _cleanup_old_backups(self, backup_path: Path):
        """Remove old backups keeping only the most recent ones"""
        try:
            backup_files = list(backup_path.glob("backup_*.json.gz"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove excess backups
            for backup_file in backup_files[self.max_backups_per_session:]:
                backup_file.unlink()
                
        except Exception as e:
            logger.warning(f"⚠️ Backup cleanup failed: {e}")
    
    def _recover_from_backup(self, session_id: str) -> Optional[SessionState]:
        """Recover session from most recent backup"""
        try:
            backup_path = self.storage_path / "backups" / session_id
            if not backup_path.exists():
                return None
            
            backup_files = list(backup_path.glob("backup_*.json.gz"))
            if not backup_files:
                return None
            
            # Get most recent backup
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_backup, 'rb') as f:
                compressed_data = f.read()
                session_data = json.loads(gzip.decompress(compressed_data).decode('utf-8'))
            
            session_state = SessionState.from_dict(session_data)
            logger.info(f"🔄 Session recovered from backup: {session_id}")
            return session_state
            
        except Exception as e:
            logger.error(f"❌ Session recovery failed: {e}")
            return None
    
    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available sessions"""
        try:
            sessions = []
            
            for session_file in self.storage_path.glob("*.session*"):
                if session_file.suffix == '.gz':
                    session_id = session_file.stem.replace('.session', '')
                else:
                    session_id = session_file.stem
                
                # Load minimal metadata
                try:
                    session_state = self.load_session(session_id)
                    if session_state:
                        if user_id is None or session_state.metadata.user_id == user_id:
                            sessions.append({
                                'session_id': session_id,
                                'name': session_state.metadata.session_name,
                                'created_at': session_state.metadata.created_at,
                                'updated_at': session_state.metadata.updated_at,
                                'duration': session_state.metadata.total_duration,
                                'word_count': session_state.metadata.transcription_word_count,
                                'speaker_count': session_state.metadata.speaker_count,
                                'quality_score': session_state.metadata.quality_score
                            })
                except Exception:
                    continue
            
            # Sort by updated_at descending
            sessions.sort(key=lambda x: x['updated_at'], reverse=True)
            return sessions
            
        except Exception as e:
            logger.error(f"❌ Session listing failed: {e}")
            return []

class EnhancedSessionManager:
    """Enhanced session manager with comprehensive features"""
    
    def __init__(self, storage_path: str = "sessions"):
        self.persistence = SessionPersistenceManager(storage_path)
        
        # Active sessions
        self.active_sessions: Dict[str, SessionState] = {}
        
        # Session pools for different purposes
        self.transcription_sessions: Dict[str, str] = {}  # client_id -> session_id
        self.collaboration_sessions: Dict[str, List[str]] = {}  # session_id -> [client_ids]
        
        # Performance tracking
        self.session_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.global_stats = {
            'total_sessions': 0,
            'active_sessions': 0,
            'total_transcription_time': 0,
            'total_words_transcribed': 0,
            'average_session_quality': 0.0
        }
        
        # Background tasks
        self.auto_save_interval = 60  # 1 minute
        self.cleanup_interval = 3600  # 1 hour
        self._background_tasks_active = True
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Start background tasks
        self._start_background_tasks()
        
        logger.info("🎯 Enhanced Session Manager initialized")
    
    def create_session(
        self, 
        user_id: Optional[str] = None, 
        session_name: str = "",
        language: str = "en",
        **kwargs
    ) -> str:
        """Create new enhanced session"""
        try:
            with self._lock:
                session_id = str(uuid.uuid4())
                
                # Create metadata
                metadata = SessionMetadata(
                    session_id=session_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    user_id=user_id,
                    session_name=session_name or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    language=language,
                    **kwargs
                )
                
                # Create session state
                session_state = SessionState(metadata=metadata)
                
                # Store in active sessions
                self.active_sessions[session_id] = session_state
                
                # Initialize session metrics
                self._initialize_session_metrics(session_id)
                
                # Save initial state
                self.persistence.save_session(session_state)
                
                # Update global stats
                self.global_stats['total_sessions'] += 1
                self.global_stats['active_sessions'] += 1
                
                logger.info(f"🆕 Created enhanced session: {session_id}")
                return session_id
                
        except Exception as e:
            logger.error(f"❌ Session creation failed: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session state (from memory or disk)"""
        try:
            with self._lock:
                # Check active sessions first
                if session_id in self.active_sessions:
                    return self.active_sessions[session_id]
                
                # Load from disk
                session_state = self.persistence.load_session(session_id)
                if session_state:
                    # Add to active sessions
                    self.active_sessions[session_id] = session_state
                    self.global_stats['active_sessions'] += 1
                    return session_state
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Session retrieval failed: {e}")
            return None
    
    def update_session(
        self, 
        session_id: str, 
        update_data: Dict[str, Any],
        auto_save: bool = True
    ) -> bool:
        """Update session with new data"""
        try:
            with self._lock:
                session_state = self.get_session(session_id)
                if not session_state:
                    return False
                
                # Update metadata
                if 'metadata' in update_data:
                    for key, value in update_data['metadata'].items():
                        if hasattr(session_state.metadata, key):
                            setattr(session_state.metadata, key, value)
                
                # Update other components
                for component in ['transcription_segments', 'speaker_profiles', 'audio_metrics_history']:
                    if component in update_data:
                        if isinstance(update_data[component], list):
                            getattr(session_state, component).extend(update_data[component])
                        elif isinstance(update_data[component], dict):
                            getattr(session_state, component).update(update_data[component])
                
                # Update timestamp
                session_state.metadata.updated_at = datetime.now()
                
                # Auto-save if enabled
                if auto_save:
                    self.persistence.save_session(session_state)
                
                # Update metrics
                self._update_session_metrics(session_id, update_data)
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Session update failed: {e}")
            return False
    
    def add_transcription_segment(
        self, 
        session_id: str, 
        segment: Dict[str, Any]
    ) -> bool:
        """Add transcription segment to session"""
        try:
            segment_data = {
                **segment,
                'timestamp': time.time(),
                'segment_id': str(uuid.uuid4())
            }
            
            return self.update_session(session_id, {
                'transcription_segments': [segment_data]
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to add transcription segment: {e}")
            return False
    
    def add_speaker_profile(
        self, 
        session_id: str, 
        speaker_id: str, 
        profile_data: Dict[str, Any]
    ) -> bool:
        """Add or update speaker profile"""
        try:
            return self.update_session(session_id, {
                'speaker_profiles': {speaker_id: profile_data}
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to add speaker profile: {e}")
            return False
    
    def create_checkpoint(self, session_id: str, description: str = "") -> bool:
        """Create session checkpoint for recovery"""
        try:
            with self._lock:
                session_state = self.get_session(session_id)
                if not session_state:
                    return False
                
                checkpoint = {
                    'checkpoint_id': str(uuid.uuid4()),
                    'timestamp': time.time(),
                    'description': description,
                    'session_snapshot': session_state.to_dict()
                }
                
                session_state.checkpoints.append(checkpoint)
                
                # Keep only recent checkpoints
                if len(session_state.checkpoints) > 10:
                    session_state.checkpoints = session_state.checkpoints[-10:]
                
                self.persistence.save_session(session_state)
                
                logger.debug(f"📋 Checkpoint created for session {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Checkpoint creation failed: {e}")
            return False
    
    def restore_checkpoint(self, session_id: str, checkpoint_id: str) -> bool:
        """Restore session from checkpoint"""
        try:
            with self._lock:
                session_state = self.get_session(session_id)
                if not session_state:
                    return False
                
                # Find checkpoint
                checkpoint = None
                for cp in session_state.checkpoints:
                    if cp['checkpoint_id'] == checkpoint_id:
                        checkpoint = cp
                        break
                
                if not checkpoint:
                    return False
                
                # Restore from checkpoint
                restored_state = SessionState.from_dict(checkpoint['session_snapshot'])
                
                # Keep current checkpoints and add restoration event
                restored_state.checkpoints = session_state.checkpoints
                restored_state.processing_events.append({
                    'event': 'checkpoint_restored',
                    'checkpoint_id': checkpoint_id,
                    'timestamp': time.time()
                })
                
                # Update active session
                self.active_sessions[session_id] = restored_state
                self.persistence.save_session(restored_state)
                
                logger.info(f"🔄 Session {session_id} restored from checkpoint {checkpoint_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Checkpoint restoration failed: {e}")
            return False
    
    def export_session(
        self, 
        session_id: str, 
        export_format: str = "json",
        include_audio: bool = False
    ) -> Optional[bytes]:
        """Export session in various formats"""
        try:
            session_state = self.get_session(session_id)
            if not session_state:
                return None
            
            if export_format.lower() == "json":
                return self._export_json(session_state)
            elif export_format.lower() == "txt":
                return self._export_text(session_state)
            elif export_format.lower() == "srt":
                return self._export_srt(session_state)
            elif export_format.lower() == "csv":
                return self._export_csv(session_state)
            else:
                logger.warning(f"⚠️ Unsupported export format: {export_format}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Session export failed: {e}")
            return None
    
    def _export_json(self, session_state: SessionState) -> bytes:
        """Export session as JSON"""
        export_data = session_state.to_dict()
        return json.dumps(export_data, indent=2, default=str).encode('utf-8')
    
    def _export_text(self, session_state: SessionState) -> bytes:
        """Export session as plain text transcript"""
        lines = []
        lines.append(f"Session: {session_state.metadata.session_name}")
        lines.append(f"Date: {session_state.metadata.created_at}")
        lines.append(f"Duration: {session_state.metadata.total_duration:.1f} seconds")
        lines.append(f"Words: {session_state.metadata.transcription_word_count}")
        lines.append("-" * 50)
        lines.append("")
        
        # Group segments by speaker
        current_speaker = None
        speaker_text = []
        
        for segment in session_state.transcription_segments:
            speaker_id = segment.get('speaker_id', 'Unknown')
            text = segment.get('text', '').strip()
            
            if speaker_id != current_speaker:
                if speaker_text:
                    lines.append(f"{current_speaker}: {' '.join(speaker_text)}")
                    lines.append("")
                current_speaker = speaker_id
                speaker_text = []
            
            if text:
                speaker_text.append(text)
        
        # Add final speaker text
        if speaker_text:
            lines.append(f"{current_speaker}: {' '.join(speaker_text)}")
        
        return '\n'.join(lines).encode('utf-8')
    
    def _export_srt(self, session_state: SessionState) -> bytes:
        """Export session as SRT subtitle format"""
        lines = []
        subtitle_index = 1
        
        for segment in session_state.transcription_segments:
            start_time = segment.get('start_time', 0)
            end_time = segment.get('end_time', start_time + 2)
            text = segment.get('text', '').strip()
            speaker_id = segment.get('speaker_id', '')
            
            if text:
                # Format timestamps
                start_srt = self._seconds_to_srt_time(start_time)
                end_srt = self._seconds_to_srt_time(end_time)
                
                # Add speaker prefix if available
                if speaker_id and speaker_id != 'Unknown':
                    text = f"[{speaker_id}] {text}"
                
                lines.append(str(subtitle_index))
                lines.append(f"{start_srt} --> {end_srt}")
                lines.append(text)
                lines.append("")
                
                subtitle_index += 1
        
        return '\n'.join(lines).encode('utf-8')
    
    def _export_csv(self, session_state: SessionState) -> bytes:
        """Export session as CSV"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'timestamp', 'speaker_id', 'text', 'confidence', 
            'start_time', 'end_time', 'is_final'
        ])
        
        # Data rows
        for segment in session_state.transcription_segments:
            writer.writerow([
                segment.get('timestamp', ''),
                segment.get('speaker_id', ''),
                segment.get('text', ''),
                segment.get('confidence', ''),
                segment.get('start_time', ''),
                segment.get('end_time', ''),
                segment.get('is_final', False)
            ])
        
        return output.getvalue().encode('utf-8')
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _initialize_session_metrics(self, session_id: str):
        """Initialize metrics tracking for session"""
        self.session_metrics[session_id] = {
            'start_time': time.time(),
            'audio_chunks_processed': 0,
            'transcription_requests': 0,
            'average_latency': 0.0,
            'error_count': 0,
            'speaker_changes': 0,
            'quality_scores': []
        }
    
    def _update_session_metrics(self, session_id: str, update_data: Dict[str, Any]):
        """Update session metrics"""
        try:
            if session_id not in self.session_metrics:
                self._initialize_session_metrics(session_id)
            
            metrics = self.session_metrics[session_id]
            
            # Update based on data type
            if 'transcription_segments' in update_data:
                metrics['transcription_requests'] += len(update_data['transcription_segments'])
            
            if 'audio_metrics_history' in update_data:
                metrics['audio_chunks_processed'] += len(update_data['audio_metrics_history'])
            
            if 'processing_events' in update_data:
                for event in update_data['processing_events']:
                    if event.get('event') == 'speaker_change':
                        metrics['speaker_changes'] += 1
                    elif event.get('event') == 'error':
                        metrics['error_count'] += 1
                        
        except Exception as e:
            logger.warning(f"⚠️ Metrics update failed: {e}")
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        def background_worker():
            while self._background_tasks_active:
                try:
                    # Auto-save active sessions
                    for session_id, session_state in self.active_sessions.items():
                        self.persistence.save_session(session_state)
                    
                    # Clean up old inactive sessions
                    self._cleanup_inactive_sessions()
                    
                    # Update global statistics
                    self._update_global_stats()
                    
                    time.sleep(self.auto_save_interval)
                    
                except Exception as e:
                    logger.error(f"❌ Background task error: {e}")
                    time.sleep(5)
        
        worker_thread = threading.Thread(target=background_worker, daemon=True)
        worker_thread.start()
    
    def _cleanup_inactive_sessions(self):
        """Remove inactive sessions from memory"""
        try:
            current_time = time.time()
            inactive_threshold = 3600  # 1 hour
            
            inactive_sessions = []
            for session_id, session_state in self.active_sessions.items():
                last_updated = session_state.metadata.updated_at.timestamp()
                if current_time - last_updated > inactive_threshold:
                    inactive_sessions.append(session_id)
            
            for session_id in inactive_sessions:
                del self.active_sessions[session_id]
                if session_id in self.session_metrics:
                    del self.session_metrics[session_id]
                
                self.global_stats['active_sessions'] -= 1
                logger.debug(f"🧹 Cleaned up inactive session: {session_id}")
                
        except Exception as e:
            logger.warning(f"⚠️ Session cleanup failed: {e}")
    
    def _update_global_stats(self):
        """Update global statistics"""
        try:
            # Update from active sessions
            total_words = 0
            total_time = 0
            quality_scores = []
            
            for session_state in self.active_sessions.values():
                total_words += session_state.metadata.transcription_word_count
                total_time += session_state.metadata.total_duration
                if session_state.metadata.quality_score > 0:
                    quality_scores.append(session_state.metadata.quality_score)
            
            self.global_stats['total_words_transcribed'] = total_words
            self.global_stats['total_transcription_time'] = total_time
            
            if quality_scores:
                self.global_stats['average_session_quality'] = sum(quality_scores) / len(quality_scores)
                
        except Exception as e:
            logger.warning(f"⚠️ Global stats update failed: {e}")
    
    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session analytics"""
        try:
            session_state = self.get_session(session_id)
            if not session_state:
                return {}
            
            metrics = self.session_metrics.get(session_id, {})
            
            return {
                'session_metadata': asdict(session_state.metadata),
                'processing_metrics': metrics,
                'performance_summary': {
                    'total_segments': len(session_state.transcription_segments),
                    'total_speakers': len(session_state.speaker_profiles),
                    'total_events': len(session_state.processing_events),
                    'error_rate': metrics.get('error_count', 0) / max(1, metrics.get('transcription_requests', 1)),
                    'average_quality': session_state.metadata.quality_score
                },
                'checkpoints_available': len(session_state.checkpoints)
            }
            
        except Exception as e:
            logger.error(f"❌ Analytics generation failed: {e}")
            return {}
    
    def get_global_analytics(self) -> Dict[str, Any]:
        """Get global system analytics"""
        return {
            'global_stats': self.global_stats,
            'active_sessions_count': len(self.active_sessions),
            'total_sessions_in_memory': len(self.active_sessions),
            'system_uptime': time.time() - getattr(self, '_start_time', time.time()),
            'background_tasks_active': self._background_tasks_active
        }
    
    def close(self):
        """Gracefully close session manager"""
        try:
            self._background_tasks_active = False
            
            # Save all active sessions
            for session_id, session_state in self.active_sessions.items():
                self.persistence.save_session(session_state)
            
            logger.info("🔒 Enhanced Session Manager closed gracefully")
            
        except Exception as e:
            logger.error(f"❌ Session manager close failed: {e}")

# Global session manager instance
_session_manager = None
_session_manager_lock = threading.Lock()

def get_enhanced_session_manager() -> EnhancedSessionManager:
    """Get global enhanced session manager instance"""
    global _session_manager
    
    with _session_manager_lock:
        if _session_manager is None:
            _session_manager = EnhancedSessionManager()
        return _session_manager

logger.info("✅ Enhanced Session Manager module initialized")