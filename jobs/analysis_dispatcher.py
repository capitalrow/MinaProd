# jobs/analysis_dispatcher.py
import asyncio
import logging
from datetime import datetime
from services.analysis_service import AnalysisService
from services.analytics_service import AnalyticsService
from models.analysis_run import AnalysisRun
from app import db

# Import Celery instance (lazy import avoids circulars)
try:
    from celery_app import celery
except Exception:
    celery = None

logger = logging.getLogger(__name__)


class AnalysisDispatcher:
    """Unified dispatcher for triggering post-meeting analysis and insights."""

    @staticmethod
    async def run_full_analysis(session_id: int, meeting_id: int, force_local: bool = False):
        run = AnalysisRun(session_id=session_id, meeting_id=meeting_id)
        db.session.add(run)
        db.session.commit()

        try:
            use_celery = not force_local and (celery is not None)

            if use_celery:
                logger.info(f"[Dispatcher] Offloading heavy analysis to Celery for session={session_id}, meeting={meeting_id}")
                celery.send_task("run_meeting_analysis", args=[session_id, meeting_id])
                run.status = "queued"
                db.session.commit()
                return {"status": "queued", "engine": "celery"}

            # Otherwise run locally (async)
            logger.info(f"[Dispatcher] Running inline async analysis for session={session_id}, meeting={meeting_id}")

            # Run synchronous code in worker threads
            summary_task = asyncio.to_thread(AnalysisService.generate_summary, session_id)
            analytics_task = asyncio.to_thread(AnalyticsService().analyze_meeting, meeting_id)

            results = await asyncio.gather(summary_task, analytics_task, return_exceptions=True)

            run.mark_completed()
            db.session.commit()

            logger.info(f"[Dispatcher] ✅ Completed analysis for meeting {meeting_id}")
            return {"status": "completed", "results": results}

        except Exception as e:
            logger.error(f"[Dispatcher] ❌ Error running full analysis: {e}")
            run.mark_failed(str(e))
            db.session.commit()
            return {"status": "error", "error": str(e)}