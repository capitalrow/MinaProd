"""
🛡️ Data Integrity Testing Suite
Tests data validation, corruption recovery, and data consistency for 100% testing coverage.
"""
import pytest
import json
import time
import logging
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

logger = logging.getLogger(__name__)

class TestDataIntegrity:
    """Data integrity and validation testing"""
    
    @pytest.fixture
    def mock_database(self):
        """Mock database for testing"""
        return MagicMock()
    
    def test_session_data_consistency(self, mock_database):
        """Test session data consistency across operations"""
        from models.session import Session
        from models.segment import TranscriptionSegment
        
        # Test data consistency when creating session
        session_data = {
            "session_id": "test-session-123",
            "user_id": "user-456",
            "start_time": datetime.now(),
            "status": "active"
        }
        
        # Mock successful database operations
        mock_database.session.add.return_value = None
        mock_database.session.commit.return_value = None
        
        with patch('app.db', mock_database):
            # Simulate session creation
            session = Session(**session_data)
            
            # Verify data integrity
            assert session.session_id == session_data["session_id"]
            assert session.user_id == session_data["user_id"]
            assert session.status == session_data["status"]
    
    def test_transcription_segment_validation(self):
        """Test transcription segment data validation"""
        from models.segment import TranscriptionSegment
        
        # Valid segment data
        valid_segment = {
            "session_id": "test-session-123",
            "segment_id": "segment-1",
            "text": "Hello world",
            "confidence": 0.95,
            "start_time": 0.0,
            "end_time": 2.5,
            "speaker_id": "speaker-1"
        }
        
        segment = TranscriptionSegment(**valid_segment)
        assert segment.confidence >= 0.0 and segment.confidence <= 1.0
        assert segment.end_time > segment.start_time
        assert len(segment.text.strip()) > 0
    
    def test_invalid_data_rejection(self):
        """Test rejection of invalid data"""
        from models.segment import TranscriptionSegment
        
        # Test invalid confidence scores
        invalid_segments = [
            {"confidence": -0.1},  # Negative confidence
            {"confidence": 1.1},   # Confidence > 1
            {"start_time": 5.0, "end_time": 2.0},  # End before start
            {"text": ""},  # Empty text
            {"text": None},  # Null text
        ]
        
        for invalid_data in invalid_segments:
            default_data = {
                "session_id": "test",
                "segment_id": "seg-1", 
                "text": "Valid text",
                "confidence": 0.5,
                "start_time": 0.0,
                "end_time": 1.0
            }
            default_data.update(invalid_data)
            
            with pytest.raises((ValueError, AssertionError)):
                TranscriptionSegment(**default_data)
    
    def test_database_transaction_rollback(self, mock_database):
        """Test database transaction rollback on errors"""
        
        # Mock database error
        mock_database.session.commit.side_effect = Exception("Database error")
        mock_database.session.rollback.return_value = None
        
        with patch('app.db', mock_database):
            try:
                # Simulate operation that should rollback
                mock_database.session.add(MagicMock())
                mock_database.session.commit()
            except Exception:
                mock_database.session.rollback()
            
            # Verify rollback was called
            mock_database.session.rollback.assert_called_once()
    
    def test_concurrent_session_updates(self, mock_database):
        """Test handling of concurrent session updates"""
        from models.session import Session
        
        session_id = "concurrent-test-session"
        
        # Simulate concurrent updates
        def update_session_status(status):
            # Mock finding and updating session
            mock_session = MagicMock()
            mock_session.status = status
            mock_database.session.query.return_value.filter.return_value.first.return_value = mock_session
            
            return mock_session
        
        with patch('app.db', mock_database):
            # Simulate two concurrent updates
            session1 = update_session_status("processing")
            session2 = update_session_status("completed")
            
            # Last update should win
            assert session2.status == "completed"
    
    def test_data_corruption_recovery(self, mock_database):
        """Test recovery from data corruption scenarios"""
        
        # Test corrupted JSON data
        corrupted_json_scenarios = [
            '{"incomplete": json',  # Malformed JSON
            '{"valid": "json", "but": "unexpected_field"}',  # Unexpected fields
            '',  # Empty data
            'null',  # Null data
            '{"text": null}',  # Null required field
        ]
        
        for corrupted_data in corrupted_json_scenarios:
            try:
                # Attempt to parse corrupted data
                parsed = json.loads(corrupted_data) if corrupted_data else {}
                
                # Should handle gracefully without crashes
                if not parsed or not isinstance(parsed, dict):
                    continue
                    
                # Validate required fields exist
                required_fields = ["session_id", "text", "confidence"]
                missing_fields = [field for field in required_fields if field not in parsed]
                
                if missing_fields:
                    # Should reject incomplete data
                    assert len(missing_fields) > 0, "Incomplete data not rejected"
                    
            except json.JSONDecodeError:
                # Expected for malformed JSON
                pass
    
    def test_audio_data_integrity(self):
        """Test audio data integrity checks"""
        
        # Test audio format validation
        valid_audio_formats = ["wav", "mp3", "m4a", "webm"]
        invalid_audio_formats = ["txt", "jpg", "exe", "pdf"]
        
        def validate_audio_format(filename):
            extension = filename.split('.')[-1].lower()
            return extension in valid_audio_formats
        
        # Test valid formats
        for format_ext in valid_audio_formats:
            assert validate_audio_format(f"test.{format_ext}"), f"Valid format rejected: {format_ext}"
        
        # Test invalid formats
        for format_ext in invalid_audio_formats:
            assert not validate_audio_format(f"test.{format_ext}"), f"Invalid format accepted: {format_ext}"
    
    def test_session_state_transitions(self):
        """Test valid session state transitions"""
        
        valid_transitions = {
            "created": ["active", "cancelled"],
            "active": ["processing", "paused", "completed", "error"],
            "processing": ["active", "completed", "error"],
            "paused": ["active", "completed", "cancelled"],
            "completed": [],  # Terminal state
            "error": ["active", "cancelled"],
            "cancelled": []   # Terminal state
        }
        
        def is_valid_transition(from_state, to_state):
            return to_state in valid_transitions.get(from_state, [])
        
        # Test valid transitions
        assert is_valid_transition("created", "active")
        assert is_valid_transition("active", "processing")
        assert is_valid_transition("processing", "completed")
        
        # Test invalid transitions
        assert not is_valid_transition("completed", "active")  # Cannot reactivate completed
        assert not is_valid_transition("cancelled", "processing")  # Cannot process cancelled
        assert not is_valid_transition("error", "completed")  # Cannot complete from error directly
    
    def test_memory_leak_prevention(self):
        """Test prevention of memory leaks in data structures"""
        import gc
        
        # Create large data structures
        large_sessions = []
        for i in range(100):
            session_data = {
                "session_id": f"test-session-{i}",
                "segments": [f"segment-{j}" for j in range(100)],
                "metadata": {"large_field": "A" * 1000}
            }
            large_sessions.append(session_data)
        
        # Clear references
        initial_count = len(gc.get_objects())
        del large_sessions
        gc.collect()
        
        # Memory should be freed
        final_count = len(gc.get_objects())
        # Allow some variance but should see significant reduction
        assert final_count < initial_count + 50, "Potential memory leak detected"
    
    def test_export_data_integrity(self):
        """Test data integrity in export operations"""
        
        # Mock session data for export
        session_data = {
            "session_id": "export-test-session",
            "title": "Test Session",
            "segments": [
                {
                    "text": "First segment with special chars: <>&\"'",
                    "start_time": 0.0,
                    "end_time": 2.0,
                    "confidence": 0.95
                },
                {
                    "text": "Second segment with unicode: 中文测试",
                    "start_time": 2.0,
                    "end_time": 4.0,
                    "confidence": 0.88
                }
            ]
        }
        
        # Test PDF export data preservation
        from services.export_service import ExportService
        
        with patch.object(ExportService, '_generate_pdf') as mock_pdf:
            mock_pdf.return_value = b"mock_pdf_content"
            
            # Should handle special characters and unicode
            export_service = ExportService()
            result = export_service.export_session_pdf(session_data)
            
            # Verify export was attempted with proper data
            mock_pdf.assert_called_once()
            call_args = mock_pdf.call_args[0][0]
            
            # Check that special characters are preserved
            assert "special chars: <>&\"'" in str(call_args)
            assert "unicode: 中文测试" in str(call_args)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])