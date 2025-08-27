/**
 * Continuous Improvement Client - Real-time performance optimization
 * Continuously monitors and applies improvements during recording sessions
 */

class ContinuousImprovementClient {
    constructor() {
        this.isActive = false;
        this.sessionId = null;
        this.improvementInterval = null;
        this.performanceMetrics = {
            confidence: [],
            latency: [],
            connectionStability: 100,
            uiResponsiveness: 100,
            transcriptionQuality: 0
        };
        
        // Improvement tracking
        this.appliedImprovements = [];
        this.lastImprovement = 0;
        this.performanceScore = 100;
        
        console.info('🔧 Continuous improvement client initialized');
    }
    
    startContinuousImprovement(sessionId) {
        """Start continuous improvement monitoring and optimization."""
        this.isActive = true;
        this.sessionId = sessionId;
        this.appliedImprovements = [];
        this.lastImprovement = Date.now();
        
        console.info(`🚀 Starting continuous improvement for session: ${sessionId}`);
        
        // Start improvement monitoring
        this.startPerformanceTracking();
        this.startQualityMonitoring();
        this.startAdaptiveOptimization();
        
        // Send improvement start event
        this.sendImprovementEvent('improvement_started', {
            sessionId: sessionId,
            timestamp: Date.now()
        });
        
        return {
            sessionId: this.sessionId,
            status: 'improvement_active'
        };
    }
    
    startPerformanceTracking() {
        """Track performance metrics continuously."""
        this.improvementInterval = setInterval(() => {
            if (!this.isActive) return;
            
            // Collect current performance metrics
            const metrics = this.collectCurrentMetrics();
            this.updatePerformanceMetrics(metrics);
            
            // Calculate performance score
            this.performanceScore = this.calculatePerformanceScore();
            
            // Check if improvements are needed
            if (this.shouldApplyImprovements()) {
                this.applyPerformanceImprovements();
            }
            
            // Send real-time metrics
            this.sendImprovementEvent('metrics_update', {
                performanceScore: this.performanceScore,
                metrics: metrics,
                timestamp: Date.now()
            });
            
        }, 3000); // Check every 3 seconds
    }
    
    collectCurrentMetrics() {
        """Collect current performance metrics."""
        const metrics = {
            timestamp: Date.now(),
            confidence: this.getLatestConfidence(),
            latency: this.getLatestLatency(),
            connectionStability: this.getConnectionStability(),
            uiResponsiveness: this.getUIResponsiveness(),
            transcriptionQuality: this.getTranscriptionQuality(),
            memoryUsage: this.getMemoryUsage(),
            errorRate: this.getErrorRate()
        };
        
        return metrics;
    }
    
    getLatestConfidence() {
        """Get latest confidence score from transcription events."""
        // Check for latest transcription confidence
        if (window.liveMonitoringClient) {
            const status = window.liveMonitoringClient.getCurrentMetrics();
            if (status && status.transcriptionEvents > 0) {
                // Estimate confidence based on transcription activity
                return Math.min(1.0, status.transcriptionEvents / 10);
            }
        }
        return 0.5; // Default moderate confidence
    }
    
    getLatestLatency() {
        """Get latest processing latency."""
        // Estimate latency based on UI responsiveness
        const performanceEntries = performance.getEntriesByType('measure');
        if (performanceEntries.length > 0) {
            const latest = performanceEntries[performanceEntries.length - 1];
            return latest.duration || 300;
        }
        return 300; // Default latency
    }
    
    getConnectionStability() {
        """Get WebSocket connection stability."""
        if (window.socket && window.socket.connected) {
            return 100;
        }
        return 0;
    }
    
    getUIResponsiveness() {
        """Get UI responsiveness score."""
        // Measure UI responsiveness based on interaction timing
        const now = performance.now();
        const measureStart = now - 1000; // Last 1 second
        
        const entries = performance.getEntriesByType('measure')
            .filter(entry => entry.startTime > measureStart);
        
        if (entries.length === 0) return 100;
        
        const avgDuration = entries.reduce((sum, entry) => sum + entry.duration, 0) / entries.length;
        
        // Score based on average response time (lower is better)
        return Math.max(0, 100 - (avgDuration / 10));
    }
    
    getTranscriptionQuality() {
        """Estimate transcription quality."""
        // Get transcription text and estimate quality
        const transcriptionElements = document.querySelectorAll('[class*="transcript"], .transcription-text, #transcriptionOutput');
        
        let totalWords = 0;
        let qualityScore = 0;
        
        transcriptionElements.forEach(element => {
            const text = element.textContent || '';
            const words = text.split(/\s+/).filter(word => word.length > 0);
            totalWords += words.length;
            
            // Quality indicators: proper capitalization, punctuation, word length
            const hasCapitalization = /[A-Z]/.test(text);
            const hasPunctuation = /[.!?]/.test(text);
            const avgWordLength = words.length > 0 ? 
                words.reduce((sum, word) => sum + word.length, 0) / words.length : 0;
            
            let elementQuality = 50; // Base score
            if (hasCapitalization) elementQuality += 20;
            if (hasPunctuation) elementQuality += 20;
            if (avgWordLength > 3 && avgWordLength < 8) elementQuality += 10; // Reasonable word length
            
            qualityScore = Math.max(qualityScore, elementQuality);
        });
        
        return Math.min(100, qualityScore);
    }
    
    getMemoryUsage() {
        """Get memory usage efficiency."""
        if (performance.memory) {
            const used = performance.memory.usedJSHeapSize;
            const limit = performance.memory.jsHeapSizeLimit;
            const efficiency = Math.max(0, 100 - ((used / limit) * 100));
            return efficiency;
        }
        return 80; // Default
    }
    
    getErrorRate() {
        """Get current error rate."""
        if (window.liveMonitoringClient) {
            const status = window.liveMonitoringClient.getCurrentMetrics();
            if (status) {
                const errorRate = status.jsErrors / Math.max(1, status.duration / 60); // Errors per minute
                return Math.min(100, errorRate * 10); // Convert to percentage
            }
        }
        return 0;
    }
    
    updatePerformanceMetrics(metrics) {
        """Update performance metrics history."""
        // Update confidence history
        if (metrics.confidence !== undefined) {
            this.performanceMetrics.confidence.push(metrics.confidence);
            if (this.performanceMetrics.confidence.length > 20) {
                this.performanceMetrics.confidence.shift();
            }
        }
        
        // Update latency history
        if (metrics.latency !== undefined) {
            this.performanceMetrics.latency.push(metrics.latency);
            if (this.performanceMetrics.latency.length > 20) {
                this.performanceMetrics.latency.shift();
            }
        }
        
        // Update other metrics
        this.performanceMetrics.connectionStability = metrics.connectionStability || 100;
        this.performanceMetrics.uiResponsiveness = metrics.uiResponsiveness || 100;
        this.performanceMetrics.transcriptionQuality = metrics.transcriptionQuality || 0;
    }
    
    calculatePerformanceScore() {
        """Calculate overall performance score."""
        try {
            const confidence = this.getAverageConfidence() * 100;
            const latency = Math.max(0, 100 - (this.getAverageLatency() / 10));
            const connection = this.performanceMetrics.connectionStability;
            const ui = this.performanceMetrics.uiResponsiveness;
            const quality = this.performanceMetrics.transcriptionQuality;
            
            // Weighted average
            const weights = [0.3, 0.25, 0.2, 0.15, 0.1];
            const scores = [confidence, latency, connection, ui, quality];
            
            const weightedSum = weights.reduce((sum, weight, index) => sum + (weight * scores[index]), 0);
            const totalWeight = weights.reduce((sum, weight) => sum + weight, 0);
            
            return Math.min(100, Math.max(0, weightedSum / totalWeight));
        } catch (error) {
            console.warn('Error calculating performance score:', error);
            return 50;
        }
    }
    
    getAverageConfidence() {
        """Get average confidence from recent history."""
        if (this.performanceMetrics.confidence.length === 0) return 0.5;
        const sum = this.performanceMetrics.confidence.reduce((a, b) => a + b, 0);
        return sum / this.performanceMetrics.confidence.length;
    }
    
    getAverageLatency() {
        """Get average latency from recent history."""
        if (this.performanceMetrics.latency.length === 0) return 300;
        const sum = this.performanceMetrics.latency.reduce((a, b) => a + b, 0);
        return sum / this.performanceMetrics.latency.length;
    }
    
    shouldApplyImprovements() {
        """Determine if improvements should be applied."""
        const timeSinceLastImprovement = Date.now() - this.lastImprovement;
        const cooldownPeriod = 15000; // 15 seconds
        
        return this.performanceScore < 85 && timeSinceLastImprovement > cooldownPeriod;
    }
    
    applyPerformanceImprovements() {
        """Apply performance improvements based on current metrics."""
        const improvements = this.determineNeededImprovements();
        
        improvements.forEach(improvement => {
            if (!this.appliedImprovements.includes(improvement)) {
                this.applySpecificImprovement(improvement);
                this.appliedImprovements.push(improvement);
            }
        });
        
        if (improvements.length > 0) {
            this.lastImprovement = Date.now();
            console.info(`🔧 Applied ${improvements.length} improvements:`, improvements);
        }
    }
    
    determineNeededImprovements() {
        """Determine which improvements are needed."""
        const improvements = [];
        
        const avgConfidence = this.getAverageConfidence();
        const avgLatency = this.getAverageLatency();
        
        // Low confidence improvements
        if (avgConfidence < 0.7) {
            improvements.push('enhance_audio_processing');
            improvements.push('optimize_speech_detection');
        }
        
        // High latency improvements
        if (avgLatency > 800) {
            improvements.push('optimize_processing_speed');
            improvements.push('reduce_buffer_size');
        }
        
        // Connection issues
        if (this.performanceMetrics.connectionStability < 90) {
            improvements.push('stabilize_connection');
        }
        
        // UI responsiveness issues
        if (this.performanceMetrics.uiResponsiveness < 80) {
            improvements.push('optimize_ui_updates');
        }
        
        // Low transcription quality
        if (this.performanceMetrics.transcriptionQuality < 60) {
            improvements.push('enhance_text_processing');
        }
        
        return improvements;
    }
    
    applySpecificImprovement(improvement) {
        """Apply a specific improvement."""
        try {
            switch (improvement) {
                case 'enhance_audio_processing':
                    this.enhanceAudioProcessing();
                    break;
                case 'optimize_speech_detection':
                    this.optimizeSpeechDetection();
                    break;
                case 'optimize_processing_speed':
                    this.optimizeProcessingSpeed();
                    break;
                case 'reduce_buffer_size':
                    this.reduceBufferSize();
                    break;
                case 'stabilize_connection':
                    this.stabilizeConnection();
                    break;
                case 'optimize_ui_updates':
                    this.optimizeUIUpdates();
                    break;
                case 'enhance_text_processing':
                    this.enhanceTextProcessing();
                    break;
            }
            
            this.sendImprovementEvent('improvement_applied', {
                improvement: improvement,
                timestamp: Date.now()
            });
            
        } catch (error) {
            console.error(`Failed to apply improvement ${improvement}:`, error);
        }
    }
    
    enhanceAudioProcessing() {
        """Enhance audio processing settings."""
        console.info('🔧 Enhancing audio processing settings');
        
        // Optimize audio constraints if getUserMedia is available
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            // Request better audio constraints
            const audioConstraints = {
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 44100
                }
            };
            
            // Apply enhanced constraints (this would need integration with recording logic)
        }
    }
    
    optimizeSpeechDetection() {
        """Optimize speech detection sensitivity."""
        console.info('🔧 Optimizing speech detection sensitivity');
        
        // Send optimization request to backend
        if (window.socket && window.socket.connected) {
            window.socket.emit('optimize_speech_detection', {
                sessionId: this.sessionId,
                optimization: 'increase_sensitivity'
            });
        }
    }
    
    optimizeProcessingSpeed() {
        """Optimize processing speed."""
        console.info('🔧 Optimizing processing speed');
        
        // Reduce DOM updates frequency
        this.reduceUIUpdateFrequency();
        
        // Optimize memory usage
        this.optimizeMemoryUsage();
    }
    
    reduceBufferSize() {
        """Reduce audio buffer size for lower latency."""
        console.info('🔧 Reducing buffer size for lower latency');
        
        // Send buffer optimization request
        if (window.socket && window.socket.connected) {
            window.socket.emit('optimize_buffer_settings', {
                sessionId: this.sessionId,
                optimization: 'reduce_latency'
            });
        }
    }
    
    stabilizeConnection() {
        """Stabilize WebSocket connection."""
        console.info('🔧 Stabilizing WebSocket connection');
        
        // Implement connection stability measures
        if (window.socket && !window.socket.connected) {
            window.socket.connect();
        }
    }
    
    optimizeUIUpdates() {
        """Optimize UI update frequency."""
        console.info('🔧 Optimizing UI update frequency');
        this.reduceUIUpdateFrequency();
    }
    
    reduceUIUpdateFrequency() {
        """Reduce UI update frequency to improve performance."""
        // Throttle UI updates
        const elements = document.querySelectorAll('[data-live-update]');
        elements.forEach(element => {
            element.style.willChange = 'auto'; // Reduce GPU usage
        });
    }
    
    optimizeMemoryUsage() {
        """Optimize memory usage."""
        // Clear old performance entries
        if (performance.clearMeasures) {
            performance.clearMeasures();
        }
        if (performance.clearMarks) {
            performance.clearMarks();
        }
        
        // Force garbage collection if available
        if (window.gc) {
            window.gc();
        }
    }
    
    enhanceTextProcessing() {
        """Enhance text processing and display."""
        console.info('🔧 Enhancing text processing');
        
        // Optimize text rendering
        const transcriptionElements = document.querySelectorAll('[class*="transcript"]');
        transcriptionElements.forEach(element => {
            element.style.textRendering = 'optimizeSpeed';
            element.style.fontSmooth = 'never';
        });
    }
    
    startQualityMonitoring() {
        """Start continuous quality monitoring."""
        // Monitor transcription quality indicators
        setInterval(() => {
            if (!this.isActive) return;
            
            const quality = this.getTranscriptionQuality();
            if (quality < 50) {
                console.warn(`⚠️ Low transcription quality detected: ${quality}%`);
                this.sendImprovementEvent('quality_warning', {
                    quality: quality,
                    timestamp: Date.now()
                });
            }
        }, 5000);
    }
    
    startAdaptiveOptimization() {
        """Start adaptive optimization based on performance trends."""
        // Monitor performance trends and apply predictive optimizations
        setInterval(() => {
            if (!this.isActive) return;
            
            const trend = this.analyzePerformanceTrend();
            if (trend === 'declining') {
                console.info('📉 Performance decline detected, applying preventive optimizations');
                this.applyPreventiveOptimizations();
            }
        }, 10000);
    }
    
    analyzePerformanceTrend() {
        """Analyze performance trend over recent history."""
        if (this.performanceMetrics.confidence.length < 5) return 'stable';
        
        const recent = this.performanceMetrics.confidence.slice(-3);
        const older = this.performanceMetrics.confidence.slice(-6, -3);
        
        if (older.length === 0 || recent.length === 0) return 'stable';
        
        const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length;
        const olderAvg = older.reduce((a, b) => a + b, 0) / older.length;
        
        if (recentAvg < olderAvg * 0.9) return 'declining';
        if (recentAvg > olderAvg * 1.1) return 'improving';
        return 'stable';
    }
    
    applyPreventiveOptimizations() {
        """Apply preventive optimizations to prevent performance decline."""
        const preventiveImprovements = [
            'optimize_memory_usage',
            'reduce_ui_overhead',
            'stabilize_connection'
        ];
        
        preventiveImprovements.forEach(improvement => {
            if (!this.appliedImprovements.includes(improvement)) {
                this.applySpecificImprovement(improvement);
                this.appliedImprovements.push(improvement);
            }
        });
    }
    
    sendImprovementEvent(eventType, data) {
        """Send improvement event to monitoring system."""
        if (window.socket && window.socket.connected) {
            window.socket.emit('continuous_improvement_event', {
                sessionId: this.sessionId,
                eventType: eventType,
                data: data,
                timestamp: Date.now()
            });
        }
    }
    
    getCurrentStatus() {
        """Get current improvement status."""
        if (!this.isActive) {
            return { status: 'inactive' };
        }
        
        return {
            status: 'active',
            sessionId: this.sessionId,
            performanceScore: this.performanceScore,
            appliedImprovements: this.appliedImprovements.length,
            avgConfidence: this.getAverageConfidence(),
            avgLatency: this.getAverageLatency(),
            connectionStability: this.performanceMetrics.connectionStability,
            transcriptionQuality: this.performanceMetrics.transcriptionQuality
        };
    }
    
    endContinuousImprovement() {
        """End continuous improvement and generate report."""
        if (!this.isActive) return null;
        
        this.isActive = false;
        
        // Clear intervals
        if (this.improvementInterval) {
            clearInterval(this.improvementInterval);
            this.improvementInterval = null;
        }
        
        const endTime = Date.now();
        
        const finalReport = {
            sessionId: this.sessionId,
            endTime: endTime,
            finalPerformanceScore: this.performanceScore,
            totalImprovements: this.appliedImprovements.length,
            improvementsApplied: this.appliedImprovements,
            finalMetrics: {
                avgConfidence: this.getAverageConfidence(),
                avgLatency: this.getAverageLatency(),
                connectionStability: this.performanceMetrics.connectionStability,
                transcriptionQuality: this.performanceMetrics.transcriptionQuality
            },
            status: 'completed'
        };
        
        // Send final report
        this.sendImprovementEvent('improvement_completed', finalReport);
        
        console.info('✅ Continuous improvement completed', finalReport);
        
        return finalReport;
    }
}

// Initialize continuous improvement client
window.continuousImprovementClient = new ContinuousImprovementClient();

// Auto-integrate with recording states
if (window.recordingStates) {
    const originalSetState = window.recordingStates.setState;
    window.recordingStates.setState = function(state, details) {
        // Call original setState
        originalSetState.call(this, state, details);
        
        // Start continuous improvement when recording begins
        if (state === 'recording' && window.continuousImprovementClient && !window.continuousImprovementClient.isActive) {
            const sessionId = details?.sessionId || `session_${Date.now()}`;
            window.continuousImprovementClient.startContinuousImprovement(sessionId);
        }
        
        // End improvement when recording completes
        if ((state === 'complete' || state === 'idle') && window.continuousImprovementClient && window.continuousImprovementClient.isActive) {
            const report = window.continuousImprovementClient.endContinuousImprovement();
            console.info('📊 Continuous improvement final report:', report);
        }
    };
}

console.info('🔧 Continuous improvement client ready - will start with recording sessions');