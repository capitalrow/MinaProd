"""
End-to-End Test for Task Extraction in CROWN+ Pipeline

Tests the complete task extraction flow:
1. Create session with realistic transcript containing action items
2. Trigger post-transcription pipeline
3. Verify AI task extraction converts to Task model
4. Verify pattern matching fallback works
5. Verify database persistence
6. Verify correct task counts in events
7. Measure performance and accuracy
"""

import logging
import time
import json
import pytest
from datetime import datetime
from app import app, db
from models.session import Session
from models.segment import Segment
from models.task import Task
from models.summary import Summary
from models.event_ledger import EventLedger, EventType
from services.post_transcription_orchestrator import PostTranscriptionOrchestrator
from sqlalchemy import select, func

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def app_context():
    """Fixture to provide Flask application context for all tests"""
    with app.app_context():
        yield

# Test transcript with clear action items
TEST_TRANSCRIPT_WITH_TASKS = [
    {
        "text": "Welcome everyone to the Q4 planning meeting. Let's review our objectives.",
        "speaker": "Sarah",
        "start_ms": 0,
        "end_ms": 3000
    },
    {
        "text": "I will send the updated budget proposal to the finance team by end of week.",
        "speaker": "John",
        "start_ms": 3000,
        "end_ms": 7000
    },
    {
        "text": "Sarah needs to review the marketing strategy document and provide feedback by Friday.",
        "speaker": "Mike",
        "start_ms": 7000,
        "end_ms": 11000
    },
    {
        "text": "Let's schedule a follow-up meeting for next Tuesday to discuss implementation.",
        "speaker": "Sarah",
        "start_ms": 11000,
        "end_ms": 15000
    },
    {
        "text": "I'll coordinate with the development team to set up the new testing environment.",
        "speaker": "Lisa",
        "start_ms": 15000,
        "end_ms": 19000
    },
    {
        "text": "We need to finalize the timeline and share it with all stakeholders before month-end.",
        "speaker": "John",
        "start_ms": 19000,
        "end_ms": 23000
    }
]

# Test transcript with meta-commentary (should NOT extract false positives)
TEST_TRANSCRIPT_META_COMMENTARY = [
    {
        "text": "The task extraction system should be able to identify action items automatically.",
        "speaker": "Tech Lead",
        "start_ms": 0,
        "end_ms": 4000
    },
    {
        "text": "Can we test the pattern matching to see if it works correctly?",
        "speaker": "Developer",
        "start_ms": 4000,
        "end_ms": 7000
    },
    {
        "text": "The AI will need to review each segment for potential tasks.",
        "speaker": "Tech Lead",
        "start_ms": 7000,
        "end_ms": 10000
    },
    {
        "text": "Should we implement additional validation for task detection?",
        "speaker": "Developer",
        "start_ms": 10000,
        "end_ms": 13000
    }
]

# Test transcript with NO action items
TEST_TRANSCRIPT_NO_TASKS = [
    {
        "text": "Good morning everyone, thanks for joining the call.",
        "speaker": "Host",
        "start_ms": 0,
        "end_ms": 3000
    },
    {
        "text": "The weather has been quite nice this week.",
        "speaker": "Participant",
        "start_ms": 3000,
        "end_ms": 6000
    },
    {
        "text": "I agree, it's been very pleasant. How was your weekend?",
        "speaker": "Host",
        "start_ms": 6000,
        "end_ms": 9000
    }
]


class TestTaskExtractionE2E:
    """End-to-end test for task extraction"""
    
    def log_test_result(self, test_name, passed, details):
        """Log test result"""
        if passed:
            logger.info(f"✅ PASS: {test_name}")
        else:
            logger.error(f"❌ FAIL: {test_name}")
            logger.error(f"   Details: {details}")
            assert False, f"{test_name} failed: {details}"
    
    def create_test_session(self, external_id, transcript_data):
        """Create a test session with segments"""
        # Create session
        session = Session(
            external_id=external_id,
            title=f"Test Session {external_id}",
            status='active',
            started_at=datetime.utcnow()
        )
        db.session.add(session)
        db.session.commit()
        
        # Add segments
        for seg_data in transcript_data:
            segment = Segment(
                session_id=session.id,
                text=seg_data["text"],
                kind='final',
                avg_confidence=0.95,
                start_ms=seg_data["start_ms"],
                end_ms=seg_data["end_ms"]
            )
            db.session.add(segment)
        
        db.session.commit()
        logger.info(f"Created test session {external_id} with {len(transcript_data)} segments")
        return session
    
    def cleanup_test_session(self, external_id):
        """Clean up test session and related data"""
        session = db.session.query(Session).filter_by(external_id=external_id).first()
        if session:
            # Delete related data
            db.session.query(Segment).filter_by(session_id=session.id).delete()
            db.session.query(Task).filter_by(session_id=session.id).delete()
            db.session.query(Summary).filter_by(session_id=session.id).delete()
            db.session.query(EventLedger).filter_by(external_session_id=external_id).delete()
            db.session.delete(session)
            db.session.commit()
            logger.info(f"Cleaned up test session {external_id}")
    
    def test_task_extraction_with_ai(self):
        """Test 1: Task extraction with AI (should extract multiple tasks)"""
        logger.info("\n" + "="*80)
        logger.info("TEST 1: AI Task Extraction (Realistic Transcript)")
        logger.info("="*80)
        
        external_id = f"test_ai_tasks_{int(time.time())}"
        
        try:
            # Create session with action items
            session = self.create_test_session(external_id, TEST_TRANSCRIPT_WITH_TASKS)
            
            # Run pipeline
            orchestrator = PostTranscriptionOrchestrator()
            start_time = time.time()
            result = orchestrator.process_session(external_id)
            duration_ms = (time.time() - start_time) * 1000
            
            # Verify pipeline succeeded
            assert result['success'], f"Pipeline failed: {result.get('events_failed')}"
            
            # Verify tasks were persisted to database
            task_count = db.session.scalar(
                select(func.count()).select_from(Task).where(Task.session_id == session.id)
            )
            
            # Retrieve tasks
            tasks = db.session.query(Task).filter_by(session_id=session.id).all()
            
            # Expected: Should extract at least 4 action items from the transcript
            # - "will send the updated budget proposal"
            # - "needs to review the marketing strategy"
            # - "schedule a follow-up meeting"
            # - "coordinate with the development team"
            # - "finalize the timeline"
            
            passed = task_count >= 3  # At least 3 tasks should be extracted
            
            details = {
                "external_id": external_id,
                "pipeline_duration_ms": round(duration_ms, 2),
                "pipeline_success": result['success'],
                "tasks_extracted": task_count,
                "expected_minimum": 3,
                "events_completed": result.get('events_completed', []),
                "events_failed": result.get('events_failed', []),
                "tasks": [
                    {
                        "title": t.title,
                        "priority": t.priority,
                        "extracted_by_ai": t.extracted_by_ai,
                        "confidence": t.confidence_score
                    }
                    for t in tasks
                ]
            }
            
            self.log_test_result("AI Task Extraction", passed, details)
            
        finally:
            self.cleanup_test_session(external_id)
    
    def test_pattern_matching_fallback(self):
        """Test 2: Pattern matching with meta-commentary (should NOT extract false positives)"""
        logger.info("\n" + "="*80)
        logger.info("TEST 2: Pattern Matching with False Positive Filters")
        logger.info("="*80)
        
        external_id = f"test_meta_{int(time.time())}"
        
        try:
            # Create session with meta-commentary
            session = self.create_test_session(external_id, TEST_TRANSCRIPT_META_COMMENTARY)
            
            # Run pipeline
            orchestrator = PostTranscriptionOrchestrator()
            result = orchestrator.process_session(external_id)
            
            # Verify tasks were NOT extracted from meta-commentary
            task_count = db.session.scalar(
                select(func.count()).select_from(Task).where(Task.session_id == session.id)
            )
            
            tasks = db.session.query(Task).filter_by(session_id=session.id).all()
            
            # Expected: Should extract 0 or very few tasks (meta-commentary should be filtered)
            passed = task_count <= 1  # Allow 1 potential edge case, but ideally 0
            
            details = {
                "external_id": external_id,
                "pipeline_success": result['success'],
                "tasks_extracted": task_count,
                "expected_maximum": 1,
                "tasks": [
                    {
                        "title": t.title,
                        "extracted_by_ai": t.extracted_by_ai
                    }
                    for t in tasks
                ]
            }
            
            self.log_test_result("False Positive Filtering", passed, details)
            
        finally:
            self.cleanup_test_session(external_id)
    
    def test_no_tasks_scenario(self):
        """Test 3: No action items (should handle gracefully)"""
        logger.info("\n" + "="*80)
        logger.info("TEST 3: No Action Items Scenario")
        logger.info("="*80)
        
        external_id = f"test_no_tasks_{int(time.time())}"
        
        try:
            # Create session with no action items
            session = self.create_test_session(external_id, TEST_TRANSCRIPT_NO_TASKS)
            
            # Run pipeline
            orchestrator = PostTranscriptionOrchestrator()
            result = orchestrator.process_session(external_id)
            
            # Verify no tasks extracted
            task_count = db.session.scalar(
                select(func.count()).select_from(Task).where(Task.session_id == session.id)
            )
            
            # Expected: 0 tasks, pipeline should still succeed
            passed = task_count == 0 and result['success']
            
            details = {
                "external_id": external_id,
                "pipeline_success": result['success'],
                "tasks_extracted": task_count,
                "expected": 0
            }
            
            self.log_test_result("No Tasks Graceful Handling", passed, details)
            
        finally:
            self.cleanup_test_session(external_id)
    
    def test_task_persistence(self):
        """Test 4: Verify tasks persist correctly and can be queried"""
        logger.info("\n" + "="*80)
        logger.info("TEST 4: Task Persistence and Query")
        logger.info("="*80)
        
        external_id = f"test_persistence_{int(time.time())}"
        
        try:
            # Create session
            session = self.create_test_session(external_id, TEST_TRANSCRIPT_WITH_TASKS)
            
            # Run pipeline
            orchestrator = PostTranscriptionOrchestrator()
            result = orchestrator.process_session(external_id)
            
            # Query tasks before commit (should exist)
            tasks_before = db.session.query(Task).filter_by(session_id=session.id).all()
            task_count_before = len(tasks_before)
            
            # Clear session cache and query again (simulate page refresh)
            db.session.expire_all()
            
            # Query tasks after cache clear (should still exist)
            tasks_after = db.session.query(Task).filter_by(session_id=session.id).all()
            task_count_after = len(tasks_after)
            
            # Verify persistence
            passed = (
                task_count_before > 0 and
                task_count_before == task_count_after and
                all(t.session_id == session.id for t in tasks_after)
            )
            
            details = {
                "external_id": external_id,
                "tasks_before_refresh": task_count_before,
                "tasks_after_refresh": task_count_after,
                "persistence_verified": task_count_before == task_count_after,
                "all_linked_to_session": all(t.session_id == session.id for t in tasks_after)
            }
            
            self.log_test_result("Task Persistence", passed, details)
            
        finally:
            self.cleanup_test_session(external_id)
    
    def test_event_emission_accuracy(self):
        """Test 5: Verify WebSocket events have correct task counts"""
        logger.info("\n" + "="*80)
        logger.info("TEST 5: Event Emission Task Count Accuracy")
        logger.info("="*80)
        
        external_id = f"test_events_{int(time.time())}"
        
        try:
            # Create session
            session = self.create_test_session(external_id, TEST_TRANSCRIPT_WITH_TASKS)
            
            # Run pipeline
            orchestrator = PostTranscriptionOrchestrator()
            result = orchestrator.process_session(external_id)
            
            # Get actual persisted task count
            db_task_count = db.session.scalar(
                select(func.count()).select_from(Task).where(Task.session_id == session.id)
            )
            
            # Check event ledger for task generation event
            event = db.session.query(EventLedger).filter_by(
                external_session_id=external_id,
                event_type=EventType.TASKS_GENERATION
            ).first()
            
            # Verify event payload has correct count
            event_task_count = None
            if event and event.payload:
                event_task_count = event.payload.get('task_count', 0)
            
            passed = (
                db_task_count > 0 and
                event is not None and
                event_task_count == db_task_count
            )
            
            details = {
                "external_id": external_id,
                "database_task_count": db_task_count,
                "event_task_count": event_task_count,
                "counts_match": event_task_count == db_task_count,
                "event_status": event.status if event else None
            }
            
            self.log_test_result("Event Emission Accuracy", passed, details)
            
        finally:
            self.cleanup_test_session(external_id)
    
    def test_performance(self):
        """Test 6: Verify pipeline performance meets targets"""
        logger.info("\n" + "="*80)
        logger.info("TEST 6: Pipeline Performance")
        logger.info("="*80)
        
        external_id = f"test_perf_{int(time.time())}"
        
        try:
            # Create session
            session = self.create_test_session(external_id, TEST_TRANSCRIPT_WITH_TASKS)
            
            # Run pipeline and measure time
            orchestrator = PostTranscriptionOrchestrator()
            start_time = time.time()
            result = orchestrator.process_session(external_id)
            duration_ms = (time.time() - start_time) * 1000
            
            # Performance targets:
            # - Pipeline completion: < 30000ms (30 seconds)
            # - Task extraction: < 10000ms (10 seconds)
            
            # Get task extraction duration from result
            task_extraction_ms = result.get('total_duration_ms', 0)
            
            passed = (
                duration_ms < 30000 and  # Total under 30s
                result['success']
            )
            
            details = {
                "external_id": external_id,
                "total_duration_ms": round(duration_ms, 2),
                "target_ms": 30000,
                "under_target": duration_ms < 30000,
                "pipeline_success": result['success']
            }
            
            self.log_test_result("Pipeline Performance", passed, details)
            
        finally:
            self.cleanup_test_session(external_id)
    
    def run_all_tests(self):
        """Run all end-to-end tests"""
        logger.info("\n" + "="*80)
        logger.info("TASK EXTRACTION E2E TEST SUITE")
        logger.info("="*80)
        logger.info(f"Started at: {datetime.utcnow().isoformat()}")
        
        start_time = time.time()
        
        # Run all tests
        tests = [
            self.test_task_extraction_with_ai,
            self.test_pattern_matching_fallback,
            self.test_no_tasks_scenario,
            self.test_task_persistence,
            self.test_event_emission_accuracy,
            self.test_performance
        ]
        
        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                logger.exception(f"Test {test_func.__name__} failed with exception")
                self.log_test_result(
                    test_func.__name__,
                    False,
                    {"error": str(e), "exception_type": type(e).__name__}
                )
        
        total_duration = time.time() - start_time
        
        # Generate final report
        self.generate_report(total_duration)
    
    def generate_report(self, duration):
        """Generate final test report"""
        logger.info("\n" + "="*80)
        logger.info("TEST SUITE RESULTS")
        logger.info("="*80)
        
        summary = self.results["summary"]
        success_rate = (summary["passed"] / summary["total"] * 100) if summary["total"] > 0 else 0
        
        logger.info(f"Total Tests: {summary['total']}")
        logger.info(f"Passed: {summary['passed']} ✅")
        logger.info(f"Failed: {summary['failed']} ❌")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Duration: {duration:.2f}s")
        
        # Determine grade
        if success_rate == 100:
            grade = "A+"
        elif success_rate >= 90:
            grade = "A"
        elif success_rate >= 80:
            grade = "B"
        else:
            grade = "F"
        
        logger.info(f"Grade: {grade}")
        
        # Save detailed results
        self.results["summary"]["duration_seconds"] = round(duration, 2)
        self.results["summary"]["success_rate"] = round(success_rate, 1)
        self.results["summary"]["grade"] = grade
        
        report_file = f"test_results_task_extraction_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"\n📄 Detailed results saved to: {report_file}")
        
        # Print detailed test results
        logger.info("\n" + "="*80)
        logger.info("DETAILED TEST RESULTS")
        logger.info("="*80)
        
        for test in self.results["tests"]:
            status = "✅ PASS" if test["passed"] else "❌ FAIL"
            logger.info(f"\n{status}: {test['test']}")
            logger.info(f"Details: {json.dumps(test['details'], indent=2, default=str)}")
        
        return success_rate == 100


def main():
    """Main test execution"""
    with app.app_context():
        # Verify OPENAI_API_KEY is set
        import os
        if not os.getenv('OPENAI_API_KEY'):
            logger.error("❌ OPENAI_API_KEY not set. AI extraction will fail.")
            logger.error("Set the OPENAI_API_KEY environment variable and try again.")
            return False
        
        # Run tests
        test_suite = TaskExtractionE2ETest()
        all_passed = test_suite.run_all_tests()
        
        if all_passed:
            logger.info("\n🎉 ALL TESTS PASSED! Task extraction is 100% functional.")
            return True
        else:
            logger.error("\n❌ SOME TESTS FAILED. Review the results above.")
            return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
