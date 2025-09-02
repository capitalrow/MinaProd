/**
 * 🛡️ ROBUST ERROR HANDLING & RECOVERY SYSTEM
 * Implements retry/backoff, connection recovery, and user-friendly error flows
 */

class RobustErrorHandling {
    constructor() {
        this.retryConfig = {
            maxRetries: 3,
            baseDelay: 1000,
            maxDelay: 8000,
            backoffMultiplier: 2,
            jitter: true
        };
        
        this.errorTypes = {
            NETWORK: 'network',
            PERMISSION: 'permission', 
            API_KEY: 'api_key',
            RATE_LIMIT: 'rate_limit',
            SERVER: 'server',
            UNKNOWN: 'unknown'
        };
        
        this.connectionState = {
            isOnline: navigator.onLine,
            wsConnected: false,
            apiAvailable: true,
            permissionGranted: false
        };
        
        this.errorHistory = [];
        this.recoveryAttempts = new Map();
        
        this.setupErrorHandlers();
        console.log('🛡️ Robust Error Handling initialized');
    }
    
    /**
     * Setup global error handlers and monitoring
     */
    setupErrorHandlers() {
        // Network status monitoring
        window.addEventListener('online', () => {
            this.connectionState.isOnline = true;
            this.handleNetworkRecovery();
        });
        
        window.addEventListener('offline', () => {
            this.connectionState.isOnline = false;
            this.showUserFriendlyError('network_offline', 'No internet connection. Please check your network and try again.');
        });
        
        // Unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            console.error('🚨 Unhandled promise rejection:', event.reason);
            this.handleError(event.reason, 'unhandled_promise');
        });
        
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('🚨 Global error:', event.error);
            this.handleError(event.error, 'global_error');
        });
    }
    
    /**
     * Classify error type for appropriate handling
     */
    classifyError(error) {
        const message = error.message || error.toString() || '';
        const lowerMessage = message.toLowerCase();
        
        if (lowerMessage.includes('network') || lowerMessage.includes('fetch') || 
            lowerMessage.includes('connection') || error.name === 'NetworkError') {
            return this.errorTypes.NETWORK;
        }
        
        if (lowerMessage.includes('permission') || lowerMessage.includes('denied') ||
            lowerMessage.includes('getusermedia')) {
            return this.errorTypes.PERMISSION;
        }
        
        if (lowerMessage.includes('api_key') || lowerMessage.includes('401') ||
            lowerMessage.includes('unauthorized')) {
            return this.errorTypes.API_KEY;
        }
        
        if (lowerMessage.includes('rate_limit') || lowerMessage.includes('429') ||
            lowerMessage.includes('too many requests')) {
            return this.errorTypes.RATE_LIMIT;
        }
        
        if (lowerMessage.includes('500') || lowerMessage.includes('503') ||
            lowerMessage.includes('server') || lowerMessage.includes('internal')) {
            return this.errorTypes.SERVER;
        }
        
        return this.errorTypes.UNKNOWN;
    }
    
    /**
     * Handle error with appropriate recovery strategy
     */
    async handleError(error, context = 'unknown') {
        const errorType = this.classifyError(error);
        const errorId = this.generateErrorId();
        
        const errorRecord = {
            id: errorId,
            type: errorType,
            message: error.message || error.toString(),
            context: context,
            timestamp: Date.now(),
            retryCount: 0,
            resolved: false
        };
        
        this.errorHistory.push(errorRecord);
        console.error(`🚨 Error ${errorId} [${errorType}]:`, error);
        
        // Update system status
        this.updateSystemStatus(errorType, 'error');
        
        // Choose recovery strategy
        if (this.shouldRetry(errorType, errorRecord)) {
            await this.attemptRecovery(errorRecord, error);
        } else {
            this.showUserFriendlyError(errorType, this.getUserFriendlyMessage(errorType, error));
        }
        
        return errorRecord;
    }
    
    /**
     * Determine if error should trigger retry
     */
    shouldRetry(errorType, errorRecord) {
        // Don't retry permission errors - need user action
        if (errorType === this.errorTypes.PERMISSION) return false;
        
        // Don't retry API key errors - need configuration
        if (errorType === this.errorTypes.API_KEY) return false;
        
        // Check if we've exceeded retry limit for this error type
        const recentErrors = this.errorHistory.filter(e => 
            e.type === errorType && 
            Date.now() - e.timestamp < 60000 && // Last minute
            !e.resolved
        );
        
        return recentErrors.length < this.retryConfig.maxRetries;
    }
    
    /**
     * Attempt automatic error recovery
     */
    async attemptRecovery(errorRecord, originalError) {
        const retryKey = `${errorRecord.type}_${errorRecord.context}`;
        const existingRetry = this.recoveryAttempts.get(retryKey) || { count: 0, lastAttempt: 0 };
        
        if (existingRetry.count >= this.retryConfig.maxRetries) {
            this.showUserFriendlyError(errorRecord.type, 'Maximum retry attempts exceeded. Please try again later.');
            return;
        }
        
        // Calculate delay with exponential backoff and jitter
        const baseDelay = this.retryConfig.baseDelay * Math.pow(this.retryConfig.backoffMultiplier, existingRetry.count);
        const jitter = this.retryConfig.jitter ? Math.random() * 0.3 : 0;
        const delay = Math.min(baseDelay * (1 + jitter), this.retryConfig.maxDelay);
        
        console.log(`🔄 Attempting recovery for ${errorRecord.type} in ${delay}ms (attempt ${existingRetry.count + 1})`);
        
        // Update retry tracking
        existingRetry.count++;
        existingRetry.lastAttempt = Date.now();
        this.recoveryAttempts.set(retryKey, existingRetry);
        
        // Show user feedback for retry
        this.showRetryFeedback(errorRecord.type, existingRetry.count, delay);
        
        // Wait for retry delay
        await new Promise(resolve => setTimeout(resolve, delay));
        
        try {
            // Attempt recovery based on error type
            await this.performRecovery(errorRecord.type, originalError);
            
            // Mark as resolved
            errorRecord.resolved = true;
            errorRecord.retryCount = existingRetry.count;
            
            // Clear retry tracking
            this.recoveryAttempts.delete(retryKey);
            
            // Show success feedback
            this.showRecoverySuccess(errorRecord.type);
            
            console.log(`✅ Recovery successful for ${errorRecord.type}`);
            
        } catch (recoveryError) {
            console.error(`❌ Recovery failed for ${errorRecord.type}:`, recoveryError);
            
            // If we have more retries, schedule another attempt
            if (existingRetry.count < this.retryConfig.maxRetries) {
                setTimeout(() => this.attemptRecovery(errorRecord, originalError), 1000);
            } else {
                this.showUserFriendlyError(errorRecord.type, 'Unable to recover automatically. Please check your connection and try again.');
            }
        }
    }
    
    /**
     * Perform specific recovery actions based on error type
     */
    async performRecovery(errorType, originalError) {
        switch (errorType) {
            case this.errorTypes.NETWORK:
                return this.recoverNetwork();
                
            case this.errorTypes.RATE_LIMIT:
                return this.recoverRateLimit();
                
            case this.errorTypes.SERVER:
                return this.recoverServer();
                
            default:
                throw new Error(`No recovery strategy for ${errorType}`);
        }
    }
    
    /**
     * Recover from network errors
     */
    async recoverNetwork() {
        // Test network connectivity
        try {
            const response = await fetch('/health', { 
                method: 'HEAD',
                cache: 'no-cache',
                signal: AbortSignal.timeout(5000)
            });
            
            if (response.ok) {
                this.connectionState.apiAvailable = true;
                this.updateSystemStatus('connection', 'connected');
                
                // Restart transcription if it was active
                if (window.realWhisperIntegration?.isRecording) {
                    await this.restartTranscription();
                }
                
                return true;
            } else {
                throw new Error(`Health check failed: ${response.status}`);
            }
        } catch (error) {
            this.connectionState.apiAvailable = false;
            throw error;
        }
    }
    
    /**
     * Recover from rate limiting
     */
    async recoverRateLimit() {
        // Wait longer for rate limit recovery
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        // Test with a simple request
        const response = await fetch('/api/transcribe-audio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ test: true })
        });
        
        if (response.status !== 429) {
            this.updateSystemStatus('transcription', 'ready');
            return true;
        } else {
            throw new Error('Rate limit still active');
        }
    }
    
    /**
     * Recover from server errors
     */
    async recoverServer() {
        // Test server health
        const response = await fetch('/health');
        if (response.ok) {
            this.updateSystemStatus('transcription', 'ready');
            return true;
        } else {
            throw new Error(`Server still unavailable: ${response.status}`);
        }
    }
    
    /**
     * Restart transcription after recovery
     */
    async restartTranscription() {
        if (window.realWhisperIntegration) {
            console.log('🔄 Restarting transcription after recovery');
            const sessionId = `recovery_${Date.now()}`;
            await window.realWhisperIntegration.startTranscription(sessionId);
        }
    }
    
    /**
     * Handle network recovery
     */
    handleNetworkRecovery() {
        this.showRecoverySuccess('network');
        
        // Test if transcription service is available
        this.recoverNetwork().catch(error => {
            console.warn('⚠️ Network recovered but transcription service unavailable:', error);
        });
    }
    
    /**
     * Show user-friendly error message
     */
    showUserFriendlyError(errorType, message) {
        const errorContainer = this.getErrorContainer();
        const errorId = this.generateErrorId();
        
        const userMessages = {
            [this.errorTypes.NETWORK]: {
                title: 'Connection Error',
                message: 'Unable to connect to the transcription service. Please check your internet connection.',
                actions: ['Retry', 'Refresh Page']
            },
            [this.errorTypes.PERMISSION]: {
                title: 'Microphone Permission Required',
                message: 'Please allow microphone access to use live transcription.',
                actions: ['Grant Permission', 'Learn More']
            },
            [this.errorTypes.API_KEY]: {
                title: 'Service Configuration Error',
                message: 'Transcription service is not properly configured. Please contact support.',
                actions: ['Contact Support']
            },
            [this.errorTypes.RATE_LIMIT]: {
                title: 'Service Temporarily Unavailable',
                message: 'Too many requests. Please wait a moment and try again.',
                actions: ['Wait and Retry']
            },
            [this.errorTypes.SERVER]: {
                title: 'Service Error',
                message: 'The transcription service is temporarily unavailable. Please try again.',
                actions: ['Retry', 'Check Status']
            }
        };
        
        const errorInfo = userMessages[errorType] || {
            title: 'Unexpected Error',
            message: message || 'An unexpected error occurred. Please try again.',
            actions: ['Retry']
        };
        
        const errorHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert" id="error-${errorId}">
                <div class="d-flex align-items-start">
                    <i class="bi bi-exclamation-triangle-fill text-danger me-2 mt-1" aria-hidden="true"></i>
                    <div class="flex-grow-1">
                        <h6 class="alert-heading mb-1">${errorInfo.title}</h6>
                        <p class="mb-2">${errorInfo.message}</p>
                        <div class="error-actions">
                            ${errorInfo.actions.map(action => 
                                `<button class="btn btn-sm btn-outline-danger me-2" onclick="window.robustErrorHandling.handleErrorAction('${action}', '${errorType}')">${action}</button>`
                            ).join('')}
                        </div>
                    </div>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        errorContainer.innerHTML = errorHTML;
        
        // Update system status indicator
        this.updateSystemStatus(this.getSystemComponent(errorType), 'error');
        
        // Announce to screen readers
        this.announceError(errorInfo.title, errorInfo.message);
    }
    
    /**
     * Show retry feedback to user
     */
    showRetryFeedback(errorType, attemptNumber, delay) {
        if (window.toastSystem) {
            window.toastSystem.showInfo(`🔄 Attempting to reconnect... (${attemptNumber}/${this.retryConfig.maxRetries})`);
        }
        
        console.log(`🔄 Retry ${attemptNumber}: ${errorType} recovery in ${delay}ms`);
    }
    
    /**
     * Show recovery success message
     */
    showRecoverySuccess(errorType) {
        if (window.toastSystem) {
            window.toastSystem.showSuccess('✅ Connection restored successfully!');
        }
        
        // Update system status
        this.updateSystemStatus(this.getSystemComponent(errorType), 'connected');
        
        // Clear error messages
        const errorContainer = this.getErrorContainer();
        errorContainer.innerHTML = '';
    }
    
    /**
     * Handle error action buttons
     */
    handleErrorAction(action, errorType) {
        switch (action) {
            case 'Retry':
                window.location.reload();
                break;
                
            case 'Refresh Page':
                window.location.reload();
                break;
                
            case 'Grant Permission':
                this.requestMicrophonePermission();
                break;
                
            case 'Learn More':
                this.showPermissionHelp();
                break;
                
            case 'Contact Support':
                this.showSupportInfo();
                break;
                
            case 'Wait and Retry':
                setTimeout(() => window.location.reload(), 5000);
                break;
                
            case 'Check Status':
                window.open('/health', '_blank');
                break;
        }
    }
    
    /**
     * Request microphone permission
     */
    async requestMicrophonePermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            
            this.connectionState.permissionGranted = true;
            this.updateSystemStatus('microphone', 'active');
            this.showRecoverySuccess('permission');
            
        } catch (error) {
            this.showUserFriendlyError('permission', 'Microphone permission was denied. Please enable it in your browser settings.');
        }
    }
    
    /**
     * Show permission help
     */
    showPermissionHelp() {
        const helpHTML = `
            <div class="alert alert-info">
                <h6>How to enable microphone permission:</h6>
                <ol>
                    <li>Click the microphone icon in your browser's address bar</li>
                    <li>Select "Allow" for microphone access</li>
                    <li>Refresh the page and try again</li>
                </ol>
                <p class="mb-0"><small>Your privacy is important - audio is only processed for transcription and not stored.</small></p>
            </div>
        `;
        
        const errorContainer = this.getErrorContainer();
        errorContainer.innerHTML = helpHTML;
    }
    
    /**
     * Show support information
     */
    showSupportInfo() {
        const supportHTML = `
            <div class="alert alert-info">
                <h6>Need Help?</h6>
                <p>If you continue experiencing issues, please check:</p>
                <ul>
                    <li>Your internet connection is stable</li>
                    <li>Your browser supports WebRTC and MediaRecorder</li>
                    <li>No other applications are using your microphone</li>
                </ul>
            </div>
        `;
        
        const errorContainer = this.getErrorContainer();
        errorContainer.innerHTML = supportHTML;
    }
    
    /**
     * Get or create error container
     */
    getErrorContainer() {
        let container = document.getElementById('error-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'error-container';
            container.className = 'mt-3';
            
            // Insert at top of main content
            const mainContent = document.getElementById('main-content');
            if (mainContent) {
                mainContent.insertBefore(container, mainContent.firstChild);
            } else {
                document.body.appendChild(container);
            }
        }
        return container;
    }
    
    /**
     * Update system status indicators
     */
    updateSystemStatus(component, status) {
        const healthElement = document.querySelector(`[data-health="${component}"]`);
        if (healthElement) {
            healthElement.textContent = this.getStatusText(status);
            healthElement.className = `badge ${this.getStatusClass(status)}`;
        }
        
        // Show system health section when errors occur
        const systemHealth = document.getElementById('systemHealth');
        if (systemHealth && status === 'error') {
            systemHealth.classList.remove('d-none');
        }
    }
    
    /**
     * Get status text for display
     */
    getStatusText(status) {
        const statusMap = {
            'connected': 'Connected',
            'active': 'Active',
            'ready': 'Ready',
            'error': 'Error',
            'disconnected': 'Disconnected',
            'permission_required': 'Permission Required'
        };
        return statusMap[status] || status;
    }
    
    /**
     * Get CSS class for status
     */
    getStatusClass(status) {
        const classMap = {
            'connected': 'bg-success',
            'active': 'bg-success',
            'ready': 'bg-success',
            'error': 'bg-danger',
            'disconnected': 'bg-danger',
            'permission_required': 'bg-warning'
        };
        return classMap[status] || 'bg-secondary';
    }
    
    /**
     * Get system component from error type
     */
    getSystemComponent(errorType) {
        const componentMap = {
            [this.errorTypes.NETWORK]: 'connection',
            [this.errorTypes.PERMISSION]: 'microphone',
            [this.errorTypes.API_KEY]: 'transcription',
            [this.errorTypes.RATE_LIMIT]: 'transcription',
            [this.errorTypes.SERVER]: 'transcription'
        };
        return componentMap[errorType] || 'connection';
    }
    
    /**
     * Announce error to screen readers
     */
    announceError(title, message) {
        const announcement = document.getElementById('error-messages');
        if (announcement) {
            announcement.textContent = `Error: ${title}. ${message}`;
        }
    }
    
    /**
     * Get user-friendly error message
     */
    getUserFriendlyMessage(errorType, error) {
        // Fallback messages if specific ones aren't used
        const messages = {
            [this.errorTypes.NETWORK]: 'Connection to transcription service failed. Please check your internet connection.',
            [this.errorTypes.PERMISSION]: 'Microphone permission is required for live transcription.',
            [this.errorTypes.API_KEY]: 'Transcription service configuration error.',
            [this.errorTypes.RATE_LIMIT]: 'Service temporarily unavailable due to high demand.',
            [this.errorTypes.SERVER]: 'Transcription service is temporarily unavailable.'
        };
        
        return messages[errorType] || error.message || 'An unexpected error occurred.';
    }
    
    /**
     * Generate unique error ID
     */
    generateErrorId() {
        return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * Get error statistics
     */
    getErrorStats() {
        const recentErrors = this.errorHistory.filter(e => Date.now() - e.timestamp < 300000); // Last 5 minutes
        
        const stats = {
            total: this.errorHistory.length,
            recent: recentErrors.length,
            resolved: this.errorHistory.filter(e => e.resolved).length,
            byType: {}
        };
        
        // Count by type
        Object.values(this.errorTypes).forEach(type => {
            stats.byType[type] = recentErrors.filter(e => e.type === type).length;
        });
        
        return stats;
    }
    
    /**
     * Clear error history
     */
    clearErrorHistory() {
        this.errorHistory = [];
        this.recoveryAttempts.clear();
        console.log('🧹 Error history cleared');
    }
}

// Create global instance
window.robustErrorHandling = new RobustErrorHandling();

console.log('✅ Robust Error Handling system loaded');