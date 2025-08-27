/**
 * Automatic Session Testing - Client-side testing that starts with recording
 * Monitors JavaScript errors, WebSocket connectivity, and UI responsiveness
 */

class AutomaticSessionTesting {
    constructor() {
        this.isTestingActive = false;
        this.sessionId = null;
        this.testResults = {
            jsErrors: [],
            connectionEvents: [],
            uiResponsiveness: [],
            transcriptionEvents: []
        };
        this.startTime = null;
        
        // Initialize monitoring
        this.setupErrorMonitoring();
        this.setupConnectionMonitoring();
        this.setupUIMonitoring();
        
        console.info('🔍 Automatic session testing initialized');
    }
    
    startSessionTesting(sessionId) {
        """Start comprehensive testing when recording begins."""
        this.isTestingActive = true;
        this.sessionId = sessionId;
        this.startTime = Date.now();
        this.testResults = {
            jsErrors: [],
            connectionEvents: [],
            uiResponsiveness: [],
            transcriptionEvents: []
        };
        
        console.info(`🚀 Starting automatic testing for session: ${sessionId}`);
        
        // Start all test suites
        this.testWebSocketConnection();
        this.testAudioProcessing();
        this.testUIResponsiveness();
        this.monitorTranscriptionEvents();
        
        return {
            sessionId: this.sessionId,
            startTime: this.startTime,
            status: 'testing_started'
        };
    }
    
    setupErrorMonitoring() {
        """Monitor JavaScript errors during recording sessions."""
        
        // Override console.error to capture errors
        const originalError = console.error;
        console.error = (...args) => {
            if (this.isTestingActive) {
                this.testResults.jsErrors.push({
                    timestamp: Date.now(),
                    type: 'console_error',
                    message: args.join(' '),
                    stack: new Error().stack
                });
            }
            originalError.apply(console, args);
        };
        
        // Capture unhandled errors
        window.addEventListener('error', (event) => {
            if (this.isTestingActive) {
                this.testResults.jsErrors.push({
                    timestamp: Date.now(),
                    type: 'unhandled_error',
                    message: event.message,
                    filename: event.filename,
                    lineno: event.lineno,
                    colno: event.colno,
                    stack: event.error?.stack
                });
            }
        });
        
        // Capture unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            if (this.isTestingActive) {
                this.testResults.jsErrors.push({
                    timestamp: Date.now(),
                    type: 'unhandled_rejection',
                    reason: event.reason?.toString() || 'Unknown promise rejection',
                    stack: event.reason?.stack
                });
            }
        });
    }
    
    setupConnectionMonitoring() {
        """Monitor WebSocket connection events."""
        
        // Monitor socket events if available
        if (window.socket) {
            const monitorEvent = (eventName, level = 'info') => {
                window.socket.on(eventName, (data) => {
                    if (this.isTestingActive) {
                        this.testResults.connectionEvents.push({
                            timestamp: Date.now(),
                            event: eventName,
                            level: level,
                            data: data,
                            connected: window.socket.connected
                        });
                    }
                });
            };
            
            // Monitor key events
            monitorEvent('connect', 'success');
            monitorEvent('disconnect', 'warning');
            monitorEvent('error', 'error');
            monitorEvent('reconnect', 'info');
            monitorEvent('session_joined', 'success');
            monitorEvent('transcription_result', 'info');
        }
    }
    
    setupUIMonitoring() {
        """Monitor UI responsiveness and interactions."""
        
        // Monitor button clicks for responsiveness
        document.addEventListener('click', (event) => {
            if (this.isTestingActive && event.target.tagName === 'BUTTON') {
                const responseTime = this.measureResponseTime(event.target);
                this.testResults.uiResponsiveness.push({
                    timestamp: Date.now(),
                    element: event.target.id || event.target.className,
                    responseTime: responseTime,
                    type: 'button_click'
                });
            }
        });
    }
    
    testWebSocketConnection() {
        """Test WebSocket connection reliability."""
        
        const connectionTest = {
            timestamp: Date.now(),
            test: 'websocket_connection',
            status: 'running'
        };
        
        if (window.socket) {
            if (window.socket.connected) {
                connectionTest.status = 'passed';
                connectionTest.details = 'WebSocket connected successfully';
            } else {
                connectionTest.status = 'failed';
                connectionTest.details = 'WebSocket not connected';
            }
        } else {
            connectionTest.status = 'failed';
            connectionTest.details = 'WebSocket object not available';
        }
        
        this.testResults.connectionEvents.push(connectionTest);
        return connectionTest;
    }
    
    testAudioProcessing() {
        """Test audio processing components."""
        
        const audioTest = {
            timestamp: Date.now(),
            test: 'audio_processing',
            status: 'running'
        };
        
        try {
            // Check if MediaRecorder is available
            if (typeof MediaRecorder !== 'undefined') {
                audioTest.status = 'passed';
                audioTest.details = 'MediaRecorder API available';
            } else {
                audioTest.status = 'failed';
                audioTest.details = 'MediaRecorder API not available';
            }
            
            // Check for audio context
            if (window.AudioContext || window.webkitAudioContext) {
                audioTest.audioContext = 'available';
            } else {
                audioTest.audioContext = 'not_available';
                audioTest.status = 'failed';
            }
            
        } catch (error) {
            audioTest.status = 'failed';
            audioTest.details = `Audio processing test failed: ${error.message}`;
        }
        
        this.testResults.uiResponsiveness.push(audioTest);
        return audioTest;
    }
    
    testUIResponsiveness() {
        """Test UI element responsiveness."""
        
        const uiTest = {
            timestamp: Date.now(),
            test: 'ui_responsiveness',
            status: 'running'
        };
        
        try {
            // Test key UI elements
            const criticalElements = [
                'startRecordingBtn',
                'stopRecordingBtn', 
                'micStatus',
                'wsStatus'
            ];
            
            let elementsFound = 0;
            criticalElements.forEach(elementId => {
                if (document.getElementById(elementId)) {
                    elementsFound++;
                }
            });
            
            if (elementsFound === criticalElements.length) {
                uiTest.status = 'passed';
                uiTest.details = 'All critical UI elements found';
            } else {
                uiTest.status = 'warning';
                uiTest.details = `${elementsFound}/${criticalElements.length} critical elements found`;
            }
            
        } catch (error) {
            uiTest.status = 'failed';
            uiTest.details = `UI responsiveness test failed: ${error.message}`;
        }
        
        this.testResults.uiResponsiveness.push(uiTest);
        return uiTest;
    }
    
    monitorTranscriptionEvents() {
        """Monitor transcription events during recording."""
        
        if (window.socket) {
            window.socket.on('transcription_result', (data) => {
                if (this.isTestingActive) {
                    this.testResults.transcriptionEvents.push({
                        timestamp: Date.now(),
                        type: 'final_result',
                        text: data.text || '',
                        confidence: data.confidence || 0,
                        session_id: data.session_id
                    });
                }
            });
            
            window.socket.on('interim_result', (data) => {
                if (this.isTestingActive) {
                    this.testResults.transcriptionEvents.push({
                        timestamp: Date.now(),
                        type: 'interim_result',
                        text: data.text || '',
                        confidence: data.confidence || 0,
                        session_id: data.session_id
                    });
                }
            });
        }
    }
    
    measureResponseTime(element) {
        """Measure UI response time for interactions."""
        const startTime = performance.now();
        
        // Simulate measuring response time
        setTimeout(() => {
            const endTime = performance.now();
            return endTime - startTime;
        }, 0);
        
        return 0; // Placeholder for actual measurement
    }
    
    endSessionTesting() {
        """Complete testing and generate report."""
        if (!this.isTestingActive) {
            return null;
        }
        
        this.isTestingActive = false;
        const endTime = Date.now();
        const duration = endTime - this.startTime;
        
        // Calculate scores
        const totalJsErrors = this.testResults.jsErrors.length;
        const connectionSuccessRate = this.calculateConnectionSuccessRate();
        const uiResponsivenessScore = this.calculateUIScore();
        const transcriptionEventCount = this.testResults.transcriptionEvents.length;
        
        // Generate overall score
        let overallScore = 100;
        if (totalJsErrors > 0) overallScore -= (totalJsErrors * 10);
        if (connectionSuccessRate < 100) overallScore -= (100 - connectionSuccessRate);
        if (uiResponsivenessScore < 100) overallScore -= (100 - uiResponsivenessScore);
        if (transcriptionEventCount === 0) overallScore -= 50; // Major penalty for no transcription
        
        overallScore = Math.max(0, overallScore);
        
        const report = {
            sessionId: this.sessionId,
            duration: duration,
            overallScore: overallScore,
            jsErrors: totalJsErrors,
            connectionSuccessRate: connectionSuccessRate,
            uiResponsivenessScore: uiResponsivenessScore,
            transcriptionEvents: transcriptionEventCount,
            detailedResults: this.testResults,
            endTime: endTime,
            status: 'completed'
        };
        
        console.info(`✅ Automatic testing completed. Score: ${overallScore}%`, report);
        
        return report;
    }
    
    calculateConnectionSuccessRate() {
        """Calculate WebSocket connection success rate."""
        const connectionEvents = this.testResults.connectionEvents;
        if (connectionEvents.length === 0) return 0;
        
        const successEvents = connectionEvents.filter(event => 
            event.level === 'success' || event.event === 'connect'
        ).length;
        
        return (successEvents / connectionEvents.length) * 100;
    }
    
    calculateUIScore() {
        """Calculate UI responsiveness score."""
        const uiTests = this.testResults.uiResponsiveness;
        if (uiTests.length === 0) return 0;
        
        const passedTests = uiTests.filter(test => test.status === 'passed').length;
        return (passedTests / uiTests.length) * 100;
    }
    
    getCurrentStatus() {
        """Get current testing status."""
        if (!this.isTestingActive) {
            return { status: 'inactive' };
        }
        
        return {
            status: 'active',
            sessionId: this.sessionId,
            duration: Date.now() - this.startTime,
            jsErrors: this.testResults.jsErrors.length,
            connectionEvents: this.testResults.connectionEvents.length,
            transcriptionEvents: this.testResults.transcriptionEvents.length
        };
    }
}

// Initialize automatic testing
window.automaticSessionTesting = new AutomaticSessionTesting();

// Auto-start testing when recording begins
if (window.recordingStates) {
    const originalSetState = window.recordingStates.setState;
    window.recordingStates.setState = function(state, details) {
        // Call original setState
        originalSetState.call(this, state, details);
        
        // Start testing when recording begins
        if (state === 'recording' && window.automaticSessionTesting) {
            const sessionId = details?.sessionId || 'session_' + Date.now();
            window.automaticSessionTesting.startSessionTesting(sessionId);
        }
        
        // End testing when recording completes
        if (state === 'complete' && window.automaticSessionTesting) {
            const report = window.automaticSessionTesting.endSessionTesting();
            console.info('📊 Automatic testing report:', report);
        }
    };
}

console.info('🔍 Automatic session testing ready - will start with recording sessions');