# routes/settings.py
from flask import Blueprint, render_template, request, jsonify
from models import Workspace
from db import db

settings_bp = Blueprint("settings", __name__)

@settings_bp.get("/settings")
def settings_page():
    ws = Workspace.query.first()
    return render_template("settings.html", ws=ws)

@settings_bp.post("/api/settings/workspace")
def save_workspace():
    data = request.json or {}
    ws = Workspace.query.first() or Workspace(name=data.get("name","My Workspace"))
    ws.name = data.get("name", ws.name)
    ws.retention_days = int(data.get("retention_days", ws.retention_days or 90))
    db.session.add(ws); db.session.commit()
    return jsonify({"ok": True})