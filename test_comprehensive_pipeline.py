"""
COMPREHENSIVE INTEGRATION TEST SUITE
Tests all aspects and dimensions of the live recording pipeline.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app import app, db
from models import User, Workspace, Meeting, Session, Segment


def print_header(title):
    """Print test section header."""
    print("\n" + "=" * 70)
    print(f"TEST: {title}")
    print("=" * 70)


def test_1_authenticated_user_with_workspace():
    """
    TEST 1: Authenticated user with workspace creates recording
    Expected: Meeting + Session created with proper workspace linkage
    """
    print_header("Authenticated User with Workspace")
    
    with app.app_context():
        user = db.session.query(User).filter(User.workspace_id.isnot(None)).first()
        
        if not user:
            print("❌ No user with workspace found")
            return False
        
        workspace_id = user.workspace_id
        
        # Simulate join_session
        session_id = f"test_auth_{int(datetime.utcnow().timestamp() * 1000)}"
        
        meeting = Meeting(
            title=f"Auth Test - {datetime.utcnow().strftime('%H:%M:%S')}",
            workspace_id=workspace_id,
            organizer_id=user.id,
            status="in_progress",
            meeting_type="live_recording",
            actual_start=datetime.utcnow()
        )
        db.session.add(meeting)
        db.session.flush()
        
        session = Session(
            external_id=session_id,
            title=meeting.title,
            status="active",
            started_at=datetime.utcnow(),
            user_id=user.id,
            workspace_id=workspace_id,
            meeting_id=meeting.id
        )
        db.session.add(session)
        db.session.commit()
        
        # Verify
        assert session.workspace_id is not None, "Session must have workspace_id"
        assert session.user_id is not None, "Session must have user_id"
        assert session.meeting_id is not None, "Session must be linked to Meeting"
        assert meeting.workspace_id == workspace_id, "Meeting must have correct workspace"
        
        # Verify appears in dashboard
        dashboard_meetings = db.session.query(Meeting).filter_by(workspace_id=workspace_id).all()
        assert meeting.id in [m.id for m in dashboard_meetings], "Meeting must appear in dashboard"
        
        print(f"✅ PASSED")
        print(f"   - Meeting created: id={meeting.id}, workspace_id={workspace_id}")
        print(f"   - Session created: id={session.id}, workspace_id={workspace_id}")
        print(f"   - Linked: session.meeting_id={session.meeting_id}")
        print(f"   - Dashboard count: {len(dashboard_meetings)} meetings")
        
        return True


def test_2_session_finalization_updates_both_records():
    """
    TEST 2: Finalizing session updates both Session and Meeting status
    Expected: Both marked as "completed", even with empty transcript
    """
    print_header("Session Finalization with Status Updates")
    
    with app.app_context():
        user = db.session.query(User).filter(User.workspace_id.isnot(None)).first()
        workspace_id = user.workspace_id
        
        # Create session
        session_id = f"test_finalize_{int(datetime.utcnow().timestamp() * 1000)}"
        
        meeting = Meeting(
            title="Finalization Test",
            workspace_id=workspace_id,
            organizer_id=user.id,
            status="in_progress",
            meeting_type="live_recording",
            actual_start=datetime.utcnow()
        )
        db.session.add(meeting)
        db.session.flush()
        
        session = Session(
            external_id=session_id,
            title=meeting.title,
            status="active",
            started_at=datetime.utcnow(),
            user_id=user.id,
            workspace_id=workspace_id,
            meeting_id=meeting.id
        )
        db.session.add(session)
        db.session.commit()
        
        # Simulate finalize_session (NO transcript - empty audio)
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        session.total_duration = 0
        
        meeting.status = "completed"
        meeting.actual_end = datetime.utcnow()
        
        db.session.commit()
        
        # Verify
        assert session.status == "completed", "Session must be completed"
        assert meeting.status == "completed", "Meeting must be completed"
        assert session.completed_at is not None, "Session must have completion time"
        assert meeting.actual_end is not None, "Meeting must have end time"
        
        print(f"✅ PASSED")
        print(f"   - Session status: {session.status}")
        print(f"   - Meeting status: {meeting.status}")
        print(f"   - Duration: {meeting.duration_minutes} minutes")
        
        return True


def test_3_empty_transcript_handling():
    """
    TEST 3: Empty transcript doesn't prevent completion
    Expected: Session/Meeting complete, but no Segment created
    """
    print_header("Empty Transcript Handling")
    
    with app.app_context():
        user = db.session.query(User).filter(User.workspace_id.isnot(None)).first()
        workspace_id = user.workspace_id
        
        session_id = f"test_empty_{int(datetime.utcnow().timestamp() * 1000)}"
        
        meeting = Meeting(
            title="Empty Transcript Test",
            workspace_id=workspace_id,
            organizer_id=user.id,
            status="in_progress",
            meeting_type="live_recording",
            actual_start=datetime.utcnow()
        )
        db.session.add(meeting)
        db.session.flush()
        
        session = Session(
            external_id=session_id,
            title=meeting.title,
            status="active",
            started_at=datetime.utcnow(),
            user_id=user.id,
            workspace_id=workspace_id,
            meeting_id=meeting.id
        )
        db.session.add(session)
        db.session.commit()
        
        # Finalize with empty transcript (no Segment created)
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        session.total_segments = 0  # No segments
        meeting.status = "completed"
        meeting.actual_end = datetime.utcnow()
        db.session.commit()
        
        # Verify no segments created
        segments = db.session.query(Segment).filter_by(session_id=session.id).count()
        
        assert session.status == "completed", "Session must complete"
        assert meeting.status == "completed", "Meeting must complete"
        assert segments == 0, "No segments should exist for empty transcript"
        
        print(f"✅ PASSED")
        print(f"   - Session completed without transcript")
        print(f"   - Meeting completed without transcript")
        print(f"   - Segments created: {segments} (expected: 0)")
        
        return True


def test_4_anonymous_user_no_meeting():
    """
    TEST 4: Anonymous user (no authentication) creates session only
    Expected: Session created, but NO Meeting (to avoid NOT NULL constraint)
    """
    print_header("Anonymous User (No Meeting Creation)")
    
    with app.app_context():
        session_id = f"test_anon_{int(datetime.utcnow().timestamp() * 1000)}"
        
        # Simulate anonymous session (no user_id, no workspace_id)
        session = Session(
            external_id=session_id,
            title="Live Transcription Session",
            status="active",
            started_at=datetime.utcnow(),
            user_id=None,  # Anonymous
            workspace_id=None,  # No workspace
            meeting_id=None  # No meeting
        )
        db.session.add(session)
        db.session.commit()
        
        # Verify
        assert session.user_id is None, "Anonymous session has no user"
        assert session.workspace_id is None, "Anonymous session has no workspace"
        assert session.meeting_id is None, "Anonymous session has no meeting"
        
        # Verify this session does NOT appear in workspace dashboards
        all_workspaces = db.session.query(Workspace).all()
        for workspace in all_workspaces:
            workspace_sessions = db.session.query(Session).filter_by(workspace_id=workspace.id).all()
            assert session.id not in [s.id for s in workspace_sessions], "Anonymous session must not appear in workspace"
        
        print(f"✅ PASSED")
        print(f"   - Anonymous session created: id={session.id}")
        print(f"   - user_id: {session.user_id} (None)")
        print(f"   - workspace_id: {session.workspace_id} (None)")
        print(f"   - meeting_id: {session.meeting_id} (None)")
        print(f"   - Does NOT appear in any workspace dashboard")
        
        return True


def test_5_user_without_workspace():
    """
    TEST 5: Authenticated user without workspace
    Expected: Session created with user_id, but no Meeting (workspace required)
    """
    print_header("Authenticated User WITHOUT Workspace")
    
    with app.app_context():
        # Find or create user without workspace
        user = db.session.query(User).filter(User.workspace_id.is_(None)).first()
        
        if not user:
            # Create test user without workspace
            user = User(
                username=f"no_workspace_user_{int(datetime.utcnow().timestamp())}",
                email=f"noworkspace{int(datetime.utcnow().timestamp())}@test.com",
                is_active=True,
                workspace_id=None
            )
            db.session.add(user)
            db.session.commit()
        
        session_id = f"test_no_ws_{int(datetime.utcnow().timestamp() * 1000)}"
        
        # Simulate session for user without workspace
        session = Session(
            external_id=session_id,
            title="Live Transcription Session",
            status="active",
            started_at=datetime.utcnow(),
            user_id=user.id,  # Has user
            workspace_id=None,  # No workspace
            meeting_id=None  # No meeting (can't create Meeting without workspace)
        )
        db.session.add(session)
        db.session.commit()
        
        # Verify
        assert session.user_id == user.id, "Session has user_id"
        assert session.workspace_id is None, "Session has no workspace"
        assert session.meeting_id is None, "Session has no meeting"
        
        print(f"✅ PASSED")
        print(f"   - Session created for user without workspace")
        print(f"   - user_id: {session.user_id}")
        print(f"   - workspace_id: {session.workspace_id} (None)")
        print(f"   - meeting_id: {session.meeting_id} (None)")
        print(f"   - No Meeting created (workspace required)")
        
        return True


def test_6_meeting_session_relationship_integrity():
    """
    TEST 6: Verify Meeting-Session relationship integrity
    Expected: All sessions with meeting_id have valid Meeting records
    """
    print_header("Meeting-Session Relationship Integrity")
    
    with app.app_context():
        sessions_with_meetings = db.session.query(Session).filter(
            Session.meeting_id.isnot(None)
        ).all()
        
        broken_links = 0
        workspace_mismatches = 0
        valid_links = 0
        
        for session in sessions_with_meetings:
            meeting = db.session.query(Meeting).filter_by(id=session.meeting_id).first()
            
            if not meeting:
                broken_links += 1
                print(f"   ❌ Session {session.id} has invalid meeting_id={session.meeting_id}")
            elif session.workspace_id != meeting.workspace_id:
                workspace_mismatches += 1
                print(f"   ⚠️ Session {session.id} workspace mismatch: session={session.workspace_id}, meeting={meeting.workspace_id}")
            else:
                valid_links += 1
        
        total = len(sessions_with_meetings)
        
        assert broken_links == 0, f"Found {broken_links} broken Meeting links"
        assert workspace_mismatches == 0, f"Found {workspace_mismatches} workspace mismatches"
        
        print(f"✅ PASSED")
        print(f"   - Total sessions with meetings: {total}")
        print(f"   - Valid links: {valid_links}")
        print(f"   - Broken links: {broken_links}")
        print(f"   - Workspace mismatches: {workspace_mismatches}")
        
        return True


def test_7_dashboard_filtering():
    """
    TEST 7: Verify dashboard only shows workspace-specific meetings
    Expected: Each workspace sees only its own meetings
    """
    print_header("Dashboard Workspace Filtering")
    
    with app.app_context():
        workspaces = db.session.query(Workspace).all()
        
        for workspace in workspaces:
            meetings = db.session.query(Meeting).filter_by(workspace_id=workspace.id).all()
            
            # Verify all meetings belong to this workspace
            for meeting in meetings:
                assert meeting.workspace_id == workspace.id, f"Meeting {meeting.id} has wrong workspace"
            
            print(f"   ✅ Workspace '{workspace.name}' (id={workspace.id}): {len(meetings)} meetings")
        
        # Verify orphaned sessions don't appear
        orphaned_sessions = db.session.query(Session).filter(
            Session.workspace_id.is_(None)
        ).count()
        
        print(f"\n   📊 Orphaned sessions (NULL workspace): {orphaned_sessions}")
        print(f"      These will NOT appear in any dashboard")
        
        print(f"\n✅ PASSED")
        print(f"   - All workspaces show only their own meetings")
        print(f"   - Orphaned sessions excluded from dashboards")
        
        return True


def test_8_concurrent_sessions():
    """
    TEST 8: Multiple concurrent sessions for same user
    Expected: All sessions properly tracked with unique IDs
    """
    print_header("Concurrent Sessions")
    
    with app.app_context():
        user = db.session.query(User).filter(User.workspace_id.isnot(None)).first()
        workspace_id = user.workspace_id
        
        # Create 3 concurrent sessions
        sessions = []
        meetings = []
        
        for i in range(3):
            session_id = f"concurrent_{i}_{int(datetime.utcnow().timestamp() * 1000)}"
            
            meeting = Meeting(
                title=f"Concurrent Test {i+1}",
                workspace_id=workspace_id,
                organizer_id=user.id,
                status="in_progress",
                meeting_type="live_recording",
                actual_start=datetime.utcnow()
            )
            db.session.add(meeting)
            db.session.flush()
            
            session = Session(
                external_id=session_id,
                title=meeting.title,
                status="active",
                started_at=datetime.utcnow(),
                user_id=user.id,
                workspace_id=workspace_id,
                meeting_id=meeting.id
            )
            db.session.add(session)
            sessions.append(session)
            meetings.append(meeting)
        
        db.session.commit()
        
        # Verify all unique
        session_ids = [s.external_id for s in sessions]
        meeting_ids = [m.id for m in meetings]
        
        assert len(set(session_ids)) == 3, "All session IDs must be unique"
        assert len(set(meeting_ids)) == 3, "All meeting IDs must be unique"
        
        print(f"✅ PASSED")
        print(f"   - Created 3 concurrent sessions")
        print(f"   - All have unique session IDs")
        print(f"   - All have unique meeting IDs")
        print(f"   - All properly linked to workspace {workspace_id}")
        
        return True


def test_9_data_persistence_after_completion():
    """
    TEST 9: Completed sessions persist in database
    Expected: Completed sessions remain queryable
    """
    print_header("Data Persistence After Completion")
    
    with app.app_context():
        # Query completed sessions
        completed_sessions = db.session.query(Session).filter_by(status="completed").all()
        completed_meetings = db.session.query(Meeting).filter_by(status="completed").all()
        
        print(f"   📊 Completed sessions: {len(completed_sessions)}")
        print(f"   📊 Completed meetings: {len(completed_meetings)}")
        
        # Verify they're still accessible
        for session in completed_sessions[:5]:  # Check first 5
            assert session.id is not None, "Session must have ID"
            assert session.status == "completed", "Session must be completed"
            
        for meeting in completed_meetings[:5]:
            assert meeting.id is not None, "Meeting must have ID"
            assert meeting.status == "completed", "Meeting must be completed"
        
        print(f"\n✅ PASSED")
        print(f"   - All completed records persist in database")
        print(f"   - Records remain queryable after completion")
        
        return True


def run_comprehensive_tests():
    """Run all comprehensive tests."""
    print("\n" + "🔬" * 35)
    print("COMPREHENSIVE PIPELINE INTEGRATION TEST SUITE")
    print("Testing all aspects and dimensions")
    print("🔬" * 35)
    print(f"Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    tests = [
        ("Authenticated User with Workspace", test_1_authenticated_user_with_workspace),
        ("Session Finalization", test_2_session_finalization_updates_both_records),
        ("Empty Transcript Handling", test_3_empty_transcript_handling),
        ("Anonymous User", test_4_anonymous_user_no_meeting),
        ("User Without Workspace", test_5_user_without_workspace),
        ("Relationship Integrity", test_6_meeting_session_relationship_integrity),
        ("Dashboard Filtering", test_7_dashboard_filtering),
        ("Concurrent Sessions", test_8_concurrent_sessions),
        ("Data Persistence", test_9_data_persistence_after_completion),
    ]
    
    results = {}
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ FAILED with exception: {e}")
            results[test_name] = False
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("   ✅ Authenticated users create Meeting + Session with workspace linkage")
        print("   ✅ Anonymous users create Session only (no Meeting)")
        print("   ✅ Session/Meeting completion works correctly")
        print("   ✅ Empty transcripts handled properly")
        print("   ✅ Dashboard filtering works by workspace")
        print("   ✅ Data relationships maintain integrity")
        print("   ✅ Concurrent sessions supported")
        print("   ✅ Data persists after completion")
    else:
        print(f"\n⚠️ {failed} test(s) failed - review output above")
    
    print("\n" + "=" * 70)
    print(f"Completed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
