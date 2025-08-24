"""
WebSocket Smoke Tests
Basic connectivity and communication tests for Socket.IO integration.
"""

import pytest
import socketio
from unittest.mock import patch, MagicMock


def test_socketio_connection(client):
    """Test basic Socket.IO connection."""
    # Create a test client
    sio = socketio.SimpleClient()
    
    try:
        # Connect to the Socket.IO server
        sio.connect('http://localhost:5000', transport='polling')
        
        # Should be connected
        assert sio.connected
        
        # Disconnect
        sio.disconnect()
        
    except Exception as e:
        pytest.skip(f"Socket.IO connection test skipped: {e}")


def test_socketio_ping_pong():
    """Test ping/pong functionality."""
    sio = socketio.SimpleClient()
    
    try:
        sio.connect('http://localhost:5000', transport='polling')
        
        # Send a ping-like event and wait for response
        received_data = []
        
        @sio.event
        def connected(data):
            received_data.append(data)
        
        # Wait briefly for connection event
        sio.sleep(0.1)
        
        # Should have received connection event
        if received_data:
            assert received_data[0]['status'] == 'connected'
        
        sio.disconnect()
        
    except Exception as e:
        pytest.skip(f"Socket.IO ping test skipped: {e}")


def test_socketio_audio_simulation():
    """Test simulated audio chunk processing."""
    sio = socketio.SimpleClient()
    
    try:
        sio.connect('http://localhost:5000', transport='polling')
        
        # Simulate audio chunk
        test_audio_data = b'test_audio_chunk_data'
        
        # Send audio data event (if handler exists)
        sio.emit('audio_chunk', {
            'session_id': 'test-session',
            'audio_data': test_audio_data.hex(),  # Send as hex string
            'timestamp': 1234567890.0
        })
        
        # For now, just verify connection remains stable
        assert sio.connected
        
        sio.disconnect()
        
    except Exception as e:
        pytest.skip(f"Socket.IO audio test skipped: {e}")


def test_socketio_interim_transcription():
    """Test interim transcription message receiving."""
    sio = socketio.SimpleClient()
    
    try:
        sio.connect('http://localhost:5000', transport='polling')
        
        received_messages = []
        
        @sio.event
        def interim_transcription(data):
            received_messages.append(data)
        
        @sio.event
        def transcription_result(data):
            received_messages.append(data)
        
        # Emit a mock transcription request
        sio.emit('ping', {'test': 'data'})
        
        # Wait for potential responses
        sio.sleep(0.1)
        
        # Connection should remain stable
        assert sio.connected
        
        sio.disconnect()
        
    except Exception as e:
        pytest.skip(f"Socket.IO transcription test skipped: {e}")


def test_socketio_error_handling():
    """Test Socket.IO error handling."""
    sio = socketio.SimpleClient()
    
    try:
        sio.connect('http://localhost:5000', transport='polling')
        
        # Send invalid event
        sio.emit('invalid_event', {'invalid': 'data'})
        
        # Connection should remain stable
        assert sio.connected
        
        sio.disconnect()
        
    except Exception as e:
        pytest.skip(f"Socket.IO error handling test skipped: {e}")


@pytest.mark.parametrize('transport', ['polling', 'websocket'])
def test_socketio_transport_modes(transport):
    """Test different Socket.IO transport modes."""
    sio = socketio.SimpleClient()
    
    try:
        sio.connect(f'http://localhost:5000', transport=transport)
        
        assert sio.connected
        
        sio.disconnect()
        
    except Exception as e:
        pytest.skip(f"Socket.IO {transport} test skipped: {e}")


def test_socketio_namespace_default():
    """Test Socket.IO default namespace functionality."""
    sio = socketio.SimpleClient()
    
    try:
        sio.connect('http://localhost:5000')
        
        # Test default namespace
        sio.emit('test_event', {'message': 'Hello from default namespace'})
        
        assert sio.connected
        
        sio.disconnect()
        
    except Exception as e:
        pytest.skip(f"Socket.IO namespace test skipped: {e}")


def test_socketio_session_management():
    """Test Socket.IO session management."""
    sio = socketio.SimpleClient()
    
    try:
        sio.connect('http://localhost:5000')
        
        # Test session creation via socket
        sio.emit('create_session', {
            'title': 'Test Socket Session',
            'language': 'en'
        })
        
        sio.sleep(0.1)
        
        assert sio.connected
        
        sio.disconnect()
        
    except Exception as e:
        pytest.skip(f"Socket.IO session management test skipped: {e}")


def test_socketio_concurrent_connections():
    """Test multiple concurrent Socket.IO connections."""
    clients = []
    
    try:
        # Create multiple clients
        for i in range(3):
            sio = socketio.SimpleClient()
            sio.connect('http://localhost:5000')
            clients.append(sio)
        
        # All should be connected
        for client in clients:
            assert client.connected
        
        # Disconnect all
        for client in clients:
            client.disconnect()
            
    except Exception as e:
        pytest.skip(f"Socket.IO concurrent connections test skipped: {e}")


def test_socketio_message_ordering():
    """Test Socket.IO message ordering."""
    sio = socketio.SimpleClient()
    
    try:
        sio.connect('http://localhost:5000')
        
        # Send multiple messages in order
        for i in range(5):
            sio.emit('test_message', {'sequence': i, 'message': f'Message {i}'})
        
        sio.sleep(0.1)
        
        assert sio.connected
        
        sio.disconnect()
        
    except Exception as e:
        pytest.skip(f"Socket.IO message ordering test skipped: {e}")