/**
 * GOOGLE RECORDER UI SYSTEM
 * Professional UI/UX matching Google Recorder's polish and user experience
 */

class GoogleRecorderUISystem {
    constructor() {
        this.isActive = false;
        this.animationState = {
            isTyping: false,
            currentAnimation: null,
            typewriterSpeed: 30, // ms per character
            fadeTransitionSpeed: 200
        };
        
        this.uiElements = {
            transcriptContainer: null,
            statusIndicator: null,
            confidenceOverlay: null,
            qualityIndicators: null
        };
        
        this.textStates = {
            interim: '',
            final: '',
            confidence: [],
            timestamps: []
        };
        
        this.visualTheme = {
            darkMode: false,
            highContrast: false,
            largeText: false,
            animations: true
        };
        
        this.setupUITheme();
    }
    
    initialize() {
        console.log('🎨 Initializing Google Recorder UI System');
        
        this.setupUIElements();
        this.setupAnimationSystem();
        this.setupAccessibility();
        this.setupResponsiveDesign();
        this.isActive = true;
        
        console.log('✅ Professional UI system active');
        return true;
    }
    
    setupUIElements() {
        // Create professional UI structure
        this.createTranscriptDisplayArea();
        this.createStatusIndicators();
        this.createQualityMetrics();
        this.createControlPanel();
        this.applyProfessionalStyling();
    }
    
    createTranscriptDisplayArea() {
        // Enhanced transcript container
        let container = document.getElementById('transcriptContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'transcriptContainer';
            document.body.appendChild(container);
        }
        
        // Clear and recreate with professional structure
        container.innerHTML = `
            <div class="transcript-display-area">
                <div class="status-header">
                    <div class="recording-indicator">
                        <div class="pulse-dot"></div>
                        <span class="status-text">Ready to record</span>
                    </div>
                    <div class="quality-metrics-mini">
                        <span class="quality-badge" data-metric="overall">--</span>
                    </div>
                </div>
                
                <div class="transcript-content">
                    <div class="interim-text-container">
                        <span class="interim-text" id="interimText"></span>
                        <span class="typing-cursor"></span>
                    </div>
                    <div class="final-text-container" id="finalTextContainer">
                        <!-- Final text segments will appear here -->
                    </div>
                </div>
                
                <div class="transcript-footer">
                    <div class="session-info">
                        <span class="word-count">0 words</span>
                        <span class="session-duration">00:00</span>
                    </div>
                    <div class="confidence-indicator">
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: 0%"></div>
                        </div>
                        <span class="confidence-text">--</span>
                    </div>
                </div>
            </div>
        `;
        
        this.uiElements.transcriptContainer = container;
    }
    
    createStatusIndicators() {
        // Professional status indicator system
        const statusContainer = document.createElement('div');
        statusContainer.className = 'status-indicator-system';
        statusContainer.innerHTML = `
            <div class="primary-status">
                <div class="status-icon">
                    <svg class="microphone-icon" viewBox="0 0 24 24">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                        <line x1="12" y1="19" x2="12" y2="23"/>
                        <line x1="8" y1="23" x2="16" y2="23"/>
                    </svg>
                </div>
                <span class="status-message">Ready to transcribe</span>
            </div>
            
            <div class="processing-indicator" style="display: none;">
                <div class="processing-animation">
                    <div class="wave"></div>
                    <div class="wave"></div>
                    <div class="wave"></div>
                </div>
                <span class="processing-text">Processing speech...</span>
            </div>
            
            <div class="connection-status">
                <div class="connection-dot online"></div>
                <span class="connection-text">Connected</span>
            </div>
        `;
        
        // Insert at the beginning of transcript container
        this.uiElements.transcriptContainer.insertBefore(
            statusContainer, 
            this.uiElements.transcriptContainer.firstChild
        );
        
        this.uiElements.statusIndicator = statusContainer;
    }
    
    createQualityMetrics() {
        // Live quality metrics display
        const qualityPanel = document.createElement('div');
        qualityPanel.className = 'quality-metrics-panel';
        qualityPanel.innerHTML = `
            <div class="metrics-header">
                <h4>Live Quality Metrics</h4>
                <button class="metrics-toggle">Hide</button>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-icon audio-icon"></div>
                    <span class="metric-label">Audio</span>
                    <span class="metric-value" data-metric="audio">--</span>
                </div>
                
                <div class="metric-item">
                    <div class="metric-icon accuracy-icon"></div>
                    <span class="metric-label">Accuracy</span>
                    <span class="metric-value" data-metric="accuracy">--</span>
                </div>
                
                <div class="metric-item">
                    <div class="metric-icon latency-icon"></div>
                    <span class="metric-label">Latency</span>
                    <span class="metric-value" data-metric="latency">--ms</span>
                </div>
                
                <div class="metric-item">
                    <div class="metric-icon completeness-icon"></div>
                    <span class="metric-label">Coverage</span>
                    <span class="metric-value" data-metric="completeness">--</span>
                </div>
            </div>
            
            <div class="performance-chart">
                <canvas id="performanceChart" width="280" height="100"></canvas>
            </div>
        `;
        
        document.body.appendChild(qualityPanel);
        this.uiElements.qualityIndicators = qualityPanel;
        
        // Initialize performance chart
        this.initializePerformanceChart();
    }
    
    createControlPanel() {
        // Professional control interface
        const controlPanel = document.createElement('div');
        controlPanel.className = 'transcription-controls';
        controlPanel.innerHTML = `
            <div class="primary-controls">
                <button class="record-button" id="recordButton">
                    <div class="button-icon">
                        <svg class="record-icon" viewBox="0 0 24 24">
                            <circle cx="12" cy="12" r="10"/>
                        </svg>
                    </div>
                    <span class="button-text">Start Recording</span>
                </button>
                
                <button class="stop-button" id="stopButton" disabled>
                    <div class="button-icon">
                        <svg class="stop-icon" viewBox="0 0 24 24">
                            <rect x="6" y="6" width="12" height="12"/>
                        </svg>
                    </div>
                    <span class="button-text">Stop</span>
                </button>
            </div>
            
            <div class="secondary-controls">
                <button class="settings-button" title="Settings">
                    <svg viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="3"/>
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                    </svg>
                </button>
                
                <button class="export-button" title="Export Transcript">
                    <svg viewBox="0 0 24 24">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="7,10 12,15 17,10"/>
                        <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                </button>
                
                <button class="theme-toggle" title="Toggle Dark Mode">
                    <svg viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="5"/>
                        <line x1="12" y1="1" x2="12" y2="3"/>
                        <line x1="12" y1="21" x2="12" y2="23"/>
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                        <line x1="1" y1="12" x2="3" y2="12"/>
                        <line x1="21" y1="12" x2="23" y2="12"/>
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                    </svg>
                </button>
            </div>
        `;
        
        this.uiElements.transcriptContainer.appendChild(controlPanel);
        this.setupControlHandlers();
    }
    
    applyProfessionalStyling() {
        // Inject Google Recorder-inspired CSS
        const style = document.createElement('style');
        style.textContent = `
            /* Google Recorder-Inspired Professional Styling */
            .transcript-display-area {
                max-width: 800px;
                margin: 0 auto;
                background: var(--surface-color);
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                padding: 24px;
                font-family: 'Google Sans', 'Segoe UI', system-ui, sans-serif;
                transition: all 0.3s ease;
            }
            
            .status-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 16px;
                border-bottom: 1px solid var(--border-color);
            }
            
            .recording-indicator {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .pulse-dot {
                width: 12px;
                height: 12px;
                background: #34a853;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.2); opacity: 0.7; }
                100% { transform: scale(1); opacity: 1; }
            }
            
            .status-text {
                font-weight: 500;
                color: var(--text-primary);
                font-size: 14px;
            }
            
            .quality-badge {
                background: var(--accent-color);
                color: white;
                padding: 4px 12px;
                border-radius: 16px;
                font-size: 12px;
                font-weight: 600;
            }
            
            .transcript-content {
                min-height: 200px;
                max-height: 400px;
                overflow-y: auto;
                padding: 16px 0;
                line-height: 1.6;
                font-size: 16px;
                scroll-behavior: smooth;
            }
            
            .interim-text-container {
                display: flex;
                align-items: center;
                margin-bottom: 8px;
            }
            
            .interim-text {
                color: var(--text-secondary);
                font-style: italic;
                opacity: 0.8;
                transition: all 0.2s ease;
            }
            
            .typing-cursor {
                width: 2px;
                height: 20px;
                background: var(--accent-color);
                margin-left: 2px;
                animation: blink 1s infinite;
            }
            
            @keyframes blink {
                50% { opacity: 0; }
            }
            
            .final-text-container {
                color: var(--text-primary);
                line-height: 1.7;
            }
            
            .final-text-segment {
                display: inline;
                animation: fadeIn 0.3s ease;
                margin-right: 4px;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(2px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .confidence-low {
                text-decoration: underline;
                text-decoration-color: #fbbc04;
                text-decoration-style: wavy;
            }
            
            .confidence-medium {
                border-bottom: 1px dotted var(--text-secondary);
            }
            
            .confidence-high {
                /* No special styling for high confidence */
            }
            
            .transcript-footer {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 16px;
                padding-top: 16px;
                border-top: 1px solid var(--border-color);
                font-size: 12px;
                color: var(--text-secondary);
            }
            
            .confidence-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .confidence-bar {
                width: 60px;
                height: 4px;
                background: var(--background-secondary);
                border-radius: 2px;
                overflow: hidden;
            }
            
            .confidence-fill {
                height: 100%;
                background: linear-gradient(90deg, #ea4335 0%, #fbbc04 50%, #34a853 100%);
                transition: width 0.3s ease;
            }
            
            .transcription-controls {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 24px;
                padding-top: 20px;
                border-top: 1px solid var(--border-color);
            }
            
            .primary-controls {
                display: flex;
                gap: 12px;
            }
            
            .record-button, .stop-button {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 12px 24px;
                border: none;
                border-radius: 24px;
                font-weight: 600;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s ease;
                outline: none;
            }
            
            .record-button {
                background: #34a853;
                color: white;
            }
            
            .record-button:hover {
                background: #2d8f47;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(52, 168, 83, 0.3);
            }
            
            .stop-button {
                background: #ea4335;
                color: white;
            }
            
            .stop-button:hover {
                background: #d73527;
            }
            
            .stop-button:disabled {
                background: var(--background-secondary);
                color: var(--text-disabled);
                cursor: not-allowed;
            }
            
            .secondary-controls {
                display: flex;
                gap: 8px;
            }
            
            .settings-button, .export-button, .theme-toggle {
                width: 40px;
                height: 40px;
                border: none;
                border-radius: 20px;
                background: var(--background-secondary);
                color: var(--text-secondary);
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .settings-button:hover, .export-button:hover, .theme-toggle:hover {
                background: var(--accent-color);
                color: white;
                transform: translateY(-1px);
            }
            
            .settings-button svg, .export-button svg, .theme-toggle svg {
                width: 18px;
                height: 18px;
            }
            
            .quality-metrics-panel {
                position: fixed;
                top: 20px;
                right: 20px;
                width: 320px;
                background: var(--surface-color);
                border-radius: 12px;
                box-shadow: 0 6px 24px rgba(0,0,0,0.15);
                padding: 20px;
                z-index: 1000;
                transition: all 0.3s ease;
            }
            
            .metrics-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 16px;
            }
            
            .metrics-header h4 {
                margin: 0;
                color: var(--text-primary);
                font-size: 16px;
                font-weight: 600;
            }
            
            .metrics-toggle {
                background: none;
                border: none;
                color: var(--text-secondary);
                cursor: pointer;
                font-size: 12px;
                padding: 4px 8px;
                border-radius: 4px;
                transition: background 0.2s ease;
            }
            
            .metrics-toggle:hover {
                background: var(--background-secondary);
            }
            
            .metrics-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
                margin-bottom: 16px;
            }
            
            .metric-item {
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 12px;
                background: var(--background-secondary);
                border-radius: 8px;
                transition: all 0.2s ease;
            }
            
            .metric-item:hover {
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .metric-icon {
                width: 24px;
                height: 24px;
                margin-bottom: 8px;
                border-radius: 50%;
            }
            
            .audio-icon { background: linear-gradient(135deg, #4285f4, #34a853); }
            .accuracy-icon { background: linear-gradient(135deg, #34a853, #fbbc04); }
            .latency-icon { background: linear-gradient(135deg, #fbbc04, #ea4335); }
            .completeness-icon { background: linear-gradient(135deg, #ea4335, #9aa0a6); }
            
            .metric-label {
                font-size: 11px;
                color: var(--text-secondary);
                margin-bottom: 4px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .metric-value {
                font-size: 16px;
                font-weight: 600;
                color: var(--text-primary);
            }
            
            .performance-chart {
                margin-top: 16px;
                padding-top: 16px;
                border-top: 1px solid var(--border-color);
            }
            
            /* Dark mode theme variables */
            [data-theme="dark"] {
                --surface-color: #202124;
                --background-secondary: #303134;
                --text-primary: #e8eaed;
                --text-secondary: #9aa0a6;
                --text-disabled: #5f6368;
                --border-color: #3c4043;
                --accent-color: #8ab4f8;
            }
            
            /* Light mode theme variables */
            [data-theme="light"], :root {
                --surface-color: #ffffff;
                --background-secondary: #f8f9fa;
                --text-primary: #202124;
                --text-secondary: #5f6368;
                --text-disabled: #9aa0a6;
                --border-color: #dadce0;
                --accent-color: #1a73e8;
            }
            
            /* Responsive design */
            @media (max-width: 768px) {
                .transcript-display-area {
                    margin: 16px;
                    padding: 16px;
                }
                
                .quality-metrics-panel {
                    position: relative;
                    top: 0;
                    right: 0;
                    width: 100%;
                    margin-top: 20px;
                }
                
                .transcription-controls {
                    flex-direction: column;
                    gap: 16px;
                }
                
                .primary-controls {
                    justify-content: center;
                    width: 100%;
                }
                
                .secondary-controls {
                    justify-content: center;
                }
            }
            
            /* Accessibility enhancements */
            @media (prefers-reduced-motion: reduce) {
                *, *::before, *::after {
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: 0.01ms !important;
                }
            }
            
            @media (prefers-high-contrast: high) {
                .transcript-display-area {
                    border: 2px solid currentColor;
                }
                
                .confidence-low {
                    background: yellow;
                    color: black;
                }
            }
            
            /* Focus indicators for keyboard navigation */
            button:focus-visible {
                outline: 2px solid var(--accent-color);
                outline-offset: 2px;
            }
            
            /* Large text mode */
            .large-text {
                font-size: 120% !important;
            }
            
            .large-text .transcript-content {
                font-size: 20px !important;
            }
        `;
        
        document.head.appendChild(style);
    }
    
    setupAnimationSystem() {
        // Advanced animation system for smooth text updates
        this.animationQueue = [];
        this.isAnimating = false;
        
        // Text update animation handler
        this.textUpdateHandler = this.createTextUpdateHandler();
    }
    
    createTextUpdateHandler() {
        return {
            typewriterEffect: (element, text, speed = 30) => {
                return new Promise((resolve) => {
                    element.textContent = '';
                    let index = 0;
                    
                    const type = () => {
                        if (index < text.length) {
                            element.textContent += text[index];
                            index++;
                            setTimeout(type, speed);
                        } else {
                            resolve();
                        }
                    };
                    
                    type();
                });
            },
            
            fadeTransition: (element, newText, duration = 200) => {
                return new Promise((resolve) => {
                    element.style.transition = `opacity ${duration}ms ease`;
                    element.style.opacity = '0';
                    
                    setTimeout(() => {
                        element.textContent = newText;
                        element.style.opacity = '1';
                        setTimeout(resolve, duration);
                    }, duration);
                });
            },
            
            slideIn: (element, text) => {
                return new Promise((resolve) => {
                    const span = document.createElement('span');
                    span.className = 'final-text-segment';
                    span.textContent = text + ' ';
                    
                    element.appendChild(span);
                    
                    // Scroll to bottom smoothly
                    element.scrollTop = element.scrollHeight;
                    
                    setTimeout(resolve, 300);
                });
            }
        };
    }
    
    setupAccessibility() {
        // WCAG 2.1 AA compliance
        this.setupKeyboardNavigation();
        this.setupScreenReaderSupport();
        this.setupReducedMotionSupport();
        this.setupHighContrastSupport();
    }
    
    setupKeyboardNavigation() {
        // Keyboard shortcuts and navigation
        document.addEventListener('keydown', (event) => {
            if (event.ctrlKey || event.metaKey) {
                switch (event.key) {
                    case 'r':
                        event.preventDefault();
                        this.toggleRecording();
                        break;
                    case 's':
                        event.preventDefault();
                        this.stopRecording();
                        break;
                    case 'd':
                        event.preventDefault();
                        this.toggleDarkMode();
                        break;
                    case 'e':
                        event.preventDefault();
                        this.exportTranscript();
                        break;
                }
            }
        });
        
        // Tab navigation enhancement
        const focusableElements = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
        const focusableElementsList = Array.from(
            this.uiElements.transcriptContainer.querySelectorAll(focusableElements)
        );
        
        focusableElementsList.forEach((element, index) => {
            element.addEventListener('keydown', (event) => {
                if (event.key === 'Tab') {
                    // Enhanced tab navigation logic can be added here
                }
            });
        });
    }
    
    setupScreenReaderSupport() {
        // ARIA labels and live regions
        const transcriptContent = document.querySelector('.transcript-content');
        if (transcriptContent) {
            transcriptContent.setAttribute('aria-live', 'polite');
            transcriptContent.setAttribute('aria-label', 'Live transcription text');
        }
        
        const statusIndicator = document.querySelector('.status-text');
        if (statusIndicator) {
            statusIndicator.setAttribute('aria-live', 'polite');
            statusIndicator.setAttribute('role', 'status');
        }
        
        // Add descriptive labels to all interactive elements
        const recordButton = document.getElementById('recordButton');
        if (recordButton) {
            recordButton.setAttribute('aria-describedby', 'record-button-description');
            
            const description = document.createElement('div');
            description.id = 'record-button-description';
            description.className = 'sr-only';
            description.textContent = 'Start recording audio for real-time transcription. Use Ctrl+R as keyboard shortcut.';
            recordButton.appendChild(description);
        }
    }
    
    setupReducedMotionSupport() {
        // Respect user's motion preferences
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        
        if (prefersReducedMotion) {
            this.visualTheme.animations = false;
            this.animationState.typewriterSpeed = 1; // Instant
            this.animationState.fadeTransitionSpeed = 1; // Instant
        }
    }
    
    setupHighContrastSupport() {
        // High contrast mode support
        const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches;
        
        if (prefersHighContrast) {
            this.visualTheme.highContrast = true;
            document.body.classList.add('high-contrast');
        }
    }
    
    setupResponsiveDesign() {
        // Responsive layout adjustments
        const handleResize = () => {
            const width = window.innerWidth;
            
            if (width <= 768) {
                document.body.classList.add('mobile-layout');
                this.adjustMobileLayout();
            } else {
                document.body.classList.remove('mobile-layout');
                this.adjustDesktopLayout();
            }
        };
        
        window.addEventListener('resize', handleResize);
        handleResize(); // Initial call
    }
    
    adjustMobileLayout() {
        // Mobile-specific UI adjustments
        const qualityPanel = this.uiElements.qualityIndicators;
        if (qualityPanel) {
            qualityPanel.style.position = 'relative';
            qualityPanel.style.top = 'auto';
            qualityPanel.style.right = 'auto';
            qualityPanel.style.width = '100%';
            qualityPanel.style.marginTop = '20px';
        }
    }
    
    adjustDesktopLayout() {
        // Desktop-specific UI adjustments
        const qualityPanel = this.uiElements.qualityIndicators;
        if (qualityPanel) {
            qualityPanel.style.position = 'fixed';
            qualityPanel.style.top = '20px';
            qualityPanel.style.right = '20px';
            qualityPanel.style.width = '320px';
            qualityPanel.style.marginTop = '0';
        }
    }
    
    setupControlHandlers() {
        // Control button event handlers
        const recordButton = document.getElementById('recordButton');
        const stopButton = document.getElementById('stopButton');
        const themeToggle = document.querySelector('.theme-toggle');
        const exportButton = document.querySelector('.export-button');
        
        if (recordButton) {
            recordButton.addEventListener('click', () => this.toggleRecording());
        }
        
        if (stopButton) {
            stopButton.addEventListener('click', () => this.stopRecording());
        }
        
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleDarkMode());
        }
        
        if (exportButton) {
            exportButton.addEventListener('click', () => this.exportTranscript());
        }
        
        // Quality metrics toggle
        const metricsToggle = document.querySelector('.metrics-toggle');
        if (metricsToggle) {
            metricsToggle.addEventListener('click', () => this.toggleQualityMetrics());
        }
    }
    
    initializePerformanceChart() {
        // Initialize performance chart using Canvas
        const canvas = document.getElementById('performanceChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        this.performanceChart = {
            canvas: canvas,
            ctx: ctx,
            data: [],
            maxDataPoints: 50
        };
        
        this.drawPerformanceChart();
    }
    
    drawPerformanceChart() {
        const chart = this.performanceChart;
        if (!chart || !chart.ctx) return;
        
        const { canvas, ctx, data } = chart;
        const width = canvas.width;
        const height = canvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Draw grid
        ctx.strokeStyle = getComputedStyle(document.documentElement)
            .getPropertyValue('--border-color') || '#dadce0';
        ctx.lineWidth = 1;
        
        // Horizontal grid lines
        for (let i = 0; i <= 4; i++) {
            const y = (height / 4) * i;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }
        
        // Draw performance data
        if (data.length > 1) {
            ctx.strokeStyle = '#34a853';
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            data.forEach((point, index) => {
                const x = (width / (data.length - 1)) * index;
                const y = height - (height * (point / 100)); // Assuming 0-100 scale
                
                if (index === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });
            
            ctx.stroke();
        }
    }
    
    // Public methods for updating UI state
    updateInterimText(text, confidence = 0.9) {
        if (!this.isActive) return;
        
        const interimElement = document.getElementById('interimText');
        if (!interimElement) return;
        
        this.textStates.interim = text;
        
        if (this.visualTheme.animations) {
            this.textUpdateHandler.fadeTransition(interimElement, text, 100);
        } else {
            interimElement.textContent = text;
        }
        
        // Update confidence styling
        this.updateConfidenceDisplay(confidence);
    }
    
    updateFinalText(text, confidence = 0.9) {
        if (!this.isActive) return;
        
        const finalContainer = document.getElementById('finalTextContainer');
        if (!finalContainer) return;
        
        this.textStates.final += text;
        
        // Clear interim text
        const interimElement = document.getElementById('interimText');
        if (interimElement) {
            interimElement.textContent = '';
        }
        
        // Add final text with animation
        if (this.visualTheme.animations) {
            this.textUpdateHandler.slideIn(finalContainer, text);
        } else {
            const span = document.createElement('span');
            span.className = 'final-text-segment';
            span.textContent = text + ' ';
            finalContainer.appendChild(span);
        }
        
        this.updateWordCount();
        this.updateConfidenceDisplay(confidence);
    }
    
    updateStatus(status, message) {
        const statusText = document.querySelector('.status-text');
        const pulseDot = document.querySelector('.pulse-dot');
        
        if (statusText) {
            statusText.textContent = message;
        }
        
        if (pulseDot) {
            pulseDot.className = `pulse-dot ${status}`;
        }
    }
    
    updateQualityMetrics(metrics) {
        // Update individual metric displays
        Object.entries(metrics).forEach(([key, value]) => {
            const element = document.querySelector(`[data-metric="${key}"]`);
            if (element) {
                if (key === 'latency') {
                    element.textContent = `${Math.round(value)}ms`;
                } else if (typeof value === 'number') {
                    element.textContent = `${Math.round(value)}%`;
                } else {
                    element.textContent = value;
                }
                
                // Update styling based on value
                this.updateMetricStyling(element, value);
            }
        });
        
        // Update performance chart
        if (metrics.overall && this.performanceChart) {
            this.performanceChart.data.push(metrics.overall);
            
            if (this.performanceChart.data.length > this.performanceChart.maxDataPoints) {
                this.performanceChart.data.shift();
            }
            
            this.drawPerformanceChart();
        }
    }
    
    updateMetricStyling(element, value) {
        // Apply color coding based on metric value
        element.classList.remove('metric-excellent', 'metric-good', 'metric-warning', 'metric-poor');
        
        if (typeof value === 'number') {
            if (value >= 90) {
                element.classList.add('metric-excellent');
            } else if (value >= 75) {
                element.classList.add('metric-good');
            } else if (value >= 50) {
                element.classList.add('metric-warning');
            } else {
                element.classList.add('metric-poor');
            }
        }
    }
    
    updateConfidenceDisplay(confidence) {
        const confidenceFill = document.querySelector('.confidence-fill');
        const confidenceText = document.querySelector('.confidence-text');
        
        if (confidenceFill) {
            confidenceFill.style.width = `${confidence * 100}%`;
        }
        
        if (confidenceText) {
            confidenceText.textContent = `${Math.round(confidence * 100)}%`;
        }
    }
    
    updateWordCount() {
        const wordCountElement = document.querySelector('.word-count');
        if (wordCountElement) {
            const words = this.textStates.final.split(/\s+/).filter(word => word.length > 0);
            wordCountElement.textContent = `${words.length} words`;
        }
    }
    
    // Control methods
    toggleRecording() {
        // This would integrate with the existing recording system
        if (window.minaTranscriptionFix) {
            if (window.minaTranscriptionFix.isRecording) {
                this.stopRecording();
            } else {
                this.startRecording();
            }
        }
    }
    
    startRecording() {
        this.updateStatus('recording', 'Recording...');
        
        const recordButton = document.getElementById('recordButton');
        const stopButton = document.getElementById('stopButton');
        
        if (recordButton && stopButton) {
            recordButton.disabled = true;
            stopButton.disabled = false;
            recordButton.style.background = '#9aa0a6';
            stopButton.style.background = '#ea4335';
        }
        
        // Start actual recording
        if (window.minaTranscriptionFix) {
            window.minaTranscriptionFix.startRecording();
        }
    }
    
    stopRecording() {
        this.updateStatus('stopped', 'Recording stopped');
        
        const recordButton = document.getElementById('recordButton');
        const stopButton = document.getElementById('stopButton');
        
        if (recordButton && stopButton) {
            recordButton.disabled = false;
            stopButton.disabled = true;
            recordButton.style.background = '#34a853';
            stopButton.style.background = '#9aa0a6';
        }
        
        // Stop actual recording
        if (window.minaTranscriptionFix) {
            window.minaTranscriptionFix.stopRecording();
        }
    }
    
    toggleDarkMode() {
        this.visualTheme.darkMode = !this.visualTheme.darkMode;
        
        if (this.visualTheme.darkMode) {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
        }
        
        // Save preference
        localStorage.setItem('mina-theme', this.visualTheme.darkMode ? 'dark' : 'light');
    }
    
    toggleQualityMetrics() {
        const panel = this.uiElements.qualityIndicators;
        const toggle = document.querySelector('.metrics-toggle');
        
        if (panel && toggle) {
            const isHidden = panel.style.display === 'none';
            panel.style.display = isHidden ? 'block' : 'none';
            toggle.textContent = isHidden ? 'Hide' : 'Show';
        }
    }
    
    exportTranscript() {
        const transcript = this.textStates.final.trim();
        
        if (!transcript) {
            alert('No transcript to export');
            return;
        }
        
        // Create and download transcript file
        const blob = new Blob([transcript], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `transcript-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    setupUITheme() {
        // Load saved theme preference
        const savedTheme = localStorage.getItem('mina-theme');
        if (savedTheme) {
            this.visualTheme.darkMode = savedTheme === 'dark';
            document.documentElement.setAttribute('data-theme', savedTheme);
        }
    }
    
    stop() {
        this.isActive = false;
        console.log('🛑 Google Recorder UI system stopped');
    }
}

// Export for global use
window.GoogleRecorderUISystem = GoogleRecorderUISystem;