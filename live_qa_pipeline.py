#!/usr/bin/env python3
"""
Live Transcription QA Pipeline
Computes WER, drift, duplicates, hallucinations in real-time
"""

import json
import time
import logging
import difflib
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics

logger = logging.getLogger('live_qa_pipeline')

@dataclass
class QualityMetrics:
    """Real-time quality metrics"""
    session_id: str
    timestamp: float
    wer_score: float = 0.0
    confidence_avg: float = 0.0
    duplicate_ratio: float = 0.0
    repetitive_patterns: int = 0
    text_length: int = 0
    words_per_minute: float = 0.0
    overall_quality: float = 0.0

class LiveQAProcessor:
    """Real-time quality assessment processor"""
    
    def __init__(self):
        self.session_transcripts: Dict[str, List[str]] = {}
        self.session_audio: Dict[str, List[bytes]] = {}
        self.quality_history: Dict[str, List[QualityMetrics]] = {}
        self.repetitive_patterns = [
            r'\b(\w+)\s+\1\b',  # Word repetition: "you you"
            r'\b(\w+)\s+\1\s+\1\b',  # Triple repetition
            r'\b(\w{1,3})\s+\1\s+\1\b'  # Short word repetition
        ]
        
    def store_audio(self, session_id: str, audio_data: bytes):
        """Store raw audio for analysis"""
        if session_id not in self.session_audio:
            self.session_audio[session_id] = []
        self.session_audio[session_id].append(audio_data)
        
    def store_transcript(self, session_id: str, text: str, confidence: float = 1.0):
        """Store transcript segment and analyze quality"""
        if session_id not in self.session_transcripts:
            self.session_transcripts[session_id] = []
            self.quality_history[session_id] = []
        
        self.session_transcripts[session_id].append(text)
        
        # Real-time quality analysis
        metrics = self._analyze_quality(session_id, text, confidence)
        self.quality_history[session_id].append(metrics)
        
        logger.info(f"QA Analysis - Session {session_id}: Quality={metrics.overall_quality:.2f}, WER={metrics.wer_score:.2f}")
        return metrics
    
    def _analyze_quality(self, session_id: str, text: str, confidence: float) -> QualityMetrics:
        """Analyze quality metrics for transcript segment"""
        metrics = QualityMetrics(
            session_id=session_id,
            timestamp=time.time(),
            confidence_avg=confidence,
            text_length=len(text)
        )
        
        # Detect repetitive patterns
        for pattern in self.repetitive_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            metrics.repetitive_patterns += len(matches)
        
        # Calculate duplicate ratio against recent segments
        recent_transcripts = self.session_transcripts[session_id][-5:]  # Last 5 segments
        duplicates = sum(1 for prev_text in recent_transcripts if 
                        self._similarity(text, prev_text) > 0.8)
        metrics.duplicate_ratio = duplicates / max(len(recent_transcripts), 1)
        
        # Estimate WER (without ground truth, use heuristics)
        metrics.wer_score = self._estimate_wer(text, confidence)
        
        # Calculate words per minute
        words = len(text.split())
        time_elapsed = max(time.time() - (self.quality_history[session_id][0].timestamp if self.quality_history[session_id] else time.time()), 1)
        metrics.words_per_minute = (words * 60) / time_elapsed
        
        # Overall quality score
        metrics.overall_quality = self._calculate_overall_quality(metrics)
        
        return metrics
    
    def _similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using sequence matcher"""
        return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def _estimate_wer(self, text: str, confidence: float) -> float:
        """Estimate WER using confidence and heuristics"""
        # Heuristic: lower confidence correlates with higher WER
        confidence_wer = 1.0 - confidence
        
        # Pattern-based WER estimation
        pattern_penalty = min(len(re.findall(r'\b(\w+)\s+\1\b', text, re.IGNORECASE)) * 0.2, 0.5)
        
        # Length-based adjustment (very short or long texts may have issues)
        words = text.split()
        length_penalty = 0.1 if len(words) < 3 or len(words) > 50 else 0.0
        
        estimated_wer = confidence_wer + pattern_penalty + length_penalty
        return min(estimated_wer, 1.0)
    
    def _calculate_overall_quality(self, metrics: QualityMetrics) -> float:
        """Calculate overall quality score (0-1)"""
        if metrics.text_length == 0:
            return 0.0
        
        # Quality factors
        confidence_quality = metrics.confidence_avg
        wer_quality = 1.0 - metrics.wer_score
        duplicate_quality = 1.0 - metrics.duplicate_ratio
        repetition_quality = 1.0 - min(metrics.repetitive_patterns / 5.0, 1.0)
        
        # Weighted average
        overall = (
            confidence_quality * 0.4 +
            wer_quality * 0.3 +
            duplicate_quality * 0.2 +
            repetition_quality * 0.1
        )
        
        return min(max(overall, 0.0), 1.0)
    
    def get_session_report(self, session_id: str) -> Dict[str, Any]:
        """Generate comprehensive QA report for session"""
        if session_id not in self.quality_history:
            return {'error': f'No data for session {session_id}'}
        
        metrics_list = self.quality_history[session_id]
        if not metrics_list:
            return {'error': 'No metrics available'}
        
        # Aggregate statistics
        avg_quality = statistics.mean(m.overall_quality for m in metrics_list)
        avg_wer = statistics.mean(m.wer_score for m in metrics_list)
        avg_confidence = statistics.mean(m.confidence_avg for m in metrics_list)
        total_repetitions = sum(m.repetitive_patterns for m in metrics_list)
        
        # Full transcript analysis
        full_transcript = ' '.join(self.session_transcripts.get(session_id, []))
        
        return {
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_segments': len(metrics_list),
                'avg_quality_score': avg_quality,
                'avg_wer': avg_wer,
                'avg_confidence': avg_confidence,
                'total_repetitive_patterns': total_repetitions,
                'full_transcript': full_transcript,
                'total_words': len(full_transcript.split())
            },
            'timeline': [asdict(m) for m in metrics_list]
        }
    
    def export_results(self, filename: str):
        """Export all QA results to JSON"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'sessions': {sid: self.get_session_report(sid) 
                        for sid in self.quality_history.keys()}
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"QA results exported to {filename}")

# Global QA processor
qa_processor = LiveQAProcessor()

def get_qa_processor() -> LiveQAProcessor:
    """Get the global QA processor instance"""
    return qa_processor