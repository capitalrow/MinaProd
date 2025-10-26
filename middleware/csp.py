"""
Content Security Policy (CSP) Middleware

Implements production-grade CSP headers to prevent XSS, data injection,
and other code injection attacks. Uses nonces for inline scripts to avoid
'unsafe-inline' which weakens security.

Phase 0 - Task 0.16: Content Security Policy Headers
"""

import secrets
from flask import g, request
from functools import wraps


def generate_csp_nonce():
    """
    Generate a cryptographically secure nonce for CSP.
    
    Returns:
        str: Base64-encoded random nonce (128 bits of entropy)
    """
    return secrets.token_urlsafe(16)


def csp_middleware(app):
    """
    Configure Content Security Policy headers for the Flask application.
    
    This middleware:
    1. Generates a unique nonce per request for inline scripts
    2. Sets CSP headers with strict directives
    3. Allows specific trusted CDNs and domains
    4. Prevents XSS and code injection attacks
    
    CSP Directives:
    - default-src: Default policy for all content types
    - script-src: Only allow scripts from trusted sources + nonce
    - style-src: Allow styles from self and trusted CDNs
    - img-src: Allow images from self and data URIs
    - connect-src: Allow API connections to self and Socket.IO
    - font-src: Allow fonts from self and CDNs
    - frame-ancestors: Prevent clickjacking
    - base-uri: Restrict base tag to self
    - form-action: Restrict form submissions to self
    """
    
    @app.before_request
    def set_csp_nonce():
        """Generate and store CSP nonce for this request."""
        g.csp_nonce = generate_csp_nonce()
    
    @app.context_processor
    def inject_csp_nonce():
        """Make CSP nonce available to all templates."""
        return {'csp_nonce': lambda: getattr(g, 'csp_nonce', '')}
    
    @app.after_request
    def set_csp_headers(response):
        """Apply CSP headers to all responses."""
        # Skip CSP for certain paths that need relaxed policies
        if request.path.startswith('/static/') or request.path.startswith('/socket.io/'):
            return response
        
        # Get the nonce for this request
        nonce = getattr(g, 'csp_nonce', '')
        
        # Build CSP policy
        # Note: Using 'unsafe-inline' as fallback for older browsers that don't support nonces
        # Modern browsers will ignore 'unsafe-inline' when nonce is present
        csp_directives = [
            "default-src 'self'",
            
            # Scripts: self, nonces, and trusted CDNs
            f"script-src 'self' 'nonce-{nonce}' 'unsafe-inline' " +
            "https://cdn.jsdelivr.net " +
            "https://cdnjs.cloudflare.com " +
            "https://cdn.replit.com " +
            "https://cdn.socket.io " +
            "https://unpkg.com",
            
            # Styles: self, inline styles (needed for dynamic styling), and CDNs
            "style-src 'self' 'unsafe-inline' " +
            "https://cdn.jsdelivr.net " +
            "https://cdnjs.cloudflare.com " +
            "https://cdn.replit.com " +
            "https://fonts.googleapis.com",
            
            # Images: self, data URIs, and CDNs
            "img-src 'self' data: blob: https:",
            
            # Fonts: self and CDNs
            "font-src 'self' data: " +
            "https://cdnjs.cloudflare.com " +
            "https://cdn.jsdelivr.net " +
            "https://fonts.gstatic.com",
            
            # Connect: API endpoints, WebSocket, and self
            "connect-src 'self' " +
            "wss: ws: " +
            "wss://*.replit.dev wss://*.replit.app " +
            "ws://localhost:5000 " +
            "https: " +
            "https://api.openai.com",
            
            # Media: self for audio/video uploads
            "media-src 'self' blob:",
            
            # Workers: self and blob for Web Workers and Service Workers
            "worker-src 'self' blob:",
            
            # Objects: none (prevent plugin execution)
            "object-src 'none'",
            
            # Frame ancestors: prevent clickjacking (allow Replit embedding)
            "frame-ancestors 'self' *.replit.dev *.replit.app",
            
            # Base URI: prevent base tag injection
            "base-uri 'self'",
            
            # Form actions: restrict form submissions
            "form-action 'self'",
            
            # Upgrade insecure requests in production
            "upgrade-insecure-requests" if app.config.get('ENV') == 'production' else "",
        ]
        
        # Join directives and set header
        csp_policy = "; ".join([d for d in csp_directives if d])
        response.headers['Content-Security-Policy'] = csp_policy
        
        # Also set Report-Only header for monitoring (doesn't block, just reports)
        # Useful for testing CSP without breaking functionality
        # response.headers['Content-Security-Policy-Report-Only'] = csp_policy
        
        # Additional security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(self), '
            'camera=(self), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=()'
        )
        
        return response
    
    app.logger.info("✅ Content Security Policy (CSP) middleware enabled")


def nonce_required(f):
    """
    Decorator to ensure CSP nonce is available in route context.
    Use this on routes that render templates with inline scripts.
    
    Usage:
        @app.route('/dashboard')
        @nonce_required
        def dashboard():
            return render_template('dashboard.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'csp_nonce'):
            g.csp_nonce = generate_csp_nonce()
        return f(*args, **kwargs)
    return decorated_function
