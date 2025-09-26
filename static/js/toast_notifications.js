/**
 * Toast Notification System
 * Provides user-friendly notifications with auto-dismiss
 */

class ToastSystem {
    constructor() {
        this.container = null;
        this.init();
    }
    
    init() {
        // Create toast container if it doesn't exist
        if (!document.getElementById('toastContainer')) {
            this.container = document.createElement('div');
            this.container.id = 'toastContainer';
            this.container.className = 'toast-container';
            this.container.setAttribute('aria-live', 'polite');
            this.container.setAttribute('aria-atomic', 'true');
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('toastContainer');
        }
    }
    
    show(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type} p-3 mb-2`;
        toast.setAttribute('role', 'alert');
        
        // Create toast content
        const content = document.createElement('div');
        content.className = 'd-flex align-items-center justify-content-between';
        
        // Icon based on type
        const icons = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        
        content.innerHTML = `
            <div class="d-flex align-items-center">
                <span class="me-2" style="font-size: 1.2rem;">${icons[type] || icons.info}</span>
                <span>${message}</span>
            </div>
            <button type="button" class="btn-close btn-close-white ms-3" aria-label="Close"></button>
        `;
        
        toast.appendChild(content);
        
        // Add close functionality
        const closeBtn = toast.querySelector('.btn-close');
        closeBtn.addEventListener('click', () => this.dismiss(toast));
        
        // Add to container
        this.container.appendChild(toast);
        
        // Auto-dismiss after duration
        if (duration > 0) {
            setTimeout(() => this.dismiss(toast), duration);
        }
        
        return toast;
    }
    
    dismiss(toast) {
        if (!toast || !toast.parentElement) return;
        
        // Fade out animation
        toast.style.animation = 'fadeOut 0.3s ease-out';
        
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 300);
    }
    
    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    }
    
    error(message, duration = 8000) {
        return this.show(message, 'error', duration);
    }
    
    warning(message, duration = 6000) {
        return this.show(message, 'warning', duration);
    }
    
    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }
    
    // Add aliases for compatibility with different naming conventions
    showSuccess(message, duration = 5000) {
        return this.success(message, duration);
    }
    
    showError(message, duration = 8000) {
        return this.error(message, duration);
    }
    
    showWarning(message, duration = 6000) {
        return this.warning(message, duration);
    }
    
    showInfo(message, duration = 5000) {
        return this.info(message, duration);
    }
}

// Initialize global toast system
window.toastSystem = new ToastSystem();

// Add CSS for animations
const toastStyle = document.createElement('style');
toastStyle.textContent = `
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
    
    .toast {
        background: rgba(0, 0, 0, 0.9);
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        min-width: 300px;
        max-width: 500px;
    }
    
    .toast.success {
        background: linear-gradient(135deg, #28a745, #20c997);
    }
    
    .toast.error {
        background: linear-gradient(135deg, #dc3545, #c82333);
    }
    
    .toast.warning {
        background: linear-gradient(135deg, #ffc107, #ffb300);
        color: #212529;
    }
    
    .toast.info {
        background: linear-gradient(135deg, #17a2b8, #138496);
    }
    
    .btn-close-white {
        filter: brightness(0) invert(1);
    }
`;
document.head.appendChild(toastStyle);

console.log('✅ Toast notification system initialized');