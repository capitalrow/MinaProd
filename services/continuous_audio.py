#!/usr/bin/env python3
# 🎵 Production Feature: Continuous Audio Capture with Overlapping Context
"""
Implements continuous audio capture with overlapping context windows to prevent
cut-off phrases and improve transcription accuracy.

Addresses: "Streaming Transcription Pipeline" gap from production assessment.

Key Features:
- Overlapping audio contexts to prevent phrase cut-offs
- Sliding window buffer management
- Context-aware chunk processing
- Memory-efficient audio stream handling
"""

import logging
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class AudioChunk:
    """Audio chunk with timing and context information."""
    data: bytes
    timestamp: float
    duration_s: float
    chunk_id: str
    mime_type: str
    rms: float = 0.0
    context_start: float = 0.0  # Start time of overlapping context
    context_end: float = 0.0    # End time of overlapping context
    
class ContinuousAudioCapture:
    """
    🎵 Production-grade continuous audio capture with overlapping context.
    
    Maintains sliding windows of audio to provide context for better transcription
    accuracy and prevents phrase cut-offs at chunk boundaries.
    """
    
    def __init__(self, overlap_duration_s: float = 2.0, max_chunk_duration_s: float = 10.0, 
                 buffer_size_mb: int = 50):
        self.overlap_duration_s = overlap_duration_s
        self.max_chunk_duration_s = max_chunk_duration_s
        self.max_buffer_size = buffer_size_mb * 1024 * 1024  # Convert to bytes
        
        # Audio buffer management
        self.audio_buffer = deque()  # Store AudioChunk objects
        self.current_buffer_size = 0
        self.buffer_lock = threading.RLock()
        
        # Context tracking
        self.last_context_end = 0.0
        self.chunk_sequence = 0
        
        # Metrics
        self.total_chunks_processed = 0
        self.total_context_overlaps = 0
        self.buffer_overflows = 0
        self.avg_chunk_duration = 0.0
        
        logger.info(f"🎵 Continuous audio capture initialized: {overlap_duration_s}s overlap, "
                   f"{max_chunk_duration_s}s max chunk, {buffer_size_mb}MB buffer")
    
    def add_audio_chunk(self, audio_data: bytes, mime_type: str, rms: float = 0.0, 
                       estimated_duration_s: float = None) -> AudioChunk:
        """
        Add audio chunk to the continuous buffer.
        
        Args:
            audio_data: Raw audio bytes
            mime_type: MIME type of the audio
            rms: RMS level of the audio
            estimated_duration_s: Estimated duration (calculated if not provided)
            
        Returns:
            AudioChunk with context information
        """
        with self.buffer_lock:
            timestamp = time.time()
            
            # Estimate duration if not provided (rough calculation)
            if estimated_duration_s is None:
                # Assume ~16kHz, 16-bit, mono for estimation
                estimated_duration_s = len(audio_data) / (16000 * 2)  # bytes / (sample_rate * bytes_per_sample)
            
            # Create chunk
            chunk = AudioChunk(
                data=audio_data,
                timestamp=timestamp,
                duration_s=estimated_duration_s,
                chunk_id=f"chunk_{self.chunk_sequence:06d}",
                mime_type=mime_type,
                rms=rms
            )
            
            # Add to buffer
            self.audio_buffer.append(chunk)
            self.current_buffer_size += len(audio_data)
            self.chunk_sequence += 1
            
            # Update metrics
            self.total_chunks_processed += 1
            self.avg_chunk_duration = (
                (self.avg_chunk_duration * (self.total_chunks_processed - 1) + estimated_duration_s) /
                self.total_chunks_processed
            )
            
            # Manage buffer size
            self._manage_buffer_size()
            
            logger.debug(f"Added audio chunk {chunk.chunk_id}: {len(audio_data)} bytes, "
                        f"{estimated_duration_s:.2f}s, RMS: {rms:.3f}")
            
            return chunk
    
    def get_contextual_chunk(self, target_duration_s: float = None) -> Optional[Tuple[bytes, Dict[str, Any]]]:
        """
        Get next audio chunk with overlapping context for transcription.
        
        Args:
            target_duration_s: Target duration for the chunk (uses max if not specified)
            
        Returns:
            Tuple of (concatenated_audio_bytes, context_metadata) or None if insufficient data
        """
        if target_duration_s is None:
            target_duration_s = self.max_chunk_duration_s
        
        with self.buffer_lock:
            if not self.audio_buffer:
                return None
            
            # Find chunks to include in this contextual window
            context_chunks = []
            current_duration = 0.0
            overlap_start_time = None
            
            # Calculate overlap start time
            if self.last_context_end > 0:
                overlap_start_time = self.last_context_end - self.overlap_duration_s
            
            # Collect chunks for context
            for chunk in self.audio_buffer:
                # Include if within overlap or if we haven't reached target duration
                if (overlap_start_time is None or 
                    chunk.timestamp >= overlap_start_time or 
                    current_duration < target_duration_s):
                    
                    context_chunks.append(chunk)
                    current_duration += chunk.duration_s
                    
                    # Stop if we've reached target duration (beyond overlap)
                    if current_duration >= target_duration_s and overlap_start_time is not None:
                        break
            
            if not context_chunks:
                return None
            
            # Concatenate audio data
            audio_parts = []
            total_size = 0
            context_start = context_chunks[0].timestamp
            context_end = context_chunks[-1].timestamp + context_chunks[-1].duration_s
            
            for chunk in context_chunks:
                audio_parts.append(chunk.data)
                total_size += len(chunk.data)
            
            # Create metadata
            metadata = {
                'context_start_time': context_start,
                'context_end_time': context_end,
                'context_duration_s': context_end - context_start,
                'overlap_duration_s': self.overlap_duration_s if overlap_start_time else 0.0,
                'chunk_count': len(context_chunks),
                'total_bytes': total_size,
                'chunk_ids': [chunk.chunk_id for chunk in context_chunks],
                'avg_rms': sum(chunk.rms for chunk in context_chunks) / len(context_chunks),
                'has_overlap': overlap_start_time is not None,
                'mime_type': context_chunks[0].mime_type  # Assume all chunks have same MIME type
            }
            
            # Update tracking
            self.last_context_end = context_end
            if overlap_start_time is not None:
                self.total_context_overlaps += 1
            
            logger.debug(f"Generated contextual chunk: {len(context_chunks)} chunks, "
                        f"{metadata['context_duration_s']:.2f}s duration, "
                        f"{metadata['overlap_duration_s']:.2f}s overlap")
            
            return b''.join(audio_parts), metadata
    
    def _manage_buffer_size(self):
        """Manage buffer size by removing old chunks if necessary."""
        while self.current_buffer_size > self.max_buffer_size and self.audio_buffer:
            old_chunk = self.audio_buffer.popleft()
            self.current_buffer_size -= len(old_chunk.data)
            self.buffer_overflows += 1
            
            logger.debug(f"Removed old chunk {old_chunk.chunk_id} to manage buffer size")
    
    def cleanup_processed_chunks(self, before_timestamp: float):
        """
        Remove processed chunks before the given timestamp to free memory.
        
        Args:
            before_timestamp: Remove chunks older than this timestamp
        """
        with self.buffer_lock:
            removed_count = 0
            
            while self.audio_buffer and self.audio_buffer[0].timestamp < before_timestamp:
                old_chunk = self.audio_buffer.popleft()
                self.current_buffer_size -= len(old_chunk.data)
                removed_count += 1
            
            if removed_count > 0:
                logger.debug(f"Cleaned up {removed_count} processed chunks")
    
    def get_buffer_stats(self) -> Dict[str, Any]:
        """Get current buffer statistics."""
        with self.buffer_lock:
            return {
                'buffer_size_mb': round(self.current_buffer_size / (1024 * 1024), 2),
                'buffer_utilization_percent': round(
                    (self.current_buffer_size / self.max_buffer_size) * 100, 1
                ),
                'chunk_count': len(self.audio_buffer),
                'total_chunks_processed': self.total_chunks_processed,
                'total_context_overlaps': self.total_context_overlaps,
                'buffer_overflows': self.buffer_overflows,
                'avg_chunk_duration_s': round(self.avg_chunk_duration, 3),
                'overlap_duration_s': self.overlap_duration_s,
                'max_chunk_duration_s': self.max_chunk_duration_s
            }
    
    def reset(self):
        """Reset the audio capture state."""
        with self.buffer_lock:
            self.audio_buffer.clear()
            self.current_buffer_size = 0
            self.last_context_end = 0.0
            self.chunk_sequence = 0
            
            logger.info("🔄 Continuous audio capture reset")

# Session-based audio capture management
_audio_captures: Dict[str, ContinuousAudioCapture] = {}
_captures_lock = threading.RLock()

def get_audio_capture(session_id: str) -> ContinuousAudioCapture:
    """Get or create audio capture for a session."""
    global _audio_captures
    
    with _captures_lock:
        if session_id not in _audio_captures:
            _audio_captures[session_id] = ContinuousAudioCapture()
            logger.info(f"Created continuous audio capture for session {session_id}")
        
        return _audio_captures[session_id]

def cleanup_audio_capture(session_id: str):
    """Clean up audio capture for a session."""
    global _audio_captures
    
    with _captures_lock:
        if session_id in _audio_captures:
            del _audio_captures[session_id]
            logger.info(f"Cleaned up audio capture for session {session_id}")

def get_all_capture_stats() -> Dict[str, Any]:
    """Get statistics for all active audio captures."""
    with _captures_lock:
        return {
            'active_sessions': len(_audio_captures),
            'sessions': {
                session_id: capture.get_buffer_stats()
                for session_id, capture in _audio_captures.items()
            }
        }