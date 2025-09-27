# services/enhanced_streaming_processor.py
"""
Enhanced Streaming Transcription Processor
Advanced streaming pipeline with intelligent partial results, confidence-based filtering,
progressive enhancement, and sophisticated result management.
"""

import asyncio
import logging
import time
import threading
import uuid
from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Tuple
from enum import Enum
import numpy as np
import json
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class ProcessingState(Enum):
    """Processing state for streaming results"""
    INITIAL = "initial"
    PARTIAL = "partial"
    STABLE = "stable"
    FINAL = "final"
    ENHANCED = "enhanced"

class ConfidenceLevel(Enum):
    """Confidence level classifications"""
    VERY_LOW = "very_low"  # < 0.3
    LOW = "low"            # 0.3-0.5
    MEDIUM = "medium"      # 0.5-0.7
    HIGH = "high"          # 0.7-0.9
    VERY_HIGH = "very_high" # > 0.9

@dataclass
class StreamingResult:
    """Advanced streaming transcription result"""
    id: str
    text: str
    confidence: float
    speaker_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    state: ProcessingState = ProcessingState.INITIAL
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    language: Optional[str] = None
    emotions: Dict[str, float] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    sentiment: Optional[float] = None
    stability_score: float = 0.0
    processing_latency: Optional[float] = None
    chunk_id: Optional[str] = None
    session_id: Optional[str] = None
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.confidence_level = self._calculate_confidence_level()
    
    def _calculate_confidence_level(self) -> ConfidenceLevel:
        """Calculate confidence level from score"""
        if self.confidence < 0.3:
            return ConfidenceLevel.VERY_LOW
        elif self.confidence < 0.5:
            return ConfidenceLevel.LOW
        elif self.confidence < 0.7:
            return ConfidenceLevel.MEDIUM
        elif self.confidence < 0.9:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH
    
    def is_acceptable(self, min_confidence: float = 0.5) -> bool:
        """Check if result meets minimum confidence threshold"""
        return self.confidence >= min_confidence
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'text': self.text,
            'confidence': self.confidence,
            'speaker_id': self.speaker_id,
            'timestamp': self.timestamp,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'state': self.state.value,
            'confidence_level': self.confidence_level.value,
            'language': self.language,
            'emotions': self.emotions,
            'keywords': self.keywords,
            'sentiment': self.sentiment,
            'stability_score': self.stability_score,
            'processing_latency': self.processing_latency,
            'chunk_id': self.chunk_id,
            'session_id': self.session_id,
            'alternatives': self.alternatives,
            'metadata': self.metadata
        }

@dataclass
class StreamingConfig:
    """Configuration for streaming processor"""
    min_confidence_threshold: float = 0.5
    stability_threshold: float = 0.8
    partial_results_enabled: bool = True
    max_alternatives: int = 3
    language_detection_enabled: bool = True
    emotion_analysis_enabled: bool = True
    keyword_extraction_enabled: bool = True
    sentiment_analysis_enabled: bool = True
    progressive_enhancement: bool = True
    result_buffering_ms: int = 200
    max_buffer_size: int = 1000
    duplicate_detection_enabled: bool = True
    auto_punctuation: bool = True
    speaker_adaptation: bool = True
    quality_gates_enabled: bool = True

class ResultBuffer:
    """Intelligent result buffering system"""
    
    def __init__(self, config: StreamingConfig):
        self.config = config
        self.buffer = deque(maxlen=config.max_buffer_size)
        self.stability_tracker = defaultdict(list)
        self.last_emission_time = 0
        self.emission_callbacks: List[Callable] = []
        self.lock = threading.Lock()
    
    def add_result(self, result: StreamingResult) -> Optional[StreamingResult]:
        """Add result to buffer and check for emission"""
        with self.lock:
            # Check for duplicates
            if self.config.duplicate_detection_enabled:
                if self._is_duplicate(result):
                    logger.debug(f"🔄 Duplicate result filtered: {result.id}")
                    return None
            
            # Add to buffer
            self.buffer.append(result)
            
            # Track stability
            if result.text:
                self.stability_tracker[result.text].append(result.confidence)
                result.stability_score = self._calculate_stability(result.text)
            
            # Check emission criteria
            return self._check_emission_criteria(result)
    
    def _is_duplicate(self, result: StreamingResult) -> bool:
        """Check if result is a duplicate"""
        for existing in list(self.buffer)[-5:]:  # Check last 5 results
            if (existing.text == result.text and 
                existing.speaker_id == result.speaker_id and
                abs(existing.timestamp - result.timestamp) < 1.0):
                return True
        return False
    
    def _calculate_stability(self, text: str) -> float:
        """Calculate stability score for text"""
        confidences = self.stability_tracker[text]
        if len(confidences) < 2:
            return 0.0
        
        # Calculate variance in confidence
        variance = np.var(confidences)
        stability = max(0.0, 1.0 - variance)
        return stability
    
    def _check_emission_criteria(self, result: StreamingResult) -> Optional[StreamingResult]:
        """Check if result should be emitted"""
        current_time = time.time() * 1000
        
        # Time-based emission
        if (current_time - self.last_emission_time) >= self.config.result_buffering_ms:
            self.last_emission_time = current_time
            return self._get_best_result()
        
        # Confidence-based emission
        if result.confidence >= self.config.stability_threshold:
            self.last_emission_time = current_time
            return result
        
        # Stability-based emission
        if result.stability_score >= self.config.stability_threshold:
            self.last_emission_time = current_time
            return result
        
        return None
    
    def _get_best_result(self) -> Optional[StreamingResult]:
        """Get the best result from buffer"""
        if not self.buffer:
            return None
        
        # Sort by combined score (confidence + stability)
        sorted_results = sorted(
            self.buffer, 
            key=lambda r: r.confidence * 0.7 + r.stability_score * 0.3,
            reverse=True
        )
        
        return sorted_results[0] if sorted_results else None
    
    def force_flush(self) -> List[StreamingResult]:
        """Force flush all buffered results"""
        with self.lock:
            results = list(self.buffer)
            self.buffer.clear()
            self.last_emission_time = time.time() * 1000
            return results

class EnhancedStreamingProcessor:
    """Advanced streaming transcription processor"""
    
    def __init__(self, config: Optional[StreamingConfig] = None):
        self.config = config or StreamingConfig()
        self.result_buffer = ResultBuffer(self.config)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.enhancement_pipeline = []
        self.lock = threading.Lock()
        
        # Initialize enhancement pipeline
        self._initialize_enhancement_pipeline()
        
        logger.info("🚀 Enhanced Streaming Processor initialized with advanced features")
    
    def _initialize_enhancement_pipeline(self):
        """Initialize result enhancement pipeline"""
        self.enhancement_pipeline = [
            self._enhance_punctuation,
            self._enhance_capitalization,
            self._extract_keywords,
            self._analyze_sentiment,
            self._detect_emotions,
            self._normalize_text
        ]
    
    def create_session(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """Create new processing session"""
        with self.lock:
            session_info = {
                'id': session_id,
                'created_at': time.time(),
                'results': [],
                'speakers': {},
                'language': kwargs.get('language'),
                'quality_metrics': {
                    'total_results': 0,
                    'avg_confidence': 0.0,
                    'avg_latency': 0.0,
                    'error_rate': 0.0
                },
                'config': self.config,
                'metadata': kwargs
            }
            
            self.sessions[session_id] = session_info
            logger.info(f"📝 Created enhanced streaming session: {session_id}")
            return session_info
    
    def process_streaming_result(self, session_id: str, raw_result: Dict[str, Any]) -> Optional[StreamingResult]:
        """Process raw transcription result through streaming pipeline"""
        try:
            processing_start = time.time()
            
            # Create streaming result
            result = self._create_streaming_result(session_id, raw_result)
            
            # Apply quality gates
            if self.config.quality_gates_enabled and not self._passes_quality_gates(result):
                logger.debug(f"🚫 Result failed quality gates: {result.id}")
                return None
            
            # Progressive enhancement
            if self.config.progressive_enhancement:
                result = self._apply_progressive_enhancement(result)
            
            # Calculate processing latency
            result.processing_latency = (time.time() - processing_start) * 1000
            
            # Update session metrics
            self._update_session_metrics(session_id, result)
            
            # Buffer and check for emission
            emission_result = self.result_buffer.add_result(result)
            
            if emission_result:
                logger.debug(f"✅ Emitting enhanced result: {emission_result.id}")
                return emission_result
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error processing streaming result: {e}")
            return None
    
    def _create_streaming_result(self, session_id: str, raw_result: Dict[str, Any]) -> StreamingResult:
        """Create StreamingResult from raw result"""
        result_id = raw_result.get('id', str(uuid.uuid4()))
        
        # Determine processing state
        state = ProcessingState.PARTIAL
        if raw_result.get('is_final', False):
            state = ProcessingState.FINAL
        elif raw_result.get('stability', 0) > 0.8:
            state = ProcessingState.STABLE
        
        return StreamingResult(
            id=result_id,
            text=raw_result.get('text', ''),
            confidence=raw_result.get('confidence', 0.0),
            speaker_id=raw_result.get('speaker_id'),
            start_time=raw_result.get('start_time'),
            end_time=raw_result.get('end_time'),
            state=state,
            language=raw_result.get('language'),
            chunk_id=raw_result.get('chunk_id'),
            session_id=session_id,
            alternatives=raw_result.get('alternatives', []),
            metadata=raw_result.get('metadata', {})
        )
    
    def _passes_quality_gates(self, result: StreamingResult) -> bool:
        """Check if result passes quality gates"""
        # Minimum confidence check
        if result.confidence < self.config.min_confidence_threshold:
            return False
        
        # Text length check
        if len(result.text.strip()) < 2:
            return False
        
        # Language consistency check
        if result.language and result.session_id in self.sessions:
            session_lang = self.sessions[result.session_id].get('language')
            if session_lang and session_lang != result.language:
                # Allow language switching with high confidence
                if result.confidence < 0.8:
                    return False
        
        return True
    
    def _apply_progressive_enhancement(self, result: StreamingResult) -> StreamingResult:
        """Apply progressive enhancement pipeline"""
        for enhancer in self.enhancement_pipeline:
            try:
                result = enhancer(result)
            except Exception as e:
                logger.warning(f"⚠️ Enhancement step failed: {e}")
                continue
        
        result.state = ProcessingState.ENHANCED
        return result
    
    def _enhance_punctuation(self, result: StreamingResult) -> StreamingResult:
        """Add intelligent punctuation"""
        if not self.config.auto_punctuation or not result.text:
            return result
        
        text = result.text.strip()
        
        # Simple punctuation rules
        if text and not text[-1] in '.!?':
            # Add period for statements
            if not any(word in text.lower() for word in ['what', 'how', 'when', 'where', 'why', 'who']):
                text += '.'
            else:
                text += '?'
        
        result.text = text
        return result
    
    def _enhance_capitalization(self, result: StreamingResult) -> StreamingResult:
        """Improve capitalization"""
        if not result.text:
            return result
        
        # Capitalize first word and after periods
        sentences = result.text.split('. ')
        capitalized = []
        
        for sentence in sentences:
            if sentence:
                sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                capitalized.append(sentence)
        
        result.text = '. '.join(capitalized)
        return result
    
    def _extract_keywords(self, result: StreamingResult) -> StreamingResult:
        """Extract keywords from text"""
        if not self.config.keyword_extraction_enabled or not result.text:
            return result
        
        # Simple keyword extraction (could be enhanced with NLP)
        words = result.text.lower().split()
        
        # Filter common words and find important terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Take top keywords by length (simple heuristic)
        keywords = sorted(set(keywords), key=len, reverse=True)[:5]
        result.keywords = keywords
        
        return result
    
    def _analyze_sentiment(self, result: StreamingResult) -> StreamingResult:
        """Analyze sentiment of text"""
        if not self.config.sentiment_analysis_enabled or not result.text:
            return result
        
        # Simple sentiment analysis (could be enhanced with ML models)
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'like', 'happy', 'pleased']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'sad', 'angry', 'disappointed', 'frustrated']
        
        text_lower = result.text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count + negative_count > 0:
            result.sentiment = (positive_count - negative_count) / (positive_count + negative_count)
        else:
            result.sentiment = 0.0
        
        return result
    
    def _detect_emotions(self, result: StreamingResult) -> StreamingResult:
        """Detect emotions in text"""
        if not self.config.emotion_analysis_enabled or not result.text:
            return result
        
        # Simple emotion detection (could be enhanced with ML models)
        emotion_keywords = {
            'joy': ['happy', 'excited', 'wonderful', 'fantastic', 'love', 'great'],
            'anger': ['angry', 'mad', 'furious', 'hate', 'annoyed'],
            'sadness': ['sad', 'depressed', 'disappointed', 'unhappy'],
            'fear': ['scared', 'afraid', 'worried', 'nervous'],
            'surprise': ['surprised', 'shocked', 'amazed', 'wow']
        }
        
        text_lower = result.text.lower()
        emotions = {}
        
        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                emotions[emotion] = min(1.0, score / 3.0)  # Normalize to 0-1
        
        result.emotions = emotions
        return result
    
    def _normalize_text(self, result: StreamingResult) -> StreamingResult:
        """Normalize text formatting"""
        if not result.text:
            return result
        
        # Clean up extra spaces
        text = ' '.join(result.text.split())
        
        # Fix common transcription issues
        text = text.replace(' i ', ' I ')
        text = text.replace(' i\'', ' I\'')
        
        result.text = text
        return result
    
    def _update_session_metrics(self, session_id: str, result: StreamingResult):
        """Update session quality metrics"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        metrics = session['quality_metrics']
        
        # Update counters
        metrics['total_results'] += 1
        
        # Update running averages
        total = metrics['total_results']
        metrics['avg_confidence'] = ((metrics['avg_confidence'] * (total - 1)) + result.confidence) / total
        
        if result.processing_latency:
            metrics['avg_latency'] = ((metrics['avg_latency'] * (total - 1)) + result.processing_latency) / total
        
        # Store result
        session['results'].append(result)
        
        # Update speaker info
        if result.speaker_id:
            if result.speaker_id not in session['speakers']:
                session['speakers'][result.speaker_id] = {
                    'first_seen': time.time(),
                    'total_words': 0,
                    'avg_confidence': 0.0
                }
            
            speaker = session['speakers'][result.speaker_id]
            speaker['total_words'] += len(result.text.split())
            speaker['last_seen'] = time.time()
    
    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session analytics"""
        if session_id not in self.sessions:
            return {}
        
        session = self.sessions[session_id]
        results = session['results']
        
        if not results:
            return session
        
        # Calculate advanced metrics
        total_duration = max(r.timestamp for r in results) - min(r.timestamp for r in results)
        total_words = sum(len(r.text.split()) for r in results)
        confidence_scores = [r.confidence for r in results]
        
        analytics = {
            **session,
            'analytics': {
                'total_duration_seconds': total_duration,
                'total_words': total_words,
                'words_per_minute': (total_words / max(total_duration / 60, 1)),
                'confidence_distribution': {
                    'mean': np.mean(confidence_scores),
                    'std': np.std(confidence_scores),
                    'min': np.min(confidence_scores),
                    'max': np.max(confidence_scores)
                },
                'state_distribution': {
                    state.value: sum(1 for r in results if r.state == state)
                    for state in ProcessingState
                },
                'language_distribution': {
                    lang: sum(1 for r in results if r.language == lang)
                    for lang in set(r.language for r in results if r.language)
                },
                'emotion_summary': self._analyze_session_emotions(results),
                'keyword_frequency': self._analyze_session_keywords(results)
            }
        }
        
        return analytics
    
    def _analyze_session_emotions(self, results: List[StreamingResult]) -> Dict[str, Any]:
        """Analyze emotions across session"""
        all_emotions = defaultdict(list)
        
        for result in results:
            for emotion, score in result.emotions.items():
                all_emotions[emotion].append(score)
        
        emotion_summary = {}
        for emotion, scores in all_emotions.items():
            emotion_summary[emotion] = {
                'mean': np.mean(scores),
                'max': np.max(scores),
                'frequency': len(scores)
            }
        
        return emotion_summary
    
    def _analyze_session_keywords(self, results: List[StreamingResult]) -> Dict[str, int]:
        """Analyze keyword frequency across session"""
        keyword_counts = defaultdict(int)
        
        for result in results:
            for keyword in result.keywords:
                keyword_counts[keyword] += 1
        
        # Return top 20 keywords
        return dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:20])
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End session and return final analytics"""
        if session_id not in self.sessions:
            return {}
        
        # Force flush any remaining results
        remaining_results = self.result_buffer.force_flush()
        
        # Get final analytics
        final_analytics = self.get_session_analytics(session_id)
        
        # Cleanup
        del self.sessions[session_id]
        
        logger.info(f"🏁 Enhanced streaming session ended: {session_id}")
        return final_analytics

# Global processor instance
_streaming_processor = None
_processor_lock = threading.Lock()

def get_enhanced_streaming_processor(config: Optional[StreamingConfig] = None) -> EnhancedStreamingProcessor:
    """Get global enhanced streaming processor instance"""
    global _streaming_processor
    
    with _processor_lock:
        if _streaming_processor is None:
            _streaming_processor = EnhancedStreamingProcessor(config)
        return _streaming_processor

logger.info("✅ Enhanced Streaming Processor module initialized")