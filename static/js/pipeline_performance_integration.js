/**
 * 📊 PIPELINE PERFORMANCE INTEGRATION
 * Connects comprehensive profiler with live transcription pipeline
 */

class PipelinePerformanceIntegration {
    constructor() {
        this.profiler = null;
        this.sessionMetrics = {
            chunks: { total: 0, successful: 0, failed: 0, dropped: 0 },
            latencies: [],
            queueLengths: [],
            interimFinalRatio: { interim: 0, final: 0 },
            memoryUsage: [],
            cpuUsage: [],
            errors: [],
            deduplicationStats: { duplicates: 0, processed: 0 }
        };
        
        this.startTime = null;
        this.lastChunkTime = null;
        this.processingQueue = [];
        
        console.log('📊 Pipeline Performance Integration initialized');
    }
    
    /**
     * Initialize with backend profiler
     */
    async initializeProfiler() {
        try {
            // Try to connect to backend profiler
            const response = await fetch('/api/profiler/status');
            if (response.ok) {
                const status = await response.json();
                console.log('✅ Backend profiler connected:', status);
                this.profiler = { connected: true, backend: true };
            }
        } catch (error) {
            console.log('⚠️ Backend profiler not available, using frontend metrics');
            this.profiler = { connected: true, backend: false };
        }
        
        this.setupMetricsCollection();
    }
    
    /**
     * Setup comprehensive metrics collection
     */
    setupMetricsCollection() {
        // Monitor chunk processing
        this.interceptAudioProcessing();
        
        // Monitor HTTP transcription requests
        this.interceptTranscriptionRequests();
        
        // Monitor system resources
        this.startResourceMonitoring();
        
        // Setup deduplication monitoring
        this.setupDeduplicationMonitoring();
        
        console.log('✅ Comprehensive metrics collection setup complete');
    }
    
    /**
     * Intercept audio processing to measure chunk metrics
     */
    interceptAudioProcessing() {
        // Monitor audio chunk collection events
        window.addEventListener('audiochunkcollected', (event) => {
            const { size, timestamp } = event.detail || { size: 0, timestamp: Date.now() };
            
            this.sessionMetrics.chunks.total++;
            
            // Check for dropped chunks (gaps in timestamps)
            if (this.lastChunkTime && timestamp - this.lastChunkTime > 2000) {
                this.sessionMetrics.chunks.dropped++;
                console.warn(`⚠️ Potential dropped chunk detected: ${timestamp - this.lastChunkTime}ms gap`);
            }
            
            this.lastChunkTime = timestamp;
            
            // Track queue length
            this.sessionMetrics.queueLengths.push(this.processingQueue.length);
            
            console.log(`📦 Chunk metrics: Total=${this.sessionMetrics.chunks.total}, Queue=${this.processingQueue.length}`);
        });
        
        // Create synthetic events for existing audio processing
        const originalLog = console.log;
        console.log = (...args) => {
            if (args[0] && args[0].includes('📦 Audio chunk collected:')) {
                const sizeMatch = args[0].match(/(\d+) bytes/);
                if (sizeMatch) {
                    window.dispatchEvent(new CustomEvent('audiochunkcollected', {
                        detail: { size: parseInt(sizeMatch[1]), timestamp: Date.now() }
                    }));
                }
            }
            originalLog.apply(console, args);
        };
    }
    
    /**
     * Intercept transcription requests for latency measurement
     */
    interceptTranscriptionRequests() {
        const originalFetch = window.fetch;
        window.fetch = async (url, options) => {
            const startTime = performance.now();
            
            if (url.includes('/api/transcribe')) {
                const chunkId = this.generateChunkId();
                this.processingQueue.push({ id: chunkId, startTime });
                
                console.log(`🚀 Transcription request started: ${chunkId}`);
                
                try {
                    const response = await originalFetch(url, options);
                    const endTime = performance.now();
                    const latency = endTime - startTime;
                    
                    // Remove from processing queue
                    this.processingQueue = this.processingQueue.filter(item => item.id !== chunkId);
                    
                    if (response.ok) {
                        this.sessionMetrics.chunks.successful++;
                        this.sessionMetrics.latencies.push(latency);
                        
                        // Parse response for additional metrics
                        const responseClone = response.clone();
                        const result = await responseClone.json();
                        
                        // Track interim vs final ratio
                        if (result.is_interim || result.interim) {
                            this.sessionMetrics.interimFinalRatio.interim++;
                        } else {
                            this.sessionMetrics.interimFinalRatio.final++;
                        }
                        
                        // Emit transcription result event
                        window.dispatchEvent(new CustomEvent('transcriptionresult', {
                            detail: { 
                                transcript: result.transcript || '',
                                timestamp: Date.now(),
                                confidence: result.segments?.[0]?.confidence || 0
                            }
                        }));
                        
                        // Send metrics to backend profiler if available
                        if (this.profiler?.backend) {
                            this.sendMetricsToBackend({
                                type: 'transcription_complete',
                                latency: latency,
                                success: true,
                                text: result.transcript,
                                confidence: result.segments?.[0]?.confidence,
                                session_id: result.session_id,
                                chunk_id: chunkId
                            });
                        }
                        
                        console.log(`✅ Transcription completed: ${chunkId} (${latency.toFixed(0)}ms)`);
                    } else {
                        this.sessionMetrics.chunks.failed++;
                        console.error(`❌ Transcription failed: ${chunkId} (${response.status})`);
                    }
                    
                    return response;
                    
                } catch (error) {
                    // Remove from processing queue
                    this.processingQueue = this.processingQueue.filter(item => item.id !== chunkId);
                    
                    this.sessionMetrics.chunks.failed++;
                    this.sessionMetrics.errors.push({
                        timestamp: Date.now(),
                        error: error.message,
                        type: 'transcription_error'
                    });
                    
                    console.error(`❌ Transcription error: ${chunkId}`, error);
                    throw error;
                }
            }
            
            return originalFetch(url, options);
        };
    }
    
    /**
     * Start monitoring system resources
     */
    startResourceMonitoring() {
        setInterval(() => {
            // Memory usage (approximate)
            if (performance.memory) {
                const memoryMB = performance.memory.usedJSHeapSize / 1024 / 1024;
                this.sessionMetrics.memoryUsage.push(memoryMB);
                
                // Check for memory leaks
                if (this.sessionMetrics.memoryUsage.length > 10) {
                    const recent = this.sessionMetrics.memoryUsage.slice(-10);
                    const trend = recent[recent.length - 1] - recent[0];
                    if (trend > 50) { // 50MB increase
                        console.warn('⚠️ Potential memory leak detected:', trend.toFixed(1), 'MB increase');
                    }
                }
            }
            
            // CPU usage approximation (task scheduling)
            const cpuStart = performance.now();
            setTimeout(() => {
                const cpuLatency = performance.now() - cpuStart;
                this.sessionMetrics.cpuUsage.push(cpuLatency);
                
                // Detect event loop blocking
                if (cpuLatency > 100) {
                    console.warn(`⚠️ Event loop blocking detected: ${cpuLatency.toFixed(0)}ms delay`);
                }
            }, 0);
            
        }, 5000); // Every 5 seconds
    }
    
    /**
     * Setup deduplication monitoring
     */
    setupDeduplicationMonitoring() {
        // Monitor for duplicate transcriptions
        let lastTranscript = '';
        let lastTimestamp = 0;
        
        window.addEventListener('transcriptionresult', (event) => {
            const { transcript, timestamp } = event.detail;
            
            this.sessionMetrics.deduplicationStats.processed++;
            
            // Check for duplicates (same text within 2 seconds)
            if (transcript === lastTranscript && timestamp - lastTimestamp < 2000) {
                this.sessionMetrics.deduplicationStats.duplicates++;
                console.warn(`⚠️ Duplicate transcription detected: "${transcript}"`);
            }
            
            lastTranscript = transcript;
            lastTimestamp = timestamp;
        });
    }
    
    /**
     * Send metrics to backend profiler
     */
    async sendMetricsToBackend(metrics) {
        try {
            await fetch('/api/profiler/metrics', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(metrics)
            });
        } catch (error) {
            console.debug('Backend metrics upload failed:', error.message);
        }
    }
    
    /**
     * Generate unique chunk ID
     */
    generateChunkId() {
        return `chunk_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * Start session profiling
     */
    startSession(sessionId) {
        this.startTime = Date.now();
        this.sessionId = sessionId;
        
        // Reset metrics
        this.sessionMetrics = {
            chunks: { total: 0, successful: 0, failed: 0, dropped: 0 },
            latencies: [],
            queueLengths: [],
            interimFinalRatio: { interim: 0, final: 0 },
            memoryUsage: [],
            cpuUsage: [],
            errors: [],
            deduplicationStats: { duplicates: 0, processed: 0 }
        };
        
        console.log(`📈 Performance profiling started for session: ${sessionId}`);
    }
    
    /**
     * End session and generate comprehensive report
     */
    endSession() {
        const endTime = Date.now();
        const sessionDuration = endTime - this.startTime;
        
        const report = this.generateComprehensiveReport(sessionDuration);
        
        // Send final report to backend
        if (this.profiler?.backend) {
            this.sendMetricsToBackend({
                type: 'session_complete',
                session_id: this.sessionId,
                report: report
            });
        }
        
        console.log('📊 Session Performance Report:', report);
        return report;
    }
    
    /**
     * Generate comprehensive performance report
     */
    generateComprehensiveReport(sessionDuration) {
        const latencies = this.sessionMetrics.latencies;
        
        const report = {
            session: {
                id: this.sessionId,
                duration_ms: sessionDuration,
                start_time: new Date(this.startTime).toISOString(),
                end_time: new Date().toISOString()
            },
            
            chunks: {
                total: this.sessionMetrics.chunks.total,
                successful: this.sessionMetrics.chunks.successful,
                failed: this.sessionMetrics.chunks.failed,
                dropped: this.sessionMetrics.chunks.dropped,
                success_rate: this.sessionMetrics.chunks.total > 0 ? 
                    (this.sessionMetrics.chunks.successful / this.sessionMetrics.chunks.total * 100).toFixed(1) : 0
            },
            
            latency: {
                avg_ms: latencies.length > 0 ? (latencies.reduce((a, b) => a + b, 0) / latencies.length).toFixed(0) : 0,
                min_ms: latencies.length > 0 ? Math.min(...latencies).toFixed(0) : 0,
                max_ms: latencies.length > 0 ? Math.max(...latencies).toFixed(0) : 0,
                p95_ms: latencies.length > 0 ? this.percentile(latencies, 95).toFixed(0) : 0,
                p99_ms: latencies.length > 0 ? this.percentile(latencies, 99).toFixed(0) : 0,
                target_met: latencies.length > 0 ? (latencies.filter(l => l < 500).length / latencies.length * 100).toFixed(1) : 0
            },
            
            queue: {
                avg_length: this.sessionMetrics.queueLengths.length > 0 ? 
                    (this.sessionMetrics.queueLengths.reduce((a, b) => a + b, 0) / this.sessionMetrics.queueLengths.length).toFixed(1) : 0,
                max_length: this.sessionMetrics.queueLengths.length > 0 ? Math.max(...this.sessionMetrics.queueLengths) : 0,
                overflows: this.sessionMetrics.queueLengths.filter(l => l > 5).length
            },
            
            interim_final: {
                interim_count: this.sessionMetrics.interimFinalRatio.interim,
                final_count: this.sessionMetrics.interimFinalRatio.final,
                ratio: this.sessionMetrics.interimFinalRatio.final > 0 ? 
                    (this.sessionMetrics.interimFinalRatio.interim / this.sessionMetrics.interimFinalRatio.final).toFixed(2) : 'N/A'
            },
            
            resources: {
                avg_memory_mb: this.sessionMetrics.memoryUsage.length > 0 ? 
                    (this.sessionMetrics.memoryUsage.reduce((a, b) => a + b, 0) / this.sessionMetrics.memoryUsage.length).toFixed(1) : 0,
                max_memory_mb: this.sessionMetrics.memoryUsage.length > 0 ? Math.max(...this.sessionMetrics.memoryUsage).toFixed(1) : 0,
                avg_cpu_latency_ms: this.sessionMetrics.cpuUsage.length > 0 ? 
                    (this.sessionMetrics.cpuUsage.reduce((a, b) => a + b, 0) / this.sessionMetrics.cpuUsage.length).toFixed(1) : 0,
                event_loop_blocks: this.sessionMetrics.cpuUsage.filter(c => c > 100).length
            },
            
            quality: {
                total_errors: this.sessionMetrics.errors.length,
                duplicate_rate: this.sessionMetrics.deduplicationStats.processed > 0 ? 
                    (this.sessionMetrics.deduplicationStats.duplicates / this.sessionMetrics.deduplicationStats.processed * 100).toFixed(1) : 0,
                deduplication_effectiveness: this.sessionMetrics.deduplicationStats.duplicates === 0 ? 'Excellent' : 
                    this.sessionMetrics.deduplicationStats.duplicates < 3 ? 'Good' : 'Needs Improvement'
            },
            
            performance_assessment: this.assessPerformance(latencies)
        };
        
        return report;
    }
    
    /**
     * Assess overall performance against targets
     */
    assessPerformance(latencies) {
        const avgLatency = latencies.length > 0 ? latencies.reduce((a, b) => a + b, 0) / latencies.length : 0;
        const successRate = this.sessionMetrics.chunks.total > 0 ? 
            this.sessionMetrics.chunks.successful / this.sessionMetrics.chunks.total * 100 : 0;
        
        const assessment = {
            latency_target: avgLatency < 500 ? 'PASS' : 'FAIL',
            success_rate_target: successRate >= 95 ? 'PASS' : 'FAIL',
            queue_stability: Math.max(...this.sessionMetrics.queueLengths || [0]) < 10 ? 'PASS' : 'FAIL',
            memory_stability: this.sessionMetrics.memoryUsage.length > 0 && 
                Math.max(...this.sessionMetrics.memoryUsage) - Math.min(...this.sessionMetrics.memoryUsage) < 100 ? 'PASS' : 'FAIL',
            overall: 'PENDING'
        };
        
        const passCount = Object.values(assessment).filter(v => v === 'PASS').length;
        const totalChecks = Object.keys(assessment).length - 1; // Exclude 'overall'
        
        if (passCount >= totalChecks * 0.8) {
            assessment.overall = 'PASS';
        } else if (passCount >= totalChecks * 0.6) {
            assessment.overall = 'PARTIAL';
        } else {
            assessment.overall = 'FAIL';
        }
        
        return assessment;
    }
    
    /**
     * Calculate percentile
     */
    percentile(arr, p) {
        const sorted = [...arr].sort((a, b) => a - b);
        const index = (p / 100) * (sorted.length - 1);
        const lower = Math.floor(index);
        const upper = Math.ceil(index);
        const weight = index % 1;
        
        return sorted[lower] * (1 - weight) + sorted[upper] * weight;
    }
    
    /**
     * Get current performance snapshot
     */
    getPerformanceSnapshot() {
        const recentLatencies = this.sessionMetrics.latencies.slice(-10);
        
        return {
            current_time: new Date().toISOString(),
            chunks_processed: this.sessionMetrics.chunks.total,
            success_rate: this.sessionMetrics.chunks.total > 0 ? 
                (this.sessionMetrics.chunks.successful / this.sessionMetrics.chunks.total * 100).toFixed(1) : 0,
            avg_latency_recent: recentLatencies.length > 0 ? 
                (recentLatencies.reduce((a, b) => a + b, 0) / recentLatencies.length).toFixed(0) : 0,
            queue_length: this.processingQueue.length,
            errors_count: this.sessionMetrics.errors.length,
            status: this.processingQueue.length > 5 ? 'OVERLOADED' : 
                   this.sessionMetrics.errors.length > 3 ? 'DEGRADED' : 'HEALTHY'
        };
    }
}

// Initialize pipeline performance integration
window.pipelinePerformance = new PipelinePerformanceIntegration();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.pipelinePerformance.initializeProfiler();
});

console.log('✅ Pipeline Performance Integration loaded');

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
