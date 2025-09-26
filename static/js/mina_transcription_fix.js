/**
 * MINA TRANSCRIPTION SYSTEM FIX
 * Complete integration of all fixes with HTTP fallback
 */

class MinaTranscriptionFix {
    constructor() {
        this.isInitialized = false;
        this.transcriptionMode = 'auto'; // auto, websocket, http
        this.activeTranscription = null;
        this.statusFixer = null;
        this.currentSession = null;
        
        // System state
        this.isRecording = false;
        this.recordingStartTime = null;
        this.stats = {
            totalWords: 0,
            totalChunks: 0,
            averageLatency: 0,
            accuracy: 90
        };
        
        // UI elements cache
        this.uiElements = {};
        this.statusUpdateInterval = null;
    }
    
    async initialize() {
        if (this.isInitialized) return true;
        
        console.log('🚀 Initializing MINA Transcription Fix System');
        
        try {
            // Initialize status fixer first
            this.initializeStatusFixer();
            
            // Cache UI elements
            this.cacheUIElements();
            
            // Initialize transcription system
            await this.initializeTranscription();
            
            // Set up UI event handlers
            this.setupEventHandlers();
            
            // Start monitoring
            this.startStatusMonitoring();
            
            this.isInitialized = true;
            this.updateStatus('ready', 'Transcription system ready');
            
            console.log('✅ MINA Transcription Fix System initialized');
            return true;
            
        } catch (error) {
            console.error('❌ Failed to initialize transcription system:', error);
            this.updateStatus('error', 'Initialization failed');
            return false;
        }
    }
    
    initializeStatusFixer() {
        // Use global status fixer if available
        if (window.statusFixer) {
            this.statusFixer = window.statusFixer;
            console.log('✅ Using existing status fixer');
        } else if (window.StatusDisplayFixer) {
            this.statusFixer = new window.StatusDisplayFixer();
            this.statusFixer.initialize();
            console.log('✅ Created new status fixer');
        } else {
            console.warn('⚠️ Status fixer not available');
        }
    }
    
    cacheUIElements() {
        const elementIds = [
            'recordBtn', 'stopBtn', 'pauseBtn',
            'statusText', 'statusDot',
            'sessionTime', 'wordCount', 'confidenceScore',
            'chunksProcessed', 'latencyMs', 'qualityScore',
            'transcriptDisplay', 'liveTranscript'
        ];
        
        elementIds.forEach(id => {
            this.uiElements[id] = document.getElementById(id);
        });
        
        console.log(`📊 Cached ${Object.keys(this.uiElements).filter(k => this.uiElements[k]).length} UI elements`);
    }
    
    async initializeTranscription() {
        console.log('🔄 Detecting transcription method...');
        
        // Try WebSocket first
        if (await this.testWebSocketConnection()) {
            console.log('✅ WebSocket connection available');
            this.transcriptionMode = 'websocket';
            // Initialize WebSocket transcription if available
            await this.initializeWebSocketTranscription();
        } else {
            console.log('⚠️ WebSocket not available, using HTTP fallback');
            this.transcriptionMode = 'http';
            await this.initializeHttpTranscription();
        }
    }
    
    async testWebSocketConnection() {
        return new Promise((resolve) => {
            try {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/socket.io/?transport=websocket`;
                
                const ws = new WebSocket(wsUrl);
                
                ws.onopen = () => {
                    ws.close();
                    resolve(true);
                };
                
                ws.onerror = () => {
                    resolve(false);
                };
                
                ws.onclose = () => {
                    resolve(false);
                };
                
                // Timeout after 2 seconds
                setTimeout(() => {
                    ws.close();
                    resolve(false);
                }, 2000);
                
            } catch (error) {
                resolve(false);
            }
        });
    }
    
    async initializeWebSocketTranscription() {
        // Try to use existing WebSocket transcription systems
        const systems = [
            'fixedTranscription',
            'minaTranscription', 
            'transcriptionSystem',
            'FixedMinaTranscription'
        ];
        
        for (const systemName of systems) {
            if (window[systemName] && typeof window[systemName] === 'object') {
                this.activeTranscription = window[systemName];
                console.log(`✅ Using existing ${systemName}`);
                return;
            }
        }
        
        console.log('⚠️ No WebSocket transcription system found, falling back to HTTP');
        this.transcriptionMode = 'http';
        await this.initializeHttpTranscription();
    }
    
    async initializeHttpTranscription() {
        if (window.HttpTranscriptionFallback) {
            this.activeTranscription = new window.HttpTranscriptionFallback();
            
            // Set up callbacks
            this.activeTranscription.onStatusUpdate = (status, message) => {
                this.updateStatus(status, message);
            };
            
            this.activeTranscription.onTranscriptionResult = (result) => {
                this.handleTranscriptionResult(result);
            };
            
            this.activeTranscription.onStatsUpdate = (stats) => {
                this.updateStats(stats);
            };
            
            this.activeTranscription.onError = (error) => {
                this.handleError(error);
            };
            
            await this.activeTranscription.initialize();
            console.log('✅ HTTP transcription initialized');
        } else {
            throw new Error('HTTP transcription fallback not available');
        }
    }
    
    setupEventHandlers() {
        // Record button
        if (this.uiElements.recordBtn) {
            this.uiElements.recordBtn.addEventListener('click', () => {
                this.startRecording();
            });
        }
        
        // Stop button  
        if (this.uiElements.stopBtn) {
            this.uiElements.stopBtn.addEventListener('click', () => {
                this.stopRecording();
            });
        }
        
        // Also try to find buttons by class
        const recordButtons = document.querySelectorAll('.record-btn, [data-action="start-recording"]');
        recordButtons.forEach(btn => {
            btn.addEventListener('click', () => this.startRecording());
        });
        
        const stopButtons = document.querySelectorAll('.stop-btn, [data-action="stop-recording"]');
        stopButtons.forEach(btn => {
            btn.addEventListener('click', () => this.stopRecording());
        });
        
        console.log('🎛️ Event handlers set up');
    }
    
    startStatusMonitoring() {
        // Update UI every 500ms while recording
        this.statusUpdateInterval = setInterval(() => {
            if (this.isRecording) {
                this.updateSessionTimer();
                this.updateUIMetrics();
            }
            
            // Apply status fixes
            if (this.statusFixer) {
                this.statusFixer.fixNow();
            }
        }, 500);
    }
    
    async startRecording() {
        if (this.isRecording) {
            console.log('⚠️ Recording already in progress');
            return false;
        }
        
        console.log('🎙️ Starting recording...');
        this.recordingStartTime = Date.now();
        this.isRecording = true;
        
        try {
            if (this.activeTranscription && this.activeTranscription.startRecording) {
                const success = await this.activeTranscription.startRecording();
                
                if (success) {
                    this.updateStatus('recording', 'Recording active');
                    this.updateRecordingButtons(true);
                    return true;
                } else {
                    this.isRecording = false;
                    this.updateStatus('error', 'Failed to start recording');
                    return false;
                }
            } else {
                this.isRecording = false;
                this.updateStatus('error', 'No transcription system available');
                return false;
            }
            
        } catch (error) {
            console.error('❌ Recording start error:', error);
            this.isRecording = false;
            this.updateStatus('error', 'Recording error');
            this.handleError(error);
            return false;
        }
    }
    
    async stopRecording() {
        if (!this.isRecording) {
            console.log('⚠️ Not currently recording');
            return false;
        }
        
        console.log('⏹️ Stopping recording...');
        this.isRecording = false;
        
        try {
            if (this.activeTranscription && this.activeTranscription.stopRecording) {
                await this.activeTranscription.stopRecording();
            }
            
            this.updateStatus('processing', 'Processing final audio');
            this.updateRecordingButtons(false);
            
            // After a delay, show ready status
            setTimeout(() => {
                this.updateStatus('ready', 'Recording complete');
            }, 2000);
            
            return true;
            
        } catch (error) {
            console.error('❌ Recording stop error:', error);
            this.updateStatus('error', 'Stop recording error');
            this.handleError(error);
            return false;
        }
    }
    
    updateStatus(status, message) {
        console.log(`📊 Status: ${status} - ${message}`);
        
        // Update status text
        if (this.uiElements.statusText) {
            this.uiElements.statusText.textContent = message;
        }
        
        // Update status dot
        if (this.uiElements.statusDot) {
            this.uiElements.statusDot.className = `status-dot ${status}`;
        }
        
        // Update all status elements on page
        const statusElements = document.querySelectorAll('.status-text, [data-status]');
        statusElements.forEach(el => {
            el.textContent = message;
            el.className = el.className.replace(/status-\\w+/g, '') + ` status-${status}`;
        });
    }
    
    updateRecordingButtons(isRecording) {
        // Update record button
        if (this.uiElements.recordBtn) {
            this.uiElements.recordBtn.disabled = isRecording;
            this.uiElements.recordBtn.classList.toggle('recording', isRecording);
        }
        
        // Update stop button
        if (this.uiElements.stopBtn) {
            this.uiElements.stopBtn.disabled = !isRecording;
        }
        
        // Update all recording buttons on page
        const recordBtns = document.querySelectorAll('.record-btn, [data-action="start-recording"]');
        recordBtns.forEach(btn => {
            btn.disabled = isRecording;
            btn.classList.toggle('recording', isRecording);
        });
        
        const stopBtns = document.querySelectorAll('.stop-btn, [data-action="stop-recording"]');
        stopBtns.forEach(btn => {
            btn.disabled = !isRecording;
        });
    }
    
    updateSessionTimer() {
        if (!this.recordingStartTime) return;
        
        const elapsed = Date.now() - this.recordingStartTime;
        const minutes = Math.floor(elapsed / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        if (this.uiElements.sessionTime) {
            this.uiElements.sessionTime.textContent = timeString;
        }
        
        // Update all duration displays
        const durationElements = document.querySelectorAll('[data-metric="duration"], .duration-display');
        durationElements.forEach(el => {
            el.textContent = timeString;
        });
    }
    
    updateUIMetrics() {
        // Update cached metrics
        const metrics = {
            words: this.stats.totalWords,
            chunks: this.stats.totalChunks,
            latency: this.stats.averageLatency,
            accuracy: this.stats.accuracy,
            quality: Math.min(100, this.stats.accuracy + 5) // Simple quality calculation
        };
        
        // Update UI elements
        if (this.uiElements.wordCount) this.uiElements.wordCount.textContent = metrics.words;
        if (this.uiElements.confidenceScore) this.uiElements.confidenceScore.textContent = `${metrics.accuracy}%`;
        if (this.uiElements.chunksProcessed) this.uiElements.chunksProcessed.textContent = metrics.chunks;
        if (this.uiElements.latencyMs) this.uiElements.latencyMs.textContent = `${metrics.latency}ms`;
        if (this.uiElements.qualityScore) this.uiElements.qualityScore.textContent = `${metrics.quality}%`;
        
        // Update metric displays throughout the page
        Object.entries(metrics).forEach(([key, value]) => {
            const elements = document.querySelectorAll(`[data-metric="${key}"], .metric-${key}`);
            elements.forEach(el => {
                let displayValue = value;
                if (key === 'accuracy' || key === 'quality') {
                    displayValue = `${Math.round(value)}%`;
                } else if (key === 'latency') {
                    displayValue = `${Math.round(value)}ms`;
                }
                el.textContent = displayValue;
            });
        });
    }
    
    handleTranscriptionResult(result) {
        console.log('📝 Transcription result:', result.text);
        
        // Update stats
        if (result.text && result.text.trim()) {
            const words = result.text.trim().split(/\\s+/).length;
            this.stats.totalWords += words;
        }
        
        // CRITICAL FIX: Use dedicated transcript display
        if (window.transcriptDisplayFix && window.transcriptDisplayFix.isInitialized) {
            window.transcriptDisplayFix.displayTranscriptionResult(result);
            window.transcriptDisplayFix.updateLiveTranscriptElements(result);
        } else {
            this.displayTranscriptionFallback(result);
        }
        
    }
    
    displayTranscriptionFallback(result) {
        console.log('🔧 Using fallback transcript display');
        
        // Find any available transcript container
        const containers = [
            document.getElementById('transcriptContainer'),
            document.getElementById('transcript'),
            document.querySelector('.transcript-content'),
            document.querySelector('.transcription-container')
        ].filter(el => el);
        
        if (containers.length === 0) {
            console.error('❌ No transcript container found for fallback');
            return;
        }
        
        const container = containers[0];
        
        // Clear empty state
        const emptyState = container.querySelector('.transcript-empty');
        if (emptyState) {
            emptyState.style.display = 'none';
        }
        
        // Create transcript segment
        const segmentElement = document.createElement('div');
        segmentElement.className = `transcript-segment ${result.is_final ? 'final' : 'interim'}`;
        segmentElement.innerHTML = `
            <div class="transcript-header">
                <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                <span class="confidence">${Math.round((result.confidence || 0.9) * 100)}%</span>
            </div>
            <div class="text-content">${result.text}</div>
        `;
        
        // Handle interim vs final
        if (!result.is_final) {
            const existingInterim = container.querySelector('.transcript-segment.interim');
            if (existingInterim) {
                existingInterim.replaceWith(segmentElement);
            } else {
                container.appendChild(segmentElement);
            }
        } else {
            const existingInterim = container.querySelector('.transcript-segment.interim');
            if (existingInterim) {
                existingInterim.remove();
            }
            container.appendChild(segmentElement);
        }
        
        // Auto-scroll
        container.scrollTop = container.scrollHeight;
        
        console.log('✅ Fallback transcript displayed');
    }
    
    updateStats(stats) {
        Object.assign(this.stats, stats);
        this.updateUIMetrics();
    }
    
    handleError(error) {
        console.error('❌ Transcription system error:', error);
        
        const errorMsg = this.getErrorMessage(error);
        this.updateStatus('error', errorMsg);
        
        // Show error in UI
        const errorElements = document.querySelectorAll('.error-display, [data-error]');
        errorElements.forEach(el => {
            el.textContent = errorMsg;
            el.style.display = 'block';
        });
        
        // Auto-hide error after 5 seconds
        setTimeout(() => {
            errorElements.forEach(el => {
                el.style.display = 'none';
            });
            if (!this.isRecording) {
                this.updateStatus('ready', 'Ready');
            }
        }, 5000);
    }
    
    getErrorMessage(error) {
        const errorStr = error.toString().toLowerCase();
        
        if (errorStr.includes('permission') || errorStr.includes('notallowed')) {
            return 'Microphone access denied. Please allow microphone access.';
        } else if (errorStr.includes('notfound')) {
            return 'No microphone found. Please check your audio device.';
        } else if (errorStr.includes('network') || errorStr.includes('timeout')) {
            return 'Network error. Please check your connection.';
        } else if (errorStr.includes('websocket')) {
            return 'Connection error. Using backup mode.';
        } else {
            return 'Transcription error. Please try again.';
        }
    }
    
    // Public API
    getStats() {
        return { ...this.stats };
    }
    
    getStatus() {
        return {
            isRecording: this.isRecording,
            transcriptionMode: this.transcriptionMode,
            isInitialized: this.isInitialized,
            activeTranscription: !!this.activeTranscription
        };
    }
    
    cleanup() {
        if (this.statusUpdateInterval) {
            clearInterval(this.statusUpdateInterval);
        }
        
        if (this.activeTranscription && this.activeTranscription.cleanup) {
            this.activeTranscription.cleanup();
        }
    }
}

// Initialize the fixed transcription system
let minaTranscriptionFix = null;

document.addEventListener('DOMContentLoaded', async function() {
    console.log('🌟 Initializing MINA Transcription Fix');
    
    minaTranscriptionFix = new MinaTranscriptionFix();
    const success = await minaTranscriptionFix.initialize();
    
    if (success) {
        console.log('✅ MINA Transcription Fix ready');
        
        // Make available globally
        window.minaTranscriptionFix = minaTranscriptionFix;
        
        // Override global recording functions
        window.startRecording = () => minaTranscriptionFix.startRecording();
        window.stopRecording = () => minaTranscriptionFix.stopRecording();
        
    } else {
        console.error('❌ MINA Transcription Fix failed to initialize');
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (minaTranscriptionFix) {
        minaTranscriptionFix.cleanup();
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MinaTranscriptionFix };
}

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
