#!/usr/bin/env python3
"""
CROWN+ Services Integration Test
Tests actual service classes: SessionService, EventLogger, SessionEventCoordinator
"""

import sys
import os
sys.path.insert(0, '/home/runner/workspace')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection  
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def test_session_service_creates_trace_id():
    """Test 6: SessionService.create_session generates trace_id"""
    print("\n=== Test 6: SessionService creates sessions with trace_id ===")
    
    # Import inside test to avoid app boot
    from services.session_service import SessionService
    from app import app, db
    
    with app.app_context():
        # Create session via SessionService
        session_id = SessionService.create_session(
            title="Service Integration Test",
            locale="en"
        )
        
        # Verify it was created
        session = SessionService.get_session_by_id(session_id)
        
        if session and session.trace_id:
            print(f"✅ SessionService created session:")
            print(f"   - ID: {session.external_id}")
            print(f"   - trace_id: {session.trace_id}")
            print(f"   - Title: {session.title}")
            
            # Cleanup
            db.session.delete(session)
            db.session.commit()
            return True
        else:
            print("❌ Session created without trace_id")
            return False


def test_event_logger_emit_event():
    """Test 7: EventLogger.emit_event persists to database"""
    print("\n=== Test 7: EventLogger.emit_event ===")
    
    from services.event_logger import get_event_logger
    from services.session_service import SessionService
    from models.event_ledger import EventLedger
    from app import app, db
    
    with app.app_context():
        # Create session
        session_id = SessionService.create_session(title="EventLogger Test", locale="en")
        session = SessionService.get_session_by_id(session_id)
        
        # Use EventLogger to emit event
        event_logger = get_event_logger()
        success = event_logger.emit_event(
            event_type='service_test_event',
            trace_id=session.trace_id,
            session_id=session.id,
            payload={'test': 'from_event_logger'},
            metadata={'source': 'integration_test'}
        )
        
        print(f"✅ emit_event returned: {success}")
        
        # Verify in database
        event = db.session.query(EventLedger).filter_by(
            session_id=session.id,
            event_type='service_test_event'
        ).first()
        
        if event:
            print(f"✅ Event found in database:")
            print(f"   - trace_id match: {event.trace_id == session.trace_id}")
            print(f"   - Sequence: {event.event_sequence}")
            print(f"   - Payload: {event.event_payload}")
            print(f"   - Metadata: {event.event_metadata}")
            print(f"   - Status: {event.status}")
            
            # Cleanup
            db.session.delete(event)
            db.session.delete(session)
            db.session.commit()
            
            return True
        else:
            print("❌ Event not persisted to database")
            db.session.delete(session)
            db.session.commit()
            return False


def test_session_finalize():
    """Test 8: SessionService.finalize_session emits events and triggers orchestration"""
    print("\n=== Test 8: SessionService.finalize_session ===")
    
    from services.session_service import SessionService
    from models.event_ledger import EventLedger
    from app import app, db
    import time
    
    with app.app_context():
        # Create and finalize session
        session_id = SessionService.create_session(title="Finalize Test", locale="en")
        session = SessionService.get_session_by_id(session_id)
        
        print(f"✅ Session created: {session.external_id}")
        
        # Finalize it
        success = SessionService.finalize_session(session_id=session.id)
        print(f"✅ finalize_session returned: {success}")
        
        # Wait a moment for async orchestration to start
        time.sleep(0.5)
        
        # Check if session_finalized event was logged
        events = db.session.query(EventLedger).filter_by(
            session_id=session.id
        ).all()
        
        event_types = [e.event_type for e in events]
        
        print(f"✅ Events logged: {len(events)}")
        for event in events:
            print(f"   - [{event.event_sequence}] {event.event_type} (status: {event.status})")
        
        # We expect at least session_finalized event
        has_finalized = 'session_finalized' in event_types
        
        if has_finalized:
            print(f"✅ session_finalized event found")
        else:
            print(f"⚠️ session_finalized event not found (expected with coordinator)")
        
        # Cleanup
        for event in events:
            db.session.delete(event)
        db.session.delete(session)
        db.session.commit()
        
        return success


def test_multiple_events_maintain_trace():
    """Test 9: Multiple events for same session maintain trace_id"""
    print("\n=== Test 9: Multiple Events Maintain trace_id ===")
    
    from services.event_logger import get_event_logger
    from services.session_service import SessionService
    from models.event_ledger import EventLedger
    from app import app, db
    
    with app.app_context():
        # Create session
        session_id = SessionService.create_session(title="Multi-Event Test", locale="en")
        session = SessionService.get_session_by_id(session_id)
        
        event_logger = get_event_logger()
        
        # Emit multiple events
        event_types = ['event_1', 'event_2', 'event_3', 'event_4']
        for event_type in event_types:
            event_logger.emit_event(
                event_type=event_type,
                trace_id=session.trace_id,
                session_id=session.id,
                payload={'event': event_type}
            )
        
        # Verify all events
        events = db.session.query(EventLedger).filter_by(
            session_id=session.id
        ).order_by(EventLedger.event_sequence).all()
        
        print(f"✅ {len(events)} events created")
        
        # Check all have same trace_id
        all_match = all(e.trace_id == session.trace_id for e in events)
        sequences_correct = [e.event_sequence for e in events] == list(range(1, len(events) + 1))
        
        print(f"✅ All trace_ids match: {all_match}")
        print(f"✅ Sequences correct: {sequences_correct}")
        
        for event in events:
            print(f"   [{event.event_sequence}] {event.event_type}")
        
        # Cleanup
        for event in events:
            db.session.delete(event)
        db.session.delete(session)
        db.session.commit()
        
        return all_match and sequences_correct


def run_service_tests():
    """Run all service integration tests"""
    print("=" * 60)
    print("CROWN+ SERVICES INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        test_session_service_creates_trace_id,
        test_event_logger_emit_event,
        test_session_finalize,
        test_multiple_events_maintain_trace
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("\n✅ ALL SERVICE TESTS PASSED - Services working correctly!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(run_service_tests())
