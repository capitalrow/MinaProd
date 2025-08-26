/**
 * Browser Mic-Path Simulation using WebAudio API
 * Simulates real microphone input from a loaded audio file
 * Uses same MediaRecorder pathway as real mic for exact pipeline testing
 */

class AudioFileSimulator {
    constructor() {
        this.audioContext = null;
        this.mediaRecorder = null;
        this.sourceNode = null;
        this.analyserNode = null;
        this.mediaStreamDestination = null;
        this.audioElement = null;
        this.isRecording = false;
        this.sessionId = null;
        
        // Metrics tracking
        this.metrics = {
            chunksProcessed: 0,
            startTime: null,
            firstInterimReceived: null,
            interimCount: 0,
            finalCount: 0,
            rmsValues: []
        };
        
        // Debug logging
        this.debug = true;
        
        this.log("🎵 AudioFileSimulator initialized");
    }
    
    log(message, ...args) {
        if (this.debug) {
            console.log(`[AudioSim] ${message}`, ...args);
        }
    }
    
    error(message, ...args) {
        console.error(`[AudioSim] ❌ ${message}`, ...args);
    }
    
    async initializeAudioGraph() {
        // Initialize WebAudio graph: AudioContext → MediaElementSource → AnalyserNode → MediaStreamDestination
        try {
            this.log("🔧 Initializing WebAudio graph...");
            
            // Create audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create hidden audio element
            this.audioElement = document.createElement('audio');
            this.audioElement.src = '/static/test/podcast.mp3';
            this.audioElement.crossOrigin = 'anonymous';
            this.audioElement.preload = 'auto';
            
            // Wait for audio to be loadable
            await new Promise((resolve, reject) => {
                this.audioElement.addEventListener('canplay', resolve);
                this.audioElement.addEventListener('error', reject);
                this.audioElement.load();
            });
            
            this.log("✅ Audio file loaded successfully");
            
            // Create audio graph
            this.sourceNode = this.audioContext.createMediaElementSource(this.audioElement);
            this.analyserNode = this.audioContext.createAnalyser();
            this.mediaStreamDestination = this.audioContext.createMediaStreamDestination();
            
            // Configure analyser for RMS calculation
            this.analyserNode.fftSize = 2048;
            this.analyserNode.smoothingTimeConstant = 0.8;
            
            // Connect graph: source → analyser → destination
            this.sourceNode.connect(this.analyserNode);
            this.analyserNode.connect(this.mediaStreamDestination);
            
            this.log("✅ WebAudio graph connected successfully");
            return true;
            
        } catch (error) {
            this.error("Failed to initialize audio graph:", error);
            throw error;
        }
    }
    
    calculateRMS() {
        // Calculate RMS from AnalyserNode - same as real mic path
        if (!this.analyserNode) return 0.5;
        
        const bufferLength = this.analyserNode.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        this.analyserNode.getByteFrequencyData(dataArray);
        
        // Calculate RMS
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
            const normalized = dataArray[i] / 255.0;
            sum += normalized * normalized;
        }
        
        const rms = Math.sqrt(sum / bufferLength);
        this.metrics.rmsValues.push(rms);
        
        return rms;
    }
    
    async setupMediaRecorder() {
        // Setup MediaRecorder from MediaStreamDestination - identical to real mic path
        try {
            this.log("🎤 Setting up MediaRecorder...");
            
            const stream = this.mediaStreamDestination.stream;
            
            // Choose mime type like real mic path (prefer Opus in WebM)
            let mimeType = 'audio/webm;codecs=opus';
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = 'audio/webm';
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = 'audio/wav';
                }
            }
            
            this.log(`📊 Using MIME type: ${mimeType}`);
            
            // Create MediaRecorder with same config as real mic
            const options = {
                mimeType: mimeType,
                audioBitsPerSecond: 128000
            };
            
            this.mediaRecorder = new MediaRecorder(stream, options);
            
            // Handle data availability - same as real mic path
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.handleAudioData(event.data, mimeType);
                }
            };
            
            this.mediaRecorder.onstart = () => {
                this.log("🎵 MediaRecorder started");
                this.metrics.startTime = Date.now();
            };
            
            this.mediaRecorder.onstop = () => {
                this.log("⏹️ MediaRecorder stopped");
            };
            
            this.mediaRecorder.onerror = (error) => {
                this.error("MediaRecorder error:", error);
            };
            
            this.log("✅ MediaRecorder setup complete");
            return true;
            
        } catch (error) {
            this.error("MediaRecorder setup failed:", error);
            throw error;
        }
    }
    
    async handleAudioData(audioBlob, mimeType) {
        // Handle audio data - emit same payload as real mic path
        try {
            this.metrics.chunksProcessed++;
            
            // Convert blob to base64 - same as real mic
            const arrayBuffer = await audioBlob.arrayBuffer();
            const uint8Array = new Uint8Array(arrayBuffer);
            const base64 = btoa(String.fromCharCode(...uint8Array));
            
            // Calculate RMS
            const rms = this.calculateRMS();
            
            // Create payload identical to real mic path
            const payload = {
                session_id: this.sessionId,
                audio_data_b64: base64,
                mime_type: mimeType,
                rms: rms,
                ts_client: Date.now(),
                is_final_chunk: false
            };
            
            // Emit via same socket path as real mic
            if (window.socket && window.socket.connected) {
                window.socket.emit('audio_chunk', payload);
                this.log(`📦 Chunk ${this.metrics.chunksProcessed} sent (${audioBlob.size} bytes, RMS: ${rms.toFixed(3)})`);
            } else {
                this.error("Socket not connected, cannot send audio chunk");
            }
            
        } catch (error) {
            this.error("Failed to handle audio data:", error);
        }
    }
    
    async startSimulation() {
        // Start simulation - creates session and begins MediaRecorder
        try {
            this.log("🚀 Starting audio file simulation...");
            
            // Initialize audio graph
            await this.initializeAudioGraph();
            
            // Setup MediaRecorder
            await this.setupMediaRecorder();
            
            // Create session (same as real UI)
            this.log("📋 Creating session...");
            const response = await fetch('/api/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            
            if (!response.ok) {
                throw new Error(`Session creation failed: ${response.status}`);
            }
            
            const sessionData = await response.json();
            this.sessionId = sessionData.session_id;
            this.log(`✅ Session created: ${this.sessionId}`);
            
            // Join session via WebSocket
            if (window.socket && window.socket.connected) {
                window.socket.emit('join_session', { session_id: this.sessionId });
                this.log(`🏠 Joined session: ${this.sessionId}`);
            } else {
                throw new Error("WebSocket not connected");
            }
            
            // Wait for session join
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Start MediaRecorder with chunk interval (300ms like real mic)
            this.mediaRecorder.start(300);
            
            // Start audio playback
            await this.audioElement.play();
            this.isRecording = true;
            
            this.log("✅ Simulation started successfully");
            
            // Handle audio end
            this.audioElement.onended = () => {
                this.log("🔚 Audio playback ended");
                this.stopSimulation();
            };
            
            return {
                success: true,
                sessionId: this.sessionId,
                message: "Simulation started"
            };
            
        } catch (error) {
            this.error("Failed to start simulation:", error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    async stopSimulation() {
        // Stop simulation - send final chunk and cleanup
        try {
            this.log("⏹️ Stopping simulation...");
            
            if (this.audioElement) {
                this.audioElement.pause();
                this.audioElement.currentTime = 0;
            }
            
            if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                this.mediaRecorder.stop();
            }
            
            // Send final chunk signal (same as real mic)
            if (this.sessionId && window.socket && window.socket.connected) {
                const finalPayload = {
                    session_id: this.sessionId,
                    audio_data_b64: '',
                    mime_type: 'audio/webm',
                    rms: 0.0,
                    ts_client: Date.now(),
                    is_final_chunk: true
                };
                
                window.socket.emit('audio_chunk', finalPayload);
                this.log("🏁 Final chunk sent");
            }
            
            // Cleanup
            if (this.audioContext && this.audioContext.state !== 'closed') {
                await this.audioContext.close();
            }
            
            this.isRecording = false;
            
            // Calculate final metrics
            const duration = this.metrics.startTime ? (Date.now() - this.metrics.startTime) / 1000 : 0;
            const avgRMS = this.metrics.rmsValues.length > 0 ? 
                this.metrics.rmsValues.reduce((a, b) => a + b) / this.metrics.rmsValues.length : 0;
            
            this.log("📊 Simulation completed:");
            this.log(`   Duration: ${duration.toFixed(1)}s`);
            this.log(`   Chunks processed: ${this.metrics.chunksProcessed}`);
            this.log(`   Average RMS: ${avgRMS.toFixed(3)}`);
            this.log(`   Session ID: ${this.sessionId}`);
            
            return {
                success: true,
                sessionId: this.sessionId,
                duration: duration,
                chunksProcessed: this.metrics.chunksProcessed,
                averageRMS: avgRMS
            };
            
        } catch (error) {
            this.error("Failed to stop simulation:", error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    getMetrics() {
        // Get current simulation metrics
        return {
            ...this.metrics,
            isRecording: this.isRecording,
            sessionId: this.sessionId
        };
    }
}

// Global simulator instance
window.audioFileSimulator = new AudioFileSimulator();

// Helper functions for UI integration
window.simFromAudioStart = async function() {
    // Start simulation - called by UI button
    console.log("🎬 Starting file simulation...");
    
    try {
        const result = await window.audioFileSimulator.startSimulation();
        
        if (result.success) {
            console.log("✅ Simulation started successfully");
            
            // Update UI to show simulation state
            if (window.updateUIForSimulation) {
                window.updateUIForSimulation(true, result.sessionId);
            }
            
            return result;
        } else {
            console.error("❌ Simulation failed:", result.error);
            alert(`Simulation failed: ${result.error}`);
            return result;
        }
        
    } catch (error) {
        console.error("❌ Simulation error:", error);
        alert(`Simulation error: ${error.message}`);
        return { success: false, error: error.message };
    }
};

window.simFromAudioStop = async function() {
    // Stop simulation - called by UI button
    console.log("⏹️ Stopping file simulation...");
    
    try {
        const result = await window.audioFileSimulator.stopSimulation();
        
        if (result.success) {
            console.log("✅ Simulation stopped successfully");
            
            // Update UI to show simulation stopped
            if (window.updateUIForSimulation) {
                window.updateUIForSimulation(false, result.sessionId);
            }
            
            return result;
        } else {
            console.error("❌ Stop failed:", result.error);
            return result;
        }
        
    } catch (error) {
        console.error("❌ Stop error:", error);
        return { success: false, error: error.message };
    }
};

console.log("✅ Audio file simulation module loaded");