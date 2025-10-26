"""
htmx Utilities for Flask
Provides helpers for partial rendering and htmx integration
"""

from flask import request, render_template
from functools import wraps


def is_htmx_request():
    """
    Check if the current request is from htmx.
    
    Returns:
        bool: True if request has HX-Request header
    """
    return request.headers.get('HX-Request') == 'true'


def render_partial(template_name, **context):
    """
    Render a template as either a full page or partial content for htmx.
    
    For htmx requests, tries to render a _partial.html version if it exists.
    Falls back to extracting #main-content from the full template.
    For regular requests, renders the full page normally.
    
    Args:
        template_name: The template to render (e.g., 'dashboard/index.html')
        **context: Template context variables
        
    Returns:
        Rendered HTML string
        
    Usage:
        @app.route('/dashboard')
        def dashboard():
            return render_partial('dashboard/index.html', meetings=meetings)
        
    Template Structure:
        dashboard/index.html - Full page (extends base.html)
        dashboard/_index_partial.html - Content only (for htmx, optional)
    """
    from flask import current_app
    from bs4 import BeautifulSoup
    
    if not is_htmx_request():
        # Regular request: return full page
        return render_template(template_name, **context)
    
    # htmx request: try partial template first
    # Convert 'dashboard/index.html' to 'dashboard/_index_partial.html'
    path_parts = template_name.rsplit('/', 1)
    if len(path_parts) == 2:
        folder, filename = path_parts
        name_without_ext = filename.rsplit('.', 1)[0]
        partial_template = f"{folder}/_{name_without_ext}_partial.html"
    else:
        filename = template_name
        name_without_ext = filename.rsplit('.', 1)[0]
        partial_template = f"_{name_without_ext}_partial.html"
    
    # Try to render partial template
    try:
        return render_template(partial_template, **context)
    except Exception:
        # Partial doesn't exist, extract from full template
        pass
    
    # Render full template and extract #main-content
    full_html = render_template(template_name, **context)
    
    try:
        soup = BeautifulSoup(full_html, 'html.parser')
        main_content = soup.find(id='main-content')
        if main_content:
            return str(main_content)
    except Exception as e:
        current_app.logger.warning(f"Failed to extract #main-content: {e}")
    
    # Fallback: return full page (htmx will handle it)
    return full_html


def htmx_redirect(url):
    """
    Tell htmx to redirect to a new URL.
    
    Args:
        url: The URL to redirect to
        
    Returns:
        Response object with HX-Redirect header
        
    Usage:
        @app.route('/logout')
        def logout():
            logout_user()
            return htmx_redirect(url_for('auth.login'))
    """
    from flask import make_response
    response = make_response('', 200)
    response.headers['HX-Redirect'] = url
    return response


def htmx_refresh():
    """
    Tell htmx to refresh the current page.
    
    Returns:
        Response object with HX-Refresh header
        
    Usage:
        @app.route('/settings/update')
        def update_settings():
            # Update settings
            return htmx_refresh()
    """
    from flask import make_response
    response = make_response('', 200)
    response.headers['HX-Refresh'] = 'true'
    return response


def htmx_trigger(event_name, event_detail=None):
    """
    Trigger a client-side event from htmx response.
    
    Args:
        event_name: Name of the event to trigger
        event_detail: Optional event detail data (will be JSON encoded)
        
    Returns:
        Response object with HX-Trigger header
        
    Usage:
        @app.route('/task/complete')
        def complete_task():
            # Complete task
            return htmx_trigger('taskCompleted', {'task_id': task_id})
    """
    from flask import make_response
    import json
    
    response = make_response('', 200)
    if event_detail:
        response.headers['HX-Trigger'] = json.dumps({event_name: event_detail})
    else:
        response.headers['HX-Trigger'] = event_name
    return response


def htmx_location(url, target=None, swap=None):
    """
    Tell htmx to navigate to a new location with options.
    
    Args:
        url: The URL to navigate to
        target: Optional CSS selector to target
        swap: Optional swap strategy
        
    Returns:
        Response object with HX-Location header
        
    Usage:
        return htmx_location('/dashboard', target='#main-content', swap='innerHTML')
    """
    from flask import make_response
    import json
    
    response = make_response('', 200)
    location_data = {'path': url}
    if target:
        location_data['target'] = target
    if swap:
        location_data['swap'] = swap
    response.headers['HX-Location'] = json.dumps(location_data)
    return response


def htmx_push_url(url):
    """
    Update the browser URL without full page reload.
    
    Args:
        url: The URL to push to browser history
        
    Usage:
        Add to response headers in your route
    """
    from flask import make_response, g
    if hasattr(g, 'htmx_push_url'):
        return
    g.htmx_push_url = url


def htmx_only(f):
    """
    Decorator to restrict route to htmx requests only.
    
    Returns 400 Bad Request if accessed without htmx.
    
    Usage:
        @app.route('/api/partial/dashboard')
        @htmx_only
        def dashboard_partial():
            return render_template('partials/dashboard.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_htmx_request():
            from flask import abort
            abort(400, description="This endpoint only accepts htmx requests")
        return f(*args, **kwargs)
    return decorated_function
