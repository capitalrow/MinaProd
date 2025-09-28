"""
😊 REAL-TIME SENTIMENT ANALYSIS: Advanced emotion detection and sentiment tracking
Provides comprehensive sentiment analysis, emotion detection, and meeting mood tracking
"""

import os
import time
import logging
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
import re
import json
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class SentimentScore:
    """Individual sentiment analysis result"""
    positive: float = 0.0
    negative: float = 0.0
    neutral: float = 0.0
    compound: float = 0.0  # Overall sentiment (-1 to 1)
    confidence: float = 0.0

@dataclass
class EmotionProfile:
    """Comprehensive emotion profile"""
    joy: float = 0.0
    sadness: float = 0.0
    anger: float = 0.0
    fear: float = 0.0
    surprise: float = 0.0
    disgust: float = 0.0
    excitement: float = 0.0
    frustration: float = 0.0
    confidence_level: float = 0.0
    stress_indicators: float = 0.0

@dataclass
class SpeakerMood:
    """Individual speaker mood analysis"""
    speaker_id: str
    current_sentiment: SentimentScore = field(default_factory=SentimentScore)
    current_emotions: EmotionProfile = field(default_factory=EmotionProfile)
    sentiment_history: deque = field(default_factory=lambda: deque(maxlen=20))
    emotion_history: deque = field(default_factory=lambda: deque(maxlen=20))
    mood_trajectory: str = "neutral"  # "improving", "declining", "stable", "neutral"
    engagement_level: float = 0.5
    energy_level: float = 0.5
    last_updated: float = 0.0

@dataclass
class MeetingMoodAnalysis:
    """Overall meeting mood and dynamics"""
    session_id: str
    overall_sentiment: SentimentScore = field(default_factory=SentimentScore)
    meeting_energy: str = "medium"  # "low", "medium", "high"
    engagement_distribution: Dict[str, float] = field(default_factory=dict)
    emotional_peaks: List[Tuple[float, str, float]] = field(default_factory=list)  # (timestamp, emotion, intensity)
    sentiment_trends: Dict[str, List[float]] = field(default_factory=dict)
    mood_transitions: List[Tuple[float, str, str]] = field(default_factory=list)  # (timestamp, from_mood, to_mood)
    tension_indicators: List[Tuple[float, str]] = field(default_factory=list)  # (timestamp, indicator)
    positive_moments: List[Tuple[float, str]] = field(default_factory=list)  # (timestamp, description)

class SentimentAnalysisService:
    """
    Advanced real-time sentiment analysis and emotion detection
    """
    
    def __init__(self):
        self.speaker_moods: Dict[str, Dict[str, SpeakerMood]] = {}  # session_id -> speaker_id -> mood
        self.meeting_analyses: Dict[str, MeetingMoodAnalysis] = {}
        self.analysis_lock = threading.RLock()
        
        # Sentiment lexicons and patterns
        self.positive_words = self._load_positive_lexicon()
        self.negative_words = self._load_negative_lexicon()
        self.emotion_patterns = self._load_emotion_patterns()
        self.intensifiers = self._load_intensifiers()
        self.negation_words = {'not', 'no', 'never', 'none', 'neither', 'nowhere', 'nothing'}
        
        # Voice-based emotion indicators
        self.voice_emotion_mapping = self._create_voice_emotion_mapping()
        
        logger.info("😊 Sentiment Analysis Service initialized")
    
    def analyze_segment_sentiment(self, 
                                session_id: str,
                                speaker_id: str,
                                text: str,
                                timestamp: float,
                                voice_features: Optional[Dict[str, Any]] = None) -> Tuple[SentimentScore, EmotionProfile]:
        """Analyze sentiment and emotions for a single segment"""
        try:
            # Text-based sentiment analysis
            text_sentiment = self._analyze_text_sentiment(text)
            text_emotions = self._analyze_text_emotions(text)
            
            # Voice-based emotion analysis (if available)
            voice_emotions = EmotionProfile()
            if voice_features:
                voice_emotions = self._analyze_voice_emotions(voice_features)
            
            # Combine text and voice analysis
            combined_sentiment = self._combine_sentiment_scores(text_sentiment, voice_emotions)
            combined_emotions = self._combine_emotion_profiles(text_emotions, voice_emotions)
            
            # Update speaker mood tracking
            self._update_speaker_mood(session_id, speaker_id, combined_sentiment, combined_emotions, timestamp)
            
            # Update meeting-level analysis
            self._update_meeting_analysis(session_id, speaker_id, combined_sentiment, combined_emotions, timestamp)
            
            logger.debug(f"😊 Analyzed sentiment for {speaker_id}: "
                        f"compound={combined_sentiment.compound:.2f}")
            
            return combined_sentiment, combined_emotions
            
        except Exception as e:
            logger.error(f"❌ Sentiment analysis failed: {e}")
            return SentimentScore(), EmotionProfile()
    
    def _analyze_text_sentiment(self, text: str) -> SentimentScore:
        """Analyze sentiment from text content"""
        try:
            if not text.strip():
                return SentimentScore(neutral=1.0)
            
            # Preprocess text
            words = self._preprocess_text(text)
            
            if not words:
                return SentimentScore(neutral=1.0)
            
            # Calculate sentiment scores
            positive_score = 0.0
            negative_score = 0.0
            word_count = len(words)
            
            # Analyze each word with context
            for i, word in enumerate(words):
                word_lower = word.lower()
                
                # Check for negation context
                negated = self._check_negation_context(words, i)
                
                # Get word sentiment
                word_sentiment = self._get_word_sentiment(word_lower)
                
                # Apply intensifiers
                intensity_multiplier = self._check_intensifiers(words, i)
                
                # Apply negation
                if negated:
                    word_sentiment = -word_sentiment
                
                # Apply intensity
                word_sentiment *= intensity_multiplier
                
                # Accumulate scores
                if word_sentiment > 0:
                    positive_score += word_sentiment
                elif word_sentiment < 0:
                    negative_score += abs(word_sentiment)
            
            # Normalize scores
            if word_count > 0:
                positive_score /= word_count
                negative_score /= word_count
            
            # Calculate neutral and compound scores
            total_score = positive_score + negative_score
            neutral_score = max(0, 1 - total_score)
            
            # Compound score (-1 to 1)
            compound = positive_score - negative_score
            
            # Calculate confidence based on text length and word coverage
            confidence = min(1.0, len(text) / 100 + (total_score * 0.5))
            
            return SentimentScore(
                positive=positive_score,
                negative=negative_score,
                neutral=neutral_score,
                compound=compound,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"❌ Text sentiment analysis failed: {e}")
            return SentimentScore(neutral=1.0)
    
    def _analyze_text_emotions(self, text: str) -> EmotionProfile:
        """Analyze emotions from text content"""
        try:
            emotions = EmotionProfile()
            
            if not text.strip():
                return emotions
            
            text_lower = text.lower()
            
            # Emotion pattern matching
            for emotion, patterns in self.emotion_patterns.items():
                emotion_score = 0.0
                
                for pattern in patterns:
                    if isinstance(pattern, str):
                        # Simple word matching
                        if pattern in text_lower:
                            emotion_score += 0.3
                    else:
                        # Regex pattern matching
                        matches = re.findall(pattern, text_lower)
                        emotion_score += len(matches) * 0.2
                
                # Normalize and set emotion score
                emotion_score = min(1.0, emotion_score)
                setattr(emotions, emotion, emotion_score)
            
            # Special analysis for confidence and stress
            emotions.confidence_level = self._analyze_confidence_indicators(text_lower)
            emotions.stress_indicators = self._analyze_stress_indicators(text_lower)
            
            return emotions
            
        except Exception as e:
            logger.error(f"❌ Text emotion analysis failed: {e}")
            return EmotionProfile()
    
    def _analyze_voice_emotions(self, voice_features: Dict[str, Any]) -> EmotionProfile:
        """Analyze emotions from voice characteristics"""
        try:
            emotions = EmotionProfile()
            
            # Extract key voice features
            pitch_mean = voice_features.get('pitch_mean', 0)
            pitch_std = voice_features.get('pitch_std', 0)
            energy_mean = voice_features.get('energy_mean', 0)
            jitter = voice_features.get('jitter', 0)
            shimmer = voice_features.get('shimmer', 0)
            speaking_rate = voice_features.get('speaking_rate', 0)
            
            # Map voice features to emotions
            
            # Excitement: High pitch + high energy
            if pitch_mean > 200 and energy_mean > 0.1:
                emotions.excitement = min(1.0, (pitch_mean - 200) / 100 + energy_mean * 3)
            
            # Joy: Moderate high pitch + stable energy + low jitter
            if pitch_mean > 150 and energy_mean > 0.05 and jitter < 0.02:
                emotions.joy = min(1.0, (pitch_mean - 150) / 150 + energy_mean * 2)
            
            # Anger: High energy + high jitter + variable pitch
            if energy_mean > 0.15 and jitter > 0.03:
                emotions.anger = min(1.0, energy_mean * 3 + jitter * 20)
            
            # Sadness: Low energy + low pitch + high shimmer
            if energy_mean < 0.05 and pitch_mean < 120:
                emotions.sadness = min(1.0, (120 - pitch_mean) / 120 + (0.05 - energy_mean) * 10)
            
            # Fear/Anxiety: High jitter + variable pitch + moderate energy
            if jitter > 0.025 and pitch_std > 30:
                emotions.fear = min(1.0, jitter * 25 + pitch_std / 100)
            
            # Stress indicators: High jitter + high shimmer + fast speaking
            if jitter > 0.02 or shimmer > 0.03 or speaking_rate > 200:
                emotions.stress_indicators = min(1.0, 
                    jitter * 30 + shimmer * 20 + max(0, (speaking_rate - 150) / 100))
            
            # Confidence: Stable pitch + appropriate energy + steady rate
            if pitch_std < 20 and 0.05 < energy_mean < 0.15 and 120 < speaking_rate < 180:
                emotions.confidence_level = min(1.0, 
                    (20 - pitch_std) / 20 + energy_mean * 2)
            
            return emotions
            
        except Exception as e:
            logger.error(f"❌ Voice emotion analysis failed: {e}")
            return EmotionProfile()
    
    def _combine_sentiment_scores(self, text_sentiment: SentimentScore, voice_emotions: EmotionProfile) -> SentimentScore:
        """Combine text and voice-based sentiment analysis"""
        try:
            # Weight text more heavily for sentiment, voice for emotional intensity
            text_weight = 0.7
            voice_weight = 0.3
            
            # Voice-based sentiment adjustment
            voice_positive = voice_emotions.joy + voice_emotions.excitement
            voice_negative = voice_emotions.anger + voice_emotions.sadness + voice_emotions.fear
            
            # Combine scores
            combined_positive = (text_sentiment.positive * text_weight + 
                               voice_positive * voice_weight)
            combined_negative = (text_sentiment.negative * text_weight + 
                               voice_negative * voice_weight)
            
            # Recalculate neutral and compound
            total = combined_positive + combined_negative
            combined_neutral = max(0, 1 - total)
            combined_compound = combined_positive - combined_negative
            
            # Confidence based on agreement between text and voice
            agreement = 1 - abs(text_sentiment.compound - (voice_positive - voice_negative))
            combined_confidence = (text_sentiment.confidence + agreement) / 2
            
            return SentimentScore(
                positive=combined_positive,
                negative=combined_negative,
                neutral=combined_neutral,
                compound=combined_compound,
                confidence=combined_confidence
            )
            
        except Exception as e:
            logger.error(f"❌ Sentiment combination failed: {e}")
            return text_sentiment
    
    def _combine_emotion_profiles(self, text_emotions: EmotionProfile, voice_emotions: EmotionProfile) -> EmotionProfile:
        """Combine text and voice-based emotion analysis"""
        try:
            combined = EmotionProfile()
            
            # Combine each emotion with appropriate weighting
            emotion_weights = {
                'joy': (0.6, 0.4),  # Text slightly more important for joy
                'sadness': (0.7, 0.3),  # Text more important for sadness
                'anger': (0.5, 0.5),  # Equal weighting for anger
                'fear': (0.6, 0.4),  # Text slightly more important
                'surprise': (0.8, 0.2),  # Text much more important
                'disgust': (0.8, 0.2),  # Text much more important
                'excitement': (0.3, 0.7),  # Voice more important for excitement
                'frustration': (0.6, 0.4),  # Text slightly more important
                'confidence_level': (0.4, 0.6),  # Voice more important for confidence
                'stress_indicators': (0.3, 0.7)  # Voice more important for stress
            }
            
            for emotion, (text_weight, voice_weight) in emotion_weights.items():
                text_score = getattr(text_emotions, emotion, 0.0)
                voice_score = getattr(voice_emotions, emotion, 0.0)
                
                combined_score = text_score * text_weight + voice_score * voice_weight
                setattr(combined, emotion, combined_score)
            
            return combined
            
        except Exception as e:
            logger.error(f"❌ Emotion combination failed: {e}")
            return text_emotions
    
    def _update_speaker_mood(self, session_id: str, speaker_id: str, 
                           sentiment: SentimentScore, emotions: EmotionProfile, timestamp: float):
        """Update speaker mood tracking"""
        with self.analysis_lock:
            if session_id not in self.speaker_moods:
                self.speaker_moods[session_id] = {}
            
            if speaker_id not in self.speaker_moods[session_id]:
                self.speaker_moods[session_id][speaker_id] = SpeakerMood(speaker_id=speaker_id)
            
            mood = self.speaker_moods[session_id][speaker_id]
            
            # Update current state
            mood.current_sentiment = sentiment
            mood.current_emotions = emotions
            mood.last_updated = timestamp
            
            # Add to history
            mood.sentiment_history.append((timestamp, sentiment.compound))
            mood.emotion_history.append((timestamp, emotions))
            
            # Calculate mood trajectory
            mood.mood_trajectory = self._calculate_mood_trajectory(mood.sentiment_history)
            
            # Update engagement and energy levels
            mood.engagement_level = self._calculate_engagement_level(sentiment, emotions)
            mood.energy_level = self._calculate_energy_level(emotions)
    
    def _update_meeting_analysis(self, session_id: str, speaker_id: str,
                               sentiment: SentimentScore, emotions: EmotionProfile, timestamp: float):
        """Update meeting-level mood analysis"""
        with self.analysis_lock:
            if session_id not in self.meeting_analyses:
                self.meeting_analyses[session_id] = MeetingMoodAnalysis(session_id=session_id)
            
            analysis = self.meeting_analyses[session_id]
            
            # Update overall sentiment (weighted average)
            self._update_overall_sentiment(analysis, sentiment)
            
            # Track emotional peaks
            self._track_emotional_peaks(analysis, emotions, timestamp)
            
            # Update engagement distribution
            if session_id in self.speaker_moods and speaker_id in self.speaker_moods[session_id]:
                speaker_mood = self.speaker_moods[session_id][speaker_id]
                analysis.engagement_distribution[speaker_id] = speaker_mood.engagement_level
            
            # Detect tension indicators
            self._detect_tension_indicators(analysis, sentiment, emotions, timestamp)
            
            # Track positive moments
            self._track_positive_moments(analysis, sentiment, emotions, timestamp)
    
    def _calculate_mood_trajectory(self, sentiment_history: deque) -> str:
        """Calculate mood trajectory from sentiment history"""
        try:
            if len(sentiment_history) < 3:
                return "neutral"
            
            recent_sentiments = [score for _, score in list(sentiment_history)[-5:]]
            
            # Calculate trend
            if len(recent_sentiments) >= 3:
                early_avg = np.mean(recent_sentiments[:len(recent_sentiments)//2])
                late_avg = np.mean(recent_sentiments[len(recent_sentiments)//2:])
                
                diff = late_avg - early_avg
                
                if diff > 0.1:
                    return "improving"
                elif diff < -0.1:
                    return "declining"
                else:
                    return "stable"
            
            return "neutral"
            
        except Exception:
            return "neutral"
    
    def _calculate_engagement_level(self, sentiment: SentimentScore, emotions: EmotionProfile) -> float:
        """Calculate speaker engagement level"""
        try:
            # High engagement indicators
            engagement_score = 0.0
            
            # Positive sentiment indicates engagement
            engagement_score += sentiment.positive * 0.3
            
            # Strong emotions (positive or negative) indicate engagement
            emotion_intensity = (emotions.joy + emotions.excitement + emotions.anger + 
                               emotions.surprise + emotions.frustration)
            engagement_score += min(1.0, emotion_intensity) * 0.4
            
            # High confidence indicates engagement
            engagement_score += emotions.confidence_level * 0.3
            
            return min(1.0, engagement_score)
            
        except Exception:
            return 0.5
    
    def _calculate_energy_level(self, emotions: EmotionProfile) -> float:
        """Calculate speaker energy level"""
        try:
            # High energy emotions
            high_energy = emotions.excitement + emotions.joy + emotions.anger
            
            # Low energy emotions
            low_energy = emotions.sadness + emotions.fear
            
            # Base energy level
            energy_level = 0.5 + (high_energy - low_energy) * 0.5
            
            return max(0.0, min(1.0, energy_level))
            
        except Exception:
            return 0.5
    
    def get_session_mood_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive mood summary for a session"""
        try:
            with self.analysis_lock:
                summary = {
                    'session_id': session_id,
                    'timestamp': time.time(),
                    'speaker_moods': {},
                    'meeting_analysis': None,
                    'overall_statistics': {}
                }
                
                # Speaker mood summaries
                if session_id in self.speaker_moods:
                    for speaker_id, mood in self.speaker_moods[session_id].items():
                        summary['speaker_moods'][speaker_id] = {
                            'current_sentiment': mood.current_sentiment.compound,
                            'mood_trajectory': mood.mood_trajectory,
                            'engagement_level': mood.engagement_level,
                            'energy_level': mood.energy_level,
                            'dominant_emotions': self._get_dominant_emotions(mood.current_emotions)
                        }
                
                # Meeting analysis
                if session_id in self.meeting_analyses:
                    analysis = self.meeting_analyses[session_id]
                    summary['meeting_analysis'] = {
                        'overall_sentiment': analysis.overall_sentiment.compound,
                        'meeting_energy': analysis.meeting_energy,
                        'emotional_peaks_count': len(analysis.emotional_peaks),
                        'tension_indicators_count': len(analysis.tension_indicators),
                        'positive_moments_count': len(analysis.positive_moments)
                    }
                
                # Overall statistics
                if session_id in self.speaker_moods:
                    all_sentiments = [mood.current_sentiment.compound 
                                    for mood in self.speaker_moods[session_id].values()]
                    all_engagement = [mood.engagement_level 
                                    for mood in self.speaker_moods[session_id].values()]
                    
                    summary['overall_statistics'] = {
                        'average_sentiment': np.mean(all_sentiments) if all_sentiments else 0,
                        'sentiment_variance': np.var(all_sentiments) if all_sentiments else 0,
                        'average_engagement': np.mean(all_engagement) if all_engagement else 0,
                        'total_speakers': len(self.speaker_moods[session_id])
                    }
                
                return summary
                
        except Exception as e:
            logger.error(f"❌ Mood summary generation failed: {e}")
            return {'session_id': session_id, 'error': str(e)}
    
    def _get_dominant_emotions(self, emotions: EmotionProfile) -> List[str]:
        """Get dominant emotions for a speaker"""
        emotion_scores = {
            'joy': emotions.joy,
            'sadness': emotions.sadness,
            'anger': emotions.anger,
            'fear': emotions.fear,
            'excitement': emotions.excitement,
            'frustration': emotions.frustration
        }
        
        # Return emotions above threshold, sorted by intensity
        dominant = [(emotion, score) for emotion, score in emotion_scores.items() if score > 0.3]
        dominant.sort(key=lambda x: x[1], reverse=True)
        
        return [emotion for emotion, _ in dominant[:3]]  # Top 3 emotions
    
    # Lexicon and pattern loading methods
    def _load_positive_lexicon(self) -> set:
        """Load positive sentiment words"""
        return {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome',
            'love', 'like', 'enjoy', 'happy', 'pleased', 'satisfied', 'delighted',
            'perfect', 'brilliant', 'outstanding', 'superb', 'marvelous', 'terrific',
            'yes', 'definitely', 'absolutely', 'certainly', 'sure', 'agree',
            'success', 'win', 'achievement', 'accomplish', 'effective', 'efficient'
        }
    
    def _load_negative_lexicon(self) -> set:
        """Load negative sentiment words"""
        return {
            'bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate', 'dislike',
            'sad', 'angry', 'frustrated', 'annoyed', 'disappointed', 'upset', 'worried',
            'problem', 'issue', 'trouble', 'difficult', 'hard', 'impossible', 'wrong',
            'no', 'never', 'refuse', 'reject', 'disagree', 'oppose', 'against',
            'fail', 'failure', 'lose', 'loss', 'mistake', 'error', 'broken'
        }
    
    def _load_emotion_patterns(self) -> Dict[str, List]:
        """Load emotion detection patterns"""
        return {
            'joy': ['happy', 'glad', 'joyful', 'cheerful', 'delighted', 'elated'],
            'sadness': ['sad', 'depressed', 'down', 'blue', 'melancholy', 'gloomy'],
            'anger': ['angry', 'mad', 'furious', 'rage', 'irritated', 'annoyed'],
            'fear': ['afraid', 'scared', 'fearful', 'worried', 'anxious', 'nervous'],
            'surprise': ['surprised', 'shocked', 'amazed', 'astonished', 'unexpected'],
            'disgust': ['disgusting', 'gross', 'revolting', 'repulsive', 'sick'],
            'excitement': ['excited', 'thrilled', 'enthusiastic', 'eager', 'pumped'],
            'frustration': ['frustrated', 'irritated', 'exasperated', 'aggravated']
        }
    
    def _load_intensifiers(self) -> Dict[str, float]:
        """Load intensity modifiers"""
        return {
            'very': 1.5, 'really': 1.4, 'extremely': 2.0, 'incredibly': 1.8,
            'absolutely': 1.7, 'completely': 1.6, 'totally': 1.5, 'quite': 1.2,
            'rather': 1.1, 'somewhat': 0.8, 'slightly': 0.7, 'barely': 0.5
        }
    
    def _create_voice_emotion_mapping(self) -> Dict[str, Dict[str, Any]]:
        """Create voice feature to emotion mapping"""
        return {
            'excitement': {'pitch_min': 200, 'energy_min': 0.1, 'jitter_max': 0.025},
            'joy': {'pitch_min': 150, 'energy_min': 0.05, 'jitter_max': 0.02},
            'anger': {'energy_min': 0.15, 'jitter_min': 0.03},
            'sadness': {'pitch_max': 120, 'energy_max': 0.05},
            'fear': {'jitter_min': 0.025, 'pitch_std_min': 30}
        }
    
    # Helper methods for text processing
    def _preprocess_text(self, text: str) -> List[str]:
        """Preprocess text for sentiment analysis"""
        # Convert to lowercase and split into words
        words = re.findall(r'\b\w+\b', text.lower())
        return words
    
    def _check_negation_context(self, words: List[str], index: int) -> bool:
        """Check if word is in negation context"""
        # Look for negation words within 3 positions before current word
        start = max(0, index - 3)
        context = words[start:index]
        return any(word in self.negation_words for word in context)
    
    def _check_intensifiers(self, words: List[str], index: int) -> float:
        """Check for intensity modifiers"""
        # Look for intensifiers within 2 positions before current word
        if index > 0 and words[index - 1] in self.intensifiers:
            return self.intensifiers[words[index - 1]]
        if index > 1 and words[index - 2] in self.intensifiers:
            return self.intensifiers[words[index - 2]] * 0.8  # Reduced effect at distance
        return 1.0
    
    def _get_word_sentiment(self, word: str) -> float:
        """Get sentiment score for a word"""
        if word in self.positive_words:
            return 1.0
        elif word in self.negative_words:
            return -1.0
        else:
            return 0.0
    
    def _analyze_confidence_indicators(self, text: str) -> float:
        """Analyze confidence indicators in text"""
        confidence_patterns = [
            'i think', 'i believe', 'i know', 'definitely', 'certainly', 'sure',
            'confident', 'positive', 'absolutely', 'without doubt'
        ]
        
        uncertainty_patterns = [
            'maybe', 'perhaps', 'might', 'could be', 'not sure', 'uncertain',
            'i guess', 'probably', 'possibly', 'i suppose'
        ]
        
        confidence_score = sum(0.2 for pattern in confidence_patterns if pattern in text)
        uncertainty_score = sum(0.2 for pattern in uncertainty_patterns if pattern in text)
        
        return max(0, min(1, 0.5 + confidence_score - uncertainty_score))
    
    def _analyze_stress_indicators(self, text: str) -> float:
        """Analyze stress indicators in text"""
        stress_patterns = [
            'stressed', 'pressure', 'overwhelmed', 'busy', 'rushed', 'deadline',
            'urgent', 'crisis', 'problem', 'difficult', 'hard', 'struggle'
        ]
        
        stress_score = sum(0.15 for pattern in stress_patterns if pattern in text)
        return min(1.0, stress_score)
    
    # Helper methods for meeting analysis updates
    def _update_overall_sentiment(self, analysis: MeetingMoodAnalysis, sentiment: SentimentScore):
        """Update overall meeting sentiment"""
        # Simple exponential moving average
        alpha = 0.1
        current = analysis.overall_sentiment
        
        current.positive = alpha * sentiment.positive + (1 - alpha) * current.positive
        current.negative = alpha * sentiment.negative + (1 - alpha) * current.negative
        current.neutral = alpha * sentiment.neutral + (1 - alpha) * current.neutral
        current.compound = alpha * sentiment.compound + (1 - alpha) * current.compound
        current.confidence = alpha * sentiment.confidence + (1 - alpha) * current.confidence
    
    def _track_emotional_peaks(self, analysis: MeetingMoodAnalysis, emotions: EmotionProfile, timestamp: float):
        """Track significant emotional peaks"""
        # Check for strong emotions
        emotion_threshold = 0.7
        
        strong_emotions = []
        for emotion_name in ['joy', 'anger', 'sadness', 'excitement', 'fear']:
            emotion_value = getattr(emotions, emotion_name, 0)
            if emotion_value > emotion_threshold:
                strong_emotions.append((emotion_name, emotion_value))
        
        if strong_emotions:
            # Record the strongest emotion
            strongest = max(strong_emotions, key=lambda x: x[1])
            analysis.emotional_peaks.append((timestamp, strongest[0], strongest[1]))
            
            # Keep only recent peaks (last 100)
            if len(analysis.emotional_peaks) > 100:
                analysis.emotional_peaks = analysis.emotional_peaks[-100:]
    
    def _detect_tension_indicators(self, analysis: MeetingMoodAnalysis, 
                                 sentiment: SentimentScore, emotions: EmotionProfile, timestamp: float):
        """Detect tension indicators in the meeting"""
        # High negative sentiment
        if sentiment.negative > 0.6:
            analysis.tension_indicators.append((timestamp, "high_negative_sentiment"))
        
        # Strong anger or frustration
        if emotions.anger > 0.5 or emotions.frustration > 0.5:
            analysis.tension_indicators.append((timestamp, "anger_frustration_detected"))
        
        # High stress indicators
        if emotions.stress_indicators > 0.6:
            analysis.tension_indicators.append((timestamp, "high_stress_detected"))
        
        # Keep only recent indicators
        if len(analysis.tension_indicators) > 50:
            analysis.tension_indicators = analysis.tension_indicators[-50:]
    
    def _track_positive_moments(self, analysis: MeetingMoodAnalysis,
                              sentiment: SentimentScore, emotions: EmotionProfile, timestamp: float):
        """Track positive moments in the meeting"""
        # High positive sentiment
        if sentiment.positive > 0.7:
            analysis.positive_moments.append((timestamp, "high_positive_sentiment"))
        
        # Strong joy or excitement
        if emotions.joy > 0.6 or emotions.excitement > 0.6:
            analysis.positive_moments.append((timestamp, "joy_excitement_detected"))
        
        # Keep only recent moments
        if len(analysis.positive_moments) > 50:
            analysis.positive_moments = analysis.positive_moments[-50:]
    
    def clear_session_data(self, session_id: str):
        """Clear sentiment data for a session"""
        with self.analysis_lock:
            if session_id in self.speaker_moods:
                del self.speaker_moods[session_id]
            if session_id in self.meeting_analyses:
                del self.meeting_analyses[session_id]
            logger.info(f"🗑️ Cleared sentiment data for session {session_id}")

# Global sentiment service
_global_sentiment_service = None
_sentiment_lock = threading.Lock()

def get_sentiment_service() -> SentimentAnalysisService:
    """Get global sentiment analysis service"""
    global _global_sentiment_service
    
    if _global_sentiment_service is None:
        with _sentiment_lock:
            if _global_sentiment_service is None:
                _global_sentiment_service = SentimentAnalysisService()
    
    return _global_sentiment_service

logger.info("😊 Sentiment Analysis Service initialized")