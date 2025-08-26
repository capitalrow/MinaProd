"""
Export Routes for M4 functionality.
Handles DOCX and PDF export endpoints.
"""

from flask import Blueprint, send_file, abort
from services.export_service import ExportService
from models.session import Session
from services.session_service import SessionService
from app import db
from io import BytesIO


export_bp = Blueprint('export', __name__)


@export_bp.route('/sessions/<session_identifier>/export.docx')
def export_docx(session_identifier: str):
    """Export session as DOCX file."""
    try:
        # Check if session exists using external ID
        session = SessionService.get_session_by_external(session_identifier)
        if not session:
            abort(404)
        
        # Generate DOCX
        docx_buffer = ExportService.session_to_docx(session.id)
        if not docx_buffer:
            abort(404)
        
        # Generate filename
        safe_title = "".join(c for c in session.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"mina-session-{session_identifier}-{safe_title[:30]}.docx"
        
        return send_file(
            docx_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        abort(500)


@export_bp.route('/sessions/<session_identifier>/export.pdf')
def export_pdf(session_identifier: str):
    """Export session as PDF file."""
    try:
        # Check if session exists using external ID
        session = SessionService.get_session_by_external(session_identifier)
        if not session:
            abort(404)
        
        # Generate PDF
        pdf_buffer = ExportService.session_to_pdf(session.id)
        if not pdf_buffer:
            abort(404)
        
        # Generate filename
        safe_title = "".join(c for c in session.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"mina-session-{session_identifier}-{safe_title[:30]}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        abort(500)


@export_bp.route('/sessions/<session_identifier>/export.txt')
def export_txt(session_identifier: str):
    """Export session as TXT file."""
    try:
        session = SessionService.get_session_by_external(session_identifier)
        if not session: 
            abort(404)
        txt = ExportService.session_to_txt(session.id)
        if txt is None: 
            abort(404)
        
        return send_file(BytesIO(txt.encode('utf-8')), mimetype='text/plain',
                         as_attachment=True, download_name=f"{session_identifier}.txt")
    except Exception as e:
        abort(500)


@export_bp.route('/sessions/<session_identifier>/export.vtt')  
def export_vtt(session_identifier: str):
    """Export session as WebVTT file."""
    try:
        session = SessionService.get_session_by_external(session_identifier)
        if not session: 
            abort(404)
        vtt = ExportService.session_to_vtt(session.id)
        if vtt is None: 
            abort(404)
        
        return send_file(BytesIO(vtt.encode('utf-8')), mimetype='text/vtt',
                         as_attachment=True, download_name=f"{session_identifier}.vtt")
    except Exception as e:
        abort(500)