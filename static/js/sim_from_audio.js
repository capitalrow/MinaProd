/**
 * Audio File Simulation for End-to-End Testing
 * Feeds MP3 through WebAudio → MediaRecorder pipeline identical to mic input
 */

class MinaAudioSimulator {
    constructor() {
        this.isSimulating = false;
        this.audioContext = null;
        this.mediaRecorder = null;
        this.sourceNode = null;
        this.destinationNode = null;
        this.audioElement = null;
        this.recordingStartTime = null;
        this.chunks = [];
        this.timesliceMs = 300;
        
        this.metrics = {
            chunksGenerated: 0,
            totalBytes: 0,
            simulationDuration: 0,
            audioDuration: 0,
            errors: [],
            interimCount: 0,
            finalCount: 0,
            firstInterimTime: null,
            firstFinalTime: null
        };
        
        // Listen for transcription events to track metrics
        this.setupTranscriptionEventListeners();
        
        console.log('🎬 MinaAudioSimulator initialized');
    }
    
    setupTranscriptionEventListeners() {
        // Listen for transcription results to track interim/final counts
        if (window.socket) {
            window.socket.on('transcription_result', (data) => {
                this.trackTranscriptionResult(data);
            });
        }
        
        // Also listen for custom events if available
        window.addEventListener('transcriptionResult', (event) => {
            this.trackTranscriptionResult(event.detail);
        });
    }
    
    trackTranscriptionResult(data) {
        const now = Date.now();
        const isInterim = !data.is_final;
        
        if (isInterim) {
            this.metrics.interimCount++;
            if (!this.metrics.firstInterimTime) {
                this.metrics.firstInterimTime = now;
                console.log(`🎯 First interim received: ${now - this.recordingStartTime}ms after start`);
            }
        } else {
            this.metrics.finalCount++;
            if (!this.metrics.firstFinalTime) {
                this.metrics.firstFinalTime = now;
                console.log(`🎯 First final received: ${now - this.recordingStartTime}ms after start`);
            }
        }
        
        console.log(`📝 ${isInterim ? 'INTERIM' : 'FINAL'}: "${data.text}" (${this.metrics.interimCount}I/${this.metrics.finalCount}F)`);
    }
    
    async startSimulation(audioUrl, options = {}) {
        if (this.isSimulating) {
            console.warn('⚠️ Simulation already running');
            return false;
        }
        
        console.log(`🎬 Starting audio simulation: ${audioUrl}`);
        
        try {
            // Apply options
            this.timesliceMs = options.timesliceMs || 300;
            
            // Reset metrics
            this.resetMetrics();
            
            // Create audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create audio element
            this.audioElement = document.createElement('audio');
            this.audioElement.src = audioUrl;
            this.audioElement.crossOrigin = 'anonymous';
            this.audioElement.preload = 'auto';
            
            // Wait for audio to load
            await this.waitForAudioLoad();
            
            // Setup audio routing
            this.setupAudioRouting();
            
            // Setup media recorder
            await this.setupMediaRecorder();
            
            // Start simulation
            this.isSimulating = true;
            this.recordingStartTime = Date.now();
            this.chunks = [];
            
            // Start recording and playback
            this.mediaRecorder.start(this.timesliceMs);
            this.audioElement.play();
            
            this.metrics.audioDuration = this.audioElement.duration * 1000; // Convert to ms
            
            console.log(`🎬 Simulation started: ${this.audioElement.duration}s audio, ${this.timesliceMs}ms chunks`);
            
            // Auto-stop when audio ends
            this.audioElement.addEventListener('ended', () => {
                console.log('🎬 Audio ended, stopping simulation');
                setTimeout(() => this.stopSimulation(), 1000); // Wait for final chunks
            });
            
            return true;
            
        } catch (error) {
            console.error('❌ Failed to start simulation:', error);
            this.metrics.errors.push({
                timestamp: Date.now(),
                error: error.message,
                type: 'simulation_start'
            });
            this.cleanup();
            return false;
        }
    }
    
    resetMetrics() {
        this.metrics = {
            chunksGenerated: 0,
            totalBytes: 0,
            simulationDuration: 0,
            audioDuration: 0,
            errors: [],
            interimCount: 0,
            finalCount: 0,
            firstInterimTime: null,
            firstFinalTime: null
        };
    }
    
    async waitForAudioLoad() {
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('Audio load timeout'));
            }, 10000);
            
            this.audioElement.addEventListener('loadeddata', () => {
                clearTimeout(timeout);
                console.log(`🎵 Audio loaded: ${this.audioElement.duration}s`);
                resolve();
            });
            
            this.audioElement.addEventListener('error', (e) => {
                clearTimeout(timeout);
                reject(new Error(`Audio load error: ${e.message}`));
            });
        });
    }
    
    setupAudioRouting() {
        // Create audio source from element
        this.sourceNode = this.audioContext.createMediaElementSource(this.audioElement);
        
        // Create destination for MediaRecorder
        this.destinationNode = this.audioContext.createMediaStreamDestination();
        
        // Connect: source → destination
        this.sourceNode.connect(this.destinationNode);
        
        // Also connect to speakers for monitoring (optional)
        if (window.location.hash.includes('monitor')) {
            this.sourceNode.connect(this.audioContext.destination);
        }
        
        console.log('🔗 Audio routing setup complete');
    }
    
    async setupMediaRecorder() {
        const stream = this.destinationNode.stream;
        
        // Check for supported mime types
        const mimeTypes = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/mp4',
            'audio/wav'
        ];
        
        let selectedMimeType = null;
        for (const mimeType of mimeTypes) {
            if (MediaRecorder.isTypeSupported(mimeType)) {
                selectedMimeType = mimeType;
                break;
            }
        }
        
        if (!selectedMimeType) {
            throw new Error('No supported audio mime type found');
        }
        
        console.log(`🎙️ Using mime type: ${selectedMimeType}`);
        
        // Create MediaRecorder
        this.mediaRecorder = new MediaRecorder(stream, {
            mimeType: selectedMimeType,
            audioBitsPerSecond: 128000
        });
        
        // Setup event handlers
        this.mediaRecorder.addEventListener('dataavailable', (event) => {
            this.handleAudioChunk(event.data);
        });
        
        this.mediaRecorder.addEventListener('start', () => {
            console.log('🎙️ MediaRecorder started');
        });
        
        this.mediaRecorder.addEventListener('stop', () => {
            console.log('🎙️ MediaRecorder stopped');
        });
        
        this.mediaRecorder.addEventListener('error', (event) => {
            console.error('❌ MediaRecorder error:', event.error);
            this.metrics.errors.push({
                timestamp: Date.now(),
                error: event.error.message,
                type: 'mediarecorder'
            });
        });
    }
    
    handleAudioChunk(blob) {
        if (!this.isSimulating) return;
        
        console.log(`🎵 Processing chunk ${this.metrics.chunksGenerated + 1}: ${blob.size} bytes`);
        
        this.chunks.push(blob);
        this.metrics.chunksGenerated++;
        this.metrics.totalBytes += blob.size;
        
        // Send chunk through the same pipeline as live mic
        this.sendChunkToTranscription(blob);
    }
    
    async sendChunkToTranscription(blob) {
        try {
            // Convert blob to array buffer for processing
            const arrayBuffer = await blob.arrayBuffer();
            
            // Try multiple integration approaches in order of preference
            let sent = false;
            
            // Approach 1: Enhanced transcription system
            if (window.enhancedTranscriptionSystem && window.enhancedTranscriptionSystem.processAudioChunk) {
                try {
                    await window.enhancedTranscriptionSystem.processAudioChunk(arrayBuffer);
                    sent = true;
                } catch (error) {
                    console.warn('Enhanced system failed, trying fallback:', error.message);
                }
            }
            
            // Approach 2: Basic transcription system
            if (!sent && window.transcriptionSystem && window.transcriptionSystem.sendAudioChunk) {
                try {
                    await window.transcriptionSystem.sendAudioChunk(arrayBuffer);
                    sent = true;
                } catch (error) {
                    console.warn('Basic system failed, trying socket:', error.message);
                }
            }
            
            // Approach 3: Direct WebSocket with same format as existing system
            if (!sent && window.socket && window.socket.connected) {
                try {
                    const base64Audio = await this.blobToBase64(blob);
                    
                    // Use the same payload format as the existing audio file simulator
                    const payload = {
                        session_id: this.getCurrentSessionId(),
                        audio_data_b64: base64Audio,
                        mime_type: blob.type || 'audio/webm',
                        rms: 0.5, // Placeholder RMS value
                        ts_client: Date.now(),
                        is_final_chunk: false
                    };
                    
                    window.socket.emit('audio_chunk', payload);
                    sent = true;
                } catch (error) {
                    console.warn('Socket approach failed:', error.message);
                }
            }
            
            // Approach 4: HTTP API fallback
            if (!sent) {
                try {
                    const formData = new FormData();
                    formData.append('audio', blob, 'chunk.webm');
                    
                    const response = await fetch('/api/transcribe-audio', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        // Manually trigger transcription result event
                        window.dispatchEvent(new CustomEvent('transcriptionResult', {
                            detail: result
                        }));
                        sent = true;
                    }
                } catch (error) {
                    console.warn('HTTP API fallback failed:', error.message);
                }
            }
            
            if (!sent) {
                throw new Error('All transcription approaches failed');
            }
            
        } catch (error) {
            console.error('❌ Failed to send chunk:', error);
            this.metrics.errors.push({
                timestamp: Date.now(),
                error: error.message,
                type: 'chunk_send'
            });
        }
    }
    
    getCurrentSessionId() {
        // Try to get session ID from various possible sources
        if (window.currentSessionId) return window.currentSessionId;
        if (window.sessionId) return window.sessionId;
        if (window.audioFileSimulator && window.audioFileSimulator.sessionId) {
            return window.audioFileSimulator.sessionId;
        }
        return 'sim_' + Date.now();
    }
    
    async blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }
    
    stopSimulation() {
        if (!this.isSimulating) {
            console.warn('⚠️ No simulation running');
            return false;
        }
        
        console.log('🛑 Stopping audio simulation');
        
        this.isSimulating = false;
        this.metrics.simulationDuration = Date.now() - this.recordingStartTime;
        
        // Stop recording
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
        
        // Stop audio playback
        if (this.audioElement) {
            this.audioElement.pause();
            this.audioElement.currentTime = 0;
        }
        
        // Send final chunk signal if using socket
        if (window.socket && window.socket.connected) {
            try {
                const finalPayload = {
                    session_id: this.getCurrentSessionId(),
                    audio_data_b64: '',
                    mime_type: 'audio/webm',
                    rms: 0.0,
                    ts_client: Date.now(),
                    is_final_chunk: true
                };
                
                window.socket.emit('audio_chunk', finalPayload);
                console.log('🏁 Final chunk signal sent');
            } catch (error) {
                console.warn('Failed to send final chunk signal:', error);
            }
        }
        
        // Cleanup
        this.cleanup();
        
        const metrics = this.getMetrics();
        console.log('📊 Simulation metrics:', metrics);
        
        return true;
    }
    
    cleanup() {
        // Close audio context
        if (this.audioContext && this.audioContext.state !== 'closed') {
            this.audioContext.close().catch(console.error);
        }
        
        // Clean up nodes
        this.sourceNode = null;
        this.destinationNode = null;
        this.mediaRecorder = null;
        this.audioElement = null;
    }
    
    getMetrics() {
        const now = Date.now();
        const interimLatency = this.metrics.firstInterimTime ? 
            this.metrics.firstInterimTime - this.recordingStartTime : null;
        const finalLatency = this.metrics.firstFinalTime ? 
            this.metrics.firstFinalTime - this.recordingStartTime : null;
        
        return {
            ...this.metrics,
            isSimulating: this.isSimulating,
            chunksInBuffer: this.chunks.length,
            avgChunkSize: this.metrics.chunksGenerated > 0 ? 
                Math.round(this.metrics.totalBytes / this.metrics.chunksGenerated) : 0,
            firstInterimLatency: interimLatency,
            firstFinalLatency: finalLatency,
            currentTime: this.audioElement ? this.audioElement.currentTime : 0
        };
    }
    
    // Validation helpers for tests
    validateResults() {
        const metrics = this.getMetrics();
        const validation = {
            success: true,
            errors: [],
            warnings: []
        };
        
        // Check for minimum chunks
        if (metrics.chunksGenerated < 10) {
            validation.errors.push(`Too few chunks generated: ${metrics.chunksGenerated} < 10`);
            validation.success = false;
        }
        
        // Check for interim responses
        if (metrics.interimCount === 0) {
            validation.errors.push('No interim responses received');
            validation.success = false;
        }
        
        // Check for final responses
        if (metrics.finalCount === 0) {
            validation.errors.push('No final responses received');
            validation.success = false;
        }
        
        // Check interim latency
        if (metrics.firstInterimLatency > 2000) {
            validation.warnings.push(`High interim latency: ${metrics.firstInterimLatency}ms > 2000ms`);
        }
        
        // Check for errors
        if (metrics.errors.length > 0) {
            validation.warnings.push(`${metrics.errors.length} errors occurred during simulation`);
        }
        
        return validation;
    }
}

// Legacy compatibility - keep existing simulator but enhance it
class AudioFileSimulator {
    constructor() {
        // Delegate to new simulator
        this.newSimulator = new MinaAudioSimulator();
        
        // Legacy properties for compatibility
        this.audioContext = null;
        this.mediaRecorder = null;
        this.sourceNode = null;
        this.analyserNode = null;
        this.mediaStreamDestination = null;
        this.audioElement = null;
        this.isRecording = false;
        this.sessionId = null;
        
        this.metrics = {
            chunksProcessed: 0,
            startTime: null,
            firstInterimReceived: null,
            interimCount: 0,
            finalCount: 0,
            rmsValues: []
        };
        
        this.debug = true;
        this.log("🎵 AudioFileSimulator (legacy) initialized");
    }
    
    log(message, ...args) {
        if (this.debug) {
            console.log(`[AudioSim] ${message}`, ...args);
        }
    }
    
    // Legacy methods that delegate to new simulator
    async startSimulation() {
        this.log("🚀 Starting legacy simulation (delegating to new simulator)");
        
        // Use default MP3 file
        const audioUrl = '/static/test/djvlad_120s.mp3';
        const result = await this.newSimulator.startSimulation(audioUrl, { timesliceMs: 300 });
        
        if (result) {
            this.isRecording = true;
            this.sessionId = this.newSimulator.getCurrentSessionId();
            this.metrics.startTime = Date.now();
            
            return {
                success: true,
                sessionId: this.sessionId,
                message: "Legacy simulation started"
            };
        } else {
            return {
                success: false,
                error: "Failed to start simulation"
            };
        }
    }
    
    async stopSimulation() {
        this.log("⏹️ Stopping legacy simulation");
        
        const result = this.newSimulator.stopSimulation();
        this.isRecording = false;
        
        const newMetrics = this.newSimulator.getMetrics();
        const duration = newMetrics.simulationDuration / 1000;
        
        return {
            success: result,
            sessionId: this.sessionId,
            duration: duration,
            chunksProcessed: newMetrics.chunksGenerated,
            averageRMS: 0.5 // Placeholder
        };
    }
    
    getMetrics() {
        const newMetrics = this.newSimulator.getMetrics();
        return {
            ...this.metrics,
            isRecording: this.isRecording,
            sessionId: this.sessionId,
            // Map new metrics to legacy format
            chunksProcessed: newMetrics.chunksGenerated,
            interimCount: newMetrics.interimCount,
            finalCount: newMetrics.finalCount
        };
    }
}

// Global instances for compatibility
window.minaSimulator = new MinaAudioSimulator();
window.audioFileSimulator = new AudioFileSimulator();

// Global API functions (new interface)
window._minaSimStart = async function(audioUrl, options = {}) {
    return await window.minaSimulator.startSimulation(audioUrl, options);
};

window._minaSimStop = function() {
    return window.minaSimulator.stopSimulation();
};

window._minaSimMetrics = function() {
    return window.minaSimulator.getMetrics();
};

window._minaSimValidate = function() {
    return window.minaSimulator.validateResults();
};

window._minaSimInfo = function() {
    const metrics = window.minaSimulator.getMetrics();
    return {
        audio: window.minaSimulator.audioElement ? {
            duration: window.minaSimulator.audioElement.duration,
            currentTime: window.minaSimulator.audioElement.currentTime,
            src: window.minaSimulator.audioElement.src,
            readyState: window.minaSimulator.audioElement.readyState,
            paused: window.minaSimulator.audioElement.paused
        } : null,
        context: window.minaSimulator.audioContext ? {
            state: window.minaSimulator.audioContext.state,
            sampleRate: window.minaSimulator.audioContext.sampleRate,
            currentTime: window.minaSimulator.audioContext.currentTime
        } : null,
        metrics: metrics
    };
};

// Legacy helper functions (for compatibility)
window.simFromAudioStart = async function() {
    console.log("🎬 Starting legacy file simulation...");
    return await window.audioFileSimulator.startSimulation();
};

window.simFromAudioStop = async function() {
    console.log("⏹️ Stopping legacy file simulation...");
    return await window.audioFileSimulator.stopSimulation();
};

// Auto-initialize if we're in test mode
if (window.location.search.includes('test=audio') || window.location.hash.includes('test')) {
    console.log('🎬 Audio simulation ready - use _minaSimStart(url) to begin');
    console.log('Example: _minaSimStart("/static/test/djvlad_120s.mp3", {timesliceMs: 300})');
}

console.log('🎬 Enhanced audio simulation system loaded');

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
