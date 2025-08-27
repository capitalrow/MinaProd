/**
 * Real Whisper API Integration for Main Live Transcription Page
 * Replaces Socket.IO with direct WebSocket connection to real Whisper transcription
 */

class RealWhisperIntegration {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.isRecording = false;
        this.sessionId = null;
        this.mediaRecorder = null;
        this.mediaStream = null;
        this.connectionAttempts = 0;
        this.maxConnectionAttempts = 3;
        
        // Real-time transcription state
        this.transcriptionBuffer = [];
        this.processingFeedback = false;
        
        console.log('Real Whisper Integration initialized');
    }
    
    async initializeConnection() {
        try {
            console.log('🔗 Initializing real-time transcription connection...');
            
            // MANUAL MONITORING RECOMMENDATION #1: Use existing WebSocket infrastructure 
            // Connect to enhanced browser WebSocket server (port 8773)
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.hostname;
            const port = '8773';  // Enhanced WebSocket server port
            const wsUrl = `${protocol}//${host}:${port}`;
            
            console.log(`Connecting to enhanced WebSocket server: ${wsUrl}`);
            
            // Create native WebSocket connection
            this.socket = new WebSocket(wsUrl);
            
            // MANUAL MONITORING RECOMMENDATION #2: Enhanced WebSocket event handlers
            this.socket.onopen = () => {
                this.isConnected = true;
                this.connectionAttempts = 0;
                console.log('✅ Real-time transcription connected via Enhanced WebSocket');
                
                // Update UI with connection status
                if (window.professionalRecorder) {
                    window.professionalRecorder.updateConnectionStatus('connected');
                }
                
                // Show success notification
                if (window.toastSystem) {
                    window.toastSystem.showSuccess('🔗 Enhanced transcription service connected');
                }
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleTranscriptionMessage(data);
                } catch (error) {
                    console.error('❌ Failed to parse WebSocket message:', error);
                }
            };
            
            this.socket.onclose = () => {
                this.isConnected = false;
                console.log('🔌 Real-time transcription disconnected');
                this.handleReconnection();
                
                // Update UI
                if (window.professionalRecorder) {
                    window.professionalRecorder.updateConnectionStatus('disconnected');
                }
            };
            
            this.socket.onerror = (error) => {
                console.error('❌ Enhanced WebSocket connection error:', error);
                this.handleConnectionError(error);
                
                // Show error notification
                if (window.toastSystem) {
                    window.toastSystem.showError('❌ Connection failed - retrying...');
                }
            };
            
            // MANUAL MONITORING RECOMMENDATION #3: Enhanced WebSocket connection promise
            return new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Enhanced WebSocket connection timeout after 10 seconds'));
                }, 10000);
                
                this.socket.onopen = () => {
                    clearTimeout(timeout);
                    this.isConnected = true;
                    this.connectionAttempts = 0;
                    console.log('✅ Real-time transcription connected via Enhanced WebSocket');
                    resolve();
                };
                
                this.socket.onerror = (error) => {
                    clearTimeout(timeout);
                    console.error('❌ Enhanced WebSocket connection error:', error);
                    reject(new Error(`Enhanced WebSocket connection failed: ${error.message || error}`));
                };
            });
            
        } catch (error) {
            console.error('Failed to initialize connection:', error);
            throw error;
        }
    }
    
    // MANUAL MONITORING RECOMMENDATION #4: Enhanced WebSocket client (no external dependencies needed)
    
    async startTranscription(sessionId) {
        try {
            if (!this.isConnected) {
                await this.initializeConnection();
            }
            
            this.sessionId = sessionId;
            
            // Send session join message via Enhanced WebSocket
            this.socket.send(JSON.stringify({
                type: 'join_session',
                session_id: sessionId
            }));
            
            // Initialize audio recording
            await this.initializeAudioRecording();
            
            console.log('✅ Real-time transcription started');
            return true;
            
        } catch (error) {
            console.error('Failed to start transcription:', error);
            throw error;
        }
    }
    
    async initializeAudioRecording() {
        try {
            // Get microphone access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000
                }
            });
            
            // Set up MediaRecorder for high-quality audio
            const options = {
                mimeType: 'audio/webm;codecs=opus',
                audioBitsPerSecond: 128000
            };
            
            // Fallback for browsers that don't support webm/opus
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                options.mimeType = 'audio/webm';
            }
            
            this.mediaRecorder = new MediaRecorder(this.mediaStream, options);
            
            // Handle audio data
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0 && this.socket && this.socket.readyState === WebSocket.OPEN) {
                    // Send audio data directly as binary
                    this.socket.send(event.data);
                    console.log(`📤 Audio chunk sent: ${event.data.size} bytes`);
                }
            };
            
            // Start recording with 1-second chunks for optimal accuracy
            this.mediaRecorder.start(1000);
            this.isRecording = true;
            
            console.log('🎤 Audio recording initialized');
            
        } catch (error) {
            console.error('Failed to initialize audio recording:', error);
            throw error;
        }
    }
    
    handleTranscriptionMessage(data) {
        console.log('📨 Transcription message:', data);
        
        switch (data.type) {
            case 'connected':
                console.log('🔗 Server handshake complete');
                break;
                
            case 'session_joined':
                console.log('📝 Session joined:', data.session_id);
                break;
                
            case 'transcription_result':
                this.handleTranscriptionResult(data);
                break;
                
            case 'error':
                console.error('❌ Server error:', data.message);
                break;
        }
    }
    
    handleTranscriptionResult(data) {
        const timestamp = new Date().toLocaleTimeString();
        const confidence = Math.round(data.confidence * 100);
        
        // Handle different types of responses
        if (data.processing) {
            // Show processing feedback immediately
            this.displayProcessingFeedback(data.text);
        } else {
            // Show real transcription result
            this.displayTranscriptionResult({
                text: data.text,
                confidence: confidence,
                is_final: data.is_final,
                timestamp: timestamp
            });
        }
        
        // Update transcription statistics if available
        if (window.professionalRecorder && window.professionalRecorder.updateTranscriptionStats) {
            window.professionalRecorder.updateTranscriptionStats({
                segments: this.transcriptionBuffer.length,
                avgConfidence: confidence
            });
        }
        
        console.log(`📝 Transcription: "${data.text}" (${confidence}% confidence)`);
    }
    
    displayProcessingFeedback(text) {
        // Add processing feedback to main transcript
        const transcriptContainer = document.getElementById('transcript') || 
                                  document.getElementById('transcriptContent') ||
                                  document.querySelector('.transcript-content');
                                  
        if (transcriptContainer) {
            const processingElement = document.createElement('div');
            processingElement.className = 'transcript-segment processing';
            processingElement.innerHTML = `
                <span class="timestamp">[${new Date().toLocaleTimeString()}]</span>
                <span class="processing-text">${text}</span>
            `;
            
            transcriptContainer.appendChild(processingElement);
            transcriptContainer.scrollTop = transcriptContainer.scrollHeight;
            
            // Remove processing feedback after a short delay
            setTimeout(() => {
                if (processingElement.parentNode) {
                    processingElement.remove();
                }
            }, 2000);
        }
    }
    
    displayTranscriptionResult(result) {
        // Clear "Ready to record" text and add real transcription
        const transcriptContainer = document.querySelector('.live-transcript-container') ||
                                  document.getElementById('transcript') || 
                                  document.getElementById('transcriptContent') ||
                                  document.querySelector('.transcript-content');
                                  
        if (transcriptContainer) {
            // Remove "Ready to record" placeholder if it exists
            const placeholder = transcriptContainer.querySelector('.text-muted');
            if (placeholder && placeholder.textContent.includes('Ready to record')) {
                placeholder.remove();
            }
            
            const segmentElement = document.createElement('div');
            segmentElement.className = `transcript-segment ${result.is_final ? 'final' : 'interim'} mb-2`;
            segmentElement.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="transcript-text">
                        <small class="text-muted">[${result.timestamp}]</small>
                        <span class="ms-2 ${result.is_final ? 'text-light fw-bold' : 'text-warning'}">${result.text}</span>
                    </div>
                    <small class="text-muted">${result.confidence}%</small>
                </div>
            `;
            
            transcriptContainer.appendChild(segmentElement);
            transcriptContainer.scrollTop = transcriptContainer.scrollHeight;
            
            // Update word count in the stats
            const wordCountElement = document.querySelector('.metric-value');
            if (wordCountElement && wordCountElement.textContent === '0') {
                const words = result.text.split(' ').filter(word => word.length > 0).length;
                wordCountElement.textContent = words;
            }
        }
        
        // Add to transcription buffer
        this.transcriptionBuffer.push(result);
        
        // Trigger segment update event for other components
        window.dispatchEvent(new CustomEvent('transcriptionSegment', {
            detail: result
        }));
    }
    
    // MANUAL MONITORING RECOMMENDATION #5: Enhanced connection error handling
    handleConnectionError(error) {
        console.error('❌ Connection error:', error);
        
        // Update UI immediately
        if (window.professionalRecorder) {
            window.professionalRecorder.updateConnectionStatus('error');
        }
        
        if (this.connectionAttempts < this.maxConnectionAttempts) {
            this.connectionAttempts++;
            const delay = Math.pow(2, this.connectionAttempts) * 1000; // Exponential backoff
            console.log(`🔄 Retrying connection (attempt ${this.connectionAttempts}/${this.maxConnectionAttempts}) in ${delay}ms`);
            
            // Show retry notification
            if (window.toastSystem) {
                window.toastSystem.showWarning(`🔄 Retrying connection... (${this.connectionAttempts}/${this.maxConnectionAttempts})`);
            }
            
            setTimeout(() => this.initializeConnection(), delay);
        } else {
            console.error('❌ Max connection attempts reached - connection failed permanently');
            
            // Show failure notification
            if (window.toastSystem) {
                window.toastSystem.showError('❌ Connection failed after multiple attempts');
            }
            
            // Update UI to show connection failure
            if (window.professionalRecorder) {
                window.professionalRecorder.updateConnectionStatus('failed');
            }
        }
        
        // Also use enhanced error handler if available
        if (window.enhancedErrorHandler) {
            window.enhancedErrorHandler.handleError(error, 'Socket.IO', () => {
                this.attemptReconnection();
            });
        }
    }
    
    handleReconnection() {
        if (this.connectionAttempts < this.maxConnectionAttempts) {
            this.connectionAttempts++;
            console.log(`🔄 Attempting reconnection (${this.connectionAttempts}/${this.maxConnectionAttempts})`);
            
            setTimeout(() => {
                this.initializeConnection().catch(error => {
                    console.error('Reconnection failed:', error);
                });
            }, 2000 * this.connectionAttempts);
        } else {
            console.error('❌ Max reconnection attempts reached');
        }
    }
    
    stopTranscription() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
        }
        
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
        
        console.log('⏹️ Transcription stopped');
    }
    
    disconnect() {
        this.stopTranscription();
        
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        
        this.isConnected = false;
        console.log('🔌 Disconnected from real-time transcription');
    }
}

// Initialize global instance and professional recorder replacement
window.realWhisperIntegration = new RealWhisperIntegration();

// Professional Recorder replacement for compatibility
class ProfessionalRecorder {
    constructor() {
        this.isRecording = false;
        this.sessionId = null;
        console.log('✅ Professional Recorder initialized with Real Whisper integration');
    }
    
    async startRecording() {
        try {
            this.sessionId = `live_${Date.now()}`;
            await window.realWhisperIntegration.startTranscription(this.sessionId);
            this.isRecording = true;
            console.log('✅ Recording started with Real Whisper API');
            return { success: true, sessionId: this.sessionId };
        } catch (error) {
            console.error('❌ Failed to start recording:', error);
            return { success: false, error: error.message };
        }
    }
    
    stopRecording() {
        window.realWhisperIntegration.stopTranscription();
        this.isRecording = false;
        console.log('⏹️ Recording stopped');
        return { success: true };
    }
    
    updateConnectionStatus(status) {
        const wsStatus = document.querySelector('#wsStatus');
        if (wsStatus) {
            wsStatus.textContent = status === 'connected' ? 'Connected' : 'Disconnected';
            wsStatus.className = `status-indicator ${status}`;
        }
    }
    
    updateTranscriptionStats(stats) {
        // Update UI with transcription statistics
        console.log('📊 Transcription stats:', stats);
    }
}

// Initialize professional recorder replacement
window.professionalRecorder = new ProfessionalRecorder();

// Add CSS for processing feedback
const style = document.createElement('style');
style.textContent = `
    .transcript-segment.processing .processing-text {
        color: #ffc107;
        font-style: italic;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .transcript-segment.final .text {
        color: #28a745;
        font-weight: bold;
    }
    
    .transcript-segment.interim .text {
        color: #17a2b8;
        font-style: italic;
    }
    
    .transcript-segment .confidence {
        font-size: 0.8em;
        color: #6c757d;
        margin-left: 0.5em;
    }
`;
document.head.appendChild(style);

console.log('Real Whisper Integration loaded successfully');