"""
Utility to backfill user_id and workspace_id for existing sessions.
This script helps migrate old sessions that were created before ownership tracking.
"""

from app import app
from models import db, Session, User, Workspace, Meeting
from sqlalchemy import or_

def backfill_session_ownership():
    """Backfill user_id and workspace_id for orphaned sessions."""
    
    with app.app_context():
        print("=== SESSION OWNERSHIP BACKFILL ===\n")
        
        # Find orphaned sessions (no user_id or workspace_id)
        orphaned_sessions = db.session.query(Session).filter(
            or_(Session.user_id.is_(None), Session.workspace_id.is_(None))
        ).all()
        
        print(f"Found {len(orphaned_sessions)} orphaned session(s)\n")
        
        if not orphaned_sessions:
            print("✅ No orphaned sessions found - all sessions have ownership!")
            return
        
        # Get default user and workspace for backfill
        default_user = db.session.query(User).first()
        default_workspace = db.session.query(Workspace).first()
        
        if not default_user or not default_workspace:
            print("❌ Cannot backfill - no users or workspaces exist")
            print("   Create at least one user and workspace first")
            return
        
        print(f"Backfilling with default user: {default_user.username}")
        print(f"Backfilling with default workspace: {default_workspace.name}\n")
        
        updated_count = 0
        for session in orphaned_sessions:
            # Check if session is linked to a meeting
            if session.meeting_id:
                meeting = db.session.query(Meeting).get(session.meeting_id)
                if meeting:
                    # Use meeting's organizer and workspace
                    session.user_id = meeting.organizer_id
                    session.workspace_id = meeting.workspace_id
                    print(f"✅ Session {session.external_id} → Meeting organizer (user={meeting.organizer_id})")
                else:
                    # Fallback to default
                    if not session.user_id:
                        session.user_id = default_user.id
                    if not session.workspace_id:
                        session.workspace_id = default_workspace.id
                    print(f"✅ Session {session.external_id} → Default (user={default_user.id})")
            else:
                # No meeting link - use defaults
                if not session.user_id:
                    session.user_id = default_user.id
                if not session.workspace_id:
                    session.workspace_id = default_workspace.id
                print(f"✅ Session {session.external_id} → Default (user={default_user.id})")
            
            updated_count += 1
        
        db.session.commit()
        
        print(f"\n=== BACKFILL COMPLETE ===")
        print(f"✅ Updated {updated_count} session(s)")
        print(f"✅ All sessions now have ownership tracking")


if __name__ == "__main__":
    backfill_session_ownership()
