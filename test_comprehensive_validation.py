"""
Comprehensive ValidationEngine Testing Suite
Tests all changes made to achieve 100% extraction rate
"""
import sys
from services.validation_engine import ValidationEngine

def test_validation_engine():
    """Test ValidationEngine with all recent changes"""
    engine = ValidationEngine()
    
    print("="*80)
    print("COMPREHENSIVE VALIDATION ENGINE TEST SUITE")
    print("="*80)
    
    # Test 1: 2-word tasks (previously rejected)
    print("\n[TEST 1] Two-Word Tasks (MIN_TASK_LENGTH=2)")
    print("-" * 80)
    two_word_tasks = [
        "Clean bedroom",
        "Buy milk",
        "Call Sarah",
        "Book desk",
        "Get coffee"
    ]
    
    passed = 0
    failed = 0
    for task in two_word_tasks:
        result = engine.check_sentence_completeness(task)
        status = "✅ PASS" if result.is_valid else "❌ FAIL"
        print(f"{status}: '{task}' - Score: {result.score:.2f}, Reasons: {result.reasons}")
        if result.is_valid:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResult: {passed}/{len(two_word_tasks)} passed ({passed/len(two_word_tasks)*100:.0f}%)")
    
    # Test 2: New action verbs (previously rejected)
    print("\n\n[TEST 2] New Action Verbs Added")
    print("-" * 80)
    new_verb_tasks = [
        "Withdraw 30 pounds from ATM",
        "Clean the office",
        "Book a meeting room",
        "Get the report from John",
        "Take notes during meeting",
        "Collect feedback from team",
        "Gather requirements for project",
        "Obtain approval from manager",
        "Pick up supplies",
        "Fetch data from API",
        "Retrieve documents from archive",
        "Arrange team lunch",
        "Reserve conference room",
        "Cancel old subscription"
    ]
    
    passed = 0
    failed = 0
    for task in new_verb_tasks:
        result = engine.check_sentence_completeness(task)
        has_verb = any(verb in task.lower() for verb in engine.ACTION_VERBS)
        status = "✅ PASS" if (result.is_valid and has_verb) else "❌ FAIL"
        print(f"{status}: '{task}' - HasVerb: {has_verb}, Score: {result.score:.2f}")
        if result.is_valid and has_verb:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResult: {passed}/{len(new_verb_tasks)} passed ({passed/len(new_verb_tasks)*100:.0f}%)")
    
    # Test 3: Edge cases that should be REJECTED
    print("\n\n[TEST 3] Edge Cases - Should Be REJECTED")
    print("-" * 80)
    reject_cases = [
        "and",  # Too short (1 word)
        "or",  # Too short (1 word)
        "the quick",  # No action verb
        "is then",  # Broken grammar
        "Check to make sure that the tabs are relevantly and correctly",  # Incomplete
        "I will check",  # First-person (should get professional penalty)
        "Let's review",  # First-person (should get professional penalty)
    ]
    
    passed = 0
    failed = 0
    for task in reject_cases:
        result = engine.check_sentence_completeness(task)
        status = "✅ PASS (rejected)" if not result.is_valid else "❌ FAIL (accepted)"
        print(f"{status}: '{task}' - Score: {result.score:.2f}, Reasons: {result.reasons}")
        if not result.is_valid:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResult: {passed}/{len(reject_cases)} correctly rejected ({passed/len(reject_cases)*100:.0f}%)")
    
    # Test 4: Task quality scoring
    print("\n\n[TEST 4] Task Quality Scoring")
    print("-" * 80)
    test_transcript = "I need to go back upstairs to my bedroom and clean it up. Let's do this right away today."
    
    quality_tests = [
        ("Clean bedroom", "I need to go back upstairs to my bedroom and clean it up"),
        ("Review budget proposal", "We discussed the budget proposal in the meeting"),
        ("I will check the pipeline", "I will check the pipeline"),  # Should get penalty
        ("Update dashboard", "The dashboard needs updates"),
    ]
    
    for task_text, evidence in quality_tests:
        score = engine.score_task_quality(task_text, evidence, test_transcript)
        status = "✅ PASS" if score.total_score >= engine.MIN_TASK_SCORE else "❌ FAIL"
        print(f"{status}: '{task_text}' - Score: {score.total_score:.2f} (threshold: {engine.MIN_TASK_SCORE})")
        print(f"  Verb: {score.has_action_verb}, Subject: {score.has_subject}, Length: {score.appropriate_length}")
    
    # Test 5: Meta-testing detection
    print("\n\n[TEST 5] Meta-Testing Detection")
    print("-" * 80)
    meta_examples = [
        "Test live transcription and ensure post-transcription is working",
        "Check if the pipeline extracts tasks correctly",
        "Verify that the system is functioning properly",
        "I am testing the application functionality"
    ]
    
    real_examples = [
        "Clean bedroom",
        "Withdraw 30 pounds from ATM",
        "Buy train ticket for tomorrow",
        "Prepare Christmas gifts"
    ]
    
    print("Meta-testing examples (should detect):")
    for example in meta_examples:
        result = engine.detect_meta_testing(example)
        status = "✅ DETECTED" if result.is_valid else "❌ MISSED"
        print(f"{status}: '{example}' - Score: {result.score:.2f}")
    
    print("\nReal tasks (should NOT detect):")
    for example in real_examples:
        result = engine.detect_meta_testing(example)
        status = "✅ PASS" if not result.is_valid else "❌ FALSE POSITIVE"
        print(f"{status}: '{example}' - Score: {result.score:.2f}")
    
    print("\n" + "="*80)
    print("VALIDATION ENGINE TEST SUITE COMPLETE")
    print("="*80)

if __name__ == "__main__":
    try:
        test_validation_engine()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
