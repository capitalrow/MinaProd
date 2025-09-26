/**
 * Keyboard Navigation for WCAG 2.1 AA Compliance
 * Provides keyboard shortcuts and navigation support
 */

class KeyboardNavigation {
    constructor() {
        this.shortcuts = {
            ' ': this.toggleRecording.bind(this),    // Spacebar
            'Enter': this.toggleRecording.bind(this), // Enter key
            'r': this.startRecording.bind(this),      // R key
            's': this.stopRecording.bind(this),       // S key  
            'c': this.clearTranscript.bind(this),     // C key
            'e': this.exportTranscript.bind(this),    // E key
            '?': this.showHelp.bind(this),            // ? key
            'h': this.showHelp.bind(this),            // H key
            'Escape': this.closeDialogs.bind(this)    // Escape key
        };
        
        this.init();
    }
    
    init() {
        // Add keyboard event listener
        document.addEventListener('keydown', (e) => {
            // Skip if user is typing in an input or textarea
            if (e.target.tagName === 'INPUT' || 
                e.target.tagName === 'TEXTAREA' || 
                e.target.isContentEditable) {
                return;
            }
            
            // Check for shortcuts
            const handler = this.shortcuts[e.key];
            if (handler) {
                e.preventDefault();
                handler();
            }
            
            // Tab navigation enhancement
            if (e.key === 'Tab') {
                this.handleTabNavigation(e);
            }
        });
        
        // Add focus styles
        this.addFocusStyles();
        
        // Announce to screen readers
        this.announceKeyboardSupport();
    }
    
    toggleRecording() {
        const button = document.getElementById('recordButton');
        if (button) {
            button.click();
            const isRecording = button.getAttribute('aria-pressed') === 'true';
            this.announceAction(isRecording ? 'Recording started' : 'Recording stopped');
        }
    }
    
    startRecording() {
        const button = document.getElementById('recordButton');
        if (button && button.getAttribute('aria-pressed') === 'false') {
            button.click();
            this.announceAction('Recording started');
        }
    }
    
    stopRecording() {
        const button = document.getElementById('recordButton');
        if (button && button.getAttribute('aria-pressed') === 'true') {
            button.click();
            this.announceAction('Recording stopped');
        }
    }
    
    clearTranscript() {
        const transcriptArea = document.querySelector('.transcript-content');
        if (transcriptArea) {
            transcriptArea.innerHTML = '';
            this.announceAction('Transcript cleared');
        }
    }
    
    exportTranscript() {
        const transcripts = document.querySelectorAll('.transcript-segment');
        if (transcripts.length > 0) {
            let text = '';
            transcripts.forEach(segment => {
                text += segment.textContent + '\n';
            });
            
            // Create download
            const blob = new Blob([text], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `transcript_${new Date().toISOString()}.txt`;
            a.click();
            URL.revokeObjectURL(url);
            
            this.announceAction('Transcript exported');
        } else {
            this.announceAction('No transcript to export');
        }
    }
    
    showHelp() {
        // Check if help dialog already exists
        if (document.getElementById('keyboard-help-dialog')) {
            this.closeDialogs();
            return;
        }
        
        const helpDialog = document.createElement('div');
        helpDialog.id = 'keyboard-help-dialog';
        helpDialog.className = 'help-dialog';
        helpDialog.setAttribute('role', 'dialog');
        helpDialog.setAttribute('aria-modal', 'true');
        helpDialog.setAttribute('aria-labelledby', 'help-title');
        
        helpDialog.innerHTML = `
            <div class="help-content">
                <h2 id="help-title">Keyboard Shortcuts</h2>
                <button class="close-btn" onclick="keyboardNav.closeDialogs()" aria-label="Close help dialog">×</button>
                <dl class="shortcuts-list">
                    <dt><kbd>Space</kbd> or <kbd>Enter</kbd></dt>
                    <dd>Toggle recording on/off</dd>
                    
                    <dt><kbd>R</kbd></dt>
                    <dd>Start recording</dd>
                    
                    <dt><kbd>S</kbd></dt>
                    <dd>Stop recording</dd>
                    
                    <dt><kbd>C</kbd></dt>
                    <dd>Clear transcript</dd>
                    
                    <dt><kbd>E</kbd></dt>
                    <dd>Export transcript to file</dd>
                    
                    <dt><kbd>?</kbd> or <kbd>H</kbd></dt>
                    <dd>Show this help dialog</dd>
                    
                    <dt><kbd>Escape</kbd></dt>
                    <dd>Close dialogs</dd>
                    
                    <dt><kbd>Tab</kbd></dt>
                    <dd>Navigate between elements</dd>
                </dl>
                <p class="help-note">
                    <strong>Note:</strong> These shortcuts work when focus is not in a text input field.
                </p>
            </div>
        `;
        
        document.body.appendChild(helpDialog);
        
        // Focus on close button
        helpDialog.querySelector('.close-btn').focus();
        
        // Trap focus within dialog
        this.trapFocus(helpDialog);
        
        this.announceAction('Help dialog opened');
    }
    
    closeDialogs() {
        const dialogs = document.querySelectorAll('.help-dialog, .permission-dialog');
        dialogs.forEach(dialog => dialog.remove());
        
        // Return focus to record button
        const recordButton = document.getElementById('recordButton');
        if (recordButton) {
            recordButton.focus();
        }
        
        this.announceAction('Dialog closed');
    }
    
    announceAction(message) {
        // Update screen reader announcement area
        const statusElement = document.getElementById('recording-status');
        if (statusElement) {
            statusElement.textContent = message;
        }
        
        // Also update visual status
        const statusText = document.getElementById('statusText');
        if (statusText) {
            statusText.textContent = message;
        }
        
        // Log for debugging
        console.log(`🔊 Announced: ${message}`);
    }
    
    announceKeyboardSupport() {
        // Create announcement for screen readers
        const announcement = document.createElement('div');
        announcement.className = 'sr-only';
        announcement.setAttribute('role', 'status');
        announcement.setAttribute('aria-live', 'polite');
        announcement.textContent = 'Keyboard shortcuts available. Press question mark for help.';
        document.body.appendChild(announcement);
        
        // Remove after announcement
        setTimeout(() => announcement.remove(), 3000);
    }
    
    handleTabNavigation(e) {
        // Enhance tab navigation with visual indicators
        const focusableElements = document.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements.length === 0) return;
        
        const currentIndex = Array.from(focusableElements).indexOf(document.activeElement);
        
        // Add visual focus indicator
        if (document.activeElement) {
            document.activeElement.classList.add('keyboard-focused');
        }
    }
    
    trapFocus(element) {
        const focusableElements = element.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements.length === 0) return;
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        element.addEventListener('keydown', (e) => {
            if (e.key !== 'Tab') return;
            
            if (e.shiftKey) {
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        });
    }
    
    addFocusStyles() {
        // Add CSS for keyboard focus indicators
        const style = document.createElement('style');
        style.textContent = `
            /* Skip to main content link */
            .skip-link {
                position: absolute;
                top: -40px;
                left: 0;
                background: var(--primary-bg, #1a1a1a);
                color: var(--primary-text, #ffffff);
                padding: 8px 16px;
                text-decoration: none;
                border-radius: 0 0 4px 0;
                z-index: 10000;
                transition: top 0.2s;
            }
            
            .skip-link:focus {
                top: 0;
                outline: 3px solid var(--accent-color, #4a9eff);
                outline-offset: 2px;
            }
            
            /* Focus indicators */
            *:focus {
                outline: 3px solid var(--accent-color, #4a9eff);
                outline-offset: 2px;
            }
            
            .keyboard-focused {
                box-shadow: 0 0 0 3px rgba(74, 158, 255, 0.4);
            }
            
            /* Help dialog styles */
            .help-dialog {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: var(--secondary-bg, #2d2d2d);
                color: var(--primary-text, #ffffff);
                padding: 24px;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
                z-index: 10001;
                max-width: 500px;
                max-height: 80vh;
                overflow-y: auto;
            }
            
            .help-content h2 {
                margin-top: 0;
                margin-bottom: 20px;
                color: var(--primary-text, #ffffff);
            }
            
            .close-btn {
                position: absolute;
                top: 12px;
                right: 12px;
                background: transparent;
                border: none;
                color: var(--primary-text, #ffffff);
                font-size: 24px;
                cursor: pointer;
                padding: 4px 8px;
            }
            
            .close-btn:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            
            .shortcuts-list dt {
                font-weight: bold;
                margin-top: 12px;
                display: inline-block;
                min-width: 120px;
            }
            
            .shortcuts-list dd {
                display: inline-block;
                margin-left: 8px;
                color: var(--secondary-text, #b3b3b3);
            }
            
            kbd {
                background: var(--primary-bg, #1a1a1a);
                padding: 2px 6px;
                border-radius: 3px;
                border: 1px solid var(--border-color, #444);
                font-family: monospace;
                font-size: 0.9em;
            }
            
            .help-note {
                margin-top: 20px;
                padding-top: 16px;
                border-top: 1px solid var(--border-color, #444);
                color: var(--secondary-text, #b3b3b3);
                font-size: 0.9em;
            }
            
            /* Screen reader only content */
            .sr-only {
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border: 0;
            }
            
            /* High contrast mode support */
            @media (prefers-contrast: high) {
                *:focus {
                    outline-width: 4px;
                }
                
                .help-dialog {
                    border: 2px solid currentColor;
                }
            }
            
            /* Reduced motion support */
            @media (prefers-reduced-motion: reduce) {
                * {
                    animation-duration: 0.01ms !important;
                    transition-duration: 0.01ms !important;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Initialize keyboard navigation when DOM is ready
let keyboardNav;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        keyboardNav = new KeyboardNavigation();
        window.keyboardNav = keyboardNav;
    });
} else {
    keyboardNav = new KeyboardNavigation();
    window.keyboardNav = keyboardNav;
}

console.log('⌨️ Keyboard navigation initialized - Press ? for help');

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
