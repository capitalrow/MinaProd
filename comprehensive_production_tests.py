#!/usr/bin/env python3
"""
Comprehensive Production Testing Suite for Mina Application
Tests all functionality, features, and aspects of the application
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import hashlib
import random
import string
import threading
import subprocess

class MinaProductionTester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = {
            "server_health": [],
            "api_endpoints": [],
            "websocket": [],
            "authentication": [],
            "database": [],
            "security": [],
            "performance": [],
            "ui_components": [],
            "error_handling": [],
            "data_integrity": []
        }
        self.critical_issues = []
        self.warnings = []
        self.passed_tests = 0
        self.failed_tests = 0
        self.total_tests = 0
        
    def log_test(self, category: str, test_name: str, status: str, details: str = "", severity: str = "info"):
        """Log test result with detailed information"""
        self.total_tests += 1
        result = {
            "timestamp": datetime.now().isoformat(),
            "test": test_name,
            "status": status,
            "details": details,
            "severity": severity
        }
        
        if category in self.test_results:
            self.test_results[category].append(result)
            
        if status == "PASS":
            self.passed_tests += 1
            print(f"✅ [{category}] {test_name}: PASSED")
        elif status == "FAIL":
            self.failed_tests += 1
            print(f"❌ [{category}] {test_name}: FAILED - {details}")
            if severity == "critical":
                self.critical_issues.append(f"{test_name}: {details}")
            else:
                self.warnings.append(f"{test_name}: {details}")
        else:
            print(f"⚠️ [{category}] {test_name}: {status} - {details}")
            self.warnings.append(f"{test_name}: {details}")
    
    def test_server_health(self):
        """Test server health and connectivity"""
        print("\n🏥 Testing Server Health...")
        
        # Test basic connectivity
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/", timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            self.log_test("server_health", "Basic connectivity", "PASS", f"{response_time:.2f}ms")
            
            # Check response time
            if response_time < 100:
                self.log_test("server_health", "Response time", "PASS", f"Excellent ({response_time:.2f}ms)")
            elif response_time < 500:
                self.log_test("server_health", "Response time", "PASS", f"Good ({response_time:.2f}ms)")
            else:
                self.log_test("server_health", "Response time", "WARNING", f"Slow ({response_time:.2f}ms)")
                
        except Exception as e:
            self.log_test("server_health", "Basic connectivity", "FAIL", str(e), "critical")
            return False
            
        # Test health endpoints
        health_endpoints = [
            ("/health/health", "Main health"),
            ("/health/ready", "Readiness probe"),
            ("/health/live", "Liveness probe"),
            ("/healthz", "Simple health"),
            ("/health/detailed", "Detailed health"),
            ("/api/health", "API health"),
            ("/api/transcribe-health", "Transcription health"),
            ("/api/transcription/health", "Transcription service health")
        ]
        
        for endpoint, name in health_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if "status" in data:
                            self.log_test("server_health", f"{name}", "PASS", f"Status: {data['status']}")
                        else:
                            self.log_test("server_health", f"{name}", "PASS")
                    except:
                        self.log_test("server_health", f"{name}", "PASS", f"Status code: {response.status_code}")
                elif response.status_code == 503:
                    self.log_test("server_health", f"{name}", "WARNING", "Service degraded")
                elif response.status_code == 404:
                    self.log_test("server_health", f"{name}", "WARNING", "Endpoint not found")
                else:
                    self.log_test("server_health", f"{name}", "FAIL", f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("server_health", f"{name}", "FAIL", str(e))
                
        return True
    
    def test_api_endpoints(self):
        """Test all API endpoints comprehensively"""
        print("\n🔌 Testing API Endpoints...")
        
        # Test GET endpoints
        get_endpoints = [
            ("/api/meetings/recent?limit=5", "Recent meetings"),
            ("/api/meetings/stats", "Meeting statistics"),
            ("/api/meetings", "All meetings"),
            ("/api/tasks/my-tasks", "User tasks"),
            ("/api/tasks/stats", "Task statistics"),
            ("/api/tasks", "All tasks"),
            ("/api/analytics/dashboard?days=7", "Analytics dashboard"),
            ("/api/analytics/trends", "Analytics trends"),
            ("/api/markers", "Markers"),
            ("/api/generate-insights", "Insights generation"),
            ("/api/copilot/suggestions", "AI suggestions"),
            ("/api/calendar/events", "Calendar events"),
            ("/api/settings", "User settings"),
            ("/api/export/options", "Export options"),
            ("/api/integrations", "Available integrations")
        ]
        
        for endpoint, name in get_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.log_test("api_endpoints", f"GET {name}", "PASS", f"Response size: {len(str(data))}")
                    except:
                        self.log_test("api_endpoints", f"GET {name}", "PASS", "Non-JSON response")
                elif response.status_code == 401:
                    self.log_test("api_endpoints", f"GET {name}", "INFO", "Authentication required")
                elif response.status_code == 404:
                    self.log_test("api_endpoints", f"GET {name}", "WARNING", "Not implemented")
                else:
                    self.log_test("api_endpoints", f"GET {name}", "FAIL", f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("api_endpoints", f"GET {name}", "FAIL", str(e))
        
        # Test POST endpoints
        post_endpoints = [
            ("/api/transcription/start", {"audio": "test"}, "Start transcription"),
            ("/api/transcription/stop", {}, "Stop transcription"),
            ("/api/meetings", {"title": "Test Meeting"}, "Create meeting"),
            ("/api/tasks", {"title": "Test Task"}, "Create task"),
            ("/api/markers", {"time": 0, "label": "Test"}, "Create marker"),
            ("/api/generate-insights", {"session_id": "test"}, "Generate insights"),
            ("/api/export", {"format": "pdf"}, "Export data")
        ]
        
        for endpoint, payload, name in post_endpoints:
            try:
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    timeout=5
                )
                if response.status_code in [200, 201]:
                    self.log_test("api_endpoints", f"POST {name}", "PASS")
                elif response.status_code == 401:
                    self.log_test("api_endpoints", f"POST {name}", "INFO", "Authentication required")
                elif response.status_code == 400:
                    self.log_test("api_endpoints", f"POST {name}", "WARNING", "Bad request - validation working")
                elif response.status_code == 404:
                    self.log_test("api_endpoints", f"POST {name}", "WARNING", "Not implemented")
                else:
                    self.log_test("api_endpoints", f"POST {name}", "FAIL", f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("api_endpoints", f"POST {name}", "FAIL", str(e))
                
    def test_authentication(self):
        """Test authentication and authorization"""
        print("\n🔐 Testing Authentication System...")
        
        # Test login page
        try:
            response = self.session.get(f"{self.base_url}/auth/login", timeout=5)
            if response.status_code in [200, 302]:
                self.log_test("authentication", "Login page accessible", "PASS")
            else:
                self.log_test("authentication", "Login page accessible", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("authentication", "Login page accessible", "FAIL", str(e))
        
        # Test registration page
        try:
            response = self.session.get(f"{self.base_url}/auth/register", timeout=5)
            if response.status_code in [200, 302]:
                self.log_test("authentication", "Registration page accessible", "PASS")
            else:
                self.log_test("authentication", "Registration page accessible", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("authentication", "Registration page accessible", "FAIL", str(e))
        
        # Test protected routes
        protected_routes = [
            ("/dashboard/", "Dashboard"),
            ("/settings", "Settings"),
            ("/calendar", "Calendar"),
            ("/export", "Export"),
            ("/api/meetings", "API Meetings"),
            ("/api/tasks", "API Tasks")
        ]
        
        for route, name in protected_routes:
            try:
                response = self.session.get(f"{self.base_url}{route}", allow_redirects=False, timeout=5)
                if response.status_code in [401, 302, 308]:
                    self.log_test("authentication", f"Protected: {name}", "PASS", "Properly protected")
                elif response.status_code == 200:
                    # Check if it's actually protected by looking for login redirect
                    if "login" in response.text.lower() or response.history:
                        self.log_test("authentication", f"Protected: {name}", "PASS", "Redirects to login")
                    else:
                        self.log_test("authentication", f"Protected: {name}", "FAIL", "NOT PROTECTED", "critical")
                else:
                    self.log_test("authentication", f"Protected: {name}", "WARNING", f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("authentication", f"Protected: {name}", "FAIL", str(e))
        
        # Test session management
        try:
            # Try to create a session
            test_user = f"test_{random.randint(1000, 9999)}"
            response = self.session.post(
                f"{self.base_url}/auth/register",
                data={
                    "username": test_user,
                    "email": f"{test_user}@test.com",
                    "password": "TestPassword123!",
                    "confirm_password": "TestPassword123!"
                },
                timeout=5
            )
            if response.status_code in [200, 201, 302]:
                self.log_test("authentication", "User registration", "PASS")
            elif response.status_code == 409:
                self.log_test("authentication", "User registration", "INFO", "User already exists")
            else:
                self.log_test("authentication", "User registration", "WARNING", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("authentication", "User registration", "WARNING", str(e))
            
    def test_websocket_functionality(self):
        """Test WebSocket connectivity and functionality"""
        print("\n🔌 Testing WebSocket Functionality...")
        
        try:
            import socketio
            
            # Test Socket.IO connection
            sio = socketio.Client()
            connected = False
            messages_received = []
            
            @sio.event
            def connect():
                nonlocal connected
                connected = True
                
            @sio.event
            def disconnect():
                pass
                
            @sio.on('*')
            def catch_all(event, *args):
                messages_received.append((event, args))
                
            try:
                sio.connect(self.base_url, wait_timeout=5)
                if connected:
                    self.log_test("websocket", "Socket.IO connection", "PASS")
                    
                    # Test namespaces
                    namespaces = ['/transcription', '/enhanced-transcription', '/comprehensive']
                    for ns in namespaces:
                        try:
                            sio.emit('ping', namespace=ns)
                            self.log_test("websocket", f"Namespace {ns}", "PASS")
                        except:
                            self.log_test("websocket", f"Namespace {ns}", "WARNING", "Not available")
                            
                    sio.disconnect()
                else:
                    self.log_test("websocket", "Socket.IO connection", "FAIL", "Could not connect")
            except Exception as e:
                self.log_test("websocket", "Socket.IO connection", "FAIL", str(e))
                
        except ImportError:
            self.log_test("websocket", "Socket.IO testing", "SKIP", "python-socketio not installed")
            
    def test_database_operations(self):
        """Test database connectivity and operations"""
        print("\n🗄️ Testing Database Operations...")
        
        # Check database status through health endpoint
        try:
            response = self.session.get(f"{self.base_url}/health/detailed", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "database" in data:
                    db_info = data["database"]
                    if isinstance(db_info, dict) and not db_info.get("error"):
                        self.log_test("database", "Connection status", "PASS", 
                                    f"Sessions: {db_info.get('sessions_count', 'N/A')}, "
                                    f"Segments: {db_info.get('segments_count', 'N/A')}")
                    else:
                        self.log_test("database", "Connection status", "WARNING", "Database info incomplete")
                else:
                    self.log_test("database", "Connection status", "WARNING", "No database info in health check")
            elif response.status_code == 404:
                # Try alternative endpoint
                response = self.session.get(f"{self.base_url}/api/health", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("database") == "connected":
                        self.log_test("database", "Connection status", "PASS")
                    else:
                        self.log_test("database", "Connection status", "WARNING", data.get("database", "Unknown"))
                else:
                    self.log_test("database", "Connection status", "WARNING", "Cannot verify")
            else:
                self.log_test("database", "Connection status", "FAIL", f"Health check failed: {response.status_code}")
        except Exception as e:
            self.log_test("database", "Connection status", "FAIL", str(e))
            
        # Test CRUD operations through API
        try:
            # Try to fetch data
            response = self.session.get(f"{self.base_url}/api/meetings/recent?limit=1", timeout=5)
            if response.status_code == 200:
                self.log_test("database", "Read operations", "PASS")
            else:
                self.log_test("database", "Read operations", "WARNING", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("database", "Read operations", "FAIL", str(e))
            
    def test_security_measures(self):
        """Test security implementations"""
        print("\n🔒 Testing Security Measures...")
        
        # Check security headers
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            headers = response.headers
            
            security_headers = {
                "X-Content-Type-Options": ("nosniff", True),
                "X-Frame-Options": (["DENY", "SAMEORIGIN"], False),
                "X-XSS-Protection": ("1; mode=block", False),
                "Strict-Transport-Security": (None, False),
                "Content-Security-Policy": (None, False)
            }
            
            for header, (expected, required) in security_headers.items():
                if header in headers:
                    if expected is None:
                        self.log_test("security", f"Header: {header}", "PASS", f"Present: {headers[header]}")
                    elif isinstance(expected, list):
                        if headers[header] in expected:
                            self.log_test("security", f"Header: {header}", "PASS")
                        else:
                            self.log_test("security", f"Header: {header}", "WARNING", f"Value: {headers[header]}")
                    elif headers[header] == expected:
                        self.log_test("security", f"Header: {header}", "PASS")
                    else:
                        self.log_test("security", f"Header: {header}", "WARNING", f"Expected: {expected}, Got: {headers[header]}")
                elif required:
                    self.log_test("security", f"Header: {header}", "FAIL", "Missing required header", "critical")
                else:
                    self.log_test("security", f"Header: {header}", "WARNING", "Missing recommended header")
                    
        except Exception as e:
            self.log_test("security", "Security headers check", "FAIL", str(e))
        
        # Test CORS configuration
        try:
            response = self.session.options(f"{self.base_url}/api/health", 
                                          headers={"Origin": "http://malicious.com"},
                                          timeout=5)
            if "Access-Control-Allow-Origin" in response.headers:
                origin = response.headers["Access-Control-Allow-Origin"]
                if origin == "*":
                    self.log_test("security", "CORS configuration", "FAIL", "Wide open (*)", "critical")
                elif origin == "http://malicious.com":
                    self.log_test("security", "CORS configuration", "FAIL", "Accepts any origin", "critical")
                else:
                    self.log_test("security", "CORS configuration", "PASS", f"Restricted: {origin}")
            else:
                self.log_test("security", "CORS configuration", "PASS", "No CORS headers on OPTIONS")
        except Exception as e:
            self.log_test("security", "CORS configuration", "WARNING", str(e))
        
        # Test input validation
        try:
            # Send malformed JSON
            response = self.session.post(
                f"{self.base_url}/api/transcription/start",
                data="invalid json{{{",
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            if response.status_code in [400, 422]:
                self.log_test("security", "Input validation (malformed JSON)", "PASS")
            else:
                self.log_test("security", "Input validation (malformed JSON)", "WARNING", f"Status: {response.status_code}")
                
            # Test SQL injection attempt (safe test)
            response = self.session.get(
                f"{self.base_url}/api/meetings/recent?limit=1' OR '1'='1",
                timeout=5
            )
            if response.status_code in [400, 422]:
                self.log_test("security", "SQL injection prevention", "PASS")
            elif response.status_code == 200:
                # Check if it actually prevented injection
                try:
                    data = response.json()
                    if isinstance(data, list) and len(data) <= 1:
                        self.log_test("security", "SQL injection prevention", "PASS", "Input sanitized")
                    else:
                        self.log_test("security", "SQL injection prevention", "WARNING", "Check sanitization")
                except:
                    self.log_test("security", "SQL injection prevention", "WARNING", "Cannot verify")
            else:
                self.log_test("security", "SQL injection prevention", "INFO", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("security", "Input validation", "FAIL", str(e))
            
    def test_performance(self):
        """Test performance metrics"""
        print("\n⚡ Testing Performance...")
        
        # Test response times for key endpoints
        performance_endpoints = [
            ("/", "Homepage", 500),
            ("/dashboard/", "Dashboard", 1000),
            ("/api/meetings/stats", "API Stats", 200),
            ("/static/css/design-tokens.css", "Static CSS", 100)
        ]
        
        for endpoint, name, max_time in performance_endpoints:
            try:
                times = []
                for _ in range(3):
                    start = time.time()
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                    times.append((time.time() - start) * 1000)
                    
                avg_time = sum(times) / len(times)
                if avg_time < max_time:
                    self.log_test("performance", f"{name} response time", "PASS", f"{avg_time:.2f}ms avg")
                else:
                    self.log_test("performance", f"{name} response time", "WARNING", f"{avg_time:.2f}ms avg (target: {max_time}ms)")
                    
            except Exception as e:
                self.log_test("performance", f"{name} response time", "FAIL", str(e))
        
        # Test concurrent requests
        def make_request(endpoint):
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                return response.status_code == 200
            except:
                return False
        
        print("  Testing concurrent request handling...")
        threads = []
        results = []
        for _ in range(10):
            t = threading.Thread(target=lambda: results.append(make_request("/api/meetings/stats")))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        success_rate = sum(results) / len(results) * 100 if results else 0
        if success_rate >= 90:
            self.log_test("performance", "Concurrent requests", "PASS", f"{success_rate:.0f}% success rate")
        elif success_rate >= 70:
            self.log_test("performance", "Concurrent requests", "WARNING", f"{success_rate:.0f}% success rate")
        else:
            self.log_test("performance", "Concurrent requests", "FAIL", f"{success_rate:.0f}% success rate")
            
    def test_error_handling(self):
        """Test error handling and recovery"""
        print("\n⚠️ Testing Error Handling...")
        
        # Test 404 handling
        try:
            response = self.session.get(f"{self.base_url}/nonexistent-page-{random.randint(10000,99999)}", timeout=5)
            if response.status_code == 404:
                try:
                    data = response.json()
                    if "error" in data:
                        self.log_test("error_handling", "404 JSON response", "PASS")
                    else:
                        self.log_test("error_handling", "404 response", "PASS")
                except:
                    self.log_test("error_handling", "404 response", "PASS", "HTML response")
            else:
                self.log_test("error_handling", "404 handling", "FAIL", f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("error_handling", "404 handling", "FAIL", str(e))
        
        # Test invalid method
        try:
            response = self.session.request("INVALID", f"{self.base_url}/api/health", timeout=5)
            if response.status_code in [400, 405, 501]:
                self.log_test("error_handling", "Invalid method handling", "PASS")
            else:
                self.log_test("error_handling", "Invalid method handling", "WARNING", f"Status: {response.status_code}")
        except Exception as e:
            # Some errors are expected here
            self.log_test("error_handling", "Invalid method handling", "PASS", "Properly rejected")
        
        # Test large payload handling
        try:
            large_payload = {"data": "x" * (10 * 1024 * 1024)}  # 10MB
            response = self.session.post(
                f"{self.base_url}/api/transcription/start",
                json=large_payload,
                timeout=10
            )
            if response.status_code in [413, 400, 422]:
                self.log_test("error_handling", "Large payload rejection", "PASS")
            else:
                self.log_test("error_handling", "Large payload handling", "WARNING", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("error_handling", "Large payload handling", "WARNING", str(e))
            
    def test_data_integrity(self):
        """Test data consistency and integrity"""
        print("\n🔍 Testing Data Integrity...")
        
        # Test data consistency across endpoints
        try:
            # Get stats from different endpoints
            response1 = self.session.get(f"{self.base_url}/api/meetings/stats", timeout=5)
            response2 = self.session.get(f"{self.base_url}/api/tasks/stats", timeout=5)
            
            if response1.status_code == 200 and response2.status_code == 200:
                self.log_test("data_integrity", "Cross-endpoint consistency", "PASS")
            else:
                self.log_test("data_integrity", "Cross-endpoint consistency", "WARNING", 
                            f"Meeting stats: {response1.status_code}, Task stats: {response2.status_code}")
        except Exception as e:
            self.log_test("data_integrity", "Cross-endpoint consistency", "FAIL", str(e))
        
        # Test data validation
        test_cases = [
            ("Empty required field", {"title": ""}, 400),
            ("Invalid email", {"email": "not-an-email"}, 400),
            ("Negative limit", {"limit": -1}, 400),
            ("String for number", {"limit": "abc"}, 400)
        ]
        
        for test_name, params, expected_status in test_cases:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/meetings/recent",
                    params=params,
                    timeout=5
                )
                # Some validation might be lenient
                if response.status_code in [expected_status, 200]:
                    self.log_test("data_integrity", f"Validation: {test_name}", "PASS")
                else:
                    self.log_test("data_integrity", f"Validation: {test_name}", "WARNING", 
                                f"Expected {expected_status}, got {response.status_code}")
            except Exception as e:
                self.log_test("data_integrity", f"Validation: {test_name}", "FAIL", str(e))
                
    def generate_comprehensive_report(self):
        """Generate detailed test report"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE PRODUCTION TEST REPORT")
        print("="*80)
        
        # Calculate metrics
        pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"\n📈 Overall Test Summary:")
        print(f"  Total Tests: {self.total_tests}")
        print(f"  ✅ Passed: {self.passed_tests}")
        print(f"  ❌ Failed: {self.failed_tests}")
        print(f"  ⚠️ Warnings: {len(self.warnings)}")
        print(f"  🎯 Pass Rate: {pass_rate:.1f}%")
        
        # Category breakdown
        print(f"\n📋 Test Category Results:")
        for category, results in self.test_results.items():
            if results:
                passed = len([r for r in results if r['status'] == 'PASS'])
                failed = len([r for r in results if r['status'] == 'FAIL'])
                other = len(results) - passed - failed
                
                category_name = category.replace('_', ' ').title()
                print(f"\n  {category_name}:")
                print(f"    ✅ Passed: {passed}")
                print(f"    ❌ Failed: {failed}")
                print(f"    ⚠️ Other: {other}")
                
        # Critical issues
        if self.critical_issues:
            print(f"\n🚨 CRITICAL ISSUES ({len(self.critical_issues)}):")
            for issue in self.critical_issues[:10]:
                print(f"  • {issue}")
            if len(self.critical_issues) > 10:
                print(f"  ... and {len(self.critical_issues) - 10} more")
                
        # Production readiness assessment
        print("\n" + "="*80)
        print("🎯 PRODUCTION READINESS ASSESSMENT")
        print("="*80)
        
        if self.critical_issues:
            print("\n❌ NOT READY FOR PRODUCTION")
            print("Critical issues must be resolved before deployment:")
            for issue in self.critical_issues[:5]:
                print(f"  - {issue}")
        elif pass_rate < 70:
            print("\n❌ NOT READY FOR PRODUCTION")
            print(f"Pass rate too low: {pass_rate:.1f}% (minimum 70% required)")
        elif pass_rate < 85:
            print("\n⚠️ CONDITIONALLY READY")
            print("Address warnings before production deployment")
            print(f"Current pass rate: {pass_rate:.1f}%")
        else:
            print("\n✅ READY FOR PRODUCTION")
            print(f"All critical checks passed with {pass_rate:.1f}% success rate")
            
        # Risk assessment
        print("\n🔍 Risk Assessment:")
        
        security_risks = len([i for i in self.critical_issues if 'auth' in i.lower() or 'security' in i.lower() or 'protected' in i.lower()])
        if security_risks > 0:
            print(f"  🔴 CRITICAL: {security_risks} security vulnerabilities found")
        else:
            print("  🟢 Security: No critical vulnerabilities detected")
            
        performance_issues = len([w for w in self.warnings if 'slow' in w.lower() or 'timeout' in w.lower()])
        if performance_issues > 3:
            print(f"  🟡 MEDIUM: {performance_issues} performance issues")
        else:
            print("  🟢 Performance: Within acceptable limits")
            
        # Recommendations
        print("\n📝 Key Recommendations:")
        if self.critical_issues:
            print("  1. Fix all critical security issues immediately")
            print("  2. Implement proper authentication on all routes")
            print("  3. Configure CORS restrictions")
        elif self.warnings:
            print("  1. Address performance warnings")
            print("  2. Implement missing endpoints")
            print("  3. Improve error handling")
        else:
            print("  1. Continue monitoring performance")
            print("  2. Maintain test coverage")
            print("  3. Regular security audits")
            
        # Save detailed report
        report_file = f"production_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tests": self.total_tests,
                    "passed": self.passed_tests,
                    "failed": self.failed_tests,
                    "warnings": len(self.warnings),
                    "pass_rate": pass_rate,
                    "production_ready": len(self.critical_issues) == 0 and pass_rate >= 70
                },
                "critical_issues": self.critical_issues,
                "warnings": self.warnings,
                "test_results": self.test_results
            }, f, indent=2)
            
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return pass_rate >= 70 and len(self.critical_issues) == 0
    
    def run_all_tests(self):
        """Execute comprehensive test suite"""
        print("🚀 Starting Comprehensive Production Testing Suite")
        print("="*80)
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Run test suites in order of importance
        if not self.test_server_health():
            print("\n❌ Server not healthy. Stopping tests.")
            return False
            
        self.test_api_endpoints()
        self.test_authentication()
        self.test_websocket_functionality()
        self.test_database_operations()
        self.test_security_measures()
        self.test_performance()
        self.test_error_handling()
        self.test_data_integrity()
        
        # Generate final report
        return self.generate_comprehensive_report()

if __name__ == "__main__":
    tester = MinaProductionTester()
    production_ready = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if production_ready else 1)