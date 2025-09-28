"""
Markers API Routes
REST API endpoints for managing meeting markers (/decision, /todo, /risk).
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Meeting, Marker
from datetime import datetime


api_markers_bp = Blueprint('api_markers', __name__, url_prefix='/api/markers')


@api_markers_bp.route('/create', methods=['POST'])
@login_required
def create_marker():
    """Create a new marker from transcription text."""
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        required_fields = ['type', 'content', 'sessionId']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        marker_type = data.get('type', '').lower()
        if marker_type not in ['decision', 'todo', 'risk']:
            return jsonify({
                'success': False,
                'error': 'Invalid marker type. Must be decision, todo, or risk'
            }), 400
        
        # Create marker
        marker = Marker(
            type=marker_type,
            content=data.get('content', '').strip(),
            speaker=data.get('speaker', 'Unknown'),
            session_id=data.get('sessionId'),
            timestamp=datetime.fromtimestamp(data.get('timestamp', 0) / 1000) if data.get('timestamp') else datetime.utcnow(),
            user_id=current_user.id
        )
        
        db.session.add(marker)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'marker': {
                'id': marker.id,
                'type': marker.type,
                'content': marker.content,
                'speaker': marker.speaker,
                'timestamp': marker.timestamp.isoformat(),
                'session_id': marker.session_id
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to create marker: {str(e)}'
        }), 500


@api_markers_bp.route('/session/<session_id>', methods=['GET'])
@login_required
def get_session_markers(session_id):
    """Get all markers for a specific session."""
    try:
        markers = db.session.query(Marker).filter_by(
            session_id=session_id,
            user_id=current_user.id
        ).order_by(Marker.timestamp.asc()).all()
        
        return jsonify({
            'success': True,
            'markers': [{
                'id': marker.id,
                'type': marker.type,
                'content': marker.content,
                'speaker': marker.speaker,
                'timestamp': marker.timestamp.isoformat(),
                'session_id': marker.session_id
            } for marker in markers]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get markers: {str(e)}'
        }), 500


@api_markers_bp.route('/<int:marker_id>', methods=['PUT'])
@login_required
def update_marker(marker_id):
    """Update an existing marker."""
    try:
        marker = db.session.query(Marker).filter_by(
            id=marker_id,
            user_id=current_user.id
        ).first()
        
        if not marker:
            return jsonify({
                'success': False,
                'error': 'Marker not found'
            }), 404
        
        data = request.get_json() or {}
        
        # Update allowed fields
        if 'content' in data:
            marker.content = data['content'].strip()
        if 'type' in data and data['type'] in ['decision', 'todo', 'risk']:
            marker.type = data['type']
        
        marker.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'marker': {
                'id': marker.id,
                'type': marker.type,
                'content': marker.content,
                'speaker': marker.speaker,
                'timestamp': marker.timestamp.isoformat(),
                'session_id': marker.session_id
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to update marker: {str(e)}'
        }), 500


@api_markers_bp.route('/<int:marker_id>', methods=['DELETE'])
@login_required
def delete_marker(marker_id):
    """Delete a marker."""
    try:
        marker = db.session.query(Marker).filter_by(
            id=marker_id,
            user_id=current_user.id
        ).first()
        
        if not marker:
            return jsonify({
                'success': False,
                'error': 'Marker not found'
            }), 404
        
        db.session.delete(marker)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Marker deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to delete marker: {str(e)}'
        }), 500


@api_markers_bp.route('/stats', methods=['GET'])
@login_required
def get_markers_stats():
    """Get marker statistics for the current user."""
    try:
        # Count markers by type
        marker_counts = db.session.query(
            Marker.type,
            db.func.count(Marker.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(Marker.type).all()
        
        stats = {
            'total_markers': sum(count for _, count in marker_counts),
            'by_type': {marker_type: count for marker_type, count in marker_counts},
            'decisions': next((count for marker_type, count in marker_counts if marker_type == 'decision'), 0),
            'todos': next((count for marker_type, count in marker_counts if marker_type == 'todo'), 0),
            'risks': next((count for marker_type, count in marker_counts if marker_type == 'risk'), 0)
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get marker stats: {str(e)}'
        }), 500