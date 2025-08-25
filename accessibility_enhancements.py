#!/usr/bin/env python3
"""
Accessibility Enhancement Utilities
Provides ARIA labels, keyboard navigation, and accessibility testing helpers
"""

def get_accessibility_attributes() -> dict:
    """Get comprehensive accessibility attributes for UI components"""
    
    return {
        'recording_controls': {
            'start_button': {
                'aria-label': 'Start recording audio for transcription',
                'aria-describedby': 'recording-status',
                'role': 'button',
                'tabindex': '0',
                'keyboard_shortcut': 'Space'
            },
            'stop_button': {
                'aria-label': 'Stop recording audio',
                'aria-describedby': 'recording-status',
                'role': 'button',
                'tabindex': '1'
            }
        },
        
        'status_indicators': {
            'connection_status': {
                'aria-live': 'polite',
                'aria-atomic': 'true',
                'role': 'status'
            },
            'recording_status': {
                'aria-live': 'polite',
                'aria-atomic': 'true',
                'role': 'status',
                'id': 'recording-status'
            },
            'quality_status': {
                'aria-live': 'assertive',
                'aria-atomic': 'true',
                'role': 'alert'
            }
        },
        
        'transcription_display': {
            'interim_text': {
                'aria-live': 'polite',
                'aria-label': 'Live transcription in progress',
                'role': 'log'
            },
            'final_text': {
                'aria-live': 'polite',
                'aria-label': 'Final transcription results',
                'role': 'log',
                'tabindex': '0'
            }
        },
        
        'controls': {
            'auto_scroll': {
                'aria-label': 'Automatically scroll to show latest transcription',
                'role': 'switch',
                'tabindex': '2'
            },
            'show_interim': {
                'aria-label': 'Show interim transcription results while speaking',
                'role': 'switch',
                'tabindex': '3'
            }
        }
    }

def get_keyboard_navigation_script() -> str:
    """Generate JavaScript for keyboard navigation"""
    
    return """
// Enhanced Keyboard Navigation for Accessibility
class AccessibilityKeyboardHandler {
    constructor() {
        this.focusableElements = [];
        this.currentFocus = 0;
        this.init();
    }
    
    init() {
        // Find all focusable elements
        this.focusableElements = document.querySelectorAll(
            'button, [tabindex]:not([tabindex="-1"]), input, select, textarea'
        );
        
        // Add keyboard event listeners
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
        document.addEventListener('keyup', this.handleKeyUp.bind(this));
        
        // Focus management
        this.updateFocusIndicators();
    }
    
    handleKeyDown(event) {
        switch(event.key) {
            case ' ':
            case 'Spacebar':
                if (event.target.id === 'startRecording') {
                    event.preventDefault();
                    this.toggleRecording();
                }
                break;
                
            case 'Tab':
                this.handleTabNavigation(event);
                break;
                
            case 'Escape':
                this.handleEscape();
                break;
                
            case 'Enter':
                if (event.target.role === 'button') {
                    event.target.click();
                }
                break;
        }
    }
    
    handleTabNavigation(event) {
        // Enhanced tab navigation with proper focus management
        const focusable = Array.from(this.focusableElements);
        const currentIndex = focusable.indexOf(event.target);
        
        if (event.shiftKey) {
            // Shift+Tab - go backward
            const nextIndex = currentIndex > 0 ? currentIndex - 1 : focusable.length - 1;
            focusable[nextIndex].focus();
            event.preventDefault();
        } else {
            // Tab - go forward
            const nextIndex = currentIndex < focusable.length - 1 ? currentIndex + 1 : 0;
            focusable[nextIndex].focus();
            event.preventDefault();
        }
    }
    
    handleEscape() {
        // Escape key handling - dismiss modals, reset focus
        const activeModals = document.querySelectorAll('.modal.show, .toast.show');
        if (activeModals.length > 0) {
            activeModals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal) || bootstrap.Toast.getInstance(modal);
                if (bsModal) bsModal.hide();
            });
        }
    }
    
    toggleRecording() {
        const startBtn = document.getElementById('startRecording');
        const stopBtn = document.getElementById('stopRecording');
        
        if (window.isRecording) {
            stopBtn.click();
        } else {
            startBtn.click();
        }
    }
    
    updateFocusIndicators() {
        // Add visual focus indicators for better accessibility
        const style = document.createElement('style');
        style.textContent = `
            *:focus {
                outline: 2px solid #0d6efd !important;
                outline-offset: 2px !important;
            }
            
            .focus-visible {
                outline: 2px solid #0d6efd !important;
                outline-offset: 2px !important;
            }
            
            .sr-only {
                position: absolute !important;
                width: 1px !important;
                height: 1px !important;
                padding: 0 !important;
                margin: -1px !important;
                overflow: hidden !important;
                clip: rect(0, 0, 0, 0) !important;
                white-space: nowrap !important;
                border: 0 !important;
            }
        `;
        document.head.appendChild(style);
    }
    
    announceStatusChange(message) {
        // Screen reader announcements
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'assertive');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        setTimeout(() => document.body.removeChild(announcement), 1000);
    }
}

// Initialize accessibility features
document.addEventListener('DOMContentLoaded', () => {
    window.accessibilityHandler = new AccessibilityKeyboardHandler();
});
"""

def get_color_contrast_checker() -> str:
    """Get JavaScript for color contrast validation"""
    
    return """
// Color Contrast Checker for AA+ Compliance
class ColorContrastChecker {
    constructor() {
        this.minContrastAA = 4.5;
        this.minContrastAAA = 7.0;
    }
    
    getLuminance(r, g, b) {
        const [rs, gs, bs] = [r, g, b].map(c => {
            c = c / 255;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
    }
    
    getContrastRatio(color1, color2) {
        const lum1 = this.getLuminance(...color1);
        const lum2 = this.getLuminance(...color2);
        const brightest = Math.max(lum1, lum2);
        const darkest = Math.min(lum1, lum2);
        return (brightest + 0.05) / (darkest + 0.05);
    }
    
    checkElementContrast(element) {
        const styles = window.getComputedStyle(element);
        const bgColor = this.parseColor(styles.backgroundColor);
        const textColor = this.parseColor(styles.color);
        
        if (bgColor && textColor) {
            const ratio = this.getContrastRatio(bgColor, textColor);
            return {
                ratio: ratio,
                passAA: ratio >= this.minContrastAA,
                passAAA: ratio >= this.minContrastAAA
            };
        }
        return null;
    }
    
    parseColor(colorString) {
        if (colorString.startsWith('rgb')) {
            const matches = colorString.match(/\\d+/g);
            return matches ? matches.slice(0, 3).map(Number) : null;
        }
        return null;
    }
    
    auditPageContrast() {
        const results = [];
        const elements = document.querySelectorAll('*');
        
        elements.forEach(element => {
            if (element.textContent.trim()) {
                const result = this.checkElementContrast(element);
                if (result && !result.passAA) {
                    results.push({
                        element: element.tagName + (element.className ? '.' + element.className : ''),
                        ratio: result.ratio.toFixed(2),
                        passAA: result.passAA,
                        passAAA: result.passAAA
                    });
                }
            }
        });
        
        return results;
    }
}

// Global contrast checker
window.contrastChecker = new ColorContrastChecker();
"""