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
        # Get recent sessions
        recent_sessions = Session.query.order_by(desc(Session.created_at)).limit(10).all()
        
        # Get global statistics
        total_sessions = Session.query.count()
        total_segments = Segment.query.count()
        
        # Active sessions count
        active_sessions = Session.query.filter_by(status='active').count()
        
        # Calculate total transcription time
        total_duration = db.session.query(db.func.sum(Session.total_duration)).scalar() or 0.0
        
        stats = {
            'total_sessions': total_sessions,
            'total_segments': total_segments,
            'active_sessions': active_sessions,
            'total_duration': total_duration,
            'total_duration_hours': total_duration / 3600.0
        }
        
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
        
        # Build query
        query = Session.query
        
        if status:
            query = query.filter(Session.status == status)
        
        if language:
            query = query.filter(Session.language == language)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Session.created_at >= date_from_obj)
            except ValueError:
                flash('Invalid date format for date_from', 'warning')
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(Session.created_at < date_to_obj)
            except ValueError:
                flash('Invalid date format for date_to', 'warning')
        
        # Paginate results
        sessions = query.order_by(desc(Session.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('sessions.html', 
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

@transcription_bp.route('/sessions/<session_id>')
def view_session(session_id):
    """
    View detailed transcription session with segments.
    """
    try:
        session = Session.query.filter_by(session_id=session_id).first_or_404()
        
        # Get segments with pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        segments = Segment.query.filter_by(session_id=session_id).order_by(
            Segment.sequence_number
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        # Get session statistics
        session_stats = {
            'total_segments': session.total_segments,
            'average_confidence': session.average_confidence,
            'duration_minutes': session.duration_minutes,
            'speakers_count': session.total_speakers or 0
        }
        
        return render_template('session_detail.html',
                             session=session,
                             segments=segments,
                             stats=session_stats)
    
    except Exception as e:
        logger.error(f"Error viewing session {session_id}: {e}")
        flash(f"Error loading session: {str(e)}", 'error')
        return redirect(url_for('transcription.list_sessions'))

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
        
        # Create session with service
        session_id = asyncio.run(service.start_session(
            user_config={
                'title': title,
                'description': description,
                'language': language,
                'enable_speaker_detection': enable_speaker_detection,
                'enable_sentiment_analysis': enable_sentiment_analysis
            }
        ))
        
        # Get the created session from database
        session = Session.query.filter_by(session_id=session_id).first()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'session': session.to_dict() if session else None
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
        session = Session.query.filter_by(session_id=session_id).first_or_404()
        
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
        session = Session.query.filter_by(session_id=session_id).first_or_404()
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        final_only = request.args.get('final_only', 'false').lower() == 'true'
        
        # Build query
        query = Segment.query.filter_by(session_id=session_id)
        
        if final_only:
            query = query.filter_by(is_final=True)
        
        segments = query.order_by(Segment.sequence_number).offset(offset).limit(limit).all()
        
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
        session = Session.query.filter_by(session_id=session_id).first_or_404()
        segments = Segment.get_final_segments(session_id)
        
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
        session = Session.query.filter_by(session_id=session_id).first_or_404()
        
        if session.status == 'completed':
            return jsonify({
                'success': True,
                'message': 'Session already completed'
            })
        
        # End session via service
        service = get_transcription_service()
        if session_id in service.active_sessions:
            final_stats = asyncio.run(service.end_session(session_id))
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
        total_sessions = Session.query.count()
        total_segments = Segment.query.count()
        active_sessions = Session.query.filter_by(status='active').count()
        
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
