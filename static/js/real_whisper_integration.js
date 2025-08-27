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
        this.cumulativeTranscript = '';  // For building progressive transcript
        this.chunkCount = 0;  // Track number of chunks processed
        this.processingFeedback = false;
        
        console.log('Real Whisper Integration initialized');
    }
    
    async initializeConnection() {
        try {
            console.log('🔗 Initializing real-time transcription connection...');
            
            // MANUAL MONITORING RECOMMENDATION #1: Smart port detection with fallback
            // Try multiple ports to find working Enhanced WebSocket server
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.hostname;
            const portsToTry = ['8774', '8775', '8776', '8773'];  // Try alternatives first
            
            let connected = false;
            for (const port of portsToTry) {
                try {
                    const wsUrl = `${protocol}//${host}:${port}`;
                    console.log(`🔧 Attempting Enhanced WebSocket connection: ${wsUrl}`);
                    
                    this.socket = new WebSocket(wsUrl);
                    
                    // Test connection with timeout
                    await new Promise((resolve, reject) => {
                        const timeout = setTimeout(() => {
                            reject(new Error(`Port ${port} timeout`));
                        }, 2000);
                        
                        this.socket.onopen = () => {
                            clearTimeout(timeout);
                            console.log(`✅ Connected to Enhanced WebSocket on port ${port}`);
                            connected = true;
                            resolve();
                        };
                        
                        this.socket.onerror = () => {
                            clearTimeout(timeout);
                            reject(new Error(`Port ${port} failed`));
                        };
                    });
                    
                    if (connected) break;
                    
                } catch (error) {
                    console.warn(`⚠️ Port ${port} failed: ${error.message}`);
                    continue;
                }
            }
            
            if (!connected) {
                throw new Error('Enhanced WebSocket server not available on any port');
            }
            
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
            
            // Message handler will be set up after connection handshake
            
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
            
            // Enhanced WebSocket connection with message handling
            return new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Enhanced WebSocket connection timeout after 10 seconds'));
                }, 10000);
                
                this.socket.onopen = () => {
                    console.log('🔗 Enhanced WebSocket connection opened, waiting for server handshake...');
                    // Don't resolve immediately, wait for server welcome message
                };
                
                this.socket.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log('📨 Server message:', data);
                        
                        if (data.type === 'connected') {
                            clearTimeout(timeout);
                            this.isConnected = true;
                            this.connectionAttempts = 0;
                            console.log('✅ Enhanced WebSocket Server handshake complete:', data.server);
                            resolve();
                        } else {
                            // Handle other message types during connection
                            this.handleTranscriptionMessage(data);
                        }
                    } catch (e) {
                        console.warn('📨 Non-JSON message during connection:', event.data);
                    }
                };
                
                this.socket.onerror = (error) => {
                    clearTimeout(timeout);
                    console.error('❌ Enhanced WebSocket connection error:', error);
                    reject(new Error(`Enhanced WebSocket connection failed: ${error.message || error}`));
                };
            });
            
            // Set up message handler for ongoing communication
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleTranscriptionMessage(data);
                } catch (e) {
                    console.warn('📨 Non-JSON message received:', event.data);
                }
            };
            
        } catch (error) {
            console.error('Failed to initialize connection:', error);
            throw error;
        }
    }
    
    // Enhanced WebSocket client with proper session management
    
    async startTranscription(sessionId) {
        try {
            console.log('🎯 STARTING REAL WHISPER INTEGRATION');
            
            if (!this.isConnected) {
                await this.initializeConnection();
            }
            
            this.sessionId = sessionId;
            
            // CRITICAL: Reset cumulative transcript for new recording
            this.cumulativeTranscript = '';
            this.chunkCount = 0;
            this.transcriptionBuffer = [];
            console.log('🎯 RESET: Starting fresh transcription session');
            
            // Send session join message via Enhanced WebSocket
            this.socket.send(JSON.stringify({
                type: 'join_session',
                session_id: sessionId
            }));
            
            // CRITICAL: Clear the transcript area and show active status
            this.clearTranscriptArea();
            this.showTranscriptionActive();
            
            // Initialize audio recording
            await this.initializeAudioRecording();
            
            console.log('✅ Real-time transcription started');
            return true;
            
        } catch (error) {
            console.error('Failed to start transcription:', error);
            throw error;
        }
    }
    
    clearTranscriptArea() {
        const transcriptContainer = document.querySelector('.live-transcript-container') ||
                                  document.getElementById('transcript') || 
                                  document.getElementById('transcriptContent') ||
                                  document.querySelector('.transcript-content');
                                  
        if (transcriptContainer) {
            transcriptContainer.innerHTML = '';
            console.log('🧹 Transcript area cleared');
        }
    }
    
    showTranscriptionActive() {
        const transcriptContainer = document.querySelector('.live-transcript-container') ||
                                  document.getElementById('transcript') || 
                                  document.getElementById('transcriptContent') ||
                                  document.querySelector('.transcript-content');
                                  
        if (transcriptContainer) {
            transcriptContainer.innerHTML = `
                <div class="transcription-active p-3 text-center">
                    <div class="spinner-border text-success mb-2" role="status">
                        <span class="visually-hidden">Processing...</span>
                    </div>
                    <h6 class="text-success">🎤 Live Transcription Active</h6>
                    <p class="text-muted mb-0">Listening for speech...</p>
                </div>
            `;
            console.log('🎤 Showing active transcription status');
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
                    this.chunkCount++;
                    
                    // Send audio data directly as binary
                    this.socket.send(event.data);
                    console.log(`📤 CHUNK ${this.chunkCount}: ${event.data.size} bytes sent (Real Whisper Integration)`);
                    
                    // Show chunk processing feedback in UI
                    this.showChunkProcessingFeedback(this.chunkCount, event.data.size);
                    
                    // Update UI with audio transmission feedback (less frequent)
                    if (this.chunkCount % 2 === 0 && window.toastSystem) {
                        window.toastSystem.showInfo(`🎵 Processing chunk ${this.chunkCount}...`);
                    }
                } else {
                    console.warn('⚠️ Cannot send audio: WebSocket not ready or no data');
                }
            };
            
            // Start recording with 1-second chunks for optimal accuracy
            this.mediaRecorder.start(1000);
            this.isRecording = true;
            
            console.log('🎤 Audio recording initialized');
            console.log('✅ Real Whisper Integration: MediaRecorder active, ready for transcription');
            
        } catch (error) {
            console.error('Failed to initialize audio recording:', error);
            throw error;
        }
    }
    
    handleTranscriptionMessage(data) {
        console.log('📨 Enhanced WebSocket message:', data);
        
        switch (data.type) {
            case 'connected':
                console.log('🔗 Enhanced WebSocket Server handshake complete:', data.message);
                break;
                
            case 'session_joined':
                console.log('📝 Session joined successfully:', data.session_id);
                if (window.toastSystem) {
                    window.toastSystem.showSuccess(`Session ${data.session_id} ready for transcription`);
                }
                break;
                
            case 'transcription_result':
                this.handleTranscriptionResult(data);
                break;
                
            case 'error':
                console.error('❌ Enhanced WebSocket Server error:', data.message);
                if (window.toastSystem) {
                    window.toastSystem.showError(`Server Error: ${data.message}`);
                }
                break;
                
            default:
                console.log('📨 Unknown message type:', data.type);
        }
    }
    
    handleTranscriptionResult(data) {
        const timestamp = new Date().toLocaleTimeString();
        const confidence = Math.round(data.confidence * 100);
        const latency = Date.now() - (data.timestamp || Date.now());
        
        // INDUSTRY STANDARD: Update performance metrics
        if (window.performanceMonitor && window.performanceMonitor.isActive) {
            window.performanceMonitor.segmentCount++;
            window.performanceMonitor.latencies.push(latency);
            window.performanceMonitor.confidenceScores.push(confidence / 100);
            
            if (data.text) {
                const wordCount = data.text.split(' ').filter(word => word.length > 0).length;
                window.performanceMonitor.wordCount += wordCount;
            }
        }
        
        // Handle different types of responses
        if (data.processing) {
            // Show processing feedback immediately
            this.displayProcessingFeedback(data.text);
        } else if (data.text && data.text.trim() && data.text !== "[No speech detected]") {
            // CRITICAL: Build cumulative transcript for progressive display
            this.buildCumulativeTranscript({
                text: data.text,
                confidence: confidence,
                is_final: data.is_final,
                timestamp: timestamp,
                latency: latency
            });
        }
        
        console.log(`📝 Transcription: "${data.text}" (${confidence}% confidence, ${latency}ms latency)`);
    }
    
    buildCumulativeTranscript(result) {
        // Initialize cumulative transcript if not exists
        if (!this.cumulativeTranscript) {
            this.cumulativeTranscript = '';
        }
        
        // Add interim results to build progressive transcript
        if (!result.is_final) {
            // For interim results, append to cumulative transcript
            const newText = result.text.trim();
            if (newText && !this.cumulativeTranscript.includes(newText)) {
                this.cumulativeTranscript += (this.cumulativeTranscript ? ' ' : '') + newText;
                console.log(`📝 INTERIM: "${this.cumulativeTranscript}"`);
            }
        } else {
            // For final results, ensure it's included in cumulative
            const finalText = result.text.trim();
            if (finalText && !this.cumulativeTranscript.includes(finalText)) {
                this.cumulativeTranscript += (this.cumulativeTranscript ? ' ' : '') + finalText;
                console.log(`📝 FINAL: "${this.cumulativeTranscript}"`);
            }
        }
        
        // Update UI with progressive transcript
        this.displayProgressiveTranscript({
            text: this.cumulativeTranscript,
            confidence: result.confidence,
            is_final: result.is_final,
            timestamp: result.timestamp,
            latency: result.latency
        });
    }
    
    displayProgressiveTranscript(result) {
        // Find transcript container
        const transcriptContainer = document.querySelector('.live-transcript-container') ||
                                  document.getElementById('transcript') || 
                                  document.getElementById('transcriptContent') ||
                                  document.querySelector('.transcript-content');
                                  
        if (transcriptContainer) {
            // Remove placeholder if exists
            const placeholder = transcriptContainer.querySelector('.text-muted');
            if (placeholder && placeholder.textContent.includes('Ready to record')) {
                placeholder.remove();
            }
            
            // Clear and update with cumulative transcript (PROGRESSIVE DISPLAY)
            transcriptContainer.innerHTML = '';
            
            // Create main transcript element
            const mainTranscriptElement = document.createElement('div');
            mainTranscriptElement.className = 'cumulative-transcript mb-3';
            mainTranscriptElement.innerHTML = `
                <div class="transcript-header d-flex justify-content-between align-items-center mb-2">
                    <h6 class="text-light mb-0">🎤 Live Transcription</h6>
                    <div class="transcript-stats">
                        <small class="text-muted">Chunk: ${this.chunkCount}</small>
                        <small class="text-muted ms-2">Words: ${result.text.split(' ').length}</small>
                    </div>
                </div>
                <div class="transcript-content p-3 border border-secondary rounded">
                    <div class="progressive-text ${result.is_final ? 'text-success fw-bold' : 'text-warning'}">
                        ${result.text}
                    </div>
                    <div class="transcript-metadata mt-2 pt-2 border-top border-secondary">
                        <small class="text-muted">
                            ${result.timestamp} • ${result.confidence}% confidence
                            ${result.latency ? ` • ${result.latency}ms` : ''}
                            • ${result.is_final ? 'FINAL' : 'INTERIM'}
                        </small>
                    </div>
                </div>
            `;
            
            transcriptContainer.appendChild(mainTranscriptElement);
            transcriptContainer.scrollTop = transcriptContainer.scrollHeight;
            
            // Store for final transcript generation
            this.transcriptionBuffer.push(result);
            
            // Update word count in performance monitor
            if (window.performanceMonitor) {
                window.performanceMonitor.wordCount = result.text.split(' ').filter(w => w.length > 0).length;
            }
            
            // Trigger segment update event
            window.dispatchEvent(new CustomEvent('transcriptionSegment', {
                detail: result
            }));
        }
    }
    
    showChunkProcessingFeedback(chunkNumber, chunkSize) {
        // Show processing feedback for each chunk
        const statusElement = document.querySelector('#connectionStatus') || 
                             document.querySelector('.connection-status') ||
                             document.querySelector('#wsStatus');
                             
        if (statusElement) {
            statusElement.innerHTML = `
                <span class="text-warning">
                    🎵 Processing chunk ${chunkNumber} (${chunkSize} bytes)...
                </span>
            `;
            
            // Clear after 2 seconds
            setTimeout(() => {
                if (statusElement) {
                    statusElement.innerHTML = '<span class="text-success">🔗 Connected & Recording</span>';
                }
            }, 2000);
        }
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
        // INDUSTRY STANDARD: Separate interim and final transcript handling
        if (result.is_final) {
            // Store final transcripts for GPT-4 refinement
            if (window.finalTranscripts) {
                window.finalTranscripts.push({
                    text: result.text,
                    confidence: result.confidence,
                    timestamp: result.timestamp
                });
                console.log(`📄 Final transcript segment stored: "${result.text}"`);
            }
        } else {
            // Store interim transcripts for real-time display
            if (window.interimTranscripts) {
                window.interimTranscripts.push({
                    text: result.text,
                    confidence: result.confidence,
                    timestamp: result.timestamp
                });
            }
        }
        
        // Display transcription in UI
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
            segmentElement.className = `transcript-segment ${result.is_final ? 'final' : 'interim'} mb-2 fade-in`;
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

// Initialize Real Whisper Integration globally
window.realWhisperIntegration = new RealWhisperIntegration();

// CRITICAL FIX: Button Event Binding for Real Whisper Integration
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 CRITICAL FIX: Binding Real Whisper Integration to UI buttons');
    
    // Find the recording buttons
    const startBtn = document.getElementById('startRecordingBtn') || 
                    document.querySelector('.start-recording-btn') ||
                    document.querySelector('[data-action="start"]');
                    
    const stopBtn = document.getElementById('stopRecordingBtn') || 
                   document.querySelector('.stop-recording-btn') ||
                   document.querySelector('[data-action="stop"]');
    
    if (!startBtn || !stopBtn) {
        console.error('❌ CRITICAL: Recording buttons not found in DOM');
        return;
    }
    
    console.log('✅ Found recording buttons:', startBtn, stopBtn);
    
    // EXCLUSIVE Real Whisper Integration button handlers
    startBtn.addEventListener('click', async function(event) {
        event.preventDefault();
        event.stopImmediatePropagation();
        
        console.log('🎯 EXCLUSIVE Real Whisper Integration handling start button');
        
        try {
            // Disable button to prevent double-clicks
            startBtn.disabled = true;
            startBtn.textContent = 'Connecting...';
            
            // Update UI immediately
            if (window.toastSystem) {
                window.toastSystem.showInfo('🔗 Connecting to real-time transcription...');
            }
            
            // Generate session ID
            const sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(7)}`;
            
            // Start Real Whisper Integration transcription
            await window.realWhisperIntegration.startTranscription(sessionId);
            
            // Update button states
            startBtn.style.display = 'none';
            stopBtn.style.display = 'inline-block';
            stopBtn.disabled = false;
            
            // Start performance monitoring
            if (window.performanceMonitor) {
                window.performanceMonitor.startMonitoring();
            }
            
            console.log('✅ Real Whisper Integration started successfully');
            
            if (window.toastSystem) {
                window.toastSystem.showSuccess('🎤 Live transcription started!');
            }
            
        } catch (error) {
            console.error('❌ Real Whisper Integration start failed:', error);
            
            // Reset button state on error
            startBtn.disabled = false;
            startBtn.textContent = 'Start Recording';
            
            if (window.toastSystem) {
                window.toastSystem.showError(`❌ Failed to start: ${error.message}`);
            }
        }
    });
    
    stopBtn.addEventListener('click', async function(event) {
        event.preventDefault();
        event.stopImmediatePropagation();
        
        console.log('🎯 EXCLUSIVE Real Whisper Integration handling stop button');
        
        try {
            // Disable button
            stopBtn.disabled = true;
            stopBtn.textContent = 'Stopping...';
            
            // Update UI
            if (window.toastSystem) {
                window.toastSystem.showInfo('🛑 Stopping transcription...');
            }
            
            // Stop Real Whisper Integration
            await window.realWhisperIntegration.stopTranscription();
            
            // Update button states
            stopBtn.style.display = 'none';
            startBtn.style.display = 'inline-block';
            startBtn.disabled = false;
            startBtn.textContent = 'Start Recording';
            
            // Stop performance monitoring
            if (window.performanceMonitor) {
                window.performanceMonitor.stopMonitoring();
            }
            
            console.log('✅ Real Whisper Integration stopped successfully');
            
            if (window.toastSystem) {
                window.toastSystem.showSuccess('✅ Recording stopped - processing final transcript...');
            }
            
            // TODO: Generate final transcript here
            
        } catch (error) {
            console.error('❌ Real Whisper Integration stop failed:', error);
            
            // Reset button state on error
            stopBtn.disabled = false;
            stopBtn.textContent = 'Stop Recording';
            
            if (window.toastSystem) {
                window.toastSystem.showError(`❌ Failed to stop: ${error.message}`);
            }
        }
    });
    
    console.log('🎯 CRITICAL FIX COMPLETE: Real Whisper Integration bound to buttons');
});

console.log('Real Whisper Integration loaded successfully');