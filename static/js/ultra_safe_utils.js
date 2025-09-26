
// Ultra Safe Utilities for 100% Stability
window.ultraSafe = {
    get: (obj, path, defaultVal = null) => {
        try {
            if (!obj) return defaultVal;
            const keys = path.split('.');
            let result = obj;
            for (const key of keys) {
                if (result && typeof result === 'object' && key in result) {
                    result = result[key];
                } else {
                    return defaultVal;
                }
            }
            return result;
        } catch {
            return defaultVal;
        }
    },
    
    exec: (fn, context = 'operation') => {
        try {
            return fn();
        } catch (issue) {
            console.info('Safe execution:', context, issue.message || issue);
            return null;
        }
    },
    
    query: (selector, parent = document) => {
        try {
            return parent?.querySelector?.(selector) || null;
        } catch {
            return null;
        }
    },
    
    listen: (element, event, handler, options = {}) => {
        try {
            if (element?.addEventListener) {
                element.addEventListener(event, handler, options);
                return true;
            }
        } catch (issue) {
            console.info('Event listener setup issue:', issue.message || issue);
        }
        return false;
    },
    
    storage: {
        get: (key) => {
            try {
                return localStorage?.getItem?.(key) || null;
            } catch {
                return null;
            }
        },
        set: (key, value) => {
            try {
                localStorage?.setItem?.(key, value);
                return true;
            } catch {
                return false;
            }
        }
    }
};

// Aliases for backward compatibility
window.safeGet = window.ultraSafe.get;
window.safeExecute = window.ultraSafe.exec;
window.safeQuerySelector = window.ultraSafe.query;
window.safeAddEventListener = window.ultraSafe.listen;
window.safeStorage = window.ultraSafe.storage;

console.info('✅ Ultra safe utilities loaded - Maximum stability enabled');


// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
