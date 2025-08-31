"""
🔬 COMPREHENSIVE QA PIPELINE: Real-time audio vs transcript quality analysis
Measures WER, drift, hallucinations, and performance metrics against industry standards
"""

import os
import time
import logging
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import difflib
import re

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionQualityMetrics:
    """Comprehensive quality metrics for transcription analysis"""
    session_id: str
    chunk_id: str
    timestamp: float
    
    # Core metrics
    wer: float  # Word Error Rate
    drift: float  # Semantic drift percentage
    latency_ms: float  # Processing latency
    confidence: float  # Confidence score
    
    # Text analysis
    word_count: int
    duplicate_ratio: float
    hallucination_score: float
    coherence_score: float
    
    # Audio analysis
    audio_duration_ms: float
    audio_quality_score: float
    signal_to_noise_ratio: float
    
    # Performance
    processing_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float

class ComprehensiveQAPipeline:
    """Production-grade QA pipeline for transcription quality analysis"""
    
    def __init__(self):
        self.session_data = defaultdict(list)
        self.metrics_history = deque(maxlen=1000)  # Last 1000 measurements
        self.performance_thresholds = {
            'wer_excellent': 0.05,  # <5% WER is excellent
            'wer_good': 0.10,       # <10% WER is good
            'latency_excellent': 500,  # <500ms is excellent
            'latency_good': 1000,      # <1s is good
            'confidence_good': 0.80,   # >80% confidence is good
            'drift_acceptable': 0.05    # <5% drift is acceptable
        }
        self.reference_transcripts = {}  # For WER calculation
        self.initialize_qa_pipeline()
        
    def initialize_qa_pipeline(self):
        """Initialize QA pipeline components"""
        try:
            # Initialize performance monitoring
            import psutil
            self.system_monitor = psutil
            logger.info("✅ System monitoring initialized")
        except ImportError:
            logger.warning("⚠️ System monitoring not available")
            self.system_monitor = None
        
        logger.info("🔬 Comprehensive QA Pipeline initialized")
    
    def analyze_transcription_quality(
        self, 
        session_id: str,
        chunk_id: str,
        transcript: str,
        audio_data: bytes,
        confidence: float,
        processing_time_ms: float,
        reference_transcript: Optional[str] = None
    ) -> TranscriptionQualityMetrics:
        """
        Comprehensive quality analysis of transcription result
        """
        start_time = time.time()
        
        try:
            # Calculate WER if reference available
            wer = self._calculate_wer(transcript, reference_transcript) if reference_transcript else 0.0
            
            # Calculate semantic drift
            drift = self._calculate_drift(session_id, transcript)
            
            # Detect hallucinations
            hallucination_score = self._detect_hallucinations(transcript, audio_data)
            
            # Calculate duplicate ratio
            duplicate_ratio = self._calculate_duplicate_ratio(session_id, transcript)
            
            # Analyze coherence
            coherence_score = self._calculate_coherence_score(transcript)
            
            # Audio quality analysis
            audio_quality, snr = self._analyze_audio_quality(audio_data)
            
            # Performance metrics
            performance_metrics = self._get_performance_metrics()
            
            # Create comprehensive metrics
            metrics = TranscriptionQualityMetrics(
                session_id=session_id,
                chunk_id=chunk_id,
                timestamp=time.time(),
                wer=wer,
                drift=drift,
                latency_ms=processing_time_ms,
                confidence=confidence,
                word_count=len(transcript.split()) if transcript else 0,
                duplicate_ratio=duplicate_ratio,
                hallucination_score=hallucination_score,
                coherence_score=coherence_score,
                audio_duration_ms=len(audio_data) / 16,  # Approximate for 16kHz
                audio_quality_score=audio_quality,
                signal_to_noise_ratio=snr,
                processing_time_ms=processing_time_ms,
                memory_usage_mb=performance_metrics['memory_mb'],
                cpu_usage_percent=performance_metrics['cpu_percent']
            )
            
            # Store metrics
            self.session_data[session_id].append(metrics)
            self.metrics_history.append(metrics)
            
            # Log quality assessment
            quality_grade = self._calculate_quality_grade(metrics)
            logger.info(f"🔬 QA Analysis [{session_id}:{chunk_id}] Grade: {quality_grade} | WER: {wer:.1%} | Drift: {drift:.1%} | Latency: {processing_time_ms:.0f}ms")
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ QA analysis failed: {e}")
            # Return minimal metrics on error
            return TranscriptionQualityMetrics(
                session_id=session_id,
                chunk_id=chunk_id,
                timestamp=time.time(),
                wer=1.0,  # Assume worst case
                drift=1.0,
                latency_ms=processing_time_ms,
                confidence=0.0,
                word_count=0,
                duplicate_ratio=1.0,
                hallucination_score=1.0,
                coherence_score=0.0,
                audio_duration_ms=0,
                audio_quality_score=0.0,
                signal_to_noise_ratio=0.0,
                processing_time_ms=processing_time_ms,
                memory_usage_mb=0,
                cpu_usage_percent=0
            )
    
    def _calculate_wer(self, hypothesis: str, reference: str) -> float:
        """Calculate Word Error Rate (WER) between hypothesis and reference"""
        if not hypothesis or not reference:
            return 0.0
        
        # Normalize text
        hyp_words = self._normalize_text(hypothesis).split()
        ref_words = self._normalize_text(reference).split()
        
        if not ref_words:
            return 1.0 if hyp_words else 0.0
        
        # Calculate edit distance
        d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
        
        for i in range(len(ref_words) + 1):
            d[i][0] = i
        for j in range(len(hyp_words) + 1):
            d[0][j] = j
        
        for i in range(1, len(ref_words) + 1):
            for j in range(1, len(hyp_words) + 1):
                if ref_words[i-1] == hyp_words[j-1]:
                    d[i][j] = d[i-1][j-1]
                else:
                    d[i][j] = min(d[i-1][j], d[i][j-1], d[i-1][j-1]) + 1
        
        wer = d[len(ref_words)][len(hyp_words)] / len(ref_words)
        return min(1.0, wer)  # Cap at 100%
    
    def _calculate_drift(self, session_id: str, transcript: str) -> float:
        """Calculate semantic drift within session"""
        session_transcripts = [m.transcript for m in self.session_data[session_id] if hasattr(m, 'transcript')]
        
        if len(session_transcripts) < 2:
            return 0.0
        
        # Compare with previous transcript
        prev_transcript = session_transcripts[-1]
        
        # Simple similarity measure using difflib
        similarity = difflib.SequenceMatcher(None, prev_transcript, transcript).ratio()
        drift = 1.0 - similarity
        
        return min(1.0, max(0.0, drift))
    
    def _detect_hallucinations(self, transcript: str, audio_data: bytes) -> float:
        """Detect Whisper hallucination patterns"""
        if not transcript:
            return 0.0
        
        # Common hallucination patterns
        hallucination_patterns = [
            r'\b(you|you you|thank you)\b',  # Repetitive "you"
            r'\b(\w+)\s+\1\b',              # Word repetition
            r'\b(the the|and and|to to)\b', # Common word repetition
            r'\b[A-Z]{2,}\b',               # All caps (often artifacts)
        ]
        
        hallucination_score = 0.0
        text_lower = transcript.lower()
        
        for pattern in hallucination_patterns:
            matches = len(re.findall(pattern, text_lower))
            if matches > 0:
                hallucination_score += matches * 0.1
        
        # Check audio-text length mismatch (strong hallucination indicator)
        estimated_audio_duration = len(audio_data) / 16000  # Approximate seconds
        word_count = len(transcript.split())
        
        # Typical speaking rate: 150-200 words per minute
        expected_words = estimated_audio_duration * 3  # ~180 WPM
        
        if word_count > expected_words * 2:  # More than double expected
            hallucination_score += 0.5
        
        return min(1.0, hallucination_score)
    
    def _calculate_duplicate_ratio(self, session_id: str, transcript: str) -> float:
        """Calculate ratio of duplicate content in session"""
        session_texts = [getattr(m, 'transcript', '') for m in self.session_data[session_id]]
        
        if not session_texts or not transcript:
            return 0.0
        
        # Check for exact duplicates
        duplicates = sum(1 for text in session_texts if text == transcript)
        
        # Check for partial duplicates (>80% similarity)
        partial_duplicates = 0
        for text in session_texts:
            if text != transcript:
                similarity = difflib.SequenceMatcher(None, text, transcript).ratio()
                if similarity > 0.8:
                    partial_duplicates += 1
        
        total_comparisons = len(session_texts)
        if total_comparisons == 0:
            return 0.0
        
        duplicate_ratio = (duplicates + partial_duplicates * 0.5) / total_comparisons
        return min(1.0, duplicate_ratio)
    
    def _calculate_coherence_score(self, transcript: str) -> float:
        """Calculate transcript coherence score"""
        if not transcript or len(transcript.split()) < 3:
            return 0.0
        
        words = transcript.split()
        coherence_score = 1.0
        
        # Check for basic grammar patterns
        # Penalize too many short words
        short_words = sum(1 for word in words if len(word) <= 2)
        if short_words > len(words) * 0.7:  # More than 70% short words
            coherence_score -= 0.3
        
        # Penalize excessive repetition
        unique_words = len(set(words))
        repetition_ratio = unique_words / len(words) if words else 1.0
        if repetition_ratio < 0.5:  # Less than 50% unique words
            coherence_score -= 0.3
        
        # Penalize missing punctuation in long texts
        if len(words) > 10 and not re.search(r'[.!?]', transcript):
            coherence_score -= 0.2
        
        return max(0.0, coherence_score)
    
    def _analyze_audio_quality(self, audio_data: bytes) -> Tuple[float, float]:
        """Analyze audio quality and signal-to-noise ratio"""
        if not audio_data or len(audio_data) < 1000:
            return 0.0, 0.0
        
        try:
            # Simple quality metrics based on audio characteristics
            audio_length = len(audio_data)
            
            # Estimate quality based on size (higher bitrate = better quality)
            expected_size = audio_length * 0.5  # Rough baseline
            quality_ratio = min(1.0, audio_length / expected_size)
            
            # Estimate SNR (simplified - would need actual audio analysis)
            # For now, use audio length as proxy
            snr_estimate = min(40.0, max(5.0, quality_ratio * 25))
            
            return quality_ratio, snr_estimate
            
        except Exception:
            return 0.5, 10.0  # Default values
    
    def _get_performance_metrics(self) -> Dict[str, float]:
        """Get current system performance metrics"""
        try:
            if self.system_monitor:
                # Get memory usage
                memory = self.system_monitor.virtual_memory()
                memory_mb = memory.used / (1024 * 1024)
                
                # Get CPU usage
                cpu_percent = self.system_monitor.cpu_percent(interval=None)
                
                return {
                    'memory_mb': memory_mb,
                    'cpu_percent': cpu_percent
                }
            else:
                return {'memory_mb': 0, 'cpu_percent': 0}
        except Exception:
            return {'memory_mb': 0, 'cpu_percent': 0}
    
    def _calculate_quality_grade(self, metrics: TranscriptionQualityMetrics) -> str:
        """Calculate overall quality grade A+ to F"""
        score = 100
        
        # WER penalty
        if metrics.wer > 0.15:  # >15% WER
            score -= 40
        elif metrics.wer > 0.10:  # >10% WER
            score -= 25
        elif metrics.wer > 0.05:  # >5% WER
            score -= 10
        
        # Latency penalty
        if metrics.latency_ms > 2000:  # >2s
            score -= 20
        elif metrics.latency_ms > 1000:  # >1s
            score -= 10
        elif metrics.latency_ms > 500:  # >500ms
            score -= 5
        
        # Confidence penalty
        if metrics.confidence < 0.6:
            score -= 20
        elif metrics.confidence < 0.8:
            score -= 10
        
        # Drift penalty
        if metrics.drift > 0.2:
            score -= 15
        elif metrics.drift > 0.1:
            score -= 5
        
        # Hallucination penalty
        if metrics.hallucination_score > 0.3:
            score -= 15
        elif metrics.hallucination_score > 0.1:
            score -= 5
        
        # Grade assignment
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 75:
            return 'C+'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def get_session_report(self, session_id: str) -> Dict:
        """Generate comprehensive session report"""
        session_metrics = self.session_data.get(session_id, [])
        
        if not session_metrics:
            return {'error': 'No data for session'}
        
        # Calculate aggregates
        avg_wer = sum(m.wer for m in session_metrics) / len(session_metrics)
        avg_latency = sum(m.latency_ms for m in session_metrics) / len(session_metrics)
        avg_confidence = sum(m.confidence for m in session_metrics) / len(session_metrics)
        total_words = sum(m.word_count for m in session_metrics)
        
        return {
            'session_id': session_id,
            'total_chunks': len(session_metrics),
            'total_words': total_words,
            'average_wer': avg_wer,
            'average_latency_ms': avg_latency,
            'average_confidence': avg_confidence,
            'quality_grade': self._calculate_quality_grade(session_metrics[-1]),
            'timestamps': [m.timestamp for m in session_metrics],
            'detailed_metrics': [
                {
                    'chunk_id': m.chunk_id,
                    'wer': m.wer,
                    'latency_ms': m.latency_ms,
                    'confidence': m.confidence,
                    'quality_grade': self._calculate_quality_grade(m)
                }
                for m in session_metrics
            ]
        }

# Global QA pipeline instance
qa_pipeline = ComprehensiveQAPipeline()

def analyze_transcription(session_id: str, chunk_id: str, transcript: str, 
                         audio_data: bytes, confidence: float, processing_time_ms: float,
                         reference_transcript: Optional[str] = None) -> TranscriptionQualityMetrics:
    """Convenience function for QA analysis"""
    return qa_pipeline.analyze_transcription_quality(
        session_id, chunk_id, transcript, audio_data, 
        confidence, processing_time_ms, reference_transcript
    )

def get_session_report(session_id: str) -> Dict:
    """Get comprehensive session quality report"""
    return qa_pipeline.get_session_report(session_id)