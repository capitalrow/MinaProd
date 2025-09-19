# services/share_service.py
from datetime import datetime, timedelta, timezone
import secrets
import uuid

from app_refactored import db
from models import SharedLink, Meeting

# Helper: generate a short, URL-safe token
def _new_token() -> str:
    # 22–24 chars urlsafe token is fine; keep stable for existing links
    return secrets.token_urlsafe(18)

def create_share_link(meeting_id: int, expires_in_hours: int | None = 72) -> SharedLink:
    """
    Create (or refresh) a share link for a meeting.
    If one already exists and isn't expired, return it.
    """
    meeting = db.session.get(Meeting, meeting_id)
    if not meeting:
        raise ValueError(f"Meeting {meeting_id} not found")

    existing = SharedLink.query.filter_by(meeting_id=meeting_id).first()
    if existing and (not existing.expires_at or existing.expires_at > datetime.now(timezone.utc)):
        return existing

    token = _new_token()
    expires_at = (
        datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        if expires_in_hours
        else None
    )

    link = SharedLink(
        id=str(uuid.uuid4()),
        meeting_id=meeting_id,
        token=token,
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(link)
    db.session.commit()
    return link

def get_meeting_id_from_token(token: str) -> int | None:
    """
    Resolve a token to a meeting_id if valid and not expired.
    """
    link = SharedLink.query.filter_by(token=token).first()
    if not link:
        return None
    if link.expires_at and link.expires_at <= datetime.now(timezone.utc):
        return None
    return link.meeting_id

# Backwards-compat: if older code calls create_shared_link, keep it working.
def create_shared_link(meeting_id: int, expires_in_hours: int | None = 72) -> SharedLink:
    return create_share_link(meeting_id, expires_in_hours)