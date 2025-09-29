"""
📅 Consolidated Meetings API
Unified endpoint consolidating all meetings functionality to eliminate duplication.
Replaces: api_meetings.py, meetings_api_fix.py
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from extensions import get_service, get_db
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Create consolidated blueprint
meetings_api_bp = Blueprint('meetings_api', __name__, url_prefix='/api/meetings')

@meetings_api_bp.route('', methods=['GET'])
@login_required
def get_meetings():
    """Get user's meetings with filtering and pagination"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)  # Max 100 per page
        status = request.args.get('status', None)  # active, completed, cancelled
        date_from = request.args.get('date_from', None)
        date_to = request.args.get('date_to', None)
        search = request.args.get('search', None)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build filter criteria
        filters = {
            'user_id': current_user.id,
            'page': page,
            'per_page': per_page,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
        
        if status:
            filters['status'] = status
        if date_from:
            filters['date_from'] = datetime.fromisoformat(date_from)
        if date_to:
            filters['date_to'] = datetime.fromisoformat(date_to)
        if search:
            filters['search'] = search
        
        # Get meetings from service
        db = get_db()
        from models.session import Session
        
        query = db.session.query(Session).filter_by(user_id=current_user.id)
        
        # Apply filters
        if status:
            query = query.filter(Session.status == status)
        if date_from:
            query = query.filter(Session.created_at >= filters['date_from'])
        if date_to:
            query = query.filter(Session.created_at <= filters['date_to'])
        if search:
            query = query.filter(Session.title.ilike(f'%{search}%'))
        
        # Apply sorting
        if sort_by == 'created_at':
            if sort_order == 'desc':
                query = query.order_by(Session.created_at.desc())
            else:
                query = query.order_by(Session.created_at.asc())
        elif sort_by == 'title':
            if sort_order == 'desc':
                query = query.order_by(Session.title.desc())
            else:
                query = query.order_by(Session.title.asc())
        
        # Paginate
        paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        meetings = []
        for session in paginated.items:
            meetings.append({
                'id': session.session_id,
                'title': session.title or f'Meeting {session.session_id[:8]}',
                'status': session.status,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'updated_at': session.updated_at.isoformat() if session.updated_at else None,
                'duration': session.duration_seconds,
                'segments_count': session.segments_count,
                'participants_count': session.participants_count or 1,
                'language': session.language_detected,
                'confidence_avg': session.confidence_avg
            })
        
        return jsonify({
            'status': 'success',
            'meetings': meetings,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            },
            'filters': filters
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get meetings: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve meetings'
        }), 500

@meetings_api_bp.route('', methods=['POST'])
@login_required
def create_meeting():
    """Create a new meeting"""
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        title = data.get('title', '').strip()
        if not title:
            return jsonify({
                'status': 'error',
                'message': 'Meeting title is required'
            }), 400
        
        # Get services
        transcription_service = get_service('transcription')
        business_metrics = get_service('business_metrics')
        
        # Create meeting configuration
        config = {
            'title': title,
            'description': data.get('description', ''),
            'language': data.get('language', 'auto'),
            'model': data.get('model', 'whisper-1'),
            'enhanced_processing': data.get('enhanced_processing', True),
            'speaker_diarization': data.get('speaker_diarization', True),
            'auto_summarization': data.get('auto_summarization', True),
            'scheduled_start': data.get('scheduled_start'),
            'expected_duration': data.get('expected_duration', 3600)
        }
        
        # Create session
        session_id = transcription_service.create_session(
            user_id=current_user.id,
            config=config
        )
        
        # Track metrics
        business_metrics.create_meeting(
            user_id=current_user.id,
            meeting_id=session_id,
            config=config
        )
        
        logger.info(f"📅 Meeting created: {session_id} - {title}")
        
        return jsonify({
            'status': 'success',
            'meeting': {
                'id': session_id,
                'title': title,
                'status': 'created',
                'config': config,
                'websocket_url': f'/socket.io',
                'websocket_namespace': '/transcription'
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create meeting: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to create meeting'
        }), 500

@meetings_api_bp.route('/<meeting_id>', methods=['GET'])
@login_required
def get_meeting(meeting_id: str):
    """Get specific meeting details"""
    try:
        db = get_db()
        from models.session import Session
        from models.segment import TranscriptionSegment
        
        session = db.session.query(Session).filter_by(
            session_id=meeting_id,
            user_id=current_user.id
        ).first()
        
        if not session:
            return jsonify({
                'status': 'error',
                'message': 'Meeting not found'
            }), 404
        
        # Get segments if requested
        include_transcript = request.args.get('include_transcript', 'false').lower() == 'true'
        segments = []
        
        if include_transcript:
            segment_records = db.session.query(TranscriptionSegment).filter_by(
                session_id=meeting_id
            ).order_by(TranscriptionSegment.start_time).all()
            
            segments = [{
                'id': seg.segment_id,
                'text': seg.text,
                'start_time': seg.start_time,
                'end_time': seg.end_time,
                'confidence': seg.confidence,
                'speaker_id': seg.speaker_id,
                'language': seg.language_detected
            } for seg in segment_records]
        
        meeting_data = {
            'id': session.session_id,
            'title': session.title or f'Meeting {session.session_id[:8]}',
            'description': session.description,
            'status': session.status,
            'created_at': session.created_at.isoformat() if session.created_at else None,
            'updated_at': session.updated_at.isoformat() if session.updated_at else None,
            'started_at': session.started_at.isoformat() if session.started_at else None,
            'ended_at': session.ended_at.isoformat() if session.ended_at else None,
            'duration': session.duration_seconds,
            'segments_count': session.segments_count,
            'participants_count': session.participants_count or 1,
            'language': session.language_detected,
            'confidence_avg': session.confidence_avg,
            'ai_summary': session.ai_summary,
            'key_insights': session.key_insights,
            'action_items': session.action_items,
            'config': session.config or {}
        }
        
        if include_transcript:
            meeting_data['transcript'] = segments
        
        return jsonify({
            'status': 'success',
            'meeting': meeting_data
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get meeting: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve meeting'
        }), 500

@meetings_api_bp.route('/<meeting_id>', methods=['PUT'])
@login_required
def update_meeting(meeting_id: str):
    """Update meeting details"""
    try:
        data = request.get_json() or {}
        
        db = get_db()
        from models.session import Session
        
        session = db.session.query(Session).filter_by(
            session_id=meeting_id,
            user_id=current_user.id
        ).first()
        
        if not session:
            return jsonify({
                'status': 'error',
                'message': 'Meeting not found'
            }), 404
        
        # Update allowed fields
        if 'title' in data:
            session.title = data['title'].strip()
        if 'description' in data:
            session.description = data['description']
        if 'ai_summary' in data:
            session.ai_summary = data['ai_summary']
        if 'key_insights' in data:
            session.key_insights = data['key_insights']
        if 'action_items' in data:
            session.action_items = data['action_items']
        
        session.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"📅 Meeting updated: {meeting_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Meeting updated successfully',
            'meeting': {
                'id': session.session_id,
                'title': session.title,
                'description': session.description,
                'updated_at': session.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to update meeting: {e}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Failed to update meeting'
        }), 500

@meetings_api_bp.route('/<meeting_id>', methods=['DELETE'])
@login_required
def delete_meeting(meeting_id: str):
    """Delete a meeting"""
    try:
        db = get_db()
        from models.session import Session
        from models.segment import TranscriptionSegment
        
        session = db.session.query(Session).filter_by(
            session_id=meeting_id,
            user_id=current_user.id
        ).first()
        
        if not session:
            return jsonify({
                'status': 'error',
                'message': 'Meeting not found'
            }), 404
        
        # Delete associated segments first
        db.session.query(TranscriptionSegment).filter_by(
            session_id=meeting_id
        ).delete()
        
        # Delete session
        db.session.delete(session)
        db.session.commit()
        
        # Track metrics
        business_metrics = get_service('business_metrics')
        business_metrics.delete_meeting(
            user_id=current_user.id,
            meeting_id=meeting_id
        )
        
        logger.info(f"📅 Meeting deleted: {meeting_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Meeting deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to delete meeting: {e}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Failed to delete meeting'
        }), 500

@meetings_api_bp.route('/<meeting_id>/start', methods=['POST'])
@login_required
def start_meeting(meeting_id: str):
    """Start a meeting (begin transcription)"""
    try:
        transcription_service = get_service('transcription')
        
        result = transcription_service.start_session(meeting_id)
        
        if not result:
            return jsonify({
                'status': 'error',
                'message': 'Failed to start meeting'
            }), 400
        
        logger.info(f"📅 Meeting started: {meeting_id}")
        
        return jsonify({
            'status': 'success',
            'meeting_id': meeting_id,
            'message': 'Meeting started successfully',
            'websocket_url': f'/socket.io',
            'websocket_namespace': '/transcription'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to start meeting: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to start meeting'
        }), 500

@meetings_api_bp.route('/<meeting_id>/stop', methods=['POST'])
@login_required
def stop_meeting(meeting_id: str):
    """Stop a meeting (end transcription)"""
    try:
        transcription_service = get_service('transcription')
        
        final_stats = transcription_service.stop_session(meeting_id)
        
        logger.info(f"📅 Meeting stopped: {meeting_id}")
        
        return jsonify({
            'status': 'success',
            'meeting_id': meeting_id,
            'message': 'Meeting stopped successfully',
            'final_stats': final_stats
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to stop meeting: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to stop meeting'
        }), 500

@meetings_api_bp.route('/recent', methods=['GET'])
@login_required
def get_recent_meetings():
    """Get user's recent meetings"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)  # Max 50
        
        db = get_db()
        from models.session import Session
        
        sessions = db.session.query(Session).filter_by(
            user_id=current_user.id
        ).order_by(
            Session.updated_at.desc()
        ).limit(limit).all()
        
        meetings = []
        for session in sessions:
            meetings.append({
                'id': session.session_id,
                'title': session.title or f'Meeting {session.session_id[:8]}',
                'status': session.status,
                'updated_at': session.updated_at.isoformat() if session.updated_at else None,
                'duration': session.duration_seconds,
                'segments_count': session.segments_count
            })
        
        return jsonify({
            'status': 'success',
            'meetings': meetings,
            'count': len(meetings)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get recent meetings: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve recent meetings'
        }), 500

# Error handlers for this blueprint
@meetings_api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'status': 'error',
        'message': 'Bad request'
    }), 400

@meetings_api_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'status': 'error',
        'message': 'Authentication required'
    }), 401

@meetings_api_bp.errorhandler(403)
def forbidden(error):
    return jsonify({
        'status': 'error',
        'message': 'Insufficient permissions'
    }), 403

@meetings_api_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Meeting not found'
    }), 404

@meetings_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500