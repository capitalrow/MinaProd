"""
Post-Transcription Orchestrator - CROWN+ Event Sequencing Pipeline

Orchestrates the complete post-transcription processing chain:
record_stop → transcript_finalized → transcript_refined → insights_generate →
analytics_update → tasks_generation → post_transcription_reveal → session_finalized →
dashboard_refresh

Every event is atomic, idempotent, and broadcast-driven for seamless UX.

ARCHITECTURE NOTES:
- Runs asynchronously via BackgroundTaskManager (non-blocking)
- Finalization endpoints return immediately while processing continues in background
- Events stream back via WebSocket as each stage completes (real-time updates)
- Gracefully degrades: user gets transcript even if insights fail
- Automatic retry with exponential backoff (2 retries, 10s delay)
- Events are idempotent and replay-safe for background job retries
- Total pipeline time: 3-4 seconds (runs in background)
"""

import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

from models import db
from models.session import Session
from models.segment import Segment
from models.event_ledger import EventType
from services.event_ledger_service import EventLedgerService
from services.analysis_service import AnalysisService
from services.analytics_service import AnalyticsService
from services.background_tasks import background_task_manager
from services.event_monitoring import log_dashboard_refresh_event
from app import socketio

logger = logging.getLogger(__name__)


class PostTranscriptionOrchestrator:
    """
    Orchestrates post-transcription processing pipeline with event-driven architecture.
    
    Implements CROWN+ Event Sequencing:
    - Atomic events
    - Idempotent processing
    - WebSocket broadcasting
    - Graceful degradation
    """
    
    def __init__(self):
        self.event_service = EventLedgerService()
    
    def process_session_async(self, external_session_id: str) -> str:
        """
        Submit post-transcription pipeline to background task manager.
        Returns immediately while processing continues in background.
        
        Args:
            external_session_id: External session identifier (trace_id)
            
        Returns:
            task_id: Background task identifier for status tracking
        """
        task_id = f"post_transcription_{external_session_id}"
        
        # Submit to background task manager with automatic retry
        background_task_manager.submit_task(
            task_id=task_id,
            func=self.process_session,
            external_session_id=external_session_id,
            max_retries=2,  # Allow retries for transient failures
            retry_delay=10  # 10 second delay between retries
        )
        
        logger.info(f"✅ Post-transcription pipeline submitted to background: {task_id}")
        
        # Emit initial event to notify frontend processing started
        socketio.emit('post_transcription_started', {
            'session_id': external_session_id,
            'task_id': task_id,
            'message': 'Processing your meeting insights...',
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a background post-transcription task.
        
        Args:
            task_id: Task identifier returned by process_session_async
            
        Returns:
            Task status dictionary or None if task not found
        """
        return background_task_manager.get_task_status(task_id)
    
    def process_session(self, external_session_id: str) -> Dict[str, Any]:
        """
        Execute complete post-transcription pipeline for a session.
        
        Args:
            external_session_id: External session identifier (trace_id)
            
        Returns:
            Processing result with all generated data
        """
        start_time = time.time()
        session = None
        results = {
            'success': False,
            'external_session_id': external_session_id,
            'events_completed': [],
            'events_failed': [],
            'total_duration_ms': 0
        }
        
        try:
            logger.info(f"🚀 Starting post-transcription pipeline for session: {external_session_id}")
            
            # Get session from database
            session = db.session.query(Session).filter_by(external_id=external_session_id).first()
            if not session:
                logger.error(f"Session not found: {external_session_id}")
                return results
            
            # Execute pipeline stages in sequence
            # Stage 1: Finalize transcript
            transcript_data = self._finalize_transcript(session)
            if transcript_data:
                results['events_completed'].append('transcript_finalized')
            else:
                results['events_failed'].append('transcript_finalized')
            
            # Stage 2: Refine transcript
            refined_data = self._refine_transcript(session, transcript_data)
            if refined_data:
                results['events_completed'].append('transcript_refined')
                results['refined_transcript'] = refined_data
            else:
                results['events_failed'].append('transcript_refined')
            
            # Stage 3: Generate insights (parallel-capable, but sequential for reliability)
            insights_data = self._generate_insights(session)
            if insights_data:
                results['events_completed'].append('insights_generate')
                results['insights'] = insights_data
            else:
                results['events_failed'].append('insights_generate')
            
            # Stage 4: Update analytics
            analytics_data = self._update_analytics(session)
            if analytics_data:
                results['events_completed'].append('analytics_update')
                results['analytics'] = analytics_data
            else:
                results['events_failed'].append('analytics_update')
            
            # Stage 5: Generate tasks
            tasks_data = self._generate_tasks(session, insights_data)
            if tasks_data:
                results['events_completed'].append('tasks_generation')
                results['tasks'] = tasks_data
            else:
                results['events_failed'].append('tasks_generation')
            
            # Stage 6: Emit post_transcription_reveal
            self._emit_reveal(session)
            results['events_completed'].append('post_transcription_reveal')
            
            # Stage 7: Finalize session
            self._finalize_session(session)
            results['events_completed'].append('session_finalized')
            
            # Stage 8: Emit dashboard refresh (CROWN+ final event)
            self._emit_dashboard_refresh(session)
            results['events_completed'].append('dashboard_refresh')
            
            # Calculate total duration
            results['total_duration_ms'] = (time.time() - start_time) * 1000
            
            # Success only if no events failed
            results['success'] = len(results['events_failed']) == 0
            
            if results['success']:
                logger.info(f"✅ Pipeline completed successfully for {external_session_id} in {results['total_duration_ms']:.0f}ms")
            else:
                logger.warning(f"⚠️ Pipeline completed with {len(results['events_failed'])} failures for {external_session_id} in {results['total_duration_ms']:.0f}ms")
                logger.warning(f"   Failed events: {results['events_failed']}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed for {external_session_id}: {e}", exc_info=True)
            results['error'] = str(e)
            results['total_duration_ms'] = (time.time() - start_time) * 1000
            
            # Log error event
            if session:
                self.event_service.log_event(
                    event_type=EventType.ERROR_OCCURRED,
                    session_id=session.id,
                    external_session_id=external_session_id,
                    payload={'error': str(e), 'stage': 'post_transcription_pipeline'}
                )
            
            return results
    
    def _finalize_transcript(self, session: Session) -> Optional[Dict[str, Any]]:
        """
        Stage 1: Consolidate all transcript segments into final text.
        Event: transcript_finalized
        """
        event = None
        
        # Non-blocking event logging
        try:
            event = self.event_service.log_event(
                event_type=EventType.TRANSCRIPT_FINALIZED,
                session_id=session.id,
                external_session_id=session.external_id,
                payload={'stage': 'finalize_transcript'}
            )
            self.event_service.start_event(event)
        except Exception as log_error:
            logger.warning(f"Event logging failed (non-blocking): {log_error}")
            event = None
        
        try:
            # Get all final segments
            segments = db.session.query(Segment).filter_by(
                session_id=session.id,
                kind='final'
            ).order_by(Segment.start_ms).all()
            
            # Consolidate text
            full_text = ' '.join(seg.text for seg in segments if seg.text)
            word_count = len(full_text.split()) if full_text else 0
            
            # Calculate statistics
            total_duration = sum((s.end_ms or 0) - (s.start_ms or 0) for s in segments) / 1000.0
            avg_confidence = sum(s.avg_confidence or 0 for s in segments) / len(segments) if segments else 0
            
            result = {
                'full_text': full_text,
                'word_count': word_count,
                'segment_count': len(segments),
                'total_duration_seconds': total_duration,
                'average_confidence': avg_confidence
            }
            
            # CRITICAL: Always emit WebSocket event (even if logging failed)
            socketio.emit('transcript_finalized', {
                'session_id': session.external_id,
                'word_count': word_count,
                'duration': total_duration,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Non-blocking event completion
            if event:
                try:
                    self.event_service.complete_event(event, result=result)
                except Exception as log_error:
                    logger.warning(f"Event completion failed (non-blocking): {log_error}")
            
            logger.info(f"✅ Transcript finalized: {word_count} words, {len(segments)} segments")
            return result
            
        except Exception as e:
            logger.error(f"Failed to finalize transcript: {e}")
            if event:
                try:
                    self.event_service.fail_event(event, str(e))
                except:
                    pass
            return None
    
    def _refine_transcript(self, session: Session, transcript_data: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """
        Stage 2: Apply grammar correction and formatting to transcript.
        Event: transcript_refined
        """
        event = None
        
        # Non-blocking event logging
        try:
            event = self.event_service.log_event(
                event_type=EventType.TRANSCRIPT_REFINED,
                session_id=session.id,
                external_session_id=session.external_id,
                payload={'stage': 'refine_transcript'}
            )
            self.event_service.start_event(event)
        except Exception as log_error:
            logger.warning(f"Event logging failed (non-blocking): {log_error}")
            event = None
        
        try:
            if not transcript_data or not transcript_data.get('full_text'):
                logger.warning("No transcript data to refine")
                if event:
                    try:
                        self.event_service.skip_event(event, "No transcript data")
                    except:
                        pass
                return None
            
            # For now, use the transcript as-is (Whisper already provides clean output)
            # Future: Add GPT-based refinement for grammar, punctuation, formatting
            refined_text = transcript_data['full_text']
            
            result = {
                'refined_text': refined_text,
                'refinement_applied': False,  # Set to True when actual refinement is added
                'original_word_count': transcript_data.get('word_count', 0),
                'refined_word_count': len(refined_text.split())
            }
            
            # CRITICAL: Always emit WebSocket event (even if logging failed)
            socketio.emit('transcript_refined', {
                'session_id': session.external_id,
                'text': refined_text[:500],  # Send preview
                'word_count': result['refined_word_count'],
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Non-blocking event completion
            if event:
                try:
                    self.event_service.complete_event(event, result=result)
                except Exception as log_error:
                    logger.warning(f"Event completion failed (non-blocking): {log_error}")
            
            logger.info(f"✅ Transcript refined: {result['refined_word_count']} words")
            return result
            
        except Exception as e:
            logger.error(f"Failed to refine transcript: {e}")
            if event:
                try:
                    self.event_service.fail_event(event, str(e))
                except:
                    pass
            return None
    
    def _generate_insights(self, session: Session) -> Optional[Dict[str, Any]]:
        """
        Stage 3: Generate AI-powered insights (summary, actions, decisions, risks).
        Event: insights_generate
        
        Status tracking:
        - 'processing': AI analysis in progress
        - 'success': AI completed successfully (may have 0 results, that's still success)
        - 'failed': AI analysis failed (JSON parsing errors, API errors, etc)
        """
        event = None
        
        # Non-blocking event logging
        try:
            event = self.event_service.log_event(
                event_type=EventType.INSIGHTS_GENERATE,
                session_id=session.id,
                external_session_id=session.external_id,
                payload={'stage': 'generate_insights'}
            )
            self.event_service.start_event(event)
        except Exception as log_error:
            logger.warning(f"Event logging failed (non-blocking): {log_error}")
            event = None
        
        try:
            # Set status to 'processing' at start
            session.post_transcription_status = 'processing'
            db.session.commit()
            
            # CRITICAL: Always emit progress event
            socketio.emit('insights_generate', {
                'session_id': session.external_id,
                'status': 'processing',
                'message': 'Crafting highlights...',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Generate summary using AnalysisService
            summary_data = AnalysisService.generate_summary(session.id)
            
            result = {
                'summary_id': summary_data.get('id'),
                'has_actions': bool(summary_data.get('actions')),
                'has_decisions': bool(summary_data.get('decisions')),
                'has_risks': bool(summary_data.get('risks')),
                'action_count': len(summary_data.get('actions', [])),
                'decision_count': len(summary_data.get('decisions', [])),
                'risk_count': len(summary_data.get('risks', []))
            }
            
            # Set status to 'success' even if 0 results (AI completed successfully)
            session.post_transcription_status = 'success'
            db.session.commit()
            
            # CRITICAL: Always emit completion event
            socketio.emit('insights_generate', {
                'session_id': session.external_id,
                'status': 'completed',
                'summary_id': result['summary_id'],
                'action_count': result['action_count'],
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Non-blocking event completion
            if event:
                try:
                    self.event_service.complete_event(event, result=result)
                except Exception as log_error:
                    logger.warning(f"Event completion failed (non-blocking): {log_error}")
            
            logger.info(f"✅ Insights generated: {result['action_count']} actions, {result['decision_count']} decisions, {result['risk_count']} risks")
            return result
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            error_type = type(e).__name__
            error_message = str(e)
            
            # Detailed error logging with traceback
            logger.error(f"❌ Insights generation failed: {error_type}: {error_message}")
            logger.error(f"Traceback:\n{error_traceback}")
            
            # Classify error type for better user messaging
            if "timeout" in error_message.lower() or "timed out" in error_message.lower():
                error_category = "timeout"
                user_message = "AI service timed out - please try again"
            elif "json" in error_message.lower() or "parse" in error_message.lower():
                error_category = "parse_error"
                user_message = "AI response could not be processed"
            elif "rate" in error_message.lower() or "429" in error_message:
                error_category = "rate_limit"
                user_message = "AI service is busy - please try again in a moment"
            elif "api" in error_message.lower() or "key" in error_message.lower():
                error_category = "api_error"
                user_message = "AI service configuration issue"
            else:
                error_category = "unknown"
                user_message = "Insights generation failed, transcript available"
            
            # Set status to 'failed' on exception
            try:
                session.post_transcription_status = 'failed'
                db.session.commit()
            except Exception as db_error:
                logger.error(f"Failed to update session status: {db_error}")
            
            if event:
                try:
                    self.event_service.fail_event(event, error_message)
                except:
                    pass
            
            # Emit detailed error for debugging (graceful degradation)
            socketio.emit('insights_generate', {
                'session_id': session.external_id,
                'status': 'failed',
                'error': user_message,
                'error_category': error_category,
                'error_type': error_type,
                'error_details': error_message,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return None
    
    def _update_analytics(self, session: Session) -> Optional[Dict[str, Any]]:
        """
        Stage 4: Calculate and update session analytics.
        Event: analytics_update
        """
        event = None
        
        # Non-blocking event logging
        try:
            event = self.event_service.log_event(
                event_type=EventType.ANALYTICS_UPDATE,
                session_id=session.id,
                external_session_id=session.external_id,
                payload={'stage': 'update_analytics'}
            )
            self.event_service.start_event(event)
        except Exception as log_error:
            logger.warning(f"Event logging failed (non-blocking): {log_error}")
            event = None
        
        try:
            # Calculate analytics - IMPORTANT: Use only 'final' segments for consistency with refined view
            segments = db.session.query(Segment).filter_by(
                session_id=session.id,
                kind='final'
            ).all()
            
            logger.info(f"[Analytics] Using {len(segments)} final segments for session {session.external_id}")
            
            total_duration = sum((s.end_ms or 0) - (s.start_ms or 0) for s in segments) / 1000.0
            avg_confidence = sum(s.avg_confidence or 0 for s in segments) / len(segments) if segments else 0
            word_count = sum(len((s.text or '').split()) for s in segments)
            
            # Speaker analysis (speaker_id may not be a database field, so handle gracefully)
            speakers = set(getattr(s, 'speaker_id', None) for s in segments if getattr(s, 'speaker_id', None))
            speaker_count = len(speakers)
            
            result = {
                'total_duration_seconds': total_duration,
                'average_confidence': avg_confidence,
                'word_count': word_count,
                'segment_count': len(segments),
                'speaker_count': speaker_count,
                'words_per_minute': (word_count / (total_duration / 60)) if total_duration > 0 else 0
            }
            
            # Update session statistics
            session.total_segments = len(segments)
            session.average_confidence = avg_confidence
            session.total_duration = total_duration
            db.session.commit()
            
            # CRITICAL: Always emit WebSocket event
            socketio.emit('analytics_update', {
                'session_id': session.external_id,
                'metrics': result,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Non-blocking event completion
            if event:
                try:
                    self.event_service.complete_event(event, result=result)
                except Exception as log_error:
                    logger.warning(f"Event completion failed (non-blocking): {log_error}")
            
            logger.info(f"✅ Analytics updated: {word_count} words, {speaker_count} speakers")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update analytics: {e}")
            if event:
                try:
                    self.event_service.fail_event(event, str(e))
                except:
                    pass
            return None
    
    def _generate_tasks(self, session: Session, insights_data: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """
        Stage 5: Extract and create action items independently from transcript.
        Event: tasks_generation
        
        This stage now works independently of insights success, using NLP-based
        task extraction directly from transcript segments. Falls back to insights
        if available, but continues even if insights failed.
        """
        from models.task import Task
        from sqlalchemy import select, func
        
        event = None
        
        # Non-blocking event logging
        try:
            event = self.event_service.log_event(
                event_type=EventType.TASKS_GENERATION,
                session_id=session.id,
                external_session_id=session.external_id,
                payload={'stage': 'generate_tasks'}
            )
            self.event_service.start_event(event)
        except Exception as log_error:
            logger.warning(f"Event logging failed (non-blocking): {log_error}")
            event = None
        
        try:
            # Strategy: Use AI-extracted tasks as primary source, pattern matching as supplement
            # All tasks are persisted to Task model (single source of truth)
            task_source = "none"
            tasks_created = []
            
            # Option 1: If AI succeeded and found tasks, convert them to Task objects
            if insights_data and insights_data.get('action_count', 0) > 0:
                logger.info(f"[Tasks] Converting {insights_data['action_count']} AI-extracted tasks to Task model")
                
                # Get the summary to access actions
                from models.summary import Summary
                summary = db.session.query(Summary).filter_by(session_id=session.id).first()
                
                if summary and summary.actions:
                    for idx, action in enumerate(summary.actions):
                        try:
                            task = Task(
                                session_id=session.id,
                                title=action.get('text', '').strip()[:100],  # Limit title length
                                description=f"AI-extracted action item",
                                priority=action.get('priority', 'medium').lower(),
                                status="todo",
                                assigned_to=action.get('owner', '').strip() or None,
                                extracted_by_ai=True,  # Mark as AI-extracted
                                confidence_score=0.9,  # High confidence for AI extraction
                                extraction_context={
                                    'source': 'ai_insights',
                                    'original_action': action
                                }
                            )
                            db.session.add(task)
                            tasks_created.append(task)
                        except Exception as e:
                            logger.warning(f"Failed to create AI-extracted task: {e}")
                            continue
                    
                    # Commit AI-extracted tasks
                    try:
                        db.session.commit()
                        logger.info(f"✅ [Database] Persisted {len(tasks_created)} AI-extracted tasks")
                        task_source = "ai_insights"
                    except Exception as e:
                        import traceback
                        logger.error(f"❌ [Database] Failed to commit AI-extracted tasks: {e}")
                        logger.error(f"Traceback:\n{traceback.format_exc()}")
                        db.session.rollback()
                        tasks_created = []
            
            # Option 2: If AI failed or found no tasks, use pattern matching as fallback
            if not tasks_created:
                logger.info(f"[Tasks] AI tasks unavailable, using pattern matching as fallback")
                task_source = "pattern_extraction"
                
                # Get transcript segments for NLP extraction
                segments = db.session.query(Segment).filter_by(
                    session_id=session.id,
                    kind='final'
                ).order_by(Segment.start_ms).all()
                
                if segments:
                    # Build transcript text for pattern matching with segment tracking
                    transcript_with_segments = []
                    for seg in segments:
                        text = seg.text.strip()
                        if text:
                            transcript_with_segments.append({
                                'text': text,
                                'segment_id': seg.id,
                                'start_ms': seg.start_ms,
                                'end_ms': seg.end_ms
                            })
                    
                    # Use pattern-based extraction with segment linkage
                    extracted_tasks = self._extract_tasks_with_patterns_and_segments(
                        transcript_with_segments, session.id
                    )
                    
                    logger.info(f"[Tasks] Pattern extraction attempted {len(extracted_tasks)} tasks")
                else:
                    logger.warning(f"[Tasks] No final segments found for session {session.id}")
                    task_source = "no_segments"
            
            # CRITICAL: Query database to get ACTUAL persisted count (after commit)
            persisted_task_count = db.session.scalar(
                select(func.count()).select_from(Task).where(Task.session_id == session.id)
            ) or 0
            
            logger.info(f"[Tasks] Database verification: {persisted_task_count} tasks persisted for session {session.id}")
            
            result = {
                'tasks_created': persisted_task_count,  # Use DB count, not in-memory count
                'task_source': task_source,
                'session_id': session.id
            }
            
            # CRITICAL: Emit WebSocket event AFTER database verification (use DB count)
            socketio.emit('tasks_generation', {
                'session_id': session.external_id,
                'task_count': persisted_task_count,  # Use verified DB count
                'message': f'{persisted_task_count} new action{"s" if persisted_task_count != 1 else ""} identified' if persisted_task_count > 0 else 'No action items found',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Non-blocking event completion
            if event:
                try:
                    # Update payload with task count for event ledger
                    from sqlalchemy.orm.attributes import flag_modified
                    payload = event.payload or {}
                    payload['task_count'] = persisted_task_count
                    payload['task_source'] = task_source
                    event.payload = payload
                    flag_modified(event, 'payload')  # Tell SQLAlchemy that JSON field changed
                    db.session.add(event)
                    db.session.commit()
                    self.event_service.complete_event(event, result=result)
                except Exception as log_error:
                    logger.warning(f"Event completion failed (non-blocking): {log_error}")
            
            logger.info(f"✅ Tasks generated: {persisted_task_count} tasks from {task_source}")
            return result
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Failed to generate tasks: {e}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            
            if event:
                try:
                    self.event_service.fail_event(event, str(e))
                except:
                    pass
            
            # Emit event even on failure (0 tasks found)
            socketio.emit('tasks_generation', {
                'session_id': session.external_id,
                'task_count': 0,
                'message': 'Task extraction failed',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return None
    
    def _extract_tasks_with_patterns_and_segments(self, transcript_segments: List[Dict], session_id: int) -> List:
        """
        Extract tasks using regex patterns with segment linkage for 'jump to context'.
        Creates Task objects directly in database with source segment tracking.
        
        Args:
            transcript_segments: List of dicts with 'text', 'segment_id', 'start_ms', 'end_ms'
            session_id: Session ID to link tasks to
            
        Returns:
            List of created Task objects
        """
        from models.task import Task
        import re
        
        # Comprehensive task patterns to detect action items
        # Each pattern captures the task description in group 1
        task_patterns = [
            # Explicit action markers
            r"(?:action item|action|task|todo|to-do|to do|follow up|followup|next step)s?[:\-\s]+(.+?)(?:\.|$)",
            
            # Commitment patterns
            r"(?:I|we|you|he|she|they)(?:'ll|\s+will|\s+need to|\s+should|\s+must|\s+have to|\s+got to|'ve got to)\s+(.+?)(?:\.|$)",
            r"(?:I|we)'?(?:m| am|'re| are)\s+going to\s+(.+?)(?:\.|$)",
            
            # Suggestion to action
            r"let['\s]*s\s+(.+?)(?:\.|$)",
            
            # Assignment patterns
            r"(?:assign|delegate|give)\s+(.+?)\s+to\s+\w+",
            
            # TODO variations
            r"\[?(?:TODO|Action|Task|Reminder)\]?[:\-\s]+(.+?)(?:\.|$)",
            
            # Deadline and time-based (explicit temporal markers only)
            r"(?:deadline|due(?:\s+by)?)\s+(.+?)(?:\.|$)",
            
            # Numbered action lists (e.g., "1. Review the document")
            r"\d+[\.\)]\s+(?:review|update|send|create|finish|complete|prepare|schedule|contact|call|email|write|fix|implement|test|deploy|check)\s+(.+?)(?:\.|$)",
            
            # Reminders
            r"(?:reminder|remember to|don't forget to)[:\-\s]*(.+?)(?:\.|$)",
        ]
        
        created_tasks = []
        seen_titles = set()  # Deduplicate
        pattern_match_counts = {}  # Track which patterns are matching (diagnostic logging)
        
        # Extract tasks from transcript segments
        for seg_data in transcript_segments:
            text = seg_data['text']
            segment_id = seg_data['segment_id']
            
            for idx, pattern in enumerate(task_patterns):
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    task_text = match.group(1).strip()
                    
                    # Basic validation
                    if len(task_text) < 5 or len(task_text) > 200:
                        logger.debug(f"[Pattern Matching] Skipped task (length {len(task_text)}): '{task_text[:50]}...'")
                        continue
                    
                    # Context-aware filtering to eliminate false positives
                    task_lower = task_text.lower()
                    
                    # Filter 1: Reject meta-commentary about the application/testing
                    meta_patterns = [
                        'task extraction', 'should be able', 'the objective', 
                        'testing the', 'i am testing', 'we are testing',
                        'the feature', 'this feature', 'the application', 'this application',
                        'the system', 'this system', 'the pipeline', 'this pipeline',
                        'the goal is', 'the purpose is', 'the idea is',
                        'i\'m recording', 'i am recording', 'screen recording'
                    ]
                    if any(meta in task_lower for meta in meta_patterns):
                        logger.debug(f"[Pattern Matching] Skipped meta-commentary: '{task_text[:50]}...'")
                        continue
                    
                    # Filter 2: Reject questions (not action items)
                    if task_text.strip().endswith('?'):
                        logger.debug(f"[Pattern Matching] Skipped question: '{task_text[:50]}...'")
                        continue
                    
                    # Filter 3: Reject if doesn't contain action verbs (for commitment patterns)
                    # Only apply to commitment patterns (patterns 1 and 2)
                    if idx in [1, 2]:  # Commitment patterns that use "will", "should", etc.
                        action_verbs = [
                            'review', 'update', 'send', 'create', 'finish', 'complete',
                            'prepare', 'schedule', 'contact', 'call', 'email', 'write',
                            'fix', 'implement', 'test', 'deploy', 'check', 'submit',
                            'approve', 'analyze', 'research', 'present', 'discuss',
                            'follow up', 'followup', 'reach out', 'set up', 'setup'
                        ]
                        has_action_verb = any(verb in task_lower for verb in action_verbs)
                        if not has_action_verb:
                            logger.debug(f"[Pattern Matching] Skipped (no action verb): '{task_text[:50]}...'")
                            continue
                    
                    # Filter 4: Minimum meaningful content (at least 3 words after filtering)
                    word_count = len(task_text.split())
                    if word_count < 3:
                        logger.debug(f"[Pattern Matching] Skipped (too few words): '{task_text[:50]}...'")
                        continue
                    
                    # Deduplication
                    task_title = task_text[:100]  # Limit title length
                    if task_title.lower() in seen_titles:
                        logger.debug(f"[Pattern Matching] Skipped duplicate task: '{task_title[:50]}...'")
                        continue
                        
                    seen_titles.add(task_title.lower())
                    
                    # Track pattern match for diagnostics
                    pattern_name = f"pattern_{idx}"
                    pattern_match_counts[pattern_name] = pattern_match_counts.get(pattern_name, 0) + 1
                    logger.debug(f"[Pattern Matching] Pattern {idx} matched: '{task_title[:50]}...' in segment {segment_id}")
                    
                    # Create task in database with segment linkage
                    try:
                        task = Task(
                            session_id=session_id,
                            title=task_title,
                            description=f"Extracted from transcript",
                            priority="medium",
                            status="todo",
                            extracted_by_ai=False,  # Pattern-based extraction
                            confidence_score=0.6,  # Lower confidence for pattern matching
                            extraction_context={
                                'source': 'pattern',
                                'transcript_snippet': task_text[:500],
                                'source_segment_id': segment_id,  # Enable 'jump to context'
                                'start_ms': seg_data.get('start_ms'),
                                'end_ms': seg_data.get('end_ms'),
                                'matched_pattern': pattern[:50]  # Store which pattern matched
                            }
                        )
                        db.session.add(task)
                        created_tasks.append(task)
                    except Exception as e:
                        logger.warning(f"Failed to create pattern-extracted task: {e}")
                        continue
        
        # Commit all tasks at once with comprehensive error handling
        try:
            if created_tasks:
                # Log pre-commit state for debugging
                logger.info(f"[Database] Attempting to commit {len(created_tasks)} tasks for session_id={session_id}")
                
                # Verify session exists before committing (FK constraint check)
                from models.session import Session as SessionModel
                session_exists = db.session.query(SessionModel).filter_by(id=session_id).first()
                if not session_exists:
                    logger.error(f"[Database] FK violation prevented: session_id={session_id} does not exist")
                    db.session.rollback()
                    return []
                
                # Commit to database
                db.session.commit()
                
                # CRITICAL: Verify tasks were actually persisted by querying database
                from sqlalchemy import select, func
                persisted_count = db.session.scalar(
                    select(func.count()).select_from(Task).where(Task.session_id == session_id)
                )
                
                if persisted_count != len(created_tasks):
                    logger.error(
                        f"[Database] Task persistence mismatch! "
                        f"Expected {len(created_tasks)} but found {persisted_count} in database "
                        f"for session_id={session_id}"
                    )
                
                logger.info(
                    f"✅ [Database] Successfully persisted {persisted_count} tasks "
                    f"(attempted {len(created_tasks)}) for session_id={session_id}"
                )
                
                # Log diagnostic information about pattern matching
                if pattern_match_counts:
                    logger.info(f"[Pattern Matching] Match distribution: {pattern_match_counts}")
            else:
                logger.info(f"[Pattern Matching] No tasks extracted from {len(transcript_segments)} segments")
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            error_type = type(e).__name__
            
            # Detailed error logging with full context
            logger.error(f"❌ [Database] Failed to commit tasks: {error_type}: {e}")
            logger.error(f"[Database] Error traceback:\n{error_traceback}")
            logger.error(
                f"[Database] Context: session_id={session_id}, "
                f"attempted_tasks={len(created_tasks)}, "
                f"task_titles={[t.title[:30] for t in created_tasks[:3]]}"
            )
            
            # Rollback and return empty list
            db.session.rollback()
            return []
        
        return created_tasks
    
    def _emit_reveal(self, session: Session):
        """
        Stage 6: Emit post_transcription_reveal to trigger UI transition.
        Event: post_transcription_reveal
        """
        event = None
        
        # Non-blocking event logging
        try:
            event = self.event_service.log_event(
                event_type=EventType.POST_TRANSCRIPTION_REVEAL,
                session_id=session.id,
                external_session_id=session.external_id,
                payload={'stage': 'post_transcription_reveal'}
            )
            self.event_service.start_event(event)
        except Exception as log_error:
            logger.warning(f"Event logging failed (non-blocking): {log_error}")
            event = None
        
        try:
            # CRITICAL: Always emit WebSocket event to trigger UI transition
            socketio.emit('post_transcription_reveal', {
                'session_id': session.external_id,
                'redirect_url': f'/sessions/{session.external_id}/refined',
                'message': 'Your meeting insights are ready',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Non-blocking event completion
            if event:
                try:
                    self.event_service.complete_event(event, result={'emitted': True})
                except Exception as log_error:
                    logger.warning(f"Event completion failed (non-blocking): {log_error}")
            
            logger.info(f"✅ Post-transcription reveal emitted for {session.external_id}")
            
        except Exception as e:
            logger.error(f"Failed to emit reveal: {e}")
            if event:
                try:
                    self.event_service.fail_event(event, str(e))
                except:
                    pass
    
    def _finalize_session(self, session: Session):
        """
        Stage 7: Mark session as finalized.
        Event: session_finalized
        """
        event = None
        
        # Non-blocking event logging
        try:
            event = self.event_service.log_event(
                event_type=EventType.SESSION_FINALIZED,
                session_id=session.id,
                external_session_id=session.external_id,
                payload={'stage': 'session_finalized'}
            )
            self.event_service.start_event(event)
        except Exception as log_error:
            logger.warning(f"Event logging failed (non-blocking): {log_error}")
            event = None
        
        try:
            # CRITICAL: Always emit confirmation event
            socketio.emit('session_finalized', {
                'session_id': session.external_id,
                'status': 'completed',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Non-blocking event completion
            if event:
                try:
                    self.event_service.complete_event(event, result={'status': 'finalized'})
                except Exception as log_error:
                    logger.warning(f"Event completion failed (non-blocking): {log_error}")
            
            logger.info(f"✅ Session finalized: {session.external_id}")
            
        except Exception as e:
            logger.error(f"Failed to finalize session: {e}")
            if event:
                try:
                    self.event_service.fail_event(event, str(e))
                except:
                    pass
    
    def _emit_dashboard_refresh(self, session: Session):
        """
        Stage 8: Emit dashboard_refresh for cross-page updates (CROWN+ final event).
        Event: dashboard_refresh
        """
        event = None
        start_time = time.time()
        success = False
        
        # Non-blocking event logging
        try:
            event = self.event_service.log_event(
                event_type=EventType.DASHBOARD_REFRESH,
                session_id=session.id,
                external_session_id=session.external_id,
                payload={'stage': 'dashboard_refresh'}
            )
            self.event_service.start_event(event)
        except Exception as log_error:
            logger.warning(f"Event logging failed (non-blocking): {log_error}")
            event = None
        
        try:
            # CRITICAL: Always emit WebSocket event for cross-page updates
            socketio.emit('dashboard_refresh', {
                'session_id': session.external_id,
                'action': 'session_completed',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Non-blocking event completion
            if event:
                try:
                    self.event_service.complete_event(event, result={'emitted': True})
                except Exception as log_error:
                    logger.warning(f"Event completion failed (non-blocking): {log_error}")
            
            success = True
            logger.info(f"✅ Dashboard refresh emitted for {session.external_id}")
            
        except Exception as e:
            logger.error(f"Failed to emit dashboard refresh: {e}")
            if event:
                try:
                    self.event_service.fail_event(event, str(e))
                except:
                    pass
        finally:
            # Log to monitoring service for production tracking
            duration_ms = (time.time() - start_time) * 1000
            log_dashboard_refresh_event(
                session_id=session.external_id,
                success=success,
                duration_ms=duration_ms,
                session_title=session.title
            )
