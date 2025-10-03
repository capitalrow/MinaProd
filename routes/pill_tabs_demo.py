"""
Pill Tabs Component Demo Route
Temporary route to demonstrate and test the pill tabs component
"""

from flask import Blueprint, render_template
from flask_login import login_required

pill_tabs_demo_bp = Blueprint('pill_tabs_demo', __name__, url_prefix='/demo')


@pill_tabs_demo_bp.route('/pill-tabs')
@login_required
def pill_tabs():
    """Demo page for pill tabs component."""
    return render_template('demo/pill_tabs.html')
