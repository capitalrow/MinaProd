# routes/ui.py — single UI blueprint for SPA at /app + redirect from /
import os
from flask import Blueprint, send_from_directory, current_app, redirect

ui_bp = Blueprint("ui", __name__)

def _ui_dir() -> str:
    return os.path.join(current_app.static_folder, "ui")

@ui_bp.route("/")
def root_redirect():
    # Always land on SPA path; avoids route wars at "/"
    return redirect("/app", code=302)

@ui_bp.route("/app")
def spa_root():
    ui_dir = _ui_dir()
    index_path = os.path.join(ui_dir, "index.html")
    if not os.path.exists(index_path):
        return ("[mina] SPA not found at static/ui/index.html", 500)
    return send_from_directory(ui_dir, "index.html")

@ui_bp.route("/app/<path:filename>")
def spa_assets(filename):
    # Serve any assets under /app/* if we later split files
    ui_dir = _ui_dir()
    target = os.path.join(ui_dir, filename)
    if not os.path.exists(target):
        return "Not Found", 404
    return send_from_directory(ui_dir, filename)

# Catch-all under /app/* — enables client-side routing later
@ui_bp.route("/app-<path:anything>")
@ui_bp.route("/app/<path:anything>")
def spa_catchall(anything):
    ui_dir = _ui_dir()
    index_path = os.path.join(ui_dir, "index.html")
    if not os.path.exists(index_path):
        return "Not Found", 404
    return send_from_directory(ui_dir, "index.html")