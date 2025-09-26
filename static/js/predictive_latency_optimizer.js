/**
 * PREDICTIVE LATENCY OPTIMIZER
 * Advanced latency prediction and preemptive optimization
 */

class PredictiveLatencyOptimizer {
    constructor() {
        this.isActive = false;
        this.latencyHistory = [];
        this.predictionModel = {
            networkPatterns: new Map(),
            processingPatterns: new Map(),
            audioPatterns: new Map(),
            systemLoadPatterns: new Map()
        };
        
        this.optimizationStrategies = {
            preemptiveChunking: false,
            adaptiveBandwidth: false,
            resourcePredictiveScaling: false,
            networkLatencyCompensation: false
        };
        
        this.performanceTargets = {
            targetLatency: 400,
            acceptableLatency: 800,
            criticalLatency: 1500,
            optimizationThreshold: 600
        };
        
        this.predictionAccuracy = {
            shortTerm: 0,  // Next chunk prediction
            mediumTerm: 0, // Next 5 chunks
            longTerm: 0    // Session trend
        };
        
        this.setupPredictionModels();
    }
    
    initialize() {
        console.log('🔮 Initializing Predictive Latency Optimizer');
        
        this.startLatencyMonitoring();
        this.setupPredictiveOptimization();
        this.calibratePredictionModels();
        this.isActive = true;
        
        console.log('✅ Predictive latency optimization active');
        return true;
    }
    
    setupPredictionModels() {
        // Initialize pattern recognition models
        this.predictionModel = {
            networkPatterns: new Map([
                ['peak_hours', { factor: 1.3, confidence: 0.8 }],
                ['off_peak', { factor: 0.8, confidence: 0.9 }],
                ['high_traffic', { factor: 1.5, confidence: 0.7 }],
                ['stable_connection', { factor: 1.0, confidence: 0.95 }]
            ]),
            
            processingPatterns: new Map([
                ['simple_speech', { latency: 200, confidence: 0.9 }],
                ['complex_speech', { latency: 400, confidence: 0.8 }],
                ['noisy_audio', { latency: 600, confidence: 0.7 }],
                ['clear_audio', { latency: 250, confidence: 0.95 }]
            ]),
            
            audioPatterns: new Map([
                ['continuous_speech', { chunks: 'large', latency: 300 }],
                ['sporadic_speech', { chunks: 'small', latency: 500 }],
                ['quiet_environment', { processing: 'fast', latency: 200 }],
                ['noisy_environment', { processing: 'complex', latency: 700 }]
            ]),
            
            systemLoadPatterns: new Map([
                ['low_load', { multiplier: 0.8, optimization: 'quality' }],
                ['medium_load', { multiplier: 1.0, optimization: 'balanced' }],
                ['high_load', { multiplier: 1.4, optimization: 'speed' }],
                ['critical_load', { multiplier: 2.0, optimization: 'emergency' }]
            ])
        };
    }
    
    startLatencyMonitoring() {
        // Monitor various latency sources
        this.monitoringInterval = setInterval(() => {
            this.measureAndRecordLatency();
            this.updatePredictionModels();
            this.applyPredictiveOptimizations();
        }, 1000);
        
        // Listen for transcription events to measure actual latency
        window.addEventListener('transcriptionLatencyMeasured', (event) => {
            this.recordLatencyMeasurement(event.detail);
        });
    }
    
    measureAndRecordLatency() {
        // Comprehensive latency measurement
        const latencyData = {
            timestamp: Date.now(),
            network: this.measureNetworkLatency(),
            processing: this.estimateProcessingLatency(),
            system: this.measureSystemLatency(),
            audio: this.estimateAudioLatency()
        };
        
        this.latencyHistory.push(latencyData);
        
        // Keep history bounded (last 200 measurements)
        if (this.latencyHistory.length > 200) {
            this.latencyHistory.shift();
        }
        
        // Calculate total predicted latency
        latencyData.total = latencyData.network + latencyData.processing + latencyData.system + latencyData.audio;
        
        // Broadcast latency prediction
        this.broadcastLatencyPrediction(latencyData);
    }
    
    async measureNetworkLatency() {
        try {
            const start = performance.now();
            
            // Use fetch with AbortController for timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2000);
            
            await fetch('/api/ping', { 
                method: 'HEAD',
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            const latency = performance.now() - start;
            
            return Math.min(latency, 2000); // Cap at 2 seconds
        } catch (error) {
            return 1000; // Default assumption on error
        }
    }
    
    estimateProcessingLatency() {
        // Estimate based on current system performance metrics
        let processingLatency = 200; // Base processing time
        
        // Check performance optimizer metrics
        if (window.performanceOptimizer) {
            const metrics = window.performanceOptimizer.getOptimizationSettings();
            
            // Adjust based on current load
            if (metrics.currentMetrics) {
                const load = metrics.currentMetrics.currentLoad || 0;
                processingLatency += load * 300; // Add latency based on load
                
                const queueLength = metrics.currentMetrics.queueLength || 0;
                processingLatency += queueLength * 100; // Add latency for queue
            }
        }
        
        // Check memory pressure
        if (performance.memory) {
            const memoryUsage = performance.memory.usedJSHeapSize / performance.memory.totalJSHeapSize;
            if (memoryUsage > 0.8) {
                processingLatency += 200; // Add latency for memory pressure
            }
        }
        
        return processingLatency;
    }
    
    measureSystemLatency() {
        // Measure browser/system responsiveness
        const start = performance.now();
        
        // Force a synchronous operation to measure system responsiveness
        for (let i = 0; i < 1000; i++) {
            Math.random();
        }
        
        const systemLatency = (performance.now() - start) * 10; // Scale up
        return Math.min(systemLatency, 500); // Cap at 500ms
    }
    
    estimateAudioLatency() {
        // Estimate audio processing latency based on quality
        let audioLatency = 100; // Base audio latency
        
        // Check audio quality metrics
        if (window.enhancedSystemIntegration?.audioOptimizer) {
            const quality = window.enhancedSystemIntegration.audioOptimizer.getQualityMetrics();
            
            if (quality) {
                // Poor quality requires more processing
                if (quality.overallScore < 50) {
                    audioLatency += 200;
                } else if (quality.overallScore < 70) {
                    audioLatency += 100;
                }
                
                // Low SNR requires more processing
                if (quality.snr < 2.0) {
                    audioLatency += 150;
                }
            }
        }
        
        return audioLatency;
    }
    
    updatePredictionModels() {
        if (this.latencyHistory.length < 10) return; // Need minimum data
        
        // Analyze recent patterns
        const recent = this.latencyHistory.slice(-20);
        
        // Update network patterns
        this.updateNetworkPatterns(recent);
        
        // Update processing patterns
        this.updateProcessingPatterns(recent);
        
        // Update system load patterns
        this.updateSystemLoadPatterns(recent);
        
        // Calculate prediction accuracy
        this.calculatePredictionAccuracy();
    }
    
    updateNetworkPatterns(recentData) {
        const networkLatencies = recentData.map(d => d.network);
        const avgNetworkLatency = networkLatencies.reduce((a, b) => a + b, 0) / networkLatencies.length;
        const networkVariance = this.calculateVariance(networkLatencies);
        
        // Classify network condition
        let networkCondition;
        if (avgNetworkLatency < 100 && networkVariance < 50) {
            networkCondition = 'stable_connection';
        } else if (avgNetworkLatency > 500) {
            networkCondition = 'high_traffic';
        } else if (this.isCurrentlyPeakHours()) {
            networkCondition = 'peak_hours';
        } else {
            networkCondition = 'off_peak';
        }
        
        // Update pattern with new data
        const pattern = this.predictionModel.networkPatterns.get(networkCondition);
        if (pattern) {
            pattern.factor = (pattern.factor * 0.9) + (avgNetworkLatency / 100 * 0.1);
            pattern.confidence = Math.min(pattern.confidence + 0.01, 0.99);
        }
    }
    
    updateProcessingPatterns(recentData) {
        const processingLatencies = recentData.map(d => d.processing);
        const avgProcessingLatency = processingLatencies.reduce((a, b) => a + b, 0) / processingLatencies.length;
        
        // Determine processing complexity based on audio quality
        let processingType = 'simple_speech';
        if (window.enhancedSystemIntegration?.audioOptimizer) {
            const quality = window.enhancedSystemIntegration.audioOptimizer.getQualityMetrics();
            if (quality) {
                if (quality.overallScore > 80) {
                    processingType = 'clear_audio';
                } else if (quality.overallScore < 50) {
                    processingType = 'noisy_audio';
                } else if (quality.snr < 2.0) {
                    processingType = 'complex_speech';
                }
            }
        }
        
        // Update processing pattern
        const pattern = this.predictionModel.processingPatterns.get(processingType);
        if (pattern) {
            pattern.latency = (pattern.latency * 0.9) + (avgProcessingLatency * 0.1);
            pattern.confidence = Math.min(pattern.confidence + 0.01, 0.99);
        }
    }
    
    updateSystemLoadPatterns(recentData) {
        const systemLatencies = recentData.map(d => d.system);
        const avgSystemLatency = systemLatencies.reduce((a, b) => a + b, 0) / systemLatencies.length;
        
        // Classify system load
        let loadLevel;
        if (avgSystemLatency < 50) {
            loadLevel = 'low_load';
        } else if (avgSystemLatency < 150) {
            loadLevel = 'medium_load';
        } else if (avgSystemLatency < 300) {
            loadLevel = 'high_load';
        } else {
            loadLevel = 'critical_load';
        }
        
        // Update load pattern
        const pattern = this.predictionModel.systemLoadPatterns.get(loadLevel);
        if (pattern) {
            pattern.multiplier = (pattern.multiplier * 0.9) + (avgSystemLatency / 100 * 0.1);
        }
    }
    
    predictNextLatency() {
        if (this.latencyHistory.length < 5) {
            return this.performanceTargets.targetLatency; // Default prediction
        }
        
        const recent = this.latencyHistory.slice(-5);
        const trends = this.analyzeTrends(recent);
        
        // Base prediction on recent average
        let prediction = recent.reduce((sum, data) => sum + data.total, 0) / recent.length;
        
        // Apply trend adjustments
        if (trends.increasing) {
            prediction *= 1.1;
        } else if (trends.decreasing) {
            prediction *= 0.9;
        }
        
        // Apply pattern-based adjustments
        prediction = this.applyPatternAdjustments(prediction);
        
        // Clamp to reasonable bounds
        return Math.max(50, Math.min(prediction, 5000));
    }
    
    analyzeTrends(data) {
        if (data.length < 3) return { stable: true };
        
        const latencies = data.map(d => d.total);
        let increasingCount = 0;
        let decreasingCount = 0;
        
        for (let i = 1; i < latencies.length; i++) {
            if (latencies[i] > latencies[i - 1]) {
                increasingCount++;
            } else if (latencies[i] < latencies[i - 1]) {
                decreasingCount++;
            }
        }
        
        return {
            increasing: increasingCount > decreasingCount,
            decreasing: decreasingCount > increasingCount,
            stable: increasingCount === decreasingCount
        };
    }
    
    applyPatternAdjustments(basePrediction) {
        let adjustedPrediction = basePrediction;
        
        // Apply network pattern adjustment
        const networkCondition = this.getCurrentNetworkCondition();
        const networkPattern = this.predictionModel.networkPatterns.get(networkCondition);
        if (networkPattern) {
            adjustedPrediction *= networkPattern.factor;
        }
        
        // Apply processing pattern adjustment
        const processingType = this.getCurrentProcessingType();
        const processingPattern = this.predictionModel.processingPatterns.get(processingType);
        if (processingPattern) {
            adjustedPrediction = (adjustedPrediction + processingPattern.latency) / 2;
        }
        
        // Apply system load adjustment
        const loadLevel = this.getCurrentLoadLevel();
        const loadPattern = this.predictionModel.systemLoadPatterns.get(loadLevel);
        if (loadPattern) {
            adjustedPrediction *= loadPattern.multiplier;
        }
        
        return adjustedPrediction;
    }
    
    applyPredictiveOptimizations() {
        const predictedLatency = this.predictNextLatency();
        
        // Apply optimizations if predicted latency exceeds threshold
        if (predictedLatency > this.performanceTargets.optimizationThreshold) {
            this.triggerPreemptiveOptimizations(predictedLatency);
        }
        
        // Broadcast optimization status
        this.broadcastOptimizationStatus(predictedLatency);
    }
    
    triggerPreemptiveOptimizations(predictedLatency) {
        console.log(`🔮 Predicted high latency (${Math.round(predictedLatency)}ms), applying optimizations`);
        
        // 1. Reduce chunk size for faster processing
        if (window.performanceOptimizer && predictedLatency > 800) {
            const currentChunkSize = window.performanceOptimizer.optimizations.chunkSize;
            window.performanceOptimizer.optimizations.chunkSize = Math.max(
                currentChunkSize * 0.8,
                1000
            );
            this.optimizationStrategies.preemptiveChunking = true;
        }
        
        // 2. Reduce concurrent processing to avoid overload
        if (window.performanceOptimizer && predictedLatency > 1000) {
            window.performanceOptimizer.optimizations.maxConcurrent = Math.max(
                window.performanceOptimizer.optimizations.maxConcurrent - 1,
                1
            );
        }
        
        // 3. Adjust audio quality processing
        if (window.enhancedSystemIntegration?.audioOptimizer && predictedLatency > 1200) {
            const optimizer = window.enhancedSystemIntegration.audioOptimizer;
            if (optimizer.filters?.compressor) {
                // Reduce processing complexity
                optimizer.filters.compressor.ratio.setValueAtTime(2, optimizer.audioContext.currentTime);
            }
            this.optimizationStrategies.adaptiveBandwidth = true;
        }
        
        // 4. Enable emergency mode for critical latency
        if (predictedLatency > this.performanceTargets.criticalLatency) {
            this.enableEmergencyMode();
        }
    }
    
    enableEmergencyMode() {
        console.log('🚨 Enabling emergency latency mode');
        
        // Minimal processing configuration
        if (window.performanceOptimizer) {
            window.performanceOptimizer.optimizations.chunkSize = 800;
            window.performanceOptimizer.optimizations.maxConcurrent = 1;
            window.performanceOptimizer.optimizations.bufferSize = 1;
        }
        
        // Disable non-essential enhancements
        if (window.enhancedSystemIntegration) {
            this.optimizationStrategies.resourcePredictiveScaling = true;
        }
        
        // Set flag for emergency mode
        this.optimizationStrategies.emergencyMode = true;
        
        // Auto-disable emergency mode after improvement
        setTimeout(() => {
            this.disableEmergencyMode();
        }, 10000);
    }
    
    disableEmergencyMode() {
        if (!this.optimizationStrategies.emergencyMode) return;
        
        console.log('✅ Disabling emergency latency mode');
        
        // Restore normal settings
        if (window.performanceOptimizer) {
            window.performanceOptimizer.optimizations.chunkSize = 2000;
            window.performanceOptimizer.optimizations.maxConcurrent = 2;
            window.performanceOptimizer.optimizations.bufferSize = 3;
        }
        
        this.optimizationStrategies.emergencyMode = false;
        this.optimizationStrategies.resourcePredictiveScaling = false;
    }
    
    recordLatencyMeasurement(actualLatency) {
        // Compare prediction with actual measurement
        if (this.latencyHistory.length > 0) {
            const lastPrediction = this.predictNextLatency();
            const error = Math.abs(actualLatency - lastPrediction);
            const accuracy = Math.max(0, 1 - (error / actualLatency));
            
            // Update prediction accuracy
            this.predictionAccuracy.shortTerm = (this.predictionAccuracy.shortTerm * 0.9) + (accuracy * 0.1);
        }
    }
    
    calculatePredictionAccuracy() {
        // Calculate how well we're predicting latency
        if (this.latencyHistory.length < 10) return;
        
        const recent = this.latencyHistory.slice(-10);
        let totalError = 0;
        
        for (let i = 1; i < recent.length; i++) {
            const predicted = recent[i - 1].total * 1.1; // Simple next-value prediction
            const actual = recent[i].total;
            const error = Math.abs(predicted - actual) / actual;
            totalError += error;
        }
        
        const avgError = totalError / (recent.length - 1);
        this.predictionAccuracy.mediumTerm = Math.max(0, 1 - avgError);
    }
    
    getCurrentNetworkCondition() {
        if (this.latencyHistory.length === 0) return 'stable_connection';
        
        const recent = this.latencyHistory.slice(-5);
        const avgNetworkLatency = recent.reduce((sum, d) => sum + d.network, 0) / recent.length;
        
        if (avgNetworkLatency > 500) return 'high_traffic';
        if (this.isCurrentlyPeakHours()) return 'peak_hours';
        if (avgNetworkLatency < 100) return 'stable_connection';
        return 'off_peak';
    }
    
    getCurrentProcessingType() {
        if (window.enhancedSystemIntegration?.audioOptimizer) {
            const quality = window.enhancedSystemIntegration.audioOptimizer.getQualityMetrics();
            if (quality) {
                if (quality.overallScore > 80) return 'clear_audio';
                if (quality.overallScore < 50) return 'noisy_audio';
                if (quality.snr < 2.0) return 'complex_speech';
            }
        }
        return 'simple_speech';
    }
    
    getCurrentLoadLevel() {
        if (this.latencyHistory.length === 0) return 'medium_load';
        
        const recent = this.latencyHistory.slice(-3);
        const avgSystemLatency = recent.reduce((sum, d) => sum + d.system, 0) / recent.length;
        
        if (avgSystemLatency < 50) return 'low_load';
        if (avgSystemLatency < 150) return 'medium_load';
        if (avgSystemLatency < 300) return 'high_load';
        return 'critical_load';
    }
    
    isCurrentlyPeakHours() {
        const hour = new Date().getHours();
        // Assume peak hours are 9 AM - 6 PM local time
        return hour >= 9 && hour <= 18;
    }
    
    calculateVariance(numbers) {
        const mean = numbers.reduce((a, b) => a + b, 0) / numbers.length;
        const squaredDiffs = numbers.map(n => Math.pow(n - mean, 2));
        return squaredDiffs.reduce((a, b) => a + b, 0) / numbers.length;
    }
    
    broadcastLatencyPrediction(latencyData) {
        const event = new CustomEvent('latencyPrediction', {
            detail: {
                predicted: latencyData.total,
                breakdown: {
                    network: latencyData.network,
                    processing: latencyData.processing,
                    system: latencyData.system,
                    audio: latencyData.audio
                },
                accuracy: this.predictionAccuracy,
                optimizationsActive: this.optimizationStrategies
            }
        });
        
        window.dispatchEvent(event);
    }
    
    broadcastOptimizationStatus(predictedLatency) {
        const event = new CustomEvent('latencyOptimizationStatus', {
            detail: {
                predictedLatency: predictedLatency,
                targetLatency: this.performanceTargets.targetLatency,
                optimizationsApplied: Object.values(this.optimizationStrategies).some(Boolean),
                strategies: this.optimizationStrategies
            }
        });
        
        window.dispatchEvent(event);
    }
    
    getOptimizationReport() {
        const recent = this.latencyHistory.slice(-20);
        
        return {
            currentPrediction: this.predictNextLatency(),
            predictionAccuracy: this.predictionAccuracy,
            optimizationStrategies: this.optimizationStrategies,
            performanceTargets: this.performanceTargets,
            recentLatencyTrend: recent.length > 0 ? 
                recent.reduce((sum, d) => sum + d.total, 0) / recent.length : 0,
            patternAnalysis: {
                networkCondition: this.getCurrentNetworkCondition(),
                processingType: this.getCurrentProcessingType(),
                loadLevel: this.getCurrentLoadLevel()
            }
        };
    }
    
    stop() {
        this.isActive = false;
        
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
        }
        
        this.disableEmergencyMode();
        console.log('🛑 Predictive latency optimizer stopped');
    }
}

// Export for global use
window.PredictiveLatencyOptimizer = PredictiveLatencyOptimizer;

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
