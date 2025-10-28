/**
 * Dashboard Error Handler - Comprehensive error handling for CROWN⁴
 * 
 * Features:
 * - Missing session recovery (404 handling)
 * - Stale cache purge with auto-retry
 * - Navigation abort cleanup
 * - Graceful degradation patterns
 * - User-friendly error messaging
 */

class DashboardErrorHandler {
    constructor(options = {}) {
        this.cache = options.cache; // IndexedDBCache instance
        this.prefetchController = options.prefetchController;
        this.websocketManager = options.websocketManager;
        
        // Error tracking
        this.errorLog = [];
        this.maxLogSize = 100;
        
        // Recovery strategies
        this.recoveryAttempts = new Map(); // sessionId -> attempt count
        this.maxRetries = 3;
        
        // Stale cache detection
        this.staleCacheThreshold = 24 * 60 * 60 * 1000; // 24 hours
        this.lastPurgeTime = Date.now();
        this.purgeInterval = 60 * 60 * 1000; // Purge every hour
        
        // Navigation abort tracking
        this.activeNavigations = new Map(); // route -> abortController
        
        console.log('🛡️ DashboardErrorHandler initialized');
        
        // Start periodic cache purge
        this.startPeriodicPurge();
    }
    
    /**
     * Handle missing session (404 error)
     * Attempts recovery from cache, server, or shows user-friendly error
     */
    async handleMissingSession(sessionId, error) {
        console.warn(`⚠️ Missing session detected: ${sessionId}`, error);
        
        // Track recovery attempts
        const attempts = (this.recoveryAttempts.get(sessionId) || 0) + 1;
        this.recoveryAttempts.set(sessionId, attempts);
        
        // Log error
        this._logError({
            type: 'missing_session',
            sessionId,
            attempts,
            timestamp: new Date().toISOString(),
            error: error.message
        });
        
        if (attempts > this.maxRetries) {
            console.error(`❌ Max recovery attempts exceeded for session ${sessionId}`);
            return this._showSessionNotFoundError(sessionId);
        }
        
        // Recovery strategy 1: Check cache
        if (this.cache) {
            try {
                const cached = await this.cache.get(this.cache.STORES.MEETINGS, parseInt(sessionId));
                if (cached && !this._isCacheStale(cached)) {
                    console.log(`✅ Recovered session ${sessionId} from cache`);
                    this.recoveryAttempts.delete(sessionId);
                    return { success: true, data: cached, source: 'cache' };
                }
            } catch (cacheError) {
                console.warn(`⚠️ Cache lookup failed for ${sessionId}:`, cacheError);
            }
        }
        
        // Recovery strategy 2: Retry with backoff
        if (attempts <= 2) {
            const backoffMs = Math.min(1000 * Math.pow(2, attempts - 1), 5000);
            console.log(`🔄 Retrying session ${sessionId} in ${backoffMs}ms (attempt ${attempts})`);
            
            await new Promise(resolve => setTimeout(resolve, backoffMs));
            
            try {
                const response = await fetch(`/api/meetings/${sessionId}`);
                if (response.ok) {
                    const data = await response.json();
                    console.log(`✅ Recovered session ${sessionId} from server`);
                    this.recoveryAttempts.delete(sessionId);
                    
                    // Update cache
                    if (this.cache) {
                        await this.cache.put(this.cache.STORES.MEETINGS, data);
                    }
                    
                    return { success: true, data, source: 'server' };
                }
            } catch (retryError) {
                console.warn(`⚠️ Retry failed for ${sessionId}:`, retryError);
            }
        }
        
        // Recovery strategy 3: Remove from cache and show error
        if (this.cache) {
            await this.cache.delete(this.cache.STORES.MEETINGS, parseInt(sessionId));
            console.log(`🗑️ Removed stale session ${sessionId} from cache`);
        }
        
        return this._showSessionNotFoundError(sessionId);
    }
    
    /**
     * Purge stale cache entries
     * Removes entries older than threshold and invalid data
     */
    async purgeStaleCache(options = {}) {
        const force = options.force || false;
        const now = Date.now();
        
        // Skip if purged recently (unless forced)
        if (!force && (now - this.lastPurgeTime) < this.purgeInterval) {
            return { skipped: true, reason: 'too_soon' };
        }
        
        console.log('🧹 Starting stale cache purge...');
        
        if (!this.cache || !this.cache.db) {
            console.warn('⚠️ Cache not available for purge');
            return { success: false, reason: 'no_cache' };
        }
        
        const results = {
            meetings: 0,
            analytics: 0,
            tasks: 0,
            sessions: 0,
            errors: []
        };
        
        try {
            // Purge meetings store
            results.meetings = await this._purgeStore(
                this.cache.STORES.MEETINGS,
                (item) => this._isCacheStale(item)
            );
            
            // Purge analytics store
            results.analytics = await this._purgeStore(
                this.cache.STORES.ANALYTICS,
                (item) => this._isCacheStale(item)
            );
            
            // Purge tasks store
            results.tasks = await this._purgeStore(
                this.cache.STORES.TASKS,
                (item) => this._isCacheStale(item)
            );
            
            // Purge sessions store (remove old sessions not accessed recently)
            results.sessions = await this._purgeStore(
                this.cache.STORES.SESSIONS,
                (item) => {
                    const lastAccessed = new Date(item.last_accessed || 0).getTime();
                    return (now - lastAccessed) > this.staleCacheThreshold;
                }
            );
            
            this.lastPurgeTime = now;
            
            const total = results.meetings + results.analytics + results.tasks + results.sessions;
            console.log(`✅ Purged ${total} stale cache entries:`, results);
            
            return { success: true, results, timestamp: new Date().toISOString() };
            
        } catch (error) {
            console.error('❌ Cache purge failed:', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Handle navigation abort - cleanup pending operations
     */
    abortNavigation(route) {
        console.log(`🛑 Aborting navigation to: ${route}`);
        
        // Abort active navigation request
        if (this.activeNavigations.has(route)) {
            const controller = this.activeNavigations.get(route);
            controller.abort();
            this.activeNavigations.delete(route);
            console.log(`✅ Navigation aborted: ${route}`);
        }
        
        // Cancel related prefetch requests if controller is available
        if (this.prefetchController) {
            const sessionId = this._extractSessionIdFromRoute(route);
            if (sessionId) {
                this.prefetchController.abort(sessionId);
            }
        }
        
        return { aborted: true, route };
    }
    
    /**
     * Track navigation with abort controller
     */
    trackNavigation(route, abortController) {
        // Abort any existing navigation to same route
        this.abortNavigation(route);
        
        // Track new navigation
        this.activeNavigations.set(route, abortController);
        
        console.log(`📍 Tracking navigation: ${route}`);
    }
    
    /**
     * Complete navigation (cleanup)
     */
    completeNavigation(route) {
        if (this.activeNavigations.has(route)) {
            this.activeNavigations.delete(route);
            console.log(`✅ Navigation completed: ${route}`);
        }
    }
    
    /**
     * Start periodic cache purge
     */
    startPeriodicPurge() {
        setInterval(() => {
            this.purgeStaleCache({ force: false });
        }, this.purgeInterval);
        
        console.log(`⏰ Periodic cache purge scheduled (every ${this.purgeInterval / 60000} minutes)`);
    }
    
    /**
     * Check if cache entry is stale
     */
    _isCacheStale(item) {
        if (!item || !item._cached_at) {
            return true; // No timestamp = stale
        }
        
        const cachedAt = new Date(item._cached_at).getTime();
        const age = Date.now() - cachedAt;
        
        return age > this.staleCacheThreshold;
    }
    
    /**
     * Purge items from store based on predicate
     */
    async _purgeStore(storeName, shouldPurge) {
        return new Promise((resolve, reject) => {
            const transaction = this.cache.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.openCursor();
            
            let purgedCount = 0;
            const deletePromises = [];
            
            request.onsuccess = (event) => {
                const cursor = event.target.result;
                
                if (cursor) {
                    const item = cursor.value;
                    
                    if (shouldPurge(item)) {
                        deletePromises.push(
                            new Promise((res, rej) => {
                                const delReq = cursor.delete();
                                delReq.onsuccess = () => {
                                    purgedCount++;
                                    res();
                                };
                                delReq.onerror = () => rej(delReq.error);
                            })
                        );
                    }
                    
                    cursor.continue();
                } else {
                    // No more entries
                    Promise.all(deletePromises)
                        .then(() => resolve(purgedCount))
                        .catch(reject);
                }
            };
            
            request.onerror = () => reject(request.error);
        });
    }
    
    /**
     * Show user-friendly session not found error
     */
    _showSessionNotFoundError(sessionId) {
        console.error(`❌ Session not found: ${sessionId}`);
        
        // Show toast notification
        if (window.toast) {
            window.toast.error(
                `Meeting not found. It may have been deleted or you don't have access.`,
                5000,
                {
                    actionCallback: () => {
                        window.location.href = '/dashboard';
                    },
                    actionText: 'Back to Dashboard'
                }
            );
        }
        
        // Navigate back to dashboard after delay
        setTimeout(() => {
            if (window.location.pathname.includes(`/sessions/${sessionId}`)) {
                window.location.href = '/dashboard';
            }
        }, 3000);
        
        return { 
            success: false, 
            error: 'session_not_found',
            sessionId,
            redirected: true
        };
    }
    
    /**
     * Extract session ID from route
     */
    _extractSessionIdFromRoute(route) {
        const match = route.match(/\/sessions\/(\d+)/);
        return match ? match[1] : null;
    }
    
    /**
     * Log error for debugging
     */
    _logError(error) {
        this.errorLog.push(error);
        
        // Maintain max log size
        if (this.errorLog.length > this.maxLogSize) {
            this.errorLog.shift();
        }
    }
    
    /**
     * Get error statistics
     */
    getStats() {
        const byType = {};
        
        for (const error of this.errorLog) {
            byType[error.type] = (byType[error.type] || 0) + 1;
        }
        
        return {
            total: this.errorLog.length,
            byType,
            recentErrors: this.errorLog.slice(-10),
            activeNavigations: this.activeNavigations.size,
            activeRecoveries: this.recoveryAttempts.size
        };
    }
    
    /**
     * Clear error log
     */
    clearLog() {
        this.errorLog = [];
        console.log('🧹 Error log cleared');
    }
}

// Export for use in dashboard
window.DashboardErrorHandler = DashboardErrorHandler;
