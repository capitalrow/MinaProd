/**
 * CROWN⁴ Performance Monitor
 * 
 * Measures and validates:
 * - Sub-300ms event propagation latency
 * - Animation sync timing
 * - Emotional consistency (smooth transitions)
 * - Cache-first bootstrap performance
 */

class CROWN4PerformanceMonitor {
    constructor() {
        this.measurements = [];
        this.thresholds = {
            eventPropagation: 300,      // ms
            cacheBootstrap: 200,        // ms (TTI target)
            animationFrame: 16.67,      // ms (60fps)
            wsReconnection: 5000        // ms
        };
        
        this.metrics = {
            eventLatencies: [],
            bootstrapTimes: [],
            frameRates: [],
            reconnectionTimes: []
        };
        
        console.log('📊 CROWN⁴ Performance Monitor initialized');
    }
    
    /**
     * Start performance monitoring session
     */
    startSession() {
        this.sessionStart = performance.now();
        this.measurements = [];
        
        // Monitor frame rate
        this._startFrameRateMonitoring();
        
        // Monitor events
        this._startEventMonitoring();
        
        console.log('🎬 Performance monitoring session started');
    }
    
    /**
     * Measure event propagation latency
     */
    measureEventPropagation(eventType, startTime) {
        const endTime = performance.now();
        const latency = endTime - (startTime || this.sessionStart);
        
        this.metrics.eventLatencies.push({
            eventType,
            latency,
            timestamp: new Date().toISOString(),
            withinThreshold: latency < this.thresholds.eventPropagation
        });
        
        const status = latency < this.thresholds.eventPropagation ? '✅' : '⚠️';
        console.log(`${status} Event latency [${eventType}]: ${latency.toFixed(2)}ms (threshold: ${this.thresholds.eventPropagation}ms)`);
        
        return latency;
    }
    
    /**
     * Measure cache-first bootstrap time
     */
    async measureBootstrap() {
        const startTime = performance.now();
        
        try {
            // Simulate cache-first bootstrap
            const cacheAvailable = typeof window.cache !== 'undefined';
            
            if (cacheAvailable && window.cache) {
                // Attempt to load from cache
                const cachedData = await window.cache.get(window.cache.STORES.MEETINGS, 1);
            }
            
            const endTime = performance.now();
            const bootstrapTime = endTime - startTime;
            
            this.metrics.bootstrapTimes.push({
                time: bootstrapTime,
                fromCache: cacheAvailable,
                timestamp: new Date().toISOString(),
                withinThreshold: bootstrapTime < this.thresholds.cacheBootstrap
            });
            
            const status = bootstrapTime < this.thresholds.cacheBootstrap ? '✅' : '⚠️';
            console.log(`${status} Bootstrap time: ${bootstrapTime.toFixed(2)}ms (target: ${this.thresholds.cacheBootstrap}ms)`);
            
            return bootstrapTime;
        } catch (error) {
            console.error('❌ Bootstrap measurement failed:', error);
            return null;
        }
    }
    
    /**
     * Measure animation sync and smoothness
     */
    measureAnimationSync() {
        return new Promise((resolve) => {
            const measurements = [];
            let lastFrameTime = performance.now();
            let frameCount = 0;
            const maxFrames = 60; // Measure 1 second at 60fps
            
            const measureFrame = () => {
                const currentTime = performance.now();
                const frameDuration = currentTime - lastFrameTime;
                
                measurements.push({
                    duration: frameDuration,
                    isSmooth: frameDuration < this.thresholds.animationFrame * 1.5
                });
                
                lastFrameTime = currentTime;
                frameCount++;
                
                if (frameCount < maxFrames) {
                    requestAnimationFrame(measureFrame);
                } else {
                    // Calculate stats
                    const avgFrameTime = measurements.reduce((sum, m) => sum + m.duration, 0) / measurements.length;
                    const fps = 1000 / avgFrameTime;
                    const smoothFrames = measurements.filter(m => m.isSmooth).length;
                    const smoothnessPercentage = (smoothFrames / measurements.length) * 100;
                    
                    const result = {
                        averageFrameTime: avgFrameTime,
                        fps: fps,
                        smoothnessPercentage: smoothnessPercentage,
                        withinThreshold: smoothnessPercentage > 90
                    };
                    
                    this.metrics.frameRates.push(result);
                    
                    const status = result.withinThreshold ? '✅' : '⚠️';
                    console.log(`${status} Animation performance: ${fps.toFixed(1)} fps, ${smoothnessPercentage.toFixed(1)}% smooth`);
                    
                    resolve(result);
                }
            };
            
            requestAnimationFrame(measureFrame);
        });
    }
    
    /**
     * Measure WebSocket reconnection time
     */
    measureReconnection(startTime) {
        const endTime = performance.now();
        const reconnectionTime = endTime - startTime;
        
        this.metrics.reconnectionTimes.push({
            time: reconnectionTime,
            timestamp: new Date().toISOString(),
            withinThreshold: reconnectionTime < this.thresholds.wsReconnection
        });
        
        const status = reconnectionTime < this.thresholds.wsReconnection ? '✅' : '⚠️';
        console.log(`${status} WebSocket reconnection: ${reconnectionTime.toFixed(2)}ms (max: ${this.thresholds.wsReconnection}ms)`);
        
        return reconnectionTime;
    }
    
    /**
     * Monitor frame rate continuously
     */
    _startFrameRateMonitoring() {
        let lastTime = performance.now();
        let frames = [];
        
        const monitorFrame = () => {
            const currentTime = performance.now();
            const delta = currentTime - lastTime;
            
            frames.push(delta);
            
            // Keep only last 60 frames
            if (frames.length > 60) {
                frames.shift();
            }
            
            lastTime = currentTime;
            
            if (this.sessionStart) {
                requestAnimationFrame(monitorFrame);
            }
        };
        
        requestAnimationFrame(monitorFrame);
    }
    
    /**
     * Monitor WebSocket events
     */
    _startEventMonitoring() {
        if (!window.websocketManager) {
            console.warn('⚠️ WebSocket manager not available for event monitoring');
            return;
        }
        
        // Hook into event handling to measure latency
        const originalHandler = window.websocketManager.handleSequencedEvent;
        if (typeof originalHandler === 'function') {
            window.websocketManager.handleSequencedEvent = (eventName, data, namespace) => {
                const startTime = data.server_timestamp ? new Date(data.server_timestamp).getTime() : performance.now();
                
                // Call original handler
                const result = originalHandler.call(window.websocketManager, eventName, data, namespace);
                
                // Measure latency
                this.measureEventPropagation(eventName, startTime);
                
                return result;
            };
        }
    }
    
    /**
     * Run comprehensive performance audit
     */
    async runAudit() {
        console.log('🔍 Starting comprehensive performance audit...');
        
        const results = {
            timestamp: new Date().toISOString(),
            tests: {}
        };
        
        // Test 1: Event propagation
        console.log('\n📡 Testing event propagation latency...');
        const eventStart = performance.now();
        await new Promise(resolve => setTimeout(resolve, 10));
        const eventLatency = this.measureEventPropagation('test_event', eventStart);
        results.tests.eventPropagation = {
            latency: eventLatency,
            threshold: this.thresholds.eventPropagation,
            passed: eventLatency < this.thresholds.eventPropagation
        };
        
        // Test 2: Bootstrap time
        console.log('\n🚀 Testing cache-first bootstrap...');
        const bootstrapTime = await this.measureBootstrap();
        results.tests.bootstrap = {
            time: bootstrapTime,
            threshold: this.thresholds.cacheBootstrap,
            passed: bootstrapTime < this.thresholds.cacheBootstrap
        };
        
        // Test 3: Animation smoothness
        console.log('\n🎬 Testing animation smoothness (60 frames)...');
        const animationResult = await this.measureAnimationSync();
        results.tests.animation = {
            fps: animationResult.fps,
            smoothness: animationResult.smoothnessPercentage,
            passed: animationResult.withinThreshold
        };
        
        // Test 4: Historical metrics
        results.historical = {
            eventLatencies: this.metrics.eventLatencies.length,
            avgEventLatency: this._calculateAverage(this.metrics.eventLatencies.map(e => e.latency)),
            bootstrapTimes: this.metrics.bootstrapTimes.length,
            avgBootstrapTime: this._calculateAverage(this.metrics.bootstrapTimes.map(b => b.time))
        };
        
        // Overall assessment
        const allPassed = Object.values(results.tests).every(test => test.passed !== false);
        results.overall = {
            passed: allPassed,
            score: this._calculateScore(results.tests)
        };
        
        this._printAuditReport(results);
        
        return results;
    }
    
    /**
     * Calculate average
     */
    _calculateAverage(numbers) {
        if (numbers.length === 0) return 0;
        return numbers.reduce((sum, n) => sum + n, 0) / numbers.length;
    }
    
    /**
     * Calculate performance score
     */
    _calculateScore(tests) {
        const total = Object.keys(tests).length;
        const passed = Object.values(tests).filter(t => t.passed !== false).length;
        return Math.round((passed / total) * 100);
    }
    
    /**
     * Print audit report
     */
    _printAuditReport(results) {
        console.log('');
        console.log('═'.repeat(70));
        console.log('📊 CROWN⁴ Performance Audit Report');
        console.log('═'.repeat(70));
        
        console.log('\n📡 Event Propagation:');
        console.log(`   Latency: ${results.tests.eventPropagation.latency.toFixed(2)}ms`);
        console.log(`   Threshold: <${results.tests.eventPropagation.threshold}ms`);
        console.log(`   Status: ${results.tests.eventPropagation.passed ? '✅ PASS' : '❌ FAIL'}`);
        
        console.log('\n🚀 Cache-First Bootstrap:');
        console.log(`   Time: ${results.tests.bootstrap.time.toFixed(2)}ms`);
        console.log(`   Target: <${results.tests.bootstrap.threshold}ms`);
        console.log(`   Status: ${results.tests.bootstrap.passed ? '✅ PASS' : '❌ FAIL'}`);
        
        console.log('\n🎬 Animation Performance:');
        console.log(`   FPS: ${results.tests.animation.fps.toFixed(1)}`);
        console.log(`   Smoothness: ${results.tests.animation.smoothness.toFixed(1)}%`);
        console.log(`   Status: ${results.tests.animation.passed ? '✅ PASS' : '❌ FAIL'}`);
        
        console.log('\n📈 Historical Metrics:');
        console.log(`   Avg Event Latency: ${results.historical.avgEventLatency.toFixed(2)}ms`);
        console.log(`   Avg Bootstrap Time: ${results.historical.avgBootstrapTime.toFixed(2)}ms`);
        
        console.log('\n🎯 Overall Assessment:');
        console.log(`   Score: ${results.overall.score}/100`);
        console.log(`   Status: ${results.overall.passed ? '✅ ALL TESTS PASSED' : '⚠️ SOME TESTS FAILED'}`);
        
        console.log('═'.repeat(70));
        console.log('');
    }
    
    /**
     * Get performance summary
     */
    getSummary() {
        return {
            eventLatencies: {
                count: this.metrics.eventLatencies.length,
                average: this._calculateAverage(this.metrics.eventLatencies.map(e => e.latency)),
                max: Math.max(...this.metrics.eventLatencies.map(e => e.latency), 0),
                min: Math.min(...this.metrics.eventLatencies.map(e => e.latency), 0),
                withinThreshold: this.metrics.eventLatencies.filter(e => e.withinThreshold).length
            },
            bootstrapTimes: {
                count: this.metrics.bootstrapTimes.length,
                average: this._calculateAverage(this.metrics.bootstrapTimes.map(b => b.time)),
                withinThreshold: this.metrics.bootstrapTimes.filter(b => b.withinThreshold).length
            },
            frameRates: {
                count: this.metrics.frameRates.length,
                average: this._calculateAverage(this.metrics.frameRates.map(f => f.fps))
            }
        };
    }
}

// Export for use in console
window.CROWN4PerformanceMonitor = CROWN4PerformanceMonitor;

// Auto-start monitoring in development
if (window.location.search.includes('monitor_performance=true')) {
    window.perfMonitor = new CROWN4PerformanceMonitor();
    window.perfMonitor.startSession();
    console.log('🎯 Performance monitoring active. Run window.perfMonitor.runAudit() for full report.');
}
