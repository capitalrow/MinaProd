from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

ui_bp = Blueprint('ui', __name__, url_prefix='/ui', template_folder='../templates')

@ui_bp.route('/dashboard')
def dashboard():
    try:
        return render_template('base.html', title='Dashboard')
    except TemplateNotFound:
        abort(404)

@ui_bp.route('/transcript')
def transcript():
    try:
        # Temporary dummy data for rendering
        sample_transcript = "This is a sample transcript. Say hi to Mina!"
        return render_template(
            'transcript.html',
            title='Transcript Viewer',
            session_id=1,
            transcript=sample_transcript,
            summary="Demo summary",
            actions=["Follow up with client", "Prepare proposal"],
            decisions=["Proceed with MVP"],
            risks=["Tight deadline"]
        )
    except TemplateNotFound:
        abort(404)

@ui_bp.route('/admin/flags')
def admin_flags():
    try:
        return render_template('admin_flags.html', title='Feature Flags')
    except TemplateNotFound:
        abort(404)

@ui_bp.route('/billing')
def billing():
    try:
        return render_template('billing.html', title='Billing')
    except TemplateNotFound:
        abort(404)

@ui_bp.route('/integrations')
def integrations():
    try:
        return render_template('integrations.html', title='Integrations')
    except TemplateNotFound:
        abort(404)