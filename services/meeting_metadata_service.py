"""
Meeting Metadata Service
Service for managing meeting metadata, participant data, and speaker diarization.
"""

import json
import re
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass
from models import db, Meeting, Participant, Session, Segment
from services.openai_client_manager import get_openai_client


@dataclass
class SpeakerInfo:
    """Information about a detected speaker."""
    speaker_id: str
    name: Optional[str] = None
    confidence: float = 0.0
    total_segments: int = 0
    total_words: int = 0
    total_duration: float = 0.0
    first_appearance: Optional[datetime] = None
    last_appearance: Optional[datetime] = None


@dataclass
class ParticipantMetrics:
    """Comprehensive metrics for a meeting participant."""
    talk_time_seconds: float = 0.0
    word_count: int = 0
    interruption_count: int = 0
    question_count: int = 0
    sentiment_scores: List[float] = None
    engagement_indicators: List[str] = None


class MeetingMetadataService:
    """Service for extracting and managing meeting metadata and participant information."""
    
    def __init__(self):
        self.client = get_openai_client()
        self.question_patterns = [
            r'\?',  # Ends with question mark
            r'^(?:what|how|why|when|where|who|which|can|could|would|should|will|is|are|do|does|did)',
            r'(?:what do you think|what are your thoughts|any questions|thoughts on)',
        ]
        
        self.engagement_patterns = {
            'agreement': [r'\b(yes|yeah|absolutely|exactly|right|correct|agree|definitely)\b'],
            'disagreement': [r'\b(no|nope|disagree|wrong|incorrect|not really)\b'],
            'enthusiasm': [r'\b(great|awesome|excellent|fantastic|amazing|love it)\b'],
            'uncertainty': [r'\b(maybe|perhaps|not sure|hmm|um|uh)\b'],
            'idea': [r'\b(idea|suggestion|propose|think we should|what if|how about)\b']
        }

    async def process_meeting_metadata(self, meeting_id: int) -> Dict:
        """Process complete meeting metadata including participants and diarization."""
        meeting = Meeting.query.get(meeting_id)
        if not meeting or not meeting.session:
            return {"success": False, "message": "Meeting or session not found"}
        
        try:
            # Analyze speakers and participants
            speaker_analysis = await self._analyze_speakers(meeting.session)
            
            # Create or update participant records
            participants = await self._create_participants(meeting, speaker_analysis)
            
            # Calculate participant metrics
            for participant in participants:
                metrics = await self._calculate_participant_metrics(participant, meeting.session)
                self._update_participant_with_metrics(participant, metrics)
            
            # Update meeting metadata
            await self._update_meeting_metadata(meeting, participants)
            
            db.session.commit()
            
            return {
                "success": True,
                "message": "Meeting metadata processed successfully",
                "participants_count": len(participants),
                "speakers_detected": len(speaker_analysis),
                "participants": [p.to_dict() for p in participants]
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"Processing failed: {str(e)}"}

    async def _analyze_speakers(self, session: Session) -> Dict[str, SpeakerInfo]:
        """Analyze speakers from session segments using AI and patterns."""
        segments = Segment.query.filter_by(
            session_id=session.id,
            is_final=True
        ).order_by(Segment.timestamp).all()
        
        if not segments:
            return {}
        
        # Group segments by speaker
        speaker_segments = defaultdict(list)
        for segment in segments:
            speaker_id = getattr(segment, 'speaker', 'Unknown')
            speaker_segments[speaker_id].append(segment)
        
        # Analyze each speaker
        speaker_info = {}
        for speaker_id, segments in speaker_segments.items():
            info = await self._analyze_single_speaker(speaker_id, segments)
            speaker_info[speaker_id] = info
        
        # Use AI to identify actual names if possible
        speaker_info = await self._identify_speaker_names(speaker_info, segments)
        
        return speaker_info

    async def _analyze_single_speaker(self, speaker_id: str, segments: List) -> SpeakerInfo:
        """Analyze metrics for a single speaker."""
        if not segments:
            return SpeakerInfo(speaker_id=speaker_id)
        
        total_words = sum(len(segment.text.split()) for segment in segments)
        total_duration = sum(getattr(segment, 'duration', 2.0) for segment in segments)
        
        first_time = min(segment.timestamp for segment in segments)
        last_time = max(segment.timestamp for segment in segments)
        
        return SpeakerInfo(
            speaker_id=speaker_id,
            confidence=0.8,  # Base confidence for speaker detection
            total_segments=len(segments),
            total_words=total_words,
            total_duration=total_duration,
            first_appearance=first_time,
            last_appearance=last_time
        )

    async def _identify_speaker_names(self, speaker_info: Dict[str, SpeakerInfo], 
                                    all_segments: List) -> Dict[str, SpeakerInfo]:
        """Use AI to identify actual speaker names from transcript."""
        if not self.client or len(speaker_info) <= 1:
            return speaker_info
        
        # Build a sample transcript for analysis
        transcript_sample = []
        for segment in all_segments[:20]:  # First 20 segments
            speaker = getattr(segment, 'speaker', 'Unknown')
            text = segment.text.strip()
            transcript_sample.append(f"{speaker}: {text}")
        
        sample_text = "\n".join(transcript_sample)
        
        system_prompt = """Analyze this meeting transcript and identify the actual names of participants.
        
        Look for:
        1. Self-introductions ("Hi, I'm John", "This is Sarah speaking")
        2. Direct address ("Thanks John", "Sarah, what do you think?")
        3. Name mentions in context
        
        Return a JSON mapping of speaker IDs to likely real names:
        {
          "Speaker_1": "John Smith",
          "Speaker_2": "Sarah Johnson",
          "Speaker_3": null
        }
        
        Only include names you're confident about. Use null for uncertain cases."""
        
        try:
            response = await self.client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Transcript sample:\n{sample_text}"}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            name_mapping = json.loads(response.choices[0].message.content)
            
            # Update speaker info with identified names
            for speaker_id, info in speaker_info.items():
                if speaker_id in name_mapping and name_mapping[speaker_id]:
                    info.name = name_mapping[speaker_id]
                    info.confidence = min(0.9, info.confidence + 0.1)
            
        except Exception as e:
            print(f"Speaker name identification failed: {e}")
        
        return speaker_info

    async def _create_participants(self, meeting: Meeting, 
                                 speaker_analysis: Dict[str, SpeakerInfo]) -> List[Participant]:
        """Create participant records for the meeting."""
        participants = []
        
        for speaker_id, info in speaker_analysis.items():
            # Check if participant already exists
            existing = Participant.query.filter_by(
                meeting_id=meeting.id,
                speaker_id=speaker_id
            ).first()
            
            if existing:
                participant = existing
            else:
                participant = Participant(
                    meeting_id=meeting.id,
                    speaker_id=speaker_id,
                    name=info.name or f"Participant {speaker_id}",
                    confidence_score=info.confidence,
                    joined_at=info.first_appearance,
                    left_at=info.last_appearance
                )
                db.session.add(participant)
            
            participants.append(participant)
        
        return participants

    async def _calculate_participant_metrics(self, participant: Participant, 
                                           session: Session) -> ParticipantMetrics:
        """Calculate comprehensive metrics for a participant."""
        segments = Segment.query.filter_by(
            session_id=session.id,
            speaker=participant.speaker_id,
            is_final=True
        ).all()
        
        if not segments:
            return ParticipantMetrics()
        
        # Basic metrics
        total_words = sum(len(segment.text.split()) for segment in segments)
        total_duration = sum(getattr(segment, 'duration', 2.0) for segment in segments)
        
        # Count questions
        question_count = self._count_questions(segments)
        
        # Count interruptions (basic heuristic)
        interruption_count = self._count_interruptions(segments)
        
        # Analyze sentiment
        sentiment_scores = await self._analyze_sentiment(segments)
        
        # Identify engagement indicators
        engagement_indicators = self._identify_engagement(segments)
        
        return ParticipantMetrics(
            talk_time_seconds=total_duration,
            word_count=total_words,
            interruption_count=interruption_count,
            question_count=question_count,
            sentiment_scores=sentiment_scores,
            engagement_indicators=engagement_indicators
        )

    def _count_questions(self, segments: List) -> int:
        """Count questions asked by participant."""
        question_count = 0
        
        for segment in segments:
            text = segment.text.lower().strip()
            
            # Check for question mark
            if '?' in text:
                question_count += text.count('?')
                continue
            
            # Check for question patterns
            for pattern in self.question_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    question_count += 1
                    break
        
        return question_count

    def _count_interruptions(self, segments: List) -> int:
        """Count likely interruptions (basic heuristic)."""
        interruption_count = 0
        
        for i, segment in enumerate(segments):
            # Look for short segments followed by another speaker
            if (len(segment.text.split()) < 5 and 
                getattr(segment, 'duration', 2.0) < 3.0):
                interruption_count += 1
        
        return max(0, interruption_count - 2)  # Remove false positives

    async def _analyze_sentiment(self, segments: List) -> List[float]:
        """Analyze sentiment for participant's contributions."""
        if not self.client or not segments:
            return []
        
        # Sample segments for sentiment analysis
        sample_texts = [segment.text for segment in segments[:10]]
        combined_text = " ".join(sample_texts)
        
        try:
            response = await self.client.chat.completions.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "Analyze the sentiment of this text. Return a JSON array of sentiment scores between -1 (very negative) and 1 (very positive) for each major point or sentence."
                    },
                    {"role": "user", "content": combined_text}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result = json.loads(response.choices[0].message.content)
            return result if isinstance(result, list) else [0.0]
            
        except Exception:
            return [0.0]  # Neutral sentiment as fallback

    def _identify_engagement(self, segments: List) -> List[str]:
        """Identify engagement patterns in participant's speech."""
        engagement_indicators = []
        
        all_text = " ".join(segment.text.lower() for segment in segments)
        
        for engagement_type, patterns in self.engagement_patterns.items():
            for pattern in patterns:
                if re.search(pattern, all_text, re.IGNORECASE):
                    engagement_indicators.append(engagement_type)
                    break
        
        return engagement_indicators

    def _update_participant_with_metrics(self, participant: Participant, 
                                       metrics: ParticipantMetrics):
        """Update participant record with calculated metrics."""
        participant.talk_time_seconds = metrics.talk_time_seconds
        participant.word_count = metrics.word_count
        participant.interruption_count = metrics.interruption_count
        participant.question_count = metrics.question_count
        
        # Calculate derived metrics
        if metrics.sentiment_scores:
            participant.sentiment_score = sum(metrics.sentiment_scores) / len(metrics.sentiment_scores)
        
        # Basic engagement score calculation
        engagement_score = 0.5  # Base score
        if metrics.word_count > 100:
            engagement_score += 0.2
        if metrics.question_count > 0:
            engagement_score += 0.2
        if 'agreement' in metrics.engagement_indicators:
            engagement_score += 0.1
        
        participant.engagement_score = min(1.0, engagement_score)

    async def _update_meeting_metadata(self, meeting: Meeting, participants: List[Participant]):
        """Update meeting metadata based on participant analysis."""
        if not participants:
            return
        
        # Calculate total duration
        total_duration = sum(p.talk_time_seconds for p in participants if p.talk_time_seconds)
        
        # Update meeting fields
        if not meeting.actual_start and participants:
            earliest_join = min(p.joined_at for p in participants if p.joined_at)
            meeting.actual_start = earliest_join
        
        if not meeting.actual_end and participants:
            latest_leave = max(p.left_at for p in participants if p.left_at)
            meeting.actual_end = latest_leave
        
        # Update participant count
        meeting.participant_count = len(participants)

    def get_meeting_participant_summary(self, meeting_id: int) -> Dict:
        """Get a summary of meeting participants and their contributions."""
        participants = Participant.query.filter_by(meeting_id=meeting_id).all()
        
        if not participants:
            return {"participants": [], "summary": {}}
        
        total_talk_time = sum(p.talk_time_seconds or 0 for p in participants)
        total_words = sum(p.word_count or 0 for p in participants)
        
        # Find most active participant
        most_active = max(participants, key=lambda p: p.talk_time_seconds or 0)
        
        # Find quietest participant
        quietest = min(participants, key=lambda p: p.talk_time_seconds or 0)
        
        # Calculate participation balance
        if participants and total_talk_time > 0:
            talk_times = [p.talk_time_seconds or 0 for p in participants]
            max_time = max(talk_times)
            participation_balance = 1 - (max_time / total_talk_time) if total_talk_time > 0 else 0
        else:
            participation_balance = 0
        
        return {
            "participants": [p.to_dict() for p in participants],
            "summary": {
                "total_participants": len(participants),
                "total_talk_time": total_talk_time,
                "total_words": total_words,
                "most_active": most_active.name if most_active else None,
                "quietest": quietest.name if quietest else None,
                "participation_balance": participation_balance,
                "average_sentiment": sum(p.sentiment_score or 0 for p in participants) / len(participants)
            }
        }


# Singleton instance
meeting_metadata_service = MeetingMetadataService()