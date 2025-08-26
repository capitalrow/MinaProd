#!/usr/bin/env python3
"""
🔬 TRANSCRIPTION QA PIPELINE
Comprehensive Quality Assurance for Live Transcription
"""

import time
import json
import asyncio
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import base64
import Levenshtein  # For WER calculation

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionQAMetrics:
    """Quality metrics for transcription analysis"""
    session_id: str
    timestamp: float
    
    # Accuracy Metrics
    wer: float  # Word Error Rate
    cer: float  # Character Error Rate
    bleu_score: float  # BLEU score for fluency
    
    # Latency Metrics
    avg_chunk_latency_ms: float
    p95_chunk_latency_ms: float
    max_chunk_latency_ms: float
    interim_to_final_latency_ms: float
    
    # Quality Metrics
    avg_confidence: float
    min_confidence: float
    confidence_variance: float
    
    # Pipeline Health
    total_chunks: int
    dropped_chunks: int
    retry_count: int
    duplicate_segments: int
    hallucination_count: int
    
    # Audio Quality
    audio_dropout_seconds: float
    noise_ratio: float
    signal_quality_score: float

@dataclass
class TranscriptionSegment:
    """Individual transcription segment for analysis"""
    text: str
    confidence: float
    start_time: float
    end_time: float
    is_final: bool
    latency_ms: float
    chunk_id: str

class TranscriptionQAPipeline:
    """🔬 Comprehensive QA Pipeline for Live Transcription"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.reference_transcripts: Dict[str, str] = {}
        self.audio_buffers: Dict[str, List[bytes]] = {}
        
    def start_session_qa(self, session_id: str, reference_text: Optional[str] = None):
        """Start QA monitoring for a session"""
        self.active_sessions[session_id] = {
            'start_time': time.time(),
            'segments': [],
            'chunks': [],
            'latencies': [],
            'errors': [],
            'audio_chunks': [],
            'interim_segments': [],
            'final_segments': []
        }
        
        if reference_text:
            self.reference_transcripts[session_id] = reference_text
            
        logger.info(f"🔬 QA Pipeline started for session {session_id}")
    
    def record_audio_chunk(self, session_id: str, audio_data: bytes, timestamp: float):
        """Record audio chunk for analysis"""
        if session_id not in self.active_sessions:
            return
            
        chunk_info = {
            'data': audio_data,
            'timestamp': timestamp,
            'size': len(audio_data)
        }
        
        self.active_sessions[session_id]['audio_chunks'].append(chunk_info)
        
        # Analyze audio quality
        self._analyze_audio_quality(session_id, audio_data)
    
    def record_transcription_segment(self, session_id: str, segment: TranscriptionSegment):
        """Record transcription segment for analysis"""
        if session_id not in self.active_sessions:
            return
            
        session_data = self.active_sessions[session_id]
        session_data['segments'].append(segment)
        session_data['latencies'].append(segment.latency_ms)
        
        if segment.is_final:
            session_data['final_segments'].append(segment)
        else:
            session_data['interim_segments'].append(segment)
            
        # Real-time quality checks
        self._check_segment_quality(session_id, segment)
        
        logger.debug(f"📊 Recorded segment: {segment.text[:50]}... (confidence: {segment.confidence:.2f})")
    
    def record_error(self, session_id: str, error_type: str, error_message: str):
        """Record error for analysis"""
        if session_id not in self.active_sessions:
            return
            
        error_info = {
            'type': error_type,
            'message': error_message,
            'timestamp': time.time()
        }
        
        self.active_sessions[session_id]['errors'].append(error_info)
        logger.warning(f"🚨 QA Error recorded: {error_type} - {error_message}")
    
    def calculate_wer(self, reference: str, hypothesis: str) -> float:
        """Calculate Word Error Rate"""
        if not reference or not hypothesis:
            return 1.0
            
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        if not ref_words:
            return 1.0 if hyp_words else 0.0
            
        # Use Levenshtein distance for word-level comparison
        distance = Levenshtein.distance(ref_words, hyp_words)
        wer = distance / len(ref_words)
        
        return min(wer, 1.0)  # Cap at 100%
    
    def calculate_cer(self, reference: str, hypothesis: str) -> float:
        """Calculate Character Error Rate"""
        if not reference or not hypothesis:
            return 1.0
            
        ref_chars = reference.lower().replace(' ', '')
        hyp_chars = hypothesis.lower().replace(' ', '')
        
        if not ref_chars:
            return 1.0 if hyp_chars else 0.0
            
        distance = Levenshtein.distance(ref_chars, hyp_chars)
        cer = distance / len(ref_chars)
        
        return min(cer, 1.0)  # Cap at 100%
    
    def detect_hallucinations(self, segments: List[TranscriptionSegment]) -> int:
        """Detect potential hallucination patterns"""
        hallucination_count = 0
        
        # Common hallucination patterns
        hallucination_patterns = [
            "thank you for watching",
            "subscribe and like",
            "don't forget to",
            "please subscribe",
            "thanks for listening"
        ]
        
        for segment in segments:
            text_lower = segment.text.lower()
            for pattern in hallucination_patterns:
                if pattern in text_lower and segment.confidence > 0.8:
                    hallucination_count += 1
                    logger.warning(f"🤖 Potential hallucination detected: {segment.text}")
                    break
                    
        return hallucination_count
    
    def detect_duplicates(self, segments: List[TranscriptionSegment]) -> int:
        """Detect duplicate segments"""
        duplicate_count = 0
        seen_texts = set()
        
        for segment in segments:
            if segment.is_final:
                text_normalized = segment.text.lower().strip()
                if text_normalized in seen_texts and len(text_normalized) > 10:
                    duplicate_count += 1
                    logger.warning(f"🔄 Duplicate segment detected: {segment.text}")
                else:
                    seen_texts.add(text_normalized)
                    
        return duplicate_count
    
    def _analyze_audio_quality(self, session_id: str, audio_data: bytes):
        """Analyze audio quality metrics"""
        try:
            # Convert audio to numpy array for analysis
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            if len(audio_array) == 0:
                return
                
            # Calculate signal quality metrics
            signal_power = np.mean(audio_array ** 2)
            signal_rms = np.sqrt(signal_power)
            
            # Detect dropouts (periods of silence)
            silence_threshold = 100  # Adjust based on your needs
            silence_samples = np.sum(np.abs(audio_array) < silence_threshold)
            dropout_ratio = silence_samples / len(audio_array)
            
            # Store quality metrics
            session_data = self.active_sessions[session_id]
            if 'audio_quality' not in session_data:
                session_data['audio_quality'] = []
                
            session_data['audio_quality'].append({
                'timestamp': time.time(),
                'signal_rms': float(signal_rms),
                'dropout_ratio': float(dropout_ratio),
                'sample_count': len(audio_array)
            })
            
        except Exception as e:
            logger.error(f"Audio quality analysis failed: {e}")
    
    def _check_segment_quality(self, session_id: str, segment: TranscriptionSegment):
        """Real-time quality checks for segments"""
        # Check for low confidence
        if segment.confidence < 0.3:
            self.record_error(session_id, 'low_confidence', 
                            f"Low confidence segment: {segment.confidence:.2f}")
        
        # Check for excessive latency
        if segment.latency_ms > 3000:  # 3 seconds
            self.record_error(session_id, 'high_latency', 
                            f"High latency: {segment.latency_ms}ms")
        
        # Check for empty segments
        if not segment.text.strip():
            self.record_error(session_id, 'empty_segment', "Empty transcription segment")
    
    def finalize_session_qa(self, session_id: str) -> TranscriptionQAMetrics:
        """Generate final QA metrics for a session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found in QA pipeline")
            
        session_data = self.active_sessions[session_id]
        segments = session_data['segments']
        
        # Calculate comprehensive metrics
        metrics = self._calculate_comprehensive_metrics(session_id, session_data)
        
        # Generate detailed report
        self._generate_qa_report(session_id, metrics)
        
        # Clean up session data
        del self.active_sessions[session_id]
        
        logger.info(f"🔬 QA Pipeline completed for session {session_id}")
        logger.info(f"📊 Final WER: {metrics.wer:.2%}, Avg Latency: {metrics.avg_chunk_latency_ms:.1f}ms")
        
        return metrics
    
    def _calculate_comprehensive_metrics(self, session_id: str, session_data: Dict) -> TranscriptionQAMetrics:
        """Calculate all QA metrics"""
        segments = session_data['segments']
        latencies = session_data['latencies']
        final_segments = session_data['final_segments']
        
        # Combine final segments into complete transcript
        complete_transcript = ' '.join([seg.text for seg in final_segments])
        
        # Calculate accuracy metrics
        wer = 0.0
        cer = 0.0
        if session_id in self.reference_transcripts:
            reference = self.reference_transcripts[session_id]
            wer = self.calculate_wer(reference, complete_transcript)
            cer = self.calculate_cer(reference, complete_transcript)
        
        # Calculate latency metrics
        avg_latency = np.mean(latencies) if latencies else 0.0
        p95_latency = np.percentile(latencies, 95) if latencies else 0.0
        max_latency = max(latencies) if latencies else 0.0
        
        # Calculate confidence metrics
        confidences = [seg.confidence for seg in segments]
        avg_confidence = np.mean(confidences) if confidences else 0.0
        min_confidence = min(confidences) if confidences else 0.0
        confidence_variance = np.var(confidences) if confidences else 0.0
        
        # Calculate quality issues
        duplicate_count = self.detect_duplicates(segments)
        hallucination_count = self.detect_hallucinations(segments)
        
        # Calculate audio quality
        audio_quality = session_data.get('audio_quality', [])
        avg_dropout = np.mean([aq['dropout_ratio'] for aq in audio_quality]) if audio_quality else 0.0
        avg_signal_rms = np.mean([aq['signal_rms'] for aq in audio_quality]) if audio_quality else 0.0
        
        return TranscriptionQAMetrics(
            session_id=session_id,
            timestamp=time.time(),
            wer=wer,
            cer=cer,
            bleu_score=0.0,  # TODO: Implement BLEU calculation
            avg_chunk_latency_ms=avg_latency,
            p95_chunk_latency_ms=p95_latency,
            max_chunk_latency_ms=max_latency,
            interim_to_final_latency_ms=0.0,  # TODO: Calculate interim->final latency
            avg_confidence=avg_confidence,
            min_confidence=min_confidence,
            confidence_variance=confidence_variance,
            total_chunks=len(session_data['audio_chunks']),
            dropped_chunks=len([e for e in session_data['errors'] if e['type'] == 'dropped_chunk']),
            retry_count=len([e for e in session_data['errors'] if e['type'] == 'retry']),
            duplicate_segments=duplicate_count,
            hallucination_count=hallucination_count,
            audio_dropout_seconds=avg_dropout * len(audio_quality),  # Approximate
            noise_ratio=0.0,  # TODO: Implement noise analysis
            signal_quality_score=min(avg_signal_rms / 1000, 1.0)  # Normalized signal quality
        )
    
    def _generate_qa_report(self, session_id: str, metrics: TranscriptionQAMetrics):
        """Generate detailed QA report"""
        report = {
            'session_id': session_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metrics': asdict(metrics),
            'grade': self._calculate_qa_grade(metrics),
            'recommendations': self._generate_recommendations(metrics)
        }
        
        # Save report to file
        filename = f"qa_report_{session_id}_{int(time.time())}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"📄 QA Report saved: {filename}")
        except Exception as e:
            logger.error(f"Failed to save QA report: {e}")
    
    def _calculate_qa_grade(self, metrics: TranscriptionQAMetrics) -> str:
        """Calculate overall QA grade"""
        score = 100
        
        # Deduct for high WER
        score -= metrics.wer * 50  # Max 50 points for accuracy
        
        # Deduct for high latency
        if metrics.avg_chunk_latency_ms > 1000:
            score -= min((metrics.avg_chunk_latency_ms - 1000) / 100, 20)
        
        # Deduct for low confidence
        if metrics.avg_confidence < 0.7:
            score -= (0.7 - metrics.avg_confidence) * 30
        
        # Deduct for quality issues
        score -= metrics.duplicate_segments * 5
        score -= metrics.hallucination_count * 10
        
        score = max(0, score)
        
        if score >= 90: return "A"
        elif score >= 80: return "B"
        elif score >= 70: return "C"
        elif score >= 60: return "D"
        else: return "F"
    
    def _generate_recommendations(self, metrics: TranscriptionQAMetrics) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if metrics.wer > 0.2:  # 20% WER
            recommendations.append("Consider improving audio quality or using a better microphone")
        
        if metrics.avg_chunk_latency_ms > 1500:
            recommendations.append("Optimize transcription pipeline to reduce latency")
        
        if metrics.avg_confidence < 0.6:
            recommendations.append("Check audio input levels and reduce background noise")
        
        if metrics.duplicate_segments > 0:
            recommendations.append("Implement better deduplication logic")
        
        if metrics.hallucination_count > 0:
            recommendations.append("Review transcription model settings to reduce hallucinations")
        
        if metrics.audio_dropout_seconds > 5:
            recommendations.append("Improve audio capture stability")
        
        return recommendations

# Global QA pipeline instance
qa_pipeline = TranscriptionQAPipeline()

def get_qa_pipeline() -> TranscriptionQAPipeline:
    """Get the global QA pipeline instance"""
    return qa_pipeline