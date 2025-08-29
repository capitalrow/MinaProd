/**
 * ENHANCED SYSTEM INTEGRATION
 * Orchestrates all performance enhancements for optimal transcription
 */

class EnhancedSystemIntegration {
    constructor() {
        this.audioOptimizer = null;
        this.accuracyEnhancer = null;
        this.performanceOptimizer = null;
        this.isEnhancedMode = false;
        this.enhancementMetrics = {
            audioQuality: 0,
            accuracyBoost: 0,
            latencyReduction: 0,
            completenessScore: 0
        };
    }
    
    async initialize() {
        try {
            console.log('🚀 Initializing Enhanced System Integration');
            
            // Initialize all enhancement systems
            this.accuracyEnhancer = new window.TranscriptionAccuracyEnhancer();
            this.performanceOptimizer = new window.PerformanceOptimizer();
            
            console.log('✅ Enhancement systems ready');
            this.isEnhancedMode = true;
            
            // Set up event listeners for system coordination
            this.setupSystemCoordination();
            
            return true;
            
        } catch (error) {
            console.error('❌ Enhanced system initialization failed:', error);
            return false;
        }
    }
    
    async initializeAudioOptimizer(mediaStream) {
        if (window.AudioQualityOptimizer && mediaStream) {
            this.audioOptimizer = new window.AudioQualityOptimizer();
            const success = await this.audioOptimizer.initialize(mediaStream);
            
            if (success) {
                console.log('✅ Audio quality optimizer active');
                this.setupAudioQualityMonitoring();
                return this.audioOptimizer.getOptimizedStream();
            }
        }
        return mediaStream;
    }
    
    setupSystemCoordination() {
        // Listen for audio quality updates
        window.addEventListener('audioQualityUpdate', (event) => {
            this.enhancementMetrics.audioQuality = event.detail.overallScore;
            this.adaptSystemToAudioQuality(event.detail);
        });
        
        // Monitor transcription performance
        this.setupTranscriptionMonitoring();
    }
    
    setupAudioQualityMonitoring() {
        if (!this.audioOptimizer) return;
        
        setInterval(() => {
            const quality = this.audioOptimizer.getQualityMetrics();
            
            // Broadcast quality metrics to UI
            this.updateQualityDisplay(quality);
            
            // Adjust processing parameters based on audio quality
            this.adaptToAudioQuality(quality);
            
        }, 1000);
    }
    
    setupTranscriptionMonitoring() {
        // Track transcription completeness and accuracy
        let lastTranscriptionTime = Date.now();
        
        const originalHandleResult = window.minaTranscriptionFix?.handleTranscriptionResult;
        
        if (originalHandleResult) {
            window.minaTranscriptionFix.handleTranscriptionResult = (result) => {
                // Measure latency
                const now = Date.now();
                const latency = now - lastTranscriptionTime;
                lastTranscriptionTime = now;
                
                // Apply accuracy enhancements
                const enhancedResult = this.enhanceTranscriptionResult(result, latency);
                
                // Call original handler with enhanced result
                return originalHandleResult.call(window.minaTranscriptionFix, enhancedResult);
            };
        }
    }
    
    enhanceTranscriptionResult(originalResult, latency) {
        if (!this.isEnhancedMode || !this.accuracyEnhancer) {
            return originalResult;
        }
        
        // Apply accuracy enhancements
        const enhancedResult = this.accuracyEnhancer.enhanceTranscription(originalResult);
        
        // Add performance metrics
        enhancedResult.latency_ms = latency;
        enhancedResult.enhanced_mode = true;
        
        // Update enhancement metrics
        this.updateEnhancementMetrics(originalResult, enhancedResult, latency);
        
        // Log enhancement details
        this.logEnhancementResults(originalResult, enhancedResult);
        
        return enhancedResult;
    }
    
    updateEnhancementMetrics(original, enhanced, latency) {
        // Calculate accuracy boost
        const originalConfidence = original.confidence || 0.9;
        const enhancedConfidence = enhanced.confidence || 0.9;
        this.enhancementMetrics.accuracyBoost = ((enhancedConfidence - originalConfidence) / originalConfidence) * 100;
        
        // Track latency improvements
        if (latency < 2000) {
            this.enhancementMetrics.latencyReduction = Math.max(0, (2000 - latency) / 2000 * 100);
        }
        
        // Calculate completeness score
        this.enhancementMetrics.completenessScore = enhanced.quality_score || 75;
        
        // Broadcast metrics update
        this.broadcastEnhancementMetrics();
    }
    
    adaptToAudioQuality(quality) {
        if (!this.performanceOptimizer) return;
        
        // Adjust processing parameters based on audio quality
        if (quality.overallScore < 50) {
            // Poor audio quality - use smaller chunks for more frequent processing
            this.performanceOptimizer.optimizations.chunkSize = Math.max(
                this.performanceOptimizer.optimizations.chunkSize * 0.8, 
                1000
            );
        } else if (quality.overallScore > 80) {
            // Excellent audio quality - can use larger chunks for efficiency
            this.performanceOptimizer.optimizations.chunkSize = Math.min(
                this.performanceOptimizer.optimizations.chunkSize * 1.1, 
                4000
            );
        }
    }
    
    adaptSystemToAudioQuality(qualityDetail) {
        // Comprehensive system adaptation based on audio quality
        const { snr, volume, clarity, stability } = qualityDetail;
        
        // Adjust transcription confidence thresholds
        if (this.accuracyEnhancer) {
            if (snr < 2.0) {
                this.accuracyEnhancer.wordConfidenceThreshold = 0.8; // Higher threshold for noisy audio
            } else {
                this.accuracyEnhancer.wordConfidenceThreshold = 0.7; // Standard threshold
            }
        }
        
        // Adjust processing concurrency based on stability
        if (this.performanceOptimizer && stability < 0.5) {
            this.performanceOptimizer.optimizations.maxConcurrent = 1; // Single-threaded for unstable audio
        }
    }
    
    updateQualityDisplay(quality) {
        // Update audio quality indicators in UI
        const qualityElements = document.querySelectorAll('[data-metric="audio-quality"]');
        qualityElements.forEach(el => {
            el.textContent = `${Math.round(quality.overallScore)}%`;
            
            // Color coding
            el.className = el.className.replace(/quality-\w+/g, '');
            if (quality.overallScore > 80) {
                el.classList.add('quality-excellent');
            } else if (quality.overallScore > 60) {
                el.classList.add('quality-good');
            } else {
                el.classList.add('quality-poor');
            }
        });
        
        // Update individual quality metrics
        const metricsMap = {
            'snr': quality.snr.toFixed(1),
            'volume': `${Math.round(quality.volume * 100)}%`,
            'clarity': `${Math.round(quality.clarity * 100)}%`,
            'stability': `${Math.round(quality.stability * 100)}%`
        };
        
        Object.entries(metricsMap).forEach(([metric, value]) => {
            const elements = document.querySelectorAll(`[data-metric="${metric}"]`);
            elements.forEach(el => {
                el.textContent = value;
            });
        });
    }
    
    broadcastEnhancementMetrics() {
        const event = new CustomEvent('enhancementMetricsUpdate', {
            detail: this.enhancementMetrics
        });
        window.dispatchEvent(event);
        
        // Update UI elements
        Object.entries(this.enhancementMetrics).forEach(([key, value]) => {
            const elements = document.querySelectorAll(`[data-enhancement="${key}"]`);
            elements.forEach(el => {
                if (key.includes('Boost') || key.includes('Reduction')) {
                    el.textContent = `+${Math.round(value)}%`;
                } else {
                    el.textContent = Math.round(value);
                }
            });
        });
    }
    
    logEnhancementResults(original, enhanced) {
        if (original.text !== enhanced.text) {
            console.log(`🔍 Text Enhancement: "${original.text}" → "${enhanced.text}"`);
        }
        
        if (enhanced.confidence > original.confidence) {
            const boost = ((enhanced.confidence - original.confidence) / original.confidence * 100).toFixed(1);
            console.log(`📈 Confidence Boost: ${(original.confidence * 100).toFixed(1)}% → ${(enhanced.confidence * 100).toFixed(1)}% (+${boost}%)`);
        }
        
        if (enhanced.quality_score) {
            console.log(`🎯 Quality Score: ${enhanced.quality_score}%`);
        }
    }
    
    async processAudioWithEnhancements(audioData) {
        if (!this.performanceOptimizer) {
            return audioData;
        }
        
        // Use performance optimizer for processing
        return this.performanceOptimizer.processWithOptimization(audioData, async (data) => {
            // Basic audio processing - could be enhanced further
            return data;
        });
    }
    
    getSystemStatus() {
        return {
            enhancedMode: this.isEnhancedMode,
            audioOptimizerActive: !!this.audioOptimizer,
            accuracyEnhancerActive: !!this.accuracyEnhancer,
            performanceOptimizerActive: !!this.performanceOptimizer,
            currentMetrics: this.enhancementMetrics,
            performanceReport: this.performanceOptimizer?.getPerformanceReport() || null
        };
    }
    
    getDetailedMetrics() {
        const metrics = {
            system: this.getSystemStatus(),
            audio: this.audioOptimizer?.getQualityMetrics() || null,
            accuracy: this.accuracyEnhancer?.getContextSummary() || null,
            performance: this.performanceOptimizer?.getOptimizationSettings() || null
        };
        
        return metrics;
    }
    
    stop() {
        if (this.audioOptimizer) {
            this.audioOptimizer.stop();
        }
        
        if (this.performanceOptimizer) {
            this.performanceOptimizer.stop();
        }
        
        if (this.accuracyEnhancer) {
            this.accuracyEnhancer.reset();
        }
        
        this.isEnhancedMode = false;
        console.log('🛑 Enhanced system integration stopped');
    }
}

// Initialize enhanced system
window.enhancedSystemIntegration = new EnhancedSystemIntegration();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async function() {
    const success = await window.enhancedSystemIntegration.initialize();
    if (success) {
        console.log('🌟 Enhanced Transcription System Active');
    }
});