# routes/pages.py
from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/live")
def live():
    return render_template("live.html")