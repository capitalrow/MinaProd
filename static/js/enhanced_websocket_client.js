/**
 * Enhanced WebSocket Client - Google Recorder Level Integration
 * Frontend client for the enhanced transcription service with <400ms latency.
 * Addresses Phase 0 frontend integration issues.
 */

class EnhancedWebSocketClient {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        // Session management
        this.sessionId = null;
        this.isRecording = false;
        
        // Audio processing
        this.mediaRecorder = null;
        this.audioStream = null;
        this.audioChunks = [];
        
        // Performance tracking
        this.metrics = {
            chunksProcessed: 0,
            totalLatency: 0,
            avgLatency: 0,
            lastChunkTime: 0
        };
        
        // UI elements cache
        this.elements = {
            transcriptDisplay: null,
            recordButton: null,
            statusDisplay: null,
            wordCounter: null,
            confidenceLevel: null
        };
        
        this.init();
    }
    
    init() {
        console.log('🎯 Enhanced WebSocket Client initializing...');
        this.cacheElements();
        this.setupEventListeners();
        this.getWebSocketInfo();
    }
    
    cacheElements() {
        // Cache frequently used DOM elements with fallback handling
        this.elements.transcriptDisplay = document.getElementById('transcriptDisplay') || 
                                         document.querySelector('.live-transcript-container') ||
                                         document.querySelector('[data-transcript-display]');
        
        this.elements.recordButton = document.getElementById('recordButton') ||
                                    document.querySelector('[data-record-button]');
        
        this.elements.statusDisplay = document.getElementById('recording-status') ||
                                     document.querySelector('[data-status-display]');
        
        this.elements.wordCounter = document.getElementById('wordCounter') ||
                                   document.querySelector('[data-word-counter]');
        
        this.elements.confidenceLevel = document.getElementById('confidenceLevel') ||
                                       document.querySelector('[data-confidence-level]');
        
        // 🔥 PHASE 0 FIX: Ensure transcript display exists
        if (!this.elements.transcriptDisplay) {
            console.warn('⚠️ No transcript display element found, creating fallback');
            this.createFallbackTranscriptDisplay();
        }
    }
    
    createFallbackTranscriptDisplay() {
        // Create fallback transcript display to prevent null element crashes
        const container = document.querySelector('.col-lg-8') || 
                         document.querySelector('main') || 
                         document.body;
        
        if (container) {
            const fallbackDiv = document.createElement('div');
            fallbackDiv.id = 'transcriptDisplay';
            fallbackDiv.className = 'card bg-secondary border-secondary';
            fallbackDiv.innerHTML = `
                <div class="card-header">
                    <h5 class="card-title mb-0">
                        <i class="bi bi-file-text"></i> Live Transcript
                    </h5>
                </div>
                <div class="card-body">
                    <div class="live-transcript-container" style="min-height: 300px; padding: 20px;">
                        <div class="text-muted text-center">
                            <i class="bi bi-mic-mute"></i>
                            <p>Click "Start Recording" to begin transcription...</p>
                        </div>
                    </div>
                </div>
            `;
            
            container.appendChild(fallbackDiv);
            this.elements.transcriptDisplay = fallbackDiv;
            
            console.log('✅ Fallback transcript display created');
        }
    }
    
    setupEventListeners() {
        // Record button
        if (this.elements.recordButton) {
            this.elements.recordButton.addEventListener('click', () => {
                if (this.isRecording) {
                    this.stopRecording();
                } else {
                    this.startRecording();
                }
            });
        }
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.isRecording) {
                console.log('🔄 Page hidden, maintaining connection...');
            } else if (!document.hidden && this.websocket && this.websocket.readyState !== WebSocket.OPEN) {
                console.log('🔄 Page visible, checking connection...');
                this.connect();
            }
        });
        
        // Handle before unload
        window.addEventListener('beforeunload', () => {
            if (this.isRecording) {
                this.stopRecording();
            }
            if (this.websocket) {
                this.disconnect();
            }
        });
    }
    
    async getWebSocketInfo() {
        try {
            const response = await fetch('/api/enhanced-ws/info');
            if (response.ok) {
                const data = await response.json();
                this.wsUrl = data.enhanced_websocket.url;
                console.log(`🌐 Enhanced WebSocket URL: ${this.wsUrl}`);
                
                // Show enhanced features in status
                this.updateStatus('Enhanced transcription ready (Google Recorder-level)', 'success');
            } else {
                throw new Error('Failed to get WebSocket info');
            }
        } catch (error) {
            console.error('❌ Failed to get WebSocket info:', error);
            this.updateStatus('Enhanced transcription unavailable', 'error');
        }
    }
    
    connect() {
        if (this.isConnected || (this.websocket && this.websocket.readyState === WebSocket.CONNECTING)) {
            return;
        }
        
        if (!this.wsUrl) {
            console.error('❌ WebSocket URL not available');
            this.updateStatus('Connection failed - URL not available', 'error');
            return;
        }
        
        try {
            console.log(`🔗 Connecting to Enhanced WebSocket: ${this.wsUrl}`);
            this.websocket = new WebSocket(this.wsUrl);
            
            this.websocket.onopen = (event) => {
                console.log('✅ Enhanced WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateStatus('Connected to enhanced transcription service', 'success');
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('❌ Failed to parse WebSocket message:', error);
                }
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ Enhanced WebSocket error:', error);
                this.updateStatus('Connection error', 'error');
            };
            
            this.websocket.onclose = (event) => {
                console.log('🔌 Enhanced WebSocket disconnected:', event);
                this.isConnected = false;
                
                if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.scheduleReconnect();
                } else {
                    this.updateStatus('Disconnected', 'warning');
                }
            };
            
        } catch (error) {
            console.error('❌ Failed to create WebSocket connection:', error);
            this.updateStatus('Connection failed', 'error');
        }
    }
    
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        this.isConnected = false;
        this.sessionId = null;
    }
    
    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`🔄 Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
        this.updateStatus(`Reconnecting in ${Math.ceil(delay/1000)}s... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`, 'warning');
        
        setTimeout(() => {
            if (!this.isConnected) {
                this.connect();
            }
        }, delay);
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'connection_ack':
                console.log('🤝 Connection acknowledged:', data);
                break;
                
            case 'session_started':
                console.log('🚀 Session started:', data.session_id);
                this.sessionId = data.session_id;
                this.updateStatus('Recording session active', 'recording');
                break;
                
            case 'transcription_result':
                this.handleTranscriptionResult(data);
                break;
                
            case 'session_ended':
                console.log('⏹️ Session ended:', data);
                this.sessionId = null;
                this.updateStatus('Session ended', 'success');
                break;
                
            case 'error':
                console.error('❌ Server error:', data);
                this.handleError(data);
                break;
                
            case 'pong':
                // Heartbeat response
                break;
                
            default:
                console.log('📨 Unknown message type:', data);
        }
    }
    
    handleTranscriptionResult(data) {
        const startTime = performance.now();
        
        try {
            // 🔥 PHASE 0 FIX: Safe transcript display update with null checks
            if (this.elements.transcriptDisplay) {
                const transcriptContainer = this.elements.transcriptDisplay.querySelector('.live-transcript-container') ||
                                           this.elements.transcriptDisplay.querySelector('.card-body') ||
                                           this.elements.transcriptDisplay;
                
                if (transcriptContainer) {
                    this.updateTranscriptDisplay(transcriptContainer, data);
                }
            }
            
            // Update metrics display
            this.updateMetricsDisplay(data);
            
            // Track performance
            this.updatePerformanceMetrics(data, startTime);
            
            // Log enhanced features
            if (data.context_correlation || data.interim_update) {
                console.log('🧠 Enhanced features active:', {
                    context_correlation: !!data.context_correlation,
                    interim_update: !!data.interim_update,
                    latency_ms: data.latency_ms
                });
            }
            
        } catch (error) {
            console.error('❌ Failed to handle transcription result:', error);
            // Don't throw - continue processing
        }
    }
    
    updateTranscriptDisplay(container, data) {
        // Remove initial message if present
        const initialMessage = container.querySelector('#initialMessage');
        if (initialMessage) {
            initialMessage.remove();
        }
        
        if (data.is_final) {
            // Final transcript - add as permanent segment
            const finalSegment = document.createElement('div');
            finalSegment.className = 'transcript-segment final';
            finalSegment.innerHTML = `
                <div class="transcript-text">${this.escapeHtml(data.transcript)}</div>
                <div class="transcript-meta">
                    <small class="text-muted">
                        Confidence: ${(data.confidence * 100).toFixed(1)}% | 
                        Latency: ${data.latency_ms.toFixed(0)}ms
                        ${data.meets_target ? ' ✅' : ' ⚠️'}
                    </small>
                </div>
            `;
            
            container.appendChild(finalSegment);
            
            // Remove any interim segments
            const interimSegments = container.querySelectorAll('.transcript-segment.interim');
            interimSegments.forEach(segment => segment.remove());
            
        } else {
            // Interim transcript - update or create interim segment
            let interimSegment = container.querySelector('.transcript-segment.interim');
            
            if (!interimSegment) {
                interimSegment = document.createElement('div');
                interimSegment.className = 'transcript-segment interim';
                container.appendChild(interimSegment);
            }
            
            interimSegment.innerHTML = `
                <div class="transcript-text text-muted">${this.escapeHtml(data.transcript)}</div>
                <div class="transcript-meta">
                    <small class="text-muted">
                        Interim | Confidence: ${(data.confidence * 100).toFixed(1)}%
                    </small>
                </div>
            `;
        }
        
        // Auto-scroll to bottom
        container.scrollTop = container.scrollHeight;
    }
    
    updateMetricsDisplay(data) {
        // Update word counter
        if (this.elements.wordCounter) {
            const allTranscriptText = Array.from(
                this.elements.transcriptDisplay?.querySelectorAll('.transcript-text') || []
            ).map(el => el.textContent).join(' ');
            
            const wordCount = allTranscriptText.trim().split(/\s+/).filter(word => word.length > 0).length;
            this.elements.wordCounter.textContent = wordCount.toString();
        }
        
        // Update confidence level
        if (this.elements.confidenceLevel) {
            const confidencePercent = (data.confidence * 100).toFixed(1);
            this.elements.confidenceLevel.textContent = `${confidencePercent}%`;
        }
    }
    
    updatePerformanceMetrics(data, startTime) {
        const processingTime = performance.now() - startTime;
        
        this.metrics.chunksProcessed++;
        this.metrics.totalLatency += data.latency_ms || 0;
        this.metrics.avgLatency = this.metrics.totalLatency / this.metrics.chunksProcessed;
        this.metrics.lastChunkTime = processingTime;
        
        // Log performance if significant
        if (data.latency_ms > 400) {
            console.warn(`⚠️ High latency detected: ${data.latency_ms}ms (target: <400ms)`);
        }
    }
    
    handleError(data) {
        const errorMessage = data.message || 'Unknown error occurred';
        console.error('❌ Transcription error:', errorMessage);
        
        this.updateStatus(`Error: ${errorMessage}`, 'error');
        
        // Handle specific error types
        switch (data.error_type) {
            case 'session_start_failed':
                this.isRecording = false;
                this.updateRecordButtonState();
                break;
                
            case 'transcription_failed':
                // Continue recording but show warning
                console.warn('⚠️ Transcription failed for chunk, continuing...');
                break;
                
            case 'no_active_session':
                // Restart session
                if (this.isRecording) {
                    console.log('🔄 Restarting session...');
                    this.startSession();
                }
                break;
                
            default:
                // Show generic error
                this.showErrorDialog(errorMessage);
        }
    }
    
    async startRecording() {
        try {
            console.log('🎤 Starting enhanced recording...');
            
            // Connect if not connected
            if (!this.isConnected) {
                this.connect();
                
                // Wait for connection
                await this.waitForConnection();
            }
            
            // Start session
            await this.startSession();
            
            // Request microphone access
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000
                }
            });
            
            // Setup MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.sendAudioChunk(event.data);
                }
            };
            
            this.mediaRecorder.start(250); // 250ms chunks for low latency
            
            this.isRecording = true;
            this.updateRecordButtonState();
            this.updateStatus('Recording and transcribing...', 'recording');
            
            console.log('✅ Enhanced recording started');
            
        } catch (error) {
            console.error('❌ Failed to start recording:', error);
            this.updateStatus('Failed to start recording', 'error');
            this.showErrorDialog('Failed to start recording: ' + error.message);
        }
    }
    
    async stopRecording() {
        try {
            console.log('🛑 Stopping enhanced recording...');
            
            if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
                this.mediaRecorder.stop();
            }
            
            if (this.audioStream) {
                this.audioStream.getTracks().forEach(track => track.stop());
                this.audioStream = null;
            }
            
            // End session
            if (this.sessionId) {
                await this.endSession();
            }
            
            this.isRecording = false;
            this.updateRecordButtonState();
            this.updateStatus('Recording stopped', 'success');
            
            console.log('✅ Enhanced recording stopped');
            
        } catch (error) {
            console.error('❌ Failed to stop recording:', error);
            this.updateStatus('Error stopping recording', 'error');
        }
    }
    
    async sendAudioChunk(audioBlob) {
        if (!this.isConnected || !this.sessionId) {
            console.warn('⚠️ Cannot send audio chunk - not connected or no session');
            return;
        }
        
        try {
            // Convert blob to base64
            const arrayBuffer = await audioBlob.arrayBuffer();
            const base64Data = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
            
            const message = {
                type: 'audio_chunk',
                session_id: this.sessionId,
                audio_data: base64Data,
                timestamp: Date.now(),
                duration: 0.25, // 250ms chunks
                is_final: false
            };
            
            this.websocket.send(JSON.stringify(message));
            
        } catch (error) {
            console.error('❌ Failed to send audio chunk:', error);
        }
    }
    
    async startSession() {
        if (!this.isConnected) {
            throw new Error('Not connected to WebSocket');
        }
        
        const message = {
            type: 'start_session',
            language: 'en',
            quality_mode: 'adaptive'
        };
        
        this.websocket.send(JSON.stringify(message));
    }
    
    async endSession() {
        if (!this.isConnected || !this.sessionId) {
            return;
        }
        
        const message = {
            type: 'end_session',
            session_id: this.sessionId
        };
        
        this.websocket.send(JSON.stringify(message));
    }
    
    async waitForConnection(timeout = 5000) {
        return new Promise((resolve, reject) => {
            if (this.isConnected) {
                resolve();
                return;
            }
            
            const checkConnection = () => {
                if (this.isConnected) {
                    resolve();
                } else {
                    setTimeout(checkConnection, 100);
                }
            };
            
            setTimeout(() => reject(new Error('Connection timeout')), timeout);
            checkConnection();
        });
    }
    
    updateRecordButtonState() {
        if (!this.elements.recordButton) return;
        
        const icon = this.elements.recordButton.querySelector('i');
        const text = this.elements.recordButton.querySelector('span');
        
        if (this.isRecording) {
            this.elements.recordButton.className = 'btn btn-danger btn-lg';
            if (icon) icon.className = 'bi bi-stop-fill';
            if (text) text.textContent = 'Stop Recording';
        } else {
            this.elements.recordButton.className = 'btn btn-primary btn-lg';
            if (icon) icon.className = 'bi bi-mic';
            if (text) text.textContent = 'Start Recording';
        }
    }
    
    updateStatus(message, type = 'info') {
        if (!this.elements.statusDisplay) return;
        
        const icon = this.elements.statusDisplay.querySelector('i');
        const text = this.elements.statusDisplay.querySelector('span');
        
        // Update classes
        this.elements.statusDisplay.className = `alert mb-3 alert-${this.getAlertClass(type)}`;
        
        // Update icon
        if (icon) {
            icon.className = `bi ${this.getStatusIcon(type)}`;
        }
        
        // Update text
        if (text) {
            text.textContent = message;
        }
    }
    
    getAlertClass(type) {
        switch (type) {
            case 'success': return 'success';
            case 'error': return 'danger';
            case 'warning': return 'warning';
            case 'recording': return 'primary';
            default: return 'secondary';
        }
    }
    
    getStatusIcon(type) {
        switch (type) {
            case 'success': return 'bi-check-circle-fill text-success';
            case 'error': return 'bi-exclamation-triangle-fill text-danger';
            case 'warning': return 'bi-exclamation-circle-fill text-warning';
            case 'recording': return 'bi-record-circle-fill text-primary';
            default: return 'bi-circle-fill text-secondary';
        }
    }
    
    showErrorDialog(message) {
        // Simple error dialog - could be enhanced with a modal
        alert(`Transcription Error: ${message}`);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getMetrics() {
        return {
            ...this.metrics,
            isConnected: this.isConnected,
            isRecording: this.isRecording,
            sessionId: this.sessionId
        };
    }
}

// Initialize enhanced WebSocket client when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎯 Initializing Enhanced WebSocket Client...');
    window.enhancedWebSocketClient = new EnhancedWebSocketClient();
    
    // Global access for debugging
    window.getEnhancedMetrics = () => window.enhancedWebSocketClient.getMetrics();
});