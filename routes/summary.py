"""
Summary routes (M3) - API endpoints for AI-powered meeting insights.

Provides endpoints for generating and retrieving meeting summaries,
actions, decisions, and risks extracted from session transcripts.
"""

import logging
from flask import Blueprint, request, jsonify, current_app
# from flask_socketio import emit  # Disabled for native WebSocket testing

from services.analysis_service import AnalysisService
# from app import socketio  # Disabled for native WebSocket testing

logger = logging.getLogger(__name__)

# Create summary blueprint
summary_bp = Blueprint('summary', __name__, url_prefix='/sessions')


@summary_bp.route('/<int:session_id>/summarise', methods=['POST'])
def generate_summary(session_id: int):
    """
    Generate AI-powered summary for a session.
    
    Analyses the session transcript and extracts:
    - Meeting summary in markdown format
    - Action items with owners and due dates
    - Key decisions made
    - Identified risks with suggested mitigations
    
    Args:
        session_id: ID of the session to analyse
        
    Returns:
        JSON: Generated summary data with metadata
        
    Status Codes:
        200: Summary generated successfully
        404: Session not found
        400: Invalid request or no segments available
        500: Analysis service error
    """
    try:
        logger.info(f"Request to generate summary for session {session_id}")
        
        # Generate summary using analysis service
        summary_data = AnalysisService.generate_summary(session_id)
        
        logger.info(f"Successfully generated summary {summary_data['id']} for session {session_id}")
        
        return jsonify({
            'success': True,
            'message': f'Summary generated for session {session_id}',
            'summary': summary_data
        }), 200
        
    except ValueError as e:
        logger.warning(f"Summary generation failed for session {session_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404 if 'not found' in str(e) else 400
        
    except Exception as e:
        logger.error(f"Summary generation error for session {session_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate summary'
        }), 500


@summary_bp.route('/<int:session_id>/summary', methods=['GET'])
def get_summary(session_id: int):
    """
    Get the latest summary for a session.
    
    Args:
        session_id: ID of the session
        
    Returns:
        JSON: Summary data or 404 if not found
        
    Status Codes:
        200: Summary found and returned
        404: No summary found for session
    """
    try:
        logger.debug(f"Request to get summary for session {session_id}")
        
        summary_data = AnalysisService.get_session_summary(session_id)
        
        if not summary_data:
            return jsonify({
                'success': False,
                'error': f'No summary found for session {session_id}'
            }), 404
        
        return jsonify({
            'success': True,
            'summary': summary_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving summary for session {session_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve summary'
        }), 500


def trigger_auto_summary(session_id: int):
    """
    Trigger automatic summary generation for a session.
    
    This function is called as a background task when AUTO_SUMMARY_ON_FINALIZE
    is enabled and a session is finalized.
    
    Args:
        session_id: ID of the session to analyze
    """
    try:
        logger.info(f"Auto-generating summary for session {session_id}")
        
        # Generate summary in background
        summary_data = AnalysisService.generate_summary(session_id)
        
        # Emit event to notify clients that summary is ready
        # socketio.emit('summary_generated', { 'session_id': session_id, 'summary_id': summary_data['id'] }, room=f'session_{session_id}')  # Disabled
        
        logger.info(f"Auto-summary {summary_data['id']} generated for session {session_id}")
        
    except Exception as e:
        logger.error(f"Auto-summary generation failed for session {session_id}: {e}")
        
        # Emit error event
        # socketio.emit('summary_error', { 'session_id': session_id, 'error': 'Failed to auto-generate summary' }, room=f'session_{session_id}')  # Disabled