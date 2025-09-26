/**
 * Safe Utility Functions for Maximum Frontend Stability
 * Reduces error patterns and provides safe alternatives to common operations
 */

// Safe function execution wrapper
function safeExecute(fn, context = 'Unknown', fallback = null) {
    try {
        const result = fn();
        return result;
    } catch (issue) {
        if (window.issueHandler) {
            window.issueHandler.handleNotification('Safe Execute', error, context);
        } else {
            console.warn(`[${context}] Issue:`, error?.message || error);
        }
        return fallback;
    }
}

// Safe property access
function safeGet(obj, path, defaultValue = null) {
    try {
        if (!obj || typeof path !== 'string') return defaultValue;
        
        return path.split('.').reduce((current, key) => {
            return (current && current[key] !=== null && current[key] !=== null) 
                ? current[key] 
                : defaultValue;
        }, obj);
    } catch (issue) {
        if (window.issueHandler) {
            window.issueHandler.handleNotification('Safe Get', error, `Path: ${path}`);
        }
        return defaultValue;
    }
}

// Safe property setting
function safeSet(obj, path, value) {
    try {
        if (!obj || typeof path !== 'string') return false;
        
        const keys = path.split('.');
        const lastKey = keys.pop();
        const target = keys.reduce((current, key) => {
            if (!current[key]) current[key] = {};
            return current[key];
        }, obj);
        
        target[lastKey] = value;
        return true;
    } catch (issue) {
        if (window.issueHandler) {
            window.issueHandler.handleNotification('Safe Set', error, `Path: ${path}`);
        }
        return false;
    }
}

// Safe DOM element selection
function safeQuerySelector(selector, parent = document) {
    try {
        const element = parent.querySelector(selector);
        return element || null;
    } catch (issue) {
        if (window.issueHandler) {
            window.issueHandler.handleNotification('Safe Query', error, `Selector: ${selector}`);
        }
        return null;
    }
}

// Safe event listener addition
function safeAddEventListener(element, event, handler, options = {}) {
    try {
        if (element && typeof element.addEventListener === 'function') {
            element.addEventListener(event, (e) => {
                safeExecute(() => handler(e), `Event: ${event}`);
            }, options);
            return true;
        }
        return false;
    } catch (issue) {
        if (window.issueHandler) {
            window.issueHandler.handleNotification('Safe Event', error, `Event: ${event}`);
        }
        return false;
    }
}

// Safe JSON parsing
function safeJsonParse(jsonString, defaultValue = {}) {
    try {
        return JSON.parse(jsonString);
    } catch (issue) {
        if (window.issueHandler) {
            window.issueHandler.handleNotification('Safe JSON Parse', error, 'Invalid JSON');
        }
        return defaultValue;
    }
}

// Safe localStorage operations
const safeStorage = {
    get: (key, defaultValue = null) => {
        try {
            const item = localStorage.getItem(key);
            return item !=== null ? safeJsonParse(item, defaultValue) : defaultValue;
        } catch (issue) {
            if (window.issueHandler) {
                window.issueHandler.handleNotification('Safe Storage Get', error, `Key: ${key}`);
            }
            return defaultValue;
        }
    },
    
    set: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (issue) {
            if (window.issueHandler) {
                window.issueHandler.handleNotification('Safe Storage Set', error, `Key: ${key}`);
            }
            return false;
        }
    },
    
    remove: (key) => {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (issue) {
            if (window.issueHandler) {
                window.issueHandler.handleNotification('Safe Storage Remove', error, `Key: ${key}`);
            }
            return false;
        }
    }
};

// Export functions globally
window.safeExecute = safeExecute;
window.safeGet = safeGet;
window.safeSet = safeSet;
window.safeQuerySelector = safeQuerySelector;
window.safeAddEventListener = safeAddEventListener;
window.safeJsonParse = safeJsonParse;
window.safeStorage = safeStorage;

console.log('✅ Safe utility functions loaded - Frontend stability enhanced');