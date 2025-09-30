#!/usr/bin/env python3
"""
Comprehensive Frontend UI/UX Audit for Mina Application
Deep testing of all UI components, accessibility, responsiveness, and user experience
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess

class ComprehensiveFrontendAudit:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.audit_results = {
            "accessibility": [],
            "ui_components": [],
            "responsiveness": [],
            "performance": [],
            "seo": [],
            "navigation": [],
            "forms": [],
            "javascript": [],
            "css": [],
            "cross_browser": []
        }
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.warnings = []
        self.critical_issues = []
        
    def log_test(self, category: str, test_name: str, status: str, details: str = "", severity: str = "info"):
        """Log audit test result"""
        self.total_tests += 1
        result = {
            "timestamp": datetime.now().isoformat(),
            "test": test_name,
            "status": status,
            "details": details,
            "severity": severity
        }
        
        if category in self.audit_results:
            self.audit_results[category].append(result)
            
        if status == "PASS":
            self.passed_tests += 1
            print(f"✅ [{category}] {test_name}")
        elif status == "FAIL":
            self.failed_tests += 1
            print(f"❌ [{category}] {test_name}: {details}")
            if severity == "critical":
                self.critical_issues.append(f"{test_name}: {details}")
            else:
                self.warnings.append(f"{test_name}: {details}")
        else:
            print(f"⚠️ [{category}] {test_name}: {details}")
            self.warnings.append(f"{test_name}: {details}")
    
    def fetch_page(self, path: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page"""
        try:
            response = self.session.get(f"{self.base_url}{path}", timeout=10)
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'html.parser')
            elif response.status_code == 302:
                # Follow redirect
                if 'location' in response.headers:
                    new_path = response.headers['location']
                    response = self.session.get(f"{self.base_url}{new_path}", timeout=10)
                    if response.status_code == 200:
                        return BeautifulSoup(response.text, 'html.parser')
            return None
        except Exception as e:
            print(f"  Failed to fetch {path}: {e}")
            return None
    
    def test_accessibility(self, soup: BeautifulSoup, page_name: str):
        """Comprehensive accessibility testing (WCAG 2.1 AA)"""
        print(f"  Testing accessibility for {page_name}...")
        
        # 1. Language attribute
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            self.log_test("accessibility", f"{page_name} - HTML lang attribute", "PASS")
        else:
            self.log_test("accessibility", f"{page_name} - HTML lang attribute", "FAIL", 
                         "Missing lang attribute", "critical")
        
        # 2. Page title
        title = soup.find('title')
        if title and title.string and len(title.string.strip()) > 0:
            if len(title.string) > 60:
                self.log_test("accessibility", f"{page_name} - Page title", "WARNING", 
                             f"Title too long ({len(title.string)} chars)")
            else:
                self.log_test("accessibility", f"{page_name} - Page title", "PASS")
        else:
            self.log_test("accessibility", f"{page_name} - Page title", "FAIL", 
                         "Missing or empty title", "critical")
        
        # 3. Heading hierarchy
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        h1_count = len(soup.find_all('h1'))
        if h1_count == 0:
            self.log_test("accessibility", f"{page_name} - H1 heading", "FAIL", 
                         "No H1 heading found", "high")
        elif h1_count > 1:
            self.log_test("accessibility", f"{page_name} - H1 heading", "WARNING", 
                         f"Multiple H1 headings ({h1_count})")
        else:
            self.log_test("accessibility", f"{page_name} - H1 heading", "PASS")
        
        # 4. Image alt text
        images = soup.find_all('img')
        images_without_alt = [img for img in images if not img.get('alt')]
        if images:
            if images_without_alt:
                self.log_test("accessibility", f"{page_name} - Image alt text", "FAIL", 
                             f"{len(images_without_alt)}/{len(images)} missing alt text", "high")
            else:
                self.log_test("accessibility", f"{page_name} - Image alt text", "PASS", 
                             f"All {len(images)} images have alt text")
        
        # 5. Form labels
        forms = soup.find_all('form')
        unlabeled_inputs = 0
        total_inputs = 0
        for form in forms:
            inputs = form.find_all(['input', 'textarea', 'select'])
            for input_elem in inputs:
                input_type = input_elem.get('type', 'text')
                if input_type not in ['submit', 'button', 'hidden']:
                    total_inputs += 1
                    input_id = input_elem.get('id')
                    label = soup.find('label', {'for': input_id}) if input_id else None
                    if not label and not input_elem.get('aria-label') and not input_elem.get('aria-labelledby'):
                        unlabeled_inputs += 1
        
        if total_inputs > 0:
            if unlabeled_inputs > 0:
                self.log_test("accessibility", f"{page_name} - Form labels", "FAIL", 
                             f"{unlabeled_inputs}/{total_inputs} inputs missing labels", "high")
            else:
                self.log_test("accessibility", f"{page_name} - Form labels", "PASS")
        
        # 6. ARIA attributes
        aria_elements = soup.find_all(attrs={"role": True})
        aria_labels = soup.find_all(attrs={"aria-label": True})
        if aria_elements or aria_labels:
            self.log_test("accessibility", f"{page_name} - ARIA usage", "PASS", 
                         f"{len(aria_elements)} roles, {len(aria_labels)} labels")
        else:
            self.log_test("accessibility", f"{page_name} - ARIA usage", "WARNING", 
                         "No ARIA attributes found")
        
        # 7. Keyboard navigation (check for tabindex)
        interactive_elements = soup.find_all(['a', 'button', 'input', 'textarea', 'select'])
        elements_with_tabindex = soup.find_all(attrs={"tabindex": True})
        if elements_with_tabindex:
            negative_tabindex = [e for e in elements_with_tabindex if int(e.get('tabindex', 0)) < 0]
            if negative_tabindex:
                self.log_test("accessibility", f"{page_name} - Keyboard navigation", "WARNING", 
                             f"{len(negative_tabindex)} elements with negative tabindex")
            else:
                self.log_test("accessibility", f"{page_name} - Keyboard navigation", "PASS")
        
        # 8. Color contrast (basic check for text visibility)
        small_text = soup.find_all(string=True)
        if small_text:
            self.log_test("accessibility", f"{page_name} - Text content", "PASS", 
                         "Text content present")
        
        # 9. Skip navigation link
        skip_link = soup.find('a', string=re.compile('skip', re.I)) or \
                   soup.find('a', {'href': '#main'}) or \
                   soup.find('a', {'href': '#content'})
        if skip_link:
            self.log_test("accessibility", f"{page_name} - Skip navigation", "PASS")
        else:
            self.log_test("accessibility", f"{page_name} - Skip navigation", "WARNING", 
                         "No skip navigation link found")
    
    def test_ui_components(self, soup: BeautifulSoup, page_name: str):
        """Test UI components and structure"""
        print(f"  Testing UI components for {page_name}...")
        
        # Navigation
        nav = soup.find('nav') or soup.find(class_=re.compile('nav', re.I))
        if nav:
            nav_links = nav.find_all('a')
            self.log_test("ui_components", f"{page_name} - Navigation", "PASS", 
                         f"{len(nav_links)} links")
        else:
            self.log_test("ui_components", f"{page_name} - Navigation", "WARNING", 
                         "No navigation element")
        
        # Header
        header = soup.find('header') or soup.find(class_=re.compile('header', re.I))
        if header:
            self.log_test("ui_components", f"{page_name} - Header", "PASS")
        else:
            self.log_test("ui_components", f"{page_name} - Header", "WARNING", 
                         "No header element")
        
        # Footer
        footer = soup.find('footer') or soup.find(class_=re.compile('footer', re.I))
        if footer:
            self.log_test("ui_components", f"{page_name} - Footer", "PASS")
        else:
            self.log_test("ui_components", f"{page_name} - Footer", "WARNING", 
                         "No footer element")
        
        # Buttons
        buttons = soup.find_all(['button']) + soup.find_all('input', {'type': 'button'}) + \
                 soup.find_all('input', {'type': 'submit'})
        if buttons:
            disabled_buttons = [b for b in buttons if b.get('disabled')]
            self.log_test("ui_components", f"{page_name} - Buttons", "PASS", 
                         f"{len(buttons)} buttons ({len(disabled_buttons)} disabled)")
        
        # Forms
        forms = soup.find_all('form')
        if forms:
            forms_with_action = [f for f in forms if f.get('action')]
            forms_with_method = [f for f in forms if f.get('method')]
            self.log_test("ui_components", f"{page_name} - Forms", "PASS", 
                         f"{len(forms)} forms")
        
        # Loading indicators
        loading = soup.find_all(class_=re.compile('load|spin|progress', re.I))
        if loading:
            self.log_test("ui_components", f"{page_name} - Loading indicators", "PASS", 
                         f"{len(loading)} indicators")
        
        # Error containers
        errors = soup.find_all(class_=re.compile('error|alert|warning', re.I))
        if errors:
            self.log_test("ui_components", f"{page_name} - Error handling UI", "PASS", 
                         f"{len(errors)} error containers")
        
        # Modals/Dialogs
        modals = soup.find_all(class_=re.compile('modal|dialog', re.I))
        if modals:
            self.log_test("ui_components", f"{page_name} - Modals", "PASS", 
                         f"{len(modals)} modals")
    
    def test_responsiveness(self, soup: BeautifulSoup, page_name: str):
        """Test responsive design implementation"""
        print(f"  Testing responsiveness for {page_name}...")
        
        # Viewport meta tag
        viewport = soup.find('meta', {'name': 'viewport'})
        if viewport:
            content = viewport.get('content', '')
            if 'width=device-width' in content:
                self.log_test("responsiveness", f"{page_name} - Viewport meta", "PASS")
            else:
                self.log_test("responsiveness", f"{page_name} - Viewport meta", "WARNING", 
                             "Viewport meta incomplete")
        else:
            self.log_test("responsiveness", f"{page_name} - Viewport meta", "FAIL", 
                         "Missing viewport meta tag", "high")
        
        # Check for responsive classes (Bootstrap, Tailwind, etc.)
        responsive_classes = soup.find_all(class_=re.compile('col-|sm-|md-|lg-|xl-|mobile|tablet|desktop', re.I))
        if responsive_classes:
            self.log_test("responsiveness", f"{page_name} - Responsive classes", "PASS", 
                         f"{len(responsive_classes)} responsive elements")
        else:
            self.log_test("responsiveness", f"{page_name} - Responsive classes", "WARNING", 
                         "No responsive classes found")
        
        # Check for media queries in style tags
        style_tags = soup.find_all('style')
        media_queries_found = False
        for style in style_tags:
            if style.string and '@media' in style.string:
                media_queries_found = True
                break
        
        if media_queries_found:
            self.log_test("responsiveness", f"{page_name} - Media queries", "PASS", 
                         "Inline media queries found")
        
        # Check for flexible images
        images = soup.find_all('img')
        flexible_images = [img for img in images if 
                          img.get('class') and ('responsive' in str(img.get('class')) or 
                          'fluid' in str(img.get('class')))]
        if images and flexible_images:
            self.log_test("responsiveness", f"{page_name} - Flexible images", "PASS", 
                         f"{len(flexible_images)}/{len(images)} flexible")
    
    def test_performance(self, soup: BeautifulSoup, page_name: str):
        """Test frontend performance factors"""
        print(f"  Testing performance for {page_name}...")
        
        # Check external resources
        external_css = soup.find_all('link', {'rel': 'stylesheet'})
        external_js = soup.find_all('script', {'src': True})
        
        if len(external_css) <= 5:
            self.log_test("performance", f"{page_name} - CSS files", "PASS", 
                         f"{len(external_css)} files")
        else:
            self.log_test("performance", f"{page_name} - CSS files", "WARNING", 
                         f"Too many CSS files ({len(external_css)})")
        
        if len(external_js) <= 10:
            self.log_test("performance", f"{page_name} - JS files", "PASS", 
                         f"{len(external_js)} files")
        else:
            self.log_test("performance", f"{page_name} - JS files", "WARNING", 
                         f"Too many JS files ({len(external_js)})")
        
        # Check for inline styles/scripts
        inline_styles = soup.find_all(style=True)
        inline_scripts = soup.find_all('script', string=True)
        inline_scripts = [s for s in inline_scripts if s.string and len(s.string.strip()) > 100]
        
        if len(inline_styles) > 20:
            self.log_test("performance", f"{page_name} - Inline styles", "WARNING", 
                         f"{len(inline_styles)} inline styles")
        else:
            self.log_test("performance", f"{page_name} - Inline styles", "PASS")
        
        if len(inline_scripts) > 5:
            self.log_test("performance", f"{page_name} - Inline scripts", "WARNING", 
                         f"{len(inline_scripts)} large inline scripts")
        else:
            self.log_test("performance", f"{page_name} - Inline scripts", "PASS")
        
        # Check for lazy loading
        lazy_images = soup.find_all('img', {'loading': 'lazy'})
        total_images = len(soup.find_all('img'))
        if total_images > 5:
            if lazy_images:
                self.log_test("performance", f"{page_name} - Lazy loading", "PASS", 
                             f"{len(lazy_images)}/{total_images} images")
            else:
                self.log_test("performance", f"{page_name} - Lazy loading", "WARNING", 
                             "No lazy loading on images")
        
        # Check for async/defer on scripts
        async_scripts = soup.find_all('script', {'async': True})
        defer_scripts = soup.find_all('script', {'defer': True})
        if async_scripts or defer_scripts:
            self.log_test("performance", f"{page_name} - Script loading", "PASS", 
                         f"{len(async_scripts)} async, {len(defer_scripts)} defer")
        elif external_js:
            self.log_test("performance", f"{page_name} - Script loading", "WARNING", 
                         "No async/defer on scripts")
    
    def test_seo(self, soup: BeautifulSoup, page_name: str):
        """Test SEO implementation"""
        print(f"  Testing SEO for {page_name}...")
        
        # Meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            content = meta_desc.get('content', '')
            if len(content) > 160:
                self.log_test("seo", f"{page_name} - Meta description", "WARNING", 
                             f"Too long ({len(content)} chars)")
            elif len(content) < 50:
                self.log_test("seo", f"{page_name} - Meta description", "WARNING", 
                             f"Too short ({len(content)} chars)")
            else:
                self.log_test("seo", f"{page_name} - Meta description", "PASS")
        else:
            self.log_test("seo", f"{page_name} - Meta description", "WARNING", 
                         "Missing meta description")
        
        # Open Graph tags
        og_tags = soup.find_all('meta', property=re.compile('^og:'))
        if og_tags:
            og_required = ['og:title', 'og:description', 'og:image']
            og_present = [tag.get('property') for tag in og_tags]
            missing = [req for req in og_required if req not in og_present]
            if missing:
                self.log_test("seo", f"{page_name} - Open Graph", "WARNING", 
                             f"Missing: {', '.join(missing)}")
            else:
                self.log_test("seo", f"{page_name} - Open Graph", "PASS", 
                             f"{len(og_tags)} tags")
        else:
            self.log_test("seo", f"{page_name} - Open Graph", "WARNING", 
                         "No Open Graph tags")
        
        # Canonical URL
        canonical = soup.find('link', {'rel': 'canonical'})
        if canonical:
            self.log_test("seo", f"{page_name} - Canonical URL", "PASS")
        else:
            self.log_test("seo", f"{page_name} - Canonical URL", "WARNING", 
                         "No canonical URL")
        
        # Structured data (JSON-LD)
        json_ld = soup.find('script', {'type': 'application/ld+json'})
        if json_ld:
            self.log_test("seo", f"{page_name} - Structured data", "PASS")
        else:
            self.log_test("seo", f"{page_name} - Structured data", "INFO", 
                         "No structured data")
    
    def test_javascript_functionality(self, soup: BeautifulSoup, page_name: str):
        """Test JavaScript implementation"""
        print(f"  Testing JavaScript for {page_name}...")
        
        # Check for JavaScript files
        scripts = soup.find_all('script', {'src': True})
        script_sources = [s.get('src') for s in scripts]
        
        # Check for common libraries
        jquery_found = any('jquery' in src.lower() for src in script_sources)
        bootstrap_found = any('bootstrap' in src.lower() for src in script_sources)
        socketio_found = any('socket.io' in src.lower() for src in script_sources)
        
        if socketio_found:
            self.log_test("javascript", f"{page_name} - Socket.IO", "PASS")
        
        # Check for error handling in inline scripts
        inline_scripts = soup.find_all('script', string=True)
        error_handling_found = False
        for script in inline_scripts:
            if script.string and ('try' in script.string and 'catch' in script.string):
                error_handling_found = True
                break
        
        if error_handling_found:
            self.log_test("javascript", f"{page_name} - Error handling", "PASS")
        elif inline_scripts:
            self.log_test("javascript", f"{page_name} - Error handling", "WARNING", 
                         "No try-catch blocks found")
        
        # Check for console.log statements (should be removed in production)
        console_logs = 0
        for script in inline_scripts:
            if script.string and 'console.log' in script.string:
                console_logs += script.string.count('console.log')
        
        if console_logs > 5:
            self.log_test("javascript", f"{page_name} - Console logs", "WARNING", 
                         f"{console_logs} console.log statements")
        else:
            self.log_test("javascript", f"{page_name} - Console logs", "PASS")
    
    def test_specific_pages(self):
        """Test specific important pages"""
        pages_to_test = [
            ("/", "Homepage"),
            ("/dashboard/", "Dashboard"),
            ("/live", "Live Transcription"),
            ("/auth/login", "Login"),
            ("/auth/register", "Registration")
        ]
        
        for path, name in pages_to_test:
            print(f"\n📄 Testing {name} ({path})...")
            soup = self.fetch_page(path)
            if soup:
                self.test_accessibility(soup, name)
                self.test_ui_components(soup, name)
                self.test_responsiveness(soup, name)
                self.test_performance(soup, name)
                self.test_seo(soup, name)
                self.test_javascript_functionality(soup, name)
            else:
                self.log_test("ui_components", f"{name} page", "FAIL", 
                             "Could not fetch page", "critical")
    
    def test_live_transcription_page(self):
        """Special tests for live transcription page"""
        print("\n🎤 Special Testing: Live Transcription Page")
        
        soup = self.fetch_page("/live")
        if not soup:
            self.log_test("ui_components", "Live page accessibility", "FAIL", 
                         "Cannot access page", "critical")
            return
        
        # Check for critical components
        critical_components = {
            "statusChip": "Status indicator",
            "recordButton": "Record button",
            "transcriptDisplay": "Transcript area",
            "audioVisualizer": "Audio visualizer",
            "transcriptionCanvas": "Transcription canvas",
            "settingsPanel": "Settings panel"
        }
        
        for component_id, component_name in critical_components.items():
            element = soup.find(id=component_id) or \
                     soup.find(class_=component_id) or \
                     soup.find(attrs={"data-component": component_id})
            if element:
                self.log_test("ui_components", f"Live - {component_name}", "PASS")
            else:
                self.log_test("ui_components", f"Live - {component_name}", "WARNING", 
                             f"Component '{component_id}' not found")
        
        # Check for WebSocket setup
        scripts = soup.find_all('script', string=True)
        websocket_init = False
        audio_permission = False
        
        for script in scripts:
            if script.string:
                if 'socket.io' in script.string.lower() or 'websocket' in script.string.lower():
                    websocket_init = True
                if 'getUserMedia' in script.string or 'navigator.mediaDevices' in script.string:
                    audio_permission = True
        
        if websocket_init:
            self.log_test("ui_components", "Live - WebSocket initialization", "PASS")
        else:
            self.log_test("ui_components", "Live - WebSocket initialization", "FAIL", 
                         "No WebSocket setup found", "critical")
        
        if audio_permission:
            self.log_test("ui_components", "Live - Audio permissions", "PASS")
        else:
            self.log_test("ui_components", "Live - Audio permissions", "WARNING", 
                         "No audio permission handling")
    
    def generate_report(self):
        """Generate comprehensive audit report"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE FRONTEND UI/UX AUDIT REPORT")
        print("="*80)
        
        # Calculate metrics
        pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"\n📈 Overall Audit Summary:")
        print(f"  Total Tests: {self.total_tests}")
        print(f"  ✅ Passed: {self.passed_tests}")
        print(f"  ❌ Failed: {self.failed_tests}")
        print(f"  ⚠️ Warnings: {len(self.warnings)}")
        print(f"  🎯 Score: {pass_rate:.1f}%")
        
        # Category breakdown
        print(f"\n📋 Category Results:")
        for category, results in self.audit_results.items():
            if results:
                passed = len([r for r in results if r['status'] == 'PASS'])
                failed = len([r for r in results if r['status'] == 'FAIL'])
                other = len(results) - passed - failed
                
                category_name = category.replace('_', ' ').title()
                print(f"\n  {category_name}:")
                print(f"    ✅ Passed: {passed}")
                print(f"    ❌ Failed: {failed}")
                print(f"    ⚠️ Warnings: {other}")
        
        # Critical issues
        if self.critical_issues:
            print(f"\n🚨 CRITICAL UI/UX ISSUES ({len(self.critical_issues)}):")
            for issue in self.critical_issues[:10]:
                print(f"  • {issue}")
            if len(self.critical_issues) > 10:
                print(f"  ... and {len(self.critical_issues) - 10} more")
        
        # UI/UX Production readiness
        print("\n" + "="*80)
        print("🎯 UI/UX PRODUCTION READINESS")
        print("="*80)
        
        if self.critical_issues:
            print("\n❌ UI/UX NOT READY FOR PRODUCTION")
            print("Critical issues must be resolved:")
            for issue in self.critical_issues[:5]:
                print(f"  - {issue}")
        elif pass_rate < 70:
            print("\n⚠️ UI/UX NEEDS IMPROVEMENT")
            print(f"Score too low: {pass_rate:.1f}% (minimum 70% recommended)")
        elif pass_rate < 85:
            print("\n⚠️ UI/UX CONDITIONALLY READY")
            print(f"Good score ({pass_rate:.1f}%) but address warnings for best UX")
        else:
            print("\n✅ UI/UX READY FOR PRODUCTION")
            print(f"Excellent score: {pass_rate:.1f}%")
        
        # Specific recommendations
        print("\n📝 Top Recommendations:")
        
        accessibility_issues = len([i for i in self.critical_issues + self.warnings 
                                  if 'accessibility' in i.lower() or 'alt' in i.lower() or 'label' in i.lower()])
        if accessibility_issues > 0:
            print(f"  1. Fix {accessibility_issues} accessibility issues for WCAG compliance")
        
        performance_issues = len([w for w in self.warnings if 'performance' in w.lower() or 'lazy' in w.lower()])
        if performance_issues > 0:
            print(f"  2. Address {performance_issues} performance optimizations")
        
        responsive_issues = len([w for w in self.warnings if 'responsive' in w.lower() or 'viewport' in w.lower()])
        if responsive_issues > 0:
            print(f"  3. Improve responsive design ({responsive_issues} issues)")
        
        # Save detailed report
        report_file = f"frontend_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tests": self.total_tests,
                    "passed": self.passed_tests,
                    "failed": self.failed_tests,
                    "warnings": len(self.warnings),
                    "score": pass_rate
                },
                "critical_issues": self.critical_issues,
                "warnings": self.warnings,
                "audit_results": self.audit_results
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return pass_rate >= 70 and len(self.critical_issues) == 0
    
    def run_full_audit(self):
        """Execute comprehensive frontend audit"""
        print("🚀 Starting Comprehensive Frontend UI/UX Audit")
        print("="*80)
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Test all pages
        self.test_specific_pages()
        self.test_live_transcription_page()
        
        # Generate report
        return self.generate_report()

if __name__ == "__main__":
    auditor = ComprehensiveFrontendAudit()
    ui_ready = auditor.run_full_audit()
    
    # Exit with appropriate code
    import sys
    sys.exit(0 if ui_ready else 1)