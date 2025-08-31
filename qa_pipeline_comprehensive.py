#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE: QA Pipeline for Live Transcription Quality Analysis
Measures WER, drift, duplicates, and transcription quality metrics.
"""

import json
import time
import difflib
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import math

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionQualityMetrics:
    """Comprehensive transcription quality metrics."""
    # Core Quality Metrics
    word_error_rate: float
    character_error_rate: float
    semantic_similarity: float
    
    # Drift Analysis
    temporal_drift_score: float
    speaker_consistency: float
    topic_coherence: float
    
    # Error Categories
    substitution_errors: int
    insertion_errors: int
    deletion_errors: int
    
    # Content Analysis
    duplicate_segments: int
    hallucination_count: int
    incomplete_sentences: int
    
    # Timing Metrics
    processing_latency_ms: float
    real_time_factor: float
    
    # Quality Score (0-100)
    overall_quality_score: float

@dataclass
class QAPipelineResult:
    """Complete QA pipeline analysis results."""
    analysis_timestamp: str
    session_id: str
    raw_audio_info: Dict[str, Any]
    live_transcript_info: Dict[str, Any]
    quality_metrics: TranscriptionQualityMetrics
    detailed_analysis: Dict[str, Any]
    recommendations: List[str]

class TranscriptionQAAnalyzer:
    """
    🎯 ENHANCED: Comprehensive transcription quality analyzer.
    """
    
    def __init__(self):
        self.reference_texts = []
        self.hypothesis_texts = []
        self.timestamp_data = []
        
    def calculate_wer(self, reference: str, hypothesis: str) -> Tuple[float, Dict[str, int]]:
        """Calculate Word Error Rate and error breakdown."""
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        # Use dynamic programming for edit distance
        d = [[0 for _ in range(len(hyp_words) + 1)] for _ in range(len(ref_words) + 1)]
        
        # Initialize base cases
        for i in range(len(ref_words) + 1):
            d[i][0] = i
        for j in range(len(hyp_words) + 1):
            d[0][j] = j
        
        # Fill DP table
        for i in range(1, len(ref_words) + 1):
            for j in range(1, len(hyp_words) + 1):
                if ref_words[i-1] == hyp_words[j-1]:
                    d[i][j] = d[i-1][j-1]
                else:
                    substitution = d[i-1][j-1] + 1
                    insertion = d[i][j-1] + 1
                    deletion = d[i-1][j] + 1
                    d[i][j] = min(substitution, insertion, deletion)
        
        # Calculate error counts
        substitutions = 0
        insertions = 0
        deletions = 0
        
        # Backtrack to find operations
        i, j = len(ref_words), len(hyp_words)
        while i > 0 or j > 0:
            if i > 0 and j > 0 and ref_words[i-1] == hyp_words[j-1]:
                i -= 1
                j -= 1
            elif i > 0 and j > 0 and d[i][j] == d[i-1][j-1] + 1:
                substitutions += 1
                i -= 1
                j -= 1
            elif j > 0 and d[i][j] == d[i][j-1] + 1:
                insertions += 1
                j -= 1
            elif i > 0 and d[i][j] == d[i-1][j] + 1:
                deletions += 1
                i -= 1
        
        total_errors = d[len(ref_words)][len(hyp_words)]
        wer = total_errors / len(ref_words) if ref_words else 0
        
        error_breakdown = {
            'substitutions': substitutions,
            'insertions': insertions,
            'deletions': deletions,
            'total': total_errors
        }
        
        return wer, error_breakdown
    
    def calculate_cer(self, reference: str, hypothesis: str) -> float:
        """Calculate Character Error Rate."""
        ref_chars = list(reference.lower())
        hyp_chars = list(hypothesis.lower())
        
        if not ref_chars:
            return 0.0
        
        # Simple Levenshtein distance for characters
        distance = self._levenshtein_distance(ref_chars, hyp_chars)
        return distance / len(ref_chars)
    
    def _levenshtein_distance(self, s1: List[str], s2: List[str]) -> int:
        """Calculate Levenshtein distance between two sequences."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def calculate_semantic_similarity(self, reference: str, hypothesis: str) -> float:
        """Calculate semantic similarity using simple techniques."""
        if not reference or not hypothesis:
            return 0.0
        
        # Word overlap similarity
        ref_words = set(reference.lower().split())
        hyp_words = set(hypothesis.lower().split())
        
        if not ref_words:
            return 0.0
        
        intersection = len(ref_words.intersection(hyp_words))
        union = len(ref_words.union(hyp_words))
        
        jaccard_similarity = intersection / union if union > 0 else 0
        
        # Sequence similarity
        sequence_similarity = difflib.SequenceMatcher(None, reference.lower(), hypothesis.lower()).ratio()
        
        # Combined similarity score
        return (jaccard_similarity + sequence_similarity) / 2
    
    def detect_temporal_drift(self, transcription_segments: List[Dict[str, Any]]) -> float:
        """Detect temporal drift in transcription quality."""
        if len(transcription_segments) < 2:
            return 0.0
        
        # Calculate quality trend over time
        segment_qualities = []
        for segment in transcription_segments:
            confidence = segment.get('confidence', 0.8)
            length = len(segment.get('text', '').split())
            
            # Simple quality metric: confidence * length normalization
            quality = confidence * min(length / 10, 1.0)  # Normalize for reasonable length
            segment_qualities.append(quality)
        
        # Calculate drift as variance in quality over time
        if len(segment_qualities) < 2:
            return 0.0
        
        mean_quality = sum(segment_qualities) / len(segment_qualities)
        variance = sum((q - mean_quality) ** 2 for q in segment_qualities) / len(segment_qualities)
        drift_score = math.sqrt(variance)
        
        return min(drift_score, 1.0)  # Cap at 1.0
    
    def detect_duplicates(self, transcription_segments: List[Dict[str, Any]]) -> int:
        """Detect duplicate or near-duplicate segments."""
        texts = [segment.get('text', '').strip().lower() for segment in transcription_segments]
        
        duplicates = 0
        seen_texts = set()
        
        for text in texts:
            if text in seen_texts and text:
                duplicates += 1
            else:
                seen_texts.add(text)
        
        return duplicates
    
    def detect_hallucinations(self, reference_context: str, hypothesis: str) -> int:
        """Detect potential hallucinations (content not in reference)."""
        if not reference_context or not hypothesis:
            return 0
        
        ref_words = set(reference_context.lower().split())
        hyp_words = hypothesis.lower().split()
        
        # Count words in hypothesis that don't appear in reference context
        hallucinations = 0
        for word in hyp_words:
            if word not in ref_words and len(word) > 2:  # Ignore short words
                hallucinations += 1
        
        return hallucinations
    
    def analyze_incomplete_sentences(self, text: str) -> int:
        """Count incomplete sentences in transcription."""
        if not text.strip():
            return 0
        
        # Split by potential sentence endings
        sentences = re.split(r'[.!?]+', text.strip())
        
        incomplete = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 0:
                # Check for incomplete patterns
                if sentence.endswith(('and', 'or', 'but', 'the', 'a', 'an')):
                    incomplete += 1
                elif len(sentence.split()) < 3:  # Very short fragments
                    incomplete += 1
        
        return incomplete
    
    def calculate_processing_latency(self, audio_duration: float, processing_time: float) -> Tuple[float, float]:
        """Calculate processing latency and real-time factor."""
        latency_ms = processing_time * 1000
        
        # Real-time factor: processing_time / audio_duration
        # <1.0 = faster than real-time, >1.0 = slower than real-time
        rtf = processing_time / audio_duration if audio_duration > 0 else float('inf')
        
        return latency_ms, rtf
    
    def calculate_overall_quality_score(self, metrics: TranscriptionQualityMetrics) -> float:
        """Calculate overall quality score (0-100)."""
        # Weighted scoring
        weights = {
            'accuracy': 0.4,      # WER/CER impact
            'semantic': 0.2,      # Semantic similarity
            'consistency': 0.15,  # Temporal drift
            'completeness': 0.15, # Incomplete sentences
            'duplicates': 0.1     # Duplicate penalty
        }
        
        # Accuracy score (inverted WER/CER)
        accuracy_score = max(0, 100 - (metrics.word_error_rate * 100))
        
        # Semantic score
        semantic_score = metrics.semantic_similarity * 100
        
        # Consistency score (inverted drift)
        consistency_score = max(0, 100 - (metrics.temporal_drift_score * 100))
        
        # Completeness score (penalty for incomplete sentences)
        completeness_penalty = min(metrics.incomplete_sentences * 10, 50)
        completeness_score = max(0, 100 - completeness_penalty)
        
        # Duplicate penalty
        duplicate_penalty = min(metrics.duplicate_segments * 5, 30)
        duplicate_score = max(0, 100 - duplicate_penalty)
        
        # Weighted sum
        overall_score = (
            weights['accuracy'] * accuracy_score +
            weights['semantic'] * semantic_score +
            weights['consistency'] * consistency_score +
            weights['completeness'] * completeness_score +
            weights['duplicates'] * duplicate_score
        )
        
        return round(overall_score, 1)
    
    def run_comprehensive_analysis(self, 
                                 reference_text: str,
                                 live_transcript: str,
                                 transcription_segments: List[Dict[str, Any]],
                                 audio_duration: float,
                                 processing_time: float,
                                 session_id: str = "unknown") -> QAPipelineResult:
        """Run comprehensive QA analysis."""
        
        # Core quality metrics
        wer, error_breakdown = self.calculate_wer(reference_text, live_transcript)
        cer = self.calculate_cer(reference_text, live_transcript)
        semantic_sim = self.calculate_semantic_similarity(reference_text, live_transcript)
        
        # Drift and consistency analysis
        temporal_drift = self.detect_temporal_drift(transcription_segments)
        
        # Content analysis
        duplicates = self.detect_duplicates(transcription_segments)
        hallucinations = self.detect_hallucinations(reference_text, live_transcript)
        incomplete_sentences = self.analyze_incomplete_sentences(live_transcript)
        
        # Performance metrics
        latency_ms, rtf = self.calculate_processing_latency(audio_duration, processing_time)
        
        # Create metrics object
        quality_metrics = TranscriptionQualityMetrics(
            word_error_rate=wer,
            character_error_rate=cer,
            semantic_similarity=semantic_sim,
            temporal_drift_score=temporal_drift,
            speaker_consistency=0.8,  # Placeholder - would need speaker analysis
            topic_coherence=semantic_sim,  # Using semantic similarity as proxy
            substitution_errors=error_breakdown['substitutions'],
            insertion_errors=error_breakdown['insertions'],
            deletion_errors=error_breakdown['deletions'],
            duplicate_segments=duplicates,
            hallucination_count=hallucinations,
            incomplete_sentences=incomplete_sentences,
            processing_latency_ms=latency_ms,
            real_time_factor=rtf,
            overall_quality_score=0  # Will be calculated
        )
        
        # Calculate overall quality score
        quality_metrics.overall_quality_score = self.calculate_overall_quality_score(quality_metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(quality_metrics)
        
        # Detailed analysis
        detailed_analysis = {
            'error_analysis': error_breakdown,
            'performance_analysis': {
                'real_time_capable': rtf < 1.0,
                'latency_acceptable': latency_ms < 2000,
                'quality_threshold_met': quality_metrics.overall_quality_score > 70
            },
            'content_analysis': {
                'semantic_coherence': semantic_sim > 0.7,
                'temporal_stability': temporal_drift < 0.3,
                'duplicate_rate': duplicates / max(len(transcription_segments), 1)
            }
        }
        
        return QAPipelineResult(
            analysis_timestamp=datetime.utcnow().isoformat(),
            session_id=session_id,
            raw_audio_info={
                'duration_seconds': audio_duration,
                'estimated_words': len(reference_text.split()) if reference_text else 0
            },
            live_transcript_info={
                'word_count': len(live_transcript.split()) if live_transcript else 0,
                'segment_count': len(transcription_segments),
                'processing_time_seconds': processing_time
            },
            quality_metrics=quality_metrics,
            detailed_analysis=detailed_analysis,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, metrics: TranscriptionQualityMetrics) -> List[str]:
        """Generate quality improvement recommendations."""
        recommendations = []
        
        if metrics.word_error_rate > 0.2:
            recommendations.append("🔴 HIGH WER: Improve audio quality or model accuracy")
        
        if metrics.temporal_drift_score > 0.4:
            recommendations.append("📈 HIGH DRIFT: Stabilize transcription consistency")
        
        if metrics.duplicate_segments > 5:
            recommendations.append("🔄 DUPLICATES: Implement better deduplication")
        
        if metrics.processing_latency_ms > 3000:
            recommendations.append("⏱️ HIGH LATENCY: Optimize processing pipeline")
        
        if metrics.real_time_factor > 1.2:
            recommendations.append("🐌 SLOW RTF: Improve real-time performance")
        
        if metrics.incomplete_sentences > 3:
            recommendations.append("📝 INCOMPLETE: Improve sentence boundary detection")
        
        if metrics.overall_quality_score < 70:
            recommendations.append("⚠️ LOW QUALITY: Overall transcription quality needs improvement")
        
        return recommendations

def run_qa_analysis_demo() -> Dict[str, Any]:
    """Run QA analysis with demo data."""
    analyzer = TranscriptionQAAnalyzer()
    
    # Demo data based on current system state
    reference_text = "Hello, this is a test of the transcription system. Thank you for listening."
    live_transcript = "You"  # What we're currently seeing
    
    transcription_segments = [
        {
            'text': 'You',
            'confidence': 0.8,
            'timestamp': time.time(),
            'is_final': True
        }
    ]
    
    audio_duration = 5.0  # 5 seconds
    processing_time = 2.5  # 2.5 seconds processing
    
    result = analyzer.run_comprehensive_analysis(
        reference_text=reference_text,
        live_transcript=live_transcript,
        transcription_segments=transcription_segments,
        audio_duration=audio_duration,
        processing_time=processing_time,
        session_id="demo_session"
    )
    
    return asdict(result)

# Initialize global QA pipeline instance for integration
qa_pipeline = TranscriptionQAAnalyzer()

if __name__ == "__main__":
    print("🧪 QA Pipeline Demo")
    results = run_qa_analysis_demo()
    print(json.dumps(results, indent=2))