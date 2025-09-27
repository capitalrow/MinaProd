# services/conversation_analytics.py
"""
Conversation Analytics Engine
Advanced conversation flow analysis, meeting insights, action item extraction,
and comprehensive session analytics with NLP and machine learning capabilities.
"""

import logging
import time
import threading
import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Set
from enum import Enum
import numpy as np
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ConversationState(Enum):
    """Conversation flow states"""
    INTRODUCTION = "introduction"
    DISCUSSION = "discussion"
    DECISION = "decision"
    ACTION_PLANNING = "action_planning"
    CONCLUSION = "conclusion"
    BREAK = "break"
    UNKNOWN = "unknown"

class SentimentTrend(Enum):
    """Sentiment trend directions"""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"

class UrgencyLevel(Enum):
    """Action item urgency levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ActionItem:
    """Extracted action item"""
    id: str
    text: str
    assigned_to: Optional[str] = None
    deadline: Optional[str] = None
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM
    confidence: float = 0.0
    context: str = ""
    timestamp: float = field(default_factory=time.time)
    completed: bool = False
    source_segment_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'text': self.text,
            'assigned_to': self.assigned_to,
            'deadline': self.deadline,
            'urgency': self.urgency.value,
            'confidence': self.confidence,
            'context': self.context,
            'timestamp': self.timestamp,
            'completed': self.completed,
            'source_segment_id': self.source_segment_id
        }

@dataclass
class MeetingInsight:
    """Meeting insight or key point"""
    id: str
    title: str
    description: str
    category: str  # decision, problem, opportunity, etc.
    participants: List[str] = field(default_factory=list)
    confidence: float = 0.0
    importance: float = 0.0
    timestamp: float = field(default_factory=time.time)
    related_segments: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'participants': self.participants,
            'confidence': self.confidence,
            'importance': self.importance,
            'timestamp': self.timestamp,
            'related_segments': self.related_segments,
            'tags': self.tags
        }

@dataclass
class ConversationFlow:
    """Conversation flow analysis"""
    current_state: ConversationState = ConversationState.UNKNOWN
    state_history: List[Tuple[ConversationState, float]] = field(default_factory=list)
    topic_transitions: List[Dict[str, Any]] = field(default_factory=list)
    engagement_levels: Dict[str, List[float]] = field(default_factory=dict)
    interruption_patterns: List[Dict[str, Any]] = field(default_factory=list)
    speaking_time_distribution: Dict[str, float] = field(default_factory=dict)
    turn_taking_patterns: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class SentimentAnalysis:
    """Sentiment analysis results"""
    overall_sentiment: float = 0.0
    sentiment_trend: SentimentTrend = SentimentTrend.STABLE
    speaker_sentiments: Dict[str, float] = field(default_factory=dict)
    sentiment_timeline: List[Tuple[float, float]] = field(default_factory=list)
    emotional_peaks: List[Dict[str, Any]] = field(default_factory=list)
    conflict_indicators: List[Dict[str, Any]] = field(default_factory=list)

class TopicAnalyzer:
    """Analyze conversation topics and themes"""
    
    def __init__(self):
        self.topic_keywords = {
            'planning': ['plan', 'schedule', 'timeline', 'roadmap', 'strategy', 'goal', 'objective'],
            'technical': ['code', 'system', 'database', 'api', 'architecture', 'development', 'bug', 'feature'],
            'business': ['revenue', 'profit', 'customer', 'market', 'sales', 'budget', 'investment'],
            'operations': ['process', 'workflow', 'efficiency', 'optimization', 'procedure', 'standard'],
            'hr': ['team', 'hiring', 'training', 'performance', 'evaluation', 'skills', 'onboarding'],
            'finance': ['cost', 'budget', 'expense', 'funding', 'financial', 'roi', 'investment'],
            'product': ['product', 'feature', 'user', 'customer', 'feedback', 'requirements', 'design'],
            'marketing': ['campaign', 'brand', 'promotion', 'advertising', 'content', 'social media']
        }
        
        self.current_topics = defaultdict(float)
        self.topic_transitions = []
        self.topic_timeline = []
    
    def analyze_segment_topics(self, text: str, timestamp: float) -> Dict[str, float]:
        """Analyze topics in a text segment"""
        text_lower = text.lower()
        segment_topics = {}
        
        for topic, keywords in self.topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                # Normalize by text length
                normalized_score = score / max(len(text.split()), 1)
                segment_topics[topic] = normalized_score
        
        # Update current topics with decay
        decay_factor = 0.9
        for topic in self.current_topics:
            self.current_topics[topic] *= decay_factor
        
        # Add new topics
        for topic, score in segment_topics.items():
            self.current_topics[topic] += score
        
        # Track topic timeline
        self.topic_timeline.append({
            'timestamp': timestamp,
            'topics': dict(segment_topics),
            'dominant_topic': max(segment_topics.items(), key=lambda x: x[1])[0] if segment_topics else None
        })
        
        return segment_topics
    
    def detect_topic_transitions(self) -> List[Dict[str, Any]]:
        """Detect when conversation topics change"""
        if len(self.topic_timeline) < 2:
            return []
        
        transitions = []
        window_size = 3  # Compare topics over 3 segments
        
        for i in range(window_size, len(self.topic_timeline)):
            current_window = self.topic_timeline[i-window_size:i]
            next_segment = self.topic_timeline[i]
            
            # Calculate topic stability in current window
            current_topics = defaultdict(float)
            for segment in current_window:
                for topic, score in segment['topics'].items():
                    current_topics[topic] += score
            
            # Normalize
            total_score = sum(current_topics.values())
            if total_score > 0:
                for topic in current_topics:
                    current_topics[topic] /= total_score
            
            # Compare with next segment
            next_topics = next_segment['topics']
            total_next = sum(next_topics.values())
            if total_next > 0:
                for topic in next_topics:
                    next_topics[topic] /= total_next
            
            # Calculate topic shift
            topic_shift = 0.0
            all_topics = set(current_topics.keys()) | set(next_topics.keys())
            
            for topic in all_topics:
                current_score = current_topics.get(topic, 0)
                next_score = next_topics.get(topic, 0)
                topic_shift += abs(current_score - next_score)
            
            # If significant shift, record transition
            if topic_shift > 0.5:  # Threshold for topic change
                old_dominant = max(current_topics.items(), key=lambda x: x[1])[0] if current_topics else None
                new_dominant = max(next_topics.items(), key=lambda x: x[1])[0] if next_topics else None
                
                if old_dominant != new_dominant:
                    transitions.append({
                        'timestamp': next_segment['timestamp'],
                        'from_topic': old_dominant,
                        'to_topic': new_dominant,
                        'shift_magnitude': topic_shift,
                        'context': f"Topic changed from {old_dominant} to {new_dominant}"
                    })
        
        return transitions

class ActionItemExtractor:
    """Extract action items from conversation"""
    
    def __init__(self):
        # Patterns for identifying action items
        self.action_patterns = [
            r'(?:we|I|you|they)\s+(?:need to|should|must|will|have to|going to)\s+(.+)',
            r'(?:let\'s|let us)\s+(.+)',
            r'(?:action item|todo|task|assignment):\s*(.+)',
            r'(?:by|before|until)\s+(.+?),?\s+(?:we|I|you|they)\s+(?:need|should|must|will)\s+(.+)',
            r'(?:we|I|you|they)\s+(?:need|should|must|will)\s+(.+?)\s+(?:by|before|until)\s+(.+)',
            r'(?:assigned to|responsible for|owns)\s+(.+)',
            r'(?:deadline|due date|target date):\s*(.+)',
        ]
        
        # Deadline patterns
        self.deadline_patterns = [
            r'(?:by|before|until|due)\s+(today|tomorrow|this week|next week|end of week|eow)',
            r'(?:by|before|until|due)\s+(\d{1,2}[/-]\d{1,2}[/-]?\d{0,4})',
            r'(?:by|before|until|due)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(?:by|before|until|due)\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}',
            r'in\s+(\d+)\s+(days?|weeks?|months?)',
        ]
        
        # Urgency indicators
        self.urgency_indicators = {
            UrgencyLevel.CRITICAL: ['urgent', 'critical', 'asap', 'immediately', 'emergency'],
            UrgencyLevel.HIGH: ['important', 'priority', 'high priority', 'soon', 'quickly'],
            UrgencyLevel.MEDIUM: ['should', 'need to', 'when possible'],
            UrgencyLevel.LOW: ['eventually', 'when time permits', 'nice to have']
        }
    
    def extract_from_segment(self, text: str, speaker: str, timestamp: float, segment_id: str) -> List[ActionItem]:
        """Extract action items from a text segment"""
        actions = []
        text_lower = text.lower()
        
        # Try each action pattern
        for pattern in self.action_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                action_text = match.group(1) if match.groups() else match.group(0)
                action_text = action_text.strip()
                
                if len(action_text) > 5:  # Filter out very short matches
                    action = ActionItem(
                        id=f"action_{segment_id}_{len(actions)}",
                        text=action_text,
                        assigned_to=self._extract_assignee(text, action_text),
                        deadline=self._extract_deadline(text),
                        urgency=self._determine_urgency(text_lower),
                        confidence=self._calculate_confidence(text, action_text),
                        context=text[:100] + "..." if len(text) > 100 else text,
                        timestamp=timestamp,
                        source_segment_id=segment_id
                    )
                    actions.append(action)
        
        return actions
    
    def _extract_assignee(self, text: str, action_text: str) -> Optional[str]:
        """Extract who is assigned to the action"""
        # Look for assignment patterns
        assign_patterns = [
            r'assigned to\s+(\w+)',
            r'(\w+)\s+will\s+',
            r'(\w+)\s+should\s+',
            r'(\w+)\s+needs? to\s+'
        ]
        
        for pattern in assign_patterns:
            match = re.search(pattern, text.lower())
            if match:
                assignee = match.group(1)
                # Filter out common words
                if assignee not in ['we', 'they', 'someone', 'anyone']:
                    return assignee.capitalize()
        
        return None
    
    def _extract_deadline(self, text: str) -> Optional[str]:
        """Extract deadline from text"""
        for pattern in self.deadline_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1)
        return None
    
    def _determine_urgency(self, text_lower: str) -> UrgencyLevel:
        """Determine urgency level from text"""
        for urgency, indicators in self.urgency_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                return urgency
        return UrgencyLevel.MEDIUM
    
    def _calculate_confidence(self, text: str, action_text: str) -> float:
        """Calculate confidence score for extracted action"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for clear action verbs
        action_verbs = ['will', 'must', 'need', 'should', 'assigned', 'responsible']
        if any(verb in text.lower() for verb in action_verbs):
            confidence += 0.2
        
        # Boost for specific details
        if self._extract_deadline(text):
            confidence += 0.15
        if self._extract_assignee(text, action_text):
            confidence += 0.15
        
        return min(1.0, confidence)

class MeetingInsightGenerator:
    """Generate meeting insights and key points"""
    
    def __init__(self):
        self.insight_categories = {
            'decision': ['decided', 'agreed', 'conclusion', 'resolved', 'final'],
            'problem': ['issue', 'problem', 'concern', 'challenge', 'blocker'],
            'opportunity': ['opportunity', 'potential', 'advantage', 'benefit'],
            'risk': ['risk', 'danger', 'threat', 'vulnerability', 'concern'],
            'milestone': ['milestone', 'achievement', 'completed', 'delivered'],
            'requirement': ['requirement', 'must have', 'necessary', 'essential']
        }
        
        self.insights = []
    
    def generate_insights(self, segments: List[Dict[str, Any]]) -> List[MeetingInsight]:
        """Generate insights from conversation segments"""
        insights = []
        
        # Analyze segments for patterns
        for i, segment in enumerate(segments):
            text = segment.get('text', '')
            speaker = segment.get('speaker', 'Unknown')
            timestamp = segment.get('timestamp', time.time())
            
            # Check for insight patterns
            for category, keywords in self.insight_categories.items():
                if any(keyword in text.lower() for keyword in keywords):
                    insight = self._create_insight(
                        text, speaker, timestamp, category, segment.get('id', f'seg_{i}')
                    )
                    if insight:
                        insights.append(insight)
        
        # Merge related insights
        insights = self._merge_related_insights(insights)
        
        # Score insights by importance
        for insight in insights:
            insight.importance = self._calculate_importance(insight, segments)
        
        return sorted(insights, key=lambda x: x.importance, reverse=True)
    
    def _create_insight(self, text: str, speaker: str, timestamp: float, category: str, segment_id: str) -> Optional[MeetingInsight]:
        """Create insight from text segment"""
        # Extract key phrases
        sentences = text.split('.')
        key_sentence = max(sentences, key=len) if sentences else text
        
        if len(key_sentence.strip()) < 10:
            return None
        
        insight_id = f"insight_{int(timestamp)}_{len(self.insights)}"
        
        return MeetingInsight(
            id=insight_id,
            title=self._generate_title(key_sentence, category),
            description=key_sentence.strip(),
            category=category,
            participants=[speaker],
            confidence=0.7,  # Base confidence
            timestamp=timestamp,
            related_segments=[segment_id],
            tags=self._extract_tags(text)
        )
    
    def _generate_title(self, text: str, category: str) -> str:
        """Generate title for insight"""
        # Simple title generation
        words = text.split()[:8]  # First 8 words
        title = ' '.join(words)
        if len(title) > 50:
            title = title[:47] + "..."
        return f"{category.title()}: {title}"
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text"""
        # Simple tag extraction based on common terms
        tag_patterns = {
            'technical': ['system', 'code', 'api', 'database', 'software'],
            'timeline': ['deadline', 'schedule', 'timeline', 'date'],
            'budget': ['cost', 'budget', 'money', 'financial'],
            'team': ['team', 'people', 'staff', 'resource'],
            'urgent': ['urgent', 'critical', 'asap', 'important']
        }
        
        tags = []
        text_lower = text.lower()
        
        for tag, keywords in tag_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        return tags
    
    def _merge_related_insights(self, insights: List[MeetingInsight]) -> List[MeetingInsight]:
        """Merge insights that are similar or related"""
        # Simple similarity check based on overlapping words
        merged = []
        used_indices = set()
        
        for i, insight1 in enumerate(insights):
            if i in used_indices:
                continue
            
            # Look for similar insights
            similar_insights = [insight1]
            
            for j, insight2 in enumerate(insights[i+1:], i+1):
                if j in used_indices:
                    continue
                
                if self._are_insights_similar(insight1, insight2):
                    similar_insights.append(insight2)
                    used_indices.add(j)
            
            # Merge if multiple similar insights found
            if len(similar_insights) > 1:
                merged_insight = self._merge_insights(similar_insights)
                merged.append(merged_insight)
            else:
                merged.append(insight1)
            
            used_indices.add(i)
        
        return merged
    
    def _are_insights_similar(self, insight1: MeetingInsight, insight2: MeetingInsight) -> bool:
        """Check if two insights are similar"""
        # Same category
        if insight1.category != insight2.category:
            return False
        
        # Similar content (simple word overlap)
        words1 = set(insight1.description.lower().split())
        words2 = set(insight2.description.lower().split())
        overlap = len(words1 & words2) / max(len(words1), len(words2))
        
        return overlap > 0.4  # 40% word overlap threshold
    
    def _merge_insights(self, insights: List[MeetingInsight]) -> MeetingInsight:
        """Merge multiple related insights"""
        base_insight = insights[0]
        
        # Combine descriptions
        descriptions = [insight.description for insight in insights]
        combined_description = ". ".join(descriptions)
        
        # Combine participants
        all_participants = set()
        for insight in insights:
            all_participants.update(insight.participants)
        
        # Combine related segments
        all_segments = []
        for insight in insights:
            all_segments.extend(insight.related_segments)
        
        # Combine tags
        all_tags = set()
        for insight in insights:
            all_tags.update(insight.tags)
        
        return MeetingInsight(
            id=base_insight.id,
            title=f"Combined: {base_insight.title}",
            description=combined_description,
            category=base_insight.category,
            participants=list(all_participants),
            confidence=max(insight.confidence for insight in insights),
            timestamp=base_insight.timestamp,
            related_segments=all_segments,
            tags=list(all_tags)
        )
    
    def _calculate_importance(self, insight: MeetingInsight, segments: List[Dict[str, Any]]) -> float:
        """Calculate importance score for insight"""
        importance = 0.5  # Base importance
        
        # More participants = more important
        importance += len(insight.participants) * 0.1
        
        # More related segments = more important
        importance += len(insight.related_segments) * 0.05
        
        # Category-based importance
        category_weights = {
            'decision': 0.9,
            'problem': 0.8,
            'risk': 0.7,
            'opportunity': 0.6,
            'milestone': 0.5,
            'requirement': 0.4
        }
        importance *= category_weights.get(insight.category, 0.5)
        
        # High confidence = more important
        importance *= insight.confidence
        
        return min(1.0, importance)

class ConversationAnalytics:
    """Main conversation analytics engine"""
    
    def __init__(self):
        self.topic_analyzer = TopicAnalyzer()
        self.action_extractor = ActionItemExtractor()
        self.insight_generator = MeetingInsightGenerator()
        
        # Session data
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.segments_buffer: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Analytics results
        self.analytics_cache: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
        logger.info("🔍 Conversation Analytics Engine initialized")
    
    def create_session(self, session_id: str, **metadata) -> Dict[str, Any]:
        """Create new analytics session"""
        with self.lock:
            session_info = {
                'id': session_id,
                'created_at': time.time(),
                'metadata': metadata,
                'segments_processed': 0,
                'action_items': [],
                'insights': [],
                'conversation_flow': ConversationFlow(),
                'sentiment_analysis': SentimentAnalysis(),
                'speakers': set(),
                'topics_detected': set(),
                'last_analysis': 0
            }
            
            self.sessions[session_id] = session_info
            logger.info(f"📊 Created analytics session: {session_id}")
            return session_info
    
    def add_segment(self, session_id: str, segment: Dict[str, Any]) -> Dict[str, Any]:
        """Add conversation segment for analysis"""
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        # Add to buffer
        self.segments_buffer[session_id].append(segment)
        
        # Update session info
        session = self.sessions[session_id]
        session['segments_processed'] += 1
        
        if segment.get('speaker'):
            session['speakers'].add(segment['speaker'])
        
        # Trigger analysis if buffer is large enough or enough time has passed
        should_analyze = (
            len(self.segments_buffer[session_id]) >= 5 or  # Every 5 segments
            time.time() - session['last_analysis'] > 30    # Every 30 seconds
        )
        
        if should_analyze:
            return self.analyze_session(session_id)
        
        return {}
    
    def analyze_session(self, session_id: str) -> Dict[str, Any]:
        """Perform comprehensive session analysis"""
        if session_id not in self.sessions:
            return {}
        
        with self.lock:
            session = self.sessions[session_id]
            segments = self.segments_buffer[session_id]
            
            if not segments:
                return {}
            
            start_time = time.time()
            
            # Perform all analyses
            analysis_results = {
                'session_id': session_id,
                'timestamp': start_time,
                'segments_analyzed': len(segments),
                'topic_analysis': self._analyze_topics(segments),
                'action_items': self._extract_action_items(segments, session_id),
                'insights': self._generate_insights(segments),
                'conversation_flow': self._analyze_conversation_flow(segments, session),
                'sentiment_analysis': self._analyze_sentiment(segments),
                'speaker_analytics': self._analyze_speakers(segments),
                'performance_metrics': {
                    'analysis_time_ms': (time.time() - start_time) * 1000,
                    'segments_per_second': len(segments) / max(time.time() - start_time, 0.001)
                }
            }
            
            # Update session with results
            session['action_items'] = analysis_results['action_items']
            session['insights'] = analysis_results['insights']
            session['conversation_flow'] = analysis_results['conversation_flow']
            session['sentiment_analysis'] = analysis_results['sentiment_analysis']
            session['last_analysis'] = time.time()
            
            # Cache results
            self.analytics_cache[session_id] = analysis_results
            
            # Clear processed segments (keep last 10 for context)
            if len(segments) > 10:
                self.segments_buffer[session_id] = segments[-10:]
            
            logger.info(f"🔍 Analyzed {len(segments)} segments for session {session_id}")
            
            return analysis_results
    
    def _analyze_topics(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze conversation topics"""
        topic_results = {
            'current_topics': {},
            'topic_timeline': [],
            'topic_transitions': [],
            'dominant_topics': []
        }
        
        for segment in segments:
            text = segment.get('text', '')
            timestamp = segment.get('timestamp', time.time())
            
            segment_topics = self.topic_analyzer.analyze_segment_topics(text, timestamp)
            
        # Get current state
        topic_results['current_topics'] = dict(self.topic_analyzer.current_topics)
        topic_results['topic_timeline'] = self.topic_analyzer.topic_timeline[-20:]  # Last 20 entries
        topic_results['topic_transitions'] = self.topic_analyzer.detect_topic_transitions()
        
        # Find dominant topics
        if topic_results['current_topics']:
            sorted_topics = sorted(
                topic_results['current_topics'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            topic_results['dominant_topics'] = sorted_topics[:5]
        
        return topic_results
    
    def _extract_action_items(self, segments: List[Dict[str, Any]], session_id: str) -> List[Dict[str, Any]]:
        """Extract action items from segments"""
        all_actions = []
        
        for segment in segments:
            text = segment.get('text', '')
            speaker = segment.get('speaker', 'Unknown')
            timestamp = segment.get('timestamp', time.time())
            segment_id = segment.get('id', f'seg_{len(all_actions)}')
            
            actions = self.action_extractor.extract_from_segment(
                text, speaker, timestamp, segment_id
            )
            
            all_actions.extend([action.to_dict() for action in actions])
        
        return all_actions
    
    def _generate_insights(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate meeting insights"""
        insights = self.insight_generator.generate_insights(segments)
        return [insight.to_dict() for insight in insights]
    
    def _analyze_conversation_flow(self, segments: List[Dict[str, Any]], session: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation flow patterns"""
        flow_analysis = {
            'current_state': ConversationState.DISCUSSION.value,
            'state_transitions': [],
            'engagement_patterns': {},
            'speaking_distribution': {},
            'turn_taking_analysis': {},
            'interruption_patterns': []
        }
        
        # Analyze speaking time distribution
        speaker_times = defaultdict(float)
        total_time = 0
        
        for i, segment in enumerate(segments):
            speaker = segment.get('speaker', 'Unknown')
            duration = segment.get('duration', 3.0)  # Default 3 seconds
            
            speaker_times[speaker] += duration
            total_time += duration
        
        # Calculate percentages
        if total_time > 0:
            for speaker, time_spent in speaker_times.items():
                flow_analysis['speaking_distribution'][speaker] = {
                    'time_seconds': time_spent,
                    'percentage': (time_spent / total_time) * 100
                }
        
        # Analyze turn-taking patterns
        if len(segments) > 1:
            turns = []
            current_speaker = None
            turn_start = None
            
            for segment in segments:
                speaker = segment.get('speaker', 'Unknown')
                timestamp = segment.get('timestamp', time.time())
                
                if speaker != current_speaker:
                    if current_speaker is not None:
                        turns.append({
                            'speaker': current_speaker,
                            'start': turn_start,
                            'end': timestamp,
                            'duration': timestamp - turn_start
                        })
                    current_speaker = speaker
                    turn_start = timestamp
            
            # Add final turn
            if current_speaker and turn_start:
                turns.append({
                    'speaker': current_speaker,
                    'start': turn_start,
                    'end': segments[-1].get('timestamp', time.time()),
                    'duration': segments[-1].get('timestamp', time.time()) - turn_start
                })
            
            flow_analysis['turn_taking_analysis'] = {
                'total_turns': len(turns),
                'avg_turn_duration': np.mean([turn['duration'] for turn in turns]) if turns else 0,
                'speaker_turn_counts': {
                    speaker: sum(1 for turn in turns if turn['speaker'] == speaker)
                    for speaker in set(turn['speaker'] for turn in turns)
                }
            }
        
        return flow_analysis
    
    def _analyze_sentiment(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze conversation sentiment"""
        sentiment_analysis = {
            'overall_sentiment': 0.0,
            'sentiment_trend': SentimentTrend.STABLE.value,
            'speaker_sentiments': {},
            'sentiment_timeline': [],
            'emotional_highlights': []
        }
        
        sentiment_scores = []
        speaker_sentiments = defaultdict(list)
        
        for segment in segments:
            text = segment.get('text', '')
            speaker = segment.get('speaker', 'Unknown')
            timestamp = segment.get('timestamp', time.time())
            
            # Simple sentiment analysis
            sentiment = self._calculate_segment_sentiment(text)
            sentiment_scores.append(sentiment)
            speaker_sentiments[speaker].append(sentiment)
            
            sentiment_analysis['sentiment_timeline'].append({
                'timestamp': timestamp,
                'sentiment': sentiment,
                'speaker': speaker
            })
        
        # Calculate overall sentiment
        if sentiment_scores:
            sentiment_analysis['overall_sentiment'] = np.mean(sentiment_scores)
        
        # Calculate speaker sentiments
        for speaker, scores in speaker_sentiments.items():
            sentiment_analysis['speaker_sentiments'][speaker] = {
                'average': np.mean(scores),
                'variance': np.var(scores),
                'trend': self._calculate_sentiment_trend(scores)
            }
        
        # Determine overall trend
        if len(sentiment_scores) >= 3:
            sentiment_analysis['sentiment_trend'] = self._calculate_sentiment_trend(sentiment_scores)
        
        return sentiment_analysis
    
    def _analyze_speakers(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze individual speaker patterns"""
        speaker_analysis = {}
        speaker_data = defaultdict(lambda: {
            'total_words': 0,
            'total_time': 0,
            'segments': 0,
            'avg_confidence': 0,
            'topics': defaultdict(int),
            'sentiment_scores': []
        })
        
        for segment in segments:
            speaker = segment.get('speaker', 'Unknown')
            text = segment.get('text', '')
            confidence = segment.get('confidence', 0.8)
            duration = segment.get('duration', 3.0)
            
            data = speaker_data[speaker]
            data['total_words'] += len(text.split())
            data['total_time'] += duration
            data['segments'] += 1
            data['avg_confidence'] = (data['avg_confidence'] * (data['segments'] - 1) + confidence) / data['segments']
            data['sentiment_scores'].append(self._calculate_segment_sentiment(text))
        
        # Process speaker data
        for speaker, data in speaker_data.items():
            speaker_analysis[speaker] = {
                'total_words': data['total_words'],
                'total_time_seconds': data['total_time'],
                'segments_count': data['segments'],
                'words_per_minute': (data['total_words'] / max(data['total_time'] / 60, 0.1)),
                'avg_confidence': data['avg_confidence'],
                'avg_sentiment': np.mean(data['sentiment_scores']) if data['sentiment_scores'] else 0,
                'engagement_score': self._calculate_engagement_score(data)
            }
        
        return speaker_analysis
    
    def _calculate_segment_sentiment(self, text: str) -> float:
        """Calculate sentiment score for text segment"""
        # Simple sentiment calculation
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'perfect', 'love', 'like', 'happy', 'pleased', 'satisfied', 'agree', 'yes', 'awesome', 'fantastic']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'sad', 'angry', 'disappointed', 'frustrated', 'no', 'disagree', 'problem', 'issue', 'concern', 'worry']
        
        text_lower = text.lower()
        words = text_lower.split()
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count + negative_count == 0:
            return 0.0  # Neutral
        
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    def _calculate_sentiment_trend(self, scores: List[float]) -> str:
        """Calculate sentiment trend direction"""
        if len(scores) < 3:
            return SentimentTrend.STABLE.value
        
        # Calculate moving average slope
        recent_scores = scores[-5:]  # Last 5 scores
        early_scores = scores[:5]   # First 5 scores
        
        recent_avg = np.mean(recent_scores)
        early_avg = np.mean(early_scores)
        
        diff = recent_avg - early_avg
        
        if diff > 0.1:
            return SentimentTrend.IMPROVING.value
        elif diff < -0.1:
            return SentimentTrend.DECLINING.value
        else:
            # Check volatility
            variance = np.var(scores)
            if variance > 0.3:
                return SentimentTrend.VOLATILE.value
            else:
                return SentimentTrend.STABLE.value
    
    def _calculate_engagement_score(self, speaker_data: Dict[str, Any]) -> float:
        """Calculate engagement score for a speaker"""
        score = 0.5  # Base score
        
        # More words = higher engagement
        if speaker_data['total_words'] > 100:
            score += 0.2
        
        # Regular participation
        if speaker_data['segments'] > 10:
            score += 0.1
        
        # Good speaking pace
        words_per_minute = speaker_data['total_words'] / max(speaker_data['total_time'] / 60, 0.1)
        if 100 <= words_per_minute <= 200:  # Optimal range
            score += 0.1
        
        # Positive sentiment
        avg_sentiment = np.mean(speaker_data['sentiment_scores']) if speaker_data['sentiment_scores'] else 0
        score += avg_sentiment * 0.1
        
        return min(1.0, score)
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        if session_id not in self.sessions:
            return {}
        
        session = self.sessions[session_id]
        cached_analysis = self.analytics_cache.get(session_id, {})
        
        summary = {
            'session_info': {
                'id': session_id,
                'created_at': session['created_at'],
                'duration_seconds': time.time() - session['created_at'],
                'segments_processed': session['segments_processed'],
                'speakers_count': len(session['speakers']),
                'speakers': list(session['speakers'])
            },
            'key_metrics': {
                'total_action_items': len(session.get('action_items', [])),
                'total_insights': len(session.get('insights', [])),
                'topics_covered': len(session.get('topics_detected', [])),
                'overall_sentiment': cached_analysis.get('sentiment_analysis', {}).get('overall_sentiment', 0)
            },
            'latest_analysis': cached_analysis
        }
        
        return summary
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End session and return final analytics"""
        if session_id not in self.sessions:
            return {}
        
        # Perform final analysis
        final_analysis = self.analyze_session(session_id)
        
        # Get comprehensive summary
        final_summary = self.get_session_summary(session_id)
        
        # Cleanup
        with self.lock:
            del self.sessions[session_id]
            self.segments_buffer.pop(session_id, None)
            # Keep cached results for potential retrieval
        
        logger.info(f"🏁 Ended analytics session: {session_id}")
        
        return {
            'final_analysis': final_analysis,
            'session_summary': final_summary
        }

# Global analytics instance
_analytics_engine = None
_analytics_lock = threading.Lock()

def get_conversation_analytics() -> ConversationAnalytics:
    """Get global conversation analytics instance"""
    global _analytics_engine
    
    with _analytics_lock:
        if _analytics_engine is None:
            _analytics_engine = ConversationAnalytics()
        return _analytics_engine

logger.info("✅ Conversation Analytics module initialized")