#!/usr/bin/env python3
"""
Direct test of AI action item extraction with the new permissive prompt.
This bypasses all background tasks and tests the AI service directly.
"""

import os
import sys

# Test transcript from session 1761590047986
TEST_TRANSCRIPT = """Right, here, I am testing the live transcription. And the idea is we're going to check to make sure that the post-transcription is working as expected. So from here, let me take that as an action. Another action that I need to do is I need to go back upstairs to my living room, or my bedroom, sorry, and clean it up. Let's do this right away today. I need to then go downstairs and get 30 pounds out as cash from the ATM machine after I've filled out the bedroom. I also need to then go back home and buy a train ticket for tomorrow to work. I also need to book a desk on the desk booking app for the office. I'm also planning to prepare to buy Christmas gifts around late November time. I also need to define my handover tasks at work before I leave and move on to my new role at Monzo. I also need to write a New Year's resolution plan for the new year coming."""

def test_ai_extraction():
    print("="*80)
    print("🧪 DIRECT TEST: AI Action Item Extraction")
    print("="*80)
    print()
    
    # Check OpenAI API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not set in environment")
        return False
    
    print(f"✅ OpenAI API key found: {api_key[:15]}...")
    print()
    
    # Import AI insights service
    try:
        from services.ai_insights_service import AIInsightsService
        print("✅ AIInsightsService imported successfully")
    except Exception as e:
        print(f"❌ Failed to import AIInsightsService: {e}")
        return False
    
    # Create service instance
    try:
        service = AIInsightsService()
        print("✅ AIInsightsService initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize AIInsightsService: {e}")
        return False
    
    # Test extraction
    print("📝 Test Transcript:")
    print("-" * 80)
    print(TEST_TRANSCRIPT[:200] + "...")
    print("-" * 80)
    print()
    
    print("🎯 Calling extract_action_items()...")
    print()
    
    try:
        action_items = service.extract_action_items(TEST_TRANSCRIPT)
        
        print(f"✅ Extraction completed!")
        print(f"📊 Result: {len(action_items)} tasks extracted")
        print()
        
        if len(action_items) == 0:
            print("❌ ZERO TASKS EXTRACTED - This is the bug!")
            print()
            print("Expected tasks:")
            print("  1. Clean up bedroom")
            print("  2. Get £30 cash from ATM")
            print("  3. Buy train ticket for tomorrow")
            print("  4. Book desk on desk booking app")
            print("  5. Prepare to buy Christmas gifts (late November)")
            print("  6. Define handover tasks at work")
            print("  7. Write New Year's resolution plan")
            print()
            return False
        
        print("✅ Tasks extracted successfully!")
        print()
        print("📋 Extracted Tasks:")
        print("=" * 80)
        
        for i, item in enumerate(action_items, 1):
            task = item.get('task', 'NO_TASK')
            assignee = item.get('assignee', 'null')
            due_date = item.get('due_date', 'null')
            priority = item.get('priority', 'null')
            
            print(f"{i}. {task}")
            print(f"   Assignee: {assignee}, Due: {due_date}, Priority: {priority}")
            print()
        
        print("=" * 80)
        print(f"✅ SUCCESS: {len(action_items)} tasks extracted")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"❌ Extraction failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ai_extraction()
    sys.exit(0 if success else 1)
