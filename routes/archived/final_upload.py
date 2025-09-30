# routes/final_upload.py
from flask import Blueprint, jsonify
final_bp = Blueprint("final", __name__)

@final_bp.route("/final/ping", methods=["GET"])
def final_ping():
    return jsonify({"ok": True})