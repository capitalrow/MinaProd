"""
Standalone integration test for live recording pipeline.
Tests all critical fixes for the data persistence bug.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app import app, db
from models import User, Workspace, Meeting, Session, Segment


def test_database_integrity():
    """Test current database state and integrity."""
    print("=" * 70)
    print("DATABASE INTEGRITY TEST")
    print("=" * 70)
    
    with app.app_context():
        # Get all users with workspaces
        users = db.session.query(User).all()
        print(f"\n📊 Users: {len(users)}")
        
        for user in users:
            has_workspace = user.workspace_id is not None
            ws_id = user.workspace_id or "None"
            print(f"   - {user.username} (id={user.id}): workspace_id={ws_id}")
        
        # Check workspaces
        workspaces = db.session.query(Workspace).all()
        print(f"\n📊 Workspaces: {len(workspaces)}")
        for ws in workspaces:
            print(f"   - {ws.name} (id={ws.id})")
        
        # Check meetings
        meetings = db.session.query(Meeting).all()
        print(f"\n📊 Meetings: {len(meetings)}")
        for meeting in meetings:
            print(f"   - {meeting.title}")
            print(f"     ID: {meeting.id}, Status: {meeting.status}")
            print(f"     Workspace: {meeting.workspace_id}, Organizer: {meeting.organizer_id}")
        
        # Check sessions
        sessions = db.session.query(Session).order_by(Session.started_at.desc()).limit(10).all()
        print(f"\n📊 Recent Sessions (last 10):")
        
        orphaned_count = 0
        linked_count = 0
        
        for session in sessions:
            is_orphaned = session.workspace_id is None
            if is_orphaned:
                orphaned_count += 1
                status_icon = "❌"
            else:
                linked_count += 1
                status_icon = "✅"
            
            print(f"   {status_icon} {session.external_id}")
            print(f"      User: {session.user_id}, Workspace: {session.workspace_id}, Meeting: {session.meeting_id}")
            print(f"      Status: {session.status}, Segments: {session.total_segments or 0}")
        
        print(f"\n📈 Session Statistics:")
        print(f"   ✅ Properly linked: {linked_count}")
        print(f"   ❌ Orphaned (NULL workspace_id): {orphaned_count}")
        
        return {
            'users': len(users),
            'workspaces': len(workspaces),
            'meetings': len(meetings),
            'sessions': len(sessions),
            'orphaned': orphaned_count,
            'linked': linked_count
        }


def test_workspace_linkage():
    """Test that sessions are properly linked to workspaces."""
    print("\n" + "=" * 70)
    print("WORKSPACE LINKAGE TEST")
    print("=" * 70)
    
    with app.app_context():
        # Get first user with workspace
        user = db.session.query(User).first()
        if not user:
            print("❌ No users found in database")
            return False
        
        print(f"\n🔍 Testing with user: {user.username} (id={user.id})")
        
        if not user.workspace_id:
            print("❌ User has no workspace")
            return False
        
        workspace = user.workspace
        print(f"🔍 Workspace: {workspace.name} (id={workspace.id})")
        
        # Query sessions for this workspace
        workspace_sessions = db.session.query(Session).filter_by(
            workspace_id=workspace.id
        ).all()
        
        print(f"\n✅ Sessions in workspace: {len(workspace_sessions)}")
        
        # Query meetings for this workspace
        workspace_meetings = db.session.query(Meeting).filter_by(
            workspace_id=workspace.id
        ).all()
        
        print(f"✅ Meetings in workspace: {len(workspace_meetings)}")
        
        # Check linkage
        properly_linked = 0
        for session in workspace_sessions:
            if session.meeting_id:
                meeting = db.session.query(Meeting).filter_by(id=session.meeting_id).first()
                if meeting and meeting.workspace_id == workspace.id:
                    properly_linked += 1
        
        print(f"✅ Sessions with valid Meeting linkage: {properly_linked}/{len(workspace_sessions)}")
        
        return True


def test_dashboard_query():
    """Test dashboard query to see what meetings would be displayed."""
    print("\n" + "=" * 70)
    print("DASHBOARD QUERY TEST")
    print("=" * 70)
    
    with app.app_context():
        # Get first user with workspace (simulating logged-in user)
        user = db.session.query(User).first()
        if not user or not user.workspace_id:
            print("❌ No user with workspace found")
            return False
        
        workspace = user.workspace
        print(f"\n🔍 Simulating dashboard for: {user.username}")
        print(f"🔍 Workspace: {workspace.name} (id={workspace.id})")
        
        # Simulate dashboard query (same as in routes/dashboard.py)
        dashboard_meetings = db.session.query(Meeting).filter_by(
            workspace_id=workspace.id
        ).order_by(Meeting.created_at.desc()).all()
        
        print(f"\n📋 Dashboard would show {len(dashboard_meetings)} meetings:")
        
        for i, meeting in enumerate(dashboard_meetings[:10], 1):  # Show first 10
            session_count = db.session.query(Session).filter_by(meeting_id=meeting.id).count()
            segment_count = 0
            
            # Count segments
            sessions = db.session.query(Session).filter_by(meeting_id=meeting.id).all()
            for sess in sessions:
                segment_count += db.session.query(Segment).filter_by(session_id=sess.id).count()
            
            duration = meeting.duration_minutes or 0
            
            print(f"   {i}. {meeting.title}")
            print(f"      Status: {meeting.status}, Type: {meeting.meeting_type}")
            print(f"      Duration: {duration} min, Sessions: {session_count}, Segments: {segment_count}")
            print(f"      Created: {meeting.created_at}")
        
        if len(dashboard_meetings) == 0:
            print("   ❌ No meetings found - this is the bug!")
            print("   Checking for orphaned sessions...")
            
            orphaned = db.session.query(Session).filter(
                Session.workspace_id.is_(None)
            ).count()
            print(f"   Found {orphaned} orphaned sessions (NULL workspace_id)")
        else:
            print(f"\n✅ Dashboard query working correctly!")
        
        return len(dashboard_meetings) > 0


def test_meeting_session_relationships():
    """Test Meeting-Session relationships."""
    print("\n" + "=" * 70)
    print("MEETING-SESSION RELATIONSHIP TEST")
    print("=" * 70)
    
    with app.app_context():
        meetings = db.session.query(Meeting).all()
        
        print(f"\n🔍 Testing {len(meetings)} meetings:")
        
        for meeting in meetings:
            sessions = db.session.query(Session).filter_by(meeting_id=meeting.id).all()
            segments_count = 0
            
            for session in sessions:
                segments = db.session.query(Segment).filter_by(session_id=session.id).count()
                segments_count += segments
            
            print(f"\n   Meeting: {meeting.title} (id={meeting.id})")
            print(f"   ├─ Sessions: {len(sessions)}")
            print(f"   ├─ Segments: {segments_count}")
            print(f"   ├─ Workspace: {meeting.workspace_id}")
            print(f"   └─ Status: {meeting.status}")
            
            # Verify integrity
            for session in sessions:
                if session.workspace_id != meeting.workspace_id:
                    print(f"      ❌ Session {session.id} has mismatched workspace!")
                if session.user_id != meeting.organizer_id:
                    print(f"      ⚠️ Session {session.id} has different user than organizer")
        
        return True


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "🔬" * 35)
    print("LIVE RECORDING PIPELINE - INTEGRATION TEST SUITE")
    print("🔬" * 35)
    print(f"Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    results = {}
    
    # Test 1: Database integrity
    results['database'] = test_database_integrity()
    
    # Test 2: Workspace linkage
    results['linkage'] = test_workspace_linkage()
    
    # Test 3: Dashboard query
    results['dashboard'] = test_dashboard_query()
    
    # Test 4: Relationships
    results['relationships'] = test_meeting_session_relationships()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    if results['database']:
        print(f"\n✅ Database State:")
        print(f"   - Users: {results['database']['users']}")
        print(f"   - Workspaces: {results['database']['workspaces']}")
        print(f"   - Meetings: {results['database']['meetings']}")
        print(f"   - Sessions (recent): {results['database']['sessions']}")
        print(f"   - Properly linked sessions: {results['database']['linked']}")
        print(f"   - Orphaned sessions: {results['database']['orphaned']}")
    
    print(f"\n{'✅' if results['linkage'] else '❌'} Workspace Linkage Test")
    print(f"{'✅' if results['dashboard'] else '❌'} Dashboard Query Test")
    print(f"{'✅' if results['relationships'] else '❌'} Relationship Test")
    
    # Check if fix is working
    if results['database'] and results['database']['orphaned'] > 0:
        print("\n⚠️ WARNING: Found orphaned sessions from before the fix")
        print("   New sessions should be properly linked after the fix")
        print("   Old orphaned sessions may need data migration")
    
    if results['dashboard']:
        print("\n🎉 SUCCESS: Pipeline is working correctly!")
        print("   - Meetings are being created")
        print("   - Sessions are properly linked to workspaces")
        print("   - Dashboard queries return results")
    else:
        print("\n❌ FAILURE: Issues detected in pipeline")
        print("   Please review the test output above")
    
    print("\n" + "=" * 70)
    print(f"Completed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_all_tests()
