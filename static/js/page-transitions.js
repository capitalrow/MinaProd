/**
 * Premium Page Transitions with View Transitions API
 * Provides smooth, app-like navigation with fallbacks for unsupported browsers
 */

class PageTransitionManager {
    constructor() {
        this.isSupported = 'startViewTransition' in document;
        this.prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.isNavigating = false;
        
        this.init();
    }

    init() {
        // Listen for reduced motion preference changes
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
            this.prefersReducedMotion = e.matches;
        });

        // Intercept navigation for same-origin links
        this.interceptNavigation();
        
        // Handle browser back/forward
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.transitioned) {
                this.handleBrowserNavigation(window.location.href);
            }
        });

        console.log('🚀 Page Transitions initialized', {
            viewTransitionsSupported: this.isSupported,
            reducedMotion: this.prefersReducedMotion
        });
    }

    interceptNavigation() {
        // Intercept clicks on same-origin links
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            
            if (!link || this.isNavigating) return;
            
            const href = link.getAttribute('href');
            
            // Only handle same-origin navigation
            if (this.shouldInterceptNavigation(link, href)) {
                e.preventDefault();
                this.navigateToPage(href);
            }
        });
    }

    shouldInterceptNavigation(link, href) {
        // Skip if:
        return !(
            !href || 
            href.startsWith('#') || 
            href.startsWith('mailto:') || 
            href.startsWith('tel:') ||
            href.includes('://') && !href.startsWith(window.location.origin) ||
            link.hasAttribute('download') ||
            link.hasAttribute('target') ||
            link.getAttribute('rel') === 'external' ||
            this.prefersReducedMotion ||
            href.includes('/live') || // Force full page load for /live (requires JS initialization)
            href.includes('/auth/') // Force full page load for auth pages
        );
    }

    async navigateToPage(url) {
        if (this.isNavigating) return;
        
        this.isNavigating = true;
        
        try {
            // Add loading state
            this.showLoadingState();
            
            if (this.isSupported && !this.prefersReducedMotion) {
                await this.performViewTransition(url);
            } else {
                await this.performFallbackTransition(url);
            }
        } catch (error) {
            console.error('Navigation failed:', error);
            // Fallback to normal navigation
            window.location.href = url;
        } finally {
            this.isNavigating = false;
            this.hideLoadingState();
        }
    }

    async performViewTransition(url) {
        const transition = document.startViewTransition(async () => {
            await this.updatePage(url);
        });

        await transition.ready;
        
        // Custom transition logic can be added here
        return transition.finished;
    }

    async performFallbackTransition(url) {
        // CSS-based fallback transition
        document.documentElement.classList.add('page-transitioning-out');
        
        await new Promise(resolve => setTimeout(resolve, 150));
        await this.updatePage(url);
        
        document.documentElement.classList.remove('page-transitioning-out');
        document.documentElement.classList.add('page-transitioning-in');
        
        await new Promise(resolve => setTimeout(resolve, 150));
        document.documentElement.classList.remove('page-transitioning-in');
    }

    async updatePage(url) {
        try {
            const response = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'text/html,application/xhtml+xml'
                },
                redirect: 'follow'
            });

            // If the server redirected us (e.g., to login page), do a full page navigation
            // This is important for auth flows and other server-side redirects
            if (response.redirected) {
                window.location.href = response.url;
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const html = await response.text();
            const parser = new DOMParser();
            const newDoc = parser.parseFromString(html, 'text/html');

            // Update page content
            this.updateDocumentContent(newDoc);
            
            // Update browser history
            window.history.pushState({ transitioned: true }, '', url);
            
            // Reinitialize components that need it
            this.reinitializeComponents();
            
        } catch (error) {
            throw new Error(`Failed to fetch page: ${error.message}`);
        }
    }

    updateDocumentContent(newDoc) {
        // Update title
        document.title = newDoc.title;
        
        // Update main content
        const newMain = newDoc.querySelector('#main-content');
        const currentMain = document.querySelector('#main-content');
        
        if (newMain && currentMain) {
            currentMain.innerHTML = newMain.innerHTML;
        }
        
        // Update meta tags
        this.updateMetaTags(newDoc);
        
        // Update active navigation states
        this.updateNavigationStates(newDoc);
    }

    updateMetaTags(newDoc) {
        // Update relevant meta tags
        const metaSelectors = [
            'meta[name="description"]',
            'meta[property^="og:"]',
            'meta[name^="twitter:"]'
        ];

        metaSelectors.forEach(selector => {
            const newMeta = newDoc.querySelector(selector);
            const currentMeta = document.querySelector(selector);
            
            if (newMeta && currentMeta) {
                currentMeta.setAttribute('content', newMeta.getAttribute('content'));
            } else if (newMeta && !currentMeta) {
                document.head.appendChild(newMeta.cloneNode(true));
            }
        });
    }

    updateNavigationStates(newDoc) {
        // Update active sidebar items
        const newActive = newDoc.querySelector('.sidebar-item.active');
        const currentItems = document.querySelectorAll('.sidebar-item');
        
        currentItems.forEach(item => item.classList.remove('active'));
        
        if (newActive) {
            const route = newActive.getAttribute('data-route');
            const matchingItem = document.querySelector(`[data-route="${route}"]`);
            if (matchingItem) {
                matchingItem.classList.add('active');
            }
        }
    }

    reinitializeComponents() {
        // Reinitialize components that need it after page transition
        
        // Update sidebar active state
        if (window.SidebarNavigation) {
            window.SidebarNavigation.markActiveRoute();
        }
        
        // Reinitialize any chart libraries
        if (typeof initializeCharts === 'function') {
            initializeCharts();
        }
        
        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('page-transitioned', {
            detail: { url: window.location.href }
        }));
    }

    showLoadingState() {
        document.documentElement.classList.add('page-loading');
        
        // Show a subtle loading indicator
        const loader = document.createElement('div');
        loader.className = 'page-transition-loader';
        loader.innerHTML = `
            <div class="loader-bar"></div>
        `;
        document.body.appendChild(loader);
    }

    hideLoadingState() {
        document.documentElement.classList.remove('page-loading');
        
        const loader = document.querySelector('.page-transition-loader');
        if (loader) {
            loader.remove();
        }
    }

    async handleBrowserNavigation(url) {
        // Handle browser back/forward navigation
        try {
            await this.updatePage(url);
        } catch (error) {
            console.error('Browser navigation failed:', error);
            window.location.reload();
        }
    }
}

// CSS for View Transitions API
const transitionStyles = `
/* View Transitions API Styles */
::view-transition-old(root),
::view-transition-new(root) {
  animation-duration: 0.25s;
  animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}

::view-transition-old(root) {
  animation-name: slide-out-left;
}

::view-transition-new(root) {
  animation-name: slide-in-right;
}

/* Fallback animations for non-supporting browsers */
.page-transitioning-out {
  opacity: 0;
  transform: translateX(-10px);
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.page-transitioning-in {
  opacity: 0;
  transform: translateX(10px);
  animation: slideInFallback 0.15s ease forwards;
}

@keyframes slide-out-left {
  to {
    opacity: 0;
    transform: translateX(-20px);
  }
}

@keyframes slide-in-right {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInFallback {
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Loading indicator */
.page-transition-loader {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 9999;
  background: var(--mina-bg-primary);
}

.loader-bar {
  height: 100%;
  background: linear-gradient(
    90deg,
    var(--mina-primary),
    var(--mina-primary-light),
    var(--mina-primary)
  );
  width: 0%;
  animation: loading-progress 0.5s ease-in-out forwards;
}

@keyframes loading-progress {
  to {
    width: 100%;
  }
}

/* Respect reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  ::view-transition-old(root),
  ::view-transition-new(root) {
    animation: none !important;
  }
  
  .page-transitioning-out,
  .page-transitioning-in {
    transition: none !important;
    animation: none !important;
    opacity: 1 !important;
    transform: none !important;
  }
  
  .page-transition-loader {
    display: none;
  }
}
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = transitionStyles;
document.head.appendChild(styleSheet);

// Initialize when DOM is ready (only if enhanced version isn't loaded)
if (!window.pageTransitionsInitialized) {
  window.pageTransitionsInitialized = true;
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      new PageTransitionManager();
    });
  } else {
    new PageTransitionManager();
  }
}

// Export for use in other scripts
window.PageTransitionManager = PageTransitionManager;