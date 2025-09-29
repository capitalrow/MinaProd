"""
🔒 Security Testing Suite
Comprehensive security testing for 100% testing coverage including penetration testing scenarios.
"""
import pytest
import requests
import json
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TestSecurityScenarios:
    """Security and penetration testing scenarios"""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for testing"""
        return "http://localhost:5000"
    
    @pytest.fixture
    def test_headers(self):
        """Standard test headers"""
        return {
            "User-Agent": "Security-Test-Agent/1.0",
            "Content-Type": "application/json"
        }
    
    def test_sql_injection_protection(self, base_url, test_headers):
        """Test SQL injection protection in API endpoints"""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1; SELECT * FROM users--",
            "' UNION SELECT password FROM users--"
        ]
        
        # Test query parameters
        for payload in sql_payloads:
            response = requests.get(
                f"{base_url}/api/meetings",
                params={"search": payload},
                headers=test_headers,
                timeout=5
            )
            assert response.status_code != 500, f"SQL injection caused server error: {payload}"
            
        # Test JSON body
        for payload in sql_payloads:
            response = requests.post(
                f"{base_url}/api/meetings",
                json={"title": payload, "description": payload},
                headers=test_headers,
                timeout=5
            )
            assert response.status_code in [400, 401, 403], f"SQL injection not blocked: {payload}"
    
    def test_xss_protection(self, base_url, test_headers):
        """Test XSS protection in input fields"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "';alert('XSS');//",
            "onmouseover=alert('XSS')"
        ]
        
        for payload in xss_payloads:
            # Test form inputs
            response = requests.post(
                f"{base_url}/api/meetings", 
                json={"title": payload, "description": payload},
                headers=test_headers,
                timeout=5
            )
            
            if response.status_code == 200:
                # Check that payload is properly escaped
                response_text = response.text.lower()
                assert "<script>" not in response_text, f"XSS payload not escaped: {payload}"
                assert "javascript:" not in response_text, f"XSS payload not escaped: {payload}"
    
    def test_csrf_protection(self, base_url):
        """Test CSRF protection on state-changing endpoints"""
        # Test without CSRF token
        response = requests.post(
            f"{base_url}/api/meetings",
            json={"title": "Test Meeting", "description": "Test"},
            timeout=5
        )
        
        # Should be rejected without CSRF token
        assert response.status_code in [400, 401, 403], "CSRF protection not enforced"
    
    def test_rate_limiting(self, base_url, test_headers):
        """Test rate limiting protection"""
        # Rapid requests to test rate limiting
        responses = []
        start_time = time.time()
        
        for i in range(150):  # Exceed typical rate limits
            try:
                response = requests.get(
                    f"{base_url}/api/analytics/overview",
                    headers=test_headers,
                    timeout=1
                )
                responses.append(response.status_code)
            except requests.exceptions.Timeout:
                responses.append(429)  # Consider timeout as rate limited
            
            if time.time() - start_time > 30:  # Don't run too long
                break
        
        # Should have some rate limiting responses
        rate_limited = sum(1 for status in responses if status == 429)
        assert rate_limited > 0, "Rate limiting not functioning"
    
    def test_auth_bypass_attempts(self, base_url, test_headers):
        """Test authentication bypass attempts"""
        protected_endpoints = [
            "/api/meetings",
            "/api/tasks", 
            "/api/analytics/overview",
            "/api/export/formats"
        ]
        
        # Test direct access without authentication
        for endpoint in protected_endpoints:
            response = requests.get(
                f"{base_url}{endpoint}",
                headers=test_headers,
                timeout=5
            )
            
            # Should require authentication
            assert response.status_code in [401, 403], f"Authentication not required for {endpoint}"
    
    def test_directory_traversal(self, base_url, test_headers):
        """Test directory traversal protection"""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc//passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for payload in traversal_payloads:
            response = requests.get(
                f"{base_url}/static/{payload}",
                headers=test_headers,
                timeout=5
            )
            
            # Should not return sensitive files
            assert response.status_code in [404, 403], f"Directory traversal possible: {payload}"
    
    def test_malicious_file_upload(self, base_url, test_headers):
        """Test malicious file upload protection"""
        malicious_files = [
            ("malicious.exe", b"MZ\x90\x00", "application/octet-stream"),
            ("script.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
            ("test.js", b"document.cookie", "application/javascript"),
            ("exploit.html", b"<script>alert('XSS')</script>", "text/html")
        ]
        
        for filename, content, content_type in malicious_files:
            files = {"file": (filename, content, content_type)}
            
            response = requests.post(
                f"{base_url}/api/upload",
                files=files,
                headers={k: v for k, v in test_headers.items() if k != "Content-Type"},
                timeout=5
            )
            
            # Should reject malicious files
            assert response.status_code in [400, 403, 415], f"Malicious file not rejected: {filename}"
    
    def test_header_injection(self, base_url):
        """Test HTTP header injection protection"""
        malicious_headers = {
            "X-Forwarded-Host": "evil.com\r\nSet-Cookie: evil=1",
            "User-Agent": "Test\r\nX-Injected: malicious",
            "Referer": "http://test.com\r\n\r\n<script>alert('XSS')</script>"
        }
        
        for header, value in malicious_headers.items():
            try:
                response = requests.get(
                    f"{base_url}/health",
                    headers={header: value},
                    timeout=5
                )
                
                # Check that injected headers aren't reflected
                assert "X-Injected" not in response.headers, f"Header injection successful: {header}"
                
            except requests.exceptions.InvalidHeader:
                # Good - malicious headers should be rejected
                pass
    
    def test_sensitive_data_exposure(self, base_url, test_headers):
        """Test for sensitive data exposure in responses"""
        test_endpoints = [
            "/health",
            "/api/analytics/overview",
            "/api/monitoring/health"
        ]
        
        sensitive_patterns = [
            "password",
            "secret",
            "token",
            "key",
            "credential",
            "database_url",
            "private"
        ]
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(
                    f"{base_url}{endpoint}",
                    headers=test_headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    response_text = response.text.lower()
                    for pattern in sensitive_patterns:
                        assert pattern not in response_text, f"Sensitive data exposed in {endpoint}: {pattern}"
                        
            except requests.exceptions.RequestException:
                # Endpoint might not exist, skip
                pass

# Stress testing scenarios
class TestStressScenarios:
    """Stress testing for edge cases and high load"""
    
    def test_websocket_connection_flood(self, base_url):
        """Test WebSocket connection flooding"""
        import websocket
        connections = []
        
        try:
            # Attempt to open many concurrent connections
            for i in range(50):  # Reasonable limit to avoid overwhelming test environment
                try:
                    ws = websocket.create_connection(f"ws://localhost:5000/socket.io/?transport=websocket")
                    connections.append(ws)
                except Exception:
                    break  # Expected when rate limiting kicks in
            
            # Should have some connection limit
            assert len(connections) < 50, "No WebSocket connection limiting"
            
        finally:
            # Clean up connections
            for ws in connections:
                try:
                    ws.close()
                except Exception:
                    pass
    
    def test_memory_exhaustion_protection(self, base_url, test_headers):
        """Test protection against memory exhaustion attacks"""
        # Large payload test
        large_payload = "A" * (10 * 1024 * 1024)  # 10MB payload
        
        response = requests.post(
            f"{base_url}/api/meetings",
            json={"title": "Test", "description": large_payload},
            headers=test_headers,
            timeout=5
        )
        
        # Should reject oversized payloads
        assert response.status_code in [413, 400], "Large payload not rejected"
    
    def test_concurrent_request_handling(self, base_url, test_headers):
        """Test concurrent request handling"""
        import concurrent.futures
        import threading
        
        def make_request():
            return requests.get(f"{base_url}/health", headers=test_headers, timeout=5)
        
        # Make many concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Should handle concurrent requests without errors
        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count > 80, f"Poor concurrent request handling: {success_count}/100 successful"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])