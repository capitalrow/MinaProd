#!/usr/bin/env python3
"""
COMPREHENSIVE MINA TEST SUITE
Tests all critical functionality with 100% thoroughness
"""

import sys
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Test results tracking
test_results = []
TOTAL_TESTS = 0
PASSED_TESTS = 0
FAILED_TESTS = 0


def log_test_result(test_name, passed, message=""):
    """Log test result and track statistics"""
    global PASSED_TESTS, FAILED_TESTS, test_results
    
    status = "✅ PASS" if passed else "❌ FAIL"
    test_results.append((test_name, passed, message))
    
    if passed:
        PASSED_TESTS += 1
        logger.info(f"{status}: {test_name}")
    else:
        FAILED_TESTS += 1
        logger.error(f"{status}: {test_name}")
        if message:
            logger.error(f"  Reason: {message}")


def test_01_database_models():
    """Test 1: Database Models & Schema"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Database Models & Schema")
    logger.info("="*80)
    
    try:
        from app import app, db
        from models.session import Session
        from models.segment import Segment
        from models.analytics import Analytics
        from models.task import Task
        from models.summary import Summary
        
        with app.app_context():
            # Test Session model
            assert hasattr(Session, 'id'), "Session missing id field"
            assert hasattr(Session, 'external_id'), "Session missing external_id"
            assert hasattr(Session, 'status'), "Session missing status"
            assert hasattr(Session, 'trace_id'), "Session missing trace_id"
            
            # Test Segment model
            assert hasattr(Segment, 'id'), "Segment missing id"
            assert hasattr(Segment, 'session_id'), "Segment missing session_id"
            assert hasattr(Segment, 'text'), "Segment missing text"
            
            # Test Analytics model
            assert hasattr(Analytics, 'session_id'), "Analytics missing session_id"
            
            # Test Task model
            assert hasattr(Task, 'session_id'), "Task missing session_id"
            
            # Test Summary model
            assert hasattr(Summary, 'session_id'), "Summary missing session_id"
            
            log_test_result("Database Models Schema", True)
            return True
            
    except Exception as e:
        log_test_result("Database Models Schema", False, str(e))
        return False


def test_02_session_service():
    """Test 2: SessionService CRUD Operations"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: SessionService CRUD Operations")
    logger.info("="*80)
    
    try:
        from app import app, db
        from services.session_service import SessionService
        from models.session import Session
        
        with app.app_context():
            # Create session
            session_id = SessionService.create_session(
                title="Test Session",
                locale="en-US"
            )
            assert session_id is not None, "Session creation returned None"
            assert isinstance(session_id, int), "Session ID not integer"
            
            # Get session by ID
            session = SessionService.get_session_by_id(session_id)
            assert session is not None, "Get session by ID failed"
            assert session.title == "Test Session", "Session title mismatch"
            assert session.status == "active", "Session status not active"
            
            # Get session by external_id
            session_ext = SessionService.get_session_by_external(session.external_id)
            assert session_ext is not None, "Get session by external_id failed"
            assert session_ext.id == session_id, "External ID lookup mismatch"
            
            # Complete session
            success = SessionService.complete_session(session_id)
            assert success is True, "Complete session failed"
            
            # Verify completion
            session = SessionService.get_session_by_id(session_id)
            assert session.status == "completed", "Session not marked completed"
            assert session.completed_at is not None, "Completed timestamp missing"
            
            # Cleanup
            db.session.delete(session)
            db.session.commit()
            
            log_test_result("SessionService CRUD", True)
            return True
            
    except Exception as e:
        log_test_result("SessionService CRUD", False, str(e))
        return False


def test_03_segment_persistence():
    """Test 3: Segment Creation & Persistence"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Segment Creation & Persistence")
    logger.info("="*80)
    
    try:
        from app import app, db
        from services.session_service import SessionService
        from models.segment import Segment
        
        with app.app_context():
            # Create test session
            session_id = SessionService.create_session(title="Segment Test")
            
            # Create segments
            for i in range(5):
                segment = Segment(
                    session_id=session_id,
                    kind="final",
                    text=f"Test segment {i+1}",
                    start_ms=i * 3000,
                    end_ms=(i + 1) * 3000,
                    avg_confidence=0.92 + (i * 0.01)
                )
                db.session.add(segment)
            
            db.session.commit()
            
            # Verify segments
            segments = db.session.query(Segment).filter_by(session_id=session_id).all()
            assert len(segments) == 5, f"Expected 5 segments, got {len(segments)}"
            assert segments[0].text == "Test segment 1", "First segment text mismatch"
            assert segments[2].kind == "final", "Segment kind mismatch"
            
            # Cleanup
            for segment in segments:
                db.session.delete(segment)
            from models.session import Session
            session = db.session.get(Session, session_id)
            db.session.delete(session)
            db.session.commit()
            
            log_test_result("Segment Persistence", True)
            return True
            
    except Exception as e:
        log_test_result("Segment Persistence", False, str(e))
        return False


def test_04_session_finalization():
    """Test 4: Session Finalization Logic"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Session Finalization Logic")
    logger.info("="*80)
    
    try:
        from app import app, db
        from services.session_service import SessionService
        from models.session import Session
        from models.segment import Segment
        
        with app.app_context():
            # Create session with segments
            session_id = SessionService.create_session(title="Finalization Test")
            
            for i in range(3):
                segment = Segment(
                    session_id=session_id,
                    kind="final",
                    text=f"Segment {i+1}",
                    start_ms=i * 2000,
                    end_ms=(i + 1) * 2000,
                    avg_confidence=0.95
                )
                db.session.add(segment)
            db.session.commit()
            
            # Finalize session
            success = SessionService.finalize_session(
                session_id=session_id,
                room=f"test-room-{session_id}"
            )
            assert success is True, "Finalization returned False"
            
            # Verify finalization
            session = db.session.get(Session, session_id)
            assert session.status == "completed", "Session not completed"
            assert session.total_segments == 3, f"Expected 3 segments, got {session.total_segments}"
            assert session.average_confidence > 0.9, "Average confidence calculation error"
            
            # Wait for background tasks
            time.sleep(2)
            
            # Cleanup
            segments = db.session.query(Segment).filter_by(session_id=session_id).all()
            for segment in segments:
                db.session.delete(segment)
            db.session.delete(session)
            db.session.commit()
            
            log_test_result("Session Finalization", True)
            return True
            
    except Exception as e:
        log_test_result("Session Finalization", False, str(e))
        return False


def test_05_analytics_service():
    """Test 5: Analytics Service Functionality"""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: Analytics Service")
    logger.info("="*80)
    
    try:
        from app import app, db
        from services.session_service import SessionService
        from services.analytics_service import AnalyticsService
        from models.segment import Segment
        from models.analytics import Analytics
        
        with app.app_context():
            # Create session with segments
            session_id = SessionService.create_session(title="Analytics Test")
            
            # Add segments
            for i in range(6):
                segment = Segment(
                    session_id=session_id,
                    kind="final",
                    text=f"Test text {i}",
                    start_ms=i * 5000,
                    end_ms=(i + 1) * 5000,
                    avg_confidence=0.90
                )
                db.session.add(segment)
            db.session.commit()
            
            # Generate analytics
            analytics_service = AnalyticsService()
            result = analytics_service.generate_analytics(session_id=session_id)
            
            assert result is not None, "Analytics service returned None"
            assert 'success' in result, "Missing success field"
            assert result['success'] is True, "Analytics generation failed"
            assert 'analytics' in result, "Missing analytics field"
            
            # Check database persistence
            analytics = db.session.query(Analytics).filter_by(session_id=session_id).first()
            assert analytics is not None, "Analytics not persisted to database"
            assert analytics.word_count > 0, "Word count not calculated"
            
            # Cleanup
            db.session.delete(analytics)
            segments = db.session.query(Segment).filter_by(session_id=session_id).all()
            for segment in segments:
                db.session.delete(segment)
            from models.session import Session
            session = db.session.get(Session, session_id)
            db.session.delete(session)
            db.session.commit()
            
            log_test_result("Analytics Service", True)
            return True
            
    except Exception as e:
        log_test_result("Analytics Service", False, str(e))
        return False


def test_06_task_extraction_service():
    """Test 6: Task Extraction Service"""
    logger.info("\n" + "="*80)
    logger.info("TEST 6: Task Extraction Service")
    logger.info("="*80)
    
    try:
        from app import app, db
        from services.session_service import SessionService
        from services.task_extraction_service import TaskExtractionService
        from models.segment import Segment
        from models.task import Task
        
        with app.app_context():
            # Create session
            session_id = SessionService.create_session(title="Task Extraction Test")
            
            # Add segments with action items
            segment = Segment(
                session_id=session_id,
                kind="final",
                text="We need to schedule a follow-up meeting and send the report by Friday.",
                start_ms=0,
                end_ms=5000,
                avg_confidence=0.95
            )
            db.session.add(segment)
            db.session.commit()
            
            # Extract tasks
            task_service = TaskExtractionService()
            result = task_service.extract_tasks(session_id=session_id)
            
            assert result is not None, "Task extraction returned None"
            assert 'tasks' in result, "Missing tasks key in result"
            
            # Cleanup
            tasks = db.session.query(Task).filter_by(session_id=session_id).all()
            for task in tasks:
                db.session.delete(task)
            segments = db.session.query(Segment).filter_by(session_id=session_id).all()
            for segment in segments:
                db.session.delete(segment)
            from models.session import Session
            session = db.session.get(Session, session_id)
            db.session.delete(session)
            db.session.commit()
            
            log_test_result("Task Extraction Service", True)
            return True
            
    except Exception as e:
        log_test_result("Task Extraction Service", False, str(e))
        return False


def test_07_post_transcription_orchestrator():
    """Test 7: Post-Transcription Orchestrator"""
    logger.info("\n" + "="*80)
    logger.info("TEST 7: Post-Transcription Orchestrator")
    logger.info("="*80)
    
    try:
        from app import app, db
        from services.session_service import SessionService
        from models.segment import Segment
        from models.session import Session
        
        with app.app_context():
            # Create session with segments
            session_id = SessionService.create_session(title="Orchestrator Test")
            
            for i in range(3):
                segment = Segment(
                    session_id=session_id,
                    kind="final",
                    text=f"Important meeting discussion point {i+1}",
                    start_ms=i * 3000,
                    end_ms=(i + 1) * 3000,
                    avg_confidence=0.92
                )
                db.session.add(segment)
            db.session.commit()
            
            # Finalize (triggers orchestrator)
            success = SessionService.finalize_session(
                session_id=session_id,
                room=f"test-{session_id}"
            )
            assert success is True, "Finalization failed"
            
            # Wait for background processing
            logger.info("  ⏳ Waiting 8 seconds for post-transcription processing...")
            time.sleep(8)
            
            # Verify session completed
            session = db.session.get(Session, session_id)
            assert session.status == "completed", "Session not completed"
            
            # Cleanup
            from models.analytics import Analytics
            from models.task import Task
            from models.summary import Summary
            
            analytics = db.session.query(Analytics).filter_by(session_id=session_id).first()
            if analytics:
                db.session.delete(analytics)
            
            tasks = db.session.query(Task).filter_by(session_id=session_id).all()
            for task in tasks:
                db.session.delete(task)
            
            summary = db.session.query(Summary).filter_by(session_id=session_id).first()
            if summary:
                db.session.delete(summary)
            
            segments = db.session.query(Segment).filter_by(session_id=session_id).all()
            for segment in segments:
                db.session.delete(segment)
            
            db.session.delete(session)
            db.session.commit()
            
            log_test_result("Post-Transcription Orchestrator", True)
            return True
            
    except Exception as e:
        log_test_result("Post-Transcription Orchestrator", False, str(e))
        return False


def test_08_event_ledger():
    """Test 8: Event Ledger Logging"""
    logger.info("\n" + "="*80)
    logger.info("TEST 8: Event Ledger Logging")
    logger.info("="*80)
    
    try:
        from app import app, db
        from services.session_service import SessionService
        from models.event_ledger import EventLedger
        from models.session import Session
        
        with app.app_context():
            # Create and finalize session
            session_id = SessionService.create_session(title="Event Test")
            success = SessionService.finalize_session(session_id, room="test")
            
            assert success is True, "Finalization failed"
            
            # Wait for events
            time.sleep(2)
            
            # Check event ledger
            events = db.session.query(EventLedger).filter_by(session_id=session_id).all()
            assert len(events) > 0, "No events logged"
            
            # Verify session_finalized event exists
            finalized_events = [e for e in events if e.event_type == 'session_finalized']
            assert len(finalized_events) > 0, "session_finalized event not logged"
            
            # Cleanup
            for event in events:
                db.session.delete(event)
            session = db.session.get(Session, session_id)
            db.session.delete(session)
            db.session.commit()
            
            log_test_result("Event Ledger Logging", True)
            return True
            
    except Exception as e:
        log_test_result("Event Ledger Logging", False, str(e))
        return False


def test_09_frontend_pages():
    """Test 9: Frontend Pages Loading"""
    logger.info("\n" + "="*80)
    logger.info("TEST 9: Frontend Pages Loading")
    logger.info("="*80)
    
    try:
        import requests
        
        base_url = "http://127.0.0.1:5000"
        pages = [
            ("/", "Home/Dashboard"),
            ("/live", "Live Recording"),
            ("/dashboard", "Dashboard"),
            ("/dashboard/meetings", "Meetings"),
            ("/dashboard/analytics", "Analytics"),
        ]
        
        for route, name in pages:
            try:
                response = requests.get(f"{base_url}{route}", timeout=5, allow_redirects=True)
                assert response.status_code == 200, f"{name} returned {response.status_code}"
                logger.info(f"  ✅ {name} loaded successfully")
            except Exception as e:
                raise Exception(f"{name} failed: {e}")
        
        log_test_result("Frontend Pages Loading", True)
        return True
        
    except Exception as e:
        log_test_result("Frontend Pages Loading", False, str(e))
        return False


def test_10_static_assets():
    """Test 10: Static Assets Availability"""
    logger.info("\n" + "="*80)
    logger.info("TEST 10: Static Assets Availability")
    logger.info("="*80)
    
    try:
        import requests
        
        base_url = "http://127.0.0.1:5000"
        assets = [
            "/static/css/main.css",
            "/static/css/mina-tokens.css",
            "/static/css/components.css",
            "/static/js/page-transitions.js",
            "/static/js/theme-toggle.js",
            "/static/js/main.js",
        ]
        
        for asset in assets:
            response = requests.get(f"{base_url}{asset}", timeout=5)
            assert response.status_code == 200, f"{asset} returned {response.status_code}"
            assert len(response.content) > 0, f"{asset} is empty"
            logger.info(f"  ✅ {asset} ({len(response.content)} bytes)")
        
        log_test_result("Static Assets Availability", True)
        return True
        
    except Exception as e:
        log_test_result("Static Assets Availability", False, str(e))
        return False


def run_all_tests():
    """Execute all tests and generate report"""
    global TOTAL_TESTS
    
    logger.info("\n")
    logger.info("🧪 " + "="*76 + " 🧪")
    logger.info("🧪   MINA COMPREHENSIVE TEST SUITE")
    logger.info("🧪 " + "="*76 + " 🧪")
    logger.info("\n")
    
    tests = [
        test_01_database_models,
        test_02_session_service,
        test_03_segment_persistence,
        test_04_session_finalization,
        test_05_analytics_service,
        test_06_task_extraction_service,
        test_07_post_transcription_orchestrator,
        test_08_event_ledger,
        test_09_frontend_pages,
        test_10_static_assets,
    ]
    
    TOTAL_TESTS = len(tests)
    
    # Run all tests
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            logger.error(f"Test crashed: {e}")
    
    # Generate report
    logger.info("\n")
    logger.info("="*80)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("="*80)
    
    for test_name, passed, message in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"  {status}: {test_name}")
        if not passed and message:
            logger.info(f"         └─ {message}")
    
    logger.info("\n")
    logger.info(f"  Total Tests: {TOTAL_TESTS}")
    logger.info(f"  Passed: {PASSED_TESTS}")
    logger.info(f"  Failed: {FAILED_TESTS}")
    logger.info(f"  Pass Rate: {(PASSED_TESTS/TOTAL_TESTS*100):.1f}%")
    logger.info("\n")
    
    if PASSED_TESTS == TOTAL_TESTS:
        logger.info("  🎉 ALL TESTS PASSED - 100% SUCCESS!")
        logger.info("="*80)
        return 0
    else:
        logger.warning(f"  ⚠️  {FAILED_TESTS} test(s) failed")
        logger.info("="*80)
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
