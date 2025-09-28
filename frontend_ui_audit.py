#!/usr/bin/env python3
"""
Comprehensive Frontend UI/UX Audit for Mina Application
Tests UI components, accessibility, responsiveness, and user experience
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from typing import Dict, List, Any

class FrontendAudit:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.audit_results = {
            "ui_components": [],
            "accessibility": [],
            "responsiveness": [],
            "performance": [],
            "seo": [],
            "best_practices": []
        }
        self.issues_found = 0
        self.warnings_found = 0
        self.passed_checks = 0
        
    def log_finding(self, category: str, check: str, status: str, details: str = "", severity: str = "info"):
        """Log audit finding"""
        finding = {
            "timestamp": datetime.now().isoformat(),
            "check": check,
            "status": status,
            "details": details,
            "severity": severity
        }
        
        if category in self.audit_results:
            self.audit_results[category].append(finding)
            
        if status == "FAIL":
            self.issues_found += 1
            print(f"❌ [{category}] {check}: {details}")
        elif status == "WARNING":
            self.warnings_found += 1
            print(f"⚠️ [{category}] {check}: {details}")
        else:
            self.passed_checks += 1
            print(f"✅ [{category}] {check}")
            
    def audit_page(self, path: str, page_name: str):
        """Audit a specific page"""
        print(f"\n📄 Auditing {page_name} ({path})...")
        
        try:
            response = requests.get(f"{self.base_url}{path}", timeout=10)
            if response.status_code != 200:
                self.log_finding("ui_components", f"{page_name} accessibility", "FAIL", 
                               f"Page returned status {response.status_code}", "critical")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
            
        except Exception as e:
            self.log_finding("ui_components", f"{page_name} accessibility", "FAIL", 
                           str(e), "critical")
            return None
            
    def check_accessibility(self, soup: BeautifulSoup, page_name: str):
        """Check accessibility standards"""
        print(f"  🔍 Checking accessibility...")
        
        # Check for alt text on images
        images = soup.find_all('img')
        images_without_alt = [img for img in images if not img.get('alt')]
        if images_without_alt:
            self.log_finding("accessibility", f"{page_name} - Image alt text", "FAIL",
                           f"{len(images_without_alt)} images missing alt text", "high")
        elif images:
            self.log_finding("accessibility", f"{page_name} - Image alt text", "PASS")
            
        # Check for form labels
        forms = soup.find_all('form')
        for form in forms:
            inputs = form.find_all(['input', 'textarea', 'select'])
            for input_elem in inputs:
                input_id = input_elem.get('id')
                input_type = input_elem.get('type', 'text')
                
                if input_type not in ['submit', 'button', 'hidden']:
                    label = soup.find('label', {'for': input_id}) if input_id else None
                    if not label and not input_elem.get('aria-label'):
                        self.log_finding("accessibility", f"{page_name} - Form labels", "WARNING",
                                       f"Input missing label: {input_elem.get('name', 'unnamed')}")
                                       
        # Check for ARIA attributes
        aria_elements = soup.find_all(attrs={"role": True})
        if aria_elements:
            self.log_finding("accessibility", f"{page_name} - ARIA roles", "PASS",
                           f"{len(aria_elements)} elements with ARIA roles")
        else:
            self.log_finding("accessibility", f"{page_name} - ARIA roles", "WARNING",
                           "No ARIA roles found")
                           
        # Check for heading hierarchy
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        h1_count = len(soup.find_all('h1'))
        if h1_count == 0:
            self.log_finding("accessibility", f"{page_name} - Heading hierarchy", "WARNING",
                           "No H1 heading found")
        elif h1_count > 1:
            self.log_finding("accessibility", f"{page_name} - Heading hierarchy", "WARNING",
                           f"Multiple H1 headings found ({h1_count})")
        else:
            self.log_finding("accessibility", f"{page_name} - Heading hierarchy", "PASS")
            
        # Check for lang attribute
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            self.log_finding("accessibility", f"{page_name} - Language attribute", "PASS")
        else:
            self.log_finding("accessibility", f"{page_name} - Language attribute", "FAIL",
                           "Missing lang attribute on HTML tag", "high")
                           
    def check_ui_components(self, soup: BeautifulSoup, page_name: str):
        """Check UI components and structure"""
        print(f"  🎨 Checking UI components...")
        
        # Check for navigation
        nav = soup.find('nav') or soup.find(class_=re.compile('nav'))
        if nav:
            self.log_finding("ui_components", f"{page_name} - Navigation", "PASS")
        else:
            self.log_finding("ui_components", f"{page_name} - Navigation", "WARNING",
                           "No navigation element found")
                           
        # Check for buttons
        buttons = soup.find_all(['button', 'input[type="button"]', 'input[type="submit"]'])
        if buttons:
            self.log_finding("ui_components", f"{page_name} - Buttons", "PASS",
                           f"{len(buttons)} buttons found")
                           
        # Check for loading indicators
        loading_indicators = soup.find_all(class_=re.compile('load|spin|progress'))
        if loading_indicators:
            self.log_finding("ui_components", f"{page_name} - Loading indicators", "PASS")
        else:
            self.log_finding("ui_components", f"{page_name} - Loading indicators", "INFO",
                           "No loading indicators found")
                           
        # Check for error message containers
        error_containers = soup.find_all(class_=re.compile('error|alert|warning'))
        if error_containers:
            self.log_finding("ui_components", f"{page_name} - Error handling", "PASS")
            
        # Check for responsive meta tag
        viewport_meta = soup.find('meta', {'name': 'viewport'})
        if viewport_meta:
            self.log_finding("responsiveness", f"{page_name} - Viewport meta", "PASS")
        else:
            self.log_finding("responsiveness", f"{page_name} - Viewport meta", "FAIL",
                           "Missing viewport meta tag", "high")
                           
    def check_performance(self, soup: BeautifulSoup, page_name: str):
        """Check performance-related issues"""
        print(f"  ⚡ Checking performance...")
        
        # Check for inline styles
        inline_styles = soup.find_all(style=True)
        if len(inline_styles) > 10:
            self.log_finding("performance", f"{page_name} - Inline styles", "WARNING",
                           f"{len(inline_styles)} inline styles found - consider external CSS")
                           
        # Check for inline scripts
        inline_scripts = soup.find_all('script', string=True)
        inline_scripts = [s for s in inline_scripts if s.string and len(s.string.strip()) > 0]
        if len(inline_scripts) > 3:
            self.log_finding("performance", f"{page_name} - Inline scripts", "WARNING",
                           f"{len(inline_scripts)} inline scripts - consider external JS")
                           
        # Check for external resources
        external_css = soup.find_all('link', {'rel': 'stylesheet'})
        external_js = soup.find_all('script', {'src': True})
        
        self.log_finding("performance", f"{page_name} - External resources", "INFO",
                       f"{len(external_css)} CSS files, {len(external_js)} JS files")
                       
        # Check for lazy loading
        lazy_images = soup.find_all('img', {'loading': 'lazy'})
        total_images = len(soup.find_all('img'))
        if total_images > 5 and len(lazy_images) == 0:
            self.log_finding("performance", f"{page_name} - Lazy loading", "WARNING",
                           "No lazy loading on images")
                           
    def check_seo(self, soup: BeautifulSoup, page_name: str):
        """Check SEO best practices"""
        print(f"  🔍 Checking SEO...")
        
        # Check for title tag
        title = soup.find('title')
        if title and title.string:
            if len(title.string) > 60:
                self.log_finding("seo", f"{page_name} - Title tag", "WARNING",
                               f"Title too long ({len(title.string)} chars)")
            else:
                self.log_finding("seo", f"{page_name} - Title tag", "PASS")
        else:
            self.log_finding("seo", f"{page_name} - Title tag", "FAIL",
                           "Missing title tag", "high")
                           
        # Check for meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            content = meta_desc.get('content', '')
            if len(content) > 160:
                self.log_finding("seo", f"{page_name} - Meta description", "WARNING",
                               f"Description too long ({len(content)} chars)")
            else:
                self.log_finding("seo", f"{page_name} - Meta description", "PASS")
        else:
            self.log_finding("seo", f"{page_name} - Meta description", "WARNING",
                           "Missing meta description")
                           
        # Check for Open Graph tags
        og_tags = soup.find_all('meta', property=re.compile('^og:'))
        if og_tags:
            self.log_finding("seo", f"{page_name} - Open Graph tags", "PASS",
                           f"{len(og_tags)} OG tags found")
                           
    def audit_live_transcription(self):
        """Special audit for live transcription page"""
        print("\n🎤 Special Audit: Live Transcription Page")
        
        soup = self.audit_page("/live", "Live Transcription")
        if not soup:
            return
            
        # Check for required components
        required_components = {
            "statusChip": "Status indicator",
            "recordButton": "Record button",
            "transcriptDisplay": "Transcript display area",
            "audioVisualizer": "Audio visualizer"
        }
        
        for component_id, component_name in required_components.items():
            element = soup.find(id=component_id) or soup.find(class_=component_id)
            if element:
                self.log_finding("ui_components", f"Live - {component_name}", "PASS")
            else:
                self.log_finding("ui_components", f"Live - {component_name}", "WARNING",
                               f"Component '{component_id}' not found")
                               
        # Check for WebSocket initialization
        scripts = soup.find_all('script')
        websocket_found = False
        for script in scripts:
            if script.string and ('socket.io' in script.string.lower() or 'websocket' in script.string.lower()):
                websocket_found = True
                break
                
        if websocket_found:
            self.log_finding("ui_components", "Live - WebSocket setup", "PASS")
        else:
            self.log_finding("ui_components", "Live - WebSocket setup", "WARNING",
                           "No WebSocket initialization found")
                           
        # Check for audio permissions handling
        if any('getUserMedia' in str(script.string) for script in scripts if script.string):
            self.log_finding("ui_components", "Live - Audio permissions", "PASS")
        else:
            self.log_finding("ui_components", "Live - Audio permissions", "WARNING",
                           "No audio permission handling found")
                           
    def audit_dashboard(self):
        """Audit dashboard page"""
        soup = self.audit_page("/dashboard/", "Dashboard")
        if soup:
            self.check_accessibility(soup, "Dashboard")
            self.check_ui_components(soup, "Dashboard")
            self.check_performance(soup, "Dashboard")
            
    def audit_landing_page(self):
        """Audit landing/marketing page"""
        soup = self.audit_page("/", "Landing Page")
        if soup:
            self.check_accessibility(soup, "Landing")
            self.check_ui_components(soup, "Landing")
            self.check_performance(soup, "Landing")
            self.check_seo(soup, "Landing")
            
    def generate_report(self):
        """Generate comprehensive audit report"""
        print("\n" + "="*60)
        print("📊 FRONTEND UI/UX AUDIT REPORT")
        print("="*60)
        
        total_checks = self.issues_found + self.warnings_found + self.passed_checks
        
        print(f"\n📈 Audit Summary:")
        print(f"  Total Checks: {total_checks}")
        print(f"  ✅ Passed: {self.passed_checks}")
        print(f"  ⚠️ Warnings: {self.warnings_found}")
        print(f"  ❌ Issues: {self.issues_found}")
        
        if total_checks > 0:
            score = ((self.passed_checks / total_checks) * 100)
            print(f"  UI/UX Score: {score:.1f}%")
            
        # Category summaries
        for category, findings in self.audit_results.items():
            if findings:
                issues = len([f for f in findings if f['status'] == 'FAIL'])
                warnings = len([f for f in findings if f['status'] == 'WARNING'])
                passed = len([f for f in findings if f['status'] == 'PASS'])
                
                print(f"\n📋 {category.replace('_', ' ').title()}:")
                print(f"  ✅ Passed: {passed}")
                print(f"  ⚠️ Warnings: {warnings}")
                print(f"  ❌ Issues: {issues}")
                
        # Production readiness for UI
        print("\n🎯 UI/UX PRODUCTION READINESS:")
        
        if self.issues_found > 5:
            print("  ❌ NOT READY - Critical UI/UX issues found")
            print("  • Fix accessibility violations")
            print("  • Address missing UI components")
        elif self.warnings_found > 10:
            print("  ⚠️ NEEDS IMPROVEMENT")
            print("  • Address accessibility warnings")
            print("  • Optimize performance issues")
        else:
            print("  ✅ UI/UX READY FOR PRODUCTION")
            
        # Save detailed report
        report_file = f"frontend_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_checks": total_checks,
                    "passed": self.passed_checks,
                    "warnings": self.warnings_found,
                    "issues": self.issues_found
                },
                "findings": self.audit_results
            }, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")
        
    def run_full_audit(self):
        """Run complete frontend audit"""
        print("\n🚀 Starting Comprehensive Frontend UI/UX Audit")
        print("="*60)
        
        # Audit main pages
        self.audit_landing_page()
        self.audit_dashboard()
        self.audit_live_transcription()
        
        # Generate report
        self.generate_report()

if __name__ == "__main__":
    auditor = FrontendAudit()
    auditor.run_full_audit()