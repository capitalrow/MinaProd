/**
 * Direct Audio Transcription via HTTP
 * Works on same port as main app - no connection issues!
 */

class DirectAudioTranscription {
    constructor() {
        this.isRecording = false;
        this.sessionId = null;
        this.mediaRecorder = null;
        this.mediaStream = null;
        this.chunkCount = 0;
        this.cumulativeTranscript = '';
        
        console.log('✅ Direct Audio Transcription initialized');
    }
    
    async startTranscription(sessionId) {
        try {
            this.sessionId = sessionId;
            this.chunkCount = 0;
            this.cumulativeTranscript = '';
            
            console.log('🎯 Starting direct audio transcription');
            
            // Clear transcript area and show active status
            this.clearTranscriptArea();
            this.showTranscriptionActive();
            
            // Initialize audio recording
            await this.initializeAudioRecording();
            
            console.log('✅ Direct transcription started');
            return true;
            
        } catch (error) {
            console.error('❌ Failed to start transcription:', error);
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
            
            // Create MediaRecorder
            const options = {
                mimeType: 'audio/webm;codecs=opus'
            };
            
            this.mediaRecorder = new MediaRecorder(this.mediaStream, options);
            
            // Handle audio data - process each chunk
            this.mediaRecorder.ondataavailable = async (event) => {
                if (event.data.size > 0) {
                    this.chunkCount++;
                    console.log(`🎵 Processing chunk ${this.chunkCount}: ${event.data.size} bytes`);
                    
                    // Show chunk processing feedback
                    this.showChunkProcessing(this.chunkCount, event.data.size);
                    
                    // Process audio chunk via HTTP
                    await this.processAudioChunk(event.data);
                }
            };
            
            // Start recording with 1-second chunks
            this.mediaRecorder.start(1000);
            this.isRecording = true;
            
            console.log('🎤 Audio recording started - 1-second chunks');
            
        } catch (error) {
            console.error('❌ Audio recording initialization failed:', error);
            throw error;
        }
    }
    
    async processAudioChunk(audioBlob) {
        try {
            // Convert blob to base64
            const arrayBuffer = await audioBlob.arrayBuffer();
            const uint8Array = new Uint8Array(arrayBuffer);
            const base64Audio = btoa(String.fromCharCode.apply(null, uint8Array));
            
            // Send to HTTP endpoint
            const response = await fetch('/api/transcribe-audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    audio_data: base64Audio
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.handleTranscriptionResult(result);
            } else {
                console.error('❌ HTTP transcription failed:', response.status);
                this.handleTranscriptionResult({
                    text: '[Transcription service unavailable]',
                    is_final: false,
                    confidence: 0.0
                });
            }
            
        } catch (error) {
            console.error('❌ Audio chunk processing failed:', error);
            this.handleTranscriptionResult({
                text: '[Audio processing error]',
                is_final: false,
                confidence: 0.0
            });
        }
    }
    
    handleTranscriptionResult(data) {
        const timestamp = new Date().toLocaleTimeString();
        const confidence = Math.round((data.confidence || 0) * 100);
        
        // Skip if no actual speech detected
        if (data.text && data.text.trim() && data.text !== '[No speech detected]') {
            // Build cumulative transcript
            const newText = data.text.trim();
            if (!this.cumulativeTranscript.includes(newText)) {
                this.cumulativeTranscript += (this.cumulativeTranscript ? ' ' : '') + newText;
                console.log(`📝 CUMULATIVE: "${this.cumulativeTranscript}"`);
            }
            
            // Update UI with progressive transcript
            this.displayProgressiveTranscript({
                text: this.cumulativeTranscript,
                confidence: confidence,
                is_final: data.is_final,
                timestamp: timestamp,
                chunk: this.chunkCount
            });
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
                    <p class="text-muted mb-0">Listening for speech... HTTP mode</p>
                </div>
            `;
        }
    }
    
    showChunkProcessing(chunkNumber, chunkSize) {
        const statusElement = document.querySelector('#connectionStatus') || 
                             document.querySelector('.connection-status') ||
                             document.querySelector('#wsStatus');
                             
        if (statusElement) {
            statusElement.innerHTML = `
                <span class="text-info">
                    🎵 Processing chunk ${chunkNumber} (${chunkSize} bytes)...
                </span>
            `;
        }
    }
    
    displayProgressiveTranscript(result) {
        const transcriptContainer = document.querySelector('.live-transcript-container') ||
                                  document.getElementById('transcript') || 
                                  document.getElementById('transcriptContent') ||
                                  document.querySelector('.transcript-content');
                                  
        if (transcriptContainer) {
            transcriptContainer.innerHTML = `
                <div class="progressive-transcript mb-3">
                    <div class="transcript-header d-flex justify-content-between align-items-center mb-2">
                        <h6 class="text-success mb-0">🎤 Live Transcription (HTTP)</h6>
                        <div class="transcript-stats">
                            <small class="text-muted">Chunk: ${result.chunk}</small>
                            <small class="text-muted ms-2">Words: ${result.text.split(' ').length}</small>
                        </div>
                    </div>
                    <div class="transcript-content p-3 border border-success rounded">
                        <div class="progressive-text text-success fw-bold">
                            ${result.text}
                        </div>
                        <div class="transcript-metadata mt-2 pt-2 border-top border-secondary">
                            <small class="text-muted">
                                ${result.timestamp} • ${result.confidence}% confidence • HTTP Mode
                            </small>
                        </div>
                    </div>
                </div>
            `;
            
            transcriptContainer.scrollTop = transcriptContainer.scrollHeight;
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
        
        console.log('⏹️ Direct transcription stopped');
        
        // Show final transcript
        if (this.cumulativeTranscript) {
            this.displayFinalTranscript();
        }
    }
    
    displayFinalTranscript() {
        const transcriptContainer = document.querySelector('.live-transcript-container') ||
                                  document.getElementById('transcript');
        
        if (transcriptContainer && this.cumulativeTranscript) {
            const finalSection = document.createElement('div');
            finalSection.className = 'final-transcript-section mt-4 p-3 border border-success rounded';
            finalSection.innerHTML = `
                <h5 class="text-success mb-3">📄 Final Transcript</h5>
                <div class="final-transcript-content p-3 bg-dark border rounded">
                    <p class="text-light mb-3">${this.cumulativeTranscript}</p>
                    <div class="final-transcript-actions">
                        <button class="btn btn-sm btn-outline-success me-2" onclick="navigator.clipboard.writeText('${this.cumulativeTranscript.replace(/'/g, "\\'")}')">
                            📋 Copy
                        </button>
                    </div>
                </div>
            `;
            
            transcriptContainer.appendChild(finalSection);
        }
    }
}

// Initialize global instance
window.directAudioTranscription = new DirectAudioTranscription();

// Replace any existing recorder references
if (window.realWhisperIntegration) {
    window.realWhisperIntegration.startTranscription = window.directAudioTranscription.startTranscription.bind(window.directAudioTranscription);
    window.realWhisperIntegration.stopTranscription = window.directAudioTranscription.stopTranscription.bind(window.directAudioTranscription);
}