/**
 * Frontend Integration for Pipeline Performance Monitor
 * Real-time QA metrics collection and display
 */

class FrontendPipelineMonitor {
    constructor() {
        this.isMonitoring = false;
        this.sessionMetrics = {};
        this.startTime = null;
        console.log('📊 Frontend Pipeline Monitor initialized');
    }
    
    startMonitoring() {
        this.isMonitoring = true;
        this.startTime = performance.now();
        this.sessionMetrics = {
            chunks: [],
            errors: [],
            latencies: [],
            confidences: []
        };
        
        console.log('📊 Performance monitoring started');
    }
    
    stopMonitoring() {
        this.isMonitoring = false;
        
        if (this.sessionMetrics.chunks.length > 0) {
            this.generatePerformanceReport();
        }
        
        console.log('📊 Performance monitoring stopped');
    }
    
    log_chunk_metrics(sessionId, metrics) {
        if (!this.isMonitoring) return;
        
        this.sessionMetrics.chunks.push({
            ...metrics,
            timestamp: Date.now()
        });
        
        // Update real-time performance display
        this.updatePerformanceDisplay(metrics);
        
        // Log structured metrics for backend analysis
        console.log('📊 CHUNK_METRICS:', JSON.stringify(metrics));
    }
    
    updatePerformanceDisplay(metrics) {
        try {
            // Update latency display
            const latencyElement = document.getElementById('latencyMs');
            if (latencyElement && metrics.processing_time) {
                const latencyMs = Math.round(metrics.processing_time);
                latencyElement.textContent = `${latencyMs}ms`;
                
                // Color-code based on performance target (500ms)
                if (latencyMs < 500) {
                    latencyElement.style.color = '#51cf66'; // Green
                } else if (latencyMs < 1000) {
                    latencyElement.style.color = '#ffd93d'; // Yellow
                } else {
                    latencyElement.style.color = '#ff6b6b'; // Red
                }
            }
            
            // Update quality score
            const qualityElement = document.getElementById('qualityScore');
            if (qualityElement && metrics.confidence) {
                const quality = Math.round(metrics.confidence * 100);
                qualityElement.textContent = `${quality}%`;
            }
            
            // Update chunks processed
            const chunksElement = document.getElementById('chunksProcessed');
            if (chunksElement) {
                chunksElement.textContent = metrics.chunk_id || this.sessionMetrics.chunks.length;
            }
            
        } catch (error) {
            console.warn('⚠️ Failed to update performance display:', error);
        }
    }
    
    generatePerformanceReport() {
        const chunks = this.sessionMetrics.chunks;
        if (chunks.length === 0) return;
        
        // Calculate performance metrics
        const latencies = chunks.map(c => c.processing_time).filter(l => l);
        const avgLatency = latencies.reduce((sum, l) => sum + l, 0) / latencies.length;
        const p95Latency = this.calculatePercentile(latencies, 95);
        
        const confidences = chunks.map(c => c.confidence).filter(c => c);
        const avgConfidence = confidences.reduce((sum, c) => sum + c, 0) / confidences.length;
        
        const report = {
            session_summary: {
                total_chunks: chunks.length,
                avg_latency_ms: Math.round(avgLatency),
                p95_latency_ms: Math.round(p95Latency),
                avg_confidence: Math.round(avgConfidence * 100),
                total_duration: performance.now() - this.startTime
            },
            performance_targets: {
                latency_target: 500,
                latency_met: avgLatency < 500,
                confidence_target: 80,
                confidence_met: avgConfidence > 0.8
            }
        };
        
        console.log('📋 PERFORMANCE_REPORT:', JSON.stringify(report, null, 2));
        
        // Show performance summary in UI
        if (window.toastSystem) {
            const status = report.performance_targets.latency_met ? '✅' : '⚠️';
            window.toastSystem.showInfo(
                `${status} Session complete: ${report.session_summary.avg_latency_ms}ms avg latency, ${report.session_summary.avg_confidence}% confidence`
            );
        }
        
        return report;
    }
    
    calculatePercentile(values, percentile) {
        if (values.length === 0) return 0;
        const sorted = [...values].sort((a, b) => a - b);
        const index = (percentile / 100) * (sorted.length - 1);
        const lower = Math.floor(index);
        const upper = Math.ceil(index);
        const weight = index % 1;
        
        if (upper >= sorted.length) return sorted[sorted.length - 1];
        return sorted[lower] * (1 - weight) + sorted[upper] * weight;
    }
}

// Initialize global performance monitor
window.pipeline_monitor = new FrontendPipelineMonitor();

// Expose convenience functions
window.logTranscriptionMetrics = (sessionId, metrics) => {
    window.pipeline_monitor.log_chunk_metrics(sessionId, metrics);
};

console.log('📊 Frontend Pipeline Monitor ready');