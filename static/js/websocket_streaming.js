/**
 * WebSocket Audio Streaming Manager
 * Handles real-time audio streaming to server via Socket.IO
 * Integrates with VAD processor for optimized transmission
 */

class WebSocketStreaming {
    constructor(options = {}) {
        this.config = {
            socket: options.socket || null,
            chunkDuration: options.chunkDuration || 1000, // ms
            sampleRate: options.sampleRate || 16000,
            enableVAD: options.enableVAD !== false,
            vadThreshold: options.vadThreshold || 0.5,
            enableCompression: options.enableCompression !== false,
            maxRetries: options.maxRetries || 3,
            retryDelay: options.retryDelay || 1000,
            bufferSize: options.bufferSize || 8192,
            enableBackpressure: options.enableBackpressure !== false,
            maxPendingChunks: options.maxPendingChunks || 5
        };
        
        // Audio streaming state
        this.isStreaming = false;
        this.isPaused = false;
        this.sessionId = null;
        
        // Buffering and transmission
        this.audioBuffer = [];
        this.pendingChunks = new Map();
        this.chunkSequence = 0;
        this.lastTransmissionTime = 0;
        
        // Connection management
        this.connectionState = 'disconnected';
        this.retryCount = 0;
        this.retryTimer = null;
        
        // Statistics and monitoring
        this.stats = {
            totalChunksSent: 0,
            totalBytesTransmitted: 0,
            averageLatency: 0,
            transmissionErrors: 0,
            vadFilteredChunks: 0,
            backpressureEvents: 0,
            connectionDrops: 0
        };
        
        // Callback functions
        this.onConnectionChange = null;
        this.onTransmissionStats = null;
        this.onError = null;
        
        // Initialize
        this.initializeSocket();
        
        console.log('WebSocketStreaming initialized with config:', this.config);
    }
    
    initializeSocket() {
        if (!this.config.socket) {
            console.error('Socket.IO instance required for WebSocket streaming');
            return;
        }
        
        this.socket = this.config.socket;
        
        // Set up socket event handlers
        this.socket.on('connect', () => {
            this.handleConnectionChange('connected');
        });
        
        this.socket.on('disconnect', (reason) => {
            this.handleConnectionChange('disconnected', reason);
        });
        
        this.socket.on('connect_error', (error) => {
            this.handleConnectionError(error);
        });
        
        this.socket.on('audio_chunk_ack', (data) => {
            this.handleChunkAcknowledgment(data);
        });
        
        this.socket.on('backpressure_warning', (data) => {
            this.handleBackpressureWarning(data);
        });
        
        console.log('Socket event handlers registered');
    }
    
    async startStreaming(sessionId) {
        try {
            console.log('Starting audio streaming...', { sessionId });
            
            if (this.isStreaming) {
                console.warn('Streaming already in progress');
                return false;
            }
            
            this.sessionId = sessionId;
            this.isStreaming = true;
            this.isPaused = false;
            
            // Reset statistics
            this.resetStatistics();
            
            // Initialize MediaRecorder for audio capture
            await this.initializeMediaRecorder();
            
            // Start transmission loop
            this.startTransmissionLoop();
            
            console.log('Audio streaming started successfully');
            return true;
            
        } catch (error) {
            console.error('Failed to start streaming:', error);
            this.isStreaming = false;
            
            if (this.onError) {
                this.onError(error);
            }
            
            throw error;
        }
    }
    
    async initializeMediaRecorder() {
        try {
            // Get audio stream with specific constraints
            const constraints = {
                audio: {
                    sampleRate: this.config.sampleRate,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: false // We handle this in VAD processor
                }
            };
            
            this.mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
            
            // Create MediaRecorder for chunked audio capture
            const options = {
                mimeType: this.getSupportedMimeType(),
                audioBitsPerSecond: this.config.sampleRate * 16 // 16-bit audio
            };
            
            this.mediaRecorder = new MediaRecorder(this.mediaStream, options);
            
            // Set up MediaRecorder event handlers
            this.mediaRecorder.ondataavailable = (event) => {
                this.handleAudioData(event.data);
            };
            
            this.mediaRecorder.onerror = (error) => {
                console.error('MediaRecorder error:', error);
                if (this.onError) {
                    this.onError(error);
                }
            };
            
            // Start recording with specified interval
            this.mediaRecorder.start(this.config.chunkDuration);
            
            console.log('MediaRecorder initialized and started');
            
        } catch (error) {
            console.error('Failed to initialize MediaRecorder:', error);
            throw error;
        }
    }
    
    getSupportedMimeType() {
        const mimeTypes = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/mp4',
            'audio/wav'
        ];
        
        for (const mimeType of mimeTypes) {
            if (MediaRecorder.isTypeSupported(mimeType)) {
                console.log('Using mime type:', mimeType);
                return mimeType;
            }
        }
        
        console.warn('No supported mime type found, using default');
        return '';
    }
    
    startTransmissionLoop() {
        this.transmissionInterval = setInterval(() => {
            this.processAudioBuffer();
        }, Math.floor(this.config.chunkDuration / 4)); // Process 4x faster than chunk duration
        
        console.log('Transmission loop started');
    }
    
    handleAudioData(audioBlob) {
        if (!this.isStreaming || this.isPaused) return;
        
        const timestamp = Date.now();
        
        // Convert blob to array buffer
        audioBlob.arrayBuffer().then(arrayBuffer => {
            const audioData = new Uint8Array(arrayBuffer);
            
            // Add to buffer with metadata
            this.audioBuffer.push({
                data: audioData,
                timestamp: timestamp,
                sequence: this.chunkSequence++,
                size: audioData.byteLength
            });
            
            // Process immediately if buffer is getting full
            if (this.audioBuffer.length >= this.config.bufferSize) {
                this.processAudioBuffer();
            }
        }).catch(error => {
            console.error('Failed to process audio data:', error);
        });
    }
    
    processAudioBuffer() {
        if (!this.isStreaming || this.isPaused || this.audioBuffer.length === 0) return;
        
        // Check for backpressure
        if (this.config.enableBackpressure && this.pendingChunks.size >= this.config.maxPendingChunks) {
            this.stats.backpressureEvents++;
            console.warn('Backpressure detected, skipping transmission');
            return;
        }
        
        // Get next chunk from buffer
        const chunk = this.audioBuffer.shift();
        if (!chunk) return;
        
        // Apply VAD filtering if enabled
        if (this.config.enableVAD && this.shouldFilterChunk(chunk)) {
            this.stats.vadFilteredChunks++;
            return;
        }
        
        // Transmit chunk
        this.transmitAudioChunk(chunk);
    }
    
    shouldFilterChunk(chunk) {
        // In a real implementation, this would integrate with VAD results
        // For now, we'll use a simple energy-based filter
        
        // Convert audio data to Float32Array for analysis
        const float32Data = new Float32Array(chunk.data.buffer);
        
        // Calculate RMS energy
        let sum = 0;
        for (let i = 0; i < float32Data.length; i++) {
            sum += float32Data[i] * float32Data[i];
        }
        const rms = Math.sqrt(sum / float32Data.length);
        
        // Filter out low-energy chunks
        return rms < this.config.vadThreshold * 0.01;
    }
    
    async transmitAudioChunk(chunk) {
        try {
            const transmissionStartTime = Date.now();
            
            // Prepare chunk data
            const chunkData = {
                session_id: this.sessionId,
                audio_data: this.encodeAudioData(chunk.data),
                timestamp: chunk.timestamp,
                sequence: chunk.sequence,
                size: chunk.size,
                format: 'webm', // or detected format
                sample_rate: this.config.sampleRate
            };
            
            // Add to pending chunks for acknowledgment tracking
            this.pendingChunks.set(chunk.sequence, {
                chunk: chunkData,
                transmissionTime: transmissionStartTime,
                retries: 0
            });
            
            // Emit chunk to server
            this.socket.emit('audio_chunk', chunkData);
            
            // Update statistics
            this.stats.totalChunksSent++;
            this.stats.totalBytesTransmitted += chunk.size;
            this.lastTransmissionTime = transmissionStartTime;
            
            // Set timeout for acknowledgment
            setTimeout(() => {
                this.handleChunkTimeout(chunk.sequence);
            }, 5000); // 5 second timeout
            
        } catch (error) {
            console.error('Failed to transmit audio chunk:', error);
            this.stats.transmissionErrors++;
            
            if (this.onError) {
                this.onError(error);
            }
        }
    }
    
    encodeAudioData(audioData) {
        if (this.config.enableCompression) {
            // Apply compression if enabled
            return this.compressAudioData(audioData);
        }
        
        // Convert to base64 for transmission
        return btoa(String.fromCharCode(...audioData));
    }
    
    compressAudioData(audioData) {
        // Simple compression using RLE for silence
        // In production, you might want to use more sophisticated compression
        
        const compressed = [];
        let lastValue = audioData[0];
        let count = 1;
        
        for (let i = 1; i < audioData.length; i++) {
            if (audioData[i] === lastValue && count < 255) {
                count++;
            } else {
                compressed.push(count, lastValue);
                lastValue = audioData[i];
                count = 1;
            }
        }
        
        compressed.push(count, lastValue);
        
        // Convert to base64
        const compressedArray = new Uint8Array(compressed);
        return btoa(String.fromCharCode(...compressedArray));
    }
    
    handleChunkAcknowledgment(data) {
        const sequence = data.sequence;
        const pending = this.pendingChunks.get(sequence);
        
        if (pending) {
            // Calculate latency
            const latency = Date.now() - pending.transmissionTime;
            this.updateLatencyStats(latency);
            
            // Remove from pending
            this.pendingChunks.delete(sequence);
            
            console.debug(`Chunk ${sequence} acknowledged in ${latency}ms`);
        }
    }
    
    handleChunkTimeout(sequence) {
        const pending = this.pendingChunks.get(sequence);
        
        if (pending && pending.retries < this.config.maxRetries) {
            // Retry transmission
            pending.retries++;
            console.warn(`Retrying chunk ${sequence} (attempt ${pending.retries})`);
            
            this.socket.emit('audio_chunk', pending.chunk);
            
            // Set new timeout
            setTimeout(() => {
                this.handleChunkTimeout(sequence);
            }, this.config.retryDelay * pending.retries);
            
        } else if (pending) {
            // Max retries reached, remove from pending
            this.pendingChunks.delete(sequence);
            this.stats.transmissionErrors++;
            
            console.error(`Failed to transmit chunk ${sequence} after ${this.config.maxRetries} attempts`);
        }
    }
    
    handleBackpressureWarning(data) {
        console.warn('Server backpressure warning:', data);
        
        // Temporarily reduce transmission rate
        if (this.transmissionInterval) {
            clearInterval(this.transmissionInterval);
            this.transmissionInterval = setInterval(() => {
                this.processAudioBuffer();
            }, this.config.chunkDuration); // Reduce to normal chunk duration
            
            // Restore normal rate after delay
            setTimeout(() => {
                if (this.transmissionInterval) {
                    clearInterval(this.transmissionInterval);
                    this.startTransmissionLoop();
                }
            }, data.backoff_duration || 5000);
        }
    }
    
    handleConnectionChange(state, reason) {
        const prevState = this.connectionState;
        this.connectionState = state;
        
        console.log(`Connection state changed: ${prevState} -> ${state}`, { reason });
        
        if (state === 'connected' && prevState !== 'connected') {
            this.retryCount = 0;
            if (this.retryTimer) {
                clearTimeout(this.retryTimer);
                this.retryTimer = null;
            }
        } else if (state === 'disconnected' && this.isStreaming) {
            this.stats.connectionDrops++;
            this.scheduleReconnection();
        }
        
        if (this.onConnectionChange) {
            this.onConnectionChange(state, reason);
        }
    }
    
    handleConnectionError(error) {
        console.error('Connection error:', error);
        this.stats.transmissionErrors++;
        
        if (this.onError) {
            this.onError(error);
        }
    }
    
    scheduleReconnection() {
        if (this.retryCount >= this.config.maxRetries) {
            console.error('Max reconnection attempts reached');
            this.stopStreaming();
            return;
        }
        
        const delay = this.config.retryDelay * Math.pow(2, this.retryCount); // Exponential backoff
        this.retryCount++;
        
        console.log(`Scheduling reconnection attempt ${this.retryCount} in ${delay}ms`);
        
        this.retryTimer = setTimeout(() => {
            if (this.socket && this.socket.disconnected) {
                this.socket.connect();
            }
        }, delay);
    }
    
    updateLatencyStats(latency) {
        const alpha = 0.1; // Smoothing factor for running average
        this.stats.averageLatency = (1 - alpha) * this.stats.averageLatency + alpha * latency;
    }
    
    pauseStreaming() {
        if (!this.isStreaming || this.isPaused) return;
        
        this.isPaused = true;
        
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.pause();
        }
        
        console.log('Audio streaming paused');
    }
    
    resumeStreaming() {
        if (!this.isStreaming || !this.isPaused) return;
        
        this.isPaused = false;
        
        if (this.mediaRecorder && this.mediaRecorder.state === 'paused') {
            this.mediaRecorder.resume();
        }
        
        console.log('Audio streaming resumed');
    }
    
    async stopStreaming() {
        console.log('Stopping audio streaming...');
        
        this.isStreaming = false;
        this.isPaused = false;
        
        // Clear transmission loop
        if (this.transmissionInterval) {
            clearInterval(this.transmissionInterval);
            this.transmissionInterval = null;
        }
        
        // Clear retry timer
        if (this.retryTimer) {
            clearTimeout(this.retryTimer);
            this.retryTimer = null;
        }
        
        // Stop MediaRecorder
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
        
        // Stop media stream
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
        
        // Process remaining buffer
        while (this.audioBuffer.length > 0) {
            const chunk = this.audioBuffer.shift();
            if (chunk) {
                await this.transmitAudioChunk(chunk);
            }
        }
        
        // Clear pending chunks
        this.pendingChunks.clear();
        
        console.log('Audio streaming stopped');
    }
    
    getStatistics() {
        return {
            ...this.stats,
            connectionState: this.connectionState,
            isStreaming: this.isStreaming,
            isPaused: this.isPaused,
            bufferSize: this.audioBuffer.length,
            pendingChunks: this.pendingChunks.size,
            retryCount: this.retryCount,
            lastTransmissionTime: this.lastTransmissionTime
        };
    }
    
    resetStatistics() {
        this.stats = {
            totalChunksSent: 0,
            totalBytesTransmitted: 0,
            averageLatency: 0,
            transmissionErrors: 0,
            vadFilteredChunks: 0,
            backpressureEvents: 0,
            connectionDrops: 0
        };
    }
    
    updateConfig(newConfig) {
        Object.assign(this.config, newConfig);
        console.log('WebSocket streaming configuration updated:', newConfig);
    }
    
    // Utility methods
    static checkWebRTCSupport() {
        return !!(navigator.mediaDevices && 
                 navigator.mediaDevices.getUserMedia && 
                 window.MediaRecorder);
    }
    
    static async getAvailableAudioInputs() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            return devices.filter(device => device.kind === 'audioinput');
        } catch (error) {
            console.error('Failed to enumerate audio devices:', error);
            return [];
        }
    }
}

// Export for use in other modules
window.WebSocketStreaming = WebSocketStreaming;

// Export as module if in Node.js environment
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketStreaming;
}
