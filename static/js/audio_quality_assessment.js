/**
 * Audio Quality Assessment System
 * Implements comprehensive audio quality monitoring and comparison for Google Recorder-level performance.
 */

class AudioQualityAssessment {
    constructor() {
        this.audioContext = null;
        this.analyserNode = null;
        this.sourceNode = null;
        
        // Quality metrics tracking
        this.qualityMetrics = {
            signalToNoiseRatio: 0,
            frequencyResponse: [],
            volumeLevel: 0,
            clarity: 0,
            stability: 0,
            backgroundNoise: 0,
            qualityScore: 0
        };
        
        // Real-time analysis data
        this.analysisData = {
            frequencyData: null,
            timeData: null,
            rmsLevel: 0,
            peakLevel: 0,
            zeroCrossingRate: 0
        };
        
        // Quality thresholds
        this.qualityThresholds = {
            excellent: 0.9,
            good: 0.7,
            acceptable: 0.5,
            poor: 0.3
        };
        
        // Recording for quality comparison
        this.recordedChunks = [];
        this.isRecording = false;
        
        this.initialized = false;
        this.init();
    }
    
    async init() {
        if (this.initialized) return;
        
        try {
            console.log('🔊 Initializing audio quality assessment...');
            
            // Initialize Web Audio API
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create analyser node
            this.analyserNode = this.audioContext.createAnalyser();
            this.analyserNode.fftSize = 2048;
            this.analyserNode.smoothingTimeConstant = 0.8;
            
            // Initialize data arrays
            this.analysisData.frequencyData = new Uint8Array(this.analyserNode.frequencyBinCount);
            this.analysisData.timeData = new Uint8Array(this.analyserNode.fftSize);
            
            this.initialized = true;
            console.log('✅ Audio quality assessment initialized');
            
            // Start monitoring when recording begins
            this.setupRecordingMonitoring();
            
        } catch (error) {
            console.error('❌ Failed to initialize audio quality assessment:', error);
        }
    }
    
    setupRecordingMonitoring() {
        // Monitor for recording start/stop
        const checkForRecording = () => {
            if (window.enhancedWebSocketClient) {
                this.integrateWithWebSocketClient(window.enhancedWebSocketClient);
            } else {
                setTimeout(checkForRecording, 100);
            }
        };
        
        checkForRecording();
    }
    
    integrateWithWebSocketClient(client) {
        console.log('🔊 Integrating audio quality assessment with WebSocket client...');
        
        // Override startRecording to add quality monitoring
        const originalStartRecording = client.startRecording;
        if (originalStartRecording) {
            client.startRecording = async () => {
                try {
                    const result = await originalStartRecording.call(client);
                    
                    // Start quality monitoring
                    if (client.audioStream) {
                        await this.startQualityMonitoring(client.audioStream);
                    }
                    
                    return result;
                } catch (error) {
                    console.error('❌ Enhanced startRecording failed:', error);
                    throw error;
                }
            };
        }
        
        // Override stopRecording to stop quality monitoring
        const originalStopRecording = client.stopRecording;
        if (originalStopRecording) {
            client.stopRecording = async () => {
                try {
                    this.stopQualityMonitoring();
                    const result = await originalStopRecording.call(client);
                    return result;
                } catch (error) {
                    console.error('❌ Enhanced stopRecording failed:', error);
                    throw error;
                }
            };
        }
        
        // Add quality metrics to transcription results
        const originalHandleTranscriptionResult = client.handleTranscriptionResult;
        if (originalHandleTranscriptionResult) {
            client.handleTranscriptionResult = (data) => {
                // Add quality assessment to transcription data
                data.audioQuality = this.getCurrentQualityAssessment();
                
                // Call original handler
                originalHandleTranscriptionResult.call(client, data);
                
                // Update quality display
                this.updateQualityDisplay(data.audioQuality);
            };
        }
    }
    
    async startQualityMonitoring(stream) {
        try {
            console.log('🔊 Starting audio quality monitoring...');
            
            // Connect audio stream to analyser
            this.sourceNode = this.audioContext.createMediaStreamSource(stream);
            this.sourceNode.connect(this.analyserNode);
            
            // Start real-time analysis
            this.startRealTimeAnalysis();
            
            // Start recording for comparison
            this.startQualityRecording(stream);
            
            this.isRecording = true;
            
        } catch (error) {
            console.error('❌ Failed to start quality monitoring:', error);
        }
    }
    
    stopQualityMonitoring() {
        console.log('🔊 Stopping audio quality monitoring...');
        
        this.isRecording = false;
        
        // Disconnect audio nodes
        if (this.sourceNode) {
            this.sourceNode.disconnect();
            this.sourceNode = null;
        }
        
        // Stop recording
        this.stopQualityRecording();
        
        // Generate final quality report
        const finalReport = this.generateQualityReport();
        console.log('📊 Final audio quality report:', finalReport);
        
        return finalReport;
    }
    
    startRealTimeAnalysis() {
        const analyzeAudio = () => {
            if (!this.isRecording) return;
            
            // Get frequency and time domain data
            this.analyserNode.getByteFrequencyData(this.analysisData.frequencyData);
            this.analyserNode.getByteTimeDomainData(this.analysisData.timeData);
            
            // Calculate quality metrics
            this.calculateRealTimeMetrics();
            
            // Continue analysis
            requestAnimationFrame(analyzeAudio);
        };
        
        analyzeAudio();
    }
    
    calculateRealTimeMetrics() {
        // Calculate RMS level (volume)
        this.analysisData.rmsLevel = this.calculateRMS(this.analysisData.timeData);
        
        // Calculate peak level
        this.analysisData.peakLevel = this.calculatePeak(this.analysisData.timeData);
        
        // Calculate zero crossing rate (clarity indicator)
        this.analysisData.zeroCrossingRate = this.calculateZeroCrossingRate(this.analysisData.timeData);
        
        // Update quality metrics
        this.updateQualityMetrics();
    }
    
    calculateRMS(timeData) {
        let sum = 0;
        for (let i = 0; i < timeData.length; i++) {
            const sample = (timeData[i] - 128) / 128;
            sum += sample * sample;
        }
        return Math.sqrt(sum / timeData.length);
    }
    
    calculatePeak(timeData) {
        let peak = 0;
        for (let i = 0; i < timeData.length; i++) {
            const sample = Math.abs((timeData[i] - 128) / 128);
            if (sample > peak) {
                peak = sample;
            }
        }
        return peak;
    }
    
    calculateZeroCrossingRate(timeData) {
        let crossings = 0;
        for (let i = 1; i < timeData.length; i++) {
            const prev = timeData[i - 1] - 128;
            const curr = timeData[i] - 128;
            if ((prev >= 0 && curr < 0) || (prev < 0 && curr >= 0)) {
                crossings++;
            }
        }
        return crossings / timeData.length;
    }
    
    updateQualityMetrics() {
        // Volume level (normalized 0-1)
        this.qualityMetrics.volumeLevel = Math.min(this.analysisData.rmsLevel * 10, 1);
        
        // Signal-to-noise ratio estimation
        this.qualityMetrics.signalToNoiseRatio = this.estimateSignalToNoiseRatio();
        
        // Clarity based on zero crossing rate and frequency distribution
        this.qualityMetrics.clarity = this.calculateClarity();
        
        // Background noise estimation
        this.qualityMetrics.backgroundNoise = this.estimateBackgroundNoise();
        
        // Stability (consistency of signal)
        this.qualityMetrics.stability = this.calculateStability();
        
        // Overall quality score
        this.qualityMetrics.qualityScore = this.calculateOverallQuality();
    }
    
    estimateSignalToNoiseRatio() {
        // Estimate SNR based on signal strength vs background noise
        const signalStrength = this.analysisData.rmsLevel;
        const noiseFloor = this.estimateNoiseFloor();
        
        if (noiseFloor === 0) return 1;
        return Math.min(signalStrength / noiseFloor, 10) / 10; // Normalize to 0-1
    }
    
    estimateNoiseFloor() {
        // Estimate noise floor from low-amplitude portions
        const sortedAmplitudes = Array.from(this.analysisData.timeData)
            .map(val => Math.abs(val - 128))
            .sort((a, b) => a - b);
        
        // Take 10th percentile as noise floor
        const noiseFloorIndex = Math.floor(sortedAmplitudes.length * 0.1);
        return sortedAmplitudes[noiseFloorIndex] / 128;
    }
    
    calculateClarity() {
        // Clarity based on frequency distribution and zero crossing rate
        const frequencyClarity = this.analyzeFrequencyDistribution();
        const temporalClarity = Math.min(this.analysisData.zeroCrossingRate * 100, 1);
        
        return (frequencyClarity + temporalClarity) / 2;
    }
    
    analyzeFrequencyDistribution() {
        // Analyze frequency distribution for clarity
        const freqData = this.analysisData.frequencyData;
        
        // Focus on speech frequency range (300-3400 Hz)
        const sampleRate = this.audioContext.sampleRate;
        const binSize = sampleRate / (2 * freqData.length);
        
        const speechStart = Math.floor(300 / binSize);
        const speechEnd = Math.floor(3400 / binSize);
        
        let speechEnergy = 0;
        let totalEnergy = 0;
        
        for (let i = 0; i < freqData.length; i++) {
            const energy = freqData[i] / 255;
            totalEnergy += energy;
            
            if (i >= speechStart && i <= speechEnd) {
                speechEnergy += energy;
            }
        }
        
        return totalEnergy > 0 ? speechEnergy / totalEnergy : 0;
    }
    
    estimateBackgroundNoise() {
        // Estimate background noise level
        const lowFreqEnergy = this.calculateFrequencyBandEnergy(0, 200);
        const highFreqEnergy = this.calculateFrequencyBandEnergy(8000, 16000);
        
        return (lowFreqEnergy + highFreqEnergy) / 2;
    }
    
    calculateFrequencyBandEnergy(startFreq, endFreq) {
        const freqData = this.analysisData.frequencyData;
        const sampleRate = this.audioContext.sampleRate;
        const binSize = sampleRate / (2 * freqData.length);
        
        const startBin = Math.floor(startFreq / binSize);
        const endBin = Math.floor(endFreq / binSize);
        
        let energy = 0;
        let count = 0;
        
        for (let i = startBin; i <= endBin && i < freqData.length; i++) {
            energy += freqData[i] / 255;
            count++;
        }
        
        return count > 0 ? energy / count : 0;
    }
    
    calculateStability() {
        // Calculate stability based on volume consistency
        if (!this.volumeHistory) {
            this.volumeHistory = [];
        }
        
        this.volumeHistory.push(this.analysisData.rmsLevel);
        
        // Keep only last 50 measurements
        if (this.volumeHistory.length > 50) {
            this.volumeHistory.shift();
        }
        
        if (this.volumeHistory.length < 10) return 0.5; // Not enough data
        
        // Calculate coefficient of variation
        const mean = this.volumeHistory.reduce((a, b) => a + b) / this.volumeHistory.length;
        const variance = this.volumeHistory.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / this.volumeHistory.length;
        const stdDev = Math.sqrt(variance);
        
        const coefficientOfVariation = mean > 0 ? stdDev / mean : 1;
        
        // Convert to stability score (lower variation = higher stability)
        return Math.max(0, 1 - coefficientOfVariation);
    }
    
    calculateOverallQuality() {
        // Weighted average of quality metrics
        const weights = {
            signalToNoiseRatio: 0.3,
            clarity: 0.25,
            volumeLevel: 0.15,
            stability: 0.2,
            backgroundNoise: -0.1 // Negative weight (lower noise = better quality)
        };
        
        let score = 0;
        score += this.qualityMetrics.signalToNoiseRatio * weights.signalToNoiseRatio;
        score += this.qualityMetrics.clarity * weights.clarity;
        score += Math.min(this.qualityMetrics.volumeLevel, 0.8) * weights.volumeLevel; // Cap volume contribution
        score += this.qualityMetrics.stability * weights.stability;
        score += (1 - this.qualityMetrics.backgroundNoise) * Math.abs(weights.backgroundNoise);
        
        return Math.max(0, Math.min(1, score));
    }
    
    startQualityRecording(stream) {
        try {
            // Record audio for quality comparison
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.recordedChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.recordedChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.start(1000); // Record in 1-second chunks
            
        } catch (error) {
            console.error('❌ Failed to start quality recording:', error);
        }
    }
    
    stopQualityRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
    }
    
    getCurrentQualityAssessment() {
        return {
            metrics: { ...this.qualityMetrics },
            analysis: { ...this.analysisData },
            qualityLevel: this.getQualityLevel(this.qualityMetrics.qualityScore),
            recommendations: this.getQualityRecommendations()
        };
    }
    
    getQualityLevel(score) {
        if (score >= this.qualityThresholds.excellent) return 'excellent';
        if (score >= this.qualityThresholds.good) return 'good';
        if (score >= this.qualityThresholds.acceptable) return 'acceptable';
        return 'poor';
    }
    
    getQualityRecommendations() {
        const recommendations = [];
        
        if (this.qualityMetrics.volumeLevel < 0.3) {
            recommendations.push('Speak louder or move closer to microphone');
        } else if (this.qualityMetrics.volumeLevel > 0.9) {
            recommendations.push('Reduce volume or distance from microphone');
        }
        
        if (this.qualityMetrics.backgroundNoise > 0.3) {
            recommendations.push('Reduce background noise or use noise cancellation');
        }
        
        if (this.qualityMetrics.stability < 0.5) {
            recommendations.push('Maintain consistent distance and volume');
        }
        
        if (this.qualityMetrics.clarity < 0.5) {
            recommendations.push('Speak more clearly and at a steady pace');
        }
        
        if (recommendations.length === 0) {
            recommendations.push('Audio quality is optimal');
        }
        
        return recommendations;
    }
    
    generateQualityReport() {
        const report = {
            timestamp: new Date().toISOString(),
            duration: this.recordedChunks.length, // Approximate duration in seconds
            finalMetrics: { ...this.qualityMetrics },
            qualityLevel: this.getQualityLevel(this.qualityMetrics.qualityScore),
            recommendations: this.getQualityRecommendations(),
            comparison: this.compareWithTargetQuality(),
            recordedData: {
                chunks: this.recordedChunks.length,
                totalSize: this.recordedChunks.reduce((total, chunk) => total + chunk.size, 0)
            }
        };
        
        // Reset for next recording
        this.volumeHistory = [];
        this.recordedChunks = [];
        
        return report;
    }
    
    compareWithTargetQuality() {
        // Compare current quality with Google Recorder targets
        const targets = {
            signalToNoiseRatio: 0.8,
            clarity: 0.75,
            volumeLevel: 0.6,
            stability: 0.7,
            backgroundNoise: 0.2,
            qualityScore: 0.75
        };
        
        const comparison = {};
        
        for (const [metric, target] of Object.entries(targets)) {
            const current = this.qualityMetrics[metric];
            const difference = current - target;
            const percentage = target > 0 ? (current / target) * 100 : 100;
            
            comparison[metric] = {
                current,
                target,
                difference,
                percentage,
                meetsTarget: metric === 'backgroundNoise' ? current <= target : current >= target
            };
        }
        
        return comparison;
    }
    
    updateQualityDisplay(qualityData) {
        // Update real-time quality indicators in UI
        this.updateQualityBadge(qualityData);
        this.updateQualityMetrics(qualityData);
        this.showQualityRecommendations(qualityData);
    }
    
    updateQualityBadge(qualityData) {
        const qualityBadge = document.getElementById('qualityDisplay') || 
                           document.querySelector('[data-quality-display]');
        
        if (qualityBadge) {
            const score = Math.round(qualityData.metrics.qualityScore * 100);
            const level = qualityData.qualityLevel;
            
            qualityBadge.textContent = `${score}%`;
            qualityBadge.className = `badge ${this.getQualityBadgeClass(level)}`;
            qualityBadge.title = `Audio quality: ${level} (${score}%)`;
        }
    }
    
    updateQualityMetrics(qualityData) {
        // Update detailed quality metrics if display exists
        const metricsContainer = document.querySelector('.quality-metrics');
        
        if (metricsContainer) {
            const metrics = qualityData.metrics;
            
            metricsContainer.innerHTML = `
                <div class="quality-metric">
                    <span class="metric-label">Signal/Noise:</span>
                    <span class="metric-value">${(metrics.signalToNoiseRatio * 100).toFixed(0)}%</span>
                </div>
                <div class="quality-metric">
                    <span class="metric-label">Clarity:</span>
                    <span class="metric-value">${(metrics.clarity * 100).toFixed(0)}%</span>
                </div>
                <div class="quality-metric">
                    <span class="metric-label">Stability:</span>
                    <span class="metric-value">${(metrics.stability * 100).toFixed(0)}%</span>
                </div>
                <div class="quality-metric">
                    <span class="metric-label">Volume:</span>
                    <span class="metric-value">${(metrics.volumeLevel * 100).toFixed(0)}%</span>
                </div>
            `;
        }
    }
    
    showQualityRecommendations(qualityData) {
        // Show quality recommendations if quality is below good
        if (qualityData.qualityLevel === 'poor' || qualityData.qualityLevel === 'acceptable') {
            const recommendations = qualityData.recommendations;
            
            if (recommendations.length > 0 && window.mobileOptimizations) {
                window.mobileOptimizations.showMobileToast(
                    `Audio Quality Tips:\n${recommendations.slice(0, 2).join('\n')}`,
                    'warning',
                    4000
                );
            }
        }
    }
    
    getQualityBadgeClass(level) {
        switch (level) {
            case 'excellent': return 'bg-success';
            case 'good': return 'bg-info';
            case 'acceptable': return 'bg-warning';
            case 'poor': return 'bg-danger';
            default: return 'bg-secondary';
        }
    }
    
    // Public API
    getQualityMetrics() {
        return { ...this.qualityMetrics };
    }
    
    getQualityReport() {
        return this.generateQualityReport();
    }
    
    isMonitoring() {
        return this.isRecording;
    }
}

// Initialize audio quality assessment
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔊 Initializing audio quality assessment system...');
    window.audioQualityAssessment = new AudioQualityAssessment();
    
    // Global access for debugging and testing
    window.getAudioQualityMetrics = () => window.audioQualityAssessment.getQualityMetrics();
    window.getAudioQualityReport = () => window.audioQualityAssessment.getQualityReport();
    
    console.log('✅ Audio quality assessment system ready');
});

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
