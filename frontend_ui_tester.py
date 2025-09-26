#!/usr/bin/env python3
"""
Comprehensive Frontend UI Testing Suite
Tests all aspects of the MINA frontend - functionality and cosmetics
"""

import requests
import re
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sys

class ComprehensiveFrontendTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'test_details': []
        }
    
    def log_result(self, test_name, status, details="", category=""):
        """Log test results"""
        self.results['total_tests'] += 1
        if status == 'PASS':
            self.results['passed'] += 1
            print(f"✅ {test_name}: {status}")
        elif status == 'FAIL':
            self.results['failed'] += 1
            print(f"❌ {test_name}: {status} - {details}")
        elif status == 'WARN':
            self.results['warnings'] += 1
            print(f"⚠️ {test_name}: {status} - {details}")
        
        self.results['test_details'].append({
            'test': test_name,
            'category': category,
            'status': status,
            'details': details
        })
    
    def test_homepage_loading(self):
        """Test homepage loads and basic structure"""
        print("\n🏠 TESTING HOMEPAGE...")
        try:
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                self.log_result("Homepage HTTP Response", "PASS", "200 OK", "Functionality")
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Test HTML structure
                if soup.find('html'):
                    self.log_result("HTML Structure", "PASS", "Valid HTML document", "Functionality")
                else:
                    self.log_result("HTML Structure", "FAIL", "Invalid HTML structure", "Functionality")
                
                # Test title
                title = soup.find('title')
                if title and 'mina' in title.text.lower():
                    self.log_result("Page Title", "PASS", f"Title: {title.text}", "Cosmetics")
                else:
                    self.log_result("Page Title", "WARN", "Title may not be descriptive", "Cosmetics")
                
                # Test viewport meta tag
                viewport = soup.find('meta', attrs={'name': 'viewport'})
                if viewport:
                    self.log_result("Responsive Viewport", "PASS", "Viewport meta tag present", "Cosmetics")
                else:
                    self.log_result("Responsive Viewport", "WARN", "Missing viewport meta tag", "Cosmetics")
                
                # Test CSS loading
                css_links = soup.find_all('link', rel='stylesheet')
                if css_links:
                    self.log_result("CSS Loading", "PASS", f"Found {len(css_links)} stylesheets", "Cosmetics")
                    for css in css_links:
                        href = css.get('href', '')
                        if 'bootstrap' in href:
                            self.log_result("Bootstrap CSS", "PASS", "Bootstrap detected", "Cosmetics")
                        if 'tailwind' in href:
                            self.log_result("TailwindCSS", "PASS", "Tailwind detected", "Cosmetics")
                else:
                    self.log_result("CSS Loading", "FAIL", "No stylesheets found", "Cosmetics")
                
                # Test JavaScript loading
                scripts = soup.find_all('script')
                js_count = len([s for s in scripts if s.get('src')])
                if js_count > 0:
                    self.log_result("JavaScript Loading", "PASS", f"Found {js_count} script files", "Functionality")
                else:
                    self.log_result("JavaScript Loading", "WARN", "No external JS files", "Functionality")
                
                # Test navigation structure
                nav = soup.find('nav') or soup.find(class_=re.compile('nav', re.I))
                if nav:
                    self.log_result("Navigation Structure", "PASS", "Navigation element found", "Functionality")
                else:
                    self.log_result("Navigation Structure", "WARN", "No navigation found", "Functionality")
                
                # Test main content area
                main = soup.find('main') or soup.find(class_=re.compile('main|content', re.I))
                if main:
                    self.log_result("Main Content Area", "PASS", "Main content area found", "Functionality")
                else:
                    self.log_result("Main Content Area", "WARN", "No main content area", "Functionality")
                
                # Test buttons
                buttons = soup.find_all('button') + soup.find_all('a', class_=re.compile('btn', re.I))
                if buttons:
                    self.log_result("Interactive Buttons", "PASS", f"Found {len(buttons)} buttons/links", "Functionality")
                else:
                    self.log_result("Interactive Buttons", "WARN", "No buttons found", "Functionality")
                
                # Test forms
                forms = soup.find_all('form')
                if forms:
                    self.log_result("Forms Present", "PASS", f"Found {len(forms)} forms", "Functionality")
                else:
                    self.log_result("Forms Present", "WARN", "No forms found", "Functionality")
                
                return soup
                
            else:
                self.log_result("Homepage HTTP Response", "FAIL", f"Status: {response.status_code}", "Functionality")
                return None
                
        except Exception as e:
            self.log_result("Homepage Loading", "FAIL", str(e), "Functionality")
            return None
    
    def test_authentication_pages(self):
        """Test login and register page functionality and design"""
        print("\n🔐 TESTING AUTHENTICATION PAGES...")
        
        # Test login page
        try:
            login_response = self.session.get(f"{self.base_url}/login")
            if login_response.status_code == 200:
                self.log_result("Login Page Access", "PASS", "Login page loads", "Functionality")
                
                soup = BeautifulSoup(login_response.content, 'html.parser')
                
                # Check for login form
                login_form = soup.find('form')
                if login_form:
                    self.log_result("Login Form Present", "PASS", "Form element found", "Functionality")
                    
                    # Check for email/username field
                    email_field = soup.find('input', type='email') or soup.find('input', attrs={'name': re.compile('email|username', re.I)})
                    if email_field:
                        self.log_result("Email/Username Field", "PASS", "Input field found", "Functionality")
                    else:
                        self.log_result("Email/Username Field", "WARN", "No email/username field", "Functionality")
                    
                    # Check for password field
                    password_field = soup.find('input', type='password')
                    if password_field:
                        self.log_result("Password Field", "PASS", "Password input found", "Functionality")
                    else:
                        self.log_result("Password Field", "FAIL", "No password field", "Functionality")
                    
                    # Check for submit button
                    submit_btn = soup.find('button', type='submit') or soup.find('input', type='submit')
                    if submit_btn:
                        self.log_result("Submit Button", "PASS", "Submit button found", "Functionality")
                    else:
                        self.log_result("Submit Button", "WARN", "No submit button", "Functionality")
                
        except Exception as e:
            self.log_result("Login Page Testing", "FAIL", str(e), "Functionality")
        
        # Test register page
        try:
            register_response = self.session.get(f"{self.base_url}/register")
            if register_response.status_code == 200:
                self.log_result("Register Page Access", "PASS", "Register page loads", "Functionality")
            else:
                self.log_result("Register Page Access", "WARN", f"Status: {register_response.status_code}", "Functionality")
        except Exception as e:
            self.log_result("Register Page Testing", "WARN", str(e), "Functionality")
    
    def test_main_transcription_interface(self):
        """Test the main transcription interface"""
        print("\n🎤 TESTING TRANSCRIPTION INTERFACE...")
        
        # First check if we can access transcription page
        endpoints_to_test = ['/transcribe', '/app', '/dashboard', '/live', '/session']
        
        for endpoint in endpoints_to_test:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    self.log_result(f"Transcription Page ({endpoint})", "PASS", "Page accessible", "Functionality")
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for audio/recording related elements
                    record_btn = soup.find('button', class_=re.compile('record', re.I)) or soup.find(id=re.compile('record', re.I))
                    if record_btn:
                        self.log_result("Record Button", "PASS", "Recording button found", "Functionality")
                    else:
                        self.log_result("Record Button", "WARN", "No recording button found", "Functionality")
                    
                    # Look for transcription display area
                    transcript_area = soup.find(class_=re.compile('transcript|text|output', re.I)) or soup.find('textarea') or soup.find('div', class_=re.compile('live|real.*time', re.I))
                    if transcript_area:
                        self.log_result("Transcript Display Area", "PASS", "Display area found", "Functionality")
                    else:
                        self.log_result("Transcript Display Area", "WARN", "No transcript display area", "Functionality")
                    
                    # Look for WebSocket/Socket.IO integration
                    socket_scripts = soup.find_all('script', string=re.compile('socket', re.I))
                    if socket_scripts or soup.find('script', src=re.compile('socket', re.I)):
                        self.log_result("Real-time Communication", "PASS", "Socket.IO detected", "Functionality")
                    else:
                        self.log_result("Real-time Communication", "WARN", "No Socket.IO found", "Functionality")
                    
                    break
                elif response.status_code in [302, 401]:
                    self.log_result(f"Transcription Page ({endpoint})", "WARN", f"Requires authentication ({response.status_code})", "Functionality")
                else:
                    self.log_result(f"Transcription Page ({endpoint})", "WARN", f"Status: {response.status_code}", "Functionality")
                    
            except Exception as e:
                self.log_result(f"Transcription Interface ({endpoint})", "WARN", str(e), "Functionality")
    
    def test_responsive_design(self):
        """Test responsive design elements"""
        print("\n📱 TESTING RESPONSIVE DESIGN...")
        
        try:
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check for responsive meta tag
                viewport = soup.find('meta', attrs={'name': 'viewport'})
                if viewport:
                    content = viewport.get('content', '')
                    if 'width=device-width' in content:
                        self.log_result("Mobile Viewport", "PASS", "Proper viewport configuration", "Cosmetics")
                    else:
                        self.log_result("Mobile Viewport", "WARN", "Viewport may not be optimized", "Cosmetics")
                
                # Check for responsive CSS classes (Bootstrap/Tailwind)
                html_content = str(soup)
                responsive_patterns = [
                    r'col-\w+-\d+',  # Bootstrap columns
                    r'sm:|md:|lg:|xl:',  # Tailwind breakpoints
                    r'@media',  # Media queries
                    r'responsive',  # Responsive classes
                ]
                
                responsive_found = False
                for pattern in responsive_patterns:
                    if re.search(pattern, html_content, re.I):
                        responsive_found = True
                        break
                
                if responsive_found:
                    self.log_result("Responsive CSS Classes", "PASS", "Responsive design patterns found", "Cosmetics")
                else:
                    self.log_result("Responsive CSS Classes", "WARN", "No responsive patterns detected", "Cosmetics")
                
        except Exception as e:
            self.log_result("Responsive Design Test", "FAIL", str(e), "Cosmetics")
    
    def test_accessibility_features(self):
        """Test accessibility features"""
        print("\n♿ TESTING ACCESSIBILITY FEATURES...")
        
        try:
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check for proper heading structure
                headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if headings:
                    self.log_result("Heading Structure", "PASS", f"Found {len(headings)} headings", "Accessibility")
                    
                    # Check if h1 exists
                    h1_tags = soup.find_all('h1')
                    if h1_tags:
                        self.log_result("H1 Tag Present", "PASS", "Page has H1 heading", "Accessibility")
                    else:
                        self.log_result("H1 Tag Present", "WARN", "No H1 heading found", "Accessibility")
                else:
                    self.log_result("Heading Structure", "WARN", "No headings found", "Accessibility")
                
                # Check for alt text on images
                images = soup.find_all('img')
                if images:
                    images_with_alt = [img for img in images if img.get('alt')]
                    alt_percentage = len(images_with_alt) / len(images) * 100
                    if alt_percentage >= 90:
                        self.log_result("Image Alt Text", "PASS", f"{alt_percentage:.0f}% images have alt text", "Accessibility")
                    else:
                        self.log_result("Image Alt Text", "WARN", f"Only {alt_percentage:.0f}% images have alt text", "Accessibility")
                else:
                    self.log_result("Image Alt Text", "PASS", "No images to check", "Accessibility")
                
                # Check for form labels
                inputs = soup.find_all('input')
                if inputs:
                    labeled_inputs = 0
                    for input_elem in inputs:
                        input_id = input_elem.get('id')
                        input_name = input_elem.get('name')
                        
                        # Check for associated label
                        if input_id and soup.find('label', attrs={'for': input_id}):
                            labeled_inputs += 1
                        elif input_elem.find_parent('label'):
                            labeled_inputs += 1
                        elif input_elem.get('aria-label') or input_elem.get('placeholder'):
                            labeled_inputs += 1
                    
                    label_percentage = labeled_inputs / len(inputs) * 100
                    if label_percentage >= 90:
                        self.log_result("Form Labels", "PASS", f"{label_percentage:.0f}% inputs have labels", "Accessibility")
                    else:
                        self.log_result("Form Labels", "WARN", f"Only {label_percentage:.0f}% inputs have labels", "Accessibility")
                
                # Check for ARIA attributes
                aria_elements = soup.find_all(attrs={'aria-label': True}) + soup.find_all(attrs={'aria-describedby': True}) + soup.find_all(attrs={'role': True})
                if aria_elements:
                    self.log_result("ARIA Attributes", "PASS", f"Found {len(aria_elements)} ARIA attributes", "Accessibility")
                else:
                    self.log_result("ARIA Attributes", "WARN", "No ARIA attributes found", "Accessibility")
                
        except Exception as e:
            self.log_result("Accessibility Testing", "FAIL", str(e), "Accessibility")
    
    def test_performance_metrics(self):
        """Test basic performance metrics"""
        print("\n⚡ TESTING PERFORMANCE...")
        
        # Test page load time
        start_time = time.time()
        try:
            response = self.session.get(self.base_url)
            load_time = time.time() - start_time
            
            if load_time < 2.0:
                self.log_result("Page Load Time", "PASS", f"{load_time:.2f}s (Excellent)", "Performance")
            elif load_time < 5.0:
                self.log_result("Page Load Time", "PASS", f"{load_time:.2f}s (Good)", "Performance")
            else:
                self.log_result("Page Load Time", "WARN", f"{load_time:.2f}s (Slow)", "Performance")
            
            # Test content size
            content_size = len(response.content) / 1024  # KB
            if content_size < 500:
                self.log_result("Page Size", "PASS", f"{content_size:.1f}KB (Optimized)", "Performance")
            elif content_size < 1000:
                self.log_result("Page Size", "PASS", f"{content_size:.1f}KB (Reasonable)", "Performance")
            else:
                self.log_result("Page Size", "WARN", f"{content_size:.1f}KB (Large)", "Performance")
            
        except Exception as e:
            self.log_result("Performance Testing", "FAIL", str(e), "Performance")
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n🔌 TESTING API ENDPOINTS...")
        
        endpoints_to_test = [
            ('/api/health', 'Health Check'),
            ('/api/transcribe', 'Transcription API'),
            ('/api/sessions', 'Sessions API'),
            ('/api/status', 'Status API'),
        ]
        
        for endpoint, description in endpoints_to_test:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    self.log_result(f"API - {description}", "PASS", f"Endpoint accessible ({response.status_code})", "API")
                elif response.status_code in [401, 403]:
                    self.log_result(f"API - {description}", "PASS", f"Protected endpoint ({response.status_code})", "API")
                elif response.status_code == 404:
                    self.log_result(f"API - {description}", "WARN", f"Endpoint not found ({response.status_code})", "API")
                else:
                    self.log_result(f"API - {description}", "WARN", f"Unexpected status ({response.status_code})", "API")
                    
            except Exception as e:
                self.log_result(f"API - {description}", "WARN", str(e), "API")
    
    def test_static_assets(self):
        """Test static assets loading"""
        print("\n📦 TESTING STATIC ASSETS...")
        
        try:
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Test CSS files
                css_links = soup.find_all('link', rel='stylesheet')
                for css in css_links:
                    href = css.get('href', '')
                    if href.startswith('/'):
                        css_url = urljoin(self.base_url, href)
                        try:
                            css_response = self.session.get(css_url)
                            if css_response.status_code == 200:
                                self.log_result(f"CSS Asset: {href}", "PASS", "CSS file loads", "Assets")
                            else:
                                self.log_result(f"CSS Asset: {href}", "FAIL", f"Status: {css_response.status_code}", "Assets")
                        except:
                            self.log_result(f"CSS Asset: {href}", "WARN", "Could not load CSS", "Assets")
                
                # Test JS files
                js_scripts = soup.find_all('script', src=True)
                for script in js_scripts:
                    src = script.get('src', '')
                    if src.startswith('/'):
                        js_url = urljoin(self.base_url, src)
                        try:
                            js_response = self.session.get(js_url)
                            if js_response.status_code == 200:
                                self.log_result(f"JS Asset: {src}", "PASS", "JavaScript file loads", "Assets")
                            else:
                                self.log_result(f"JS Asset: {src}", "FAIL", f"Status: {js_response.status_code}", "Assets")
                        except:
                            self.log_result(f"JS Asset: {src}", "WARN", "Could not load JavaScript", "Assets")
                
        except Exception as e:
            self.log_result("Static Assets Testing", "FAIL", str(e), "Assets")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("🎯 COMPREHENSIVE FRONTEND UI TEST REPORT")
        print("="*60)
        
        # Summary
        total = self.results['total_tests']
        passed = self.results['passed']
        failed = self.results['failed']
        warnings = self.results['warnings']
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n📊 SUMMARY:")
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed} ({pass_rate:.1f}%)")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Warnings: {warnings}")
        
        # Category breakdown
        categories = {}
        for test in self.results['test_details']:
            cat = test['category'] or 'Other'
            if cat not in categories:
                categories[cat] = {'pass': 0, 'fail': 0, 'warn': 0}
            
            if test['status'] == 'PASS':
                categories[cat]['pass'] += 1
            elif test['status'] == 'FAIL':
                categories[cat]['fail'] += 1
            elif test['status'] == 'WARN':
                categories[cat]['warn'] += 1
        
        print(f"\n📋 BY CATEGORY:")
        for cat, stats in categories.items():
            total_cat = stats['pass'] + stats['fail'] + stats['warn']
            pass_rate_cat = (stats['pass'] / total_cat * 100) if total_cat > 0 else 0
            print(f"{cat}: ✅{stats['pass']} ❌{stats['fail']} ⚠️{stats['warn']} ({pass_rate_cat:.1f}%)")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if pass_rate >= 90:
            print("🟢 EXCELLENT - Production Ready")
        elif pass_rate >= 80:
            print("🟡 GOOD - Minor Issues")
        elif pass_rate >= 70:
            print("🟠 NEEDS IMPROVEMENT")
        else:
            print("🔴 NEEDS SIGNIFICANT WORK")
        
        # Detailed results
        print(f"\n📝 DETAILED RESULTS:")
        current_category = ""
        for test in self.results['test_details']:
            if test['category'] != current_category:
                current_category = test['category']
                print(f"\n{current_category.upper()}:")
            
            status_icon = "✅" if test['status'] == 'PASS' else "❌" if test['status'] == 'FAIL' else "⚠️"
            details = f" - {test['details']}" if test['details'] else ""
            print(f"  {status_icon} {test['test']}{details}")
        
        return self.results
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🧪 MINA COMPREHENSIVE FRONTEND UI TESTING")
        print("="*60)
        print("Testing both functionality and cosmetic aspects...")
        
        # Run all test categories
        homepage_soup = self.test_homepage_loading()
        self.test_authentication_pages()
        self.test_main_transcription_interface()
        self.test_responsive_design()
        self.test_accessibility_features()
        self.test_performance_metrics()
        self.test_api_endpoints()
        self.test_static_assets()
        
        # Generate final report
        return self.generate_report()

def main():
    """Main execution function"""
    tester = ComprehensiveFrontendTester()
    results = tester.run_comprehensive_test()
    
    # Return appropriate exit code
    if results['failed'] == 0:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Some failures

if __name__ == "__main__":
    main()