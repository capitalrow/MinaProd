/**
 * PERFORMANCE OPTIMIZER
 * Comprehensive system optimization for minimal latency and maximum throughput
 */

class PerformanceOptimizer {
    constructor() {
        this.metrics = {
            latency: [],
            throughput: [],
            memoryUsage: [],
            cpuUsage: [],
            networkDelay: []
        };
        
        this.optimizations = {
            chunkSize: 2000, // Base chunk size in ms
            bufferSize: 3,   // Number of chunks to buffer
            maxConcurrent: 2, // Max concurrent processing
            adaptiveMode: true
        };
        
        this.currentLoad = 0;
        this.processingQueue = [];
        this.activeProcessing = 0;
        this.performanceHistory = [];
        
        this.startPerformanceMonitoring();
    }
    
    startPerformanceMonitoring() {
        // Monitor system performance every second
        this.monitoringInterval = setInterval(() => {
            this.measureSystemPerformance();
            this.optimizeParameters();
            this.cleanupResources();
        }, 1000);
        
        console.log('📊 Performance monitoring started');
    }
    
    measureSystemPerformance() {
        const now = performance.now();
        
        // Memory usage (if available)
        if (performance.memory) {
            const memoryUsage = performance.memory.usedJSHeapSize / performance.memory.totalJSHeapSize;
            this.metrics.memoryUsage.push(memoryUsage);
        }
        
        // Network performance estimation
        const networkStart = performance.now();
        fetch('/api/ping').then(() => {
            const networkLatency = performance.now() - networkStart;
            this.metrics.networkDelay.push(networkLatency);
        }).catch(() => {
            // Fallback for network measurement
            this.metrics.networkDelay.push(100); // Assume 100ms baseline
        });
        
        // Keep metrics arrays bounded
        Object.keys(this.metrics).forEach(key => {
            if (this.metrics[key].length > 60) { // Keep last 60 seconds
                this.metrics[key].shift();
            }
        });
    }
    
    optimizeParameters() {
        const avgLatency = this.getAverageLatency();
        const memoryPressure = this.getMemoryPressure();
        const networkDelay = this.getAverageNetworkDelay();
        
        // Adaptive chunk size optimization
        if (this.optimizations.adaptiveMode) {
            this.optimizeChunkSize(avgLatency, networkDelay);
            this.optimizeBufferSize(memoryPressure);
            this.optimizeConcurrency(avgLatency, this.currentLoad);
        }
        
        // Log optimization decisions
        this.logOptimizationMetrics();
    }
    
    optimizeChunkSize(latency, networkDelay) {
        let optimalChunkSize = this.optimizations.chunkSize;
        
        // If latency is high, use larger chunks for efficiency
        if (latency > 3000) {
            optimalChunkSize = Math.min(optimalChunkSize * 1.2, 5000);
        } 
        // If latency is low, use smaller chunks for responsiveness
        else if (latency < 1500) {
            optimalChunkSize = Math.max(optimalChunkSize * 0.9, 1000);
        }
        
        // Adjust for network conditions
        if (networkDelay > 200) {
            optimalChunkSize = Math.min(optimalChunkSize * 1.1, 5000);
        }
        
        this.optimizations.chunkSize = Math.round(optimalChunkSize);
    }
    
    optimizeBufferSize(memoryPressure) {
        if (memoryPressure > 0.8) {
            // High memory pressure - reduce buffer
            this.optimizations.bufferSize = Math.max(this.optimizations.bufferSize - 1, 1);
        } else if (memoryPressure < 0.5) {
            // Low memory pressure - can increase buffer
            this.optimizations.bufferSize = Math.min(this.optimizations.bufferSize + 1, 5);
        }
    }
    
    optimizeConcurrency(latency, currentLoad) {
        if (latency > 4000 && currentLoad < 0.7) {
            // High latency but low load - increase concurrency
            this.optimizations.maxConcurrent = Math.min(this.optimizations.maxConcurrent + 1, 4);
        } else if (latency > 5000 || currentLoad > 0.9) {
            // Very high latency or load - reduce concurrency
            this.optimizations.maxConcurrent = Math.max(this.optimizations.maxConcurrent - 1, 1);
        }
    }
    
    getAverageLatency() {
        if (this.metrics.latency.length === 0) return 2000; // Default
        return this.metrics.latency.reduce((a, b) => a + b, 0) / this.metrics.latency.length;
    }
    
    getMemoryPressure() {
        if (this.metrics.memoryUsage.length === 0) return 0.5; // Default
        const recent = this.metrics.memoryUsage.slice(-10);
        return recent.reduce((a, b) => a + b, 0) / recent.length;
    }
    
    getAverageNetworkDelay() {
        if (this.metrics.networkDelay.length === 0) return 100; // Default
        const recent = this.metrics.networkDelay.slice(-5);
        return recent.reduce((a, b) => a + b, 0) / recent.length;
    }
    
    async processWithOptimization(audioData, processor) {
        const startTime = performance.now();
        
        // Check if we can process now or need to queue
        if (this.activeProcessing >= this.optimizations.maxConcurrent) {
            return this.queueProcessing(audioData, processor);
        }
        
        this.activeProcessing++;
        this.currentLoad = this.activeProcessing / this.optimizations.maxConcurrent;
        
        try {
            const result = await processor(audioData);
            const endTime = performance.now();
            const processingTime = endTime - startTime;
            
            // Record metrics
            this.recordProcessingMetrics(processingTime, audioData.size);
            
            return result;
            
        } finally {
            this.activeProcessing--;
            this.currentLoad = this.activeProcessing / this.optimizations.maxConcurrent;
            
            // Process next item in queue
            this.processQueue();
        }
    }
    
    queueProcessing(audioData, processor) {
        return new Promise((resolve, reject) => {
            this.processingQueue.push({
                audioData,
                processor,
                resolve,
                reject,
                queueTime: performance.now()
            });
            
            // Prevent queue from growing too large
            if (this.processingQueue.length > 10) {
                const dropped = this.processingQueue.shift();
                dropped.reject(new Error('Processing queue overflow'));
            }
        });
    }
    
    async processQueue() {
        if (this.processingQueue.length === 0 || this.activeProcessing >= this.optimizations.maxConcurrent) {
            return;
        }
        
        const item = this.processingQueue.shift();
        const queueDelay = performance.now() - item.queueTime;
        
        try {
            const result = await this.processWithOptimization(item.audioData, item.processor);
            
            // Add queue delay to result
            if (result && typeof result === 'object') {
                result.queue_delay_ms = queueDelay;
            }
            
            item.resolve(result);
        } catch (error) {
            item.reject(error);
        }
    }
    
    recordProcessingMetrics(processingTime, dataSize) {
        // Record latency
        this.metrics.latency.push(processingTime);
        
        // Record throughput (bytes per second)
        const throughput = dataSize / (processingTime / 1000);
        this.metrics.throughput.push(throughput);
        
        // Update performance history
        this.performanceHistory.push({
            timestamp: Date.now(),
            latency: processingTime,
            throughput: throughput,
            concurrency: this.activeProcessing,
            queueLength: this.processingQueue.length
        });
        
        // Keep history bounded
        if (this.performanceHistory.length > 100) {
            this.performanceHistory.shift();
        }
    }
    
    logOptimizationMetrics() {
        if (this.performanceHistory.length % 10 === 0) { // Log every 10 measurements
            const avgLatency = this.getAverageLatency();
            const memoryPressure = this.getMemoryPressure();
            
            console.log(`🔧 Performance Optimization Status:
                Avg Latency: ${Math.round(avgLatency)}ms
                Chunk Size: ${this.optimizations.chunkSize}ms
                Buffer Size: ${this.optimizations.bufferSize}
                Max Concurrent: ${this.optimizations.maxConcurrent}
                Current Load: ${Math.round(this.currentLoad * 100)}%
                Memory Pressure: ${Math.round(memoryPressure * 100)}%
                Queue Length: ${this.processingQueue.length}`);
        }
    }
    
    cleanupResources() {
        // Clean up old processing items that might be stuck
        const now = performance.now();
        this.processingQueue = this.processingQueue.filter(item => {
            const age = now - item.queueTime;
            if (age > 30000) { // 30 seconds timeout
                item.reject(new Error('Processing timeout'));
                return false;
            }
            return true;
        });
    }
    
    getOptimizationSettings() {
        return {
            ...this.optimizations,
            currentMetrics: {
                avgLatency: this.getAverageLatency(),
                memoryPressure: this.getMemoryPressure(),
                networkDelay: this.getAverageNetworkDelay(),
                currentLoad: this.currentLoad,
                queueLength: this.processingQueue.length
            }
        };
    }
    
    getPerformanceReport() {
        const recent = this.performanceHistory.slice(-20);
        
        if (recent.length === 0) {
            return { status: 'No data available' };
        }
        
        return {
            averageLatency: recent.reduce((sum, item) => sum + item.latency, 0) / recent.length,
            averageThroughput: recent.reduce((sum, item) => sum + item.throughput, 0) / recent.length,
            peakConcurrency: Math.max(...recent.map(item => item.concurrency)),
            averageQueueLength: recent.reduce((sum, item) => sum + item.queueLength, 0) / recent.length,
            optimizationSettings: this.optimizations,
            recommendations: this.generateRecommendations()
        };
    }
    
    generateRecommendations() {
        const avgLatency = this.getAverageLatency();
        const memoryPressure = this.getMemoryPressure();
        const recommendations = [];
        
        if (avgLatency > 4000) {
            recommendations.push('Consider increasing chunk size for better efficiency');
        }
        
        if (memoryPressure > 0.8) {
            recommendations.push('High memory usage detected - consider reducing buffer size');
        }
        
        if (this.processingQueue.length > 5) {
            recommendations.push('Processing queue building up - consider increasing concurrency');
        }
        
        return recommendations;
    }
    
    stop() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
        }
        
        // Reject any pending queue items
        this.processingQueue.forEach(item => {
            item.reject(new Error('Performance optimizer stopped'));
        });
        
        console.log('🛑 Performance optimizer stopped');
    }
}

// Export for global use
window.PerformanceOptimizer = PerformanceOptimizer;

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
