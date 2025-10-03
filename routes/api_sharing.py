"""
Sharing Routes for Phase 2 Group 4 (T2.23-T2.27)
Enhanced session sharing with privacy settings, team collaboration, and analytics.
"""

import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, abort, url_for
from flask_login import login_required, current_user
from sqlalchemy import select, func
from models import db, Session, Meeting, SharedLink, TeamShare, ShareAnalytic, User
from services.share_service import ShareService
from services.email_service import email_service
from services.slack_service import slack_service

sharing_bp = Blueprint('sharing', __name__)


def check_meeting_access(session_id: int, required_role: str = 'viewer'):
    """
    Helper function to verify user has access to a meeting.
    Returns (meeting, error_response) tuple.
    If meeting is None, error_response contains the error to return.
    """
    # Verify session exists
    session = db.session.get(Session, session_id)
    if not session:
        return None, (jsonify({'success': False, 'error': 'Session not found'}), 404)
    
    # Find the meeting that owns this session
    meeting_stmt = select(Meeting).where(Meeting.session_id == session_id)
    meeting = db.session.scalars(meeting_stmt).first()
    
    if not meeting:
        return None, (jsonify({'success': False, 'error': 'Meeting not found for this session'}), 404)
    
    # Check if user has permission
    # User must be either the organizer or have appropriate team role
    is_organizer = meeting.organizer_id == current_user.id
    
    if is_organizer:
        return meeting, None
    
    # Check team permissions based on required role
    if required_role == 'viewer':
        # Any team member can view
        team_share_stmt = select(TeamShare).where(
            TeamShare.meeting_id == meeting.id,
            TeamShare.user_id == current_user.id
        )
    else:
        # Editor/admin roles required
        team_share_stmt = select(TeamShare).where(
            TeamShare.meeting_id == meeting.id,
            TeamShare.user_id == current_user.id,
            TeamShare.role.in_(['editor', 'admin'])
        )
    
    has_team_permission = db.session.scalars(team_share_stmt).first() is not None
    
    if not has_team_permission:
        return None, (jsonify({'success': False, 'error': 'You do not have permission to access this meeting'}), 403)
    
    return meeting, None


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
        # SECURITY: Verify user has editor/admin access
        meeting, error = check_meeting_access(session_id, required_role='editor')
        if error:
            return error
        
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
    Records analytics (T2.25).
    """
    try:
        share_service = ShareService()
        
        # Validate token and get session
        session = share_service.validate_share_token(token)
        
        if not session:
            return render_template('share/expired.html'), 403
        
        # Record analytics (T2.25)
        stmt = select(SharedLink).where(SharedLink.token == token)
        shared_link = db.session.scalars(stmt).first()
        
        if shared_link:
            analytic = ShareAnalytic(
                shared_link_id=shared_link.id,
                visitor_ip=request.remote_addr,
                visitor_user_agent=request.headers.get('User-Agent', '')[:500],
                referrer=request.headers.get('Referer', '')[:500]
            )
            db.session.add(analytic)
            db.session.commit()
        
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
        # SECURITY: Verify user has viewer access
        meeting, error = check_meeting_access(session_id, required_role='viewer')
        if error:
            return error
        
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
        # SECURITY: Verify user has editor/admin access
        meeting, error = check_meeting_access(session_id, required_role='editor')
        if error:
            return error
        
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


@sharing_bp.route('/api/sessions/<int:session_id>/team', methods=['POST'])
@login_required
def share_with_team(session_id: int):
    """
    Share session with team members (T2.24).
    
    Request body:
    {
        "user_email": "colleague@example.com",
        "role": "viewer"  // viewer, editor, or admin
    }
    """
    try:
        data = request.get_json() or {}
        user_email = data.get('user_email')
        role = data.get('role', 'viewer')
        
        # Validate inputs
        if not user_email:
            return jsonify({'success': False, 'error': 'User email required'}), 400
        
        if role not in ['viewer', 'editor', 'admin']:
            return jsonify({'success': False, 'error': 'Invalid role'}), 400
        
        # Verify session exists
        session = db.session.get(Session, session_id)
        if not session:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        # Find user by email
        stmt = select(User).where(User.email == user_email)
        user = db.session.scalars(stmt).first()
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Check if already shared
        stmt = select(TeamShare).where(
            TeamShare.session_id == session_id,
            TeamShare.user_id == user.id
        )
        existing_share = db.session.scalars(stmt).first()
        
        if existing_share:
            # Update role
            existing_share.role = role
            existing_share.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Updated {user.username}\'s role to {role}',
                'share': existing_share.to_dict()
            })
        else:
            # Create new team share
            team_share = TeamShare(
                session_id=session_id,
                user_id=user.id,
                shared_by_id=current_user.id,
                role=role
            )
            db.session.add(team_share)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Shared with {user.username} as {role}',
                'share': team_share.to_dict()
            }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@sharing_bp.route('/api/sessions/<int:session_id>/team', methods=['GET'])
@login_required
def get_team_shares(session_id: int):
    """Get all team members with access to session (T2.24)."""
    try:
        # Verify session exists
        session = db.session.get(Session, session_id)
        if not session:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        # Get all team shares for this session
        stmt = select(TeamShare).where(TeamShare.session_id == session_id)
        team_shares = db.session.scalars(stmt).all()
        
        return jsonify({
            'success': True,
            'team_shares': [share.to_dict() for share in team_shares]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@sharing_bp.route('/api/sessions/<int:session_id>/team/<int:share_id>', methods=['DELETE'])
@login_required  
def remove_team_access(session_id: int, share_id: int):
    """Remove team member's access to session (T2.24)."""
    try:
        team_share = db.session.get(TeamShare, share_id)
        
        if not team_share or team_share.session_id != session_id:
            return jsonify({'success': False, 'error': 'Team share not found'}), 404
        
        db.session.delete(team_share)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Team member access removed'
        })
        
    except Exception as e:
        db.session.rollback()
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
        
        # Get analytics data
        total_views = db.session.query(func.count(ShareAnalytic.id)).filter(
            ShareAnalytic.shared_link_id == shared_link.id
        ).scalar() or 0
        
        # Get unique visitors (count distinct IPs)
        unique_visitors = db.session.query(func.count(func.distinct(ShareAnalytic.visitor_ip))).filter(
            ShareAnalytic.shared_link_id == shared_link.id
        ).scalar() or 0
        
        # Get last viewed timestamp
        last_view = db.session.query(func.max(ShareAnalytic.viewed_at)).filter(
            ShareAnalytic.shared_link_id == shared_link.id
        ).scalar()
        
        # Get recent views (last 10)
        recent_views_stmt = select(ShareAnalytic).where(
            ShareAnalytic.shared_link_id == shared_link.id
        ).order_by(ShareAnalytic.viewed_at.desc()).limit(10)
        recent_views = db.session.scalars(recent_views_stmt).all()
        
        return jsonify({
            'success': True,
            'analytics': {
                'created_at': shared_link.created_at.isoformat(),
                'expires_at': shared_link.expires_at.isoformat() if shared_link.expires_at else None,
                'is_active': shared_link.is_active,
                'total_views': total_views,
                'unique_visitors': unique_visitors,
                'last_viewed': last_view.isoformat() if last_view else None,
                'recent_views': [
                    {
                        'viewed_at': view.viewed_at.isoformat(),
                        'visitor_country': view.visitor_country,
                        'referrer': view.referrer
                    }
                    for view in recent_views
                ]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
