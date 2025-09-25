# routes/http.py
import os
import time
import hashlib
from flask import Blueprint, jsonify, send_from_directory, current_app, redirect

http_bp = Blueprint("http", __name__)

def _ui_dir() -> str:
    # e.g. <repo>/static/ui
    return os.path.join(current_app.static_folder, "ui")

@http_bp.route("/health")
def health():
    return jsonify({"status": "ok", "version": "0.1.0"})

# ---------- SPA root ----------
@http_bp.route("/")
def root():
    ui_dir = _ui_dir()
    index_path = os.path.join(ui_dir, "index.html")
    if not os.path.exists(index_path):
        return (
            f"[mina] SPA index not found at {index_path}. "
            "Ensure static/ui/index.html exists (all lowercase).",
            500,
        )
    return send_from_directory(ui_dir, "index.html")

# ---------- Redirect any legacy routes to SPA ----------
@http_bp.route("/live")
@http_bp.route("/old-live")
@http_bp.route("/live_modern")
@http_bp.route("/live_clean_fixed")
def legacy_live():
    return redirect("/", code=302)

# ---------- Serve extra UI assets under /ui/* ----------
@http_bp.route("/ui/<path:filename>")
def ui_assets(filename: str):
    ui_dir = _ui_dir()
    target = os.path.join(ui_dir, filename)
    if not os.path.exists(target):
        return "Not Found", 404
    return send_from_directory(ui_dir, filename)

# ---------- Catch-all for clean SPA URLs ----------
@http_bp.route("/<path:any_path>")
def spa_fallback(any_path: str):
    ui_dir = _ui_dir()
    index_path = os.path.join(ui_dir, "index.html")
    if not os.path.exists(index_path):
        return "Not Found", 404
    return send_from_directory(ui_dir, "index.html")

# ---------- Debug: show exactly what file would be served ----------
@http_bp.route("/__debug_ui")
def debug_ui():
    ui_dir = _ui_dir()
    index_path = os.path.join(ui_dir, "index.html")
    exists = os.path.exists(index_path)
    size = os.path.getsize(index_path) if exists else 0
    mtime = time.ctime(os.path.getmtime(index_path)) if exists else None
    sha = None
    if exists:
        with open(index_path, "rb") as f:
            data = f.read()
            sha = hashlib.sha1(data).hexdigest()
    return jsonify({
        "static_folder": current_app.static_folder,
        "ui_dir": ui_dir,
        "index_exists": exists,
        "index_size_bytes": size,
        "index_mtime": mtime,
        "index_sha1": sha,
        "note": "If index_exists is true, GET /static/ui/index.html should return the SPA."
    })