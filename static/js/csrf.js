/**
 * CSRF Protection Utility for Mina
 * Automatically adds CSRF tokens to all AJAX requests
 */

(function() {
    'use strict';

    // Get CSRF token from meta tag
    function getCSRFToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : null;
    }

    // Add CSRF token to fetch requests
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        if (/^https?:\/\//i.test(url) && !url.includes(window.location.origin)) {
            return originalFetch(url, options);
        }

        const method = (options.method || 'GET').toUpperCase();
        if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
            options.headers = options.headers || {};
            
            if (options.headers instanceof Headers) {
                options.headers.set('X-CSRFToken', getCSRFToken());
            } else {
                options.headers['X-CSRFToken'] = getCSRFToken();
            }
        }

        return originalFetch(url, options);
    };

    // Add CSRF token to XMLHttpRequest
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
        this._method = method.toUpperCase();
        this._url = url;
        return originalOpen.call(this, method, url, ...rest);
    };

    XMLHttpRequest.prototype.send = function(...args) {
        if (/^https?:\/\//i.test(this._url) && !this._url.includes(window.location.origin)) {
            return originalSend.apply(this, args);
        }

        if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(this._method)) {
            const token = getCSRFToken();
            if (token) {
                this.setRequestHeader('X-CSRFToken', token);
            }
        }

        return originalSend.apply(this, args);
    };

    // Add CSRF token to jQuery AJAX (if jQuery is loaded)
    if (window.jQuery) {
        jQuery.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader('X-CSRFToken', getCSRFToken());
                }
            }
        });
    }

    // Export for manual use
    window.Mina = window.Mina || {};
    window.Mina.csrf = {
        getToken: getCSRFToken,
        
        // Helper to get headers object with CSRF token
        getHeaders: function(additionalHeaders = {}) {
            return {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json',
                ...additionalHeaders
            };
        }
    };

    console.log('✅ CSRF protection enabled');
})();
