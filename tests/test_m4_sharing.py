"""
Test suite for M4 Sharing functionality.
Verifies share link creation, validation, and export features.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from services.share_service import ShareService
from services.export_service import ExportService
from models.shared_link import SharedLink
from models.session import Session


class TestShareService:
    """Test the ShareService functionality."""
    
    def test_create_share_link(self):
        """Test creating a share link."""
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_session.get.return_value = MagicMock(spec=Session)
        
        share_service = ShareService(mock_session)
        
        with patch('secrets.token_urlsafe', return_value='test-token'):
            token = share_service.create_share_link(session_id=1, days=7)
            
        assert token == 'test-token'
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_validate_share_token_valid(self):
        """Test validating a valid share token."""
        mock_db = MagicMock()
        mock_session = MagicMock()
        
        # Mock a valid shared link
        mock_link = MagicMock(spec=SharedLink)
        mock_link.session_id = 1
        mock_link.is_active = True
        mock_link.expires_at = datetime.utcnow() + timedelta(days=1)
        
        mock_session.scalars.return_value.first.return_value = mock_link
        
        share_service = ShareService(mock_session)
        result = share_service.validate_share_token('valid-token')
        
        assert result == 1  # session_id
    
    def test_validate_share_token_expired(self):
        """Test validating an expired share token."""
        mock_db = MagicMock()
        mock_session = MagicMock()
        
        # Mock an expired shared link
        mock_link = MagicMock(spec=SharedLink)
        mock_link.session_id = 1
        mock_link.is_active = True
        mock_link.expires_at = datetime.utcnow() - timedelta(days=1)
        
        mock_session.scalars.return_value.first.return_value = mock_link
        
        share_service = ShareService(mock_session)
        result = share_service.validate_share_token('expired-token')
        
        assert result is None


class TestExportService:
    """Test the ExportService functionality."""
    
    @patch('services.export_service.SessionService.get_session_detail')
    def test_session_to_markdown(self, mock_get_detail):
        """Test exporting session to markdown."""
        # Mock session detail
        mock_get_detail.return_value = {
            'session': {
                'id': 1,
                'external_id': 'test-session-123',
                'title': 'Test Meeting',
                'status': 'finalized',
                'started_at': '2025-08-25T10:00:00Z',
                'locale': 'en'
            },
            'segments': [
                {
                    'text': 'Hello, this is a test.',
                    'start_time': '2025-08-25T10:00:00Z',
                    'confidence_score': 0.95
                }
            ]
        }
        
        markdown = ExportService.session_to_markdown(1)
        
        assert '# Test Meeting' in markdown
        assert 'Hello, this is a test.' in markdown
        assert 'test-session-123' in markdown
    
    @patch('services.export_service.SessionService.get_session_detail')
    def test_session_to_docx(self, mock_get_detail):
        """Test exporting session to DOCX."""
        # Mock session detail
        mock_get_detail.return_value = {
            'session': {
                'id': 1,
                'external_id': 'test-session-123',
                'title': 'Test Meeting',
                'status': 'finalized',
                'started_at': '2025-08-25T10:00:00Z',
                'locale': 'en'
            },
            'segments': [
                {
                    'text': 'Hello, this is a test.',
                    'start_time': '10:00:00',
                    'confidence_score': 0.95
                }
            ]
        }
        
        docx_buffer = ExportService.session_to_docx(1)
        
        assert docx_buffer is not None
        assert hasattr(docx_buffer, 'read')  # It's a BytesIO buffer
    
    @patch('services.export_service.SessionService.get_session_detail')
    def test_session_to_pdf(self, mock_get_detail):
        """Test exporting session to PDF."""
        # Mock session detail
        mock_get_detail.return_value = {
            'session': {
                'id': 1,
                'external_id': 'test-session-123',
                'title': 'Test Meeting',
                'status': 'finalized',
                'started_at': '2025-08-25T10:00:00Z',
                'locale': 'en'
            },
            'segments': [
                {
                    'text': 'Hello, this is a test.',
                    'start_time': '10:00:00',
                    'confidence_score': 0.95
                }
            ]
        }
        
        pdf_buffer = ExportService.session_to_pdf(1)
        
        assert pdf_buffer is not None
        assert hasattr(pdf_buffer, 'read')  # It's a BytesIO buffer
    
    def test_get_export_filename(self):
        """Test generating export filenames."""
        with patch('services.export_service.SessionService.get_session_by_id') as mock_get:
            mock_session = MagicMock()
            mock_session.title = 'Test Meeting 2025'
            mock_get.return_value = mock_session
            
            filename = ExportService.get_export_filename(1, 'docx')
            
            assert filename.startswith('mina-')
            assert filename.endswith('-1.docx')
            assert 'test-meeting' in filename.lower()


if __name__ == '__main__':
    pytest.main([__file__])