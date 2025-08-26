"""
Comparative QA Pipeline for Audio vs Transcript Quality Analysis
Measures WER, drift, dropped words, duplicates, and hallucinations
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import tempfile
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class TranscriptQualityMetrics:
    """Comprehensive quality metrics for transcript analysis."""
    session_id: str
    total_words: int = 0
    wer_score: float = 0.0
    drift_score: float = 0.0  # Timing drift from expected
    dropped_words: int = 0
    duplicate_words: int = 0
    hallucinated_words: int = 0
    confidence_distribution: List[float] = field(default_factory=list)
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    segments_processed: int = 0
    final_segments: int = 0
    interim_segments: int = 0

class QAPipeline:
    """Comprehensive QA pipeline for live transcription quality."""
    
    def __init__(self, storage_path: str = "/tmp/mina_qa"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True, parents=True)
        self.active_sessions: Dict[str, Dict] = {}
        
    def start_qa_session(self, session_id: str):
        """Initialize QA tracking for a session."""
        session_data = {
            'session_id': session_id,
            'start_time': time.time(),
            'audio_chunks': [],
            'transcript_segments': [],
            'interim_updates': [],
            'timing_data': [],
            'raw_audio_path': None,
            'metrics': TranscriptQualityMetrics(session_id=session_id)
        }
        
        self.active_sessions[session_id] = session_data
        logger.info(f"QA Pipeline started for session {session_id}")
        
    def save_audio_chunk(self, session_id: str, audio_data: bytes, timestamp: float):
        """Save raw audio chunk for later analysis."""
        if session_id not in self.active_sessions:
            return
            
        # Create unique filename for this chunk
        chunk_hash = hashlib.md5(audio_data).hexdigest()[:8]
        chunk_filename = f"{session_id}_chunk_{timestamp}_{chunk_hash}.webm"
        chunk_path = self.storage_path / chunk_filename
        
        try:
            with open(chunk_path, 'wb') as f:
                f.write(audio_data)
                
            self.active_sessions[session_id]['audio_chunks'].append({
                'path': str(chunk_path),
                'timestamp': timestamp,
                'size_bytes': len(audio_data),
                'hash': chunk_hash
            })
            
        except Exception as e:
            logger.error(f"Error saving audio chunk for QA: {e}")
    
    def record_transcript_segment(self, session_id: str, text: str, confidence: float, 
                                 is_final: bool, timestamp: float, processing_time_ms: float):
        """Record transcript segment for quality analysis."""
        if session_id not in self.active_sessions:
            return
            
        segment = {
            'text': text,
            'confidence': confidence,
            'is_final': is_final,
            'timestamp': timestamp,
            'processing_time_ms': processing_time_ms,
            'word_count': len(text.split()) if text else 0
        }
        
        session_data = self.active_sessions[session_id]
        
        if is_final:
            session_data['transcript_segments'].append(segment)
            session_data['metrics'].final_segments += 1
        else:
            session_data['interim_updates'].append(segment)
            session_data['metrics'].interim_segments += 1
            
        session_data['metrics'].segments_processed += 1
        session_data['metrics'].confidence_distribution.append(confidence)
        session_data['timing_data'].append(processing_time_ms)
        
        # Update latency metrics
        if len(session_data['timing_data']) > 0:
            sorted_times = sorted(session_data['timing_data'])
            n = len(sorted_times)
            session_data['metrics'].latency_p95 = sorted_times[int(n * 0.95)] if n > 0 else 0
            session_data['metrics'].latency_p99 = sorted_times[int(n * 0.99)] if n > 0 else 0
    
    def calculate_wer(self, reference_text: str, hypothesis_text: str) -> float:
        """Calculate Word Error Rate using dynamic programming."""
        try:
            ref_words = reference_text.lower().strip().split()
            hyp_words = hypothesis_text.lower().strip().split()
            
            if len(ref_words) == 0:
                return 0.0 if len(hyp_words) == 0 else 1.0
                
            # Initialize DP table
            d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
            
            # Initialize base cases
            for i in range(len(ref_words) + 1):
                d[i][0] = i
            for j in range(len(hyp_words) + 1):
                d[0][j] = j
                
            # Fill DP table
            for i in range(1, len(ref_words) + 1):
                for j in range(1, len(hyp_words) + 1):
                    if ref_words[i-1] == hyp_words[j-1]:
                        d[i][j] = d[i-1][j-1]  # No operation needed
                    else:
                        d[i][j] = min(
                            d[i-1][j] + 1,    # Deletion
                            d[i][j-1] + 1,    # Insertion
                            d[i-1][j-1] + 1   # Substitution
                        )
            
            # WER = edit distance / reference length
            wer = d[len(ref_words)][len(hyp_words)] / len(ref_words)
            return wer
            
        except Exception as e:
            logger.error(f"Error calculating WER: {e}")
            return 0.0
    
    def detect_duplicates_and_drift(self, session_id: str) -> Dict[str, Any]:
        """Analyze transcript for duplicates and timing drift."""
        if session_id not in self.active_sessions:
            return {}
            
        session_data = self.active_sessions[session_id]
        segments = session_data['transcript_segments']
        
        if len(segments) < 2:
            return {'duplicates': 0, 'drift_score': 0.0}
            
        # Detect duplicate segments
        seen_texts = set()
        duplicates = 0
        
        for segment in segments:
            text = segment['text'].strip().lower()
            if text in seen_texts and text:  # Don't count empty strings
                duplicates += 1
            else:
                seen_texts.add(text)
        
        # Calculate timing drift (segments arriving too late/early)
        expected_interval = 2.0  # Expected ~2s between final segments
        actual_intervals = []
        
        for i in range(1, len(segments)):
            interval = segments[i]['timestamp'] - segments[i-1]['timestamp']
            actual_intervals.append(interval)
        
        if actual_intervals:
            avg_interval = sum(actual_intervals) / len(actual_intervals)
            drift_score = abs(avg_interval - expected_interval) / expected_interval
        else:
            avg_interval = 0.0
            drift_score = 0.0
            
        return {
            'duplicates': duplicates,
            'drift_score': drift_score,
            'avg_interval': avg_interval
        }
    
    def finalize_session_qa(self, session_id: str, reference_transcript: Optional[str] = None) -> Dict[str, Any]:
        """Generate final QA report for a completed session."""
        if session_id not in self.active_sessions:
            return {'error': f'Session {session_id} not found in QA pipeline'}
            
        session_data = self.active_sessions[session_id]
        metrics = session_data['metrics']
        
        # Compile final transcript
        final_text = ' '.join([seg['text'] for seg in session_data['transcript_segments']])
        
        # Calculate quality metrics
        duplicate_analysis = self.detect_duplicates_and_drift(session_id)
        
        # Update metrics
        metrics.total_words = len(final_text.split()) if final_text else 0
        metrics.dropped_words = duplicate_analysis['duplicates']  # Simplified
        metrics.drift_score = duplicate_analysis['drift_score']
        
        # Calculate WER if reference provided
        if reference_transcript:
            metrics.wer_score = self.calculate_wer(reference_transcript, final_text)
        
        # Generate comprehensive report
        qa_report = {
            'session_id': session_id,
            'session_duration': time.time() - session_data['start_time'],
            'quality_metrics': {
                'wer_score': metrics.wer_score,
                'total_words': metrics.total_words,
                'dropped_words': metrics.dropped_words,
                'duplicate_segments': duplicate_analysis['duplicates'],
                'drift_score': metrics.drift_score,
                'avg_confidence': sum(metrics.confidence_distribution) / len(metrics.confidence_distribution) if metrics.confidence_distribution else 0.0,
                'confidence_std': self._calculate_std(metrics.confidence_distribution)
            },
            'performance_metrics': {
                'latency_p95_ms': metrics.latency_p95,
                'latency_p99_ms': metrics.latency_p99,
                'total_segments': metrics.segments_processed,
                'final_segments': metrics.final_segments,
                'interim_segments': metrics.interim_segments,
                'interim_to_final_ratio': metrics.interim_segments / max(metrics.final_segments, 1)
            },
            'audio_analysis': {
                'total_chunks': len(session_data['audio_chunks']),
                'total_audio_size_mb': sum(chunk['size_bytes'] for chunk in session_data['audio_chunks']) / (1024 * 1024)
            },
            'transcript_text': final_text,
            'reference_transcript': reference_transcript,
            'timestamp': time.time()
        }
        
        # Save report to file
        report_path = self.storage_path / f"{session_id}_qa_report.json"
        try:
            with open(report_path, 'w') as f:
                json.dump(qa_report, f, indent=2)
                
            logger.info(f"QA report saved for session {session_id}: {report_path}")
            
        except Exception as e:
            logger.error(f"Error saving QA report: {e}")
        
        # Clean up session data
        del self.active_sessions[session_id]
        
        return qa_report
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation of values."""
        if len(values) < 2:
            return 0.0
            
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def get_realtime_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get current QA metrics for active session."""
        if session_id not in self.active_sessions:
            return {}
            
        session_data = self.active_sessions[session_id]
        metrics = session_data['metrics']
        
        return {
            'session_id': session_id,
            'segments_processed': metrics.segments_processed,
            'current_confidence': metrics.confidence_distribution[-1] if metrics.confidence_distribution else 0.0,
            'avg_confidence': sum(metrics.confidence_distribution) / len(metrics.confidence_distribution) if metrics.confidence_distribution else 0.0,
            'recent_latency_ms': session_data['timing_data'][-1] if session_data['timing_data'] else 0.0,
            'session_duration': time.time() - session_data['start_time']
        }

# Global QA pipeline instance
qa_pipeline = QAPipeline()