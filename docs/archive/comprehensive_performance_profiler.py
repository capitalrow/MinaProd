#!/usr/bin/env python3
"""
MINA COMPREHENSIVE PERFORMANCE PROFILER
Real-time pipeline analysis with QA metrics, WER calculation, and comparative audio analysis
"""

import time
import json
import logging
import asyncio
import threading
import psutil
import numpy as np
from collections import deque, defaultdict
from datetime import datetime
import os
import tempfile
import base64
from typing import Dict, List, Optional, Tuple, Any
import difflib
import re

class ComprehensivePerformanceProfiler:
    """
    Real-time performance profiler for the MINA transcription pipeline.
    Measures end-to-end latency, queue performance, chunk processing, and QA metrics.
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.is_active = False
        
        # Performance metrics
        self.chunk_metrics = deque(maxlen=1000)
        self.session_metrics = {}
        self.pipeline_metrics = {
            'total_chunks': 0,
            'successful_chunks': 0,
            'failed_chunks': 0,
            'retry_attempts': 0,
            'dropped_chunks': 0,
            'queue_overflows': 0,
            'memory_leaks': 0,
            'processing_latencies': deque(maxlen=100),
            'queue_lengths': deque(maxlen=100),
            'interim_final_ratios': deque(maxlen=50)
        }
        
        # QA Metrics
        self.qa_metrics = {
            'reference_audio': [],
            'live_transcripts': [],
            'wer_scores': deque(maxlen=100),
            'drift_measurements': deque(maxlen=100),
            'duplicate_count': 0,
            'hallucination_count': 0,
            'confidence_accuracy': deque(maxlen=100)
        }
        
        # System resource monitoring
        self.resource_monitor = {
            'cpu_usage': deque(maxlen=100),
            'memory_usage': deque(maxlen=100),
            'disk_io': deque(maxlen=100),
            'network_io': deque(maxlen=100)
        }
        
        # Error pattern analysis
        self.error_patterns = defaultdict(int)
        self.critical_errors = []
        
        # Lock for thread-safe operations
        self.lock = threading.Lock()
        
        # Monitoring thread
        self.monitor_thread = None
        self.monitoring_active = False
        
        self.logger = logging.getLogger(__name__)
        
    def start_profiling(self):
        """Start comprehensive profiling with real-time monitoring."""
        self.is_active = True
        self.monitoring_active = True
        
        # Start resource monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("🔄 Comprehensive Performance Profiler ACTIVE")
        return True
    
    def stop_profiling(self):
        """Stop profiling and generate final report."""
        self.is_active = False
        self.monitoring_active = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        report = self.generate_comprehensive_report()
        self.logger.info("📊 Performance Profiling COMPLETE")
        return report
    
    def profile_chunk_processing(self, session_id: str, chunk_id: int, audio_size: int, 
                               start_time: float, end_time: float, success: bool, 
                               text: str = "", confidence: float = 0.0, error: str = ""):
        """Profile individual chunk processing with detailed metrics."""
        if not self.is_active:
            return
        
        with self.lock:
            latency = (end_time - start_time) * 1000  # Convert to ms
            
            # Update pipeline metrics
            self.pipeline_metrics['total_chunks'] += 1
            if success:
                self.pipeline_metrics['successful_chunks'] += 1
            else:
                self.pipeline_metrics['failed_chunks'] += 1
                
            self.pipeline_metrics['processing_latencies'].append(latency)
            
            # Track chunk details
            chunk_data = {
                'session_id': session_id,
                'chunk_id': chunk_id,
                'timestamp': end_time,
                'audio_size_bytes': audio_size,
                'latency_ms': latency,
                'success': success,
                'text': text,
                'confidence': confidence,
                'error': error,
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage_mb': psutil.virtual_memory().used / 1024 / 1024
            }
            
            self.chunk_metrics.append(chunk_data)
            
            # Session-specific tracking
            if session_id not in self.session_metrics:
                self.session_metrics[session_id] = {
                    'start_time': start_time,
                    'chunks': [],
                    'total_words': 0,
                    'total_confidence': 0.0,
                    'successful_chunks': 0,
                    'errors': []
                }
            
            self.session_metrics[session_id]['chunks'].append(chunk_data)
            
            if success and text:
                self.session_metrics[session_id]['total_words'] += len(text.split())
                self.session_metrics[session_id]['total_confidence'] += confidence
                self.session_metrics[session_id]['successful_chunks'] += 1
            elif not success:
                self.session_metrics[session_id]['errors'].append(error)
                
            # Error pattern analysis
            if error:
                self.error_patterns[error] += 1
                if 'critical' in error.lower() or 'severe' in error.lower():
                    self.critical_errors.append({
                        'timestamp': end_time,
                        'error': error,
                        'session_id': session_id,
                        'chunk_id': chunk_id
                    })
    
    def profile_queue_performance(self, queue_length: int, processing_time: float, 
                                overflow_detected: bool = False):
        """Profile queue performance and backpressure management."""
        if not self.is_active:
            return
            
        with self.lock:
            self.pipeline_metrics['queue_lengths'].append(queue_length)
            
            if overflow_detected:
                self.pipeline_metrics['queue_overflows'] += 1
                self.logger.warning(f"🚨 Queue overflow detected: {queue_length} items")
    
    def profile_interim_final_ratio(self, interim_count: int, final_count: int):
        """Track interim to final result ratios for processing efficiency."""
        if not self.is_active or final_count == 0:
            return
            
        ratio = interim_count / final_count
        self.pipeline_metrics['interim_final_ratios'].append(ratio)
        
        # Alert on concerning ratios
        if ratio > 10:  # More than 10 interim results per final
            self.logger.warning(f"🚨 High interim/final ratio: {ratio:.1f}")
    
    def calculate_wer(self, reference_text: str, hypothesis_text: str) -> float:
        """Calculate Word Error Rate (WER) between reference and hypothesis."""
        reference_words = reference_text.lower().split()
        hypothesis_words = hypothesis_text.lower().split()
        
        if len(reference_words) == 0:
            return 0.0 if len(hypothesis_words) == 0 else 100.0
        
        # Use SequenceMatcher for edit distance calculation
        matcher = difflib.SequenceMatcher(None, reference_words, hypothesis_words)
        opcodes = matcher.get_opcodes()
        
        substitutions = sum(1 for tag, _, _, _, _ in opcodes if tag == 'replace')
        deletions = sum(1 for tag, _, _, _, _ in opcodes if tag == 'delete')
        insertions = sum(1 for tag, _, _, _, _ in opcodes if tag == 'insert')
        
        total_errors = substitutions + deletions + insertions
        wer = (total_errors / len(reference_words)) * 100
        
        return min(100.0, wer)  # Cap at 100%
    
    def detect_semantic_drift(self, text_sequence: List[str]) -> float:
        """Detect semantic drift in transcription quality over time."""
        if len(text_sequence) < 3:
            return 0.0
        
        drift_scores = []
        for i in range(1, len(text_sequence)):
            prev_text = text_sequence[i-1].lower()
            curr_text = text_sequence[i].lower()
            
            # Calculate semantic similarity using simple word overlap
            prev_words = set(prev_text.split())
            curr_words = set(curr_text.split())
            
            if len(prev_words) == 0 and len(curr_words) == 0:
                similarity = 1.0
            elif len(prev_words) == 0 or len(curr_words) == 0:
                similarity = 0.0
            else:
                overlap = len(prev_words.intersection(curr_words))
                union = len(prev_words.union(curr_words))
                similarity = overlap / union if union > 0 else 0.0
            
            drift_scores.append(1.0 - similarity)  # Higher score = more drift
        
        return np.mean(drift_scores) * 100  # Convert to percentage
    
    def detect_duplicates_and_hallucinations(self, text_list: List[str]) -> Dict[str, int]:
        """Detect duplicate segments and hallucination patterns."""
        duplicates = 0
        hallucinations = 0
        
        # Common hallucination patterns
        hallucination_patterns = [
            r'\b(you|right|okay|um|uh|ah)\b\s*\.?\s*$',
            r'^(thank you for watching|thanks for watching)\.?$',
            r'^(bye|goodbye|see you)\.?$',
            r'^\[.*\]$',  # [music], [laughter], etc.
            r'^\(.*\)$',  # (music), (applause), etc.
        ]
        
        seen_texts = set()
        
        for text in text_list:
            text_clean = text.strip().lower()
            
            # Check for duplicates
            if text_clean in seen_texts:
                duplicates += 1
            else:
                seen_texts.add(text_clean)
            
            # Check for hallucinations
            for pattern in hallucination_patterns:
                if re.match(pattern, text_clean, re.IGNORECASE):
                    hallucinations += 1
                    break
        
        return {
            'duplicates': duplicates,
            'hallucinations': hallucinations,
            'unique_segments': len(seen_texts),
            'total_segments': len(text_list)
        }
    
    def _monitor_resources(self):
        """Background thread to monitor system resources."""
        while self.monitoring_active:
            try:
                # CPU and Memory
                cpu_usage = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                with self.lock:
                    self.resource_monitor['cpu_usage'].append(cpu_usage)
                    self.resource_monitor['memory_usage'].append(memory.percent)
                
                # Check for resource issues
                if cpu_usage > 80:
                    self.logger.warning(f"🚨 High CPU usage: {cpu_usage}%")
                
                if memory.percent > 85:
                    self.logger.warning(f"🚨 High memory usage: {memory.percent}%")
                
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
            
            time.sleep(5)  # Monitor every 5 seconds
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance and QA report."""
        with self.lock:
            # Calculate summary statistics
            total_latencies = list(self.pipeline_metrics['processing_latencies'])
            avg_latency = np.mean(total_latencies) if total_latencies else 0
            p95_latency = np.percentile(total_latencies, 95) if total_latencies else 0
            p99_latency = np.percentile(total_latencies, 99) if total_latencies else 0
            
            success_rate = (self.pipeline_metrics['successful_chunks'] / 
                          max(1, self.pipeline_metrics['total_chunks'])) * 100
            
            # Queue performance
            avg_queue_length = np.mean(list(self.pipeline_metrics['queue_lengths'])) if self.pipeline_metrics['queue_lengths'] else 0
            max_queue_length = max(list(self.pipeline_metrics['queue_lengths'])) if self.pipeline_metrics['queue_lengths'] else 0
            
            # Resource utilization
            avg_cpu = np.mean(list(self.resource_monitor['cpu_usage'])) if self.resource_monitor['cpu_usage'] else 0
            avg_memory = np.mean(list(self.resource_monitor['memory_usage'])) if self.resource_monitor['memory_usage'] else 0
            
            # Error analysis
            top_errors = sorted(self.error_patterns.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'profiling_duration_seconds': time.time() - self.start_time,
                'pipeline_performance': {
                    'total_chunks_processed': self.pipeline_metrics['total_chunks'],
                    'success_rate_percent': round(success_rate, 2),
                    'failure_rate_percent': round(100 - success_rate, 2),
                    'retry_attempts': self.pipeline_metrics['retry_attempts'],
                    'dropped_chunks': self.pipeline_metrics['dropped_chunks'],
                    'queue_overflows': self.pipeline_metrics['queue_overflows']
                },
                'latency_analysis': {
                    'average_latency_ms': round(avg_latency, 2),
                    'p95_latency_ms': round(p95_latency, 2),
                    'p99_latency_ms': round(p99_latency, 2),
                    'min_latency_ms': round(min(total_latencies), 2) if total_latencies else 0,
                    'max_latency_ms': round(max(total_latencies), 2) if total_latencies else 0
                },
                'queue_performance': {
                    'average_queue_length': round(avg_queue_length, 2),
                    'max_queue_length': max_queue_length,
                    'queue_overflow_rate': self.pipeline_metrics['queue_overflows']
                },
                'resource_utilization': {
                    'average_cpu_percent': round(avg_cpu, 2),
                    'average_memory_percent': round(avg_memory, 2),
                    'peak_cpu_percent': max(list(self.resource_monitor['cpu_usage'])) if self.resource_monitor['cpu_usage'] else 0,
                    'peak_memory_percent': max(list(self.resource_monitor['memory_usage'])) if self.resource_monitor['memory_usage'] else 0
                },
                'error_analysis': {
                    'total_error_types': len(self.error_patterns),
                    'critical_errors': len(self.critical_errors),
                    'top_error_patterns': [{'error': error, 'count': count} for error, count in top_errors],
                    'most_recent_critical_errors': self.critical_errors[-5:]  # Last 5 critical errors
                },
                'qa_metrics': self._calculate_qa_metrics(),
                'recommendations': self._generate_recommendations(success_rate, avg_latency)
            }
    
    def _calculate_qa_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive QA metrics including WER, drift, duplicates."""
        if len(self.qa_metrics['live_transcripts']) < 2:
            return {
                'status': 'insufficient_data',
                'message': 'Need at least 2 transcript segments for QA analysis'
            }
        
        transcripts = self.qa_metrics['live_transcripts']
        
        # Calculate WER if reference audio available
        wer_scores = list(self.qa_metrics['wer_scores'])
        avg_wer = np.mean(wer_scores) if wer_scores else None
        
        # Semantic drift analysis
        drift_score = self.detect_semantic_drift(transcripts)
        
        # Duplicate and hallucination detection
        duplicate_analysis = self.detect_duplicates_and_hallucinations(transcripts)
        
        # Confidence accuracy (how well confidence predicts actual quality)
        confidence_scores = list(self.qa_metrics['confidence_accuracy'])
        avg_confidence_accuracy = np.mean(confidence_scores) if confidence_scores else None
        
        return {
            'wer_analysis': {
                'average_wer_percent': round(avg_wer, 2) if avg_wer is not None else None,
                'wer_samples': len(wer_scores),
                'target_wer_percent': 10.0,  # User requirement: WER ≤10%
                'meets_target': avg_wer <= 10.0 if avg_wer is not None else False
            },
            'semantic_drift': {
                'drift_score_percent': round(drift_score, 2),
                'target_drift_percent': 5.0,  # User requirement: drift <5%
                'meets_target': drift_score < 5.0
            },
            'duplicate_analysis': duplicate_analysis,
            'confidence_accuracy': {
                'average_accuracy_percent': round(avg_confidence_accuracy, 2) if avg_confidence_accuracy is not None else None,
                'samples': len(confidence_scores)
            },
            'transcript_coverage': {
                'total_segments': len(transcripts),
                'non_empty_segments': len([t for t in transcripts if t.strip()]),
                'coverage_percent': round((len([t for t in transcripts if t.strip()]) / max(1, len(transcripts))) * 100, 2)
            }
        }
    
    def _generate_recommendations(self, success_rate: float, avg_latency: float) -> List[str]:
        """Generate specific recommendations based on profiling results."""
        recommendations = []
        
        # Success rate recommendations
        if success_rate < 80:
            recommendations.append("🚨 CRITICAL: Success rate below 80%. Implement exponential backoff and circuit breaker.")
        elif success_rate < 95:
            recommendations.append("⚠️ WARNING: Success rate below 95%. Review error handling and retry logic.")
        
        # Latency recommendations
        if avg_latency > 2000:
            recommendations.append("🚨 CRITICAL: Average latency > 2s. Optimize audio processing pipeline.")
        elif avg_latency > 1000:
            recommendations.append("⚠️ WARNING: Average latency > 1s. Consider chunk size optimization.")
        
        # Queue recommendations
        queue_lengths = list(self.pipeline_metrics['queue_lengths'])
        if queue_lengths and max(queue_lengths) > 20:
            recommendations.append("🚨 CRITICAL: Queue overflow detected. Implement backpressure handling.")
        
        # Error pattern recommendations
        if self.pipeline_metrics['queue_overflows'] > 0:
            recommendations.append("🔧 FIX: Implement bounded queues and graceful degradation.")
        
        if len(self.critical_errors) > 5:
            recommendations.append("🚨 CRITICAL: Multiple critical errors detected. Implement comprehensive error recovery.")
        
        # QA-specific recommendations
        wer_scores = list(self.qa_metrics['wer_scores'])
        if wer_scores and np.mean(wer_scores) > 10:
            recommendations.append("📊 QA FAIL: WER > 10%. Improve audio quality and deduplication.")
        
        if self.qa_metrics['duplicate_count'] > 10:
            recommendations.append("🔄 DUPLICATES: High duplicate rate. Strengthen deduplication algorithms.")
        
        return recommendations
    
    def add_qa_measurement(self, reference_audio: bytes, live_transcript: str, 
                          expected_text: str = None):
        """Add QA measurement for audio vs transcript comparison."""
        if not self.is_active:
            return
        
        with self.lock:
            self.qa_metrics['reference_audio'].append(base64.b64encode(reference_audio).decode())
            self.qa_metrics['live_transcripts'].append(live_transcript)
            
            # Calculate WER if expected text provided
            if expected_text:
                wer = self.calculate_wer(expected_text, live_transcript)
                self.qa_metrics['wer_scores'].append(wer)
                
                # Log WER results
                if wer > 15:
                    self.logger.warning(f"🚨 High WER detected: {wer:.1f}% (Target: ≤10%)")
                elif wer <= 10:
                    self.logger.info(f"✅ WER within target: {wer:.1f}%")
    
    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for live monitoring."""
        if not self.is_active:
            return {'status': 'inactive'}
        
        with self.lock:
            recent_latencies = list(self.pipeline_metrics['processing_latencies'])[-10:]
            recent_queue_lengths = list(self.pipeline_metrics['queue_lengths'])[-10:]
            recent_cpu = list(self.resource_monitor['cpu_usage'])[-5:]
            recent_memory = list(self.resource_monitor['memory_usage'])[-5:]
            
            return {
                'status': 'active',
                'timestamp': time.time(),
                'current_performance': {
                    'recent_avg_latency_ms': round(np.mean(recent_latencies), 2) if recent_latencies else 0,
                    'recent_max_latency_ms': round(max(recent_latencies), 2) if recent_latencies else 0,
                    'current_queue_length': recent_queue_lengths[-1] if recent_queue_lengths else 0,
                    'success_rate_percent': round((self.pipeline_metrics['successful_chunks'] / max(1, self.pipeline_metrics['total_chunks'])) * 100, 2)
                },
                'resource_usage': {
                    'current_cpu_percent': round(recent_cpu[-1], 2) if recent_cpu else 0,
                    'current_memory_percent': round(recent_memory[-1], 2) if recent_memory else 0
                },
                'error_status': {
                    'total_errors': self.pipeline_metrics['failed_chunks'],
                    'recent_critical_errors': len([e for e in self.critical_errors if time.time() - e['timestamp'] < 60])  # Last minute
                }
            }

# Global profiler instance
performance_profiler = ComprehensivePerformanceProfiler()

def start_comprehensive_profiling():
    """Start the comprehensive performance profiler."""
    return performance_profiler.start_profiling()

def stop_comprehensive_profiling():
    """Stop profiling and get final report."""
    return performance_profiler.stop_profiling()

def get_live_metrics():
    """Get real-time performance metrics."""
    return performance_profiler.get_realtime_metrics()

if __name__ == "__main__":
    # Test the profiler
    profiler = ComprehensivePerformanceProfiler()
    profiler.start_profiling()
    
    # Simulate some chunk processing
    profiler.profile_chunk_processing(
        session_id="test_session",
        chunk_id=1,
        audio_size=32000,
        start_time=time.time() - 1.5,
        end_time=time.time(),
        success=True,
        text="Hello world",
        confidence=0.95
    )
    
    # Generate report
    report = profiler.stop_profiling()
    print(json.dumps(report, indent=2))