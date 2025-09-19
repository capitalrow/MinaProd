# routes/pages.py
from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/")
def index():
    # keep your existing home if you have one; this prevents TemplateNotFound
    return render_template("pages/index.html")

@pages_bp.route("/dashboard")
def dashboard_page():
    return render_template("pages/dashboard.html")

@pages_bp.route("/meetings")
def meetings_page():
    return render_template("pages/meetings.html")

@pages_bp.route("/tasks")
def tasks_page():
    return render_template("pages/tasks.html")

@pages_bp.route("/calendar")
def calendar_page():
    return render_template("pages/calendar.html")

@pages_bp.route("/live")
def live():
    # live transcription UI
    return render_template("pages/live.html")

@pages_bp.route("/settings")
def settings_page():
    return render_template("pages/settings.html")