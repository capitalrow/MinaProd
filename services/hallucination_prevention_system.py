"""
Hallucination Prevention System - Google Recorder Level Accuracy
Advanced detection and prevention of transcription hallucinations for enterprise-grade accuracy.
Implements multi-layer validation, confidence analysis, and intelligent filtering.
"""

import logging
import time
import re
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import deque, Counter
from enum import Enum
import string

logger = logging.getLogger(__name__)

class HallucinationType(Enum):
    """Types of transcription hallucinations."""
    REPETITIVE_PHRASES = "repetitive_phrases"
    NONSENSE_WORDS = "nonsense_words"
    AUDIO_ARTIFACTS = "audio_artifacts"
    LANGUAGE_CONFUSION = "language_confusion"
    PHANTOM_SPEECH = "phantom_speech"
    OVERCONFIDENT_NOISE = "overconfident_noise"
    MUSICAL_INTERPRETATION = "musical_interpretation"

@dataclass
class HallucinationDetection:
    """Hallucination detection result."""
    is_hallucination: bool
    confidence: float
    hallucination_type: Optional[HallucinationType]
    severity: float
    evidence: List[str]
    corrected_text: Optional[str] = None
    prevention_action: str = "none"

@dataclass
class ValidationContext:
    """Context for hallucination validation."""
    original_text: str
    audio_duration: float
    audio_quality_score: float
    confidence_score: float
    previous_segments: List[str]
    environmental_noise_level: float
    speaker_detection_confidence: float
    language_detection_confidence: float

class HallucinationPreventionSystem:
    """
    🛡️ Google Recorder-level hallucination prevention system.
    
    Implements comprehensive validation and prevention mechanisms:
    - Multi-layer confidence analysis and thresholding
    - Pattern recognition for common hallucination types
    - Audio-text correlation validation
    - Contextual consistency checking
    - Intelligent filtering and correction
    - Real-time quality gates
    """
    
    def __init__(self, strictness_level: float = 0.8):
        self.strictness_level = strictness_level  # 0.0 = permissive, 1.0 = strict
        
        # Detection thresholds
        self.min_confidence_threshold = 0.6 + (strictness_level * 0.2)
        self.max_repetition_ratio = 0.3 - (strictness_level * 0.1)
        self.min_audio_duration_ratio = 0.1  # text should be at least 10% of audio duration
        self.max_words_per_second = 8.0 - (strictness_level * 2.0)
        
        # Pattern databases
        self._initialize_hallucination_patterns()
        
        # Context tracking
        self.session_history: Dict[str, deque] = {}
        self.global_patterns = deque(maxlen=1000)
        
        # Performance tracking
        self.detection_stats = {
            'total_validations': 0,
            'hallucinations_detected': 0,
            'hallucinations_by_type': Counter(),
            'false_positive_rate': 0.0,
            'prevention_success_rate': 0.0
        }
        
        logger.info(f"🛡️ Hallucination Prevention System initialized (strictness: {strictness_level})")
    
    def _initialize_hallucination_patterns(self):
        """🔍 Initialize known hallucination patterns."""
        # Common repetitive phrases that indicate hallucinations
        self.repetitive_patterns = {
            'thank_you_loops': [r'\b(thank you\s*){3,}', r'\b(thanks\s*){3,}'],
            'bye_loops': [r'\b(bye\s*){3,}', r'\b(goodbye\s*){3,}'],
            'music_artifacts': [r'\b(la\s*){4,}', r'\b(na\s*){4,}', r'\b(da\s*){4,}'],
            'applause_misinterpret': [r'\b(clap\s*){3,}', r'\b(applause\s*){2,}'],
            'breathing_artifacts': [r'\b(ah\s*){3,}', r'\b(uh\s*){4,}', r'\b(um\s*){4,}']
        }
        
        # Nonsense word patterns
        self.nonsense_patterns = [
            r'\b[bcdfghjklmnpqrstvwxyz]{4,}\b',  # Consonant clusters
            r'\b[aeiou]{4,}\b',                  # Vowel clusters
            r'\b\w*[xyz]\w*[xyz]\w*\b',          # Multiple rare letters
            r'\b[qx]\w*[qx]\w*\b'                # Multiple very rare letters
        ]
        
        # Audio artifact indicators
        self.audio_artifact_patterns = [
            r'\b(static|noise|buzz|hum|interference)\b',
            r'\b(beep|boop|click|pop|crack)\b',
            r'\b(echo|reverb|feedback)\b'
        ]
        
        # Language confusion indicators
        self.language_confusion_patterns = [
            r'[^\x00-\x7F]+',  # Non-ASCII characters in English mode
            r'\b(the|and|or|but)\s+[^\x00-\x7F]+',  # Mixed language patterns
        ]
        
        # Musical interpretation patterns
        self.musical_patterns = [
            r'\b(do|re|mi|fa|sol|la|ti)\s+(do|re|mi|fa|sol|la|ti)\b',
            r'\b(one|two|three|four)\s+and\s+(one|two|three|four)\b',  # Beat counting
            r'\b(instrumental|music|song|melody|rhythm)\b'
        ]
        
        # Common words for validation
        self.common_words = set([
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'can', 'could', 'should', 'may', 'might', 'must',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'this', 'that', 'these', 'those', 'what', 'where', 'when', 'why', 'how', 'who',
            'yes', 'no', 'ok', 'okay', 'right', 'good', 'well', 'nice', 'great', 'fine'
        ])
    
    def validate_transcription(self, text: str, context: ValidationContext, 
                             session_id: str) -> HallucinationDetection:
        """
        🔍 Validate transcription for potential hallucinations.
        
        Args:
            text: Transcribed text to validate
            context: Validation context with audio and quality information
            session_id: Session identifier for context tracking
            
        Returns:
            Hallucination detection result with prevention recommendations
        """
        start_time = time.time()
        
        try:
            self.detection_stats['total_validations'] += 1
            
            # Initialize session history if needed
            if session_id not in self.session_history:
                self.session_history[session_id] = deque(maxlen=20)
            
            # Run multiple validation layers
            validations = []
            
            # Layer 1: Basic quality validation
            basic_validation = self._validate_basic_quality(text, context)
            validations.append(basic_validation)
            
            # Layer 2: Pattern-based detection
            pattern_validation = self._detect_pattern_hallucinations(text, context)
            validations.append(pattern_validation)
            
            # Layer 3: Audio-text correlation
            correlation_validation = self._validate_audio_text_correlation(text, context)
            validations.append(correlation_validation)
            
            # Layer 4: Contextual consistency
            context_validation = self._validate_contextual_consistency(text, session_id)
            validations.append(context_validation)
            
            # Layer 5: Confidence analysis
            confidence_validation = self._analyze_confidence_patterns(text, context)
            validations.append(confidence_validation)
            
            # Combine validation results
            final_detection = self._combine_validation_results(validations, text, context)
            
            # Update session history
            self.session_history[session_id].append({
                'text': text,
                'timestamp': time.time(),
                'is_hallucination': final_detection.is_hallucination,
                'confidence': context.confidence_score
            })
            
            # Update statistics
            if final_detection.is_hallucination:
                self.detection_stats['hallucinations_detected'] += 1
                if final_detection.hallucination_type:
                    self.detection_stats['hallucinations_by_type'][final_detection.hallucination_type.value] += 1
            
            # Add to global patterns
            self.global_patterns.append({
                'text': text,
                'is_hallucination': final_detection.is_hallucination,
                'type': final_detection.hallucination_type.value if final_detection.hallucination_type else 'none',
                'confidence': context.confidence_score,
                'audio_quality': context.audio_quality_score
            })
            
            logger.debug(f"🔍 Validation completed in {time.time() - start_time:.3f}s: "
                        f"hallucination={final_detection.is_hallucination}, "
                        f"confidence={final_detection.confidence:.2f}")
            
            return final_detection
            
        except Exception as e:
            logger.error(f"❌ Transcription validation failed: {e}")
            return HallucinationDetection(
                is_hallucination=False,
                confidence=0.5,
                hallucination_type=None,
                severity=0.0,
                evidence=['validation_error'],
                prevention_action='allow_with_warning'
            )
    
    def _validate_basic_quality(self, text: str, context: ValidationContext) -> HallucinationDetection:
        """✅ Basic quality validation checks."""
        try:
            evidence = []
            severity_factors = []
            
            # Check minimum confidence threshold
            if context.confidence_score < self.min_confidence_threshold:
                evidence.append(f"Low confidence: {context.confidence_score:.2f}")
                severity_factors.append((context.confidence_score - self.min_confidence_threshold) * -2)
            
            # Check audio quality correlation
            if context.audio_quality_score < 0.4 and context.confidence_score > 0.8:
                evidence.append("High confidence despite poor audio quality")
                severity_factors.append(0.6)
            
            # Check text-to-audio duration ratio
            if context.audio_duration > 0:
                words = len(text.split())
                words_per_second = words / context.audio_duration
                
                if words_per_second > self.max_words_per_second:
                    evidence.append(f"Unrealistic speech rate: {words_per_second:.1f} words/sec")
                    severity_factors.append(min(1.0, (words_per_second - self.max_words_per_second) / 5))
                
                # Check minimum duration ratio
                estimated_speech_duration = words * 0.6  # ~0.6 seconds per word
                duration_ratio = estimated_speech_duration / context.audio_duration
                
                if duration_ratio < self.min_audio_duration_ratio:
                    evidence.append(f"Text too long for audio duration: {duration_ratio:.2f} ratio")
                    severity_factors.append(0.4)
            
            # Check empty or very short text with high confidence
            if len(text.strip()) < 3 and context.confidence_score > 0.7:
                evidence.append("Very short text with high confidence")
                severity_factors.append(0.3)
            
            # Calculate overall severity
            severity = np.mean(severity_factors) if severity_factors else 0.0
            is_hallucination = severity > 0.3 or len(evidence) >= 2
            
            return HallucinationDetection(
                is_hallucination=is_hallucination,
                confidence=min(1.0, severity + 0.2),
                hallucination_type=HallucinationType.OVERCONFIDENT_NOISE if is_hallucination else None,
                severity=severity,
                evidence=evidence,
                prevention_action='filter' if is_hallucination else 'allow'
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Basic quality validation failed: {e}")
            return HallucinationDetection(
                is_hallucination=False, confidence=0.0, hallucination_type=None,
                severity=0.0, evidence=['validation_error']
            )
    
    def _detect_pattern_hallucinations(self, text: str, context: ValidationContext) -> HallucinationDetection:
        """🔍 Detect pattern-based hallucinations."""
        try:
            evidence = []
            severity_factors = []
            hallucination_type = None
            
            text_lower = text.lower()
            
            # Check repetitive patterns
            for pattern_name, patterns in self.repetitive_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, text_lower)
                    if matches:
                        evidence.append(f"Repetitive pattern detected: {pattern_name}")
                        severity_factors.append(0.7)
                        hallucination_type = HallucinationType.REPETITIVE_PHRASES
            
            # Check nonsense words
            for pattern in self.nonsense_patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    # Validate against common words
                    nonsense_matches = [m for m in matches if m not in self.common_words]
                    if nonsense_matches:
                        evidence.append(f"Nonsense words detected: {nonsense_matches[:3]}")
                        severity_factors.append(0.5)
                        hallucination_type = HallucinationType.NONSENSE_WORDS
            
            # Check audio artifact patterns
            for pattern in self.audio_artifact_patterns:
                if re.search(pattern, text_lower):
                    evidence.append("Audio artifact interpretation detected")
                    severity_factors.append(0.6)
                    hallucination_type = HallucinationType.AUDIO_ARTIFACTS
            
            # Check language confusion
            for pattern in self.language_confusion_patterns:
                if re.search(pattern, text):
                    evidence.append("Language confusion detected")
                    severity_factors.append(0.4)
                    hallucination_type = HallucinationType.LANGUAGE_CONFUSION
            
            # Check musical patterns
            for pattern in self.musical_patterns:
                if re.search(pattern, text_lower):
                    evidence.append("Musical interpretation detected")
                    severity_factors.append(0.5)
                    hallucination_type = HallucinationType.MUSICAL_INTERPRETATION
            
            # Check character repetition
            char_repetition = self._analyze_character_repetition(text)
            if char_repetition > 0.4:
                evidence.append(f"High character repetition: {char_repetition:.2f}")
                severity_factors.append(char_repetition)
                hallucination_type = HallucinationType.REPETITIVE_PHRASES
            
            # Check word repetition
            word_repetition = self._analyze_word_repetition(text)
            if word_repetition > self.max_repetition_ratio:
                evidence.append(f"High word repetition: {word_repetition:.2f}")
                severity_factors.append(word_repetition)
                hallucination_type = HallucinationType.REPETITIVE_PHRASES
            
            severity = np.max(severity_factors) if severity_factors else 0.0
            is_hallucination = severity > 0.4 or len(evidence) >= 2
            
            return HallucinationDetection(
                is_hallucination=is_hallucination,
                confidence=min(1.0, severity + 0.1),
                hallucination_type=hallucination_type,
                severity=severity,
                evidence=evidence,
                prevention_action='filter' if is_hallucination else 'allow'
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Pattern detection failed: {e}")
            return HallucinationDetection(
                is_hallucination=False, confidence=0.0, hallucination_type=None,
                severity=0.0, evidence=['pattern_detection_error']
            )
    
    def _validate_audio_text_correlation(self, text: str, context: ValidationContext) -> HallucinationDetection:
        """🎵 Validate correlation between audio and text."""
        try:
            evidence = []
            severity_factors = []
            
            # High confidence with very noisy environment
            if context.environmental_noise_level > 0.7 and context.confidence_score > 0.8:
                evidence.append("High confidence despite noisy environment")
                severity_factors.append(0.5)
            
            # Long text from very short audio
            if context.audio_duration < 1.0 and len(text.split()) > 5:
                evidence.append("Long text from short audio")
                severity_factors.append(0.6)
            
            # Speaker detection mismatch
            if context.speaker_detection_confidence < 0.3 and len(text.strip()) > 10:
                evidence.append("Text detected without clear speaker presence")
                severity_factors.append(0.4)
            
            # Language detection confidence mismatch
            if context.language_detection_confidence < 0.5 and context.confidence_score > 0.7:
                evidence.append("Language uncertainty with high transcription confidence")
                severity_factors.append(0.3)
            
            severity = np.mean(severity_factors) if severity_factors else 0.0
            is_hallucination = severity > 0.4
            
            return HallucinationDetection(
                is_hallucination=is_hallucination,
                confidence=severity,
                hallucination_type=HallucinationType.PHANTOM_SPEECH if is_hallucination else None,
                severity=severity,
                evidence=evidence,
                prevention_action='filter' if is_hallucination else 'allow'
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Audio-text correlation validation failed: {e}")
            return HallucinationDetection(
                is_hallucination=False, confidence=0.0, hallucination_type=None,
                severity=0.0, evidence=['correlation_validation_error']
            )
    
    def _validate_contextual_consistency(self, text: str, session_id: str) -> HallucinationDetection:
        """📚 Validate contextual consistency within session."""
        try:
            evidence = []
            severity_factors = []
            
            if session_id not in self.session_history:
                return HallucinationDetection(
                    is_hallucination=False, confidence=0.0, hallucination_type=None,
                    severity=0.0, evidence=['no_context_available']
                )
            
            history = list(self.session_history[session_id])
            
            if len(history) < 2:
                return HallucinationDetection(
                    is_hallucination=False, confidence=0.0, hallucination_type=None,
                    severity=0.0, evidence=['insufficient_context']
                )
            
            # Check for sudden confidence jumps
            recent_confidences = [h['confidence'] for h in history[-3:]]
            if len(recent_confidences) >= 2:
                confidence_variance = np.var(recent_confidences)
                if confidence_variance > 0.3:
                    evidence.append(f"High confidence variance: {confidence_variance:.2f}")
                    severity_factors.append(min(0.4, confidence_variance))
            
            # Check for text similarity patterns
            recent_texts = [h['text'].lower() for h in history[-3:]]
            text_lower = text.lower()
            
            for prev_text in recent_texts:
                similarity = self._calculate_text_similarity(text_lower, prev_text)
                if similarity > 0.8 and len(text.split()) > 3:
                    evidence.append(f"Very similar to previous text: {similarity:.2f}")
                    severity_factors.append(0.5)
            
            # Check for hallucination clusters
            recent_hallucinations = [h for h in history[-5:] if h.get('is_hallucination', False)]
            if len(recent_hallucinations) >= 2:
                evidence.append("Multiple recent hallucinations detected")
                severity_factors.append(0.6)
            
            severity = np.max(severity_factors) if severity_factors else 0.0
            is_hallucination = severity > 0.3
            
            return HallucinationDetection(
                is_hallucination=is_hallucination,
                confidence=severity,
                hallucination_type=HallucinationType.REPETITIVE_PHRASES if is_hallucination else None,
                severity=severity,
                evidence=evidence,
                prevention_action='review' if is_hallucination else 'allow'
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Contextual consistency validation failed: {e}")
            return HallucinationDetection(
                is_hallucination=False, confidence=0.0, hallucination_type=None,
                severity=0.0, evidence=['context_validation_error']
            )
    
    def _analyze_confidence_patterns(self, text: str, context: ValidationContext) -> HallucinationDetection:
        """📊 Analyze confidence patterns for anomalies."""
        try:
            evidence = []
            severity_factors = []
            
            # Overconfident short text
            if len(text.split()) <= 2 and context.confidence_score > 0.9:
                evidence.append("Overconfident very short text")
                severity_factors.append(0.4)
            
            # Confidence-quality mismatch
            expected_confidence = self._estimate_expected_confidence(context)
            confidence_deviation = abs(context.confidence_score - expected_confidence)
            
            if confidence_deviation > 0.3:
                evidence.append(f"Confidence deviation from expected: {confidence_deviation:.2f}")
                severity_factors.append(confidence_deviation)
            
            # Perfect confidence (suspicious)
            if context.confidence_score >= 0.99:
                evidence.append("Suspiciously perfect confidence")
                severity_factors.append(0.2)
            
            severity = np.mean(severity_factors) if severity_factors else 0.0
            is_hallucination = severity > 0.3
            
            return HallucinationDetection(
                is_hallucination=is_hallucination,
                confidence=severity,
                hallucination_type=HallucinationType.OVERCONFIDENT_NOISE if is_hallucination else None,
                severity=severity,
                evidence=evidence,
                prevention_action='review' if is_hallucination else 'allow'
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Confidence pattern analysis failed: {e}")
            return HallucinationDetection(
                is_hallucination=False, confidence=0.0, hallucination_type=None,
                severity=0.0, evidence=['confidence_analysis_error']
            )
    
    def _combine_validation_results(self, validations: List[HallucinationDetection], 
                                  text: str, context: ValidationContext) -> HallucinationDetection:
        """🔗 Combine multiple validation results into final decision."""
        try:
            # Count hallucination detections
            hallucination_votes = sum(1 for v in validations if v.is_hallucination)
            total_votes = len(validations)
            
            # Calculate weighted confidence
            confidences = [v.confidence for v in validations if v.confidence > 0]
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            # Calculate weighted severity
            severities = [v.severity for v in validations if v.severity > 0]
            max_severity = np.max(severities) if severities else 0.0
            
            # Collect all evidence
            all_evidence = []
            for v in validations:
                all_evidence.extend(v.evidence)
            
            # Determine primary hallucination type
            hallucination_types = [v.hallucination_type for v in validations if v.hallucination_type]
            primary_type = hallucination_types[0] if hallucination_types else None
            
            # Decision logic
            vote_ratio = hallucination_votes / total_votes
            
            # Strict decision making
            is_hallucination = (
                vote_ratio >= 0.4 or  # 40% of validators agree
                max_severity > 0.6 or  # High severity detected
                (avg_confidence > 0.7 and vote_ratio >= 0.3)  # High confidence with some votes
            )
            
            # Apply strictness adjustment
            strictness_adjustment = self.strictness_level * 0.2
            if avg_confidence > (0.5 - strictness_adjustment):
                is_hallucination = True
            
            # Determine prevention action
            if is_hallucination:
                if max_severity > 0.8:
                    prevention_action = 'block'
                elif max_severity > 0.5:
                    prevention_action = 'filter'
                else:
                    prevention_action = 'review'
            else:
                prevention_action = 'allow'
            
            # Generate corrected text if needed
            corrected_text = None
            if is_hallucination and max_severity > 0.6:
                corrected_text = self._generate_corrected_text(text, primary_type)
            
            return HallucinationDetection(
                is_hallucination=is_hallucination,
                confidence=avg_confidence,
                hallucination_type=primary_type,
                severity=max_severity,
                evidence=all_evidence,
                corrected_text=corrected_text,
                prevention_action=prevention_action
            )
            
        except Exception as e:
            logger.error(f"❌ Validation result combination failed: {e}")
            return HallucinationDetection(
                is_hallucination=True,  # Fail safe
                confidence=1.0,
                hallucination_type=None,
                severity=1.0,
                evidence=['combination_error'],
                prevention_action='block'
            )
    
    def _analyze_character_repetition(self, text: str) -> float:
        """📝 Analyze character repetition ratio."""
        try:
            if len(text) < 3:
                return 0.0
            
            char_counts = Counter(text.lower())
            most_common_char, max_count = char_counts.most_common(1)[0]
            
            # Ignore spaces and common punctuation
            if most_common_char in ' .,!?':
                if len(char_counts) > 1:
                    most_common_char, max_count = char_counts.most_common(2)[1]
                else:
                    return 0.0
            
            repetition_ratio = max_count / len(text)
            return repetition_ratio
            
        except Exception:
            return 0.0
    
    def _analyze_word_repetition(self, text: str) -> float:
        """🔤 Analyze word repetition ratio."""
        try:
            words = text.lower().split()
            if len(words) < 2:
                return 0.0
            
            word_counts = Counter(words)
            most_common_word, max_count = word_counts.most_common(1)[0]
            
            repetition_ratio = max_count / len(words)
            return repetition_ratio
            
        except Exception:
            return 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """📊 Calculate text similarity."""
        try:
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            similarity = len(intersection) / len(union)
            return similarity
            
        except Exception:
            return 0.0
    
    def _estimate_expected_confidence(self, context: ValidationContext) -> float:
        """🎯 Estimate expected confidence based on context."""
        try:
            # Base confidence from audio quality
            base_confidence = context.audio_quality_score * 0.8
            
            # Adjust for noise level
            noise_penalty = context.environmental_noise_level * 0.3
            base_confidence -= noise_penalty
            
            # Adjust for speaker detection
            speaker_bonus = context.speaker_detection_confidence * 0.2
            base_confidence += speaker_bonus
            
            # Clamp to valid range
            expected_confidence = max(0.0, min(1.0, base_confidence))
            
            return expected_confidence
            
        except Exception:
            return 0.5
    
    def _generate_corrected_text(self, text: str, hallucination_type: Optional[HallucinationType]) -> str:
        """🔧 Generate corrected text by removing hallucination artifacts."""
        try:
            if not hallucination_type:
                return text
            
            corrected = text
            
            if hallucination_type == HallucinationType.REPETITIVE_PHRASES:
                # Remove excessive repetitions
                words = corrected.split()
                deduplicated_words = []
                
                for word in words:
                    if not deduplicated_words or word != deduplicated_words[-1]:
                        deduplicated_words.append(word)
                
                corrected = ' '.join(deduplicated_words)
            
            elif hallucination_type == HallucinationType.AUDIO_ARTIFACTS:
                # Remove audio artifact descriptions
                for pattern in self.audio_artifact_patterns:
                    corrected = re.sub(pattern, '', corrected, flags=re.IGNORECASE)
            
            elif hallucination_type == HallucinationType.MUSICAL_INTERPRETATION:
                # Remove musical patterns
                for pattern in self.musical_patterns:
                    corrected = re.sub(pattern, '', corrected, flags=re.IGNORECASE)
            
            # Clean up whitespace
            corrected = re.sub(r'\s+', ' ', corrected).strip()
            
            return corrected if corrected else ""
            
        except Exception:
            return text
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """📊 Get hallucination detection statistics."""
        try:
            total_validations = self.detection_stats['total_validations']
            
            if total_validations == 0:
                return {'status': 'no_data'}
            
            detection_rate = self.detection_stats['hallucinations_detected'] / total_validations
            
            return {
                'total_validations': total_validations,
                'hallucinations_detected': self.detection_stats['hallucinations_detected'],
                'detection_rate': detection_rate,
                'hallucinations_by_type': dict(self.detection_stats['hallucinations_by_type']),
                'strictness_level': self.strictness_level,
                'active_sessions': len(self.session_history),
                'prevention_effectiveness': {
                    'confidence_threshold': self.min_confidence_threshold,
                    'repetition_threshold': self.max_repetition_ratio,
                    'max_words_per_second': self.max_words_per_second
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Statistics calculation failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def update_strictness_level(self, new_level: float):
        """🎛️ Update strictness level and recalculate thresholds."""
        try:
            self.strictness_level = max(0.0, min(1.0, new_level))
            
            # Recalculate thresholds
            self.min_confidence_threshold = 0.6 + (self.strictness_level * 0.2)
            self.max_repetition_ratio = 0.3 - (self.strictness_level * 0.1)
            self.max_words_per_second = 8.0 - (self.strictness_level * 2.0)
            
            logger.info(f"🎛️ Strictness level updated to {self.strictness_level}")
            
        except Exception as e:
            logger.error(f"❌ Strictness level update failed: {e}")
    
    def reset_session_history(self, session_id: Optional[str] = None):
        """🔄 Reset session history."""
        try:
            if session_id:
                if session_id in self.session_history:
                    del self.session_history[session_id]
                    logger.info(f"🔄 Session history reset for {session_id}")
            else:
                self.session_history.clear()
                logger.info("🔄 All session history reset")
                
        except Exception as e:
            logger.error(f"❌ Session history reset failed: {e}")