/**
 * INTELLIGENT CHUNKING OPTIMIZER
 * Advanced speech-aware chunking for optimal transcription performance
 */

class IntelligentChunkingOptimizer {
    constructor() {
        this.speechPatterns = {
            silenceThreshold: 0.01,
            speechThreshold: 0.05,
            minChunkDuration: 800,
            maxChunkDuration: 4000,
            optimalChunkDuration: 2000,
            pauseDetectionMs: 300
        };
        
        this.chunkingHistory = [];
        this.currentChunk = {
            startTime: null,
            audioData: [],
            speechDetected: false,
            silenceStreak: 0
        };
        
        this.performanceMetrics = {
            avgChunkSize: 0,
            speechToSilenceRatio: 0,
            chunkingAccuracy: 0,
            latencyImpact: 0
        };
        
        this.isActive = false;
    }
    
    initialize() {
        console.log('🧠 Initializing Intelligent Chunking Optimizer');
        
        // Reset all metrics
        this.chunkingHistory = [];
        this.resetCurrentChunk();
        this.isActive = true;
        
        console.log('✅ Intelligent chunking ready');
        return true;
    }
    
    processAudioFrame(audioData, volumeLevel, timestamp) {
        if (!this.isActive) return null;
        
        // Determine if current frame contains speech
        const isSpeech = this.detectSpeechInFrame(audioData, volumeLevel);
        
        // Initialize chunk if not started
        if (!this.currentChunk.startTime) {
            this.startNewChunk(timestamp);
        }
        
        // Add frame to current chunk
        this.currentChunk.audioData.push({
            data: audioData,
            timestamp: timestamp,
            volume: volumeLevel,
            isSpeech: isSpeech
        });
        
        // Update speech detection status
        if (isSpeech) {
            this.currentChunk.speechDetected = true;
            this.currentChunk.silenceStreak = 0;
        } else {
            this.currentChunk.silenceStreak++;
        }
        
        // Determine if chunk should be finalized
        const shouldFinalize = this.shouldFinalizeChunk(timestamp);
        
        if (shouldFinalize) {
            return this.finalizeCurrentChunk(timestamp);
        }
        
        return null;
    }
    
    detectSpeechInFrame(audioData, volumeLevel) {
        // Multi-factor speech detection
        
        // Volume-based detection
        const volumeSpeech = volumeLevel > this.speechPatterns.speechThreshold;
        
        // Frequency analysis for speech characteristics
        const frequencySpeech = this.analyzeFrequencyContent(audioData);
        
        // Zero-crossing rate (speech has higher ZCR than silence)
        const zcrSpeech = this.calculateZeroCrossingRate(audioData) > 0.1;
        
        // Combine all factors with weights
        const speechProbability = (
            (volumeSpeech ? 0.4 : 0) +
            (frequencySpeech ? 0.4 : 0) +
            (zcrSpeech ? 0.2 : 0)
        );
        
        return speechProbability > 0.5;
    }
    
    analyzeFrequencyContent(audioData) {
        // Simple frequency analysis - speech typically has energy in mid frequencies
        if (!audioData || audioData.length < 16) return false;
        
        // Calculate basic spectral centroid
        let weightedSum = 0;
        let magnitudeSum = 0;
        
        for (let i = 0; i < audioData.length; i++) {
            const magnitude = Math.abs(audioData[i]);
            weightedSum += magnitude * i;
            magnitudeSum += magnitude;
        }
        
        if (magnitudeSum === 0) return false;
        
        const spectralCentroid = weightedSum / magnitudeSum;
        const normalizedCentroid = spectralCentroid / audioData.length;
        
        // Speech typically has centroid in middle range
        return normalizedCentroid > 0.2 && normalizedCentroid < 0.8;
    }
    
    calculateZeroCrossingRate(audioData) {
        if (!audioData || audioData.length < 2) return 0;
        
        let crossings = 0;
        for (let i = 1; i < audioData.length; i++) {
            if ((audioData[i] >= 0) !== (audioData[i-1] >= 0)) {
                crossings++;
            }
        }
        
        return crossings / (audioData.length - 1);
    }
    
    shouldFinalizeChunk(currentTime) {
        const chunkDuration = currentTime - this.currentChunk.startTime;
        
        // Force finalize if max duration reached
        if (chunkDuration >= this.speechPatterns.maxChunkDuration) {
            return true;
        }
        
        // Don't finalize if below minimum duration
        if (chunkDuration < this.speechPatterns.minChunkDuration) {
            return false;
        }
        
        // Finalize if we have speech and detect a pause
        if (this.currentChunk.speechDetected && 
            this.currentChunk.silenceStreak >= this.speechPatterns.pauseDetectionMs / 50) { // Assuming 50ms frames
            return true;
        }
        
        // Finalize if optimal duration reached with speech
        if (chunkDuration >= this.speechPatterns.optimalChunkDuration && 
            this.currentChunk.speechDetected) {
            return true;
        }
        
        return false;
    }
    
    finalizeCurrentChunk(endTime) {
        const chunk = this.currentChunk;
        const duration = endTime - chunk.startTime;
        
        // Create optimized chunk
        const optimizedChunk = {
            id: `chunk_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
            startTime: chunk.startTime,
            endTime: endTime,
            duration: duration,
            audioFrames: chunk.audioData,
            speechDetected: chunk.speechDetected,
            frameCount: chunk.audioData.length,
            quality: this.calculateChunkQuality(chunk),
            priority: this.calculateProcessingPriority(chunk)
        };
        
        // Add to history for learning
        this.chunkingHistory.push(optimizedChunk);
        
        // Keep history bounded
        if (this.chunkingHistory.length > 100) {
            this.chunkingHistory.shift();
        }
        
        // Update performance metrics
        this.updatePerformanceMetrics(optimizedChunk);
        
        // Reset for next chunk
        this.resetCurrentChunk();
        
        console.log(`🔍 Optimized chunk: ${duration}ms, ${optimizedChunk.frameCount} frames, quality: ${optimizedChunk.quality.toFixed(2)}`);
        
        return optimizedChunk;
    }
    
    calculateChunkQuality(chunk) {
        if (!chunk.audioData || chunk.audioData.length === 0) return 0;
        
        // Quality factors
        const speechRatio = chunk.audioData.filter(frame => frame.isSpeech).length / chunk.audioData.length;
        const avgVolume = chunk.audioData.reduce((sum, frame) => sum + frame.volume, 0) / chunk.audioData.length;
        const consistency = this.calculateVolumeConsistency(chunk.audioData);
        const durationScore = this.calculateDurationScore(chunk);
        
        // Weighted quality score
        const quality = (
            speechRatio * 0.3 +
            Math.min(avgVolume * 2, 1.0) * 0.25 +
            consistency * 0.25 +
            durationScore * 0.2
        );
        
        return Math.max(0, Math.min(1, quality));
    }
    
    calculateVolumeConsistency(audioFrames) {
        if (audioFrames.length < 2) return 1;
        
        const volumes = audioFrames.map(frame => frame.volume);
        const mean = volumes.reduce((a, b) => a + b, 0) / volumes.length;
        const variance = volumes.reduce((sum, vol) => sum + Math.pow(vol - mean, 2), 0) / volumes.length;
        const stdDev = Math.sqrt(variance);
        
        // Lower standard deviation = higher consistency
        return Math.max(0, 1 - (stdDev / mean));
    }
    
    calculateDurationScore(chunk) {
        const duration = chunk.audioData.length * 50; // Assuming 50ms frames
        const optimal = this.speechPatterns.optimalChunkDuration;
        
        if (duration === optimal) return 1.0;
        
        const deviation = Math.abs(duration - optimal) / optimal;
        return Math.max(0, 1 - deviation);
    }
    
    calculateProcessingPriority(chunk) {
        // Higher priority for better quality chunks
        const qualityFactor = chunk.quality;
        
        // Higher priority for speech-heavy chunks
        const speechFactor = chunk.speechDetected ? 1.0 : 0.3;
        
        // Higher priority for optimal-duration chunks
        const durationFactor = this.calculateDurationScore(chunk);
        
        return qualityFactor * speechFactor * durationFactor;
    }
    
    updatePerformanceMetrics(chunk) {
        // Update running averages
        const historyCount = this.chunkingHistory.length;
        
        if (historyCount > 0) {
            this.performanceMetrics.avgChunkSize = 
                this.chunkingHistory.reduce((sum, c) => sum + c.duration, 0) / historyCount;
            
            const speechChunks = this.chunkingHistory.filter(c => c.speechDetected).length;
            this.performanceMetrics.speechToSilenceRatio = speechChunks / historyCount;
            
            this.performanceMetrics.chunkingAccuracy = 
                this.chunkingHistory.reduce((sum, c) => sum + c.quality, 0) / historyCount;
        }
        
        // Broadcast metrics update
        this.broadcastMetrics();
    }
    
    broadcastMetrics() {
        const event = new CustomEvent('chunkingMetricsUpdate', {
            detail: {
                avgChunkSize: this.performanceMetrics.avgChunkSize,
                speechRatio: this.performanceMetrics.speechToSilenceRatio,
                accuracy: this.performanceMetrics.chunkingAccuracy,
                totalChunks: this.chunkingHistory.length
            }
        });
        
        window.dispatchEvent(event);
    }
    
    adaptToConditions(audioQuality, networkLatency, processingLoad) {
        // Adaptive chunking based on conditions
        
        if (audioQuality < 0.5) {
            // Poor audio quality - use smaller chunks for more frequent processing
            this.speechPatterns.optimalChunkDuration = Math.max(1000, this.speechPatterns.optimalChunkDuration * 0.8);
        } else if (audioQuality > 0.8) {
            // Excellent audio quality - can use larger chunks
            this.speechPatterns.optimalChunkDuration = Math.min(3500, this.speechPatterns.optimalChunkDuration * 1.1);
        }
        
        if (networkLatency > 200) {
            // High latency - use larger chunks to reduce overhead
            this.speechPatterns.optimalChunkDuration = Math.min(4000, this.speechPatterns.optimalChunkDuration * 1.2);
        }
        
        if (processingLoad > 0.8) {
            // High processing load - optimize for efficiency
            this.speechPatterns.maxChunkDuration = Math.min(5000, this.speechPatterns.maxChunkDuration * 1.1);
        }
        
        console.log(`🔧 Chunking adapted: optimal=${this.speechPatterns.optimalChunkDuration}ms, max=${this.speechPatterns.maxChunkDuration}ms`);
    }
    
    resetCurrentChunk() {
        this.currentChunk = {
            startTime: null,
            audioData: [],
            speechDetected: false,
            silenceStreak: 0
        };
    }
    
    startNewChunk(timestamp) {
        this.currentChunk.startTime = timestamp;
        this.currentChunk.audioData = [];
        this.currentChunk.speechDetected = false;
        this.currentChunk.silenceStreak = 0;
    }
    
    getOptimizationReport() {
        const recent = this.chunkingHistory.slice(-20);
        
        if (recent.length === 0) {
            return { status: 'No chunking data available' };
        }
        
        return {
            totalChunks: this.chunkingHistory.length,
            averageChunkSize: this.performanceMetrics.avgChunkSize,
            speechDetectionRate: this.performanceMetrics.speechToSilenceRatio * 100,
            chunkingAccuracy: this.performanceMetrics.chunkingAccuracy * 100,
            qualityDistribution: this.calculateQualityDistribution(recent),
            recommendations: this.generateChunkingRecommendations()
        };
    }
    
    calculateQualityDistribution(chunks) {
        const buckets = { excellent: 0, good: 0, fair: 0, poor: 0 };
        
        chunks.forEach(chunk => {
            if (chunk.quality > 0.8) buckets.excellent++;
            else if (chunk.quality > 0.6) buckets.good++;
            else if (chunk.quality > 0.4) buckets.fair++;
            else buckets.poor++;
        });
        
        return buckets;
    }
    
    generateChunkingRecommendations() {
        const recommendations = [];
        
        if (this.performanceMetrics.avgChunkSize > 3500) {
            recommendations.push('Consider reducing chunk size for better responsiveness');
        }
        
        if (this.performanceMetrics.speechToSilenceRatio < 0.3) {
            recommendations.push('Low speech detection - check microphone or reduce noise threshold');
        }
        
        if (this.performanceMetrics.chunkingAccuracy < 0.6) {
            recommendations.push('Chunking accuracy low - consider adjusting speech detection parameters');
        }
        
        return recommendations;
    }
    
    stop() {
        this.isActive = false;
        this.resetCurrentChunk();
        console.log('🛑 Intelligent chunking optimizer stopped');
    }
}

// Export for global use
window.IntelligentChunkingOptimizer = IntelligentChunkingOptimizer;

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
