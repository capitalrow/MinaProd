"""
Operations and monitoring routes for testing and validation.

This module provides endpoints for operational tasks like:
- Sentry error tracking validation
- Performance monitoring demonstration
- Health checks and diagnostics
"""

import logging
import time
import random
from flask import Blueprint, jsonify, current_app
import sentry_sdk

logger = logging.getLogger(__name__)

ops_bp = Blueprint('ops', __name__, url_prefix='/ops')


@ops_bp.route('/test-sentry-error', methods=['GET'])
def test_sentry_error():
    """
    Test endpoint to validate Sentry error tracking.
    
    This triggers both a message and an exception to verify:
    1. Sentry is properly configured
    2. Errors are captured and sent
    3. Context and breadcrumbs work correctly
    
    Usage:
        GET /ops/test-sentry-error
    
    Returns:
        JSON response with test status
    """
    # Check if Sentry is enabled
    if not current_app.config.get('SENTRY_DSN') and not sentry_sdk.Hub.current.client:
        return jsonify({
            "status": "error",
            "message": "Sentry is not configured (SENTRY_DSN not set)"
        }), 503
    
    # Add custom context
    sentry_sdk.set_context("test_context", {
        "test_type": "error_tracking",
        "timestamp": time.time(),
        "environment": current_app.config.get('ENV', 'unknown')
    })
    
    # Add tags for filtering
    sentry_sdk.set_tag("test", "true")
    sentry_sdk.set_tag("endpoint", "/ops/test-sentry-error")
    
    # Send a test message
    sentry_sdk.capture_message("Test message from Mina ops endpoint", level="info")
    logger.info("Sentry test message sent")
    
    # Trigger a test exception
    try:
        # Intentional error for testing
        test_value = 1 / 0  # ZeroDivisionError
    except ZeroDivisionError as e:
        sentry_sdk.capture_exception(e)
        logger.error("Sentry test exception captured")
    
    return jsonify({
        "status": "success",
        "message": "Test error and message sent to Sentry",
        "check": "Visit Sentry dashboard to verify events were captured",
        "events": [
            {"type": "message", "content": "Test message from Mina ops endpoint"},
            {"type": "exception", "content": "ZeroDivisionError: division by zero"}
        ]
    }), 200


@ops_bp.route('/test-sentry-performance', methods=['GET'])
def test_sentry_performance():
    """
    Test endpoint to demonstrate Sentry performance monitoring (APM).
    
    This creates a transaction with multiple spans to show:
    1. Transaction tracking (overall request timing)
    2. Span tracking (individual operation timing)
    3. Database query simulation
    4. API call simulation
    5. Custom operations
    
    Usage:
        GET /ops/test-sentry-performance
    
    Returns:
        JSON response with performance test results
    """
    # Check if Sentry is enabled
    if not current_app.config.get('SENTRY_DSN') and not sentry_sdk.Hub.current.client:
        return jsonify({
            "status": "error",
            "message": "Sentry is not configured (SENTRY_DSN not set)"
        }), 503
    
    # Start a transaction for the entire operation
    with sentry_sdk.start_transaction(op="test", name="/ops/test-sentry-performance") as transaction:
        transaction.set_tag("test", "true")
        transaction.set_tag("feature", "performance_monitoring")
        
        results = {
            "status": "success",
            "message": "Performance test completed",
            "operations": []
        }
        
        # Simulate database query
        with sentry_sdk.start_span(op="db.query", description="Fetch user data") as span:
            span.set_tag("db.system", "postgresql")
            span.set_data("query", "SELECT * FROM users WHERE active = true")
            
            start_time = time.time()
            time.sleep(random.uniform(0.05, 0.15))  # Simulate query time
            duration = time.time() - start_time
            
            results["operations"].append({
                "name": "Database Query",
                "duration_ms": round(duration * 1000, 2),
                "description": "Simulated user fetch"
            })
        
        # Simulate API call
        with sentry_sdk.start_span(op="http.client", description="OpenAI API call") as span:
            span.set_tag("http.method", "POST")
            span.set_tag("service", "openai")
            span.set_data("url", "https://api.openai.com/v1/audio/transcriptions")
            
            start_time = time.time()
            time.sleep(random.uniform(0.1, 0.3))  # Simulate API latency
            duration = time.time() - start_time
            
            results["operations"].append({
                "name": "OpenAI API Call",
                "duration_ms": round(duration * 1000, 2),
                "description": "Simulated transcription request"
            })
        
        # Simulate data processing
        with sentry_sdk.start_span(op="process", description="Process transcription results") as span:
            span.set_data("items_processed", 42)
            
            start_time = time.time()
            time.sleep(random.uniform(0.02, 0.08))  # Simulate processing
            duration = time.time() - start_time
            
            results["operations"].append({
                "name": "Data Processing",
                "duration_ms": round(duration * 1000, 2),
                "description": "Process and format results"
            })
        
        # Simulate cache operation
        with sentry_sdk.start_span(op="cache.set", description="Cache transcription") as span:
            span.set_tag("cache.system", "redis")
            span.set_data("key", "meeting:12345:transcript")
            
            start_time = time.time()
            time.sleep(random.uniform(0.01, 0.03))  # Simulate cache write
            duration = time.time() - start_time
            
            results["operations"].append({
                "name": "Cache Write",
                "duration_ms": round(duration * 1000, 2),
                "description": "Store in Redis"
            })
        
        # Calculate total duration
        total_duration = sum(op["duration_ms"] for op in results["operations"])
        results["total_duration_ms"] = round(total_duration, 2)
        results["check"] = "Visit Sentry Performance tab to view transaction details"
        
        logger.info(f"Performance test completed: {total_duration}ms total")
    
    return jsonify(results), 200


@ops_bp.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint for monitoring.
    
    Returns:
        JSON response with health status
    """
    return jsonify({
        "status": "healthy",
        "service": "mina-transcription",
        "sentry_enabled": sentry_sdk.Hub.current.client is not None
    }), 200


def register_ops_routes(app):
    """Register ops blueprint with the Flask app."""
    app.register_blueprint(ops_bp)
    logger.info("✅ Ops routes registered (Sentry testing, performance demos)")
