"""
File: /routes/api_session_finalize.py
Purpose: Safely finalize an active transcription session once recording stops.
Author: GPT-5 CTO Assistant for Chinyemba Malowa (Crown+ Fix Pack – Oct 2025)
---------------------------------------------------------------------------
This endpoint marks a Session as 'completed', calculates core metrics
(total segments, avg confidence, total duration), commits them,
and invalidates cached analytics/dashboard data.
---------------------------------------------------------------------------
"""

from flask import Blueprint, jsonify, request
# If you do NOT have extensions.cache or library.log:
from flask import current_app as app
from models import db
from services.cache import cache  # or wherever your cache is; if none, stub out cache.delete_prefix
from datetime import datetime
from sqlalchemy import func
from models import Session, Segment
from models.metrics import SessionMetric
import logging
logger = logging.getLogger(__name__)

api_session_finalize_bp = Blueprint("api_session_finalize", __name__, url_prefix="/api/sessions")


@api_session_finalize_bp.route("/<external_id>/complete", methods=["POST"])
def finalize_session(external_id: str):
    """
    🎯 Finalize a transcription session and trigger post-transcription orchestration.
    Expected payload: { "force": bool (optional) }
    
    CRITICAL: This endpoint now uses SessionService.finalize_session() which:
    1. Updates session status and calculates metrics
    2. Emits session_finalized event
    3. Triggers PostTranscriptionOrchestrator asynchronously
    """
    try:
        logger.info(f"🔹 Finalizing session: {external_id}")
        session_obj: Session | None = (
            db.session.query(Session)
            .filter_by(external_id=external_id)
            .first()
        )

        if not session_obj:
            return jsonify({"error": "Session not found"}), 404

        # Skip if already finalized unless force=True
        force = request.json.get("force", False) if request.json else False
        if session_obj.status == "completed" and not force:
            return jsonify({"message": "Session already finalized"}), 200

        # CRITICAL FIX: Use SessionService.finalize_session() instead of manual updates
        # This ensures post-transcription orchestration is triggered
        from services.session_service import SessionService
        
        success = SessionService.finalize_session(
            session_id=session_obj.id,
            room=external_id,  # Use external_id as Socket.IO room
            metadata={
                'finalized_via': 'api_endpoint',
                'force': force
            }
        )
        
        if success:
            logger.info(f"✅ Session {external_id} finalized successfully via SessionService")
            
            # --- Cache invalidation -------------------------------------------
            try:
                cache.delete_prefix("analytics")
                logger.info("🧹 Analytics cache invalidated.")
            except Exception as ce:
                logger.warning(f"Cache clear failed: {ce}")
            
            # Refresh session data after finalization
            db.session.refresh(session_obj)
            
            return jsonify({
                "message": "Session finalized successfully - post-transcription processing initiated",
                "session_id": session_obj.id,
                "external_id": external_id,
                "total_segments": session_obj.total_segments or 0,
                "average_confidence": session_obj.average_confidence or 0.0,
                "total_duration": session_obj.total_duration or 0.0,
                "status": session_obj.status
            }), 200
        else:
            logger.error(f"❌ SessionService.finalize_session() failed for {external_id}")
            return jsonify({"error": "Session finalization failed"}), 500

    except Exception as e:
        logger.error(f"❌ Finalization failed for {external_id}: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500