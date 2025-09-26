"""
Analytics Service
Comprehensive meeting analytics, insights, and performance metrics calculation.
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from statistics import mean, median
from collections import defaultdict
from models import db, Analytics, Meeting, Participant, Task, Session, Segment
from services.openai_client_manager import get_openai_client


class AnalyticsService:
    """Service for calculating comprehensive meeting analytics and insights."""
    
    def __init__(self):
        self.client = get_openai_client()
        
        # Keywords for different analysis
        self.decision_keywords = [
            "decide", "decision", "agreed", "consensus", "vote", "choose",
            "final", "settled", "resolved", "conclusion"
        ]
        
        self.idea_keywords = [
            "idea", "suggestion", "propose", "think", "concept", "approach",
            "solution", "way", "method", "strategy"
        ]
        
        self.disagreement_keywords = [
            "disagree", "no", "wrong", "incorrect", "but", "however",
            "against", "oppose", "different", "alternative"
        ]

    async def analyze_meeting(self, meeting_id: int) -> Dict:
        """Perform comprehensive analysis of a meeting."""
        meeting = Meeting.query.get(meeting_id)
        if not meeting:
            return {"success": False, "message": "Meeting not found"}
        
        try:
            # Create or get analytics record
            analytics = Analytics.query.filter_by(meeting_id=meeting_id).first()
            if not analytics:
                analytics = Analytics(meeting_id=meeting_id)
                db.session.add(analytics)
            
            analytics.start_analysis()
            db.session.commit()
            
            # Perform various analyses
            await self._analyze_basic_metrics(analytics, meeting)
            await self._analyze_engagement(analytics, meeting)
            await self._analyze_sentiment(analytics, meeting)
            await self._analyze_productivity(analytics, meeting)
            await self._analyze_content(analytics, meeting)
            await self._analyze_communication_patterns(analytics, meeting)
            await self._analyze_efficiency(analytics, meeting)
            await self._generate_insights(analytics, meeting)
            
            # Calculate overall effectiveness score
            analytics.calculate_effectiveness_score()
            
            analytics.complete_analysis()
            db.session.commit()
            
            return {
                "success": True,
                "message": "Meeting analysis completed",
                "analytics": analytics.to_dict(include_detailed_data=True)
            }
            
        except Exception as e:
            if analytics:
                analytics.fail_analysis(str(e))
                db.session.commit()
            return {"success": False, "message": f"Analysis failed: {str(e)}"}

    async def _analyze_basic_metrics(self, analytics: Analytics, meeting: Meeting):
        """Analyze basic meeting metrics."""
        # Duration analysis
        if meeting.actual_start and meeting.actual_end:
            duration = meeting.actual_end - meeting.actual_start
            analytics.total_duration_minutes = duration.total_seconds() / 60
        
        if meeting.scheduled_start and meeting.scheduled_end and analytics.total_duration_minutes:
            scheduled_duration = (meeting.scheduled_end - meeting.scheduled_start).total_seconds() / 60
            analytics.actual_vs_scheduled_ratio = analytics.total_duration_minutes / scheduled_duration
        
        # Participant count
        participants = Participant.query.filter_by(meeting_id=meeting.id).all()
        analytics.participant_count = len(participants)
        analytics.unique_speakers = len([p for p in participants if p.talk_time_seconds and p.talk_time_seconds > 0])
        
        # Word count from transcript
        if meeting.session:
            segments = Segment.query.filter_by(session_id=meeting.session.id, is_final=True).all()
            analytics.word_count = sum(len(segment.text.split()) for segment in segments)

    async def _analyze_engagement(self, analytics: Analytics, meeting: Meeting):
        """Analyze participant engagement metrics."""
        participants = Participant.query.filter_by(meeting_id=meeting.id).all()
        
        if not participants:
            return
        
        # Calculate engagement metrics
        talk_times = [p.talk_time_seconds or 0 for p in participants]
        engagement_scores = [p.engagement_score or 0 for p in participants]
        
        if talk_times:
            analytics.average_talk_time_per_person = sum(talk_times) / len(talk_times) / 60  # Convert to minutes
            
            # Talk time distribution
            total_talk_time = sum(talk_times)
            if total_talk_time > 0:
                distribution = {
                    p.name: (p.talk_time_seconds or 0) / total_talk_time 
                    for p in participants
                }
                analytics.talk_time_distribution = distribution
                
                # Check if participation is balanced (no single speaker dominates)
                max_percentage = max(distribution.values()) if distribution else 0
                analytics.dominant_speaker_percentage = max_percentage
                analytics.balanced_participation = max_percentage < 0.6  # No one speaks more than 60%
        
        if engagement_scores:
            analytics.overall_engagement_score = sum(engagement_scores) / len(engagement_scores)
        
        # Find most active and quietest participants
        if participants:
            most_active = max(participants, key=lambda p: p.talk_time_seconds or 0)
            quietest = min(participants, key=lambda p: p.talk_time_seconds or 0)
            analytics.most_active_participant = most_active.name
            analytics.quietest_participant = quietest.name
        
        # Interruption analysis
        interruptions = sum(p.interruption_count or 0 for p in participants)
        if analytics.total_duration_minutes:
            analytics.interruption_frequency = interruptions / analytics.total_duration_minutes

    async def _analyze_sentiment(self, analytics: Analytics, meeting: Meeting):
        """Analyze sentiment patterns throughout the meeting."""
        participants = Participant.query.filter_by(meeting_id=meeting.id).all()
        
        sentiment_scores = []
        for participant in participants:
            if participant.sentiment_score is not None:
                sentiment_scores.append(participant.sentiment_score)
        
        if sentiment_scores:
            analytics.overall_sentiment_score = sum(sentiment_scores) / len(sentiment_scores)
        
        # Analyze sentiment trend over time (would need more detailed timestamp data)
        if meeting.session:
            sentiment_trend = await self._analyze_sentiment_trend(meeting.session)
            analytics.sentiment_trend = sentiment_trend
            
            # Identify positive and negative moments
            positive_moments = [i for i, score in enumerate(sentiment_trend) if score > 0.5]
            negative_moments = [i for i, score in enumerate(sentiment_trend) if score < -0.2]
            analytics.positive_moments = positive_moments
            analytics.negative_moments = negative_moments

    async def _analyze_sentiment_trend(self, session: Session) -> List[float]:
        """Analyze sentiment trend over time during the meeting."""
        if not self.client:
            return [0.0]
        
        segments = Segment.query.filter_by(
            session_id=session.id, 
            is_final=True
        ).order_by(Segment.timestamp).all()
        
        if not segments:
            return [0.0]
        
        # Group segments into time windows (e.g., 5-minute intervals)
        window_size = 5 * 60  # 5 minutes in seconds
        time_windows = defaultdict(list)
        
        start_time = segments[0].timestamp
        for segment in segments:
            time_diff = (segment.timestamp - start_time).total_seconds()
            window_index = int(time_diff // window_size)
            time_windows[window_index].append(segment.text)
        
        # Analyze sentiment for each window
        sentiment_trend = []
        for window_index in sorted(time_windows.keys()):
            window_text = " ".join(time_windows[window_index])
            sentiment = await self._get_text_sentiment(window_text)
            sentiment_trend.append(sentiment)
        
        return sentiment_trend

    async def _get_text_sentiment(self, text: str) -> float:
        """Get sentiment score for a piece of text."""
        if not self.client or not text.strip():
            return 0.0
        
        try:
            response = await self.client.chat.completions.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the sentiment of the following text. Return only a number between -1 (very negative) and 1 (very positive)."
                    },
                    {"role": "user", "content": text[:500]}  # Limit text length
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            sentiment_text = response.choices[0].message.content.strip()
            return float(sentiment_text)
        except Exception:
            return 0.0

    async def _analyze_productivity(self, analytics: Analytics, meeting: Meeting):
        """Analyze meeting productivity metrics."""
        # Task analysis
        tasks = Task.query.filter_by(meeting_id=meeting.id).all()
        analytics.action_items_created = len(tasks)
        
        # Decision analysis
        if meeting.session:
            segments = Segment.query.filter_by(session_id=meeting.session.id, is_final=True).all()
            full_text = " ".join(segment.text.lower() for segment in segments)
            
            # Count decisions made
            decision_count = sum(1 for keyword in self.decision_keywords if keyword in full_text)
            analytics.decisions_made_count = decision_count
            
            # Analyze agenda completion (if agenda exists)
            if meeting.agenda:
                agenda_completion = await self._analyze_agenda_completion(meeting.agenda, full_text)
                analytics.agenda_completion_rate = agenda_completion
        
        # Follow-up analysis
        unresolved_count = len([task for task in tasks if task.status in ['todo', 'in_progress']])
        analytics.unresolved_issues_count = unresolved_count
        analytics.follow_up_required = unresolved_count > 0

    async def _analyze_agenda_completion(self, agenda: Dict, transcript: str) -> float:
        """Analyze how well the meeting covered the planned agenda."""
        if not agenda or not isinstance(agenda, dict):
            return 0.0
        
        agenda_items = agenda.get('items', [])
        if not agenda_items:
            return 0.0
        
        covered_items = 0
        for item in agenda_items:
            item_text = item.get('title', '') + ' ' + item.get('description', '')
            # Simple keyword matching - could be enhanced with semantic analysis
            keywords = item_text.lower().split()
            if any(keyword in transcript for keyword in keywords[:3]):  # Check first 3 keywords
                covered_items += 1
        
        return covered_items / len(agenda_items)

    async def _analyze_content(self, analytics: Analytics, meeting: Meeting):
        """Analyze meeting content patterns."""
        if not meeting.session:
            return
        
        segments = Segment.query.filter_by(session_id=meeting.session.id, is_final=True).all()
        full_text = " ".join(segment.text.lower() for segment in segments)
        
        # Count different types of content
        analytics.question_count = full_text.count('?')
        analytics.idea_count = sum(1 for keyword in self.idea_keywords if keyword in full_text)
        analytics.disagreement_count = sum(1 for keyword in self.disagreement_keywords if keyword in full_text)
        
        # Extract key topics and keywords
        if self.client:
            topics = await self._extract_key_topics(full_text)
            analytics.key_topics = topics
            
            keywords = await self._extract_keywords(full_text)
            analytics.topic_keywords = keywords

    async def _extract_key_topics(self, text: str) -> List[str]:
        """Extract main topics discussed in the meeting."""
        if not self.client:
            return []
        
        try:
            response = await self.client.chat.completions.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Extract the 5 main topics discussed in this meeting. Return as a JSON array of strings."
                    },
                    {"role": "user", "content": text[:2000]}
                ],
                temperature=0.2,
                max_tokens=200
            )
            
            topics = json.loads(response.choices[0].message.content)
            return topics if isinstance(topics, list) else []
        except Exception:
            return []

    async def _extract_keywords(self, text: str) -> List[str]:
        """Extract key terms and phrases from the meeting."""
        # Simple keyword extraction - could be enhanced with NLP libraries
        words = text.split()
        word_freq = defaultdict(int)
        
        for word in words:
            word = word.strip('.,!?').lower()
            if len(word) > 3:  # Skip very short words
                word_freq[word] += 1
        
        # Return top 10 most frequent words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10]]

    async def _analyze_communication_patterns(self, analytics: Analytics, meeting: Meeting):
        """Analyze communication patterns and dynamics."""
        if not meeting.session:
            return
        
        segments = Segment.query.filter_by(session_id=meeting.session.id, is_final=True).all()
        
        # Analyze consensus moments (simplified)
        consensus_indicators = ["everyone agrees", "we all think", "consensus", "unanimous"]
        consensus_moments = []
        
        for i, segment in enumerate(segments):
            if any(indicator in segment.text.lower() for indicator in consensus_indicators):
                consensus_moments.append(i)
        
        analytics.consensus_moments = consensus_moments

    async def _analyze_efficiency(self, analytics: Analytics, meeting: Meeting):
        """Analyze meeting efficiency metrics."""
        # Basic efficiency calculation
        efficiency_score = 0.5  # Base score
        
        # Boost for task creation
        if analytics.action_items_created and analytics.action_items_created > 0:
            efficiency_score += 0.2
        
        # Boost for decision making
        if analytics.decisions_made_count and analytics.decisions_made_count > 0:
            efficiency_score += 0.2
        
        # Penalty for going over scheduled time
        if analytics.actual_vs_scheduled_ratio and analytics.actual_vs_scheduled_ratio > 1.2:
            efficiency_score -= 0.1
        
        analytics.meeting_efficiency_score = min(1.0, max(0.0, efficiency_score))
        
        # Estimate time spent on agenda vs off-topic
        if analytics.agenda_completion_rate:
            analytics.time_spent_on_agenda = analytics.agenda_completion_rate * 100
            analytics.off_topic_time_percentage = max(0, 100 - analytics.time_spent_on_agenda)

    async def _generate_insights(self, analytics: Analytics, meeting: Meeting):
        """Generate AI-powered insights and recommendations."""
        if not self.client:
            return
        
        # Prepare meeting summary for AI analysis
        meeting_summary = {
            "duration": analytics.total_duration_minutes,
            "participants": analytics.participant_count,
            "engagement": analytics.overall_engagement_score,
            "sentiment": analytics.overall_sentiment_score,
            "tasks_created": analytics.action_items_created,
            "decisions_made": analytics.decisions_made_count
        }
        
        try:
            response = await self.client.chat.completions.acreate(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze this meeting data and provide insights and recommendations.
                        Return a JSON object with:
                        {
                          "insights": ["insight 1", "insight 2", ...],
                          "recommendations": ["recommendation 1", "recommendation 2", ...]
                        }"""
                    },
                    {"role": "user", "content": json.dumps(meeting_summary)}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content)
            analytics.insights_generated = result.get("insights", [])
            analytics.recommendations = result.get("recommendations", [])
            
        except Exception as e:
            print(f"Insight generation failed: {e}")

    def get_workspace_analytics_summary(self, workspace_id: int, days: int = 30) -> Dict:
        """Get analytics summary for a workspace over specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        meetings = Meeting.query.filter(
            Meeting.workspace_id == workspace_id,
            Meeting.created_at >= cutoff_date
        ).all()
        
        if not meetings:
            return {"meetings": [], "summary": {}}
        
        analytics_records = []
        for meeting in meetings:
            analytics = Analytics.query.filter_by(meeting_id=meeting.id).first()
            if analytics and analytics.is_analysis_complete:
                analytics_records.append(analytics)
        
        if not analytics_records:
            return {"meetings": [m.to_dict() for m in meetings], "summary": {}}
        
        # Calculate workspace averages
        avg_effectiveness = mean([a.meeting_effectiveness_score for a in analytics_records if a.meeting_effectiveness_score])
        avg_engagement = mean([a.overall_engagement_score for a in analytics_records if a.overall_engagement_score])
        avg_sentiment = mean([a.overall_sentiment_score for a in analytics_records if a.overall_sentiment_score])
        total_tasks = sum(a.action_items_created or 0 for a in analytics_records)
        total_decisions = sum(a.decisions_made_count or 0 for a in analytics_records)
        
        return {
            "meetings": [m.to_dict() for m in meetings],
            "analytics": [a.to_dict() for a in analytics_records],
            "summary": {
                "total_meetings": len(meetings),
                "analyzed_meetings": len(analytics_records),
                "avg_effectiveness": round(avg_effectiveness, 2) if avg_effectiveness else 0,
                "avg_engagement": round(avg_engagement, 2) if avg_engagement else 0,
                "avg_sentiment": round(avg_sentiment, 2) if avg_sentiment else 0,
                "total_tasks_created": total_tasks,
                "total_decisions_made": total_decisions,
                "productivity_score": round((total_tasks + total_decisions) / len(meetings), 2) if meetings else 0
            }
        }


# Singleton instance
analytics_service = AnalyticsService()