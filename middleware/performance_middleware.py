"""
Flask middleware for automatic performance tracking.
"""
import time
from flask import request, g
from services.performance_monitoring import performance_monitor
import logging

logger = logging.getLogger(__name__)


def setup_performance_middleware(app):
    """Setup performance monitoring middleware for Flask app."""
    
    @app.before_request
    def before_request():
        """Record request start time."""
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Track request performance after completion."""
        if hasattr(g, 'start_time'):
            duration_ms = (time.time() - g.start_time) * 1000
            
            performance_monitor.track_request(
                route=request.endpoint or request.path,
                method=request.method,
                duration_ms=duration_ms,
                status_code=response.status_code
            )
            
            response.headers['X-Response-Time'] = f"{duration_ms:.2f}ms"
        
        return response
    
    @app.route('/metrics')
    def metrics_endpoint():
        """Endpoint for monitoring tools to scrape metrics."""
        stats = performance_monitor.get_stats()
        return {
            'status': 'ok',
            'performance': stats
        }, 200
    
    logger.info("Performance monitoring middleware initialized")
