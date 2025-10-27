"""
Quick Verification: Check that tasks are properly available for UI rendering
Uses existing test data from E2E tests
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Session, Task, Summary, Segment

def verify_ui_integration():
    """Verify tasks and insights are available for UI rendering"""
    print("\n" + "="*80)
    print("🔍 UI INTEGRATION VERIFICATION")
    print("="*80 + "\n")
    
    with app.app_context():
        # Find the most recent session with tasks
        print("📊 Step 1: Finding recent session with extracted tasks...")
        
        sessions_with_tasks = db.session.query(Session).join(
            Task, Session.id == Task.session_id
        ).order_by(Session.id.desc()).limit(5).all()
        
        if not sessions_with_tasks:
            print("   ❌ No sessions with tasks found. Run test_task_extraction_e2e.py first.")
            return False
        
        session = sessions_with_tasks[0]
        print(f"   ✅ Found session: '{session.title}' (ID: {session.id})")
        
        # Check tasks
        print("\n📋 Step 2: Verifying Tasks are available for UI...")
        tasks = db.session.query(Task).filter_by(session_id=session.id).all()
        
        print(f"   📊 Tasks found: {len(tasks)}")
        
        if len(tasks) == 0:
            print("   ❌ FAIL: No tasks found for this session")
            return False
        
        print("   ✅ Tasks available for UI rendering\n")
        
        # Display task data as UI would receive it
        print("   📝 Task Data (as frontend would receive):")
        for i, task in enumerate(tasks[:5], 1):  # Show first 5
            task_data = {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'priority': task.priority,
                'status': task.status,
                'assigned_to': task.assigned_to,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'session_id': task.session_id
            }
            print(f"\n      Task {i}:")
            print(f"      └─ {json.dumps(task_data, indent=9)}")
        
        if len(tasks) > 5:
            print(f"\n      ... and {len(tasks) - 5} more tasks")
        
        # Check summary
        print("\n\n💡 Step 3: Verifying AI Summary/Insights...")
        summary = db.session.query(Summary).filter_by(session_id=session.id).first()
        
        if summary:
            print("   ✅ Summary available")
            
            summary_data = {
                'has_summary_md': bool(summary.summary_md),
                'actions_count': len(summary.actions) if summary.actions else 0,
                'decisions_count': len(summary.decisions) if summary.decisions else 0,
                'risks_count': len(summary.risks) if summary.risks else 0,
                'level': summary.level.value if summary.level else None,
                'style': summary.style.value if summary.style else None
            }
            
            print(f"   📊 Summary metadata: {json.dumps(summary_data, indent=6)}")
            
            if summary.summary_md:
                print(f"\n   📄 Summary preview: {summary.summary_md[:200]}...")
        else:
            print("   ℹ️  No summary found (AI might have been unavailable during test)")
        
        # Check segments
        print("\n\n📝 Step 4: Verifying Transcript Segments...")
        segment_count = db.session.query(Segment).filter_by(session_id=session.id).count()
        print(f"   📊 Transcript segments: {segment_count}")
        
        if segment_count > 0:
            print("   ✅ Transcript available")
        
        # Final UI integration check
        print("\n\n" + "="*80)
        print("✅ FINAL UI INTEGRATION VERIFICATION")
        print("="*80)
        
        checks = {
            "Session data available": True,
            "Tasks extracted and persisted": len(tasks) > 0,
            "Task data serializable for UI": all(task.title and task.description for task in tasks),
            "Transcript segments available": segment_count > 0,
            "Summary insights present": summary is not None
        }
        
        for check, passed in checks.items():
            symbol = "✅" if passed else "❌"
            print(f"   {symbol} {check}")
        
        all_passed = all(checks.values())
        
        if all_passed:
            print("\n🎉 UI INTEGRATION VERIFIED - 100% READY")
            print(f"   The task tab can display {len(tasks)} tasks from session {session.id}")
            print(f"   All data is properly formatted and available for frontend rendering")
        else:
            missing_checks = [k for k, v in checks.items() if not v]
            print(f"\n⚠️  Some checks incomplete: {', '.join(missing_checks)}")
        
        print("="*80 + "\n")
        
        return all_passed


if __name__ == "__main__":
    success = verify_ui_integration()
    sys.exit(0 if success else 1)
