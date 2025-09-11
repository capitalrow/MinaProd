#!/usr/bin/env python3
# 🌍 Production Feature: Multi-language Detection & Automatic Language Switching
"""
Enterprise-grade multi-language detection and automatic language switching service.
Implements real-time language identification with confidence scoring and seamless transitions.

Addresses: "Multi-language Detection & Automatic Switching" for Fix Pack 4.

Key Features:
- Real-time language detection from audio and text
- Confidence scoring for language predictions
- Automatic language switching with hysteresis
- Support for 30+ languages with regional variants
- Acoustic and linguistic feature analysis
- Language transition smoothing and validation
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from collections import deque, Counter
from enum import Enum
import time
import re
from scipy.stats import entropy

logger = logging.getLogger(__name__)

class LanguageConfidence(Enum):
    """Language detection confidence levels."""
    VERY_HIGH = "very_high"    # > 95%
    HIGH = "high"              # 85-95%
    MEDIUM = "medium"          # 70-85%
    LOW = "low"               # 50-70%
    VERY_LOW = "very_low"     # < 50%

@dataclass
class LanguageFeatures:
    """Language-specific acoustic and linguistic features."""
    # Acoustic features
    phoneme_frequencies: Dict[str, float] = field(default_factory=dict)
    prosodic_patterns: Dict[str, float] = field(default_factory=dict)
    rhythm_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Linguistic features
    character_ngrams: Dict[str, float] = field(default_factory=dict)
    word_patterns: Dict[str, float] = field(default_factory=dict)
    morphological_markers: Dict[str, float] = field(default_factory=dict)
    
    # Statistical features
    syllable_complexity: float = 0.0
    vowel_consonant_ratio: float = 0.0
    lexical_diversity: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'phoneme_frequencies': self.phoneme_frequencies,
            'prosodic_patterns': self.prosodic_patterns,
            'rhythm_metrics': self.rhythm_metrics,
            'character_ngrams': self.character_ngrams,
            'word_patterns': self.word_patterns,
            'morphological_markers': self.morphological_markers,
            'syllable_complexity': self.syllable_complexity,
            'vowel_consonant_ratio': self.vowel_consonant_ratio,
            'lexical_diversity': self.lexical_diversity
        }

@dataclass
class LanguagePrediction:
    """Language prediction with confidence scoring."""
    language_code: str
    language_name: str
    confidence: float
    evidence: Dict[str, float] = field(default_factory=dict)
    
    # Prediction metadata
    detection_method: str = "hybrid"  # acoustic, linguistic, or hybrid
    timestamp: float = field(default_factory=time.time)
    audio_duration: float = 0.0
    text_length: int = 0
    
    @property
    def confidence_level(self) -> LanguageConfidence:
        """Get confidence level enum."""
        if self.confidence >= 0.95:
            return LanguageConfidence.VERY_HIGH
        elif self.confidence >= 0.85:
            return LanguageConfidence.HIGH
        elif self.confidence >= 0.70:
            return LanguageConfidence.MEDIUM
        elif self.confidence >= 0.50:
            return LanguageConfidence.LOW
        else:
            return LanguageConfidence.VERY_LOW

@dataclass
class LanguageTransition:
    """Language transition event."""
    from_language: str
    to_language: str
    transition_time: float
    confidence_before: float
    confidence_after: float
    evidence: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LanguageDetectionConfig:
    """Configuration for language detection."""
    # Detection settings
    min_confidence_threshold: float = 0.7  # Minimum confidence for language switch
    hysteresis_factor: float = 0.15       # Confidence difference required for switch
    min_detection_duration: float = 2.0   # Minimum duration for reliable detection
    
    # Language support
    supported_languages: Set[str] = field(default_factory=lambda: {
        'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko',
        'ar', 'hi', 'th', 'vi', 'tr', 'pl', 'nl', 'sv', 'da', 'no',
        'fi', 'cs', 'sk', 'hu', 'ro', 'bg', 'hr', 'sl', 'et', 'lv',
        'lt', 'mt', 'el', 'cy', 'ga', 'is', 'fo'
    })
    
    # Processing parameters
    analysis_window_size: float = 3.0     # Window size for analysis (seconds)
    overlap_ratio: float = 0.5            # Overlap between analysis windows
    smoothing_factor: float = 0.3         # Exponential smoothing for predictions
    
    # Quality control
    min_audio_quality: float = 0.6        # Minimum audio quality for detection
    max_uncertainty: float = 0.3          # Maximum prediction uncertainty allowed
    
    # Feature weights
    acoustic_weight: float = 0.6          # Weight for acoustic features
    linguistic_weight: float = 0.4        # Weight for linguistic features

# Language-specific patterns and characteristics
LANGUAGE_CHARACTERISTICS = {
    'en': {
        'name': 'English',
        'family': 'Germanic',
        'typical_phonemes': ['θ', 'ð', 'ɹ', 'w'],
        'vowel_system': ['i:', 'ɪ', 'e', 'æ', 'ɑ:', 'ɔ:', 'ʊ', 'u:', 'ʌ', 'ə'],
        'prosodic_stress': 'stress-timed',
        'character_patterns': ['th', 'ing', 'tion', 'ed'],
        'word_patterns': ['the', 'and', 'of', 'to', 'a', 'in', 'is', 'it'],
        'syllable_structure': 'complex'
    },
    'es': {
        'name': 'Spanish',
        'family': 'Romance',
        'typical_phonemes': ['r', 'rr', 'x', 'ñ'],
        'vowel_system': ['a', 'e', 'i', 'o', 'u'],
        'prosodic_stress': 'syllable-timed',
        'character_patterns': ['ción', 'dad', 'que', 'll', 'ñ'],
        'word_patterns': ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es'],
        'syllable_structure': 'simple'
    },
    'fr': {
        'name': 'French',
        'family': 'Romance',
        'typical_phonemes': ['ʁ', 'y', 'ø', 'œ'],
        'vowel_system': ['i', 'e', 'ɛ', 'a', 'ɔ', 'o', 'u', 'y', 'ø', 'œ', 'ə'],
        'prosodic_stress': 'syllable-timed',
        'character_patterns': ['tion', 'eau', 'eur', 'eux'],
        'word_patterns': ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et'],
        'syllable_structure': 'moderate'
    },
    'de': {
        'name': 'German',
        'family': 'Germanic',
        'typical_phonemes': ['x', 'ç', 'ʏ', 'œ'],
        'vowel_system': ['i:', 'ɪ', 'e:', 'ɛ', 'a:', 'a', 'o:', 'ɔ', 'u:', 'ʊ', 'y:', 'ʏ', 'ø:', 'œ'],
        'prosodic_stress': 'stress-timed',
        'character_patterns': ['sch', 'ung', 'keit', 'lich'],
        'word_patterns': ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das'],
        'syllable_structure': 'complex'
    },
    # Add more languages as needed...
}

class LanguageDetectionService:
    """
    🌍 Enterprise-grade multi-language detection service.
    
    Provides real-time language identification with confidence scoring,
    automatic language switching, and seamless transitions for global applications.
    """
    
    def __init__(self, config: Optional[LanguageDetectionConfig] = None):
        self.config = config or LanguageDetectionConfig()
        
        # Detection state
        self.current_language: Optional[str] = None
        self.language_history: deque = deque(maxlen=100)
        self.prediction_buffer: deque = deque(maxlen=50)
        
        # Language models and patterns
        self.language_models: Dict[str, Dict[str, Any]] = {}
        self._initialize_language_models()
        
        # Statistics and metrics
        self.detection_stats = {
            'total_detections': 0,
            'language_switches': 0,
            'confidence_distribution': Counter(),
            'detection_accuracy': 0.0,
            'processing_time': 0.0
        }
        
        # Smoothing and hysteresis
        self.smoothed_predictions: Dict[str, float] = {}
        self.last_confident_language: Optional[str] = None
        self.last_switch_time: float = 0.0
        
        logger.info(f"🌍 Language detection service initialized with {len(self.config.supported_languages)} languages")
    
    def _initialize_language_models(self):
        """Initialize language models and patterns."""
        for lang_code in self.config.supported_languages:
            if lang_code in LANGUAGE_CHARACTERISTICS:
                char_data = LANGUAGE_CHARACTERISTICS[lang_code]
                
                # Build n-gram models
                character_patterns = char_data.get('character_patterns', [])
                word_patterns = char_data.get('word_patterns', [])
                
                self.language_models[lang_code] = {
                    'characteristics': char_data,
                    'character_patterns': set(character_patterns),
                    'word_patterns': set(word_patterns),
                    'phoneme_patterns': set(char_data.get('typical_phonemes', [])),
                    'vowel_system': set(char_data.get('vowel_system', [])),
                    'prosodic_type': char_data.get('prosodic_stress', 'unknown')
                }
    
    def detect_language(self, audio_data: Optional[np.ndarray] = None,
                       text: Optional[str] = None,
                       sample_rate: int = 16000) -> LanguagePrediction:
        """
        Detect language from audio and/or text with confidence scoring.
        
        Args:
            audio_data: Audio samples as numpy array
            text: Text content for linguistic analysis
            sample_rate: Audio sample rate
            
        Returns:
            Language prediction with confidence score
        """
        try:
            start_time = time.time()
            
            if audio_data is None and text is None:
                logger.warning("🌍 No audio or text provided for language detection")
                return LanguagePrediction("unknown", "Unknown", 0.0)
            
            # Extract features
            acoustic_features = self._extract_acoustic_features(audio_data, sample_rate) if audio_data is not None else {}
            linguistic_features = self._extract_linguistic_features(text) if text else {}
            
            # Predict language using different methods
            predictions = self._predict_languages(acoustic_features, linguistic_features)
            
            # Select best prediction
            best_prediction = self._select_best_prediction(predictions)
            
            # Apply smoothing and hysteresis
            smoothed_prediction = self._apply_smoothing(best_prediction)
            
            # Update statistics
            processing_time = time.time() - start_time
            self.detection_stats['total_detections'] += 1
            self.detection_stats['processing_time'] += processing_time
            self.detection_stats['confidence_distribution'][smoothed_prediction.confidence_level.value] += 1
            
            # Add to prediction buffer
            self.prediction_buffer.append(smoothed_prediction)
            
            logger.debug(f"🌍 Language detected: {smoothed_prediction.language_code} ({smoothed_prediction.confidence:.3f})")
            return smoothed_prediction
            
        except Exception as e:
            logger.error(f"❌ Error in language detection: {e}")
            return LanguagePrediction("error", "Error", 0.0)
    
    def _extract_acoustic_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Extract acoustic features for language identification."""
        if len(audio_data) == 0:
            return {}
        
        features = {}
        
        # === PROSODIC FEATURES ===
        # Rhythm metrics
        features['rhythm_metrics'] = self._analyze_rhythm(audio_data, sample_rate)
        
        # Pitch patterns
        features['pitch_patterns'] = self._analyze_pitch_patterns(audio_data, sample_rate)
        
        # Energy distribution
        features['energy_patterns'] = self._analyze_energy_distribution(audio_data, sample_rate)
        
        # === PHONEME-LEVEL FEATURES ===
        # Spectral characteristics for phoneme identification
        features['phoneme_indicators'] = self._extract_phoneme_indicators(audio_data, sample_rate)
        
        # Voice quality indicators
        features['voice_quality'] = self._analyze_voice_quality(audio_data, sample_rate)
        
        return features
    
    def _extract_linguistic_features(self, text: str) -> Dict[str, Any]:
        """Extract linguistic features from text."""
        if not text or len(text.strip()) == 0:
            return {}
        
        features = {}
        text_clean = text.lower().strip()
        
        # === CHARACTER-LEVEL FEATURES ===
        features['character_distribution'] = self._analyze_character_distribution(text_clean)
        features['character_ngrams'] = self._extract_character_ngrams(text_clean)
        
        # === WORD-LEVEL FEATURES ===
        words = re.findall(r'\b\w+\b', text_clean)
        features['word_patterns'] = self._analyze_word_patterns(words)
        features['word_statistics'] = self._calculate_word_statistics(words)
        
        # === MORPHOLOGICAL FEATURES ===
        features['morphological_patterns'] = self._analyze_morphological_patterns(text_clean)
        
        # === SYNTACTIC INDICATORS ===
        features['syntactic_patterns'] = self._analyze_syntactic_patterns(text_clean)
        
        return features
    
    def _analyze_rhythm(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Analyze speech rhythm patterns."""
        # Energy envelope analysis
        frame_size = int(0.02 * sample_rate)  # 20ms frames
        hop_size = int(0.01 * sample_rate)    # 10ms hop
        
        energy_envelope = []
        for i in range(0, len(audio_data) - frame_size, hop_size):
            frame_energy = np.sum(audio_data[i:i+frame_size] ** 2)
            energy_envelope.append(frame_energy)
        
        if len(energy_envelope) < 10:
            return {'rhythm_regularity': 0.0, 'stress_timing': 0.0, 'syllable_timing': 0.0}
        
        energy_envelope = np.array(energy_envelope)
        
        # Rhythm regularity (variance in inter-peak intervals)
        peaks = []
        threshold = np.mean(energy_envelope) + np.std(energy_envelope)
        
        for i in range(1, len(energy_envelope) - 1):
            if (energy_envelope[i] > energy_envelope[i-1] and 
                energy_envelope[i] > energy_envelope[i+1] and 
                energy_envelope[i] > threshold):
                peaks.append(i)
        
        rhythm_regularity = 0.0
        if len(peaks) > 2:
            intervals = np.diff(peaks)
            rhythm_regularity = 1.0 - (np.std(intervals) / np.mean(intervals)) if np.mean(intervals) > 0 else 0.0
            rhythm_regularity = max(0.0, min(1.0, rhythm_regularity))
        
        # Stress-timing vs syllable-timing indicators
        # Stress-timed languages have more variable intervals
        stress_timing = 1.0 - rhythm_regularity  # More variability = more stress-timed
        syllable_timing = rhythm_regularity       # More regular = more syllable-timed
        
        return {
            'rhythm_regularity': float(rhythm_regularity),
            'stress_timing': float(stress_timing),
            'syllable_timing': float(syllable_timing)
        }
    
    def _analyze_pitch_patterns(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Analyze pitch patterns for language identification."""
        # Simplified F0 contour analysis
        frame_size = int(0.02 * sample_rate)  # 20ms frames
        f0_values = []
        
        for i in range(0, len(audio_data) - frame_size, frame_size):
            frame = audio_data[i:i+frame_size]
            
            # Simple autocorrelation-based F0 estimation
            autocorr = np.correlate(frame, frame, mode='full')
            autocorr = autocorr[autocorr.size // 2:]
            
            # Look for F0 in speech range (80-400 Hz)
            min_period = int(sample_rate / 400)
            max_period = int(sample_rate / 80)
            
            if max_period < len(autocorr):
                search_range = autocorr[min_period:max_period]
                if len(search_range) > 0:
                    peak_idx = np.argmax(search_range) + min_period
                    f0 = sample_rate / peak_idx
                    if 80 <= f0 <= 400:
                        f0_values.append(f0)
        
        if len(f0_values) < 5:
            return {'pitch_range': 0.0, 'pitch_variability': 0.0, 'intonation_complexity': 0.0}
        
        f0_values = np.array(f0_values)
        
        # Pitch range (normalized)
        pitch_range = (np.max(f0_values) - np.min(f0_values)) / np.mean(f0_values)
        
        # Pitch variability (coefficient of variation)
        pitch_variability = np.std(f0_values) / np.mean(f0_values)
        
        # Intonation complexity (entropy of pitch changes)
        pitch_changes = np.diff(f0_values)
        intonation_complexity = 0.0
        if len(pitch_changes) > 0:
            # Quantize pitch changes
            change_bins = np.histogram(pitch_changes, bins=10)[0]
            change_probs = change_bins / np.sum(change_bins) if np.sum(change_bins) > 0 else change_bins
            change_probs = change_probs[change_probs > 0]  # Remove zeros for entropy calculation
            if len(change_probs) > 1:
                intonation_complexity = entropy(change_probs)
        
        return {
            'pitch_range': float(pitch_range),
            'pitch_variability': float(pitch_variability),
            'intonation_complexity': float(intonation_complexity)
        }
    
    def _analyze_energy_distribution(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Analyze energy distribution patterns."""
        # Spectral energy distribution
        spectrum = np.abs(np.fft.rfft(audio_data * np.hanning(len(audio_data))))
        freqs = np.fft.rfftfreq(len(audio_data), 1/sample_rate)
        
        # Energy in different frequency bands
        low_energy = np.sum(spectrum[(freqs >= 0) & (freqs < 500)])
        mid_energy = np.sum(spectrum[(freqs >= 500) & (freqs < 2000)])
        high_energy = np.sum(spectrum[(freqs >= 2000) & (freqs < 8000)])
        
        total_energy = low_energy + mid_energy + high_energy
        
        if total_energy > 0:
            return {
                'low_frequency_ratio': float(low_energy / total_energy),
                'mid_frequency_ratio': float(mid_energy / total_energy),
                'high_frequency_ratio': float(high_energy / total_energy)
            }
        
        return {'low_frequency_ratio': 0.33, 'mid_frequency_ratio': 0.33, 'high_frequency_ratio': 0.33}
    
    def _extract_phoneme_indicators(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Extract phoneme-specific acoustic indicators."""
        # Simplified phoneme detection based on spectral characteristics
        spectrum = np.abs(np.fft.rfft(audio_data * np.hanning(len(audio_data))))
        freqs = np.fft.rfftfreq(len(audio_data), 1/sample_rate)
        
        indicators = {}
        
        # Fricative indicators (high-frequency noise)
        fricative_energy = np.sum(spectrum[(freqs >= 4000) & (freqs < 8000)])
        total_energy = np.sum(spectrum)
        indicators['fricative_ratio'] = fricative_energy / total_energy if total_energy > 0 else 0.0
        
        # Vowel indicators (formant structure)
        # Look for peaks in vowel formant regions
        f1_region = spectrum[(freqs >= 200) & (freqs < 1000)]
        f2_region = spectrum[(freqs >= 800) & (freqs < 2500)]
        
        indicators['vowel_strength'] = (np.max(f1_region) + np.max(f2_region)) / 2 if len(f1_region) > 0 and len(f2_region) > 0 else 0.0
        
        # Nasal indicators (low-frequency resonance)
        nasal_region = spectrum[(freqs >= 200) & (freqs < 500)]
        indicators['nasal_strength'] = np.max(nasal_region) if len(nasal_region) > 0 else 0.0
        
        return indicators
    
    def _analyze_voice_quality(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Analyze voice quality characteristics."""
        # Harmonic-to-noise ratio (simplified)
        autocorr = np.correlate(audio_data, audio_data, mode='full')
        autocorr = autocorr[autocorr.size // 2:]
        
        max_autocorr = np.max(autocorr[1:]) if len(autocorr) > 1 else 0
        noise_floor = np.mean(autocorr[len(autocorr)//2:]) if len(autocorr) > 10 else 0
        
        hnr = 20 * np.log10(max_autocorr / noise_floor) if noise_floor > 0 else 0
        hnr = max(0.0, min(40.0, hnr))  # Cap between 0-40 dB
        
        # Spectral tilt (energy distribution slope)
        spectrum = np.abs(np.fft.rfft(audio_data * np.hanning(len(audio_data))))
        freqs = np.fft.rfftfreq(len(audio_data), 1/sample_rate)
        
        # Fit line to log spectrum
        log_spectrum = np.log(spectrum + 1e-10)
        if len(freqs) > 10:
            spectral_tilt = np.polyfit(freqs[:len(freqs)//2], log_spectrum[:len(freqs)//2], 1)[0]
        else:
            spectral_tilt = 0.0
        
        return {
            'harmonicity': float(hnr / 40.0),  # Normalize to 0-1
            'spectral_tilt': float(spectral_tilt)
        }
    
    def _analyze_character_distribution(self, text: str) -> Dict[str, float]:
        """Analyze character frequency distribution."""
        char_counts = Counter(char.lower() for char in text if char.isalpha())
        total_chars = sum(char_counts.values())
        
        if total_chars == 0:
            return {}
        
        char_freqs = {char: count / total_chars for char, count in char_counts.items()}
        
        # Language-specific character indicators
        indicators = {}
        
        # Vowel ratio
        vowels = set('aeiou')
        vowel_count = sum(char_counts[char] for char in vowels if char in char_counts)
        indicators['vowel_ratio'] = vowel_count / total_chars
        
        # Language-specific characters
        indicators['has_accents'] = any(char in 'áéíóúàèìòùâêîôûäëïöüãõñç' for char in text)
        indicators['has_umlauts'] = any(char in 'äöüß' for char in text)
        indicators['has_tildes'] = any(char in 'ñãõ' for char in text)
        indicators['has_cedillas'] = any(char in 'ç' for char in text)
        
        return indicators
    
    def _extract_character_ngrams(self, text: str, n: int = 3) -> Dict[str, float]:
        """Extract character n-grams."""
        ngrams = Counter()
        
        for i in range(len(text) - n + 1):
            ngram = text[i:i+n]
            if ngram.isalpha():
                ngrams[ngram] += 1
        
        total_ngrams = sum(ngrams.values())
        if total_ngrams == 0:
            return {}
        
        return {ngram: count / total_ngrams for ngram, count in ngrams.most_common(50)}
    
    def _analyze_word_patterns(self, words: List[str]) -> Dict[str, Any]:
        """Analyze word patterns and statistics."""
        if not words:
            return {}
        
        word_counts = Counter(words)
        total_words = len(words)
        unique_words = len(word_counts)
        
        # Word length distribution
        word_lengths = [len(word) for word in words]
        avg_word_length = np.mean(word_lengths)
        
        # Most common words
        common_words = {word: count / total_words for word, count in word_counts.most_common(20)}
        
        return {
            'lexical_diversity': unique_words / total_words if total_words > 0 else 0,
            'average_word_length': avg_word_length,
            'common_words': common_words,
            'total_words': total_words
        }
    
    def _calculate_word_statistics(self, words: List[str]) -> Dict[str, float]:
        """Calculate word-level statistics."""
        if not words:
            return {}
        
        word_lengths = [len(word) for word in words]
        
        return {
            'mean_length': float(np.mean(word_lengths)),
            'std_length': float(np.std(word_lengths)),
            'min_length': float(np.min(word_lengths)),
            'max_length': float(np.max(word_lengths)),
            'median_length': float(np.median(word_lengths))
        }
    
    def _analyze_morphological_patterns(self, text: str) -> Dict[str, float]:
        """Analyze morphological patterns."""
        # Common suffixes by language family
        morphological_indicators = {}
        
        # Romance language patterns
        romance_patterns = ['tion', 'sion', 'ment', 'ance', 'ence', 'idad', 'edad']
        romance_count = sum(text.count(pattern) for pattern in romance_patterns)
        morphological_indicators['romance_morphology'] = romance_count
        
        # Germanic language patterns
        germanic_patterns = ['ing', 'ed', 'er', 'est', 'ly', 'ness', 'ung', 'keit']
        germanic_count = sum(text.count(pattern) for pattern in germanic_patterns)
        morphological_indicators['germanic_morphology'] = germanic_count
        
        # Slavic language patterns
        slavic_patterns = ['ский', 'ность', 'ение', 'ание', 'ový', 'ní']
        slavic_count = sum(text.count(pattern) for pattern in slavic_patterns)
        morphological_indicators['slavic_morphology'] = slavic_count
        
        return morphological_indicators
    
    def _analyze_syntactic_patterns(self, text: str) -> Dict[str, float]:
        """Analyze syntactic patterns."""
        # Simple syntactic indicators
        indicators = {}
        
        # Article patterns (simplified)
        articles = {
            'english': ['the', 'a', 'an'],
            'spanish': ['el', 'la', 'los', 'las', 'un', 'una'],
            'french': ['le', 'la', 'les', 'un', 'une'],
            'german': ['der', 'die', 'das', 'ein', 'eine']
        }
        
        words = text.lower().split()
        for lang, lang_articles in articles.items():
            article_count = sum(words.count(article) for article in lang_articles)
            indicators[f'{lang}_articles'] = article_count
        
        return indicators
    
    def _predict_languages(self, acoustic_features: Dict[str, Any], 
                          linguistic_features: Dict[str, Any]) -> Dict[str, float]:
        """Predict language probabilities using multiple methods."""
        predictions = {}
        
        # Initialize predictions
        for lang_code in self.config.supported_languages:
            predictions[lang_code] = 0.0
        
        # Acoustic-based predictions
        if acoustic_features:
            acoustic_pred = self._predict_from_acoustic_features(acoustic_features)
            for lang, score in acoustic_pred.items():
                predictions[lang] += score * self.config.acoustic_weight
        
        # Linguistic-based predictions
        if linguistic_features:
            linguistic_pred = self._predict_from_linguistic_features(linguistic_features)
            for lang, score in linguistic_pred.items():
                predictions[lang] += score * self.config.linguistic_weight
        
        # Normalize predictions
        total_score = sum(predictions.values())
        if total_score > 0:
            predictions = {lang: score / total_score for lang, score in predictions.items()}
        
        return predictions
    
    def _predict_from_acoustic_features(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Predict language from acoustic features."""
        predictions = {}
        
        # Initialize equal probabilities
        for lang_code in self.config.supported_languages:
            predictions[lang_code] = 1.0 / len(self.config.supported_languages)
        
        # Use rhythm patterns for language family classification
        rhythm_metrics = features.get('rhythm_metrics', {})
        stress_timing = rhythm_metrics.get('stress_timing', 0.5)
        syllable_timing = rhythm_metrics.get('syllable_timing', 0.5)
        
        # Stress-timed languages (Germanic)
        if stress_timing > 0.6:
            stress_timed_langs = ['en', 'de', 'nl', 'sv', 'da', 'no']
            for lang in stress_timed_langs:
                if lang in predictions:
                    predictions[lang] *= 1.5
        
        # Syllable-timed languages (Romance, most others)
        if syllable_timing > 0.6:
            syllable_timed_langs = ['es', 'fr', 'it', 'pt', 'tr', 'fi', 'ja']
            for lang in syllable_timed_langs:
                if lang in predictions:
                    predictions[lang] *= 1.3
        
        # Normalize
        total = sum(predictions.values())
        if total > 0:
            predictions = {lang: score / total for lang, score in predictions.items()}
        
        return predictions
    
    def _predict_from_linguistic_features(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Predict language from linguistic features."""
        predictions = {}
        
        # Initialize equal probabilities
        for lang_code in self.config.supported_languages:
            predictions[lang_code] = 1.0 / len(self.config.supported_languages)
        
        # Character distribution analysis
        char_dist = features.get('character_distribution', {})
        
        # Language-specific character indicators
        if char_dist.get('has_umlauts', False):
            predictions['de'] *= 3.0  # Strong German indicator
        
        if char_dist.get('has_tildes', False):
            predictions['es'] *= 2.5  # Spanish indicator
            predictions['pt'] *= 2.0  # Portuguese indicator
        
        if char_dist.get('has_cedillas', False):
            predictions['fr'] *= 2.0  # French indicator
            predictions['pt'] *= 1.5  # Portuguese indicator
        
        # Common word analysis
        word_patterns = features.get('word_patterns', {})
        common_words = word_patterns.get('common_words', {})
        
        # English indicators
        english_words = {'the', 'and', 'of', 'to', 'a', 'in', 'is', 'it'}
        english_score = sum(common_words.get(word, 0) for word in english_words)
        if english_score > 0.1:  # 10% of words are English function words
            predictions['en'] *= (1 + english_score * 5)
        
        # Spanish indicators
        spanish_words = {'el', 'la', 'de', 'que', 'y', 'en', 'un', 'es'}
        spanish_score = sum(common_words.get(word, 0) for word in spanish_words)
        if spanish_score > 0.1:
            predictions['es'] *= (1 + spanish_score * 5)
        
        # French indicators
        french_words = {'le', 'de', 'et', 'à', 'un', 'il', 'être', 'et'}
        french_score = sum(common_words.get(word, 0) for word in french_words)
        if french_score > 0.1:
            predictions['fr'] *= (1 + french_score * 5)
        
        # German indicators
        german_words = {'der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das'}
        german_score = sum(common_words.get(word, 0) for word in german_words)
        if german_score > 0.1:
            predictions['de'] *= (1 + german_score * 5)
        
        # Normalize
        total = sum(predictions.values())
        if total > 0:
            predictions = {lang: score / total for lang, score in predictions.items()}
        
        return predictions
    
    def _select_best_prediction(self, predictions: Dict[str, float]) -> LanguagePrediction:
        """Select the best language prediction."""
        if not predictions:
            return LanguagePrediction("unknown", "Unknown", 0.0)
        
        # Find the language with highest probability
        best_lang = max(predictions.keys(), key=lambda x: predictions[x])
        best_confidence = predictions[best_lang]
        
        # Create evidence dictionary
        evidence = {
            'predictions': predictions,
            'second_best': max(predictions.keys(), key=lambda x: predictions[x] if x != best_lang else 0),
            'entropy': entropy(list(predictions.values())) if len(predictions) > 1 else 0.0
        }
        
        # Get language name
        lang_name = LANGUAGE_CHARACTERISTICS.get(best_lang, {}).get('name', best_lang.upper())
        
        return LanguagePrediction(
            language_code=best_lang,
            language_name=lang_name,
            confidence=best_confidence,
            evidence=evidence,
            detection_method="hybrid"
        )
    
    def _apply_smoothing(self, prediction: LanguagePrediction) -> LanguagePrediction:
        """Apply exponential smoothing to predictions."""
        lang_code = prediction.language_code
        
        # Exponential smoothing
        if lang_code in self.smoothed_predictions:
            smoothed_confidence = (
                self.config.smoothing_factor * prediction.confidence +
                (1 - self.config.smoothing_factor) * self.smoothed_predictions[lang_code]
            )
        else:
            smoothed_confidence = prediction.confidence
        
        self.smoothed_predictions[lang_code] = smoothed_confidence
        
        # Create smoothed prediction
        smoothed_prediction = LanguagePrediction(
            language_code=lang_code,
            language_name=prediction.language_name,
            confidence=smoothed_confidence,
            evidence=prediction.evidence,
            detection_method=prediction.detection_method
        )
        
        return smoothed_prediction
    
    def should_switch_language(self, new_prediction: LanguagePrediction) -> bool:
        """Determine if language should be switched based on hysteresis."""
        if self.current_language is None:
            return True
        
        if new_prediction.language_code == self.current_language:
            return False
        
        # Check confidence threshold
        if new_prediction.confidence < self.config.min_confidence_threshold:
            return False
        
        # Apply hysteresis - require higher confidence to switch away from current language
        current_confidence = self.smoothed_predictions.get(self.current_language, 0.0)
        confidence_diff = new_prediction.confidence - current_confidence
        
        if confidence_diff > self.config.hysteresis_factor:
            return True
        
        return False
    
    def switch_language(self, new_language: str) -> LanguageTransition:
        """Switch to a new language and record the transition."""
        from_language = self.current_language
        transition_time = time.time()
        
        # Create transition event
        transition = LanguageTransition(
            from_language=from_language or "unknown",
            to_language=new_language,
            transition_time=transition_time,
            confidence_before=self.smoothed_predictions.get(from_language, 0.0) if from_language else 0.0,
            confidence_after=self.smoothed_predictions.get(new_language, 0.0),
            evidence={'switch_reason': 'confidence_threshold'}
        )
        
        # Update state
        self.current_language = new_language
        self.last_switch_time = transition_time
        self.detection_stats['language_switches'] += 1
        
        # Add to history
        self.language_history.append(transition)
        
        logger.info(f"🌍 Language switched: {from_language} → {new_language}")
        return transition
    
    def get_language_statistics(self) -> Dict[str, Any]:
        """Get language detection statistics."""
        return {
            'current_language': self.current_language,
            'supported_languages': list(self.config.supported_languages),
            'detection_stats': self.detection_stats.copy(),
            'smoothed_predictions': self.smoothed_predictions.copy(),
            'recent_transitions': [
                {
                    'from': t.from_language,
                    'to': t.to_language,
                    'time': t.transition_time,
                    'confidence': t.confidence_after
                }
                for t in list(self.language_history)[-10:]  # Last 10 transitions
            ]
        }
    
    def reset_detection_state(self):
        """Reset language detection state."""
        self.current_language = None
        self.prediction_buffer.clear()
        self.language_history.clear()
        self.smoothed_predictions.clear()
        self.last_switch_time = 0.0
        
        logger.info("🌍 Language detection state reset")

# Global language detection service
_language_service: Optional[LanguageDetectionService] = None

def get_language_detection_service() -> Optional[LanguageDetectionService]:
    """Get the global language detection service."""
    return _language_service

def initialize_language_detection_service(config: Optional[LanguageDetectionConfig] = None) -> LanguageDetectionService:
    """Initialize the global language detection service."""
    global _language_service
    _language_service = LanguageDetectionService(config)
    return _language_service

# Tiny heuristic: if LANGUAGE_HINT is set, we use it.
# Otherwise we inspect first few hundred chars of interims and finals (held in memory by caller),
# and return a best-guess ISO code for OpenAI (supported: 'en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'sv').
# This avoids mis-hinting English when the user speaks another major language.

VOCABS = {
    "en": r"\b(the|and|you|that|for|with|this|have|was|are)\b",
    "es": r"\b(el|la|de|que|y|en|los|del|se|por)\b",
    "fr": r"\b(le|la|et|les|des|est|pour|que|une|dans)\b",
    "de": r"\b(der|die|und|das|ist|mit|den|nicht|ein|zu)\b",
    "it": r"\b(il|la|e|di|che|per|un|una|del|dei)\b",
    "pt": r"\b(o|a|de|que|e|em|os|do|da|um)\b",
    "nl": r"\b(de|het|en|van|een|dat|is|op|te|voor)\b",
    "sv": r"\b(och|att|det|som|en|är|på|av|för|med)\b",
}

COMPILED = {k: re.compile(v, re.I) for k, v in VOCABS.items()}

def guess_lang(text: str) -> str | None:
    if not text or len(text) < 20:
        return None
    scores = Counter()
    for code, rx in COMPILED.items():
        hits = rx.findall(text)
        if hits:
            scores[code] = len(hits)
    if not scores:
        return None
    # return top-1 if strong enough
    code, n = scores.most_common(1)[0]
    return code if n >= 2 else None