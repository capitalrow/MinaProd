/**
 * Professional Audio Recorder with MediaRecorder API
 * Handles mic permissions, error states, and chunk generation
 */

class ProfessionalRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioStream = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.chunkInterval = null;
        this.sessionId = null;
        
        // Configuration
        this.config = {
            chunkDuration: 1000, // 1 second chunks
            sampleRate: 16000,
            channelCount: 1,
            audioBitsPerSecond: 128000
        };
        
        this.initializeRecorder();
    }
    
    async initializeRecorder() {
        try {
            console.log('🎤 Initializing professional audio recorder...');
            
            // Check browser support
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Browser does not support audio recording');
            }
            
            // Check for MediaRecorder support
            if (!window.MediaRecorder) {
                throw new Error('MediaRecorder API not supported');
            }
            
            console.log('✅ Browser supports audio recording');
            
        } catch (error) {
            console.error('❌ Recorder initialization failed:', error);
            window.toastSystem?.error(`Recording not supported: ${error.message}`);
        }
    }
    
    async requestMicrophonePermission() {
        try {
            console.log('🎤 Requesting microphone permission...');
            
            // Request audio stream with optimal settings
            const constraints = {
                audio: {
                    channelCount: this.config.channelCount,
                    sampleRate: this.config.sampleRate,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            };
            
            this.audioStream = await navigator.mediaDevices.getUserMedia(constraints);
            console.log('✅ Microphone permission granted');
            
            // Determine best MIME type
            const mimeTypes = [
                'audio/webm;codecs=opus',
                'audio/webm',
                'audio/ogg;codecs=opus',
                'audio/mp4'
            ];
            
            let selectedMimeType = 'audio/webm';
            for (const mimeType of mimeTypes) {
                if (MediaRecorder.isTypeSupported(mimeType)) {
                    selectedMimeType = mimeType;
                    console.log(`✅ Using MIME type: ${mimeType}`);
                    break;
                }
            }
            
            // Create MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: selectedMimeType,
                audioBitsPerSecond: this.config.audioBitsPerSecond
            });
            
            // Set up event handlers
            this.setupEventHandlers();
            
            return true;
            
        } catch (error) {
            console.error('❌ Microphone permission failed:', error);
            
            // Provide specific error messages
            if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                window.toastSystem?.error('🎤 Microphone permission denied. Please allow access in your browser settings.');
                this.updateUIStatus('Permission denied - click to retry');
            } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
                window.toastSystem?.error('🎤 No microphone found. Please connect a microphone.');
                this.updateUIStatus('No microphone detected');
            } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
                window.toastSystem?.error('🎤 Microphone is already in use by another application.');
                this.updateUIStatus('Microphone busy');
            } else if (error.name === 'OverconstrainedError') {
                // Try with basic constraints
                console.log('Retrying with basic constraints...');
                this.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                this.mediaRecorder = new MediaRecorder(this.audioStream);
                this.setupEventHandlers();
                return true;
            } else {
                window.toastSystem?.error(`Audio error: ${error.message}`);
                this.updateUIStatus('Recording error');
            }
            
            return false;
        }
    }
    
    setupEventHandlers() {
        if (!this.mediaRecorder) return;
        
        // Collect audio data
        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                this.audioChunks.push(event.data);
                console.log(`📦 Audio chunk collected: ${event.data.size} bytes`);
            }
        };
        
        // Handle recording start
        this.mediaRecorder.onstart = () => {
            console.log('🔴 Recording started');
            this.isRecording = true;
            this.updateUIStatus('Recording...');
            window.toastSystem?.success('Recording started');
            
            // Update UI statistics
            if (window.updateSessionStats) {
                window.updateSessionStats({
                    chunks: this.audioChunks.length,
                    quality: '100%'
                });
            }
        };
        
        // Handle recording stop
        this.mediaRecorder.onstop = () => {
            console.log('⏹️ Recording stopped');
            this.isRecording = false;
            this.processAudioChunks();
            this.updateUIStatus('Processing...');
        };
        
        // Handle errors
        this.mediaRecorder.onerror = (event) => {
            console.error('❌ MediaRecorder error:', event.error);
            window.toastSystem?.error(`Recording error: ${event.error?.message || 'Unknown error'}`);
            this.stopRecording();
        };
    }
    
    async startRecording() {
        try {
            console.log('🎤 Starting recording...');
            
            // Reset state
            this.audioChunks = [];
            this.sessionId = `session_${Date.now()}`;
            
            // Request permission if not already granted
            if (!this.mediaRecorder || this.mediaRecorder.state === 'inactive') {
                const hasPermission = await this.requestMicrophonePermission();
                if (!hasPermission) {
                    return false;
                }
            }
            
            // Start recording
            this.mediaRecorder.start();
            
            // Set up chunking interval
            this.chunkInterval = setInterval(() => {
                if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                    this.mediaRecorder.requestData();
                    this.sendAudioChunk();
                }
            }, this.config.chunkDuration);
            
            return true;
            
        } catch (error) {
            console.error('❌ Failed to start recording:', error);
            window.toastSystem?.error(`Failed to start: ${error.message}`);
            return false;
        }
    }
    
    stopRecording() {
        try {
            console.log('⏹️ Stopping recording...');
            
            // Clear chunk interval
            if (this.chunkInterval) {
                clearInterval(this.chunkInterval);
                this.chunkInterval = null;
            }
            
            // Stop media recorder
            if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                this.mediaRecorder.stop();
            }
            
            // Stop audio tracks
            if (this.audioStream) {
                this.audioStream.getTracks().forEach(track => track.stop());
                this.audioStream = null;
            }
            
            this.isRecording = false;
            this.updateUIStatus('Stopped');
            
        } catch (error) {
            console.error('❌ Error stopping recording:', error);
            window.toastSystem?.error(`Stop error: ${error.message}`);
        }
    }
    
    async sendAudioChunk() {
        if (this.audioChunks.length === 0) return;
        
        try {
            // Create blob from chunks
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            this.audioChunks = []; // Clear sent chunks
            
            // Prepare form data
            const formData = new FormData();
            formData.append('audio', audioBlob, 'chunk.webm');
            formData.append('session_id', this.sessionId);
            formData.append('chunk_index', Date.now().toString());
            
            // Send to backend
            const response = await fetch('/api/transcribe', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ Chunk transcribed:', result);
                
                // Update transcript display
                if (result.transcript && window.updateTranscriptDisplay) {
                    window.updateTranscriptDisplay(result);
                }
                
                // Update statistics
                if (window.updateSessionStats) {
                    window.updateSessionStats({
                        words: result.word_count || 0,
                        chunks: (window.sessionStats?.chunks || 0) + 1,
                        latency: result.processing_time ? `${Math.round(result.processing_time * 1000)}ms` : '0ms'
                    });
                }
            } else {
                console.error('❌ Transcription failed:', response.status);
            }
            
        } catch (error) {
            console.error('❌ Error sending chunk:', error);
        }
    }
    
    async processAudioChunks() {
        if (this.audioChunks.length === 0) {
            console.log('No audio chunks to process');
            return;
        }
        
        try {
            console.log(`Processing ${this.audioChunks.length} audio chunks...`);
            
            // Send final chunk
            await this.sendAudioChunk();
            
            window.toastSystem?.success('Recording completed successfully');
            this.updateUIStatus('Ready');
            
        } catch (error) {
            console.error('❌ Error processing audio:', error);
            window.toastSystem?.error(`Processing error: ${error.message}`);
        }
    }
    
    updateUIStatus(status) {
        // Update status element if it exists
        const statusElement = document.querySelector('.status-text');
        if (statusElement) {
            statusElement.textContent = status;
        }
        
        // Update console log
        console.log(`📊 Status: ${status}`);
    }
    
    getRecordingState() {
        return {
            isRecording: this.isRecording,
            hasPermission: !!this.audioStream,
            mediaRecorderState: this.mediaRecorder?.state || 'inactive',
            chunksCollected: this.audioChunks.length
        };
    }
}

// Initialize global recorder instance
window.professionalRecorder = new ProfessionalRecorder();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProfessionalRecorder;
}

console.log('✅ Professional recorder module loaded');