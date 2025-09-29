# routes/export.py
import os, io, zipfile, logging
from flask import Blueprint, jsonify, send_file, abort, request
from flask_login import login_required, current_user

from services.files import session_audio_path, session_transcript_path
from services.export_service import (
    ExportService, 
    advanced_export_service,
    ExportRequest,
    ExportFormat,
    ExportTemplate
)

logger = logging.getLogger(__name__)

export_bp = Blueprint("export", __name__)

@export_bp.route("/export/ping", methods=["GET"])
def export_ping():
    return jsonify({"ok": True})

@export_bp.route("/session/<session_id>/audio", methods=["GET"])
def get_audio(session_id: str):
    path = session_audio_path(session_id)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=f"mina-{session_id}.webm")

@export_bp.route("/session/<session_id>/transcript", methods=["GET"])
def get_transcript(session_id: str):
    path = session_transcript_path(session_id)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=f"mina-{session_id}.txt")

@export_bp.route("/session/<session_id>/bundle.zip", methods=["GET"])
def get_bundle(session_id: str):
    audio = session_audio_path(session_id)
    txt = session_transcript_path(session_id)
    if not os.path.isfile(audio) and not os.path.isfile(txt):
        abort(404)

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.isfile(audio): zf.write(audio, f"mina-{session_id}.webm")
        if os.path.isfile(txt):   zf.write(txt,   f"mina-{session_id}.txt")
    mem.seek(0)
    return send_file(mem, as_attachment=True, download_name=f"mina-{session_id}.zip")


# Advanced Export Routes
@export_bp.route("/api/formats", methods=["GET"])
@login_required
def get_export_formats():
    """Get available export formats and templates."""
    try:
        return jsonify({
            'success': True,
            'formats': [format.value for format in ExportFormat],
            'templates': [template.value for template in ExportTemplate]
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving export formats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve export formats'
        }), 500


@export_bp.route("/api/sessions/<int:session_id>/<format_type>", methods=["GET"])
@login_required
def export_single_session_legacy(session_id: int, format_type: str):
    """Export a single session using enhanced legacy export functionality."""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        # Map format types to legacy methods
        if format_type == 'md' or format_type == 'markdown':
            content = ExportService.session_to_markdown(session_id)
            if content is None:
                abort(404)
            
            filename = ExportService.get_export_filename(session_id, 'md')
            return send_file(
                io.BytesIO(content.encode('utf-8')),
                as_attachment=True,
                download_name=filename,
                mimetype='text/markdown'
            )
        
        elif format_type == 'pdf':
            buffer = ExportService.session_to_pdf(session_id)
            if buffer is None:
                abort(404)
                
            filename = ExportService.get_export_filename(session_id, 'pdf')
            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        
        elif format_type == 'docx':
            buffer = ExportService.session_to_docx(session_id)
            if buffer is None:
                abort(404)
                
            filename = ExportService.get_export_filename(session_id, 'docx')
            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        
        elif format_type == 'txt':
            content = ExportService.session_to_txt(session_id)
            if content is None:
                abort(404)
                
            filename = ExportService.get_export_filename(session_id, 'txt')
            return send_file(
                io.BytesIO(content.encode('utf-8')),
                as_attachment=True,
                download_name=filename,
                mimetype='text/plain'
            )
        
        elif format_type == 'vtt':
            content = ExportService.session_to_vtt(session_id)
            if content is None:
                abort(404)
                
            filename = ExportService.get_export_filename(session_id, 'vtt')
            return send_file(
                io.BytesIO(content.encode('utf-8')),
                as_attachment=True,
                download_name=filename,
                mimetype='text/vtt'
            )
        
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported format: {format_type}'
            }), 400
    
    except Exception as e:
        logger.error(f"Error exporting session {session_id} to {format_type}: {e}")
        return jsonify({
            'success': False,
            'error': f'Export failed: {str(e)}'
        }), 500


@export_bp.route("/api/advanced", methods=["POST"])
@login_required
def export_advanced():
    """Export multiple sessions with advanced formatting options."""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json() or {}
        
        # Validate required fields
        session_ids = data.get('session_ids', [])
        if not session_ids:
            return jsonify({
                'success': False,
                'error': 'session_ids is required and must be a non-empty list'
            }), 400
        
        # Validate format
        format_str = data.get('format', 'pdf').lower()
        try:
            export_format = ExportFormat(format_str)
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid format: {format_str}. Must be one of: {[f.value for f in ExportFormat]}'
            }), 400
        
        # Validate template
        template_str = data.get('template', 'standard').lower()
        try:
            export_template = ExportTemplate(template_str)
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid template: {template_str}. Must be one of: {[t.value for t in ExportTemplate]}'
            }), 400
        
        # Create export request
        export_request = ExportRequest(
            format=export_format,
            template=export_template,
            session_ids=session_ids,
            include_transcript=data.get('include_transcript', True),
            include_summary=data.get('include_summary', True),
            include_tasks=data.get('include_tasks', True),
            include_analytics=data.get('include_analytics', False),
            custom_title=data.get('custom_title'),
            custom_header=data.get('custom_header'),
            custom_footer=data.get('custom_footer')
        )
        
        # Perform export
        result = advanced_export_service.export_multiple_sessions(export_request)
        
        if not result.success:
            return jsonify({
                'success': False,
                'error': result.error_message
            }), 500
        
        # Determine MIME type
        mime_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'markdown': 'text/markdown',
            'html': 'text/html',
            'txt': 'text/plain'
        }
        
        mime_type = mime_types.get(export_format.value, 'application/octet-stream')
        
        # Return file
        return send_file(
            io.BytesIO(result.file_content),
            as_attachment=True,
            download_name=result.filename,
            mimetype=mime_type
        )
    
    except Exception as e:
        logger.error(f"Error in advanced export: {e}")
        return jsonify({
            'success': False,
            'error': f'Export failed: {str(e)}'
        }), 500


@export_bp.route("/api/templates", methods=["GET"])
@login_required
def get_export_templates():
    """Get available export templates with descriptions."""
    try:
        templates = {
            'standard': {
                'name': 'Standard',
                'description': 'Clean, professional format suitable for most use cases',
                'features': ['Full transcript', 'Summary sections', 'Task lists', 'Professional styling']
            },
            'executive': {
                'name': 'Executive',
                'description': 'Concise format focused on key decisions and action items',
                'features': ['Executive summary', 'Key decisions', 'Action items', 'Minimal transcript']
            },
            'technical': {
                'name': 'Technical',
                'description': 'Detailed format with technical annotations and metadata',
                'features': ['Full transcript', 'Confidence scores', 'Timestamps', 'Technical details']
            },
            'minimal': {
                'name': 'Minimal',
                'description': 'Simple, clean format with essential information only',
                'features': ['Basic summary', 'Key points', 'Clean typography']
            },
            'branded': {
                'name': 'Branded',
                'description': 'Professional format with Mina branding and styling',
                'features': ['Company branding', 'Professional styling', 'Full content', 'Enhanced visuals']
            }
        }
        
        return jsonify({
            'success': True,
            'templates': templates
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving export templates: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve export templates'
        }), 500


@export_bp.route("/api/preview", methods=["POST"])
@login_required
def preview_export():
    """Generate a preview of what the export would look like."""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        data = request.get_json() or {}
        
        session_ids = data.get('session_ids', [])
        if not session_ids:
            return jsonify({
                'success': False,
                'error': 'session_ids is required'
            }), 400
        
        # Get session data for preview
        sessions_data = advanced_export_service.get_session_data_advanced(session_ids)
        
        if not sessions_data:
            return jsonify({
                'success': False,
                'error': 'No session data found'
            }), 404
        
        # Generate preview information
        preview_info = {
            'sessions_count': len(sessions_data),
            'estimated_pages': len(sessions_data) * 3,  # Rough estimate
            'content_breakdown': {
                'total_segments': sum(len(s['transcript']) for s in sessions_data),
                'total_tasks': sum(len(s['tasks']) for s in sessions_data),
                'has_summaries': sum(1 for s in sessions_data if s['summary']),
                'date_range': {
                    'earliest': min(s.get('started_at', '') for s in sessions_data if s.get('started_at')),
                    'latest': max(s.get('started_at', '') for s in sessions_data if s.get('started_at'))
                }
            },
            'sessions': [
                {
                    'id': s['id'],
                    'title': s['title'],
                    'date': s.get('started_at', ''),
                    'segments_count': len(s['transcript']),
                    'tasks_count': len(s['tasks']),
                    'has_summary': bool(s['summary'])
                }
                for s in sessions_data
            ]
        }
        
        return jsonify({
            'success': True,
            'preview': preview_info,
            'format': data.get('format', 'pdf'),
            'template': data.get('template', 'standard')
        }), 200
    
    except Exception as e:
        logger.error(f"Error generating export preview: {e}")
        return jsonify({
            'success': False,
            'error': f'Preview generation failed: {str(e)}'
        }), 500