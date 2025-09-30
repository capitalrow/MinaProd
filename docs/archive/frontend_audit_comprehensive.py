#!/usr/bin/env python3
"""
🔍 Comprehensive Frontend Audit for Mina Live Transcription
Analyzes UI/UX, accessibility, responsiveness, and error handling.
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import re

@dataclass
class AccessibilityIssue:
    """Accessibility issue found in the UI."""
    level: str  # 'error', 'warning', 'info'
    guideline: str  # WCAG guideline reference
    element: str
    description: str
    fix_suggestion: str

@dataclass
class UIFlowIssue:
    """UI flow or interaction issue."""
    category: str  # 'error_handling', 'state_management', 'user_feedback'
    severity: str  # 'critical', 'major', 'minor'
    issue: str
    impact: str
    fix_suggestion: str

@dataclass
class ResponsiveIssue:
    """Responsive design issue."""
    breakpoint: str  # 'mobile', 'tablet', 'desktop'
    element: str
    issue: str
    fix_suggestion: str

class FrontendAuditor:
    """Comprehensive frontend auditor."""
    
    def __init__(self):
        self.accessibility_issues: List[AccessibilityIssue] = []
        self.ui_flow_issues: List[UIFlowIssue] = []
        self.responsive_issues: List[ResponsiveIssue] = []
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def audit_html_template(self, html_content: str, template_name: str) -> Dict[str, Any]:
        """Audit HTML template for accessibility and structure issues."""
        
        self.logger.info(f"🔍 Auditing template: {template_name}")
        
        # Check for basic accessibility requirements
        self._check_aria_labels(html_content)
        self._check_semantic_structure(html_content)
        self._check_form_accessibility(html_content)
        self._check_color_contrast_indicators(html_content)
        self._check_keyboard_navigation(html_content)
        
        # Check UI flow and error handling
        self._check_error_handling_ui(html_content)
        self._check_loading_states(html_content)
        self._check_user_feedback_mechanisms(html_content)
        
        # Check responsive design indicators
        self._check_responsive_design(html_content)
        
        return {
            'template': template_name,
            'accessibility_issues': [asdict(issue) for issue in self.accessibility_issues],
            'ui_flow_issues': [asdict(issue) for issue in self.ui_flow_issues],
            'responsive_issues': [asdict(issue) for issue in self.responsive_issues],
            'summary': self._generate_summary()
        }
    
    def audit_javascript(self, js_content: str, file_name: str) -> Dict[str, Any]:
        """Audit JavaScript for error handling and UX patterns."""
        
        self.logger.info(f"🔍 Auditing JavaScript: {file_name}")
        
        # Check error handling patterns
        self._check_js_error_handling(js_content)
        self._check_websocket_resilience(js_content)
        self._check_user_feedback_js(js_content)
        self._check_accessibility_js(js_content)
        
        return {
            'file': file_name,
            'ui_flow_issues': [asdict(issue) for issue in self.ui_flow_issues],
            'summary': self._generate_summary()
        }
    
    def _check_aria_labels(self, html: str):
        """Check for proper ARIA labels and accessibility attributes."""
        
        # Check for buttons without aria-label or descriptive text
        button_pattern = r'<button[^>]*>([^<]*)</button>'
        buttons = re.findall(button_pattern, html, re.IGNORECASE)
        
        for button_text in buttons:
            if not button_text.strip():
                self.accessibility_issues.append(AccessibilityIssue(
                    level='error',
                    guideline='WCAG 2.1 AA - 4.1.2 Name, Role, Value',
                    element='button',
                    description='Button without descriptive text or aria-label',
                    fix_suggestion='Add descriptive text inside button or aria-label attribute'
                ))
        
        # Check for missing aria-live regions for dynamic content
        if 'interim' in html.lower() or 'transcript' in html.lower():
            if 'aria-live' not in html:
                self.accessibility_issues.append(AccessibilityIssue(
                    level='error',
                    guideline='WCAG 2.1 AA - 4.1.3 Status Messages',
                    element='transcription area',
                    description='Dynamic transcription content missing aria-live attribute',
                    fix_suggestion='Add aria-live="polite" to transcription containers'
                ))
        
        # Check for form inputs without labels
        input_pattern = r'<input[^>]*>'
        inputs = re.findall(input_pattern, html, re.IGNORECASE)
        
        for input_tag in inputs:
            if 'aria-label' not in input_tag and 'id=' not in input_tag:
                self.accessibility_issues.append(AccessibilityIssue(
                    level='warning',
                    guideline='WCAG 2.1 AA - 3.3.2 Labels or Instructions',
                    element='input',
                    description='Input field without proper labeling',
                    fix_suggestion='Add aria-label or associate with label element'
                ))
    
    def _check_semantic_structure(self, html: str):
        """Check for proper semantic HTML structure."""
        
        # Check for heading hierarchy
        h1_count = len(re.findall(r'<h1[^>]*>', html, re.IGNORECASE))
        if h1_count == 0:
            self.accessibility_issues.append(AccessibilityIssue(
                level='warning',
                guideline='WCAG 2.1 AA - 1.3.1 Info and Relationships',
                element='page structure',
                description='Page missing main heading (h1)',
                fix_suggestion='Add an h1 element for the main page title'
            ))
        elif h1_count > 1:
            self.accessibility_issues.append(AccessibilityIssue(
                level='warning',
                guideline='WCAG 2.1 AA - 1.3.1 Info and Relationships',
                element='page structure',
                description='Multiple h1 elements found',
                fix_suggestion='Use only one h1 per page, use h2-h6 for subsections'
            ))
        
        # Check for main landmark
        if '<main' not in html and 'role="main"' not in html:
            self.accessibility_issues.append(AccessibilityIssue(
                level='warning',
                guideline='WCAG 2.1 AA - 1.3.1 Info and Relationships',
                element='page structure',
                description='Page missing main landmark',
                fix_suggestion='Wrap main content in <main> element or add role="main"'
            ))
    
    def _check_form_accessibility(self, html: str):
        """Check form accessibility features."""
        
        # Check for fieldsets in complex forms
        if html.count('<input') > 3 and '<fieldset' not in html:
            self.accessibility_issues.append(AccessibilityIssue(
                level='info',
                guideline='WCAG 2.1 AA - 1.3.1 Info and Relationships',
                element='form',
                description='Complex form without fieldset grouping',
                fix_suggestion='Consider grouping related form controls with fieldset and legend'
            ))
        
        # Check for required field indicators
        if 'required' in html and 'aria-required' not in html:
            self.accessibility_issues.append(AccessibilityIssue(
                level='warning',
                guideline='WCAG 2.1 AA - 3.3.2 Labels or Instructions',
                element='form',
                description='Required fields not properly indicated to screen readers',
                fix_suggestion='Add aria-required="true" to required form fields'
            ))
    
    def _check_color_contrast_indicators(self, html: str):
        """Check for color contrast issues in CSS classes."""
        
        # Look for potential low contrast combinations in class names
        low_contrast_patterns = [
            'text-muted', 'text-secondary', 'text-light'
        ]
        
        for pattern in low_contrast_patterns:
            if pattern in html:
                self.accessibility_issues.append(AccessibilityIssue(
                    level='warning',
                    guideline='WCAG 2.1 AA - 1.4.3 Contrast (Minimum)',
                    element=f'element with {pattern}',
                    description='Potentially low contrast text detected',
                    fix_suggestion='Verify contrast ratio meets 4.5:1 minimum for normal text'
                ))
    
    def _check_keyboard_navigation(self, html: str):
        """Check for keyboard navigation support."""
        
        # Check for skip links
        if 'skip-link' not in html and 'skip to content' not in html.lower():
            self.accessibility_issues.append(AccessibilityIssue(
                level='info',
                guideline='WCAG 2.1 AA - 2.4.1 Bypass Blocks',
                element='page navigation',
                description='No skip link found',
                fix_suggestion='Add skip link to main content for keyboard users'
            ))
        
        # Check for tabindex usage
        tabindex_pattern = r'tabindex=[\'"]-?(\d+)[\'"]'
        tabindexes = re.findall(tabindex_pattern, html)
        
        for tabindex in tabindexes:
            if int(tabindex) > 0:
                self.accessibility_issues.append(AccessibilityIssue(
                    level='warning',
                    guideline='WCAG 2.1 AA - 2.4.3 Focus Order',
                    element=f'element with tabindex={tabindex}',
                    description='Positive tabindex can disrupt natural focus order',
                    fix_suggestion='Use tabindex="0" or "-1", avoid positive values'
                ))
    
    def _check_error_handling_ui(self, html: str):
        """Check for error handling UI patterns."""
        
        # Check for error message containers
        if 'error' in html.lower():
            if 'role="alert"' not in html and 'aria-live="assertive"' not in html:
                self.ui_flow_issues.append(UIFlowIssue(
                    category='error_handling',
                    severity='major',
                    issue='Error messages not announced to screen readers',
                    impact='Screen reader users may miss critical error information',
                    fix_suggestion='Add role="alert" or aria-live="assertive" to error containers'
                ))
        
        # Check for loading states
        if 'record' in html.lower() or 'transcript' in html.lower():
            if 'loading' not in html.lower() and 'spinner' not in html.lower():
                self.ui_flow_issues.append(UIFlowIssue(
                    category='user_feedback',
                    severity='minor',
                    issue='No visible loading states for async operations',
                    impact='Users unsure if actions are processing',
                    fix_suggestion='Add loading indicators for async operations'
                ))
    
    def _check_loading_states(self, html: str):
        """Check for proper loading state handling."""
        
        # Look for loading indicators
        loading_indicators = ['spinner', 'loading', 'progress', 'skeleton']
        has_loading = any(indicator in html.lower() for indicator in loading_indicators)
        
        if not has_loading and ('record' in html.lower() or 'process' in html.lower()):
            self.ui_flow_issues.append(UIFlowIssue(
                category='user_feedback',
                severity='minor',
                issue='Missing loading indicators for long-running operations',
                impact='Users may think interface is unresponsive',
                fix_suggestion='Add spinners or progress indicators for operations >200ms'
            ))
    
    def _check_user_feedback_mechanisms(self, html: str):
        """Check for user feedback and notification systems."""
        
        # Check for toast/notification system
        notification_elements = ['toast', 'alert', 'notification', 'message']
        has_notifications = any(element in html.lower() for element in notification_elements)
        
        if not has_notifications:
            self.ui_flow_issues.append(UIFlowIssue(
                category='user_feedback',
                severity='major',
                issue='No notification system for user feedback',
                impact='Users may miss important status updates or errors',
                fix_suggestion='Implement toast notifications or alert system'
            ))
    
    def _check_responsive_design(self, html: str):
        """Check for responsive design indicators."""
        
        # Check for viewport meta tag
        if 'viewport' not in html:
            self.responsive_issues.append(ResponsiveIssue(
                breakpoint='mobile',
                element='meta viewport',
                issue='Missing viewport meta tag',
                fix_suggestion='Add <meta name="viewport" content="width=device-width, initial-scale=1">'
            ))
        
        # Check for responsive grid classes
        responsive_classes = ['col-sm', 'col-md', 'col-lg', 'col-xl']
        has_responsive_grid = any(cls in html for cls in responsive_classes)
        
        if 'col-' in html and not has_responsive_grid:
            self.responsive_issues.append(ResponsiveIssue(
                breakpoint='all',
                element='grid system',
                issue='Using grid without responsive breakpoints',
                fix_suggestion='Add responsive classes (col-sm-, col-md-, etc.) for different screen sizes'
            ))
    
    def _check_js_error_handling(self, js: str):
        """Check JavaScript error handling patterns."""
        
        # Check for try-catch blocks
        try_catch_count = js.count('try {')
        function_count = js.count('function ') + js.count('=>')
        
        if function_count > 5 and try_catch_count == 0:
            self.ui_flow_issues.append(UIFlowIssue(
                category='error_handling',
                severity='major',
                issue='No try-catch error handling found',
                impact='Unhandled errors may break the user experience',
                fix_suggestion='Add try-catch blocks around async operations and API calls'
            ))
        
        # Check for console.error usage
        if 'console.error' not in js and 'console.warn' not in js:
            self.ui_flow_issues.append(UIFlowIssue(
                category='error_handling',
                severity='minor',
                issue='No error logging found',
                impact='Difficult to debug issues in production',
                fix_suggestion='Add console.error() for debugging and monitoring'
            ))
    
    def _check_websocket_resilience(self, js: str):
        """Check WebSocket connection resilience."""
        
        if 'socket' in js.lower() or 'websocket' in js.lower():
            # Check for reconnection logic
            if 'reconnect' not in js.lower():
                self.ui_flow_issues.append(UIFlowIssue(
                    category='error_handling',
                    severity='critical',
                    issue='WebSocket connection without reconnection logic',
                    impact='Users lose connection permanently if WebSocket disconnects',
                    fix_suggestion='Implement automatic reconnection with exponential backoff'
                ))
            
            # Check for connection state handling
            if 'disconnect' not in js.lower():
                self.ui_flow_issues.append(UIFlowIssue(
                    category='state_management',
                    severity='major',
                    issue='No WebSocket disconnection handling',
                    impact='Users not notified when connection is lost',
                    fix_suggestion='Add disconnect event handlers and user notifications'
                ))
    
    def _check_user_feedback_js(self, js: str):
        """Check for user feedback in JavaScript."""
        
        # Check for user notifications
        notification_patterns = ['alert(', 'toast', 'notification', 'showError', 'showSuccess']
        has_notifications = any(pattern in js for pattern in notification_patterns)
        
        if not has_notifications and 'error' in js.lower():
            self.ui_flow_issues.append(UIFlowIssue(
                category='user_feedback',
                severity='major',
                issue='Error handling without user notification',
                impact='Users not informed when errors occur',
                fix_suggestion='Add user-friendly error messages and notifications'
            ))
    
    def _check_accessibility_js(self, js: str):
        """Check JavaScript accessibility considerations."""
        
        # Check for focus management
        if 'focus()' not in js and ('modal' in js.lower() or 'popup' in js.lower()):
            self.accessibility_issues.append(AccessibilityIssue(
                level='warning',
                guideline='WCAG 2.1 AA - 2.4.3 Focus Order',
                element='modal/popup',
                description='Modal or popup without focus management',
                fix_suggestion='Set focus to modal content when opened, return focus when closed'
            ))
        
        # Check for keyboard event handling
        if 'addEventListener' in js and 'keydown' not in js and 'keyup' not in js:
            self.accessibility_issues.append(AccessibilityIssue(
                level='info',
                guideline='WCAG 2.1 AA - 2.1.1 Keyboard',
                element='interactive elements',
                description='Event listeners without keyboard support',
                fix_suggestion='Add keyboard event handlers for interactive elements'
            ))
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate audit summary."""
        
        accessibility_by_level = {'error': 0, 'warning': 0, 'info': 0}
        for issue in self.accessibility_issues:
            accessibility_by_level[issue.level] += 1
        
        ui_flow_by_severity = {'critical': 0, 'major': 0, 'minor': 0}
        for issue in self.ui_flow_issues:
            ui_flow_by_severity[issue.severity] += 1
        
        responsive_by_breakpoint = {'mobile': 0, 'tablet': 0, 'desktop': 0, 'all': 0}
        for issue in self.responsive_issues:
            responsive_by_breakpoint[issue.breakpoint] += 1
        
        return {
            'total_issues': len(self.accessibility_issues) + len(self.ui_flow_issues) + len(self.responsive_issues),
            'accessibility': {
                'total': len(self.accessibility_issues),
                'by_level': accessibility_by_level
            },
            'ui_flow': {
                'total': len(self.ui_flow_issues),
                'by_severity': ui_flow_by_severity
            },
            'responsive': {
                'total': len(self.responsive_issues),
                'by_breakpoint': responsive_by_breakpoint
            }
        }
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report."""
        
        return {
            'timestamp': time.time(),
            'audit_summary': self._generate_summary(),
            'accessibility_issues': [asdict(issue) for issue in self.accessibility_issues],
            'ui_flow_issues': [asdict(issue) for issue in self.ui_flow_issues],
            'responsive_issues': [asdict(issue) for issue in self.responsive_issues],
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate prioritized recommendations."""
        
        recommendations = []
        
        # Critical issues first
        critical_ui = [issue for issue in self.ui_flow_issues if issue.severity == 'critical']
        if critical_ui:
            recommendations.append("🚨 CRITICAL: Fix WebSocket resilience and connection handling")
        
        # Accessibility errors
        accessibility_errors = [issue for issue in self.accessibility_issues if issue.level == 'error']
        if accessibility_errors:
            recommendations.append("🚨 ACCESSIBILITY: Fix missing ARIA labels and live regions")
        
        # Major UI issues
        major_ui = [issue for issue in self.ui_flow_issues if issue.severity == 'major']
        if major_ui:
            recommendations.append("⚠️ UX: Improve error handling and user feedback")
        
        # Responsive issues
        if self.responsive_issues:
            recommendations.append("📱 RESPONSIVE: Fix mobile and tablet layout issues")
        
        # Minor improvements
        minor_issues = len([issue for issue in self.ui_flow_issues if issue.severity == 'minor'])
        if minor_issues > 0:
            recommendations.append(f"ℹ️ POLISH: Address {minor_issues} minor UX improvements")
        
        return recommendations

def audit_live_transcription_frontend(html_file: str, js_file: str) -> Dict[str, Any]:
    """Comprehensive audit of live transcription frontend."""
    
    auditor = FrontendAuditor()
    
    # Read files
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        html_content = ""
    
    try:
        with open(js_file, 'r', encoding='utf-8') as f:
            js_content = f.read()
    except FileNotFoundError:
        js_content = ""
    
    # Perform audits
    html_audit = auditor.audit_html_template(html_content, html_file)
    js_audit = auditor.audit_javascript(js_content, js_file)
    
    # Generate comprehensive report
    comprehensive_report = auditor.generate_comprehensive_report()
    
    return {
        'html_audit': html_audit,
        'js_audit': js_audit,
        'comprehensive_report': comprehensive_report
    }

if __name__ == '__main__':
    # Demo mode
    print("🔍 Frontend Audit Demo")
    
    # Test with sample HTML
    sample_html = '''
    <div class="container">
        <h1>Live Transcription</h1>
        <button>Start Recording</button>
        <div id="transcript"></div>
    </div>
    '''
    
    auditor = FrontendAuditor()
    result = auditor.audit_html_template(sample_html, "demo.html")
    print(json.dumps(result, indent=2))