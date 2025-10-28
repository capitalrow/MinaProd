/**
 * CROWN⁴ Load Testing Suite
 * 
 * Tests system performance under load:
 * - 10k+ sessions in IndexedDB
 * - Event sequence ordering at scale
 * - Memory limits and leak detection
 * - Cache performance degradation
 */

class CROWN4LoadTest {
    constructor() {
        this.testData = [];
        this.results = {
            sessions: {
                created: 0,
                failed: 0,
                totalTime: 0
            },
            events: {
                processed: 0,
                outOfOrder: 0,
                duplicates: 0
            },
            memory: {
                initial: 0,
                peak: 0,
                final: 0,
                leakDetected: false
            },
            cache: {
                writes: 0,
                reads: 0,
                avgWriteTime: 0,
                avgReadTime: 0
            }
        };
        
        console.log('🚀 CROWN⁴ Load Test Suite initialized');
    }
    
    /**
     * Run full load test suite
     */
    async runFullSuite(options = {}) {
        const sessionCount = options.sessionCount || 10000;
        const eventCount = options.eventCount || 5000;
        const concurrency = options.concurrency || 100;
        
        console.log('═'.repeat(70));
        console.log(`🏋️ Starting CROWN⁴ Load Test Suite`);
        console.log(`   Sessions: ${sessionCount.toLocaleString()}`);
        console.log(`   Events: ${eventCount.toLocaleString()}`);
        console.log(`   Concurrency: ${concurrency}`);
        console.log('═'.repeat(70));
        
        // Record initial memory
        this.results.memory.initial = this._getMemoryUsage();
        
        try {
            // Test 1: Session creation and IndexedDB storage
            await this.testSessionCreation(sessionCount, concurrency);
            
            // Test 2: Event sequencing at scale
            await this.testEventSequencing(eventCount);
            
            // Test 3: Cache read performance
            await this.testCachePerformance();
            
            // Test 4: Memory leak detection
            await this.testMemoryLeaks();
            
            // Test 5: Concurrent operations
            await this.testConcurrency(concurrency);
            
        } catch (error) {
            console.error('❌ Load test failed:', error);
        }
        
        // Record final memory
        this.results.memory.final = this._getMemoryUsage();
        
        return this._generateReport();
    }
    
    /**
     * Test session creation at scale
     */
    async testSessionCreation(count, batchSize = 100) {
        console.log(`\n📝 Testing session creation (${count.toLocaleString()} sessions)...`);
        
        const startTime = performance.now();
        const cache = window.cache;
        
        if (!cache) {
            console.warn('⚠️ Cache not available, skipping session creation test');
            return;
        }
        
        try {
            // Create sessions in batches
            for (let batch = 0; batch < count; batch += batchSize) {
                const batchEnd = Math.min(batch + batchSize, count);
                const promises = [];
                
                for (let i = batch; i < batchEnd; i++) {
                    const session = this._generateMockSession(i);
                    promises.push(
                        cache.put(cache.STORES.MEETINGS, session)
                            .then(() => {
                                this.results.sessions.created++;
                            })
                            .catch(err => {
                                this.results.sessions.failed++;
                                console.error(`Failed to create session ${i}:`, err);
                            })
                    );
                }
                
                await Promise.all(promises);
                
                // Progress update
                if ((batch + batchSize) % 1000 === 0) {
                    const progress = ((batch + batchSize) / count * 100).toFixed(1);
                    console.log(`   Progress: ${progress}% (${batch + batchSize}/${count})`);
                }
            }
            
            const endTime = performance.now();
            this.results.sessions.totalTime = endTime - startTime;
            
            const rate = count / (this.results.sessions.totalTime / 1000);
            console.log(`✅ Created ${this.results.sessions.created.toLocaleString()} sessions in ${this.results.sessions.totalTime.toFixed(2)}ms`);
            console.log(`   Rate: ${rate.toFixed(0)} sessions/second`);
            
        } catch (error) {
            console.error('❌ Session creation test failed:', error);
        }
    }
    
    /**
     * Test event sequencing at scale
     */
    async testEventSequencing(count) {
        console.log(`\n⚡ Testing event sequencing (${count.toLocaleString()} events)...`);
        
        const events = [];
        
        // Generate events
        for (let i = 1; i <= count; i++) {
            events.push({
                event_id: i,
                sequence: i,
                event_type: 'test_event',
                data: { index: i },
                timestamp: new Date().toISOString()
            });
        }
        
        // Shuffle to simulate out-of-order arrival
        const shuffled = this._shuffle([...events]);
        
        // Process events with sequence validation
        const processed = [];
        const buffer = [];
        const seenIds = new Set();
        let lastSequence = 0;
        
        const startTime = performance.now();
        
        for (const event of shuffled) {
            // Check for duplicates
            if (seenIds.has(event.event_id)) {
                this.results.events.duplicates++;
                continue;
            }
            seenIds.add(event.event_id);
            
            // Add to buffer
            buffer.push(event);
            buffer.sort((a, b) => a.sequence - b.sequence);
            
            // Process in-order events
            while (buffer.length > 0 && buffer[0].sequence === lastSequence + 1) {
                const next = buffer.shift();
                processed.push(next);
                lastSequence = next.sequence;
                this.results.events.processed++;
            }
        }
        
        // Process remaining buffered events
        while (buffer.length > 0) {
            const next = buffer.shift();
            if (next.sequence !== lastSequence + 1) {
                this.results.events.outOfOrder++;
            }
            processed.push(next);
            lastSequence = next.sequence;
            this.results.events.processed++;
        }
        
        const endTime = performance.now();
        const processingTime = endTime - startTime;
        const rate = count / (processingTime / 1000);
        
        console.log(`✅ Processed ${this.results.events.processed.toLocaleString()} events in ${processingTime.toFixed(2)}ms`);
        console.log(`   Rate: ${rate.toFixed(0)} events/second`);
        console.log(`   Out-of-order: ${this.results.events.outOfOrder}`);
        console.log(`   Duplicates filtered: ${this.results.events.duplicates}`);
    }
    
    /**
     * Test cache read performance
     */
    async testCachePerformance() {
        console.log('\n💾 Testing cache read performance...');
        
        const cache = window.cache;
        if (!cache) {
            console.warn('⚠️ Cache not available');
            return;
        }
        
        const readCount = Math.min(1000, this.results.sessions.created);
        const readTimes = [];
        
        for (let i = 0; i < readCount; i++) {
            const sessionId = Math.floor(Math.random() * this.results.sessions.created);
            
            const startTime = performance.now();
            try {
                await cache.get(cache.STORES.MEETINGS, sessionId);
                const endTime = performance.now();
                readTimes.push(endTime - startTime);
                this.results.cache.reads++;
            } catch (error) {
                console.warn(`Failed to read session ${sessionId}:`, error);
            }
        }
        
        this.results.cache.avgReadTime = readTimes.reduce((sum, t) => sum + t, 0) / readTimes.length;
        
        console.log(`✅ Completed ${this.results.cache.reads} cache reads`);
        console.log(`   Average read time: ${this.results.cache.avgReadTime.toFixed(2)}ms`);
        console.log(`   Max read time: ${Math.max(...readTimes).toFixed(2)}ms`);
        console.log(`   Min read time: ${Math.min(...readTimes).toFixed(2)}ms`);
    }
    
    /**
     * Test memory leaks
     */
    async testMemoryLeaks() {
        console.log('\n🧠 Testing memory leak detection...');
        
        const measurements = [];
        
        // Take 5 measurements with garbage collection
        for (let i = 0; i < 5; i++) {
            // Force garbage collection if available
            if (window.gc) {
                window.gc();
            }
            
            await new Promise(resolve => setTimeout(resolve, 100));
            measurements.push(this._getMemoryUsage());
        }
        
        // Check for consistent growth (potential leak)
        let growthCount = 0;
        for (let i = 1; i < measurements.length; i++) {
            if (measurements[i] > measurements[i - 1] * 1.1) { // 10% growth
                growthCount++;
            }
        }
        
        this.results.memory.peak = Math.max(...measurements);
        this.results.memory.leakDetected = growthCount >= 3;
        
        const status = this.results.memory.leakDetected ? '⚠️' : '✅';
        console.log(`${status} Memory leak detection: ${this.results.memory.leakDetected ? 'POTENTIAL LEAK DETECTED' : 'NO LEAKS DETECTED'}`);
        console.log(`   Initial: ${this.results.memory.initial.toFixed(2)} MB`);
        console.log(`   Peak: ${this.results.memory.peak.toFixed(2)} MB`);
        console.log(`   Current: ${this.results.memory.final.toFixed(2)} MB`);
    }
    
    /**
     * Test concurrent operations
     */
    async testConcurrency(concurrency) {
        console.log(`\n🔄 Testing concurrent operations (${concurrency} concurrent)...`);
        
        const operations = [];
        const startTime = performance.now();
        
        for (let i = 0; i < concurrency; i++) {
            operations.push(
                this._simulateOperation()
            );
        }
        
        await Promise.all(operations);
        
        const endTime = performance.now();
        const totalTime = endTime - startTime;
        
        console.log(`✅ Completed ${concurrency} concurrent operations in ${totalTime.toFixed(2)}ms`);
        console.log(`   Average per operation: ${(totalTime / concurrency).toFixed(2)}ms`);
    }
    
    /**
     * Generate mock session data
     */
    _generateMockSession(id) {
        return {
            id: id,
            title: `Load Test Session ${id}`,
            status: id % 10 === 0 ? 'archived' : 'active',
            created_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
            duration: Math.floor(Math.random() * 3600),
            summary: `This is a test session generated for load testing purposes. Session ID: ${id}`,
            task_count: Math.floor(Math.random() * 20),
            participant_count: Math.floor(Math.random() * 10) + 1,
            _cached_at: new Date().toISOString()
        };
    }
    
    /**
     * Shuffle array (Fisher-Yates)
     */
    _shuffle(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }
    
    /**
     * Simulate operation
     */
    async _simulateOperation() {
        return new Promise(resolve => {
            setTimeout(() => {
                // Simulate work
                let sum = 0;
                for (let i = 0; i < 1000; i++) {
                    sum += Math.sqrt(i);
                }
                resolve(sum);
            }, Math.random() * 100);
        });
    }
    
    /**
     * Get memory usage (if available)
     */
    _getMemoryUsage() {
        if (performance.memory) {
            return performance.memory.usedJSHeapSize / 1024 / 1024; // MB
        }
        return 0;
    }
    
    /**
     * Generate test report
     */
    _generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            results: this.results,
            summary: {
                totalSessions: this.results.sessions.created,
                totalEvents: this.results.events.processed,
                avgCacheRead: this.results.cache.avgReadTime,
                memoryDelta: this.results.memory.final - this.results.memory.initial,
                leakDetected: this.results.memory.leakDetected,
                passed: !this.results.memory.leakDetected && 
                       this.results.cache.avgReadTime < 10 &&
                       this.results.events.outOfOrder < this.results.events.processed * 0.01
            }
        };
        
        this._printReport(report);
        
        return report;
    }
    
    /**
     * Print test report
     */
    _printReport(report) {
        console.log('');
        console.log('═'.repeat(70));
        console.log('🏋️ CROWN⁴ Load Test Report');
        console.log('═'.repeat(70));
        
        console.log('\n📊 Session Creation:');
        console.log(`   Created: ${report.results.sessions.created.toLocaleString()}`);
        console.log(`   Failed: ${report.results.sessions.failed}`);
        console.log(`   Total time: ${report.results.sessions.totalTime.toFixed(2)}ms`);
        
        console.log('\n⚡ Event Processing:');
        console.log(`   Processed: ${report.results.events.processed.toLocaleString()}`);
        console.log(`   Out-of-order: ${report.results.events.outOfOrder}`);
        console.log(`   Duplicates: ${report.results.events.duplicates}`);
        
        console.log('\n💾 Cache Performance:');
        console.log(`   Reads: ${report.results.cache.reads}`);
        console.log(`   Avg read time: ${report.results.cache.avgReadTime.toFixed(2)}ms`);
        
        console.log('\n🧠 Memory Analysis:');
        console.log(`   Initial: ${report.results.memory.initial.toFixed(2)} MB`);
        console.log(`   Peak: ${report.results.memory.peak.toFixed(2)} MB`);
        console.log(`   Final: ${report.results.memory.final.toFixed(2)} MB`);
        console.log(`   Delta: ${report.summary.memoryDelta.toFixed(2)} MB`);
        console.log(`   Leak detected: ${report.results.memory.leakDetected ? '⚠️ YES' : '✅ NO'}`);
        
        console.log('\n🎯 Overall Assessment:');
        console.log(`   Status: ${report.summary.passed ? '✅ PASSED' : '❌ FAILED'}`);
        
        console.log('═'.repeat(70));
        console.log('');
    }
}

// Export for use in console
window.CROWN4LoadTest = CROWN4LoadTest;

// Usage instructions
console.log('💡 Load Test Usage:');
console.log('   const loadTest = new CROWN4LoadTest();');
console.log('   await loadTest.runFullSuite({ sessionCount: 10000, eventCount: 5000 });');
