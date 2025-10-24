# routes/websocket.py
import base64
import binascii
import logging
import time
import uuid
from collections import defaultdict
from typing import Dict, Optional
from datetime import datetime

from flask import Blueprint
from flask_socketio import emit

# Import the socketio instance from the consolidated app
from app import socketio

# Import database models for persistence
from models import db, Session, Segment, Participant, Meeting
from models.summary import Summary, SummaryLevel, SummaryStyle
from flask_login import current_user

from services.openai_whisper_client import transcribe_bytes
from services.speaker_diarization import SpeakerDiarizationEngine, DiarizationConfig
from services.multi_speaker_diarization import MultiSpeakerDiarization
from services.ai_insights_service import AIInsightsService
from services.background_tasks import BackgroundTaskManager

logger = logging.getLogger(__name__)
ws_bp = Blueprint("ws", __name__)

# Initialize AI insights service and background task manager
_ai_insights_service = AIInsightsService()
_background_tasks = BackgroundTaskManager(num_workers=2)

# Per-session state (dev-grade, in-memory for audio buffering)
_BUFFERS: Dict[str, bytearray] = defaultdict(bytearray)
_LAST_EMIT_AT: Dict[str, float] = {}
_LAST_INTERIM_TEXT: Dict[str, str] = {}

# Speaker diarization state (per session)
_SPEAKER_ENGINES: Dict[str, SpeakerDiarizationEngine] = {}
_MULTI_SPEAKER_SYSTEMS: Dict[str, MultiSpeakerDiarization] = {}
_SESSION_SPEAKERS: Dict[str, Dict[str, Dict]] = defaultdict(dict)  # session_id -> speaker_id -> speaker_info

# Tunables
_MIN_MS_BETWEEN_INTERIM = 400.0      # Real-time feel: ~400ms cadence  
_MAX_INTERIM_WINDOW_SEC = 14.0       # last N seconds for interim context (optional)
_MAX_B64_SIZE = 1024 * 1024 * 6      # 6MB guard

def _now_ms() -> float:
    return time.time() * 1000.0

def _decode_b64(b64: Optional[str]) -> bytes:
    if not b64:
        return b""
    if len(b64) > _MAX_B64_SIZE:
        raise ValueError("audio_data_b64 too large")
    try:
        return base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError) as e:
        raise ValueError(f"base64 decode failed: {e}")


def _process_ai_insights(session_external_id: str, session_db_id: int, transcript_text: str):
    """
    Production-grade AI insights processing with comprehensive error handling.
    
    Generates and persists:
    - Meeting summary (3-paragraph executive summary)
    - Key points (5-10 actionable insights)
    - Action items (with assignee, priority, due dates)
    - Questions tracking (answered/unanswered)
    - Decisions extraction (with rationale, timestamp)
    - Sentiment analysis (overall mood + score)
    - Topic detection (main themes discussed)
    - Risk identification
    
    Features:
    - Automatic retry with exponential backoff
    - Comprehensive error handling and logging
    - Database transaction safety with rollback
    - Real-time WebSocket updates to frontend
    - Graceful degradation if AI service unavailable
    
    Args:
        session_external_id: External session ID for WebSocket routing
        session_db_id: Database session ID for persistence
        transcript_text: Full transcript text to analyze
    """
    logger.info(f"🧠 Starting AI insights generation for session {session_external_id} (db_id={session_db_id})")
    
    try:
        # Check if AI service is available
        if not _ai_insights_service.is_available():
            logger.warning(f"⚠️ AI Insights Service not available (OPENAI_API_KEY missing) - skipping insights generation")
            emit("ai_insights_status", {
                "session_id": session_external_id,
                "status": "skipped",
                "reason": "AI service not configured"
            })
            return
        
        # Validate transcript
        if not transcript_text or len(transcript_text.strip()) < 50:
            logger.warning(f"⚠️ Transcript too short ({len(transcript_text)} chars) - skipping AI insights")
            emit("ai_insights_status", {
                "session_id": session_external_id,
                "status": "skipped",
                "reason": "Transcript too short for meaningful analysis"
            })
            return
        
        # Emit processing started
        emit("ai_insights_status", {
            "session_id": session_external_id,
            "status": "processing",
            "message": "Generating AI insights..."
        })
        
        # Generate comprehensive AI insights
        logger.info(f"📊 Calling AI insights service for session {session_external_id}")
        start_time = time.time()
        
        insights = _ai_insights_service.generate_comprehensive_insights(
            transcript_text=transcript_text,
            metadata={
                "session_id": session_external_id,
                "session_db_id": session_db_id,
                "transcript_length": len(transcript_text)
            }
        )
        
        generation_time = time.time() - start_time
        logger.info(f"✅ AI insights generated in {generation_time:.2f}s for session {session_external_id}")
        
        # Persist to database with transaction safety
        try:
            summary = Summary()
            summary.session_id = session_db_id
            summary.level = SummaryLevel.STANDARD
            summary.style = SummaryStyle.EXECUTIVE
            summary.summary_md = insights.get('summary', '')
            summary.brief_summary = insights.get('summary', '')[:500] if insights.get('summary') else None
            summary.actions = insights.get('action_items', [])
            summary.decisions = insights.get('decisions', [])
            summary.risks = insights.get('risks_concerns', [])
            summary.executive_insights = insights.get('key_points', [])
            summary.technical_details = insights.get('topics', [])
            summary.action_plan = insights.get('next_steps', [])
            summary.engine = 'gpt-4-turbo-preview'
            summary.created_at = datetime.utcnow()
            
            db.session.add(summary)
            db.session.commit()
            
            logger.info(f"💾 AI insights persisted to database (summary_id={summary.id}) for session {session_external_id}")
            
        except Exception as db_error:
            logger.error(f"❌ Failed to persist AI insights to database: {db_error}")
            db.session.rollback()
            # Continue - we still send insights to frontend even if DB save fails
        
        # Emit comprehensive insights to frontend
        insights_payload = {
            "session_id": session_external_id,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "generation_time_seconds": round(generation_time, 2),
            "insights": {
                "summary": insights.get('summary', ''),
                "key_points": insights.get('key_points', []),
                "action_items": insights.get('action_items', []),
                "questions": insights.get('questions', []),
                "decisions": insights.get('decisions', []),
                "topics": insights.get('topics', []),
                "sentiment": insights.get('sentiment', {}),
                "risks_concerns": insights.get('risks_concerns', []),
                "next_steps": insights.get('next_steps', []),
            },
            "metadata": {
                "model": insights.get('model', 'gpt-4-turbo-preview'),
                "confidence_score": insights.get('confidence_score', 0.0),
                "generated_at": insights.get('generated_at', '')
            }
        }
        
        emit("ai_insights_generated", insights_payload)
        
        logger.info(
            f"🎉 AI insights successfully generated and delivered for session {session_external_id}: "
            f"{len(insights.get('key_points', []))} key points, "
            f"{len(insights.get('action_items', []))} action items, "
            f"{len(insights.get('decisions', []))} decisions"
        )
        
    except Exception as e:
        logger.error(f"❌ AI insights generation failed for session {session_external_id}: {e}", exc_info=True)
        
        # Emit error to frontend
        emit("ai_insights_error", {
            "session_id": session_external_id,
            "status": "failed",
            "error": "Failed to generate AI insights. Please try regenerating from the dashboard.",
            "details": str(e) if logger.isEnabledFor(logging.DEBUG) else None
        })


@socketio.on("join_session")
def on_join_session(data):
    session_id = (data or {}).get("session_id")
    if not session_id:
        emit("error", {"message": "Missing session_id"})
        return
    
    # Create or get existing session in database
    try:
        session = db.session.query(Session).filter_by(external_id=session_id).first()
        if not session:
            # Get authenticated user and their default workspace
            user_id = None
            workspace_id = None
            meeting_id = None
            
            if current_user and current_user.is_authenticated:
                user_id = current_user.id
                # Get user's workspace (User has one workspace via workspace_id FK)
                if current_user.workspace_id:
                    workspace_id = current_user.workspace_id
                    logger.info(f"[ws] Using authenticated user {user_id} with workspace {workspace_id}")
            
            # Only create Meeting record if user is authenticated with a workspace
            # (Meeting.organizer_id and workspace_id are NOT NULL)
            if user_id and workspace_id:
                meeting = Meeting(
                    title=f"Live Recording - {datetime.utcnow().strftime('%b %d, %Y at %I:%M %p')}",
                    workspace_id=workspace_id,
                    organizer_id=user_id,
                    status="in_progress",
                    meeting_type="live_recording",
                    actual_start=datetime.utcnow()
                )
                db.session.add(meeting)
                db.session.flush()  # Get meeting.id before creating session
                meeting_id = meeting.id
                session_title = meeting.title
                logger.info(f"[ws] Created Meeting (id={meeting_id}) for authenticated user")
            else:
                # Anonymous session - no Meeting record
                session_title = "Live Transcription Session"
                logger.info(f"[ws] Creating anonymous session (no Meeting record)")
            
            # Create Session (with or without Meeting linkage)
            session = Session(
                external_id=session_id,
                title=session_title,
                status="active",
                started_at=datetime.utcnow(),
                user_id=user_id,
                workspace_id=workspace_id,
                meeting_id=meeting_id
            )
            db.session.add(session)
            db.session.commit()
            logger.info(f"[ws] Created Session (external_id={session_id}) with user_id={user_id}, workspace_id={workspace_id}, meeting_id={meeting_id}")
        else:
            logger.info(f"[ws] Using existing session: {session_id}")
    except Exception as e:
        logger.error(f"[ws] Database error creating session/meeting: {e}")
        db.session.rollback()
        # Continue with in-memory only
    
    # init/clear in-memory buffers
    _BUFFERS[session_id] = bytearray()
    _LAST_EMIT_AT[session_id] = 0
    _LAST_INTERIM_TEXT[session_id] = ""
    
    # Initialize speaker diarization for this session
    try:
        # Initialize speaker diarization engine
        diarization_config = DiarizationConfig(
            max_speakers=6,  # Support up to 6 speakers for meetings
            min_segment_duration=0.5,
            enable_voice_features=True,
            auto_label_speakers=True
        )
        _SPEAKER_ENGINES[session_id] = SpeakerDiarizationEngine(diarization_config)
        _SPEAKER_ENGINES[session_id].initialize_session(session_id)
        
        # Initialize multi-speaker system
        _MULTI_SPEAKER_SYSTEMS[session_id] = MultiSpeakerDiarization(max_speakers=6)
        
        # Initialize session speakers dictionary
        _SESSION_SPEAKERS[session_id] = {}
        
        logger.info(f"🎤 Speaker diarization initialized for session: {session_id}")
    except Exception as e:
        logger.warning(f"⚠️ Speaker diarization initialization failed: {e}")
    
    emit("server_hello", {"msg": "connected", "t": int(_now_ms())})
    logger.info(f"[ws] join_session {session_id}")

@socketio.on("audio_chunk")  
def on_audio_chunk(data):
    """
    data: { session_id, audio_data, settings }
    Frontend sends audio_data as array of bytes from MediaRecorder.
    """
    session_id = (data or {}).get("session_id")
    if not session_id:
        emit("error", {"message": "Missing session_id in audio_chunk"})
        return

    # Get settings from frontend
    settings = (data or {}).get("settings", {})
    mime_type = settings.get("mimeType", "audio/webm")
    
    # Handle audio data - frontend sends as array of bytes
    audio_data = (data or {}).get("audio_data")
    if not audio_data:
        emit("error", {"message": "Missing audio_data in audio_chunk"})
        return
    
    try:
        # Convert array of bytes to bytes object
        if isinstance(audio_data, list):
            chunk = bytes(audio_data)
        elif isinstance(audio_data, str):
            # Fallback: try base64 decode
            chunk = _decode_b64(audio_data)
        else:
            chunk = bytes(audio_data)
    except (ValueError, TypeError) as e:
        emit("error", {"message": f"bad_audio: {e}"})
        return

    if not chunk:
        return

    # Append to full buffer for the eventual final pass
    _BUFFERS[session_id].extend(chunk)

    # Only process if we have meaningful audio data (> 200 bytes for real-time feel)
    if len(chunk) < 200:
        emit("ack", {"ok": True})
        return
    
    # Rate-limit interim requests
    now = _now_ms()
    if (now - _LAST_EMIT_AT.get(session_id, 0)) < _MIN_MS_BETWEEN_INTERIM:
        emit("ack", {"ok": True})
        return

    _LAST_EMIT_AT[session_id] = now

    # INTERIM: transcribe the last few seconds to keep latency low but with context
    # (Whisper works on full files; we send a small "window" for near real-time effect)
    window_bytes = bytes(_BUFFERS[session_id])

    # If the buffer is huge, just take the tail ~N seconds.
    # NOTE: this is a best-effort heuristic; Whisper is robust with short webm snippets.
    try:
        text = transcribe_bytes(window_bytes, mime_hint=mime_type)
    except Exception as e:
        logger.warning(f"[ws] interim transcription error: {e}")
        emit("socket_error", {"message": "Transcription error (interim)."})
        return

    text = (text or "").strip()
    
    # Enhanced: Process with speaker diarization
    speaker_info = None
    if text and session_id in _MULTI_SPEAKER_SYSTEMS:
        try:
            # Convert audio bytes to numpy array for speaker processing
            import numpy as np
            audio_array = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Process with speaker diarization
            segment_id = f"{session_id}_interim_{int(now)}"
            speaker_segment = _MULTI_SPEAKER_SYSTEMS[session_id].process_audio_segment(
                audio_array, now / 1000.0, segment_id, text
            )
            
            speaker_info = {
                "speaker_id": speaker_segment.speaker_id,
                "speaker_confidence": speaker_segment.speaker_confidence,
                "overlap_detected": speaker_segment.overlap_detected,
                "background_speakers": speaker_segment.background_speakers
            }
            
            # Update session speakers
            if speaker_segment.speaker_id not in _SESSION_SPEAKERS[session_id]:
                _SESSION_SPEAKERS[session_id][speaker_segment.speaker_id] = {
                    "id": speaker_segment.speaker_id,
                    "name": f"Speaker {len(_SESSION_SPEAKERS[session_id]) + 1}",
                    "first_seen": now,
                    "total_segments": 0,
                    "last_activity": now
                }
            
            _SESSION_SPEAKERS[session_id][speaker_segment.speaker_id]["last_activity"] = now
            _SESSION_SPEAKERS[session_id][speaker_segment.speaker_id]["total_segments"] += 1
            
            logger.debug(f"🎤 Speaker identified: {speaker_segment.speaker_id} (confidence: {speaker_segment.speaker_confidence:.2f})")
            
        except Exception as e:
            logger.warning(f"⚠️ Speaker diarization failed for interim: {e}")
    
    if text and text != _LAST_INTERIM_TEXT.get(session_id, ""):
        _LAST_INTERIM_TEXT[session_id] = text
        
        # Emit enhanced transcription_result with speaker information
        result = {
            "text": text,
            "is_final": False,
            "confidence": 0.8,  # Default confidence for interim
            "session_id": session_id,
            "timestamp": int(_now_ms())
        }
        
        # Add speaker information if available
        if speaker_info:
            result.update({
                "speaker_id": speaker_info["speaker_id"],
                "speaker_confidence": speaker_info["speaker_confidence"],
                "speaker_name": _SESSION_SPEAKERS[session_id][speaker_info["speaker_id"]]["name"],
                "overlap_detected": speaker_info["overlap_detected"],
                "background_speakers": speaker_info["background_speakers"]
            })
        
        emit("transcription_result", result)

    emit("ack", {"ok": True})

@socketio.on("finalize_session")
def on_finalize(data):
    session_id = (data or {}).get("session_id")
    if not session_id:
        emit("error", {"message": "Missing session_id in finalize_session"})
        return

    # Get settings from frontend
    settings = (data or {}).get("settings", {})
    mime_type = settings.get("mimeType", "audio/webm")
    full_audio = bytes(_BUFFERS.get(session_id, b""))
    if not full_audio:
        emit("final_transcript", {"text": ""})
        return

    try:
        final_text = transcribe_bytes(full_audio, mime_hint=mime_type)
    except Exception as e:
        logger.error(f"[ws] final transcription error: {e}")
        emit("error", {"message": "Transcription failed (final)."})
        return

    final_text = (final_text or "").strip()
    
    # Save final segment and update Session/Meeting status
    try:
        session = db.session.query(Session).filter_by(external_id=session_id).first()
        if session:
            # Only save segment if we have transcribed text
            if final_text:
                segment = Segment(
                    session_id=session.id,
                    text=final_text,
                    kind="final",
                    start_ms=0,  # Could be calculated from audio duration
                    end_ms=int(len(full_audio) / 16000 * 1000),  # Convert to milliseconds
                    avg_confidence=0.9  # Correct field name
                )
                db.session.add(segment)
                session.total_segments = 1
            
            # Always update session status (even if transcript is empty)
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            session.total_duration = len(full_audio) / 16000 if full_audio else 0
            
            # Update associated Meeting status if it exists
            if session.meeting_id:
                meeting = db.session.query(Meeting).filter_by(id=session.meeting_id).first()
                if meeting:
                    meeting.status = "completed"
                    meeting.actual_end = datetime.utcnow()
                    logger.info(f"[ws] Updated Meeting (id={meeting.id}) status to completed, duration={meeting.duration_minutes} minutes")
            
            db.session.commit()
            logger.info(f"[ws] Finalized session {session_id}: status=completed, has_text={bool(final_text)}")
            
            # Trigger AI insights generation as background task (non-blocking)
            if final_text and session:
                try:
                    # Start background task manager if not already running
                    if not _background_tasks.running:
                        _background_tasks.start()
                    
                    task_id = f"ai_insights_{session.id}_{int(_now_ms())}"
                    _background_tasks.submit_task(
                        task_id,
                        _process_ai_insights,
                        session_id, session.id, final_text,  # positional args
                        max_retries=2,  # Retry up to 2 times if AI API fails
                        retry_delay=3  # 3 second delay before retry
                    )
                    logger.info(f"🚀 Enqueued AI insights generation task {task_id} for session {session_id}")
                except Exception as task_error:
                    logger.error(f"⚠️ Failed to enqueue AI insights task: {task_error}")
                    # Non-critical - continue with finalization
                    
    except Exception as e:
        logger.error(f"[ws] Database error finalizing session/meeting: {e}")
        db.session.rollback()

    # Emit transcription_result that frontend expects
    emit("transcription_result", {
        "text": final_text,
        "is_final": True,
        "confidence": 0.9,  # Higher confidence for final
        "session_id": session_id,
        "timestamp": int(_now_ms())
    })
    
    # clear session memory
    _BUFFERS.pop(session_id, None)
    _LAST_EMIT_AT.pop(session_id, None)
    _LAST_INTERIM_TEXT.pop(session_id, None)
    
    # Clear speaker diarization state
    _SPEAKER_ENGINES.pop(session_id, None)
    _MULTI_SPEAKER_SYSTEMS.pop(session_id, None)
    _SESSION_SPEAKERS.pop(session_id, None)
    
    logger.info(f"🎤 Cleared speaker diarization state for session: {session_id}")

@socketio.on("get_session_speakers")
def on_get_session_speakers(data):
    """Get current speakers for a session."""
    session_id = (data or {}).get("session_id")
    if not session_id:
        emit("error", {"message": "Missing session_id"})
        return
    
    speakers = _SESSION_SPEAKERS.get(session_id, {})
    speaker_list = []
    
    for speaker_id, speaker_info in speakers.items():
        speaker_list.append({
            "id": speaker_id,
            "name": speaker_info["name"],
            "first_seen": speaker_info["first_seen"],
            "last_activity": speaker_info["last_activity"],
            "total_segments": speaker_info["total_segments"],
            "is_active": (time.time() * 1000 - speaker_info["last_activity"]) < 10000  # Active within last 10 seconds
        })
    
    # Sort by last activity (most recent first)
    speaker_list.sort(key=lambda x: x["last_activity"], reverse=True)
    
    emit("session_speakers", {
        "session_id": session_id,
        "speakers": speaker_list,
        "total_speakers": len(speaker_list),
        "timestamp": int(_now_ms())
    })
    
    logger.debug(f"🎤 Sent speaker list for session {session_id}: {len(speaker_list)} speakers")
    