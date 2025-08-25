#!/usr/bin/env python3
"""
🔍 Comparative QA Pipeline for Mina Live Transcription
Measures Word Error Rate (WER), drift, duplicates, and hallucinations by comparing
live transcription output against reference transcriptions.
"""

import time
import json
import logging
import difflib
import re
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np

@dataclass
class QAMetrics:
    """Quality assurance metrics for transcription comparison."""
    # Core accuracy metrics
    wer: float  # Word Error Rate
    cer: float  # Character Error Rate
    substitutions: int
    insertions: int
    deletions: int
    
    # Content quality metrics
    duplicate_ratio: float  # Ratio of duplicate words/phrases
    hallucination_ratio: float  # Ratio of words not in reference
    drift_score: float  # Semantic drift from reference
    
    # Timing and flow metrics
    latency_seconds: float  # Time to first word
    completion_ratio: float  # Portion of reference captured
    segment_count: int  # Number of transcript segments
    
    # Confidence and reliability
    avg_confidence: float
    low_confidence_ratio: float  # Ratio of segments below threshold
    confidence_correlation: float  # How well confidence predicts accuracy

@dataclass
class TranscriptSegment:
    """Individual transcript segment for analysis."""
    timestamp: float
    text: str
    confidence: float
    is_final: bool
    session_id: str

class QAPipeline:
    """Comparative quality assurance pipeline."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        # Storage for analysis
        self.reference_transcripts: Dict[str, str] = {}
        self.live_segments: Dict[str, List[TranscriptSegment]] = {}
        self.audio_files: Dict[str, str] = {}
        
        # QA thresholds
        self.confidence_threshold = 0.6
        self.duplicate_similarity_threshold = 0.8
        
    def register_reference(self, session_id: str, reference_text: str, audio_file_path: Optional[str] = None):
        """Register reference transcript for comparison."""
        self.reference_transcripts[session_id] = reference_text.strip()
        if audio_file_path:
            self.audio_files[session_id] = audio_file_path
        
        self.logger.info(f"📝 Registered reference for session {session_id}: {len(reference_text)} chars")
    
    def add_live_segment(self, segment: TranscriptSegment):
        """Add live transcription segment for analysis."""
        if segment.session_id not in self.live_segments:
            self.live_segments[segment.session_id] = []
        
        self.live_segments[segment.session_id].append(segment)
        
        # Log significant segments
        if segment.is_final or len(segment.text) > 10:
            self.logger.debug(f"➕ Added segment: {segment.text[:50]}...")
    
    def calculate_wer(self, reference: str, hypothesis: str) -> Tuple[float, int, int, int]:
        """Calculate Word Error Rate and edit operations."""
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        # Use dynamic programming to find edit distance
        d = np.zeros((len(ref_words) + 1, len(hyp_words) + 1), dtype=int)
        
        # Initialize first row and column
        for i in range(len(ref_words) + 1):
            d[i][0] = i
        for j in range(len(hyp_words) + 1):
            d[0][j] = j
        
        # Fill the matrix
        for i in range(1, len(ref_words) + 1):
            for j in range(1, len(hyp_words) + 1):
                if ref_words[i-1] == hyp_words[j-1]:
                    d[i][j] = d[i-1][j-1]
                else:
                    d[i][j] = min(
                        d[i-1][j] + 1,    # deletion
                        d[i][j-1] + 1,    # insertion
                        d[i-1][j-1] + 1   # substitution
                    )
        
        # Backtrack to count operations
        substitutions = insertions = deletions = 0
        i, j = len(ref_words), len(hyp_words)
        
        while i > 0 or j > 0:
            if i > 0 and j > 0 and ref_words[i-1] == hyp_words[j-1]:
                i -= 1
                j -= 1
            elif i > 0 and j > 0 and d[i][j] == d[i-1][j-1] + 1:
                substitutions += 1
                i -= 1
                j -= 1
            elif i > 0 and d[i][j] == d[i-1][j] + 1:
                deletions += 1
                i -= 1
            else:
                insertions += 1
                j -= 1
        
        # Calculate WER
        total_words = len(ref_words)
        wer = d[len(ref_words)][len(hyp_words)] / max(total_words, 1)
        
        return wer, substitutions, insertions, deletions
    
    def calculate_cer(self, reference: str, hypothesis: str) -> float:
        """Calculate Character Error Rate."""
        ref_chars = list(reference.lower())
        hyp_chars = list(hypothesis.lower())
        
        # Simple edit distance for characters
        d = np.zeros((len(ref_chars) + 1, len(hyp_chars) + 1), dtype=int)
        
        for i in range(len(ref_chars) + 1):
            d[i][0] = i
        for j in range(len(hyp_chars) + 1):
            d[0][j] = j
        
        for i in range(1, len(ref_chars) + 1):
            for j in range(1, len(hyp_chars) + 1):
                if ref_chars[i-1] == hyp_chars[j-1]:
                    d[i][j] = d[i-1][j-1]
                else:
                    d[i][j] = min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + 1)
        
        cer = d[len(ref_chars)][len(hyp_chars)] / max(len(ref_chars), 1)
        return cer
    
    def detect_duplicates(self, text: str) -> float:
        """Detect duplicate phrases in transcription."""
        words = text.lower().split()
        if len(words) < 4:
            return 0.0
        
        # Look for repeated n-grams
        duplicate_count = 0
        total_ngrams = 0
        
        for n in range(2, min(6, len(words) // 2)):  # 2-5 word phrases
            ngrams = []
            for i in range(len(words) - n + 1):
                ngram = ' '.join(words[i:i+n])
                ngrams.append(ngram)
            
            # Count duplicates
            ngram_counts = {}
            for ngram in ngrams:
                ngram_counts[ngram] = ngram_counts.get(ngram, 0) + 1
            
            for count in ngram_counts.values():
                if count > 1:
                    duplicate_count += (count - 1) * n  # Extra occurrences * words
                total_ngrams += count * n
        
        return duplicate_count / max(total_ngrams, 1)
    
    def detect_hallucinations(self, reference: str, hypothesis: str) -> float:
        """Detect hallucinated content not present in reference."""
        ref_words = set(reference.lower().split())
        hyp_words = hypothesis.lower().split()
        
        if not hyp_words:
            return 0.0
        
        # Count words in hypothesis not in reference
        hallucinated_words = 0
        for word in hyp_words:
            # Remove punctuation for comparison
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word and clean_word not in ref_words:
                # Check for partial matches (could be valid variations)
                found_similar = False
                for ref_word in ref_words:
                    if len(clean_word) > 3 and (clean_word in ref_word or ref_word in clean_word):
                        found_similar = True
                        break
                
                if not found_similar:
                    hallucinated_words += 1
        
        return hallucinated_words / len(hyp_words)
    
    def calculate_drift_score(self, reference: str, hypothesis: str) -> float:
        """Calculate semantic drift between reference and hypothesis."""
        # Simple approach: measure how much the order and content diverge
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        if not ref_words or not hyp_words:
            return 1.0
        
        # Use sequence similarity
        matcher = difflib.SequenceMatcher(None, ref_words, hyp_words)
        similarity = matcher.ratio()
        
        # Drift is inverse of similarity
        return 1.0 - similarity
    
    def calculate_confidence_correlation(self, segments: List[TranscriptSegment], reference: str) -> float:
        """Calculate how well confidence scores correlate with actual accuracy."""
        if not segments:
            return 0.0
        
        # For each segment, calculate local accuracy and compare with confidence
        correlations = []
        ref_words = reference.lower().split()
        
        for segment in segments:
            if not segment.text.strip():
                continue
            
            # Find best matching portion of reference
            seg_words = segment.text.lower().split()
            best_match_score = 0.0
            
            # Sliding window approach
            for i in range(max(1, len(ref_words) - len(seg_words) + 1)):
                ref_slice = ref_words[i:i+len(seg_words)]
                matcher = difflib.SequenceMatcher(None, seg_words, ref_slice)
                score = matcher.ratio()
                best_match_score = max(best_match_score, score)
            
            correlations.append((segment.confidence, best_match_score))
        
        if len(correlations) < 2:
            return 0.0
        
        # Calculate Pearson correlation
        confidences = [c[0] for c in correlations]
        accuracies = [c[1] for c in correlations]
        
        conf_mean = np.mean(confidences)
        acc_mean = np.mean(accuracies)
        
        numerator = sum((c - conf_mean) * (a - acc_mean) for c, a in zip(confidences, accuracies))
        conf_var = sum((c - conf_mean) ** 2 for c in confidences)
        acc_var = sum((a - acc_mean) ** 2 for a in accuracies)
        
        denominator = np.sqrt(conf_var * acc_var)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def analyze_session(self, session_id: str) -> Optional[QAMetrics]:
        """Analyze a complete session and generate QA metrics."""
        
        if session_id not in self.reference_transcripts:
            self.logger.warning(f"No reference transcript for session {session_id}")
            return None
        
        if session_id not in self.live_segments:
            self.logger.warning(f"No live segments for session {session_id}")
            return None
        
        reference = self.reference_transcripts[session_id]
        segments = self.live_segments[session_id]
        
        # Combine all final segments for comparison
        final_segments = [s for s in segments if s.is_final]
        live_text = ' '.join(s.text for s in final_segments).strip()
        
        if not live_text:
            self.logger.warning(f"No final text for session {session_id}")
            return None
        
        self.logger.info(f"🔍 Analyzing session {session_id}")
        self.logger.info(f"   Reference: {len(reference)} chars")
        self.logger.info(f"   Live text: {len(live_text)} chars")
        self.logger.info(f"   Segments: {len(segments)} total, {len(final_segments)} final")
        
        # Calculate core metrics
        wer, substitutions, insertions, deletions = self.calculate_wer(reference, live_text)
        cer = self.calculate_cer(reference, live_text)
        
        # Calculate quality metrics
        duplicate_ratio = self.detect_duplicates(live_text)
        hallucination_ratio = self.detect_hallucinations(reference, live_text)
        drift_score = self.calculate_drift_score(reference, live_text)
        
        # Calculate timing metrics
        first_segment_time = min((s.timestamp for s in segments), default=0)
        latency_seconds = first_segment_time
        completion_ratio = len(live_text.split()) / max(len(reference.split()), 1)
        
        # Calculate confidence metrics
        confidences = [s.confidence for s in segments if s.confidence > 0]
        avg_confidence = np.mean(confidences) if confidences else 0.0
        low_confidence_ratio = len([c for c in confidences if c < self.confidence_threshold]) / max(len(confidences), 1)
        confidence_correlation = self.calculate_confidence_correlation(segments, reference)
        
        metrics = QAMetrics(
            wer=wer,
            cer=cer,
            substitutions=substitutions,
            insertions=insertions,
            deletions=deletions,
            duplicate_ratio=duplicate_ratio,
            hallucination_ratio=hallucination_ratio,
            drift_score=drift_score,
            latency_seconds=latency_seconds,
            completion_ratio=completion_ratio,
            segment_count=len(segments),
            avg_confidence=avg_confidence,
            low_confidence_ratio=low_confidence_ratio,
            confidence_correlation=confidence_correlation
        )
        
        self.logger.info(f"📊 QA Results for {session_id}:")
        self.logger.info(f"   WER: {wer:.3f} ({wer*100:.1f}%)")
        self.logger.info(f"   CER: {cer:.3f} ({cer*100:.1f}%)")
        self.logger.info(f"   Duplicates: {duplicate_ratio:.3f}")
        self.logger.info(f"   Hallucinations: {hallucination_ratio:.3f}")
        self.logger.info(f"   Completion: {completion_ratio:.3f}")
        
        return metrics
    
    def generate_comparative_report(self) -> Dict[str, Any]:
        """Generate comprehensive comparative QA report."""
        
        all_metrics = {}
        failed_sessions = []
        
        for session_id in self.reference_transcripts.keys():
            try:
                metrics = self.analyze_session(session_id)
                if metrics:
                    all_metrics[session_id] = asdict(metrics)
                else:
                    failed_sessions.append(session_id)
            except Exception as e:
                self.logger.error(f"Failed to analyze session {session_id}: {e}")
                failed_sessions.append(session_id)
        
        if not all_metrics:
            return {
                'error': 'No sessions could be analyzed',
                'failed_sessions': failed_sessions
            }
        
        # Calculate aggregate statistics
        wers = [m['wer'] for m in all_metrics.values()]
        cers = [m['cer'] for m in all_metrics.values()]
        duplicates = [m['duplicate_ratio'] for m in all_metrics.values()]
        hallucinations = [m['hallucination_ratio'] for m in all_metrics.values()]
        
        aggregate_stats = {
            'wer': {
                'mean': np.mean(wers),
                'median': np.median(wers),
                'p95': np.percentile(wers, 95),
                'std': np.std(wers)
            },
            'cer': {
                'mean': np.mean(cers),
                'median': np.median(cers),
                'p95': np.percentile(cers, 95)
            },
            'quality': {
                'avg_duplicate_ratio': np.mean(duplicates),
                'avg_hallucination_ratio': np.mean(hallucinations),
                'sessions_analyzed': len(all_metrics),
                'sessions_failed': len(failed_sessions)
            }
        }
        
        # Generate recommendations
        recommendations = []
        if aggregate_stats['wer']['mean'] > 0.3:
            recommendations.append("🚨 HIGH WER: Word Error Rate exceeds 30%. Check confidence thresholds and VAD settings.")
        
        if aggregate_stats['quality']['avg_duplicate_ratio'] > 0.1:
            recommendations.append("⚠️ HIGH DUPLICATES: Excessive duplicate content detected. Review deduplication logic.")
        
        if aggregate_stats['quality']['avg_hallucination_ratio'] > 0.2:
            recommendations.append("⚠️ HIGH HALLUCINATIONS: Significant non-reference content. Check model stability.")
        
        if not recommendations:
            recommendations.append("✅ Quality metrics within acceptable ranges.")
        
        return {
            'timestamp': time.time(),
            'aggregate_statistics': aggregate_stats,
            'session_metrics': all_metrics,
            'failed_sessions': failed_sessions,
            'recommendations': recommendations,
            'methodology': {
                'wer_calculation': 'Levenshtein distance at word level',
                'duplicate_detection': 'N-gram repetition analysis (2-5 words)',
                'hallucination_detection': 'Words in hypothesis not in reference',
                'confidence_threshold': self.confidence_threshold
            }
        }
    
    def save_report(self, report: Dict[str, Any], output_file: str):
        """Save QA report to file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 QA report saved to {output_file}")

def run_qa_pipeline_demo():
    """Run demonstration of QA pipeline."""
    
    qa = QAPipeline()
    
    # Sample reference text
    reference = "The quick brown fox jumps over the lazy dog. This is a test of the transcription system."
    
    # Sample live transcription with various issues
    segments = [
        TranscriptSegment(1.0, "The quick brown", 0.8, False, "demo"),
        TranscriptSegment(1.5, "The quick brown fox", 0.9, False, "demo"),
        TranscriptSegment(2.0, "The quick brown fox jumps", 0.85, False, "demo"),
        TranscriptSegment(3.0, "The quick brown fox jumps over the lazy dog.", 0.9, True, "demo"),
        TranscriptSegment(4.0, "This is a test test of the transcription system.", 0.7, True, "demo"),  # duplicate
    ]
    
    # Register and analyze
    qa.register_reference("demo", reference)
    for segment in segments:
        qa.add_live_segment(segment)
    
    report = qa.generate_comparative_report()
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    run_qa_pipeline_demo()