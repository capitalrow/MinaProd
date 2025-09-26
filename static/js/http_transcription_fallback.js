/**
 * HTTP-BASED TRANSCRIPTION FALLBACK
 * When WebSocket is not available, use HTTP endpoints for transcription
 */

class HttpTranscriptionFallback {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.mediaStream = null;
        this.recordingChunks = [];
        this.sessionId = null;
        this.chunkCounter = 0;
        this.recordingStartTime = null;
        
        // Configuration
        this.config = {
            chunkDurationMs: 2000, // 2 second chunks
            maxRetries: 3,
            retryDelay: 1000,
            maxChunkSize: 1024 * 1024, // 1MB
            timeout: 10000 // 10 second timeout
        };
        
        // Statistics
        this.stats = {
            totalChunks: 0,
            successfulChunks: 0,
            failedChunks: 0,
            totalWords: 0,
            averageLatency: 0,
            totalLatency: 0
        };
        
        // UI update callbacks
        this.onStatusUpdate = null;
        this.onTranscriptionResult = null;
        this.onStatsUpdate = null;
        this.onError = null;
    }
    
    async initialize() {
        console.log('🔄 Initializing HTTP Transcription Fallback');
        
        // Generate session ID
        this.sessionId = 'http_' + Date.now() + '_' + Math.random().toString(36).substring(2);
        
        // Create session via HTTP
        try {
            const response = await fetch('/sessions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    mode: 'http_fallback',
                    config: this.config
                })
            });
            
            if (!response.ok) {
                throw new Error(`Session creation failed: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('✅ HTTP session created:', result);
            
            this.updateStatus('ready', 'HTTP transcription ready');
            return true;
            
        } catch (error) {
            console.error('❌ HTTP session creation failed:', error);
            this.updateStatus('error', 'Failed to initialize HTTP transcription');
            this.handleError(error);
            return false;
        }
    }
    
    async startRecording() {
        if (this.isRecording) {
            console.warn('Recording already in progress');
            return false;
        }
        
        try {
            console.log('🎙️ Starting HTTP recording...');
            this.updateStatus('connecting', 'Requesting microphone access');
            
            // Get media stream
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            // Set up MediaRecorder
            const options = { mimeType: 'audio/webm;codecs=opus' };
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                options.mimeType = 'audio/webm';
                if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                    options.mimeType = '';
                }
            }
            
            this.mediaRecorder = new MediaRecorder(this.mediaStream, options);
            this.recordingChunks = [];
            this.chunkCounter = 0;
            this.recordingStartTime = Date.now();
            
            // Set up event handlers
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    this.recordingChunks.push(event.data);
                    this.processAudioChunk(event.data);
                }
            };
            
            this.mediaRecorder.onstart = () => {
                console.log('🎙️ Recording started');
                this.isRecording = true;
                this.updateStatus('recording', 'Recording in progress');
                
                // Start chunk interval
                this.startChunkInterval();
            };
            
            this.mediaRecorder.onstop = () => {
                console.log('⏹️ Recording stopped');
                this.isRecording = false;
                this.updateStatus('processing', 'Processing final audio');
                this.processRemainingAudio();
            };
            
            this.mediaRecorder.onerror = (error) => {
                console.error('❌ MediaRecorder error:', error);
                this.handleError(error);
            };
            
            // Start recording
            this.mediaRecorder.start();
            
            return true;
            
        } catch (error) {
            console.error('❌ Failed to start HTTP recording:', error);
            this.updateStatus('error', 'Failed to start recording');
            this.handleError(error);
            return false;
        }
    }
    
    startChunkInterval() {
        // Request data every configured interval
        this.chunkInterval = setInterval(() => {
            if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                this.mediaRecorder.requestData();
            }
        }, this.config.chunkDurationMs);
    }
    
    async processAudioChunk(audioBlob) {
        this.chunkCounter++;
        const chunkId = this.chunkCounter;
        const timestamp = Date.now();
        
        console.log(`🎵 Processing audio chunk ${chunkId} (${audioBlob.size} bytes)`);
        
        try {
            // Convert blob to base64 for transmission
            const base64Audio = await this.blobToBase64(audioBlob);
            
            const startTime = Date.now();
            
            // Send to server via HTTP
            const response = await fetch('/api/transcribe-audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    chunk_id: chunkId,
                    audio_data: base64Audio,
                    mime_type: audioBlob.type,
                    size: audioBlob.size,
                    timestamp: timestamp,
                    is_final: false
                }),
                signal: AbortSignal.timeout(this.config.timeout)
            });
            
            const latency = Date.now() - startTime;
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Update statistics
            this.stats.totalChunks++;
            this.stats.successfulChunks++;
            this.stats.totalLatency += latency;
            this.stats.averageLatency = this.stats.totalLatency / this.stats.successfulChunks;
            
            // Process transcription result
            if (result.text && result.text.trim()) {
                const words = result.text.trim().split(/\\s+/).length;
                this.stats.totalWords += words;
                
                console.log(`✅ Chunk ${chunkId} processed: "${result.text}" (${latency}ms)`);
                
                // Call transcription callback
                if (this.onTranscriptionResult) {
                    this.onTranscriptionResult({
                        text: result.text,
                        confidence: result.confidence || 0.9,
                        is_final: result.is_final || false,
                        timestamp: timestamp,
                        latency: latency,
                        chunk_id: chunkId
                    });
                }
            }
            
            // Update UI stats
            this.updateStats();
            
        } catch (error) {
            console.error(`❌ Failed to process chunk ${chunkId}:`, error);
            this.stats.failedChunks++;
            this.handleError(error);
            
            // Try retry logic for failed chunks
            if (this.config.maxRetries > 0) {
                setTimeout(() => {
                    this.retryChunk(audioBlob, chunkId, 1);
                }, this.config.retryDelay);
            }
        }
    }
    
    async retryChunk(audioBlob, chunkId, attempt) {
        if (attempt > this.config.maxRetries) {
            console.error(`❌ Chunk ${chunkId} failed after ${this.config.maxRetries} attempts`);
            return;
        }
        
        console.log(`🔄 Retrying chunk ${chunkId} (attempt ${attempt})`);
        
        try {
            await this.processAudioChunk(audioBlob);
        } catch (error) {
            setTimeout(() => {
                this.retryChunk(audioBlob, chunkId, attempt + 1);
            }, this.config.retryDelay * attempt);
        }
    }
    
    async blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const base64 = reader.result.split(',')[1]; // Remove data:audio/webm;base64, prefix
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }
    
    async stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) {
            return false;
        }
        
        console.log('⏹️ Stopping HTTP recording...');
        
        // Clear chunk interval
        if (this.chunkInterval) {
            clearInterval(this.chunkInterval);
            this.chunkInterval = null;
        }
        
        // Stop media recorder
        this.mediaRecorder.stop();
        
        // Stop media stream
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
        }
        
        return true;
    }
    
    async processRemainingAudio() {
        if (this.recordingChunks.length === 0) {
            this.updateStatus('ready', 'Recording complete');
            return;
        }
        
        // Combine all chunks for final processing
        const finalBlob = new Blob(this.recordingChunks, { type: 'audio/webm' });
        
        try {
            const base64Audio = await this.blobToBase64(finalBlob);
            
            const response = await fetch('/api/transcribe-audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    audio_data: base64Audio,
                    mime_type: finalBlob.type,
                    size: finalBlob.size,
                    timestamp: Date.now(),
                    is_final: true
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ Final transcription:', result);
                
                if (this.onTranscriptionResult) {
                    this.onTranscriptionResult({
                        text: result.text,
                        confidence: result.confidence || 0.9,
                        is_final: true,
                        timestamp: Date.now()
                    });
                }
            }
            
            this.updateStatus('ready', 'Transcription complete');
            
        } catch (error) {
            console.error('❌ Failed to process final audio:', error);
            this.updateStatus('error', 'Failed to process final audio');
            this.handleError(error);
        }
    }
    
    updateStatus(status, message) {
        console.log(`📊 Status: ${status} - ${message}`);
        
        if (this.onStatusUpdate) {
            this.onStatusUpdate(status, message);
        }
        
        // Update UI elements directly
        const statusElements = document.querySelectorAll('.system-status, [data-status]');
        statusElements.forEach(el => {
            el.textContent = message;
            el.className = el.className.replace(/status-\\w+/g, '') + ` status-${status}`;
        });
    }
    
    updateStats() {
        const statsData = {
            chunks: this.stats.totalChunks,
            words: this.stats.totalWords,
            accuracy: this.stats.successfulChunks / Math.max(1, this.stats.totalChunks) * 100,
            latency: Math.round(this.stats.averageLatency),
            quality: this.calculateQualityScore()
        };
        
        if (this.onStatsUpdate) {
            this.onStatsUpdate(statsData);
        }
        
        // Update UI metrics
        this.updateUIMetrics(statsData);
    }
    
    updateUIMetrics(stats) {
        // Update metrics display
        const metricsMap = {
            'chunks': stats.chunks,
            'words': stats.words,
            'accuracy': `${Math.round(stats.accuracy)}%`,
            'latency': `${stats.latency}ms`,
            'quality': `${Math.round(stats.quality)}%`
        };
        
        Object.entries(metricsMap).forEach(([key, value]) => {
            const elements = document.querySelectorAll(`[data-metric="${key}"], .metric-${key}, #${key}Metric`);
            elements.forEach(el => {
                if (el.textContent !== value.toString()) {
                    el.textContent = value;
                }
            });
        });
        
        // Update duration
        if (this.recordingStartTime && this.isRecording) {
            const duration = Math.floor((Date.now() - this.recordingStartTime) / 1000);
            const minutes = Math.floor(duration / 60);
            const seconds = duration % 60;
            const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            const durationElements = document.querySelectorAll('[data-metric="duration"], .metric-duration, #durationMetric');
            durationElements.forEach(el => {
                el.textContent = timeString;
            });
        }
    }
    
    calculateQualityScore() {
        const successRate = this.stats.successfulChunks / Math.max(1, this.stats.totalChunks);
        const latencyScore = Math.max(0, 1 - (this.stats.averageLatency - 1000) / 5000); // Good if < 1s
        return (successRate * 0.7 + latencyScore * 0.3) * 100;
    }
    
    handleError(error) {
        console.error('❌ HTTP Transcription Error:', error);
        
        if (this.onError) {
            this.onError(error);
        }
        
        // Show user-friendly error message
        const errorMsg = this.getErrorMessage(error);
        this.updateStatus('error', errorMsg);
    }
    
    getErrorMessage(error) {
        const errorStr = error.toString().toLowerCase();
        
        if (errorStr.includes('timeout')) {
            return 'Request timeout - please check your connection';
        } else if (errorStr.includes('network')) {
            return 'Network error - please check your connection';
        } else if (errorStr.includes('permission')) {
            return 'Microphone permission denied';
        } else if (errorStr.includes('not found')) {
            return 'Microphone not found';
        } else {
            return 'Transcription error - please try again';
        }
    }
    
    // Public API
    getStats() {
        return { ...this.stats };
    }
    
    isActive() {
        return this.isRecording;
    }
    
    getSessionId() {
        return this.sessionId;
    }
}

// Export for use
window.HttpTranscriptionFallback = HttpTranscriptionFallback;

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
