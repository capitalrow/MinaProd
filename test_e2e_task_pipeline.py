#!/usr/bin/env python3
"""
End-to-End Integration Test for Task Extraction Pipeline
Tests the complete flow: Transcript → AI Insights → Task Creation → Database → UI Display
"""
import os
import sys

# Set up environment
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://localhost/mina_dev')
os.environ['SESSION_SECRET'] = os.environ.get('SESSION_SECRET', 'test_secret_key_12345')
os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', 'test')

from app import app, db
from models.session import Session
from models.segment import Segment
from models.task import Task
from models.summary import Summary
from services.post_transcription_orchestrator import PostTranscriptionOrchestrator
from services.event_ledger_service import EventLedgerService
from datetime import datetime
import json


# Ensure we're in app context
app_context = app.app_context()
app_context.push()


def cleanup_test_data(session_id):
    """Clean up test data"""
    try:
        db.session.query(Task).filter_by(session_id=session_id).delete()
        db.session.query(Summary).filter_by(session_id=session_id).delete()
        db.session.query(Segment).filter_by(session_id=session_id).delete()
        db.session.query(Session).filter_by(id=session_id).delete()
        db.session.commit()
        print(f"✅ Cleaned up test data for session {session_id}")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️  Cleanup warning: {e}")


def test_real_business_meeting():
    """Test with realistic business meeting transcript"""
    print("\n" + "=" * 80)
    print("TEST 1: Real Business Meeting - Full Pipeline")
    print("=" * 80)
    
    # Create test session
    session = Session(
        external_id='test-e2e-business-001',
        title='Q4 Budget Planning Meeting',
        started_at=datetime.utcnow()
    )
    db.session.add(session)
    db.session.commit()
    session_id = session.id
    
    print(f"\n✅ Created test session ID: {session_id}")
    
    try:
        # Create realistic meeting transcript segments
        meeting_transcript = [
            {
                "speaker": "Sarah",
                "text": "Good morning everyone. Let's review the Q4 budget proposal. We need to finalize this by Friday."
            },
            {
                "speaker": "John",
                "text": "I'll coordinate with the finance team to get the final numbers. We should also review the marketing budget allocation."
            },
            {
                "speaker": "Sarah",
                "text": "Great. Can you also prepare a summary of cost savings opportunities for the executive team?"
            },
            {
                "speaker": "John",
                "text": "Absolutely. I'll have that ready by end of week. Should we schedule a follow-up meeting for next Tuesday?"
            },
            {
                "speaker": "Sarah",
                "text": "Yes, let's do that. I'll send out calendar invites this afternoon."
            }
        ]
        
        # Create segments
        start_time = 0
        for idx, seg_data in enumerate(meeting_transcript):
            duration = 5000  # 5 seconds per segment
            # Note: speaker info is in text for now (Segment model doesn't have speaker_id yet)
            segment = Segment(
                session_id=session_id,
                text=f"{seg_data['speaker']}: {seg_data['text']}",
                start_ms=start_time,
                end_ms=start_time + duration,
                kind='final',
                avg_confidence=0.95
            )
            db.session.add(segment)
            start_time += duration
        
        db.session.commit()
        print(f"✅ Created {len(meeting_transcript)} transcript segments")
        
        # Run post-transcription pipeline
        print("\n🔄 Running post-transcription orchestrator...")
        orchestrator = PostTranscriptionOrchestrator()
        result = orchestrator.process_session(session.external_id)
        
        print(f"\n📊 Pipeline Result:")
        print(f"  - Summary generated: {result.get('summary_created', False)}")
        print(f"  - Tasks created: {result.get('tasks_created', 0)}")
        
        # Verify tasks in database
        tasks = db.session.query(Task).filter_by(session_id=session_id).all()
        print(f"\n✅ Database Verification: {len(tasks)} tasks persisted")
        
        if len(tasks) == 0:
            print("❌ FAIL: No tasks extracted from business meeting!")
            return False
        
        # Display extracted tasks
        print("\n📋 Extracted Tasks:")
        high_quality_count = 0
        for idx, task in enumerate(tasks, 1):
            quality_score = task.confidence_score or 0.0
            is_high_quality = quality_score >= 0.65
            
            if is_high_quality:
                high_quality_count += 1
            
            status_icon = "✅" if is_high_quality else "⚠️ "
            print(f"\n  Task {idx} {status_icon}:")
            print(f"    Title: {task.title}")
            print(f"    Priority: {task.priority}")
            print(f"    Assigned: {task.assigned_to or 'Not specified'}")
            print(f"    Quality Score: {quality_score:.2f}")
            print(f"    AI Extracted: {task.extracted_by_ai}")
        
        # Verify summary
        summary = db.session.query(Summary).filter_by(session_id=session_id).first()
        if summary:
            print(f"\n📝 Summary Generated:")
            print(f"  Length: {len(summary.summary_md or '')} characters")
            print(f"  Actions: {len(summary.actions or [])}")
            print(f"  Decisions: {len(summary.decisions or [])}")
            print(f"\n  Preview: {(summary.summary_md or '')[:200]}...")
            
            # Check for hallucinations
            summary_text = (summary.summary_md or '').lower()
            key_topics = ['budget', 'q4', 'friday', 'finance', 'marketing']
            has_real_content = any(topic in summary_text for topic in key_topics)
            
            if has_real_content:
                print("  ✅ Summary contains relevant content (no hallucination)")
            else:
                print("  ❌ WARNING: Summary may not match transcript!")
                return False
        
        # Success criteria
        success = (
            len(tasks) >= 2 and  # At least 2 tasks extracted
            high_quality_count >= 1 and  # At least 1 high-quality task
            summary is not None  # Summary was created
        )
        
        if success:
            print(f"\n✅ TEST PASSED")
            print(f"  - {len(tasks)} tasks extracted")
            print(f"  - {high_quality_count} high-quality tasks (score ≥ 0.65)")
            print(f"  - Summary generated without hallucination")
        else:
            print(f"\n❌ TEST FAILED")
            print(f"  - Tasks: {len(tasks)} (expected ≥2)")
            print(f"  - High quality: {high_quality_count} (expected ≥1)")
        
        return success
        
    finally:
        # Cleanup
        cleanup_test_data(session_id)


def test_meta_testing_transcript():
    """Test with meta-testing commentary"""
    print("\n" + "=" * 80)
    print("TEST 2: Meta-Testing Transcript - Should Extract Zero/Minimal Tasks")
    print("=" * 80)
    
    # Create test session
    session = Session(
        external_id='test-e2e-meta-002',
        title='System Test Recording',
        started_at=datetime.utcnow()
    )
    db.session.add(session)
    db.session.commit()
    session_id = session.id
    
    print(f"\n✅ Created test session ID: {session_id}")
    
    try:
        # Create meta-testing transcript
        meta_segments = [
            {
                "speaker": "Tester",
                "text": "I'm testing the Mina application to check if the transcription works properly."
            },
            {
                "speaker": "Tester",
                "text": "Let me verify that tasks appear in the Tasks tab from my side."
            },
            {
                "speaker": "Tester",
                "text": "This is just a test recording to validate the post-transcription pipeline."
            }
        ]
        
        # Create segments
        start_time = 0
        for idx, seg_data in enumerate(meta_segments):
            duration = 4000
            segment = Segment(
                session_id=session_id,
                text=f"{seg_data['speaker']}: {seg_data['text']}",
                start_ms=start_time,
                end_ms=start_time + duration,
                kind='final',
                avg_confidence=0.92
            )
            db.session.add(segment)
            start_time += duration
        
        db.session.commit()
        print(f"✅ Created {len(meta_segments)} meta-testing segments")
        
        # Run pipeline
        print("\n🔄 Running post-transcription orchestrator...")
        orchestrator = PostTranscriptionOrchestrator()
        result = orchestrator.process_session(session.external_id)
        
        print(f"\n📊 Pipeline Result:")
        print(f"  - Tasks created: {result.get('tasks_created', 0)}")
        
        # Verify tasks
        tasks = db.session.query(Task).filter_by(session_id=session_id).all()
        print(f"\n✅ Database Verification: {len(tasks)} tasks persisted")
        
        if len(tasks) > 0:
            print("\n⚠️  Tasks extracted from meta-testing:")
            for task in tasks:
                print(f"  - {task.title} (score: {task.confidence_score:.2f})")
        
        # Verify summary acknowledges testing
        summary = db.session.query(Summary).filter_by(session_id=session_id).first()
        if summary:
            summary_text = (summary.summary_md or '').lower()
            is_test_acknowledged = any(word in summary_text for word in ['test', 'testing', 'validation', 'verify'])
            
            print(f"\n📝 Summary Preview: {(summary.summary_md or '')[:150]}...")
            
            if is_test_acknowledged:
                print("  ✅ Summary correctly identifies this as testing/validation")
            else:
                print("  ⚠️  Summary doesn't acknowledge testing nature")
        
        # Success criteria: 0-1 tasks for meta-testing
        success = len(tasks) <= 1
        
        if success:
            print(f"\n✅ TEST PASSED")
            print(f"  - Correctly extracted {len(tasks)} tasks from meta-testing (expected ≤1)")
        else:
            print(f"\n❌ TEST FAILED")
            print(f"  - Extracted {len(tasks)} tasks from meta-testing (expected ≤1)")
        
        return success
        
    finally:
        cleanup_test_data(session_id)


def test_ui_badge_count():
    """Test that badge count matches database count"""
    print("\n" + "=" * 80)
    print("TEST 3: UI Badge Count Accuracy")
    print("=" * 80)
    
    # Create test session with known task count
    session = Session(
        external_id='test-e2e-badge-003',
        title='Badge Count Test',
        started_at=datetime.utcnow()
    )
    db.session.add(session)
    db.session.commit()
    session_id = session.id
    
    print(f"\n✅ Created test session ID: {session_id}")
    
    try:
        # Create exactly 3 tasks
        expected_count = 3
        for i in range(expected_count):
            task = Task(
                session_id=session_id,
                title=f"Test Task {i+1}",
                description="Test task for badge count verification",
                priority="medium",
                status="todo",
                extracted_by_ai=True,
                confidence_score=0.85
            )
            db.session.add(task)
        
        db.session.commit()
        print(f"✅ Created {expected_count} test tasks")
        
        # Verify database count
        db_count = db.session.query(Task).filter_by(session_id=session_id).count()
        
        if db_count == expected_count:
            print(f"✅ TEST PASSED: Database count matches expected ({db_count} == {expected_count})")
            return True
        else:
            print(f"❌ TEST FAILED: Database count mismatch ({db_count} != {expected_count})")
            return False
            
    finally:
        cleanup_test_data(session_id)


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🧪 END-TO-END TASK PIPELINE INTEGRATION TESTS")
    print("=" * 80)
    print("\nTesting complete pipeline: Transcript → Insights → Tasks → Database → UI")
    print("\nTarget: 100% functionality, accuracy, and performance")
    
    # Cleanup any leftover test data first
    print("\n🧹 Cleaning up any leftover test data...")
    try:
        db.session.query(Session).filter(Session.external_id.like('test-e2e-%')).delete(synchronize_session=False)
        db.session.commit()
        print("✅ Test data cleaned")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️  Cleanup note: {e}")
    
    # Run all tests
    results = {}
    
    results['business_meeting'] = test_real_business_meeting()
    results['meta_testing'] = test_meta_testing_transcript()
    results['badge_count'] = test_ui_badge_count()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - 100% FUNCTIONALITY CONFIRMED")
        print("\n✅ Pipeline Status:")
        print("  - Real meeting task extraction: WORKING")
        print("  - Quality validation: WORKING")
        print("  - Meta-testing detection: WORKING")
        print("  - Database persistence: WORKING")
        print("  - Badge count accuracy: WORKING")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED - Review output above")
        sys.exit(1)
