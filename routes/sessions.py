"""
Session Routes (M2)
REST API endpoints for session management, list, detail, and finalization.
"""

import logging
from flask import Blueprint, request, jsonify, render_template, abort, Response
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
        if hasattr(sessions_result, 'items'):
            sessions = sessions_result.items
            total_count = sessions_result.total
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
    
    # Try to get session by database ID first (if it's numeric), then by external_id
    session_detail = None
    if session_identifier.isdigit():
        session_detail = SessionService.get_session_detail(int(session_identifier))
    else:
        session_detail = SessionService.get_session_detail_by_external(session_identifier)
    
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