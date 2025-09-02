"""
Streaming-specific database models for real-time transcription
"""

from app import db
from datetime import datetime
from sqlalchemy import JSON


class TranscriptionSession(db.Model):
    """Model for tracking transcription sessions with comprehensive analytics"""
    __tablename__ = 'transcription_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, nullable=True)  # Remove FK constraint for now
    
    # Session metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Float, nullable=True)
    
    # Performance metrics
    total_chunks = db.Column(db.Integer, default=0)
    successful_chunks = db.Column(db.Integer, default=0)
    failed_chunks = db.Column(db.Integer, default=0)
    dropped_chunks = db.Column(db.Integer, default=0)
    avg_latency_ms = db.Column(db.Float, default=0.0)
    max_latency_ms = db.Column(db.Float, default=0.0)
    p95_latency_ms = db.Column(db.Float, default=0.0)
    
    # Quality metrics  
    avg_confidence = db.Column(db.Float, default=0.0)
    word_error_rate = db.Column(db.Float, default=0.0)
    semantic_drift_score = db.Column(db.Float, default=0.0)
    total_words = db.Column(db.Integer, default=0)
    
    # Audio metrics
    total_audio_duration_ms = db.Column(db.Float, default=0.0)
    audio_quality_score = db.Column(db.Float, default=0.0)
    silence_ratio = db.Column(db.Float, default=0.0)
    
    # System performance
    memory_peak_mb = db.Column(db.Float, default=0.0)
    cpu_avg_percent = db.Column(db.Float, default=0.0)
    event_loop_blocking_ms = db.Column(db.Float, default=0.0)
    
    # Status and error tracking
    status = db.Column(db.String(50), default='active')  # active, completed, failed, abandoned
    error_count = db.Column(db.Integer, default=0)
    retry_count = db.Column(db.Integer, default=0)
    
    # Configuration
    audio_format = db.Column(db.String(50), default='webm')
    sample_rate = db.Column(db.Integer, default=16000)
    model_used = db.Column(db.String(100), default='whisper-1')
    
    # Additional metadata
    client_info = db.Column(JSON, nullable=True)  # Browser, device, etc
    final_transcript = db.Column(db.Text, nullable=True)
    
    # Relationships
    chunks = db.relationship('TranscriptionChunk', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<TranscriptionSession {self.session_id}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'duration_seconds': self.duration_seconds,
            'performance_metrics': {
                'total_chunks': self.total_chunks,
                'successful_chunks': self.successful_chunks,
                'failed_chunks': self.failed_chunks,
                'avg_latency_ms': self.avg_latency_ms,
                'max_latency_ms': self.max_latency_ms,
                'p95_latency_ms': self.p95_latency_ms,
            },
            'quality_metrics': {
                'avg_confidence': self.avg_confidence,
                'word_error_rate': self.word_error_rate,
                'semantic_drift_score': self.semantic_drift_score,
                'total_words': self.total_words,
            },
            'status': self.status,
            'final_transcript': self.final_transcript
        }


class TranscriptionChunk(db.Model):
    """Model for individual transcription chunks with detailed metrics"""
    __tablename__ = 'transcription_chunks'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), db.ForeignKey('transcription_sessions.session_id'), nullable=False)
    chunk_id = db.Column(db.String(100), nullable=False)
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processing_started_at = db.Column(db.DateTime, nullable=True)
    processing_completed_at = db.Column(db.DateTime, nullable=True)
    processing_time_ms = db.Column(db.Float, nullable=True)
    
    # Audio data
    audio_size_bytes = db.Column(db.Integer, nullable=True)
    audio_duration_ms = db.Column(db.Float, nullable=True)
    audio_format = db.Column(db.String(50), nullable=True)
    has_speech = db.Column(db.Boolean, default=True)
    vad_confidence = db.Column(db.Float, nullable=True)
    
    # Transcription results
    transcript_text = db.Column(db.Text, nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)
    word_count = db.Column(db.Integer, default=0)
    is_interim = db.Column(db.Boolean, default=False)
    is_final = db.Column(db.Boolean, default=False)
    
    # Quality metrics
    duplicate_of_chunk = db.Column(db.String(100), nullable=True)  # For deduplication tracking
    semantic_similarity = db.Column(db.Float, nullable=True)  # Compared to previous chunks
    
    # Processing details
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    error_message = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    
    # Model and configuration
    model_used = db.Column(db.String(100), default='whisper-1')
    temperature = db.Column(db.Float, default=0.2)
    language_detected = db.Column(db.String(10), nullable=True)
    
    def __repr__(self):
        return f'<TranscriptionChunk {self.session_id}-{self.chunk_id}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'chunk_id': self.chunk_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processing_time_ms': self.processing_time_ms,
            'transcript_text': self.transcript_text,
            'confidence_score': self.confidence_score,
            'word_count': self.word_count,
            'is_interim': self.is_interim,
            'is_final': self.is_final,
            'status': self.status,
            'audio_duration_ms': self.audio_duration_ms,
            'has_speech': self.has_speech
        }


class SessionAnalytics(db.Model):
    """Aggregated analytics for performance monitoring and optimization"""
    __tablename__ = 'session_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    hour = db.Column(db.Integer, nullable=False)  # 0-23
    
    # Volume metrics
    total_sessions = db.Column(db.Integer, default=0)
    completed_sessions = db.Column(db.Integer, default=0)
    failed_sessions = db.Column(db.Integer, default=0)
    total_chunks = db.Column(db.Integer, default=0)
    
    # Performance aggregates
    avg_latency_ms = db.Column(db.Float, default=0.0)
    p95_latency_ms = db.Column(db.Float, default=0.0)
    avg_wer = db.Column(db.Float, default=0.0)
    avg_confidence = db.Column(db.Float, default=0.0)
    
    # System metrics
    avg_memory_usage_mb = db.Column(db.Float, default=0.0)
    avg_cpu_usage_percent = db.Column(db.Float, default=0.0)
    error_rate_percent = db.Column(db.Float, default=0.0)
    
    def __repr__(self):
        return f'<SessionAnalytics {self.date} {self.hour:02d}:00>'