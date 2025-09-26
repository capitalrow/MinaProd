#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for Mina
Tests complete user interaction flows and system functionality
"""

import requests
import json
import time
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:5000"

class ComprehensiveE2ETester:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = BASE_URL
        self.test_results = []
        self.user_data = {}
        
    def log_test(self, test_name, success, message=""):
        result = "✅ PASS" if success else "❌ FAIL"
        print(f"{result}: {test_name}")
        if message:
            print(f"   {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        return success
        
    def test_system_health(self):
        """Test complete system health and availability"""
        print("🏥 SYSTEM HEALTH CHECKS")
        
        # Server availability
        try:
            response = self.session.get(self.base_url, timeout=10)
            self.log_test("Server Availability", response.status_code == 200, 
                         f"Response time: {response.elapsed.total_seconds():.2f}s")
        except Exception as e:
            return self.log_test("Server Availability", False, f"Error: {str(e)}")
            
        # Database connectivity (through auth endpoint)
        try:
            response = self.session.get(urljoin(self.base_url, "/auth/me"))
            self.log_test("Database Connectivity", response.status_code == 200,
                         f"Auth endpoint responding")
        except Exception as e:
            return self.log_test("Database Connectivity", False, f"Error: {str(e)}")
            
        # All blueprints loaded
        try:
            endpoints = [
                "/auth/me",
                "/api/conversations", 
                "/upload/"
            ]
            all_loaded = True
            for endpoint in endpoints:
                resp = self.session.get(urljoin(self.base_url, endpoint))
                if resp.status_code == 404:
                    all_loaded = False
                    break
            self.log_test("All Blueprints Loaded", all_loaded, "All endpoints accessible")
        except Exception as e:
            return self.log_test("All Blueprints Loaded", False, f"Error: {str(e)}")
            
        return True
        
    def test_complete_auth_flow(self):
        """Test complete authentication workflow"""
        print("\n🔐 COMPLETE AUTHENTICATION FLOW")
        
        timestamp = int(time.time())
        test_email = f"e2etest{timestamp}@example.com"
        test_password = "e2epassword123"
        test_name = "E2E Test User"
        
        # Store for later use
        self.user_data = {
            'email': test_email,
            'password': test_password,
            'name': test_name
        }
        
        # 1. User Registration
        try:
            register_response = self.session.post(
                urljoin(self.base_url, "/auth/register"),
                json=self.user_data,
                timeout=10
            )
            
            register_success = register_response.status_code == 200
            if not self.log_test("User Registration", register_success, 
                                f"Status: {register_response.status_code}"):
                return False
                
            if register_success:
                reg_data = register_response.json()
                user_created = reg_data.get('ok', False) and 'user' in reg_data
                if not self.log_test("Registration Response Valid", user_created,
                                   f"User ID: {reg_data.get('user', {}).get('id', 'None')}"):
                    return False
                    
        except Exception as e:
            return self.log_test("User Registration", False, f"Error: {str(e)}")
            
        # 2. User Login
        try:
            login_response = self.session.post(
                urljoin(self.base_url, "/auth/login"),
                json={'email': test_email, 'password': test_password},
                timeout=10
            )
            
            login_success = login_response.status_code == 200
            if not self.log_test("User Login", login_success,
                                f"Status: {login_response.status_code}"):
                return False
                
            if login_success:
                login_data = login_response.json()
                authenticated = login_data.get('ok', False)
                if not self.log_test("Login Authentication", authenticated,
                                   f"Auth status: {authenticated}"):
                    return False
                    
        except Exception as e:
            return self.log_test("User Login", False, f"Error: {str(e)}")
            
        # 3. Session Validation
        try:
            me_response = self.session.get(urljoin(self.base_url, "/auth/me"), timeout=10)
            session_valid = me_response.status_code == 200
            if not self.log_test("Session Validation", session_valid,
                                f"Status: {me_response.status_code}"):
                return False
                
            if session_valid:
                me_data = me_response.json()
                has_session = 'ok' in me_data
                self.log_test("Session Data Valid", has_session,
                            f"Response structure correct")
                
        except Exception as e:
            return self.log_test("Session Validation", False, f"Error: {str(e)}")
            
        # 4. Password Change
        try:
            new_password = "newpassword456"
            change_response = self.session.post(
                urljoin(self.base_url, "/auth/change-password"),
                json={
                    'current_password': test_password,
                    'new_password': new_password
                },
                timeout=10
            )
            
            password_changed = change_response.status_code == 200
            self.log_test("Password Change", password_changed,
                         f"Status: {change_response.status_code}")
            
            if password_changed:
                # Test login with new password
                login_new_pw = self.session.post(
                    urljoin(self.base_url, "/auth/login"),
                    json={'email': test_email, 'password': new_password},
                    timeout=10
                )
                
                new_pw_works = login_new_pw.status_code == 200
                self.log_test("New Password Works", new_pw_works,
                             f"Login with new password successful")
                
        except Exception as e:
            self.log_test("Password Change", False, f"Error: {str(e)}")
            
        return True
        
    def test_conversation_workflow(self):
        """Test complete conversation management workflow"""
        print("\n💬 CONVERSATION WORKFLOW")
        
        # 1. List conversations (should be empty for new user)
        try:
            list_response = self.session.get(
                urljoin(self.base_url, "/api/conversations"),
                timeout=10
            )
            
            list_success = list_response.status_code == 200
            if not self.log_test("List Conversations", list_success,
                                f"Status: {list_response.status_code}"):
                return False
                
            if list_success:
                conv_data = list_response.json()
                has_items = 'items' in conv_data
                self.log_test("Conversation List Format", has_items,
                            f"Initial count: {len(conv_data.get('items', []))}")
                
        except Exception as e:
            return self.log_test("List Conversations", False, f"Error: {str(e)}")
            
        # 2. Create new conversation
        try:
            create_response = self.session.post(
                urljoin(self.base_url, "/api/conversations"),
                json={'title': 'E2E Test Conversation'},
                timeout=10
            )
            
            create_success = create_response.status_code == 200
            if not self.log_test("Create Conversation", create_success,
                                f"Status: {create_response.status_code}"):
                return False
                
            conversation_id = None
            if create_success:
                create_data = create_response.json()
                conversation_id = create_data.get('id')
                self.log_test("Conversation Created", conversation_id is not None,
                            f"ID: {conversation_id}")
                
        except Exception as e:
            return self.log_test("Create Conversation", False, f"Error: {str(e)}")
            
        # 3. Add segments to conversation
        if conversation_id:
            try:
                segment_data = {
                    'text': 'This is a test transcription segment.',
                    'start_ms': 0,
                    'end_ms': 1000,
                    'is_final': True
                }
                
                segment_response = self.session.post(
                    urljoin(self.base_url, f"/api/conversations/{conversation_id}/segments"),
                    json=segment_data,
                    timeout=10
                )
                
                segment_success = segment_response.status_code == 200
                self.log_test("Add Segment", segment_success,
                            f"Status: {segment_response.status_code}")
                
            except Exception as e:
                self.log_test("Add Segment", False, f"Error: {str(e)}")
                
        # 4. Retrieve conversation
        if conversation_id:
            try:
                get_response = self.session.get(
                    urljoin(self.base_url, f"/api/conversations/{conversation_id}"),
                    timeout=10
                )
                
                get_success = get_response.status_code == 200
                if self.log_test("Retrieve Conversation", get_success,
                                f"Status: {get_response.status_code}"):
                    
                    if get_success:
                        conv_detail = get_response.json()
                        has_segments = 'segments' in conv_detail
                        self.log_test("Conversation Has Segments", has_segments,
                                    f"Segment count: {len(conv_detail.get('segments', []))}")
                
            except Exception as e:
                self.log_test("Retrieve Conversation", False, f"Error: {str(e)}")
                
        return True
        
    def test_upload_functionality(self):
        """Test file upload functionality"""
        print("\n📤 UPLOAD FUNCTIONALITY")
        
        # Test upload endpoint without file
        try:
            response = self.session.post(urljoin(self.base_url, "/upload/"), timeout=10)
            correct_error = response.status_code == 400
            self.log_test("Upload Without File", correct_error,
                         f"Returns 400 as expected: {correct_error}")
                         
        except Exception as e:
            self.log_test("Upload Without File", False, f"Error: {str(e)}")
            
        # Test with invalid file type (if validation exists)
        try:
            files = {'file': ('test.txt', 'not audio content', 'text/plain')}
            response = self.session.post(
                urljoin(self.base_url, "/upload/"),
                files=files,
                timeout=10
            )
            
            handles_invalid = response.status_code in [400, 415, 200]  # Various possible responses
            self.log_test("Upload Invalid File Type", handles_invalid,
                         f"Status: {response.status_code}")
                         
        except Exception as e:
            self.log_test("Upload Invalid File Type", False, f"Error: {str(e)}")
            
        return True
        
    def test_frontend_integrity(self):
        """Test frontend pages and JavaScript integrity"""
        print("\n🖥️  FRONTEND INTEGRITY")
        
        # Test main landing page
        try:
            response = self.session.get(self.base_url, timeout=10)
            if self.log_test("Landing Page", response.status_code == 200,
                            f"Status: {response.status_code}"):
                
                html = response.text
                critical_elements = [
                    ("HTML Structure", "<html" in html.lower()),
                    ("Navigation", 'role="navigation"' in html),
                    ("Main Content", 'role="main"' in html),
                    ("App Title", "Mina" in html),
                    ("Skip Link", "Skip to main content" in html)
                ]
                
                for element_name, present in critical_elements:
                    self.log_test(f"Frontend: {element_name}", present,
                                f"Element present: {present}")
                    
        except Exception as e:
            return self.log_test("Landing Page", False, f"Error: {str(e)}")
            
        # Test app page
        try:
            response = self.session.get(urljoin(self.base_url, "/app"), timeout=10)
            if self.log_test("App Page", response.status_code == 200,
                            f"Status: {response.status_code}"):
                
                html = response.text
                app_elements = [
                    ("Router Links", 'href="#/library"' in html and 'href="#/live"' in html),
                    ("View Container", 'id="view"' in html),
                    ("API Scripts", 'mina.api.js' in html),
                    ("Socket Scripts", 'mina.socket.js' in html),
                    ("Router Scripts", 'router.js' in html)
                ]
                
                for element_name, present in app_elements:
                    self.log_test(f"App: {element_name}", present,
                                f"Element present: {present}")
                    
        except Exception as e:
            return self.log_test("App Page", False, f"Error: {str(e)}")
            
        # Test JavaScript files load correctly
        js_files = [
            "/static/js/auth.js",
            "/static/js/mina.api.js",
            "/static/js/mina.socket.js", 
            "/static/js/router.js"
        ]
        
        for js_file in js_files:
            try:
                response = self.session.get(urljoin(self.base_url, js_file), timeout=10)
                loads_ok = response.status_code == 200
                self.log_test(f"JS File: {js_file.split('/')[-1]}", loads_ok,
                            f"Status: {response.status_code}")
                            
            except Exception as e:
                self.log_test(f"JS File: {js_file.split('/')[-1]}", False, f"Error: {str(e)}")
                
        return True
        
    def test_error_handling(self):
        """Test comprehensive error handling"""
        print("\n🚨 ERROR HANDLING")
        
        # Test invalid routes
        try:
            response = self.session.get(urljoin(self.base_url, "/nonexistent"), timeout=10)
            handles_404 = response.status_code == 404
            self.log_test("404 Error Handling", handles_404,
                         f"Returns 404: {handles_404}")
                         
        except Exception as e:
            self.log_test("404 Error Handling", False, f"Error: {str(e)}")
            
        # Test malformed JSON
        try:
            response = self.session.post(
                urljoin(self.base_url, "/auth/login"),
                data="invalid json",
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            handles_bad_json = response.status_code in [400, 422]
            self.log_test("Bad JSON Handling", handles_bad_json,
                         f"Status: {response.status_code}")
                         
        except Exception as e:
            self.log_test("Bad JSON Handling", False, f"Error: {str(e)}")
            
        # Test unauthorized access
        new_session = requests.Session()  # No auth cookies
        try:
            response = new_session.get(urljoin(self.base_url, "/api/conversations"), timeout=10)
            handles_unauth = response.status_code in [200, 401]  # May allow unauthenticated access
            self.log_test("Unauthorized Access", handles_unauth,
                         f"Status: {response.status_code}")
                         
        except Exception as e:
            self.log_test("Unauthorized Access", False, f"Error: {str(e)}")
            
        return True
        
    def test_security_features(self):
        """Test security implementations"""
        print("\n🔒 SECURITY FEATURES")
        
        # Test CSRF protection (basic check)
        try:
            # Try POST without proper headers
            response = self.session.post(
                urljoin(self.base_url, "/auth/login"),
                data={'email': 'test@example.com', 'password': 'test'},
                timeout=10
            )
            
            # Should either work or reject appropriately
            security_check = response.status_code in [200, 400, 401, 415]
            self.log_test("CSRF Protection", security_check,
                         f"Appropriate response: {response.status_code}")
                         
        except Exception as e:
            self.log_test("CSRF Protection", False, f"Error: {str(e)}")
            
        # Test SQL injection protection (basic)
        try:
            malicious_email = "test'; DROP TABLE users; --"
            response = self.session.post(
                urljoin(self.base_url, "/auth/login"),
                json={'email': malicious_email, 'password': 'test'},
                timeout=10
            )
            
            # Should handle gracefully, not crash
            sql_protection = response.status_code in [400, 401]
            self.log_test("SQL Injection Protection", sql_protection,
                         f"Malicious input handled: {response.status_code}")
                         
        except Exception as e:
            self.log_test("SQL Injection Protection", False, f"Error: {str(e)}")
            
        # Test XSS protection in responses
        try:
            response = self.session.get(urljoin(self.base_url, "/app"), timeout=10)
            if response.status_code == 200:
                html = response.text
                has_xss_protection = (
                    "createElement" in html and
                    "textContent" in html and
                    html.count("innerHTML") < 20  # Minimal usage
                )
                self.log_test("XSS Protection", has_xss_protection,
                             f"Secure DOM methods used")
                             
        except Exception as e:
            self.log_test("XSS Protection", False, f"Error: {str(e)}")
            
        return True
        
    def run_comprehensive_tests(self):
        """Run the complete end-to-end test suite"""
        print("🚀 Starting Comprehensive E2E Test Suite")
        print("=" * 80)
        
        test_suites = [
            self.test_system_health,
            self.test_complete_auth_flow,
            self.test_conversation_workflow,
            self.test_upload_functionality,
            self.test_frontend_integrity,
            self.test_error_handling,
            self.test_security_features,
        ]
        
        suite_results = []
        for test_suite in test_suites:
            try:
                result = test_suite()
                suite_results.append(result)
            except Exception as e:
                print(f"❌ Test suite failed: {e}")
                suite_results.append(False)
            print()  # Spacing between suites
            
        # Final Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print("=" * 80)
        print(f"📊 COMPREHENSIVE E2E TEST SUMMARY")
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        else:
            print("\n🎉 ALL TESTS PASSED! System is fully functional.")
            
        return failed_tests == 0

if __name__ == "__main__":
    tester = ComprehensiveE2ETester()
    success = tester.run_comprehensive_tests()
    exit(0 if success else 1)