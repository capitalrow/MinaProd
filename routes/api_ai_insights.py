"""
AI Insights API Routes
REST API endpoints for AI-powered meeting analysis.
Part of Phase 2: Transcript Experience Enhancement (T2.11-T2.22)
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Meeting, Session, Segment
import logging

logger = logging.getLogger(__name__)

# Import AI service
try:
    from services.ai_insights_service import ai_insights_service
    AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AI Insights Service not available: {e}")
    AI_AVAILABLE = False
    ai_insights_service = None

api_ai_insights_bp = Blueprint('api_ai_insights', __name__, url_prefix='/api/meetings')


@api_ai_insights_bp.route('/<int:meeting_id>/ai/insights', methods=['GET'])
@login_required
def get_ai_insights(meeting_id):
    """
    Get comprehensive AI insights for a meeting.
    Implements T2.11-T2.17: Summary, key points, action items, questions, decisions, sentiment, topics.
    """
    # Verify meeting ownership
    meeting = db.session.query(Meeting).filter_by(
        id=meeting_id,
        workspace_id=current_user.workspace_id
    ).first()
    
    if not meeting:
        return jsonify({'success': False, 'message': 'Meeting not found'}), 404
    
    if not AI_AVAILABLE or not ai_insights_service or not ai_insights_service.is_available():
        return jsonify({
            'success': False,
            'message': 'AI insights not available. Please configure OPENAI_API_KEY.',
            'ai_available': False
        }), 503
    
    # Get transcript text
    transcript_text = get_meeting_transcript(meeting)
    
    if not transcript_text:
        return jsonify({
            'success': False,
            'message': 'No transcript available for this meeting'
        }), 404
    
    # Check if insights already cached (in production, check database)
    # For now, generate fresh insights
    try:
        insights = ai_insights_service.generate_comprehensive_insights(
            transcript_text,
            metadata={
                'meeting_id': meeting.id,
                'title': meeting.title,
                'date': meeting.created_at.isoformat() if meeting.created_at else None
            }
        )
        
        return jsonify({
            'success': True,
            'insights': insights,
            'meeting_id': meeting_id
        })
    
    except Exception as e:
        logger.error(f"Failed to generate insights for meeting {meeting_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Error generating insights: {str(e)}'
        }), 500


@api_ai_insights_bp.route('/<int:meeting_id>/ai/summary', methods=['GET'])
@login_required
def get_ai_summary(meeting_id):
    """T2.11: Get AI-generated summary."""
    meeting = db.session.query(Meeting).filter_by(
        id=meeting_id,
        workspace_id=current_user.workspace_id
    ).first()
    
    if not meeting:
        return jsonify({'success': False, 'message': 'Meeting not found'}), 404
    
    if not AI_AVAILABLE or not ai_insights_service:
        return jsonify({'success': False, 'message': 'AI not available'}), 503
    
    transcript = get_meeting_transcript(meeting)
    if not transcript:
        return jsonify({'success': False, 'message': 'No transcript'}), 404
    
    try:
        summary = ai_insights_service.generate_summary(transcript)
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_ai_insights_bp.route('/<int:meeting_id>/ai/key-points', methods=['GET'])
@login_required
def get_key_points(meeting_id):
    """T2.12: Get AI-extracted key points."""
    meeting = db.session.query(Meeting).filter_by(
        id=meeting_id,
        workspace_id=current_user.workspace_id
    ).first()
    
    if not meeting:
        return jsonify({'success': False, 'message': 'Meeting not found'}), 404
    
    if not AI_AVAILABLE or not ai_insights_service:
        return jsonify({'success': False, 'message': 'AI not available'}), 503
    
    transcript = get_meeting_transcript(meeting)
    if not transcript:
        return jsonify({'success': False, 'message': 'No transcript'}), 404
    
    try:
        key_points = ai_insights_service.extract_key_points(transcript)
        return jsonify({'success': True, 'key_points': key_points})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_ai_insights_bp.route('/<int:meeting_id>/ai/action-items', methods=['GET'])
@login_required
def get_action_items(meeting_id):
    """T2.13: Get AI-extracted action items."""
    meeting = db.session.query(Meeting).filter_by(
        id=meeting_id,
        workspace_id=current_user.workspace_id
    ).first()
    
    if not meeting:
        return jsonify({'success': False, 'message': 'Meeting not found'}), 404
    
    if not AI_AVAILABLE or not ai_insights_service:
        return jsonify({'success': False, 'message': 'AI not available'}), 503
    
    transcript = get_meeting_transcript(meeting)
    if not transcript:
        return jsonify({'success': False, 'message': 'No transcript'}), 404
    
    try:
        action_items = ai_insights_service.extract_action_items(transcript)
        return jsonify({'success': True, 'action_items': action_items})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_ai_insights_bp.route('/<int:meeting_id>/ai/questions', methods=['GET'])
@login_required
def get_questions(meeting_id):
    """T2.14: Get AI-extracted questions."""
    meeting = db.session.query(Meeting).filter_by(
        id=meeting_id,
        workspace_id=current_user.workspace_id
    ).first()
    
    if not meeting:
        return jsonify({'success': False, 'message': 'Meeting not found'}), 404
    
    if not AI_AVAILABLE or not ai_insights_service:
        return jsonify({'success': False, 'message': 'AI not available'}), 503
    
    transcript = get_meeting_transcript(meeting)
    if not transcript:
        return jsonify({'success': False, 'message': 'No transcript'}), 404
    
    try:
        questions = ai_insights_service.extract_questions(transcript)
        return jsonify({'success': True, 'questions': questions})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_ai_insights_bp.route('/<int:meeting_id>/ai/decisions', methods=['GET'])
@login_required
def get_decisions(meeting_id):
    """T2.15: Get AI-extracted decisions."""
    meeting = db.session.query(Meeting).filter_by(
        id=meeting_id,
        workspace_id=current_user.workspace_id
    ).first()
    
    if not meeting:
        return jsonify({'success': False, 'message': 'Meeting not found'}), 404
    
    if not AI_AVAILABLE or not ai_insights_service:
        return jsonify({'success': False, 'message': 'AI not available'}), 503
    
    transcript = get_meeting_transcript(meeting)
    if not transcript:
        return jsonify({'success': False, 'message': 'No transcript'}), 404
    
    try:
        decisions = ai_insights_service.extract_decisions(transcript)
        return jsonify({'success': True, 'decisions': decisions})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_ai_insights_bp.route('/<int:meeting_id>/ai/sentiment', methods=['GET'])
@login_required
def get_sentiment(meeting_id):
    """T2.16: Get AI sentiment analysis."""
    meeting = db.session.query(Meeting).filter_by(
        id=meeting_id,
        workspace_id=current_user.workspace_id
    ).first()
    
    if not meeting:
        return jsonify({'success': False, 'message': 'Meeting not found'}), 404
    
    if not AI_AVAILABLE or not ai_insights_service:
        return jsonify({'success': False, 'message': 'AI not available'}), 503
    
    transcript = get_meeting_transcript(meeting)
    if not transcript:
        return jsonify({'success': False, 'message': 'No transcript'}), 404
    
    try:
        sentiment = ai_insights_service.analyze_sentiment(transcript)
        return jsonify({'success': True, 'sentiment': sentiment})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_ai_insights_bp.route('/<int:meeting_id>/ai/topics', methods=['GET'])
@login_required
def get_topics(meeting_id):
    """T2.17: Get AI-detected topics."""
    meeting = db.session.query(Meeting).filter_by(
        id=meeting_id,
        workspace_id=current_user.workspace_id
    ).first()
    
    if not meeting:
        return jsonify({'success': False, 'message': 'Meeting not found'}), 404
    
    if not AI_AVAILABLE or not ai_insights_service:
        return jsonify({'success': False, 'message': 'AI not available'}), 503
    
    transcript = get_meeting_transcript(meeting)
    if not transcript:
        return jsonify({'success': False, 'message': 'No transcript'}), 404
    
    try:
        topics = ai_insights_service.detect_topics(transcript)
        return jsonify({'success': True, 'topics': topics})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_ai_insights_bp.route('/<int:meeting_id>/ai/custom-prompt', methods=['POST'])
@login_required
def execute_custom_prompt(meeting_id):
    """T2.19: Execute custom AI prompt on transcript."""
    meeting = db.session.query(Meeting).filter_by(
        id=meeting_id,
        workspace_id=current_user.workspace_id
    ).first()
    
    if not meeting:
        return jsonify({'success': False, 'message': 'Meeting not found'}), 404
    
    if not AI_AVAILABLE or not ai_insights_service:
        return jsonify({'success': False, 'message': 'AI not available'}), 503
    
    data = request.get_json()
    custom_prompt = data.get('prompt', '').strip()
    
    if not custom_prompt:
        return jsonify({'success': False, 'message': 'Prompt is required'}), 400
    
    transcript = get_meeting_transcript(meeting)
    if not transcript:
        return jsonify({'success': False, 'message': 'No transcript'}), 404
    
    try:
        result = ai_insights_service.execute_custom_prompt(transcript, custom_prompt)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_ai_insights_bp.route('/<int:meeting_id>/ai/cost-estimate', methods=['GET'])
@login_required
def get_cost_estimate(meeting_id):
    """T2.20: Get estimated cost for AI processing."""
    meeting = db.session.query(Meeting).filter_by(
        id=meeting_id,
        workspace_id=current_user.workspace_id
    ).first()
    
    if not meeting:
        return jsonify({'success': False, 'message': 'Meeting not found'}), 404
    
    if not AI_AVAILABLE or not ai_insights_service:
        return jsonify({'success': False, 'message': 'AI not available'}), 503
    
    transcript = get_meeting_transcript(meeting)
    if not transcript:
        return jsonify({'success': False, 'message': 'No transcript'}), 404
    
    try:
        cost_estimate = ai_insights_service.estimate_cost(len(transcript))
        return jsonify({'success': True, 'cost_estimate': cost_estimate})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# Helper Functions
# ============================================

def get_meeting_transcript(meeting: Meeting) -> str:
    """Get full transcript text for a meeting."""
    if not meeting.session_id:
        return ""
    
    session = db.session.query(Session).filter_by(external_id=meeting.session_id).first()
    if not session:
        return ""
    
    segments = db.session.query(Segment).filter_by(
        session_id=session.id,
        kind='final'
    ).order_by(Segment.start_ms.asc()).all()
    
    if not segments:
        return ""
    
    # Build transcript with speaker labels
    transcript_lines = []
    for segment in segments:
        speaker = getattr(segment, 'speaker_name', None) or getattr(segment, 'speaker_id', 'Speaker')
        transcript_lines.append(f"{speaker}: {segment.text}")
    
    return "\n".join(transcript_lines)
