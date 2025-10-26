# routes/pages.py
from flask import Blueprint, redirect, url_for, render_template, make_response
from flask_login import login_required, current_user

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return render_template("marketing/landing_standalone.html")

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
    response = make_response(render_template("pages/live.html"))
    # Force cache invalidation for mobile browsers
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@pages_bp.route("/live-enhanced")
@login_required
def live_enhanced():
    """Legacy route - redirects to main live interface"""
    return redirect(url_for("pages.live"))

@pages_bp.route("/live-comprehensive")
@login_required
def live_comprehensive():
    """Legacy route - redirects to main live interface"""
    return redirect(url_for("pages.live"))

# Legal Pages
@pages_bp.route("/privacy")
def privacy():
    """Privacy Policy page"""
    return render_template("legal/privacy.html")

@pages_bp.route("/terms")
def terms():
    """Terms of Service page"""
    return render_template("legal/terms.html")

@pages_bp.route("/cookies")
def cookies():
    """Cookie Policy page"""
    return render_template("legal/cookies.html")

# Onboarding
@pages_bp.route("/onboarding")
@login_required
def onboarding():
    """Onboarding wizard for new users"""
    return render_template("onboarding/wizard.html")

@pages_bp.route("/onboarding/complete", methods=["POST"])
@login_required
def onboarding_complete():
    """Handle onboarding completion"""
    from flask import request
    
    # Get form data
    workspace_name = request.form.get('workspace_name', '')
    workspace_role = request.form.get('workspace_role', '')
    email_notifications = request.form.get('email_notifications') == 'on'
    meeting_reminders = request.form.get('meeting_reminders') == 'on'
    task_updates = request.form.get('task_updates') == 'on'
    
    # In production, save user preferences to database
    # For now, just log and redirect
    print(f"Onboarding completed: {workspace_name}, {workspace_role}")
    print(f"Preferences: email={email_notifications}, reminders={meeting_reminders}, tasks={task_updates}")
    
    return redirect(url_for("dashboard.index"))