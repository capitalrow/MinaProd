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
            
            // Initialize advanced systems
            if (window.AdaptiveMLCorrectionEngine) {
                this.mlCorrectionEngine = new window.AdaptiveMLCorrectionEngine();
                await this.mlCorrectionEngine.initialize();
            }
            
            if (window.PredictiveLatencyOptimizer) {
                this.latencyOptimizer = new window.PredictiveLatencyOptimizer();
                await this.latencyOptimizer.initialize();
            }
            
            if (window.DynamicQualityAdaptation) {
                this.qualityAdaptation = new window.DynamicQualityAdaptation();
                await this.qualityAdaptation.initialize();
            }
            
            if (window.GoogleRecorderUISystem) {
                this.uiSystem = new window.GoogleRecorderUISystem();
                await this.uiSystem.initialize();
            }
            
            if (window.SessionReliabilityManager) {
                this.reliabilityManager = new window.SessionReliabilityManager();
                await this.reliabilityManager.initialize();
            }
            
            if (window.QuantumPerformanceOptimizer) {
                this.quantumOptimizer = new window.QuantumPerformanceOptimizer();
                await this.quantumOptimizer.initialize();
            }
            
            if (window.BiometricAudioAnalysis) {
                this.biometricAnalyzer = new window.BiometricAudioAnalysis();
                await this.biometricAnalyzer.initialize();
            }
            
            if (window.ContextualIntelligenceSystem) {
                this.contextualIntelligence = new window.ContextualIntelligenceSystem();
                await this.contextualIntelligence.initialize();
            }
            
            if (window.UltraResponsiveUIEngine) {
                this.ultraUI = new window.UltraResponsiveUIEngine();
                await this.ultraUI.initialize();
            }
            
            console.log('✅ All enhancement systems ready');
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
        
        let enhancedResult = originalResult;
        
        // Step 1: Apply accuracy enhancements
        enhancedResult = this.accuracyEnhancer.enhanceTranscription(enhancedResult);
        
        // Step 2: Apply ML corrections if available
        if (this.mlCorrectionEngine) {
            enhancedResult = this.mlCorrectionEngine.processTranscription(enhancedResult);
        }
        
        // Step 3: Apply quantum optimization
        if (this.quantumOptimizer) {
            enhancedResult = this.quantumOptimizer.optimizeTranscription(enhancedResult);
        }
        
        // Step 4: Apply biometric analysis
        if (this.biometricAnalyzer && originalResult.audioData) {
            const biometricReport = this.biometricAnalyzer.processAudioSegment(
                originalResult.audioData, 
                Date.now()
            );
            enhancedResult.biometricAnalysis = biometricReport;
        }
        
        // Step 5: Apply contextual intelligence
        if (this.contextualIntelligence) {
            enhancedResult = this.contextualIntelligence.processTranscriptionWithContext(enhancedResult);
        }
        
        // Step 6: Apply ultra-responsive UI enhancements
        if (this.ultraUI) {
            enhancedResult = this.ultraUI.enhanceTranscriptionUI(enhancedResult);
        }
        
        // Add performance metrics
        enhancedResult.latency_ms = latency;
        enhancedResult.enhanced_mode = true;
        enhancedResult.total_enhancements = this.countAppliedEnhancements(enhancedResult);
        
        // Update enhancement metrics
        this.updateEnhancementMetrics(originalResult, enhancedResult, latency);
        
        // Log enhancement details
        this.logEnhancementResults(originalResult, enhancedResult);
        
        return enhancedResult;
    }
    
    countAppliedEnhancements(result) {
        let count = 0;
        
        if (result.enhancement_applied) count++;
        if (result.ml_processed) count++;
        if (result.ml_corrections && result.ml_corrections.length > 0) count += result.ml_corrections.length;
        
        return count;
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
        
        if (this.mlCorrectionEngine) {
            this.mlCorrectionEngine.stop();
        }
        
        if (this.latencyOptimizer) {
            this.latencyOptimizer.stop();
        }
        
        if (this.qualityAdaptation) {
            this.qualityAdaptation.stop();
        }
        
        if (this.uiSystem) {
            this.uiSystem.stop();
        }
        
        if (this.reliabilityManager) {
            this.reliabilityManager.stop();
        }
        
        if (this.quantumOptimizer) {
            this.quantumOptimizer.stop();
        }
        
        if (this.biometricAnalyzer) {
            this.biometricAnalyzer.stop();
        }
        
        if (this.contextualIntelligence) {
            this.contextualIntelligence.stop();
        }
        
        if (this.ultraUI) {
            this.ultraUI.stop();
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

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
