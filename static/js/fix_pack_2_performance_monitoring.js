/**
 * 📊 FIX PACK 2: PERFORMANCE & MONITORING ENHANCEMENTS
 * Real-time pipeline metrics and comprehensive performance tracking
 */

class PerformanceMonitoringEnhancements {
    constructor() {
        this.metrics = {
            latency: { current: 0, average: 0, p95: 0, samples: [] },
            throughput: { chunksPerSecond: 0, bytesPerSecond: 0 },
            quality: { wer: 0, accuracy: 0, confidence: 0 },
            system: { cpuUsage: 0, memoryUsage: 0, networkLatency: 0 },
            errors: { count: 0, rate: 0, types: {} }
        };
        
        this.performanceTargets = {
            latency: 500, // <500ms target
            wer: 0.10,    // ≤10% WER target
            accuracy: 0.95, // ≥95% accuracy target
            availability: 0.99 // ≥99% uptime target
        };
        
        this.startTime = Date.now();
        this.lastUpdateTime = Date.now();
        this.sampleWindow = 30000; // 30-second sliding window
        
        console.log('📊 Performance Monitoring Enhancements initialized');
    }
    
    /**
     * Start comprehensive performance monitoring
     */
    startMonitoring() {
        // Start metrics collection
        this.startLatencyMonitoring();
        this.startThroughputMonitoring();
        this.startQualityMonitoring();
        this.startSystemMonitoring();
        this.startErrorTracking();
        
        // Start dashboard updates
        this.startDashboardUpdates();
        
        console.log('✅ Performance monitoring active');
    }
    
    /**
     * Monitor transcription latency
     */
    startLatencyMonitoring() {
        // Hook into transcription events
        window.addEventListener('transcriptionStart', (event) => {
            const { chunkId, timestamp } = event.detail;
            this.trackLatencyStart(chunkId, timestamp);
        });
        
        window.addEventListener('transcriptionComplete', (event) => {
            const { chunkId, timestamp, text } = event.detail;
            this.trackLatencyEnd(chunkId, timestamp, text);
        });
    }
    
    /**
     * Track latency start
     */
    trackLatencyStart(chunkId, timestamp) {
        if (!this.latencyTracker) {
            this.latencyTracker = new Map();
        }
        
        this.latencyTracker.set(chunkId, {
            startTime: timestamp || Date.now(),
            endTime: null
        });
    }
    
    /**
     * Track latency end and calculate metrics
     */
    trackLatencyEnd(chunkId, timestamp, text) {
        if (!this.latencyTracker || !this.latencyTracker.has(chunkId)) {
            return;
        }
        
        const tracking = this.latencyTracker.get(chunkId);
        tracking.endTime = timestamp || Date.now();
        
        const latency = tracking.endTime - tracking.startTime;
        
        // Update latency metrics
        this.metrics.latency.current = latency;
        this.metrics.latency.samples.push({
            latency: latency,
            timestamp: tracking.endTime,
            textLength: text ? text.length : 0
        });
        
        // Maintain sliding window
        const cutoffTime = Date.now() - this.sampleWindow;
        this.metrics.latency.samples = this.metrics.latency.samples
            .filter(sample => sample.timestamp > cutoffTime);
        
        // Calculate statistics
        this.updateLatencyStatistics();
        
        // Clean up
        this.latencyTracker.delete(chunkId);
        
        console.log(`⚡ Latency: ${latency}ms (target: <${this.performanceTargets.latency}ms)`);
    }
    
    /**
     * Update latency statistics
     */
    updateLatencyStatistics() {
        const samples = this.metrics.latency.samples;
        if (samples.length === 0) return;
        
        const latencies = samples.map(s => s.latency).sort((a, b) => a - b);
        
        this.metrics.latency.average = latencies.reduce((a, b) => a + b, 0) / latencies.length;
        this.metrics.latency.p95 = latencies[Math.floor(latencies.length * 0.95)] || 0;
    }
    
    /**
     * Monitor throughput metrics
     */
    startThroughputMonitoring() {
        this.throughputTracker = {
            chunks: 0,
            bytes: 0,
            startTime: Date.now()
        };
        
        // Track audio chunks
        window.addEventListener('audioChunkProcessed', (event) => {
            const { size } = event.detail || {};
            this.throughputTracker.chunks++;
            this.throughputTracker.bytes += size || 0;
            
            this.updateThroughputMetrics();
        });
    }
    
    /**
     * Update throughput metrics
     */
    updateThroughputMetrics() {
        const elapsed = (Date.now() - this.throughputTracker.startTime) / 1000;
        if (elapsed > 0) {
            this.metrics.throughput.chunksPerSecond = this.throughputTracker.chunks / elapsed;
            this.metrics.throughput.bytesPerSecond = this.throughputTracker.bytes / elapsed;
        }
    }
    
    /**
     * Monitor quality metrics
     */
    startQualityMonitoring() {
        // Hook into QA pipeline if available
        window.addEventListener('qaMetricsUpdate', (event) => {
            const { wer, accuracy, confidence } = event.detail || {};
            
            if (wer !== undefined) this.metrics.quality.wer = wer;
            if (accuracy !== undefined) this.metrics.quality.accuracy = accuracy;
            if (confidence !== undefined) this.metrics.quality.confidence = confidence;
        });
    }
    
    /**
     * Monitor system performance
     */
    startSystemMonitoring() {
        setInterval(() => {
            // Monitor memory usage
            if (performance.memory) {
                const memUsed = performance.memory.usedJSHeapSize;
                const memLimit = performance.memory.jsHeapSizeLimit;
                this.metrics.system.memoryUsage = (memUsed / memLimit) * 100;
            }
            
            // Monitor network latency
            this.measureNetworkLatency();
            
        }, 5000); // Every 5 seconds
    }
    
    /**
     * Measure network latency
     */
    async measureNetworkLatency() {
        try {
            const startTime = performance.now();
            const response = await fetch('/health', { method: 'HEAD' });
            const endTime = performance.now();
            
            if (response.ok) {
                this.metrics.system.networkLatency = endTime - startTime;
            }
        } catch (error) {
            console.warn('Network latency measurement failed:', error);
        }
    }
    
    /**
     * Track errors
     */
    startErrorTracking() {
        this.errorTracker = {
            errors: [],
            startTime: Date.now()
        };
        
        // Hook into global error events
        window.addEventListener('error', (event) => {
            this.trackError('javascript', event.error, event.message);
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.trackError('promise', event.reason, 'Unhandled promise rejection');
        });
        
        // Hook into transcription errors
        window.addEventListener('transcriptionError', (event) => {
            const { error, context } = event.detail || {};
            this.trackError('transcription', error, context);
        });
    }
    
    /**
     * Track specific error
     */
    trackError(type, error, message) {
        const errorRecord = {
            type: type,
            error: error,
            message: message,
            timestamp: Date.now(),
            stack: error?.stack
        };
        
        this.errorTracker.errors.push(errorRecord);
        
        // Update error metrics
        this.metrics.errors.count = this.errorTracker.errors.length;
        
        // Calculate error rate
        const elapsed = (Date.now() - this.errorTracker.startTime) / 1000;
        this.metrics.errors.rate = elapsed > 0 ? this.metrics.errors.count / elapsed : 0;
        
        // Update error types
        this.metrics.errors.types[type] = (this.metrics.errors.types[type] || 0) + 1;
        
        console.error(`🚨 Error tracked: ${type} - ${message}`);
    }
    
    /**
     * Start real-time dashboard updates
     */
    startDashboardUpdates() {
        setInterval(() => {
            this.updatePerformanceDashboard();
        }, 2000); // Update every 2 seconds
    }
    
    /**
     * Update performance dashboard
     */
    updatePerformanceDashboard() {
        const now = Date.now();
        const uptime = (now - this.startTime) / 1000;
        
        // Update latency display
        const latencyElement = document.getElementById('latencyMetric');
        if (latencyElement) {
            const latency = this.metrics.latency.current;
            const status = latency <= this.performanceTargets.latency ? 'success' : 'warning';
            latencyElement.className = `badge bg-${status}`;
            latencyElement.innerHTML = `⚡ Latency: ${latency.toFixed(0)}ms`;
        }
        
        // Update WER display
        const werElement = document.getElementById('werMetric');
        if (werElement) {
            const wer = this.metrics.quality.wer;
            const status = wer <= this.performanceTargets.wer ? 'success' : 'warning';
            werElement.className = `badge bg-${status}`;
            werElement.innerHTML = `📊 WER: ${(wer * 100).toFixed(1)}%`;
        }
        
        // Update accuracy display
        const accuracyElement = document.getElementById('accuracyMetric');
        if (accuracyElement) {
            const accuracy = this.metrics.quality.accuracy;
            const status = accuracy >= this.performanceTargets.accuracy ? 'success' : 'warning';
            accuracyElement.className = `badge bg-${status}`;
            accuracyElement.innerHTML = `🎯 Accuracy: ${(accuracy * 100).toFixed(1)}%`;
        }
        
        // Update throughput display
        const throughputElement = document.getElementById('throughputMetric');
        if (throughputElement) {
            const cps = this.metrics.throughput.chunksPerSecond;
            throughputElement.className = 'badge bg-info';
            throughputElement.innerHTML = `📦 ${cps.toFixed(1)} chunks/s`;
        }
        
        // Update error count
        const errorElement = document.getElementById('errorMetric');
        if (errorElement) {
            const errorCount = this.metrics.errors.count;
            const status = errorCount === 0 ? 'success' : 'danger';
            errorElement.className = `badge bg-${status}`;
            errorElement.innerHTML = `🚨 ${errorCount} errors`;
        }
        
        console.log(`📊 Performance Update: Latency=${this.metrics.latency.current}ms, WER=${(this.metrics.quality.wer * 100).toFixed(1)}%, Accuracy=${(this.metrics.quality.accuracy * 100).toFixed(1)}%`);
    }
    
    /**
     * Get comprehensive performance report
     */
    getPerformanceReport() {
        const now = Date.now();
        const uptime = (now - this.startTime) / 1000;
        
        return {
            uptime: uptime,
            metrics: this.metrics,
            targets: this.performanceTargets,
            compliance: {
                latency: this.metrics.latency.average <= this.performanceTargets.latency,
                wer: this.metrics.quality.wer <= this.performanceTargets.wer,
                accuracy: this.metrics.quality.accuracy >= this.performanceTargets.accuracy
            },
            timestamp: new Date().toISOString()
        };
    }
}

// Initialize performance monitoring
window.performanceMonitoringEnhancements = new PerformanceMonitoringEnhancements();

// Auto-start monitoring when systems are ready
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        if (window.performanceMonitoringEnhancements) {
            window.performanceMonitoringEnhancements.startMonitoring();
        }
    }, 2000);
});

console.log('✅ Fix Pack 2: Performance Monitoring Enhancements loaded');