"""
Simple test to verify the updated AI prompt extracts tasks
"""
import os
import json
from openai import OpenAI

# Real user transcript from session 314
TRANSCRIPT = """Thank you very much for that, and it's nice to hear some new voices represented in this forum, so thanks for that. Emre, what's a new voice? I'm not going to repeat a couple of things that have been said, especially around cost, operational metrics. One thing that we thought about is around what does being outcome-oriented mean concretely, and how can we capture that? And I wonder if some sort of dash around how many requests do we have in time to completion, how many requests have been complete"""

# Updated prompt (same as in analysis_service.py)
SYSTEM_PROMPT = """You are an insightful meeting analyst. Extract actionable insights from this transcript including commitments, proposals, questions that need answers, and ideas that require follow-up.

WHAT TO EXTRACT (be inclusive of valuable work insights):
1. ✓ Explicit commitments: "I will...", "I need to...", "Action item:..."
2. ✓ Proposals and ideas: "We could...", "What about...", "I wonder if...", "Consider..."
3. ✓ Questions needing answers: "How do we...", "What's the plan for...", "Should we..."
4. ✓ Suggestions for improvement: "We should improve...", "Let's optimize...", "Think about..."
5. ✓ Discussion points implying action: "Look into...", "Explore...", "Investigate..."

WHAT NOT TO EXTRACT (filter these out):
✗ Meta-commentary about testing: "I'm testing the application", "Recording this for demo"
✗ Casual personal tasks: "I will go check my car", "I'll grab coffee"
✗ Current activities: "I'm writing code now", "Currently working on..."
✗ Pure narration: "Testing the pipeline", "Sharing my screen"

Return ONLY valid JSON:
{
    "brief_summary": "2-3 sentence summary of what was discussed",
    "action_plan": [
        {
            "action": "Clear, actionable task title", 
            "evidence_quote": "Quote from transcript showing this was mentioned",
            "owner": "Person mentioned or 'Not specified'", 
            "priority": "high/medium/low",
            "due": "Date mentioned or 'Not specified'"
        }
    ]
}"""

print("\n" + "="*80)
print("🧪 TESTING UPDATED AI PROMPT WITH REAL USER TRANSCRIPT")
print("="*80)

print(f"\n📝 User's Transcript:")
print(f"   {TRANSCRIPT}")

print(f"\n🤖 Calling OpenAI with UPDATED prompt...")
print(f"   (Now extracts proposals, questions, and ideas!)")

try:
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Meeting transcript:\n{TRANSCRIPT}"}
        ],
        temperature=0.3
    )
    
    content = response.choices[0].message.content
    result = json.loads(content)
    
    print(f"\n✅ AI Response received!")
    print(f"\n📊 Summary:")
    print(f"   {result.get('brief_summary', 'N/A')}")
    
    actions = result.get('action_plan', [])
    print(f"\n📋 Extracted {len(actions)} Tasks:")
    
    if len(actions) > 0:
        print(f"\n✅ SUCCESS! The updated prompt now extracts valuable insights!\n")
        for idx, action in enumerate(actions, 1):
            print(f"   {idx}. {action.get('action', 'N/A')}")
            print(f"      Evidence: \"{action.get('evidence_quote', 'N/A')}\"")
            print(f"      Priority: {action.get('priority', 'medium')}")
            print()
    else:
        print(f"\n⚠️ Still extracted 0 tasks - prompt needs more adjustment")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
