"""
Meeting Session Model
Represents a meeting session with metadata and transcription settings.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, JSON
from app_refactored import db

class Session(db.Model):
    """
    Meeting session model for storing session metadata and settings.
    Each session represents a single meeting or recording session.
    """
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    
    # Session identification
    session_id = Column(String(128), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False, default='Untitled Meeting')
    description = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Session status and settings
    status = Column(String(50), default='created', nullable=False)  # created, active, paused, completed, error
    language = Column(String(10), default='en', nullable=False)
    
    # Real-time settings
    enable_realtime = Column(Boolean, default=True)
    enable_speaker_detection = Column(Boolean, default=True)
    enable_sentiment_analysis = Column(Boolean, default=False)
    
    # Audio configuration
    sample_rate = Column(Integer, default=16000)
    chunk_size = Column(Integer, default=1024)
    min_confidence = Column(Float, default=0.7)
    
    # VAD configuration
    vad_sensitivity = Column(Float, default=0.5)
    vad_min_speech_duration = Column(Integer, default=300)  # ms
    vad_min_silence_duration = Column(Integer, default=500)  # ms
    
    # Session statistics
    total_duration = Column(Float, default=0.0)  # seconds
    total_segments = Column(Integer, default=0)
    total_speakers = Column(Integer, default=0)
    average_confidence = Column(Float, default=0.0)
    
    # Metadata and custom settings
    session_metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # User and organization (for future multi-tenancy)
    user_id = Column(String(128))
    organization_id = Column(String(128))
    
    def __repr__(self):
        return f'<Session {self.session_id}: {self.title}>'
    
    @property
    def is_active(self):
        """Check if session is currently active."""
        return self.status == 'active'
    
    @property
    def duration_minutes(self):
        """Get session duration in minutes."""
        return self.total_duration / 60.0 if self.total_duration else 0.0
    
    def to_dict(self):
        """Convert session to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'language': self.language,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'total_duration': self.total_duration,
            'total_segments': self.total_segments,
            'total_speakers': self.total_speakers,
            'average_confidence': self.average_confidence,
            'enable_realtime': self.enable_realtime,
            'enable_speaker_detection': self.enable_speaker_detection,
            'enable_sentiment_analysis': self.enable_sentiment_analysis,
            'session_metadata': self.session_metadata,
            'tags': self.tags,
        }
    
    def start_session(self):
        """Mark session as started."""
        self.status = 'active'
        self.started_at = datetime.utcnow()
        db.session.commit()
    
    def end_session(self):
        """Mark session as completed."""
        self.status = 'completed'
        self.ended_at = datetime.utcnow()
        if self.started_at:
            self.total_duration = (self.ended_at - self.started_at).total_seconds()
        db.session.commit()
    
    def pause_session(self):
        """Pause the session."""
        self.status = 'paused'
        db.session.commit()
    
    def resume_session(self):
        """Resume the session."""
        self.status = 'active'
        db.session.commit()
    
    def add_segment(self):
        """Increment segment count."""
        self.total_segments += 1
        db.session.commit()
    
    def update_stats(self, confidence=None, speaker_count=None):
        """Update session statistics."""
        if confidence is not None:
            # Update average confidence using running average
            total_conf = self.average_confidence * (self.total_segments - 1) + confidence
            self.average_confidence = total_conf / self.total_segments
        
        if speaker_count is not None and speaker_count > self.total_speakers:
            self.total_speakers = speaker_count
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
