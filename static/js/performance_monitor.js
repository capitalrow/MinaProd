/**
 * 🚀 PERFORMANCE MONITOR: Real-time pipeline performance tracking
 * Monitors latency, memory usage, chunk processing, and error rates
 */

class PerformanceMonitor {
    constructor() {
        this.metrics = {
            latency: [],
            throughput: [],
            errorRate: [],
            memoryUsage: [],
            chunkQueue: [],
            processingTime: []
        };
        
        this.thresholds = {
            latency: { good: 500, warning: 1000, critical: 2000 },
            errorRate: { good: 0.01, warning: 0.05, critical: 0.1 },
            memory: { good: 100, warning: 200, critical: 500 }, // MB
            queueLength: { good: 3, warning: 10, critical: 20 }
        };
        
        this.startTime = Date.now();
        this.sessionMetrics = new Map();
        this.alertShown = new Set();
        
        this.initializeMonitoring();
        console.log('🚀 Performance Monitor initialized');
    }
    
    initializeMonitoring() {
        // Create performance display if it doesn't exist
        this.createPerformanceDisplay();
        
        // Start continuous monitoring
        this.monitoringInterval = setInterval(() => {
            this.updatePerformanceMetrics();
        }, 1000);
        
        // Monitor browser performance
        this.startBrowserMonitoring();
    }
    
    createPerformanceDisplay() {
        let perfDisplay = document.getElementById('performance-monitor');
        if (!perfDisplay) {
            perfDisplay = document.createElement('div');
            perfDisplay.id = 'performance-monitor';
            perfDisplay.className = 'performance-monitor';
            perfDisplay.innerHTML = `
                <div class="perf-header">
                    <h4>Pipeline Performance</h4>
                    <div class="perf-status" id="perf-status">Good</div>
                </div>
                <div class="perf-metrics">
                    <div class="metric">
                        <span class="metric-label">Latency</span>
                        <span class="metric-value" id="latency-metric">0ms</span>
                        <div class="metric-bar">
                            <div class="metric-fill" id="latency-fill"></div>
                        </div>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Throughput</span>
                        <span class="metric-value" id="throughput-metric">0 chunks/s</span>
                        <div class="metric-bar">
                            <div class="metric-fill" id="throughput-fill"></div>
                        </div>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Error Rate</span>
                        <span class="metric-value" id="error-metric">0%</span>
                        <div class="metric-bar">
                            <div class="metric-fill" id="error-fill"></div>
                        </div>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Queue Length</span>
                        <span class="metric-value" id="queue-metric">0</span>
                        <div class="metric-bar">
                            <div class="metric-fill" id="queue-fill"></div>
                        </div>
                    </div>
                </div>
                <div class="perf-details" id="perf-details">
                    <div class="detail-item">
                        <span>Avg Latency:</span>
                        <span id="avg-latency">0ms</span>
                    </div>
                    <div class="detail-item">
                        <span>Total Chunks:</span>
                        <span id="total-chunks">0</span>
                    </div>
                    <div class="detail-item">
                        <span>Success Rate:</span>
                        <span id="success-rate">100%</span>
                    </div>
                    <div class="detail-item">
                        <span>Uptime:</span>
                        <span id="uptime">00:00</span>
                    </div>
                </div>
            `;
            
            // Add to page
            const container = document.querySelector('.system-health') || document.body;
            container.appendChild(perfDisplay);
        }
        
        return perfDisplay;
    }
    
    recordChunkProcessing(startTime, endTime, success = true, errorType = null) {
        const latency = endTime - startTime;
        const now = Date.now();
        
        // Record metrics
        this.metrics.latency.push({ timestamp: now, value: latency });
        this.metrics.processingTime.push({ timestamp: now, value: latency });
        
        if (!success) {
            this.metrics.errorRate.push({ 
                timestamp: now, 
                value: 1, 
                errorType: errorType || 'unknown' 
            });
        }
        
        // Trim old data (keep last 100 measurements)
        Object.keys(this.metrics).forEach(key => {
            if (this.metrics[key].length > 100) {
                this.metrics[key].shift();
            }
        });
        
        // Calculate throughput
        this.calculateThroughput();
        
        // Check for performance issues
        this.checkPerformanceAlerts(latency, success);
        
        console.log(`📊 Performance: ${latency}ms latency, ${success ? 'success' : 'error'}`);
    }
    
    recordQueueLength(length) {
        this.metrics.chunkQueue.push({
            timestamp: Date.now(),
            value: length
        });
        
        // Check queue length alerts
        if (length > this.thresholds.queueLength.critical) {
            this.showAlert('critical', 'Queue Overload', `${length} chunks queued - system overloaded`);
        } else if (length > this.thresholds.queueLength.warning) {
            this.showAlert('warning', 'Queue Building', `${length} chunks queued`);
        }
    }
    
    calculateThroughput() {
        const now = Date.now();
        const oneSecondAgo = now - 1000;
        
        // Count chunks processed in last second
        const recentChunks = this.metrics.processingTime.filter(
            metric => metric.timestamp > oneSecondAgo
        );
        
        const throughput = recentChunks.length;
        this.metrics.throughput.push({ timestamp: now, value: throughput });
        
        if (this.metrics.throughput.length > 100) {
            this.metrics.throughput.shift();
        }
    }
    
    updatePerformanceMetrics() {
        const now = Date.now();
        
        // Calculate current values
        const currentLatency = this.getAverageLatency();
        const currentThroughput = this.getCurrentThroughput();
        const currentErrorRate = this.getCurrentErrorRate();
        const currentQueueLength = this.getCurrentQueueLength();
        
        // Update display
        this.updateMetricDisplay('latency', currentLatency, 'ms');
        this.updateMetricDisplay('throughput', currentThroughput, ' chunks/s');
        this.updateMetricDisplay('error', (currentErrorRate * 100).toFixed(1), '%');
        this.updateMetricDisplay('queue', currentQueueLength, '');
        
        // Update status
        this.updateOverallStatus(currentLatency, currentErrorRate);
        
        // Update detailed metrics
        this.updateDetailedMetrics();
        
        // Monitor memory usage if available
        this.monitorMemoryUsage();
    }
    
    updateMetricDisplay(metricName, value, unit) {
        const element = document.getElementById(`${metricName}-metric`);
        const fillElement = document.getElementById(`${metricName}-fill`);
        
        if (element) {
            element.textContent = `${value}${unit}`;
        }
        
        if (fillElement) {
            // Calculate fill percentage and color based on thresholds
            let percentage, color;
            
            switch (metricName) {
                case 'latency':
                    percentage = Math.min(100, (value / this.thresholds.latency.critical) * 100);
                    color = this.getMetricColor(value, this.thresholds.latency);
                    break;
                case 'error':
                    percentage = Math.min(100, (value / 10) * 100); // Cap at 10%
                    color = value < 1 ? '#4CAF50' : value < 5 ? '#FF9800' : '#F44336';
                    break;
                case 'queue':
                    percentage = Math.min(100, (value / this.thresholds.queueLength.critical) * 100);
                    color = this.getMetricColor(value, this.thresholds.queueLength);
                    break;
                case 'throughput':
                    percentage = Math.min(100, value * 10); // Scale for display
                    color = value > 5 ? '#4CAF50' : value > 2 ? '#FF9800' : '#F44336';
                    break;
            }
            
            fillElement.style.width = `${percentage}%`;
            fillElement.style.backgroundColor = color;
        }
    }
    
    getMetricColor(value, thresholds) {
        if (value <= thresholds.good) return '#4CAF50'; // Green
        if (value <= thresholds.warning) return '#FF9800'; // Orange
        return '#F44336'; // Red
    }
    
    getAverageLatency() {
        if (this.metrics.latency.length === 0) return 0;
        
        const recent = this.metrics.latency.slice(-10); // Last 10 measurements
        const sum = recent.reduce((acc, metric) => acc + metric.value, 0);
        return Math.round(sum / recent.length);
    }
    
    getCurrentThroughput() {
        if (this.metrics.throughput.length === 0) return 0;
        return this.metrics.throughput[this.metrics.throughput.length - 1].value;
    }
    
    getCurrentErrorRate() {
        if (this.metrics.processingTime.length === 0) return 0;
        
        const totalChunks = this.metrics.processingTime.length;
        const errorChunks = this.metrics.errorRate.length;
        return errorChunks / totalChunks;
    }
    
    getCurrentQueueLength() {
        if (this.metrics.chunkQueue.length === 0) return 0;
        return this.metrics.chunkQueue[this.metrics.chunkQueue.length - 1].value;
    }
    
    updateOverallStatus(latency, errorRate) {
        const statusElement = document.getElementById('perf-status');
        if (!statusElement) return;
        
        let status, className;
        
        if (latency > this.thresholds.latency.critical || errorRate > this.thresholds.errorRate.critical) {
            status = 'Critical';
            className = 'status-critical';
        } else if (latency > this.thresholds.latency.warning || errorRate > this.thresholds.errorRate.warning) {
            status = 'Warning';
            className = 'status-warning';
        } else {
            status = 'Good';
            className = 'status-good';
        }
        
        statusElement.textContent = status;
        statusElement.className = `perf-status ${className}`;
    }
    
    updateDetailedMetrics() {
        const avgLatencyElement = document.getElementById('avg-latency');
        const totalChunksElement = document.getElementById('total-chunks');
        const successRateElement = document.getElementById('success-rate');
        const uptimeElement = document.getElementById('uptime');
        
        if (avgLatencyElement) {
            avgLatencyElement.textContent = `${this.getAverageLatency()}ms`;
        }
        
        if (totalChunksElement) {
            totalChunksElement.textContent = this.metrics.processingTime.length;
        }
        
        if (successRateElement) {
            const successRate = (1 - this.getCurrentErrorRate()) * 100;
            successRateElement.textContent = `${successRate.toFixed(1)}%`;
        }
        
        if (uptimeElement) {
            const uptime = Date.now() - this.startTime;
            uptimeElement.textContent = this.formatUptime(uptime);
        }
    }
    
    formatUptime(milliseconds) {
        const seconds = Math.floor(milliseconds / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) {
            return `${hours}:${(minutes % 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
        }
        return `${minutes}:${(seconds % 60).toString().padStart(2, '0')}`;
    }
    
    checkPerformanceAlerts(latency, success) {
        const alertKey = `latency-${Date.now()}`;
        
        if (latency > this.thresholds.latency.critical && !this.alertShown.has('latency-critical')) {
            this.showAlert('critical', 'High Latency', `Processing taking ${latency}ms - performance degraded`);
            this.alertShown.add('latency-critical');
            setTimeout(() => this.alertShown.delete('latency-critical'), 30000);
        }
        
        if (!success && !this.alertShown.has('error-spike')) {
            const recentErrors = this.metrics.errorRate.filter(
                metric => Date.now() - metric.timestamp < 10000
            );
            
            if (recentErrors.length > 3) {
                this.showAlert('warning', 'Error Spike', 'Multiple transcription errors detected');
                this.alertShown.add('error-spike');
                setTimeout(() => this.alertShown.delete('error-spike'), 60000);
            }
        }
    }
    
    showAlert(level, title, message) {
        console.warn(`🚨 Performance Alert [${level.toUpperCase()}] ${title}: ${message}`);
        
        if (window.toastSystem) {
            window.toastSystem.show({
                type: level === 'critical' ? 'error' : 'warning',
                title: title,
                message: message,
                duration: level === 'critical' ? 10000 : 5000
            });
        }
        
        // Also update UI status
        const statusElement = document.getElementById('perf-status');
        if (statusElement && level === 'critical') {
            statusElement.textContent = 'Critical';
            statusElement.className = 'perf-status status-critical';
        }
    }
    
    startBrowserMonitoring() {
        // Monitor browser performance APIs if available
        if ('performance' in window) {
            setInterval(() => {
                const navigation = performance.getEntriesByType('navigation')[0];
                if (navigation) {
                    // Track page load performance
                    const loadTime = navigation.loadEventEnd - navigation.fetchStart;
                    console.log(`📊 Page performance: ${loadTime}ms load time`);
                }
            }, 60000); // Every minute
        }
    }
    
    monitorMemoryUsage() {
        // Monitor memory if available (Chrome only)
        if ('memory' in performance) {
            const memory = performance.memory;
            const usedMB = Math.round(memory.usedJSHeapSize / 1048576);
            const limitMB = Math.round(memory.jsHeapSizeLimit / 1048576);
            
            this.metrics.memoryUsage.push({
                timestamp: Date.now(),
                value: usedMB,
                limit: limitMB
            });
            
            // Keep last 60 measurements
            if (this.metrics.memoryUsage.length > 60) {
                this.metrics.memoryUsage.shift();
            }
            
            // Check memory alerts
            if (usedMB > this.thresholds.memory.critical) {
                this.showAlert('critical', 'High Memory Usage', `${usedMB}MB used - risk of crashes`);
            } else if (usedMB > this.thresholds.memory.warning) {
                this.showAlert('warning', 'Memory Usage High', `${usedMB}MB used`);
            }
        }
    }
    
    getPerformanceReport() {
        return {
            summary: {
                avgLatency: this.getAverageLatency(),
                currentThroughput: this.getCurrentThroughput(),
                errorRate: this.getCurrentErrorRate(),
                uptime: Date.now() - this.startTime,
                totalChunks: this.metrics.processingTime.length
            },
            metrics: this.metrics,
            thresholds: this.thresholds
        };
    }
    
    reset() {
        // Clear all metrics
        Object.keys(this.metrics).forEach(key => {
            this.metrics[key] = [];
        });
        
        this.startTime = Date.now();
        this.alertShown.clear();
        
        console.log('🔄 Performance monitor reset');
    }
    
    destroy() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
        }
        
        const display = document.getElementById('performance-monitor');
        if (display) {
            display.remove();
        }
        
        console.log('🗑️ Performance monitor destroyed');
    }
}

// Initialize global performance monitor
window.performanceMonitor = new PerformanceMonitor();

// Hook into existing transcription functions
if (window.audioChunkHandler) {
    const originalSend = window.audioChunkHandler.sendCompleteAudio;
    window.audioChunkHandler.sendCompleteAudio = function(audioBlob) {
        const startTime = Date.now();
        
        return originalSend.call(this, audioBlob).then(result => {
            const endTime = Date.now();
            window.performanceMonitor.recordChunkProcessing(startTime, endTime, true);
            return result;
        }).catch(error => {
            const endTime = Date.now();
            window.performanceMonitor.recordChunkProcessing(startTime, endTime, false, error.message);
            throw error;
        });
    };
}

console.log('✅ Performance monitoring system loaded');