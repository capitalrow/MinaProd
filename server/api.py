import secrets
from flask import Blueprint, request, jsonify, current_app
from .models import db, Conversation, Segment, Highlight, Task, Share

bp_api = Blueprint("api", __name__, url_prefix="/api")

def _json():
    try: return request.get_json(force=True) or {}
    except Exception: return {}

def _uid_from_access():
    try:
        from .auth import _verify
        tok = request.cookies.get(current_app.config["ACCESS_COOKIE_NAME"])
        if not tok: return None
        d = _verify(tok, int(current_app.config["ACCESS_EXPIRES"].total_seconds()))
        return d["uid"] if d.get("t") == "access" else None
    except Exception:
        return None

# Conversations
@bp_api.post("/conversations")
def create_conversation():
    uid = _uid_from_access()
    data = _json()
    title = (data.get("title") or "Untitled Conversation")[:255]
    conv = Conversation(title=title, user_id=uid, status="live", source="realtime")
    db.session.add(conv); db.session.commit()
    return jsonify(ok=True, id=conv.id)

@bp_api.get("/conversations")
def list_conversations():
    uid = _uid_from_access()
    q = (request.args.get("q") or "").strip()
    limit = min(int(request.args.get("limit", "20")), 50)
    qry = Conversation.query
    if uid: qry = qry.filter((Conversation.user_id == uid) | (Conversation.user_id.is_(None)))
    if q: qry = qry.filter(Conversation.title.ilike(f"%{q}%"))
    qry = qry.order_by(Conversation.created_at.desc())
    items = qry.limit(limit).all()
    data = [{
        "id": c.id, "title": c.title,
        "created_at": c.created_at.isoformat() + "Z",
        "duration_s": c.duration_s, "word_count": c.word_count,
        "status": c.status
    } for c in items]
    return jsonify(ok=True, items=data)

@bp_api.get("/conversations/<cid>")
def get_conversation(cid):
    c = Conversation.query.get(cid)
    if not c: return jsonify(ok=False, code="not_found"), 404
    segs = Segment.query.filter_by(conversation_id=cid).order_by(Segment.idx.asc()).all()
    return jsonify(ok=True, conversation={
        "id": c.id, "title": c.title, "created_at": c.created_at.isoformat() + "Z",
        "duration_s": c.duration_s, "word_count": c.word_count, "status": c.status
    }, segments=[{"idx": s.idx, "start_ms": s.start_ms, "end_ms": s.end_ms, "text": s.text, "is_final": s.is_final} for s in segs])

@bp_api.post("/conversations/<cid>/segments")
def post_segment(cid):
    c = Conversation.query.get(cid)
    if not c: return jsonify(ok=False, code="not_found"), 404
    data = _json()
    text = (data.get("text") or "").strip()
    if len(text) > 10000: return jsonify(ok=False, code="too_long"), 413
    seg = Segment(
        conversation_id=cid,
        idx=int(data.get("idx") or 0),
        start_ms=int(data.get("start_ms") or 0),
        end_ms=int(data.get("end_ms") or 0),
        text=text, is_final=bool(data.get("is_final") or False)
    )
    db.session.add(seg)
    # update stats
    c.word_count = (c.word_count or 0) + len(text.split())
    c.duration_s = max(c.duration_s or 0, seg.end_ms // 1000)
    db.session.commit()
    return jsonify(ok=True)

@bp_api.post("/conversations/<cid>/finalize")
def finalize(cid):
    c = Conversation.query.get(cid)
    if not c: return jsonify(ok=False, code="not_found"), 404
    c.status = "final"
    db.session.commit()
    return jsonify(ok=True)

# Highlights
@bp_api.route("/conversations/<cid>/highlights", methods=["GET","POST","DELETE"])
def highlights(cid):
    if request.method == "POST":
        d = _json()
        h = Highlight(conversation_id=cid, start_ms=int(d.get("start_ms") or 0),
                      end_ms=int(d.get("end_ms") or 0), text=(d.get("text") or ""), label=(d.get("label") or ""))
        db.session.add(h); db.session.commit()
        return jsonify(ok=True, id=h.id)
    if request.method == "GET":
        hs = Highlight.query.filter_by(conversation_id=cid).all()
        return jsonify(ok=True, items=[{"id": x.id, "text": x.text, "label": x.label, "start_ms": x.start_ms, "end_ms": x.end_ms} for x in hs])
    Highlight.query.filter_by(conversation_id=cid).delete(); db.session.commit()
    return jsonify(ok=True)

# Tasks
@bp_api.route("/conversations/<cid>/tasks", methods=["GET","POST","PATCH"])
def tasks(cid):
    if request.method == "POST":
        d = _json()
        t = Task(conversation_id=cid, text=(d.get("text") or ""), assignee=(d.get("assignee") or ""))
        db.session.add(t); db.session.commit()
        return jsonify(ok=True, id=t.id)
    if request.method == "GET":
        ts = Task.query.filter_by(conversation_id=cid).all()
        return jsonify(ok=True, items=[{"id": x.id, "text": x.text, "assignee": x.assignee, "status": x.status} for x in ts])
    d = _json()
    tid = d.get("id"); status = d.get("status")
    t = Task.query.get(tid)
    if not t or t.conversation_id != cid: return jsonify(ok=False, code="not_found"), 404
    if status: t.status = status
    db.session.commit()
    return jsonify(ok=True)

# Shares
@bp_api.post("/conversations/<cid>/share")
def create_share(cid):
    if not Conversation.query.get(cid): return jsonify(ok=False, code="not_found"), 404
    token = secrets.token_urlsafe(current_app.config["SHARE_TOKEN_BYTES"])
    db.session.add(Share(conversation_id=cid, token=token)); db.session.commit()
    return jsonify(ok=True, token=token)

@bp_api.get("/shares/<token>")
def get_share(token):
    s = Share.query.filter_by(token=token).first()
    if not s: return jsonify(ok=False, code="not_found"), 404
    c = Conversation.query.get(s.conversation_id)
    segs = Segment.query.filter_by(conversation_id=c.id).order_by(Segment.idx.asc()).all()
    return jsonify(ok=True, conversation={"id": c.id, "title": c.title, "created_at": c.created_at.isoformat()+"Z"},
                   segments=[{"idx": x.idx, "text": x.text, "start_ms": x.start_ms, "end_ms": x.end_ms} for x in segs])