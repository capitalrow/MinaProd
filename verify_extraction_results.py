#!/usr/bin/env python3
"""
Verification script for CROWN+ Task Extraction Pipeline
Tests current extraction rate and quality on session 1761590047986
"""

import os
import sys
from sqlalchemy import create_engine, text

def verify_extraction():
    """Verify task extraction results for test session"""
    
    db_url = os.environ.get("DATABASE_URL")
    engine = create_engine(db_url)
    
    print("=" * 80)
    print("CROWN+ Task Extraction Pipeline - Verification Report")
    print("=" * 80)
    print()
    
    # Session info
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT external_id, started_at, total_duration 
            FROM sessions 
            WHERE external_id = '1761590047986'
        """))
        session = result.fetchone()
        
        if not session:
            print("❌ Test session not found!")
            return
        
        print(f"📊 Test Session: {session[0]}")
        print(f"   Started: {session[1]}")
        print(f"   Duration: {session[2]:.1f}s")
        print()
        
        # Get transcript
        result = conn.execute(text("""
            SELECT text FROM segments 
            WHERE session_id = (SELECT id FROM sessions WHERE external_id = '1761590047986')
            ORDER BY id
        """))
        transcript_rows = result.fetchall()
        full_transcript = " ".join([row[0] for row in transcript_rows])
        
        print("📝 Full Transcript:")
        print("-" * 80)
        print(full_transcript)
        print("-" * 80)
        print()
        
        # Expected tasks (manually identified from transcript)
        expected_tasks = [
            "Test the live transcription and ensure post-transcription functionality (META - should be filtered)",
            "Clean my bedroom",
            "Get £30 from the ATM",
            "Buy a train ticket for tomorrow's journey to work",
            "Book a desk on the desk booking app",
            "Buy Christmas gifts in late November",
            "Define handover tasks at current job before moving to new role at Monzo",
            "Define and start working on New Year's resolution plan"
        ]
        
        print(f"🎯 Expected Tasks: {len(expected_tasks)}")
        print("-" * 80)
        for i, task in enumerate(expected_tasks, 1):
            marker = "⚠️ " if "META" in task else "✓ "
            print(f"{marker}{i}. {task}")
        print()
        
        # Extracted tasks
        result = conn.execute(text("""
            SELECT id, title, priority, due_date, confidence_score
            FROM tasks 
            WHERE session_id = (SELECT id FROM sessions WHERE external_id = '1761590047986')
            ORDER BY id
        """))
        extracted_tasks = result.fetchall()
        
        print(f"🤖 Extracted Tasks: {len(extracted_tasks)}")
        print("-" * 80)
        for task in extracted_tasks:
            task_id, title, priority, due_date, confidence = task
            due_str = f"📅 {due_date}" if due_date else "📅 No due date"
            print(f"✅ {title}")
            print(f"   Priority: {priority} | {due_str} | Confidence: {confidence}")
            print()
        
        # Analysis
        print("=" * 80)
        print("📈 EXTRACTION ANALYSIS")
        print("=" * 80)
        
        legitimate_expected = len([t for t in expected_tasks if "META" not in t])
        extraction_rate = (len(extracted_tasks) / legitimate_expected) * 100
        
        print(f"✅ Tasks Extracted: {len(extracted_tasks)}")
        print(f"🎯 Expected (excluding meta): {legitimate_expected}")
        print(f"📊 Extraction Rate: {extraction_rate:.1f}%")
        print()
        
        # Missing tasks
        extracted_titles_lower = [t[1].lower() for t in extracted_tasks]
        missing_tasks = []
        
        if not any("clean" in title and "bedroom" in title for title in extracted_titles_lower):
            missing_tasks.append("Clean bedroom")
        if not any("£30" in title or "30 pounds" in title or "atm" in title.lower() for title in extracted_titles_lower):
            missing_tasks.append("Get £30 from ATM")
        if not any("desk" in title and "book" in title for title in extracted_titles_lower):
            missing_tasks.append("Book desk on app")
        
        if missing_tasks:
            print("❌ Missing Tasks:")
            for task in missing_tasks:
                print(f"   • {task}")
            print()
        
        # Quality issues
        meta_task_found = any("test" in title.lower() and "transcription" in title.lower() for title in extracted_titles_lower)
        
        if meta_task_found:
            print("⚠️  Quality Issues:")
            print("   • Meta-testing task not filtered by ValidationEngine")
            print("     (Should recognize 'Test the live transcription...' as meta-commentary)")
            print()
        
        # Next Steps
        print("=" * 80)
        print("🎯 NEXT STEPS TO REACH 100%")
        print("=" * 80)
        print()
        print("1. 🔍 Investigate why AI missed 3 tasks:")
        print("   • Review AI extraction logs to see raw GPT-4 response")
        print("   • Check if tasks were in raw response but filtered by ValidationEngine")
        print("   • Or if GPT-4 genuinely didn't extract them from transcript")
        print()
        print("2. 🧹 Improve ValidationEngine filtering:")
        print("   • Add pattern to detect meta-testing commentary")
        print("   • Filter out 'Test the live transcription...' type tasks")
        print()
        print("3. ✨ Enhance extraction completeness:")
        print("   • If tasks missing from raw AI response: strengthen prompts")
        print("   • If tasks filtered incorrectly: tune ValidationEngine thresholds")
        print()
        print("4. 🎨 Verify badge counts on UI:")
        print("   • Check that session detail page shows correct task count")
        print("   • Ensure action items badge displays '5' (or final count)")
        print()
        
        # Success criteria
        print("=" * 80)
        print("✅ SUCCESS CRITERIA FOR 100% COMPLETION")
        print("=" * 80)
        print()
        print("• Extract ALL 7 legitimate tasks (100% coverage)")
        print("• Filter out 1 meta-testing task (0 false positives)")
        print("• Professional formatting (proper grammar, punctuation, capitalization)")
        print("• Accurate metadata (priority, due dates, assignees)")
        print("• Semantic deduplication (no duplicate tasks)")
        print("• Correct UI badge counts (match database)")
        print()

if __name__ == "__main__":
    verify_extraction()
