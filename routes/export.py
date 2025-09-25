# routes/export.py
import os, io, zipfile
from flask import Blueprint, jsonify, send_file, abort
from services.files import session_audio_path, session_transcript_path

export_bp = Blueprint("export", __name__)

@export_bp.route("/export/ping", methods=["GET"])
def export_ping():
    return jsonify({"ok": True})

@export_bp.route("/session/<session_id>/audio", methods=["GET"])
def get_audio(session_id: str):
    path = session_audio_path(session_id)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=f"mina-{session_id}.webm")

@export_bp.route("/session/<session_id>/transcript", methods=["GET"])
def get_transcript(session_id: str):
    path = session_transcript_path(session_id)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=f"mina-{session_id}.txt")

@export_bp.route("/session/<session_id>/bundle.zip", methods=["GET"])
def get_bundle(session_id: str):
    audio = session_audio_path(session_id)
    txt = session_transcript_path(session_id)
    if not os.path.isfile(audio) and not os.path.isfile(txt):
        abort(404)

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.isfile(audio): zf.write(audio, f"mina-{session_id}.webm")
        if os.path.isfile(txt):   zf.write(txt,   f"mina-{session_id}.txt")
    mem.seek(0)
    return send_file(mem, as_attachment=True, download_name=f"mina-{session_id}.zip")