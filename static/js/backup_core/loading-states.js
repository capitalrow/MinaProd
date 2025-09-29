/**
 * Premium Loading States Management System
 * Provides unified loading feedback across all dashboard components
 */

class LoadingStatesManager {
    constructor() {
        this.loadingStates = new Set();
        this.init();
    }

    init() {
        // Initialize toast container
        this.createToastContainer();
        
        // Auto-enhance refresh buttons
        this.enhanceRefreshButtons();
        
        console.log('🔄 Loading States Manager initialized');
    }

    /**
     * Show loading state for a button
     */
    showButtonLoading(buttonElement, originalText = null) {
        if (!buttonElement) return;
        
        // Store original text if provided
        if (originalText) {
            buttonElement.dataset.originalText = originalText;
        } else if (!buttonElement.dataset.originalText) {
            buttonElement.dataset.originalText = buttonElement.textContent.trim();
        }
        
        // Add loading class and wrap text
        buttonElement.classList.add('loading');
        const textSpan = buttonElement.querySelector('.btn-text') || 
                        this.wrapButtonText(buttonElement);
        
        this.loadingStates.add(buttonElement);
    }

    /**
     * Hide loading state for a button
     */
    hideButtonLoading(buttonElement) {
        if (!buttonElement) return;
        
        buttonElement.classList.remove('loading');
        
        // Restore original text
        if (buttonElement.dataset.originalText) {
            const textSpan = buttonElement.querySelector('.btn-text');
            if (textSpan) {
                textSpan.textContent = buttonElement.dataset.originalText;
            }
        }
        
        this.loadingStates.delete(buttonElement);
    }

    /**
     * Wrap button text in span for loading animation
     */
    wrapButtonText(buttonElement) {
        const originalHTML = buttonElement.innerHTML;
        const textContent = buttonElement.textContent.trim();
        
        // Check if there's an icon
        const icon = buttonElement.querySelector('i');
        
        if (icon) {
            buttonElement.innerHTML = '';
            buttonElement.appendChild(icon);
            const textSpan = document.createElement('span');
            textSpan.className = 'btn-text';
            textSpan.textContent = textContent.replace(icon.textContent || '', '').trim();
            buttonElement.appendChild(textSpan);
            return textSpan;
        } else {
            const textSpan = document.createElement('span');
            textSpan.className = 'btn-text';
            textSpan.textContent = textContent;
            buttonElement.innerHTML = '';
            buttonElement.appendChild(textSpan);
            return textSpan;
        }
    }

    /**
     * Show loading overlay for a section
     */
    showSectionLoading(sectionElement) {
        if (!sectionElement) return;
        
        sectionElement.classList.add('section-loading');
        this.loadingStates.add(sectionElement);
    }

    /**
     * Hide loading overlay for a section
     */
    hideSectionLoading(sectionElement) {
        if (!sectionElement) return;
        
        sectionElement.classList.remove('section-loading');
        this.loadingStates.delete(sectionElement);
    }

    /**
     * Show empty state for a container
     */
    showEmptyState(container, options = {}) {
        if (!container) return;
        
        const {
            icon = 'fas fa-inbox',
            title = 'No data available',
            description = 'There are no items to display at the moment.',
            actionText = null,
            actionCallback = null
        } = options;
        
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.innerHTML = `
            <div class="empty-state-icon">
                <i class="${icon}"></i>
            </div>
            <h3 class="empty-state-title">${title}</h3>
            <p class="empty-state-description">${description}</p>
            ${actionText ? `
                <div class="empty-state-action">
                    <button class="btn btn-primary empty-state-btn">
                        ${actionText}
                    </button>
                </div>
            ` : ''}
        `;
        
        // Add action callback if provided
        if (actionText && actionCallback) {
            const actionBtn = emptyState.querySelector('.empty-state-btn');
            actionBtn.addEventListener('click', actionCallback);
        }
        
        container.innerHTML = '';
        container.appendChild(emptyState);
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        toast.innerHTML = `
            <div class="toast-header">
                <div class="toast-title">
                    <i class="${iconMap[type]}"></i>
                    ${type.charAt(0).toUpperCase() + type.slice(1)}
                </div>
                <button class="toast-close">&times;</button>
            </div>
            <div class="toast-body">${message}</div>
        `;
        
        // Add to container
        const container = document.querySelector('.toast-container');
        container.appendChild(toast);
        
        // Show toast
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // Auto-hide after duration
        const hideTimer = setTimeout(() => {
            this.hideToast(toast);
        }, duration);
        
        // Add close functionality
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            clearTimeout(hideTimer);
            this.hideToast(toast);
        });
        
        return toast;
    }

    /**
     * Hide toast notification
     */
    hideToast(toast) {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    /**
     * Create toast container if it doesn't exist
     */
    createToastContainer() {
        if (!document.querySelector('.toast-container')) {
            const container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
    }

    /**
     * Enhance refresh buttons with loading states
     */
    enhanceRefreshButtons() {
        const refreshButtons = document.querySelectorAll('[id*="refresh"], [class*="refresh"]');
        
        refreshButtons.forEach(button => {
            if (!button.dataset.enhanced) {
                button.addEventListener('click', (e) => {
                    this.handleRefreshClick(button, e);
                });
                button.dataset.enhanced = 'true';
            }
        });
    }

    /**
     * Handle refresh button clicks with loading feedback
     */
    async handleRefreshClick(button, event) {
        // Prevent default if it would cause issues
        if (button.type === 'submit') {
            event.preventDefault();
        }
        
        // Show loading state
        this.showButtonLoading(button);
        
        try {
            // Simulate refresh operation (or call actual refresh logic)
            await this.performRefreshOperation(button);
            
            // Show success toast
            this.showToast('Data refreshed successfully', 'success', 3000);
            
        } catch (error) {
            console.error('Refresh failed:', error);
            this.showToast('Failed to refresh data. Please try again.', 'error');
        } finally {
            // Always hide loading state
            setTimeout(() => {
                this.hideButtonLoading(button);
            }, 500); // Small delay for better UX
        }
    }

    /**
     * Perform actual refresh operation (can be overridden)
     */
    async performRefreshOperation(button) {
        // This can be customized per page
        return new Promise(resolve => {
            // Simulate network request
            setTimeout(resolve, 1000 + Math.random() * 1000);
        });
    }

    /**
     * Clean up all loading states (useful for page transitions)
     */
    cleanup() {
        this.loadingStates.forEach(element => {
            if (element.classList.contains('section-loading')) {
                this.hideSectionLoading(element);
            } else {
                this.hideButtonLoading(element);
            }
        });
        this.loadingStates.clear();
    }
}

// Global instance
window.LoadingStates = new LoadingStatesManager();

// Auto-enhance on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.LoadingStates.enhanceRefreshButtons();
    });
} else {
    window.LoadingStates.enhanceRefreshButtons();
}

// Clean up on page transition
window.addEventListener('beforeunload', () => {
    window.LoadingStates.cleanup();
});

// Export for modules if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoadingStatesManager;
}