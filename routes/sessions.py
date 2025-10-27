"""
Session Routes (M2)
REST API endpoints for session management, list, detail, and finalization.
"""

import logging
from flask import Blueprint, request, jsonify, render_template, abort, Response
from app import db
from services.session_service import SessionService
from services.export_service import ExportService

logger = logging.getLogger(__name__)

sessions_bp = Blueprint('sessions', __name__, url_prefix='/sessions')


@sessions_bp.route('/', methods=['GET'])
def list_sessions():
    """
    GET /sessions - List sessions with optional filtering
    
    Query parameters:
    - q: Search query for title
    - status: Status filter (active, completed, error)  
    - limit: Maximum results (default: 50)
    - offset: Results offset (default: 0)
    - format: Response format ('json' or 'html', default: 'html')
    """
    # Get query parameters
    q = request.args.get('q', None)
    status = request.args.get('status', None)
    limit = min(int(request.args.get('limit', 50)), 100)  # Cap at 100
    offset = int(request.args.get('offset', 0))
    response_format = request.args.get('format', 'html')
    
    # Get sessions from service with error handling
    try:
        sessions_result = SessionService.list_sessions(q=q, status=status, limit=limit, offset=offset)
        
        # Handle pagination object vs list
        if hasattr(sessions_result, 'items') and hasattr(sessions_result, 'total'):
            sessions = sessions_result.items  # type: ignore
            total_count = sessions_result.total  # type: ignore
        elif isinstance(sessions_result, list):
            sessions = sessions_result
            total_count = len(sessions)
        else:
            sessions = []
            total_count = 0
            
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return jsonify({'error': 'Failed to load sessions'}), 500
    
    # Return JSON for API requests
    if response_format == 'json':
        return jsonify({
            'sessions': [session.to_dict() for session in sessions] if sessions else [],
            'total': total_count,
            'query': {
                'q': q,
                'status': status,
                'limit': limit,
                'offset': offset
            }
        })
    
    # Return HTML template for browser requests
    # Pass pagination object or create simple wrapper for template compatibility
    if hasattr(sessions_result, 'items'):
        # Already a pagination object from SQLAlchemy
        meetings_obj = sessions_result
    else:
        # Create simple pagination wrapper with proper method signatures
        class SimplePagination:
            def __init__(self, items, total):
                self.items = items
                self.total = total
                self.pages = 1
                self.page = 1
                self.per_page = len(items) if items else 0
                self.has_prev = False
                self.has_next = False
                self.prev_num = None
                self.next_num = None
            
            def iter_pages(self, left_edge=0, right_edge=0, left_current=0, right_current=0):
                """Generator for page numbers"""
                yield 1
        
        meetings_obj = SimplePagination(sessions, total_count)
    
    return render_template('dashboard/meetings.html', 
                         meetings=meetings_obj,
                         search_query=q, 
                         status_filter=status,
                         limit=limit,
                         offset=offset)


@sessions_bp.route('/<session_identifier>', methods=['GET'])
def get_session_detail(session_identifier):
    """
    GET /sessions/<id_or_external_id> - Get session detail with segments
    
    Query parameters:
    - format: Response format ('json' or 'html', default: 'html')
    """
    response_format = request.args.get('format', 'html')
    
    # Try external_id first (since most lookups use external_id), then database ID as fallback
    session_detail = SessionService.get_session_detail_by_external(session_identifier)
    
    # If not found by external_id and identifier is numeric, try database ID
    if not session_detail and session_identifier.isdigit():
        session_detail = SessionService.get_session_detail(int(session_identifier))
    
    if not session_detail:
        if response_format == 'json':
            return jsonify({'error': 'Session not found'}), 404
        else:
            abort(404)
    
    # Return JSON for API requests
    if response_format == 'json':
        return jsonify(session_detail)
    
    # Return HTML template for browser requests  
    return render_template('dashboard/meeting_detail.html',
                         meeting=session_detail['session'],
                         segments=session_detail['segments'])


@sessions_bp.route('/', methods=['POST'])
def create_session():
    """
    POST /sessions - Create a new session
    
    Request body (JSON):
    - title: Optional session title
    - external_id: Optional external ID (auto-generated if not provided)
    - locale: Optional language/locale code
    - device_info: Optional device information dictionary
    """
    data = request.get_json() or {}
    
    try:
        session_id = SessionService.create_session(
            title=data.get('title'),
            external_id=data.get('external_id'),
            locale=data.get('locale'),
            device_info=data.get('device_info')
        )
        
        # Get created session for response
        session = SessionService.get_session_by_id(session_id)
        if session:
            return jsonify({
                'id': session.id,
                'external_id': session.external_id,
                'title': session.title,
                'status': session.status,
                'started_at': session.started_at.isoformat()
            }), 201
        else:
            return jsonify({'error': 'Failed to create session'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to create session: {str(e)}'}), 500


@sessions_bp.route('/<int:session_id>/finalize', methods=['POST'])
def finalize_session(session_id):
    """
    POST /sessions/<id>/finalize - Mark session as completed (idempotent)
    
    Request body (JSON, optional):
    - final_text: Optional final transcript text to add
    """
    data = request.get_json() or {}
    final_text = data.get('final_text')
    
    try:
        # Check if session exists
        session = SessionService.get_session_by_id(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Complete the session (idempotent)
        SessionService.complete_session(session_id)
        
        # Finalize segments if final text provided
        if final_text:
            finalized_count = SessionService.finalize_session_segments(session_id, final_text)
            return jsonify({
                'message': f'Session {session_id} completed',
                'finalized_segments': finalized_count,
                'status': 'completed'
            })
        else:
            return jsonify({
                'message': f'Session {session_id} completed',
                'status': 'completed'
            })
            
    except Exception as e:
        return jsonify({'error': f'Failed to finalize session: {str(e)}'}), 500


@sessions_bp.route('/stats', methods=['GET'])
def get_session_stats():
    """
    GET /sessions/stats - Get session statistics
    """
    try:
        stats = SessionService.get_session_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500


@sessions_bp.route('/<session_identifier>/refined', methods=['GET'])
def get_session_refined(session_identifier):
    """
    GET /sessions/<id_or_external_id>/refined - Refined session view with tabs
    
    This is the post-transcription view with:
    - Transcript tab
    - Highlights tab (summary, insights)
    - Analytics tab (metrics, sentiment)
    - Tasks tab (action items)
    - Replay tab (audio sync)
    
    Automatically navigated to after post_transcription_reveal event.
    
    IMPORTANT: This view only loads 'final' segments to ensure all tabs
    analyze the same refined transcript that the AI analyzed.
    """
    # Try external_id first (since redirect uses external_id), then database ID as fallback
    # Load ONLY final segments for consistency across all tabs
    session_detail = SessionService.get_session_detail_by_external(session_identifier, kind='final')
    
    # If not found by external_id and identifier is numeric, try database ID
    if not session_detail and session_identifier.isdigit():
        session_detail = SessionService.get_session_detail(int(session_identifier), kind='final')
    
    if not session_detail:
        abort(404)
    
    # Get additional data for tabs
    session_data = session_detail['session']
    segments = session_detail['segments']
    
    # Log what we're working with for debugging
    logger.info(f"[Refined View] Session {session_identifier}: {len(segments)} final segments loaded")
    
    # Get summary/insights data
    summary_data = None
    try:
        from services.analysis_service import AnalysisService
        summary_data = AnalysisService.get_session_summary(session_data['id'])
    except Exception as e:
        logger.warning(f"Failed to get summary for session {session_identifier}: {e}")
    
    # Get analytics data
    analytics_data = None
    try:
        # Calculate basic analytics from segments
        word_count = sum(len((s.get('text') or '').split()) for s in segments)
        total_duration = sum((s.get('end_ms', 0) - s.get('start_ms', 0)) for s in segments) / 1000.0
        avg_confidence = sum(s.get('avg_confidence', 0) for s in segments) / len(segments) if segments else 0
        
        analytics_data = {
            'word_count': word_count,
            'total_duration': total_duration,
            'average_confidence': avg_confidence,
            'segment_count': len(segments),
            'words_per_minute': (word_count / (total_duration / 60)) if total_duration > 0 else 0
        }
    except Exception as e:
        logger.warning(f"Failed to calculate analytics for session {session_identifier}: {e}")
    
    # Get tasks/action items
    tasks_data = []
    try:
        from models.task import Task
        from sqlalchemy import select
        stmt = select(Task).filter(Task.session_id == session_data['id']).order_by(Task.created_at)
        tasks = db.session.execute(stmt).scalars().all()
        tasks_data = [task.to_dict(include_relationships=True) for task in tasks] if tasks else []
    except Exception as e:
        logger.warning(f"Failed to get tasks for session {session_identifier}: {e}")
    
    # Get event timeline for debugging/status
    event_timeline = []
    try:
        from services.event_ledger_service import EventLedgerService
        event_timeline = EventLedgerService.get_event_timeline(
            session_data.get('external_id') or session_identifier
        )
    except Exception as e:
        logger.warning(f"Failed to get event timeline: {e}")
    
    # Render refined template with all data
    return render_template(
        'session_refined.html',
        session=session_data,
        segments=segments,
        summary=summary_data,
        analytics=analytics_data,
        tasks=tasks_data,
        event_timeline=event_timeline
    )


@sessions_bp.route('/<int:session_id>/export.md', methods=['GET'])
def export_session_markdown(session_id):
    """
    GET /sessions/<id>/export.md - Export session to Markdown
    
    Returns:
        Markdown file download with Content-Disposition header
    """
    try:
        # Generate markdown content
        markdown_content = ExportService.session_to_markdown(session_id)
        if not markdown_content:
            abort(404)
        
        # Generate filename
        filename = ExportService.get_export_filename(session_id, 'md')
        
        # Return as downloadable file
        return Response(
            markdown_content,
            mimetype='text/markdown',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        return jsonify({'error': f'Failed to export session: {str(e)}'}), 500