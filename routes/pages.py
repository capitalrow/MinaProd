# routes/pages.py
from flask import Blueprint, redirect, url_for, render_template
from flask_login import login_required, current_user

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))

@pages_bp.route("/live")
@login_required
def live():
    return render_template("live.html")