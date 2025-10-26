"""
Test Suite for CROWN+ Event Sequencing Pipeline

Tests the complete post-transcription orchestration pipeline including:
- Event sequencing (8 stages)
- Background task execution
- WebSocket event broadcasting
- Error handling and graceful degradation
- Event ledger tracking
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import models and services
from models import db
from models.session import Session
from models.segment import Segment
from models.event_ledger import EventLedger, EventType, EventStatus
from services.post_transcription_orchestrator import PostTranscriptionOrchestrator
from services.event_ledger_service import EventLedgerService
from services.background_tasks import background_task_manager


class TestCROWNEventSequencing:
    """Test CROWN+ Event Sequencing Pipeline"""
    
    @pytest.fixture(autouse=True)
    def setup(self, app):
        """Set up test environment"""
        self.app = app
        with app.app_context():
            db.create_all()
            
            # Create test session with segments
            self.test_session = Session(
                external_id='test-session-001',
                title='Test Meeting',
                status='active',
                started_at=datetime.utcnow()
            )
            db.session.add(self.test_session)
            db.session.commit()
            
            # Add test segments
            for i in range(3):
                segment = Segment(
                    session_id=self.test_session.id,
                    text=f'Test segment {i+1}',
                    kind='final',
                    avg_confidence=0.9,
                    start_ms=i*1000,
                    end_ms=(i+1)*1000
                )
                db.session.add(segment)
            db.session.commit()
            
            yield
            
            db.session.remove()
            db.drop_all()
    
    def test_event_sequence_order(self, app):
        """Test that events execute in correct CROWN+ sequence"""
        with app.app_context():
            orchestrator = PostTranscriptionOrchestrator()
            
            # Mock services to avoid external API calls
            with patch('services.post_transcription_orchestrator.AnalysisService'):
                with patch('services.post_transcription_orchestrator.AnalyticsService'):
                    with patch('services.post_transcription_orchestrator.socketio'):
                        results = orchestrator.process_session('test-session-001')
            
            # Verify event sequence
            expected_sequence = [
                'transcript_finalized',
                'transcript_refined',
                'insights_generate',
                'analytics_update',
                'tasks_generation',
                'post_transcription_reveal',
                'session_finalized',
                'dashboard_refresh'
            ]
            
            assert 'events_completed' in results
            for event in expected_sequence:
                assert event in results['events_completed'], f"Missing event: {event}"
    
    def test_event_ledger_tracking(self, app):
        """Test that all events are logged to EventLedger"""
        with app.app_context():
            orchestrator = PostTranscriptionOrchestrator()
            initial_count = EventLedger.query.count()
            
            # Mock services
            with patch('services.post_transcription_orchestrator.AnalysisService'):
                with patch('services.post_transcription_orchestrator.AnalyticsService'):
                    with patch('services.post_transcription_orchestrator.socketio'):
                        orchestrator.process_session('test-session-001')
            
            # Check that events were logged
            final_count = EventLedger.query.count()
            assert final_count > initial_count, "No events were logged to EventLedger"
            
            # Verify specific event types were logged
            events = EventLedger.query.filter_by(external_session_id='test-session-001').all()
            event_types = [e.event_type for e in events]
            
            assert EventType.TRANSCRIPT_FINALIZED in event_types
            assert EventType.DASHBOARD_REFRESH in event_types
    
    def test_graceful_degradation(self, app):
        """Test that pipeline continues even if stages fail"""
        with app.app_context():
            orchestrator = PostTranscriptionOrchestrator()
            
            # Mock insights service to fail
            with patch('services.post_transcription_orchestrator.AnalysisService') as mock_analysis:
                mock_analysis.return_value.generate_ai_insights.side_effect = Exception("AI service down")
                
                with patch('services.post_transcription_orchestrator.AnalyticsService'):
                    with patch('services.post_transcription_orchestrator.socketio'):
                        results = orchestrator.process_session('test-session-001')
            
            # Pipeline should still complete other stages
            assert 'transcript_finalized' in results['events_completed']
            assert 'insights_generate' in results['events_failed']
            assert 'session_finalized' in results['events_completed']
    
    def test_success_flag_accuracy(self, app):
        """Test that success flag is only True when no events fail"""
        with app.app_context():
            orchestrator = PostTranscriptionOrchestrator()
            
            # Test 1: All stages succeed
            with patch('services.post_transcription_orchestrator.AnalysisService'):
                with patch('services.post_transcription_orchestrator.AnalyticsService'):
                    with patch('services.post_transcription_orchestrator.socketio'):
                        results = orchestrator.process_session('test-session-001')
            
            assert len(results['events_failed']) == 0
            assert results['success'] is True
            
            # Test 2: One stage fails
            with patch('services.post_transcription_orchestrator.AnalysisService') as mock_analysis:
                mock_analysis.return_value.generate_ai_insights.side_effect = Exception("Failure")
                
                with patch('services.post_transcription_orchestrator.AnalyticsService'):
                    with patch('services.post_transcription_orchestrator.socketio'):
                        results = orchestrator.process_session('test-session-001')
            
            assert len(results['events_failed']) > 0
            assert results['success'] is False
    
    def test_async_background_execution(self, app):
        """Test that process_session_async submits to background task manager"""
        with app.app_context():
            orchestrator = PostTranscriptionOrchestrator()
            
            # Start background task manager if not running
            if not background_task_manager.running:
                background_task_manager.start()
            
            # Mock socketio to avoid actual emissions
            with patch('services.post_transcription_orchestrator.socketio'):
                task_id = orchestrator.process_session_async('test-session-001')
            
            # Verify task was submitted
            assert task_id is not None
            assert task_id.startswith('post_transcription_')
            
            # Verify task exists in background manager
            task_status = orchestrator.get_task_status(task_id)
            assert task_status is not None
            assert task_status['task_id'] == task_id
    
    def test_websocket_emissions(self, app):
        """Test that WebSocket events are emitted at each stage"""
        with app.app_context():
            orchestrator = PostTranscriptionOrchestrator()
            
            emission_log = []
            
            def mock_emit(event_name, data):
                emission_log.append({'event': event_name, 'data': data})
            
            # Mock services and track emissions
            with patch('services.post_transcription_orchestrator.AnalysisService'):
                with patch('services.post_transcription_orchestrator.AnalyticsService'):
                    with patch('services.post_transcription_orchestrator.socketio') as mock_socketio:
                        mock_socketio.emit = mock_emit
                        orchestrator.process_session('test-session-001')
            
            # Verify key events were emitted
            emitted_events = [log['event'] for log in emission_log]
            assert 'transcript_refined' in emitted_events
            assert 'insights_generate' in emitted_events
            assert 'dashboard_refresh' in emitted_events
    
    def test_idempotent_execution(self, app):
        """Test that pipeline can be safely re-run (idempotent)"""
        with app.app_context():
            orchestrator = PostTranscriptionOrchestrator()
            
            # Mock services
            with patch('services.post_transcription_orchestrator.AnalysisService'):
                with patch('services.post_transcription_orchestrator.AnalyticsService'):
                    with patch('services.post_transcription_orchestrator.socketio'):
                        # Run pipeline twice
                        results1 = orchestrator.process_session('test-session-001')
                        results2 = orchestrator.process_session('test-session-001')
            
            # Both runs should succeed
            assert results1['success'] is True
            assert results2['success'] is True
            
            # Event counts may differ, but all events should complete
            assert len(results1['events_completed']) == len(results2['events_completed'])
    
    def test_dashboard_refresh_event(self, app):
        """Test that dashboard_refresh is final event in sequence"""
        with app.app_context():
            orchestrator = PostTranscriptionOrchestrator()
            
            # Mock services
            with patch('services.post_transcription_orchestrator.AnalysisService'):
                with patch('services.post_transcription_orchestrator.AnalyticsService'):
                    with patch('services.post_transcription_orchestrator.socketio'):
                        results = orchestrator.process_session('test-session-001')
            
            # dashboard_refresh should be last completed event
            assert results['events_completed'][-1] == 'dashboard_refresh'
            
            # Verify dashboard_refresh was logged
            events = EventLedger.query.filter_by(
                external_session_id='test-session-001',
                event_type=EventType.DASHBOARD_REFRESH
            ).all()
            assert len(events) > 0
    
    def test_performance_timing(self, app):
        """Test that pipeline completes within expected time"""
        with app.app_context():
            orchestrator = PostTranscriptionOrchestrator()
            
            start_time = time.time()
            
            # Mock services for speed
            with patch('services.post_transcription_orchestrator.AnalysisService'):
                with patch('services.post_transcription_orchestrator.AnalyticsService'):
                    with patch('services.post_transcription_orchestrator.socketio'):
                        results = orchestrator.process_session('test-session-001')
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Pipeline should complete reasonably fast (under 10s with mocks)
            assert duration_ms < 10000, f"Pipeline took too long: {duration_ms}ms"
            
            # Verify timing is reported in results
            assert 'total_duration_ms' in results
            assert results['total_duration_ms'] > 0


class TestEventLedgerService:
    """Test Event Ledger Service"""
    
    @pytest.fixture(autouse=True)
    def setup(self, app):
        """Set up test environment"""
        self.app = app
        with app.app_context():
            db.create_all()
            
            # Create test session
            self.test_session = Session(
                external_id='test-ledger-001',
                title='Ledger Test',
                status='active',
                started_at=datetime.utcnow()
            )
            db.session.add(self.test_session)
            db.session.commit()
            
            self.service = EventLedgerService()
            
            yield
            
            db.session.remove()
            db.drop_all()
    
    def test_log_event(self, app):
        """Test logging an event"""
        with app.app_context():
            event = self.service.log_event(
                event_type=EventType.TRANSCRIPT_FINALIZED,
                session_id=self.test_session.id,
                external_session_id='test-ledger-001',
                payload={'test': 'data'}
            )
            
            assert event is not None
            assert event.event_type == EventType.TRANSCRIPT_FINALIZED
            assert event.status == EventStatus.PENDING
    
    def test_event_lifecycle(self, app):
        """Test complete event lifecycle: pending → in_progress → completed"""
        with app.app_context():
            # Log event
            event = self.service.log_event(
                event_type=EventType.INSIGHTS_GENERATE,
                session_id=self.test_session.id,
                external_session_id='test-ledger-001'
            )
            assert event.status == EventStatus.PENDING
            
            # Start event
            self.service.start_event(event)
            assert event.status == EventStatus.IN_PROGRESS
            assert event.started_at is not None
            
            # Complete event
            self.service.complete_event(event, result={'insights': []})
            assert event.status == EventStatus.COMPLETED
            assert event.completed_at is not None
    
    def test_event_failure(self, app):
        """Test event failure handling"""
        with app.app_context():
            event = self.service.log_event(
                event_type=EventType.ANALYTICS_UPDATE,
                session_id=self.test_session.id,
                external_session_id='test-ledger-001'
            )
            
            self.service.fail_event(event, "Test error message")
            
            assert event.status == EventStatus.FAILED
            assert event.error_message == "Test error message"
    
    def test_get_session_events(self, app):
        """Test retrieving all events for a session"""
        with app.app_context():
            # Create multiple events
            for event_type in [EventType.TRANSCRIPT_FINALIZED, EventType.TRANSCRIPT_REFINED]:
                self.service.log_event(
                    event_type=event_type,
                    session_id=self.test_session.id,
                    external_session_id='test-ledger-001'
                )
            
            # Retrieve events
            events = self.service.get_session_events('test-ledger-001')
            assert len(events) >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
