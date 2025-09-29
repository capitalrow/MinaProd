/**
 * MINA STATE MANAGER
 * Comprehensive state management for loading, empty, error, and interactive states
 */

class MinaStateManager {
  constructor() {
    this.toasts = new Map();
    this.modals = new Map();
    this.toastContainer = null;
    this.init();
  }

  init() {
    this.createToastContainer();
    this.bindGlobalEvents();
  }

  // === TOAST NOTIFICATIONS ===
  createToastContainer() {
    if (this.toastContainer) return;
    
    this.toastContainer = document.createElement('div');
    this.toastContainer.className = 'toast-container';
    this.toastContainer.setAttribute('aria-live', 'polite');
    this.toastContainer.setAttribute('aria-label', 'Notifications');
    document.body.appendChild(this.toastContainer);
  }

  showToast(message, type = 'info', options = {}) {
    const id = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    const duration = options.duration || 5000;
    const persistent = options.persistent || false;
    const title = options.title || this.getToastTitle(type);

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.id = id;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');

    const iconHtml = this.getToastIcon(type);
    
    toast.innerHTML = `
      <div class="toast-icon">${iconHtml}</div>
      <div class="toast-content">
        <div class="toast-title">${title}</div>
        <div class="toast-message">${message}</div>
      </div>
      ${!persistent ? '<button type="button" class="toast-close" aria-label="Close notification"><i class="fas fa-times"></i></button>' : ''}
      ${!persistent ? '<div class="toast-progress" style="width: 100%"></div>' : ''}
    `;

    // Add close functionality
    const closeBtn = toast.querySelector('.toast-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.dismissToast(id));
    }

    // Add to container
    this.toastContainer.appendChild(toast);
    this.toasts.set(id, toast);

    // Auto-dismiss if not persistent
    if (!persistent) {
      const progressBar = toast.querySelector('.toast-progress');
      if (progressBar) {
        // Animate progress bar
        setTimeout(() => {
          progressBar.style.transition = `width ${duration}ms linear`;
          progressBar.style.width = '0%';
        }, 100);
      }

      setTimeout(() => {
        this.dismissToast(id);
      }, duration);
    }

    return id;
  }

  dismissToast(id) {
    const toast = this.toasts.get(id);
    if (!toast) return;

    toast.classList.add('removing');
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
      this.toasts.delete(id);
    }, 200);
  }

  getToastTitle(type) {
    const titles = {
      success: 'Success',
      error: 'Error',
      warning: 'Warning',
      info: 'Information'
    };
    return titles[type] || 'Notification';
  }

  getToastIcon(type) {
    const icons = {
      success: '<i class="fas fa-check-circle"></i>',
      error: '<i class="fas fa-exclamation-circle"></i>',
      warning: '<i class="fas fa-exclamation-triangle"></i>',
      info: '<i class="fas fa-info-circle"></i>'
    };
    return icons[type] || icons.info;
  }

  // === MODAL MANAGEMENT ===
  showModal(content, options = {}) {
    const id = 'modal-' + Date.now();
    const title = options.title || '';
    const size = options.size || 'medium';
    const closable = options.closable !== false;

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.id = id;
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-labelledby', `${id}-title`);

    overlay.innerHTML = `
      <div class="modal ${size}">
        <div class="modal-header">
          <h2 class="modal-title" id="${id}-title">${title}</h2>
          ${closable ? '<button type="button" class="modal-close" aria-label="Close modal"><i class="fas fa-times"></i></button>' : ''}
        </div>
        <div class="modal-body">
          ${content}
        </div>
        ${options.footer ? `<div class="modal-footer">${options.footer}</div>` : ''}
      </div>
    `;

    // Add close functionality
    if (closable) {
      const closeBtn = overlay.querySelector('.modal-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => this.dismissModal(id));
      }

      // Close on overlay click
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
          this.dismissModal(id);
        }
      });

      // Close on escape key
      const escapeHandler = (e) => {
        if (e.key === 'Escape') {
          this.dismissModal(id);
          document.removeEventListener('keydown', escapeHandler);
        }
      };
      document.addEventListener('keydown', escapeHandler);
    }

    document.body.appendChild(overlay);
    this.modals.set(id, overlay);

    // Focus management
    const focusableElements = overlay.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    }

    return id;
  }

  dismissModal(id) {
    const modal = this.modals.get(id);
    if (!modal) return;

    modal.classList.add('removing');
    setTimeout(() => {
      if (modal.parentNode) {
        modal.parentNode.removeChild(modal);
      }
      this.modals.delete(id);
    }, 300);
  }

  // === LOADING STATES ===
  showLoading(container, options = {}) {
    if (typeof container === 'string') {
      container = document.querySelector(container);
    }
    if (!container) return;

    const type = options.type || 'spinner';
    const message = options.message || 'Loading...';
    const size = options.size || 'medium';

    container.innerHTML = `
      <div class="loading-container">
        ${this.getLoadingHTML(type, size)}
        ${message ? `<div class="loading-message">${message}</div>` : ''}
      </div>
    `;
  }

  getLoadingHTML(type, size) {
    switch (type) {
      case 'dots':
        return `
          <div class="loading-dots">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
          </div>
        `;
      case 'skeleton':
        return `
          <div class="skeleton-card">
            <div class="skeleton-text"></div>
            <div class="skeleton-text w-3/4"></div>
            <div class="skeleton-text w-1/2"></div>
          </div>
        `;
      default:
        const spinnerClass = size === 'large' ? 'loading-spinner-large' : 'loading-spinner';
        return `<div class="${spinnerClass}"></div>`;
    }
  }

  // === EMPTY STATES ===
  showEmpty(container, options = {}) {
    if (typeof container === 'string') {
      container = document.querySelector(container);
    }
    if (!container) return;

    const icon = options.icon || 'fas fa-inbox';
    const title = options.title || 'No data available';
    const description = options.description || 'There are no items to display at this time.';
    const action = options.action || null;
    const type = options.type || 'default';

    const actionHTML = action ? 
      `<div class="empty-state-action">
        <button type="button" class="btn-premium" onclick="${action.onclick}">${action.text}</button>
      </div>` : '';

    container.innerHTML = `
      <div class="empty-state ${type === 'search' ? 'empty-search' : ''}">
        <div class="empty-state-icon">
          <i class="${icon}"></i>
        </div>
        <div class="empty-state-title">${title}</div>
        <div class="empty-state-description">${description}</div>
        ${actionHTML}
      </div>
    `;
  }

  // === ERROR STATES ===
  showError(container, options = {}) {
    if (typeof container === 'string') {
      container = document.querySelector(container);
    }
    if (!container) return;

    const title = options.title || 'Something went wrong';
    const description = options.description || 'An unexpected error occurred. Please try again.';
    const error = options.error || null;
    const retry = options.retry || null;

    const retryHTML = retry ? 
      `<div class="error-state-actions">
        <button type="button" class="btn-premium" onclick="${retry.onclick}">${retry.text || 'Try again'}</button>
      </div>` : '';

    const errorDetailsHTML = error ? 
      `<div class="error-details" style="display: none;">
        <pre>${typeof error === 'string' ? error : JSON.stringify(error, null, 2)}</pre>
      </div>
      <button type="button" class="error-details-toggle" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'">
        Show details
      </button>` : '';

    container.innerHTML = `
      <div class="error-state">
        <div class="error-state-icon">
          <i class="fas fa-exclamation-triangle"></i>
        </div>
        <div class="error-state-title">${title}</div>
        <div class="error-state-description">${description}</div>
        ${retryHTML}
        ${errorDetailsHTML}
      </div>
    `;
  }

  // === UTILITY METHODS ===
  bindGlobalEvents() {
    // Global keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      // Escape key to close top modal
      if (e.key === 'Escape' && this.modals.size > 0) {
        const lastModal = Array.from(this.modals.keys()).pop();
        this.dismissModal(lastModal);
      }
    });

    // Global error handler
    window.addEventListener('error', (e) => {
      console.error('Global error:', e.error);
      this.showToast('An unexpected error occurred', 'error');
    });

    // Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', (e) => {
      console.error('Unhandled promise rejection:', e.reason);
      this.showToast('An unexpected error occurred', 'error');
    });
  }

  // === API HELPERS ===
  async handleApiCall(promise, options = {}) {
    const loadingContainer = options.loadingContainer;
    const successMessage = options.successMessage;
    const errorMessage = options.errorMessage || 'An error occurred';

    try {
      if (loadingContainer) {
        this.showLoading(loadingContainer, { message: options.loadingMessage });
      }

      const result = await promise;

      if (successMessage) {
        this.showToast(successMessage, 'success');
      }

      return result;
    } catch (error) {
      console.error('API call failed:', error);
      
      if (loadingContainer) {
        this.showError(loadingContainer, {
          title: 'Failed to load data',
          description: errorMessage,
          error: error.message,
          retry: options.retry
        });
      } else {
        this.showToast(errorMessage, 'error');
      }

      throw error;
    }
  }
}

// Global instance
window.MinaState = new MinaStateManager();

// Convenience methods
window.showToast = (message, type, options) => window.MinaState.showToast(message, type, options);
window.showModal = (content, options) => window.MinaState.showModal(content, options);
window.showLoading = (container, options) => window.MinaState.showLoading(container, options);
window.showEmpty = (container, options) => window.MinaState.showEmpty(container, options);
window.showError = (container, options) => window.MinaState.showError(container, options);

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = MinaStateManager;
}