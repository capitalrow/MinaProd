# routes/pages.py
from flask import Blueprint, redirect, url_for, render_template

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/")
def index():
    return redirect(url_for("pages.live"))

@pages_bp.route("/live")
def live():
    return render_template("live.html")