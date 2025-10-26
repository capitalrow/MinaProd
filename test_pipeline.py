"""
Test script to manually trigger post-transcription pipeline
"""
import logging
from app import app, db
from services.post_transcription_orchestrator import PostTranscriptionOrchestrator

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_pipeline():
    """Test the post-transcription pipeline for session 209"""
    with app.app_context():
        # Session 209 has external_id 1761505477403
        external_id = "1761505477403"
        
        print(f"\n{'='*80}")
        print(f"Testing Post-Transcription Pipeline for Session: {external_id}")
        print(f"{'='*80}\n")
        
        # Create orchestrator and run pipeline
        orchestrator = PostTranscriptionOrchestrator()
        result = orchestrator.process_session(external_id)
        
        print(f"\n{'='*80}")
        print(f"Pipeline Result:")
        print(f"{'='*80}")
        print(f"Success: {result.get('success')}")
        print(f"Events Completed: {result.get('events_completed')}")
        print(f"Events Failed: {result.get('events_failed')}")
        print(f"Duration: {result.get('total_duration_ms')}ms")
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        
        # Check database for saved data
        print(f"\n{'='*80}")
        print(f"Checking Database:")
        print(f"{'='*80}")
        
        from models.session import Session
        from models.summary import Summary
        from sqlalchemy import select
        
        session = db.session.query(Session).filter_by(external_id=external_id).first()
        if session:
            print(f"✅ Session found: ID {session.id}")
            
            # Check for summary
            stmt = select(Summary).filter(Summary.session_id == session.id)
            summary = db.session.execute(stmt).scalar_one_or_none()
            
            if summary:
                print(f"✅ Summary found!")
                print(f"   - Actions: {len(summary.actions) if summary.actions else 0}")
                print(f"   - Decisions: {len(summary.decisions) if summary.decisions else 0}")
                print(f"   - Risks: {len(summary.risks) if summary.risks else 0}")
            else:
                print(f"❌ No summary found in database")
        else:
            print(f"❌ Session not found")

if __name__ == "__main__":
    test_pipeline()
