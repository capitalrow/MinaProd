/**
 * WebSocket Manager - CROWN⁴ Real-time Synchronization
 * 
 * Manages Socket.IO connections to multiple namespaces:
 * - /dashboard: Dashboard real-time updates
 * - /tasks: Task synchronization  
 * - /analytics: Analytics refresh
 * - /meetings: Meeting updates
 * 
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Workspace room management
 * - Event sequencing validation
 * - Cross-tab synchronization via BroadcastChannel
 */

class WebSocketManager {
    constructor() {
        this.sockets = {};
        this.workspaceId = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.eventHandlers = {};
        this.lastEventId = null;
        
        // BroadcastChannel for cross-tab sync
        if ('BroadcastChannel' in window) {
            this.broadcastChannel = new BroadcastChannel('mina_sync');
            this.setupBroadcastChannel();
        }
        
        // Store for event sequencing
        this.eventSequence = [];
        this.lastAppliedSequence = 0;
    }
    
    /**
     * Initialize WebSocket connections
     * @param {number} workspaceId - Current workspace ID
     * @param {Array<string>} namespaces - Namespaces to connect (default: ['dashboard'])
     */
    init(workspaceId, namespaces = ['dashboard']) {
        this.workspaceId = workspaceId;
        
        namespaces.forEach(namespace => {
            this.connect(namespace);
        });
        
        // Set up heartbeat
        this.startHeartbeat();
        
        console.log(`🔌 WebSocket Manager initialized for workspace ${workspaceId}`);
    }
    
    /**
     * Connect to a specific namespace
     * @param {string} namespace - Namespace name (e.g., 'dashboard', 'tasks')
     */
    connect(namespace) {
        if (this.sockets[namespace]) {
            console.warn(`Already connected to /${namespace}`);
            return;
        }
        
        // Create Socket.IO connection
        const socket = io(`/${namespace}`, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: this.reconnectDelay,
            reconnectionAttempts: this.maxReconnectAttempts
        });
        
        // Connection event handlers
        socket.on('connect', () => {
            console.log(`✅ Connected to /${namespace} namespace`);
            this.isConnected = true;
            this.reconnectAttempts = 0;
            
            // Join workspace room
            if (this.workspaceId) {
                socket.emit('join_workspace', { workspace_id: this.workspaceId });
            }
            
            // Emit connection status
            this.emit('connection_status', { namespace, connected: true });
        });
        
        socket.on('disconnect', (reason) => {
            console.warn(`⚠️ Disconnected from /${namespace}: ${reason}`);
            this.isConnected = false;
            this.emit('connection_status', { namespace, connected: false, reason });
        });
        
        socket.on('connect_error', (error) => {
            console.error(`❌ Connection error on /${namespace}:`, error);
            this.reconnectAttempts++;
            
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                this.emit('connection_failed', { namespace, error });
            }
        });
        
        socket.on('error', (error) => {
            console.error(`❌ Socket error on /${namespace}:`, error);
            this.emit('socket_error', { namespace, error });
        });
        
        // Acknowledgment events
        socket.on('connected', (data) => {
            console.log(`📡 ${namespace} connection acknowledged:`, data);
        });
        
        socket.on('joined_workspace', (data) => {
            console.log(`🏢 Joined workspace room: workspace_${data.workspace_id}`);
        });
        
        // Register CROWN⁴ event listeners
        this.registerCROWNEvents(socket, namespace);
        
        this.sockets[namespace] = socket;
    }
    
    /**
     * Register CROWN⁴ event listeners
     * @param {Socket} socket - Socket.IO socket instance
     * @param {string} namespace - Namespace name
     */
    registerCROWNEvents(socket, namespace) {
        // Event 2: session_update:created
        socket.on('session_update:created', (data) => {
            console.log('📬 New session created:', data);
            this.handleSequencedEvent('session_update:created', data, namespace);
        });
        
        // Event 6: task_update
        socket.on('task_update', (data) => {
            console.log('✅ Task updated:', data);
            this.handleSequencedEvent('task_update', data, namespace);
        });
        
        // Event 7: analytics_refresh
        socket.on('analytics_refresh', (data) => {
            console.log('📊 Analytics refreshed:', data);
            this.handleSequencedEvent('analytics_refresh', data, namespace);
        });
        
        // Event 8: dashboard_refresh
        socket.on('dashboard_refresh', (data) => {
            console.log('🔄 Dashboard refreshed:', data);
            this.handleSequencedEvent('dashboard_refresh', data, namespace);
        });
        
        // Event 12: meeting_update
        socket.on('meeting_update', (data) => {
            console.log('📝 Meeting updated:', data);
            this.handleSequencedEvent('meeting_update', data, namespace);
        });
        
        // Event 13: dashboard_idle_sync
        socket.on('dashboard_idle_sync', (data) => {
            console.log('⏱️ Background sync:', data);
            this.handleSequencedEvent('dashboard_idle_sync', data, namespace);
        });
    }
    
    /**
     * Handle sequenced event with ordering validation
     * @param {string} eventName - Event name
     * @param {Object} data - Event data
     * @param {string} namespace - Namespace
     */
    handleSequencedEvent(eventName, data, namespace) {
        const { event_id, sequence_num, checksum, timestamp } = data;
        
        // Validate event sequencing
        if (sequence_num) {
            if (sequence_num < this.lastAppliedSequence) {
                console.warn(`⚠️ Out-of-order event ignored: ${eventName} (seq ${sequence_num} < ${this.lastAppliedSequence})`);
                return;
            }
            
            this.lastAppliedSequence = sequence_num;
        }
        
        // Store event
        this.eventSequence.push({
            event_id,
            event_name: eventName,
            sequence_num,
            data: data.data,
            timestamp: new Date(timestamp),
            namespace
        });
        
        // Keep last 100 events
        if (this.eventSequence.length > 100) {
            this.eventSequence.shift();
        }
        
        // Emit to local handlers
        this.emit(eventName, data);
        
        // Broadcast to other tabs
        if (this.broadcastChannel) {
            this.broadcastChannel.postMessage({
                type: 'event',
                eventName,
                data,
                namespace,
                timestamp: Date.now()
            });
        }
    }
    
    /**
     * Register event handler
     * @param {string} eventName - Event name
     * @param {Function} handler - Handler function
     */
    on(eventName, handler) {
        if (!this.eventHandlers[eventName]) {
            this.eventHandlers[eventName] = [];
        }
        this.eventHandlers[eventName].push(handler);
    }
    
    /**
     * Emit event to registered handlers
     * @param {string} eventName - Event name
     * @param {Object} data - Event data
     */
    emit(eventName, data) {
        if (this.eventHandlers[eventName]) {
            this.eventHandlers[eventName].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${eventName}:`, error);
                }
            });
        }
    }
    
    /**
     * Setup BroadcastChannel for cross-tab sync
     */
    setupBroadcastChannel() {
        this.broadcastChannel.addEventListener('message', (event) => {
            const { type, eventName, data } = event.data;
            
            if (type === 'event') {
                // Re-emit event in this tab
                this.emit(eventName, data);
            }
        });
    }
    
    /**
     * Send event to server
     * @param {string} namespace - Namespace
     * @param {string} eventName - Event name  
     * @param {Object} data - Event data
     */
    send(namespace, eventName, data) {
        if (this.sockets[namespace]) {
            this.sockets[namespace].emit(eventName, data);
        } else {
            console.warn(`Socket /${namespace} not connected`);
        }
    }
    
    /**
     * Request dashboard sync
     */
    requestSync() {
        this.send('dashboard', 'request_sync', {
            workspace_id: this.workspaceId,
            client_checksum: this.generateChecksum()
        });
    }
    
    /**
     * Generate checksum for current state (placeholder)
     */
    generateChecksum() {
        // TODO: Implement MD5 checksum of dashboard data
        return Date.now().toString();
    }
    
    /**
     * Start heartbeat to keep connection alive
     */
    startHeartbeat() {
        setInterval(() => {
            Object.keys(this.sockets).forEach(namespace => {
                const socket = this.sockets[namespace];
                if (socket.connected) {
                    socket.emit('ping', { timestamp: Date.now() });
                }
            });
        }, 25000); // Every 25 seconds
    }
    
    /**
     * Disconnect from namespace
     * @param {string} namespace - Namespace to disconnect
     */
    disconnect(namespace) {
        if (this.sockets[namespace]) {
            this.sockets[namespace].disconnect();
            delete this.sockets[namespace];
            console.log(`🔌 Disconnected from /${namespace}`);
        }
    }
    
    /**
     * Disconnect all namespaces
     */
    disconnectAll() {
        Object.keys(this.sockets).forEach(namespace => {
            this.disconnect(namespace);
        });
        
        if (this.broadcastChannel) {
            this.broadcastChannel.close();
        }
        
        console.log('🔌 All WebSocket connections closed');
    }
    
    /**
     * Get connection status
     * @returns {Object} Connection status for each namespace
     */
    getStatus() {
        const status = {};
        Object.keys(this.sockets).forEach(namespace => {
            status[namespace] = {
                connected: this.sockets[namespace].connected,
                id: this.sockets[namespace].id
            };
        });
        return status;
    }
}

// Create global singleton instance
window.wsManager = new WebSocketManager();

// Auto-cleanup on page unload
window.addEventListener('beforeunload', () => {
    window.wsManager.disconnectAll();
});
