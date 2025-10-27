"""
Test script to verify task extraction works with real user transcript
"""
import sys
import os
import asyncio
sys.path.insert(0, '/home/runner/workspace')

from sqlalchemy import create_engine, text
from services.analysis_service import AnalysisService
from models.summary import SummaryLevel, SummaryStyle

async def test_extraction():
    print("\n" + "="*80)
    print("🧪 TESTING TASK EXTRACTION WITH REAL USER TRANSCRIPT")
    print("="*80)
    
    # Get transcript from session 314 (user's most recent session)
    db_url = os.environ.get('DATABASE_URL')
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT text FROM segments 
            WHERE session_id = 314 AND is_final = true
            ORDER BY created_at
            LIMIT 10
        """)).fetchall()
        
        if not result:
            print("❌ No transcript found for session 314")
            return
        
        transcript = " ".join([row[0] for row in result])
        print(f"\n📝 Testing with transcript ({len(transcript)} chars):")
        print(f"   {transcript[:200]}...")
    
    # Test the analysis service
    print("\n🤖 Running AI analysis with UPDATED prompt...")
    service = AnalysisService()
    
    try:
        result = await service.generate_insights_async(
            session_id=314,
            level=SummaryLevel.BRIEF,
            style=SummaryStyle.ACTION_ORIENTED
        )
        
        print(f"\n✅ Analysis completed!")
        print(f"\n📊 Results:")
        print(f"   Summary ID: {result.get('summary_id')}")
        print(f"   Action count: {result.get('action_count', 0)}")
        print(f"   Decision count: {result.get('decision_count', 0)}")
        print(f"   Risk count: {result.get('risk_count', 0)}")
        
        if result.get('action_count', 0) > 0:
            print(f"\n✅ SUCCESS! AI extracted {result['action_count']} tasks from the transcript!")
            
            # Get the actual tasks
            with engine.connect() as conn:
                summary = conn.execute(text(f"""
                    SELECT actions FROM summaries WHERE id = {result['summary_id']}
                """)).fetchone()
                
                if summary and summary[0]:
                    import json
                    actions = json.loads(summary[0]) if isinstance(summary[0], str) else summary[0]
                    print(f"\n📋 Extracted Tasks:")
                    for idx, action in enumerate(actions, 1):
                        print(f"   {idx}. {action.get('text', 'N/A')}")
                        print(f"      Evidence: \"{action.get('evidence_quote', 'N/A')[:80]}...\"")
                        print(f"      Owner: {action.get('owner', 'Not specified')}")
                        print(f"      Due: {action.get('due', 'Not specified')}")
                        print()
        else:
            print(f"\n⚠️ WARNING: Still extracted 0 tasks!")
            print(f"   This means the AI prompt might need further adjustment.")
            
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_extraction())
