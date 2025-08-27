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
            
            // Determine WebSocket URL based on environment
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.hostname;
            const port = '8771';
            const wsUrl = `${protocol}//${host}:${port}`;
            
            console.log(`Connecting to: ${wsUrl}`);
            
            // Create WebSocket connection
            this.socket = new WebSocket(wsUrl);
            
            // Set up event handlers
            this.socket.onopen = () => {
                this.isConnected = true;
                this.connectionAttempts = 0;
                console.log('✅ Real-time transcription connected');
                
                // Update UI
                if (window.professionalRecorder) {
                    window.professionalRecorder.updateConnectionStatus('connected');
                }
            };
            
            this.socket.onmessage = (event) => {
                this.handleTranscriptionMessage(JSON.parse(event.data));
            };
            
            this.socket.onclose = () => {
                this.isConnected = false;
                console.log('🔌 Real-time transcription disconnected');
                this.handleReconnection();
            };
            
            this.socket.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.handleConnectionError(error);
            };
            
            return new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Connection timeout'));
                }, 10000);
                
                this.socket.onopen = () => {
                    clearTimeout(timeout);
                    this.isConnected = true;
                    this.connectionAttempts = 0;
                    console.log('✅ Real-time transcription connected');
                    resolve();
                };
                
                this.socket.onerror = (error) => {
                    clearTimeout(timeout);
                    reject(error);
                };
            });
            
        } catch (error) {
            console.error('Failed to initialize connection:', error);
            throw error;
        }
    }
    
    async startTranscription(sessionId) {
        try {
            if (!this.isConnected) {
                await this.initializeConnection();
            }
            
            this.sessionId = sessionId;
            
            // Send session join message
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
        // Add to main transcript
        const transcriptContainer = document.getElementById('transcript') || 
                                  document.getElementById('transcriptContent') ||
                                  document.querySelector('.transcript-content');
                                  
        if (transcriptContainer) {
            const segmentElement = document.createElement('div');
            segmentElement.className = `transcript-segment ${result.is_final ? 'final' : 'interim'}`;
            segmentElement.innerHTML = `
                <span class="timestamp">[${result.timestamp}]</span>
                <span class="text">${result.text}</span>
                <span class="confidence">(${result.confidence}% confidence)</span>
            `;
            
            transcriptContainer.appendChild(segmentElement);
            transcriptContainer.scrollTop = transcriptContainer.scrollHeight;
        }
        
        // Add to transcription buffer
        this.transcriptionBuffer.push(result);
        
        // Trigger segment update event for other components
        window.dispatchEvent(new CustomEvent('transcriptionSegment', {
            detail: result
        }));
    }
    
    handleConnectionError(error) {
        console.error('Connection error:', error);
        
        if (window.enhancedErrorHandler) {
            window.enhancedErrorHandler.handleError(error, 'WebSocket', () => {
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

// Initialize global instance
window.realWhisperIntegration = new RealWhisperIntegration();

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