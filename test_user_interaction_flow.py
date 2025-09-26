#!/usr/bin/env python3
"""
Comprehensive User Interaction Flow Test for Mina
Tests complete user journey from signup to transcription
"""

import requests
import time
import json
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:5000"

class UserInteractionFlowTester:
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
        
    def test_user_journey_complete(self):
        """Test complete user journey from signup to usage"""
        print("👤 COMPLETE USER JOURNEY TEST")
        
        timestamp = int(time.time())
        test_email = f"journey{timestamp}@example.com"
        test_password = "journeypass123"
        test_name = "Journey Test User"
        
        # Store for later use
        self.user_data = {
            'email': test_email,
            'password': test_password,
            'name': test_name
        }
        
        # Step 1: Landing page access
        try:
            landing_response = self.session.get(self.base_url, timeout=10)
            landing_ok = landing_response.status_code == 200
            if not self.log_test("Landing Page Access", landing_ok,
                                f"Status: {landing_response.status_code}"):
                return False
                
            if landing_ok:
                html = landing_response.text
                has_welcome = "Mina" in html
                has_nav = 'role="navigation"' in html
                has_main = 'role="main"' in html
                has_skip = "Skip to main content" in html
                
                structure_ok = has_welcome and has_nav and has_main and has_skip
                self.log_test("Landing Page Structure", structure_ok,
                            f"Welcome: {has_welcome}, Nav: {has_nav}, Main: {has_main}, Skip: {has_skip}")
                
        except Exception as e:
            return self.log_test("Landing Page Access", False, f"Error: {str(e)}")
            
        # Step 2: App page access
        try:
            app_response = self.session.get(urljoin(self.base_url, "/app"), timeout=10)
            app_ok = app_response.status_code == 200
            if not self.log_test("App Page Access", app_ok,
                                f"Status: {app_response.status_code}"):
                return False
                
            if app_ok:
                html = app_response.text
                has_router = "#/library" in html and "#/live" in html
                has_scripts = "mina.api.js" in html and "router.js" in html
                
                app_structure_ok = has_router and has_scripts
                self.log_test("App Page Structure", app_structure_ok,
                            f"Router: {has_router}, Scripts: {has_scripts}")
                
        except Exception as e:
            return self.log_test("App Page Access", False, f"Error: {str(e)}")
            
        # Step 3: User Registration
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
                user_id = reg_data.get('user', {}).get('id')
                
                if not self.log_test("Registration Success", user_created,
                                   f"User ID: {user_id}"):
                    return False
                    
                self.user_data['id'] = user_id
                
        except Exception as e:
            return self.log_test("User Registration", False, f"Error: {str(e)}")
            
        # Step 4: User Login
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
            
        # Step 5: Session persistence check
        try:
            me_response = self.session.get(urljoin(self.base_url, "/auth/me"), timeout=10)
            session_valid = me_response.status_code == 200
            
            if self.log_test("Session Persistence", session_valid,
                            f"Status: {me_response.status_code}"):
                
                if session_valid:
                    me_data = me_response.json()
                    session_active = me_data.get('ok', False)
                    self.log_test("Session Active", session_active,
                                f"Session working: {session_active}")
                    
        except Exception as e:
            self.log_test("Session Persistence", False, f"Error: {str(e)}")
            
        # Step 6: Create conversation
        try:
            conv_response = self.session.post(
                urljoin(self.base_url, "/api/conversations"),
                json={'title': 'Journey Test Conversation'},
                timeout=10
            )
            
            conv_success = conv_response.status_code == 200
            if self.log_test("Create Conversation", conv_success,
                            f"Status: {conv_response.status_code}"):
                
                if conv_success:
                    conv_data = conv_response.json()
                    conv_id = conv_data.get('id')
                    self.log_test("Conversation Created", conv_id is not None,
                                f"Conversation ID: {conv_id}")
                    self.user_data['conversation_id'] = conv_id
                    
        except Exception as e:
            self.log_test("Create Conversation", False, f"Error: {str(e)}")
            
        # Step 7: Add content to conversation
        if self.user_data.get('conversation_id'):
            try:
                segment_data = {
                    'text': 'Hello, this is a test transcription from the user journey.',
                    'start_ms': 0,
                    'end_ms': 2000,
                    'is_final': True
                }
                
                segment_response = self.session.post(
                    urljoin(self.base_url, f"/api/conversations/{self.user_data['conversation_id']}/segments"),
                    json=segment_data,
                    timeout=10
                )
                
                segment_success = segment_response.status_code == 200
                self.log_test("Add Transcription Segment", segment_success,
                            f"Status: {segment_response.status_code}")
                
            except Exception as e:
                self.log_test("Add Transcription Segment", False, f"Error: {str(e)}")
                
        # Step 8: Retrieve conversation with content
        if self.user_data.get('conversation_id'):
            try:
                get_conv_response = self.session.get(
                    urljoin(self.base_url, f"/api/conversations/{self.user_data['conversation_id']}"),
                    timeout=10
                )
                
                get_conv_success = get_conv_response.status_code == 200
                if self.log_test("Retrieve Conversation", get_conv_success,
                                f"Status: {get_conv_response.status_code}"):
                    
                    if get_conv_success:
                        conv_detail = get_conv_response.json()
                        has_content = (
                            'conversation' in conv_detail and
                            'segments' in conv_detail and
                            len(conv_detail.get('segments', [])) > 0
                        )
                        
                        self.log_test("Conversation Has Content", has_content,
                                    f"Segments: {len(conv_detail.get('segments', []))}")
                        
            except Exception as e:
                self.log_test("Retrieve Conversation", False, f"Error: {str(e)}")
                
        # Step 9: List all conversations
        try:
            list_response = self.session.get(
                urljoin(self.base_url, "/api/conversations"),
                timeout=10
            )
            
            list_success = list_response.status_code == 200
            if self.log_test("List Conversations", list_success,
                            f"Status: {list_response.status_code}"):
                
                if list_success:
                    list_data = list_response.json()
                    has_items = 'items' in list_data and len(list_data['items']) > 0
                    self.log_test("Conversation List Has Items", has_items,
                                f"Count: {len(list_data.get('items', []))}")
                    
        except Exception as e:
            self.log_test("List Conversations", False, f"Error: {str(e)}")
            
        # Step 10: Test logout
        try:
            logout_response = self.session.post(
                urljoin(self.base_url, "/auth/logout"),
                timeout=10
            )
            
            logout_success = logout_response.status_code == 200
            if self.log_test("User Logout", logout_success,
                            f"Status: {logout_response.status_code}"):
                
                # Verify session is cleared
                me_after_logout = self.session.get(urljoin(self.base_url, "/auth/me"), timeout=10)
                if me_after_logout.status_code == 200:
                    me_logout_data = me_after_logout.json()
                    session_cleared = not me_logout_data.get('ok', True)
                    self.log_test("Session Cleared After Logout", session_cleared,
                                f"Session cleared: {session_cleared}")
                    
        except Exception as e:
            self.log_test("User Logout", False, f"Error: {str(e)}")
            
        return True
        
    def test_error_scenarios(self):
        """Test various error scenarios and edge cases"""
        print("\n🚨 ERROR SCENARIO TESTING")
        
        # Test duplicate registration
        try:
            duplicate_response = self.session.post(
                urljoin(self.base_url, "/auth/register"),
                json=self.user_data,  # Same email as before
                timeout=10
            )
            
            handles_duplicate = duplicate_response.status_code == 409
            self.log_test("Duplicate Email Registration", handles_duplicate,
                         f"Returns 409 Conflict: {handles_duplicate}")
                         
        except Exception as e:
            self.log_test("Duplicate Email Registration", False, f"Error: {str(e)}")
            
        # Test invalid login
        try:
            invalid_response = self.session.post(
                urljoin(self.base_url, "/auth/login"),
                json={'email': 'nonexistent@example.com', 'password': 'wrongpass'},
                timeout=10
            )
            
            handles_invalid = invalid_response.status_code == 401
            self.log_test("Invalid Login Credentials", handles_invalid,
                         f"Returns 401 Unauthorized: {handles_invalid}")
                         
        except Exception as e:
            self.log_test("Invalid Login Credentials", False, f"Error: {str(e)}")
            
        # Test missing required fields
        try:
            incomplete_response = self.session.post(
                urljoin(self.base_url, "/auth/register"),
                json={'email': 'incomplete@example.com'},  # Missing password
                timeout=10
            )
            
            handles_incomplete = incomplete_response.status_code == 400
            self.log_test("Incomplete Registration Data", handles_incomplete,
                         f"Returns 400 Bad Request: {handles_incomplete}")
                         
        except Exception as e:
            self.log_test("Incomplete Registration Data", False, f"Error: {str(e)}")
            
        return True
        
    def run_user_flow_tests(self):
        """Run complete user interaction flow tests"""
        print("🎯 Starting User Interaction Flow Tests")
        print("=" * 80)
        
        test_suites = [
            self.test_user_journey_complete,
            self.test_error_scenarios,
        ]
        
        for test_suite in test_suites:
            try:
                test_suite()
            except Exception as e:
                print(f"❌ Test suite failed: {e}")
            print()  # Spacing between suites
            
        # Final Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print("=" * 80)
        print(f"📊 USER FLOW TEST SUMMARY")
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
            print("\n🎉 ALL USER FLOW TESTS PASSED! Complete functionality verified.")
            
        return failed_tests == 0

if __name__ == "__main__":
    tester = UserInteractionFlowTester()
    success = tester.run_user_flow_tests()
    exit(0 if success else 1)