/**
 * 🛡️ ROBUSTNESS ENHANCEMENTS
 * Retry logic, connection management, and structured logging
 */

class StructuredLogger {
    constructor(component) {
        this.component = component;
    }
    
    info(message, data = {}) {
        console.log(`[${this.component}] INFO: ${message}`, data);
    }
    
    warn(message, data = {}) {
        console.warn(`[${this.component}] WARN: ${message}`, data);
    }
    
    error(message, data = {}) {
        console.error(`[${this.component}] ERROR: ${message}`, data);
    }
}

class RobustnessEnhancements {
    constructor() {
        this.retryConfigs = {
            transcription: { maxRetries: 3, backoffMs: 1000, timeoutMs: 10000 },
            websocket: { maxRetries: 5, backoffMs: 2000, timeoutMs: 15000 },
            mediaPermissions: { maxRetries: 2, backoffMs: 3000, timeoutMs: 30000 }
        };
        
        this.connectionStates = {
            websocket: 'disconnected',
            microphone: 'unknown',
            transcriptionService: 'unknown'
        };
        
        this.requestLogger = new StructuredLogger('RobustnessEnhancements');
        this.activeConnections = new Set();
        this.sessionId = null;
        
        console.log('🛡️ Robustness Enhancements initialized');
    }
    
    /**
     * Initialize robustness systems
     */
    initialize() {
        this.setupConnectionManagement();
        this.setupRetryMechanisms();
        this.setupStructuredLogging();
        this.preventDuplicateConnections();
        this.setupErrorRecovery();
        this.setupPerformanceMonitoring();
        
        console.log('✅ Robustness systems activated');
    }
    
    /**
     * Setup comprehensive connection management
     */
    setupConnectionManagement() {
        // WebSocket connection monitoring
        this.monitorWebSocketConnections();
        
        // Microphone permission monitoring
        this.monitorMicrophoneAccess();
        
        // API service monitoring
        this.monitorTranscriptionService();
        
        // Connection recovery mechanisms
        this.setupConnectionRecovery();
    }
    
    /**
     * Monitor WebSocket connections
     */
    monitorWebSocketConnections() {
        // Intercept WebSocket creation
        const originalWebSocket = window.WebSocket;
        const self = this;
        
        window.WebSocket = class extends originalWebSocket {
            constructor(url, protocols) {
                super(url, protocols);
                
                this.connectionId = `ws_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                self.registerConnection(this.connectionId, 'websocket');
                
                this.addEventListener('open', (event) => {
                    self.connectionStates.websocket = 'connected';
                    self.requestLogger.info('WebSocket connected', {
                        connectionId: this.connectionId,
                        url: url
                    });
                });
                
                this.addEventListener('close', (event) => {
                    self.connectionStates.websocket = 'disconnected';
                    self.requestLogger.warn('WebSocket disconnected', {
                        connectionId: this.connectionId,
                        code: event.code,
                        reason: event.reason
                    });
                    
                    // Attempt reconnection
                    self.scheduleReconnection('websocket', 5000);
                });
                
                this.addEventListener('error', (event) => {
                    self.requestLogger.error('WebSocket error', {
                        connectionId: this.connectionId,
                        error: event.error
                    });
                });
            }
        };
    }
    
    /**
     * Register active connection
     */
    registerConnection(connectionId, type) {
        this.activeConnections.add({ id: connectionId, type: type, timestamp: Date.now() });
        this.requestLogger.info('Connection registered', { connectionId, type });
    }
    
    /**
     * Monitor microphone access
     */
    monitorMicrophoneAccess() {
        // Intercept getUserMedia calls
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            const originalGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
            
            navigator.mediaDevices.getUserMedia = async (constraints) => {
                try {
                    this.requestLogger.info('Requesting microphone access', { constraints });
                    const stream = await originalGetUserMedia(constraints);
                    
                    this.connectionStates.microphone = 'active';
                    this.requestLogger.info('Microphone access granted', {
                        tracks: stream.getTracks().length
                    });
                    
                    return stream;
                } catch (error) {
                    this.connectionStates.microphone = 'denied';
                    this.requestLogger.error('Microphone access denied', {
                        error: error.message,
                        name: error.name
                    });
                    
                    // Schedule retry for certain error types
                    if (error.name !== 'NotAllowedError') {
                        this.scheduleRetry('mediaPermissions', () => {
                            return originalGetUserMedia(constraints);
                        });
                    }
                    
                    throw error;
                }
            };
        }
    }
    
    /**
     * Monitor transcription service
     */
    monitorTranscriptionService() {
        // Intercept fetch calls to transcription endpoints
        const originalFetch = window.fetch;
        
        window.fetch = async (input, init = {}) => {
            const url = typeof input === 'string' ? input : input.url;
            
            // Check if this is a transcription API call
            if (url.includes('/api/transcribe') || url.includes('/transcription')) {
                const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                
                this.requestLogger.info('Transcription API request', {
                    requestId,
                    url: url,
                    method: init.method || 'GET'
                });
                
                try {
                    const startTime = Date.now();
                    const response = await originalFetch(input, init);
                    const endTime = Date.now();
                    
                    this.connectionStates.transcriptionService = response.ok ? 'available' : 'error';
                    
                    this.requestLogger.info('Transcription API response', {
                        requestId,
                        status: response.status,
                        latency: endTime - startTime
                    });
                    
                    return response;
                } catch (error) {
                    this.connectionStates.transcriptionService = 'unavailable';
                    this.requestLogger.error('Transcription API error', {
                        requestId,
                        error: error.message
                    });
                    
                    // Schedule retry
                    this.scheduleRetry('transcription', () => {
                        return originalFetch(input, init);
                    });
                    
                    throw error;
                }
            }
            
            return originalFetch(input, init);
        };
    }
    
    /**
     * Setup retry mechanisms
     */
    setupRetryMechanisms() {
        this.retryQueues = {
            transcription: [],
            websocket: [],
            mediaPermissions: []
        };
        
        this.retryTimers = new Map();
    }
    
    /**
     * Schedule retry for failed operation
     */
    scheduleRetry(type, operation, attempt = 1) {
        const config = this.retryConfigs[type];
        if (attempt > config.maxRetries) {
            this.requestLogger.error('Max retries exceeded', { type, attempt });
            return;
        }
        
        const delay = config.backoffMs * Math.pow(2, attempt - 1);
        const timerId = setTimeout(async () => {
            try {
                this.requestLogger.info('Retrying operation', { type, attempt, delay });
                await operation();
                this.requestLogger.info('Retry successful', { type, attempt });
            } catch (error) {
                this.requestLogger.warn('Retry failed', { type, attempt, error: error.message });
                this.scheduleRetry(type, operation, attempt + 1);
            }
        }, delay);
        
        this.retryTimers.set(`${type}_${attempt}`, timerId);
    }
    
    /**
     * Schedule reconnection attempt
     */
    scheduleReconnection(type, delay) {
        setTimeout(() => {
            if (this.connectionStates[type] === 'disconnected') {
                this.requestLogger.info('Attempting reconnection', { type });
                // Trigger reconnection based on type
                if (type === 'websocket') {
                    // This would be handled by the application's WebSocket logic
                    document.dispatchEvent(new CustomEvent('reconnectWebSocket'));
                }
            }
        }, delay);
    }
    
    /**
     * Setup structured logging
     */
    setupStructuredLogging() {
        // Enhanced logging with session correlation
        this.sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        // Override console methods for structured logging
        const originalLog = console.log;
        const originalWarn = console.warn;
        const originalError = console.error;
        
        console.log = (...args) => {
            originalLog(`[${this.sessionId}]`, ...args);
        };
        
        console.warn = (...args) => {
            originalWarn(`[${this.sessionId}]`, ...args);
        };
        
        console.error = (...args) => {
            originalError(`[${this.sessionId}]`, ...args);
        };
    }
    
    /**
     * Prevent duplicate connections
     */
    preventDuplicateConnections() {
        // Monitor for duplicate WebSocket connections
        setInterval(() => {
            const wsConnections = Array.from(this.activeConnections).filter(c => c.type === 'websocket');
            if (wsConnections.length > 1) {
                this.requestLogger.warn('Multiple WebSocket connections detected', {
                    count: wsConnections.length
                });
                
                // Close older connections
                wsConnections.slice(0, -1).forEach(conn => {
                    this.requestLogger.info('Closing duplicate connection', { connectionId: conn.id });
                    // This would need to be implemented based on how connections are stored
                });
            }
        }, 10000); // Check every 10 seconds
    }
    
    /**
     * Setup error recovery
     */
    setupErrorRecovery() {
        // Global error handlers
        window.addEventListener('error', (event) => {
            this.requestLogger.error('Global error', {
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.requestLogger.error('Unhandled promise rejection', {
                reason: event.reason
            });
        });
    }
    
    /**
     * Setup performance monitoring
     */
    setupPerformanceMonitoring() {
        // Monitor event loop blocking
        let lastTime = Date.now();
        setInterval(() => {
            const currentTime = Date.now();
            const delta = currentTime - lastTime - 1000; // Expected ~1000ms
            
            if (delta > 100) { // If blocked for more than 100ms
                this.requestLogger.warn('Event loop blocking detected', {
                    blockingTime: delta
                });
            }
            
            lastTime = currentTime;
        }, 1000);
        
        // Monitor memory usage if available
        if (performance.memory) {
            setInterval(() => {
                const memory = performance.memory;
                if (memory.usedJSHeapSize > memory.jsHeapSizeLimit * 0.9) {
                    this.requestLogger.warn('High memory usage detected', {
                        usedHeapSize: memory.usedJSHeapSize,
                        totalHeapSize: memory.totalJSHeapSize,
                        heapSizeLimit: memory.jsHeapSizeLimit
                    });
                }
            }, 30000); // Check every 30 seconds
        }
    }
    
    /**
     * Get connection states
     */
    getConnectionStates() {
        return { ...this.connectionStates };
    }
    
    /**
     * Get session metrics
     */
    getSessionMetrics() {
        return {
            sessionId: this.sessionId,
            activeConnections: this.activeConnections.size,
            connectionStates: this.connectionStates,
            retryQueues: Object.keys(this.retryQueues).reduce((acc, key) => {
                acc[key] = this.retryQueues[key].length;
                return acc;
            }, {})
        };
    }
}

// Create global instance
window.robustnessEnhancements = new RobustnessEnhancements();

console.log('✅ Robustness Enhancements system loaded');

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
