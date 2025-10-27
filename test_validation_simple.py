#!/usr/bin/env python3
"""
Simplified test for the ValidationEngine module.
Tests quality scoring and meta-testing detection without Flask dependencies.
"""
import sys
import os

# Add workspace to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.validation_engine import ValidationEngine


def test_task_quality_scoring():
    """Test the task quality rubric."""
    print("\n" + "=" * 80)
    print("TEST 1: Task Quality Scoring Rubric")
    print("=" * 80)
    
    engine = ValidationEngine()
    transcript = "We need to update the budget proposal by Friday. Sarah will review the marketing strategy. We should schedule a follow-up meeting for next week."
    
    test_cases = [
        {
            "name": "High-quality task with clear action",
            "task": "Update the budget proposal by Friday",
            "evidence": "We need to update the budget proposal by Friday",
            "expected_pass": True
        },
        {
            "name": "Fragment without action verb",
            "task": "from my side",
            "evidence": "Let me check from my side",
            "expected_pass": False
        },
        {
            "name": "Meta-testing commentary",
            "task": "check if tasks appear",
            "evidence": "I'm testing to check if tasks appear",
            "expected_pass": False
        },
        {
            "name": "Very short fragment (<8 words)",
            "task": "check it",
            "evidence": "I'll check it",
            "expected_pass": False
        },
        {
            "name": "Good task with subject and verb",
            "task": "Sarah will review the marketing strategy document",
            "evidence": "Sarah will review the marketing strategy",
            "expected_pass": True
        },
        {
            "name": "Sentence fragment without subject",
            "task": "by end of week",
            "evidence": "I'll do it by end of week",
            "expected_pass": False
        },
        {
            "name": "Clear actionable task",
            "task": "Schedule follow-up meeting for next week",
            "evidence": "Schedule follow-up meeting for next week",
            "expected_pass": True
        }
    ]
    
    passed_count = 0
    failed_count = 0
    
    for tc in test_cases:
        score = engine.score_task_quality(tc["task"], tc["evidence"], transcript)
        actual_pass = score.total_score >= engine.MIN_TASK_SCORE
        test_passed = actual_pass == tc["expected_pass"]
        
        if test_passed:
            passed_count += 1
            status = "✅ PASS"
        else:
            failed_count += 1
            status = "❌ FAIL"
        
        print(f"\n{status} {tc['name']}")
        print(f"  Task: '{tc['task']}'")
        print(f"  Score: {score.total_score:.2f} (threshold: {engine.MIN_TASK_SCORE})")
        print(f"  Result: {'PASS' if actual_pass else 'REJECT'}, Expected: {'PASS' if tc['expected_pass'] else 'REJECT'}")
        print(f"  Breakdown: verb={score.has_action_verb}, subject={score.has_subject}, "
              f"length={score.appropriate_length}, evidence={score.has_evidence}")
    
    print(f"\n{'=' * 80}")
    print(f"Test Results: {passed_count} passed, {failed_count} failed")
    return failed_count == 0


def test_meta_testing_detection():
    """Test meta-testing detection."""
    print("\n" + "=" * 80)
    print("TEST 2: Meta-Testing Detection")
    print("=" * 80)
    
    engine = ValidationEngine()
    
    test_cases = [
        {
            "name": "Clear meta-testing with 'testing the app'",
            "transcript": "I'm testing the Mina application. Let me check if tasks appear from my side.",
            "expected": True
        },
        {
            "name": "Meta-testing with 'verify' language",
            "transcript": "Let me verify the transcription pipeline is working. Make sure this gets recorded.",
            "expected": True
        },
        {
            "name": "Real business meeting",
            "transcript": "We need to finalize the Q4 budget. Sarah will review the proposal by Friday.",
            "expected": False
        },
        {
            "name": "Testing a product feature (not meta)",
            "transcript": "We're testing the new feature in production. Deploy by next week.",
            "expected": False
        },
        {
            "name": "Meta commentary about recording",
            "transcript": "Okay, I'm just checking if this is being transcribed properly.",
            "expected": True
        },
        {
            "name": "Casual conversation",
            "transcript": "Hey, how are you doing? I'm just walking around the office.",
            "expected": False
        }
    ]
    
    passed_count = 0
    failed_count = 0
    
    for tc in test_cases:
        result = engine.detect_meta_testing(tc["transcript"])
        is_meta = result.is_valid if hasattr(result, 'is_valid') else result
        test_passed = is_meta == tc["expected"]
        
        if test_passed:
            passed_count += 1
            status = "✅ PASS"
        else:
            failed_count += 1
            status = "❌ FAIL"
        
        print(f"\n{status} {tc['name']}")
        print(f"  Detected: {is_meta}, Expected: {tc['expected']}")
        if hasattr(result, 'score'):
            print(f"  Confidence: {result.score:.2f}")
        print(f"  Transcript: '{tc['transcript'][:100]}...'")
    
    print(f"\n{'=' * 80}")
    print(f"Test Results: {passed_count} passed, {failed_count} failed")
    return failed_count == 0


def test_semantic_similarity():
    """Test semantic similarity checking."""
    print("\n" + "=" * 80)
    print("TEST 3: Semantic Similarity Detection")
    print("=" * 80)
    
    engine = ValidationEngine()
    
    test_cases = [
        {
            "name": "Exact match",
            "claim": "We discussed the budget proposal",
            "transcript": "We discussed the budget proposal in detail",
            "expected_similar": True
        },
        {
            "name": "Paraphrased match",
            "claim": "The team reviewed the financial plan",
            "transcript": "We discussed the budget proposal",
            "expected_similar": True
        },
        {
            "name": "Completely unrelated",
            "claim": "We went on a tour of the pantry and terrace",
            "transcript": "The Q4 planning meeting covered budget allocation",
            "expected_similar": False
        },
        {
            "name": "Hallucinated content",
            "claim": "Discussed quarterly revenue targets",
            "transcript": "I'm testing the application to see if it works",
            "expected_similar": False
        }
    ]
    
    passed_count = 0
    failed_count = 0
    
    for tc in test_cases:
        result = engine.check_semantic_similarity(tc["claim"], tc["transcript"])
        is_similar = result.is_valid if hasattr(result, 'is_valid') else result
        test_passed = is_similar == tc["expected_similar"]
        
        if test_passed:
            passed_count += 1
            status = "✅ PASS"
        else:
            failed_count += 1
            status = "❌ FAIL"
        
        print(f"\n{status} {tc['name']}")
        print(f"  Similar: {is_similar}, Expected: {tc['expected_similar']}")
        if hasattr(result, 'score'):
            print(f"  Similarity score: {result.score:.2f}")
        print(f"  Claim: '{tc['claim']}'")
        print(f"  Transcript excerpt: '{tc['transcript'][:80]}...'")
    
    print(f"\n{'=' * 80}")
    print(f"Test Results: {passed_count} passed, {failed_count} failed")
    return failed_count == 0


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🧪 VALIDATION ENGINE TEST SUITE")
    print("=" * 80)
    print("\nTesting ValidationEngine components:")
    print("  - Task quality scoring rubric")
    print("  - Meta-testing detection")
    print("  - Semantic similarity checking")
    
    # Run all tests
    all_passed = True
    all_passed &= test_task_quality_scoring()
    all_passed &= test_meta_testing_detection()
    all_passed &= test_semantic_similarity()
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80)
    
    sys.exit(0 if all_passed else 1)
