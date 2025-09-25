# routes/metrics_stream.py
from flask import Blueprint, jsonify
metrics_stream_bp = Blueprint("metrics", __name__)

@metrics_stream_bp.route("/metrics/ping", methods=["GET"])
def metrics_ping():
    return jsonify({"ok": True})