"""
Post-Transcription Orchestrator - CROWN+ Task Coordination
Coordinates all post-recording analysis tasks with progressive event emission.
Runs asynchronously to avoid blocking the finalization request.
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from models import db, Session
from services.session_event_coordinator import get_session_event_coordinator

# Import socketio for background task execution
from app import socketio

logger = logging.getLogger(__name__)


class PostTranscriptionOrchestrator:
    """
    Orchestrates all post-transcription tasks in sequence with progressive events.
    
    Tasks executed:
    1. Transcript Refinement (grammar, punctuation, speaker labels)
    2. Analytics Generation (speaking time, pace, filler words)
    3. Task Extraction (action items, decisions, follow-ups)
    4. AI Summary Generation (key points, topics, participants)
    
    Each task emits:
    - {task_type}_started event
    - {task_type}_ready event (on success)
    - {task_type}_failed event (on error)
    """
    
    def __init__(self):
        self.coordinator = get_session_event_coordinator()
    
    def run_async(self, session_id: int, room: Optional[str] = None) -> None:
        """
        Run orchestration asynchronously in Socket.IO background task.
        
        Args:
            session_id: Database session ID
            room: Socket.IO room for event broadcasting
        """
        # Use socketio.start_background_task for proper context management
        socketio.start_background_task(self._run_orchestration, session_id, room)
        logger.info(f"✅ Post-transcription orchestration queued for session {session_id}")
    
    def _run_orchestration(self, session_id: int, room: Optional[str] = None) -> None:
        """
        Run all post-transcription tasks in sequence with Flask application context.
        
        Args:
            session_id: Database session ID
            room: Socket.IO room for broadcasting
        """
        from app import app
        
        start_time = time.time()
        
        # CRITICAL: Run in Flask application context for database access
        with app.app_context():
            try:
                # Fetch session with trace_id
                session = db.session.get(Session, session_id)
                if not session:
                    logger.error(f"❌ Session {session_id} not found")
                    return
                
                logger.info(
                    f"🚀 Starting post-transcription orchestration for session {session.external_id} "
                    f"[trace={str(session.trace_id)[:8]}]"
                )
                
                # Task 1: Transcript Refinement
                self._run_refinement(session, room)
                
                # Task 2: Analytics Generation
                self._run_analytics(session, room)
                
                # Task 3: Task Extraction
                self._run_task_extraction(session, room)
                
                # Task 4: AI Summary
                self._run_summary(session, room)
                
                total_time = time.time() - start_time
                logger.info(
                    f"✅ Post-transcription orchestration complete for session {session.external_id} "
                    f"in {total_time:.2f}s"
                )
                
                # CROWN+ Event: Emit post_transcription_reveal after all processing complete
                try:
                    self.coordinator.emit_post_transcription_reveal(
                        session=session,
                        room=room,
                        redirect_url=f'/sessions/{session.external_id}/refined',
                        metadata={'total_duration_ms': int(total_time * 1000)}
                    )
                    logger.info(f"🎉 post_transcription_reveal emitted for session {session.external_id}")
                except Exception as e:
                    logger.warning(f"Failed to emit post_transcription_reveal: {e}")
                
                # CROWN+ Event: Emit dashboard_refresh for global sync
                try:
                    # Emit to session room first
                    self.coordinator.emit_dashboard_refresh(
                        session=session,
                        action='session_completed',
                        room=room,
                        broadcast=False,
                        metadata={'processing_time_ms': int(total_time * 1000)}
                    )
                    # Then broadcast globally to all dashboards (no room = global)
                    self.coordinator.emit_dashboard_refresh(
                        session=session,
                        action='session_completed',
                        room=None,
                        broadcast=True,
                        metadata={'processing_time_ms': int(total_time * 1000)}
                    )
                    logger.info(f"📊 dashboard_refresh emitted to room and broadcast globally for session {session.external_id}")
                except Exception as e:
                    logger.warning(f"Failed to emit dashboard_refresh: {e}")
                
            except Exception as e:
                logger.error(f"❌ Post-transcription orchestration failed: {e}", exc_info=True)
                
            finally:
                # CRITICAL: Clean up database session to prevent leaks
                db.session.remove()
    
    def _run_refinement(self, session: Session, room: Optional[str]) -> None:
        """
        Run transcript refinement task with proper error handling.
        
        Improves grammar, punctuation, capitalization, and speaker labels.
        """
        task_start = time.time()
        
        try:
            # Emit started event
            self.coordinator.emit_processing_event(
                session=session,
                task_type='refinement',
                status='started',
                room=room
            )
            
            # Import and run refinement service
            from services.transcript_refinement_service import get_transcript_refinement_service
            refinement_service = get_transcript_refinement_service()
            
            refined_result = refinement_service.refine_session_transcript(
                session_id=session.id,
                trace_id=session.trace_id
            )
            
            task_duration = time.time() - task_start
            
            # Emit ready event with refined transcript
            self.coordinator.emit_processing_event(
                session=session,
                task_type='refinement',
                status='ready',
                room=room,
                payload_data={
                    'refined_transcript': refined_result.get('refined_text', ''),
                    'improvements': refined_result.get('improvements', {}),
                    'confidence': refined_result.get('confidence', 0.0),
                    'duration_ms': int(task_duration * 1000)
                }
            )
            
            logger.info(f"✅ Refinement complete for session {session.external_id} in {task_duration:.2f}s")
            
        except Exception as e:
            task_duration = time.time() - task_start
            logger.error(f"❌ Refinement failed for session {session.external_id}: {e}", exc_info=True)
            self.coordinator.emit_processing_event(
                session=session,
                task_type='refinement',
                status='failed',
                room=room,
                payload_data={
                    'error': str(e),
                    'duration_ms': int(task_duration * 1000)
                }
            )
    
    def _run_analytics(self, session: Session, room: Optional[str]) -> None:
        """
        Run analytics generation task.
        
        Analyzes speaking time, pace, filler words, interruptions, etc.
        """
        try:
            # Emit started event
            self.coordinator.emit_processing_event(
                session=session,
                task_type='analytics',
                status='started',
                room=room
            )
            
            # Import and run analytics service
            from services.analytics_service import AnalyticsService
            analytics_service = AnalyticsService()
            
            analytics_result = analytics_service.generate_analytics(session_id=session.id)
            
            # Emit ready event with analytics data
            self.coordinator.emit_processing_event(
                session=session,
                task_type='analytics',
                status='ready',
                room=room,
                payload_data={
                    'analytics': analytics_result
                }
            )
            
            logger.info(f"✅ Analytics complete for session {session.external_id}")
            
        except Exception as e:
            logger.error(f"❌ Analytics failed for session {session.external_id}: {e}", exc_info=True)
            self.coordinator.emit_processing_event(
                session=session,
                task_type='analytics',
                status='failed',
                room=room,
                payload_data={'error': str(e), 'error_type': type(e).__name__}
            )
    
    def _run_task_extraction(self, session: Session, room: Optional[str]) -> None:
        """
        Run task extraction task.
        
        Extracts action items, decisions, questions, and follow-ups.
        """
        try:
            # Emit started event
            self.coordinator.emit_processing_event(
                session=session,
                task_type='tasks',
                status='started',
                room=room
            )
            
            # Import and run task extraction service
            from services.task_extraction_service import TaskExtractionService
            task_service = TaskExtractionService()
            
            tasks_result = task_service.extract_tasks(session_id=session.id)
            
            # Emit ready event with extracted tasks
            self.coordinator.emit_processing_event(
                session=session,
                task_type='tasks',
                status='ready',
                room=room,
                payload_data={
                    'tasks': tasks_result.get('tasks', []),
                    'count': len(tasks_result.get('tasks', []))
                }
            )
            
            logger.info(f"✅ Task extraction complete for session {session.external_id}")
            
        except Exception as e:
            logger.error(f"❌ Task extraction failed for session {session.external_id}: {e}", exc_info=True)
            self.coordinator.emit_processing_event(
                session=session,
                task_type='tasks',
                status='failed',
                room=room,
                payload_data={'error': str(e), 'error_type': type(e).__name__}
            )
    
    def _run_summary(self, session: Session, room: Optional[str]) -> None:
        """
        Run AI summary generation task.
        
        Generates key points, topics, decisions, and participant summary.
        PERSISTS results to Summary table.
        """
        try:
            # Emit started event
            self.coordinator.emit_processing_event(
                session=session,
                task_type='summary',
                status='started',
                room=room
            )
            
            # Import and run AI insights service
            from services.ai_insights_service import AIInsightsService
            from models.summary import Summary, SummaryLevel, SummaryStyle
            insights_service = AIInsightsService()
            
            summary_result = insights_service.generate_insights(session_id=session.id)
            
            # PERSIST: Create or update Summary record
            existing_summary = db.session.query(Summary).filter_by(session_id=session.id).first()
            if existing_summary:
                summary = existing_summary
            else:
                summary = Summary(
                    session_id=session.id,
                    level=SummaryLevel.STANDARD,
                    style=SummaryStyle.EXECUTIVE,
                    engine=summary_result.get('model', 'gpt-3.5-turbo')
                )
                db.session.add(summary)
            
            # Update summary fields with AI insights
            summary.summary_md = summary_result.get('summary', '')
            summary.brief_summary = summary_result.get('summary', '')[:500] if summary_result.get('summary') else None
            summary.detailed_summary = summary_result.get('summary', '')
            summary.actions = summary_result.get('action_items', [])
            summary.decisions = summary_result.get('decisions', [])
            summary.risks = summary_result.get('risks_concerns', [])
            summary.executive_insights = summary_result.get('key_points', [])
            summary.action_plan = summary_result.get('next_steps', [])
            
            db.session.commit()
            logger.info(f"✅ Summary persisted to database for session {session.external_id}")
            
            # Emit ready event with summary
            self.coordinator.emit_processing_event(
                session=session,
                task_type='summary',
                status='ready',
                room=room,
                payload_data={
                    'summary': summary_result.get('summary', ''),
                    'key_points': summary_result.get('key_points', []),
                    'topics': summary_result.get('topics', [])
                }
            )
            
            logger.info(f"✅ Summary generation complete for session {session.external_id}")
            
        except Exception as e:
            logger.error(f"❌ Summary generation failed for session {session.external_id}: {e}", exc_info=True)
            db.session.rollback()
            self.coordinator.emit_processing_event(
                session=session,
                task_type='summary',
                status='failed',
                room=room,
                payload_data={'error': str(e), 'error_type': type(e).__name__}
            )


# Singleton instance
_orchestrator = None

def get_post_transcription_orchestrator() -> PostTranscriptionOrchestrator:
    """Get or create the singleton PostTranscriptionOrchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PostTranscriptionOrchestrator()
    return _orchestrator
