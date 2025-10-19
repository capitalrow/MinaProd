from __future__ import annotations
from flask import Blueprint, request, jsonify, abort
from services.slack_service import slack_svc
from services.notion_service import notion_svc

integrations_bp = Blueprint("integrations", __name__, url_prefix="/integrations")

@integrations_bp.post("/slack/test")
def slack_test():
    body = request.get_json(force=True)
    channel = body.get("channel"); text = body.get("text", "Hello from Mina")
    if not channel:
        abort(400, "channel required")
    ok = slack_svc.post_message(channel, text)
    return jsonify({"posted": ok})

@integrations_bp.post("/notion/append")
def notion_append():
    body = request.get_json(force=True)
    page_id = body.get("page_id"); content = body.get("content", "Mina update")
    if not page_id:
        abort(400, "page_id required")
    ok = notion_svc.append_paragraph(page_id, content)
    return jsonify({"appended": ok})