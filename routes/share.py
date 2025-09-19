# routes/share.py
from flask import Blueprint, request, jsonify, render_template, abort
from models import Meeting, Summary, Task
from services.share_service import create_share_link, get_meeting_id_from_token

share_bp = Blueprint("share", __name__, url_prefix="/api/share")

@share_bp.post("/api/meetings/<int:mid>/share")
def create_share(mid: int):
    data = request.json or {}
    link = create_share_link(mid, bool(data.get("redact_pii", True)))
    return jsonify({"token": link.token, "url": f"/share/{link.token}"})

@share_bp.get("/share/<token>")
def share_view(token: str):
    mid = get_meeting_id_from_token(token)
    if not mid:
        abort(404)
    m = Meeting.query.get_or_404(mid)
    s = Summary.query.filter_by(meeting_id=mid).order_by(Summary.id.desc()).first()
    tasks = Task.query.filter_by(meeting_id=mid).order_by(Task.id.asc()).all()
    return render_template("share_view.html", meeting=m, summary=s, tasks=tasks)