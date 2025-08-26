# ♿ **FIX PACK 5: Accessibility and UX Enhancement Components**

import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class AccessibilityFeature(Enum):
    SCREEN_READER = "screen_reader"
    KEYBOARD_NAVIGATION = "keyboard_navigation"
    HIGH_CONTRAST = "high_contrast"
    LARGE_TEXT = "large_text"
    REDUCED_MOTION = "reduced_motion"
    VOICE_CONTROL = "voice_control"
    CAPTIONS = "captions"

@dataclass
class UserPreferences:
    """User accessibility and UX preferences."""
    high_contrast: bool = False
    large_text: bool = False
    reduced_motion: bool = False
    screen_reader_enabled: bool = False
    keyboard_only: bool = False
    voice_control: bool = False
    font_size_multiplier: float = 1.0
    color_theme: str = "dark"  # dark, light, high_contrast
    error_verbosity: str = "standard"  # minimal, standard, verbose
    auto_scroll: bool = True
    sound_enabled: bool = True
    haptic_feedback: bool = True

class AdvancedAccessibilityManager:
    """Comprehensive accessibility management with personalization."""
    
    def __init__(self):
        self.user_preferences = {}
        self.a11y_features = {
            AccessibilityFeature.SCREEN_READER: True,
            AccessibilityFeature.KEYBOARD_NAVIGATION: True,
            AccessibilityFeature.HIGH_CONTRAST: True,
            AccessibilityFeature.LARGE_TEXT: True,
            AccessibilityFeature.REDUCED_MOTION: True,
            AccessibilityFeature.VOICE_CONTROL: False,  # Requires additional setup
            AccessibilityFeature.CAPTIONS: True
        }
        self.behavior_analytics = {}
        
    def load_user_preferences(self, user_id: str) -> UserPreferences:
        """Load user accessibility preferences."""
        if user_id in self.user_preferences:
            return self.user_preferences[user_id]
        
        # Try to load from localStorage equivalent or database
        default_prefs = UserPreferences()
        
        # Auto-detect some preferences based on browser/system
        system_prefs = self._detect_system_preferences()
        if system_prefs:
            default_prefs.high_contrast = system_prefs.get('prefers_contrast', False)
            default_prefs.reduced_motion = system_prefs.get('prefers_reduced_motion', False)
            default_prefs.large_text = system_prefs.get('prefers_large_text', False)
        
        self.user_preferences[user_id] = default_prefs
        return default_prefs
    
    def save_user_preferences(self, user_id: str, preferences: UserPreferences):
        """Save user accessibility preferences."""
        self.user_preferences[user_id] = preferences
        
        # In a real implementation, persist to database
        logger.info(f"Saved accessibility preferences for user {user_id}: {asdict(preferences)}")
    
    def _detect_system_preferences(self) -> Dict[str, Any]:
        """Detect system-level accessibility preferences."""
        # This would typically be done on the frontend with CSS media queries
        # or through browser APIs. Here we provide the structure for backend.
        return {
            'prefers_contrast': False,
            'prefers_reduced_motion': False,
            'prefers_large_text': False,
            'screen_reader_detected': False
        }
    
    def generate_a11y_config(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive accessibility configuration."""
        prefs = self.load_user_preferences(user_id)
        
        return {
            'css_classes': self._generate_css_classes(prefs),
            'aria_settings': self._generate_aria_settings(prefs),
            'keyboard_config': self._generate_keyboard_config(prefs),
            'screen_reader_config': self._generate_screen_reader_config(prefs),
            'animation_config': self._generate_animation_config(prefs),
            'color_config': self._generate_color_config(prefs),
            'font_config': self._generate_font_config(prefs)
        }
    
    def _generate_css_classes(self, prefs: UserPreferences) -> List[str]:
        """Generate CSS classes based on user preferences."""
        classes = []
        
        if prefs.high_contrast:
            classes.append('high-contrast')
        if prefs.large_text:
            classes.append('large-text')
        if prefs.reduced_motion:
            classes.append('reduced-motion')
        if prefs.screen_reader_enabled:
            classes.append('screen-reader-optimized')
        if prefs.keyboard_only:
            classes.append('keyboard-navigation')
            
        classes.append(f'theme-{prefs.color_theme}')
        
        return classes
    
    def _generate_aria_settings(self, prefs: UserPreferences) -> Dict[str, Any]:
        """Generate ARIA settings for enhanced screen reader support."""
        return {
            'live_region_politeness': 'polite' if not prefs.screen_reader_enabled else 'assertive',
            'description_verbosity': 'verbose' if prefs.screen_reader_enabled else 'standard',
            'landmark_navigation': True,
            'skip_links': True,
            'role_announcements': prefs.screen_reader_enabled,
            'progress_announcements': True
        }
    
    def _generate_keyboard_config(self, prefs: UserPreferences) -> Dict[str, Any]:
        """Generate keyboard navigation configuration."""
        return {
            'tab_navigation': True,
            'skip_to_content': True,
            'keyboard_shortcuts': prefs.keyboard_only,
            'focus_indicators': 'enhanced' if prefs.keyboard_only else 'standard',
            'escape_key_handling': True,
            'arrow_key_navigation': prefs.keyboard_only
        }
    
    def _generate_screen_reader_config(self, prefs: UserPreferences) -> Dict[str, Any]:
        """Generate screen reader optimizations."""
        return {
            'live_regions': True,
            'status_updates': prefs.screen_reader_enabled,
            'progress_announcements': True,
            'error_announcements': True,
            'content_structure_hints': prefs.screen_reader_enabled,
            'table_headers': True,
            'form_labels': True
        }
    
    def _generate_animation_config(self, prefs: UserPreferences) -> Dict[str, Any]:
        """Generate animation and motion configuration."""
        return {
            'animations_enabled': not prefs.reduced_motion,
            'transitions_duration': 0 if prefs.reduced_motion else 300,
            'auto_scroll_speed': 'slow' if prefs.reduced_motion else 'normal',
            'parallax_effects': not prefs.reduced_motion,
            'hover_effects': not prefs.reduced_motion
        }
    
    def _generate_color_config(self, prefs: UserPreferences) -> Dict[str, Any]:
        """Generate color and contrast configuration."""
        base_colors = {
            'dark': {
                'bg_primary': '#1a1a1a',
                'bg_secondary': '#2d2d2d',
                'text_primary': '#ffffff',
                'text_secondary': '#b0b0b0',
                'accent': '#007acc',
                'error': '#ff6b6b',
                'success': '#51cf66',
                'warning': '#ffd93d'
            },
            'light': {
                'bg_primary': '#ffffff',
                'bg_secondary': '#f8f9fa',
                'text_primary': '#212529',
                'text_secondary': '#6c757d',
                'accent': '#0056b3',
                'error': '#dc3545',
                'success': '#198754',
                'warning': '#ffc107'
            },
            'high_contrast': {
                'bg_primary': '#000000',
                'bg_secondary': '#1a1a1a',
                'text_primary': '#ffffff',
                'text_secondary': '#ffffff',
                'accent': '#ffff00',
                'error': '#ff0000',
                'success': '#00ff00',
                'warning': '#ffff00'
            }
        }
        
        theme = prefs.color_theme if not prefs.high_contrast else 'high_contrast'
        colors = base_colors.get(theme, base_colors['dark'])
        
        return {
            'theme': theme,
            'colors': colors,
            'contrast_ratio': 7.0 if prefs.high_contrast else 4.5,
            'color_blind_safe': True
        }
    
    def _generate_font_config(self, prefs: UserPreferences) -> Dict[str, Any]:
        """Generate font and typography configuration."""
        base_size = 16  # Base font size in px
        multiplier = prefs.font_size_multiplier
        
        if prefs.large_text:
            multiplier = max(multiplier, 1.25)
        
        return {
            'base_font_size': int(base_size * multiplier),
            'line_height': 1.6 if prefs.large_text else 1.5,
            'font_family': 'system-ui, -apple-system, "Segoe UI", sans-serif',
            'font_weight': '400',
            'letter_spacing': '0.02em' if prefs.large_text else '0',
            'dyslexia_friendly': False  # Could be added as preference
        }

class IntelligentErrorManager:
    """Enhanced error management with recovery guidance and multi-modal presentation."""
    
    def __init__(self):
        self.error_patterns = self._load_error_patterns()
        self.recovery_strategies = self._load_recovery_strategies()
        self.error_history = {}
        self.user_error_preferences = {}
        
    def handle_error(self, error: Exception, context: Dict[str, Any], 
                    user_id: Optional[str] = None) -> Dict[str, Any]:
        """Comprehensive error handling with user-friendly recovery."""
        error_analysis = self._analyze_error(error, context)
        recovery_plan = self._generate_recovery_plan(error_analysis)
        
        # Get user preferences for error presentation
        error_prefs = self.user_error_preferences.get(user_id, {})
        verbosity = error_prefs.get('verbosity', 'standard')
        
        # Create multi-modal error presentation
        error_response = {
            'error_id': f"err_{int(time.time())}_{hash(str(error)) % 10000}",
            'category': error_analysis['category'],
            'severity': error_analysis['severity'],
            'user_message': self._create_user_message(error_analysis, verbosity),
            'recovery_actions': recovery_plan['immediate_actions'],
            'troubleshooting_steps': recovery_plan['troubleshooting_steps'],
            'alternative_approaches': recovery_plan['alternative_approaches'],
            'technical_details': self._create_technical_details(error_analysis, verbosity),
            'presentation': self._create_presentation_config(error_analysis, error_prefs)
        }
        
        # Log error for analytics
        self._log_error_analytics(error_response, context)
        
        return error_response
    
    def _analyze_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze error to understand category, severity, and likely causes."""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Categorize error
        category = self._categorize_error(error_type, error_message, context)
        
        # Determine severity
        severity = self._assess_severity(error_type, context)
        
        # Identify likely causes
        likely_causes = self._identify_causes(error_type, error_message, context)
        
        # Check if this is a recurring error
        error_signature = f"{error_type}:{category}"
        recurrence_count = self.error_history.get(error_signature, 0) + 1
        self.error_history[error_signature] = recurrence_count
        
        return {
            'category': category,
            'severity': severity,
            'error_type': error_type,
            'error_message': error_message,
            'likely_causes': likely_causes,
            'recurrence_count': recurrence_count,
            'context': context,
            'timestamp': time.time()
        }
    
    def _categorize_error(self, error_type: str, message: str, context: Dict[str, Any]) -> str:
        """Categorize error into user-friendly categories."""
        if 'network' in message.lower() or 'connection' in message.lower():
            return 'connection'
        elif 'microphone' in message.lower() or 'audio' in message.lower():
            return 'microphone'
        elif 'session' in message.lower():
            return 'session'
        elif 'timeout' in message.lower():
            return 'timeout'
        elif 'permission' in message.lower():
            return 'permissions'
        elif error_type in ['ValueError', 'TypeError']:
            return 'validation'
        else:
            return 'system'
    
    def _assess_severity(self, error_type: str, context: Dict[str, Any]) -> str:
        """Assess error severity for appropriate response."""
        critical_errors = ['ConnectionError', 'TimeoutError', 'AuthenticationError']
        warning_errors = ['ValidationError', 'ValueError']
        
        if error_type in critical_errors:
            return 'critical'
        elif error_type in warning_errors:
            return 'warning'
        else:
            return 'error'
    
    def _identify_causes(self, error_type: str, message: str, context: Dict[str, Any]) -> List[str]:
        """Identify likely causes of the error."""
        causes = []
        
        if 'connection' in message.lower():
            causes.extend(['Poor internet connection', 'Server temporarily unavailable', 'Firewall blocking connection'])
        elif 'microphone' in message.lower():
            causes.extend(['Microphone not connected', 'Microphone permissions denied', 'Another app using microphone'])
        elif 'timeout' in message.lower():
            causes.extend(['Slow internet connection', 'Server overloaded', 'Large audio file'])
        
        return causes
    
    def _generate_recovery_plan(self, error_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive recovery plan."""
        category = error_analysis['category']
        severity = error_analysis['severity']
        
        recovery_strategies = {
            'connection': {
                'immediate': ['Check internet connection', 'Refresh the page', 'Try again in a moment'],
                'troubleshooting': [
                    'Check if other websites load properly',
                    'Disable VPN or proxy if using one',
                    'Contact your network administrator if on corporate network'
                ],
                'alternatives': ['Use mobile hotspot', 'Try from different location', 'Use different browser']
            },
            'microphone': {
                'immediate': ['Allow microphone access', 'Check microphone connection', 'Close other audio apps'],
                'troubleshooting': [
                    'Click microphone icon in browser address bar',
                    'Check system sound settings',
                    'Test microphone in other applications'
                ],
                'alternatives': ['Use different microphone', 'Use mobile device', 'Upload audio file instead']
            },
            'session': {
                'immediate': ['Start new session', 'Refresh the page', 'Clear browser cache'],
                'troubleshooting': [
                    'Check if logged in properly',
                    'Clear cookies and retry',
                    'Try incognito/private mode'
                ],
                'alternatives': ['Contact support', 'Try different browser', 'Use mobile app']
            }
        }
        
        default_strategy = {
            'immediate': ['Refresh the page', 'Try again', 'Check internet connection'],
            'troubleshooting': ['Clear browser cache', 'Try different browser', 'Contact support'],
            'alternatives': ['Use mobile app', 'Contact customer support']
        }
        
        strategy = recovery_strategies.get(category, default_strategy)
        
        return {
            'immediate_actions': strategy['immediate'],
            'troubleshooting_steps': strategy['troubleshooting'],
            'alternative_approaches': strategy['alternatives']
        }
    
    def _create_user_message(self, error_analysis: Dict[str, Any], verbosity: str) -> str:
        """Create user-friendly error message."""
        category = error_analysis['category']
        severity = error_analysis['severity']
        
        base_messages = {
            'connection': "We're having trouble connecting to our servers.",
            'microphone': "There's an issue with your microphone access.",
            'session': "Your session has encountered a problem.",
            'timeout': "The operation is taking longer than expected.",
            'permissions': "We need additional permissions to continue.",
            'validation': "There's an issue with the provided information.",
            'system': "We've encountered a technical issue."
        }
        
        base_message = base_messages.get(category, "Something went wrong.")
        
        if verbosity == 'minimal':
            return base_message
        elif verbosity == 'verbose':
            technical_info = f" (Error: {error_analysis['error_type']})"
            return base_message + technical_info
        else:  # standard
            return base_message + " Please try the suggested solutions below."
    
    def _create_technical_details(self, error_analysis: Dict[str, Any], verbosity: str) -> Dict[str, Any]:
        """Create technical details for debugging."""
        if verbosity == 'minimal':
            return {}
        
        return {
            'error_type': error_analysis['error_type'],
            'category': error_analysis['category'],
            'timestamp': error_analysis['timestamp'],
            'recurrence_count': error_analysis['recurrence_count'],
            'context': error_analysis['context'] if verbosity == 'verbose' else {}
        }
    
    def _create_presentation_config(self, error_analysis: Dict[str, Any], 
                                  user_prefs: Dict[str, Any]) -> Dict[str, Any]:
        """Create multi-modal presentation configuration."""
        severity = error_analysis['severity']
        
        return {
            'visual': {
                'color': '#ff6b6b' if severity == 'critical' else '#ffd93d' if severity == 'warning' else '#666',
                'icon': '🚨' if severity == 'critical' else '⚠️' if severity == 'warning' else 'ℹ️',
                'animation': not user_prefs.get('reduced_motion', False)
            },
            'audio': {
                'enabled': user_prefs.get('sound_enabled', True),
                'tone': 'error' if severity == 'critical' else 'warning'
            },
            'haptic': {
                'enabled': user_prefs.get('haptic_feedback', True),
                'pattern': 'strong' if severity == 'critical' else 'gentle'
            },
            'accessibility': {
                'announce_immediately': severity == 'critical',
                'focus_management': True,
                'keyboard_dismissible': True
            }
        }
    
    def _log_error_analytics(self, error_response: Dict[str, Any], context: Dict[str, Any]):
        """Log error for analytics and improvement."""
        analytics_data = {
            'error_id': error_response['error_id'],
            'category': error_response['category'],
            'severity': error_response['severity'],
            'context': context,
            'timestamp': time.time()
        }
        
        logger.error(f"Error analytics: {analytics_data}")
    
    def _load_error_patterns(self) -> Dict[str, Any]:
        """Load known error patterns for better categorization."""
        return {}
    
    def _load_recovery_strategies(self) -> Dict[str, Any]:
        """Load recovery strategies for different error types."""
        return {}

import time