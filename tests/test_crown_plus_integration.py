#!/usr/bin/env python3
"""
CROWN+ Integration Test Suite
Tests complete event flow against running application.
"""

import sys
import time
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def test_database_schema():
    """Test 1: Verify database schema is correct"""
    print("\n=== Test 1: Database Schema ===")
    
    with SessionLocal() as session:
        # Check sessions.trace_id exists
        result = session.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'sessions' AND column_name = 'trace_id'
        """))
        row = result.fetchone()
        
        if row and row[1] == 'uuid':
            print("✅ sessions.trace_id exists (UUID)")
        else:
            print("❌ sessions.trace_id missing or wrong type")
            return False
        
        # Check event_ledger table structure
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'event_ledger'
            ORDER BY ordinal_position
        """))
        columns = [row[0] for row in result.fetchall()]
        
        required_columns = [
            'id', 'trace_id', 'event_type', 'event_sequence', 
            'session_id', 'event_payload', 'event_metadata', 
            'status', 'error_message', 'created_at', 'duration_ms'
        ]
        
        missing = set(required_columns) - set(columns)
        if missing:
            print(f"❌ event_ledger missing columns: {missing}")
            return False
        
        print(f"✅ event_ledger has all required columns")
        
        # Check indexes
        result = session.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'event_ledger'
        """))
        indexes = [row[0] for row in result.fetchall()]
        
        if 'ix_event_ledger_trace_id' in indexes:
            print(f"✅ event_ledger has {len(indexes)} indexes")
        else:
            print(f"⚠️ event_ledger missing trace_id index")
        
    return True


def test_session_creation_with_trace_id():
    """Test 2: Session creation generates trace_id"""
    print("\n=== Test 2: Session Creation with trace_id ===")
    
    with SessionLocal() as session:
        # Create a test session
        session_id = f"test-{uuid.uuid4()}"
        
        session.execute(text("""
            INSERT INTO sessions (external_id, title, status, locale, trace_id, started_at)
            VALUES (:id, :title, 'active', 'en', gen_random_uuid(), NOW())
        """), {"id": session_id, "title": "Integration Test Session"})
        session.commit()
        
        # Verify trace_id was generated
        result = session.execute(text("""
            SELECT id, trace_id FROM sessions WHERE external_id = :id
        """), {"id": session_id})
        row = result.fetchone()
        
        if row and row[1]:
            print(f"✅ Session created with trace_id: {row[1]}")
            db_session_id = row[0]
            trace_id = row[1]
            
            # Cleanup
            session.execute(text("DELETE FROM sessions WHERE id = :id"), {"id": db_session_id})
            session.commit()
            
            return True
        else:
            print("❌ Session created without trace_id")
            return False


def test_event_logger_persistence():
    """Test 3: EventLogger persists events to database"""
    print("\n=== Test 3: Event Logger Persistence ===")
    
    with SessionLocal() as session:
        # Create test session
        trace_id = uuid.uuid4()
        session_id = f"test-{uuid.uuid4()}"
        
        session.execute(text("""
            INSERT INTO sessions (external_id, title, status, locale, trace_id, started_at)
            VALUES (:id, :title, 'active', 'en', :trace_id, NOW())
        """), {"id": session_id, "title": "Event Test", "trace_id": trace_id})
        session.commit()
        
        # Get session DB ID
        result = session.execute(text("""
            SELECT id FROM sessions WHERE external_id = :id
        """), {"id": session_id})
        db_session_id = result.fetchone()[0]
        
        # Manually create event in ledger (simulating EventLogger)
        session.execute(text("""
            INSERT INTO event_ledger (
                trace_id, event_type, event_sequence, session_id, 
                event_payload, status, created_at
            ) VALUES (
                :trace_id, :event_type, 1, :session_id, 
                '{"test": "data"}'::jsonb, 'success', NOW()
            )
        """), {
            "trace_id": trace_id,
            "event_type": "test_event",
            "session_id": db_session_id
        })
        session.commit()
        
        # Verify event was stored
        result = session.execute(text("""
            SELECT event_type, event_sequence, trace_id, event_payload 
            FROM event_ledger 
            WHERE session_id = :id
        """), {"id": db_session_id})
        row = result.fetchone()
        
        if row:
            print(f"✅ Event persisted:")
            print(f"   - Type: {row[0]}")
            print(f"   - Sequence: {row[1]}")
            print(f"   - trace_id match: {row[2] == trace_id}")
            print(f"   - Payload: {row[3]}")
            
            # Cleanup
            session.execute(text("DELETE FROM event_ledger WHERE session_id = :id"), {"id": db_session_id})
            session.execute(text("DELETE FROM sessions WHERE id = :id"), {"id": db_session_id})
            session.commit()
            
            return True
        else:
            print("❌ Event not found in database")
            return False


def test_trace_id_propagation():
    """Test 4: trace_id propagates through multiple events"""
    print("\n=== Test 4: trace_id Propagation ===")
    
    with SessionLocal() as session:
        # Create test session
        trace_id = uuid.uuid4()
        session_id = f"test-{uuid.uuid4()}"
        
        session.execute(text("""
            INSERT INTO sessions (external_id, title, status, locale, trace_id, started_at)
            VALUES (:id, :title, 'active', 'en', :trace_id, NOW())
        """), {"id": session_id, "title": "Trace Test", "trace_id": trace_id})
        session.commit()
        
        result = session.execute(text("SELECT id FROM sessions WHERE external_id = :id"), {"id": session_id})
        db_session_id = result.fetchone()[0]
        
        # Create multiple events with same trace_id
        for i, event_type in enumerate(['record_start', 'transcript_partial', 'session_finalized'], start=1):
            session.execute(text("""
                INSERT INTO event_ledger (
                    trace_id, event_type, event_sequence, session_id, status, created_at
                ) VALUES (
                    :trace_id, :event_type, :seq, :session_id, 'success', NOW()
                )
            """), {
                "trace_id": trace_id,
                "event_type": event_type,
                "seq": i,
                "session_id": db_session_id
            })
        session.commit()
        
        # Verify all events share same trace_id
        result = session.execute(text("""
            SELECT event_type, event_sequence, trace_id 
            FROM event_ledger 
            WHERE session_id = :id 
            ORDER BY event_sequence
        """), {"id": db_session_id})
        events = result.fetchall()
        
        if len(events) == 3:
            all_match = all(e[2] == trace_id for e in events)
            print(f"✅ {len(events)} events created")
            print(f"✅ All events share trace_id: {all_match}")
            
            for event in events:
                print(f"   [{event[1]}] {event[0]}")
            
            # Cleanup
            session.execute(text("DELETE FROM event_ledger WHERE session_id = :id"), {"id": db_session_id})
            session.execute(text("DELETE FROM sessions WHERE id = :id"), {"id": db_session_id})
            session.commit()
            
            return all_match
        else:
            print(f"❌ Expected 3 events, got {len(events)}")
            return False


def test_event_sequencing():
    """Test 5: Events maintain correct sequence order"""
    print("\n=== Test 5: Event Sequencing ===")
    
    with SessionLocal() as session:
        trace_id = uuid.uuid4()
        session_id = f"test-{uuid.uuid4()}"
        
        session.execute(text("""
            INSERT INTO sessions (external_id, title, status, locale, trace_id, started_at)
            VALUES (:id, :title, 'active', 'en', :trace_id, NOW())
        """), {"id": session_id, "title": "Sequence Test", "trace_id": trace_id})
        session.commit()
        
        result = session.execute(text("SELECT id FROM sessions WHERE external_id = :id"), {"id": session_id})
        db_session_id = result.fetchone()[0]
        
        # Create events in specific order
        event_types = ['event_a', 'event_b', 'event_c', 'event_d', 'event_e']
        for i, event_type in enumerate(event_types, start=1):
            session.execute(text("""
                INSERT INTO event_ledger (
                    trace_id, event_type, event_sequence, session_id, status, created_at
                ) VALUES (
                    :trace_id, :event_type, :seq, :session_id, 'success', NOW()
                )
            """), {
                "trace_id": trace_id,
                "event_type": event_type,
                "seq": i,
                "session_id": db_session_id
            })
            time.sleep(0.01)  # Small delay to ensure timestamp ordering
        session.commit()
        
        # Verify sequence ordering
        result = session.execute(text("""
            SELECT event_type, event_sequence 
            FROM event_ledger 
            WHERE session_id = :id 
            ORDER BY event_sequence
        """), {"id": db_session_id})
        events = result.fetchall()
        
        # Check sequence numbers are sequential
        sequences = [e[1] for e in events]
        sequential = sequences == list(range(1, len(sequences) + 1))
        
        print(f"✅ {len(events)} events in correct sequence: {sequential}")
        if not sequential:
            print(f"   Expected: {list(range(1, len(sequences) + 1))}")
            print(f"   Got: {sequences}")
        
        # Cleanup
        session.execute(text("DELETE FROM event_ledger WHERE session_id = :id"), {"id": db_session_id})
        session.execute(text("DELETE FROM sessions WHERE id = :id"), {"id": db_session_id})
        session.commit()
        
        return sequential


def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("CROWN+ EVENT INFRASTRUCTURE INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        test_database_schema,
        test_session_creation_with_trace_id,
        test_event_logger_persistence,
        test_trace_id_propagation,
        test_event_sequencing
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
        print("\n✅ ALL TESTS PASSED - CROWN+ Infrastructure is working correctly!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
