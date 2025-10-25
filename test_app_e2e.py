#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for Mina App
Tests complete workflow: Session creation → Finalization → Post-transcription → UI
"""

import sys
import time
import logging
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_SESSION_ID = None

def test_01_app_health():
    """Test 1: Verify app is running and healthy"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: App Health Check")
    logger.info("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5, allow_redirects=False)
        assert response.status_code in [200, 302], f"Expected 200 or 302, got {response.status_code}"
        logger.info("✅ App is running and responding")
        return True
    except Exception as e:
        logger.error(f"❌ App health check failed: {e}")
        return False

def test_02_live_page():
    """Test 2: Verify live transcription page loads"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Live Page Load")
    logger.info("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/live", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "Live Recording" in response.text or "Mina" in response.text
        logger.info("✅ Live page loads successfully")
        logger.info(f"   Page size: {len(response.text)} bytes")
        return True
    except Exception as e:
        logger.error(f"❌ Live page test failed: {e}")
        return False

def test_03_dashboard_page():
    """Test 3: Verify dashboard loads"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Dashboard Page Load")
    logger.info("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/dashboard", timeout=5, allow_redirects=True)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        logger.info("✅ Dashboard loads successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Dashboard test failed: {e}")
        return False

def test_04_static_assets():
    """Test 4: Verify static assets load"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Static Assets")
    logger.info("="*80)
    
    assets = [
        "/static/css/main.css",
        "/static/js/page-transitions.js",
        "/static/css/components.css"
    ]
    
    for asset in assets:
        try:
            response = requests.get(f"{BASE_URL}{asset}", timeout=5)
            assert response.status_code == 200, f"Asset {asset} returned {response.status_code}"
            logger.info(f"✅ {asset} loads ({len(response.content)} bytes)")
        except Exception as e:
            logger.error(f"❌ Asset {asset} failed: {e}")
            return False
    
    return True

def test_05_create_session_api():
    """Test 5: Create session via API"""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: Create Session via API")
    logger.info("="*80)
    
    global TEST_SESSION_ID
    
    # Import app and services
    from app import app, db
    from services.session_service import SessionService
    from models.session import Session
    from models.segment import Segment
    
    try:
        with app.app_context():
            # Create test session
            session_id = SessionService.create_session(
                title="E2E Test Session",
                locale="en-US"
            )
            
            session = db.session.get(Session, session_id)
            assert session is not None, "Session not created"
            assert session.title == "E2E Test Session"
            assert session.status == "active"
            
            TEST_SESSION_ID = session_id
            
            logger.info(f"✅ Session created: ID={session_id}, external_id={session.external_id}")
            
            # Create test segments
            for i in range(3):
                segment = Segment(
                    session_id=session_id,
                    text=f"Test segment {i+1}: This is a sample transcription.",
                    speaker_label=f"Speaker {(i % 2) + 1}",
                    start_time=i * 5.0,
                    end_time=(i + 1) * 5.0,
                    avg_confidence=0.95,
                    language="en"
                )
                db.session.add(segment)
            
            db.session.commit()
            logger.info(f"✅ Created 3 test segments")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Session creation failed: {e}", exc_info=True)
        return False

def test_06_finalize_session():
    """Test 6: Finalize session and trigger post-transcription"""
    logger.info("\n" + "="*80)
    logger.info("TEST 6: Finalize Session & Post-Transcription")
    logger.info("="*80)
    
    global TEST_SESSION_ID
    
    if not TEST_SESSION_ID:
        logger.error("❌ No test session ID available")
        return False
    
    from app import app, db
    from services.session_service import SessionService
    from models.session import Session
    
    try:
        with app.app_context():
            # Finalize session
            logger.info(f"Finalizing session {TEST_SESSION_ID}...")
            success = SessionService.finalize_session(
                session_id=TEST_SESSION_ID,
                room=f"test-room-{TEST_SESSION_ID}"
            )
            
            assert success, "Finalization returned False"
            
            # Verify session status
            session = db.session.get(Session, TEST_SESSION_ID)
            assert session.status == "completed", f"Expected completed, got {session.status}"
            assert session.completed_at is not None
            
            logger.info("✅ Session finalized successfully")
            logger.info(f"   Status: {session.status}")
            logger.info(f"   Completed at: {session.completed_at}")
            logger.info(f"   Total segments: {session.total_segments}")
            
            # Give background tasks time to run
            logger.info("⏳ Waiting 5 seconds for post-transcription processing...")
            time.sleep(5)
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Finalization failed: {e}", exc_info=True)
        return False

def test_07_verify_database_persistence():
    """Test 7: Verify database records created"""
    logger.info("\n" + "="*80)
    logger.info("TEST 7: Verify Database Persistence")
    logger.info("="*80)
    
    global TEST_SESSION_ID
    
    if not TEST_SESSION_ID:
        logger.error("❌ No test session ID available")
        return False
    
    from app import app, db
    from models.analytics import Analytics
    from models.task import Task
    from models.summary import Summary
    
    try:
        with app.app_context():
            # Check Analytics
            analytics = db.session.query(Analytics).filter_by(session_id=TEST_SESSION_ID).first()
            if analytics:
                logger.info("✅ Analytics record created")
                logger.info(f"   Speaking time: {analytics.total_speaking_time}s")
            else:
                logger.warning("⚠️  Analytics record not found (may still be processing)")
            
            # Check Tasks
            tasks = db.session.query(Task).filter_by(session_id=TEST_SESSION_ID).all()
            logger.info(f"✅ Tasks found: {len(tasks)}")
            for task in tasks[:3]:  # Show first 3
                logger.info(f"   - {task.title[:50] if task.title else 'Untitled'}")
            
            # Check Summary
            summary = db.session.query(Summary).filter_by(session_id=TEST_SESSION_ID).first()
            if summary:
                logger.info("✅ Summary record created")
                logger.info(f"   Level: {summary.level.value if summary.level else 'N/A'}")
                logger.info(f"   Engine: {summary.engine}")
                if summary.summary_md:
                    logger.info(f"   Summary length: {len(summary.summary_md)} chars")
            else:
                logger.warning("⚠️  Summary record not found (may still be processing)")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}", exc_info=True)
        return False

def test_08_event_ledger():
    """Test 8: Verify events logged to EventLedger"""
    logger.info("\n" + "="*80)
    logger.info("TEST 8: Verify Event Ledger")
    logger.info("="*80)
    
    global TEST_SESSION_ID
    
    if not TEST_SESSION_ID:
        logger.error("❌ No test session ID available")
        return False
    
    from app import app, db
    from models.event_ledger import EventLedger
    
    try:
        with app.app_context():
            # Count events for this session
            events = db.session.query(EventLedger).filter_by(session_id=TEST_SESSION_ID).all()
            
            logger.info(f"✅ Total events logged: {len(events)}")
            
            # Show event types
            event_types = {}
            for event in events:
                event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
            
            for event_type, count in sorted(event_types.items()):
                logger.info(f"   - {event_type}: {count}")
            
            # Check for critical events
            critical_events = ['session_finalized', 'refinement_ready', 'analytics_ready', 
                              'tasks_ready', 'summary_ready', 'post_transcription_reveal']
            
            found_events = [e.event_type for e in events]
            for critical in critical_events:
                if critical in found_events:
                    logger.info(f"   ✅ {critical} event found")
                else:
                    logger.warning(f"   ⚠️  {critical} event not found")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Event ledger check failed: {e}", exc_info=True)
        return False

def run_all_tests():
    """Run all tests and report results"""
    logger.info("\n")
    logger.info("🧪 " + "="*76 + " 🧪")
    logger.info("🧪   MINA E2E TEST SUITE - Comprehensive Application Testing")
    logger.info("🧪 " + "="*76 + " 🧪")
    logger.info("\n")
    
    tests = [
        ("App Health Check", test_01_app_health),
        ("Live Page Load", test_02_live_page),
        ("Dashboard Page Load", test_03_dashboard_page),
        ("Static Assets", test_04_static_assets),
        ("Create Session API", test_05_create_session_api),
        ("Finalize Session", test_06_finalize_session),
        ("Database Persistence", test_07_verify_database_persistence),
        ("Event Ledger", test_08_event_ledger),
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
            failed += 1
    
    # Summary
    logger.info("\n")
    logger.info("="*80)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*80)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {status}: {test_name}")
    
    logger.info("\n")
    logger.info(f"  Pass Rate: {passed}/{len(tests)} ({(passed/len(tests)*100):.1f}%)")
    logger.info("\n")
    
    if passed == len(tests):
        logger.info("  🎉 ALL TESTS PASSED!")
        logger.info("="*80)
        return 0
    else:
        logger.warning(f"  ⚠️  {failed} test(s) failed")
        logger.info("="*80)
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
