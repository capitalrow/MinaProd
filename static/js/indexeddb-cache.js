/**
 * IndexedDB Cache Layer - Client-side data persistence
 * 
 * Provides 5 stores with workspace isolation:
 * - meetings: Session/meeting data
 * - analytics: Analytics and insights
 * - tasks: Action items and tasks
 * - sessions: Session metadata
 * - metadata: Cache metadata (checksums, timestamps)
 * 
 * CROWN⁴ cache-first bootstrap pattern with drift detection.
 */

// Prevent redeclaration using window check
(function() {
    if (window.IndexedDBCache) {
        console.log('📦 IndexedDBCache already loaded, skipping redeclaration');
        return;
    }
    
window.IndexedDBCache = class IndexedDBCache {
    constructor(workspaceId) {
        this.workspaceId = workspaceId;
        this.dbName = `mina_cache_${workspaceId}`;
        this.version = 1;
        this.db = null;
        
        // Store names
        this.STORES = {
            MEETINGS: 'meetings',
            ANALYTICS: 'analytics',
            TASKS: 'tasks',
            SESSIONS: 'sessions',
            METADATA: 'metadata'
        };
    }
    
    /**
     * Initialize database and create object stores
     */
    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);
            
            request.onerror = () => {
                console.error('❌ IndexedDB failed to open:', request.error);
                reject(request.error);
            };
            
            request.onsuccess = () => {
                this.db = request.result;
                console.log(`✅ IndexedDB opened: ${this.dbName} (workspace=${this.workspaceId})`);
                resolve(this.db);
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Create meetings store
                if (!db.objectStoreNames.contains(this.STORES.MEETINGS)) {
                    const meetingsStore = db.createObjectStore(this.STORES.MEETINGS, { 
                        keyPath: 'id' 
                    });
                    meetingsStore.createIndex('created_at', 'created_at', { unique: false });
                    meetingsStore.createIndex('status', 'status', { unique: false });
                    meetingsStore.createIndex('archived', 'archived', { unique: false });
                    console.log('📦 Created meetings store');
                }
                
                // Create analytics store
                if (!db.objectStoreNames.contains(this.STORES.ANALYTICS)) {
                    const analyticsStore = db.createObjectStore(this.STORES.ANALYTICS, { 
                        keyPath: 'session_id' 
                    });
                    analyticsStore.createIndex('updated_at', 'updated_at', { unique: false });
                    console.log('📊 Created analytics store');
                }
                
                // Create tasks store
                if (!db.objectStoreNames.contains(this.STORES.TASKS)) {
                    const tasksStore = db.createObjectStore(this.STORES.TASKS, { 
                        keyPath: 'id' 
                    });
                    tasksStore.createIndex('session_id', 'session_id', { unique: false });
                    tasksStore.createIndex('status', 'status', { unique: false });
                    tasksStore.createIndex('priority', 'priority', { unique: false });
                    console.log('✅ Created tasks store');
                }
                
                // Create sessions store (lightweight metadata)
                if (!db.objectStoreNames.contains(this.STORES.SESSIONS)) {
                    const sessionsStore = db.createObjectStore(this.STORES.SESSIONS, { 
                        keyPath: 'external_session_id' 
                    });
                    sessionsStore.createIndex('session_id', 'session_id', { unique: false });
                    sessionsStore.createIndex('last_accessed', 'last_accessed', { unique: false });
                    console.log('🔑 Created sessions store');
                }
                
                // Create metadata store (checksums, cache timestamps)
                if (!db.objectStoreNames.contains(this.STORES.METADATA)) {
                    db.createObjectStore(this.STORES.METADATA, { 
                        keyPath: 'key' 
                    });
                    console.log('🏷️  Created metadata store');
                }
                
                console.log('🎉 IndexedDB schema upgrade complete');
            };
        });
    }
    
    /**
     * Get item from store
     */
    async get(storeName, key) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.get(key);
            
            request.onsuccess = () => {
                const item = request.result;
                if (item) {
                    console.log(`📖 Cache hit: ${storeName}/${key}`);
                }
                resolve(item);
            };
            
            request.onerror = () => {
                console.error(`❌ Failed to get ${storeName}/${key}:`, request.error);
                reject(request.error);
            };
        });
    }
    
    /**
     * Put item in store (create or update)
     */
    async put(storeName, item) {
        if (!this.db) await this.init();
        
        // Add cache timestamp
        item._cached_at = new Date().toISOString();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.put(item);
            
            request.onsuccess = () => {
                console.log(`💾 Cached: ${storeName}/${item.id || item.session_id || item.key}`);
                resolve(request.result);
            };
            
            request.onerror = () => {
                console.error(`❌ Failed to cache ${storeName}:`, request.error);
                reject(request.error);
            };
        });
    }
    
    /**
     * Delete item from store
     */
    async delete(storeName, key) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.delete(key);
            
            request.onsuccess = () => {
                console.log(`🗑️  Deleted: ${storeName}/${key}`);
                resolve();
            };
            
            request.onerror = () => {
                console.error(`❌ Failed to delete ${storeName}/${key}:`, request.error);
                reject(request.error);
            };
        });
    }
    
    /**
     * Get all items from store
     */
    async getAll(storeName) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.getAll();
            
            request.onsuccess = () => {
                console.log(`📦 Retrieved ${request.result.length} items from ${storeName}`);
                resolve(request.result);
            };
            
            request.onerror = () => {
                console.error(`❌ Failed to getAll from ${storeName}:`, request.error);
                reject(request.error);
            };
        });
    }
    
    /**
     * Query items by index
     */
    async queryByIndex(storeName, indexName, value) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const index = store.index(indexName);
            const request = index.getAll(value);
            
            request.onsuccess = () => {
                console.log(`🔍 Query ${storeName}.${indexName}=${value}: ${request.result.length} results`);
                resolve(request.result);
            };
            
            request.onerror = () => {
                console.error(`❌ Query failed ${storeName}.${indexName}:`, request.error);
                reject(request.error);
            };
        });
    }
    
    /**
     * Clear all items from store
     */
    async clear(storeName) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.clear();
            
            request.onsuccess = () => {
                console.log(`🧹 Cleared store: ${storeName}`);
                resolve();
            };
            
            request.onerror = () => {
                console.error(`❌ Failed to clear ${storeName}:`, request.error);
                reject(request.error);
            };
        });
    }
    
    /**
     * Clear all stores (full cache purge)
     */
    async clearAll() {
        const stores = Object.values(this.STORES);
        const promises = stores.map(store => this.clear(store));
        await Promise.all(promises);
        console.log('🧹 All caches cleared');
    }
    
    /**
     * Batch put items
     */
    async putBatch(storeName, items) {
        if (!this.db) await this.init();
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            
            let successCount = 0;
            const errors = [];
            
            items.forEach((item, index) => {
                item._cached_at = new Date().toISOString();
                const request = store.put(item);
                
                request.onsuccess = () => {
                    successCount++;
                };
                
                request.onerror = () => {
                    errors.push({ index, error: request.error });
                };
            });
            
            transaction.oncomplete = () => {
                console.log(`💾 Batch cached: ${successCount}/${items.length} items in ${storeName}`);
                resolve({ successCount, errors });
            };
            
            transaction.onerror = () => {
                console.error(`❌ Batch cache failed for ${storeName}:`, transaction.error);
                reject(transaction.error);
            };
        });
    }
    
    /**
     * Get or set metadata
     */
    async getMetadata(key) {
        return await this.get(this.STORES.METADATA, key);
    }
    
    async setMetadata(key, value) {
        return await this.put(this.STORES.METADATA, { 
            key, 
            value, 
            updated_at: new Date().toISOString() 
        });
    }
    
    /**
     * Cache meetings with checksum
     */
    async cacheMeetings(meetings, checksum) {
        await this.putBatch(this.STORES.MEETINGS, meetings);
        await this.setMetadata('meetings_checksum', checksum);
        await this.setMetadata('meetings_cached_at', new Date().toISOString());
    }
    
    /**
     * Get cached meetings with validation
     */
    async getCachedMeetings() {
        const meetings = await this.getAll(this.STORES.MEETINGS);
        const checksumData = await this.getMetadata('meetings_checksum');
        const cachedAtData = await this.getMetadata('meetings_cached_at');
        
        return {
            data: meetings,
            checksum: checksumData?.value,
            cached_at: cachedAtData?.value,
            count: meetings.length
        };
    }
    
    /**
     * Cache analytics data
     */
    async cacheAnalytics(sessionId, analytics) {
        analytics.session_id = sessionId;
        await this.put(this.STORES.ANALYTICS, analytics);
    }
    
    /**
     * Get analytics for session
     */
    async getAnalytics(sessionId) {
        return await this.get(this.STORES.ANALYTICS, sessionId);
    }
    
    /**
     * Cache tasks
     */
    async cacheTasks(tasks) {
        await this.putBatch(this.STORES.TASKS, tasks);
    }
    
    /**
     * Get tasks for session
     */
    async getTasksForSession(sessionId) {
        return await this.queryByIndex(this.STORES.TASKS, 'session_id', sessionId);
    }
    
    /**
     * Update task status optimistically
     */
    async updateTaskStatus(taskId, status) {
        const task = await this.get(this.STORES.TASKS, taskId);
        if (task) {
            task.status = status;
            task._optimistic_update = true;
            task._updated_at = new Date().toISOString();
            await this.put(this.STORES.TASKS, task);
        }
    }
    
    /**
     * Check if cache is stale
     */
    async isCacheStale(maxAgeSeconds = 300) {
        const cachedAtData = await this.getMetadata('meetings_cached_at');
        if (!cachedAtData?.value) return true;
        
        const cachedAt = new Date(cachedAtData.value);
        const ageSeconds = (new Date() - cachedAt) / 1000;
        
        return ageSeconds > maxAgeSeconds;
    }
    
    /**
     * Get cache statistics
     */
    async getStats() {
        const [meetings, analytics, tasks, sessions, metadata] = await Promise.all([
            this.getAll(this.STORES.MEETINGS),
            this.getAll(this.STORES.ANALYTICS),
            this.getAll(this.STORES.TASKS),
            this.getAll(this.STORES.SESSIONS),
            this.getAll(this.STORES.METADATA)
        ]);
        
        return {
            meetings: meetings.length,
            analytics: analytics.length,
            tasks: tasks.length,
            sessions: sessions.length,
            metadata: metadata.length,
            total: meetings.length + analytics.length + tasks.length + sessions.length + metadata.length
        };
    }
    
    /**
     * Close database connection
     */
    close() {
        if (this.db) {
            this.db.close();
            this.db = null;
            console.log('🔌 IndexedDB connection closed');
        }
    }
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.IndexedDBCache;
}
})(); // End IIFE
