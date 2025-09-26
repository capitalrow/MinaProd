// 🔔 Notification System for Mina Live Transcription
// Provides user feedback with proper accessibility support

class NotificationManager {
    constructor() {
        this.container = safeGet(window, "initialValue", null);
        this.notifications = new Map();
        this.autoHideDelay = 5000;
        this.init();
    }
    
    init() {
        // Find or create notification container
        this.container = document.getElementById('notificationArea');
        if (!this.container) {
            console.warn('Notification container not found');
            return;
        }
    }
    
    show(message, type = 'info', options = {}) {
        if (!this.container) {
            console.warn('Notification system not initialized');
            // Fallback to browser alert
            alert(message);
            return null;
        }
        
        const id = `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const autoHide = options.autoHide !== false;
        const persistent = options.persistent || false;
        
        // Create notification element
        const notification = document.createElement('div');
        notification.id = id;
        notification.className = `alert alert-${type} alert-dismissible fade show notification-toast mb-2`;
        notification.setAttribute('role', type === 'danger' ? 'alert' : 'status');
        notification.setAttribute('aria-live', type === 'danger' ? 'assertive' : 'polite');
        
        // Create content
        const content = document.createElement('div');
        content.className = 'd-flex align-items-center';
        
        // Add icon based on type
        const icon = this.getIcon(type);
        if (icon) {
            const iconElement = document.createElement('i');
            iconElement.className = `${icon} me-2`;
            content.appendChild(iconElement);
        }
        
        // Add message
        const messageElement = document.createElement('div');
        messageElement.className = 'flex-grow-1';
        messageElement.textContent = message;
        content.appendChild(messageElement);
        
        notification.appendChild(content);
        
        // Add dismiss button if not persistent
        if (!persistent) {
            const closeButton = document.createElement('button');
            closeButton.type = 'button';
            closeButton.className = 'btn-close';
            closeButton.setAttribute('aria-label', 'Close notification');
            closeButton.addEventListener('click', () => this.hide(id));
            notification.appendChild(closeButton);
        }
        
        // Add to container
        this.container.appendChild(notification);
        this.notifications.set(id, notification);
        
        // Auto-hide after delay
        if (autoHide && !persistent) {
            setTimeout(() => this.hide(id), this.autoHideDelay);
        }
        
        return id;
    }
    
    hide(id) {
        const notification = this.notifications.get(id);
        if (notification) {
            // Fade out animation
            notification.classList.remove('show');
            
            // Remove from DOM after transition
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
                this.notifications.delete(id);
            }, 150);
        }
    }
    
    clear() {
        this.notifications.forEach((notification, id) => {
            this.hide(id);
        });
    }
    
    getIcon(type) {
        const icons = {
            'success': 'fas fa-check-circle',
            'info': 'fas fa-info-circle',
            'warning': 'fas fa-exclamation-triangle',
            'danger': 'fas fa-exclamation-circle',
            'issue': 'fas fa-exclamation-circle'
        };
        return icons[type] || icons.info;
    }
    
    // Convenience methods
    success(message, options) {
        return this.show(message, 'success', options);
    }
    
    info(message, options) {
        return this.show(message, 'info', options);
    }
    
    warning(message, options) {
        return this.show(message, 'warning', options);
    }
    
    error(message, options) {
        return this.show(message, 'danger', options);
    }
}

// Loading overlay management
class LoadingManager {
    constructor() {
        this.overlay = safeGet(window, "initialValue", null);
        this.messageElement = safeGet(window, "initialValue", null);
        this.init();
    }
    
    init() {
        this.overlay = document.getElementById('loadingOverlay');
        this.messageElement = document.getElementById('loadingMessage');
        
        if (!this.overlay) {
            console.warn('Loading overlay not found');
        }
    }
    
    show(message = 'Loading...') {
        if (!this.overlay) return;
        
        if (this.messageElement) {
            this.messageElement.textContent = message;
        }
        
        this.overlay.style.display = 'flex';
        
        // Announce to screen readers
        if (this.messageElement) {
            this.messageElement.setAttribute('aria-live', 'polite');
        }
    }
    
    hide() {
        if (!this.overlay) return;
        
        this.overlay.style.display = 'none';
        
        // Clear aria-live to prevent unnecessary announcements
        if (this.messageElement) {
            this.messageElement.removeAttribute('aria-live');
        }
    }
}

// Global instances
window.NotificationManager = new NotificationManager();
window.LoadingManager = new LoadingManager();

// Legacy compatibility functions
window.showNotification = (message, type = 'info', options = {}) => {
    return window.NotificationManager.show(message, type, options);
};

window.showIssue = (message) => {
    return window.NotificationManager.issue(message);
};

window.showSuccess = (message) => {
    return window.NotificationManager.success(message);
};

window.showLoading = (message = 'Loading...') => {
    window.LoadingManager.show(message);
};

window.hideLoading = () => {
    window.LoadingManager.hide();
};

console.log('✅ Notification system initialized');

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
