"""
🧠 MEETING INSIGHTS SERVICE: Intelligent meeting analysis and action item extraction
Provides comprehensive meeting analysis, action item detection, and decision tracking
"""

import os
import time
import logging
import threading
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
import re
import json
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class ActionItem:
    """Individual action item with metadata"""
    id: str
    text: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "medium"  # low, medium, high, urgent
    status: str = "open"  # open, in_progress, completed, cancelled
    context: str = ""  # surrounding context
    confidence: float = 0.0
    timestamp: float = 0.0
    speaker_id: str = ""
    category: str = "general"  # general, follow_up, decision, research, etc.

@dataclass
class Decision:
    """Meeting decision with tracking"""
    id: str
    decision_text: str
    context: str
    participants: List[str] = field(default_factory=list)
    timestamp: float = 0.0
    confidence: float = 0.0
    decision_type: str = "general"  # general, strategic, operational, technical
    impact_level: str = "medium"  # low, medium, high
    implementation_notes: str = ""

@dataclass
class KeyTopic:
    """Important topic discussed in meeting"""
    topic: str
    mentions_count: int = 0
    speakers: Set[str] = field(default_factory=set)
    time_spent: float = 0.0  # estimated time in seconds
    sentiment_score: float = 0.0
    importance_score: float = 0.0
    first_mention: float = 0.0
    last_mention: float = 0.0
    related_keywords: List[str] = field(default_factory=list)

@dataclass
class MeetingInsights:
    """Comprehensive meeting insights and analysis"""
    session_id: str
    meeting_title: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    total_duration: float = 0.0
    
    # Content analysis
    action_items: List[ActionItem] = field(default_factory=list)
    decisions: List[Decision] = field(default_factory=list)
    key_topics: Dict[str, KeyTopic] = field(default_factory=dict)
    
    # Participation analysis
    speaker_participation: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    speaking_time_distribution: Dict[str, float] = field(default_factory=dict)
    
    # Meeting dynamics
    meeting_type: str = "general"  # standup, planning, review, brainstorm, etc.
    engagement_score: float = 0.0
    productivity_score: float = 0.0
    collaboration_score: float = 0.0
    
    # Summary and insights
    executive_summary: str = ""
    key_outcomes: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    
    # Analytics
    word_cloud_data: Dict[str, int] = field(default_factory=dict)
    sentiment_timeline: List[Tuple[float, float]] = field(default_factory=list)
    topic_timeline: List[Tuple[float, str]] = field(default_factory=list)

class MeetingInsightsService:
    """
    Advanced meeting analysis and insights generation
    """
    
    def __init__(self):
        self.meeting_insights: Dict[str, MeetingInsights] = {}
        self.session_transcripts: Dict[str, List[Dict]] = {}  # session_id -> segments
        self.insights_lock = threading.RLock()
        
        # Analysis patterns and keywords
        self.action_patterns = self._load_action_patterns()
        self.decision_patterns = self._load_decision_patterns()
        self.topic_keywords = self._load_topic_keywords()
        self.meeting_type_indicators = self._load_meeting_type_indicators()
        
        # Analysis configuration
        self.min_topic_mentions = 2
        self.action_confidence_threshold = 0.6
        self.decision_confidence_threshold = 0.7
        
        logger.info("🧠 Meeting Insights Service initialized")
    
    def process_transcript_segment(self, 
                                 session_id: str,
                                 speaker_id: str,
                                 text: str,
                                 timestamp: float,
                                 sentiment_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Process individual transcript segment for insights"""
        try:
            with self.insights_lock:
                # Initialize session if needed
                if session_id not in self.meeting_insights:
                    self._initialize_session(session_id, timestamp)
                
                if session_id not in self.session_transcripts:
                    self.session_transcripts[session_id] = []
                
                # Store segment
                segment = {
                    'speaker_id': speaker_id,
                    'text': text,
                    'timestamp': timestamp,
                    'sentiment': sentiment_data
                }
                self.session_transcripts[session_id].append(segment)
                
                # Extract insights from segment
                insights = {}
                
                # Detect action items
                action_items = self._extract_action_items(text, speaker_id, timestamp)
                if action_items:
                    insights['action_items'] = action_items
                    for action in action_items:
                        self.meeting_insights[session_id].action_items.append(action)
                
                # Detect decisions
                decisions = self._extract_decisions(text, speaker_id, timestamp)
                if decisions:
                    insights['decisions'] = decisions
                    for decision in decisions:
                        self.meeting_insights[session_id].decisions.append(decision)
                
                # Update topics
                topics = self._extract_topics(text, timestamp)
                if topics:
                    insights['topics'] = topics
                    self._update_topics(session_id, topics, speaker_id, timestamp, sentiment_data)
                
                # Update speaker participation
                self._update_speaker_participation(session_id, speaker_id, text, timestamp, sentiment_data)
                
                # Update meeting analytics
                self._update_meeting_analytics(session_id, text, timestamp, sentiment_data)
                
                return insights
                
        except Exception as e:
            logger.error(f"❌ Transcript segment processing failed: {e}")
            return {}
    
    def generate_meeting_summary(self, session_id: str) -> MeetingInsights:
        """Generate comprehensive meeting summary and insights"""
        try:
            with self.insights_lock:
                if session_id not in self.meeting_insights:
                    return MeetingInsights(session_id=session_id)
                
                insights = self.meeting_insights[session_id]
                
                # Calculate final metrics
                self._calculate_final_metrics(session_id, insights)
                
                # Generate executive summary
                insights.executive_summary = self._generate_executive_summary(session_id, insights)
                
                # Extract key outcomes
                insights.key_outcomes = self._extract_key_outcomes(insights)
                
                # Generate next steps
                insights.next_steps = self._generate_next_steps(insights)
                
                # Generate word cloud data
                insights.word_cloud_data = self._generate_word_cloud_data(session_id)
                
                # Classify meeting type
                insights.meeting_type = self._classify_meeting_type(session_id, insights)
                
                logger.info(f"🧠 Generated meeting summary for {session_id}: "
                           f"{len(insights.action_items)} actions, {len(insights.decisions)} decisions")
                
                return insights
                
        except Exception as e:
            logger.error(f"❌ Meeting summary generation failed: {e}")
            return MeetingInsights(session_id=session_id)
    
    def _initialize_session(self, session_id: str, start_time: float):
        """Initialize new meeting session"""
        self.meeting_insights[session_id] = MeetingInsights(
            session_id=session_id,
            start_time=start_time
        )
    
    def _extract_action_items(self, text: str, speaker_id: str, timestamp: float) -> List[ActionItem]:
        """Extract action items from text"""
        try:
            action_items = []
            text_lower = text.lower()
            
            for pattern_info in self.action_patterns:
                pattern = pattern_info['pattern']
                confidence_base = pattern_info['confidence']
                category = pattern_info.get('category', 'general')
                
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    # Extract the action text
                    action_text = self._extract_action_text(text, match)
                    
                    if len(action_text.strip()) < 10:  # Skip very short actions
                        continue
                    
                    # Detect assignee
                    assignee = self._detect_assignee(action_text, speaker_id)
                    
                    # Detect due date
                    due_date = self._detect_due_date(action_text)
                    
                    # Calculate priority
                    priority = self._calculate_action_priority(action_text)
                    
                    # Calculate confidence
                    confidence = self._calculate_action_confidence(action_text, confidence_base)
                    
                    if confidence >= self.action_confidence_threshold:
                        action_item = ActionItem(
                            id=f"action_{session_id}_{len(action_items)}_{int(timestamp)}",
                            text=action_text.strip(),
                            assignee=assignee,
                            due_date=due_date,
                            priority=priority,
                            context=text[:100] + "..." if len(text) > 100 else text,
                            confidence=confidence,
                            timestamp=timestamp,
                            speaker_id=speaker_id,
                            category=category
                        )
                        action_items.append(action_item)
            
            return action_items
            
        except Exception as e:
            logger.error(f"❌ Action item extraction failed: {e}")
            return []
    
    def _extract_decisions(self, text: str, speaker_id: str, timestamp: float) -> List[Decision]:
        """Extract decisions from text"""
        try:
            decisions = []
            text_lower = text.lower()
            
            for pattern_info in self.decision_patterns:
                pattern = pattern_info['pattern']
                confidence_base = pattern_info['confidence']
                decision_type = pattern_info.get('type', 'general')
                
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    # Extract decision text
                    decision_text = self._extract_decision_text(text, match)
                    
                    if len(decision_text.strip()) < 15:  # Skip very short decisions
                        continue
                    
                    # Calculate confidence
                    confidence = self._calculate_decision_confidence(decision_text, confidence_base)
                    
                    if confidence >= self.decision_confidence_threshold:
                        # Detect impact level
                        impact_level = self._detect_impact_level(decision_text)
                        
                        decision = Decision(
                            id=f"decision_{session_id}_{len(decisions)}_{int(timestamp)}",
                            decision_text=decision_text.strip(),
                            context=text[:150] + "..." if len(text) > 150 else text,
                            participants=[speaker_id],
                            timestamp=timestamp,
                            confidence=confidence,
                            decision_type=decision_type,
                            impact_level=impact_level
                        )
                        decisions.append(decision)
            
            return decisions
            
        except Exception as e:
            logger.error(f"❌ Decision extraction failed: {e}")
            return []
    
    def _extract_topics(self, text: str, timestamp: float) -> List[str]:
        """Extract topics and keywords from text"""
        try:
            topics = []
            text_lower = text.lower()
            
            # Extract key phrases and topics
            words = re.findall(r'\b\w+\b', text_lower)
            
            # Check for predefined topic keywords
            for topic, keywords in self.topic_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        topics.append(topic)
                        break
            
            # Extract potential new topics (noun phrases)
            potential_topics = self._extract_noun_phrases(text)
            for topic in potential_topics:
                if len(topic.split()) >= 2 and len(topic) > 6:  # Multi-word topics
                    topics.append(topic.lower())
            
            return list(set(topics))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"❌ Topic extraction failed: {e}")
            return []
    
    def _update_topics(self, session_id: str, topics: List[str], speaker_id: str, 
                      timestamp: float, sentiment_data: Optional[Dict]):
        """Update topic tracking"""
        try:
            insights = self.meeting_insights[session_id]
            
            for topic in topics:
                if topic not in insights.key_topics:
                    insights.key_topics[topic] = KeyTopic(
                        topic=topic,
                        first_mention=timestamp
                    )
                
                topic_obj = insights.key_topics[topic]
                topic_obj.mentions_count += 1
                topic_obj.speakers.add(speaker_id)
                topic_obj.last_mention = timestamp
                
                # Update sentiment if available
                if sentiment_data:
                    sentiment_score = sentiment_data.get('compound', 0)
                    # Running average of sentiment
                    topic_obj.sentiment_score = (
                        (topic_obj.sentiment_score * (topic_obj.mentions_count - 1) + sentiment_score) /
                        topic_obj.mentions_count
                    )
                
                # Calculate importance score
                topic_obj.importance_score = self._calculate_topic_importance(topic_obj)
                
        except Exception as e:
            logger.error(f"❌ Topic update failed: {e}")
    
    def _update_speaker_participation(self, session_id: str, speaker_id: str, text: str,
                                    timestamp: float, sentiment_data: Optional[Dict]):
        """Update speaker participation metrics"""
        try:
            insights = self.meeting_insights[session_id]
            
            if speaker_id not in insights.speaker_participation:
                insights.speaker_participation[speaker_id] = {
                    'word_count': 0,
                    'segment_count': 0,
                    'avg_sentiment': 0.0,
                    'topics_mentioned': set(),
                    'questions_asked': 0,
                    'statements_made': 0,
                    'first_contribution': timestamp,
                    'last_contribution': timestamp
                }
            
            participation = insights.speaker_participation[speaker_id]
            
            # Update basic metrics
            word_count = len(text.split())
            participation['word_count'] += word_count
            participation['segment_count'] += 1
            participation['last_contribution'] = timestamp
            
            # Update sentiment
            if sentiment_data:
                sentiment = sentiment_data.get('compound', 0)
                current_avg = participation['avg_sentiment']
                segment_count = participation['segment_count']
                participation['avg_sentiment'] = (current_avg * (segment_count - 1) + sentiment) / segment_count
            
            # Count questions vs statements
            if '?' in text:
                participation['questions_asked'] += text.count('?')
            else:
                participation['statements_made'] += 1
            
            # Update speaking time distribution
            if speaker_id not in insights.speaking_time_distribution:
                insights.speaking_time_distribution[speaker_id] = 0.0
            
            # Estimate speaking time (rough calculation: ~150 words per minute)
            estimated_time = word_count / 150 * 60  # seconds
            insights.speaking_time_distribution[speaker_id] += estimated_time
            
        except Exception as e:
            logger.error(f"❌ Speaker participation update failed: {e}")
    
    def _update_meeting_analytics(self, session_id: str, text: str, timestamp: float, sentiment_data: Optional[Dict]):
        """Update overall meeting analytics"""
        try:
            insights = self.meeting_insights[session_id]
            
            # Add to sentiment timeline
            if sentiment_data:
                sentiment_score = sentiment_data.get('compound', 0)
                insights.sentiment_timeline.append((timestamp, sentiment_score))
            
            # Keep only recent sentiment data (last 100 points)
            if len(insights.sentiment_timeline) > 100:
                insights.sentiment_timeline = insights.sentiment_timeline[-100:]
                
        except Exception as e:
            logger.error(f"❌ Meeting analytics update failed: {e}")
    
    def _calculate_final_metrics(self, session_id: str, insights: MeetingInsights):
        """Calculate final meeting metrics"""
        try:
            # Calculate total duration
            if insights.start_time > 0:
                insights.end_time = time.time()
                insights.total_duration = insights.end_time - insights.start_time
            
            # Calculate engagement score
            insights.engagement_score = self._calculate_engagement_score(insights)
            
            # Calculate productivity score
            insights.productivity_score = self._calculate_productivity_score(insights)
            
            # Calculate collaboration score
            insights.collaboration_score = self._calculate_collaboration_score(insights)
            
        except Exception as e:
            logger.error(f"❌ Final metrics calculation failed: {e}")
    
    def _calculate_engagement_score(self, insights: MeetingInsights) -> float:
        """Calculate overall meeting engagement score"""
        try:
            engagement_factors = []
            
            # Participation distribution (more even = higher engagement)
            if insights.speaker_participation:
                participation_values = [p['segment_count'] for p in insights.speaker_participation.values()]
                if len(participation_values) > 1:
                    # Use coefficient of variation (lower = more even)
                    cv = np.std(participation_values) / np.mean(participation_values)
                    participation_score = max(0, 1 - cv)
                    engagement_factors.append(participation_score * 0.3)
            
            # Question frequency (more questions = higher engagement)
            total_questions = sum(p.get('questions_asked', 0) for p in insights.speaker_participation.values())
            total_segments = sum(p.get('segment_count', 0) for p in insights.speaker_participation.values())
            if total_segments > 0:
                question_ratio = total_questions / total_segments
                question_score = min(1.0, question_ratio * 5)  # Normalize
                engagement_factors.append(question_score * 0.2)
            
            # Sentiment positivity
            if insights.sentiment_timeline:
                avg_sentiment = np.mean([s[1] for s in insights.sentiment_timeline])
                sentiment_score = (avg_sentiment + 1) / 2  # Convert from [-1,1] to [0,1]
                engagement_factors.append(sentiment_score * 0.2)
            
            # Topic diversity
            topic_count = len(insights.key_topics)
            topic_score = min(1.0, topic_count / 10)  # Normalize (10+ topics = max score)
            engagement_factors.append(topic_score * 0.3)
            
            return sum(engagement_factors) if engagement_factors else 0.5
            
        except Exception:
            return 0.5
    
    def _calculate_productivity_score(self, insights: MeetingInsights) -> float:
        """Calculate meeting productivity score"""
        try:
            productivity_factors = []
            
            # Action items generated
            action_count = len(insights.action_items)
            action_score = min(1.0, action_count / 5)  # 5+ actions = max score
            productivity_factors.append(action_score * 0.4)
            
            # Decisions made
            decision_count = len(insights.decisions)
            decision_score = min(1.0, decision_count / 3)  # 3+ decisions = max score
            productivity_factors.append(decision_score * 0.3)
            
            # High-priority/urgent items
            high_priority_actions = sum(1 for a in insights.action_items if a.priority in ['high', 'urgent'])
            priority_score = min(1.0, high_priority_actions / 2)
            productivity_factors.append(priority_score * 0.3)
            
            return sum(productivity_factors) if productivity_factors else 0.3
            
        except Exception:
            return 0.3
    
    def _calculate_collaboration_score(self, insights: MeetingInsights) -> float:
        """Calculate collaboration score"""
        try:
            if len(insights.speaker_participation) < 2:
                return 0.5  # Single speaker = moderate collaboration
            
            collaboration_factors = []
            
            # Speaker diversity in topics
            topic_speaker_diversity = []
            for topic_obj in insights.key_topics.values():
                if topic_obj.mentions_count > 1:
                    diversity = len(topic_obj.speakers) / len(insights.speaker_participation)
                    topic_speaker_diversity.append(diversity)
            
            if topic_speaker_diversity:
                avg_diversity = np.mean(topic_speaker_diversity)
                collaboration_factors.append(avg_diversity * 0.4)
            
            # Response patterns (speakers building on each other's ideas)
            # This is simplified - in practice you'd analyze adjacency patterns
            total_segments = sum(p['segment_count'] for p in insights.speaker_participation.values())
            if total_segments > 0:
                interaction_score = min(1.0, total_segments / (len(insights.speaker_participation) * 5))
                collaboration_factors.append(interaction_score * 0.3)
            
            # Balanced participation
            participation_values = [p['segment_count'] for p in insights.speaker_participation.values()]
            if len(participation_values) > 1:
                # Gini coefficient (0 = perfect equality, 1 = perfect inequality)
                sorted_values = sorted(participation_values)
                n = len(sorted_values)
                cumsum = np.cumsum(sorted_values)
                gini = (n + 1 - 2 * sum((n + 1 - i) * y for i, y in enumerate(cumsum))) / (n * sum(sorted_values))
                balance_score = 1 - gini
                collaboration_factors.append(balance_score * 0.3)
            
            return sum(collaboration_factors) if collaboration_factors else 0.5
            
        except Exception:
            return 0.5
    
    def _generate_executive_summary(self, session_id: str, insights: MeetingInsights) -> str:
        """Generate executive summary of the meeting"""
        try:
            summary_parts = []
            
            # Meeting overview
            duration_minutes = int(insights.total_duration / 60) if insights.total_duration > 0 else 0
            participant_count = len(insights.speaker_participation)
            
            summary_parts.append(f"Meeting duration: {duration_minutes} minutes with {participant_count} participants.")
            
            # Key outcomes
            if insights.action_items:
                action_count = len(insights.action_items)
                high_priority = sum(1 for a in insights.action_items if a.priority in ['high', 'urgent'])
                summary_parts.append(f"Generated {action_count} action items ({high_priority} high priority).")
            
            if insights.decisions:
                decision_count = len(insights.decisions)
                summary_parts.append(f"Made {decision_count} key decisions.")
            
            # Top topics
            if insights.key_topics:
                top_topics = sorted(insights.key_topics.values(), key=lambda t: t.importance_score, reverse=True)[:3]
                topic_names = [t.topic for t in top_topics]
                summary_parts.append(f"Main topics discussed: {', '.join(topic_names)}.")
            
            # Meeting dynamics
            engagement_level = "high" if insights.engagement_score > 0.7 else "moderate" if insights.engagement_score > 0.4 else "low"
            productivity_level = "high" if insights.productivity_score > 0.7 else "moderate" if insights.productivity_score > 0.4 else "low"
            
            summary_parts.append(f"Engagement level: {engagement_level}, productivity: {productivity_level}.")
            
            return " ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"❌ Executive summary generation failed: {e}")
            return "Meeting summary could not be generated."
    
    def _extract_key_outcomes(self, insights: MeetingInsights) -> List[str]:
        """Extract key outcomes from the meeting"""
        try:
            outcomes = []
            
            # High-impact decisions
            high_impact_decisions = [d for d in insights.decisions if d.impact_level == 'high']
            for decision in high_impact_decisions[:3]:  # Top 3
                outcomes.append(f"Decision: {decision.decision_text[:100]}...")
            
            # Urgent action items
            urgent_actions = [a for a in insights.action_items if a.priority == 'urgent']
            for action in urgent_actions[:2]:  # Top 2
                outcomes.append(f"Urgent action: {action.text[:100]}...")
            
            # Major topics with high importance
            important_topics = [t for t in insights.key_topics.values() if t.importance_score > 0.7]
            for topic in sorted(important_topics, key=lambda t: t.importance_score, reverse=True)[:2]:
                outcomes.append(f"Key topic: {topic.topic}")
            
            return outcomes
            
        except Exception:
            return []
    
    def _generate_next_steps(self, insights: MeetingInsights) -> List[str]:
        """Generate next steps based on meeting content"""
        try:
            next_steps = []
            
            # Immediate action items
            immediate_actions = [a for a in insights.action_items if a.priority in ['high', 'urgent']]
            for action in immediate_actions[:3]:
                assignee_text = f" ({action.assignee})" if action.assignee else ""
                next_steps.append(f"{action.text}{assignee_text}")
            
            # Follow-up items
            follow_up_actions = [a for a in insights.action_items if a.category == 'follow_up']
            for action in follow_up_actions[:2]:
                next_steps.append(f"Follow up: {action.text}")
            
            # Implementation notes from decisions
            implementation_decisions = [d for d in insights.decisions if d.implementation_notes]
            for decision in implementation_decisions[:2]:
                next_steps.append(f"Implement: {decision.implementation_notes}")
            
            return next_steps
            
        except Exception:
            return []
    
    def _generate_word_cloud_data(self, session_id: str) -> Dict[str, int]:
        """Generate word cloud data from meeting transcript"""
        try:
            if session_id not in self.session_transcripts:
                return {}
            
            word_counts = defaultdict(int)
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                         'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
                         'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
                         'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
            
            for segment in self.session_transcripts[session_id]:
                text = segment['text'].lower()
                words = re.findall(r'\b\w+\b', text)
                
                for word in words:
                    if len(word) > 3 and word not in stop_words:
                        word_counts[word] += 1
            
            # Return top 50 words
            sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
            return dict(sorted_words[:50])
            
        except Exception as e:
            logger.error(f"❌ Word cloud generation failed: {e}")
            return {}
    
    def _classify_meeting_type(self, session_id: str, insights: MeetingInsights) -> str:
        """Classify the type of meeting based on content and patterns"""
        try:
            if session_id not in self.session_transcripts:
                return "general"
            
            # Analyze transcript for meeting type indicators
            all_text = " ".join(segment['text'].lower() for segment in self.session_transcripts[session_id])
            
            type_scores = {}
            for meeting_type, indicators in self.meeting_type_indicators.items():
                score = 0
                for indicator in indicators:
                    score += all_text.count(indicator)
                type_scores[meeting_type] = score
            
            # Additional analysis based on structure
            if len(insights.action_items) > 5:
                type_scores['planning'] = type_scores.get('planning', 0) + 2
            
            if len(insights.decisions) > 3:
                type_scores['review'] = type_scores.get('review', 0) + 2
            
            if insights.total_duration < 900:  # Less than 15 minutes
                type_scores['standup'] = type_scores.get('standup', 0) + 3
            
            # Return the type with highest score
            if type_scores:
                return max(type_scores, key=type_scores.get)
            else:
                return "general"
                
        except Exception:
            return "general"
    
    # Pattern and configuration loading methods
    def _load_action_patterns(self) -> List[Dict]:
        """Load action item detection patterns"""
        return [
            {'pattern': r'\b(?:will|should|need to|must|have to|going to)\s+(\w+(?:\s+\w+)*)', 'confidence': 0.7, 'category': 'general'},
            {'pattern': r'\b(?:action item|todo|task):\s*(.+)', 'confidence': 0.9, 'category': 'explicit'},
            {'pattern': r'\b(\w+)\s+(?:will|should)\s+(?:follow up|reach out|contact)', 'confidence': 0.8, 'category': 'follow_up'},
            {'pattern': r'\bby\s+(\w+day|\w+\s+\d+)', 'confidence': 0.6, 'category': 'deadline'},
            {'pattern': r'\bassign(?:ed)?\s+to\s+(\w+)', 'confidence': 0.8, 'category': 'assignment'},
            {'pattern': r'\b(?:next steps?|follow up):\s*(.+)', 'confidence': 0.8, 'category': 'follow_up'}
        ]
    
    def _load_decision_patterns(self) -> List[Dict]:
        """Load decision detection patterns"""
        return [
            {'pattern': r'\b(?:we (?:decided|agreed|concluded)|decision made|it was decided)\s+(.+)', 'confidence': 0.9, 'type': 'explicit'},
            {'pattern': r'\b(?:let\'s go with|we\'ll use|we\'re going with)\s+(.+)', 'confidence': 0.8, 'type': 'selection'},
            {'pattern': r'\b(?:approved|rejected|accepted)\s+(.+)', 'confidence': 0.7, 'type': 'approval'},
            {'pattern': r'\bthe plan is to\s+(.+)', 'confidence': 0.7, 'type': 'planning'},
            {'pattern': r'\bwe will\s+(?:not\s+)?(.+)', 'confidence': 0.6, 'type': 'commitment'}
        ]
    
    def _load_topic_keywords(self) -> Dict[str, List[str]]:
        """Load topic keyword mappings"""
        return {
            'budget': ['budget', 'cost', 'expense', 'funding', 'financial', 'money'],
            'timeline': ['deadline', 'schedule', 'timeline', 'due date', 'milestone'],
            'technical': ['code', 'system', 'database', 'api', 'implementation', 'technical'],
            'marketing': ['marketing', 'campaign', 'promotion', 'brand', 'advertising'],
            'sales': ['sales', 'revenue', 'customer', 'client', 'deal', 'prospect'],
            'product': ['product', 'feature', 'development', 'design', 'user experience'],
            'strategy': ['strategy', 'strategic', 'goals', 'objectives', 'vision', 'mission'],
            'team': ['team', 'hiring', 'staffing', 'personnel', 'resources', 'capacity']
        }
    
    def _load_meeting_type_indicators(self) -> Dict[str, List[str]]:
        """Load meeting type classification indicators"""
        return {
            'standup': ['yesterday', 'today', 'blockers', 'sprint', 'daily', 'status update'],
            'planning': ['planning', 'roadmap', 'goals', 'objectives', 'strategy', 'next quarter'],
            'review': ['review', 'retrospective', 'feedback', 'lessons learned', 'what went well'],
            'brainstorm': ['brainstorm', 'ideas', 'creative', 'innovation', 'think outside'],
            'training': ['training', 'learning', 'education', 'workshop', 'tutorial'],
            'client': ['client', 'customer', 'external', 'presentation', 'demo']
        }
    
    # Helper methods for extraction
    def _extract_action_text(self, text: str, match: re.Match) -> str:
        """Extract action text from regex match"""
        try:
            # Get the sentence containing the match
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 100)
            context = text[start:end]
            
            # Find sentence boundaries
            sentences = re.split(r'[.!?]', context)
            for sentence in sentences:
                if match.group(0) in sentence.lower():
                    return sentence.strip()
            
            return match.group(1) if match.groups() else match.group(0)
            
        except Exception:
            return ""
    
    def _extract_decision_text(self, text: str, match: re.Match) -> str:
        """Extract decision text from regex match"""
        try:
            # Similar to action text extraction
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 150)
            context = text[start:end]
            
            # Find sentence boundaries
            sentences = re.split(r'[.!?]', context)
            for sentence in sentences:
                if match.group(0) in sentence.lower():
                    return sentence.strip()
            
            return match.group(1) if match.groups() else match.group(0)
            
        except Exception:
            return ""
    
    def _extract_noun_phrases(self, text: str) -> List[str]:
        """Extract noun phrases as potential topics (simplified)"""
        try:
            # Simple noun phrase extraction using patterns
            # In production, you'd use NLP libraries like spaCy
            patterns = [
                r'\b(?:the|a|an)\s+(\w+\s+\w+)',  # article + noun phrase
                r'\b(\w+\s+(?:project|system|process|strategy|plan|initiative))',
                r'\b(\w+\s+(?:team|department|group|committee))',
                r'\b(\w+\s+(?:meeting|discussion|session|call))'
            ]
            
            phrases = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                phrases.extend(matches)
            
            return phrases
            
        except Exception:
            return []
    
    # Helper methods for analysis
    def _detect_assignee(self, action_text: str, default_speaker: str) -> Optional[str]:
        """Detect who is assigned to an action item"""
        try:
            # Look for explicit assignment patterns
            assignment_patterns = [
                r'\b(\w+)\s+(?:will|should)',
                r'\bassign(?:ed)?\s+to\s+(\w+)',
                r'\b(\w+)\'s?\s+(?:responsibility|task)'
            ]
            
            for pattern in assignment_patterns:
                match = re.search(pattern, action_text.lower())
                if match:
                    return match.group(1)
            
            # If no explicit assignment, assume the speaker
            return default_speaker
            
        except Exception:
            return default_speaker
    
    def _detect_due_date(self, action_text: str) -> Optional[str]:
        """Detect due date from action text"""
        try:
            date_patterns = [
                r'\bby\s+(\w+day)',  # by Friday
                r'\bby\s+(\w+\s+\d+)',  # by March 15
                r'\b(\d+\s+days?)',  # 5 days
                r'\b(next\s+week)',
                r'\b(end\s+of\s+week)',
                r'\b(tomorrow)',
                r'\b(today)'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, action_text.lower())
                if match:
                    return match.group(1)
            
            return None
            
        except Exception:
            return None
    
    def _calculate_action_priority(self, action_text: str) -> str:
        """Calculate action item priority"""
        try:
            text_lower = action_text.lower()
            
            # Urgent indicators
            if any(word in text_lower for word in ['urgent', 'asap', 'immediately', 'critical', 'emergency']):
                return 'urgent'
            
            # High priority indicators
            if any(word in text_lower for word in ['high priority', 'important', 'must', 'required', 'essential']):
                return 'high'
            
            # Low priority indicators
            if any(word in text_lower for word in ['when possible', 'if time', 'nice to have', 'optional']):
                return 'low'
            
            # Default to medium
            return 'medium'
            
        except Exception:
            return 'medium'
    
    def _calculate_action_confidence(self, action_text: str, base_confidence: float) -> float:
        """Calculate confidence score for action item"""
        try:
            confidence = base_confidence
            
            # Boost confidence for explicit language
            if any(phrase in action_text.lower() for phrase in ['action item', 'todo', 'must do']):
                confidence += 0.2
            
            # Boost for specific assignments
            if re.search(r'\b\w+\s+will\b', action_text.lower()):
                confidence += 0.1
            
            # Reduce for vague language
            if any(word in action_text.lower() for word in ['maybe', 'might', 'perhaps', 'possibly']):
                confidence -= 0.2
            
            return max(0.0, min(1.0, confidence))
            
        except Exception:
            return base_confidence
    
    def _calculate_decision_confidence(self, decision_text: str, base_confidence: float) -> float:
        """Calculate confidence score for decision"""
        try:
            confidence = base_confidence
            
            # Boost for explicit decision language
            if any(phrase in decision_text.lower() for phrase in ['decided', 'agreed', 'concluded']):
                confidence += 0.2
            
            # Boost for definitive language
            if any(word in decision_text.lower() for word in ['will', 'shall', 'must', 'definitely']):
                confidence += 0.1
            
            # Reduce for uncertain language
            if any(word in decision_text.lower() for word in ['maybe', 'might', 'consider', 'think about']):
                confidence -= 0.3
            
            return max(0.0, min(1.0, confidence))
            
        except Exception:
            return base_confidence
    
    def _detect_impact_level(self, decision_text: str) -> str:
        """Detect impact level of a decision"""
        try:
            text_lower = decision_text.lower()
            
            # High impact indicators
            if any(word in text_lower for word in ['strategic', 'major', 'significant', 'critical', 'company-wide']):
                return 'high'
            
            # Low impact indicators
            if any(word in text_lower for word in ['minor', 'small', 'local', 'temporary', 'quick']):
                return 'low'
            
            # Default to medium
            return 'medium'
            
        except Exception:
            return 'medium'
    
    def _calculate_topic_importance(self, topic: KeyTopic) -> float:
        """Calculate topic importance score"""
        try:
            importance = 0.0
            
            # Frequency factor (normalized)
            frequency_score = min(1.0, topic.mentions_count / 10)
            importance += frequency_score * 0.3
            
            # Speaker diversity factor
            speaker_diversity = len(topic.speakers) / max(1, topic.mentions_count)
            importance += speaker_diversity * 0.3
            
            # Time span factor (topics discussed over longer periods are more important)
            time_span = topic.last_mention - topic.first_mention
            time_score = min(1.0, time_span / 1800)  # Normalize to 30 minutes
            importance += time_score * 0.2
            
            # Sentiment factor (absolute sentiment indicates importance)
            sentiment_importance = abs(topic.sentiment_score)
            importance += sentiment_importance * 0.2
            
            return min(1.0, importance)
            
        except Exception:
            return 0.5
    
    def clear_session_data(self, session_id: str):
        """Clear insights data for a session"""
        with self.insights_lock:
            if session_id in self.meeting_insights:
                del self.meeting_insights[session_id]
            if session_id in self.session_transcripts:
                del self.session_transcripts[session_id]
            logger.info(f"🗑️ Cleared insights data for session {session_id}")

# Global insights service
_global_insights_service = None
_insights_lock = threading.Lock()

def get_insights_service() -> MeetingInsightsService:
    """Get global meeting insights service"""
    global _global_insights_service
    
    if _global_insights_service is None:
        with _insights_lock:
            if _global_insights_service is None:
                _global_insights_service = MeetingInsightsService()
    
    return _global_insights_service

logger.info("🧠 Meeting Insights Service initialized")