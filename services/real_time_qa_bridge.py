"""
🔬 REAL-TIME QA BRIDGE
Integrates streaming transcription with comprehensive QA pipeline
for real-time WER calculation, latency monitoring, and quality assessment
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
import difflib
import re

logger = logging.getLogger(__name__)


@dataclass
class QAMetrics:
    """Real-time QA metrics for transcription quality"""
    wer: float = 0.0  # Word Error Rate
    accuracy: float = 0.0  # Transcription accuracy
    latency_ms: float = 0.0  # End-to-end latency
    completeness: float = 0.0  # Audio coverage
    semantic_drift: float = 0.0  # Semantic consistency
    confidence_avg: float = 0.0  # Average confidence
    processing_efficiency: float = 0.0  # VAD savings ratio
    
    # Benchmark compliance
    meets_wer_target: bool = False  # ≤10%
    meets_latency_target: bool = False  # <500ms
    meets_completeness_target: bool = False  # ≥90%
    meets_drift_target: bool = False  # <5%


@dataclass
class TranscriptionSegment:
    """Individual transcription segment for QA analysis"""
    timestamp: float
    text: str
    confidence: float
    latency_ms: float
    chunk_id: str
    is_final: bool = False
    reference_text: Optional[str] = None  # For WER calculation


class RealTimeQABridge:
    """
    Real-time QA bridge that monitors streaming transcription
    and calculates Google Recorder-level quality metrics
    """
    
    def __init__(self, target_wer: float = 10.0, target_latency: float = 500.0):
        self.target_wer = target_wer
        self.target_latency = target_latency
        
        # Session tracking
        self.current_session_id: Optional[str] = None
        self.session_start_time: float = 0.0
        self.segments: deque = deque(maxlen=1000)  # Last 1000 segments
        
        # Real-time metrics
        self.current_metrics = QAMetrics()
        self.metrics_lock = threading.Lock()
        
        # Performance tracking
        self.latency_samples: deque = deque(maxlen=100)  # Last 100 latencies
        self.wer_samples: deque = deque(maxlen=50)  # Last 50 WER calculations
        
        # Audio analysis
        self.total_audio_duration_ms: float = 0.0
        self.transcribed_duration_ms: float = 0.0
        self.silent_chunks_saved: int = 0
        self.total_chunks_processed: int = 0
        
        # Text analysis for semantic drift
        self.previous_segments: List[str] = []
        self.semantic_window_size = 10
        
        logger.info("🔬 Real-time QA bridge initialized with targets: WER≤%.1f%%, Latency<%.0fms", 
                   target_wer, target_latency)
    
    def start_qa_session(self, session_id: str) -> None:
        """Start QA monitoring for a new session"""
        with self.metrics_lock:
            self.current_session_id = session_id
            self.session_start_time = time.time()
            self.segments.clear()
            self.current_metrics = QAMetrics()
            self.latency_samples.clear()
            self.wer_samples.clear()
            self.previous_segments.clear()
            
            # Reset counters
            self.total_audio_duration_ms = 0.0
            self.transcribed_duration_ms = 0.0
            self.silent_chunks_saved = 0
            self.total_chunks_processed = 0
            
        logger.info("📊 QA session started: %s", session_id)
    
    def process_transcription_result(self, result: Dict) -> QAMetrics:
        """Process a transcription result and update QA metrics"""
        try:
            segment = TranscriptionSegment(
                timestamp=time.time(),
                text=result.get('text', ''),
                confidence=result.get('confidence', 0.0),
                latency_ms=result.get('processing_time_ms', 0.0),
                chunk_id=result.get('chunk_id', ''),
                is_final=result.get('is_final', False)
            )
            
            with self.metrics_lock:
                self.segments.append(segment)
                self.total_chunks_processed += 1
                
                # Update metrics
                self._update_latency_metrics(segment.latency_ms)
                self._update_confidence_metrics(segment.confidence)
                self._update_completeness_metrics(segment)
                self._update_semantic_drift_metrics(segment.text)
                
                # Calculate WER if we have reference text
                if segment.reference_text:
                    self._update_wer_metrics(segment)
                
                # Update processing efficiency
                self._update_efficiency_metrics()
                
                # Check benchmark compliance
                self._update_benchmark_compliance()
                
                return self.current_metrics.copy() if hasattr(self.current_metrics, 'copy') else self.current_metrics
                
        except Exception as e:
            logger.error("❌ Error processing QA result: %s", e)
            return self.current_metrics
    
    def process_vad_result(self, has_speech: bool, chunk_duration_ms: float) -> None:
        """Process VAD result for efficiency metrics"""
        with self.metrics_lock:
            self.total_audio_duration_ms += chunk_duration_ms
            
            if has_speech:
                self.transcribed_duration_ms += chunk_duration_ms
            else:
                self.silent_chunks_saved += 1
    
    def _update_latency_metrics(self, latency_ms: float) -> None:
        """Update latency-related metrics"""
        self.latency_samples.append(latency_ms)
        
        if self.latency_samples:
            self.current_metrics.latency_ms = sum(self.latency_samples) / len(self.latency_samples)
            self.current_metrics.meets_latency_target = self.current_metrics.latency_ms < self.target_latency
    
    def _update_confidence_metrics(self, confidence: float) -> None:
        """Update confidence-related metrics"""
        # Calculate running average confidence
        if hasattr(self, '_confidence_samples'):
            self._confidence_samples.append(confidence)
        else:
            self._confidence_samples = deque([confidence], maxlen=100)
        
        if self._confidence_samples:
            self.current_metrics.confidence_avg = sum(self._confidence_samples) / len(self._confidence_samples)
            # Convert confidence to accuracy percentage
            self.current_metrics.accuracy = self.current_metrics.confidence_avg * 100
    
    def _update_completeness_metrics(self, segment: TranscriptionSegment) -> None:
        """Update audio completeness metrics"""
        if self.total_audio_duration_ms > 0:
            self.current_metrics.completeness = (self.transcribed_duration_ms / self.total_audio_duration_ms) * 100
            self.current_metrics.meets_completeness_target = self.current_metrics.completeness >= 90.0
    
    def _update_wer_metrics(self, segment: TranscriptionSegment) -> None:
        """Calculate and update Word Error Rate"""
        if not segment.reference_text or not segment.text:
            return
        
        wer = self._calculate_wer(segment.reference_text, segment.text)
        self.wer_samples.append(wer)
        
        if self.wer_samples:
            self.current_metrics.wer = sum(self.wer_samples) / len(self.wer_samples)
            self.current_metrics.meets_wer_target = self.current_metrics.wer <= self.target_wer
    
    def _update_semantic_drift_metrics(self, text: str) -> None:
        """Calculate semantic drift between consecutive segments"""
        if not text.strip():
            return
        
        self.previous_segments.append(text)
        
        # Keep only recent segments for drift calculation
        if len(self.previous_segments) > self.semantic_window_size:
            self.previous_segments = self.previous_segments[-self.semantic_window_size:]
        
        if len(self.previous_segments) >= 2:
            # Calculate semantic consistency
            recent_text = ' '.join(self.previous_segments[-3:])  # Last 3 segments
            older_text = ' '.join(self.previous_segments[-6:-3])  # Previous 3 segments
            
            if older_text:
                drift = self._calculate_semantic_drift(older_text, recent_text)
                self.current_metrics.semantic_drift = drift
                self.current_metrics.meets_drift_target = drift < 5.0
    
    def _update_efficiency_metrics(self) -> None:
        """Update processing efficiency metrics"""
        if self.total_chunks_processed > 0:
            # Calculate VAD savings ratio
            total_possible_chunks = self.total_chunks_processed + self.silent_chunks_saved
            if total_possible_chunks > 0:
                self.current_metrics.processing_efficiency = (self.silent_chunks_saved / total_possible_chunks) * 100
    
    def _update_benchmark_compliance(self) -> None:
        """Update overall benchmark compliance"""
        # Google Recorder benchmark compliance
        benchmarks_met = [
            self.current_metrics.meets_wer_target,
            self.current_metrics.meets_latency_target,
            self.current_metrics.meets_completeness_target,
            self.current_metrics.meets_drift_target
        ]
        
        # Additional quality checks
        quality_checks = [
            self.current_metrics.accuracy >= 95.0,  # 95% accuracy target
            self.current_metrics.confidence_avg >= 0.8,  # 80% confidence target
            self.current_metrics.processing_efficiency >= 40.0  # 40% VAD savings target
        ]
        
        # Log compliance status
        compliance_rate = (sum(benchmarks_met) + sum(quality_checks)) / (len(benchmarks_met) + len(quality_checks))
        
        if compliance_rate >= 0.8:  # 80% of benchmarks met
            logger.debug("✅ QA compliance: %.1f%% (GOOD)", compliance_rate * 100)
        elif compliance_rate >= 0.6:
            logger.debug("⚠️ QA compliance: %.1f%% (NEEDS IMPROVEMENT)", compliance_rate * 100)
        else:
            logger.warning("❌ QA compliance: %.1f%% (POOR)", compliance_rate * 100)
    
    def _calculate_wer(self, reference: str, hypothesis: str) -> float:
        """Calculate Word Error Rate between reference and hypothesis"""
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        if not ref_words:
            return 0.0 if not hyp_words else 100.0
        
        # Use SequenceMatcher to find edit distance
        matcher = difflib.SequenceMatcher(None, ref_words, hyp_words)
        matches = matcher.get_matching_blocks()
        
        # Calculate total matching words
        matching_words = sum(match.size for match in matches)
        
        # WER = (S + D + I) / N where S=substitutions, D=deletions, I=insertions, N=reference length
        errors = len(ref_words) + len(hyp_words) - 2 * matching_words
        wer = (errors / len(ref_words)) * 100
        
        return min(wer, 100.0)  # Cap at 100%
    
    def _calculate_semantic_drift(self, text1: str, text2: str) -> float:
        """Calculate semantic drift percentage between two text segments"""
        if not text1 or not text2:
            return 0.0
        
        # Simple semantic drift based on word overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1:
            return 0.0 if not words2 else 100.0
        
        # Calculate Jaccard distance as semantic drift proxy
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
        
        similarity = intersection / union
        drift = (1 - similarity) * 100
        
        return min(drift, 100.0)
    
    def get_session_summary(self) -> Dict:
        """Get comprehensive QA summary for current session"""
        with self.metrics_lock:
            session_duration = time.time() - self.session_start_time
            
            # Calculate percentiles for latency
            latency_list = list(self.latency_samples)
            latency_list.sort()
            
            p50 = p95 = p99 = 0.0
            if latency_list:
                p50 = latency_list[len(latency_list) // 2]
                p95 = latency_list[int(len(latency_list) * 0.95)]
                p99 = latency_list[int(len(latency_list) * 0.99)]
            
            return {
                'session_id': self.current_session_id,
                'session_duration_seconds': session_duration,
                'total_segments': len(self.segments),
                'current_metrics': {
                    'wer_percent': self.current_metrics.wer,
                    'accuracy_percent': self.current_metrics.accuracy,
                    'avg_latency_ms': self.current_metrics.latency_ms,
                    'completeness_percent': self.current_metrics.completeness,
                    'semantic_drift_percent': self.current_metrics.semantic_drift,
                    'confidence_avg': self.current_metrics.confidence_avg,
                    'processing_efficiency_percent': self.current_metrics.processing_efficiency
                },
                'latency_distribution': {
                    'p50_ms': p50,
                    'p95_ms': p95,
                    'p99_ms': p99,
                    'samples': len(latency_list)
                },
                'benchmark_compliance': {
                    'wer_target_met': self.current_metrics.meets_wer_target,
                    'latency_target_met': self.current_metrics.meets_latency_target,
                    'completeness_target_met': self.current_metrics.meets_completeness_target,
                    'drift_target_met': self.current_metrics.meets_drift_target
                },
                'processing_stats': {
                    'total_chunks': self.total_chunks_processed,
                    'silent_chunks_saved': self.silent_chunks_saved,
                    'vad_efficiency_percent': self.current_metrics.processing_efficiency,
                    'audio_coverage_ms': self.transcribed_duration_ms,
                    'total_audio_ms': self.total_audio_duration_ms
                }
            }
    
    def end_qa_session(self) -> Dict:
        """End QA session and return final report"""
        summary = self.get_session_summary()
        
        logger.info("📊 QA Session ended: %s", self.current_session_id)
        logger.info("📈 Final metrics: WER=%.1f%%, Latency=%.1fms, Accuracy=%.1f%%", 
                   self.current_metrics.wer, 
                   self.current_metrics.latency_ms,
                   self.current_metrics.accuracy)
        
        # Reset session
        with self.metrics_lock:
            self.current_session_id = None
            self.session_start_time = 0.0
        
        return summary
    
    def get_real_time_metrics(self) -> QAMetrics:
        """Get current real-time QA metrics"""
        with self.metrics_lock:
            return self.current_metrics


# Global QA bridge instance
_qa_bridge = None

def get_qa_bridge() -> RealTimeQABridge:
    """Get or create global QA bridge instance"""
    global _qa_bridge
    if _qa_bridge is None:
        _qa_bridge = RealTimeQABridge()
    return _qa_bridge