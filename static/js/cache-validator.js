/**
 * CROWN⁴ Cache Validator
 * SHA-256 checksum-based validation for cache vs server data synchronization
 * 
 * Detects data drift and triggers reconciliation when needed
 */

class CacheValidator {
    constructor() {
        this.checksums = new Map();
    }

    /**
     * Generate SHA-256 checksum for data
     * @param {any} data - Data to hash
     * @returns {Promise<string>} - SHA-256 hex string
     */
    async generateChecksum(data) {
        // Normalize data to string
        const normalized = typeof data === 'string' 
            ? data 
            : JSON.stringify(this._sortObject(data));
        
        // Convert string to Uint8Array
        const encoder = new TextEncoder();
        const dataBuffer = encoder.encode(normalized);
        
        // Generate SHA-256 hash (modern browsers support SHA-256 via Web Crypto API)
        const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
        
        // Convert hash to hex string
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        
        return hashHex; // Return full 64-char SHA-256 hash
    }

    /**
     * Validate cache against server data
     * @param {Object} options - Validation options
     * @param {any} options.cachedData - Data from cache
     * @param {any} options.serverData - Data from server
     * @param {string} options.key - Cache key for tracking
     * @param {boolean} [options.persistChecksum=true] - Whether to persist checksum to metadata
     * @returns {Promise<Object>} - Validation result
     */
    async validate({ cachedData, serverData, key, persistChecksum = true }) {
        const startTime = performance.now();

        try {
            // Generate checksums
            const [cachedChecksum, serverChecksum] = await Promise.all([
                this.generateChecksum(cachedData),
                this.generateChecksum(serverData)
            ]);

            // Store checksums in memory
            this.checksums.set(key, {
                cached: cachedChecksum,
                server: serverChecksum,
                timestamp: Date.now()
            });
            
            // Persist server checksum to IndexedDB metadata for future validations
            if (persistChecksum && window.cacheManager && window.cacheManager.db) {
                try {
                    const tx = window.cacheManager.db.transaction('metadata', 'readwrite');
                    const store = tx.objectStore('metadata');
                    
                    store.put({
                        key: `checksum_${key}`,
                        checksum: serverChecksum,
                        algorithm: 'SHA-256',
                        updated_at: Date.now()
                    });
                    
                    await new Promise((resolve, reject) => {
                        tx.oncomplete = () => resolve();
                        tx.onerror = () => reject(tx.error);
                    });
                } catch (error) {
                    console.warn('Failed to persist checksum to metadata:', error);
                }
            }

            const isValid = cachedChecksum === serverChecksum;
            const validationTime = performance.now() - startTime;

            const result = {
                isValid,
                cachedChecksum,
                serverChecksum,
                validationTime: Math.round(validationTime),
                drift: !isValid,
                key
            };

            if (!isValid) {
                console.warn(`⚠️ Cache drift detected for ${key}`);
                console.log('   Cached checksum:', cachedChecksum);
                console.log('   Server checksum:', serverChecksum);
            } else {
                console.log(`✅ Cache valid for ${key} (${result.validationTime}ms)`);
            }

            return result;
        } catch (error) {
            console.error(`❌ Validation failed for ${key}:`, error);
            return {
                isValid: false,
                error: error.message,
                validationTime: performance.now() - startTime,
                drift: true,
                key
            };
        }
    }

    /**
     * Validate multiple cache entries in parallel
     * @param {Array<Object>} validations - Array of validation configs
     * @returns {Promise<Object>} - Validation results by key
     */
    async validateMultiple(validations) {
        const startTime = performance.now();
        
        const results = await Promise.all(
            validations.map(config => this.validate(config))
        );

        const totalTime = Math.round(performance.now() - startTime);
        const driftCount = results.filter(r => r.drift).length;

        console.log(`📊 Bulk validation complete: ${results.length} items, ${driftCount} drifts, ${totalTime}ms`);

        // Convert array to object keyed by cache key
        return results.reduce((acc, result) => {
            acc[result.key] = result;
            return acc;
        }, {
            _summary: {
                total: results.length,
                valid: results.length - driftCount,
                drift: driftCount,
                totalTime
            }
        });
    }

    /**
     * Get stored checksum for a key
     * @param {string} key - Cache key
     * @returns {Object|null} - Stored checksum data
     */
    getStoredChecksum(key) {
        return this.checksums.get(key) || null;
    }

    /**
     * Clear stored checksums
     * @param {string} [key] - Specific key to clear, or all if not provided
     */
    clearChecksums(key) {
        if (key) {
            this.checksums.delete(key);
        } else {
            this.checksums.clear();
        }
    }

    /**
     * Calculate delta between cached and server data
     * @param {Array} cachedData - Cached records
     * @param {Array} serverData - Server records
     * @param {string} idField - Field to use as unique identifier
     * @param {Array} [compareFields] - Optional list of fields to compare (faster than full JSON compare)
     * @returns {Object} - Delta with added, modified, removed records
     */
    calculateDelta(cachedData, serverData, idField = 'id', compareFields = null) {
        const cached = new Map(cachedData.map(item => [item[idField], item]));
        const server = new Map(serverData.map(item => [item[idField], item]));

        const delta = {
            added: [],
            modified: [],
            removed: [],
            unchanged: []
        };

        // Find added and modified
        for (const [id, serverItem] of server) {
            const cachedItem = cached.get(id);
            
            if (!cachedItem) {
                delta.added.push(serverItem);
            } else {
                // Check if modified
                let isModified = false;
                
                if (compareFields && Array.isArray(compareFields)) {
                    // Fast field-level comparison (more efficient)
                    for (const field of compareFields) {
                        if (cachedItem[field] !== serverItem[field]) {
                            isModified = true;
                            break;
                        }
                    }
                } else {
                    // Fallback to full comparison (normalize objects first)
                    const cachedNormalized = JSON.stringify(this._sortObject(cachedItem));
                    const serverNormalized = JSON.stringify(this._sortObject(serverItem));
                    isModified = cachedNormalized !== serverNormalized;
                }
                
                if (isModified) {
                    delta.modified.push({
                        id,
                        cached: cachedItem,
                        server: serverItem
                    });
                } else {
                    delta.unchanged.push(serverItem);
                }
            }
        }

        // Find removed
        for (const [id, cachedItem] of cached) {
            if (!server.has(id)) {
                delta.removed.push(cachedItem);
            }
        }

        return delta;
    }

    /**
     * Merge delta into cached data
     * @param {Array} cachedData - Current cached data
     * @param {Object} delta - Delta from calculateDelta
     * @param {string} idField - Field to use as unique identifier
     * @returns {Array} - Merged data
     */
    mergeDelta(cachedData, delta, idField = 'id') {
        const merged = new Map(cachedData.map(item => [item[idField], item]));

        // Remove deleted items
        for (const item of delta.removed) {
            merged.delete(item[idField]);
        }

        // Add new items
        for (const item of delta.added) {
            merged.set(item[idField], item);
        }

        // Update modified items
        for (const { id, server } of delta.modified) {
            merged.set(id, server);
        }

        return Array.from(merged.values());
    }

    /**
     * Generate summary of delta
     * @param {Object} delta - Delta object
     * @returns {string} - Human-readable summary
     */
    getDeltaSummary(delta) {
        const { added, modified, removed, unchanged } = delta;
        const parts = [];

        if (added.length > 0) parts.push(`+${added.length} added`);
        if (modified.length > 0) parts.push(`~${modified.length} modified`);
        if (removed.length > 0) parts.push(`-${removed.length} removed`);
        if (unchanged.length > 0) parts.push(`${unchanged.length} unchanged`);

        return parts.length > 0 ? parts.join(', ') : 'No changes';
    }

    /**
     * Helper: Sort object keys recursively for consistent hashing
     * @private
     */
    _sortObject(obj) {
        if (obj === null || typeof obj !== 'object') {
            return obj;
        }

        if (Array.isArray(obj)) {
            return obj.map(item => this._sortObject(item));
        }

        return Object.keys(obj)
            .sort()
            .reduce((result, key) => {
                result[key] = this._sortObject(obj[key]);
                return result;
            }, {});
    }
}

// Export singleton instance
window.cacheValidator = new CacheValidator();
