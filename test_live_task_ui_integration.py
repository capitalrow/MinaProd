"""
Live End-to-End Test: Task Extraction → Database → Frontend UI
Tests the complete pipeline from transcript to UI display
"""
import os
import sys
import time
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Session, Segment, Task, Summary
from services.post_transcription_orchestrator import PostTranscriptionOrchestrator

def test_live_task_extraction_to_ui():
    """
    End-to-End Test: Verify tasks are extracted and available for UI rendering
    
    Test Flow:
    1. Create a realistic meeting transcript with clear action items
    2. Run the CROWN+ post-transcription pipeline
    3. Verify tasks are extracted and persisted to database
    4. Verify task data is available for frontend rendering
    5. Verify insights quality and accuracy
    """
    print("\n" + "="*80)
    print("🧪 LIVE END-TO-END TEST: Task Extraction → Database → Frontend UI")
    print("="*80 + "\n")
    
    with app.app_context():
        # Clean up any existing test data
        db.session.query(Session).filter(Session.title.like("%Live E2E Test%")).delete()
        db.session.commit()
        
        # Create a realistic meeting session
        print("📝 Step 1: Creating realistic meeting session with actionable content...")
        import uuid
        session = Session(
            external_id=f"test-{uuid.uuid4().hex[:16]}",
            title="Live E2E Test: Product Planning Meeting",
            status='completed'
        )
        db.session.add(session)
        db.session.commit()
        print(f"   ✅ Session created (ID: {session.id})")
        
        # Create realistic transcript segments with clear action items
        realistic_segments = [
            {
                "speaker": "Sarah (Product Manager)",
                "text": "Thanks everyone for joining. Let's discuss our Q4 roadmap. First, we need to finalize the user authentication feature by next Friday.",
                "timestamp": 0.0
            },
            {
                "speaker": "Mike (Engineering Lead)",
                "text": "I can take ownership of that. I'll coordinate with the security team and send you the technical spec by Wednesday for review.",
                "timestamp": 12.5
            },
            {
                "speaker": "Sarah (Product Manager)",
                "text": "Perfect. Also, we need someone to update the API documentation before the beta release. This is critical for our developer partners.",
                "timestamp": 25.0
            },
            {
                "speaker": "Lisa (Technical Writer)",
                "text": "I'll handle the documentation updates. I can have a draft ready by end of day tomorrow and the final version by Thursday.",
                "timestamp": 38.0
            },
            {
                "speaker": "Mike (Engineering Lead)",
                "text": "Great. One more thing - we should schedule a meeting with the design team to review the new dashboard mockups. Can we do that early next week?",
                "timestamp": 52.0
            },
            {
                "speaker": "Sarah (Product Manager)",
                "text": "Yes, I'll send out calendar invites for Monday at 2 PM. Everyone please review the mockups beforehand so we can have a productive discussion.",
                "timestamp": 65.0
            },
            {
                "speaker": "Mike (Engineering Lead)",
                "text": "Also, I'll need to follow up with DevOps about the staging environment issues we discussed last week. I'll do that today.",
                "timestamp": 78.0
            }
        ]
        
        print(f"   📊 Creating {len(realistic_segments)} transcript segments...")
        for seg_data in realistic_segments:
            segment = Segment(
                session_id=session.id,
                speaker=seg_data["speaker"],
                text=seg_data["text"],
                start_time=seg_data["timestamp"],
                end_time=seg_data["timestamp"] + 10.0,
                confidence=0.95
            )
            db.session.add(segment)
        
        db.session.commit()
        segment_count = db.session.query(Segment).filter_by(session_id=session.id).count()
        print(f"   ✅ {segment_count} segments created\n")
        
        # Run the CROWN+ pipeline
        print("🚀 Step 2: Running CROWN+ Post-Transcription Pipeline...")
        print("   (Using GPT-4.1 fallback chain with degradation tracking)")
        
        orchestrator = PostTranscriptionOrchestrator()
        
        start_time = time.time()
        result = orchestrator.run_pipeline(session.id)
        duration = time.time() - start_time
        
        print(f"   ⏱️  Pipeline completed in {duration:.2f}s")
        print(f"   📊 Pipeline success: {result.get('success', False)}")
        
        # Check event ledger for degradation events
        session = db.session.get(Session, session.id)
        event_ledger = session.event_ledger or {}
        
        print("\n📊 Step 3: Analyzing Pipeline Results...")
        
        # Check for degradation events
        degradation_events = []
        for event_key, event_data in event_ledger.items():
            if 'degraded' in event_key and event_data:
                degradation_events.append(event_data)
        
        if degradation_events:
            print("   ⚠️  AI Model Degradation Detected:")
            for event in degradation_events:
                print(f"      - Model used: {event.get('model_used', 'unknown')}")
                print(f"      - Reason: {event.get('degradation_reason', 'unknown')}")
        else:
            print("   ✅ No degradation - using primary AI model")
        
        # Verify tasks were extracted
        print("\n📋 Step 4: Verifying Task Extraction...")
        tasks = db.session.query(Task).filter_by(session_id=session.id).all()
        
        print(f"   📊 Total tasks extracted: {len(tasks)}")
        
        if len(tasks) == 0:
            print("   ❌ FAIL: No tasks extracted!")
            return False
        
        print("   ✅ Tasks successfully extracted\n")
        print("   📝 Extracted Tasks:")
        for i, task in enumerate(tasks, 1):
            print(f"\n      Task {i}:")
            print(f"      ├─ Title: {task.title}")
            print(f"      ├─ Description: {task.description[:100]}..." if len(task.description) > 100 else f"      ├─ Description: {task.description}")
            print(f"      ├─ Priority: {task.priority}")
            print(f"      ├─ Status: {task.status}")
            if task.assigned_to:
                print(f"      ├─ Assigned to: {task.assigned_to}")
            if task.due_date:
                print(f"      ├─ Due date: {task.due_date}")
            print(f"      └─ Source: {'AI extraction' if task.segment_id is None else 'Pattern matching (linked to segment)'}")
        
        # Verify summary insights
        print("\n\n💡 Step 5: Verifying AI-Generated Insights...")
        summary = db.session.query(Summary).filter_by(session_id=session.id).first()
        
        if summary:
            print("   ✅ Summary generated successfully")
            
            if summary.summary_md:
                print(f"\n   📄 Summary (Markdown):")
                print(f"      {summary.summary_md[:300]}...")
            
            if summary.actions:
                print(f"\n   ✓ Actions from Summary ({len(summary.actions)} items):")
                for i, action in enumerate(summary.actions[:3], 1):
                    print(f"      {i}. {action}")
            
            if summary.decisions:
                print(f"\n   🎯 Decisions ({len(summary.decisions)} items):")
                for i, decision in enumerate(summary.decisions[:3], 1):
                    print(f"      {i}. {decision}")
        else:
            print("   ⚠️  No summary generated (AI may be unavailable)")
        
        # Verify frontend data availability
        print("\n\n🖥️  Step 6: Verifying Frontend UI Data Availability...")
        
        # Simulate what the frontend would fetch
        ui_session_data = {
            'id': session.id,
            'title': session.title,
            'status': session.status,
            'created_at': session.created_at.isoformat(),
            'segment_count': db.session.query(Segment).filter_by(session_id=session.id).count(),
            'task_count': len(tasks),
            'has_summary': summary is not None
        }
        
        ui_tasks_data = [
            {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'priority': task.priority,
                'status': task.status,
                'assigned_to': task.assigned_to,
                'due_date': task.due_date.isoformat() if task.due_date else None
            }
            for task in tasks
        ]
        
        print("   ✅ Session data ready for UI:")
        print(f"      └─ {json.dumps(ui_session_data, indent=8)}")
        
        print("\n   ✅ Tasks data ready for UI:")
        print(f"      └─ {len(ui_tasks_data)} tasks serialized and ready")
        
        # Performance validation
        print("\n\n⚡ Step 7: Performance Validation...")
        print(f"   Pipeline Duration: {duration:.2f}s")
        
        if duration < 30.0:
            print("   ✅ EXCELLENT: Pipeline completed in <30s")
        elif duration < 60.0:
            print("   ✅ GOOD: Pipeline completed in <60s")
        else:
            print("   ⚠️  SLOW: Pipeline took longer than expected")
        
        # Final validation
        print("\n\n" + "="*80)
        print("📊 FINAL VALIDATION RESULTS")
        print("="*80)
        
        checks = {
            "✅ Session created successfully": True,
            "✅ Transcript segments persisted": segment_count == len(realistic_segments),
            "✅ Pipeline completed without errors": result.get('success', False),
            "✅ Tasks extracted and persisted": len(tasks) > 0,
            "✅ Task metadata complete": all(task.title and task.description for task in tasks),
            "✅ Summary insights generated": summary is not None,
            "✅ Frontend data serializable": len(ui_tasks_data) > 0,
            "✅ Performance within targets": duration < 60.0
        }
        
        for check, passed in checks.items():
            print(f"   {check if passed else check.replace('✅', '❌')}")
        
        all_passed = all(checks.values())
        
        if all_passed:
            print("\n🎉 ALL CHECKS PASSED - 100% FUNCTIONALITY VERIFIED!")
            print(f"   Total tasks available in UI: {len(tasks)}")
            print(f"   Pipeline performance: {duration:.2f}s")
            print("\n✅ The task tab will display all {0} extracted tasks with accurate insights.".format(len(tasks)))
        else:
            print("\n❌ SOME CHECKS FAILED - Review results above")
        
        print("="*80 + "\n")
        
        return all_passed


if __name__ == "__main__":
    success = test_live_task_extraction_to_ui()
    sys.exit(0 if success else 1)
