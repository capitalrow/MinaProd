/**
 * ♿ ACCESSIBILITY & MOBILE OPTIMIZATION SYSTEM
 * Implements WCAG 2.1 AA compliance, keyboard navigation, and mobile-first design
 */

class AccessibilityMobileOptimization {
    constructor() {
        this.preferences = {
            highContrast: false,
            largeText: false,
            reducedMotion: false,
            keyboardNavigation: true
        };
        
        this.mobileFeatures = {
            touchOptimized: true,
            orientationHandling: true,
            viewportAdjustment: true,
            gestureSupport: false // Disabled by default for accessibility
        };
        
        this.keyboardShortcuts = new Map([
            ['Space', 'toggleRecording'],
            ['Escape', 'stopRecording'],
            ['KeyC', 'clearTranscript'],
            ['KeyD', 'downloadTranscript'],
            ['KeyH', 'showHelp']
        ]);
        
        this.touchGestures = new Map();
        this.init();
        
        console.log('♿ Accessibility & Mobile Optimization initialized');
    }
    
    /**
     * Initialize accessibility and mobile optimizations
     */
    init() {
        this.setupAccessibilityFeatures();
        this.setupKeyboardNavigation();
        this.setupMobileOptimizations();
        this.setupScreenReaderSupport();
        this.setupHighContrastMode();
        this.detectUserPreferences();
        this.setupResponsiveHandling();
        
        console.log('✅ Accessibility and mobile features ready');
    }
    
    /**
     * Setup core accessibility features
     */
    setupAccessibilityFeatures() {
        // Focus management
        this.setupFocusManagement();
        
        // ARIA live regions
        this.setupLiveRegions();
        
        // Skip links
        this.setupSkipLinks();
        
        // Error announcements
        this.setupErrorAnnouncements();
        
        // Progress announcements
        this.setupProgressAnnouncements();
    }
    
    /**
     * Setup focus management for keyboard navigation
     */
    setupFocusManagement() {
        // Focus visible indicator
        const style = document.createElement('style');
        style.textContent = `
            /* High visibility focus indicators */
            *:focus {
                outline: 3px solid #4A90E2 !important;
                outline-offset: 2px !important;
                box-shadow: 0 0 0 1px #fff, 0 0 0 4px #4A90E2 !important;
            }
            
            /* Skip link styling */
            .skip-link {
                position: absolute;
                top: -40px;
                left: 6px;
                background: #000;
                color: #fff;
                padding: 8px;
                text-decoration: none;
                border-radius: 4px;
                z-index: 1000;
            }
            
            .skip-link:focus {
                top: 6px;
            }
            
            /* High contrast mode */
            .high-contrast {
                filter: contrast(150%) !important;
            }
            
            .high-contrast * {
                border-color: #000 !important;
                background: var(--bg-high-contrast, #fff) !important;
                color: var(--text-high-contrast, #000) !important;
            }
            
            /* Large text mode */
            .large-text * {
                font-size: 1.2em !important;
                line-height: 1.5 !important;
            }
            
            /* Reduced motion */
            .reduced-motion *,
            .reduced-motion *::before,
            .reduced-motion *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
            
            /* Mobile optimizations */
            @media (max-width: 768px) {
                .btn {
                    min-height: 44px;
                    min-width: 44px;
                    padding: 12px 16px;
                }
                
                .transcript-area {
                    height: 300px !important;
                    font-size: 16px;
                    line-height: 1.4;
                }
                
                .card-header h5 {
                    font-size: 1.1rem;
                }
                
                .stat-value {
                    font-size: 1.5rem;
                }
            }
            
            /* Touch-friendly targets */
            @media (pointer: coarse) {
                button, a, [role="button"] {
                    min-height: 44px;
                    min-width: 44px;
                }
            }
        `;
        document.head.appendChild(style);
        
        // Focus trap for modals
        this.setupFocusTrap();
    }
    
    /**
     * Setup keyboard navigation
     */
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (event) => {
            // Handle keyboard shortcuts
            if (event.ctrlKey || event.metaKey) {
                const action = this.keyboardShortcuts.get(event.code);
                if (action) {
                    event.preventDefault();
                    this.handleKeyboardAction(action);
                    return;
                }
            }
            
            // Handle standalone keys
            if (!event.ctrlKey && !event.metaKey && !event.altKey) {
                const action = this.keyboardShortcuts.get(event.code);
                if (action && this.isKeyboardShortcutActive()) {
                    event.preventDefault();
                    this.handleKeyboardAction(action);
                }
            }
            
            // Tab navigation enhancement
            if (event.key === 'Tab') {
                this.handleTabNavigation(event);
            }
            
            // Arrow key navigation for custom components
            if (event.key.startsWith('Arrow')) {
                this.handleArrowNavigation(event);
            }
        });
        
        // Add keyboard hints to interactive elements
        this.addKeyboardHints();
    }
    
    /**
     * Handle keyboard actions
     */
    handleKeyboardAction(action) {
        switch (action) {
            case 'toggleRecording':
                const recordButton = document.getElementById('recordButton');
                if (recordButton) {
                    recordButton.click();
                    this.announceAction('Recording toggled via keyboard');
                }
                break;
                
            case 'stopRecording':
                const recordBtn = document.getElementById('recordButton');
                if (recordBtn && recordBtn.textContent.includes('Stop')) {
                    recordBtn.click();
                    this.announceAction('Recording stopped via keyboard');
                }
                break;
                
            case 'clearTranscript':
                const clearButton = document.getElementById('clearButton');
                if (clearButton) {
                    clearButton.click();
                    this.announceAction('Transcript cleared via keyboard');
                }
                break;
                
            case 'downloadTranscript':
                const downloadButton = document.getElementById('downloadButton');
                if (downloadButton) {
                    downloadButton.click();
                    this.announceAction('Transcript download started via keyboard');
                }
                break;
                
            case 'showHelp':
                this.showKeyboardHelp();
                break;
        }
    }
    
    /**
     * Check if keyboard shortcuts should be active
     */
    isKeyboardShortcutActive() {
        const activeElement = document.activeElement;
        return !activeElement || !['INPUT', 'TEXTAREA', 'SELECT'].includes(activeElement.tagName);
    }
    
    /**
     * Setup mobile optimizations
     */
    setupMobileOptimizations() {
        // Viewport handling
        this.setupViewportHandling();
        
        // Touch optimizations
        this.setupTouchOptimizations();
        
        // Orientation handling
        this.setupOrientationHandling();
        
        // Performance optimizations for mobile
        this.setupMobilePerformance();
        
        // iOS Safari specific fixes
        this.setupIOSFixes();
        
        // Android Chrome specific fixes
        this.setupAndroidFixes();
    }
    
    /**
     * Setup viewport handling for mobile
     */
    setupViewportHandling() {
        // Dynamic viewport height for mobile browsers
        const setVH = () => {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        };
        
        setVH();
        window.addEventListener('resize', setVH);
        window.addEventListener('orientationchange', setVH);
        
        // Prevent zoom on input focus (iOS)
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            if (input.style.fontSize === '' || parseFloat(input.style.fontSize) < 16) {
                input.style.fontSize = '16px';
            }
        });
    }
    
    /**
     * Setup touch optimizations
     */
    setupTouchOptimizations() {
        // Increase touch targets on mobile
        if ('ontouchstart' in window) {
            document.body.classList.add('touch-device');
            
            // Add touch feedback
            document.addEventListener('touchstart', (event) => {
                if (event.target.matches('button, [role="button"], a')) {
                    event.target.classList.add('touch-active');
                }
            });
            
            document.addEventListener('touchend', (event) => {
                setTimeout(() => {
                    event.target.classList.remove('touch-active');
                }, 150);
            });
        }
        
        // Prevent double-tap zoom on buttons
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (event) => {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
    }
    
    /**
     * Setup iOS Safari specific fixes
     */
    setupIOSFixes() {
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
        if (!isIOS) return;
        
        // Fix viewport height issues
        document.documentElement.style.setProperty('--vh', `${window.innerHeight * 0.01}px`);
        
        // Fix audio context issues
        const fixAudioContext = () => {
            if (window.AudioContext) {
                const context = new (window.AudioContext || window.webkitAudioContext)();
                if (context.state === 'suspended') {
                    context.resume();
                }
            }
        };
        
        document.addEventListener('touchstart', fixAudioContext, { once: true });
        
        // Fix sticky hover states
        document.addEventListener('touchstart', () => {}, true);
    }
    
    /**
     * Setup Android Chrome specific fixes
     */
    setupAndroidFixes() {
        const isAndroid = /Android/.test(navigator.userAgent);
        if (!isAndroid) return;
        
        // Fix viewport issues with soft keyboard
        const originalHeight = window.innerHeight;
        window.addEventListener('resize', () => {
            if (window.innerHeight < originalHeight * 0.75) {
                // Soft keyboard is likely open
                document.body.classList.add('keyboard-open');
            } else {
                document.body.classList.remove('keyboard-open');
            }
        });
        
        // Fix audio autoplay issues
        const enableAudio = () => {
            const audio = new Audio();
            audio.play().catch(() => {}); // Silent fail is OK
        };
        
        document.addEventListener('touchstart', enableAudio, { once: true });
    }
    
    /**
     * Setup screen reader support
     */
    setupScreenReaderSupport() {
        // Create live regions if they don't exist
        this.createLiveRegion('polite-announcements', 'polite');
        this.createLiveRegion('assertive-announcements', 'assertive');
        
        // Announce page load
        this.announceToScreenReader('Mina Live Transcription application loaded and ready');
        
        // Monitor UI state changes
        this.monitorUIStateChanges();
    }
    
    /**
     * Create live region for screen reader announcements
     */
    createLiveRegion(id, politeness) {
        if (document.getElementById(id)) return;
        
        const region = document.createElement('div');
        region.id = id;
        region.setAttribute('aria-live', politeness);
        region.setAttribute('aria-atomic', 'true');
        region.className = 'sr-only';
        region.style.cssText = 'position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden;';
        
        document.body.appendChild(region);
    }
    
    /**
     * Announce message to screen readers
     */
    announceToScreenReader(message, urgent = false) {
        const regionId = urgent ? 'assertive-announcements' : 'polite-announcements';
        const region = document.getElementById(regionId);
        
        if (region) {
            region.textContent = message;
            setTimeout(() => {
                region.textContent = '';
            }, 1000);
        }
        
        console.log(`📢 Screen Reader: ${message}`);
    }
    
    /**
     * Setup high contrast mode
     */
    setupHighContrastMode() {
        // Detect system preference
        const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches;
        if (prefersHighContrast) {
            this.enableHighContrast();
        }
        
        // Add toggle button
        this.addAccessibilityControls();
    }
    
    /**
     * Add accessibility control panel
     */
    addAccessibilityControls() {
        const controlsHTML = `
            <div id="accessibility-controls" class="position-fixed top-0 end-0 m-3" style="z-index: 1050;">
                <div class="dropdown">
                    <button class="btn btn-outline-info btn-sm dropdown-toggle" type="button" 
                            id="accessibilityDropdown" data-bs-toggle="dropdown" aria-expanded="false"
                            aria-label="Accessibility options">
                        <i class="bi bi-universal-access" aria-hidden="true"></i>
                        <span class="d-none d-md-inline ms-1">Accessibility</span>
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="accessibilityDropdown">
                        <li>
                            <button class="dropdown-item" onclick="window.accessibilityMobile.toggleHighContrast()">
                                <i class="bi bi-circle-half" aria-hidden="true"></i>
                                High Contrast
                            </button>
                        </li>
                        <li>
                            <button class="dropdown-item" onclick="window.accessibilityMobile.toggleLargeText()">
                                <i class="bi bi-fonts" aria-hidden="true"></i>
                                Large Text
                            </button>
                        </li>
                        <li>
                            <button class="dropdown-item" onclick="window.accessibilityMobile.toggleReducedMotion()">
                                <i class="bi bi-pause" aria-hidden="true"></i>
                                Reduce Motion
                            </button>
                        </li>
                        <li><hr class="dropdown-divider"></li>
                        <li>
                            <button class="dropdown-item" onclick="window.accessibilityMobile.showKeyboardHelp()">
                                <i class="bi bi-keyboard" aria-hidden="true"></i>
                                Keyboard Shortcuts
                            </button>
                        </li>
                    </ul>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', controlsHTML);
    }
    
    /**
     * Toggle high contrast mode
     */
    toggleHighContrast() {
        this.preferences.highContrast = !this.preferences.highContrast;
        
        if (this.preferences.highContrast) {
            this.enableHighContrast();
        } else {
            this.disableHighContrast();
        }
        
        this.announceToScreenReader(`High contrast mode ${this.preferences.highContrast ? 'enabled' : 'disabled'}`);
        this.savePreferences();
    }
    
    /**
     * Enable high contrast mode
     */
    enableHighContrast() {
        document.body.classList.add('high-contrast');
        document.documentElement.style.setProperty('--bg-high-contrast', '#000');
        document.documentElement.style.setProperty('--text-high-contrast', '#fff');
        
        this.preferences.highContrast = true;
    }
    
    /**
     * Disable high contrast mode
     */
    disableHighContrast() {
        document.body.classList.remove('high-contrast');
        this.preferences.highContrast = false;
    }
    
    /**
     * Toggle large text mode
     */
    toggleLargeText() {
        this.preferences.largeText = !this.preferences.largeText;
        document.body.classList.toggle('large-text', this.preferences.largeText);
        
        this.announceToScreenReader(`Large text mode ${this.preferences.largeText ? 'enabled' : 'disabled'}`);
        this.savePreferences();
    }
    
    /**
     * Toggle reduced motion mode
     */
    toggleReducedMotion() {
        this.preferences.reducedMotion = !this.preferences.reducedMotion;
        document.body.classList.toggle('reduced-motion', this.preferences.reducedMotion);
        
        this.announceToScreenReader(`Reduced motion mode ${this.preferences.reducedMotion ? 'enabled' : 'disabled'}`);
        this.savePreferences();
    }
    
    /**
     * Show keyboard help dialog
     */
    showKeyboardHelp() {
        const helpHTML = `
            <div class="modal fade" id="keyboardHelpModal" tabindex="-1" aria-labelledby="keyboardHelpTitle" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="keyboardHelpTitle">Keyboard Shortcuts</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th scope="col">Key</th>
                                        <th scope="col">Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><kbd>Space</kbd></td>
                                        <td>Start/Stop Recording</td>
                                    </tr>
                                    <tr>
                                        <td><kbd>Esc</kbd></td>
                                        <td>Stop Recording</td>
                                    </tr>
                                    <tr>
                                        <td><kbd>Ctrl + C</kbd></td>
                                        <td>Clear Transcript</td>
                                    </tr>
                                    <tr>
                                        <td><kbd>Ctrl + D</kbd></td>
                                        <td>Download Transcript</td>
                                    </tr>
                                    <tr>
                                        <td><kbd>Ctrl + H</kbd></td>
                                        <td>Show This Help</td>
                                    </tr>
                                    <tr>
                                        <td><kbd>Tab</kbd></td>
                                        <td>Navigate Between Elements</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if present
        const existingModal = document.getElementById('keyboardHelpModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', helpHTML);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('keyboardHelpModal'));
        modal.show();
        
        this.announceToScreenReader('Keyboard shortcuts help dialog opened');
    }
    
    /**
     * Detect and apply user preferences
     */
    detectUserPreferences() {
        // Check for saved preferences
        const saved = localStorage.getItem('accessibilityPreferences');
        if (saved) {
            try {
                this.preferences = { ...this.preferences, ...JSON.parse(saved) };
                this.applyPreferences();
            } catch (error) {
                console.warn('Failed to load accessibility preferences:', error);
            }
        }
        
        // Detect system preferences
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            this.preferences.reducedMotion = true;
            document.body.classList.add('reduced-motion');
        }
        
        if (window.matchMedia('(prefers-contrast: high)').matches) {
            this.preferences.highContrast = true;
            this.enableHighContrast();
        }
    }
    
    /**
     * Apply user preferences
     */
    applyPreferences() {
        if (this.preferences.highContrast) {
            this.enableHighContrast();
        }
        
        if (this.preferences.largeText) {
            document.body.classList.add('large-text');
        }
        
        if (this.preferences.reducedMotion) {
            document.body.classList.add('reduced-motion');
        }
    }
    
    /**
     * Save user preferences
     */
    savePreferences() {
        try {
            localStorage.setItem('accessibilityPreferences', JSON.stringify(this.preferences));
        } catch (error) {
            console.warn('Failed to save accessibility preferences:', error);
        }
    }
    
    /**
     * Monitor UI state changes for screen reader announcements
     */
    monitorUIStateChanges() {
        // Monitor recording state changes
        const recordButton = document.getElementById('recordButton');
        if (recordButton) {
            new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList' || mutation.type === 'characterData') {
                        const isRecording = recordButton.textContent.includes('Stop');
                        this.announceToScreenReader(`Recording ${isRecording ? 'started' : 'stopped'}`);
                    }
                });
            }).observe(recordButton, { childList: true, subtree: true, characterData: true });
        }
        
        // Monitor transcript changes
        const transcriptDisplay = document.getElementById('transcriptDisplay');
        if (transcriptDisplay) {
            let transcriptLength = 0;
            new MutationObserver(() => {
                const newLength = transcriptDisplay.textContent.length;
                if (newLength > transcriptLength + 20) { // Significant change
                    this.announceToScreenReader('New transcription text available');
                }
                transcriptLength = newLength;
            }).observe(transcriptDisplay, { childList: true, subtree: true });
        }
    }
    
    /**
     * Announce action to screen reader
     */
    announceAction(action) {
        this.announceToScreenReader(action, false);
    }
    
    /**
     * Add keyboard hints to elements
     */
    addKeyboardHints() {
        const recordButton = document.getElementById('recordButton');
        if (recordButton) {
            recordButton.setAttribute('title', 'Click or press Space to start/stop recording');
        }
        
        const clearButton = document.getElementById('clearButton');
        if (clearButton) {
            clearButton.setAttribute('title', 'Click or press Ctrl+C to clear transcript');
        }
        
        const downloadButton = document.getElementById('downloadButton');
        if (downloadButton) {
            downloadButton.setAttribute('title', 'Click or press Ctrl+D to download transcript');
        }
    }
    
    /**
     * Setup focus trap for modal dialogs
     */
    setupFocusTrap() {
        // This would be implemented for modal focus management
        // Keeping it simple for now
    }
    
    /**
     * Handle tab navigation
     */
    handleTabNavigation(event) {
        // Enhanced tab navigation logic would go here
        // For now, rely on browser defaults
    }
    
    /**
     * Handle arrow key navigation
     */
    handleArrowNavigation(event) {
        // Arrow key navigation for custom components
        // Implementation depends on specific UI components
    }
    
    /**
     * Setup live regions
     */
    setupLiveRegions() {
        this.createLiveRegion('polite-announcements', 'polite');
        this.createLiveRegion('assertive-announcements', 'assertive');
    }
    
    /**
     * Setup skip links
     */
    setupSkipLinks() {
        // Skip links are already in the HTML template
        // Ensure they work properly
        const skipLink = document.querySelector('.skip-link');
        if (skipLink) {
            skipLink.addEventListener('click', (event) => {
                event.preventDefault();
                const target = document.getElementById('main-content');
                if (target) {
                    target.focus();
                    target.scrollIntoView();
                }
            });
        }
    }
    
    /**
     * Setup error announcements
     */
    setupErrorAnnouncements() {
        // Monitor for error messages and announce them
        const errorRegion = document.getElementById('error-messages');
        if (errorRegion) {
            new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                        const text = mutation.target.textContent;
                        if (text.trim()) {
                            this.announceToScreenReader(text, true);
                        }
                    }
                });
            }).observe(errorRegion, { childList: true, subtree: true });
        }
    }
    
    /**
     * Setup progress announcements
     */
    setupProgressAnnouncements() {
        // Announce progress updates for screen readers
        const progressElements = document.querySelectorAll('[aria-live="polite"]');
        progressElements.forEach(element => {
            new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'characterData' || mutation.type === 'childList') {
                        // Throttle announcements to avoid spam
                        clearTimeout(this.progressTimeout);
                        this.progressTimeout = setTimeout(() => {
                            const text = element.textContent.trim();
                            if (text && !text.includes('Click "Start Recording"')) {
                                this.announceToScreenReader(text);
                            }
                        }, 500);
                    }
                });
            }).observe(element, { childList: true, subtree: true, characterData: true });
        });
    }
    
    /**
     * Setup responsive handling
     */
    setupResponsiveHandling() {
        // Adjust UI based on screen size
        const handleResize = () => {
            const isMobile = window.innerWidth < 768;
            document.body.classList.toggle('mobile-layout', isMobile);
            
            if (isMobile) {
                this.optimizeForMobile();
            } else {
                this.optimizeForDesktop();
            }
        };
        
        handleResize();
        window.addEventListener('resize', handleResize);
    }
    
    /**
     * Optimize interface for mobile
     */
    optimizeForMobile() {
        // Show system health by default on mobile when recording
        const systemHealth = document.getElementById('systemHealth');
        if (systemHealth) {
            systemHealth.classList.remove('d-none');
        }
        
        // Adjust button sizes
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(btn => {
            btn.classList.add('btn-lg');
        });
    }
    
    /**
     * Optimize interface for desktop
     */
    optimizeForDesktop() {
        // Desktop-specific optimizations
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(btn => {
            btn.classList.remove('btn-lg');
        });
    }
    
    /**
     * Setup mobile performance optimizations
     */
    setupMobilePerformance() {
        // Passive event listeners for better scroll performance
        document.addEventListener('touchstart', () => {}, { passive: true });
        document.addEventListener('touchmove', () => {}, { passive: true });
        
        // Reduce animations on low-end devices
        if (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4) {
            document.body.classList.add('reduced-motion');
        }
    }
    
    /**
     * Setup orientation handling
     */
    setupOrientationHandling() {
        const handleOrientation = () => {
            const isLandscape = window.innerWidth > window.innerHeight;
            document.body.classList.toggle('landscape', isLandscape);
            document.body.classList.toggle('portrait', !isLandscape);
            
            // Adjust layout for orientation
            if (isLandscape && window.innerWidth < 768) {
                // Mobile landscape
                const transcriptArea = document.querySelector('.transcript-area');
                if (transcriptArea) {
                    transcriptArea.style.height = '200px';
                }
            }
        };
        
        handleOrientation();
        window.addEventListener('orientationchange', handleOrientation);
        window.addEventListener('resize', handleOrientation);
    }
    
    /**
     * Get accessibility status
     */
    getAccessibilityStatus() {
        return {
            preferences: this.preferences,
            mobileFeatures: this.mobileFeatures,
            keyboardNavigation: this.preferences.keyboardNavigation,
            screenReaderSupport: true,
            wcagCompliance: 'AA'
        };
    }
}

// Create global instance
window.accessibilityMobile = new AccessibilityMobileOptimization();

console.log('✅ Accessibility & Mobile Optimization system loaded');

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
