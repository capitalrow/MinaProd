/**
 * Premium Navigation Ecosystem
 * Intelligent breadcrumbs, contextual states, and spatial guidance
 */

class PremiumNavigationSystem {
    constructor() {
        this.currentPath = window.location.pathname;
        this.breadcrumbData = new Map();
        this.contextualStates = new Map();
        this.transitionQueue = [];
        this.isTransitioning = false;
        
        this.init();
    }

    init() {
        console.log('🧭 [Navigation] Initializing Premium Navigation System');
        
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        this.setupBreadcrumbSystem();
        this.setupContextualStates();
        this.setupPageTransitions();
        this.setupNavigationEnhancements();
        this.setupActivityMonitoring();
        
        console.log('✅ [Navigation] Premium navigation system ready');
    }

    /* =============================================== */
    /* INTELLIGENT BREADCRUMB SYSTEM                  */
    /* =============================================== */

    setupBreadcrumbSystem() {
        // Define navigation hierarchy and context
        this.navigationMap = {
            '/': { 
                title: 'Home', 
                icon: 'fas fa-home',
                parent: null 
            },
            '/dashboard': { 
                title: 'Dashboard', 
                icon: 'fas fa-th-large',
                parent: '/' 
            },
            '/dashboard/': { 
                title: 'Dashboard', 
                icon: 'fas fa-th-large',
                parent: '/' 
            },
            '/live': { 
                title: 'Live Recording', 
                icon: 'fas fa-microphone',
                parent: '/dashboard',
                status: 'live'
            },
            '/meetings': { 
                title: 'Meetings', 
                icon: 'fas fa-users',
                parent: '/dashboard' 
            },
            '/dashboard/meetings': { 
                title: 'Meetings', 
                icon: 'fas fa-users',
                parent: '/dashboard' 
            },
            '/tasks': { 
                title: 'Tasks', 
                icon: 'fas fa-check-square',
                parent: '/dashboard' 
            },
            '/dashboard/tasks': { 
                title: 'Tasks', 
                icon: 'fas fa-check-square',
                parent: '/dashboard' 
            },
            '/analytics': { 
                title: 'Analytics', 
                icon: 'fas fa-chart-line',
                parent: '/dashboard' 
            },
            '/dashboard/analytics': { 
                title: 'Analytics', 
                icon: 'fas fa-chart-line',
                parent: '/dashboard' 
            },
            '/settings': { 
                title: 'Settings', 
                icon: 'fas fa-cog',
                parent: '/dashboard' 
            },
            '/calendar': { 
                title: 'Calendar', 
                icon: 'fas fa-calendar-alt',
                parent: '/dashboard' 
            }
        };

        this.renderBreadcrumbs();
        this.setupBreadcrumbListeners();
    }

    buildBreadcrumbPath(currentPath) {
        const path = [];
        let current = currentPath;
        
        // Handle exact matches and normalize paths
        if (!this.navigationMap[current]) {
            // Try with trailing slash
            if (current.endsWith('/')) {
                current = current.slice(0, -1);
            } else {
                current = current + '/';
            }
        }
        
        // Build path from current to root
        while (current && this.navigationMap[current]) {
            const item = this.navigationMap[current];
            path.unshift({
                path: current,
                title: item.title,
                icon: item.icon,
                status: item.status,
                isCurrent: current === this.currentPath || current + '/' === this.currentPath
            });
            current = item.parent;
        }
        
        return path;
    }

    renderBreadcrumbs() {
        let breadcrumbContainer = document.querySelector('.breadcrumb-container');
        
        if (!breadcrumbContainer) {
            // Create breadcrumb container if it doesn't exist
            breadcrumbContainer = this.createBreadcrumbContainer();
        }

        const breadcrumbPath = this.buildBreadcrumbPath(this.currentPath);
        const breadcrumbNav = breadcrumbContainer.querySelector('.breadcrumb-nav');
        
        if (!breadcrumbNav) return;

        // Clear existing breadcrumbs
        breadcrumbNav.innerHTML = '';

        // Render breadcrumb items
        breadcrumbPath.forEach((item, index) => {
            const breadcrumbItem = document.createElement('a');
            breadcrumbItem.href = item.path;
            breadcrumbItem.className = `breadcrumb-item ${item.isCurrent ? 'current' : ''}`;
            
            breadcrumbItem.innerHTML = `
                <i class="breadcrumb-icon ${item.icon}"></i>
                <span>${item.title}</span>
                ${item.status ? `<span class="status-dot ${item.status}"></span>` : ''}
            `;

            breadcrumbNav.appendChild(breadcrumbItem);

            // Add separator if not the last item
            if (index < breadcrumbPath.length - 1) {
                const separator = document.createElement('span');
                separator.className = 'breadcrumb-separator';
                separator.innerHTML = '<i class="fas fa-chevron-right"></i>';
                breadcrumbNav.appendChild(separator);
            }
        });

        // Update page context
        this.updatePageContext(breadcrumbPath[breadcrumbPath.length - 1]);
    }

    createBreadcrumbContainer() {
        const container = document.createElement('header');
        container.className = 'navigation-header';
        container.innerHTML = `
            <div class="breadcrumb-container">
                <nav class="breadcrumb-nav" aria-label="Breadcrumb navigation">
                    <!-- Breadcrumbs will be inserted here -->
                </nav>
                <div class="page-context">
                    <div class="context-status">
                        <span class="status-dot"></span>
                        <span class="status-text">Ready</span>
                    </div>
                </div>
            </div>
        `;

        // Insert after sidebar or at the top of main content
        const mainContent = document.querySelector('.main-content-with-sidebar') || 
                           document.querySelector('main') || 
                           document.body;
        
        mainContent.insertBefore(container, mainContent.firstChild);
        return container;
    }

    updatePageContext(currentPage) {
        const contextStatus = document.querySelector('.context-status');
        if (!contextStatus) return;

        const statusDot = contextStatus.querySelector('.status-dot');
        const statusText = contextStatus.querySelector('.status-text');

        if (currentPage && currentPage.status) {
            statusDot.className = `status-dot ${currentPage.status}`;
            statusText.textContent = this.getStatusText(currentPage.status);
        } else {
            statusDot.className = 'status-dot';
            statusText.textContent = 'Ready';
        }
    }

    getStatusText(status) {
        const statusMap = {
            'live': 'Recording Live',
            'processing': 'Processing',
            'syncing': 'Syncing',
            'offline': 'Offline'
        };
        return statusMap[status] || 'Ready';
    }

    setupBreadcrumbListeners() {
        // Listen for route changes (for SPA navigation)
        window.addEventListener('popstate', () => {
            this.currentPath = window.location.pathname;
            this.renderBreadcrumbs();
        });

        // Intercept navigation links for smooth transitions
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href^="/"]');
            if (link && !link.hasAttribute('data-no-transition')) {
                e.preventDefault();
                this.navigateWithTransition(link.href);
            }
        });
    }

    /* =============================================== */
    /* ENHANCED CONTEXTUAL STATES                     */
    /* =============================================== */

    setupContextualStates() {
        this.updateSidebarStates();
        this.setupActivityListeners();
    }

    updateSidebarStates() {
        const sidebarItems = document.querySelectorAll('.sidebar-item');
        
        sidebarItems.forEach(item => {
            const route = item.getAttribute('data-route') || item.getAttribute('href');
            
            // Mark active item
            if (this.isRouteActive(route)) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }

            // Add enhanced tooltips
            this.enhanceTooltip(item);
        });
    }

    isRouteActive(route) {
        if (!route) return false;
        
        // Handle exact matches and starts-with for nested routes
        return this.currentPath === route || 
               this.currentPath.startsWith(route + '/') ||
               (route !== '/' && this.currentPath.startsWith(route));
    }

    enhanceTooltip(item) {
        const existingTooltip = item.querySelector('.sidebar-item-tooltip');
        if (existingTooltip && !item.querySelector('.enhanced-tooltip')) {
            const enhancedTooltip = document.createElement('div');
            enhancedTooltip.className = 'enhanced-tooltip';
            enhancedTooltip.textContent = existingTooltip.textContent;
            
            // Add status information if available
            const badge = item.querySelector('.sidebar-item-badge');
            if (badge && badge.style.display !== 'none') {
                enhancedTooltip.innerHTML += `<br><small>Active: ${badge.textContent}</small>`;
            }
            
            item.appendChild(enhancedTooltip);
        }
    }

    setupActivityListeners() {
        // Listen for real-time updates from Socket.IO
        if (window.io) {
            const socket = io('/dashboard');
            
            socket.on('session_created', (data) => {
                this.handleActivityUpdate('live', 'recording');
                this.updateBadgeCount('recording', 1);
            });
            
            socket.on('session_completed', (data) => {
                this.handleActivityUpdate('ready', 'recording');
                this.updateBadgeCount('recording', 0);
            });
            
            socket.on('transcription_update', (data) => {
                this.handleActivityUpdate('activity', 'recording');
            });
        }
    }

    handleActivityUpdate(activityType, section) {
        const sidebarItem = document.querySelector(`[data-route*="${section}"]`);
        if (sidebarItem) {
            // Remove existing activity classes
            sidebarItem.classList.remove('has-activity', 'live');
            
            // Add new activity class
            if (activityType === 'live') {
                sidebarItem.classList.add('live');
            } else if (activityType === 'activity') {
                sidebarItem.classList.add('has-activity');
            }
        }
    }

    updateBadgeCount(type, count) {
        const badge = document.getElementById(`${type}-badge`);
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = '';
                if (type === 'recording' && count > 0) {
                    badge.textContent = 'LIVE';
                    badge.classList.add('live');
                }
            } else {
                badge.style.display = 'none';
                badge.classList.remove('live');
            }
        }
    }

    /* =============================================== */
    /* SMOOTH PAGE TRANSITIONS                        */
    /* =============================================== */

    setupPageTransitions() {
        // Wrap main content in transition container if not already wrapped
        const mainContent = document.querySelector('.main-content-with-sidebar');
        if (mainContent && !mainContent.querySelector('.page-container')) {
            this.wrapContentInTransitionContainer(mainContent);
        }
    }

    wrapContentInTransitionContainer(mainContent) {
        const pageContainer = document.createElement('div');
        pageContainer.className = 'page-container';
        
        // Move all children to the page container
        while (mainContent.firstChild) {
            pageContainer.appendChild(mainContent.firstChild);
        }
        
        mainContent.appendChild(pageContainer);
    }

    async navigateWithTransition(url) {
        if (this.isTransitioning) {
            this.transitionQueue.push(url);
            return;
        }

        this.isTransitioning = true;
        const pageContainer = document.querySelector('.page-container');
        
        if (pageContainer) {
            // Start exit transition
            pageContainer.classList.add('page-exiting');
            
            // Wait for transition
            await this.wait(200);
        }

        // Navigate to new page
        window.location.href = url;
    }

    async animateContentEntry() {
        const contentSections = document.querySelectorAll('.content-section');
        const contentItems = document.querySelectorAll('.content-item');
        
        // Add loaded class to trigger animations
        contentSections.forEach((section, index) => {
            setTimeout(() => {
                section.classList.add('loaded');
            }, index * 100);
        });

        // Animate individual items
        await this.wait(200);
        contentItems.forEach(item => {
            item.style.animationPlayState = 'running';
        });
    }

    /* =============================================== */
    /* NAVIGATION ENHANCEMENTS                        */
    /* =============================================== */

    setupNavigationEnhancements() {
        this.addSpatialGuidance();
        this.enhanceKeyboardNavigation();
        this.setupAccessibilityFeatures();
    }

    addSpatialGuidance() {
        const sidebar = document.querySelector('.sidebar-navigation');
        if (sidebar && !sidebar.querySelector('.navigation-flow')) {
            const flowElement = document.createElement('div');
            flowElement.className = 'navigation-flow';
            sidebar.appendChild(flowElement);
        }
    }

    enhanceKeyboardNavigation() {
        let focusedIndex = -1;
        const navigationItems = document.querySelectorAll('.sidebar-item, .breadcrumb-item');

        document.addEventListener('keydown', (e) => {
            // Arrow key navigation
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                
                if (e.key === 'ArrowDown') {
                    focusedIndex = Math.min(focusedIndex + 1, navigationItems.length - 1);
                } else {
                    focusedIndex = Math.max(focusedIndex - 1, 0);
                }
                
                navigationItems[focusedIndex]?.focus();
            }
            
            // Enter key navigation
            if (e.key === 'Enter' && document.activeElement.matches('.sidebar-item, .breadcrumb-item')) {
                document.activeElement.click();
            }
        });
    }

    setupAccessibilityFeatures() {
        // Update ARIA attributes
        const sidebarItems = document.querySelectorAll('.sidebar-item');
        sidebarItems.forEach((item, index) => {
            item.setAttribute('tabindex', index === 0 ? '0' : '-1');
            item.setAttribute('role', 'menuitem');
        });

        // Add live region for status updates
        if (!document.getElementById('navigation-live-region')) {
            const liveRegion = document.createElement('div');
            liveRegion.id = 'navigation-live-region';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.style.cssText = 'position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden;';
            document.body.appendChild(liveRegion);
        }
    }

    /* =============================================== */
    /* ACTIVITY MONITORING                            */
    /* =============================================== */

    setupActivityMonitoring() {
        // Monitor user activity and update navigation states
        this.lastActivity = Date.now();
        
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, () => {
                this.lastActivity = Date.now();
            }, { passive: true });
        });

        // Check activity periodically
        setInterval(() => {
            this.checkUserActivity();
        }, 30000); // Check every 30 seconds
    }

    checkUserActivity() {
        const isActive = Date.now() - this.lastActivity < 300000; // 5 minutes
        const statusDot = document.querySelector('.context-status .status-dot');
        const statusText = document.querySelector('.context-status .status-text');
        
        if (statusDot && statusText) {
            if (!isActive) {
                statusDot.className = 'status-dot offline';
                statusText.textContent = 'Away';
            } else if (!statusDot.classList.contains('live') && !statusDot.classList.contains('processing')) {
                statusDot.className = 'status-dot';
                statusText.textContent = 'Ready';
            }
        }
    }

    /* =============================================== */
    /* UTILITY METHODS                                */
    /* =============================================== */

    wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    announceToScreenReader(message) {
        const liveRegion = document.getElementById('navigation-live-region');
        if (liveRegion) {
            liveRegion.textContent = message;
            setTimeout(() => liveRegion.textContent = '', 1000);
        }
    }

    // Public API for external components
    updateNavigationState(state, section) {
        this.handleActivityUpdate(state, section);
    }

    refreshBreadcrumbs() {
        this.currentPath = window.location.pathname;
        this.renderBreadcrumbs();
        this.updateSidebarStates();
    }

    setBadgeCount(type, count) {
        this.updateBadgeCount(type, count);
    }
}

// Initialize premium navigation
const premiumNavigation = new PremiumNavigationSystem();

// Export for use by other modules
window.PremiumNavigation = premiumNavigation;

// Initialize content animations when page loads
window.addEventListener('load', () => {
    premiumNavigation.animateContentEntry();
});