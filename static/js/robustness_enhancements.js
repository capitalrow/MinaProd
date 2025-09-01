/**
 * 🛡️ ROBUSTNESS ENHANCEMENTS
 * Retry logic, connection management, and structured logging
 */

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
        window.WebSocket = class extends originalWebSocket {
            constructor(url, protocols) {
                super(url, protocols);
                
                this.connectionId = `ws_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                window.robustnessEnhancements.registerConnection(this.connectionId, 'websocket');
                
                this.addEventListener('open', (event) => {
                    window.robustnessEnhancements.connectionStates.websocket = 'connected';
                    window.robustnessEnhancements.requestLogger.info('WebSocket connected', {
                        connectionId: this.connectionId,
                        url: url
                    });
                });
                
                this.addEventListener('close', (event) => {
                    window.robustnessEnhancements.connectionStates.websocket = 'disconnected';
                    window.robustnessEnhancements.unregisterConnection(this.connectionId);
                    window.robustnessEnhancements.requestLogger.warn('WebSocket disconnected', {
                        connectionId: this.connectionId,
                        code: event.code,
                        reason: event.reason
                    });
                    
                    // Auto-reconnect if unexpected disconnect
                    if (event.code !== 1000 && event.code !== 1001) {
                        window.robustnessEnhancements.scheduleReconnect('websocket');
                    }
                });
                
                this.addEventListener('error', (event) => {
                    window.robustnessEnhancements.connectionStates.websocket = 'error';
                    window.robustnessEnhancements.requestLogger.error('WebSocket error', {
                        connectionId: this.connectionId,
                        event: event
                    });
                });
            }
        };
    }
    
    /**
     * Monitor microphone access
     */
    monitorMicrophoneAccess() {
        // Intercept getUserMedia calls
        const originalGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
        navigator.mediaDevices.getUserMedia = async (constraints) => {
            const requestId = this.generateRequestId();
            
            try {
                this.requestLogger.info('Requesting microphone access', {
                    requestId: requestId,
                    constraints: constraints
                });
                
                const stream = await originalGetUserMedia(constraints);
                
                this.connectionStates.microphone = 'granted';
                this.requestLogger.info('Microphone access granted', {
                    requestId: requestId,
                    tracks: stream.getTracks().length
                });
                
                // Monitor for track ending
                stream.getTracks().forEach(track => {
                    track.addEventListener('ended', () => {
                        this.connectionStates.microphone = 'ended';
                        this.requestLogger.warn('Microphone track ended', {
                            requestId: requestId,
                            trackId: track.id
                        });
                    });
                });
                
                return stream;
                
            } catch (error) {
                this.connectionStates.microphone = 'denied';
                this.requestLogger.error('Microphone access denied', {
                    requestId: requestId,
                    error: error.name,
                    message: error.message
                });
                
                // Show user-friendly error
                this.showMicrophoneError(error);
                throw error;
            }
        };
    }
    
    /**
     * Monitor transcription service
     */
    monitorTranscriptionService() {
        // Intercept fetch calls to transcription endpoints
        const originalFetch = window.fetch;
        window.fetch = async (url, options) => {
            if (url.includes('/api/transcribe')) {
                const requestId = this.generateRequestId();
                const startTime = Date.now();
                
                try {\n                    this.requestLogger.info('Transcription request started', {\n                        requestId: requestId,\n                        url: url,\n                        sessionId: this.sessionId\n                    });\n                    \n                    const response = await this.retryWithBackoff(\n                        () => originalFetch(url, options),\n                        this.retryConfigs.transcription,\n                        requestId\n                    );\n                    \n                    const duration = Date.now() - startTime;\n                    \n                    if (response.ok) {\n                        this.connectionStates.transcriptionService = 'healthy';\n                        this.requestLogger.info('Transcription request completed', {\n                            requestId: requestId,\n                            status: response.status,\n                            duration: duration\n                        });\n                    } else {\n                        this.connectionStates.transcriptionService = 'degraded';\n                        this.requestLogger.warn('Transcription request failed', {\n                            requestId: requestId,\n                            status: response.status,\n                            statusText: response.statusText,\n                            duration: duration\n                        });\n                    }\n                    \n                    return response;\n                    \n                } catch (error) {\n                    this.connectionStates.transcriptionService = 'failed';\n                    this.requestLogger.error('Transcription request error', {\n                        requestId: requestId,\n                        error: error.name,\n                        message: error.message,\n                        duration: Date.now() - startTime\n                    });\n                    \n                    throw error;\n                }\n            }\n            \n            return originalFetch(url, options);\n        };\n    }\n    \n    /**\n     * Setup connection recovery mechanisms\n     */\n    setupConnectionRecovery() {\n        // Health check interval\n        setInterval(() => {\n            this.performHealthCheck();\n        }, 10000); // Every 10 seconds\n        \n        // Visibility change recovery\n        document.addEventListener('visibilitychange', () => {\n            if (!document.hidden) {\n                this.performRecoveryActions();\n            }\n        });\n        \n        // Network status monitoring\n        window.addEventListener('online', () => {\n            this.requestLogger.info('Network connection restored');\n            this.performRecoveryActions();\n        });\n        \n        window.addEventListener('offline', () => {\n            this.requestLogger.warn('Network connection lost');\n            this.handleNetworkDisconnection();\n        });\n    }\n    \n    /**\n     * Retry mechanism with exponential backoff\n     */\n    async retryWithBackoff(operation, config, requestId) {\n        let lastError;\n        \n        for (let attempt = 0; attempt <= config.maxRetries; attempt++) {\n            try {\n                // Add timeout to the operation\n                const timeoutPromise = new Promise((_, reject) => {\n                    setTimeout(() => reject(new Error('Operation timeout')), config.timeoutMs);\n                });\n                \n                const result = await Promise.race([operation(), timeoutPromise]);\n                \n                if (attempt > 0) {\n                    this.requestLogger.info('Retry succeeded', {\n                        requestId: requestId,\n                        attempt: attempt + 1,\n                        totalAttempts: config.maxRetries + 1\n                    });\n                }\n                \n                return result;\n                \n            } catch (error) {\n                lastError = error;\n                \n                if (attempt < config.maxRetries) {\n                    const backoffTime = config.backoffMs * Math.pow(2, attempt);\n                    \n                    this.requestLogger.warn('Retry attempt failed, backing off', {\n                        requestId: requestId,\n                        attempt: attempt + 1,\n                        nextRetryIn: backoffTime,\n                        error: error.message\n                    });\n                    \n                    await this.sleep(backoffTime);\n                } else {\n                    this.requestLogger.error('All retry attempts failed', {\n                        requestId: requestId,\n                        totalAttempts: config.maxRetries + 1,\n                        finalError: error.message\n                    });\n                }\n            }\n        }\n        \n        throw lastError;\n    }\n    \n    /**\n     * Setup structured logging\n     */\n    setupStructuredLogging() {\n        // Create structured log entries for key events\n        this.sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;\n        \n        this.requestLogger.info('Session started', {\n            sessionId: this.sessionId,\n            userAgent: navigator.userAgent,\n            timestamp: new Date().toISOString()\n        });\n        \n        // Log unhandled errors\n        window.addEventListener('error', (event) => {\n            this.requestLogger.error('Unhandled error', {\n                sessionId: this.sessionId,\n                filename: event.filename,\n                lineno: event.lineno,\n                colno: event.colno,\n                message: event.message,\n                stack: event.error?.stack\n            });\n        });\n        \n        // Log unhandled promise rejections\n        window.addEventListener('unhandledrejection', (event) => {\n            this.requestLogger.error('Unhandled promise rejection', {\n                sessionId: this.sessionId,\n                reason: event.reason?.toString(),\n                stack: event.reason?.stack\n            });\n        });\n    }\n    \n    /**\n     * Prevent duplicate WebSocket connections\n     */\n    preventDuplicateConnections() {\n        this.connectionRegistry = new Map();\n        \n        // Clean up stale connections periodically\n        setInterval(() => {\n            this.cleanupStaleConnections();\n        }, 30000); // Every 30 seconds\n    }\n    \n    /**\n     * Register a new connection\n     */\n    registerConnection(connectionId, type) {\n        this.connectionRegistry.set(connectionId, {\n            type: type,\n            createdAt: Date.now(),\n            status: 'active'\n        });\n        \n        this.activeConnections.add(connectionId);\n        \n        this.requestLogger.info('Connection registered', {\n            connectionId: connectionId,\n            type: type,\n            totalConnections: this.activeConnections.size\n        });\n    }\n    \n    /**\n     * Unregister a connection\n     */\n    unregisterConnection(connectionId) {\n        this.connectionRegistry.delete(connectionId);\n        this.activeConnections.delete(connectionId);\n        \n        this.requestLogger.info('Connection unregistered', {\n            connectionId: connectionId,\n            totalConnections: this.activeConnections.size\n        });\n    }\n    \n    /**\n     * Clean up stale connections\n     */\n    cleanupStaleConnections() {\n        const now = Date.now();\n        const staleThreshold = 5 * 60 * 1000; // 5 minutes\n        \n        for (const [connectionId, connection] of this.connectionRegistry.entries()) {\n            if (now - connection.createdAt > staleThreshold) {\n                this.unregisterConnection(connectionId);\n                this.requestLogger.warn('Stale connection cleaned up', {\n                    connectionId: connectionId,\n                    age: now - connection.createdAt\n                });\n            }\n        }\n    }\n    \n    /**\n     * Perform health check\n     */\n    performHealthCheck() {\n        const healthStatus = {\n            websocket: this.connectionStates.websocket,\n            microphone: this.connectionStates.microphone,\n            transcriptionService: this.connectionStates.transcriptionService,\n            activeConnections: this.activeConnections.size,\n            timestamp: new Date().toISOString()\n        };\n        \n        this.requestLogger.debug('Health check performed', healthStatus);\n        \n        // Detect and handle unhealthy states\n        if (this.connectionStates.websocket === 'disconnected' && this.activeConnections.size === 0) {\n            this.scheduleReconnect('websocket');\n        }\n        \n        if (this.connectionStates.transcriptionService === 'failed') {\n            this.handleTranscriptionServiceFailure();\n        }\n    }\n    \n    /**\n     * Perform recovery actions\n     */\n    performRecoveryActions() {\n        this.requestLogger.info('Performing recovery actions');\n        \n        // Reconnect WebSocket if needed\n        if (this.connectionStates.websocket === 'disconnected') {\n            this.scheduleReconnect('websocket');\n        }\n        \n        // Check transcription service health\n        this.checkTranscriptionServiceHealth();\n    }\n    \n    /**\n     * Schedule reconnection attempt\n     */\n    scheduleReconnect(type) {\n        const config = this.retryConfigs[type] || this.retryConfigs.websocket;\n        \n        setTimeout(() => {\n            this.attemptReconnect(type);\n        }, config.backoffMs);\n        \n        this.requestLogger.info('Reconnection scheduled', {\n            type: type,\n            delay: config.backoffMs\n        });\n    }\n    \n    /**\n     * Attempt to reconnect\n     */\n    attemptReconnect(type) {\n        this.requestLogger.info('Attempting reconnection', { type: type });\n        \n        if (type === 'websocket') {\n            // Trigger WebSocket reconnection\n            window.dispatchEvent(new CustomEvent('websocketReconnectRequested'));\n        }\n    }\n    \n    /**\n     * Handle network disconnection\n     */\n    handleNetworkDisconnection() {\n        // Pause transcription if active\n        if (window.audioTranscription && window.audioTranscription.isRecording) {\n            window.audioTranscription.pauseRecording();\n        }\n        \n        // Show network error message\n        this.showNetworkError();\n    }\n    \n    /**\n     * Handle transcription service failure\n     */\n    handleTranscriptionServiceFailure() {\n        this.requestLogger.warn('Handling transcription service failure');\n        \n        // Try alternative endpoint or show degraded service notice\n        this.showTranscriptionServiceError();\n    }\n    \n    /**\n     * Check transcription service health\n     */\n    async checkTranscriptionServiceHealth() {\n        try {\n            const response = await fetch('/api/health');\n            if (response.ok) {\n                this.connectionStates.transcriptionService = 'healthy';\n            } else {\n                this.connectionStates.transcriptionService = 'degraded';\n            }\n        } catch (error) {\n            this.connectionStates.transcriptionService = 'failed';\n        }\n    }\n    \n    /**\n     * Show microphone error to user\n     */\n    showMicrophoneError(error) {\n        let message;\n        \n        switch (error.name) {\n            case 'NotAllowedError':\n                message = 'Microphone access denied. Please enable microphone permissions and refresh the page.';\n                break;\n            case 'NotFoundError':\n                message = 'No microphone found. Please check your microphone connection.';\n                break;\n            case 'NotReadableError':\n                message = 'Microphone is being used by another application. Please close other apps and try again.';\n                break;\n            default:\n                message = `Microphone error: ${error.message}`;\n        }\n        \n        if (window.showNotification) {\n            window.showNotification('Microphone Error', message, 'error');\n        } else {\n            alert(message);\n        }\n    }\n    \n    /**\n     * Show network error to user\n     */\n    showNetworkError() {\n        const message = 'Network connection lost. Transcription has been paused and will resume when connection is restored.';\n        \n        if (window.showNotification) {\n            window.showNotification('Network Error', message, 'warning');\n        } else {\n            console.warn(message);\n        }\n    }\n    \n    /**\n     * Show transcription service error to user\n     */\n    showTranscriptionServiceError() {\n        const message = 'Transcription service is experiencing issues. Please try again later.';\n        \n        if (window.showNotification) {\n            window.showNotification('Service Error', message, 'error');\n        } else {\n            console.error(message);\n        }\n    }\n    \n    /**\n     * Generate unique request ID\n     */\n    generateRequestId() {\n        return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;\n    }\n    \n    /**\n     * Sleep utility\n     */\n    sleep(ms) {\n        return new Promise(resolve => setTimeout(resolve, ms));\n    }\n    \n    /**\n     * Get current system status\n     */\n    getSystemStatus() {\n        return {\n            sessionId: this.sessionId,\n            connections: Object.fromEntries(this.connectionStates),\n            activeConnections: this.activeConnections.size,\n            timestamp: new Date().toISOString()\n        };\n    }\n}\n\n/**\n * Structured Logger for consistent log formatting\n */\nclass StructuredLogger {\n    constructor(component) {\n        this.component = component;\n    }\n    \n    log(level, message, data = {}) {\n        const logEntry = {\n            timestamp: new Date().toISOString(),\n            level: level.toUpperCase(),\n            component: this.component,\n            message: message,\n            sessionId: window.robustnessEnhancements?.sessionId || 'unknown',\n            ...data\n        };\n        \n        // Console output with appropriate level\n        switch (level) {\n            case 'error':\n                console.error(`[${this.component}] ${message}`, logEntry);\n                break;\n            case 'warn':\n                console.warn(`[${this.component}] ${message}`, logEntry);\n                break;\n            case 'info':\n                console.info(`[${this.component}] ${message}`, logEntry);\n                break;\n            case 'debug':\n                console.debug(`[${this.component}] ${message}`, logEntry);\n                break;\n            default:\n                console.log(`[${this.component}] ${message}`, logEntry);\n        }\n        \n        // Send to backend if available\n        this.sendToBackend(logEntry);\n    }\n    \n    error(message, data) { this.log('error', message, data); }\n    warn(message, data) { this.log('warn', message, data); }\n    info(message, data) { this.log('info', message, data); }\n    debug(message, data) { this.log('debug', message, data); }\n    \n    async sendToBackend(logEntry) {\n        try {\n            await fetch('/api/logs', {\n                method: 'POST',\n                headers: { 'Content-Type': 'application/json' },\n                body: JSON.stringify(logEntry)\n            });\n        } catch (error) {\n            // Silently fail - don't create log loops\n        }\n    }\n}\n\n// Initialize robustness enhancements\nwindow.robustnessEnhancements = new RobustnessEnhancements();\n\n// Auto-initialize when DOM is ready\ndocument.addEventListener('DOMContentLoaded', () => {\n    window.robustnessEnhancements.initialize();\n});\n\nconsole.log('\u2705 Robustness Enhancements loaded');"