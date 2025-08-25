"""
Analysis Service (M3) - AI-powered meeting insights generation.

This service handles the generation of Actions, Decisions, and Risks
from meeting transcripts using configurable AI engines.
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

from flask import current_app
from sqlalchemy.orm import Session as DbSession

from app import db
from models.session import Session
from models.segment import Segment
from models.summary import Summary

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for generating AI-powered meeting insights."""
    
    # Analysis prompt template with strict JSON requirements
    ANALYSIS_PROMPT = """
    You are a professional meeting analyst. Analyse this meeting transcript and extract key insights in British English. 
    Be concise, specific, and never fabricate information. If information is missing or unclear, use "unknown".
    
    Extract:
    1. SUMMARY: A brief meeting summary in markdown format
    2. ACTIONS: Tasks with owners and deadlines 
    3. DECISIONS: Key decisions made
    4. RISKS: Identified risks with potential mitigations
    
    Return ONLY valid JSON in this exact format:
    {
        "summary_md": "Brief meeting summary in markdown format",
        "actions": [{"text": "Action description", "owner": "Person or unknown", "due": "Date or unknown"}],
        "decisions": [{"text": "Decision description"}],
        "risks": [{"text": "Risk description", "mitigation": "Suggested mitigation or unknown"}]
    }
    
    Meeting transcript:
    {transcript}
    """
    
    @staticmethod
    def generate_summary(session_id: int) -> Dict:
        """
        Generate AI-powered summary for a session.
        
        Args:
            session_id: ID of the session to analyse
            
        Returns:
            Dict containing the generated summary data
            
        Raises:
            ValueError: If session not found or no segments available
        """
        logger.info(f"Generating summary for session {session_id}")
        
        # Load session and segments
        session = db.session.get(Session, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Load final segments ordered by timestamp
        final_segments = (
            db.session.query(Segment)
            .filter(Segment.session_id == session_id, Segment.kind == 'final')
            .order_by(Segment.start_ms)
            .all()
        )
        
        # Determine analysis engine from configuration
        engine = current_app.config.get('ANALYSIS_ENGINE', 'mock')
        
        if not final_segments:
            logger.warning(f"No final segments found for session {session_id}")
            # Create empty summary for sessions without transcript
            summary_data = {
                'summary_md': 'No transcript available for analysis.',
                'actions': [],
                'decisions': [],
                'risks': []
            }
        else:
            # Build context string from segments
            context = AnalysisService._build_context(final_segments)
            logger.info(f"Built context with {len(context)} characters for session {session_id}")
            
            # Generate insights using configured engine
            if engine == 'openai_gpt':
                summary_data = AnalysisService._analyse_with_openai(context)
            else:
                summary_data = AnalysisService._analyse_with_mock(context, final_segments)
        
        # Persist summary to database
        summary = AnalysisService._persist_summary(session_id, summary_data, engine)
        
        logger.info(f"Generated summary {summary.id} for session {session_id} using {engine}")
        return summary.to_dict()
    
    @staticmethod
    def get_session_summary(session_id: int) -> Optional[Dict]:
        """
        Get the latest summary for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Summary dictionary or None if not found
        """
        summary = (
            db.session.query(Summary)
            .filter(Summary.session_id == session_id)
            .order_by(Summary.created_at.desc())
            .first()
        )
        
        return summary.to_dict() if summary else None
    
    @staticmethod
    def _build_context(segments: List[Segment]) -> str:
        """
        Build bounded context string from final segments.
        
        Args:
            segments: List of final segments ordered by time
            
        Returns:
            Context string limited to configured character count
        """
        max_chars = current_app.config.get('SUMMARY_CONTEXT_CHARS', 12000)
        
        # Build full transcript
        transcript_parts = []
        for segment in segments:
            # Format with timestamp for context
            time_str = f"[{segment.start_time_formatted}]" if hasattr(segment, 'start_time_formatted') else f"[{segment.start_ms//1000}s]"
            transcript_parts.append(f"{time_str} {segment.text}")
        
        full_transcript = " ".join(transcript_parts)
        
        # Truncate if too long (keep ending for recent context)
        if len(full_transcript) > max_chars:
            truncated = full_transcript[-max_chars:]
            # Try to start at a sentence boundary
            sentence_start = truncated.find('. ')
            if sentence_start > 0 and sentence_start < 1000:  # Don't cut too much
                truncated = truncated[sentence_start + 2:]
            full_transcript = "..." + truncated
        
        return full_transcript
    
    @staticmethod
    def _analyse_with_openai(context: str) -> Dict:
        """
        Analyse context using OpenAI GPT.
        
        Args:
            context: Meeting transcript context
            
        Returns:
            Analysis results dictionary
        """
        try:
            from openai import OpenAI
            
            import os
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OpenAI API key not found, falling back to mock analysis")
                return AnalysisService._analyse_with_mock(context, [])
            
            client = OpenAI(api_key=api_key)
            
            # First attempt
            prompt = AnalysisService.ANALYSIS_PROMPT.format(transcript=context)
            
            response = client.chat.completions.create(
                model="gpt-5",  # Use latest model as per blueprint
                messages=[
                    {"role": "system", "content": "You are a professional meeting analyst. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3  # Lower temperature for consistent structured output
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # Validate required keys
            required_keys = ['summary_md', 'actions', 'decisions', 'risks']
            if not all(key in result for key in required_keys):
                raise ValueError(f"Missing required keys in response: {required_keys}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed on first attempt: {e}")
            
            # Retry with stricter prompt
            try:
                retry_prompt = f"The previous response was invalid JSON. Respond with VALID JSON ONLY in the exact format requested:\n\n{prompt}"
                
                response = client.chat.completions.create(
                    model="gpt-5",
                    messages=[
                        {"role": "system", "content": "Respond with valid JSON only. No additional text."},
                        {"role": "user", "content": retry_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1  # Even more deterministic
                )
                
                result_text = response.choices[0].message.content
                result = json.loads(result_text)
                
                # Validate required keys
                required_keys = ['summary_md', 'actions', 'decisions', 'risks']
                if not all(key in result for key in required_keys):
                    raise ValueError(f"Missing required keys in retry response: {required_keys}")
                
                return result
                
            except Exception as retry_e:
                logger.error(f"OpenAI analysis retry failed: {retry_e}")
                # Fall back to mock analysis
                return AnalysisService._analyse_with_mock(context, [])
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            # Fall back to mock analysis
            return AnalysisService._analyse_with_mock(context, [])
    
    @staticmethod
    def _analyse_with_mock(context: str, segments: List[Segment]) -> Dict:
        """
        Generate mock analysis for testing and development.
        
        Args:
            context: Meeting transcript context
            segments: List of segments for analysis
            
        Returns:
            Mock analysis results dictionary
        """
        # Create realistic mock insights based on transcript content
        word_count = len(context.split()) if context else 0
        
        # Generate summary based on content
        if word_count > 0:
            summary_md = f"""## Meeting Summary
This meeting covered {word_count} words of discussion. Key topics discussed included the main agenda items and various decisions were made.

### Key Discussion Points
- Primary topics were addressed
- Team collaboration was evident
- Several action items were identified
"""
        else:
            summary_md = "## Meeting Summary\nNo transcript content available for analysis."
        
        # Mock actions based on common patterns
        mock_actions = [
            {"text": "Follow up on discussed action items", "owner": "unknown", "due": "unknown"},
            {"text": "Prepare report based on meeting outcomes", "owner": "unknown", "due": "next week"}
        ] if word_count > 50 else []
        
        # Mock decisions
        mock_decisions = [
            {"text": "Agreed to proceed with the discussed approach"},
            {"text": "Decided to schedule follow-up meeting if needed"}
        ] if word_count > 30 else []
        
        # Mock risks
        mock_risks = [
            {"text": "Timeline may be challenging", "mitigation": "Regular check-ins to monitor progress"},
            {"text": "Resource allocation needs clarification", "mitigation": "Schedule resource planning meeting"}
        ] if word_count > 100 else []
        
        return {
            'summary_md': summary_md,
            'actions': mock_actions,
            'decisions': mock_decisions,
            'risks': mock_risks
        }
    
    @staticmethod
    def _persist_summary(session_id: int, summary_data: Dict, engine: str) -> Summary:
        """
        Persist analysis results to database.
        
        Args:
            session_id: ID of the session
            summary_data: Analysis results
            engine: Analysis engine used
            
        Returns:
            Persisted Summary object
        """
        # Create new summary (replace existing if any for one-to-one relationship)
        existing_summary = db.session.query(Summary).filter(Summary.session_id == session_id).first()
        if existing_summary:
            db.session.delete(existing_summary)
            db.session.flush()  # Ensure deletion is processed
        
        summary = Summary(
            session_id=session_id,
            summary_md=summary_data.get('summary_md'),
            actions=summary_data.get('actions', []),
            decisions=summary_data.get('decisions', []),
            risks=summary_data.get('risks', []),
            engine=engine,
            created_at=datetime.utcnow()
        )
        
        db.session.add(summary)
        db.session.commit()
        
        return summary