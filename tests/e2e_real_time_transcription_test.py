"""
End-to-End Real-time Transcription Tests
Comprehensive testing of the complete real-time transcription pipeline.
"""

import pytest
import asyncio
import json
import time
import base64
from unittest.mock import patch, MagicMock, AsyncMock
import socketio

from tests import MockAudioData, TestFixtures, assert_valid_session, assert_valid_segment

class TestRealTimeTranscriptionE2E:
    """End-to-end tests for real-time transcription functionality."""
    
    @pytest.fixture
    def socketio_client(self, app):
        """Create a Socket.IO test client."""
        from app_refactored import socketio as sio
        client = socketio.test.TestClient(sio, app)
        return client
    
    @pytest.fixture
    def mock_transcription_service(self):
        """Mock transcription service for testing."""
        with patch('routes.websocket.get_transcription_service') as mock:
            service = MagicMock()
            service.active_sessions = {}
            service.start_session = AsyncMock()
            service.end_session = AsyncMock()
            service.process_audio = AsyncMock()
            service.add_session_callback = MagicMock()
            service.get_session_status = MagicMock()
            mock.return_value = service
            yield service
    
    def test_socket_connection(self, socketio_client):
        """Test Socket.IO connection establishment."""
        assert socketio_client.is_connected()
        
        # Check connection event was emitted
        received = socketio_client.get_received()
        assert len(received) > 0
        
        connect_event = received[0]
        assert connect_event['name'] == 'connected'
        assert 'client_id' in connect_event['args'][0]
        assert connect_event['args'][0]['status'] == 'connected'
    
    def test_session_creation_and_join(self, client, socketio_client, mock_transcription_service, database):
        """Test creating a session and joining via Socket.IO."""
        # Step 1: Create session via API
        session_data = TestFixtures.create_test_session_data()
        response = client.post('/api/sessions', 
                              data=json.dumps(session_data),
                              content_type='application/json')
        
        assert response.status_code == 201
        
        api_data = json.loads(response.data)
        assert api_data['success'] is True
        session_id = api_data['session_id']
        assert_valid_session(api_data['session'])
        
        # Step 2: Join session via Socket.IO
        socketio_client.emit('join_session', {'session_id': session_id})
        
        received = socketio_client.get_received()
        join_event = next((event for event in received if event['name'] == 'session_joined'), None)
        
        assert join_event is not None
        assert join_event['args'][0]['session_id'] == session_id
        assert_valid_session(join_event['args'][0]['session'])
        
        # Verify service method was called
        mock_transcription_service.add_session_callback.assert_called()
    
    def test_start_transcription_flow(self, socketio_client, mock_transcription_service, database):
        """Test starting transcription process."""
        session_id = 'test-session-123'
        
        # Mock session exists
        from models.session import Session
        from app_refactored import db
        
        session = Session(
            session_id=session_id,
            title='Test Session',
            status='created'
        )
        db.session.add(session)
        db.session.commit()
        
        # Join session
        socketio_client.emit('join_session', {'session_id': session_id})
        
        # Start transcription
        socketio_client.emit('start_transcription', {'session_id': session_id})
        
        received = socketio_client.get_received()
        start_event = next((event for event in received if event['name'] == 'transcription_started'), None)
        
        assert start_event is not None
        assert start_event['args'][0]['session_id'] == session_id
        
        # Verify session status was updated
        updated_session = Session.query.filter_by(session_id=session_id).first()
        assert updated_session.status == 'active'
    
    def test_audio_chunk_processing(self, socketio_client, mock_transcription_service, mock_audio_data):
        """Test audio chunk transmission and processing."""
        session_id = 'test-session-audio'
        
        # Mock service setup
        mock_transcription_service.active_sessions = {session_id: {}}
        mock_transcription_service.process_audio.return_value = {
            'session_id': session_id,
            'timestamp': time.time(),
            'vad': {
                'is_speech': True,
                'confidence': 0.8,
                'energy': 0.5
            },
            'transcription': {
                'text': 'Hello world',
                'confidence': 0.9,
                'is_final': False
            }
        }
        
        # Generate test audio data
        audio_data = mock_audio_data.generate_sine_wave(frequency=1000, duration_ms=1000)
        base64_audio = base64.b64encode(audio_data).decode('utf-8')
        
        # Join session and send audio chunk
        socketio_client.emit('join_session', {'session_id': session_id})
        socketio_client.emit('audio_chunk', {
            'session_id': session_id,
            'audio_data': base64_audio,
            'timestamp': time.time()
        })
        
        # Verify service method was called
        mock_transcription_service.process_audio.assert_called_once()
        
        # Check for interim result
        received = socketio_client.get_received()
        interim_event = next((event for event in received if event['name'] == 'interim_result'), None)
        
        if interim_event:  # May be emitted asynchronously
            result = interim_event['args'][0]
            assert result['session_id'] == session_id
            assert 'vad' in result
            assert 'transcription' in result
    
    def test_transcription_result_callback(self, socketio_client, mock_transcription_service):
        """Test transcription result callback mechanism."""
        session_id = 'test-callback-session'
        
        # Join session to set up callback
        socketio_client.emit('join_session', {'session_id': session_id})
        
        # Get the callback function that was registered
        mock_transcription_service.add_session_callback.assert_called_once()
        callback_args = mock_transcription_service.add_session_callback.call_args
        session_callback = callback_args[0][1]  # Second argument is the callback
        
        # Simulate transcription result
        from services.whisper_streaming import TranscriptionResult
        
        mock_result = TranscriptionResult(
            text='Test transcription result',
            confidence=0.85,
            is_final=True,
            language='en',
            duration=3.5,
            timestamp=time.time(),
            words=[],
            metadata={'session_id': session_id}
        )
        
        # Call the callback
        session_callback(mock_result)
        
        # Check for transcription result event
        received = socketio_client.get_received()
        result_event = next((event for event in received if event['name'] == 'transcription_result'), None)
        
        assert result_event is not None
        result_data = result_event['args'][0]
        assert result_data['session_id'] == session_id
        assert result_data['text'] == 'Test transcription result'
        assert result_data['confidence'] == 0.85
        assert result_data['is_final'] is True
    
    def test_stop_transcription_flow(self, socketio_client, mock_transcription_service, database):
        """Test stopping transcription process."""
        session_id = 'test-stop-session'
        
        # Create and start session
        from models.session import Session
        from app_refactored import db
        
        session = Session(
            session_id=session_id,
            title='Test Stop Session',
            status='active'
        )
        db.session.add(session)
        db.session.commit()
        
        # Mock service has active session
        mock_transcription_service.active_sessions = {session_id: {}}
        mock_transcription_service.end_session.return_value = {
            'session_id': session_id,
            'final_stats': {'total_segments': 5}
        }
        
        # Join session
        socketio_client.emit('join_session', {'session_id': session_id})
        
        # Stop transcription
        socketio_client.emit('stop_transcription', {'session_id': session_id})
        
        received = socketio_client.get_received()
        stop_event = next((event for event in received if event['name'] == 'transcription_stopped'), None)
        
        assert stop_event is not None
        assert stop_event['args'][0]['session_id'] == session_id
        
        # Verify service method was called
        mock_transcription_service.end_session.assert_called_once_with(session_id)
        
        # Verify session status was updated
        updated_session = Session.query.filter_by(session_id=session_id).first()
        assert updated_session.status == 'completed'
    
    def test_session_status_retrieval(self, socketio_client, mock_transcription_service, database):
        """Test getting session status via Socket.IO."""
        session_id = 'test-status-session'
        
        # Create session
        from models.session import Session
        from app_refactored import db
        
        session = Session(
            session_id=session_id,
            title='Test Status Session',
            status='active',
            total_segments=3,
            average_confidence=0.82
        )
        db.session.add(session)
        db.session.commit()
        
        # Mock service status
        mock_transcription_service.active_sessions = {session_id: {}}
        mock_transcription_service.get_session_status.return_value = {
            'session_id': session_id,
            'state': 'active',
            'stats': {'total_segments': 3}
        }
        
        # Request session status
        socketio_client.emit('get_session_status', {'session_id': session_id})
        
        received = socketio_client.get_received()
        status_event = next((event for event in received if event['name'] == 'session_status'), None)
        
        assert status_event is not None
        status_data = status_event['args'][0]
        assert status_data['session_id'] == session_id
        assert status_data['status'] == 'active'
        assert status_data['total_segments'] == 3
    
    def test_configuration_update(self, socketio_client, mock_transcription_service):
        """Test real-time configuration updates."""
        session_id = 'test-config-session'
        
        # Mock service setup
        mock_transcription_service.active_sessions = {session_id: {}}
        
        # Join session
        socketio_client.emit('join_session', {'session_id': session_id})
        
        # Update configuration
        config_updates = {
            'vad_sensitivity': 0.7,
            'min_confidence': 0.8,
            'language': 'es'
        }
        
        socketio_client.emit('update_session_config', {
            'session_id': session_id,
            'config': config_updates
        })
        
        received = socketio_client.get_received()
        
        # Should receive config update confirmation
        config_event = next((event for event in received if event['name'] == 'config_update_success'), None)
        assert config_event is not None
        
        # Should also receive config updated broadcast
        broadcast_event = next((event for event in received if event['name'] == 'config_updated'), None)
        if broadcast_event:
            assert broadcast_event['args'][0]['session_id'] == session_id
            assert broadcast_event['args'][0]['config'] == config_updates
    
    def test_error_handling(self, socketio_client, mock_transcription_service):
        """Test error handling in Socket.IO events."""
        # Test joining non-existent session
        socketio_client.emit('join_session', {'session_id': 'non-existent'})
        
        received = socketio_client.get_received()
        error_event = next((event for event in received if event['name'] == 'error'), None)
        
        assert error_event is not None
        assert 'not found' in error_event['args'][0]['message'].lower()
        
        # Test audio chunk without session
        socketio_client.emit('audio_chunk', {
            'audio_data': 'invalid-base64',
            'timestamp': time.time()
        })
        
        received = socketio_client.get_received()
        error_event = next((event for event in received if event['name'] == 'error'), None)
        
        assert error_event is not None
        assert 'required' in error_event['args'][0]['message'].lower()
    
    def test_ping_pong(self, socketio_client):
        """Test connection health check via ping/pong."""
        socketio_client.emit('ping', {'test': 'data'})
        
        received = socketio_client.get_received()
        pong_event = next((event for event in received if event['name'] == 'pong'), None)
        
        assert pong_event is not None
        assert 'timestamp' in pong_event['args'][0]
        assert 'client_id' in pong_event['args'][0]
    
    def test_leave_session(self, socketio_client, mock_transcription_service):
        """Test leaving a session."""
        session_id = 'test-leave-session'
        
        # Join then leave session
        socketio_client.emit('join_session', {'session_id': session_id})
        socketio_client.emit('leave_session', {'session_id': session_id})
        
        received = socketio_client.get_received()
        leave_event = next((event for event in received if event['name'] == 'session_left'), None)
        
        assert leave_event is not None
        assert leave_event['args'][0]['session_id'] == session_id
    
    @patch('routes.websocket.asyncio.create_task')
    def test_async_audio_processing(self, mock_create_task, socketio_client, mock_transcription_service, mock_audio_data):
        """Test that audio processing is handled asynchronously."""
        session_id = 'test-async-session'
        
        # Mock service setup
        mock_transcription_service.active_sessions = {session_id: {}}
        
        # Generate test audio
        audio_data = mock_audio_data.generate_sine_wave()
        base64_audio = base64.b64encode(audio_data).decode('utf-8')
        
        # Send audio chunk
        socketio_client.emit('join_session', {'session_id': session_id})
        socketio_client.emit('audio_chunk', {
            'session_id': session_id,
            'audio_data': base64_audio,
            'timestamp': time.time()
        })
        
        # Verify async task was created
        mock_create_task.assert_called()
    
    def test_multiple_clients_same_session(self, app, mock_transcription_service):
        """Test multiple clients joining the same session."""
        from app_refactored import socketio as sio
        
        # Create multiple test clients
        client1 = socketio.test.TestClient(sio, app)
        client2 = socketio.test.TestClient(sio, app)
        
        session_id = 'test-multi-client-session'
        
        # Both clients join the same session
        client1.emit('join_session', {'session_id': session_id})
        client2.emit('join_session', {'session_id': session_id})
        
        # Verify both received join confirmations
        received1 = client1.get_received()
        received2 = client2.get_received()
        
        join_event1 = next((event for event in received1 if event['name'] == 'session_joined'), None)
        join_event2 = next((event for event in received2 if event['name'] == 'session_joined'), None)
        
        assert join_event1 is not None
        assert join_event2 is not None
        assert join_event1['args'][0]['session_id'] == session_id
        assert join_event2['args'][0]['session_id'] == session_id
    
    def test_disconnect_cleanup(self, socketio_client, mock_transcription_service):
        """Test cleanup when client disconnects."""
        session_id = 'test-disconnect-session'
        
        # Join session then disconnect
        socketio_client.emit('join_session', {'session_id': session_id})
        socketio_client.disconnect()
        
        # Verify disconnect was handled (would be logged in real implementation)
        assert not socketio_client.is_connected()
    
    def test_invalid_audio_data_handling(self, socketio_client, mock_transcription_service):
        """Test handling of invalid audio data."""
        session_id = 'test-invalid-audio'
        
        # Mock service setup
        mock_transcription_service.active_sessions = {session_id: {}}
        
        # Join session
        socketio_client.emit('join_session', {'session_id': session_id})
        
        # Send invalid base64 audio data
        socketio_client.emit('audio_chunk', {
            'session_id': session_id,
            'audio_data': 'invalid-base64-data!!!',
            'timestamp': time.time()
        })
        
        received = socketio_client.get_received()
        error_event = next((event for event in received if event['name'] == 'error'), None)
        
        assert error_event is not None
        assert 'invalid' in error_event['args'][0]['message'].lower()
    
    def test_concurrent_audio_processing(self, socketio_client, mock_transcription_service, mock_audio_data):
        """Test handling of concurrent audio chunk processing."""
        session_id = 'test-concurrent-session'
        
        # Mock service setup
        mock_transcription_service.active_sessions = {session_id: {}}
        
        # Generate multiple audio chunks
        audio_chunks = []
        for i in range(5):
            audio_data = mock_audio_data.generate_sine_wave(frequency=1000 + i * 100)
            base64_audio = base64.b64encode(audio_data).decode('utf-8')
            audio_chunks.append(base64_audio)
        
        # Join session
        socketio_client.emit('join_session', {'session_id': session_id})
        
        # Send multiple audio chunks rapidly
        for i, audio_chunk in enumerate(audio_chunks):
            socketio_client.emit('audio_chunk', {
                'session_id': session_id,
                'audio_data': audio_chunk,
                'timestamp': time.time() + i * 0.1
            })
        
        # All chunks should be accepted (processing happens asynchronously)
        # Verify service was called multiple times
        assert mock_transcription_service.process_audio.call_count == len(audio_chunks)

@pytest.mark.asyncio
async def test_full_transcription_pipeline_integration(app, database, mock_audio_data):
    """
    Integration test for complete transcription pipeline.
    Tests the full flow from session creation to final transcription.
    """
    from app_refactored import socketio as sio
    from models.session import Session
    from models.segment import Segment
    from app_refactored import db
    
    with app.app_context():
        # Create test client
        client = socketio.test.TestClient(sio, app)
        
        # Mock the transcription service with realistic behavior
        with patch('routes.websocket.get_transcription_service') as mock_service_getter:
            service = MagicMock()
            service.active_sessions = {}
            
            # Mock session creation
            async def mock_start_session(session_id=None, user_config=None):
                service.active_sessions[session_id] = {'started': True}
                return session_id
            
            service.start_session = mock_start_session
            
            # Mock audio processing with realistic transcription
            async def mock_process_audio(session_id, audio_data, timestamp=None):
                return {
                    'session_id': session_id,
                    'timestamp': timestamp or time.time(),
                    'vad': {
                        'is_speech': True,
                        'confidence': 0.8
                    },
                    'transcription': {
                        'text': 'This is a test transcription segment.',
                        'confidence': 0.9,
                        'is_final': True
                    }
                }
            
            service.process_audio = mock_process_audio
            service.add_session_callback = MagicMock()
            service.get_session_status = MagicMock(return_value={
                'session_id': 'test-integration',
                'state': 'active',
                'stats': {'total_segments': 1}
            })
            
            mock_service_getter.return_value = service
            
            # Step 1: Create session in database
            session = Session(
                session_id='test-integration',
                title='Integration Test Session',
                status='created'
            )
            db.session.add(session)
            db.session.commit()
            
            # Step 2: Connect and join session
            client.emit('join_session', {'session_id': 'test-integration'})
            
            # Step 3: Start transcription
            client.emit('start_transcription', {'session_id': 'test-integration'})
            
            # Step 4: Send audio data
            audio_data = mock_audio_data.generate_sine_wave(frequency=1000, duration_ms=2000)
            base64_audio = base64.b64encode(audio_data).decode('utf-8')
            
            client.emit('audio_chunk', {
                'session_id': 'test-integration',
                'audio_data': base64_audio,
                'timestamp': time.time()
            })
            
            # Step 5: Verify results
            received = client.get_received()
            
            # Should have received session_joined, transcription_started, and potentially interim_result
            event_names = [event['name'] for event in received]
            assert 'session_joined' in event_names
            assert 'transcription_started' in event_names
            
            # Step 6: Stop transcription
            client.emit('stop_transcription', {'session_id': 'test-integration'})
            
            # Step 7: Verify final state
            received = client.get_received()
            stop_event = next((event for event in received if event['name'] == 'transcription_stopped'), None)
            assert stop_event is not None
            
            # Verify session was processed
            assert service.process_audio.called
            assert 'test-integration' in service.active_sessions
        
        print("Full transcription pipeline integration test completed successfully")
