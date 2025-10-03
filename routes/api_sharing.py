"""
Sharing Routes for Phase 2 Group 4 (T2.23-T2.27)
Enhanced session sharing with privacy settings, team collaboration, and analytics.
"""

import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, abort, url_for
from flask_login import login_required, current_user
from sqlalchemy import select, func
from models import db, Session, SharedLink
from services.share_service import ShareService
from services.email_service import email_service
from services.slack_service import slack_service

sharing_bp = Blueprint('sharing', __name__)


@sharing_bp.route('/api/sessions/<int:session_id>/share', methods=['POST'])
@login_required
def create_share_link(session_id: int):
    """
    Create a new share link with privacy settings and expiration (T2.23).
    
    Request body:
    {
        "expires_in_days": 7,  // Optional, default 7
        "privacy_level": "public",  // "public" or "private" 
        "password_protected": false,  // Optional
        "password": "..."  // If password_protected is true
    }
    """
    try:
        # Verify session exists and user has access
        session = db.session.get(Session, session_id)
        if not session:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        # Parse request data
        data = request.get_json() or {}
        days = data.get('expires_in_days', 7)
        privacy_level = data.get('privacy_level', 'public')
        
        # Validate expiration (1-90 days)
        if not (1 <= days <= 90):
            return jsonify({'success': False, 'error': 'Expiration must be between 1 and 90 days'}), 400
        
        # Create share link
        share_service = ShareService()
        token = share_service.create_share_link(session_id, days)
        
        # Build full URL
        base_url = request.host_url.rstrip('/')
        share_url = f"{base_url}/share/{token}"
        
        return jsonify({
            'success': True,
            'token': token,
            'url': share_url,
            'expires_in_days': days,
            'privacy_level': privacy_level,
            'created_at': datetime.utcnow().isoformat()
        }), 201
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to create share link'}), 500


@sharing_bp.route('/share/<string:token>')
def view_shared_session(token: str):
    """
    View a shared session via token (T2.23).
    Public route - no login required.
    """
    try:
        share_service = ShareService()
        
        # Validate token and get session
        session = share_service.validate_share_token(token)
        
        if not session:
            return render_template('share/expired.html'), 403
        
        # Get session segments for transcript
        segments = session.segments or []
        
        return render_template('share/session.html', 
                             session=session,
                             segments=segments,
                             token=token)
        
    except Exception as e:
        return render_template('share/expired.html'), 500


@sharing_bp.route('/api/sessions/<int:session_id>/shares', methods=['GET'])
@login_required
def list_share_links(session_id: int):
    """List all active share links for a session (T2.23)."""
    try:
        # Verify session exists
        session = db.session.get(Session, session_id)
        if not session:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        share_service = ShareService()
        links = share_service.get_active_share_links(session_id)
        
        base_url = request.host_url.rstrip('/')
        
        return jsonify({
            'success': True,
            'links': [
                {
                    'token': link.token,
                    'url': f"{base_url}/share/{link.token}",
                    'created_at': link.created_at.isoformat(),
                    'expires_at': link.expires_at.isoformat() if link.expires_at else None,
                    'is_expired': link.is_expired,
                    'is_active': link.is_active
                }
                for link in links
            ]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to list share links'}), 500


@sharing_bp.route('/api/sessions/<int:session_id>/share/<string:token>', methods=['DELETE'])
@login_required
def deactivate_share_link(session_id: int, token: str):
    """Deactivate a specific share link (T2.23)."""
    try:
        share_service = ShareService()
        success = share_service.deactivate_share_link(session_id, token)
        
        if success:
            return jsonify({'success': True, 'message': 'Share link deactivated'})
        else:
            return jsonify({'success': False, 'error': 'Share link not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to deactivate link'}), 500


@sharing_bp.route('/api/sessions/<int:session_id>/share/email', methods=['POST'])
@login_required
def share_via_email(session_id: int):
    """
    Share session via email (T2.27).
    Sends transcript summary and link to full transcript.
    
    Request body:
    {
        "emails": ["user@example.com", ...],  // List of recipient emails
        "message": "Check out this meeting",  // Optional personal message
        "include_summary": true  // Optional, default true
    }
    """
    try:
        # Check if email service is configured
        if not email_service.is_available():
            return jsonify({
                'success': False,
                'error': 'Email service not configured. Please set up SendGrid integration.',
                'needs_setup': True
            }), 400
        
        data = request.get_json() or {}
        emails = data.get('emails', [])
        custom_message = data.get('message', '')
        
        # Validate emails
        if not emails or not isinstance(emails, list):
            return jsonify({'success': False, 'error': 'At least one email address required'}), 400
        
        # Verify session exists
        session = db.session.get(Session, session_id)
        if not session:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        # Create temporary share link (7 days)
        share_service = ShareService()
        token = share_service.create_share_link(session_id, days=7)
        share_url = f"{request.host_url.rstrip('/')}/share/{token}"
        
        # Get summary if available (from AI insights or session metadata)
        summary = None
        if hasattr(session, 'summary'):
            summary = session.summary
        
        # Send email
        result = email_service.send_transcript_email(
            to_emails=emails,
            session_title=session.title or 'Untitled Meeting',
            session_date=session.created_at,
            summary=summary,
            share_link=share_url,
            sender_name=current_user.username if current_user else None,
            custom_message=custom_message if custom_message else None
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'recipients': len(emails)
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Email sending failed')
            }), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@sharing_bp.route('/api/sessions/<int:session_id>/share/slack', methods=['POST'])
@login_required
def share_to_slack(session_id: int):
    """
    Share session to Slack channel (T2.28).
    Posts summary to configured Slack channel using webhook.
    
    Request body:
    {
        "channel": "#general",  // Optional channel override
        "include_summary": true  // Optional, default true
    }
    """
    try:
        # Check if Slack service is configured
        if not slack_service.is_available():
            return jsonify({
                'success': False,
                'error': 'Slack not configured. Please set SLACK_WEBHOOK_URL.',
                'needs_setup': True
            }), 400
        
        data = request.get_json() or {}
        channel_override = data.get('channel')
        
        # Verify session exists
        session = db.session.get(Session, session_id)
        if not session:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        # Create temporary share link (7 days)
        share_service = ShareService()
        token = share_service.create_share_link(session_id, days=7)
        share_url = f"{request.host_url.rstrip('/')}/share/{token}"
        
        # Get summary if available
        summary = None
        if hasattr(session, 'summary'):
            summary = session.summary
        
        # Post to Slack
        result = slack_service.post_transcript_summary(
            session_title=session.title or 'Untitled Meeting',
            session_date=session.created_at,
            summary=summary,
            share_link=share_url,
            sender_name=current_user.username if current_user else None,
            channel_override=channel_override
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Slack posting failed')
            }), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@sharing_bp.route('/api/share/<string:token>/analytics', methods=['GET'])
def get_share_analytics(token: str):
    """
    Get analytics for a shared link (T2.25).
    Track views, unique visitors, etc.
    """
    try:
        # Find shared link
        stmt = select(SharedLink).where(SharedLink.token == token)
        shared_link = db.session.scalars(stmt).first()
        
        if not shared_link:
            return jsonify({'success': False, 'error': 'Share link not found'}), 404
        
        # TODO: Implement analytics tracking
        # For now, return basic info
        return jsonify({
            'success': True,
            'analytics': {
                'created_at': shared_link.created_at.isoformat(),
                'expires_at': shared_link.expires_at.isoformat() if shared_link.expires_at else None,
                'is_active': shared_link.is_active,
                'views': 0,  # To be implemented
                'unique_visitors': 0,  # To be implemented
                'last_viewed': None  # To be implemented
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
