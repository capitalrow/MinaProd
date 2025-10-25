"""
Analytics Model for Meeting Insights and Performance Metrics
SQLAlchemy 2.0-safe model for comprehensive meeting analytics and AI-powered insights.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Float, Text, Boolean, ForeignKey, func, JSON, Index
from .base import Base

# Forward reference for type checking
if TYPE_CHECKING:
    from .meeting import Meeting


class Analytics(Base):
    """
    Analytics model for comprehensive meeting insights, performance metrics, and AI-powered analysis.
    Provides detailed analytics for meetings including engagement, productivity, and sentiment analysis.
    """
    __tablename__ = "analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Session and Meeting relationships (70% sessions don't create meetings)
    session_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    meeting_id: Mapped[Optional[int]] = mapped_column(ForeignKey("meetings.id"), nullable=True, unique=True)
    meeting: Mapped[Optional["Meeting"]] = relationship(back_populates="analytics")
    
    # Overall meeting metrics
    total_duration_minutes: Mapped[Optional[float]] = mapped_column(Float)
    actual_vs_scheduled_ratio: Mapped[Optional[float]] = mapped_column(Float)  # Actual/Scheduled duration
    participant_count: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Engagement metrics
    overall_engagement_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-1 scale
    average_talk_time_per_person: Mapped[Optional[float]] = mapped_column(Float)  # Minutes
    talk_time_distribution: Mapped[Optional[dict]] = mapped_column(JSON)  # Per participant breakdown
    interruption_frequency: Mapped[Optional[float]] = mapped_column(Float)  # Per minute
    
    # Sentiment analysis
    overall_sentiment_score: Mapped[Optional[float]] = mapped_column(Float)  # -1 to 1
    sentiment_trend: Mapped[Optional[list]] = mapped_column(JSON)  # Time-series sentiment data
    positive_moments: Mapped[Optional[list]] = mapped_column(JSON)  # Timestamps of positive peaks
    negative_moments: Mapped[Optional[list]] = mapped_column(JSON)  # Timestamps of negative peaks
    
    # Productivity metrics
    decisions_made_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    action_items_created: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    agenda_completion_rate: Mapped[Optional[float]] = mapped_column(Float)  # 0-1 scale
    meeting_effectiveness_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-1 scale
    
    # Content analysis
    word_count: Mapped[Optional[int]] = mapped_column(Integer)
    unique_speakers: Mapped[Optional[int]] = mapped_column(Integer)
    topic_keywords: Mapped[Optional[list]] = mapped_column(JSON)  # Most mentioned keywords
    key_topics: Mapped[Optional[list]] = mapped_column(JSON)  # AI-identified main topics
    
    # Communication patterns
    question_count: Mapped[Optional[int]] = mapped_column(Integer)
    idea_count: Mapped[Optional[int]] = mapped_column(Integer)
    disagreement_count: Mapped[Optional[int]] = mapped_column(Integer)
    consensus_moments: Mapped[Optional[list]] = mapped_column(JSON)  # Timestamps of agreement
    
    # Time management
    meeting_efficiency_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-1 scale
    time_spent_on_agenda: Mapped[Optional[float]] = mapped_column(Float)  # Percentage
    off_topic_time_percentage: Mapped[Optional[float]] = mapped_column(Float)
    
    # Participant insights
    most_active_participant: Mapped[Optional[str]] = mapped_column(String(128))
    quietest_participant: Mapped[Optional[str]] = mapped_column(String(128))
    dominant_speaker_percentage: Mapped[Optional[float]] = mapped_column(Float)
    balanced_participation: Mapped[Optional[bool]] = mapped_column(Boolean)
    
    # Follow-up analysis
    follow_up_required: Mapped[Optional[bool]] = mapped_column(Boolean)
    next_steps_clarity: Mapped[Optional[float]] = mapped_column(Float)  # 0-1 scale
    unresolved_issues_count: Mapped[Optional[int]] = mapped_column(Integer)
    
    # AI insights
    meeting_summary_quality: Mapped[Optional[float]] = mapped_column(Float)  # 0-1 scale
    ai_confidence_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-1 scale
    insights_generated: Mapped[Optional[list]] = mapped_column(JSON)  # AI-generated insights
    recommendations: Mapped[Optional[list]] = mapped_column(JSON)  # Improvement recommendations
    
    # Comparison metrics
    vs_team_average: Mapped[Optional[dict]] = mapped_column(JSON)  # How this meeting compares
    improvement_areas: Mapped[Optional[list]] = mapped_column(JSON)  # Areas for improvement
    
    # Processing status
    analysis_status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, processing, completed, failed
    analysis_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    analysis_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    analysis_error: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Database indexes for query optimization
    __table_args__ = (
        # Composite index for recent analytics queries (status + created)
        Index('ix_analytics_status_created', 'analysis_status', 'created_at'),
    )

    def __repr__(self):
        return f'<Analytics for Meeting {self.meeting_id}>'

    @property
    def is_analysis_complete(self) -> bool:
        """Check if analytics analysis is complete."""
        return self.analysis_status == "completed"

    @property
    def meeting_grade(self) -> str:
        """Get letter grade for meeting effectiveness."""
        if not self.meeting_effectiveness_score:
            return "N/A"
        
        score = self.meeting_effectiveness_score
        if score >= 0.9:
            return "A+"
        elif score >= 0.8:
            return "A"
        elif score >= 0.7:
            return "B"
        elif score >= 0.6:
            return "C"
        elif score >= 0.5:
            return "D"
        else:
            return "F"

    @property
    def engagement_level(self) -> str:
        """Get engagement level description."""
        if not self.overall_engagement_score:
            return "Unknown"
        
        score = self.overall_engagement_score
        if score >= 0.8:
            return "High"
        elif score >= 0.6:
            return "Medium"
        elif score >= 0.4:
            return "Low"
        else:
            return "Very Low"

    @property
    def sentiment_description(self) -> str:
        """Get sentiment description."""
        if self.overall_sentiment_score is None:
            return "Unknown"
        
        score = self.overall_sentiment_score
        if score >= 0.6:
            return "Very Positive"
        elif score >= 0.2:
            return "Positive"
        elif score >= -0.2:
            return "Neutral"
        elif score >= -0.6:
            return "Negative"
        else:
            return "Very Negative"

    def start_analysis(self):
        """Mark analytics processing as started."""
        self.analysis_status = "processing"
        self.analysis_started_at = datetime.utcnow()

    def complete_analysis(self):
        """Mark analytics processing as completed."""
        self.analysis_status = "completed"
        self.analysis_completed_at = datetime.utcnow()

    def fail_analysis(self, error: str):
        """Mark analytics processing as failed."""
        self.analysis_status = "failed"
        self.analysis_error = error

    def calculate_effectiveness_score(self) -> float:
        """Calculate overall meeting effectiveness score based on multiple factors."""
        factors = []
        
        # Engagement factor (0.3 weight)
        if self.overall_engagement_score is not None:
            factors.append(self.overall_engagement_score * 0.3)
        
        # Productivity factor (0.4 weight)
        productivity = 0
        if self.action_items_created and self.action_items_created > 0:
            productivity += 0.3
        if self.decisions_made_count and self.decisions_made_count > 0:
            productivity += 0.3
        if self.agenda_completion_rate:
            productivity += self.agenda_completion_rate * 0.4
        factors.append(productivity * 0.4)
        
        # Efficiency factor (0.3 weight)
        if self.meeting_efficiency_score is not None:
            factors.append(self.meeting_efficiency_score * 0.3)
        
        # Calculate weighted average
        if factors:
            self.meeting_effectiveness_score = sum(factors) / len(factors)
        else:
            self.meeting_effectiveness_score = 0.0
            
        return self.meeting_effectiveness_score

    def to_dict(self, include_detailed_data=False):
        """Convert analytics to dictionary for JSON serialization."""
        data = {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'total_duration_minutes': self.total_duration_minutes,
            'actual_vs_scheduled_ratio': self.actual_vs_scheduled_ratio,
            'participant_count': self.participant_count,
            'overall_engagement_score': self.overall_engagement_score,
            'engagement_level': self.engagement_level,
            'overall_sentiment_score': self.overall_sentiment_score,
            'sentiment_description': self.sentiment_description,
            'decisions_made_count': self.decisions_made_count,
            'action_items_created': self.action_items_created,
            'agenda_completion_rate': self.agenda_completion_rate,
            'meeting_effectiveness_score': self.meeting_effectiveness_score,
            'meeting_grade': self.meeting_grade,
            'word_count': self.word_count,
            'unique_speakers': self.unique_speakers,
            'question_count': self.question_count,
            'idea_count': self.idea_count,
            'most_active_participant': self.most_active_participant,
            'quietest_participant': self.quietest_participant,
            'dominant_speaker_percentage': self.dominant_speaker_percentage,
            'balanced_participation': self.balanced_participation,
            'follow_up_required': self.follow_up_required,
            'next_steps_clarity': self.next_steps_clarity,
            'unresolved_issues_count': self.unresolved_issues_count,
            'ai_confidence_score': self.ai_confidence_score,
            'analysis_status': self.analysis_status,
            'is_analysis_complete': self.is_analysis_complete,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_detailed_data:
            data.update({
                'talk_time_distribution': self.talk_time_distribution,
                'sentiment_trend': self.sentiment_trend,
                'positive_moments': self.positive_moments,
                'negative_moments': self.negative_moments,
                'topic_keywords': self.topic_keywords,
                'key_topics': self.key_topics,
                'consensus_moments': self.consensus_moments,
                'insights_generated': self.insights_generated,
                'recommendations': self.recommendations,
                'vs_team_average': self.vs_team_average,
                'improvement_areas': self.improvement_areas
            })
            
        return data