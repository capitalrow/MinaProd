#!/usr/bin/env python3
# 🎯 Production Feature: Advanced Confidence Scoring with Acoustic Model Improvements
"""
Enterprise-grade confidence scoring system with acoustic model improvements and quality metrics.
Implements sophisticated confidence calibration, multi-factor assessment, and quality-driven scoring.

Addresses: "Advanced confidence scoring system with acoustic model improvements" for Fix Pack 4.

Key Features:
- Multi-factor confidence scoring (acoustic, linguistic, contextual)
- Quality-aware confidence calibration
- Adaptive confidence thresholds based on audio conditions
- Confidence-driven transcription improvements
- Real-time confidence monitoring and adjustment
- Statistical confidence modeling with uncertainty quantification
- Integration with audio quality metrics and enhancement pipeline
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from collections import deque, Counter
from enum import Enum
import time
import math
from scipy import stats
from scipy.special import softmax

logger = logging.getLogger(__name__)

class ConfidenceLevel(Enum):
    """Confidence level classification."""
    VERY_HIGH = "very_high"    # > 95%
    HIGH = "high"              # 85-95%
    MEDIUM = "medium"          # 70-85%
    LOW = "low"               # 50-70%
    VERY_LOW = "very_low"     # < 50%

class ConfidenceFactorType(Enum):
    """Types of confidence factors."""
    ACOUSTIC_MODEL = "acoustic_model"      # Raw model confidence
    AUDIO_QUALITY = "audio_quality"       # Quality-based adjustment
    LINGUISTIC = "linguistic"             # Language model confidence
    CONTEXTUAL = "contextual"             # Context consistency
    TEMPORAL = "temporal"                 # Temporal stability
    SPEAKER = "speaker"                   # Speaker identification confidence
    ENVIRONMENTAL = "environmental"       # Environmental factors

@dataclass
class ConfidenceFactor:
    """Individual confidence factor with metadata."""
    factor_type: ConfidenceFactorType
    raw_score: float              # Original score (0-1)
    weighted_score: float         # Weighted contribution
    weight: float                 # Factor weight
    reliability: float = 1.0      # Factor reliability (0-1)
    uncertainty: float = 0.0      # Uncertainty estimate (0-1)
    evidence_strength: float = 1.0  # Evidence strength (0-1)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'factor_type': self.factor_type.value,
            'raw_score': self.raw_score,
            'weighted_score': self.weighted_score,
            'weight': self.weight,
            'reliability': self.reliability,
            'uncertainty': self.uncertainty,
            'evidence_strength': self.evidence_strength
        }

@dataclass
class ConfidenceAssessment:
    """Comprehensive confidence assessment."""
    # Overall confidence
    overall_confidence: float = 0.0        # Final confidence score (0-1)
    confidence_level: ConfidenceLevel = ConfidenceLevel.VERY_LOW
    
    # Component confidences
    factors: List[ConfidenceFactor] = field(default_factory=list)
    
    # Quality indicators
    audio_quality_score: float = 0.0       # Audio quality impact
    transcription_quality: float = 0.0     # Estimated transcription quality
    
    # Statistical measures
    confidence_interval: Tuple[float, float] = (0.0, 0.0)  # 95% confidence interval
    uncertainty_estimate: float = 0.0       # Overall uncertainty
    statistical_significance: float = 0.0   # Statistical significance
    
    # Contextual information
    word_count: int = 0                     # Number of words assessed
    duration_seconds: float = 0.0          # Audio duration
    speaker_consistency: float = 0.0       # Speaker identification consistency
    environmental_stability: float = 0.0   # Environmental consistency
    
    # Recommendations
    confidence_sufficient: bool = True      # Is confidence sufficient for use?
    improvement_suggestions: List[str] = field(default_factory=list)
    quality_warnings: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: float = field(default_factory=time.time)
    model_version: str = "v1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'overall_confidence': self.overall_confidence,
            'confidence_level': self.confidence_level.value,
            'factors': [f.to_dict() for f in self.factors],
            'audio_quality_score': self.audio_quality_score,
            'transcription_quality': self.transcription_quality,
            'confidence_interval': self.confidence_interval,
            'uncertainty_estimate': self.uncertainty_estimate,
            'statistical_significance': self.statistical_significance,
            'word_count': self.word_count,
            'duration_seconds': self.duration_seconds,
            'speaker_consistency': self.speaker_consistency,
            'environmental_stability': self.environmental_stability,
            'confidence_sufficient': self.confidence_sufficient,
            'improvement_suggestions': self.improvement_suggestions,
            'quality_warnings': self.quality_warnings,
            'timestamp': self.timestamp,
            'model_version': self.model_version
        }

@dataclass
class ConfidenceConfig:
    """Configuration for confidence scoring system."""
    # Factor weights
    acoustic_weight: float = 0.3           # Acoustic model weight
    audio_quality_weight: float = 0.25     # Audio quality weight
    linguistic_weight: float = 0.2         # Linguistic model weight
    contextual_weight: float = 0.15        # Contextual consistency weight
    temporal_weight: float = 0.1           # Temporal stability weight
    
    # Confidence thresholds
    very_high_threshold: float = 0.95
    high_threshold: float = 0.85
    medium_threshold: float = 0.70
    low_threshold: float = 0.50
    
    # Quality impact factors
    quality_impact_factor: float = 0.4     # How much quality affects confidence
    snr_impact_factor: float = 0.3         # SNR impact on confidence
    stability_impact_factor: float = 0.2   # Stability impact
    
    # Statistical parameters
    confidence_interval_alpha: float = 0.05  # For 95% confidence interval
    min_samples_for_stats: int = 10        # Minimum samples for statistics
    uncertainty_smoothing: float = 0.3     # Uncertainty smoothing factor
    
    # Adaptive parameters
    adaptive_thresholds: bool = True       # Enable adaptive thresholds
    environment_adaptation: bool = True    # Adapt to environment
    speaker_adaptation: bool = True        # Adapt to speaker characteristics
    
    # Enhancement integration
    enhance_low_confidence: bool = True    # Enhance low-confidence segments
    confidence_feedback: bool = True       # Use confidence for enhancement feedback

class AdvancedConfidenceScorer:
    """
    🎯 Enterprise-grade advanced confidence scoring system.
    
    Provides sophisticated confidence assessment with acoustic model improvements,
    multi-factor analysis, and quality-driven confidence calibration.
    """
    
    def __init__(self, config: Optional[ConfidenceConfig] = None):
        self.config = config or ConfidenceConfig()
        
        # Confidence history and statistics
        self.confidence_history = deque(maxlen=1000)
        self.factor_histories = {
            factor_type: deque(maxlen=500) 
            for factor_type in ConfidenceFactorType
        }
        
        # Adaptive thresholds
        self.adaptive_thresholds = {
            'very_high': self.config.very_high_threshold,
            'high': self.config.high_threshold,
            'medium': self.config.medium_threshold,
            'low': self.config.low_threshold
        }
        
        # Statistical models
        self.confidence_distribution_params = {}  # For statistical modeling
        self.calibration_curve = {}               # For confidence calibration
        
        # Environment and speaker adaptation
        self.environment_profiles = {}            # Environment-specific parameters
        self.speaker_profiles = {}                # Speaker-specific parameters
        
        # Performance tracking
        self.scoring_stats = {
            'total_assessments': 0,
            'low_confidence_count': 0,
            'high_confidence_count': 0,
            'accuracy_estimates': deque(maxlen=100),
            'calibration_errors': deque(maxlen=100),
            'processing_times': deque(maxlen=100)
        }
        
        logger.info("🎯 Advanced Confidence Scorer initialized with multi-factor analysis")
    
    def assess_confidence(self, 
                         text: str,
                         audio_data: Optional[np.ndarray] = None,
                         acoustic_confidence: Optional[float] = None,
                         linguistic_confidence: Optional[float] = None,
                         audio_quality_metrics: Optional[Dict[str, Any]] = None,
                         speaker_info: Optional[Dict[str, Any]] = None,
                         environmental_context: Optional[Dict[str, Any]] = None,
                         duration_seconds: Optional[float] = None) -> ConfidenceAssessment:
        """
        🎯 Comprehensive confidence assessment with multi-factor analysis.
        
        Args:
            text: Transcribed text to assess
            audio_data: Raw audio data (optional)
            acoustic_confidence: Raw acoustic model confidence
            linguistic_confidence: Language model confidence
            audio_quality_metrics: Audio quality assessment results
            speaker_info: Speaker identification information
            environmental_context: Environmental context information
            duration_seconds: Audio duration
            
        Returns:
            Comprehensive confidence assessment
        """
        start_time = time.time()
        
        try:
            assessment = ConfidenceAssessment()
            assessment.word_count = len(text.split()) if text else 0
            assessment.duration_seconds = duration_seconds or 0.0
            
            # === FACTOR ANALYSIS ===
            factors = []
            
            # Acoustic model confidence
            if acoustic_confidence is not None:
                factor = self._analyze_acoustic_confidence(acoustic_confidence, audio_data)
                factors.append(factor)
            
            # Audio quality confidence
            if audio_quality_metrics:
                factor = self._analyze_audio_quality_confidence(audio_quality_metrics)
                factors.append(factor)
                assessment.audio_quality_score = audio_quality_metrics.get('overall_score', 0.0)
            
            # Linguistic confidence
            if linguistic_confidence is not None:
                factor = self._analyze_linguistic_confidence(linguistic_confidence, text)
                factors.append(factor)
            
            # Contextual confidence
            if text:
                factor = self._analyze_contextual_confidence(text)
                factors.append(factor)
            
            # Temporal stability
            if len(self.confidence_history) > 5:
                factor = self._analyze_temporal_confidence()
                factors.append(factor)
            
            # Speaker consistency
            if speaker_info:
                factor = self._analyze_speaker_confidence(speaker_info)
                factors.append(factor)
                assessment.speaker_consistency = speaker_info.get('confidence', 0.0)
            
            # Environmental factors
            if environmental_context:
                factor = self._analyze_environmental_confidence(environmental_context)
                factors.append(factor)
                assessment.environmental_stability = environmental_context.get('stability', 0.0)
            
            assessment.factors = factors
            
            # === CONFIDENCE INTEGRATION ===
            # Calculate weighted confidence score
            overall_confidence = self._integrate_confidence_factors(factors)
            
            # Apply quality-based adjustments
            if audio_quality_metrics:
                overall_confidence = self._apply_quality_adjustments(
                    overall_confidence, audio_quality_metrics
                )
            
            # Apply adaptive calibration
            if self.config.adaptive_thresholds:
                overall_confidence = self._apply_adaptive_calibration(
                    overall_confidence, environmental_context, speaker_info
                )
            
            assessment.overall_confidence = overall_confidence
            assessment.confidence_level = self._determine_confidence_level(overall_confidence)
            
            # === STATISTICAL ANALYSIS ===
            # Calculate confidence interval and uncertainty
            if len(self.confidence_history) >= self.config.min_samples_for_stats:
                interval, uncertainty, significance = self._calculate_statistical_measures(
                    overall_confidence, factors
                )
                assessment.confidence_interval = interval
                assessment.uncertainty_estimate = uncertainty
                assessment.statistical_significance = significance
            
            # === QUALITY ASSESSMENT ===
            assessment.transcription_quality = self._estimate_transcription_quality(
                overall_confidence, factors, audio_quality_metrics
            )
            
            # === RECOMMENDATIONS ===
            assessment.confidence_sufficient = overall_confidence >= self.adaptive_thresholds['medium']
            assessment.improvement_suggestions = self._generate_improvement_suggestions(
                factors, audio_quality_metrics
            )
            assessment.quality_warnings = self._generate_quality_warnings(
                factors, audio_quality_metrics
            )
            
            # === UPDATES ===
            # Update history and statistics
            self._update_confidence_history(assessment)
            self._update_factor_histories(factors)
            self._update_adaptive_parameters(assessment, environmental_context, speaker_info)
            
            # Performance tracking
            processing_time = (time.time() - start_time) * 1000
            self.scoring_stats['processing_times'].append(processing_time)
            self.scoring_stats['total_assessments'] += 1
            
            if overall_confidence < self.adaptive_thresholds['medium']:
                self.scoring_stats['low_confidence_count'] += 1
            elif overall_confidence >= self.adaptive_thresholds['high']:
                self.scoring_stats['high_confidence_count'] += 1
            
            return assessment
            
        except Exception as e:
            logger.error(f"❌ Error in confidence assessment: {e}")
            return ConfidenceAssessment()
    
    def _analyze_acoustic_confidence(self, acoustic_confidence: float, 
                                   audio_data: Optional[np.ndarray] = None) -> ConfidenceFactor:
        """Analyze acoustic model confidence with enhancements."""
        # Raw acoustic confidence from model
        raw_score = max(0.0, min(1.0, acoustic_confidence))
        
        # Calculate reliability based on audio characteristics
        reliability = 1.0
        uncertainty = 0.0
        
        if audio_data is not None and len(audio_data) > 0:
            # Audio-based reliability adjustments
            
            # Signal quality impact
            snr_estimate = self._estimate_snr(audio_data)
            if snr_estimate < 10:  # Poor SNR
                reliability *= 0.7
                uncertainty += 0.2
            elif snr_estimate < 5:  # Very poor SNR
                reliability *= 0.5
                uncertainty += 0.4
            
            # Clipping detection
            clipping_ratio = np.sum(np.abs(audio_data) > 0.95) / len(audio_data)
            if clipping_ratio > 0.01:  # More than 1% clipping
                reliability *= 0.8
                uncertainty += 0.15
        
        # Evidence strength based on confidence value
        # Very high or very low confidences are stronger evidence
        evidence_strength = 1.0 - 2 * abs(raw_score - 0.5)  # V-shaped curve
        evidence_strength = max(0.3, evidence_strength)  # Minimum evidence
        
        weighted_score = raw_score * self.config.acoustic_weight * reliability
        
        return ConfidenceFactor(
            factor_type=ConfidenceFactorType.ACOUSTIC_MODEL,
            raw_score=raw_score,
            weighted_score=weighted_score,
            weight=self.config.acoustic_weight,
            reliability=reliability,
            uncertainty=uncertainty,
            evidence_strength=evidence_strength
        )
    
    def _analyze_audio_quality_confidence(self, audio_quality_metrics: Dict[str, Any]) -> ConfidenceFactor:
        """Analyze audio quality impact on confidence."""
        # Extract key quality metrics
        overall_quality = audio_quality_metrics.get('overall_score', 0.0)
        snr_db = audio_quality_metrics.get('snr_db', 0.0)
        clipping_percent = audio_quality_metrics.get('clipping_percent', 0.0)
        speech_intelligibility = audio_quality_metrics.get('speech_intelligibility', 0.0)
        
        # Quality-based confidence calculation
        quality_confidence = overall_quality
        
        # SNR impact
        if snr_db > 20:
            snr_boost = 0.1
        elif snr_db > 10:
            snr_boost = 0.05
        elif snr_db < 5:
            snr_boost = -0.2
        else:
            snr_boost = 0.0
        
        quality_confidence += snr_boost
        
        # Clipping penalty
        clipping_penalty = min(0.3, clipping_percent / 10.0)  # 10% clipping = 0.3 penalty
        quality_confidence -= clipping_penalty
        
        # Speech intelligibility boost
        if speech_intelligibility > 0.8:
            quality_confidence += 0.1
        elif speech_intelligibility < 0.4:
            quality_confidence -= 0.15
        
        raw_score = max(0.0, min(1.0, quality_confidence))
        
        # Reliability based on quality consistency
        quality_level = audio_quality_metrics.get('quality_level', 'poor')
        reliability_map = {
            'excellent': 1.0,
            'good': 0.9,
            'fair': 0.7,
            'poor': 0.5,
            'unacceptable': 0.3
        }
        reliability = reliability_map.get(quality_level, 0.5)
        
        # Uncertainty based on quality variability
        uncertainty = 1.0 - overall_quality  # Lower quality = higher uncertainty
        
        weighted_score = raw_score * self.config.audio_quality_weight * reliability
        
        return ConfidenceFactor(
            factor_type=ConfidenceFactorType.AUDIO_QUALITY,
            raw_score=raw_score,
            weighted_score=weighted_score,
            weight=self.config.audio_quality_weight,
            reliability=reliability,
            uncertainty=uncertainty,
            evidence_strength=overall_quality
        )
    
    def _analyze_linguistic_confidence(self, linguistic_confidence: float, text: str) -> ConfidenceFactor:
        """Analyze linguistic model confidence with text analysis."""
        raw_score = max(0.0, min(1.0, linguistic_confidence))
        
        # Text-based reliability adjustments
        reliability = 1.0
        uncertainty = 0.0
        
        if text:
            words = text.split()
            
            # Length-based reliability (very short or very long texts are less reliable)
            if len(words) < 3:
                reliability *= 0.7
                uncertainty += 0.2
            elif len(words) > 50:
                reliability *= 0.9
                uncertainty += 0.1
            
            # Check for unusual patterns
            # Repetitive text (might indicate recognition errors)
            unique_words = len(set(word.lower() for word in words))
            repetition_ratio = unique_words / len(words) if words else 0
            
            if repetition_ratio < 0.3:  # High repetition
                reliability *= 0.6
                uncertainty += 0.3
            
            # Check for common speech recognition artifacts
            artifacts = ['uh', 'um', 'er', 'ah', 'hmm']
            artifact_count = sum(1 for word in words if word.lower() in artifacts)
            if artifact_count / len(words) > 0.2:  # More than 20% artifacts
                reliability *= 0.8
                uncertainty += 0.15
        
        evidence_strength = linguistic_confidence * reliability
        weighted_score = raw_score * self.config.linguistic_weight * reliability
        
        return ConfidenceFactor(
            factor_type=ConfidenceFactorType.LINGUISTIC,
            raw_score=raw_score,
            weighted_score=weighted_score,
            weight=self.config.linguistic_weight,
            reliability=reliability,
            uncertainty=uncertainty,
            evidence_strength=evidence_strength
        )
    
    def _analyze_contextual_confidence(self, text: str) -> ConfidenceFactor:
        """Analyze contextual consistency and coherence."""
        if not text:
            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.CONTEXTUAL,
                raw_score=0.0,
                weighted_score=0.0,
                weight=self.config.contextual_weight
            )
        
        words = text.split()
        
        # Basic coherence measures
        coherence_score = 0.5  # Base score
        
        # Sentence structure (presence of punctuation and capitalization)
        has_punctuation = any(char in text for char in '.!?')
        has_capitalization = any(char.isupper() for char in text)
        
        if has_punctuation and has_capitalization:
            coherence_score += 0.2
        elif has_punctuation or has_capitalization:
            coherence_score += 0.1
        
        # Word frequency analysis (common words should appear)
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        common_word_count = sum(1 for word in words if word.lower() in common_words)
        common_ratio = common_word_count / len(words) if words else 0
        
        # Expect 10-30% common words in natural speech
        if 0.1 <= common_ratio <= 0.3:
            coherence_score += 0.2
        elif 0.05 <= common_ratio <= 0.4:
            coherence_score += 0.1
        else:
            coherence_score -= 0.1
        
        # Check for logical flow (simplified - look for transition words)
        transition_words = {'so', 'but', 'however', 'therefore', 'because', 'since', 'although'}
        has_transitions = any(word.lower() in transition_words for word in words)
        if has_transitions:
            coherence_score += 0.1
        
        raw_score = max(0.0, min(1.0, coherence_score))
        
        # Reliability based on text length and structure
        reliability = min(1.0, len(words) / 10.0)  # More reliable with more text
        uncertainty = 0.3 - (reliability * 0.2)    # Less uncertainty with more reliable text
        
        weighted_score = raw_score * self.config.contextual_weight * reliability
        
        return ConfidenceFactor(
            factor_type=ConfidenceFactorType.CONTEXTUAL,
            raw_score=raw_score,
            weighted_score=weighted_score,
            weight=self.config.contextual_weight,
            reliability=reliability,
            uncertainty=uncertainty,
            evidence_strength=reliability
        )
    
    def _analyze_temporal_confidence(self) -> ConfidenceFactor:
        """Analyze temporal stability of confidence scores."""
        if len(self.confidence_history) < 5:
            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.TEMPORAL,
                raw_score=0.5,
                weighted_score=0.5 * self.config.temporal_weight,
                weight=self.config.temporal_weight
            )
        
        # Get recent confidence scores
        recent_confidences = [assessment.overall_confidence for assessment in list(self.confidence_history)[-10:]]
        
        # Calculate temporal stability
        confidence_variance = np.var(recent_confidences)
        mean_confidence = np.mean(recent_confidences)
        
        # Stability score (low variance = high stability)
        stability_score = max(0.0, 1.0 - confidence_variance * 4)  # Scale variance
        
        # Trend analysis
        if len(recent_confidences) >= 5:
            # Simple trend detection
            first_half = np.mean(recent_confidences[:len(recent_confidences)//2])
            second_half = np.mean(recent_confidences[len(recent_confidences)//2:])
            trend_direction = second_half - first_half
            
            # Positive trend boosts confidence, negative trend reduces it
            trend_adjustment = max(-0.2, min(0.2, trend_direction))
            stability_score += trend_adjustment
        
        raw_score = max(0.0, min(1.0, stability_score))
        
        # Reliability based on history length
        reliability = min(1.0, len(self.confidence_history) / 20.0)
        uncertainty = 0.4 - (reliability * 0.3)
        
        weighted_score = raw_score * self.config.temporal_weight * reliability
        
        return ConfidenceFactor(
            factor_type=ConfidenceFactorType.TEMPORAL,
            raw_score=raw_score,
            weighted_score=weighted_score,
            weight=self.config.temporal_weight,
            reliability=reliability,
            uncertainty=uncertainty,
            evidence_strength=reliability
        )
    
    def _analyze_speaker_confidence(self, speaker_info: Dict[str, Any]) -> ConfidenceFactor:
        """Analyze speaker identification confidence."""
        speaker_confidence = speaker_info.get('confidence', 0.0)
        speaker_consistency = speaker_info.get('consistency', 0.0)
        voice_quality = speaker_info.get('voice_quality_score', 0.0)
        
        # Combine speaker-related factors
        speaker_score = (speaker_confidence * 0.5 + 
                        speaker_consistency * 0.3 + 
                        voice_quality * 0.2)
        
        raw_score = max(0.0, min(1.0, speaker_score))
        
        # Reliability based on voice quality
        reliability = max(0.3, voice_quality)
        uncertainty = 1.0 - speaker_confidence
        
        weighted_score = raw_score * 0.1 * reliability  # Speaker has lower weight
        
        return ConfidenceFactor(
            factor_type=ConfidenceFactorType.SPEAKER,
            raw_score=raw_score,
            weighted_score=weighted_score,
            weight=0.1,
            reliability=reliability,
            uncertainty=uncertainty,
            evidence_strength=speaker_confidence
        )
    
    def _analyze_environmental_confidence(self, environmental_context: Dict[str, Any]) -> ConfidenceFactor:
        """Analyze environmental factors impact on confidence."""
        environment_type = environmental_context.get('environment', 'unknown')
        noise_level = environmental_context.get('noise_level', 0.0)
        stability = environmental_context.get('stability', 0.0)
        snr = environmental_context.get('estimated_snr', 0.0)
        
        # Environment-based confidence
        environment_scores = {
            'quiet': 1.0,
            'office': 0.8,
            'cafe': 0.6,
            'street': 0.4,
            'construction': 0.2,
            'unknown': 0.5
        }
        
        env_score = environment_scores.get(environment_type, 0.5)
        
        # Adjust for noise level and stability
        if noise_level < 0.01:  # Very quiet
            env_score += 0.1
        elif noise_level > 0.1:  # Very noisy
            env_score -= 0.3
        
        env_score += stability * 0.2  # Stability bonus
        
        if snr > 15:
            env_score += 0.1
        elif snr < 5:
            env_score -= 0.2
        
        raw_score = max(0.0, min(1.0, env_score))
        
        # Reliability based on consistency of environmental measures
        reliability = stability
        uncertainty = noise_level  # Higher noise = higher uncertainty
        
        weighted_score = raw_score * 0.1 * reliability  # Environmental has lower weight
        
        return ConfidenceFactor(
            factor_type=ConfidenceFactorType.ENVIRONMENTAL,
            raw_score=raw_score,
            weighted_score=weighted_score,
            weight=0.1,
            reliability=reliability,
            uncertainty=uncertainty,
            evidence_strength=stability
        )
    
    def _integrate_confidence_factors(self, factors: List[ConfidenceFactor]) -> float:
        """Integrate multiple confidence factors into overall score."""
        if not factors:
            return 0.0
        
        # Method 1: Weighted average (primary)
        total_weighted_score = sum(factor.weighted_score for factor in factors)
        total_weight = sum(factor.weight * factor.reliability for factor in factors)
        
        if total_weight > 0:
            weighted_average = total_weighted_score / total_weight
        else:
            weighted_average = 0.0
        
        # Method 2: Evidence combination using Dempster-Shafer theory (simplified)
        evidence_scores = []
        evidence_weights = []
        
        for factor in factors:
            if factor.evidence_strength > 0.1:  # Only use factors with sufficient evidence
                evidence_scores.append(factor.raw_score)
                evidence_weights.append(factor.evidence_strength * factor.reliability)
        
        if evidence_scores:
            evidence_combination = np.average(evidence_scores, weights=evidence_weights)
        else:
            evidence_combination = 0.0
        
        # Method 3: Uncertainty-weighted combination
        uncertainty_weights = []
        uncertainty_scores = []
        
        for factor in factors:
            uncertainty_weight = 1.0 / (factor.uncertainty + 0.1)  # Inverse uncertainty weighting
            uncertainty_weights.append(uncertainty_weight * factor.reliability)
            uncertainty_scores.append(factor.raw_score)
        
        if uncertainty_scores:
            uncertainty_combination = np.average(uncertainty_scores, weights=uncertainty_weights)
        else:
            uncertainty_combination = 0.0
        
        # Combine methods
        final_confidence = (weighted_average * 0.5 + 
                          evidence_combination * 0.3 + 
                          uncertainty_combination * 0.2)
        
        return max(0.0, min(1.0, final_confidence))
    
    def _apply_quality_adjustments(self, confidence: float, 
                                 audio_quality_metrics: Dict[str, Any]) -> float:
        """Apply audio quality-based adjustments to confidence."""
        quality_impact = self.config.quality_impact_factor
        
        # Overall quality adjustment
        quality_score = audio_quality_metrics.get('overall_score', 0.5)
        quality_adjustment = (quality_score - 0.5) * quality_impact
        
        # SNR adjustment
        snr_db = audio_quality_metrics.get('snr_db', 0.0)
        snr_impact = self.config.snr_impact_factor
        
        if snr_db > 20:
            snr_adjustment = 0.1 * snr_impact
        elif snr_db > 15:
            snr_adjustment = 0.05 * snr_impact
        elif snr_db < 10:
            snr_adjustment = -0.1 * snr_impact
        elif snr_db < 5:
            snr_adjustment = -0.2 * snr_impact
        else:
            snr_adjustment = 0.0
        
        # Speech intelligibility adjustment
        speech_intelligibility = audio_quality_metrics.get('speech_intelligibility', 0.5)
        intelligibility_adjustment = (speech_intelligibility - 0.5) * 0.2
        
        # Apply adjustments
        adjusted_confidence = confidence + quality_adjustment + snr_adjustment + intelligibility_adjustment
        
        return max(0.0, min(1.0, adjusted_confidence))
    
    def _apply_adaptive_calibration(self, confidence: float,
                                  environmental_context: Optional[Dict[str, Any]],
                                  speaker_info: Optional[Dict[str, Any]]) -> float:
        """Apply adaptive calibration based on context."""
        if not self.config.adaptive_thresholds:
            return confidence
        
        calibrated_confidence = confidence
        
        # Environment-based calibration
        if environmental_context and self.config.environment_adaptation:
            env_type = environmental_context.get('environment', 'unknown')
            
            # Adjust confidence based on environment reliability
            env_calibration = {
                'quiet': 1.05,      # Boost confidence in quiet environments
                'office': 1.02,     # Slight boost in office
                'cafe': 0.95,       # Slight reduction in cafe
                'street': 0.90,     # Reduction in street noise
                'construction': 0.85, # Significant reduction in construction
                'unknown': 1.0      # No change for unknown
            }
            
            calibration_factor = env_calibration.get(env_type, 1.0)
            calibrated_confidence *= calibration_factor
        
        # Speaker-based calibration
        if speaker_info and self.config.speaker_adaptation:
            voice_quality = speaker_info.get('voice_quality_score', 0.5)
            
            # Higher voice quality speakers get slight confidence boost
            if voice_quality > 0.8:
                calibrated_confidence *= 1.05
            elif voice_quality < 0.4:
                calibrated_confidence *= 0.95
        
        return max(0.0, min(1.0, calibrated_confidence))
    
    def _calculate_statistical_measures(self, confidence: float, 
                                      factors: List[ConfidenceFactor]) -> Tuple[Tuple[float, float], float, float]:
        """Calculate statistical measures for confidence."""
        # Confidence interval calculation
        if len(self.confidence_history) >= self.config.min_samples_for_stats:
            historical_confidences = [a.overall_confidence for a in list(self.confidence_history)]
            
            # Calculate confidence interval using t-distribution
            mean_conf = np.mean(historical_confidences)
            std_conf = np.std(historical_confidences, ddof=1)
            n = len(historical_confidences)
            
            if std_conf > 0:
                t_critical = stats.t.ppf(1 - self.config.confidence_interval_alpha/2, n-1)
                margin_error = t_critical * std_conf / np.sqrt(n)
                
                ci_lower = max(0.0, mean_conf - margin_error)
                ci_upper = min(1.0, mean_conf + margin_error)
            else:
                ci_lower = ci_upper = mean_conf
            
            confidence_interval = (ci_lower, ci_upper)
        else:
            confidence_interval = (confidence * 0.8, confidence * 1.2)
            confidence_interval = (max(0.0, confidence_interval[0]), min(1.0, confidence_interval[1]))
        
        # Uncertainty estimation
        factor_uncertainties = [f.uncertainty for f in factors if f.uncertainty > 0]
        if factor_uncertainties:
            # Combine uncertainties (simplified approach)
            combined_uncertainty = np.sqrt(np.mean(np.array(factor_uncertainties) ** 2))
        else:
            combined_uncertainty = 0.2  # Default uncertainty
        
        # Statistical significance (simplified)
        if len(self.confidence_history) >= 10:
            recent_confidences = [a.overall_confidence for a in list(self.confidence_history)[-10:]]
            t_stat, p_value = stats.ttest_1samp(recent_confidences, 0.5)  # Test against neutral confidence
            significance = 1.0 - p_value if p_value < 1.0 else 0.0
        else:
            significance = 0.0
        
        return confidence_interval, combined_uncertainty, significance
    
    def _estimate_snr(self, audio_data: np.ndarray) -> float:
        """Estimate signal-to-noise ratio from audio data."""
        if len(audio_data) == 0:
            return 0.0
        
        # Simple SNR estimation
        signal_power = np.mean(audio_data ** 2)
        
        # Estimate noise as the lower 25th percentile of signal
        sorted_power = np.sort(audio_data ** 2)
        noise_power = np.mean(sorted_power[:len(sorted_power)//4])
        
        if noise_power > 0 and signal_power > noise_power:
            snr_linear = signal_power / noise_power
            snr_db = 10 * np.log10(snr_linear)
            return max(0.0, min(40.0, snr_db))  # Clip to reasonable range
        
        return 0.0
    
    def _estimate_transcription_quality(self, confidence: float, 
                                      factors: List[ConfidenceFactor],
                                      audio_quality_metrics: Optional[Dict[str, Any]]) -> float:
        """Estimate overall transcription quality."""
        # Base quality from confidence
        base_quality = confidence
        
        # Audio quality contribution
        if audio_quality_metrics:
            audio_quality = audio_quality_metrics.get('overall_score', 0.5)
            speech_intelligibility = audio_quality_metrics.get('speech_intelligibility', 0.5)
            
            quality_contribution = (audio_quality * 0.6 + speech_intelligibility * 0.4) * 0.3
            base_quality = base_quality * 0.7 + quality_contribution
        
        # Factor reliability contribution
        factor_reliabilities = [f.reliability for f in factors]
        if factor_reliabilities:
            avg_reliability = np.mean(factor_reliabilities)
            base_quality = base_quality * 0.8 + avg_reliability * 0.2
        
        return max(0.0, min(1.0, base_quality))
    
    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Determine confidence level from score."""
        if confidence >= self.adaptive_thresholds['very_high']:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= self.adaptive_thresholds['high']:
            return ConfidenceLevel.HIGH
        elif confidence >= self.adaptive_thresholds['medium']:
            return ConfidenceLevel.MEDIUM
        elif confidence >= self.adaptive_thresholds['low']:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _generate_improvement_suggestions(self, factors: List[ConfidenceFactor],
                                        audio_quality_metrics: Optional[Dict[str, Any]]) -> List[str]:
        """Generate suggestions for improving confidence."""
        suggestions = []
        
        # Analyze factor weaknesses
        for factor in factors:
            if factor.raw_score < 0.6:
                if factor.factor_type == ConfidenceFactorType.ACOUSTIC_MODEL:
                    suggestions.append("Improve audio quality or reduce background noise")
                elif factor.factor_type == ConfidenceFactorType.AUDIO_QUALITY:
                    suggestions.append("Use better recording equipment or quieter environment")
                elif factor.factor_type == ConfidenceFactorType.LINGUISTIC:
                    suggestions.append("Speak more clearly with proper grammar")
                elif factor.factor_type == ConfidenceFactorType.CONTEXTUAL:
                    suggestions.append("Provide more context or speak in complete sentences")
                elif factor.factor_type == ConfidenceFactorType.TEMPORAL:
                    suggestions.append("Maintain consistent speaking pace and volume")
        
        # Audio quality specific suggestions
        if audio_quality_metrics:
            if audio_quality_metrics.get('snr_db', 0) < 15:
                suggestions.append("Reduce background noise or increase microphone gain")
            
            if audio_quality_metrics.get('clipping_percent', 0) > 1:
                suggestions.append("Reduce recording volume to prevent audio clipping")
            
            if audio_quality_metrics.get('speech_intelligibility', 0) < 0.6:
                suggestions.append("Speak more clearly and articulate words better")
        
        return list(set(suggestions))  # Remove duplicates
    
    def _generate_quality_warnings(self, factors: List[ConfidenceFactor],
                                 audio_quality_metrics: Optional[Dict[str, Any]]) -> List[str]:
        """Generate quality warnings based on analysis."""
        warnings = []
        
        # Low confidence warnings
        acoustic_factors = [f for f in factors if f.factor_type == ConfidenceFactorType.ACOUSTIC_MODEL]
        if acoustic_factors and acoustic_factors[0].raw_score < 0.4:
            warnings.append("Low acoustic model confidence - transcription may be inaccurate")
        
        # Audio quality warnings
        if audio_quality_metrics:
            quality_level = audio_quality_metrics.get('quality_level', 'poor')
            if quality_level in ['poor', 'unacceptable']:
                warnings.append(f"Audio quality is {quality_level} - expect reduced accuracy")
            
            if audio_quality_metrics.get('clipping_percent', 0) > 5:
                warnings.append("Significant audio clipping detected - transcription quality affected")
            
            if audio_quality_metrics.get('snr_db', 0) < 10:
                warnings.append("Poor signal-to-noise ratio - background noise may interfere")
        
        # Temporal instability warning
        temporal_factors = [f for f in factors if f.factor_type == ConfidenceFactorType.TEMPORAL]
        if temporal_factors and temporal_factors[0].raw_score < 0.5:
            warnings.append("Inconsistent audio quality - confidence may vary significantly")
        
        return warnings
    
    def _update_confidence_history(self, assessment: ConfidenceAssessment):
        """Update confidence history for statistical analysis."""
        self.confidence_history.append(assessment)
    
    def _update_factor_histories(self, factors: List[ConfidenceFactor]):
        """Update individual factor histories."""
        for factor in factors:
            self.factor_histories[factor.factor_type].append(factor)
    
    def _update_adaptive_parameters(self, assessment: ConfidenceAssessment,
                                  environmental_context: Optional[Dict[str, Any]],
                                  speaker_info: Optional[Dict[str, Any]]):
        """Update adaptive parameters based on new assessment."""
        if not self.config.adaptive_thresholds:
            return
        
        # Environment-specific adaptation
        if environmental_context:
            env_type = environmental_context.get('environment', 'unknown')
            if env_type not in self.environment_profiles:
                self.environment_profiles[env_type] = {
                    'confidence_samples': deque(maxlen=50),
                    'quality_samples': deque(maxlen=50)
                }
            
            profile = self.environment_profiles[env_type]
            profile['confidence_samples'].append(assessment.overall_confidence)
            profile['quality_samples'].append(assessment.audio_quality_score)
            
            # Adjust thresholds based on environment performance
            if len(profile['confidence_samples']) >= 10:
                env_mean_confidence = np.mean(list(profile['confidence_samples']))
                
                # Slightly adjust thresholds for this environment
                adjustment_factor = 0.02  # Small adjustment
                if env_mean_confidence < 0.6:  # Poor performance environment
                    self.adaptive_thresholds['medium'] *= (1 - adjustment_factor)
                    self.adaptive_thresholds['high'] *= (1 - adjustment_factor)
    
    def get_confidence_statistics(self) -> Dict[str, Any]:
        """Get comprehensive confidence scoring statistics."""
        stats_dict = {
            'total_assessments': self.scoring_stats['total_assessments'],
            'low_confidence_rate': (self.scoring_stats['low_confidence_count'] / 
                                  max(1, self.scoring_stats['total_assessments'])),
            'high_confidence_rate': (self.scoring_stats['high_confidence_count'] / 
                                   max(1, self.scoring_stats['total_assessments'])),
            'adaptive_thresholds': self.adaptive_thresholds.copy(),
        }
        
        # Recent confidence statistics
        if len(self.confidence_history) > 0:
            recent_confidences = [a.overall_confidence for a in list(self.confidence_history)[-50:]]
            stats_dict.update({
                'recent_mean_confidence': np.mean(recent_confidences),
                'recent_confidence_std': np.std(recent_confidences),
                'recent_min_confidence': np.min(recent_confidences),
                'recent_max_confidence': np.max(recent_confidences)
            })
        
        # Factor performance
        factor_stats = {}
        for factor_type, history in self.factor_histories.items():
            if len(history) > 0:
                recent_factors = list(history)[-20:]
                factor_stats[factor_type.value] = {
                    'mean_score': np.mean([f.raw_score for f in recent_factors]),
                    'mean_reliability': np.mean([f.reliability for f in recent_factors]),
                    'mean_uncertainty': np.mean([f.uncertainty for f in recent_factors])
                }
        
        stats_dict['factor_performance'] = factor_stats
        
        # Processing performance
        if self.scoring_stats['processing_times']:
            stats_dict['average_processing_time_ms'] = np.mean(list(self.scoring_stats['processing_times']))
        
        return stats_dict

# Global confidence scorer instance
_confidence_scorer: Optional[AdvancedConfidenceScorer] = None

def get_confidence_scorer() -> Optional[AdvancedConfidenceScorer]:
    """Get the global confidence scorer."""
    return _confidence_scorer

def initialize_confidence_scorer(config: Optional[ConfidenceConfig] = None) -> AdvancedConfidenceScorer:
    """Initialize the global confidence scorer."""
    global _confidence_scorer
    _confidence_scorer = AdvancedConfidenceScorer(config)
    return _confidence_scorer