"""
Transcription Segment Model
Represents individual transcription segments within a meeting session.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app_refactored import db

class Segment(db.Model):
    """
    Transcription segment model for storing individual pieces of transcribed text.
    Each segment represents a continuous piece of speech from a single speaker.
    """
    __tablename__ = 'segments'
    
    id = Column(Integer, primary_key=True)
    
    # Relationship to session
    session_id = Column(String(128), ForeignKey('sessions.session_id'), nullable=False, index=True)
    session = relationship('Session', backref='segments')
    
    # Segment identification
    segment_id = Column(String(128), nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False)  # Order within session
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    start_time = Column(Float, nullable=False)  # seconds from session start
    end_time = Column(Float, nullable=False)    # seconds from session start
    
    # Transcription content
    text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    is_final = Column(Boolean, default=False, nullable=False)
    
    # Speaker information
    speaker_id = Column(String(128))  # e.g., "speaker_1", "speaker_2"
    speaker_name = Column(String(255))  # human-readable speaker name
    speaker_confidence = Column(Float, default=0.0)
    
    # Audio processing metadata
    audio_duration = Column(Float)  # duration of audio chunk in seconds
    sample_rate = Column(Integer, default=16000)
    channels = Column(Integer, default=1)
    
    # Language and processing
    language = Column(String(10), default='en')
    language_confidence = Column(Float, default=0.0)
    
    # Sentiment analysis (future enhancement)
    sentiment_score = Column(Float)  # -1 to 1 scale
    sentiment_label = Column(String(50))  # positive, negative, neutral
    sentiment_confidence = Column(Float)
    
    # Processing status
    status = Column(String(50), default='processed', nullable=False)  # interim, processed, error
    error_message = Column(Text)
    
    # Additional metadata
    segment_metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # Index for efficient querying
    __table_args__ = (
        db.Index('ix_segments_session_sequence', 'session_id', 'sequence_number'),
        db.Index('ix_segments_session_time', 'session_id', 'start_time'),
        db.Index('ix_segments_speaker', 'session_id', 'speaker_id'),
    )
    
    def __repr__(self):
        return f'<Segment {self.segment_id}: "{self.text[:50]}...">'
    
    @property
    def duration(self):
        """Get segment duration in seconds."""
        return self.end_time - self.start_time if self.end_time and self.start_time else 0.0
    
    @property
    def start_time_formatted(self):
        """Get formatted start time (MM:SS)."""
        minutes = int(self.start_time // 60)
        seconds = int(self.start_time % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def is_high_confidence(self):
        """Check if segment has high confidence."""
        return self.confidence >= 0.8
    
    def to_dict(self):
        """Convert segment to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'segment_id': self.segment_id,
            'session_id': self.session_id,
            'sequence_number': self.sequence_number,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'start_time_formatted': self.start_time_formatted,
            'text': self.text,
            'confidence': self.confidence,
            'is_final': self.is_final,
            'is_high_confidence': self.is_high_confidence,
            'speaker_id': self.speaker_id,
            'speaker_name': self.speaker_name,
            'speaker_confidence': self.speaker_confidence,
            'language': self.language,
            'language_confidence': self.language_confidence,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label,
            'sentiment_confidence': self.sentiment_confidence,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'segment_metadata': self.segment_metadata,
            'tags': self.tags,
        }
    
    def finalize(self):
        """Mark segment as final and processed."""
        self.is_final = True
        self.status = 'processed'
        db.session.commit()
    
    def update_confidence(self, confidence):
        """Update transcription confidence."""
        self.confidence = confidence
        db.session.commit()
    
    def assign_speaker(self, speaker_id, speaker_name=None, confidence=0.0):
        """Assign speaker information to segment."""
        self.speaker_id = speaker_id
        if speaker_name:
            self.speaker_name = speaker_name
        self.speaker_confidence = confidence
        db.session.commit()
    
    def add_sentiment(self, score, label, confidence=0.0):
        """Add sentiment analysis results."""
        self.sentiment_score = score
        self.sentiment_label = label
        self.sentiment_confidence = confidence
        db.session.commit()
    
    def mark_error(self, error_message):
        """Mark segment as error with message."""
        self.status = 'error'
        self.error_message = error_message
        db.session.commit()
    
    @classmethod
    def get_session_segments(cls, session_id, limit=None, offset=None):
        """Get segments for a session ordered by sequence."""
        query = cls.query.filter_by(session_id=session_id).order_by(cls.sequence_number)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_speaker_segments(cls, session_id, speaker_id):
        """Get all segments for a specific speaker in a session."""
        return cls.query.filter_by(
            session_id=session_id, 
            speaker_id=speaker_id
        ).order_by(cls.sequence_number).all()
    
    @classmethod
    def get_final_segments(cls, session_id):
        """Get only final segments for a session."""
        return cls.query.filter_by(
            session_id=session_id, 
            is_final=True
        ).order_by(cls.sequence_number).all()
