# routes/meetings.py
from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
from db import db
from models import Meeting, Summary, Task
from services.summarizer import summarize_transcript

meetings_bp = Blueprint("meetings", __name__)

@meetings_bp.get("/meetings")
def list_meetings():
    q = Meeting.query.order_by(Meeting.started_at.desc()).limit(200).all()
    return render_template("meetings.html", meetings=q)

@meetings_bp.get("/api/meetings")
def api_list_meetings():
    q = Meeting.query.order_by(Meeting.started_at.desc()).limit(200).all()
    return jsonify([{
        "id": m.id, "title": m.title,
        "started_at": m.started_at.isoformat() if m.started_at else None,
        "status": m.status
    } for m in q])

@meetings_bp.get("/meetings/<int:mid>")
def meeting_detail(mid: int):
    m = Meeting.query.get_or_404(mid)
    s = Summary.query.filter_by(meeting_id=mid).order_by(Summary.id.desc()).first()
    tasks = Task.query.filter_by(meeting_id=mid).order_by(Task.id.asc()).all()
    return render_template("meeting_detail.html", meeting=m, summary=s, tasks=tasks)

@meetings_bp.post("/api/meetings")
def create_meeting():
    data = request.json or {}
    m = Meeting(
        title=data.get("title") or "Untitled Meeting",
        participants=",".join(data.get("participants", [])) or None,
        tags=",".join(data.get("tags", [])) or None,
        started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else datetime.utcnow(),
        source=data.get("source") or "live",
        status="draft",
    )
    db.session.add(m)
    db.session.commit()
    return jsonify({"id": m.id}), 201

@meetings_bp.post("/api/meetings/<int:mid>/ingest_final")
def ingest_final(mid: int):
    """Optional hook: POST final transcript here AFTER your live pipeline finalizes.
       Does NOT modify your ASR; only persists & summarizes."""
    m = Meeting.query.get_or_404(mid)
    data = request.json or {}
    transcript = data.get("transcript") or ""
    if not transcript:
        return jsonify({"error":"missing transcript"}), 400
    m.transcript = transcript
    m.status = "processed"
    sdata = summarize_transcript(transcript)
    s = Summary(meeting_id=mid,
                tldr=sdata.get("tldr",""),
                bullets=sdata.get("bullets",""),
                decisions=sdata.get("decisions",""),
                risks=sdata.get("risks",""),
                questions=sdata.get("questions",""))
    db.session.add(s)
    db.session.commit()
    return jsonify({"ok": True})