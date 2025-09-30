from flask import Blueprint, jsonify, render_template, current_app, request
from flask import Blueprint, jsonify
errors_bp = Blueprint("errors", __name__)

errors_bp = Blueprint("errors_bp", __name__)

@errors_bp.app_errorhandler(404)
def not_found(e):
    if request.path.startswith("/api"):
        return jsonify({"ok": False, "error": "not_found"}), 404
    return render_template("error.html", code=404, message="Not Found"), 404

@errors_bp.app_errorhandler(413)
def too_large(e):
    if request.path.startswith("/api"):
        return jsonify({"ok": False, "error": "payload_too_large"}), 413
    return render_template("error.html", code=413, message="Payload Too Large"), 413

@errors_bp.app_errorhandler(Exception)
def server_error(e):
    current_app.logger.exception("unhandled_error")
    if request.path.startswith("/api"):
        return jsonify({"ok": False, "error": "server_error"}), 500
    return render_template("error.html", code=500, message="Server Error"), 500
    
@errors_bp.app_errorhandler(429)
def _429(_):
    return jsonify({"error": "rate_limited"}), 429