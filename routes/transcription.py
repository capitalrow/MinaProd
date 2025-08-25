"""
Transcription Routes
HTTP endpoints for managing transcription sessions and retrieving transcripts.
"""

import logging
import asyncio
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, timedelta
from sqlalchemy import desc

from models.session import Session
from models.segment import Segment
from services.transcription_service import TranscriptionService, TranscriptionServiceConfig
from services.session_service import SessionService
from app_refactored import db

logger = logging.getLogger(__name__)

transcription_bp = Blueprint('transcription', __name__)

# Global transcription service instance
# In production, this might be managed by a service container
_transcription_service = None

def get_transcription_service():
    """Get or create the global transcription service instance."""
    global _transcription_service
    if _transcription_service is None:
        config = TranscriptionServiceConfig()
        _transcription_service = TranscriptionService(config)
    return _transcription_service

@transcription_bp.route('/')
def index():
    """
    Main dashboard showing recent sessions and system status.
    """
    try:
        # Get recent sessions using SessionService
        recent_sessions = SessionService.list_sessions(limit=10)
        
        # Get global statistics using SessionService
        stats = SessionService.get_session_stats()
        stats['total_duration_hours'] = 0.0  # Placeholder for now
        
        return render_template('index.html', 
                             recent_sessions=recent_sessions,
                             stats=stats)
    
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash(f"Error loading dashboard: {str(e)}", 'error')
        return render_template('index.html', recent_sessions=[], stats={})

@transcription_bp.route('/live')
def live_transcription():
    """
    Real-time transcription interface.
    """
    return render_template('live.html')

@transcription_bp.route('/sessions')
def list_sessions():
    """
    List all transcription sessions with pagination.
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Filter parameters
        status = request.args.get('status')
        language = request.args.get('language')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query using SQLAlchemy 2.0
        from sqlalchemy import select
        query = select(Session)
        
        if status:
            query = query.where(Session.status == status)
        
        if language:
            query = query.where(Session.locale == language)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.where(Session.started_at >= date_from_obj)
            except ValueError:
                flash('Invalid date format for date_from', 'warning')
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.where(Session.started_at < date_to_obj)
            except ValueError:
                flash('Invalid date format for date_to', 'warning')
        
        # Get results with pagination manually for SQLAlchemy 2.0
        from sqlalchemy import func
        offset = (page - 1) * per_page
        sessions_query = query.order_by(desc(Session.started_at))
        sessions_list = db.session.scalars(sessions_query.offset(offset).limit(per_page)).all()
        total = db.session.scalars(select(func.count()).select_from(Session)).one()
        
        # Create pagination-like object
        class SessionsPagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page if per_page > 0 else 0
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None
        
        sessions = SessionsPagination(sessions_list, page, per_page, total)
        
        return render_template('sessions_list.html', 
                             sessions=sessions,
                             current_filters={
                                 'status': status,
                                 'language': language,
                                 'date_from': date_from,
                                 'date_to': date_to
                             })
    
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        flash(f"Error loading sessions: {str(e)}", 'error')
        return redirect(url_for('transcription.index'))

# Removed duplicate route - session details are handled by sessions blueprint

@transcription_bp.route('/api/sessions', methods=['POST'])
def create_session():
    """
    API endpoint to create a new transcription session.
    """
    try:
        data = request.get_json() or {}
        
        # Extract configuration
        title = data.get('title', 'New Meeting')
        description = data.get('description', '')
        language = data.get('language', 'en')
        enable_speaker_detection = data.get('enable_speaker_detection', True)
        enable_sentiment_analysis = data.get('enable_sentiment_analysis', False)
        
        # Get transcription service
        service = get_transcription_service()
        
        # Create session using SessionService
        from services.session_service import SessionService
        import uuid
        
        # Generate external_id
        external_id = str(uuid.uuid4())[:8]
        
        # Create session in database
        session_id = SessionService.create_session(
            external_id=external_id,
            title=title,
            locale=language
        )
        
        # Get the created session
        from sqlalchemy import select
        stmt = select(Session).where(Session.id == session_id)
        session = db.session.scalars(stmt).first()
        
        # Register session with transcription service for real-time processing
        try:
            service = get_transcription_service()
            service.start_session_sync(
                external_id,  # session_id should be the external_id
                user_config={
                    'title': title,
                    'language': language,
                    'enable_speaker_detection': enable_speaker_detection,
                    'enable_sentiment_analysis': enable_sentiment_analysis
                }
            )
        except Exception as e:
            logger.warning(f"Failed to register session {external_id} with transcription service: {e}")
        
        return jsonify({
            'success': True,
            'session_id': session.external_id,
            'session': session.to_dict()
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@transcription_bp.route('/api/sessions/<session_id>', methods=['GET'])
def get_session_api(session_id):
    """
    API endpoint to get session details.
    """
    try:
        from sqlalchemy import select
        stmt = select(Session).where(Session.external_id == session_id)
        session = db.session.scalars(stmt).first()
        if not session:
            abort(404)
        
        # Get service status if session is active
        service_status = None
        if session.is_active:
            try:
                service = get_transcription_service()
                service_status = service.get_session_status(session_id)
            except Exception as e:
                logger.warning(f"Could not get service status: {e}")
        
        response = session.to_dict()
        if service_status:
            response['service_status'] = service_status
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@transcription_bp.route('/api/sessions/<session_id>/segments', methods=['GET'])
def get_session_segments(session_id):
    """
    API endpoint to get session segments.
    """
    try:
        # Verify session exists
        from sqlalchemy import select
        stmt = select(Session).where(Session.external_id == session_id)
        session = db.session.scalars(stmt).first()
        if not session:
            abort(404)
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        final_only = request.args.get('final_only', 'false').lower() == 'true'
        
        # Build query using SQLAlchemy 2.0
        segments_stmt = select(Segment).where(Segment.session_id == session.id)
        
        if final_only:
            segments_stmt = segments_stmt.where(Segment.is_final == True)
        
        segments = db.session.scalars(segments_stmt.order_by(Segment.created_at).offset(offset).limit(limit)).all()
        
        return jsonify({
            'session_id': session_id,
            'segments': [segment.to_dict() for segment in segments],
            'total_segments': session.total_segments,
            'has_more': len(segments) == limit
        })
    
    except Exception as e:
        logger.error(f"Error getting segments for session {session_id}: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@transcription_bp.route('/api/sessions/<session_id>/export', methods=['GET'])
def export_session(session_id):
    """
    Export session transcript in various formats.
    """
    try:
        from sqlalchemy import select
        stmt = select(Session).where(Session.external_id == session_id)
        session = db.session.scalars(stmt).first()
        if not session:
            abort(404)
        
        # Get final segments using SQLAlchemy 2.0
        segments_stmt = select(Segment).where(Segment.session_id == session.id, Segment.kind == 'final')
        segments = db.session.scalars(segments_stmt).all()
        
        export_format = request.args.get('format', 'txt').lower()
        include_timestamps = request.args.get('timestamps', 'false').lower() == 'true'
        include_speakers = request.args.get('speakers', 'false').lower() == 'true'
        
        if export_format == 'json':
            return jsonify({
                'session': session.to_dict(),
                'segments': [segment.to_dict() for segment in segments]
            })
        
        elif export_format == 'txt':
            lines = []
            if include_timestamps or include_speakers:
                for segment in segments:
                    prefix_parts = []
                    if include_timestamps:
                        prefix_parts.append(f"[{segment.start_time_formatted}]")
                    if include_speakers and segment.speaker_name:
                        prefix_parts.append(f"{segment.speaker_name}:")
                    
                    prefix = " ".join(prefix_parts)
                    if prefix:
                        lines.append(f"{prefix} {segment.text}")
                    else:
                        lines.append(segment.text)
            else:
                lines = [segment.text for segment in segments]
            
            content = "\n".join(lines)
            
            from flask import Response
            return Response(
                content,
                mimetype='text/plain',
                headers={
                    'Content-Disposition': f'attachment; filename="{session.title}_transcript.txt"'
                }
            )
        
        else:
            return jsonify({'error': 'Unsupported export format'}), 400
    
    except Exception as e:
        logger.error(f"Error exporting session {session_id}: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@transcription_bp.route('/api/sessions/<session_id>/end', methods=['POST'])
def end_session_api(session_id):
    """
    API endpoint to end a transcription session.
    """
    try:
        from sqlalchemy import select
        stmt = select(Session).where(Session.external_id == session_id)
        session = db.session.scalars(stmt).first()
        if not session:
            abort(404)
        
        if session.status == 'completed':
            return jsonify({
                'success': True,
                'message': 'Session already completed'
            })
        
        # End session via service
        service = get_transcription_service()
        if session_id in service.active_sessions:
            final_stats = service.end_session_sync(session_id)
        else:
            # End session directly in database
            session.end_session()
            final_stats = {'session_id': session_id, 'status': 'completed'}
        
        return jsonify({
            'success': True,
            'final_stats': final_stats
        })
    
    except Exception as e:
        logger.error(f"Error ending session {session_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@transcription_bp.route('/api/stats', methods=['GET'])
def get_global_stats():
    """
    API endpoint for global transcription statistics.
    """
    try:
        # Database statistics
        # Use SessionService for stats
        stats_data = SessionService.get_session_stats()
        total_sessions = stats_data['total_sessions']
        total_segments = stats_data['total_segments'] 
        active_sessions = stats_data['active_sessions']
        
        # Service statistics
        service = get_transcription_service()
        service_stats = service.get_global_statistics()
        
        return jsonify({
            'database': {
                'total_sessions': total_sessions,
                'total_segments': total_segments,
                'active_sessions': active_sessions
            },
            'service': service_stats,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting global stats: {e}")
        return jsonify({
            'error': str(e)
        }), 500

# Error handlers for the blueprint
@transcription_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors within transcription routes."""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Resource not found'}), 404
    flash('The requested page was not found.', 'error')
    return redirect(url_for('transcription.index'))

@transcription_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors within transcription routes."""
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    flash('An internal error occurred. Please try again later.', 'error')
    return redirect(url_for('transcription.index'))
