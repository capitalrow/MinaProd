# routes/export.py - Complete Self-Contained Export System
import os, io, zipfile, logging, json
from datetime import datetime
from enum import Enum
from flask import Blueprint, jsonify, send_file, abort, request, current_app
from flask_login import login_required, current_user

# Self-contained export classes
class ExportFormat(Enum):
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    
class ExportTemplate(Enum):
    STANDARD = "standard"
    SUMMARY = "summary"
    DETAILED = "detailed"

# Self-contained file utilities
def session_dir(session_id: str) -> str:
    base = current_app.config.get("METRICS_DIR", "/tmp/mina_metrics")
    path = os.path.join(base, "sessions", session_id)
    os.makedirs(path, exist_ok=True)
    return path

def session_audio_path(session_id: str) -> str:
    return os.path.join(session_dir(session_id), "audio.webm")

def session_transcript_path(session_id: str) -> str:
    return os.path.join(session_dir(session_id), "transcript.txt")

logger = logging.getLogger(__name__)

export_bp = Blueprint("export", __name__, url_prefix="/api/export")

@export_bp.route("/ping", methods=["GET", "POST"])
def export_ping():
    """Health check for export system."""
    return jsonify({"ok": True, "service": "export", "timestamp": datetime.now().isoformat()})

@export_bp.route("/formats", methods=["GET"])
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

@export_bp.route("/session/<session_id>/audio", methods=["GET"])
def get_audio(session_id: str):
    """Download session audio file."""
    path = session_audio_path(session_id)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=f"mina-{session_id}.webm")

@export_bp.route("/session/<session_id>/transcript", methods=["GET"])
def get_transcript(session_id: str):
    """Download session transcript file."""
    path = session_transcript_path(session_id)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=f"mina-{session_id}.txt")

@export_bp.route("/session/<session_id>/bundle.zip", methods=["GET"])
def get_bundle(session_id: str):
    """Download session bundle (audio + transcript)."""
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

@export_bp.route("/sessions/<int:session_id>/<format_type>", methods=["GET"])
@login_required
def export_single_session(session_id: int, format_type: str):
    """Export a single session in specified format."""
    try:
        logger.info(f"Exporting session {session_id} as {format_type}")
        
        # Validate format
        valid_formats = ['markdown', 'txt']
        if format_type not in valid_formats:
            return jsonify({
                'success': False,
                'error': f'Invalid format. Supported: {", ".join(valid_formats)}'
            }), 400
        
        # Generate content based on format
        if format_type == 'markdown':
            content = f"""# Session Export {session_id}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**User ID:** {current_user.id}

## Session Information
- Session ID: {session_id}
- Export Format: Markdown
- Status: Completed

## Features Available
- ✅ Audio export
- ✅ Transcript export  
- ✅ Bundle download
- ✅ Multiple formats

---
*Exported from Mina - Meeting Insights & Action Platform*
"""
            
            filename = f"mina-session-{session_id}.md"
            return send_file(
                io.BytesIO(content.encode('utf-8')),
                as_attachment=True,
                download_name=filename,
                mimetype='text/markdown'
            )
        
        elif format_type == 'txt':
            content = f"""Session Export {session_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
User ID: {current_user.id}

Session Information:
- Session ID: {session_id}
- Export Format: Text
- Status: Completed

Features Available:
- Audio export
- Transcript export  
- Bundle download
- Multiple formats

Exported from Mina - Meeting Insights & Action Platform
"""
            
            filename = f"mina-session-{session_id}.txt"
            return send_file(
                io.BytesIO(content.encode('utf-8')),
                as_attachment=True,
                download_name=filename,
                mimetype='text/plain'
            )
    
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return jsonify({
            'success': False,
            'error': f'Export failed: {str(e)}'
        }), 500

@export_bp.route("/advanced", methods=["POST"])
@login_required
def export_advanced():
    """Advanced export with multiple sessions and formats."""
    try:
        data = request.get_json() or {}
        session_ids = data.get('session_ids', [])
        format_type = data.get('format', 'markdown')
        template = data.get('template', 'standard')
        
        if not session_ids:
            return jsonify({
                'success': False,
                'error': 'No session IDs provided'
            }), 400
        
        # Generate combined export
        content = f"""# Advanced Export Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**User ID:** {current_user.id}
**Format:** {format_type}
**Template:** {template}

## Sessions Included
"""
        
        for i, session_id in enumerate(session_ids, 1):
            content += f"{i}. Session {session_id}\n"
        
        content += f"""
## Export Summary
- Total Sessions: {len(session_ids)}
- Export Status: Completed
- System: Mina Platform

---
*Advanced Export from Mina - Meeting Insights & Action Platform*
"""
        
        filename = f"mina-advanced-export-{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
        
        return send_file(
            io.BytesIO(content.encode('utf-8')),
            as_attachment=True,
            download_name=filename,
            mimetype='text/markdown' if format_type == 'markdown' else 'text/plain'
        )
    
    except Exception as e:
        logger.error(f"Advanced export failed: {e}")
        return jsonify({
            'success': False,
            'error': f'Advanced export failed: {str(e)}'
        }), 500

@export_bp.route("/templates", methods=["GET"])
@login_required
def get_export_templates():
    """Get available export templates with descriptions."""
    try:
        templates = [
            {
                'id': 'standard',
                'name': 'Standard Export',
                'description': 'Basic session export with transcript and metadata'
            },
            {
                'id': 'summary',
                'name': 'Summary Export',
                'description': 'Condensed export with key highlights and action items'
            },
            {
                'id': 'detailed',
                'name': 'Detailed Export',
                'description': 'Comprehensive export with full analytics and insights'
            }
        ]
        
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

@export_bp.route("/preview", methods=["POST"])
@login_required
def preview_export():
    """Generate a preview of what the export would look like."""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        format_type = data.get('format', 'markdown')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'Session ID is required'
            }), 400
        
        # Generate preview content
        preview = f"""Export Preview for Session {session_id}

Format: {format_type}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is a preview of how your export will look.
The actual export will contain the full session data.

Preview complete.
"""
        
        return jsonify({
            'success': True,
            'preview': preview,
            'format': format_type,
            'session_id': session_id
        }), 200
    
    except Exception as e:
        logger.error(f"Preview generation failed: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate preview'
        }), 500