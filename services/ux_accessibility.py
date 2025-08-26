#!/usr/bin/env python3
# ♿ Production Feature: UX & Accessibility Enhancements
"""
Implements comprehensive UX and accessibility features for production-grade
user experience and compliance with accessibility standards.

Addresses: "Live Transcription UX and Accessibility Evaluation" from production assessment.

Key Features:
- Real-time feedback improvements
- Accessibility compliance (WCAG 2.1)
- Visual indicators and status updates
- Keyboard navigation support
- Screen reader optimization
- High contrast and font scaling
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class AccessibilityLevel(Enum):
    """WCAG accessibility levels."""
    A = "A"
    AA = "AA"
    AAA = "AAA"

class FeedbackType(Enum):
    """Types of user feedback."""
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    PROGRESS = "progress"

@dataclass
class AccessibilityConfig:
    """Configuration for accessibility features."""
    # WCAG compliance
    target_level: AccessibilityLevel = AccessibilityLevel.AA
    
    # Visual settings
    high_contrast_mode: bool = False
    large_text_mode: bool = False
    reduce_motion: bool = False
    
    # Audio settings
    audio_descriptions: bool = False
    sound_notifications: bool = True
    
    # Navigation
    keyboard_navigation: bool = True
    focus_indicators: bool = True
    skip_links: bool = True
    
    # Screen reader
    aria_live_regions: bool = True
    descriptive_labels: bool = True
    semantic_markup: bool = True

class UXAccessibilityManager:
    """
    ♿ Production-grade UX and accessibility manager.
    
    Handles real-time feedback, accessibility compliance, and enhanced
    user experience features for inclusive design.
    """
    
    def __init__(self, config: Optional[AccessibilityConfig] = None):
        self.config = config or AccessibilityConfig()
        
        # Feedback management
        self.active_feedbacks: Dict[str, Dict[str, Any]] = {}
        self.feedback_history: List[Dict[str, Any]] = []
        
        # Accessibility state
        self.user_preferences: Dict[str, Any] = {}
        self.accessibility_features: Dict[str, bool] = {}
        
        # Performance tracking
        self.feedback_count = 0
        self.accessibility_violations = []
        
        self._initialize_accessibility_features()
        
        logger.info(f"♿ UX Accessibility manager initialized (WCAG {self.config.target_level.value})")
    
    def _initialize_accessibility_features(self):
        """Initialize accessibility feature states."""
        self.accessibility_features = {
            'high_contrast': self.config.high_contrast_mode,
            'large_text': self.config.large_text_mode,
            'reduce_motion': self.config.reduce_motion,
            'audio_descriptions': self.config.audio_descriptions,
            'sound_notifications': self.config.sound_notifications,
            'keyboard_navigation': self.config.keyboard_navigation,
            'focus_indicators': self.config.focus_indicators,
            'skip_links': self.config.skip_links,
            'aria_live_regions': self.config.aria_live_regions,
            'descriptive_labels': self.config.descriptive_labels,
            'semantic_markup': self.config.semantic_markup
        }
    
    def generate_accessibility_css(self) -> str:
        """
        Generate CSS for accessibility features.
        
        Returns:
            CSS string for accessibility enhancements
        """
        css_rules = []
        
        # High contrast mode
        if self.accessibility_features.get('high_contrast'):
            css_rules.append("""
            .high-contrast {
                background-color: #000000 !important;
                color: #ffffff !important;
            }
            .high-contrast .btn {
                background-color: #ffffff !important;
                color: #000000 !important;
                border: 2px solid #ffffff !important;
            }
            .high-contrast .transcript-text {
                background-color: #000000 !important;
                color: #ffff00 !important;
            }
            """)
        
        # Large text mode
        if self.accessibility_features.get('large_text'):
            css_rules.append("""
            .large-text {
                font-size: 1.2em !important;
                line-height: 1.6 !important;
            }
            .large-text .transcript-text {
                font-size: 1.5em !important;
                line-height: 1.8 !important;
            }
            """)
        
        # Reduced motion
        if self.accessibility_features.get('reduce_motion'):
            css_rules.append("""
            .reduce-motion * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
            """)
        
        # Enhanced focus indicators
        if self.accessibility_features.get('focus_indicators'):
            css_rules.append("""
            .enhanced-focus *:focus {
                outline: 3px solid #4A90E2 !important;
                outline-offset: 2px !important;
                box-shadow: 0 0 0 1px #ffffff !important;
            }
            """)
        
        # Skip links
        if self.accessibility_features.get('skip_links'):
            css_rules.append("""
            .skip-link {
                position: absolute;
                top: -40px;
                left: 6px;
                background: #000;
                color: #fff;
                padding: 8px;
                text-decoration: none;
                z-index: 1000;
            }
            .skip-link:focus {
                top: 6px;
            }
            """)
        
        return "\\n".join(css_rules)
    
    def generate_accessibility_html(self) -> str:
        """
        Generate HTML for accessibility features.
        
        Returns:
            HTML string for accessibility enhancements
        """
        html_parts = []
        
        # Skip links
        if self.accessibility_features.get('skip_links'):
            html_parts.append("""
            <div class="skip-links">
                <a href="#main-content" class="skip-link">Skip to main content</a>
                <a href="#transcript-area" class="skip-link">Skip to transcript</a>
                <a href="#controls" class="skip-link">Skip to controls</a>
            </div>
            """)
        
        # ARIA live regions
        if self.accessibility_features.get('aria_live_regions'):
            html_parts.append("""
            <div id="aria-live-polite" aria-live="polite" aria-atomic="true" class="sr-only"></div>
            <div id="aria-live-assertive" aria-live="assertive" aria-atomic="true" class="sr-only"></div>
            <div id="status-announcements" role="status" aria-live="polite" class="sr-only"></div>
            """)
        
        # Accessibility controls
        html_parts.append("""
        <div id="accessibility-controls" class="accessibility-controls" role="region" aria-label="Accessibility Settings">
            <button type="button" id="toggle-high-contrast" class="btn btn-outline-secondary btn-sm" 
                    aria-pressed="false" aria-describedby="high-contrast-desc">
                <i class="fas fa-adjust" aria-hidden="true"></i>
                <span>High Contrast</span>
            </button>
            <button type="button" id="toggle-large-text" class="btn btn-outline-secondary btn-sm" 
                    aria-pressed="false" aria-describedby="large-text-desc">
                <i class="fas fa-text-height" aria-hidden="true"></i>
                <span>Large Text</span>
            </button>
            <button type="button" id="toggle-reduce-motion" class="btn btn-outline-secondary btn-sm" 
                    aria-pressed="false" aria-describedby="reduce-motion-desc">
                <i class="fas fa-pause" aria-hidden="true"></i>
                <span>Reduce Motion</span>
            </button>
        </div>
        
        <div class="sr-only">
            <div id="high-contrast-desc">Toggle high contrast mode for better visibility</div>
            <div id="large-text-desc">Increase text size for easier reading</div>
            <div id="reduce-motion-desc">Reduce animations and transitions</div>
        </div>
        """)
        
        return "\\n".join(html_parts)
    
    def generate_accessibility_javascript(self) -> str:
        """
        Generate JavaScript for accessibility features.
        
        Returns:
            JavaScript code for accessibility enhancements
        """
        js_code = f"""
        // Accessibility Manager JavaScript
        class AccessibilityManager {{
            constructor() {{
                this.features = {json.dumps(self.accessibility_features)};
                this.init();
            }}
            
            init() {{
                this.setupAccessibilityControls();
                this.setupKeyboardNavigation();
                this.setupScreenReaderSupport();
                this.loadUserPreferences();
            }}
            
            setupAccessibilityControls() {{
                // High contrast toggle
                const highContrastBtn = document.getElementById('toggle-high-contrast');
                if (highContrastBtn) {{
                    highContrastBtn.addEventListener('click', () => {{
                        this.toggleHighContrast();
                    }});
                }}
                
                // Large text toggle
                const largeTextBtn = document.getElementById('toggle-large-text');
                if (largeTextBtn) {{
                    largeTextBtn.addEventListener('click', () => {{
                        this.toggleLargeText();
                    }});
                }}
                
                // Reduce motion toggle
                const reduceMotionBtn = document.getElementById('toggle-reduce-motion');
                if (reduceMotionBtn) {{
                    reduceMotionBtn.addEventListener('click', () => {{
                        this.toggleReduceMotion();
                    }});
                }}
            }}
            
            setupKeyboardNavigation() {{
                // Add keyboard event listeners for navigation
                document.addEventListener('keydown', (e) => {{
                    // Alt + M: Go to main content
                    if (e.altKey && e.key === 'm') {{
                        e.preventDefault();
                        const mainContent = document.getElementById('main-content');
                        if (mainContent) {{
                            mainContent.focus();
                            mainContent.scrollIntoView();
                        }}
                    }}
                    
                    // Alt + T: Go to transcript
                    if (e.altKey && e.key === 't') {{
                        e.preventDefault();
                        const transcript = document.getElementById('transcript-area');
                        if (transcript) {{
                            transcript.focus();
                            transcript.scrollIntoView();
                        }}
                    }}
                    
                    // Alt + C: Go to controls
                    if (e.altKey && e.key === 'c') {{
                        e.preventDefault();
                        const controls = document.getElementById('controls');
                        if (controls) {{
                            controls.focus();
                            controls.scrollIntoView();
                        }}
                    }}
                    
                    // Escape: Close modals/overlays
                    if (e.key === 'Escape') {{
                        this.closeModalOrOverlay();
                    }}
                }});
            }}
            
            setupScreenReaderSupport() {{
                // Announce important changes to screen readers
                this.announceToScreenReader = (message, priority = 'polite') => {{
                    const liveRegion = document.getElementById(`aria-live-${{priority}}`);
                    if (liveRegion) {{
                        liveRegion.textContent = message;
                        setTimeout(() => {{
                            liveRegion.textContent = '';
                        }}, 1000);
                    }}
                }};
                
                // Announce status changes
                this.announceStatus = (message) => {{
                    const statusRegion = document.getElementById('status-announcements');
                    if (statusRegion) {{
                        statusRegion.textContent = message;
                        setTimeout(() => {{
                            statusRegion.textContent = '';
                        }}, 3000);
                    }}
                }};
            }}
            
            toggleHighContrast() {{
                const body = document.body;
                const btn = document.getElementById('toggle-high-contrast');
                
                if (body.classList.contains('high-contrast')) {{
                    body.classList.remove('high-contrast');
                    btn.setAttribute('aria-pressed', 'false');
                    this.announceStatus('High contrast mode disabled');
                }} else {{
                    body.classList.add('high-contrast');
                    btn.setAttribute('aria-pressed', 'true');
                    this.announceStatus('High contrast mode enabled');
                }}
                
                this.savePreference('high_contrast', body.classList.contains('high-contrast'));
            }}
            
            toggleLargeText() {{
                const body = document.body;
                const btn = document.getElementById('toggle-large-text');
                
                if (body.classList.contains('large-text')) {{
                    body.classList.remove('large-text');
                    btn.setAttribute('aria-pressed', 'false');
                    this.announceStatus('Large text mode disabled');
                }} else {{
                    body.classList.add('large-text');
                    btn.setAttribute('aria-pressed', 'true');
                    this.announceStatus('Large text mode enabled');
                }}
                
                this.savePreference('large_text', body.classList.contains('large-text'));
            }}
            
            toggleReduceMotion() {{
                const body = document.body;
                const btn = document.getElementById('toggle-reduce-motion');
                
                if (body.classList.contains('reduce-motion')) {{
                    body.classList.remove('reduce-motion');
                    btn.setAttribute('aria-pressed', 'false');
                    this.announceStatus('Motion reduction disabled');
                }} else {{
                    body.classList.add('reduce-motion');
                    btn.setAttribute('aria-pressed', 'true');
                    this.announceStatus('Motion reduction enabled');
                }}
                
                this.savePreference('reduce_motion', body.classList.contains('reduce-motion'));
            }}
            
            closeModalOrOverlay() {{
                // Close any open modals or overlays
                const modals = document.querySelectorAll('.modal.show, .overlay.show');
                modals.forEach(modal => {{
                    const closeBtn = modal.querySelector('.btn-close, .close');
                    if (closeBtn) {{
                        closeBtn.click();
                    }}
                }});
            }}
            
            savePreference(key, value) {{
                try {{
                    const preferences = JSON.parse(localStorage.getItem('accessibility_preferences') || '{{}}');
                    preferences[key] = value;
                    localStorage.setItem('accessibility_preferences', JSON.stringify(preferences));
                }} catch (e) {{
                    console.warn('Could not save accessibility preference:', e);
                }}
            }}
            
            loadUserPreferences() {{
                try {{
                    const preferences = JSON.parse(localStorage.getItem('accessibility_preferences') || '{{}}');
                    const body = document.body;
                    
                    if (preferences.high_contrast) {{
                        body.classList.add('high-contrast');
                        const btn = document.getElementById('toggle-high-contrast');
                        if (btn) btn.setAttribute('aria-pressed', 'true');
                    }}
                    
                    if (preferences.large_text) {{
                        body.classList.add('large-text');
                        const btn = document.getElementById('toggle-large-text');
                        if (btn) btn.setAttribute('aria-pressed', 'true');
                    }}
                    
                    if (preferences.reduce_motion) {{
                        body.classList.add('reduce-motion');
                        const btn = document.getElementById('toggle-reduce-motion');
                        if (btn) btn.setAttribute('aria-pressed', 'true');
                    }}
                }} catch (e) {{
                    console.warn('Could not load accessibility preferences:', e);
                }}
            }}
            
            // Enhanced transcript accessibility
            enhanceTranscriptAccessibility() {{
                const transcriptArea = document.getElementById('transcript-area');
                if (transcriptArea) {{
                    // Add proper ARIA attributes
                    transcriptArea.setAttribute('role', 'log');
                    transcriptArea.setAttribute('aria-live', 'polite');
                    transcriptArea.setAttribute('aria-label', 'Live transcription');
                    
                    // Add landmark for easy navigation
                    transcriptArea.setAttribute('aria-describedby', 'transcript-description');
                    
                    // Auto-scroll to new content for screen readers
                    const observer = new MutationObserver(() => {{
                        if (transcriptArea.scrollHeight > transcriptArea.clientHeight) {{
                            transcriptArea.scrollTop = transcriptArea.scrollHeight;
                        }}
                    }});
                    
                    observer.observe(transcriptArea, {{
                        childList: true,
                        subtree: true
                    }});
                }}
            }}
            
            // Announce transcript updates
            announceTranscriptUpdate(text, speaker = null) {{
                let announcement = '';
                if (speaker) {{
                    announcement = `${{speaker}} said: ${{text}}`;
                }} else {{
                    announcement = text;
                }}
                
                // Use polite announcement for transcript updates
                this.announceToScreenReader(announcement, 'polite');
            }}
            
            // Announce connection status
            announceConnectionStatus(status) {{
                const messages = {{
                    'connecting': 'Connecting to transcription service',
                    'connected': 'Connected to transcription service',
                    'disconnected': 'Disconnected from transcription service',
                    'reconnecting': 'Attempting to reconnect',
                    'error': 'Connection error occurred'
                }};
                
                const message = messages[status] || `Connection status: ${{status}}`;
                this.announceToScreenReader(message, 'assertive');
            }}
            
            // Announce recording status
            announceRecordingStatus(isRecording) {{
                const message = isRecording ? 'Recording started' : 'Recording stopped';
                this.announceToScreenReader(message, 'assertive');
            }}
        }}
        
        // Initialize accessibility manager when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {{
            window.accessibilityManager = new AccessibilityManager();
            
            // Enhance transcript area
            window.accessibilityManager.enhanceTranscriptAccessibility();
            
            console.log('♿ Accessibility features initialized');
        }});
        """
        
        return js_code
    
    def create_accessible_notification(self, message: str, feedback_type: FeedbackType,
                                     duration: int = 5000, aria_live: str = "polite") -> Dict[str, Any]:
        """
        Create an accessible notification.
        
        Args:
            message: Notification message
            feedback_type: Type of feedback
            duration: Display duration in milliseconds
            aria_live: ARIA live region setting
            
        Returns:
            Notification data
        """
        notification_id = f"notification_{int(time.time() * 1000)}"
        
        notification = {
            'id': notification_id,
            'message': message,
            'type': feedback_type.value,
            'duration': duration,
            'aria_live': aria_live,
            'timestamp': time.time(),
            'accessible': True,
            'screen_reader_text': self._generate_screen_reader_text(message, feedback_type)
        }
        
        self.active_feedbacks[notification_id] = notification
        self.feedback_history.append(notification)
        self.feedback_count += 1
        
        return notification
    
    def _generate_screen_reader_text(self, message: str, feedback_type: FeedbackType) -> str:
        """Generate screen reader optimized text."""
        prefixes = {
            FeedbackType.SUCCESS: "Success: ",
            FeedbackType.INFO: "Information: ",
            FeedbackType.WARNING: "Warning: ",
            FeedbackType.ERROR: "Error: ",
            FeedbackType.PROGRESS: "Progress update: "
        }
        
        prefix = prefixes.get(feedback_type, "")
        return f"{prefix}{message}"
    
    def generate_aria_attributes(self, element_type: str, context: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Generate appropriate ARIA attributes for elements.
        
        Args:
            element_type: Type of element (button, input, region, etc.)
            context: Additional context for attribute generation
            
        Returns:
            Dictionary of ARIA attributes
        """
        context = context or {}
        attrs = {}
        
        if element_type == "transcript_area":
            attrs.update({
                'role': 'log',
                'aria-live': 'polite',
                'aria-label': 'Live transcription text',
                'aria-describedby': 'transcript-description',
                'tabindex': '0'
            })
        
        elif element_type == "record_button":
            is_recording = context.get('is_recording', False)
            attrs.update({
                'role': 'button',
                'aria-pressed': 'true' if is_recording else 'false',
                'aria-label': 'Stop recording' if is_recording else 'Start recording',
                'aria-describedby': 'record-button-description'
            })
        
        elif element_type == "status_indicator":
            status = context.get('status', 'unknown')
            attrs.update({
                'role': 'status',
                'aria-live': 'polite',
                'aria-label': f'Connection status: {status}'
            })
        
        elif element_type == "volume_meter":
            level = context.get('level', 0)
            attrs.update({
                'role': 'progressbar',
                'aria-valuemin': '0',
                'aria-valuemax': '100',
                'aria-valuenow': str(int(level * 100)),
                'aria-label': 'Microphone volume level'
            })
        
        elif element_type == "speaker_label":
            speaker = context.get('speaker', 'Unknown')
            attrs.update({
                'role': 'text',
                'aria-label': f'Speaker: {speaker}'
            })
        
        return attrs
    
    def validate_accessibility_compliance(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Validate accessibility compliance (simplified validation).
        
        Args:
            html_content: HTML content to validate
            
        Returns:
            List of accessibility violations
        """
        violations = []
        
        # Check for missing alt attributes on images
        if '<img' in html_content and 'alt=' not in html_content:
            violations.append({
                'type': 'missing_alt_text',
                'severity': 'error',
                'message': 'Images missing alt text',
                'wcag_guideline': '1.1.1'
            })
        
        # Check for proper heading structure
        heading_levels = []
        import re
        headings = re.findall(r'<h([1-6])', html_content)
        if headings:
            heading_levels = [int(h) for h in headings]
            for i in range(1, len(heading_levels)):
                if heading_levels[i] > heading_levels[i-1] + 1:
                    violations.append({
                        'type': 'heading_structure',
                        'severity': 'warning',
                        'message': 'Heading levels not properly nested',
                        'wcag_guideline': '2.4.6'
                    })
        
        # Check for form labels
        if '<input' in html_content or '<select' in html_content or '<textarea' in html_content:
            if 'aria-label=' not in html_content and '<label' not in html_content:
                violations.append({
                    'type': 'missing_form_labels',
                    'severity': 'error',
                    'message': 'Form controls missing labels',
                    'wcag_guideline': '3.3.2'
                })
        
        self.accessibility_violations.extend(violations)
        return violations
    
    def get_accessibility_stats(self) -> Dict[str, Any]:
        """Get accessibility and UX statistics."""
        return {
            'wcag_target_level': self.config.target_level.value,
            'active_features': sum(1 for enabled in self.accessibility_features.values() if enabled),
            'total_features': len(self.accessibility_features),
            'feedback_count': self.feedback_count,
            'active_feedbacks': len(self.active_feedbacks),
            'accessibility_violations': len(self.accessibility_violations),
            'features_enabled': {
                name: enabled for name, enabled in self.accessibility_features.items()
            }
        }

# Global UX accessibility manager
_ux_manager: Optional[UXAccessibilityManager] = None

def get_ux_manager() -> Optional[UXAccessibilityManager]:
    """Get the global UX accessibility manager."""
    return _ux_manager

def initialize_ux_manager(config: Optional[AccessibilityConfig] = None) -> UXAccessibilityManager:
    """Initialize the global UX accessibility manager."""
    global _ux_manager
    _ux_manager = UXAccessibilityManager(config)
    return _ux_manager