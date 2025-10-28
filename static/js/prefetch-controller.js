/**
 * PrefetchController - Intelligent prefetch management with AbortController
 * 
 * Features:
 * - Abort stale prefetch requests when user navigates quickly
 * - Deduplicate concurrent requests for same resource
 * - Queue management with priority
 * - Memory-efficient caching
 * - Automatic cleanup of old prefetches
 * 
 * CROWN⁴ prefetch optimization for sub-300ms navigation
 */

class PrefetchController {
    constructor(options = {}) {
        // Configuration
        this.maxConcurrent = options.maxConcurrent || 3;
        this.maxCacheSize = options.maxCacheSize || 50;
        this.cacheTimeout = options.cacheTimeout || 60000; // 1 minute default
        
        // State tracking
        this.activeRequests = new Map(); // sessionId -> { abortController, promise, timestamp }
        this.prefetchCache = new Map(); // sessionId -> { data, timestamp }
        this.requestQueue = []; // { sessionId, priority, timestamp }
        this.completedSet = new Set(); // sessionIds that were successfully prefetched
        
        // Statistics
        this.stats = {
            totalPrefetches: 0,
            aborted: 0,
            cacheHits: 0,
            cacheMisses: 0,
            errors: 0
        };
        
        // Start cleanup timer
        this.startCleanupTimer();
        
        console.log('🎯 PrefetchController initialized:', {
            maxConcurrent: this.maxConcurrent,
            maxCacheSize: this.maxCacheSize,
            cacheTimeout: this.cacheTimeout
        });
    }
    
    /**
     * Prefetch session data with intelligent caching and abort control
     */
    async prefetch(sessionId, options = {}) {
        const priority = options.priority || 0;
        const force = options.force || false;
        
        // Validation
        if (!sessionId) {
            console.warn('⚠️ PrefetchController: No sessionId provided');
            return null;
        }
        
        // Check cache first (unless force refresh)
        if (!force && this.prefetchCache.has(sessionId)) {
            const cached = this.prefetchCache.get(sessionId);
            const age = Date.now() - cached.timestamp;
            
            if (age < this.cacheTimeout) {
                this.stats.cacheHits++;
                console.log(`💨 Prefetch cache hit: ${sessionId} (age: ${Math.round(age/1000)}s)`);
                return cached.data;
            } else {
                // Cache expired
                this.prefetchCache.delete(sessionId);
                console.log(`⏰ Prefetch cache expired: ${sessionId}`);
            }
        }
        
        this.stats.cacheMisses++;
        
        // Check if already in progress
        if (this.activeRequests.has(sessionId)) {
            console.log(`🔄 Prefetch already in progress: ${sessionId}, reusing...`);
            const existing = this.activeRequests.get(sessionId);
            return existing.promise;
        }
        
        // Check concurrent limit
        if (this.activeRequests.size >= this.maxConcurrent) {
            // Queue the request and return a Promise that resolves when it's processed
            return new Promise((resolve, reject) => {
                this.requestQueue.push({ 
                    sessionId, 
                    priority, 
                    timestamp: Date.now(),
                    resolve,
                    reject
                });
                console.log(`⏸️ Prefetch queued (${this.activeRequests.size}/${this.maxConcurrent} active): ${sessionId}`);
            });
        }
        
        // Execute prefetch
        return this._executePrefetch(sessionId);
    }
    
    /**
     * Execute prefetch with abort controller
     */
    async _executePrefetch(sessionId) {
        const abortController = new AbortController();
        const startTime = Date.now();
        
        // Create promise for this prefetch
        const promise = fetch(`/sessions/${sessionId}?format=json`, {
            signal: abortController.signal,
            headers: { 'X-Prefetch': 'true' }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            const duration = Date.now() - startTime;
            
            // Cache the result
            this.prefetchCache.set(sessionId, {
                data,
                timestamp: Date.now()
            });
            
            // Enforce cache size limit
            if (this.prefetchCache.size > this.maxCacheSize) {
                this._evictOldestCache();
            }
            
            // Mark as completed
            this.completedSet.add(sessionId);
            
            // Clean up active request
            this.activeRequests.delete(sessionId);
            
            // Process queue
            this._processQueue();
            
            this.stats.totalPrefetches++;
            console.log(`✅ Prefetch complete: ${sessionId} (${duration}ms)`);
            
            return data;
        })
        .catch(error => {
            // Clean up active request
            this.activeRequests.delete(sessionId);
            
            // Process queue even on error
            this._processQueue();
            
            if (error.name === 'AbortError') {
                this.stats.aborted++;
                console.log(`🚫 Prefetch aborted: ${sessionId}`);
            } else {
                this.stats.errors++;
                console.error(`❌ Prefetch failed: ${sessionId}`, error);
            }
            
            throw error;
        });
        
        // Track active request
        this.activeRequests.set(sessionId, {
            abortController,
            promise,
            timestamp: Date.now()
        });
        
        console.log(`🚀 Prefetch started: ${sessionId} (${this.activeRequests.size}/${this.maxConcurrent} active)`);
        
        return promise;
    }
    
    /**
     * Abort a specific prefetch request
     */
    abort(sessionId) {
        if (this.activeRequests.has(sessionId)) {
            const request = this.activeRequests.get(sessionId);
            request.abortController.abort();
            this.activeRequests.delete(sessionId);
            console.log(`🛑 Aborted prefetch: ${sessionId}`);
            
            // Process queue after abort
            this._processQueue();
            
            return true;
        }
        return false;
    }
    
    /**
     * Abort all active prefetch requests
     */
    abortAll() {
        let count = 0;
        for (const [sessionId, request] of this.activeRequests.entries()) {
            request.abortController.abort();
            count++;
        }
        this.activeRequests.clear();
        
        if (count > 0) {
            console.log(`🛑 Aborted ${count} active prefetches`);
        }
        
        return count;
    }
    
    /**
     * Process queued prefetch requests
     */
    _processQueue() {
        // Process queue only if we have capacity
        while (this.requestQueue.length > 0 && this.activeRequests.size < this.maxConcurrent) {
            // Sort by priority (higher first) and timestamp (older first)
            this.requestQueue.sort((a, b) => {
                if (a.priority !== b.priority) {
                    return b.priority - a.priority; // Higher priority first
                }
                return a.timestamp - b.timestamp; // Older first
            });
            
            // Take next request from queue
            const next = this.requestQueue.shift();
            console.log(`▶️ Processing queued prefetch: ${next.sessionId}`);
            
            // Execute it and resolve/reject the queued promise
            this._executePrefetch(next.sessionId)
                .then(data => {
                    if (next.resolve) {
                        next.resolve(data);
                    }
                })
                .catch(err => {
                    console.warn('Queued prefetch failed:', err);
                    if (next.reject) {
                        next.reject(err);
                    }
                });
        }
    }
    
    /**
     * Evict oldest cache entry to maintain size limit
     */
    _evictOldestCache() {
        let oldestId = null;
        let oldestTime = Infinity;
        
        for (const [sessionId, cached] of this.prefetchCache.entries()) {
            if (cached.timestamp < oldestTime) {
                oldestTime = cached.timestamp;
                oldestId = sessionId;
            }
        }
        
        if (oldestId) {
            this.prefetchCache.delete(oldestId);
            console.log(`🧹 Evicted oldest cache entry: ${oldestId}`);
        }
    }
    
    /**
     * Get cached data (if available and fresh)
     */
    getCached(sessionId) {
        if (this.prefetchCache.has(sessionId)) {
            const cached = this.prefetchCache.get(sessionId);
            const age = Date.now() - cached.timestamp;
            
            if (age < this.cacheTimeout) {
                return cached.data;
            } else {
                this.prefetchCache.delete(sessionId);
            }
        }
        return null;
    }
    
    /**
     * Check if session was successfully prefetched
     */
    isPrefetched(sessionId) {
        return this.completedSet.has(sessionId) || this.prefetchCache.has(sessionId);
    }
    
    /**
     * Clear all prefetch cache
     */
    clearCache() {
        const size = this.prefetchCache.size;
        this.prefetchCache.clear();
        this.completedSet.clear();
        console.log(`🧹 Cleared ${size} prefetch cache entries`);
    }
    
    /**
     * Start periodic cleanup timer
     */
    startCleanupTimer() {
        setInterval(() => {
            this._cleanupExpiredCache();
            this._cleanupStaleRequests();
        }, 30000); // Every 30 seconds
    }
    
    /**
     * Clean up expired cache entries
     */
    _cleanupExpiredCache() {
        let cleaned = 0;
        const now = Date.now();
        
        for (const [sessionId, cached] of this.prefetchCache.entries()) {
            const age = now - cached.timestamp;
            if (age > this.cacheTimeout) {
                this.prefetchCache.delete(sessionId);
                cleaned++;
            }
        }
        
        if (cleaned > 0) {
            console.log(`🧹 Cleaned up ${cleaned} expired cache entries`);
        }
    }
    
    /**
     * Clean up stale active requests (hanging > 30s)
     */
    _cleanupStaleRequests() {
        let cleaned = 0;
        const now = Date.now();
        const staleThreshold = 30000; // 30 seconds
        
        for (const [sessionId, request] of this.activeRequests.entries()) {
            const age = now - request.timestamp;
            if (age > staleThreshold) {
                request.abortController.abort();
                this.activeRequests.delete(sessionId);
                cleaned++;
            }
        }
        
        if (cleaned > 0) {
            console.log(`🧹 Cleaned up ${cleaned} stale requests`);
        }
    }
    
    /**
     * Get statistics
     */
    getStats() {
        return {
            ...this.stats,
            activeRequests: this.activeRequests.size,
            queuedRequests: this.requestQueue.length,
            cachedSessions: this.prefetchCache.size,
            completedSessions: this.completedSet.size
        };
    }
    
    /**
     * Log statistics
     */
    logStats() {
        const stats = this.getStats();
        console.log('📊 PrefetchController Stats:', stats);
        return stats;
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PrefetchController;
}
