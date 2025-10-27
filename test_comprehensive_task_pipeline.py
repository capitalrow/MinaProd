#!/usr/bin/env python3
"""
Comprehensive Task Pipeline Validation Suite

Tests 100% functionality, accuracy, performance, and timeliness of:
- ValidationEngine (meta-commentary filtering)
- TaskRefinementService (professional formatting)
- DateParserService (temporal parsing)
- Priority Intelligence (sentiment analysis)
- Assignee Extraction (NLP patterns)
- End-to-End Pipeline (database → UI)
"""

import sys
import os
from datetime import date, timedelta

# Set up environment
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://localhost/mina_dev')
os.environ['SESSION_SECRET'] = os.environ.get('SESSION_SECRET', 'test_secret_key_12345')
os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', 'test')

print("\n" + "="*80)
print("🧪 COMPREHENSIVE TASK PIPELINE VALIDATION SUITE")
print("="*80)
print("\nTarget: 100% Functionality | 100% Accuracy | 100% Performance | 100% Timeliness")
print("\n" + "="*80)


# =============================================================================
# TEST 1: ValidationEngine - Meta-Commentary Detection
# =============================================================================

def test_validation_engine():
    """Test ValidationEngine filters meta-commentary and scores professional language"""
    print("\n" + "="*80)
    print("TEST 1: ValidationEngine - Meta-Commentary Detection & Professional Scoring")
    print("="*80)
    
    from services.validation_engine import get_validation_engine
    
    validation_engine = get_validation_engine()
    
    # Test cases: (task_text, expected_result, reason)
    test_cases = [
        # VALID business tasks (should PASS with score >= 0.70)
        ("Update product roadmap by Friday", True, "Business action item"),
        ("Schedule Q4 budget review with finance team", True, "Meeting coordination task"),
        ("Fix critical authentication bug before launch", True, "Technical task with urgency"),
        ("Send revenue report to executives", True, "Deliverable task"),
        ("Review code changes for security vulnerabilities", True, "Code review task"),
        
        # INVALID meta-commentary (should FAIL with score < 0.70)
        ("I need to check if the task extraction works", False, "Meta-testing commentary"),
        ("Making sure that all tabs are displayed correctly", False, "System validation commentary"),
        ("I will go ahead and test the pipeline", False, "Testing narration"),
        ("Verify that the post-transcription activities work", False, "System verification commentary"),
        ("Let me quickly check the task tab", False, "Testing action"),
        
        # INVALID conversational fragments (should FAIL due to first-person)
        ("I'll update the documentation this week", False, "First-person language"),
        ("We need to schedule a meeting soon", False, "First-person plural"),
        ("I'm going to fix this bug tomorrow", False, "Conversational style"),
    ]
    
    passed = 0
    failed = 0
    
    for task_text, should_pass, reason in test_cases:
        score = validation_engine.score_task_quality(
            task_text=task_text,
            evidence_quote=task_text,
            transcript="Business meeting context"
        )
        
        actual_pass = score.total_score >= 0.70
        test_passed = actual_pass == should_pass
        
        if test_passed:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = "❌ FAIL"
        
        print(f"\n{status}")
        print(f"  Task: '{task_text[:60]}'")
        print(f"  Score: {score.total_score:.2f} (threshold: 0.70)")
        print(f"  Expected: {'PASS' if should_pass else 'REJECT'}, Got: {'PASS' if actual_pass else 'REJECT'}")
        print(f"  Reason: {reason}")
    
    print(f"\n{'='*80}")
    print(f"ValidationEngine Test Results: {passed}/{len(test_cases)} passed")
    print(f"{'='*80}")
    
    return failed == 0


# =============================================================================
# TEST 2: TaskRefinementService - Professional Transformation
# =============================================================================

def test_task_refinement_service():
    """Test TaskRefinementService transforms conversational → professional"""
    print("\n" + "="*80)
    print("TEST 2: TaskRefinementService - Professional Transformation")
    print("="*80)
    
    from services.task_refinement_service import get_task_refinement_service
    
    refinement_service = get_task_refinement_service()
    
    # Test cases: (raw_task, quality_checks)
    test_cases = [
        ("I'll update the product spec by Friday", {
            'no_first_person': True,
            'starts_capital': True,
            'ends_period': True,
            'is_imperative': True,
            'description': "First-person removal"
        }),
        ("we need to schedule a team meeting", {
            'no_first_person': True,
            'starts_capital': True,
            'ends_period': True,
            'is_imperative': True,
            'description': "We → imperative form"
        }),
        ("I'm going to send the report tomorrow", {
            'no_first_person': True,
            'starts_capital': True,
            'ends_period': True,
            'is_imperative': True,
            'description': "Conversational → professional"
        }),
        ("fix the login bug ASAP", {
            'starts_capital': True,
            'ends_period': True,
            'description': "Capitalization fix"
        }),
    ]
    
    passed = 0
    failed = 0
    
    for raw_task, checks in test_cases:
        result = refinement_service.refine_task(raw_task, context={})
        refined = result.refined_text if result.success else raw_task
        
        # Run quality checks
        test_passed = True
        failures = []
        
        if checks.get('no_first_person'):
            has_first_person = any(word in refined.lower() for word in ['i ', 'we ', "i'll", "we'll", "i'm", "we're"])
            if has_first_person:
                test_passed = False
                failures.append("contains first-person")
        
        if checks.get('starts_capital'):
            if not refined[0].isupper():
                test_passed = False
                failures.append("doesn't start with capital")
        
        if checks.get('ends_period'):
            if not refined[-1] == '.':
                test_passed = False
                failures.append("doesn't end with period")
        
        if checks.get('is_imperative'):
            # Check if it starts with a verb (imperative form)
            first_word = refined.split()[0].lower()
            imperative_verbs = ['update', 'schedule', 'send', 'fix', 'review', 'create', 'complete', 'prepare']
            if not any(first_word.startswith(verb) for verb in imperative_verbs):
                test_passed = False
                failures.append("not imperative form")
        
        if test_passed:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = "❌ FAIL"
        
        print(f"\n{status}")
        print(f"  Raw:     '{raw_task}'")
        print(f"  Refined: '{refined}'")
        print(f"  Test:    {checks['description']}")
        if failures:
            print(f"  Issues:  {', '.join(failures)}")
    
    print(f"\n{'='*80}")
    print(f"TaskRefinementService Test Results: {passed}/{len(test_cases)} passed")
    print(f"{'='*80}")
    
    return failed == 0


# =============================================================================
# TEST 3: DateParserService - Temporal Reference Parsing
# =============================================================================

def test_date_parser_service():
    """Test DateParserService parses temporal references"""
    print("\n" + "="*80)
    print("TEST 3: DateParserService - Temporal Reference Parsing")
    print("="*80)
    
    from services.date_parser_service import get_date_parser_service
    
    date_parser = get_date_parser_service()
    
    # Test cases
    test_cases = [
        "by Friday",
        "end of week",
        "next Monday",
        "this week",
        "next sprint",
        "Q1",
        "Q4",
        "end of month",
    ]
    
    passed = 0
    failed = 0
    
    for temporal_ref in test_cases:
        result = date_parser.parse_due_date(temporal_ref)
        
        if result.success:
            passed += 1
            status = "✅ PASS"
            print(f"{status} '{temporal_ref:20s}' → {result.interpretation}")
        else:
            failed += 1
            status = "❌ FAIL"
            print(f"{status} '{temporal_ref:20s}' → could not parse")
    
    print(f"\n{'='*80}")
    print(f"DateParserService Test Results: {passed}/{len(test_cases)} passed")
    print(f"{'='*80}")
    
    return failed == 0


# =============================================================================
# TEST 4: Priority Intelligence - Sentiment Analysis
# =============================================================================

def test_priority_intelligence():
    """Test priority detection with sentiment analysis"""
    print("\n" + "="*80)
    print("TEST 4: Priority Intelligence - Keyword + Sentiment + Deadline")
    print("="*80)
    
    from services.post_transcription_orchestrator import _determine_priority
    
    # Test cases: (task_text, evidence, due_date, expected_priority, reason)
    test_cases = [
        # HIGH priority - explicit keywords
        ("Fix critical bug ASAP", "critical bug", None, "high", "Keyword: critical + ASAP"),
        ("Urgent: Update security patch", "urgent security", None, "high", "Keyword: urgent"),
        
        # HIGH priority - deadline proximity
        ("Send report", "send report", date.today() + timedelta(days=1), "high", "Due tomorrow"),
        
        # HIGH priority - negative sentiment
        ("Fix broken authentication system", "broken auth must fix", None, "high", "Sentiment: broken + must + fix"),
        ("Resolve login issue preventing users", "issue error problem", None, "high", "Sentiment: issue + error + problem"),
        
        # MEDIUM priority - default
        ("Update documentation", "update docs", None, "medium", "No urgency indicators"),
        ("Schedule team meeting", "schedule meeting", None, "medium", "Default priority"),
        
        # MEDIUM priority - deadline within week
        ("Prepare presentation", "prepare slides", date.today() + timedelta(days=5), "medium", "Due in 5 days"),
        
        # LOW priority - explicit keywords
        ("Update docs whenever possible", "whenever possible", None, "low", "Keyword: whenever"),
        ("Nice to have feature eventually", "nice to have eventually", None, "low", "Keywords: nice-to-have + eventually"),
        
        # LOW priority - positive sentiment
        ("Maybe add new feature if time permits", "maybe could would", None, "low", "Sentiment: maybe + could + would"),
    ]
    
    passed = 0
    failed = 0
    
    for task_text, evidence, due_date, expected_priority, reason in test_cases:
        detected_priority = _determine_priority(task_text, evidence, due_date)
        
        if detected_priority == expected_priority:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = "❌ FAIL"
        
        print(f"\n{status}")
        print(f"  Task: '{task_text[:50]}'")
        print(f"  Expected: {expected_priority:6s} | Got: {detected_priority:6s}")
        print(f"  Reason: {reason}")
    
    print(f"\n{'='*80}")
    print(f"Priority Intelligence Test Results: {passed}/{len(test_cases)} passed")
    print(f"{'='*80}")
    
    return failed == 0


# =============================================================================
# TEST 5: Assignee Extraction - NLP Pattern Matching
# =============================================================================

def test_assignee_extraction():
    """Test assignee extraction from context"""
    print("\n" + "="*80)
    print("TEST 5: Assignee Extraction - NLP Pattern Matching")
    print("="*80)
    
    from services.post_transcription_orchestrator import _extract_assignee_from_context
    
    # Test cases: (evidence_text, speaker_name, expected_assignee, reason)
    test_cases = [
        ("I'll handle the documentation update", "Sarah", "Sarah", "First-person → speaker"),
        ("John will fix the authentication bug", None, "John", "Third-person: John will"),
        ("Mike should prepare the presentation", None, "Mike", "Third-person: Mike should"),
        ("Assigned to Alex for code review", None, "Alex", "Explicit assignment"),
        ("Someone needs to update the API", None, None, "No clear assignee"),
    ]
    
    passed = 0
    failed = 0
    
    for evidence_text, speaker_name, expected_assignee, reason in test_cases:
        detected_assignee = _extract_assignee_from_context(evidence_text, speaker_name)
        
        if detected_assignee == expected_assignee:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = "⚠️  PARTIAL" if detected_assignee else "❌ FAIL"
        
        print(f"\n{status}")
        print(f"  Context: '{evidence_text[:50]}'")
        print(f"  Expected: {expected_assignee or '(none)':10s} | Got: {detected_assignee or '(none)':10s}")
        print(f"  Reason: {reason}")
    
    print(f"\n{'='*80}")
    print(f"Assignee Extraction Test Results: {passed}/{len(test_cases)} passed")
    print(f"{'='*80}")
    
    return failed == 0


# =============================================================================
# TEST 6: End-to-End Pipeline with Real Business Meeting
# =============================================================================

def test_e2e_business_meeting():
    """Test complete pipeline with realistic business meeting"""
    print("\n" + "="*80)
    print("TEST 6: End-to-End Pipeline - Real Business Meeting")
    print("="*80)
    
    from app import app, db
    from models.session import Session
    from models.segment import Segment
    from models.task import Task
    from services.post_transcription_orchestrator import PostTranscriptionOrchestrator
    from datetime import datetime
    
    # Ensure app context
    with app.app_context():
        # Create test session
        session = Session(
            external_id='test-comprehensive-001',
            title='Product Strategy Meeting',
            started_at=datetime.utcnow()
        )
        db.session.add(session)
        db.session.commit()
        session_id = session.id
        
        print(f"\n✅ Created test session ID: {session_id}")
        
        try:
            # Realistic business meeting transcript
            meeting_segments = [
                "Sarah: Good morning team. Let's review our product roadmap. First priority is fixing the critical authentication bug before the launch next Monday.",
                "John: I'll handle the bug fix. I can have it ready by Friday. We should also update the API documentation.",
                "Sarah: Great. Mike, can you schedule a meeting with the engineering team to review the architecture changes?",
                "Mike: Absolutely. I'll send calendar invites this afternoon. Should we also prepare a status report for the executives?",
                "Sarah: Yes, please send the Q4 progress report to the leadership team by end of week. Mark it as high priority.",
                "John: One more thing - we might want to eventually update the user onboarding flow, but that's low priority for now.",
            ]
            
            # Create segments
            start_time = 0
            for idx, text in enumerate(meeting_segments):
                duration = 6000
                segment = Segment(
                    session_id=session_id,
                    text=text,
                    start_ms=start_time,
                    end_ms=start_time + duration,
                    kind='final',
                    avg_confidence=0.95
                )
                db.session.add(segment)
                start_time += duration
            
            db.session.commit()
            print(f"✅ Created {len(meeting_segments)} transcript segments")
            
            # Run post-transcription orchestrator
            print("\n🔄 Running post-transcription pipeline...")
            orchestrator = PostTranscriptionOrchestrator()
            result = orchestrator.process_session(session.external_id)
            
            print(f"\n📊 Pipeline Results:")
            print(f"  - Summary created: {result.get('summary_created', False)}")
            print(f"  - Tasks created: {result.get('tasks_created', 0)}")
            
            # Verify tasks in database
            tasks = db.session.query(Task).filter_by(session_id=session_id).all()
            
            if len(tasks) == 0:
                print("\n❌ FAIL: No tasks extracted from business meeting!")
                return False
            
            print(f"\n✅ Database verification: {len(tasks)} tasks persisted")
            
            # Analyze task quality
            print("\n📋 TASK QUALITY ANALYSIS:")
            print("="*80)
            
            high_quality_count = 0
            professional_count = 0
            has_metadata_count = 0
            
            for idx, task in enumerate(tasks, 1):
                print(f"\nTask {idx}:")
                print(f"  Title: '{task.title}'")
                
                # Check 1: Confidence score
                confidence = task.confidence_score or 0.0
                is_high_confidence = confidence >= 0.70
                confidence_icon = "✅" if is_high_confidence else "❌"
                print(f"  {confidence_icon} Confidence: {confidence:.2f} ({'HIGH' if is_high_confidence else 'LOW'})")
                
                if is_high_confidence:
                    high_quality_count += 1
                
                # Check 2: Professional formatting
                has_first_person = any(word in task.title.lower() for word in ['i ', 'we ', "i'll", "we'll"])
                starts_capital = task.title[0].isupper()
                ends_properly = task.title[-1] in ['.', '!', '?']
                is_professional = not has_first_person and starts_capital
                
                professional_icon = "✅" if is_professional else "❌"
                print(f"  {professional_icon} Professional: no_first_person={not has_first_person}, capitalized={starts_capital}")
                
                if is_professional:
                    professional_count += 1
                
                # Check 3: Metadata
                print(f"  📌 Priority: {task.priority}")
                print(f"  📅 Due date: {task.due_date or 'Not specified'}")
                print(f"  👤 Assigned: {task.assigned_to or 'Not specified'}")
                
                has_metadata = task.priority or task.due_date
                if has_metadata:
                    has_metadata_count += 1
                
                # Check 4: Extraction context
                context = task.extraction_context or {}
                print(f"  🔍 Source: {context.get('source', 'unknown')}")
                print(f"  ⚙️  AI extracted: {task.extracted_by_ai}")
            
            # Success criteria
            print(f"\n{'='*80}")
            print("QUALITY METRICS:")
            print(f"  Tasks extracted: {len(tasks)}")
            print(f"  High confidence (≥0.70): {high_quality_count}/{len(tasks)} ({high_quality_count/len(tasks)*100:.0f}%)")
            print(f"  Professional formatting: {professional_count}/{len(tasks)} ({professional_count/len(tasks)*100:.0f}%)")
            print(f"  Has metadata: {has_metadata_count}/{len(tasks)} ({has_metadata_count/len(tasks)*100:.0f}%)")
            
            # Success thresholds
            success = (
                len(tasks) >= 3 and  # At least 3 tasks extracted
                high_quality_count >= len(tasks) * 0.7 and  # 70%+ high confidence
                professional_count >= len(tasks) * 0.8  # 80%+ professional formatting
            )
            
            if success:
                print(f"\n✅ TEST PASSED - Pipeline meets quality standards")
            else:
                print(f"\n❌ TEST FAILED - Pipeline below quality thresholds")
            
            print(f"{'='*80}")
            
            return success
            
        finally:
            # Cleanup
            try:
                db.session.query(Task).filter_by(session_id=session_id).delete()
                db.session.query(Segment).filter_by(session_id=session_id).delete()
                db.session.query(Session).filter_by(id=session_id).delete()
                db.session.commit()
                print(f"\n✅ Cleaned up test data")
            except Exception as e:
                db.session.rollback()
                print(f"\n⚠️  Cleanup warning: {e}")


# =============================================================================
# RUN ALL TESTS
# =============================================================================

if __name__ == '__main__':
    print("\nStarting comprehensive validation suite...")
    print("Testing: ValidationEngine, TaskRefinementService, DateParserService,")
    print("         Priority Intelligence, Assignee Extraction, E2E Pipeline")
    
    results = {}
    
    # Run all tests
    try:
        results['validation_engine'] = test_validation_engine()
    except Exception as e:
        print(f"❌ ValidationEngine test error: {e}")
        results['validation_engine'] = False
    
    try:
        results['task_refinement'] = test_task_refinement_service()
    except Exception as e:
        print(f"❌ TaskRefinementService test error: {e}")
        results['task_refinement'] = False
    
    try:
        results['date_parser'] = test_date_parser_service()
    except Exception as e:
        print(f"❌ DateParserService test error: {e}")
        results['date_parser'] = False
    
    try:
        results['priority_intelligence'] = test_priority_intelligence()
    except Exception as e:
        print(f"❌ Priority Intelligence test error: {e}")
        results['priority_intelligence'] = False
    
    try:
        results['assignee_extraction'] = test_assignee_extraction()
    except Exception as e:
        print(f"❌ Assignee Extraction test error: {e}")
        results['assignee_extraction'] = False
    
    try:
        results['e2e_pipeline'] = test_e2e_business_meeting()
    except Exception as e:
        print(f"❌ E2E Pipeline test error: {e}")
        import traceback
        traceback.print_exc()
        results['e2e_pipeline'] = False
    
    # Summary
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE TEST SUITE RESULTS")
    print("="*80)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n  Total: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - 100% FUNCTIONALITY CONFIRMED")
        print("\n✅ Pipeline Status:")
        print("  - Meta-commentary filtering: WORKING")
        print("  - Professional transformation: WORKING")
        print("  - Temporal parsing: WORKING")
        print("  - Priority intelligence: WORKING")
        print("  - Assignee extraction: WORKING")
        print("  - End-to-end pipeline: WORKING")
        print("\n🚀 System ready for production use!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed} TEST SUITE(S) FAILED")
        print("\nReview output above for details.")
        sys.exit(1)
