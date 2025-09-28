#!/usr/bin/env python3
"""
Comprehensive Production Readiness Test Suite for Mina Application
This script tests all aspects of the application for production readiness.
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any
import socket
import subprocess

class MinaTestSuite:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.warnings = []
        self.critical_issues = []
        
    def log_result(self, category: str, test_name: str, status: str, details: str = "", severity: str = "info"):
        """Log test result with proper formatting"""
        self.total_tests += 1
        if status == "PASS":
            self.passed_tests += 1
            print(f"✅ [{category}] {test_name}: {status}")
        elif status == "FAIL":
            self.failed_tests += 1
            print(f"❌ [{category}] {test_name}: {status} - {details}")
            if severity == "critical":
                self.critical_issues.append(f"{test_name}: {details}")
            else:
                self.warnings.append(f"{test_name}: {details}")
        else:
            print(f"⚠️ [{category}] {test_name}: {status} - {details}")
            self.warnings.append(f"{test_name}: {details}")
            
        self.test_results.append({
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "test": test_name,
            "status": status,
            "details": details,
            "severity": severity
        })
        
    def test_server_connectivity(self):
        """Test basic server connectivity"""
        print("\n🔍 Testing Server Connectivity...")
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            self.log_result("Connectivity", "Server reachable", "PASS")
            
            # Test response time
            start = time.time()
            requests.get(f"{self.base_url}/", timeout=5)
            response_time = (time.time() - start) * 1000
            if response_time < 500:
                self.log_result("Performance", "Response time", "PASS", f"{response_time:.2f}ms")
            else:
                self.log_result("Performance", "Response time", "WARNING", f"{response_time:.2f}ms - slow response")
                
        except Exception as e:
            self.log_result("Connectivity", "Server reachable", "FAIL", str(e), "critical")
            return False
        return True
        
    def test_health_endpoints(self):
        """Test all health check endpoints"""
        print("\n🏥 Testing Health Endpoints...")
        health_endpoints = [
            "/health/health",
            "/health/detailed",
            "/health/ready",
            "/health/live",
            "/api/health",
            "/healthz",
            "/api/transcribe-health",
            "/health/api/health"
        ]
        
        for endpoint in health_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    self.log_result("Health", f"Endpoint {endpoint}", "PASS")
                    
                    # Check response content
                    try:
                        data = response.json()
                        if "status" in data and data["status"] in ["ok", "ready", "alive"]:
                            self.log_result("Health", f"{endpoint} status check", "PASS")
                        else:
                            self.log_result("Health", f"{endpoint} status check", "WARNING", f"Unexpected status: {data.get('status')}")
                    except:
                        pass
                elif response.status_code == 404:
                    self.log_result("Health", f"Endpoint {endpoint}", "WARNING", "Not found")
                else:
                    self.log_result("Health", f"Endpoint {endpoint}", "FAIL", f"Status code: {response.status_code}")
            except Exception as e:
                self.log_result("Health", f"Endpoint {endpoint}", "FAIL", str(e))
                
    def test_authentication_system(self):
        """Test authentication endpoints and security"""
        print("\n🔐 Testing Authentication System...")
        
        # Test login page availability
        try:
            response = requests.get(f"{self.base_url}/auth/login", timeout=5, allow_redirects=False)
            if response.status_code in [200, 302]:
                self.log_result("Auth", "Login page", "PASS")
            else:
                self.log_result("Auth", "Login page", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Auth", "Login page", "FAIL", str(e))
            
        # Test registration page
        try:
            response = requests.get(f"{self.base_url}/auth/register", timeout=5, allow_redirects=False)
            if response.status_code in [200, 302]:
                self.log_result("Auth", "Registration page", "PASS")
            else:
                self.log_result("Auth", "Registration page", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Auth", "Registration page", "FAIL", str(e))
            
        # Test protected routes
        protected_routes = ["/dashboard/", "/settings"]
        for route in protected_routes:
            try:
                response = requests.get(f"{self.base_url}{route}", timeout=5, allow_redirects=False)
                if response.status_code in [401, 302]:  # Should redirect to login
                    self.log_result("Auth", f"Protected route {route}", "PASS", "Properly protected")
                elif response.status_code == 200:
                    self.log_result("Auth", f"Protected route {route}", "FAIL", "NOT PROTECTED!", "critical")
                else:
                    self.log_result("Auth", f"Protected route {route}", "WARNING", f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Auth", f"Protected route {route}", "FAIL", str(e))
                
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n🔌 Testing API Endpoints...")
        
        api_endpoints = [
            ("/api/meetings/recent", "GET"),
            ("/api/meetings/stats", "GET"),
            ("/api/tasks/stats", "GET"),
            ("/api/analytics/dashboard?days=7", "GET"),
            ("/api/markers", "GET"),
            ("/api/transcription/start", "POST"),
            ("/api/transcription/health", "GET")
        ]
        
        for endpoint, method in api_endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", json={}, timeout=5)
                    
                if response.status_code in [200, 201]:
                    self.log_result("API", f"{method} {endpoint}", "PASS")
                elif response.status_code == 401:
                    self.log_result("API", f"{method} {endpoint}", "INFO", "Requires authentication")
                elif response.status_code == 404:
                    self.log_result("API", f"{method} {endpoint}", "WARNING", "Not found")
                else:
                    self.log_result("API", f"{method} {endpoint}", "FAIL", f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_result("API", f"{method} {endpoint}", "FAIL", str(e))
                
    def test_websocket_connectivity(self):
        """Test WebSocket connectivity"""
        print("\n🔌 Testing WebSocket Connectivity...")
        
        try:
            import socketio
            sio = socketio.Client()
            
            connected = False
            
            @sio.event
            def connect():
                nonlocal connected
                connected = True
                
            @sio.event
            def disconnect():
                pass
                
            try:
                sio.connect(self.base_url, wait_timeout=5)
                if connected:
                    self.log_result("WebSocket", "Connection", "PASS")
                    sio.disconnect()
                else:
                    self.log_result("WebSocket", "Connection", "FAIL", "Could not connect")
            except Exception as e:
                self.log_result("WebSocket", "Connection", "FAIL", str(e))
                
        except ImportError:
            self.log_result("WebSocket", "Connection", "SKIP", "python-socketio not installed")
            
    def test_static_files(self):
        """Test static file serving"""
        print("\n📁 Testing Static Files...")
        
        static_files = [
            "/static/css/design-tokens.css",
            "/static/css/typography.css",
            "/static/css/components.css",
            "/static/js/socket.io.min.js",
            "/static/js/mina-animated-logo.js"
        ]
        
        for file in static_files:
            try:
                response = requests.get(f"{self.base_url}{file}", timeout=5)
                if response.status_code == 200:
                    self.log_result("Static", f"File {file}", "PASS")
                elif response.status_code == 404:
                    self.log_result("Static", f"File {file}", "FAIL", "Not found")
                else:
                    self.log_result("Static", f"File {file}", "WARNING", f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Static", f"File {file}", "FAIL", str(e))
                
    def test_live_transcription_page(self):
        """Test live transcription page"""
        print("\n🎤 Testing Live Transcription Page...")
        
        try:
            response = requests.get(f"{self.base_url}/live", timeout=5)
            if response.status_code == 200:
                self.log_result("Live", "Page accessible", "PASS")
                
                # Check for required elements
                content = response.text
                required_elements = [
                    "transcriptionCanvas",
                    "recordButton",
                    "statusChip",
                    "socket.io"
                ]
                
                for element in required_elements:
                    if element in content:
                        self.log_result("Live", f"Element '{element}'", "PASS")
                    else:
                        self.log_result("Live", f"Element '{element}'", "FAIL", "Missing from page")
                        
            elif response.status_code == 401:
                self.log_result("Live", "Page accessible", "WARNING", "Requires authentication")
            else:
                self.log_result("Live", "Page accessible", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Live", "Page accessible", "FAIL", str(e))
            
    def test_database_connectivity(self):
        """Test database connectivity through health endpoint"""
        print("\n🗄️ Testing Database Connectivity...")
        
        try:
            response = requests.get(f"{self.base_url}/health/detailed", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "database" in data:
                    if data["database"].get("connection_pool", {}).get("status") == "available":
                        self.log_result("Database", "Connection", "PASS")
                    else:
                        self.log_result("Database", "Connection", "WARNING", "Database status unclear")
                else:
                    self.log_result("Database", "Connection", "WARNING", "Database info not available")
            else:
                self.log_result("Database", "Connection", "FAIL", f"Health endpoint returned {response.status_code}")
        except Exception as e:
            self.log_result("Database", "Connection", "FAIL", str(e))
            
    def test_security_headers(self):
        """Test security headers"""
        print("\n🔒 Testing Security Headers...")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            headers = response.headers
            
            # Check for security headers
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": None,  # Optional in dev
                "Content-Security-Policy": None  # Optional but recommended
            }
            
            for header, expected in security_headers.items():
                if header in headers:
                    if expected is None:
                        self.log_result("Security", f"Header {header}", "PASS", f"Present: {headers[header]}")
                    elif isinstance(expected, list):
                        if headers[header] in expected:
                            self.log_result("Security", f"Header {header}", "PASS")
                        else:
                            self.log_result("Security", f"Header {header}", "WARNING", f"Value: {headers[header]}")
                    elif headers[header] == expected:
                        self.log_result("Security", f"Header {header}", "PASS")
                    else:
                        self.log_result("Security", f"Header {header}", "WARNING", f"Expected: {expected}, Got: {headers[header]}")
                elif expected is not None:
                    self.log_result("Security", f"Header {header}", "WARNING", "Missing")
                    
        except Exception as e:
            self.log_result("Security", "Headers check", "FAIL", str(e))
            
    def test_error_handling(self):
        """Test error handling"""
        print("\n⚠️ Testing Error Handling...")
        
        # Test 404 handling
        try:
            response = requests.get(f"{self.base_url}/nonexistent-page-12345", timeout=5)
            if response.status_code == 404:
                self.log_result("Errors", "404 handling", "PASS")
            else:
                self.log_result("Errors", "404 handling", "FAIL", f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result("Errors", "404 handling", "FAIL", str(e))
            
        # Test invalid API request
        try:
            response = requests.post(f"{self.base_url}/api/transcription/start", 
                                    data="invalid json", 
                                    headers={"Content-Type": "application/json"},
                                    timeout=5)
            if response.status_code in [400, 422]:
                self.log_result("Errors", "Invalid JSON handling", "PASS")
            else:
                self.log_result("Errors", "Invalid JSON handling", "WARNING", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Errors", "Invalid JSON handling", "FAIL", str(e))
            
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("="*60)
        
        print(f"\n📈 Test Summary:")
        print(f"  Total Tests: {self.total_tests}")
        print(f"  ✅ Passed: {self.passed_tests}")
        print(f"  ❌ Failed: {self.failed_tests}")
        print(f"  ⚠️ Warnings: {len(self.warnings)}")
        
        pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"  Success Rate: {pass_rate:.1f}%")
        
        if self.critical_issues:
            print(f"\n🚨 CRITICAL ISSUES ({len(self.critical_issues)}):")
            for issue in self.critical_issues:
                print(f"  • {issue}")
                
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"  • {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more")
                
        # Production readiness assessment
        print("\n🎯 PRODUCTION READINESS ASSESSMENT:")
        
        if self.critical_issues:
            print("  ❌ NOT READY FOR PRODUCTION")
            print("  Critical issues must be resolved before deployment")
        elif self.failed_tests > self.total_tests * 0.2:  # More than 20% failure
            print("  ❌ NOT READY FOR PRODUCTION")
            print("  Too many failed tests")
        elif self.warnings and len(self.warnings) > 10:
            print("  ⚠️ CONDITIONALLY READY")
            print("  Address warnings for optimal production deployment")
        else:
            print("  ✅ READY FOR PRODUCTION")
            print("  All critical checks passed")
            
        # Save detailed report
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tests": self.total_tests,
                    "passed": self.passed_tests,
                    "failed": self.failed_tests,
                    "warnings": len(self.warnings),
                    "pass_rate": pass_rate
                },
                "critical_issues": self.critical_issues,
                "warnings": self.warnings,
                "detailed_results": self.test_results
            }, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")
        
    def run_all_tests(self):
        """Run all test suites"""
        print("\n🚀 Starting Comprehensive Application Testing")
        print("="*60)
        
        # Run tests in order of importance
        if not self.test_server_connectivity():
            print("\n❌ Server not reachable. Stopping tests.")
            return
            
        self.test_health_endpoints()
        self.test_authentication_system()
        self.test_api_endpoints()
        self.test_websocket_connectivity()
        self.test_static_files()
        self.test_live_transcription_page()
        self.test_database_connectivity()
        self.test_security_headers()
        self.test_error_handling()
        
        # Generate final report
        self.generate_report()

if __name__ == "__main__":
    # Run comprehensive tests
    tester = MinaTestSuite()
    tester.run_all_tests()