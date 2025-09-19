# routes/tasks.py
from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
from db import db
from models import Task, Meeting
from services.task_extractor import heuristic_extract, refine_with_llm

tasks_bp = Blueprint("tasks", __name__)

@tasks_bp.get("/tasks")
def list_tasks_page():
    tasks = Task.query.order_by(Task.created_at.desc()).limit(200).all()
    return render_template("tasks.html", tasks=tasks)

@tasks_bp.get("/api/tasks")
def list_tasks():
    q = Task.query.order_by(Task.created_at.desc()).limit(500).all()
    return jsonify([{
        "id": t.id, "meeting_id": t.meeting_id, "title": t.title,
        "owner": t.owner, "due_at": t.due_at.isoformat() if t.due_at else None,
        "status": t.status
    } for t in q])

@tasks_bp.post("/api/meetings/<int:mid>/extract_tasks")
def extract_tasks(mid: int):
    m = Meeting.query.get_or_404(mid)
    if not m.transcript:
        return jsonify({"error":"no transcript"}), 400
    candidates = heuristic_extract(m.transcript)
    refined = refine_with_llm(m.transcript, candidates)
    created = []
    for t in refined:
        title = (t.get("title") or "").strip()
        if not title:
            continue
        due = t.get("due_at") or t.get("due_date")
        due_dt = datetime.fromisoformat(due) if due else None
        task = Task(meeting_id=mid, title=title[:500], owner=t.get("owner"), due_at=due_dt)
        db.session.add(task); created.append(task)
    db.session.commit()
    return jsonify({"created": [ {"id":x.id,"title":x.title} for x in created ]})