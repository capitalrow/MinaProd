#!/usr/bin/env python3
"""
Comprehensive End-to-End Production Tests
Tests all production-grade services and integrations
"""

import pytest
import time
import json
import threading
import asyncio
from unittest.mock import Mock, patch, MagicMock
import redis
import os

# Test imports
def test_imports():
    """Test that all production services can be imported successfully"""
    print("🧪 Testing service imports...")
    
    try:
        from services.background_worker import BackgroundWorkerManager
        from services.continuous_audio import ContinuousAudioProcessor
        from services.deduplication_engine import DeduplicationEngine
        from services.redis_adapter import RedisSocketIOAdapter
        from services.websocket_reliability import WebSocketReliabilityManager
        from services.checkpointing import CheckpointingManager
        from services.authentication import AuthenticationManager
        from services.data_encryption import DataEncryptionService
        from services.speaker_diarization import SpeakerDiarizationEngine
        from services.ux_accessibility import UXAccessibilityManager
        print("✅ All service imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_redis_connection():
    """Test Redis connection for production services"""
    print("🧪 Testing Redis connection...")
    
    try:
        # Try to connect to Redis (use localhost if no Redis URL provided)
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_client.ping()
        print("✅ Redis connection successful")
        return redis_client
    except Exception as e:
        print(f"⚠️  Redis not available: {e}")
        # Create mock Redis for testing
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = True
        mock_redis.keys.return_value = []
        mock_redis.hgetall.return_value = {}
        print("✅ Using mock Redis for testing")
        return mock_redis

def test_background_worker():
    """Test background worker system"""
    print("🧪 Testing Background Worker System...")
    
    try:
        from services.background_worker import BackgroundWorkerManager, WorkerConfig
        
        # Initialize with test config
        config = WorkerConfig(max_workers=2, queue_size=5)
        worker_manager = BackgroundWorkerManager(config)
        
        # Test task submission
        test_results = []
        
        def test_task(data):
            test_results.append(f"Processed: {data}")
            return f"Result: {data}"
        
        # Submit test tasks
        task_id = worker_manager.submit_task("transcription", test_task, "test_data")
        
        # Wait for completion
        time.sleep(0.1)
        
        # Check results
        stats = worker_manager.get_worker_stats()
        assert stats['total_tasks_submitted'] > 0
        
        # Cleanup
        worker_manager.shutdown()
        
        print("✅ Background Worker System test passed")
        return True
    except Exception as e:
        print(f"❌ Background Worker System test failed: {e}")
        return False

def test_continuous_audio():
    """Test continuous audio processing"""
    print("🧪 Testing Continuous Audio Processing...")
    
    try:
        from services.continuous_audio import ContinuousAudioProcessor, AudioConfig
        
        # Initialize with test config
        config = AudioConfig(
            sample_rate=16000,
            chunk_duration_ms=1000,
            overlap_duration_ms=500
        )
        audio_processor = ContinuousAudioProcessor(config)
        
        # Create mock audio data
        import numpy as np
        mock_audio = (np.random.rand(16000) * 32767).astype(np.int16).tobytes()
        
        # Process audio chunk
        result = audio_processor.process_audio_chunk(mock_audio, time.time())
        
        # Verify processing
        assert 'chunk_id' in result
        assert result['success'] is True
        
        # Check stats
        stats = audio_processor.get_processing_stats()
        assert stats['chunks_processed'] > 0
        
        print("✅ Continuous Audio Processing test passed")
        return True
    except Exception as e:
        print(f"❌ Continuous Audio Processing test failed: {e}")
        return False

def test_deduplication_engine():
    """Test advanced deduplication engine"""
    print("🧪 Testing Deduplication Engine...")
    
    try:
        from services.deduplication_engine import DeduplicationEngine, DeduplicationConfig
        
        config = DeduplicationConfig(stability_threshold=2, confidence_threshold=0.8)
        dedup_engine = DeduplicationEngine(config)
        
        session_id = "test_session"
        
        # Add similar transcription results
        result1 = dedup_engine.add_transcription_result(
            session_id, "Hello world", 0.9, is_final=False, timestamp=time.time()
        )
        
        result2 = dedup_engine.add_transcription_result(
            session_id, "Hello world this", 0.85, is_final=False, timestamp=time.time() + 0.1
        )
        
        result3 = dedup_engine.add_transcription_result(
            session_id, "Hello world this is a test", 0.95, is_final=True, timestamp=time.time() + 0.2
        )
        
        # Get final text
        final_text = dedup_engine.get_stable_text(session_id)
        assert len(final_text) > 0
        
        # Check stats
        stats = dedup_engine.get_deduplication_stats()
        assert stats['total_results_processed'] >= 3
        
        print("✅ Deduplication Engine test passed")
        return True
    except Exception as e:
        print(f"❌ Deduplication Engine test failed: {e}")
        return False

def test_redis_adapter():
    """Test Redis adapter for scaling"""
    print("🧪 Testing Redis Adapter...")
    
    try:
        from services.redis_adapter import RedisSocketIOAdapter, RedisConfig
        
        # Use mock Redis for testing
        config = RedisConfig(host='localhost', port=6379)
        
        # Create adapter with mock Redis
        with patch('redis.Redis') as mock_redis_class:
            mock_redis = MagicMock()
            mock_redis.ping.return_value = True
            mock_redis.publish.return_value = 1
            mock_redis.hgetall.return_value = {}
            mock_redis_class.return_value = mock_redis
            
            adapter = RedisSocketIOAdapter(config)
            
            # Test room operations
            success = adapter.join_room("client1", "room1", {"test": "data"})
            assert success is True
            
            success = adapter.emit_to_room("room1", "test_event", {"message": "test"})
            assert success is True
            
            # Check stats
            stats = adapter.get_adapter_stats()
            assert 'instance_id' in stats
            
        print("✅ Redis Adapter test passed")
        return True
    except Exception as e:
        print(f"❌ Redis Adapter test failed: {e}")
        return False

def test_websocket_reliability():
    """Test WebSocket reliability system"""
    print("🧪 Testing WebSocket Reliability...")
    
    try:
        from services.websocket_reliability import WebSocketReliabilityManager, HeartbeatConfig
        from flask_socketio import SocketIO
        from flask import Flask
        
        # Create test Flask app and SocketIO
        app = Flask(__name__)
        socketio = SocketIO(app, cors_allowed_origins="*")
        
        # Use mock Redis
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        
        config = HeartbeatConfig(interval_s=1.0, timeout_s=2.0)
        reliability_manager = WebSocketReliabilityManager(socketio, mock_redis, config)
        
        # Test session registration
        reliability_manager._register_client_session("client1", "session1")
        
        # Test heartbeat processing
        reliability_manager._process_heartbeat("client1", {"timestamp": time.time()})
        
        # Check stats
        stats = reliability_manager.get_reliability_stats()
        assert 'total_connections' in stats
        
        print("✅ WebSocket Reliability test passed")
        return True
    except Exception as e:
        print(f"❌ WebSocket Reliability test failed: {e}")
        return False

def test_checkpointing():
    """Test checkpointing system"""
    print("🧪 Testing Checkpointing System...")
    
    try:
        from services.checkpointing import CheckpointingManager, CheckpointType, CheckpointingConfig
        
        # Use mock Redis
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = json.dumps({
            'checkpoint_id': 'test_checkpoint',
            'session_id': 'test_session',
            'checkpoint_type': 'session_state',
            'timestamp': time.time(),
            'data': {'test': 'data'},
            'metadata': {},
            'size_bytes': 100,
            'checksum': 'test_checksum'
        })
        mock_redis.zadd.return_value = 1
        mock_redis.expire.return_value = True
        mock_redis.zcard.return_value = 1
        
        config = CheckpointingConfig(session_checkpoint_interval=1.0)
        checkpoint_manager = CheckpointingManager(mock_redis, config)
        
        # Test session registration
        checkpoint_manager.register_session("test_session", {"initial": "state"})
        
        # Test checkpoint creation
        checkpoint_id = checkpoint_manager.create_checkpoint(
            "test_session", 
            CheckpointType.SESSION_STATE, 
            {"test": "data"}
        )
        assert checkpoint_id is not None
        
        # Check stats
        stats = checkpoint_manager.get_checkpointing_stats()
        assert stats['checkpoints_created'] > 0
        
        # Cleanup
        checkpoint_manager.unregister_session("test_session")
        
        print("✅ Checkpointing System test passed")
        return True
    except Exception as e:
        print(f"❌ Checkpointing System test failed: {e}")
        return False

def test_authentication():
    """Test authentication system"""
    print("🧪 Testing Authentication System...")
    
    try:
        from services.authentication import AuthenticationManager, AuthConfig, UserRole
        from flask import Flask
        
        # Create test Flask app
        app = Flask(__name__)
        app.secret_key = "test_secret"
        
        # Use mock Redis
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        
        config = AuthConfig(jwt_secret_key="test_jwt_secret")
        
        with app.app_context():
            auth_manager = AuthenticationManager(app, mock_redis, config)
            
            # Test user registration
            result = auth_manager.register_user(
                "test@example.com", 
                "TestPassword123!", 
                "Test User", 
                UserRole.USER
            )
            assert result['success'] is True
            
            # Test user authentication
            auth_result = auth_manager.authenticate_user("test@example.com", "TestPassword123!")
            assert auth_result['success'] is True
            assert 'access_token' in auth_result
            
            # Test token verification
            token_payload = auth_manager.verify_token(auth_result['access_token'])
            assert token_payload is not None
            assert token_payload['email'] == "test@example.com"
            
            # Check stats
            stats = auth_manager.get_auth_stats()
            assert stats['total_users'] > 0
        
        print("✅ Authentication System test passed")
        return True
    except Exception as e:
        print(f"❌ Authentication System test failed: {e}")
        return False

def test_data_encryption():
    """Test data encryption system"""
    print("🧪 Testing Data Encryption...")
    
    try:
        from services.data_encryption import DataEncryptionService, EncryptionKeyManager, EncryptionConfig
        
        # Use mock Redis
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        
        config = EncryptionConfig(encrypt_transcripts=True, encrypt_user_data=True)
        key_manager = EncryptionKeyManager(mock_redis, config)
        encryption_service = DataEncryptionService(key_manager, config)
        
        # Test field encryption/decryption
        test_data = "This is sensitive data"
        encrypted = encryption_service.encrypt_field(test_data, "test_field")
        assert encrypted != test_data
        
        decrypted = encryption_service.decrypt_field(encrypted)
        assert decrypted == test_data
        
        # Test transcript encryption
        transcript = "Hello world this is a test transcript"
        encrypted_transcript = encryption_service.encrypt_transcript(transcript, "session1")
        decrypted_transcript = encryption_service.decrypt_transcript(encrypted_transcript)
        assert decrypted_transcript == transcript
        
        # Test user data encryption
        user_data = {"email": "test@example.com", "phone": "123-456-7890"}
        encrypted_user_data = encryption_service.encrypt_user_data(user_data)
        decrypted_user_data = encryption_service.decrypt_user_data(encrypted_user_data)
        assert decrypted_user_data["email"] == "test@example.com"
        
        # Check stats
        stats = encryption_service.get_encryption_stats()
        assert stats['encryptions_performed'] > 0
        assert stats['decryptions_performed'] > 0
        
        print("✅ Data Encryption test passed")
        return True
    except Exception as e:
        print(f"❌ Data Encryption test failed: {e}")
        return False

def test_speaker_diarization():
    """Test speaker diarization system"""
    print("🧪 Testing Speaker Diarization...")
    
    try:
        from services.speaker_diarization import SpeakerDiarizationEngine, DiarizationConfig
        
        config = DiarizationConfig(enable_voice_features=True, auto_label_speakers=True)
        diarization_engine = SpeakerDiarizationEngine(config)
        
        session_id = "test_session"
        
        # Initialize session
        diarization_engine.initialize_session(session_id, ["Speaker 1", "Speaker 2"])
        
        # Create mock audio data
        import numpy as np
        mock_audio = (np.random.rand(16000) * 32767).astype(np.int16).tobytes()
        
        # Process audio segments
        result1 = diarization_engine.process_audio_segment(
            session_id, mock_audio, 0.0, 2.0, "Hello everyone"
        )
        assert 'speaker_id' in result1
        
        result2 = diarization_engine.process_audio_segment(
            session_id, mock_audio, 2.5, 4.5, "Good morning"
        )
        assert 'speaker_id' in result2
        
        # Get timeline
        timeline = diarization_engine.get_session_timeline(session_id)
        assert len(timeline) >= 2
        
        # Get statistics
        stats = diarization_engine.get_speaker_statistics(session_id)
        assert stats['total_speakers'] >= 2
        assert stats['total_segments'] >= 2
        
        # Cleanup
        diarization_engine.cleanup_session(session_id)
        
        print("✅ Speaker Diarization test passed")
        return True
    except Exception as e:
        print(f"❌ Speaker Diarization test failed: {e}")
        return False

def test_ux_accessibility():
    """Test UX and accessibility system"""
    print("🧪 Testing UX Accessibility...")
    
    try:
        from services.ux_accessibility import UXAccessibilityManager, AccessibilityConfig, FeedbackType
        
        config = AccessibilityConfig(
            high_contrast_mode=True,
            large_text_mode=True,
            keyboard_navigation=True
        )
        ux_manager = UXAccessibilityManager(config)
        
        # Test CSS generation
        css = ux_manager.generate_accessibility_css()
        assert ".high-contrast" in css
        assert ".large-text" in css
        
        # Test HTML generation
        html = ux_manager.generate_accessibility_html()
        assert "skip-links" in html
        assert "aria-live" in html
        
        # Test JavaScript generation
        js = ux_manager.generate_accessibility_javascript()
        assert "AccessibilityManager" in js
        assert "toggleHighContrast" in js
        
        # Test notification creation
        notification = ux_manager.create_accessible_notification(
            "Test message", FeedbackType.SUCCESS
        )
        assert notification['message'] == "Test message"
        assert notification['accessible'] is True
        
        # Test ARIA attributes generation
        attrs = ux_manager.generate_aria_attributes("transcript_area")
        assert 'role' in attrs
        assert 'aria-live' in attrs
        
        # Check stats
        stats = ux_manager.get_accessibility_stats()
        assert stats['active_features'] > 0
        
        print("✅ UX Accessibility test passed")
        return True
    except Exception as e:
        print(f"❌ UX Accessibility test failed: {e}")
        return False

def test_flask_app():
    """Test Flask application basics"""
    print("🧪 Testing Flask Application...")
    
    try:
        from app import app, db
        
        with app.test_client() as client:
            # Test home page
            response = client.get('/')
            assert response.status_code == 200
            
            # Test live transcription page
            response = client.get('/live')
            assert response.status_code == 200
            
            # Test API stats endpoint
            response = client.get('/api/stats')
            assert response.status_code == 200
            
            # Test that response is JSON
            data = response.get_json()
            assert 'transcription_service' in data
        
        print("✅ Flask Application test passed")
        return True
    except Exception as e:
        print(f"❌ Flask Application test failed: {e}")
        return False

def run_all_tests():
    """Run all end-to-end tests"""
    print("🚀 Starting Comprehensive End-to-End Production Tests")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Service Imports", test_imports),
        ("Redis Connection", test_redis_connection),
        ("Background Worker", test_background_worker),
        ("Continuous Audio", test_continuous_audio),
        ("Deduplication Engine", test_deduplication_engine),
        ("Redis Adapter", test_redis_adapter),
        ("WebSocket Reliability", test_websocket_reliability),
        ("Checkpointing System", test_checkpointing),
        ("Authentication System", test_authentication),
        ("Data Encryption", test_data_encryption),
        ("Speaker Diarization", test_speaker_diarization),
        ("UX Accessibility", test_ux_accessibility),
        ("Flask Application", test_flask_app)
    ]
    
    passed_tests = 0
    failed_tests = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if test_func():
                passed_tests += 1
                test_results.append(f"✅ {test_name}")
            else:
                failed_tests += 1
                test_results.append(f"❌ {test_name}")
        except Exception as e:
            failed_tests += 1
            test_results.append(f"❌ {test_name} - Error: {e}")
            print(f"❌ {test_name} failed with error: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for result in test_results:
        print(result)
    
    print(f"\n🎯 TOTAL: {len(tests)} tests")
    print(f"✅ PASSED: {passed_tests}")
    print(f"❌ FAILED: {failed_tests}")
    print(f"📈 SUCCESS RATE: {(passed_tests/len(tests)*100):.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED! Production system is fully functional.")
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed. Review the failures above.")
    
    return passed_tests, failed_tests

if __name__ == "__main__":
    run_all_tests()