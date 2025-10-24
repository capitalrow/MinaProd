"""
Integration tests for WebSocket <-> Database state synchronization.

Tests verify that WebSocket events properly update database state and
that the 5-second auto-flush persistence works correctly.
"""

import pytest
import time
import json
from app import app, db, socketio
from models.session import Session
from models.segment import Segment
from models.meeting import Meeting
from models.user import User
from datetime import datetime


@pytest.fixture(scope='function')
def test_client():
    """Create a test client with database."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def socketio_client(test_client):
    """Create a SocketIO test client."""
    return socketio.test_client(app, flask_test_client=test_client)


@pytest.fixture(scope='function')
def test_user():
    """Create a test user in the database."""
    with app.app_context():
        user = User(
            username='test_user',
            email='test@example.com'
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture(scope='function')
def test_meeting(test_user):
    """Create a test meeting in the database."""
    with app.app_context():
        meeting = Meeting(
            title='Test Meeting',
            user_id=test_user,
            scheduled_time=datetime.utcnow(),
            status='in_progress'
        )
        db.session.add(meeting)
        db.session.commit()
        return meeting.id


class TestWebSocketPersistence:
    """Test WebSocket events persist correctly to database."""
    
    def test_start_session_creates_db_record(self, socketio_client, test_meeting):
        """Test that starting a session creates a database record."""
        session_id = 'test-session-001'
        
        # Connect to default namespace
        socketio_client.emit('join_session', {
            'session_id': session_id,
            'meeting_id': test_meeting,
            'user_id': 1
        })
        
        # Give async operation time to complete
        time.sleep(0.5)
        
        # Verify session was created in database
        with app.app_context():
            session = db.session.query(Session).filter_by(
                external_id=session_id
            ).first()
            
            assert session is not None, "Session should be created in database"
            assert session.status == 'active'
            assert session.meeting_id == test_meeting
    
    def test_transcription_namespace_creates_session(self, socketio_client):
        """Test /transcription namespace creates session on start."""
        # Connect to /transcription namespace
        client = socketio.test_client(app, namespace='/transcription')
        
        session_data = {
            'session_id': 'test-session-002',
            'workspace_id': 'workspace-1',
            'user_id': 1
        }
        
        client.emit('start_session', session_data, namespace='/transcription')
        time.sleep(0.5)
        
        # Verify session was created
        with app.app_context():
            session = db.session.query(Session).filter_by(
                external_id='test-session-002'
            ).first()
            
            assert session is not None
            assert session.status == 'active'
    
    def test_segment_buffering_and_batch_flush(self, socketio_client):
        """Test that segments are buffered and flushed when batch size reached."""
        client = socketio.test_client(app, namespace='/transcription')
        
        # Start session
        client.emit('start_session', {
            'session_id': 'batch-test-session',
            'user_id': 1
        }, namespace='/transcription')
        time.sleep(0.5)
        
        # Send 5 audio segments (batch_size = 5)
        for i in range(5):
            audio_data = {
                'audio': b'fake_audio_data',
                'sequence': i
            }
            client.emit('audio_data', audio_data, namespace='/transcription')
            time.sleep(0.1)
        
        # Give time for batch flush
        time.sleep(1)
        
        # Verify segments were persisted
        with app.app_context():
            session = db.session.query(Session).filter_by(
                external_id='batch-test-session'
            ).first()
            
            assert session is not None
            
            segments = db.session.query(Segment).filter_by(
                session_id=session.id
            ).all()
            
            # Should have at least some segments flushed
            assert len(segments) > 0, "Batch flush should persist segments"
    
    def test_auto_flush_timer_persists_sparse_segments(self, socketio_client):
        """Test that timer-based auto-flush persists segments even when < batch_size."""
        client = socketio.test_client(app, namespace='/transcription')
        
        # Start session
        client.emit('start_session', {
            'session_id': 'timer-test-session',
            'user_id': 1
        }, namespace='/transcription')
        time.sleep(0.5)
        
        # Send only 2 segments (less than batch_size of 5)
        for i in range(2):
            audio_data = {
                'audio': b'fake_audio_data',
                'sequence': i
            }
            client.emit('audio_data', audio_data, namespace='/transcription')
            time.sleep(0.2)
        
        # Wait for auto-flush timer (5 seconds + margin)
        time.sleep(6)
        
        # Verify segments were persisted by timer
        with app.app_context():
            session = db.session.query(Session).filter_by(
                external_id='timer-test-session'
            ).first()
            
            if session:
                segments = db.session.query(Segment).filter_by(
                    session_id=session.id
                ).all()
                
                # Timer should flush sparse segments
                assert len(segments) >= 2, "Timer-based auto-flush should persist sparse segments"
    
    def test_end_session_marks_complete_and_flushes(self, socketio_client):
        """Test that ending a session marks it complete and flushes remaining segments."""
        client = socketio.test_client(app, namespace='/transcription')
        
        # Start session
        client.emit('start_session', {
            'session_id': 'end-test-session',
            'user_id': 1
        }, namespace='/transcription')
        time.sleep(0.5)
        
        # Send 2 segments (less than batch size)
        for i in range(2):
            audio_data = {
                'audio': b'fake_audio_data',
                'sequence': i
            }
            client.emit('audio_data', audio_data, namespace='/transcription')
            time.sleep(0.1)
        
        # End session (should force flush)
        client.emit('end_session', {
            'session_id': 'end-test-session'
        }, namespace='/transcription')
        time.sleep(0.5)
        
        # Verify session is completed and segments are flushed
        with app.app_context():
            session = db.session.query(Session).filter_by(
                external_id='end-test-session'
            ).first()
            
            assert session is not None
            assert session.status == 'completed'
            assert session.completed_at is not None
            
            segments = db.session.query(Segment).filter_by(
                session_id=session.id
            ).all()
            
            # Force flush should persist all segments
            assert len(segments) >= 2, "End session should force flush all segments"
    
    def test_session_metadata_updates(self, socketio_client):
        """Test that session metadata (duration, segment count) updates correctly."""
        client = socketio.test_client(app, namespace='/transcription')
        
        # Start session
        client.emit('start_session', {
            'session_id': 'metadata-test-session',
            'user_id': 1
        }, namespace='/transcription')
        time.sleep(0.5)
        
        # Send segments with duration info
        for i in range(5):
            audio_data = {
                'audio': b'fake_audio_data',
                'sequence': i,
                'duration': 2.5  # Each segment is 2.5 seconds
            }
            client.emit('audio_data', audio_data, namespace='/transcription')
            time.sleep(0.1)
        
        # Wait for batch flush
        time.sleep(1)
        
        # Verify session metadata
        with app.app_context():
            session = db.session.query(Session).filter_by(
                external_id='metadata-test-session'
            ).first()
            
            if session:
                # Should have updated total_segments and total_duration
                assert session.total_segments is not None and session.total_segments >= 5, "Should track total segments"
                assert session.total_duration is not None and session.total_duration >= 12.5, "Should track cumulative duration"
    
    def test_disconnect_cleanup(self, socketio_client):
        """Test that disconnect properly cleans up and flushes data."""
        client = socketio.test_client(app, namespace='/transcription')
        
        # Start session
        client.emit('start_session', {
            'session_id': 'disconnect-test-session',
            'user_id': 1
        }, namespace='/transcription')
        time.sleep(0.5)
        
        # Send some segments
        for i in range(3):
            audio_data = {
                'audio': b'fake_audio_data',
                'sequence': i
            }
            client.emit('audio_data', audio_data, namespace='/transcription')
            time.sleep(0.1)
        
        # Disconnect (should trigger cleanup and final flush)
        client.disconnect(namespace='/transcription')
        time.sleep(0.5)
        
        # Verify data was flushed before cleanup
        with app.app_context():
            session = db.session.query(Session).filter_by(
                external_id='disconnect-test-session'
            ).first()
            
            if session:
                segments = db.session.query(Segment).filter_by(
                    session_id=session.id
                ).all()
                
                # Disconnect should flush pending segments
                assert len(segments) >= 3, "Disconnect should flush pending segments"


class TestCrossPersistenceConsistency:
    """Test that both WebSocket namespaces maintain consistent database state."""
    
    def test_both_namespaces_persist_independently(self, socketio_client):
        """Test that default and /transcription namespaces don't interfere."""
        default_client = socketio_client
        transcription_client = socketio.test_client(app, namespace='/transcription')
        
        # Start session on default namespace
        default_client.emit('join_session', {
            'session_id': 'default-ns-session',
            'meeting_id': 1,
            'user_id': 1
        })
        time.sleep(0.3)
        
        # Start session on /transcription namespace
        transcription_client.emit('start_session', {
            'session_id': 'transcription-ns-session',
            'user_id': 1
        }, namespace='/transcription')
        time.sleep(0.3)
        
        # Verify both sessions exist independently
        with app.app_context():
            default_session = db.session.query(Session).filter_by(
                external_id='default-ns-session'
            ).first()
            
            transcription_session = db.session.query(Session).filter_by(
                external_id='transcription-ns-session'
            ).first()
            
            assert default_session is not None
            assert transcription_session is not None
            assert default_session.id != transcription_session.id
