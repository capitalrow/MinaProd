#!/usr/bin/env python3
"""
Comprehensive frontend-backend integration test suite
Tests all major functionality to ensure 100% working system
"""

import requests
import json
import time
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:5000"

class MinaFrontendTester:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = BASE_URL
        self.test_results = []
        
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
        
    def test_server_health(self):
        """Test if server is running and responsive"""
        try:
            response = self.session.get(self.base_url, timeout=5)
            success = response.status_code == 200
            self.log_test("Server Health Check", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Server Health Check", False, f"Error: {str(e)}")
            return False
            
    def test_static_assets(self):
        """Test if static assets load correctly"""
        assets = [
            "/static/js/auth.js",
            "/static/js/mina.api.js", 
            "/static/js/mina.socket.js",
            "/static/js/router.js"
        ]
        
        all_success = True
        for asset in assets:
            try:
                response = self.session.get(urljoin(self.base_url, asset), timeout=5)
                success = response.status_code == 200
                if not success:
                    all_success = False
                self.log_test(f"Static Asset: {asset}", success, f"Status: {response.status_code}")
            except Exception as e:
                all_success = False
                self.log_test(f"Static Asset: {asset}", False, f"Error: {str(e)}")
                
        return all_success
        
    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        # Test /auth/me endpoint
        try:
            response = self.session.get(urljoin(self.base_url, "/auth/me"), timeout=5)
            success = response.status_code == 200
            self.log_test("Auth Me Endpoint", success, f"Status: {response.status_code}")
            
            if success:
                data = response.json()
                self.log_test("Auth Me Response Format", 'ok' in data, f"Response: {data}")
                
        except Exception as e:
            self.log_test("Auth Me Endpoint", False, f"Error: {str(e)}")
            return False
            
        # Test registration endpoint
        try:
            test_user = {
                "email": f"test{int(time.time())}@example.com",
                "password": "testpassword123",
                "name": "Test User"
            }
            
            response = self.session.post(
                urljoin(self.base_url, "/auth/register"),
                json=test_user,
                timeout=5
            )
            
            success = response.status_code in [200, 409]  # 409 if user exists
            self.log_test("Auth Register Endpoint", success, f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Registration Response", 'ok' in data, f"Response: {data}")
                
        except Exception as e:
            self.log_test("Auth Register Endpoint", False, f"Error: {str(e)}")
            
        return True
        
    def test_api_endpoints(self):
        """Test API endpoints"""
        # Test conversation list
        try:
            response = self.session.get(urljoin(self.base_url, "/api/conversations"), timeout=5)
            success = response.status_code in [200, 401]  # May require auth
            self.log_test("API Conversations Endpoint", success, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("API Conversations Endpoint", False, f"Error: {str(e)}")
            
        return True
        
    def test_frontend_pages(self):
        """Test that frontend pages render without errors"""
        pages = [
            "/",
            "/app",
        ]
        
        all_success = True
        for page in pages:
            try:
                response = self.session.get(urljoin(self.base_url, page), timeout=5)
                success = response.status_code == 200
                if not success:
                    all_success = False
                self.log_test(f"Frontend Page: {page}", success, f"Status: {response.status_code}")
                
                # Check for basic HTML structure
                if success and response.text:
                    has_html = "<html" in response.text.lower()
                    has_head = "<head" in response.text.lower()
                    has_body = "<body" in response.text.lower()
                    
                    structure_ok = has_html and has_head and has_body
                    self.log_test(f"HTML Structure: {page}", structure_ok, 
                                f"HTML: {has_html}, HEAD: {has_head}, BODY: {has_body}")
                    
            except Exception as e:
                all_success = False
                self.log_test(f"Frontend Page: {page}", False, f"Error: {str(e)}")
                
        return all_success
        
    def test_upload_endpoint(self):
        """Test upload functionality"""
        try:
            # Test with no file
            response = self.session.post(urljoin(self.base_url, "/upload/"), timeout=5)
            success = response.status_code in [400, 401]  # Should fail without file
            self.log_test("Upload Endpoint (no file)", success, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Upload Endpoint", False, f"Error: {str(e)}")
            
        return True
        
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Mina Frontend-Backend Integration Tests")
        print("=" * 60)
        
        # Core functionality tests
        tests = [
            self.test_server_health,
            self.test_static_assets,
            self.test_frontend_pages,
            self.test_auth_endpoints,
            self.test_api_endpoints,
            self.test_upload_endpoint,
        ]
        
        for test in tests:
            test()
            print()  # Blank line between test groups
            
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print("=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
                    
        return failed_tests == 0

if __name__ == "__main__":
    tester = MinaFrontendTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)