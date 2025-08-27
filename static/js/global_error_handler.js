/**
 * Global Error Handler for Maximum Frontend Stability
 * Handles all JavaScript errors and prevents application crashes
 */
class GlobalErrorHandler {
    constructor() {
        this.errorCount = 0;
        this.maxErrors = 10;
        this.errorLog = [];
        this.initializeErrorHandling();
        console.log('✅ Global Error Handler initialized - Maximum stability active');
    }
    
    initializeErrorHandling() {
        // Global error boundary
        window.addEventListener('error', (event) => {
            this.handleError('JavaScript Error', event.error || event.message, event.filename, event.lineno);
        });
        
        // Promise rejection handling
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError('Promise Rejection', event.reason);
            event.preventDefault(); // Prevent console spam
        });
        
        // Safe function wrapper
        window.safeExecute = (fn, context = 'Unknown', fallback = null) => {
            try {
                return fn();
            } catch (error) {
                this.handleError('Safe Execute', error, context);
                return fallback;
            }
        };
    }
    
    handleError(type, error, filename = '', line = '') {
        this.errorCount++;
        const errorInfo = {
            type,
            message: error?.message || String(error),
            filename,
            line,
            timestamp: new Date().toISOString(),
            stack: error?.stack?.substring(0, 200) || 'No stack trace'
        };
        
        this.errorLog.push(errorInfo);
        
        // Keep only last 50 errors
        if (this.errorLog.length > 50) {
            this.errorLog.shift();
        }
        
        console.warn(`[${type}] ${errorInfo.message}`, errorInfo);
        
        // Auto-recovery for critical error accumulation
        if (this.errorCount > this.maxErrors) {
            this.performEmergencyRecovery();
        }
    }
    
    performEmergencyRecovery() {
        console.warn('⚠️ Performing emergency recovery due to error accumulation...');
        
        // Try graceful recovery first
        try {
            // Clear any intervals/timers
            for (let i = 1; i < 99999; i++) {
                window.clearInterval(i);
                window.clearTimeout(i);
            }
            
            // Reset error count
            this.errorCount = 0;
            this.errorLog = [];
            
            console.log('✅ Emergency recovery completed successfully');
        } catch (recoveryError) {
            console.error('❌ Emergency recovery failed, reloading page...', recoveryError);
            window.location.reload();
        }
    }
    
    getErrorReport() {
        return {
            totalErrors: this.errorCount,
            recentErrors: this.errorLog.slice(-10),
            status: this.errorCount < 5 ? 'STABLE' : this.errorCount < 10 ? 'WARNING' : 'CRITICAL'
        };
    }
}

// Safe utility functions
window.safeGet = function(obj, path, defaultValue = null) {
    try {
        return path.split('.').reduce((current, key) => 
            current && current[key] !== undefined ? current[key] : defaultValue, obj);
    } catch (error) {
        window.errorHandler?.handleError('Safe Get', error, `Path: ${path}`);
        return defaultValue;
    }
};

window.safeSet = function(obj, path, value) {
    try {
        const keys = path.split('.');
        const lastKey = keys.pop();
        const target = keys.reduce((current, key) => {
            if (!current[key]) current[key] = {};
            return current[key];
        }, obj);
        target[lastKey] = value;
        return true;
    } catch (error) {
        window.errorHandler?.handleError('Safe Set', error, `Path: ${path}`);
        return false;
    }
};

// Initialize global error handler
window.errorHandler = new GlobalErrorHandler();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GlobalErrorHandler;
}