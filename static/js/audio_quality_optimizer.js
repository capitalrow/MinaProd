/**
 * AUDIO QUALITY OPTIMIZER
 * Advanced audio preprocessing for maximum transcription accuracy
 */

class AudioQualityOptimizer {
    constructor() {
        this.audioContext = null;
        this.processor = null;
        this.filters = {
            noiseGate: null,
            compressor: null,
            highPass: null,
            lowPass: null
        };
        this.qualityMetrics = {
            snr: 0,
            volume: 0,
            clarity: 0,
            stability: 0
        };
        this.isOptimizing = false;
    }
    
    async initialize(mediaStream) {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 16000,
                latencyHint: 'interactive'
            });
            
            const source = this.audioContext.createMediaStreamSource(mediaStream);
            
            // Create advanced audio processing chain
            await this.setupAudioProcessingChain(source);
            
            console.log('✅ Audio Quality Optimizer initialized');
            this.isOptimizing = true;
            return true;
            
        } catch (error) {
            console.error('❌ Audio optimizer initialization failed:', error);
            return false;
        }
    }
    
    async setupAudioProcessingChain(source) {
        // 1. HIGH-PASS FILTER - Remove low-frequency noise
        this.filters.highPass = this.audioContext.createBiquadFilter();
        this.filters.highPass.type = 'highpass';
        this.filters.highPass.frequency.setValueAtTime(80, this.audioContext.currentTime); // Remove below 80Hz
        this.filters.highPass.Q.setValueAtTime(0.7, this.audioContext.currentTime);
        
        // 2. LOW-PASS FILTER - Remove high-frequency noise
        this.filters.lowPass = this.audioContext.createBiquadFilter();
        this.filters.lowPass.type = 'lowpass';
        this.filters.lowPass.frequency.setValueAtTime(7000, this.audioContext.currentTime); // Remove above 7kHz
        this.filters.lowPass.Q.setValueAtTime(0.7, this.audioContext.currentTime);
        
        // 3. COMPRESSOR - Dynamic range control
        this.filters.compressor = this.audioContext.createDynamicsCompressor();
        this.filters.compressor.threshold.setValueAtTime(-24, this.audioContext.currentTime);
        this.filters.compressor.knee.setValueAtTime(30, this.audioContext.currentTime);
        this.filters.compressor.ratio.setValueAtTime(3, this.audioContext.currentTime);
        this.filters.compressor.attack.setValueAtTime(0.003, this.audioContext.currentTime);
        this.filters.compressor.release.setValueAtTime(0.25, this.audioContext.currentTime);
        
        // 4. NOISE GATE - Reduce background noise
        this.filters.noiseGate = this.audioContext.createGain();
        this.filters.noiseGate.gain.setValueAtTime(1.0, this.audioContext.currentTime);
        
        // 5. ANALYZER - Real-time quality monitoring
        this.analyzer = this.audioContext.createAnalyser();
        this.analyzer.fftSize = 2048;
        this.analyzer.smoothingTimeConstant = 0.8;
        
        // Connect processing chain
        source
            .connect(this.filters.highPass)
            .connect(this.filters.lowPass)
            .connect(this.filters.compressor)
            .connect(this.filters.noiseGate)
            .connect(this.analyzer);
        
        // Start quality monitoring
        this.startQualityMonitoring();
    }
    
    startQualityMonitoring() {
        const bufferLength = this.analyzer.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        const timeArray = new Uint8Array(bufferLength);
        
        const monitor = () => {
            if (!this.isOptimizing) return;
            
            this.analyzer.getByteFrequencyData(dataArray);
            this.analyzer.getByteTimeDomainData(timeArray);
            
            // Calculate quality metrics
            this.calculateQualityMetrics(dataArray, timeArray);
            
            // Apply adaptive optimizations
            this.applyAdaptiveOptimizations();
            
            requestAnimationFrame(monitor);
        };
        
        monitor();
    }
    
    calculateQualityMetrics(frequencyData, timeData) {
        // 1. SIGNAL-TO-NOISE RATIO
        const signalPower = this.calculateSignalPower(frequencyData);
        const noisePower = this.calculateNoisePower(frequencyData);
        this.qualityMetrics.snr = signalPower / Math.max(noisePower, 1);
        
        // 2. VOLUME LEVEL
        let sum = 0;
        for (let i = 0; i < timeData.length; i++) {
            const normalized = (timeData[i] - 128) / 128;
            sum += normalized * normalized;
        }
        this.qualityMetrics.volume = Math.sqrt(sum / timeData.length);
        
        // 3. CLARITY SCORE (high-frequency content)
        const clarityRange = frequencyData.slice(Math.floor(frequencyData.length * 0.3));
        this.qualityMetrics.clarity = clarityRange.reduce((a, b) => a + b, 0) / clarityRange.length / 255;
        
        // 4. STABILITY (consistency over time)
        this.updateStabilityMetric();
        
        // Broadcast quality update
        this.broadcastQualityMetrics();
    }
    
    calculateSignalPower(frequencyData) {
        // Focus on speech frequency range (300Hz - 3400Hz)
        const speechStart = Math.floor(300 * frequencyData.length / 8000);
        const speechEnd = Math.floor(3400 * frequencyData.length / 8000);
        
        let power = 0;
        for (let i = speechStart; i < speechEnd; i++) {
            power += frequencyData[i] * frequencyData[i];
        }
        return power / (speechEnd - speechStart);
    }
    
    calculateNoisePower(frequencyData) {
        // Low frequencies typically contain noise
        const noiseEnd = Math.floor(200 * frequencyData.length / 8000);
        
        let power = 0;
        for (let i = 0; i < noiseEnd; i++) {
            power += frequencyData[i] * frequencyData[i];
        }
        return power / noiseEnd;
    }
    
    updateStabilityMetric() {
        // Track volume consistency over time
        if (!this.volumeHistory) {
            this.volumeHistory = [];
        }
        
        this.volumeHistory.push(this.qualityMetrics.volume);
        
        // Keep only last 30 samples
        if (this.volumeHistory.length > 30) {
            this.volumeHistory.shift();
        }
        
        if (this.volumeHistory.length > 5) {
            const variance = this.calculateVariance(this.volumeHistory);
            this.qualityMetrics.stability = Math.max(0, 1 - variance);
        }
    }
    
    calculateVariance(array) {
        const mean = array.reduce((a, b) => a + b) / array.length;
        const squaredDiffs = array.map(value => Math.pow(value - mean, 2));
        return squaredDiffs.reduce((a, b) => a + b) / array.length;
    }
    
    applyAdaptiveOptimizations() {
        const { snr, volume, clarity } = this.qualityMetrics;
        
        // Adaptive noise gate
        if (snr < 2.0) {
            // High noise environment - tighten noise gate
            this.filters.noiseGate.gain.setValueAtTime(0.7, this.audioContext.currentTime);
        } else {
            // Clean environment - open noise gate
            this.filters.noiseGate.gain.setValueAtTime(1.0, this.audioContext.currentTime);
        }
        
        // Adaptive compression
        if (volume < 0.1) {
            // Quiet speech - reduce compression
            this.filters.compressor.ratio.setValueAtTime(2, this.audioContext.currentTime);
        } else if (volume > 0.8) {
            // Loud speech - increase compression
            this.filters.compressor.ratio.setValueAtTime(4, this.audioContext.currentTime);
        }
        
        // Adaptive filtering based on clarity
        if (clarity < 0.3) {
            // Poor clarity - adjust filters
            this.filters.highPass.frequency.setValueAtTime(100, this.audioContext.currentTime);
            this.filters.lowPass.frequency.setValueAtTime(6000, this.audioContext.currentTime);
        }
    }
    
    broadcastQualityMetrics() {
        // Send quality metrics to UI
        const qualityEvent = new CustomEvent('audioQualityUpdate', {
            detail: {
                snr: this.qualityMetrics.snr,
                volume: this.qualityMetrics.volume,
                clarity: this.qualityMetrics.clarity,
                stability: this.qualityMetrics.stability,
                overallScore: this.calculateOverallQuality()
            }
        });
        
        window.dispatchEvent(qualityEvent);
    }
    
    calculateOverallQuality() {
        const { snr, volume, clarity, stability } = this.qualityMetrics;
        
        // Weighted quality score
        const snrScore = Math.min(snr / 5.0, 1.0) * 0.3;
        const volumeScore = Math.min(volume * 2, 1.0) * 0.25;
        const clarityScore = clarity * 0.25;
        const stabilityScore = stability * 0.2;
        
        return (snrScore + volumeScore + clarityScore + stabilityScore) * 100;
    }
    
    getOptimizedStream() {
        if (!this.audioContext || !this.filters.noiseGate) {
            return null;
        }
        
        // Create output stream from processed audio
        const destination = this.audioContext.createMediaStreamDestination();
        this.filters.noiseGate.connect(destination);
        
        return destination.stream;
    }
    
    getQualityMetrics() {
        return {
            ...this.qualityMetrics,
            overallScore: this.calculateOverallQuality()
        };
    }
    
    stop() {
        this.isOptimizing = false;
        
        if (this.audioContext) {
            this.audioContext.close();
        }
        
        console.log('🛑 Audio Quality Optimizer stopped');
    }
}

// Export for global use
window.AudioQualityOptimizer = AudioQualityOptimizer;