"""
Cross-Meeting Insights and Memory Graph Service for Mina.

This module provides advanced analytics across multiple meetings to identify
patterns, relationships, and insights that span multiple sessions.
"""

import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class InsightType(Enum):
    """Types of cross-meeting insights."""
    RECURRING_TOPIC = "recurring_topic"
    DECISION_THREAD = "decision_thread"
    PARTICIPANT_PATTERN = "participant_pattern"
    ACTION_FOLLOW_UP = "action_follow_up"
    MEETING_FREQUENCY = "meeting_frequency"
    PRODUCTIVITY_TREND = "productivity_trend"
    TOPIC_EVOLUTION = "topic_evolution"
    COLLABORATION_NETWORK = "collaboration_network"


class NodeType(Enum):
    """Types of nodes in the memory graph."""
    MEETING = "meeting"
    PERSON = "person"
    TOPIC = "topic"
    DECISION = "decision"
    ACTION_ITEM = "action_item"
    PROJECT = "project"
    KEYWORD = "keyword"


@dataclass
class MemoryNode:
    """A node in the meeting memory graph."""
    id: str
    type: NodeType
    label: str
    properties: Dict[str, Any]
    connections: List[str]  # IDs of connected nodes
    weight: float = 1.0
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class MemoryEdge:
    """An edge connecting two nodes in the memory graph."""
    source_id: str
    target_id: str
    relationship_type: str
    weight: float
    properties: Dict[str, Any]
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class CrossMeetingInsight:
    """A cross-meeting insight discovered through analysis."""
    id: str
    type: InsightType
    title: str
    description: str
    confidence: float
    meetings_involved: List[int]
    entities_involved: List[str]
    evidence: Dict[str, Any]
    actionable: bool
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class MemoryGraph:
    """Memory graph for storing and analyzing meeting relationships."""
    
    def __init__(self):
        self.nodes: Dict[str, MemoryNode] = {}
        self.edges: List[MemoryEdge] = []
        self.edge_index: Dict[str, List[MemoryEdge]] = defaultdict(list)
    
    def add_node(self, node: MemoryNode):
        """Add a node to the graph."""
        self.nodes[node.id] = node
    
    def add_edge(self, edge: MemoryEdge):
        """Add an edge to the graph."""
        self.edges.append(edge)
        self.edge_index[edge.source_id].append(edge)
        self.edge_index[edge.target_id].append(edge)
    
    def get_node(self, node_id: str) -> Optional[MemoryNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_connected_nodes(self, node_id: str, relationship_type: Optional[str] = None) -> List[MemoryNode]:
        """Get all nodes connected to the given node."""
        connected = []
        for edge in self.edge_index.get(node_id, []):
            other_id = edge.target_id if edge.source_id == node_id else edge.source_id
            if relationship_type is None or edge.relationship_type == relationship_type:
                if other_id in self.nodes:
                    connected.append(self.nodes[other_id])
        return connected
    
    def find_paths(self, start_id: str, end_id: str, max_depth: int = 3) -> List[List[str]]:
        """Find paths between two nodes."""
        if start_id not in self.nodes or end_id not in self.nodes:
            return []
        
        paths = []
        visited = set()
        
        def dfs(current_id: str, target_id: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            
            if current_id == target_id:
                paths.append(path.copy())
                return
            
            if current_id in visited:
                return
            
            visited.add(current_id)
            
            for edge in self.edge_index.get(current_id, []):
                next_id = edge.target_id if edge.source_id == current_id else edge.source_id
                if next_id and next_id not in visited:
                    path.append(next_id)
                    dfs(next_id, target_id, path, depth + 1)
                    path.pop()
            
            visited.remove(current_id)
        
        dfs(start_id, end_id, [start_id], 0)
        return paths
    
    def get_subgraph(self, node_ids: Set[str]) -> 'MemoryGraph':
        """Extract a subgraph containing only the specified nodes."""
        subgraph = MemoryGraph()
        
        # Add nodes
        for node_id in node_ids:
            if node_id in self.nodes:
                subgraph.add_node(self.nodes[node_id])
        
        # Add edges between included nodes
        for edge in self.edges:
            if edge.source_id in node_ids and edge.target_id in node_ids:
                subgraph.add_edge(edge)
        
        return subgraph


class CrossMeetingInsightsService:
    """Service for generating cross-meeting insights and managing the memory graph."""
    
    def __init__(self):
        self.memory_graph = MemoryGraph()
        self.insights_cache: Dict[str, List[CrossMeetingInsight]] = {}
        self.last_analysis_time = None
    
    def analyze_meetings(self, user_id: int, days_back: int = 30) -> List[CrossMeetingInsight]:
        """
        Analyze meetings for a user and generate cross-meeting insights.
        
        Args:
            user_id: User ID to analyze meetings for
            days_back: Number of days back to analyze
            
        Returns:
            List of cross-meeting insights
        """
        try:
            # Get meeting data
            meeting_data = self._get_meeting_data(user_id, days_back)
            
            if len(meeting_data) < 2:
                return []
            
            # Update memory graph
            self._update_memory_graph(meeting_data)
            
            # Generate insights
            insights = []
            insights.extend(self._analyze_recurring_topics(meeting_data))
            insights.extend(self._analyze_decision_threads(meeting_data))
            insights.extend(self._analyze_participant_patterns(meeting_data))
            insights.extend(self._analyze_action_follow_ups(meeting_data))
            insights.extend(self._analyze_productivity_trends(meeting_data))
            insights.extend(self._analyze_topic_evolution(meeting_data))
            insights.extend(self._analyze_collaboration_network(meeting_data))
            
            # Cache insights
            cache_key = f"{user_id}_{days_back}"
            self.insights_cache[cache_key] = insights
            self.last_analysis_time = datetime.now()
            
            return insights
            
        except Exception as e:
            logger.error(f"Error analyzing meetings for user {user_id}: {e}")
            return []
    
    def get_memory_graph_data(self, user_id: int, focus_type: str = None) -> Dict[str, Any]:
        """
        Get memory graph data for visualization.
        
        Args:
            user_id: User ID
            focus_type: Optional focus on specific node type
            
        Returns:
            Graph data for visualization
        """
        try:
            nodes = []
            edges = []
            
            # Filter nodes by focus type if specified
            filtered_nodes = self.memory_graph.nodes.values()
            if focus_type:
                filtered_nodes = [n for n in filtered_nodes if n.type.value == focus_type]
            
            # Convert nodes to visualization format
            for node in filtered_nodes:
                nodes.append({
                    'id': node.id,
                    'label': node.label,
                    'type': node.type.value,
                    'weight': node.weight,
                    'properties': node.properties
                })
            
            # Get node IDs for edge filtering
            node_ids = {node['id'] for node in nodes}
            
            # Convert edges to visualization format
            for edge in self.memory_graph.edges:
                if edge.source_id in node_ids and edge.target_id in node_ids:
                    edges.append({
                        'source': edge.source_id,
                        'target': edge.target_id,
                        'type': edge.relationship_type,
                        'weight': edge.weight,
                        'properties': edge.properties
                    })
            
            return {
                'nodes': nodes,
                'edges': edges,
                'metadata': {
                    'total_nodes': len(nodes),
                    'total_edges': len(edges),
                    'focus_type': focus_type,
                    'generated_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating memory graph data: {e}")
            return {'nodes': [], 'edges': [], 'metadata': {}}
    
    def get_insights_summary(self, user_id: int) -> Dict[str, Any]:
        """Get a summary of insights for the user."""
        try:
            cache_key = f"{user_id}_30"  # Default to 30 days
            insights = self.insights_cache.get(cache_key, [])
            
            if not insights:
                insights = self.analyze_meetings(user_id, 30)
            
            # Group insights by type
            by_type = defaultdict(list)
            for insight in insights:
                by_type[insight.type.value].append(insight)
            
            # Calculate summary statistics
            summary = {
                'total_insights': len(insights),
                'by_type': {
                    insight_type: {
                        'count': len(type_insights),
                        'avg_confidence': sum(i.confidence for i in type_insights) / len(type_insights) if type_insights else 0,
                        'actionable_count': sum(1 for i in type_insights if i.actionable)
                    }
                    for insight_type, type_insights in by_type.items()
                },
                'actionable_insights': sum(1 for i in insights if i.actionable),
                'high_confidence_insights': sum(1 for i in insights if i.confidence > 0.8),
                'last_analysis': self.last_analysis_time.isoformat() if self.last_analysis_time else None
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating insights summary: {e}")
            return {}
    
    def _get_meeting_data(self, user_id: int, days_back: int) -> List[Dict[str, Any]]:
        """Get meeting data for analysis."""
        try:
            from models.session import Session
            from models.segment import Segment
            from models.summary import Summary
            from models.task import Task
            from app import db
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Get sessions for the user within date range
            sessions = db.session.query(Session).filter(
                Session.user_id == user_id,
                Session.created_at >= start_date,
                Session.created_at <= end_date,
                Session.status == 'completed'
            ).order_by(Session.created_at.desc()).all()
            
            meeting_data = []
            
            for session in sessions:
                # Get segments
                segments = db.session.query(Segment).filter_by(session_id=session.id).all()
                
                # Get summary
                summary = db.session.query(Summary).filter_by(session_id=session.id).first()
                
                # Get tasks
                tasks = db.session.query(Task).filter_by(session_id=session.id).all()
                
                # Extract meeting data
                data = {
                    'id': session.id,
                    'title': session.title,
                    'date': session.created_at,
                    'duration': session.duration_seconds,
                    'transcript_text': ' '.join([seg.text for seg in segments if seg.text]),
                    'segments': [
                        {
                            'text': seg.text,
                            'speaker': seg.speaker_label,
                            'start_time': seg.start_time,
                            'confidence': seg.confidence
                        }
                        for seg in segments
                    ],
                    'summary': {
                        'content': summary.content if summary else '',
                        'key_points': json.loads(summary.key_points) if summary and summary.key_points else [],
                        'action_items': json.loads(summary.action_items) if summary and summary.action_items else [],
                        'decisions': json.loads(summary.decisions) if summary and summary.decisions else []
                    },
                    'tasks': [
                        {
                            'text': task.text,
                            'priority': task.priority,
                            'status': task.status,
                            'due_date': task.due_date
                        }
                        for task in tasks
                    ]
                }
                
                meeting_data.append(data)
            
            return meeting_data
            
        except Exception as e:
            logger.error(f"Error getting meeting data: {e}")
            return []
    
    def _update_memory_graph(self, meeting_data: List[Dict[str, Any]]):
        """Update the memory graph with new meeting data."""
        try:
            for meeting in meeting_data:
                # Add meeting node
                meeting_node = MemoryNode(
                    id=f"meeting_{meeting['id']}",
                    type=NodeType.MEETING,
                    label=meeting['title'],
                    properties={
                        'date': meeting['date'].isoformat(),
                        'duration': meeting['duration'],
                        'segment_count': len(meeting['segments'])
                    },
                    connections=[]
                )
                self.memory_graph.add_node(meeting_node)
                
                # Extract and add entities
                self._extract_and_add_entities(meeting, meeting_node.id)
            
        except Exception as e:
            logger.error(f"Error updating memory graph: {e}")
    
    def _extract_and_add_entities(self, meeting: Dict[str, Any], meeting_id: str):
        """Extract entities from meeting and add to graph."""
        # Extract speakers
        speakers = set()
        for segment in meeting['segments']:
            if segment['speaker']:
                speakers.add(segment['speaker'])
        
        for speaker in speakers:
            speaker_id = f"person_{speaker.lower().replace(' ', '_')}"
            
            # Add or update speaker node
            if speaker_id not in self.memory_graph.nodes:
                speaker_node = MemoryNode(
                    id=speaker_id,
                    type=NodeType.PERSON,
                    label=speaker,
                    properties={'meetings': [meeting_id]},
                    connections=[]
                )
                self.memory_graph.add_node(speaker_node)
            else:
                # Update existing speaker
                existing_meetings = self.memory_graph.nodes[speaker_id].properties.get('meetings', [])
                if meeting_id not in existing_meetings:
                    existing_meetings.append(meeting_id)
                    self.memory_graph.nodes[speaker_id].properties['meetings'] = existing_meetings
            
            # Add edge between meeting and speaker
            edge = MemoryEdge(
                source_id=meeting_id,
                target_id=speaker_id,
                relationship_type="includes_participant",
                weight=1.0,
                properties={}
            )
            self.memory_graph.add_edge(edge)
        
        # Extract topics (keywords)
        topics = self._extract_topics(meeting['transcript_text'])
        for topic, weight in topics.items():
            topic_id = f"topic_{topic.lower().replace(' ', '_')}"
            
            # Add or update topic node
            if topic_id not in self.memory_graph.nodes:
                topic_node = MemoryNode(
                    id=topic_id,
                    type=NodeType.TOPIC,
                    label=topic,
                    properties={'meetings': [meeting_id], 'total_weight': weight},
                    connections=[],
                    weight=weight
                )
                self.memory_graph.add_node(topic_node)
            else:
                # Update existing topic
                existing_meetings = self.memory_graph.nodes[topic_id].properties.get('meetings', [])
                if meeting_id not in existing_meetings:
                    existing_meetings.append(meeting_id)
                    total_weight = self.memory_graph.nodes[topic_id].properties.get('total_weight', 0) + weight
                    self.memory_graph.nodes[topic_id].properties.update({
                        'meetings': existing_meetings,
                        'total_weight': total_weight
                    })
                    self.memory_graph.nodes[topic_id].weight = total_weight
            
            # Add edge between meeting and topic
            edge = MemoryEdge(
                source_id=meeting_id,
                target_id=topic_id,
                relationship_type="discusses_topic",
                weight=weight,
                properties={}
            )
            self.memory_graph.add_edge(edge)
        
        # Extract decisions
        decisions = meeting['summary']['decisions']
        for i, decision in enumerate(decisions):
            decision_id = f"decision_{meeting['id']}_{i}"
            
            decision_node = MemoryNode(
                id=decision_id,
                type=NodeType.DECISION,
                label=decision[:50] + "..." if len(decision) > 50 else decision,
                properties={'full_text': decision, 'meeting_id': meeting['id']},
                connections=[]
            )
            self.memory_graph.add_node(decision_node)
            
            # Connect to meeting
            edge = MemoryEdge(
                source_id=meeting_id,
                target_id=decision_id,
                relationship_type="contains_decision",
                weight=1.0,
                properties={}
            )
            self.memory_graph.add_edge(edge)
        
        # Extract action items
        action_items = meeting['summary']['action_items']
        for i, action in enumerate(action_items):
            action_id = f"action_{meeting['id']}_{i}"
            
            action_node = MemoryNode(
                id=action_id,
                type=NodeType.ACTION_ITEM,
                label=action[:50] + "..." if len(action) > 50 else action,
                properties={'full_text': action, 'meeting_id': meeting['id']},
                connections=[]
            )
            self.memory_graph.add_node(action_node)
            
            # Connect to meeting
            edge = MemoryEdge(
                source_id=meeting_id,
                target_id=action_id,
                relationship_type="contains_action",
                weight=1.0,
                properties={}
            )
            self.memory_graph.add_edge(edge)
    
    def _extract_topics(self, text: str) -> Dict[str, float]:
        """Extract topics/keywords from text with weights."""
        # Simple keyword extraction (in production, use more sophisticated NLP)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter out common words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'man', 'men', 'way', 'oil', 'use', 'far', 'put', 'say', 'she', 'too', 'own', 'any', 'ask', 'big', 'try', 'let', 'end', 'why', 'ago', 'air', 'add', 'set', 'run', 'off', 'got', 'yet', 'eat', 'dog', 'car', 'act', 'cut', 'hot', 'lot', 'map', 'sat', 'box', 'job', 'hit', 'six', 'yes', 'win', 'war', 'red', 'top', 'ten', 'tax', 'sun', 'bad', 'sea', 'arm', 'art', 'age', 'bag', 'bit', 'buy', 'die', 'eye', 'few', 'fun', 'gun', 'ice', 'key', 'law', 'leg', 'lie', 'lot', 'pay', 'per', 'put', 'row', 'sex', 'six', 'sir', 'tea', 'tie', 'top', 'try', 'war', 'win', 'yes', 'yet', 'zoo', 'its', 'this', 'that', 'with', 'have', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were'
        }
        
        # Count words and calculate weights
        word_counts = Counter(word for word in words if word not in stop_words and len(word) > 3)
        
        # Get top keywords with weights
        total_words = len(words)
        topics = {}
        for word, count in word_counts.most_common(20):  # Top 20 keywords
            weight = count / total_words if total_words > 0 else 0
            if weight > 0.01:  # Only include words that appear more than 1% of the time
                topics[word] = weight
        
        return topics
    
    def _analyze_recurring_topics(self, meeting_data: List[Dict[str, Any]]) -> List[CrossMeetingInsight]:
        """Analyze recurring topics across meetings."""
        insights = []
        
        try:
            # Count topic occurrences across meetings
            topic_meetings = defaultdict(list)
            
            for meeting in meeting_data:
                topics = self._extract_topics(meeting['transcript_text'])
                for topic in topics:
                    topic_meetings[topic].append(meeting['id'])
            
            # Find topics that appear in multiple meetings
            for topic, meetings in topic_meetings.items():
                if len(meetings) >= 3:  # Topic appears in 3+ meetings
                    confidence = min(0.9, len(meetings) / len(meeting_data))
                    
                    insight = CrossMeetingInsight(
                        id=f"recurring_topic_{topic}",
                        type=InsightType.RECURRING_TOPIC,
                        title=f"Recurring Topic: {topic.title()}",
                        description=f"The topic '{topic}' has been discussed in {len(meetings)} meetings, suggesting it's an ongoing area of focus.",
                        confidence=confidence,
                        meetings_involved=meetings,
                        entities_involved=[topic],
                        evidence={'topic': topic, 'occurrence_count': len(meetings)},
                        actionable=True
                    )
                    insights.append(insight)
            
        except Exception as e:
            logger.error(f"Error analyzing recurring topics: {e}")
        
        return insights
    
    def _analyze_decision_threads(self, meeting_data: List[Dict[str, Any]]) -> List[CrossMeetingInsight]:
        """Analyze decision threads across meetings."""
        insights = []
        
        try:
            # Look for related decisions across meetings
            all_decisions = []
            for meeting in meeting_data:
                for decision in meeting['summary']['decisions']:
                    all_decisions.append({
                        'text': decision,
                        'meeting_id': meeting['id'],
                        'date': meeting['date']
                    })
            
            # Simple similarity check (in production, use more sophisticated NLP)
            decision_threads = []
            processed = set()
            
            for i, decision1 in enumerate(all_decisions):
                if i in processed:
                    continue
                
                thread = [decision1]
                processed.add(i)
                
                for j, decision2 in enumerate(all_decisions[i+1:], i+1):
                    if j in processed:
                        continue
                    
                    # Simple keyword overlap check
                    words1 = set(re.findall(r'\b[a-zA-Z]{3,}\b', decision1['text'].lower()))
                    words2 = set(re.findall(r'\b[a-zA-Z]{3,}\b', decision2['text'].lower()))
                    
                    overlap = len(words1.intersection(words2))
                    if overlap >= 3:  # At least 3 common words
                        thread.append(decision2)
                        processed.add(j)
                
                if len(thread) >= 2:
                    decision_threads.append(thread)
            
            # Create insights for decision threads
            for i, thread in enumerate(decision_threads):
                meetings_involved = [d['meeting_id'] for d in thread]
                
                insight = CrossMeetingInsight(
                    id=f"decision_thread_{i}",
                    type=InsightType.DECISION_THREAD,
                    title=f"Related Decisions Across {len(meetings_involved)} Meetings",
                    description=f"Found a series of related decisions spanning multiple meetings, indicating an evolving decision process.",
                    confidence=0.7,
                    meetings_involved=meetings_involved,
                    entities_involved=[d['text'][:30] for d in thread],
                    evidence={'thread': thread},
                    actionable=True
                )
                insights.append(insight)
            
        except Exception as e:
            logger.error(f"Error analyzing decision threads: {e}")
        
        return insights
    
    def _analyze_participant_patterns(self, meeting_data: List[Dict[str, Any]]) -> List[CrossMeetingInsight]:
        """Analyze participant patterns across meetings."""
        insights = []
        
        try:
            # Track participant combinations
            participant_sets = []
            for meeting in meeting_data:
                participants = set()
                for segment in meeting['segments']:
                    if segment['speaker']:
                        participants.add(segment['speaker'])
                if participants:
                    participant_sets.append({
                        'participants': participants,
                        'meeting_id': meeting['id'],
                        'title': meeting['title']
                    })
            
            # Find frequent participant combinations
            combination_counts = defaultdict(list)
            for pset in participant_sets:
                # Convert to sorted tuple for consistent hashing
                combo = tuple(sorted(pset['participants']))
                combination_counts[combo].append(pset)
            
            # Find combinations that appear multiple times
            for combo, meetings in combination_counts.items():
                if len(meetings) >= 3 and len(combo) >= 2:
                    insight = CrossMeetingInsight(
                        id=f"participant_pattern_{'_'.join(combo)}",
                        type=InsightType.PARTICIPANT_PATTERN,
                        title=f"Frequent Collaboration: {', '.join(combo)}",
                        description=f"This group of {len(combo)} people has met together {len(meetings)} times, indicating strong collaboration.",
                        confidence=0.8,
                        meetings_involved=[m['meeting_id'] for m in meetings],
                        entities_involved=list(combo),
                        evidence={'participant_group': combo, 'meeting_count': len(meetings)},
                        actionable=False
                    )
                    insights.append(insight)
            
        except Exception as e:
            logger.error(f"Error analyzing participant patterns: {e}")
        
        return insights
    
    def _analyze_action_follow_ups(self, meeting_data: List[Dict[str, Any]]) -> List[CrossMeetingInsight]:
        """Analyze action item follow-ups across meetings."""
        insights = []
        
        try:
            # Look for action items that might be followed up in later meetings
            all_actions = []
            for meeting in meeting_data:
                for action in meeting['summary']['action_items']:
                    all_actions.append({
                        'text': action,
                        'meeting_id': meeting['id'],
                        'date': meeting['date']
                    })
            
            # Sort by date
            all_actions.sort(key=lambda x: x['date'])
            
            # Look for potential follow-ups
            follow_ups = []
            for i, action1 in enumerate(all_actions):
                for action2 in all_actions[i+1:]:
                    # Simple keyword overlap check
                    words1 = set(re.findall(r'\b[a-zA-Z]{3,}\b', action1['text'].lower()))
                    words2 = set(re.findall(r'\b[a-zA-Z]{3,}\b', action2['text'].lower()))
                    
                    overlap = len(words1.intersection(words2))
                    if overlap >= 2:  # At least 2 common words
                        follow_ups.append((action1, action2))
            
            # Create insights for follow-ups
            if follow_ups:
                insight = CrossMeetingInsight(
                    id="action_follow_ups",
                    type=InsightType.ACTION_FOLLOW_UP,
                    title=f"Action Item Follow-ups Detected",
                    description=f"Found {len(follow_ups)} potential action item follow-ups across meetings, showing good continuity.",
                    confidence=0.6,
                    meetings_involved=list(set([f[0]['meeting_id'] for f in follow_ups] + [f[1]['meeting_id'] for f in follow_ups])),
                    entities_involved=[f[0]['text'][:30] for f in follow_ups],
                    evidence={'follow_ups': follow_ups},
                    actionable=False
                )
                insights.append(insight)
            
        except Exception as e:
            logger.error(f"Error analyzing action follow-ups: {e}")
        
        return insights
    
    def _analyze_productivity_trends(self, meeting_data: List[Dict[str, Any]]) -> List[CrossMeetingInsight]:
        """Analyze productivity trends across meetings."""
        insights = []
        
        try:
            # Calculate productivity metrics
            metrics = []
            for meeting in meeting_data:
                duration_minutes = meeting['duration'] / 60 if meeting['duration'] else 0
                action_count = len(meeting['summary']['action_items'])
                decision_count = len(meeting['summary']['decisions'])
                
                # Simple productivity score
                productivity_score = (action_count + decision_count * 2) / max(duration_minutes / 60, 0.5)
                
                metrics.append({
                    'meeting_id': meeting['id'],
                    'date': meeting['date'],
                    'productivity_score': productivity_score,
                    'duration_minutes': duration_minutes,
                    'action_count': action_count,
                    'decision_count': decision_count
                })
            
            # Sort by date
            metrics.sort(key=lambda x: x['date'])
            
            # Analyze trend
            if len(metrics) >= 3:
                scores = [m['productivity_score'] for m in metrics]
                
                # Simple trend analysis
                first_half = scores[:len(scores)//2]
                second_half = scores[len(scores)//2:]
                
                avg_first = sum(first_half) / len(first_half)
                avg_second = sum(second_half) / len(second_half)
                
                improvement = (avg_second - avg_first) / avg_first if avg_first > 0 else 0
                
                if abs(improvement) > 0.2:  # 20% change
                    trend = "improving" if improvement > 0 else "declining"
                    
                    insight = CrossMeetingInsight(
                        id="productivity_trend",
                        type=InsightType.PRODUCTIVITY_TREND,
                        title=f"Meeting Productivity is {trend.title()}",
                        description=f"Analysis shows meeting productivity has been {trend} by {abs(improvement)*100:.1f}% over recent meetings.",
                        confidence=0.7,
                        meetings_involved=[m['meeting_id'] for m in metrics],
                        entities_involved=[],
                        evidence={'trend': trend, 'improvement': improvement, 'metrics': metrics},
                        actionable=True if trend == "declining" else False
                    )
                    insights.append(insight)
            
        except Exception as e:
            logger.error(f"Error analyzing productivity trends: {e}")
        
        return insights
    
    def _analyze_topic_evolution(self, meeting_data: List[Dict[str, Any]]) -> List[CrossMeetingInsight]:
        """Analyze how topics evolve over time."""
        insights = []
        
        try:
            # Track topics over time
            topic_timeline = []
            for meeting in meeting_data:
                topics = self._extract_topics(meeting['transcript_text'])
                topic_timeline.append({
                    'meeting_id': meeting['id'],
                    'date': meeting['date'],
                    'topics': topics
                })
            
            # Sort by date
            topic_timeline.sort(key=lambda x: x['date'])
            
            # Find evolving topics
            if len(topic_timeline) >= 3:
                # Look for topics that appear and disappear
                all_topics = set()
                for entry in topic_timeline:
                    all_topics.update(entry['topics'].keys())
                
                evolving_topics = []
                for topic in all_topics:
                    appearances = []
                    for entry in topic_timeline:
                        if topic in entry['topics']:
                            appearances.append({
                                'date': entry['date'],
                                'weight': entry['topics'][topic],
                                'meeting_id': entry['meeting_id']
                            })
                    
                    if len(appearances) >= 2:
                        # Check if there's a trend in weight
                        weights = [a['weight'] for a in appearances]
                        if max(weights) - min(weights) > 0.02:  # Significant change
                            evolving_topics.append({
                                'topic': topic,
                                'appearances': appearances
                            })
                
                if evolving_topics:
                    insight = CrossMeetingInsight(
                        id="topic_evolution",
                        type=InsightType.TOPIC_EVOLUTION,
                        title="Topics are Evolving Over Time",
                        description=f"Detected {len(evolving_topics)} topics that are changing in importance across meetings.",
                        confidence=0.6,
                        meetings_involved=[a['meeting_id'] for t in evolving_topics for a in t['appearances']],
                        entities_involved=[t['topic'] for t in evolving_topics],
                        evidence={'evolving_topics': evolving_topics},
                        actionable=False
                    )
                    insights.append(insight)
            
        except Exception as e:
            logger.error(f"Error analyzing topic evolution: {e}")
        
        return insights
    
    def _analyze_collaboration_network(self, meeting_data: List[Dict[str, Any]]) -> List[CrossMeetingInsight]:
        """Analyze collaboration network structure."""
        insights = []
        
        try:
            # Build collaboration network
            collaboration_pairs = defaultdict(int)
            all_participants = set()
            
            for meeting in meeting_data:
                participants = set()
                for segment in meeting['segments']:
                    if segment['speaker']:
                        participants.add(segment['speaker'])
                        all_participants.add(segment['speaker'])
                
                # Count all pairs in this meeting
                participants_list = list(participants)
                for i in range(len(participants_list)):
                    for j in range(i+1, len(participants_list)):
                        pair = tuple(sorted([participants_list[i], participants_list[j]]))
                        collaboration_pairs[pair] += 1
            
            # Find strongest collaborations
            strong_collaborations = []
            for pair, count in collaboration_pairs.items():
                if count >= 3:  # Collaborated in 3+ meetings
                    strong_collaborations.append({
                        'pair': pair,
                        'collaboration_count': count
                    })
            
            if strong_collaborations:
                insight = CrossMeetingInsight(
                    id="collaboration_network",
                    type=InsightType.COLLABORATION_NETWORK,
                    title="Strong Collaboration Patterns Identified",
                    description=f"Found {len(strong_collaborations)} pairs of people who collaborate frequently.",
                    confidence=0.8,
                    meetings_involved=[],
                    entities_involved=[person for collab in strong_collaborations for person in collab['pair']],
                    evidence={'strong_collaborations': strong_collaborations},
                    actionable=False
                )
                insights.append(insight)
            
        except Exception as e:
            logger.error(f"Error analyzing collaboration network: {e}")
        
        return insights


# Global service instance
cross_meeting_insights_service = CrossMeetingInsightsService()