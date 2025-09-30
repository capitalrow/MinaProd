"""
Cross-Meeting Insights Routes for Mina.

This module handles API endpoints for cross-meeting insights,
memory graph visualization, and analytics.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from services.cross_meeting_insights import cross_meeting_insights_service

logger = logging.getLogger(__name__)

insights_bp = Blueprint('insights', __name__, url_prefix='/insights')


@insights_bp.route('/api/analyze', methods=['POST'])
@login_required
def analyze_meetings():
    """
    Analyze meetings for cross-meeting insights.
    
    Request Body:
        {
            "days_back": 30,
            "refresh": false
        }
    
    Returns:
        JSON: List of cross-meeting insights
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json() or {}
        days_back = data.get('days_back', 30)
        refresh = data.get('refresh', False)
        
        # Validate days_back
        if not isinstance(days_back, int) or days_back < 1 or days_back > 365:
            return jsonify({
                'success': False,
                'error': 'days_back must be an integer between 1 and 365'
            }), 400
        
        # Clear cache if refresh is requested
        if refresh:
            cache_key = f"{current_user.id}_{days_back}"
            if cache_key in cross_meeting_insights_service.insights_cache:
                del cross_meeting_insights_service.insights_cache[cache_key]
        
        # Analyze meetings
        insights = cross_meeting_insights_service.analyze_meetings(current_user.id, days_back)
        
        # Convert insights to JSON-serializable format
        insights_data = []
        for insight in insights:
            insights_data.append({
                'id': insight.id,
                'type': insight.type.value,
                'title': insight.title,
                'description': insight.description,
                'confidence': insight.confidence,
                'meetings_involved': insight.meetings_involved,
                'entities_involved': insight.entities_involved,
                'evidence': insight.evidence,
                'actionable': insight.actionable,
                'created_at': insight.created_at.isoformat() if insight.created_at else None
            })
        
        return jsonify({
            'success': True,
            'insights': insights_data,
            'total_insights': len(insights_data),
            'days_analyzed': days_back,
            'user_id': current_user.id
        }), 200
    
    except Exception as e:
        logger.error(f"Error analyzing meetings for user {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        }), 500


@insights_bp.route('/api/summary', methods=['GET'])
@login_required
def get_insights_summary():
    """
    Get a summary of insights for the current user.
    
    Returns:
        JSON: Insights summary with statistics
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        summary = cross_meeting_insights_service.get_insights_summary(current_user.id)
        
        return jsonify({
            'success': True,
            'summary': summary
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting insights summary for user {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get insights summary: {str(e)}'
        }), 500


@insights_bp.route('/api/memory-graph', methods=['GET'])
@login_required
def get_memory_graph():
    """
    Get memory graph data for visualization.
    
    Query Parameters:
        focus_type: Optional focus on specific node type (meeting, person, topic, etc.)
    
    Returns:
        JSON: Memory graph data with nodes and edges
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        focus_type = request.args.get('focus_type')
        
        # Validate focus_type if provided
        valid_types = ['meeting', 'person', 'topic', 'decision', 'action_item', 'project', 'keyword']
        if focus_type and focus_type not in valid_types:
            return jsonify({
                'success': False,
                'error': f'Invalid focus_type. Must be one of: {valid_types}'
            }), 400
        
        # Get memory graph data
        graph_data = cross_meeting_insights_service.get_memory_graph_data(current_user.id, focus_type)
        
        return jsonify({
            'success': True,
            'graph': graph_data
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting memory graph for user {current_user.id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get memory graph: {str(e)}'
        }), 500


@insights_bp.route('/api/insights/<insight_id>', methods=['GET'])
@login_required
def get_insight_details(insight_id: str):
    """
    Get detailed information about a specific insight.
    
    Args:
        insight_id: ID of the insight
    
    Returns:
        JSON: Detailed insight information
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        # Get insights from cache
        insights = []
        for cached_insights in cross_meeting_insights_service.insights_cache.values():
            insights.extend(cached_insights)
        
        # Find the specific insight
        insight = None
        for i in insights:
            if i.id == insight_id:
                insight = i
                break
        
        if not insight:
            return jsonify({
                'success': False,
                'error': 'Insight not found'
            }), 404
        
        # Return detailed insight data
        insight_data = {
            'id': insight.id,
            'type': insight.type.value,
            'title': insight.title,
            'description': insight.description,
            'confidence': insight.confidence,
            'meetings_involved': insight.meetings_involved,
            'entities_involved': insight.entities_involved,
            'evidence': insight.evidence,
            'actionable': insight.actionable,
            'created_at': insight.created_at.isoformat() if insight.created_at else None,
            'recommendations': _generate_recommendations(insight)
        }
        
        return jsonify({
            'success': True,
            'insight': insight_data
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting insight details for {insight_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get insight details: {str(e)}'
        }), 500


@insights_bp.route('/api/node/<node_id>/connections', methods=['GET'])
@login_required
def get_node_connections(node_id: str):
    """
    Get connections for a specific node in the memory graph.
    
    Args:
        node_id: ID of the node
    
    Query Parameters:
        relationship_type: Optional filter by relationship type
        max_depth: Maximum depth for traversal (default: 2)
    
    Returns:
        JSON: Node connections and related data
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        relationship_type = request.args.get('relationship_type')
        max_depth = int(request.args.get('max_depth', 2))
        
        # Validate max_depth
        if max_depth < 1 or max_depth > 5:
            return jsonify({
                'success': False,
                'error': 'max_depth must be between 1 and 5'
            }), 400
        
        # Get the node
        node = cross_meeting_insights_service.memory_graph.get_node(node_id)
        if not node:
            return jsonify({
                'success': False,
                'error': 'Node not found'
            }), 404
        
        # Get connected nodes
        connected_nodes = cross_meeting_insights_service.memory_graph.get_connected_nodes(
            node_id, relationship_type
        )
        
        # Convert to JSON format
        connections_data = []
        for connected_node in connected_nodes:
            connections_data.append({
                'id': connected_node.id,
                'label': connected_node.label,
                'type': connected_node.type.value,
                'weight': connected_node.weight,
                'properties': connected_node.properties
            })
        
        return jsonify({
            'success': True,
            'node': {
                'id': node.id,
                'label': node.label,
                'type': node.type.value,
                'weight': node.weight,
                'properties': node.properties
            },
            'connections': connections_data,
            'connection_count': len(connections_data),
            'relationship_type': relationship_type
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting node connections for {node_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get node connections: {str(e)}'
        }), 500


@insights_bp.route('/api/paths/<start_id>/<end_id>', methods=['GET'])
@login_required
def find_paths(start_id: str, end_id: str):
    """
    Find paths between two nodes in the memory graph.
    
    Args:
        start_id: Starting node ID
        end_id: Ending node ID
    
    Query Parameters:
        max_depth: Maximum path depth (default: 3)
    
    Returns:
        JSON: Paths between the nodes
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        max_depth = int(request.args.get('max_depth', 3))
        
        # Validate max_depth
        if max_depth < 1 or max_depth > 5:
            return jsonify({
                'success': False,
                'error': 'max_depth must be between 1 and 5'
            }), 400
        
        # Find paths
        paths = cross_meeting_insights_service.memory_graph.find_paths(start_id, end_id, max_depth)
        
        # Convert paths to include node details
        detailed_paths = []
        for path in paths:
            detailed_path = []
            for node_id in path:
                node = cross_meeting_insights_service.memory_graph.get_node(node_id)
                if node:
                    detailed_path.append({
                        'id': node.id,
                        'label': node.label,
                        'type': node.type.value
                    })
            if detailed_path:
                detailed_paths.append(detailed_path)
        
        return jsonify({
            'success': True,
            'start_node': start_id,
            'end_node': end_id,
            'paths': detailed_paths,
            'path_count': len(detailed_paths),
            'max_depth': max_depth
        }), 200
    
    except Exception as e:
        logger.error(f"Error finding paths from {start_id} to {end_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to find paths: {str(e)}'
        }), 500


@insights_bp.route('/api/insights/types', methods=['GET'])
@login_required
def get_insight_types():
    """
    Get available insight types and their descriptions.
    
    Returns:
        JSON: Insight types with descriptions
    """
    try:
        insight_types = {
            'recurring_topic': {
                'name': 'Recurring Topic',
                'description': 'Topics that appear frequently across multiple meetings',
                'actionable': True
            },
            'decision_thread': {
                'name': 'Decision Thread',
                'description': 'Related decisions that evolve across multiple meetings',
                'actionable': True
            },
            'participant_pattern': {
                'name': 'Participant Pattern',
                'description': 'Frequent collaboration patterns between team members',
                'actionable': False
            },
            'action_follow_up': {
                'name': 'Action Follow-up',
                'description': 'Action items that are followed up in subsequent meetings',
                'actionable': False
            },
            'meeting_frequency': {
                'name': 'Meeting Frequency',
                'description': 'Patterns in meeting frequency and scheduling',
                'actionable': True
            },
            'productivity_trend': {
                'name': 'Productivity Trend',
                'description': 'Trends in meeting productivity and outcomes',
                'actionable': True
            },
            'topic_evolution': {
                'name': 'Topic Evolution',
                'description': 'How topics change and evolve over time',
                'actionable': False
            },
            'collaboration_network': {
                'name': 'Collaboration Network',
                'description': 'Network structure of team collaboration',
                'actionable': False
            }
        }
        
        return jsonify({
            'success': True,
            'insight_types': insight_types
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting insight types: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get insight types: {str(e)}'
        }), 500


def _generate_recommendations(insight):
    """Generate actionable recommendations based on insight type."""
    recommendations = []
    
    if insight.type.value == 'recurring_topic':
        recommendations = [
            "Consider creating a dedicated project or workstream for this topic",
            "Schedule focused deep-dive sessions on this topic",
            "Document key decisions and outcomes related to this topic"
        ]
    elif insight.type.value == 'decision_thread':
        recommendations = [
            "Review the decision evolution and document the rationale",
            "Ensure all stakeholders are aligned on the current decision",
            "Consider setting up decision checkpoints for future changes"
        ]
    elif insight.type.value == 'productivity_trend':
        if 'trend' in insight.evidence and insight.evidence['trend'] == 'declining':
            recommendations = [
                "Review meeting agendas and time management",
                "Consider shorter, more focused meetings",
                "Ensure clear action items and decision points"
            ]
        else:
            recommendations = [
                "Continue current meeting practices",
                "Share successful patterns with other teams",
                "Document best practices for future reference"
            ]
    else:
        recommendations = [
            "Monitor this pattern for future changes",
            "Consider discussing this insight with your team",
            "Use this information for planning future meetings"
        ]
    
    return recommendations