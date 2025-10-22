# celery_app.py
from celery import Celery

celery = Celery(
    "mina_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery.task(name="run_meeting_analysis")
def run_meeting_analysis(session_id, meeting_id):
    from jobs.analysis_dispatcher import AnalysisDispatcher
    import asyncio
    asyncio.run(AnalysisDispatcher.run_full_analysis(session_id, meeting_id))
