"""
Export Service (M2.5)
Service for exporting sessions to various formats, starting with Markdown.
"""

from typing import Optional
from datetime import datetime
from services.session_service import SessionService


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