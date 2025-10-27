"""
Analysis Service (M3) - AI-powered meeting insights generation.

This service handles the generation of Actions, Decisions, and Risks
from meeting transcripts using configurable AI engines.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from flask import current_app
from sqlalchemy.orm import Session as DbSession

from app import db
from models.session import Session
from models.segment import Segment
from models.summary import Summary, SummaryLevel, SummaryStyle
from server.models.memory_store import MemoryStore
from services.text_matcher import TextMatcher

memory = MemoryStore()
import inspect

logger = logging.getLogger(__name__)
text_matcher = TextMatcher()


class AnalysisService:
    """Service for generating AI-powered meeting insights with multi-level and multi-style support."""
    
    # Multi-level, multi-style prompt templates
    PROMPT_TEMPLATES = {
        # Brief Level Prompts
        "brief_executive": """
        You are a C-level executive assistant. Create a brief executive summary (2-3 sentences max) of this meeting.
        Focus on strategic decisions, financial impact, and high-level outcomes only.
        
        Return ONLY valid JSON:
        {
            "brief_summary": "2-3 sentence executive summary",
            "executive_insights": [{"insight": "Key strategic point", "impact": "Business impact"}]
        }
        
        Meeting transcript:
        {transcript}
        """,
        
        "brief_action": """
        You are a strict meeting analyst. Extract ONLY explicitly stated action items from this transcript.
        
        CRITICAL RULES - YOU MUST FOLLOW THESE EXACTLY:
        1. Only extract tasks that are EXPLICITLY STATED as commitments in the transcript
        2. You MUST include the exact quote from the transcript for each task as evidence
        3. If you cannot find a direct quote, DO NOT extract that task
        4. Return an EMPTY array if there are NO clear action items
        5. Do NOT infer, assume, create, or hallucinate tasks
        6. Be extremely conservative - when in doubt, don't extract it
        
        EXAMPLES OF WHAT TO EXTRACT (with evidence):
        ✓ Transcript says: "I need to review the report by Friday"
          Extract: {"action": "Review the report", "evidence_quote": "I need to review the report by Friday", ...}
        
        ✓ Transcript says: "Action item: Let's schedule a follow-up meeting"
          Extract: {"action": "Schedule a follow-up meeting", "evidence_quote": "Let's schedule a follow-up meeting", ...}
        
        EXAMPLES OF WHAT NOT TO EXTRACT:
        ✗ Transcript says: "I'm testing the application"
          DO NOT extract "Test the application" - this is describing current activity, not a future task
        
        ✗ Transcript says: "I will go check my car"
          DO NOT extract - casual conversation, not a work task
        
        ✗ Transcript says: "We could consider improving performance"
          DO NOT extract - just an idea, not a commitment
        
        ✗ Transcript says: "Testing the post-transcription pipeline"
          DO NOT extract - describing what they're doing NOW, not a task for later
        
        REAL-WORLD NEGATIVE EXAMPLE (DO NOT EXTRACT FROM THIS):
        "Testing the Lina application. I will go ahead and share the output from my screen recording, including the post-transcription pipeline with Chad GPT. It will help me refine how the pipeline will work after recording has stopped."
        → This has NO action items. They're describing their current testing activity.
        → CORRECT response: action_plan = []
        
        Return ONLY valid JSON with evidence quotes:
        {
            "brief_summary": "2-3 sentence summary of what was discussed",
            "action_plan": [
                {
                    "action": "Exact task as stated", 
                    "evidence_quote": "REQUIRED: Exact quote from transcript showing this task was mentioned",
                    "owner": "Person mentioned or 'Not specified'", 
                    "priority": "high/medium/low if urgency mentioned",
                    "due": "Date mentioned or 'Not specified'"
                }
            ]
        }
        
        If NO action items found, return: {"brief_summary": "This was a [casual conversation/test/discussion] with no specific action items mentioned.", "action_plan": []}
        
        Meeting transcript:
        {transcript}
        """,
        
        # Standard Level Prompts
        "standard_executive": """
        You are a professional meeting analyst. Analyze this transcript and extract information STRICTLY as stated.
        
        CRITICAL RULES - FOLLOW EXACTLY:
        1. Only extract what is EXPLICITLY stated in the transcript
        2. You MUST provide evidence_quote from transcript for each extracted item
        3. Do NOT infer, assume, create, or hallucinate information
        4. Return EMPTY arrays [] if nothing was explicitly mentioned
        5. Be extremely conservative - accuracy over completeness
        
        For ACTIONS - Include evidence_quote for each:
        ✓ Extract: "I need to...", "I'll...", "Action: ...", "We should...", "Let's..."
        ✗ Skip: Casual mentions ("I'm going to check my car"), maybes ("I could..."), current activities ("I'm testing...")
        ✗ Return [] if no clear action items
        
        For DECISIONS - Include evidence_quote for each:
        ✓ Extract: "We decided...", "The decision is...", "We're going with...", "Approved..."
        ✗ Skip: Opinions ("I think..."), ideas ("We could...", "maybe...")
        ✗ Return [] if no decisions were made
        
        For RISKS - Include evidence_quote for each:
        ✓ Extract: "The risk is...", "I'm concerned about...", "This could be a problem..."
        ✗ Skip: General speculation
        ✗ Return [] if no risks mentioned
        
        REAL-WORLD NEGATIVE EXAMPLE (DO NOT EXTRACT FROM THIS):
        "Testing the Lina application. I will share the output including the post-transcription pipeline. It will help me refine how the pipeline works."
        → This is someone describing their CURRENT testing activity
        → CORRECT response: actions=[], decisions=[], risks=[]
        
        Return ONLY valid JSON with evidence quotes:
        {
            "summary_md": "Factual summary of what was discussed (2-3 paragraphs). State clearly if this was just a test/casual conversation.",
            "actions": [
                {
                    "text": "Exact action as stated", 
                    "evidence_quote": "REQUIRED: Quote from transcript",
                    "owner": "Person name or 'Not specified'", 
                    "due": "Exact date/time mentioned or 'Not specified'"
                }
            ],
            "decisions": [
                {
                    "text": "Exact decision as stated",
                    "evidence_quote": "REQUIRED: Quote from transcript",
                    "impact": "Impact mentioned or 'Not specified'"
                }
            ],
            "risks": [
                {
                    "text": "Exact risk/concern as stated",
                    "evidence_quote": "REQUIRED: Quote from transcript",
                    "mitigation": "Mitigation mentioned or 'Not specified'"
                }
            ]
        }
        
        Meeting transcript:
        {transcript}
        """,
        
        "standard_technical": """
        You are a technical lead. Create a standard technical summary (1-2 paragraphs) focusing on implementation details.
        Include technical decisions, architecture choices, and development tasks.
        
        Return ONLY valid JSON:
        {
            "summary_md": "Standard technical summary in markdown format",
            "actions": [{"text": "Technical task", "owner": "Person or unknown", "due": "Date or unknown", "complexity": "high/medium/low"}],
            "decisions": [{"text": "Technical decision", "rationale": "Why this was chosen"}],
            "risks": [{"text": "Technical risk", "mitigation": "Technical solution"}],
            "technical_details": [{"area": "Technology/Architecture", "details": "Technical specifics", "impact": "Development impact"}]
        }
        
        Meeting transcript:
        {transcript}
        """,
        
        "standard_narrative": """
        You are a storytelling analyst. Create a standard narrative summary (1-2 paragraphs) that tells the story of this meeting.
        Focus on the chronological flow of discussions and how decisions evolved.
        
        Return ONLY valid JSON:
        {
            "summary_md": "Standard narrative summary in markdown format",
            "actions": [{"text": "Action description", "owner": "Person or unknown", "due": "Date or unknown"}],
            "decisions": [{"text": "Decision description", "context": "How this decision came about"}],
            "risks": [{"text": "Risk description", "mitigation": "Suggested mitigation or unknown"}]
        }
        
        Meeting transcript:
        {transcript}
        """,
        
        "standard_bullet": """
        You are a structured analyst. Create a standard bullet-point summary (1-2 paragraphs) using clear bullet points and lists.
        Focus on organized, scannable information.
        
        Return ONLY valid JSON:
        {
            "summary_md": "Standard bullet-point summary in markdown format with bullet points",
            "actions": [{"text": "Action description", "owner": "Person or unknown", "due": "Date or unknown"}],
            "decisions": [{"text": "Decision description"}],
            "risks": [{"text": "Risk description", "mitigation": "Suggested mitigation or unknown"}]
        }
        
        Meeting transcript:
        {transcript}
        """,
        
        "brief_narrative": """
        You are a concise storyteller. Create a brief narrative summary (2-3 sentences max) that tells the key story of this meeting.
        Focus on the main flow and outcome.
        
        Return ONLY valid JSON:
        {
            "brief_summary": "2-3 sentence narrative summary"
        }
        
        Meeting transcript:
        {transcript}
        """,
        
        "brief_bullet": """
        You are a structured summarizer. Create a brief bullet-point summary (2-3 key points max).
        Focus on the most important outcomes in bullet format.
        
        Return ONLY valid JSON:
        {
            "brief_summary": "2-3 key bullet points summary"
        }
        
        Meeting transcript:
        {transcript}
        """,
        
        # Detailed Level Prompts
        "detailed_comprehensive": """
        You are a comprehensive meeting analyst. Create a detailed, multi-section analysis of this meeting.
        Include all aspects: strategic, operational, technical, and actionable items.
        
        Return ONLY valid JSON:
        {
            "detailed_summary": "Comprehensive multi-section analysis in markdown format",
            "summary_md": "Overview paragraph",
            "brief_summary": "2-3 sentence executive summary",
            "actions": [{"text": "Action item", "owner": "Person or unknown", "due": "Date or unknown", "priority": "high/medium/low", "category": "strategic/operational/technical"}],
            "decisions": [{"text": "Decision made", "rationale": "Why this was decided", "impact": "Expected impact", "stakeholders": "Who is affected"}],
            "risks": [{"text": "Risk identified", "mitigation": "Mitigation strategy", "severity": "high/medium/low", "timeline": "When this might occur"}],
            "executive_insights": [{"insight": "Strategic insight", "impact": "Business impact", "timeline": "When this matters", "stakeholders": "Who should know"}],
            "technical_details": [{"area": "Technical area", "details": "Specific details", "decisions": "Technical choices made", "next_steps": "What needs to happen"}],
            "action_plan": [{"phase": "Implementation phase", "tasks": "What needs to be done", "owner": "Who leads this", "timeline": "When this happens"}]
        }
        
        Meeting transcript:
        {transcript}
        """
    }
    
    @staticmethod
    def generate_summary(session_id: int, level: SummaryLevel = SummaryLevel.STANDARD, style: SummaryStyle = SummaryStyle.EXECUTIVE) -> Dict:
        """
        Generate AI-powered summary for a session with specified level and style.
        
        Args:
            session_id: ID of the session to analyse
            level: Summary detail level (brief, standard, detailed)
            style: Summary style (executive, action, technical, narrative, bullet)
            
        Returns:
            Dict containing the generated summary data
            
        Raises:
            ValueError: If session not found or no segments available
        """
        logger.info(f"Generating summary for session {session_id}")

        # --- Memory-aware context (NEW) ---
        try:
            memory_context = ""
            related_memories = memory.search_memory(f"session_{session_id}", top_k=10)
            if related_memories:
                joined = "\n".join([m["content"] for m in related_memories])
                memory_context = f"\n\nPreviously recalled notes:\n{joined}\n\n"
                logger.info(f"Added {len(related_memories)} related memories to context.")
            else:
                logger.info("No related memories found for this session.")
        except Exception as e:
            logger.warning(f"Memory retrieval skipped: {e}")
            memory_context = ""
        # -----------------------------------

        # Load session and segments
        session = db.session.get(Session, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Load final segments ordered by timestamp
        from sqlalchemy import select
        stmt = select(Segment).filter(
            Segment.session_id == session_id, 
            Segment.kind == 'final'
        ).order_by(Segment.start_ms)
        final_segments = db.session.execute(stmt).scalars().all()
        
        # Determine analysis engine from configuration
        # Default to 'openai_gpt' to use real AI analysis (not mock)
        try:
            engine = current_app.config.get('ANALYSIS_ENGINE', 'openai_gpt')
        except RuntimeError:
            # If running outside Flask context, check if API key is available
            import os
            api_key = os.environ.get('OPENAI_API_KEY')
            engine = 'openai_gpt' if api_key else 'mock'
            logger.warning(f"Running outside Flask context, using engine: {engine}")
        
        # Initialize context variable for all code paths
        context = ""
        
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
            context = AnalysisService._build_context(list(final_segments))
            
            # Log what we're analyzing for debugging
            word_count = len(context.split())
            logger.info(f"[AI Analysis] Session {session_id}: {len(final_segments)} final segments, {word_count} words, {len(context)} chars")
            logger.debug(f"[AI Analysis] Transcript preview: {context[:500]}...")
            
            # Combine transcript with any recalled memory context
            context_with_memory = f"{memory_context}{context}"
            
            # Validate transcript quality before processing
            validation_result = AnalysisService._validate_transcript_quality(context)
            
            if not validation_result['is_valid']:
                logger.warning(f"Transcript quality issue for session {session_id}: {validation_result['reason']}")
                # Return informative message for low-quality transcripts
                summary_data = {
                    'summary_md': validation_result['message'],
                    'actions': [],
                    'decisions': [],
                    'risks': [],
                    'validation_warning': validation_result['reason']
                }
            else:
                # Generate insights using configured engine with level and style
                if engine == 'openai_gpt':
                    summary_data = AnalysisService._analyse_with_openai(context_with_memory, level, style)
                else:
                    summary_data = AnalysisService._analyse_with_mock(context_with_memory, list(final_segments), level, style)
                
                # Attach any validation warnings to summary data for UI display
                if validation_result.get('warning'):
                    summary_data['quality_warning'] = validation_result['warning']
                    logger.info(f"Quality warning for session {session_id}: {validation_result['warning']}")
        
        # Persist summary to database
        summary = AnalysisService._persist_summary(session_id, summary_data, engine, level, style)

        logger.info(f"Generated summary {summary.id} for session {session_id} using {engine}")

        # --- Store summary + key insights back into memory (NEW) ---
        try:
            def _safe(text):
                return text.strip() if isinstance(text, str) else ""

            # store main summary
            if summary_data.get("summary_md"):
                memory.add_memory(session_id, "summary_bot", _safe(summary_data["summary_md"]), source_type="summary")

            # store highlights / actions / decisions for semantic recall
            for item in summary_data.get("actions", []) or []:
                memory.add_memory(session_id, "summary_bot", _safe(item.get("text")), source_type="action_item")

            for item in summary_data.get("decisions", []) or []:
                memory.add_memory(session_id, "summary_bot", _safe(item.get("text")), source_type="decision")

            for item in summary_data.get("risks", []) or []:
                memory.add_memory(session_id, "summary_bot", _safe(item.get("text")), source_type="risk")

            logger.info("Summary data stored back into MemoryStore successfully.")
        except Exception as e:
            logger.warning(f"Could not persist summary to MemoryStore: {e}")
        
        # 🔄 Trigger analytics sync if relevant meeting exists
        try:
            from services.analytics_service import AnalyticsService
            import threading

            session_obj = db.session.get(Session, session_id)
            meeting = getattr(session_obj, "meeting", None)

            if meeting:
                analytics_service = AnalyticsService()
                # Capture real Flask app object (not LocalProxy) for thread safety
                from flask import current_app as app_proxy
                app = app_proxy._get_current_object()  # type: ignore
                meeting_id = meeting.id
                
                # Run analytics in background thread with app context
                def run_analytics():
                    try:
                        import asyncio
                        with app.app_context():
                            asyncio.run(analytics_service.analyze_meeting(meeting_id))
                            logger.info(f"Analytics sync completed for meeting {meeting_id}")
                    except Exception as e:
                        logger.warning(f"Analytics sync failed for meeting {meeting_id}: {e}")
                
                thread = threading.Thread(target=run_analytics, daemon=True)
                thread.start()
                logger.info(f"Triggered analytics sync for meeting {meeting_id} (session {session_id})")
            else:
                logger.info(f"No linked meeting found for session {session_id}, skipping analytics sync.")
        except Exception as e:
            logger.warning(f"Failed to trigger analytics after summary: {e}")

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
        from sqlalchemy import select
        stmt = select(Summary).filter(
            Summary.session_id == session_id
        ).order_by(Summary.created_at.desc())
        summary = db.session.execute(stmt).scalar_one_or_none()
        
        return summary.to_dict() if summary else None
    
    @staticmethod
    def _validate_transcript_quality(context: str) -> Dict[str, Any]:
        """
        Validate transcript quality before AI processing.
        
        Args:
            context: Transcript text to validate
            
        Returns:
            Dictionary with validation results:
            - is_valid: bool indicating if transcript is suitable for analysis
            - reason: str explaining validation failure (if any)
            - message: str user-friendly message for invalid transcripts
        """
        # Calculate basic metrics
        word_count = len(context.split())
        char_count = len(context.strip())
        
        # Check for completely empty transcript
        if char_count == 0:
            return {
                'is_valid': False,
                'reason': 'empty_transcript',
                'message': 'No transcript content available for analysis.'
            }
        
        # Check for very short transcripts (< 30 words)
        if word_count < 30:
            return {
                'is_valid': False,
                'reason': 'transcript_too_short',
                'message': f'This recording is too short to analyze ({word_count} words). Please record at least 30 words for meaningful insights.'
            }
        
        # Check for minimal content (30-50 words - warning zone)
        if word_count < 50:
            logger.info(f"Transcript has minimal content ({word_count} words), insights may be limited")
            # Allow processing but flag as limited
            return {
                'is_valid': True,
                'reason': 'limited_content',
                'message': None,
                'warning': f'Short transcript ({word_count} words). Insights may be limited.'
            }
        
        # Check for nonsensical/repetitive content (simple heuristic)
        words = context.lower().split()
        unique_words = set(words)
        uniqueness_ratio = len(unique_words) / len(words) if words else 0
        
        # If less than 20% unique words, likely gibberish or highly repetitive
        if uniqueness_ratio < 0.2 and word_count > 50:
            return {
                'is_valid': False,
                'reason': 'low_content_quality',
                'message': 'This transcript appears to contain mostly repetitive content. Please ensure clear audio for better results.'
            }
        
        # All validation checks passed
        return {
            'is_valid': True,
            'reason': None,
            'message': None
        }
    
    @staticmethod
    def _build_context(segments: List[Segment]) -> str:
        """
        Build bounded context string from final segments.
        
        Args:
            segments: List of final segments ordered by time
            
        Returns:
            Context string limited to configured character count
        """
        try:
            max_chars = current_app.config.get('SUMMARY_CONTEXT_CHARS', 12000)
        except RuntimeError:
            max_chars = 12000
        
        # Build full transcript
        transcript_parts = []
        for segment in segments:
            # Format with timestamp for context
            if hasattr(segment, 'start_time_formatted'):
                time_str = f"[{segment.start_time_formatted}]"
            elif segment.start_ms is not None:
                time_str = f"[{segment.start_ms//1000}s]"
            else:
                time_str = "[0s]"
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
    def _analyse_with_openai(context: str, level: SummaryLevel, style: SummaryStyle) -> Dict:
        """
        Analyse context using OpenAI GPT with specified level and style.
        
        Args:
            context: Meeting transcript context
            level: Summary detail level
            style: Summary style type
            
        Returns:
            Analysis results dictionary
        """
        # Initialize variables before try block to avoid unbound errors
        client = None
        prompt = ""
        expected_keys: List[str] = []
        
        try:
            from openai import OpenAI
            
            import os
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                logger.error("OpenAI API key not found - CANNOT GENERATE INSIGHTS")
                raise ValueError("OpenAI API key not configured")
            
            client = OpenAI(api_key=api_key)
            
            # Select appropriate prompt template based on level and style
            prompt_key = AnalysisService._get_prompt_key(level, style)
            prompt_template = AnalysisService.PROMPT_TEMPLATES.get(prompt_key, AnalysisService.PROMPT_TEMPLATES["standard_executive"])
            prompt = prompt_template.format(transcript=context)
            
            # Get expected keys for this level/style combination
            expected_keys = AnalysisService._get_expected_keys(level, style)
            
            response = client.chat.completions.create(
                model="gpt-4",  # Use proven model (gpt-5 may not exist)
                messages=[
                    {"role": "system", "content": "You are a professional meeting analyst. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3  # Lower temperature for consistent structured output
            )
            
            result_text = response.choices[0].message.content
            if result_text is None:
                raise ValueError("OpenAI returned empty response")
            
            # Log the raw response for debugging
            logger.debug(f"[OpenAI Raw Response] Length: {len(result_text)} chars")
            logger.debug(f"[OpenAI Raw Response] First 500 chars: {result_text[:500]}")
            
            result = json.loads(result_text)
            
            # Log what the AI extracted (before validation)
            action_count_raw = len(result.get('actions', []))
            decision_count_raw = len(result.get('decisions', []))
            risk_count_raw = len(result.get('risks', []))
            logger.info(f"[AI Extraction RAW] Actions: {action_count_raw}, Decisions: {decision_count_raw}, Risks: {risk_count_raw}")
            
            if action_count_raw > 0:
                logger.debug(f"[AI Extraction RAW] Actions before validation: {result.get('actions')}")
            
            # CRITICAL: Validate extracted actions against transcript to prevent hallucination
            if result.get('actions'):
                logger.info(f"[Validation] Validating {len(result['actions'])} extracted actions against transcript...")
                validated_actions = text_matcher.validate_task_list(result['actions'], context)
                
                # Replace with validated actions only
                original_count = len(result['actions'])
                result['actions'] = validated_actions
                validated_count = len(validated_actions)
                
                logger.info(f"[Validation] Actions: {validated_count}/{original_count} passed validation")
                
                if validated_count < original_count:
                    rejected_count = original_count - validated_count
                    logger.warning(f"[Validation] ⚠️ REJECTED {rejected_count} hallucinated tasks that had no evidence in transcript")
            
            # Validate decisions (if present)
            if result.get('decisions'):
                logger.info(f"[Validation] Validating {len(result['decisions'])} extracted decisions...")
                validated_decisions = []
                for decision in result['decisions']:
                    decision_text = decision.get('text', '')
                    if decision_text:
                        validation = text_matcher.validate_extraction(decision_text, context, 'decision')
                        if validation['is_valid']:
                            decision['validation'] = {
                                'confidence_score': validation['confidence_score'],
                                'evidence_quote': validation['evidence_quote']
                            }
                            validated_decisions.append(decision)
                        else:
                            logger.warning(f"[Validation] ❌ Rejected decision: {decision_text[:60]}...")
                
                original_count = len(result['decisions'])
                result['decisions'] = validated_decisions
                logger.info(f"[Validation] Decisions: {len(validated_decisions)}/{original_count} passed validation")
            
            # Validate risks (if present)
            if result.get('risks'):
                logger.info(f"[Validation] Validating {len(result['risks'])} extracted risks...")
                validated_risks = []
                for risk in result['risks']:
                    risk_text = risk.get('text', '')
                    if risk_text:
                        validation = text_matcher.validate_extraction(risk_text, context, 'risk')
                        if validation['is_valid']:
                            risk['validation'] = {
                                'confidence_score': validation['confidence_score'],
                                'evidence_quote': validation['evidence_quote']
                            }
                            validated_risks.append(risk)
                        else:
                            logger.warning(f"[Validation] ❌ Rejected risk: {risk_text[:60]}...")
                
                original_count = len(result['risks'])
                result['risks'] = validated_risks
                logger.info(f"[Validation] Risks: {len(validated_risks)}/{original_count} passed validation")
            
            # Log final validated counts
            action_count = len(result.get('actions', []))
            decision_count = len(result.get('decisions', []))
            risk_count = len(result.get('risks', []))
            logger.info(f"[AI Extraction FINAL] Actions: {action_count}, Decisions: {decision_count}, Risks: {risk_count} (after validation)")
            
            # Validate required keys based on level/style
            missing_keys = [key for key in expected_keys if key not in result]
            if missing_keys:
                logger.warning(f"Missing expected keys for {level.value} {style.value}: {missing_keys}")
                # Don't fail for missing keys, just log the warning
            
            return result
            
        except json.JSONDecodeError as e:
            result_text_snippet = result_text[max(0, e.pos-50):e.pos+50] if result_text else 'N/A'
            logger.error(f"JSON parsing failed on first attempt: {e}")
            logger.error(f"[OpenAI JSON Error] Failed to parse at position {e.pos}")
            logger.error(f"[OpenAI JSON Error] Problem text: {result_text_snippet}")
            
            # Retry with stricter prompt
            try:
                if client is None:
                    raise ValueError("OpenAI client not initialized")
                    
                retry_prompt = f"The previous response was invalid JSON. Respond with VALID JSON ONLY in the exact format requested:\n\n{prompt}"
                
                logger.info("[OpenAI Retry] Attempting retry with stricter prompt...")
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Respond with valid JSON only. No additional text."},
                        {"role": "user", "content": retry_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1  # Even more deterministic
                )
                
                result_text = response.choices[0].message.content
                if result_text is None:
                    raise ValueError("OpenAI retry returned empty response")
                
                logger.debug(f"[OpenAI Retry Response] First 500 chars: {result_text[:500]}")
                result = json.loads(result_text)
                
                logger.info("[OpenAI Retry] ✅ Retry successful!")
                
                # Validate expected keys for this level/style
                missing_keys = [key for key in expected_keys if key not in result]
                if missing_keys:
                    logger.warning(f"Missing expected keys in retry for {level.value} {style.value}: {missing_keys}")
                
                return result
                
            except Exception as retry_e:
                logger.error(f"OpenAI analysis retry failed: {retry_e}")
                logger.error(f"[CRITICAL] OpenAI analysis failed - CANNOT GENERATE INSIGHTS WITHOUT VALID API RESPONSE")
                # ZERO TOLERANCE: Raise exception instead of falling back to mock
                raise ValueError(f"OpenAI analysis failed after retry: {retry_e}") from retry_e
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            logger.error(f"[CRITICAL] OpenAI analysis failed - CANNOT GENERATE INSIGHTS WITHOUT VALID API RESPONSE")
            # ZERO TOLERANCE: Raise exception instead of falling back to mock
            raise ValueError(f"OpenAI analysis failed: {e}") from e
    
    @staticmethod
    def _get_expected_keys(level: SummaryLevel, style: SummaryStyle) -> List[str]:
        """
        Get the expected JSON keys for a given level and style combination.
        
        Args:
            level: Summary detail level
            style: Summary style type
            
        Returns:
            List of expected JSON keys
        """
        if level == SummaryLevel.BRIEF:
            return ["brief_summary"]  # Brief always requires brief_summary
        elif level == SummaryLevel.DETAILED:
            return ["detailed_summary", "summary_md", "brief_summary", "actions", "decisions", "risks", 
                   "executive_insights", "technical_details", "action_plan"]
        else:  # STANDARD level
            return ["summary_md", "actions", "decisions", "risks"]
    
    @staticmethod
    def _get_prompt_key(level: SummaryLevel, style: SummaryStyle) -> str:
        """
        Get the appropriate prompt key based on level and style.
        
        Args:
            level: Summary detail level
            style: Summary style type
            
        Returns:
            Prompt template key
        """
        # Map level and style combinations to prompt keys
        if level == SummaryLevel.BRIEF:
            if style == SummaryStyle.ACTION:
                return "brief_action"
            elif style == SummaryStyle.NARRATIVE:
                return "brief_narrative"
            elif style == SummaryStyle.BULLET:
                return "brief_bullet"
            else:  # EXECUTIVE, TECHNICAL default to executive for brief
                return "brief_executive"
        elif level == SummaryLevel.DETAILED:
            return "detailed_comprehensive"
        else:  # STANDARD level
            if style == SummaryStyle.TECHNICAL:
                return "standard_technical"
            elif style == SummaryStyle.NARRATIVE:
                return "standard_narrative"
            elif style == SummaryStyle.BULLET:
                return "standard_bullet"
            else:  # EXECUTIVE, ACTION default to executive for standard
                return "standard_executive"
    
    @staticmethod
    def _analyse_with_mock(context: str, segments: List[Segment], level: SummaryLevel, style: SummaryStyle) -> Dict:
        """
        Generate mock analysis for testing and development with multi-level and multi-style support.
        
        Args:
            context: Meeting transcript context
            segments: List of segments for analysis
            level: Summary detail level
            style: Summary style type
            
        Returns:
            Mock analysis results dictionary
        """
        # Create realistic mock insights based on transcript content and style
        word_count = len(context.split()) if context else 0
        
        # Generate different content based on level and style
        brief_summary = "Key decisions were made during this meeting with several action items identified for follow-up."
        
        if level == SummaryLevel.BRIEF:
            if style == SummaryStyle.ACTION:
                summary_md = "## Action Summary\nCritical tasks were identified and assigned during this meeting."
            else:
                summary_md = "## Executive Brief\nStrategic discussions resulted in key business decisions."
        elif level == SummaryLevel.DETAILED:
            summary_md = f"""## Comprehensive Meeting Analysis

### Overview
This meeting encompassed {word_count} words of detailed discussion across multiple strategic and operational areas.

### Strategic Outcomes
- Key business decisions were finalized
- Strategic direction was clarified
- Resource allocation was discussed

### Operational Details
- Implementation plans were reviewed
- Timeline considerations were addressed
- Team responsibilities were assigned

### Technical Considerations
- Technical approaches were evaluated
- Architecture decisions were made
- Development priorities were set"""
        else:  # STANDARD
            if style == SummaryStyle.TECHNICAL:
                summary_md = f"""## Technical Meeting Summary
This meeting covered {word_count} words focusing on technical implementation and architecture decisions.

### Technical Decisions
- Architecture approaches were evaluated
- Technology choices were made
- Implementation strategies were discussed"""
            else:
                summary_md = f"""## Meeting Summary
This meeting covered {word_count} words of discussion. Key topics discussed included the main agenda items and various decisions were made.

### Key Discussion Points
- Primary topics were addressed
- Team collaboration was evident
- Several action items were identified"""
        
        detailed_summary = f"""## Comprehensive Analysis

This meeting involved extensive discussion across {word_count} words of content, covering strategic, operational, and technical aspects of the project.

### Strategic Overview
The meeting addressed high-level business objectives and strategic direction. Key stakeholders participated in decision-making processes that will impact future operations.

### Operational Focus
Day-to-day operational concerns were discussed, including resource allocation, timeline management, and team coordination.

### Technical Considerations
Technical implementation details were reviewed, including architecture decisions, technology choices, and development approaches.

### Outcomes and Next Steps
Multiple action items were identified with clear ownership and timelines. Follow-up meetings were scheduled to track progress."""
        
        # CRITICAL: Mock data must also pass validation to prevent hallucination
        # Generate candidate mock actions
        mock_actions_candidates = [
            {"text": "Follow up on discussed action items", "owner": "unknown", "due": "unknown"},
            {"text": "Prepare report based on meeting outcomes", "owner": "unknown", "due": "next week"}
        ] if word_count > 50 else []
        
        # Validate mock actions against transcript (ZERO TOLERANCE for hallucination)
        from services.text_matcher import validate_task_list
        if mock_actions_candidates and context:
            logger.warning("[MOCK DATA] Validating mock actions against transcript...")
            mock_actions = validate_task_list(mock_actions_candidates, context)
            rejected = len(mock_actions_candidates) - len(mock_actions)
            if rejected > 0:
                logger.warning(f"[MOCK DATA] ⚠️ Rejected {rejected} hallucinated mock tasks")
        else:
            mock_actions = []
        
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
        
        # Generate style-specific mock content
        executive_insights = [
            {"insight": "Strategic alignment achieved", "impact": "Improved business outcomes", "timeline": "Q1 next year", "stakeholders": "Executive team"},
            {"insight": "Resource allocation optimized", "impact": "Cost savings identified", "timeline": "This quarter", "stakeholders": "Operations team"}
        ] if style == SummaryStyle.EXECUTIVE or level == SummaryLevel.DETAILED else []
        
        technical_details = [
            {"area": "Architecture", "details": "Microservices approach selected", "decisions": "API-first design", "next_steps": "Design service boundaries"},
            {"area": "Technology Stack", "details": "Modern framework adoption", "decisions": "React/Node.js combination", "next_steps": "Set up development environment"}
        ] if style == SummaryStyle.TECHNICAL or level == SummaryLevel.DETAILED else []
        
        action_plan = [
            {"phase": "Planning", "tasks": "Finalize requirements and specifications", "owner": "Product team", "timeline": "Week 1-2"},
            {"phase": "Development", "tasks": "Implement core functionality", "owner": "Engineering team", "timeline": "Week 3-8"},
            {"phase": "Testing", "tasks": "Quality assurance and user testing", "owner": "QA team", "timeline": "Week 7-10"}
        ] if style == SummaryStyle.ACTION or level == SummaryLevel.DETAILED else []

        return {
            'summary_md': summary_md,
            'brief_summary': brief_summary,
            'detailed_summary': detailed_summary if level == SummaryLevel.DETAILED else None,
            'actions': mock_actions,
            'decisions': mock_decisions,
            'risks': mock_risks,
            'executive_insights': executive_insights,
            'technical_details': technical_details,
            'action_plan': action_plan
        }
    
    @staticmethod
    def _persist_summary(session_id: int, summary_data: Dict, engine: str, level: SummaryLevel, style: SummaryStyle) -> Summary:
        """
        Persist analysis results to database with level and style information.
        
        Args:
            session_id: ID of the session
            summary_data: Analysis results
            engine: Analysis engine used
            level: Summary detail level
            style: Summary style type
            
        Returns:
            Persisted Summary object
        """
        # Create new summary (replace existing if any for one-to-one relationship)
        from sqlalchemy import select
        stmt = select(Summary).filter(Summary.session_id == session_id)
        existing_summary = db.session.execute(stmt).scalar_one_or_none()
        if existing_summary:
            db.session.delete(existing_summary)
            db.session.flush()  # Ensure deletion is processed
        
        summary = Summary(  # type: ignore[call-arg]
            session_id=session_id,
            level=level,
            style=style,
            summary_md=summary_data.get('summary_md'),
            brief_summary=summary_data.get('brief_summary'),
            detailed_summary=summary_data.get('detailed_summary'),
            actions=summary_data.get('actions', []),
            decisions=summary_data.get('decisions', []),
            risks=summary_data.get('risks', []),
            executive_insights=summary_data.get('executive_insights', []),
            technical_details=summary_data.get('technical_details', []),
            action_plan=summary_data.get('action_plan', []),
            engine=engine,
            created_at=datetime.utcnow()
        )
        
        db.session.add(summary)
        db.session.commit()
        
        return summary