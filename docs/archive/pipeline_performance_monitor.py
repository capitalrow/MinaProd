#!/usr/bin/env python3
"""
🔍 Mina Pipeline Performance Monitor & QA Analysis
Real-time metrics collection, WER calculation, and drift detection
"""

import time
import json
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import difflib
import re

@dataclass
class TranscriptionMetrics:
    """Metrics for individual transcription segment"""
    session_id: str
    chunk_id: int
    timestamp: float
    processing_time: float
    confidence: float
    text: str
    word_count: int
    character_count: int
    audio_duration: float
    latency_ms: float
    
class PipelineMonitor:
    """Real-time pipeline performance monitoring"""
    
    def __init__(self):
        self.sessions = {}
        self.performance_history = []
        self.error_count = 0
        self.total_requests = 0
        self.start_time = time.time()
        
        # QA benchmarks (Google Recorder targets)
        self.target_wer = 0.10  # ≤10%
        self.target_latency = 500  # <500ms
        self.target_coverage = 1.0  # 100%
        self.target_drift = 0.05  # <5%
        
        # Real-time metrics
        self.chunk_latencies = []
        self.queue_lengths = []
        self.dropped_chunks = 0
        self.retry_counts = []
        self.interim_final_ratios = []
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('PipelineMonitor')
        
    def log_chunk_metrics(self, session_id: str, chunk_data: Dict):
        """Log real-time chunk processing metrics"""
        
        try:
            latency = chunk_data.get('processing_time', 0) * 1000  # Convert to ms
            queue_length = chunk_data.get('queue_length', 0)
            confidence = chunk_data.get('confidence', 0)
            
            # Track metrics
            self.chunk_latencies.append(latency)
            self.queue_lengths.append(queue_length)
            
            # Calculate interim→final ratio
            is_final = chunk_data.get('is_final', False)
            if session_id not in self.sessions:
                self.sessions[session_id] = {'interim': 0, 'final': 0, 'start_time': time.time()}
            
            if is_final:
                self.sessions[session_id]['final'] += 1
            else:
                self.sessions[session_id]['interim'] += 1
                
            # Log structured metrics
            metrics = {
                'session_id': session_id,
                'chunk_latency_ms': latency,
                'queue_length': queue_length,
                'confidence': confidence,
                'is_final': is_final,
                'timestamp': time.time(),
                'target_latency_met': latency < self.target_latency,
                'confidence_acceptable': confidence > 0.8
            }
            
            self.logger.info(f"📊 CHUNK_METRICS: {json.dumps(metrics)}")
            
            # Check for performance issues
            if latency > self.target_latency:
                self.logger.warning(f"⚠️ LATENCY_VIOLATION: {latency}ms > {self.target_latency}ms")
                
            if queue_length > 10:
                self.logger.warning(f"⚠️ QUEUE_BACKLOG: {queue_length} chunks queued")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to log chunk metrics: {e}")
    
    def calculate_wer(self, reference_text: str, hypothesis_text: str) -> float:
        """Calculate Word Error Rate between reference and hypothesis"""
        
        if not reference_text or not hypothesis_text:
            return 1.0  # 100% error if either is empty
            
        # Normalize text
        ref_words = self._normalize_text(reference_text).split()
        hyp_words = self._normalize_text(hypothesis_text).split()
        
        if not ref_words:
            return 1.0 if hyp_words else 0.0
            
        # Use difflib for sequence matching
        matcher = difflib.SequenceMatcher(None, ref_words, hyp_words)
        operations = matcher.get_opcodes()
        
        substitutions = 0
        deletions = 0
        insertions = 0
        
        for op, ref_start, ref_end, hyp_start, hyp_end in operations:
            if op == 'replace':
                substitutions += max(ref_end - ref_start, hyp_end - hyp_start)
            elif op == 'delete':
                deletions += ref_end - ref_start
            elif op == 'insert':
                insertions += hyp_end - hyp_start
                
        wer = (substitutions + deletions + insertions) / len(ref_words)
        return min(wer, 1.0)  # Cap at 100%
    
    def calculate_semantic_drift(self, segments: List[str]) -> float:
        """Calculate semantic drift between consecutive segments"""
        
        if len(segments) < 2:
            return 0.0
            
        drift_scores = []
        
        for i in range(1, len(segments)):
            prev_text = self._normalize_text(segments[i-1])
            curr_text = self._normalize_text(segments[i])
            
            # Calculate overlap ratio
            prev_words = set(prev_text.split())
            curr_words = set(curr_text.split())
            
            if not prev_words or not curr_words:
                continue
                
            overlap = len(prev_words.intersection(curr_words))
            union = len(prev_words.union(curr_words))
            
            if union > 0:
                similarity = overlap / union
                drift = 1.0 - similarity
                drift_scores.append(drift)
        
        return statistics.mean(drift_scores) if drift_scores else 0.0
    
    def detect_audio_coverage_gaps(self, session_data: Dict) -> Dict:
        """Detect gaps in audio coverage"""
        
        segments = session_data.get('segments', [])
        if len(segments) < 2:
            return {'coverage': 1.0, 'gaps': [], 'total_gap_time': 0}
            
        gaps = []
        total_gap_time = 0
        
        for i in range(1, len(segments)):
            prev_end = segments[i-1].get('end_time', 0)
            curr_start = segments[i].get('start_time', 0)
            
            if curr_start > prev_end + 0.5:  # Gap > 500ms
                gap_duration = curr_start - prev_end
                gaps.append({
                    'start': prev_end,
                    'end': curr_start,
                    'duration': gap_duration
                })
                total_gap_time += gap_duration
        
        total_audio_time = session_data.get('total_duration', 0)
        coverage = 1.0 - (total_gap_time / total_audio_time) if total_audio_time > 0 else 0.0
        
        return {
            'coverage': coverage,
            'gaps': gaps,
            'total_gap_time': total_gap_time,
            'meets_target': coverage >= self.target_coverage
        }
    
    def generate_qa_report(self, session_id: str, reference_text: str = None) -> Dict:
        """Generate comprehensive QA report for session"""
        
        session = self.sessions.get(session_id, {})
        
        # Calculate metrics
        current_time = time.time()
        session_duration = current_time - session.get('start_time', current_time)
        
        # Latency metrics
        avg_latency = statistics.mean(self.chunk_latencies) if self.chunk_latencies else 0
        p95_latency = statistics.quantiles(self.chunk_latencies, n=20)[18] if len(self.chunk_latencies) >= 20 else avg_latency
        
        # Queue metrics  
        avg_queue_length = statistics.mean(self.queue_lengths) if self.queue_lengths else 0
        max_queue_length = max(self.queue_lengths) if self.queue_lengths else 0
        
        # Interim→final ratio
        interim_count = session.get('interim', 0)
        final_count = session.get('final', 0)
        interim_final_ratio = interim_count / final_count if final_count > 0 else 0
        
        # Coverage analysis
        coverage_data = self.detect_audio_coverage_gaps(session)
        
        # WER calculation (if reference provided)
        wer = None
        if reference_text and session.get('transcript'):
            wer = self.calculate_wer(reference_text, session['transcript'])
            
        # Semantic drift
        segment_texts = [seg.get('text', '') for seg in session.get('segments', [])]
        drift = self.calculate_semantic_drift(segment_texts)
        
        report = {
            'session_id': session_id,
            'timestamp': current_time,
            'session_duration': session_duration,
            
            # Performance metrics
            'latency_metrics': {
                'avg_latency_ms': avg_latency,
                'p95_latency_ms': p95_latency,
                'target_met': avg_latency < self.target_latency,
                'target_latency_ms': self.target_latency
            },
            
            # Queue metrics
            'queue_metrics': {
                'avg_queue_length': avg_queue_length,
                'max_queue_length': max_queue_length,
                'dropped_chunks': self.dropped_chunks,
                'retry_count': sum(self.retry_counts)
            },
            
            # Transcription quality
            'quality_metrics': {
                'interim_final_ratio': interim_final_ratio,
                'interim_segments': interim_count,
                'final_segments': final_count,
                'expected_final_only': final_count > 0 and interim_count == 0
            },
            
            # Coverage analysis
            'coverage_metrics': coverage_data,
            
            # Comparative QA
            'qa_metrics': {
                'wer': wer,
                'semantic_drift': drift,
                'wer_target_met': wer <= self.target_wer if wer else None,
                'drift_target_met': drift <= self.target_drift,
                'target_wer': self.target_wer,
                'target_drift': self.target_drift
            },
            
            # Overall health
            'health_status': {
                'latency_healthy': avg_latency < self.target_latency,
                'coverage_healthy': coverage_data['meets_target'],
                'quality_healthy': drift <= self.target_drift,
                'overall_healthy': all([
                    avg_latency < self.target_latency,
                    coverage_data['meets_target'],
                    drift <= self.target_drift
                ])
            }
        }
        
        # Log structured report
        self.logger.info(f"📋 QA_REPORT: {json.dumps(report, indent=2)}")
        
        return report
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def log_performance_summary(self):
        """Log overall performance summary"""
        
        if not self.chunk_latencies:
            self.logger.info("📊 No performance data collected yet")
            return
            
        summary = {
            'total_runtime': time.time() - self.start_time,
            'total_requests': self.total_requests,
            'error_rate': self.error_count / self.total_requests if self.total_requests > 0 else 0,
            'avg_latency_ms': statistics.mean(self.chunk_latencies),
            'p95_latency_ms': statistics.quantiles(self.chunk_latencies, n=20)[18] if len(self.chunk_latencies) >= 20 else 0,
            'targets': {
                'wer_target': f"≤{self.target_wer * 100}%",
                'latency_target': f"<{self.target_latency}ms",
                'coverage_target': f"{self.target_coverage * 100}%",
                'drift_target': f"<{self.target_drift * 100}%"
            }
        }
        
        self.logger.info(f"📊 PERFORMANCE_SUMMARY: {json.dumps(summary, indent=2)}")

# Global monitor instance
pipeline_monitor = PipelineMonitor()

def log_transcription_metrics(session_id: str, metrics: Dict):
    """Public interface for logging transcription metrics"""
    pipeline_monitor.log_chunk_metrics(session_id, metrics)

def generate_qa_report(session_id: str, reference_text: str = None) -> Dict:
    """Public interface for generating QA reports"""
    return pipeline_monitor.generate_qa_report(session_id, reference_text)

if __name__ == "__main__":
    # Example usage and testing
    print("🔍 Mina Pipeline Performance Monitor")
    print("Targets:")
    print(f"  • WER: ≤{pipeline_monitor.target_wer * 100}%")
    print(f"  • Latency: <{pipeline_monitor.target_latency}ms") 
    print(f"  • Coverage: {pipeline_monitor.target_coverage * 100}%")
    print(f"  • Drift: <{pipeline_monitor.target_drift * 100}%")