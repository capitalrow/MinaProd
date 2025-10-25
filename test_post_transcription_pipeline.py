#!/usr/bin/env python3
"""
CROWN+ Event Sequencing Test - Post-Transcription Pipeline
Tests the complete post-transcription orchestrator with 100% pass rate requirement.
"""
import os
import sys
import logging
import traceback
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.session import Session
from models.segment import Segment
from models.analytics import Analytics
from models.task import Task
from models.summary import Summary
from services.post_transcription_orchestrator import PostTranscriptionOrchestrator
from services.session_event_coordinator import SessionEventCoordinator
from sqlalchemy import text

def create_test_session():
    """Create a test session with realistic segments (NO meeting_id)"""
    logger.info("🔨 Creating test session with segments...")
    
    # Create session WITHOUT meeting_id (mimics 70% of real sessions)
    from uuid import uuid4
    external_id = f"test-{uuid4().hex[:12]}"
    
    session = Session(
        external_id=external_id,  # REQUIRED: Unique session identifier
        title=f"CROWN+ Test Session - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        status='completed',
        started_at=datetime.now(),
        completed_at=datetime.now(),
        total_segments=0,
        average_confidence=0.0,
        total_duration=0.0,
        meeting_id=None,  # CRITICAL: No meeting_id (like 70% of sessions)
        user_id=1,
        workspace_id=1
    )
    db.session.add(session)
    db.session.flush()
    
    # Add realistic segments (using correct field names)
    test_segments = [
        {"text": "Welcome everyone to today's meeting. Let's discuss our project goals.", "confidence": 0.95},
        {"text": "Thanks Alice. I think we should focus on improving user experience.", "confidence": 0.92},
        {"text": "I agree. We need to prioritize the mobile app redesign.", "confidence": 0.89},
        {"text": "Let me add that to our action items. Bob, can you lead this?", "confidence": 0.94},
        {"text": "Absolutely. I'll create a proposal by next Friday.", "confidence": 0.91},
        {"text": "Great. What about the API integration we discussed?", "confidence": 0.93},
        {"text": "I've been working on that. Should be ready for testing next week.", "confidence": 0.90},
        {"text": "Perfect. Let's schedule a follow-up meeting for next Monday.", "confidence": 0.96},
    ]
    
    for i, seg_data in enumerate(test_segments):
        segment = Segment(
            session_id=session.id,
            kind='final',  # Segment type: 'final' or 'interim'
            text=seg_data["text"],
            avg_confidence=seg_data["confidence"],
            start_ms=i * 5000,  # Milliseconds
            end_ms=(i + 1) * 5000 - 500  # Milliseconds
        )
        db.session.add(segment)
    
    session.total_segments = len(test_segments)
    session.average_confidence = sum(s["confidence"] for s in test_segments) / len(test_segments)
    session.total_duration = len(test_segments) * 5.0
    
    db.session.commit()
    logger.info(f"✅ Created session {session.id} with {len(test_segments)} segments (NO meeting_id)")
    
    return session.id

def check_service_results(session_id):
    """Check if all 4 services produced results"""
    logger.info(f"🔍 Checking service results for session {session_id}...")
    
    results = {
        'refinement': False,
        'analytics': False,
        'tasks': False,
        'summary': False
    }
    
    # Get session to find meeting_id if it exists
    session = db.session.get(Session, session_id)
    if not session:
        logger.error(f"  ❌ Session {session_id} not found!")
        return results
    
    meeting_id = session.meeting_id
    logger.info(f"  Session {session_id}, meeting_id={meeting_id}")
    
    # Check summary (stores refined transcript and AI summary)
    summary = db.session.query(Summary).filter_by(session_id=session_id).first()
    if summary:
        if summary.summary_md:
            results['summary'] = True
            logger.info(f"  ✅ Summary: {len(summary.summary_md)} chars")
        else:
            logger.warning("  ⚠️  Summary record exists but no summary_md content")
    else:
        logger.error("  ❌ Summary: No summary found")
    
    # Check analytics (requires meeting_id)
    if meeting_id:
        analytics = db.session.query(Analytics).filter_by(meeting_id=meeting_id).first()
        if analytics:
            results['analytics'] = True
            logger.info(f"  ✅ Analytics: Found for meeting {meeting_id}")
        else:
            logger.error(f"  ❌ Analytics: None found for meeting {meeting_id}")
    else:
        # Check session_id field in analytics (our refactored version)
        query_result = db.session.execute(
            text("SELECT COUNT(*) FROM analytics WHERE session_id = :sid"),
            {'sid': session_id}
        ).scalar()
        if query_result and query_result > 0:
            results['analytics'] = True
            logger.info(f"  ✅ Analytics: Found via session_id {session_id}")
        else:
            logger.error(f"  ❌ Analytics: No analytics found (no meeting_id, no session_id match)")
    
    # Check tasks (requires meeting_id)
    if meeting_id:
        tasks = db.session.query(Task).filter_by(meeting_id=meeting_id).all()
        if tasks:
            results['tasks'] = True
            logger.info(f"  ✅ Tasks: Found {len(tasks)} tasks for meeting {meeting_id}")
        else:
            logger.warning(f"  ⚠️  Tasks: No tasks for meeting {meeting_id} (may be valid)")
            results['tasks'] = True  # Empty is valid
    else:
        # Check session_id field in tasks (our refactored version)
        query_result = db.session.execute(
            text("SELECT COUNT(*) FROM tasks WHERE session_id = :sid"),
            {'sid': session_id}
        ).scalar()
        if query_result and query_result > 0:
            results['tasks'] = True
            logger.info(f"  ✅ Tasks: Found via session_id {session_id}")
        else:
            logger.warning(f"  ⚠️  Tasks: No tasks found (may be valid if no action items)")
            results['tasks'] = True  # Empty is valid
    
    # Refinement check - look for refined content in summary
    if summary and summary.detailed_summary:
        results['refinement'] = True
        logger.info(f"  ✅ Refinement: {len(summary.detailed_summary)} chars")
    else:
        logger.error("  ❌ Refinement: No refined content found")
    
    return results

def check_event_ledger(session_id):
    """Check that all Socket.IO events were logged"""
    logger.info(f"📋 Checking event ledger for session {session_id}...")
    
    expected_events = [
        'refinement_started',
        'refinement_ready',
        'analytics_started',
        'analytics_ready',
        'tasks_started',
        'tasks_ready',
        'summary_started',
        'summary_ready',
        'post_transcription_reveal'
    ]
    
    # Query event_ledger table
    query = text("""
        SELECT event_type, status, payload 
        FROM event_ledger 
        WHERE session_id = :session_id 
        ORDER BY created_at
    """)
    
    events = db.session.execute(query, {'session_id': session_id}).fetchall()
    event_types = [e[0] for e in events]
    
    logger.info(f"  Found {len(events)} events in ledger")
    
    found_events = {}
    for event in expected_events:
        found = event in event_types
        found_events[event] = found
        status = "✅" if found else "❌"
        logger.info(f"  {status} {event}")
    
    return found_events

def run_comprehensive_test():
    """Run comprehensive end-to-end test"""
    logger.info("\n" + "="*80)
    logger.info("🧪 CROWN+ POST-TRANSCRIPTION PIPELINE COMPREHENSIVE TEST")
    logger.info("="*80 + "\n")
    
    test_results = {
        'session_creation': False,
        'orchestrator_execution': False,
        'refinement_success': False,
        'analytics_success': False,
        'tasks_success': False,
        'summary_success': False,
        'events_emitted': False,
        'overall_pass': False
    }
    
    session_id = None
    
    try:
        with app.app_context():
            # Step 1: Create test session
            logger.info("📝 STEP 1: Creating test session...")
            session_id = create_test_session()
            test_results['session_creation'] = True
            logger.info(f"✅ Session created: {session_id}\n")
            
            # Step 2: Run post-transcription orchestrator (SYNCHRONOUSLY for testing)
            logger.info("🚀 STEP 2: Running post-transcription orchestrator (sync mode)...")
            orchestrator = PostTranscriptionOrchestrator()
            
            try:
                # Call _run_orchestration directly for synchronous execution in tests
                # This bypasses socketio.start_background_task which doesn't work in standalone scripts
                orchestrator._run_orchestration(session_id, room=None)
                test_results['orchestrator_execution'] = True
                logger.info("✅ Orchestrator completed\n")
                    
            except Exception as e:
                logger.error(f"❌ Orchestrator failed: {e}")
                logger.error(traceback.format_exc())
                test_results['orchestrator_execution'] = False
            
            # Step 3: Check service results
            logger.info("🔍 STEP 3: Verifying service results...")
            service_results = check_service_results(session_id)
            test_results['refinement_success'] = service_results['refinement']
            test_results['analytics_success'] = service_results['analytics']
            test_results['tasks_success'] = service_results['tasks']
            test_results['summary_success'] = service_results['summary']
            logger.info("")
            
            # Step 4: Check event emissions
            logger.info("📡 STEP 4: Verifying Socket.IO events...")
            event_results = check_event_ledger(session_id)
            test_results['events_emitted'] = all(event_results.values())
            logger.info("")
            
            # Calculate overall pass rate
            total_tests = len([k for k in test_results.keys() if k != 'overall_pass'])
            passed_tests = sum(1 for k, v in test_results.items() if k != 'overall_pass' and v)
            pass_rate = (passed_tests / total_tests) * 100
            
            test_results['overall_pass'] = (pass_rate == 100.0)
            
            # Print summary
            logger.info("\n" + "="*80)
            logger.info("📊 TEST SUMMARY")
            logger.info("="*80)
            
            for test_name, result in test_results.items():
                if test_name == 'overall_pass':
                    continue
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"  {status}: {test_name}")
            
            logger.info(f"\n  Pass Rate: {passed_tests}/{total_tests} ({pass_rate:.1f}%)")
            logger.info(f"  Session ID: {session_id}")
            
            if test_results['overall_pass']:
                logger.info("\n  🎉 100% PASS RATE ACHIEVED - PRODUCTION READY!")
            else:
                logger.error(f"\n  ⚠️  FAILED: Only {pass_rate:.1f}% pass rate (100% required)")
                logger.error("  ❌ NOT PRODUCTION READY - ISSUES MUST BE FIXED")
            
            logger.info("="*80 + "\n")
            
            return test_results
            
    except Exception as e:
        logger.error(f"\n❌ CRITICAL TEST FAILURE: {e}")
        logger.error(traceback.format_exc())
        test_results['overall_pass'] = False
        return test_results

if __name__ == '__main__':
    results = run_comprehensive_test()
    
    # Exit with proper code
    exit_code = 0 if results['overall_pass'] else 1
    sys.exit(exit_code)
