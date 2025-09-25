import os
from flask import Blueprint, request, jsonify
from datetime import datetime

bp_api = Blueprint("api", __name__, url_prefix="/api")

# Simple in-memory storage for testing (replace with real database)
conversations = {}
conversation_counter = 1

@bp_api.route("/conversations", methods=["POST"])
def create_conversation():
    global conversation_counter
    data = request.get_json() or {}
    title = data.get("title", "Untitled Conversation")
    
    conv_id = str(conversation_counter)
    conversation_counter += 1
    
    conversations[conv_id] = {
        "id": conv_id,
        "title": title,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "segments": [],
        "status": "live",
        "duration_s": 0,
        "word_count": 0
    }
    
    return jsonify({"ok": True, "id": conv_id})

@bp_api.route("/conversations", methods=["GET"])
def list_conversations():
    limit = min(int(request.args.get("limit", "20")), 50)
    items = list(conversations.values())[:limit]
    return jsonify({"ok": True, "items": items})

@bp_api.route("/conversations/<conv_id>", methods=["GET"])
def get_conversation(conv_id):
    if conv_id not in conversations:
        return jsonify({"ok": False, "code": "not_found"}), 404
    
    conv = conversations[conv_id]
    return jsonify({
        "ok": True,
        "conversation": {
            "id": conv["id"],
            "title": conv["title"],
            "created_at": conv["created_at"],
            "duration_s": conv["duration_s"],
            "word_count": conv["word_count"],
            "status": conv["status"]
        },
        "segments": conv["segments"]
    })

@bp_api.route("/conversations/<conv_id>/segments", methods=["POST"])
def add_segment(conv_id):
    if conv_id not in conversations:
        return jsonify({"ok": False, "code": "not_found"}), 404
    
    data = request.get_json() or {}
    segment = {
        "idx": int(data.get("idx", 0)),
        "start_ms": int(data.get("start_ms", 0)),
        "end_ms": int(data.get("end_ms", 0)),
        "text": data.get("text", ""),
        "is_final": bool(data.get("is_final", False))
    }
    
    conversations[conv_id]["segments"].append(segment)
    conversations[conv_id]["word_count"] += len(segment["text"].split())
    
    return jsonify({"ok": True})

@bp_api.route("/conversations/<conv_id>/finalize", methods=["POST"])
def finalize_conversation(conv_id):
    if conv_id not in conversations:
        return jsonify({"ok": False, "code": "not_found"}), 404
    
    conversations[conv_id]["status"] = "completed"
    return jsonify({"ok": True})
