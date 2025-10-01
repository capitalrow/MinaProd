"""
Unit tests for test data factories.
"""
import pytest
from tests.factories import (
    UserFactory, SessionFactory, SegmentFactory,
    MeetingFactory, SummaryFactory, TaskFactory,
    WorkspaceFactory, ParticipantFactory, create_complete_meeting_data
)

@pytest.mark.unit
def test_user_factory():
    """Test UserFactory creates valid user data."""
    user = UserFactory()
    assert 'id' in user
    assert 'username' in user
    assert 'email' in user
    assert '@example.com' in user['email']
    assert user['is_active'] is True

@pytest.mark.unit
def test_session_factory():
    """Test SessionFactory creates valid session data."""
    session = SessionFactory()
    assert 'id' in session
    assert 'user_id' in session
    assert 'title' in session
    assert session['status'] in ['active', 'paused', 'completed']
    assert session['language'] == 'en'

@pytest.mark.unit
def test_segment_factory():
    """Test SegmentFactory creates valid segment data."""
    segment = SegmentFactory()
    assert 'id' in segment
    assert 'text' in segment
    assert 'confidence' in segment
    assert 0.8 <= segment['confidence'] <= 1.0
    assert segment['end_time'] > segment['start_time']

@pytest.mark.unit
def test_meeting_factory():
    """Test MeetingFactory creates valid meeting data."""
    meeting = MeetingFactory()
    assert 'id' in meeting
    assert 'title' in meeting
    assert 'status' in meeting
    assert meeting['status'] in ['scheduled', 'live', 'completed', 'cancelled']

@pytest.mark.unit
def test_summary_factory():
    """Test SummaryFactory creates valid summary data."""
    summary = SummaryFactory()
    assert 'id' in summary
    assert 'summary_text' in summary
    assert 'key_points' in summary
    assert 'action_items' in summary
    assert isinstance(summary['key_points'], list)
    assert len(summary['key_points']) > 0

@pytest.mark.unit
def test_task_factory():
    """Test TaskFactory creates valid task data."""
    task = TaskFactory()
    assert 'id' in task
    assert 'title' in task
    assert 'status' in task
    assert task['priority'] in ['low', 'medium', 'high']

@pytest.mark.unit
def test_workspace_factory():
    """Test WorkspaceFactory creates valid workspace data."""
    workspace = WorkspaceFactory()
    assert 'id' in workspace
    assert 'name' in workspace
    assert 'slug' in workspace
    assert workspace['plan'] in ['free', 'pro', 'enterprise']

@pytest.mark.unit
def test_participant_factory():
    """Test ParticipantFactory creates valid participant data."""
    participant = ParticipantFactory()
    assert 'id' in participant
    assert 'name' in participant
    assert 'email' in participant
    assert participant['role'] in ['organizer', 'presenter', 'attendee']
    assert participant['status'] in ['invited', 'accepted', 'declined', 'attended']

@pytest.mark.unit
def test_complete_meeting_data():
    """Test creating complete meeting data with all relations."""
    data = create_complete_meeting_data()
    
    assert 'user' in data
    assert 'session' in data
    assert 'segments' in data
    assert 'summary' in data
    assert 'tasks' in data
    
    assert data['session']['user_id'] == data['user']['id']
    assert len(data['segments']) == 15
    assert len(data['tasks']) == 3
    
    for segment in data['segments']:
        assert segment['session_id'] == data['session']['id']
    
    for task in data['tasks']:
        assert task['session_id'] == data['session']['id']
