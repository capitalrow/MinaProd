/**
 * MINA UI/UX Enhancement Plan
 * Comprehensive frontend improvements for live transcription experience
 */

// 1. ENHANCED ERROR STATE MANAGEMENT
const ErrorStates = {
    MIC_DENIED: 'microphone_access_denied',
    WS_DISCONNECTED: 'websocket_disconnected', 
    API_KEY_MISSING: 'openai_key_missing',
    SESSION_FAILED: 'session_creation_failed',
    TRANSCRIPTION_ERROR: 'transcription_service_error'
};

// 2. COMPREHENSIVE UI STATE MACHINE
class TranscriptionUIManager {
    constructor() {
        this.currentState = 'IDLE';
        this.stateTransitions = {
            'IDLE': ['CONNECTING', 'ERROR'],
            'CONNECTING': ['RECORDING', 'ERROR', 'IDLE'],
            'RECORDING': ['STOPPING', 'ERROR', 'IDLE'],
            'STOPPING': ['IDLE', 'ERROR'],
            'ERROR': ['IDLE']
        };
        this.setupEventHandlers();
        this.setupAccessibility();
    }

    // State transition with validation
    setState(newState, context = {}) {
        if (!this.stateTransitions[this.currentState].includes(newState)) {
            console.warn(`Invalid transition: ${this.currentState} -> ${newState}`);
            return;
        }
        
        this.currentState = newState;
        this.updateUI(newState, context);
        this.announceToScreenReader(newState, context);
    }

    // Enhanced UI updates with animations
    updateUI(state, context) {
        const elements = {
            startBtn: document.getElementById('startRecording'),
            stopBtn: document.getElementById('stopRecording'), 
            status: document.getElementById('connectionStatus'),
            transcript: document.getElementById('finalText'),
            interim: document.getElementById('interimText'),
            errorPanel: document.getElementById('errorPanel')
        };

        // State-specific UI updates
        switch(state) {
            case 'IDLE':
                elements.startBtn.disabled = false;
                elements.stopBtn.disabled = true;
                elements.status.textContent = 'Ready';
                elements.status.className = 'status-ready';
                this.hideError();
                break;
                
            case 'CONNECTING':
                elements.startBtn.disabled = true;
                elements.status.textContent = 'Connecting...';
                elements.status.className = 'status-connecting pulse-animation';
                break;
                
            case 'RECORDING':
                elements.startBtn.disabled = true;
                elements.stopBtn.disabled = false;
                elements.status.textContent = 'Recording';
                elements.status.className = 'status-recording recording-pulse';
                break;
                
            case 'ERROR':
                elements.startBtn.disabled = false;
                elements.stopBtn.disabled = true;
                this.showError(context.error, context.errorType);
                break;
        }
    }

    // Accessible error display
    showError(message, type) {
        const errorPanel = document.getElementById('errorPanel');
        const errorMessage = document.getElementById('errorMessage');
        
        errorPanel.className = `error-panel visible ${type}`;
        errorMessage.textContent = message;
        errorPanel.setAttribute('role', 'alert');
        errorPanel.setAttribute('aria-live', 'assertive');
        
        // Auto-hide after 10 seconds for non-critical errors
        if (type !== ErrorStates.MIC_DENIED) {
            setTimeout(() => this.hideError(), 10000);
        }
    }

    hideError() {
        const errorPanel = document.getElementById('errorPanel');
        errorPanel.className = 'error-panel hidden';
    }

    // Screen reader accessibility
    announceToScreenReader(state, context) {
        const announcement = document.getElementById('sr-announcements');
        let message = '';
        
        switch(state) {
            case 'RECORDING':
                message = 'Recording started. Speak now for live transcription.';
                break;
            case 'STOPPING':
                message = 'Recording stopped. Processing final transcription.';
                break;
            case 'ERROR':
                message = `Error: ${context.error}`;
                break;
        }
        
        if (message) {
            announcement.textContent = message;
        }
    }

    // Enhanced event handlers with retry logic
    setupEventHandlers() {
        // Microphone permission handling
        navigator.permissions?.query?.({name: 'microphone'})
            .then(permission => {
                if (permission.state === 'denied') {
                    this.setState('ERROR', {
                        error: 'Microphone access denied. Please enable microphone permission and refresh the page.',
                        errorType: ErrorStates.MIC_DENIED
                    });
                }
            })
            .catch(err => console.warn('Permission query failed:', err));
    }

    // WCAG AA+ accessibility setup
    setupAccessibility() {
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                const activeElement = document.activeElement;
                if (activeElement.id === 'startRecording' && !activeElement.disabled) {
                    e.preventDefault();
                    activeElement.click();
                }
            }
        });

        // Focus management
        const focusableElements = 'button, input, select, textarea, [tabindex]:not([tabindex="-1"])';
        const focusableContent = document.querySelectorAll(focusableElements);
        
        // Trap focus within modal dialogs
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const firstElement = focusableContent[0];
                const lastElement = focusableContent[focusableContent.length - 1];
                
                if (e.shiftKey && document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                } else if (!e.shiftKey && document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        });
    }
}

// 3. ENHANCED WEBSOCKET MANAGEMENT
class RobustWebSocketManager {
    constructor(url, options = {}) {
        this.url = url;
        this.options = {
            maxRetries: 5,
            retryDelay: 1000,
            backoffMultiplier: 2,
            maxRetryDelay: 30000,
            ...options
        };
        this.retryCount = 0;
        this.isIntentionallyClosed = false;
    }

    connect() {
        return new Promise((resolve, reject) => {
            try {
                this.socket = io(this.url, {
                    transports: ['websocket', 'polling'],
                    timeout: 5000,
                    forceNew: true
                });

                this.socket.on('connect', () => {
                    this.retryCount = 0;
                    resolve(this.socket);
                });

                this.socket.on('disconnect', (reason) => {
                    if (!this.isIntentionallyClosed && reason === 'io server disconnect') {
                        this.attemptReconnect();
                    }
                });

                this.socket.on('connect_error', (error) => {
                    if (this.retryCount === 0) {
                        reject(error);
                    }
                    this.attemptReconnect();
                });

            } catch (error) {
                reject(error);
            }
        });
    }

    attemptReconnect() {
        if (this.retryCount >= this.options.maxRetries) {
            console.error('Max reconnection attempts reached');
            return;
        }

        const delay = Math.min(
            this.options.retryDelay * Math.pow(this.options.backoffMultiplier, this.retryCount),
            this.options.maxRetryDelay
        );

        this.retryCount++;
        
        setTimeout(() => {
            console.log(`Reconnection attempt ${this.retryCount}/${this.options.maxRetries}`);
            this.connect().catch(err => console.warn('Reconnection failed:', err));
        }, delay);
    }

    disconnect() {
        this.isIntentionallyClosed = true;
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// 4. MOBILE-OPTIMIZED AUDIO HANDLING
class MobileAudioManager {
    static async requestPermission() {
        try {
            // iOS Safari specific handling
            if (this.isIOSSafari()) {
                await this.iosPermissionRequest();
            }

            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000
                }
            });

            return stream;
        } catch (error) {
            throw new Error(`Microphone access failed: ${error.message}`);
        }
    }

    static isIOSSafari() {
        const ua = navigator.userAgent;
        return /iPad|iPhone|iPod/.test(ua) && /Safari/.test(ua) && !/Chrome/.test(ua);
    }

    static async iosPermissionRequest() {
        // iOS requires user gesture to request microphone
        return new Promise((resolve, reject) => {
            const button = document.createElement('button');
            button.textContent = 'Enable Microphone';
            button.style.cssText = `
                position: fixed; top: 50%; left: 50%; 
                transform: translate(-50%, -50%);
                padding: 15px 30px; font-size: 18px;
                background: #007AFF; color: white; border: none; border-radius: 8px;
                z-index: 10000;
            `;

            button.onclick = async () => {
                try {
                    document.body.removeChild(button);
                    resolve();
                } catch (err) {
                    reject(err);
                }
            };

            document.body.appendChild(button);
        });
    }
}

// 5. REAL-TIME PERFORMANCE MONITORING
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            audioLatency: [],
            transcriptionLatency: [],
            uiUpdateLatency: [],
            errorRate: 0,
            totalRequests: 0
        };
    }

    recordAudioLatency(startTime, endTime) {
        const latency = endTime - startTime;
        this.metrics.audioLatency.push(latency);
        
        // Keep only last 100 measurements
        if (this.metrics.audioLatency.length > 100) {
            this.metrics.audioLatency.shift();
        }
    }

    getAverageLatency() {
        if (this.metrics.audioLatency.length === 0) return 0;
        const sum = this.metrics.audioLatency.reduce((a, b) => a + b, 0);
        return sum / this.metrics.audioLatency.length;
    }

    recordError() {
        this.metrics.errorRate++;
    }

    getErrorRate() {
        if (this.metrics.totalRequests === 0) return 0;
        return this.metrics.errorRate / this.metrics.totalRequests;
    }

    generateReport() {
        return {
            avgAudioLatency: this.getAverageLatency(),
            errorRate: this.getErrorRate(),
            totalRequests: this.metrics.totalRequests,
            timestamp: new Date().toISOString()
        };
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        TranscriptionUIManager,
        RobustWebSocketManager,
        MobileAudioManager,
        PerformanceMonitor,
        ErrorStates
    };
}