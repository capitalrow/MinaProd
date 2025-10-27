#!/usr/bin/env python3
"""
Comprehensive test for the validation pipeline improvements.
Tests anti-hallucination prompts, quality scoring, and task extraction.
"""
import os
import sys

# Set up environment
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://localhost/mina_dev')
os.environ['SESSION_SECRET'] = os.environ.get('SESSION_SECRET', 'test_secret_key_12345')

from services.validation_engine import get_validation_engine
from services.analysis_service import AnalysisService
import json


def test_task_quality_scoring():
    """Test the task quality rubric."""
    print("\n" + "=" * 80)
    print("TEST 1: Task Quality Scoring Rubric")
    print("=" * 80)
    
    engine = get_validation_engine()
    transcript = "We need to update the budget proposal by Friday. Sarah will review it."
    
    test_cases = [
        {
            "name": "High-quality task",
            "task": "Update the budget proposal by Friday",
            "evidence": "We need to update the budget proposal by Friday",
            "expected": ">0.65"
        },
        {
            "name": "Fragment without verb",
            "task": "from my side",
            "evidence": "Let me check from my side",
            "expected": "<0.65"
        },
        {
            "name": "Meta-testing commentary",
            "task": "check if tasks appear",
            "evidence": "I'm testing to check if tasks appear",
            "expected": "<0.65"
        },
        {
            "name": "Very short fragment",
            "task": "check it",
            "evidence": "I'll check it",
            "expected": "<0.65"
        },
        {
            "name": "Good task with subject and verb",
            "task": "Sarah will review the marketing strategy",
            "evidence": "Sarah will review the marketing strategy",
            "expected": ">0.65"
        }
    ]
    
    for tc in test_cases:
        score = engine.score_task_quality(tc["task"], tc["evidence"], transcript)
        passed = (score.total_score >= 0.65 and tc["expected"] == ">0.65") or \
                 (score.total_score < 0.65 and tc["expected"] == "<0.65")
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status} {tc['name']}")
        print(f"  Task: '{tc['task']}'")
        print(f"  Score: {score.total_score:.2f} (expected {tc['expected']})")
        print(f"  Breakdown: verb={score.has_action_verb}, subject={score.has_subject}, "
              f"length={score.appropriate_length}, evidence={score.has_evidence}")


def test_meta_testing_detection():
    """Test meta-testing detection."""
    print("\n" + "=" * 80)
    print("TEST 2: Meta-Testing Detection")
    print("=" * 80)
    
    engine = get_validation_engine()
    
    test_cases = [
        {
            "name": "Clear meta-testing",
            "transcript": "I'm testing the Mina application. Let me check if tasks appear from my side.",
            "expected": True
        },
        {
            "name": "Real business meeting",
            "transcript": "We need to finalize the Q4 budget. Sarah will review the proposal by Friday.",
            "expected": False
        },
        {
            "name": "Testing language in real context",
            "transcript": "We're testing the new feature in production. Deploy by next week.",
            "expected": False  # 'testing a feature' is different from 'testing the app'
        },
        {
            "name": "Meta commentary about transcription",
            "transcript": "Okay, I'm just checking if the transcription is working properly. Make sure this gets recorded.",
            "expected": True
        }
    ]
    
    for tc in test_cases:
        is_meta = engine.detect_meta_testing(tc["transcript"])
        passed = is_meta == tc["expected"]
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status} {tc['name']}")
        print(f"  Detected: {is_meta}, Expected: {tc['expected']}")
        print(f"  Transcript: '{tc['transcript'][:80]}...'")


def test_ai_prompt_quality():
    """Test AI prompts with real meeting content."""
    print("\n" + "=" * 80)
    print("TEST 3: AI Prompt Quality with Real Meeting")
    print("=" * 80)
    
    # Real business meeting transcript
    real_meeting = """
    Sarah: Good morning everyone. Let's review the Q4 roadmap.
    
    John: We need to finalize the budget proposal by Friday. I'll coordinate with finance team.
    
    Sarah: Good. Also, can you review the marketing strategy document I sent yesterday?
    
    John: Yes, I'll review it by end of week and provide feedback.
    
    Sarah: Great. We should also schedule a follow-up meeting for next week to discuss the feedback.
    
    John: Agreed. I'll send out calendar invites tomorrow.
    """
    
    print("\n📄 Test Transcript (Real Business Meeting):")
    print(real_meeting[:200] + "...")
    
    try:
        print("\n🤖 Calling AI with improved prompts (temperature=0.2, chain-of-thought)...")
        result = AnalysisService.generate_insights(
            transcript=real_meeting,
            session_id=None,  # Mock session
            level="standard",
            focus="executive"
        )
        
        print("\n📊 AI Response:")
        print(f"  Summary length: {len(result.get('summary_md', ''))} chars")
        print(f"  Actions extracted: {len(result.get('actions', []))}")
        print(f"  Decisions extracted: {len(result.get('decisions', []))}")
        
        # Verify summary doesn't hallucinate
        summary = result.get('summary_md', '').lower()
        print(f"\n📝 Summary preview: {result.get('summary_md', '')[:200]}...")
        
        # Check for hallucinations
        hallucination_indicators = ['q4 roadmap', 'budget', 'marketing', 'follow-up']
        summary_has_real_content = any(indicator in summary for indicator in hallucination_indicators)
        
        if summary_has_real_content:
            print("  ✅ Summary appears to match transcript content")
        else:
            print("  ❌ WARNING: Summary may not match transcript")
        
        # Check task quality
        print("\n📋 Extracted Actions:")
        for idx, action in enumerate(result.get('actions', []), 1):
            print(f"\n  Action {idx}:")
            print(f"    Text: {action.get('text', 'N/A')}")
            print(f"    Evidence: {action.get('evidence_quote', 'N/A')[:80]}...")
            print(f"    Owner: {action.get('owner', 'N/A')}")
        
        # Expected: Should extract tasks like:
        # - "Finalize budget proposal by Friday"  
        # - "Review marketing strategy document"
        # - "Send calendar invites for follow-up meeting"
        
        if len(result.get('actions', [])) >= 2:
            print("\n  ✅ Extracted reasonable number of actions (≥2)")
        else:
            print(f"\n  ❌ WARNING: Only extracted {len(result.get('actions', []))} actions (expected ≥2)")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


def test_meta_testing_prompt():
    """Test AI prompts with meta-testing content."""
    print("\n" + "=" * 80)
    print("TEST 4: AI Prompt with Meta-Testing Transcript")
    print("=" * 80)
    
    # Meta-testing transcript (should NOT extract fake tasks)
    meta_testing = """
    I'm testing the Mina transcription application. Let me check if the tasks appear in the Tasks tab from my side.
    Okay, I'm going to say some action-like phrases to test the extraction: 
    I need to verify the system works. Make sure the transcription is accurate. Check the UI displays correctly.
    This is just a test recording to validate the post-transcription pipeline.
    """
    
    print("\n📄 Test Transcript (Meta-Testing):")
    print(meta_testing[:200] + "...")
    
    try:
        print("\n🤖 Calling AI with improved prompts...")
        result = AnalysisService.generate_insights(
            transcript=meta_testing,
            session_id=None,
            level="standard",
            focus="executive"
        )
        
        print("\n📊 AI Response:")
        print(f"  Summary length: {len(result.get('summary_md', ''))} chars")
        print(f"  Actions extracted: {len(result.get('actions', []))}")
        
        # Summary should acknowledge this is meta-testing
        summary = result.get('summary_md', '').lower()
        print(f"\n📝 Summary preview: {result.get('summary_md', '')[:250]}...")
        
        is_meta_acknowledged = any(word in summary for word in ['test', 'testing', 'validation', 'verify'])
        
        if is_meta_acknowledged:
            print("  ✅ Summary acknowledges meta-testing nature")
        else:
            print("  ❌ WARNING: Summary doesn't acknowledge this is a test")
        
        # Should extract 0 or very few actions
        if len(result.get('actions', [])) == 0:
            print("  ✅ Correctly extracted 0 actions from meta-testing")
        else:
            print(f"  ⚠️  Extracted {len(result.get('actions', []))} actions (should be 0):")
            for idx, action in enumerate(result.get('actions', []), 1):
                print(f"    {idx}. {action.get('text', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🧪 VALIDATION PIPELINE COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print("\nTesting the improved anti-hallucination and quality validation system:")
    print("  - Quality scoring rubric")
    print("  - Meta-testing detection")
    print("  - AI prompt improvements (chain-of-thought, few-shot, anti-hallucination)")
    print("  - Task extraction quality")
    
    # Run all tests
    test_task_quality_scoring()
    test_meta_testing_detection()
    test_ai_prompt_quality()
    test_meta_testing_prompt()
    
    print("\n" + "=" * 80)
    print("✅ Test suite completed!")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Review test results above")
    print("  2. Test with live recording in the UI")
    print("  3. Verify badge count matches actual tasks")
    print("  4. Check validation logs in server output")
