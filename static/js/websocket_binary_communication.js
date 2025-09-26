/**
 * 🔄 BINARY WEBSOCKET COMMUNICATION
 * Enhanced WebSocket communication with binary data support
 */

class BinaryWebSocketCommunication {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.heartbeatInterval = null;
        this.messageQueue = [];
        
        this.connectionId = null;
        this.sessionId = null;
        
        this.eventHandlers = new Map();
        this.responseCallbacks = new Map();
        this.messageIdCounter = 0;
        
        console.log('🔄 Binary WebSocket Communication initialized');
    }
    
    /**
     * Initialize WebSocket connection
     */
    async connect(url = null) {
        const wsUrl = url || this.getWebSocketURL();
        
        try {
            console.log('🔄 Connecting to WebSocket:', wsUrl);
            
            this.socket = new WebSocket(wsUrl);
            this.socket.binaryType = 'arraybuffer'; // Enable binary data
            
            return new Promise((resolve, reject) => {
                this.socket.onopen = (event) => {
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    this.startHeartbeat();
                    this.processMessageQueue();
                    console.log('✅ WebSocket connected');
                    resolve(true);
                };
                
                this.socket.onmessage = (event) => {
                    this.handleMessage(event);
                };
                
                this.socket.onclose = (event) => {
                    this.handleDisconnection(event);
                };
                
                this.socket.onerror = (error) => {
                    console.error('❌ WebSocket error:', error);
                    reject(error);
                };
                
                // Timeout after 5 seconds
                setTimeout(() => {
                    if (!this.isConnected) {
                        reject(new Error('WebSocket connection timeout'));
                    }
                }, 5000);
            });
            
        } catch (error) {
            console.error('❌ WebSocket connection failed:', error);
            throw error;
        }
    }
    
    /**
     * Get WebSocket URL
     */
    getWebSocketURL() {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';\n        const host = location.host;\n        return `${protocol}//${host}/ws`;\n    }\n    \n    /**\n     * Send binary audio data\n     */\n    async sendBinaryAudio(audioData, metadata = {}) {\n        if (!this.isConnected) {\n            throw new Error('WebSocket not connected');\n        }\n        \n        const messageId = this.generateMessageId();\n        \n        // Create binary message with metadata header\n        const metadataStr = JSON.stringify({\n            type: 'audio_chunk',\n            messageId: messageId,\n            timestamp: Date.now(),\n            sessionId: this.sessionId,\n            ...metadata\n        });\n        \n        const metadataBytes = new TextEncoder().encode(metadataStr);\n        const headerSize = new Uint32Array([metadataBytes.length]);\n        \n        // Combine header size + metadata + audio data\n        const totalSize = 4 + metadataBytes.length + audioData.byteLength;\n        const binaryMessage = new ArrayBuffer(totalSize);\n        const view = new Uint8Array(binaryMessage);\n        \n        // Write header size (4 bytes)\n        view.set(new Uint8Array(headerSize.buffer), 0);\n        \n        // Write metadata\n        view.set(metadataBytes, 4);\n        \n        // Write audio data\n        view.set(new Uint8Array(audioData), 4 + metadataBytes.length);\n        \n        // Send binary message\n        this.socket.send(binaryMessage);\n        \n        console.log(`🔄 Sent binary audio: ${audioData.byteLength} bytes`);
        return messageId;
    }
    
    /**
     * Send JSON message
     */
    async sendJSON(data) {
        if (!this.isConnected) {
            this.messageQueue.push(data);
            return;
        }
        
        const messageId = this.generateMessageId();
        const message = {
            ...data,
            messageId: messageId,
            timestamp: Date.now()
        };
        
        this.socket.send(JSON.stringify(message));
        return messageId;
    }
    
    /**
     * Handle incoming messages
     */
    handleMessage(event) {
        try {
            if (event.data instanceof ArrayBuffer) {
                this.handleBinaryMessage(event.data);
            } else {
                this.handleJSONMessage(event.data);
            }
        } catch (error) {
            console.error('❌ Error handling message:', error);
        }
    }
    
    /**
     * Handle binary messages
     */
    handleBinaryMessage(arrayBuffer) {
        try {
            // Read header size (first 4 bytes)
            const headerSizeView = new Uint32Array(arrayBuffer.slice(0, 4));
            const headerSize = headerSizeView[0];
            
            // Read metadata
            const metadataBytes = new Uint8Array(arrayBuffer.slice(4, 4 + headerSize));
            const metadataStr = new TextDecoder().decode(metadataBytes);
            const metadata = JSON.parse(metadataStr);
            
            // Read binary data
            const binaryData = arrayBuffer.slice(4 + headerSize);
            
            this.emitEvent('binary_message', {
                metadata: metadata,
                binaryData: binaryData
            });
            
        } catch (error) {
            console.error('❌ Error parsing binary message:', error);
        }
    }
    
    /**
     * Handle JSON messages
     */
    handleJSONMessage(data) {
        try {
            const message = JSON.parse(data);
            
            // Handle response callbacks
            if (message.messageId && this.responseCallbacks.has(message.messageId)) {
                const callback = this.responseCallbacks.get(message.messageId);
                callback(message);
                this.responseCallbacks.delete(message.messageId);
                return;
            }
            
            // Emit event based on message type
            this.emitEvent(message.type || 'message', message);
            
        } catch (error) {
            console.error('❌ Error parsing JSON message:', error);
        }
    }
    
    /**
     * Handle disconnection
     */
    handleDisconnection(event) {
        this.isConnected = false;
        this.stopHeartbeat();
        
        console.log('🔄 WebSocket disconnected:', event.reason);
        this.emitEvent('disconnected', { reason: event.reason, code: event.code });
        
        // Auto-reconnect if not intentional
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.attemptReconnect();
        }
    }
    
    /**
     * Attempt to reconnect
     */
    async attemptReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`🔄 Reconnecting attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
        
        setTimeout(async () => {
            try {
                await this.connect();
                console.log('✅ Reconnected successfully');
            } catch (error) {
                console.error('❌ Reconnection failed:', error);
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.attemptReconnect();
                } else {
                    this.emitEvent('reconnect_failed', { attempts: this.reconnectAttempts });
                }
            }
        }, delay);
    }
    
    /**
     * Start heartbeat to keep connection alive
     */
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.sendJSON({ type: 'ping' });
            }
        }, 30000); // 30 seconds
    }
    
    /**
     * Stop heartbeat
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    /**
     * Process queued messages
     */
    processMessageQueue() {
        while (this.messageQueue.length > 0 && this.isConnected) {
            const message = this.messageQueue.shift();
            this.sendJSON(message);
        }
    }
    
    /**
     * Set session ID
     */
    setSessionId(sessionId) {
        this.sessionId = sessionId;
        if (this.isConnected) {
            this.sendJSON({
                type: 'join_session',
                sessionId: sessionId
            });
        }
    }
    
    /**
     * Generate unique message ID
     */
    generateMessageId() {
        return `msg_${Date.now()}_${++this.messageIdCounter}`;
    }
    
    /**
     * Register event handler
     */
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }
    
    /**
     * Emit event to registered handlers
     */
    emitEvent(event, data) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`❌ Error in event handler for ${event}:`, error);
                }
            });
        }
    }
    
    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.socket) {
            this.isConnected = false;
            this.socket.close(1000, 'Client disconnect');
            this.socket = null;
        }
        this.stopHeartbeat();
    }
    
    /**
     * Get connection statistics
     */
    getStatistics() {
        return {
            isConnected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            sessionId: this.sessionId,
            queuedMessages: this.messageQueue.length,
            readyState: this.socket ? this.socket.readyState : -1
        };
    }
}

// Initialize global binary WebSocket communication
window.binaryWebSocket = new BinaryWebSocketCommunication();

console.log('✅ Binary WebSocket Communication system loaded');