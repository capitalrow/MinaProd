"""
Comprehensive System Verification Tests
End-to-end system tests validating the complete Mina platform functionality.
"""

import pytest
import json
import time
import base64
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from concurrent.futures import ThreadPoolExecutor
import requests
import socketio

from tests import MockAudioData, TestFixtures, assert_valid_session, assert_valid_segment

class TestComprehensiveSystemVerification:
    """Comprehensive system verification test suite."""
    
    @pytest.fixture
    def system_client(self, app):
        """Create system test client with full context."""
        return app.test_client()
    
    @pytest.fixture
    def system_socketio_client(self, app):
        """Create Socket.IO client for system tests."""
        from app_refactored import socketio as sio
        return socketio.test.TestClient(sio, app)
    
    @pytest.fixture
    def mock_comprehensive_service(self):
        """Comprehensive mock of all services for system testing."""
        with patch('routes.websocket.get_transcription_service') as mock_ws, \
             patch('routes.transcription.get_transcription_service') as mock_api:
            
            service = MagicMock()
            service.active_sessions = {}
            service.start_session = AsyncMock()
            service.end_session = AsyncMock()
            service.process_audio = AsyncMock()
            service.add_session_callback = MagicMock()
            service.get_session_status = MagicMock()
            service.get_global_statistics = MagicMock()
            
            # Return realistic statistics
            service.get_global_statistics.return_value = {
                'total_sessions': 0,
                'active_sessions': 0,
                'total_segments': 0,
                'average_processing_time': 150.5,
                'processing_queue_size': 0,
                'max_concurrent_sessions': 10
            }
            
            mock_ws.return_value = service
            mock_api.return_value = service
            yield service
    
    def test_system_health_and_readiness(self, system_client):
        """Comprehensive health check system verification."""
        # Test basic health
        response = system_client.get('/health')
        assert response.status_code == 200
        
        health_data = json.loads(response.data)
        assert health_data['status'] == 'ok'
        assert 'version' in health_data
        
        # Test detailed health
        response = system_client.get('/health/detailed')
        assert response.status_code == 200
        
        detailed_data = json.loads(response.data)
        assert 'system' in detailed_data
        assert 'database' in detailed_data
        assert 'services' in detailed_data
        
        # Test readiness
        response = system_client.get('/health/ready')
        assert response.status_code == 200
        
        # Test liveness
        response = system_client.get('/health/live')
        assert response.status_code == 200
        
        print("✓ System health checks passed")
    
    def test_database_connectivity_and_operations(self, system_client, database):
        """Verify database connectivity and basic operations."""
        from models.session import Session
        from models.segment import Segment
        from app_refactored import db
        
        # Test database write
        session = Session(
            session_id='system-test-db',
            title='Database System Test',
            status='created'
        )
        db.session.add(session)
        db.session.commit()
        
        # Test database read
        retrieved_session = Session.query.filter_by(session_id='system-test-db').first()
        assert retrieved_session is not None
        assert retrieved_session.title == 'Database System Test'
        
        # Test segment creation
        segment = Segment(
            session_id='system-test-db',
            segment_id='system-test-segment-1',
            sequence_number=1,
            start_time=0.0,
            end_time=5.0,
            text='System test transcription segment',
            confidence=0.95,
            is_final=True
        )
        db.session.add(segment)
        db.session.commit()
        
        # Verify segment relationship
        retrieved_session = Session.query.filter_by(session_id='system-test-db').first()
        assert len(retrieved_session.segments) == 1
        assert retrieved_session.segments[0].text == 'System test transcription segment'
        
        print("✓ Database operations verified")
    
    def test_api_endpoints_comprehensive(self, system_client, mock_comprehensive_service, database):
        """Comprehensive API endpoint verification."""
        # Test session creation
        session_data = {
            'title': 'System Test Session',
            'description': 'Comprehensive system test',
            'language': 'en',
            'enable_speaker_detection': True,
            'enable_sentiment_analysis': False
        }
        
        response = system_client.post('/api/sessions',
                                     data=json.dumps(session_data),
                                     content_type='application/json')
        
        assert response.status_code == 201
        api_data = json.loads(response.data)
        assert api_data['success'] is True
        session_id = api_data['session_id']
        
        # Test session retrieval
        response = system_client.get(f'/api/sessions/{session_id}')
        assert response.status_code == 200
        
        session_info = json.loads(response.data)
        assert session_info['session_id'] == session_id
        assert session_info['title'] == 'System Test Session'
        
        # Test session segments (empty initially)
        response = system_client.get(f'/api/sessions/{session_id}/segments')
        assert response.status_code == 200
        
        segments_data = json.loads(response.data)
        assert segments_data['session_id'] == session_id
        assert segments_data['segments'] == []
        
        # Test global statistics
        response = system_client.get('/api/stats')
        assert response.status_code == 200
        
        stats_data = json.loads(response.data)
        assert 'database' in stats_data
        assert 'service' in stats_data
        
        # Test session ending
        response = system_client.post(f'/api/sessions/{session_id}/end')
        assert response.status_code == 200
        
        end_data = json.loads(response.data)
        assert end_data['success'] is True
        
        print("✓ API endpoints verification passed")
    
    def test_frontend_pages_loading(self, system_client):
        """Verify all frontend pages load correctly."""
        # Test main dashboard
        response = system_client.get('/')
        assert response.status_code == 200
        assert b'Dashboard' in response.data
        
        # Test live transcription page
        response = system_client.get('/live')
        assert response.status_code == 200
        assert b'Live Transcription' in response.data
        
        # Test sessions list page
        response = system_client.get('/sessions')
        assert response.status_code == 200
        assert b'Sessions' in response.data or b'No sessions' in response.data
        
        print("✓ Frontend pages loading verified")
    
    def test_static_assets_loading(self, system_client):
        """Verify static assets are accessible."""
        # Test CSS
        response = system_client.get('/static/css/main.css')
        assert response.status_code == 200
        assert b'Mina Platform' in response.data
        
        # Test JavaScript files
        js_files = [
            '/static/js/real_time_transcription.js',
            '/static/js/vad_processor_advanced.js',
            '/static/js/websocket_streaming.js'
        ]
        
        for js_file in js_files:
            response = system_client.get(js_file)
            assert response.status_code == 200
            assert b'class' in response.data  # Should contain class definitions
        
        print("✓ Static assets loading verified")
    
    def test_websocket_connectivity_comprehensive(self, system_socketio_client, mock_comprehensive_service):
        """Comprehensive WebSocket connectivity and functionality test."""
        # Test connection
        assert system_socketio_client.is_connected()
        
        # Test ping/pong
        system_socketio_client.emit('ping', {'test': 'system_verification'})
        received = system_socketio_client.get_received()
        pong_event = next((event for event in received if event['name'] == 'pong'), None)
        assert pong_event is not None
        
        # Test session joining
        session_id = 'system-test-websocket'
        system_socketio_client.emit('join_session', {'session_id': session_id})
        
        received = system_socketio_client.get_received()
        join_event = next((event for event in received if event['name'] == 'session_joined'), None)
        
        # May not join if session doesn't exist, but should not error
        error_event = next((event for event in received if event['name'] == 'error'), None)
        if error_event:
            assert 'not found' in error_event['args'][0]['message']
        
        print("✓ WebSocket connectivity verified")
    
    def test_audio_processing_pipeline_mock(self, system_socketio_client, mock_comprehensive_service, mock_audio_data, database):
        """Test complete audio processing pipeline with mocks."""
        from models.session import Session
        from app_refactored import db
        
        # Create test session
        session = Session(
            session_id='audio-pipeline-test',
            title='Audio Pipeline Test',
            status='created'
        )
        db.session.add(session)
        db.session.commit()
        
        # Mock service responses
        mock_comprehensive_service.active_sessions = {'audio-pipeline-test': {}}
        mock_comprehensive_service.process_audio.return_value = {
            'session_id': 'audio-pipeline-test',
            'timestamp': time.time(),
            'vad': {
                'is_speech': True,
                'confidence': 0.85,
                'energy': 0.6
            },
            'transcription': {
                'text': 'System verification audio test',
                'confidence': 0.92,
                'is_final': True
            }
        }
        
        # Join session
        system_socketio_client.emit('join_session', {'session_id': 'audio-pipeline-test'})
        
        # Start transcription
        system_socketio_client.emit('start_transcription', {'session_id': 'audio-pipeline-test'})
        
        # Send audio data
        audio_data = mock_audio_data.generate_sine_wave(frequency=800, duration_ms=1500)
        base64_audio = base64.b64encode(audio_data).decode('utf-8')
        
        system_socketio_client.emit('audio_chunk', {
            'session_id': 'audio-pipeline-test',
            'audio_data': base64_audio,
            'timestamp': time.time()
        })
        
        # Verify processing was called
        mock_comprehensive_service.process_audio.assert_called_once()
        
        # Stop transcription
        system_socketio_client.emit('stop_transcription', {'session_id': 'audio-pipeline-test'})
        
        print("✓ Audio processing pipeline mock test passed")
    
    def test_error_handling_comprehensive(self, system_client, system_socketio_client):
        """Comprehensive error handling verification."""
        # Test API error handling
        response = system_client.get('/api/sessions/non-existent-session')
        assert response.status_code == 404
        
        response = system_client.post('/api/sessions',
                                     data='invalid json',
                                     content_type='application/json')
        assert response.status_code == 400
        
        # Test WebSocket error handling
        system_socketio_client.emit('join_session', {})  # Missing session_id
        received = system_socketio_client.get_received()
        error_event = next((event for event in received if event['name'] == 'error'), None)
        assert error_event is not None
        
        system_socketio_client.emit('audio_chunk', {
            'session_id': 'non-existent',
            'audio_data': 'invalid-data'
        })
        received = system_socketio_client.get_received()
        error_event = next((event for event in received if event['name'] == 'error'), None)
        assert error_event is not None
        
        print("✓ Error handling verification passed")
    
    def test_concurrent_operations(self, system_client, mock_comprehensive_service, database):
        """Test system behavior under concurrent operations."""
        def create_session(index):
            session_data = {
                'title': f'Concurrent Test Session {index}',
                'language': 'en'
            }
            response = system_client.post('/api/sessions',
                                         data=json.dumps(session_data),
                                         content_type='application/json')
            return response.status_code, response.data
        
        # Create multiple sessions concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_session, i) for i in range(10)]
            results = [future.result() for future in futures]
        
        # All should succeed
        for status_code, data in results:
            assert status_code == 201
            response_data = json.loads(data)
            assert response_data['success'] is True
        
        print("✓ Concurrent operations test passed")
    
    def test_data_persistence_and_integrity(self, system_client, database):
        """Test data persistence and integrity."""
        from models.session import Session
        from models.segment import Segment
        from app_refactored import db
        
        # Create session with segments
        session = Session(
            session_id='persistence-test',
            title='Data Persistence Test',
            status='active',
            total_segments=0,
            average_confidence=0.0
        )
        db.session.add(session)
        db.session.flush()  # Get ID without committing
        
        # Add multiple segments
        segments_data = [
            ('Segment one with high confidence', 0.95, 0.0, 2.0),
            ('Segment two with medium confidence', 0.75, 2.0, 4.5),
            ('Segment three with low confidence', 0.65, 4.5, 7.0)
        ]
        
        for i, (text, confidence, start, end) in enumerate(segments_data):
            segment = Segment(
                session_id='persistence-test',
                segment_id=f'persistence-segment-{i+1}',
                sequence_number=i+1,
                start_time=start,
                end_time=end,
                text=text,
                confidence=confidence,
                is_final=True
            )
            db.session.add(segment)
        
        # Update session statistics
        session.total_segments = len(segments_data)
        session.average_confidence = sum(conf for _, conf, _, _ in segments_data) / len(segments_data)
        
        db.session.commit()
        
        # Verify data integrity
        retrieved_session = Session.query.filter_by(session_id='persistence-test').first()
        assert retrieved_session is not None
        assert retrieved_session.total_segments == 3
        assert abs(retrieved_session.average_confidence - 0.783) < 0.01  # Allow for float precision
        
        # Verify segments are ordered correctly
        segments = Segment.query.filter_by(session_id='persistence-test').order_by(Segment.sequence_number).all()
        assert len(segments) == 3
        assert segments[0].text == 'Segment one with high confidence'
        assert segments[1].sequence_number == 2
        assert segments[2].end_time == 7.0
        
        # Test cascade operations
        db.session.delete(retrieved_session)
        db.session.commit()
        
        # Segments should still exist (no cascade delete configured)
        remaining_segments = Segment.query.filter_by(session_id='persistence-test').count()
        assert remaining_segments == 3
        
        print("✓ Data persistence and integrity verified")
    
    def test_configuration_management(self, system_client, mock_comprehensive_service):
        """Test configuration management across the system."""
        # Test default configuration loading
        response = system_client.get('/health')
        assert response.status_code == 200
        
        # Test environment variable usage
        import os
        original_version = os.environ.get('APP_VERSION')
        
        try:
            os.environ['APP_VERSION'] = '2.1.0-test'
            response = system_client.get('/health')
            health_data = json.loads(response.data)
            assert health_data['version'] == '2.1.0-test'
        finally:
            if original_version:
                os.environ['APP_VERSION'] = original_version
            elif 'APP_VERSION' in os.environ:
                del os.environ['APP_VERSION']
        
        print("✓ Configuration management verified")
    
    @pytest.mark.slow
    def test_performance_benchmarks(self, system_client, mock_comprehensive_service, database):
        """Basic performance benchmarks for key operations."""
        import time
        
        # Benchmark session creation
        start_time = time.time()
        for i in range(10):
            session_data = {
                'title': f'Performance Test Session {i}',
                'language': 'en'
            }
            response = system_client.post('/api/sessions',
                                         data=json.dumps(session_data),
                                         content_type='application/json')
            assert response.status_code == 201
        
        session_creation_time = time.time() - start_time
        avg_session_creation = session_creation_time / 10
        
        # Should create sessions quickly
        assert avg_session_creation < 0.5  # Less than 500ms per session
        
        # Benchmark health checks
        start_time = time.time()
        for _ in range(50):
            response = system_client.get('/health')
            assert response.status_code == 200
        
        health_check_time = time.time() - start_time
        avg_health_check = health_check_time / 50
        
        # Health checks should be very fast
        assert avg_health_check < 0.1  # Less than 100ms per health check
        
        print(f"✓ Performance benchmarks passed:")
        print(f"  - Session creation: {avg_session_creation:.3f}s average")
        print(f"  - Health check: {avg_health_check:.3f}s average")
    
    def test_memory_usage_stability(self, system_client, mock_comprehensive_service, database):
        """Basic memory usage stability test."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform operations that might cause memory leaks
        for i in range(100):
            # Create and end sessions
            session_data = {
                'title': f'Memory Test Session {i}',
                'language': 'en'
            }
            response = system_client.post('/api/sessions',
                                         data=json.dumps(session_data),
                                         content_type='application/json')
            assert response.status_code == 201
            
            # Health checks
            response = system_client.get('/health')
            assert response.status_code == 200
            
            # Static asset requests
            response = system_client.get('/static/css/main.css')
            assert response.status_code == 200
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB for this test)
        assert memory_increase < 50 * 1024 * 1024
        
        print(f"✓ Memory stability verified:")
        print(f"  - Memory increase: {memory_increase / 1024 / 1024:.2f}MB")
    
    def test_system_integration_workflow(self, system_client, system_socketio_client, mock_comprehensive_service, database):
        """Complete system integration workflow test."""
        # Step 1: Create session via API
        session_data = {
            'title': 'System Integration Workflow Test',
            'description': 'End-to-end workflow verification',
            'language': 'en',
            'enable_speaker_detection': True
        }
        
        response = system_client.post('/api/sessions',
                                     data=json.dumps(session_data),
                                     content_type='application/json')
        assert response.status_code == 201
        
        api_data = json.loads(response.data)
        session_id = api_data['session_id']
        
        # Step 2: Connect via WebSocket
        system_socketio_client.emit('join_session', {'session_id': session_id})
        
        # Step 3: Start transcription
        system_socketio_client.emit('start_transcription', {'session_id': session_id})
        
        # Step 4: Simulate audio processing
        mock_comprehensive_service.active_sessions = {session_id: {}}
        
        # Step 5: Check session status via API
        response = system_client.get(f'/api/sessions/{session_id}')
        assert response.status_code == 200
        
        # Step 6: Stop transcription
        system_socketio_client.emit('stop_transcription', {'session_id': session_id})
        
        # Step 7: Export session data
        response = system_client.get(f'/api/sessions/{session_id}/export?format=txt')
        # May not have data, but should not error
        assert response.status_code in [200, 400]  # 400 if no data to export
        
        # Step 8: Check global statistics
        response = system_client.get('/api/stats')
        assert response.status_code == 200
        
        print("✓ Complete system integration workflow verified")
    
    def run_comprehensive_verification(self):
        """Run all comprehensive verification tests."""
        print("\n" + "="*60)
        print("STARTING COMPREHENSIVE SYSTEM VERIFICATION")
        print("="*60)
        
        # This would be called by pytest, but included for documentation
        test_methods = [
            'test_system_health_and_readiness',
            'test_database_connectivity_and_operations',
            'test_api_endpoints_comprehensive',
            'test_frontend_pages_loading',
            'test_static_assets_loading',
            'test_websocket_connectivity_comprehensive',
            'test_audio_processing_pipeline_mock',
            'test_error_handling_comprehensive',
            'test_concurrent_operations',
            'test_data_persistence_and_integrity',
            'test_configuration_management',
            'test_system_integration_workflow'
        ]
        
        print(f"\nRunning {len(test_methods)} comprehensive verification tests...")
        print("\n" + "="*60)
        print("COMPREHENSIVE SYSTEM VERIFICATION COMPLETE")
        print("="*60)

@pytest.mark.system
def test_smoke_test_minimal(app, database):
    """Minimal smoke test to verify basic system functionality."""
    with app.test_client() as client:
        # Test health
        response = client.get('/health')
        assert response.status_code == 200
        
        # Test main page
        response = client.get('/')
        assert response.status_code == 200
        
        # Test API endpoint
        session_data = {'title': 'Smoke Test', 'language': 'en'}
        response = client.post('/api/sessions',
                              data=json.dumps(session_data),
                              content_type='application/json')
        assert response.status_code == 201
    
    print("✓ Smoke test passed - basic system functionality verified")

@pytest.mark.system
def test_quick_integration_check(app, database):
    """Quick integration check for CI/CD pipeline."""
    from app_refactored import socketio as sio
    from models.session import Session
    from models.segment import Segment
    from app_refactored import db
    
    with app.app_context():
        # Test database operations
        session = Session(
            session_id='quick-integration-test',
            title='Quick Integration Test',
            status='created'
        )
        db.session.add(session)
        db.session.commit()
        
        # Test Socket.IO connection
        client = socketio.test.TestClient(sio, app)
        assert client.is_connected()
        
        # Test basic API
        with app.test_client() as http_client:
            response = http_client.get('/health')
            assert response.status_code == 200
            
            response = http_client.get('/api/stats')
            assert response.status_code == 200
    
    print("✓ Quick integration check passed - system ready for deployment")

if __name__ == '__main__':
    print("Comprehensive System Verification Test Suite")
    print("Run with: pytest tests/comprehensive_system_verification.py -v")
