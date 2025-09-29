"""
Sharing Routes for M4 functionality.
Handles session sharing with view-only links and exports.
"""

import os
from flask import Blueprint, request, jsonify, render_template, abort, url_for
from sqlalchemy.orm import Session as DBSession
from models import db
from services.share_service import ShareService
from config import Config


sharing_bp = Blueprint('sharing', __name__)


@sharing_bp.route('/sessions/<int:session_id>/share', methods=['POST'])
def create_share_link(session_id: int):
    """Create a new share link for a session."""
    try:
        share_service = ShareService(db.session())
        
        # Get expiry days from request or use default
        data = request.get_json() or {}
        days = data.get('days', 7)
        
        # Create share link
        token = share_service.create_share_link(session_id, days)
        
        # Build full URL
        base_url = os.getenv('SHARE_BASE_URL', 'http://localhost:5000')
        share_url = f"{base_url}/share/{token}"
        
        return jsonify({
            'success': True,
            'token': token,
            'url': share_url,
            'expires_in_days': days
        }), 201
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to create share link'}), 500


@sharing_bp.route('/share/<string:token>')
def view_shared_session(token: str):
    """View a shared session via token."""
    try:
        share_service = ShareService(db.session())
        
        # Validate token and get session
        session = share_service.validate_share_token(token)
        
        if not session:
            return render_template('share_expired.html'), 403
        
        # Get session summary if available
        summary = None
        try:
            from models.summary import Summary
            from sqlalchemy import select
            stmt = select(Summary).where(Summary.session_id == session.id)
            summary = db_session.scalars(stmt).first()
        except ImportError:
            # Summary model not available
            pass
        
        # Get session segments for transcript
        segments = session.segments or []
        
        return render_template('share_session.html', 
                             session=session,
                             summary=summary,
                             segments=segments,
                             token=token)
        
    except Exception as e:
        return render_template('share_expired.html'), 500


@sharing_bp.route('/sessions/<int:session_id>/share/<string:token>', methods=['DELETE'])
def deactivate_share_link(session_id: int, token: str):
    """Deactivate a specific share link."""
    try:
        share_service = ShareService(db.session())
        
        success = share_service.deactivate_share_link(session_id, token)
        
        if success:
            return jsonify({'success': True, 'message': 'Share link deactivated'})
        else:
            return jsonify({'success': False, 'error': 'Share link not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to deactivate link'}), 500


@sharing_bp.route('/sessions/<int:session_id>/shares')
def list_share_links(session_id: int):
    """List active share links for a session."""
    try:
        share_service = ShareService(db.session())
        
        links = share_service.get_active_share_links(session_id)
        
        base_url = os.getenv('SHARE_BASE_URL', 'http://localhost:5000')
        
        return jsonify({
            'success': True,
            'links': [
                {
                    'token': link.token,
                    'url': f"{base_url}/share/{link.token}",
                    'created_at': link.created_at.isoformat(),
                    'expires_at': link.expires_at.isoformat() if link.expires_at else None,
                    'is_expired': link.is_expired
                }
                for link in links
            ]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to list share links'}), 500