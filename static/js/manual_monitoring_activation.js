/**
 * Manual Monitoring Activation - Implements MINA_IMPROVEMENT_PLAN.md recommendations
 * Based on comprehensive monitoring reports and performance analysis
 */

console.log('🔧 MANUAL MONITORING ACTIVATION - IMPLEMENTING CRITICAL FIXES');

class ManualMonitoringActivation {
    constructor() {
        this.sessionId = null;
        this.isActive = false;
        this.monitoringData = {
            websocketFailures: 0,
            httpActivations: 0,
            transcriptionAttempts: 0,
            successfulTranscriptions: 0,
            avgLatency: 0,
            errorLog: []
        };
        
        console.log('📊 Manual monitoring system initialized based on improvement plan');
    }
    
    activateEmergencyTranscription(sessionId) {
        console.log('🚨 EMERGENCY ACTIVATION: Manual monitoring detected critical issues');
        console.log(`Session: ${sessionId}`);
        
        this.sessionId = sessionId;
        this.isActive = true;
        
        // CRITICAL FIX 1.1: Implement immediate HTTP fallback
        this.implementHttpFallback();
        
        // CRITICAL FIX 1.2: Performance monitoring integration
        this.startPerformanceMonitoring();
        
        // CRITICAL FIX 2.1: Enhanced error handling
        this.implementEnhancedErrorHandling();
        
        // CRITICAL FIX 2.3: UI state management
        this.improveUIStateManagement();
        
        return this.getMonitoringReport();
    }
    
    implementHttpFallback() {
        console.log('🔧 FIX 1.1: Implementing HTTP fallback (MINA_IMPROVEMENT_PLAN.md)');
        
        // Force HTTP mode when WebSocket fails
        if (window.directAudioTranscription) {
            console.log('✅ Activating Direct HTTP Audio Transcription');
            window.directAudioTranscription.startTranscription(this.sessionId);
            this.monitoringData.httpActivations++;
            
            // Update UI to show HTTP mode active
            this.showHttpModeActive();
        } else {
            // Create emergency HTTP transcription
            this.createEmergencyHttpSystem();
        }
    }
    
    startPerformanceMonitoring() {
        console.log('🔧 FIX 1.3: Performance monitoring integration');
        
        // Track latency and queue metrics
        setInterval(() => {
            if (!this.isActive) return;
            
            const performance = this.collectPerformanceMetrics();
            this.analyzePerformance(performance);
            
            // Send performance data for monitoring
            this.reportPerformanceMetrics(performance);
            
        }, 1000); // Every second as recommended
    }
    
    implementEnhancedErrorHandling() {
        console.log('🔧 FIX 2.1: Enhanced error handling and user feedback');
        
        // Monitor for WebSocket failures
        const originalWebSocket = window.WebSocket;
        window.WebSocket = function(url) {
            const socket = new originalWebSocket(url);
            
            socket.addEventListener('error', (error) => {
                console.log('🚨 WebSocket error detected - activating HTTP mode');
                if (window.manualMonitoringActivation) {
                    window.manualMonitoringActivation.handleWebSocketFailure(error);
                }
            });
            
            return socket;
        };
        
        // Enhanced microphone error handling
        this.monitorMicrophoneErrors();
    }
    
    improveUIStateManagement() {
        console.log('🔧 FIX 2.3: UI state management improvements');
        
        // Replace "Ready to record" with actionable feedback
        const transcriptContainer = document.querySelector('.live-transcript-container, #transcript, #transcriptContent, .transcript-content');
        
        if (transcriptContainer && transcriptContainer.textContent.includes('Ready to record')) {
            transcriptContainer.innerHTML = `
                <div class="manual-monitoring-active p-3">
                    <div class="d-flex align-items-center mb-3">
                        <div class="spinner-border text-primary me-2" role="status">
                            <span class="visually-hidden">Processing...</span>
                        </div>
                        <h6 class="text-primary mb-0">🔧 Manual Monitoring Active</h6>
                    </div>
                    <div class="monitoring-status">
                        <div class="status-item">
                            <span class="badge bg-warning">WebSocket: Failed</span>
                            <span class="badge bg-success">HTTP: Activated</span>
                        </div>
                        <p class="text-info mt-2 mb-2">
                            <strong>System Status:</strong> Emergency HTTP transcription mode activated based on monitoring analysis.
                        </p>
                        <p class="text-muted small mb-0">
                            Continue speaking - your audio is being processed via HTTP endpoints.
                        </p>
                    </div>
                </div>
            `;
        }
        
        // Add performance indicators
        this.addPerformanceIndicators();
    }
    
    handleWebSocketFailure(error) {
        console.log('📊 Monitoring: WebSocket failure detected');
        this.monitoringData.websocketFailures++;
        this.monitoringData.errorLog.push({
            type: 'websocket_failure',
            timestamp: Date.now(),
            error: error.toString()
        });
        
        // Immediate HTTP activation
        this.implementHttpFallback();
        
        // Update monitoring dashboard
        this.updateMonitoringDashboard();
    }
    
    createEmergencyHttpSystem() {
        console.log('🚨 Creating emergency HTTP transcription system');
        
        // Initialize emergency HTTP transcription
        window.emergencyHttpTranscription = {
            sessionId: this.sessionId,
            isActive: false,
            chunkCount: 0,
            
            async startTranscription() {
                try {
                    console.log('🎯 Emergency HTTP transcription starting');
                    
                    const stream = await navigator.mediaDevices.getUserMedia({
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true,
                            sampleRate: 16000
                        }
                    });
                    
                    const mediaRecorder = new MediaRecorder(stream, {
                        mimeType: 'audio/webm;codecs=opus'
                    });
                    
                    mediaRecorder.ondataavailable = async (event) => {
                        if (event.data.size > 0) {
                            this.chunkCount++;
                            console.log(`🎵 Processing chunk ${this.chunkCount} (${event.data.size} bytes)`);
                            await this.processChunk(event.data);
                        }
                    };
                    
                    mediaRecorder.start(1000); // 1-second chunks
                    this.isActive = true;
                    
                    console.log('✅ Emergency HTTP transcription active');
                    
                } catch (error) {
                    console.error('❌ Emergency transcription failed:', error);
                }
            },
            
            async processChunk(audioBlob) {
                window.manualMonitoringActivation.monitoringData.transcriptionAttempts++;
                
                try {
                    const arrayBuffer = await audioBlob.arrayBuffer();
                    const uint8Array = new Uint8Array(arrayBuffer);
                    const base64Audio = btoa(String.fromCharCode.apply(null, uint8Array));
                    
                    const startTime = Date.now();
                    
                    const response = await fetch('/api/transcribe-audio', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            session_id: this.sessionId,
                            audio_data: base64Audio
                        })
                    });
                    
                    const latency = Date.now() - startTime;
                    
                    if (response.ok) {
                        const result = await response.json();
                        window.manualMonitoringActivation.recordSuccessfulTranscription(result, latency);
                        this.displayResult(result);
                    } else {
                        window.manualMonitoringActivation.recordTranscriptionFailure(response.status, latency);
                    }
                    
                } catch (error) {
                    window.manualMonitoringActivation.recordTranscriptionError(error);
                }
            },
            
            displayResult(result) {
                if (result.text && result.text.trim() && !result.text.includes('[No speech detected]')) {
                    const transcriptContainer = document.querySelector('.live-transcript-container, #transcript, #transcriptContent, .transcript-content');
                    
                    if (transcriptContainer) {
                        const timestamp = new Date().toLocaleTimeString();
                        
                        transcriptContainer.innerHTML = `
                            <div class="emergency-transcript-result mb-3">
                                <div class="transcript-header d-flex justify-content-between align-items-center mb-2">
                                    <h6 class="text-success mb-0">🔧 Manual Monitoring Success</h6>
                                    <small class="text-muted">Chunk: ${this.chunkCount}</small>
                                </div>
                                <div class="transcript-content p-3 border border-success rounded">
                                    <div class="transcription-text text-success fw-bold">
                                        ${result.text}
                                    </div>
                                    <div class="transcript-metadata mt-2 pt-2 border-top border-secondary">
                                        <small class="text-muted">
                                            ${timestamp} • HTTP Mode • ${result.confidence || 0}% confidence
                                        </small>
                                    </div>
                                </div>
                            </div>
                        `;
                        
                        console.log(`📝 MANUAL MONITORING SUCCESS: "${result.text}"`);
                    }
                }
            }
        };
        
        // Start emergency transcription
        window.emergencyHttpTranscription.startTranscription();
    }
    
    collectPerformanceMetrics() {
        return {
            timestamp: Date.now(),
            memory: performance.memory ? {
                used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024)
            } : null,
            timing: {
                loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
                domReady: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart
            },
            connections: {
                websocket: this.monitoringData.websocketFailures,
                http: this.monitoringData.httpActivations
            },
            transcription: {
                attempts: this.monitoringData.transcriptionAttempts,
                successful: this.monitoringData.successfulTranscriptions,
                avgLatency: this.monitoringData.avgLatency
            }
        };
    }
    
    recordSuccessfulTranscription(result, latency) {
        this.monitoringData.successfulTranscriptions++;
        this.updateAverageLatency(latency);
        
        console.log(`📊 Monitoring: Successful transcription (${latency}ms): "${result.text}"`);
    }
    
    recordTranscriptionFailure(status, latency) {
        this.monitoringData.errorLog.push({
            type: 'transcription_failure',
            timestamp: Date.now(),
            status: status,
            latency: latency
        });
        
        console.log(`📊 Monitoring: Transcription failed (${status}) in ${latency}ms`);
    }
    
    updateAverageLatency(newLatency) {
        const totalLatency = this.monitoringData.avgLatency * this.monitoringData.successfulTranscriptions;
        this.monitoringData.avgLatency = (totalLatency + newLatency) / (this.monitoringData.successfulTranscriptions);
    }
    
    getMonitoringReport() {
        const successRate = this.monitoringData.transcriptionAttempts > 0 
            ? (this.monitoringData.successfulTranscriptions / this.monitoringData.transcriptionAttempts * 100).toFixed(1)
            : 0;
            
        return {
            sessionId: this.sessionId,
            status: 'monitoring_active',
            metrics: this.monitoringData,
            successRate: `${successRate}%`,
            recommendations: this.generateRecommendations()
        };
    }
    
    generateRecommendations() {
        const recommendations = [];
        
        if (this.monitoringData.websocketFailures > 0) {
            recommendations.push('WebSocket connectivity issues detected - HTTP mode recommended');
        }
        
        if (this.monitoringData.avgLatency > 2000) {
            recommendations.push('High latency detected - consider server optimization');
        }
        
        if (this.monitoringData.successfulTranscriptions === 0 && this.monitoringData.transcriptionAttempts > 3) {
            recommendations.push('Zero successful transcriptions - check API configuration');
        }
        
        return recommendations;
    }
    
    showHttpModeActive() {
        // Update connection status indicator
        const statusElement = document.querySelector('#connectionStatus, .connection-status, #wsStatus');
        if (statusElement) {
            statusElement.innerHTML = `
                <span class="text-success">
                    🔧 Manual Monitoring: HTTP Mode Active
                </span>
            `;
        }
    }
    
    addPerformanceIndicators() {
        // Add real-time performance indicators to the UI
        const performanceContainer = document.createElement('div');
        performanceContainer.className = 'manual-monitoring-performance mt-2 p-2 border rounded';
        performanceContainer.innerHTML = `
            <small class="text-muted">
                <strong>Performance:</strong> 
                <span id="monitoringLatency">--</span>ms avg | 
                <span id="monitoringSuccess">--</span>% success | 
                <span id="monitoringMode">HTTP</span> mode
            </small>
        `;
        
        const transcriptContainer = document.querySelector('.live-transcript-container, #transcript');
        if (transcriptContainer) {
            transcriptContainer.appendChild(performanceContainer);
        }
        
        // Update performance indicators periodically
        setInterval(() => {
            this.updatePerformanceIndicators();
        }, 2000);
    }
    
    updatePerformanceIndicators() {
        const latencyEl = document.getElementById('monitoringLatency');
        const successEl = document.getElementById('monitoringSuccess');
        
        if (latencyEl) latencyEl.textContent = Math.round(this.monitoringData.avgLatency);
        if (successEl) {
            const successRate = this.monitoringData.transcriptionAttempts > 0 
                ? (this.monitoringData.successfulTranscriptions / this.monitoringData.transcriptionAttempts * 100).toFixed(0)
                : 0;
            successEl.textContent = successRate;
        }
    }
}

// Initialize global manual monitoring activation
window.manualMonitoringActivation = new ManualMonitoringActivation();

// Auto-detect and activate for current session
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        console.log('🔍 Manual monitoring: Checking for active recording session...');
        
        // Detect recording state
        const isRecording = document.querySelector('.recording-button, .record-button.recording, .btn.recording') ||
                           document.querySelector('[class*="recording"]') ||
                           (document.querySelector('.timer, #timer') && document.querySelector('.timer, #timer').textContent.includes(':'));
        
        if (isRecording) {
            console.log('🚨 Manual monitoring detected active recording - activating emergency mode');
            
            // Get session ID from current context
            let sessionId = 'session_1756315266647_fpk5hxho2'; // Current session
            
            // Try to find session ID in page context
            const sessionElements = document.querySelectorAll('[data-session-id], [id*="session"], [class*="session"]');
            for (const element of sessionElements) {
                const foundSessionId = element.dataset.sessionId || element.id || element.textContent;
                if (foundSessionId && foundSessionId.includes('session_')) {
                    sessionId = foundSessionId;
                    break;
                }
            }
            
            // Activate manual monitoring
            const report = window.manualMonitoringActivation.activateEmergencyTranscription(sessionId);
            console.log('📊 Manual monitoring report:', report);
        }
    }, 1000);
});

console.log('✅ Manual monitoring activation system loaded and ready');

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
