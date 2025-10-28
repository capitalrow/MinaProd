/**
 * CROWN⁴ BroadcastChannel Multi-Tab Synchronization
 * 
 * Enables real-time cache invalidation and synchronization across multiple browser tabs.
 * When a user makes a change in one tab (archive, task update, etc.), all other tabs
 * receive and apply the change immediately via BroadcastChannel API.
 * 
 * Architecture:
 * - Channel: mina_sync_{workspaceId}
 * - Events: CACHE_INVALIDATE, MEETING_UPDATE, TASK_UPDATE, ARCHIVE_UPDATE
 * - Message Format: { type, payload, timestamp, tabId }
 * 
 * CROWN⁴ Phase 4 Task #12: Multi-tab sync with zero-desync architecture
 */

// Prevent redeclaration using window check
(function() {
    if (window.BroadcastSync) {
        console.log('📡 BroadcastSync already loaded, skipping redeclaration');
        return;
    }
    
window.BroadcastSync = class BroadcastSync {
    constructor(workspaceId = 'default') {
        this.workspaceId = workspaceId;
        this.channelName = `mina_sync_${workspaceId}`;
        this.channel = null;
        this.tabId = this._generateTabId();
        this.listeners = new Map();
        this.messageQueue = [];
        this.isInitialized = false;
        
        // Event types
        this.EVENTS = {
            CACHE_INVALIDATE: 'cache_invalidate',
            MEETING_UPDATE: 'meeting_update',
            MEETING_ARCHIVE: 'meeting_archive',
            MEETING_RESTORE: 'meeting_restore',
            TASK_UPDATE: 'task_update',
            STATS_UPDATE: 'stats_update',
            FULL_SYNC: 'full_sync'
        };
    }
    
    /**
     * Initialize BroadcastChannel and set up listeners
     */
    init() {
        if (this.isInitialized) {
            console.warn('[BroadcastSync] Already initialized');
            return;
        }
        
        // Check if BroadcastChannel is supported
        if (typeof BroadcastChannel === 'undefined') {
            console.warn('[BroadcastSync] BroadcastChannel not supported in this browser');
            return;
        }
        
        try {
            // Create channel
            this.channel = new BroadcastChannel(this.channelName);
            
            // Set up message listener
            this.channel.onmessage = (event) => {
                this._handleMessage(event.data);
            };
            
            // Handle errors
            this.channel.onerror = (error) => {
                console.error('[BroadcastSync] Channel error:', error);
            };
            
            this.isInitialized = true;
            console.log(`✅ BroadcastSync initialized: ${this.channelName} (tab=${this.tabId})`);
            
            // Announce tab presence
            this.broadcast(this.EVENTS.FULL_SYNC, {
                action: 'tab_connected',
                tabId: this.tabId,
                timestamp: Date.now()
            });
            
        } catch (error) {
            console.error('[BroadcastSync] Failed to initialize:', error);
        }
    }
    
    /**
     * Broadcast message to all other tabs
     * @param {string} type - Event type
     * @param {Object} payload - Message payload
     */
    broadcast(type, payload) {
        if (!this.channel) {
            console.warn('[BroadcastSync] Channel not initialized, queueing message');
            this.messageQueue.push({ type, payload });
            return;
        }
        
        const message = {
            type,
            payload,
            timestamp: Date.now(),
            tabId: this.tabId,
            workspaceId: this.workspaceId
        };
        
        try {
            this.channel.postMessage(message);
            console.log(`📡 Broadcast sent: ${type}`, payload);
        } catch (error) {
            console.error('[BroadcastSync] Failed to broadcast:', error);
        }
    }
    
    /**
     * Register listener for specific event type
     * @param {string} type - Event type
     * @param {Function} callback - Callback function (payload, message) => void
     */
    on(type, callback) {
        if (!this.listeners.has(type)) {
            this.listeners.set(type, []);
        }
        
        this.listeners.get(type).push(callback);
        console.log(`🎧 Listener registered: ${type} (total=${this.listeners.get(type).length})`);
    }
    
    /**
     * Unregister listener
     * @param {string} type - Event type
     * @param {Function} callback - Callback to remove
     */
    off(type, callback) {
        if (!this.listeners.has(type)) {
            return;
        }
        
        const callbacks = this.listeners.get(type);
        const index = callbacks.indexOf(callback);
        
        if (index > -1) {
            callbacks.splice(index, 1);
            console.log(`🔇 Listener removed: ${type}`);
        }
    }
    
    /**
     * Invalidate cache across all tabs
     * @param {string} cacheKey - Cache key to invalidate (e.g., 'meetings', 'tasks')
     * @param {Object} [options] - Additional options
     */
    invalidateCache(cacheKey, options = {}) {
        this.broadcast(this.EVENTS.CACHE_INVALIDATE, {
            cacheKey,
            ...options
        });
    }
    
    /**
     * Broadcast meeting update (archive, restore, delete)
     * @param {number} meetingId - Meeting ID
     * @param {Object} changes - Changes applied
     */
    broadcastMeetingUpdate(meetingId, changes) {
        this.broadcast(this.EVENTS.MEETING_UPDATE, {
            meetingId,
            changes,
            timestamp: Date.now()
        });
    }
    
    /**
     * Broadcast meeting archive
     * @param {number} meetingId - Meeting ID
     */
    broadcastMeetingArchive(meetingId) {
        this.broadcast(this.EVENTS.MEETING_ARCHIVE, {
            meetingId,
            archived: true,
            timestamp: Date.now()
        });
    }
    
    /**
     * Broadcast meeting restore
     * @param {number} meetingId - Meeting ID
     */
    broadcastMeetingRestore(meetingId) {
        this.broadcast(this.EVENTS.MEETING_RESTORE, {
            meetingId,
            archived: false,
            timestamp: Date.now()
        });
    }
    
    /**
     * Broadcast task update
     * @param {number} taskId - Task ID
     * @param {Object} changes - Changes applied
     */
    broadcastTaskUpdate(taskId, changes) {
        this.broadcast(this.EVENTS.TASK_UPDATE, {
            taskId,
            changes,
            timestamp: Date.now()
        });
    }
    
    /**
     * Broadcast stats update
     */
    broadcastStatsUpdate() {
        this.broadcast(this.EVENTS.STATS_UPDATE, {
            timestamp: Date.now()
        });
    }
    
    /**
     * Handle incoming broadcast message
     * @private
     */
    _handleMessage(message) {
        // Ignore messages from self
        if (message.tabId === this.tabId) {
            return;
        }
        
        // Ignore messages from different workspace
        if (message.workspaceId !== this.workspaceId) {
            return;
        }
        
        console.log(`📨 Broadcast received: ${message.type}`, message.payload);
        
        // Call registered listeners
        const listeners = this.listeners.get(message.type) || [];
        listeners.forEach(callback => {
            try {
                callback(message.payload, message);
            } catch (error) {
                console.error(`[BroadcastSync] Listener error for ${message.type}:`, error);
            }
        });
        
        // Default handlers
        this._applyDefaultHandlers(message);
    }
    
    /**
     * Apply default handlers for common events
     * @private
     */
    async _applyDefaultHandlers(message) {
        const { type, payload } = message;
        
        try {
            switch (type) {
                case this.EVENTS.CACHE_INVALIDATE:
                    await this._handleCacheInvalidate(payload);
                    break;
                    
                case this.EVENTS.MEETING_UPDATE:
                    await this._handleMeetingUpdate(payload);
                    break;
                    
                case this.EVENTS.MEETING_ARCHIVE:
                case this.EVENTS.MEETING_RESTORE:
                    await this._handleMeetingArchiveRestore(payload);
                    break;
                    
                case this.EVENTS.TASK_UPDATE:
                    await this._handleTaskUpdate(payload);
                    break;
                    
                case this.EVENTS.STATS_UPDATE:
                    await this._handleStatsUpdate();
                    break;
                    
                case this.EVENTS.FULL_SYNC:
                    console.log(`👋 Tab connected: ${payload.tabId}`);
                    break;
            }
        } catch (error) {
            console.error(`[BroadcastSync] Handler error for ${type}:`, error);
        }
    }
    
    /**
     * Handle cache invalidation
     * @private
     */
    async _handleCacheInvalidate(payload) {
        const { cacheKey } = payload;
        
        console.log(`🗑️ Cache invalidated: ${cacheKey}`);
        
        // Clear cache in IndexedDB if available
        if (window.cacheManager) {
            try {
                // Trigger refresh based on cache key
                if (cacheKey === 'meetings' && window.dashboard) {
                    await window.dashboard.loadMeetings();
                } else if (cacheKey === 'tasks' && window.dashboard) {
                    await window.dashboard.loadMyTasks();
                } else if (cacheKey === 'stats' && window.dashboard) {
                    await window.dashboard.loadStats();
                }
            } catch (error) {
                console.error('[BroadcastSync] Failed to refresh after cache invalidation:', error);
            }
        }
    }
    
    /**
     * Handle meeting update
     * @private
     */
    async _handleMeetingUpdate(payload) {
        const { meetingId, changes } = payload;
        
        console.log(`📝 Meeting updated: ${meetingId}`, changes);
        
        // Update UI if dashboard is available
        if (window.dashboard) {
            await window.dashboard.loadMeetings();
            await window.dashboard.loadStats();
        }
    }
    
    /**
     * Handle meeting archive/restore
     * @private
     */
    async _handleMeetingArchiveRestore(payload) {
        const { meetingId, archived } = payload;
        
        console.log(`${archived ? '📦' : '📂'} Meeting ${archived ? 'archived' : 'restored'}: ${meetingId}`);
        
        // Find meeting card and update UI
        const meetingCard = document.querySelector(`.meeting-card[data-meeting-id="${meetingId}"]`);
        if (meetingCard) {
            if (archived) {
                // Apply archived styling
                meetingCard.style.opacity = '0.6';
                meetingCard.style.filter = 'grayscale(30%)';
                
                // Add archived badge if not exists
                if (!meetingCard.querySelector('.badge-archived')) {
                    const titleEl = meetingCard.querySelector('.meeting-title');
                    if (titleEl) {
                        const badge = document.createElement('span');
                        badge.className = 'badge badge-secondary badge-archived ms-2';
                        badge.textContent = 'Archived';
                        titleEl.appendChild(badge);
                    }
                }
            } else {
                // Remove archived styling
                meetingCard.style.opacity = '1';
                meetingCard.style.filter = 'none';
                
                // Remove archived badge
                const badge = meetingCard.querySelector('.badge-archived');
                if (badge) {
                    badge.remove();
                }
            }
        }
        
        // Refresh data
        if (window.dashboard) {
            await window.dashboard.loadMeetings();
            await window.dashboard.loadStats();
        }
    }
    
    /**
     * Handle task update
     * @private
     */
    async _handleTaskUpdate(payload) {
        const { taskId, changes } = payload;
        
        console.log(`✅ Task updated: ${taskId}`, changes);
        
        // Update UI if dashboard is available
        if (window.dashboard) {
            await window.dashboard.loadMyTasks();
            await window.dashboard.loadStats();
        }
    }
    
    /**
     * Handle stats update
     * @private
     */
    async _handleStatsUpdate() {
        console.log('📊 Stats update requested');
        
        // Refresh stats
        if (window.dashboard) {
            await window.dashboard.loadStats();
        }
    }
    
    /**
     * Generate unique tab ID
     * @private
     */
    _generateTabId() {
        return `tab_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * Flush queued messages
     */
    flushQueue() {
        if (this.messageQueue.length === 0) {
            return;
        }
        
        console.log(`📤 Flushing ${this.messageQueue.length} queued messages`);
        
        const queue = [...this.messageQueue];
        this.messageQueue = [];
        
        queue.forEach(({ type, payload }) => {
            this.broadcast(type, payload);
        });
    }
    
    /**
     * Close channel and cleanup
     */
    destroy() {
        if (this.channel) {
            this.broadcast(this.EVENTS.FULL_SYNC, {
                action: 'tab_disconnected',
                tabId: this.tabId,
                timestamp: Date.now()
            });
            
            this.channel.close();
            this.channel = null;
        }
        
        this.listeners.clear();
        this.messageQueue = [];
        this.isInitialized = false;
        
        console.log('🔌 BroadcastSync destroyed');
    }
};

// Export singleton instance  
window.broadcastSync = new window.BroadcastSync();

// Auto-initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.broadcastSync.init();
    });
} else {
    window.broadcastSync.init();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.broadcastSync) {
        window.broadcastSync.destroy();
    }
});
})(); // End IIFE
