// Expandable Sidebar Navigation JavaScript
// Industry-standard implementation following Slack/Notion patterns

class SidebarNavigation {
    constructor() {
        this.sidebar = null;
        this.isExpanded = false;
        this.isMobile = window.innerWidth <= 768;
        this.activeRoute = window.location.pathname;
        this.init();
    }

    init() {
        // Check if sidebar state is saved in localStorage
        const savedState = localStorage.getItem('sidebarExpanded');
        this.isExpanded = savedState === 'true' && !this.isMobile;
        
        // Initialize after DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupSidebar());
        } else {
            this.setupSidebar();
        }

        // Handle window resize
        window.addEventListener('resize', () => this.handleResize());
    }

    setupSidebar() {
        // Find existing sidebar from template
        this.sidebar = document.querySelector('.sidebar-navigation');
        if (!this.sidebar) {
            console.error('Sidebar not found in template');
            return;
        }

        // Set initial state (expanded by default for premium experience)
        this.isExpanded = !this.isMobile;
        if (this.isExpanded) {
            this.sidebar.classList.add('expanded');
        } else {
            this.sidebar.classList.remove('expanded');
        }

        // Add event listeners
        this.attachEventListeners();
        
        // Mark active route
        this.markActiveRoute();
        
        // Add body class for styling adjustments
        document.body.classList.add('has-sidebar-nav');
    }

    createSidebar() {
        const sidebarHTML = `
            <aside class="sidebar-navigation" role="navigation" aria-label="Main navigation">
                <!-- Logo/Brand Section -->
                <div class="sidebar-brand" role="button" tabindex="0" aria-label="Toggle sidebar menu">
                    <div class="sidebar-brand-icon">
                        <i class="fas fa-microphone-alt"></i>
                    </div>
                    <div class="sidebar-brand-text">
                        <h1>Mina</h1>
                        <small>AI Platform</small>
                    </div>
                    <i class="fas fa-chevron-right sidebar-toggle-indicator"></i>
                </div>

                <!-- Navigation Menu -->
                <nav class="sidebar-menu" role="menu">
                    <!-- Main Section -->
                    <div class="sidebar-section">
                        <div class="sidebar-section-label">Main</div>
                        
                        <a href="/dashboard/" class="sidebar-item" data-route="/dashboard/" role="menuitem">
                            <div class="sidebar-item-icon">
                                <i class="fas fa-th-large"></i>
                            </div>
                            <span class="sidebar-item-text">Dashboard</span>
                            <div class="sidebar-item-tooltip">Dashboard</div>
                        </a>

                        <a href="/live" class="sidebar-item" data-route="/live" role="menuitem">
                            <div class="sidebar-item-icon">
                                <i class="fas fa-microphone"></i>
                            </div>
                            <span class="sidebar-item-text">Recording</span>
                            <div class="sidebar-item-badge" id="recording-badge" style="display: none;">LIVE</div>
                            <div class="sidebar-item-tooltip">Recording</div>
                        </a>

                        <a href="/meetings" class="sidebar-item" data-route="/meetings" role="menuitem">
                            <div class="sidebar-item-icon">
                                <i class="fas fa-users"></i>
                            </div>
                            <span class="sidebar-item-text">Meetings</span>
                            <div class="sidebar-item-badge" id="meetings-badge" style="display: none;">0</div>
                            <div class="sidebar-item-tooltip">Meetings</div>
                        </a>

                        <a href="/tasks" class="sidebar-item" data-route="/tasks" role="menuitem">
                            <div class="sidebar-item-icon">
                                <i class="fas fa-check-square"></i>
                            </div>
                            <span class="sidebar-item-text">Tasks</span>
                            <div class="sidebar-item-badge" id="tasks-badge" style="display: none;">0</div>
                            <div class="sidebar-item-tooltip">Tasks</div>
                        </a>
                    </div>

                    <!-- Analytics Section -->
                    <div class="sidebar-section">
                        <div class="sidebar-section-label">Analytics</div>
                        
                        <a href="/analytics" class="sidebar-item" data-route="/analytics" role="menuitem">
                            <div class="sidebar-item-icon">
                                <i class="fas fa-chart-line"></i>
                            </div>
                            <span class="sidebar-item-text">Analytics</span>
                            <div class="sidebar-item-tooltip">Analytics</div>
                        </a>

                        <a href="/insights" class="sidebar-item" data-route="/insights" role="menuitem">
                            <div class="sidebar-item-icon">
                                <i class="fas fa-lightbulb"></i>
                            </div>
                            <span class="sidebar-item-text">Insights</span>
                            <div class="sidebar-item-tooltip">Insights</div>
                        </a>

                        <a href="/reports" class="sidebar-item" data-route="/reports" role="menuitem">
                            <div class="sidebar-item-icon">
                                <i class="fas fa-file-alt"></i>
                            </div>
                            <span class="sidebar-item-text">Reports</span>
                            <div class="sidebar-item-tooltip">Reports</div>
                        </a>
                    </div>

                    <!-- Tools Section -->
                    <div class="sidebar-section">
                        <div class="sidebar-section-label">Tools</div>
                        
                        <a href="/calendar" class="sidebar-item" data-route="/calendar" role="menuitem">
                            <div class="sidebar-item-icon">
                                <i class="fas fa-calendar-alt"></i>
                            </div>
                            <span class="sidebar-item-text">Calendar</span>
                            <div class="sidebar-item-tooltip">Calendar</div>
                        </a>

                        <a href="/export" class="sidebar-item" data-route="/export" role="menuitem">
                            <div class="sidebar-item-icon">
                                <i class="fas fa-download"></i>
                            </div>
                            <span class="sidebar-item-text">Export</span>
                            <div class="sidebar-item-tooltip">Export</div>
                        </a>

                        <a href="/integrations" class="sidebar-item" data-route="/integrations" role="menuitem">
                            <div class="sidebar-item-icon">
                                <i class="fas fa-plug"></i>
                            </div>
                            <span class="sidebar-item-text">Integrations</span>
                            <div class="sidebar-item-tooltip">Integrations</div>
                        </a>
                    </div>

                    <!-- System Section -->
                    <div class="sidebar-section">
                        <div class="sidebar-section-label">System</div>
                        
                        <a href="/settings" class="sidebar-item" data-route="/settings" role="menuitem">
                            <div class="sidebar-item-icon">
                                <i class="fas fa-cog"></i>
                            </div>
                            <span class="sidebar-item-text">Settings</span>
                            <div class="sidebar-item-tooltip">Settings</div>
                        </a>

                        <a href="/help" class="sidebar-item" data-route="/help" role="menuitem">
                            <div class="sidebar-item-icon">
                                <i class="fas fa-question-circle"></i>
                            </div>
                            <span class="sidebar-item-text">Help</span>
                            <div class="sidebar-item-tooltip">Help</div>
                        </a>
                    </div>
                </nav>

                <!-- Footer Section -->
                <div class="sidebar-footer">
                    <div class="sidebar-user">
                        <div class="sidebar-user-avatar">
                            ${this.getUserInitials()}
                        </div>
                        <div class="sidebar-user-info">
                            <span class="sidebar-user-name">User</span>
                            <span class="sidebar-user-status">
                                <i class="fas fa-circle text-success" style="font-size: 8px;"></i> Online
                            </span>
                        </div>
                    </div>
                </div>
            </aside>

            <!-- Mobile Overlay -->
            <div class="sidebar-overlay" id="sidebarOverlay"></div>

            <!-- Main Content Container -->
            <div class="main-content-with-sidebar" id="mainContent">
                <!-- Original content will be moved here -->
            </div>
        `;

        // Insert sidebar at the beginning of body
        document.body.insertAdjacentHTML('afterbegin', sidebarHTML);
        this.sidebar = document.querySelector('.sidebar-navigation');

        // Move main content into container
        const mainContent = document.getElementById('mainContent');
        const existingContent = Array.from(document.body.children).filter(child => 
            !child.classList.contains('sidebar-navigation') && 
            !child.classList.contains('sidebar-overlay') &&
            !child.classList.contains('main-content-with-sidebar')
        );
        
        existingContent.forEach(element => {
            mainContent.appendChild(element);
        });
    }

    attachEventListeners() {
        // Toggle sidebar on brand click
        const brand = this.sidebar.querySelector('.sidebar-brand');
        if (brand) {
            brand.addEventListener('click', () => this.toggleSidebar());
            brand.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleSidebar();
                }
            });
        }

        // Mobile overlay click
        const overlay = document.getElementById('sidebarOverlay');
        if (overlay) {
            overlay.addEventListener('click', () => this.toggleSidebar());
        } else {
            console.warn('Sidebar overlay element not found');
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + B to toggle sidebar
            if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                e.preventDefault();
                this.toggleSidebar();
            }
            
            // Escape to close on mobile
            if (e.key === 'Escape' && this.isMobile && this.isExpanded) {
                this.toggleSidebar();
            }
        });

        // Update active state on navigation
        const menuItems = this.sidebar.querySelectorAll('.sidebar-item');
        menuItems.forEach(item => {
            item.addEventListener('click', (e) => {
                // Let the browser handle the navigation
                // Just update the active state
                menuItems.forEach(i => i.classList.remove('active'));
                item.classList.add('active');
            });
        });
    }

    toggleSidebar() {
        this.isExpanded = !this.isExpanded;
        
        const overlay = document.getElementById('sidebarOverlay');
        
        if (this.isExpanded) {
            this.sidebar.classList.add('expanded');
            if (this.isMobile && overlay) {
                overlay.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        } else {
            this.sidebar.classList.remove('expanded');
            if (this.isMobile && overlay) {
                overlay.classList.remove('active');
                document.body.style.overflow = '';
            }
        }

        // Save state to localStorage (desktop only)
        if (!this.isMobile) {
            localStorage.setItem('sidebarExpanded', this.isExpanded);
        }

        // Update ARIA attributes for accessibility
        this.sidebar.setAttribute('aria-expanded', this.isExpanded);

        // Dispatch event for other components
        window.dispatchEvent(new CustomEvent('sidebar-toggled', { 
            detail: { expanded: this.isExpanded } 
        }));
    }

    markActiveRoute() {
        const menuItems = this.sidebar.querySelectorAll('.sidebar-item');
        menuItems.forEach(item => {
            const route = item.getAttribute('data-route');
            if (route && this.activeRoute.startsWith(route)) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    handleResize() {
        const wasMobile = this.isMobile;
        this.isMobile = window.innerWidth <= 768;

        if (wasMobile !== this.isMobile) {
            // Switched between mobile and desktop
            if (this.isMobile) {
                // Switched to mobile - collapse
                this.sidebar.classList.remove('expanded');
                this.isExpanded = false;
            } else {
                // Switched to desktop - restore saved state
                const savedState = localStorage.getItem('sidebarExpanded');
                this.isExpanded = savedState === 'true';
                if (this.isExpanded) {
                    this.sidebar.classList.add('expanded');
                }
            }
        }
    }

    getUserInitials() {
        // Get user initials from current user data if available
        const userName = 'User'; // This would come from actual user data
        return userName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'U';
    }

    // Public API methods
    expand() {
        if (!this.isExpanded) {
            this.toggleSidebar();
        }
    }

    collapse() {
        if (this.isExpanded) {
            this.toggleSidebar();
        }
    }

    updateBadge(type, value) {
        const badge = document.getElementById(`${type}-badge`);
        if (badge) {
            if (value > 0) {
                badge.textContent = value > 99 ? '99+' : value;
                badge.style.display = '';
            } else {
                badge.style.display = 'none';
            }
        }
    }
}

// Initialize sidebar
const sidebarNav = new SidebarNavigation();

// Export for use in other scripts
window.SidebarNavigation = sidebarNav;