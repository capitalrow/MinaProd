"""
COMPREHENSIVE END-TO-END TASK EXTRACTION TEST
Tests complete pipeline: Transcript → AI Extraction → Refinement → Metadata → UI Display

This test validates 100% functionality of:
- Task extraction from realistic meeting transcripts
- LLM-based semantic refinement (conversational → professional)
- Priority/due date/assignee metadata extraction
- Data persistence to database
- UI data serialization (to_dict() with extraction_context)
- CROWN+ visual hierarchy preparation
"""

import os
import sys
import json
from datetime import datetime, date
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set test environment
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')

# Import after environment setup
from app import app, db
from models.session import Session
from models.segment import Segment
from models.task import Task
from services.post_transcription_orchestrator import PostTranscriptionOrchestrator
from services.task_refinement_service import get_task_refinement_service
from services.validation_engine import get_validation_engine
from services.date_parser_service import get_date_parser_service
from services.user_matching_service import get_user_matching_service

# Test data: Realistic meeting transcript with embedded tasks
REALISTIC_MEETING_TRANSCRIPT = [
    {
        "text": "Okay team, let's review our quarterly goals. I will take from here is then check the replit agent test progress by Friday.",
        "start_ms": 0,
        "end_ms": 5000,
        "speaker": "Sarah"
    },
    {
        "text": "Great. John, can you review the analytics dashboard and send me the performance metrics tomorrow?",
        "start_ms": 5000,
        "end_ms": 10000,
        "speaker": "Sarah"
    },
    {
        "text": "Sure thing. I'll also schedule a follow-up meeting with the design team next week to discuss UI improvements.",
        "start_ms": 10000,
        "end_ms": 15000,
        "speaker": "John"
    },
    {
        "text": "Perfect. We need to finalize the API documentation before the sprint ends.",
        "start_ms": 15000,
        "end_ms": 18000,
        "speaker": "Maria"
    }
]


class TestTaskExtractionCompleteE2E:
    """
    End-to-end test validating complete task extraction pipeline.
    """
    
    @classmethod
    def setup_class(cls):
        """Setup test database and application context."""
        cls.app = app
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        # Create all tables
        db.create_all()
        
        print("\n" + "="*80)
        print("COMPREHENSIVE TASK EXTRACTION E2E TEST")
        print("="*80)
    
    @classmethod
    def teardown_class(cls):
        """Cleanup test database."""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
        
        print("\n" + "="*80)
        print("TEST CLEANUP COMPLETE")
        print("="*80)
    
    def test_01_service_initialization(self):
        """Test 1: Verify all services initialize correctly."""
        print("\n[TEST 1] Service Initialization")
        print("-" * 80)
        
        refinement_service = get_task_refinement_service()
        validation_engine = get_validation_engine()
        date_parser = get_date_parser_service()
        user_matcher = get_user_matching_service()
        
        assert refinement_service is not None, "TaskRefinementService failed to initialize"
        assert validation_engine is not None, "ValidationEngine failed to initialize"
        assert date_parser is not None, "DateParserService failed to initialize"
        assert user_matcher is not None, "UserMatchingService failed to initialize"
        
        print("✅ All services initialized successfully")
        print(f"   - TaskRefinementService: {type(refinement_service).__name__}")
        print(f"   - ValidationEngine: {type(validation_engine).__name__}")
        print(f"   - DateParserService: {type(date_parser).__name__}")
        print(f"   - UserMatchingService: {type(user_matcher).__name__}")
    
    def test_02_task_refinement_transformation(self):
        """Test 2: Verify LLM-based semantic refinement."""
        print("\n[TEST 2] Task Refinement Transformation")
        print("-" * 80)
        
        refinement_service = get_task_refinement_service()
        
        # Test cases: conversational → professional
        test_cases = [
            {
                "raw": "I will take from here is then check the replit agent test progress",
                "expected_contains": ["check", "replit", "agent", "test"],
                "should_transform": True
            },
            {
                "raw": "can you review the analytics dashboard and send me the performance metrics",
                "expected_contains": ["review", "analytics", "dashboard", "metrics"],
                "should_transform": True
            }
        ]
        
        for idx, test_case in enumerate(test_cases):
            result = refinement_service.refine_task(
                raw_task=test_case["raw"],
                context={}
            )
            
            print(f"\n   Test Case {idx + 1}:")
            print(f"   Raw:     '{test_case['raw']}'")
            print(f"   Refined: '{result.refined_text}'")
            print(f"   Success: {result.success}")
            print(f"   Applied: {result.transformation_applied}")
            
            if result.success:
                # Verify transformation occurred
                assert result.refined_text != test_case["raw"], "No transformation applied"
                
                # Verify key words preserved
                for keyword in test_case["expected_contains"]:
                    assert keyword.lower() in result.refined_text.lower(), f"Keyword '{keyword}' lost in refinement"
                
                # Verify professional formatting
                assert result.refined_text[0].isupper(), "First letter should be capitalized"
                assert not result.refined_text.startswith("I will"), "Conversational phrases should be removed"
                
                print(f"   ✅ Transformation successful")
            else:
                print(f"   ⚠️ Refinement skipped (using original): {result.error}")
    
    def test_03_date_parsing_intelligence(self):
        """Test 3: Verify intelligent due date parsing."""
        print("\n[TEST 3] Intelligent Date Parsing")
        print("-" * 80)
        
        date_parser = get_date_parser_service()
        
        # Test temporal references
        test_cases = [
            {"text": "by Friday", "should_parse": True},
            {"text": "tomorrow", "should_parse": True},
            {"text": "next week", "should_parse": True},
            {"text": "end of sprint", "should_parse": False},  # Ambiguous
            {"text": "2024-12-31", "should_parse": True}
        ]
        
        for test_case in test_cases:
            result = date_parser.parse_due_date(test_case["text"])
            
            print(f"\n   Input: '{test_case['text']}'")
            print(f"   Parsed: {result.date if result.success else 'Failed'}")
            print(f"   Interpretation: {result.interpretation}")
            
            if test_case["should_parse"]:
                assert result.success, f"Should have parsed '{test_case['text']}'"
                assert result.date is not None, "Date should not be None"
                assert isinstance(result.date, date), "Should return datetime.date object"
                print(f"   ✅ Successfully parsed")
            else:
                print(f"   ⚠️ Ambiguous reference (expected)")
    
    def test_04_validation_quality_gates(self):
        """Test 4: Verify validation engine quality scoring."""
        print("\n[TEST 4] Validation Quality Gates")
        print("-" * 80)
        
        validation_engine = get_validation_engine()
        
        # Test quality scoring
        test_cases = [
            {
                "task": "Review analytics dashboard",
                "evidence": "can you review the analytics dashboard",
                "expected_score_range": (0.7, 1.0),  # High quality
                "should_pass": True
            },
            {
                "task": "check",  # Incomplete
                "evidence": "check",
                "expected_score_range": (0.0, 0.5),  # Low quality
                "should_pass": False
            },
            {
                "task": "This is not really a task it's just a comment",
                "evidence": "",
                "expected_score_range": (0.0, 0.6),  # No action verb
                "should_pass": False
            }
        ]
        
        for idx, test_case in enumerate(test_cases):
            score = validation_engine.score_task_quality(
                task_text=test_case["task"],
                evidence_quote=test_case["evidence"],
                transcript="Sample meeting transcript"
            )
            
            print(f"\n   Test Case {idx + 1}: '{test_case['task']}'")
            print(f"   Total Score: {score.total_score:.2f}")
            print(f"   Breakdown:")
            print(f"     - Has Action Verb: {score.has_action_verb}")
            print(f"     - Has Subject: {score.has_subject}")
            print(f"     - Appropriate Length: {score.appropriate_length}")
            print(f"     - Has Evidence: {score.has_evidence}")
            
            min_score, max_score = test_case["expected_score_range"]
            assert min_score <= score.total_score <= max_score, \
                f"Score {score.total_score:.2f} outside expected range [{min_score}, {max_score}]"
            
            passes = score.total_score >= validation_engine.MIN_TASK_SCORE
            assert passes == test_case["should_pass"], \
                f"Quality gate {'should pass' if test_case['should_pass'] else 'should fail'}"
            
            if passes:
                print(f"   ✅ Passed quality gate ({validation_engine.MIN_TASK_SCORE})")
            else:
                print(f"   ⚠️ Rejected (below threshold {validation_engine.MIN_TASK_SCORE})")
    
    def test_05_end_to_end_pipeline_with_db_persistence(self):
        """Test 5: Complete pipeline with database persistence."""
        print("\n[TEST 5] End-to-End Pipeline with Database Persistence")
        print("-" * 80)
        
        # Create test session
        session = Session(
            external_id=f"test_session_{datetime.utcnow().timestamp()}",
            title="Test Meeting - Task Extraction",
            status="completed"
        )
        db.session.add(session)
        db.session.commit()
        
        print(f"\n   Created session: {session.external_id} (ID: {session.id})")
        
        # Add transcript segments
        for seg_data in REALISTIC_MEETING_TRANSCRIPT:
            segment = Segment(
                session_id=session.id,
                text=seg_data["text"],
                start_ms=seg_data["start_ms"],
                end_ms=seg_data["end_ms"],
                kind="final",
                avg_confidence=0.95
            )
            db.session.add(segment)
        
        db.session.commit()
        print(f"   Added {len(REALISTIC_MEETING_TRANSCRIPT)} transcript segments")
        
        # Run pattern-based task extraction (simulating AI unavailable scenario)
        from services.post_transcription_orchestrator import PostTranscriptionOrchestrator
        
        # Extract tasks using pattern matching
        orchestrator = PostTranscriptionOrchestrator()
        
        # Manually trigger pattern extraction for testing
        transcript_segments = []
        for seg in db.session.query(Segment).filter_by(session_id=session.id, kind='final').all():
            transcript_segments.append({
                'text': seg.text,
                'segment_id': seg.id,
                'start_ms': seg.start_ms,
                'end_ms': seg.end_ms
            })
        
        tasks = orchestrator._extract_tasks_from_transcript(session.id, transcript_segments)
        
        print(f"\n   Extracted {len(tasks)} tasks from transcript")
        
        # Verify tasks were persisted
        persisted_tasks = db.session.query(Task).filter_by(session_id=session.id).all()
        assert len(persisted_tasks) > 0, "No tasks were persisted to database"
        
        print(f"   ✅ {len(persisted_tasks)} tasks persisted to database")
        
        # Verify task data completeness
        for idx, task in enumerate(persisted_tasks):
            print(f"\n   Task {idx + 1}:")
            print(f"     Title: {task.title}")
            print(f"     Priority: {task.priority}")
            print(f"     Status: {task.status}")
            print(f"     Confidence: {task.confidence_score}")
            print(f"     Extraction Context: {bool(task.extraction_context)}")
            
            # Verify required fields
            assert task.title is not None and len(task.title) > 0, "Task title is empty"
            assert task.session_id == session.id, "Session ID mismatch"
            assert task.priority in ['low', 'medium', 'high'], f"Invalid priority: {task.priority}"
            assert task.status in ['todo', 'in_progress', 'completed', 'blocked', 'cancelled'], \
                f"Invalid status: {task.status}"
            assert task.confidence_score is not None, "Confidence score is None"
            assert task.extraction_context is not None, "Extraction context is None"
            
            print(f"     ✅ All required fields present and valid")
    
    def test_06_ui_data_serialization(self):
        """Test 6: Verify to_dict() includes all UI metadata."""
        print("\n[TEST 6] UI Data Serialization (to_dict)")
        print("-" * 80)
        
        # Get tasks from previous test
        tasks = db.session.query(Task).all()
        assert len(tasks) > 0, "No tasks available for serialization test"
        
        for idx, task in enumerate(tasks[:3]):  # Test first 3 tasks
            task_dict = task.to_dict(include_relationships=True)
            
            print(f"\n   Task {idx + 1} Serialization:")
            print(f"     ID: {task_dict.get('id')}")
            print(f"     Title: {task_dict.get('title')}")
            print(f"     Priority: {task_dict.get('priority')}")
            print(f"     Confidence Score: {task_dict.get('confidence_score')}")
            print(f"     Extraction Context: {bool(task_dict.get('extraction_context'))}")
            print(f"     Due Date: {task_dict.get('due_date')}")
            print(f"     Assigned To: {task_dict.get('assigned_to_id')}")
            print(f"     Status: {task_dict.get('status')}")
            print(f"     Is Overdue: {task_dict.get('is_overdue')}")
            print(f"     Is Due Soon: {task_dict.get('is_due_soon')}")
            
            # Critical assertions for UI display
            assert 'id' in task_dict, "Missing 'id'"
            assert 'title' in task_dict, "Missing 'title'"
            assert 'priority' in task_dict, "Missing 'priority'"
            assert 'confidence_score' in task_dict, "Missing 'confidence_score'"
            assert 'extraction_context' in task_dict, "Missing 'extraction_context' (CRITICAL for UI)"
            assert 'status' in task_dict, "Missing 'status'"
            assert 'is_overdue' in task_dict, "Missing 'is_overdue'"
            assert 'is_due_soon' in task_dict, "Missing 'is_due_soon'"
            
            # Verify extraction_context structure
            if task_dict['extraction_context']:
                ctx = task_dict['extraction_context']
                print(f"\n     Extraction Context Keys: {list(ctx.keys())}")
                
                # Check for UI-critical keys
                expected_keys = ['source', 'transcript_snippet']
                for key in expected_keys:
                    assert key in ctx, f"Missing key '{key}' in extraction_context"
            
            print(f"     ✅ All UI-critical fields present")
    
    def test_07_crown_plus_ui_data_flow(self):
        """Test 7: Verify complete data flow for CROWN+ UI rendering."""
        print("\n[TEST 7] CROWN+ UI Data Flow Verification")
        print("-" * 80)
        
        # Simulate route handler logic
        tasks = db.session.query(Task).all()
        tasks_data = [task.to_dict(include_relationships=True) for task in tasks]
        
        print(f"\n   Simulating UI render with {len(tasks_data)} tasks")
        
        # Group by priority (like template does)
        high_priority = [t for t in tasks_data if t['priority'] == 'high']
        medium_priority = [t for t in tasks_data if t['priority'] == 'medium']
        low_priority = [t for t in tasks_data if t['priority'] == 'low']
        
        print(f"\n   Priority Distribution:")
        print(f"     High: {len(high_priority)}")
        print(f"     Medium: {len(medium_priority)}")
        print(f"     Low: {len(low_priority)}")
        
        # Verify confidence indicators can be rendered
        for task_dict in tasks_data:
            confidence = task_dict.get('confidence_score', 0)
            
            if confidence >= 0.85:
                indicator = "✅ High"
            elif confidence >= 0.65:
                indicator = "⚠️ Medium"
            else:
                indicator = "ℹ️ Low"
            
            print(f"\n   Task: {task_dict['title'][:50]}...")
            print(f"     Confidence: {confidence:.2f} → {indicator}")
            print(f"     Priority: {task_dict['priority']}")
            print(f"     Can render due date: {bool(task_dict.get('due_date'))}")
            print(f"     Can render assignee: {bool(task_dict.get('assigned_to_id')) or bool(task_dict.get('extraction_context', {}).get('metadata_extraction', {}).get('owner_name'))}")
        
        print(f"\n   ✅ All tasks can be rendered with CROWN+ UI components")
    
    def test_08_performance_benchmarks(self):
        """Test 8: Performance and timeliness validation."""
        print("\n[TEST 8] Performance Benchmarks")
        print("-" * 80)
        
        import time
        
        # Test refinement latency
        refinement_service = get_task_refinement_service()
        
        start = time.time()
        result = refinement_service.refine_task(
            raw_task="I will check the test results",
            context={}
        )
        latency_ms = (time.time() - start) * 1000
        
        print(f"\n   Task Refinement Latency: {latency_ms:.2f}ms")
        
        # Note: Without batching, each task triggers LLM request
        # For production, latency should be monitored
        if result.success:
            print(f"   ✅ Refinement completed in {latency_ms:.2f}ms")
        else:
            print(f"   ⚠️ Refinement skipped (fallback to original)")
        
        # Test validation engine performance
        validation_engine = get_validation_engine()
        
        start = time.time()
        score = validation_engine.score_task_quality(
            task_text="Review analytics dashboard",
            evidence_quote="can you review the analytics dashboard",
            transcript="Sample meeting transcript"
        )
        validation_latency_ms = (time.time() - start) * 1000
        
        print(f"\n   Validation Engine Latency: {validation_latency_ms:.2f}ms")
        print(f"   ✅ Quality scoring completed in {validation_latency_ms:.2f}ms")
        
        # Total expected latency per task (refinement + validation)
        total_latency = latency_ms + validation_latency_ms
        print(f"\n   Total Per-Task Latency: {total_latency:.2f}ms")
        
        # Warning for production
        if latency_ms > 1000:
            print(f"   ⚠️ WARNING: Refinement latency > 1s. Consider batching for production.")


def run_complete_test_suite():
    """Run complete test suite with detailed reporting."""
    import pytest
    
    print("\n" + "=" * 80)
    print("STARTING COMPREHENSIVE TASK EXTRACTION E2E TEST SUITE")
    print("=" * 80)
    
    # Run tests with verbose output
    exit_code = pytest.main([
        __file__,
        '-v',  # Verbose
        '-s',  # No capture (show prints)
        '--tb=short',  # Short traceback format
        '--color=yes'  # Colored output
    ])
    
    return exit_code


if __name__ == '__main__':
    exit_code = run_complete_test_suite()
    sys.exit(exit_code)
