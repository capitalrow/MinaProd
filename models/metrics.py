"""
🎯 OBSERVER METRICS - Comprehensive Performance & Quality Metrics

This module implements system performance metrics and linguistic/semantic metrics
for live transcription observability, as requested in OBSERVER-SYS and OBSERVER-LING.
"""

from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import Integer, Float, String, Text, DateTime, JSON, ForeignKey, BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from extensions import db

if TYPE_CHECKING:
    from .session import Session


class ChunkMetric(Base):
    """
    🔍 OBSERVER-SYS: Per-chunk system performance and linguistic metrics.
    
    Tracks detailed metrics for each audio chunk processed through the pipeline:
    - System performance: end-to-end latency, processing times, resource usage
    - Linguistic quality: confidence, transcript changes, interim updates
    """
    __tablename__ = "chunk_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    chunk_id: Mapped[str] = mapped_column(String(64), index=True)  # Unique chunk identifier
    
    # 🎯 OBSERVER-SYS: System Performance Timestamps (all in milliseconds)
    t_client_chunk_start: Mapped[Optional[int]] = mapped_column(BigInteger)  # Client audio chunk start
    t_client_chunk_end: Mapped[Optional[int]] = mapped_column(BigInteger)    # Client audio chunk end  
    t_client_tx: Mapped[Optional[int]] = mapped_column(BigInteger)           # Client transmission time
    t_ws_rx: Mapped[Optional[int]] = mapped_column(BigInteger)               # WebSocket receive time
    t_decode_start: Mapped[Optional[int]] = mapped_column(BigInteger)        # Audio decode start
    t_decode_done: Mapped[Optional[int]] = mapped_column(BigInteger)         # Audio decode complete
    t_api_start: Mapped[Optional[int]] = mapped_column(BigInteger)           # Whisper API call start
    t_api_done: Mapped[Optional[int]] = mapped_column(BigInteger)            # Whisper API call complete
    t_emit_interim: Mapped[Optional[int]] = mapped_column(BigInteger)        # Interim result emit time
    t_emit_final: Mapped[Optional[int]] = mapped_column(BigInteger)          # Final result emit time
    t_client_render_interim: Mapped[Optional[int]] = mapped_column(BigInteger)  # Client interim render
    t_client_render_final: Mapped[Optional[int]] = mapped_column(BigInteger)    # Client final render
    
    # 🎯 OBSERVER-SYS: Computed Performance Metrics
    end_to_end_latency: Mapped[Optional[float]] = mapped_column(Float)       # client_render_final - client_chunk_end
    partial_result_latency: Mapped[Optional[float]] = mapped_column(Float)   # client_render_interim - client_chunk_start
    finalization_latency: Mapped[Optional[float]] = mapped_column(Float)     # client_render_final - end_of_speech
    real_time_factor: Mapped[Optional[float]] = mapped_column(Float)         # processing_time / audio_duration
    throughput: Mapped[Optional[float]] = mapped_column(Float)               # audio_sec_processed / sec_wall_time
    
    # 🎯 OBSERVER-SYS: Resource Usage
    cpu_usage: Mapped[Optional[float]] = mapped_column(Float)                # CPU % during processing
    memory_usage: Mapped[Optional[float]] = mapped_column(Float)             # Memory MB during processing
    network_bytes_sent: Mapped[Optional[int]] = mapped_column(BigInteger)    # Bytes sent to API
    network_bytes_recv: Mapped[Optional[int]] = mapped_column(BigInteger)    # Bytes received from API
    
    # 🎯 OBSERVER-LING: Linguistic & Semantic Quality Metrics
    interim_updates_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)     # Number of interim updates
    transcript_change_rate: Mapped[Optional[float]] = mapped_column(Float)               # edit_distance(interim, final)/len(final)
    avg_confidence_score: Mapped[Optional[float]] = mapped_column(Float)                 # Average ASR confidence
    word_count: Mapped[Optional[int]] = mapped_column(Integer)                           # Words in final transcript
    
    # System Status
    error_count: Mapped[int] = mapped_column(Integer, default=0)             # Errors during processing
    status: Mapped[str] = mapped_column(String(32), default="completed")     # completed|error|timeout
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    session: Mapped["Session"] = relationship(back_populates="chunk_metrics")


class SessionMetric(Base):
    """
    📊 OBSERVER-SYS: Session-level aggregated performance and quality metrics.
    
    Aggregates metrics across all chunks in a session for overall assessment:
    - System performance: average latencies, resource usage trends, error rates
    - Linguistic quality: overall accuracy, confidence patterns, refinement effectiveness
    """
    __tablename__ = "session_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), unique=True, index=True)
    
    # 🎯 OBSERVER-SYS: Aggregated System Performance Metrics
    avg_end_to_end_latency: Mapped[Optional[float]] = mapped_column(Float)
    avg_partial_result_latency: Mapped[Optional[float]] = mapped_column(Float)
    avg_finalization_latency: Mapped[Optional[float]] = mapped_column(Float)
    avg_real_time_factor: Mapped[Optional[float]] = mapped_column(Float)
    avg_throughput: Mapped[Optional[float]] = mapped_column(Float)
    
    p95_end_to_end_latency: Mapped[Optional[float]] = mapped_column(Float)   # 95th percentile
    p99_end_to_end_latency: Mapped[Optional[float]] = mapped_column(Float)   # 99th percentile
    
    # Resource Usage Trends
    avg_cpu_usage: Mapped[Optional[float]] = mapped_column(Float)
    peak_cpu_usage: Mapped[Optional[float]] = mapped_column(Float)
    avg_memory_usage: Mapped[Optional[float]] = mapped_column(Float)
    peak_memory_usage: Mapped[Optional[float]] = mapped_column(Float)
    total_network_usage: Mapped[Optional[int]] = mapped_column(BigInteger)   # Total bytes transferred
    
    # System Health
    total_chunks: Mapped[int] = mapped_column(Integer, default=0)
    successful_chunks: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    timeout_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 🎯 OBSERVER-LING: Session-Level Quality Metrics
    word_error_rate: Mapped[Optional[float]] = mapped_column(Float)          # Overall WER (if reference available)
    sentence_error_rate: Mapped[Optional[float]] = mapped_column(Float)      # Sentence-level error rate
    avg_confidence_score: Mapped[Optional[float]] = mapped_column(Float)     # Session average confidence
    total_interim_updates: Mapped[int] = mapped_column(Integer, default=0)   # Total interim updates across session
    avg_transcript_change_rate: Mapped[Optional[float]] = mapped_column(Float)  # Average refinement rate
    
    # Quality-Delay Tradeoff Assessment
    quality_delay_tradeoff: Mapped[Optional[str]] = mapped_column(Text)      # JSON: {latency: X, quality_proxy: Y}
    
    # Session Context
    total_words: Mapped[Optional[int]] = mapped_column(Integer)              # Total words transcribed
    total_duration_sec: Mapped[Optional[float]] = mapped_column(Float)      # Total session duration
    audio_quality_score: Mapped[Optional[float]] = mapped_column(Float)     # Overall audio quality assessment
    
    # Metadata
    reference_transcript_available: Mapped[bool] = mapped_column(String(5), default='false')  # For test mode
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    session: Mapped["Session"] = relationship(back_populates="session_metrics")


# 🎯 Add relationships to existing Session model (to be added via migration)
"""
Add to models/session.py:

# Metrics relationships
chunk_metrics: Mapped[list["ChunkMetric"]] = relationship(
    back_populates="session", cascade="all, delete-orphan"
)
session_metrics: Mapped[Optional["SessionMetric"]] = relationship(
    back_populates="session", cascade="all, delete-orphan", uselist=False
)
"""