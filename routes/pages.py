# routes/pages.py
from flask import Blueprint, redirect, url_for, render_template
from flask_login import login_required, current_user

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return render_template("marketing/landing.html")

@pages_bp.route("/app")
def app():
    """Intelligent entry point for users coming from marketing CTAs."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    else:
        # Route new users to registration with next parameter for smooth onboarding
        return redirect(url_for("auth.register", next=url_for("dashboard.index")))

@pages_bp.route("/live")
@login_required
def live():
    """Production live recording interface with all features consolidated"""
    return render_template("live.html")

@pages_bp.route("/live-enhanced")
@login_required
def live_enhanced():
    """Legacy route - redirects to main live interface"""
    return render_template("live.html")

@pages_bp.route("/live-comprehensive")
@login_required
def live_comprehensive():
    """Legacy route - redirects to main live interface"""
    return render_template("live.html")