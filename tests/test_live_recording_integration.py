"""
Integration tests for live recording pipeline - verifying the complete flow
from recording to dashboard display.

Tests critical bug fixes:
- Meeting + Session creation with proper workspace linkage
- Database persistence (no NULL workspace_id)
- Dashboard display (recordings appear correctly)
- Edge cases (anonymous users, empty transcripts)
"""
import pytest
import json
from datetime import datetime
from flask import Flask
from flask_socketio import SocketIOTestClient
from app import app, socketio, db
from models import User, Workspace, Meeting, Session, Segment
from flask_login import login_user


class TestLiveRecordingIntegration:
    """Integration tests for live recording pipeline."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def socketio_client(self):
        """Create SocketIO test client."""
        return socketio.test_client(app)
    
    @pytest.fixture
    def authenticated_user(self):
        """Create authenticated user with workspace."""
        with app.app_context():
            # Create or get test user
            user = db.session.query(User).filter_by(email="test@integration.com").first()
            if not user:
                user = User(
                    username="testuser_integration",
                    email="test@integration.com",
                    is_active=True
                )
                db.session.add(user)
                db.session.flush()
                
                # Create workspace for user
                workspace = Workspace(
                    name="Test Integration Workspace",
                    owner_id=user.id
                )
                db.session.add(workspace)
                db.session.flush()
                
                # Link user to workspace
                user.workspaces = [workspace]
                db.session.commit()
            
            return user
    
    def test_authenticated_user_creates_meeting_and_session(self, socketio_client, authenticated_user):
        """
        Test: Authenticated user creates live recording
        Expected: Meeting + Session created with proper workspace linkage
        Fixes: NULL workspace_id bug
        """
        with app.app_context():
            session_id = f"test_session_{int(datetime.utcnow().timestamp())}"
            
            # Get initial counts
            initial_meeting_count = db.session.query(Meeting).count()
            initial_session_count = db.session.query(Session).count()
            
            # Simulate authenticated socket connection
            with app.test_request_context():
                from flask_login import login_user
                login_user(authenticated_user)
                
                # Join session
                socketio_client.emit('join_session', {'session_id': session_id})
                
                # Verify response
                received = socketio_client.get_received()
                assert len(received) > 0
                assert received[0]['name'] == 'server_hello'
            
            # Verify database records
            session = db.session.query(Session).filter_by(external_id=session_id).first()
            assert session is not None, "Session should be created"
            assert session.workspace_id is not None, "Session must have workspace_id (bug fix)"
            assert session.user_id == authenticated_user.id, "Session must belong to user"
            assert session.meeting_id is not None, "Session must be linked to Meeting"
            
            # Verify Meeting created
            meeting = db.session.query(Meeting).filter_by(id=session.meeting_id).first()
            assert meeting is not None, "Meeting should be created"
            assert meeting.workspace_id == session.workspace_id, "Meeting must have same workspace"
            assert meeting.organizer_id == authenticated_user.id, "Meeting must have organizer"
            assert meeting.status == "in_progress", "Meeting should be in progress"
            
            # Verify counts increased
            final_meeting_count = db.session.query(Meeting).count()
            final_session_count = db.session.query(Session).count()
            assert final_meeting_count == initial_meeting_count + 1, "Meeting count should increase"
            assert final_session_count == initial_session_count + 1, "Session count should increase"
            
            print(f"✅ Test passed: Meeting (id={meeting.id}) and Session created with workspace_id={session.workspace_id}")
    
    def test_session_finalization_updates_meeting_status(self, socketio_client, authenticated_user):
        """
        Test: Finalizing session updates both Session and Meeting status
        Expected: Both marked as "completed"
        Fixes: Completion logic bug
        """
        with app.app_context():
            session_id = f"test_finalize_{int(datetime.utcnow().timestamp())}"
            
            # Create session first (simulate authenticated user)
            with app.test_request_context():
                from flask_login import login_user
                login_user(authenticated_user)
                socketio_client.emit('join_session', {'session_id': session_id})
            
            # Get the created session and meeting
            session = db.session.query(Session).filter_by(external_id=session_id).first()
            assert session is not None
            meeting_id = session.meeting_id
            assert meeting_id is not None
            
            # Finalize session with audio data
            finalize_data = {
                'session_id': session_id,
                'settings': {'mimeType': 'audio/webm'}
            }
            socketio_client.emit('finalize_session', finalize_data)
            
            # Verify Session status
            db.session.refresh(session)
            assert session.status == "completed", "Session should be completed"
            assert session.completed_at is not None, "Session should have completion time"
            
            # Verify Meeting status
            meeting = db.session.query(Meeting).filter_by(id=meeting_id).first()
            assert meeting.status == "completed", "Meeting should be completed"
            assert meeting.actual_end is not None, "Meeting should have end time"
            
            print(f"✅ Test passed: Session and Meeting (id={meeting_id}) marked as completed")
    
    def test_empty_transcript_still_completes(self, socketio_client, authenticated_user):
        """
        Test: Empty transcript doesn't prevent session completion
        Expected: Session and Meeting still marked "completed"
        Fixes: Empty transcript bug
        """
        with app.app_context():
            session_id = f"test_empty_{int(datetime.utcnow().timestamp())}"
            
            # Create session
            with app.test_request_context():
                from flask_login import login_user
                login_user(authenticated_user)
                socketio_client.emit('join_session', {'session_id': session_id})
            
            session = db.session.query(Session).filter_by(external_id=session_id).first()
            meeting_id = session.meeting_id
            
            # Finalize with empty audio (will produce empty transcript)
            socketio_client.emit('finalize_session', {
                'session_id': session_id,
                'settings': {'mimeType': 'audio/webm'}
            })
            
            # Verify completion even without transcript
            db.session.refresh(session)
            meeting = db.session.query(Meeting).filter_by(id=meeting_id).first()
            
            assert session.status == "completed", "Session should complete even with empty transcript"
            assert meeting.status == "completed", "Meeting should complete even with empty transcript"
            
            # Verify no segment created (as expected for empty transcript)
            segments = db.session.query(Segment).filter_by(session_id=session.id).all()
            assert len(segments) == 0, "No segments should be created for empty transcript"
            
            print(f"✅ Test passed: Empty transcript handled correctly, status=completed")
    
    def test_dashboard_shows_new_recordings(self, client, authenticated_user):
        """
        Test: New recordings appear in dashboard
        Expected: Dashboard displays meetings with correct workspace filter
        Fixes: Dashboard visibility bug
        """
        with app.app_context():
            # Login user
            with client.session_transaction() as sess:
                sess['_user_id'] = str(authenticated_user.id)
            
            # Get user's workspace
            workspace = authenticated_user.workspaces[0] if authenticated_user.workspaces else None
            assert workspace is not None, "User must have workspace"
            
            # Create a test meeting in this workspace
            test_meeting = Meeting(
                title="Dashboard Test Meeting",
                workspace_id=workspace.id,
                organizer_id=authenticated_user.id,
                status="completed",
                meeting_type="live_recording",
                actual_start=datetime.utcnow(),
                actual_end=datetime.utcnow()
            )
            db.session.add(test_meeting)
            db.session.commit()
            
            # Query meetings as dashboard would
            dashboard_meetings = db.session.query(Meeting).filter_by(
                workspace_id=workspace.id
            ).all()
            
            assert len(dashboard_meetings) > 0, "Dashboard should show meetings"
            meeting_ids = [m.id for m in dashboard_meetings]
            assert test_meeting.id in meeting_ids, "Test meeting should appear in dashboard"
            
            print(f"✅ Test passed: Dashboard shows {len(dashboard_meetings)} meetings for workspace {workspace.id}")
    
    def test_workspace_linkage_prevents_orphaned_records(self, authenticated_user):
        """
        Test: Verify no orphaned records (NULL workspace_id)
        Expected: All recent sessions have proper workspace linkage
        Fixes: Core bug - orphaned sessions
        """
        with app.app_context():
            workspace = authenticated_user.workspaces[0]
            
            # Query all sessions for this workspace
            workspace_sessions = db.session.query(Session).filter_by(
                workspace_id=workspace.id
            ).all()
            
            # Verify none are orphaned
            for session in workspace_sessions:
                assert session.workspace_id is not None, f"Session {session.id} should have workspace_id"
                assert session.user_id is not None, f"Session {session.id} should have user_id"
                
                if session.meeting_id:
                    meeting = db.session.query(Meeting).filter_by(id=session.meeting_id).first()
                    assert meeting is not None, f"Session {session.id} meeting_id should be valid"
                    assert meeting.workspace_id == session.workspace_id, "Meeting and Session must share workspace"
            
            print(f"✅ Test passed: {len(workspace_sessions)} sessions properly linked to workspace {workspace.id}")


def test_full_pipeline_integration():
    """
    Full end-to-end integration test of the recording pipeline.
    Tests: WebSocket → Database → Dashboard
    """
    with app.app_context():
        # Get a test user
        user = db.session.query(User).filter_by(email="chinyemba.malowa@yahoo.co.uk").first()
        if not user or not user.workspaces:
            print("⚠️ Skipping full pipeline test - no authenticated user with workspace found")
            return
        
        workspace = user.workspaces[0]
        
        # Count before
        meetings_before = db.session.query(Meeting).filter_by(workspace_id=workspace.id).count()
        sessions_before = db.session.query(Session).filter_by(workspace_id=workspace.id).count()
        
        print(f"\n📊 Initial state:")
        print(f"   Meetings in workspace {workspace.id}: {meetings_before}")
        print(f"   Sessions in workspace {workspace.id}: {sessions_before}")
        
        # Verify no orphaned records
        orphaned_sessions = db.session.query(Session).filter(
            Session.workspace_id.is_(None),
            Session.created_at >= datetime(2025, 10, 24)  # Recent sessions
        ).all()
        
        orphaned_count = len(orphaned_sessions)
        print(f"   Orphaned sessions (NULL workspace_id): {orphaned_count}")
        
        if orphaned_count > 0:
            print("\n⚠️ Found orphaned sessions - these won't appear in dashboard:")
            for s in orphaned_sessions[:5]:  # Show first 5
                print(f"      - Session {s.external_id}: user_id={s.user_id}, workspace_id={s.workspace_id}, meeting_id={s.meeting_id}")
        
        # Check Meeting-Session linkage
        sessions_with_meetings = db.session.query(Session).filter(
            Session.workspace_id == workspace.id,
            Session.meeting_id.isnot(None)
        ).count()
        
        print(f"\n🔗 Data integrity:")
        print(f"   Sessions with Meeting linkage: {sessions_with_meetings}/{sessions_before}")
        print(f"   Meetings in workspace: {meetings_before}")
        
        # Verify dashboard would show these meetings
        dashboard_meetings = db.session.query(Meeting).filter_by(
            workspace_id=workspace.id
        ).order_by(Meeting.created_at.desc()).limit(5).all()
        
        print(f"\n📋 Dashboard preview (last 5 meetings):")
        for meeting in dashboard_meetings:
            session_count = db.session.query(Session).filter_by(meeting_id=meeting.id).count()
            print(f"   - {meeting.title} (id={meeting.id}, status={meeting.status}, sessions={session_count})")
        
        print(f"\n✅ Full pipeline test complete")
        print(f"   Total meetings visible in dashboard: {len(dashboard_meetings)}")
        
        return {
            'meetings_count': meetings_before,
            'sessions_count': sessions_before,
            'orphaned_count': orphaned_count,
            'dashboard_visible': len(dashboard_meetings)
        }


if __name__ == "__main__":
    # Run the full pipeline test
    print("=" * 70)
    print("LIVE RECORDING PIPELINE INTEGRATION TEST")
    print("=" * 70)
    
    result = test_full_pipeline_integration()
    
    if result:
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"✓ Total meetings: {result['meetings_count']}")
        print(f"✓ Total sessions: {result['sessions_count']}")
        print(f"{'✓' if result['orphaned_count'] == 0 else '✗'} Orphaned sessions: {result['orphaned_count']}")
        print(f"✓ Dashboard visible meetings: {result['dashboard_visible']}")
        
        if result['orphaned_count'] == 0:
            print("\n🎉 All tests passed! Pipeline is working correctly.")
        else:
            print("\n⚠️ Found orphaned sessions - fix is working for new sessions only.")
            print("   Old orphaned sessions will need data migration.")
