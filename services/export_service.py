"""
Export Service (M2.5 + M4)
Service for exporting sessions to various formats: Markdown, DOCX, and PDF.
"""

import io
from typing import Optional
from datetime import datetime
from services.session_service import SessionService

# M4 Export dependencies
from docx import Document
from docx.shared import Inches
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


class ExportService:
    """Service class for exporting session data to various formats."""
    
    @staticmethod
    def session_to_markdown(session_id: int) -> Optional[str]:
        """
        Convert a session to Markdown format.
        
        Args:
            session_id: Database session ID
            
        Returns:
            Markdown string or None if session not found
        """
        # Get session detail with segments
        session_detail = SessionService.get_session_detail(session_id)
        if not session_detail:
            return None
        
        session = session_detail['session']
        segments = session_detail['segments']
        
        # Start building markdown
        md_lines = []
        
        # Header
        md_lines.append(f"# {session['title']}")
        md_lines.append("")
        
        # Session metadata
        md_lines.append("## Session Information")
        md_lines.append("")
        md_lines.append(f"- **Session ID:** `{session['external_id']}`")
        md_lines.append(f"- **Status:** {session['status'].title()}")
        
        if session.get('started_at'):
            started = session['started_at'].replace('T', ' ')[:16]
            md_lines.append(f"- **Started:** {started}")
        
        if session.get('completed_at'):
            completed = session['completed_at'].replace('T', ' ')[:16]
            md_lines.append(f"- **Completed:** {completed}")
        
        if session.get('locale'):
            md_lines.append(f"- **Language:** {session['locale']}")
        
        md_lines.append(f"- **Total Segments:** {session['segments_count']}")
        
        # Device info if available
        if session.get('device_info'):
            md_lines.append("- **Device Information:**")
            for key, value in session['device_info'].items():
                md_lines.append(f"  - {key.title()}: {value}")
        
        md_lines.append("")
        
        # Transcript section
        if segments:
            md_lines.append("## Transcript")
            md_lines.append("")
            
            # Separate final and interim segments
            final_segments = [s for s in segments if s.get('is_final')]
            interim_segments = [s for s in segments if not s.get('is_final')]
            
            # Export final segments first (main transcript)
            if final_segments:
                md_lines.append("### Final Transcript")
                md_lines.append("")
                
                for segment in final_segments:
                    timestamp = segment.get('start_time_formatted', '00:00')
                    confidence = segment.get('avg_confidence')
                    text = segment.get('text', '').strip()
                    
                    if confidence:
                        conf_display = f" *(confidence: {confidence*100:.1f}%)*"
                    else:
                        conf_display = ""
                    
                    md_lines.append(f"**[{timestamp}]** {text}{conf_display}")
                    md_lines.append("")
            
            # Add interim segments if no final segments exist
            if not final_segments and interim_segments:
                md_lines.append("### Interim Results")
                md_lines.append("")
                md_lines.append("*Note: This session contains only interim transcription results.*")
                md_lines.append("")
                
                for segment in interim_segments[:10]:  # Limit interim to first 10
                    timestamp = segment.get('start_time_formatted', '00:00')
                    confidence = segment.get('avg_confidence')
                    text = segment.get('text', '').strip()
                    
                    if confidence:
                        conf_display = f" *(confidence: {confidence*100:.1f}%)*"
                    else:
                        conf_display = ""
                    
                    md_lines.append(f"**[{timestamp}]** {text}{conf_display}")
                    md_lines.append("")
                
                if len(interim_segments) > 10:
                    md_lines.append(f"*... and {len(interim_segments) - 10} more interim segments*")
                    md_lines.append("")
            
        else:
            md_lines.append("## Transcript")
            md_lines.append("")
            md_lines.append("*No transcript available for this session.*")
            md_lines.append("")
        
        # Footer
        md_lines.append("---")
        md_lines.append("")
        md_lines.append("*Exported from Mina - Meeting Insights & Action Platform*")
        md_lines.append(f"*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*")
        md_lines.append(f"*Engine: OpenAI Whisper API*")
        
        return "\n".join(md_lines)
    
    @staticmethod
    def session_to_docx(session_id: int) -> Optional[io.BytesIO]:
        """
        Convert a session to DOCX format.
        
        Args:
            session_id: Database session ID
            
        Returns:
            BytesIO buffer containing DOCX data or None if session not found
        """
        # Get session detail
        session_detail = SessionService.get_session_detail(session_id)
        if not session_detail:
            return None
        
        session = session_detail['session']
        segments = session_detail['segments']
        
        # Create Word document
        doc = Document()
        
        # Title
        title = doc.add_heading(session['title'], 0)
        title.alignment = 1  # Center alignment
        
        # Session info table
        doc.add_heading('Session Information', level=1)
        info_table = doc.add_table(rows=4, cols=2)
        info_table.style = 'Light Grid Accent 1'
        
        info_data = [
            ('Session ID', session['external_id']),
            ('Status', session['status'].title()),
            ('Started', session['started_at'][:16].replace('T', ' ') if session.get('started_at') else 'N/A'),
            ('Language', session.get('locale', 'Not specified'))
        ]
        
        for i, (label, value) in enumerate(info_data):
            info_table.cell(i, 0).text = label
            info_table.cell(i, 1).text = str(value)
        
        # Transcript section
        doc.add_heading('Transcript', level=1)
        
        if segments:
            for segment in segments:
                # Add timestamp
                timestamp = segment.get('start_time', '')
                if timestamp:
                    timestamp_str = str(timestamp)[:8] if isinstance(timestamp, str) else 'N/A'
                else:
                    timestamp_str = 'N/A'
                
                # Add segment with formatting
                p = doc.add_paragraph()
                p.add_run(f"[{timestamp_str}] ").bold = True
                p.add_run(segment.get('text', ''))
        else:
            doc.add_paragraph('No transcript available for this session.')
        
        # Save to BytesIO
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def session_to_pdf(session_id: int) -> Optional[io.BytesIO]:
        """
        Convert a session to PDF format.
        
        Args:
            session_id: Database session ID
            
        Returns:
            BytesIO buffer containing PDF data or None if session not found
        """
        # Get session detail
        session_detail = SessionService.get_session_detail(session_id)
        if not session_detail:
            return None
        
        session = session_detail['session']
        segments = session_detail['segments']
        
        # Create PDF document
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            alignment=1,  # Center
            spaceAfter=30
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.darkblue,
            spaceAfter=12
        )
        
        # Build story
        story = []
        
        # Title
        story.append(Paragraph(session['title'], title_style))
        story.append(Spacer(1, 20))
        
        # Session information table
        story.append(Paragraph('Session Information', heading_style))
        
        info_data = [
            ['Session ID', session['external_id']],
            ['Status', session['status'].title()],
            ['Started', session['started_at'][:16].replace('T', ' ') if session.get('started_at') else 'N/A'],
            ['Language', session.get('locale', 'Not specified')],
            ['Segments', str(len(segments))]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Transcript section
        story.append(Paragraph('Transcript', heading_style))
        
        if segments:
            for segment in segments:
                # Format timestamp
                timestamp = segment.get('start_time', '')
                timestamp_str = str(timestamp)[:8] if isinstance(timestamp, str) else 'N/A'
                
                # Create segment text
                text = f"<b>[{timestamp_str}]</b> {segment.get('text', '')}"
                story.append(Paragraph(text, styles['Normal']))
                story.append(Spacer(1, 8))
        else:
            story.append(Paragraph('No transcript available for this session.', styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def get_export_filename(session_id: int, format_type: str = "md") -> str:
        """
        Generate appropriate filename for export.
        
        Args:
            session_id: Database session ID
            format_type: Export format ('md', 'txt', 'json', etc.)
            
        Returns:
            Suggested filename
        """
        # Get session for title
        session = SessionService.get_session_by_id(session_id)
        if session:
            # Sanitize title for filename
            safe_title = "".join(c for c in session.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '-').lower()[:30]  # Limit length
            return f"mina-{safe_title}-{session_id}.{format_type}"
        else:
            return f"mina-session-{session_id}.{format_type}"
    
    @staticmethod
    def session_to_txt(session_id: int) -> Optional[str]:
        """Convert a session to plain text format."""
        d = SessionService.get_session_detail(session_id)
        if not d: 
            return None
        finals = [s['text'].strip() for s in d['segments'] if s.get('is_final')]
        return "\n".join(finals)
    
    @staticmethod
    def session_to_vtt(session_id: int) -> Optional[str]:
        """Convert a session to WebVTT subtitle format."""
        d = SessionService.get_session_detail(session_id)
        if not d: 
            return None
        lines = ["WEBVTT", ""]
        for s in d['segments']:
            if not s.get('is_final'): 
                continue
            start = s.get('start_time_formatted','00:00.000').replace('.',',')
            end = s.get('end_time_formatted','00:00.000').replace('.',',')
            lines += [f"{start} --> {end}", s.get('text','').strip(), ""]
        return "\n".join(lines)