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
            logger.error(f"Failed to generate insights: {e}")
            
            # Set status to 'failed' on exception
            try:
                session.post_transcription_status = 'failed'
                db.session.commit()
            except Exception as db_error:
                logger.error(f"Failed to update session status: {db_error}")
            
            if event:
                try:
                    self.event_service.fail_event(event, str(e))
                except:
                    pass
            
            # Emit error but continue pipeline (graceful degradation)
            socketio.emit('insights_generate', {
                'session_id': session.external_id,
                'status': 'failed',
                'error': 'Insights generation failed, transcript available',
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
        Stage 5: Extract and create action items from insights.
        Event: tasks_generation
        """
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
            if not insights_data or not insights_data.get('summary_id'):
                logger.warning("No insights data for task generation")
                if event:
                    try:
                        self.event_service.skip_event(event, "No insights available")
                    except:
                        pass
                return None
            
            # Tasks are already created by AnalysisService in summary
            # Just count and report them
            action_count = insights_data.get('action_count', 0)
            
            result = {
                'tasks_created': action_count,
                'summary_id': insights_data['summary_id']
            }
            
            # CRITICAL: Always emit WebSocket event
            if action_count > 0:
                socketio.emit('tasks_generation', {
                    'session_id': session.external_id,
                    'task_count': action_count,
                    'message': f'{action_count} new action{"s" if action_count != 1 else ""} identified',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Non-blocking event completion
            if event:
                try:
                    self.event_service.complete_event(event, result=result)
                except Exception as log_error:
                    logger.warning(f"Event completion failed (non-blocking): {log_error}")
            
            logger.info(f"✅ Tasks generated: {action_count} actions")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate tasks: {e}")
            if event:
                try:
                    self.event_service.fail_event(event, str(e))
                except:
                    pass
            return None
    
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
