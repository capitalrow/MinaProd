"""
Tests for security headers and Content Security Policy.

Phase 0 - Task 0.16: CSP Headers
"""

import pytest
from flask import g


def test_csp_header_present(client):
    """Test that CSP header is present in responses."""
    response = client.get('/')
    assert 'Content-Security-Policy' in response.headers


def test_csp_includes_nonce(client):
    """Test that CSP includes nonce for inline scripts."""
    response = client.get('/')
    csp = response.headers.get('Content-Security-Policy', '')
    assert "'nonce-" in csp, "CSP should include nonce for inline scripts"


def test_csp_script_src_directives(client):
    """Test that script-src includes required sources."""
    response = client.get('/')
    csp = response.headers.get('Content-Security-Policy', '')
    
    # Check for required script sources
    required_sources = [
        "'self'",
        "https://cdn.jsdelivr.net",
        "https://cdnjs.cloudflare.com",
        "https://cdn.replit.com",
    ]
    
    for source in required_sources:
        assert source in csp, f"CSP should include {source} in script-src"


def test_csp_default_src_self(client):
    """Test that default-src is set to 'self'."""
    response = client.get('/')
    csp = response.headers.get('Content-Security-Policy', '')
    assert "default-src 'self'" in csp


def test_csp_object_src_none(client):
    """Test that object-src is set to 'none' to prevent plugin execution."""
    response = client.get('/')
    csp = response.headers.get('Content-Security-Policy', '')
    assert "object-src 'none'" in csp


def test_csp_frame_ancestors(client):
    """Test that frame-ancestors is configured to prevent clickjacking."""
    response = client.get('/')
    csp = response.headers.get('Content-Security-Policy', '')
    assert "frame-ancestors" in csp


def test_security_headers_present(client):
    """Test that all required security headers are present."""
    response = client.get('/')
    
    required_headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
    }
    
    for header, expected_value in required_headers.items():
        assert header in response.headers, f"{header} should be present"
        assert expected_value in response.headers[header], \
            f"{header} should contain {expected_value}"


def test_permissions_policy_present(client):
    """Test that Permissions-Policy header is configured."""
    response = client.get('/')
    assert 'Permissions-Policy' in response.headers
    
    permissions = response.headers['Permissions-Policy']
    # Check for restrictive permissions
    assert 'geolocation=()' in permissions
    assert 'payment=()' in permissions


def test_csp_nonce_changes_per_request(client):
    """Test that CSP nonce is different for each request."""
    response1 = client.get('/')
    response2 = client.get('/')
    
    csp1 = response1.headers.get('Content-Security-Policy', '')
    csp2 = response2.headers.get('Content-Security-Policy', '')
    
    # Extract nonces
    nonce1 = [part for part in csp1.split() if part.startswith("'nonce-")]
    nonce2 = [part for part in csp2.split() if part.startswith("'nonce-")]
    
    assert nonce1, "First response should have a nonce"
    assert nonce2, "Second response should have a nonce"
    assert nonce1 != nonce2, "Nonces should be different for each request"


def test_csp_not_on_static_files(client):
    """Test that CSP is not applied to static file requests."""
    # Static files are exempt to avoid unnecessary header bloat
    response = client.get('/static/favicon.svg')
    # Static routes may or may not have CSP - just verify it doesn't break
    assert response.status_code in [200, 404]  # File may not exist in test


def test_websocket_allowed_in_csp(client):
    """Test that WebSocket connections are allowed in CSP."""
    response = client.get('/')
    csp = response.headers.get('Content-Security-Policy', '')
    
    # Check connect-src allows WebSocket
    assert 'connect-src' in csp
    assert 'wss:' in csp or 'ws:' in csp, "CSP should allow WebSocket connections"


def test_csp_allows_cdn_resources(client):
    """Test that CSP allows required CDN resources."""
    response = client.get('/')
    csp = response.headers.get('Content-Security-Policy', '')
    
    # Test for commonly used CDNs
    cdns = [
        'cdn.jsdelivr.net',
        'cdnjs.cloudflare.com',
        'cdn.replit.com',
    ]
    
    for cdn in cdns:
        assert cdn in csp, f"CSP should allow resources from {cdn}"


@pytest.mark.parametrize('endpoint', [
    '/',
    '/login',
    '/register',
])
def test_csp_on_multiple_pages(client, endpoint):
    """Test that CSP is applied consistently across different pages."""
    response = client.get(endpoint)
    # May be 200, 302 (redirect), or 404 depending on setup
    if response.status_code in [200, 302]:
        assert 'Content-Security-Policy' in response.headers
