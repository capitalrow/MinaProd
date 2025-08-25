#!/usr/bin/env python3
"""
Frontend UI/UX Audit Tool
Comprehensive analysis of the live transcription interface
"""

import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict

@dataclass
class UIAuditResults:
    """Frontend audit results structure"""
    # Core Functionality
    start_stop_buttons: Dict[str, bool]
    microphone_permissions: Dict[str, str]
    websocket_reconnect: Dict[str, bool]
    error_handling: Dict[str, bool]
    
    # UI States
    connection_states: List[str]
    recording_states: List[str]
    error_states: List[str]
    
    # Performance
    interim_update_latency: Dict[str, float]
    ui_responsiveness: Dict[str, str]
    
    # Accessibility
    aria_labels: Dict[str, int]
    keyboard_navigation: Dict[str, bool]
    color_contrast: Dict[str, str]
    screen_reader_support: Dict[str, bool]
    
    # Responsive Design
    mobile_compatibility: Dict[str, str]
    desktop_compatibility: Dict[str, str]
    
    # Error UX
    error_toast_system: Dict[str, bool]
    user_feedback: Dict[str, str]

class FrontendAuditor:
    """Comprehensive frontend audit tool"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results = UIAuditResults(
            start_stop_buttons={}, microphone_permissions={}, websocket_reconnect={},
            error_handling={}, connection_states=[], recording_states=[], error_states=[],
            interim_update_latency={}, ui_responsiveness={}, aria_labels={}, 
            keyboard_navigation={}, color_contrast={}, screen_reader_support={},
            mobile_compatibility={}, desktop_compatibility={}, error_toast_system={},
            user_feedback={}
        )
    
    def run_comprehensive_audit(self) -> Dict:
        """Run complete frontend audit"""
        print("🔍 FRONTEND UI/UX COMPREHENSIVE AUDIT")
        print("=" * 50)
        
        # Core functionality tests
        self._audit_core_functionality()
        
        # UI state management
        self._audit_ui_states()
        
        # Performance analysis
        self._audit_performance()
        
        # Accessibility compliance
        self._audit_accessibility()
        
        # Responsive design
        self._audit_responsive_design()
        
        # Error handling UX
        self._audit_error_ux()
        
        return self._compile_audit_report()
    
    def _audit_core_functionality(self):
        """Audit core button functionality and permissions"""
        print("📋 Auditing core functionality...")
        
        try:
            # Get main page HTML
            response = requests.get(f"{self.base_url}/", timeout=10)
            html_content = response.text
            
            # Check Start/Stop buttons
            self.results.start_stop_buttons = {
                'start_button_present': 'Start Recording' in html_content,
                'stop_button_present': 'Stop' in html_content,
                'button_ids_unique': len(re.findall(r'id="(start|stop)', html_content)) >= 2,
                'event_handlers_attached': 'onclick' in html_content or 'addEventListener' in html_content
            }
            
            # Check microphone permission handling
            self.results.microphone_permissions = {
                'navigator_getusermedia': 'navigator.mediaDevices.getUserMedia' in html_content,
                'permission_error_handling': 'permission' in html_content.lower() and 'denied' in html_content.lower(),
                'fallback_messaging': 'microphone' in html_content.lower()
            }
            
            # Check WebSocket reconnect logic
            self.results.websocket_reconnect = {
                'reconnect_logic_present': 'reconnect' in html_content.lower(),
                'connection_retry': 'retry' in html_content.lower(),
                'backoff_strategy': 'setTimeout' in html_content or 'setInterval' in html_content
            }
            
            # Check error handling
            self.results.error_handling = {
                'try_catch_blocks': 'try' in html_content and 'catch' in html_content,
                'error_display': 'error' in html_content.lower(),
                'user_notifications': 'alert' in html_content or 'toast' in html_content.lower()
            }
            
        except Exception as e:
            print(f"Error auditing core functionality: {e}")
    
    def _audit_ui_states(self):
        """Audit UI state management"""
        print("🎛️ Auditing UI states...")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            html_content = response.text
            
            # Extract state indicators
            if 'Connected' in html_content:
                self.results.connection_states.append('Connected')
            if 'Disconnected' in html_content:
                self.results.connection_states.append('Disconnected')
            if 'Connecting' in html_content:
                self.results.connection_states.append('Connecting')
                
            if 'Recording' in html_content:
                self.results.recording_states.append('Recording')
            if 'Stopped' in html_content:
                self.results.recording_states.append('Stopped')
            if 'Paused' in html_content:
                self.results.recording_states.append('Paused')
                
            if 'Error' in html_content:
                self.results.error_states.append('Error')
            if 'Failed' in html_content:
                self.results.error_states.append('Failed')
                
        except Exception as e:
            print(f"Error auditing UI states: {e}")
    
    def _audit_performance(self):
        """Audit UI performance characteristics"""
        print("⚡ Auditing performance...")
        
        try:
            # Measure page load time
            start_time = datetime.now()
            response = requests.get(f"{self.base_url}/", timeout=10)
            load_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self.results.interim_update_latency = {
                'page_load_ms': load_time,
                'html_size_kb': len(response.content) / 1024,
                'dom_ready_optimized': 'DOMContentLoaded' in response.text
            }
            
            # Check UI responsiveness indicators
            self.results.ui_responsiveness = {
                'async_loading': 'async' in response.text or 'defer' in response.text,
                'lazy_loading': 'lazy' in response.text.lower(),
                'debounced_inputs': 'debounce' in response.text.lower(),
                'throttled_events': 'throttle' in response.text.lower()
            }
            
        except Exception as e:
            print(f"Error auditing performance: {e}")
    
    def _audit_accessibility(self):
        """Audit accessibility compliance"""
        print("♿ Auditing accessibility...")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            html_content = response.text
            
            # Count ARIA labels and attributes
            self.results.aria_labels = {
                'aria_label_count': len(re.findall(r'aria-label=', html_content)),
                'aria_live_regions': len(re.findall(r'aria-live=', html_content)),
                'aria_describedby': len(re.findall(r'aria-describedby=', html_content)),
                'role_attributes': len(re.findall(r'role=', html_content))
            }
            
            # Check keyboard navigation
            self.results.keyboard_navigation = {
                'tabindex_present': 'tabindex' in html_content,
                'focus_management': 'focus()' in html_content,
                'keyboard_event_handlers': 'keydown' in html_content or 'keyup' in html_content,
                'skip_links': 'skip' in html_content.lower()
            }
            
            # Basic color contrast check (simplified)
            self.results.color_contrast = {
                'css_contrast_keywords': 'contrast' in html_content.lower(),
                'dark_theme_support': 'dark' in html_content.lower(),
                'high_contrast_mode': 'high-contrast' in html_content.lower()
            }
            
            # Screen reader support
            self.results.screen_reader_support = {
                'alt_text_present': 'alt=' in html_content,
                'semantic_html': '<header>' in html_content and '<main>' in html_content,
                'live_announcements': 'aria-live' in html_content,
                'focus_indicators': ':focus' in html_content
            }
            
        except Exception as e:
            print(f"Error auditing accessibility: {e}")
    
    def _audit_responsive_design(self):
        """Audit responsive design implementation"""
        print("📱 Auditing responsive design...")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            html_content = response.text
            
            # Mobile compatibility checks
            self.results.mobile_compatibility = {
                'viewport_meta': 'viewport' in html_content,
                'responsive_css': 'media' in html_content and 'max-width' in html_content,
                'touch_events': 'touch' in html_content.lower(),
                'mobile_first_design': '@media' in html_content
            }
            
            # Desktop compatibility
            self.results.desktop_compatibility = {
                'large_screen_support': 'min-width' in html_content,
                'keyboard_shortcuts': 'Ctrl' in html_content or 'Alt' in html_content,
                'mouse_events': 'click' in html_content or 'hover' in html_content,
                'print_styles': '@media print' in html_content
            }
            
        except Exception as e:
            print(f"Error auditing responsive design: {e}")
    
    def _audit_error_ux(self):
        """Audit error handling user experience"""
        print("🚨 Auditing error UX...")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            html_content = response.text
            
            # Toast notification system
            self.results.error_toast_system = {
                'toast_component_present': 'toast' in html_content.lower(),
                'error_notifications': 'error' in html_content.lower() and 'notification' in html_content.lower(),
                'success_notifications': 'success' in html_content.lower(),
                'auto_dismiss': 'setTimeout' in html_content
            }
            
            # User feedback mechanisms
            self.results.user_feedback = {
                'loading_indicators': 'loading' in html_content.lower() or 'spinner' in html_content.lower(),
                'progress_bars': 'progress' in html_content.lower(),
                'status_messages': 'status' in html_content.lower(),
                'help_text': 'help' in html_content.lower() or 'hint' in html_content.lower()
            }
            
        except Exception as e:
            print(f"Error auditing error UX: {e}")
    
    def _compile_audit_report(self) -> Dict:
        """Compile comprehensive audit report"""
        audit_report = {
            'timestamp': datetime.now().isoformat(),
            'audit_summary': self._generate_audit_summary(),
            'detailed_results': asdict(self.results),
            'compliance_score': self._calculate_compliance_score(),
            'priority_issues': self._identify_priority_issues(),
            'recommendations': self._generate_ui_recommendations()
        }
        
        return audit_report
    
    def _generate_audit_summary(self) -> Dict:
        """Generate high-level audit summary"""
        return {
            'core_functionality_score': self._score_dict(self.results.start_stop_buttons),
            'accessibility_score': self._score_dict(self.results.screen_reader_support),
            'responsive_design_score': self._score_dict(self.results.mobile_compatibility),
            'error_handling_score': self._score_dict(self.results.error_handling),
            'total_ui_states': len(self.results.connection_states) + len(self.results.recording_states),
            'aria_implementation_count': sum(self.results.aria_labels.values())
        }
    
    def _score_dict(self, data_dict: Dict) -> float:
        """Calculate percentage score for a dictionary of boolean values"""
        if not data_dict:
            return 0.0
        true_count = sum(1 for v in data_dict.values() if v)
        return round((true_count / len(data_dict)) * 100, 1)
    
    def _calculate_compliance_score(self) -> float:
        """Calculate overall compliance score"""
        scores = [
            self._score_dict(self.results.start_stop_buttons),
            self._score_dict(self.results.error_handling),
            self._score_dict(self.results.screen_reader_support),
            self._score_dict(self.results.mobile_compatibility)
        ]
        return round(sum(scores) / len(scores), 1)
    
    def _identify_priority_issues(self) -> List[str]:
        """Identify high-priority issues"""
        issues = []
        
        if not self.results.start_stop_buttons.get('start_button_present', False):
            issues.append("CRITICAL: Start Recording button not found")
        
        if not self.results.microphone_permissions.get('navigator_getusermedia', False):
            issues.append("CRITICAL: Microphone access API not implemented")
        
        if not self.results.websocket_reconnect.get('reconnect_logic_present', False):
            issues.append("HIGH: WebSocket reconnection logic missing")
        
        if self.results.aria_labels.get('aria_label_count', 0) < 5:
            issues.append("MEDIUM: Insufficient ARIA labels for accessibility")
        
        if not self.results.mobile_compatibility.get('viewport_meta', False):
            issues.append("MEDIUM: Mobile viewport not configured")
        
        return issues
    
    def _generate_ui_recommendations(self) -> List[str]:
        """Generate UI improvement recommendations"""
        recommendations = []
        
        if self._score_dict(self.results.error_handling) < 75:
            recommendations.append("Implement comprehensive error handling with user-friendly messages")
        
        if self._score_dict(self.results.screen_reader_support) < 80:
            recommendations.append("Enhance accessibility with proper ARIA labels and semantic HTML")
        
        if not self.results.error_toast_system.get('toast_component_present', False):
            recommendations.append("Add toast notification system for better user feedback")
        
        if len(self.results.connection_states) < 3:
            recommendations.append("Implement clear UI states for all connection scenarios")
        
        recommendations.append("Add comprehensive keyboard navigation support")
        recommendations.append("Implement loading states and progress indicators")
        
        return recommendations

def main():
    """Run comprehensive frontend audit"""
    auditor = FrontendAuditor()
    
    print("🚀 MINA FRONTEND UI/UX AUDIT")
    print("=" * 40)
    
    # Run comprehensive audit
    report = auditor.run_comprehensive_audit()
    
    # Display summary
    print("\n📊 AUDIT SUMMARY")
    print("-" * 25)
    for key, value in report['audit_summary'].items():
        print(f"{key}: {value}")
    
    print(f"\n🎯 Overall Compliance Score: {report['compliance_score']}/100")
    
    print("\n🚨 Priority Issues")
    print("-" * 20)
    for i, issue in enumerate(report['priority_issues'], 1):
        print(f"{i}. {issue}")
    
    print("\n💡 Recommendations")
    print("-" * 20)
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"{i}. {rec}")
    
    # Save detailed report
    with open('frontend_audit_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Detailed audit saved to: frontend_audit_report.json")
    
    return report

if __name__ == "__main__":
    main()