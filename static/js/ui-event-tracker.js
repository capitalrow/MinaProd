/**
 * UI Event Tracker - Industry-Standard Event Logging
 * 
 * Implements production-ready event tracking with:
 * - 1-second search debouncing (Mixpanel/Amplitude standard)
 * - Immediate filter tracking
 * - Event batching to prevent spam
 * - Integration with EventLedger backend
 * 
 * Based on best practices from Mixpanel, Amplitude, Segment, PostHog
 */

class UIEventTracker {
    constructor() {
        this.eventQueue = [];
        this.batchWindow = 300; // 300ms batching window
        this.batchTimer = null;
        this.searchDebounceTimer = null;
        this.searchDebounceDelay = 1000; // 1 second (industry standard)
        
        // Track last sent events to prevent duplicates
        this.lastSentEvents = new Map();
        this.dedupeWindow = 5000; // 5 seconds
    }
    
    /**
     * Initialize event tracking on dashboard
     */
    init() {
        this.trackSearchInput();
        this.trackFilterChanges();
        this.trackTabSwitches();
        this.trackArchiveButtons();
        
        console.log('✅ UI Event Tracker initialized');
    }
    
    /**
     * Track search input with 1-second debouncing
     * Prevents spam while user is typing
     */
    trackSearchInput() {
        const searchInput = document.getElementById('search-input');
        if (!searchInput) return;
        
        searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchDebounceTimer);
            
            const query = e.target.value.trim();
            
            // Only track if query length > 0
            if (query.length === 0) return;
            
            this.searchDebounceTimer = setTimeout(() => {
                this.logEvent('FILTER_APPLY', {
                    filter_type: 'search',
                    query: query,
                    query_length: query.length,
                    page: window.location.pathname
                });
                
                console.log(`🔍 Search tracked: "${query}"`);
            }, this.searchDebounceDelay);
        });
    }
    
    /**
     * Track filter changes (immediate, no debounce)
     */
    trackFilterChanges() {
        const timeFilter = document.getElementById('time-filter');
        if (!timeFilter) return;
        
        timeFilter.addEventListener('change', (e) => {
            const filterValue = e.target.value;
            
            // Get visible meeting count for context
            const visibleCards = document.querySelectorAll('#active-meetings .meeting-card:not([style*="display: none"])');
            
            this.logEvent('FILTER_APPLY', {
                filter_type: 'time',
                filter_value: filterValue,
                results_count: visibleCards.length,
                page: window.location.pathname
            });
            
            console.log(`📅 Time filter tracked: ${filterValue} (${visibleCards.length} results)`);
        });
    }
    
    /**
     * Track tab switches (Active ↔ Archived)
     */
    trackTabSwitches() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        if (!tabButtons.length) return;
        
        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                
                // Only track archive reveal
                if (tab === 'archive') {
                    this.logEvent('ARCHIVE_REVEAL', {
                        page: window.location.pathname,
                        timestamp: new Date().toISOString()
                    });
                    
                    console.log('📦 Archive tab revealed');
                }
            });
        });
    }
    
    /**
     * Track archive button clicks
     * Note: archiveMeeting() function should call this before archiving
     */
    trackArchiveButtons() {
        // Archive tracking is handled inline in archiveMeeting() function
        // This is a placeholder for future enhancements
    }
    
    /**
     * Log event to EventLedger backend with batching
     * @param {string} eventType - Event type enum (FILTER_APPLY, ARCHIVE_REVEAL, etc.)
     * @param {object} payload - Event payload data
     */
    logEvent(eventType, payload) {
        // Deduplication check
        const eventKey = `${eventType}:${JSON.stringify(payload)}`;
        const now = Date.now();
        const lastSent = this.lastSentEvents.get(eventKey);
        
        if (lastSent && (now - lastSent) < this.dedupeWindow) {
            console.log(`⏭️  Skipping duplicate event: ${eventType}`);
            return;
        }
        
        // Add to batch queue
        this.eventQueue.push({
            type: eventType,
            payload: payload,
            timestamp: now
        });
        
        // Update last sent time
        this.lastSentEvents.set(eventKey, now);
        
        // Schedule batch flush if not already scheduled
        if (!this.batchTimer) {
            this.batchTimer = setTimeout(() => {
                this.flushEventBatch();
            }, this.batchWindow);
        }
    }
    
    /**
     * Flush event batch to server
     * Sends all queued events in one API call
     */
    async flushEventBatch() {
        if (this.eventQueue.length === 0) {
            this.batchTimer = null;
            return;
        }
        
        const events = [...this.eventQueue];
        this.eventQueue = [];
        this.batchTimer = null;
        
        console.log(`📤 Flushing ${events.length} event(s) to EventLedger`);
        
        // Send each event to backend
        // Note: Backend endpoints expect individual calls, not batch
        for (const event of events) {
            try {
                await this.sendEventToBackend(event);
            } catch (error) {
                console.error(`Failed to send ${event.type} event:`, error);
            }
        }
    }
    
    /**
     * Send individual event to backend API
     * @param {object} event - Event object with type and payload
     */
    async sendEventToBackend(event) {
        let endpoint = null;
        
        // Map event type to backend endpoint
        switch (event.type) {
            case 'FILTER_APPLY':
                endpoint = '/dashboard/api/events/filter-apply';
                break;
            case 'ARCHIVE_REVEAL':
                endpoint = '/dashboard/api/events/archive-reveal';
                break;
            case 'SESSION_CARD_CLICK':
                endpoint = '/dashboard/api/events/card-click';
                break;
            case 'SESSION_PREFETCH':
                endpoint = '/dashboard/api/events/prefetch';
                break;
            default:
                console.warn(`Unknown event type: ${event.type}`);
                return;
        }
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(event.payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log(`✅ Event logged: ${event.type} (ID: ${result.event_id})`);
        
        return result;
    }
    
    /**
     * Cleanup on page unload
     */
    destroy() {
        // Flush any remaining events
        clearTimeout(this.batchTimer);
        clearTimeout(this.searchDebounceTimer);
        
        if (this.eventQueue.length > 0) {
            this.flushEventBatch();
        }
        
        console.log('🔌 UI Event Tracker destroyed');
    }
}

// Initialize tracker when DOM is ready
let uiTracker = null;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        uiTracker = new UIEventTracker();
        uiTracker.init();
    });
} else {
    uiTracker = new UIEventTracker();
    uiTracker.init();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (uiTracker) {
        uiTracker.destroy();
    }
});

// Export for global access
window.uiTracker = uiTracker;
