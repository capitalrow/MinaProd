/**
 * Premium Top Navigation Bar - Interactive Functionality
 * Handles dropdowns, mobile menu, and active states
 */

class TopNavigation {
    constructor() {
        this.mobileMenuToggle = document.getElementById('mobileMenuToggle');
        this.navbarMenu = document.getElementById('navbarMenu');
        this.mobileOverlay = document.getElementById('navbarMobileOverlay');
        this.moreDropdownBtn = document.getElementById('moreDropdownBtn');
        this.moreDropdownMenu = document.getElementById('moreDropdownMenu');
        this.userMenuBtn = document.getElementById('userMenuBtn');
        this.userMenu = document.getElementById('userMenu');
        
        this.initializeEventListeners();
        this.setActiveNavItem();
    }
    
    initializeEventListeners() {
        // Mobile menu toggle
        if (this.mobileMenuToggle) {
            this.mobileMenuToggle.addEventListener('click', () => {
                this.toggleMobileMenu();
            });
        }
        
        // Mobile overlay click
        if (this.mobileOverlay) {
            this.mobileOverlay.addEventListener('click', () => {
                this.closeMobileMenu();
            });
        }
        
        // More dropdown
        if (this.moreDropdownBtn) {
            this.moreDropdownBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleDropdown(this.moreDropdownBtn, this.moreDropdownMenu);
            });
        }
        
        // User menu dropdown
        if (this.userMenuBtn) {
            this.userMenuBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleDropdown(this.userMenuBtn, this.userMenu);
            });
        }
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.navbar-dropdown') && !e.target.closest('.navbar-user')) {
                this.closeAllDropdowns();
            }
        });
        
        // Handle window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                this.closeMobileMenu();
            }
        });
        
        // Close mobile menu on navigation
        document.querySelectorAll('.navbar-item[href]').forEach(item => {
            item.addEventListener('click', () => {
                if (window.innerWidth <= 768) {
                    this.closeMobileMenu();
                }
            });
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllDropdowns();
                this.closeMobileMenu();
            }
        });
        
        // Submenu toggle handlers
        document.querySelectorAll('.navbar-submenu-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleSubmenu(toggle);
            });
        });
    }
    
    toggleMobileMenu() {
        const isExpanded = this.mobileMenuToggle.getAttribute('aria-expanded') === 'true';
        
        if (isExpanded) {
            this.closeMobileMenu();
        } else {
            this.openMobileMenu();
        }
    }
    
    openMobileMenu() {
        this.navbarMenu.classList.add('show');
        this.mobileOverlay.classList.add('show');
        this.mobileMenuToggle.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden';
    }
    
    closeMobileMenu() {
        this.navbarMenu.classList.remove('show');
        this.mobileOverlay.classList.remove('show');
        this.mobileMenuToggle.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
    }
    
    toggleDropdown(button, menu) {
        const isExpanded = button.getAttribute('aria-expanded') === 'true';
        
        // Close all other dropdowns first
        this.closeAllDropdowns();
        
        if (!isExpanded) {
            menu.classList.add('show');
            button.setAttribute('aria-expanded', 'true');
        }
    }
    
    closeAllDropdowns() {
        // Close more dropdown
        if (this.moreDropdownMenu) {
            this.moreDropdownMenu.classList.remove('show');
            this.moreDropdownBtn.setAttribute('aria-expanded', 'false');
        }
        
        // Close user menu
        if (this.userMenu) {
            this.userMenu.classList.remove('show');
            this.userMenuBtn.setAttribute('aria-expanded', 'false');
        }
    }
    
    toggleSubmenu(toggle) {
        const targetId = toggle.getAttribute('data-target');
        const submenu = document.getElementById(targetId);
        
        if (!submenu) return;
        
        const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
        
        if (isExpanded) {
            submenu.classList.remove('show');
            toggle.setAttribute('aria-expanded', 'false');
        } else {
            // Close other submenus
            document.querySelectorAll('.navbar-submenu.show').forEach(menu => {
                menu.classList.remove('show');
            });
            document.querySelectorAll('.navbar-submenu-toggle[aria-expanded="true"]').forEach(btn => {
                btn.setAttribute('aria-expanded', 'false');
            });
            
            // Open this submenu
            submenu.classList.add('show');
            toggle.setAttribute('aria-expanded', 'true');
        }
    }
    
    setActiveNavItem() {
        const currentPath = window.location.pathname;
        const navItems = document.querySelectorAll('.navbar-item[data-route]');
        
        navItems.forEach(item => {
            const route = item.getAttribute('data-route');
            
            // Remove active class from all items
            item.classList.remove('active');
            
            // Add active class to matching item
            if (currentPath.startsWith(route) || 
                (route === '/dashboard' && currentPath === '/')) {
                item.classList.add('active');
            }
        });
    }
    
    // Update badge counts
    updateBadge(badgeId, count) {
        const badge = document.getElementById(badgeId);
        if (badge) {
            if (count > 0) {
                badge.textContent = count;
                badge.style.display = '';
            } else {
                badge.style.display = 'none';
            }
        }
    }
    
    // Show live recording indicator
    setRecordingStatus(isRecording) {
        const badge = document.getElementById('recording-badge');
        if (badge) {
            if (isRecording) {
                badge.textContent = 'LIVE';
                badge.style.display = '';
            } else {
                badge.style.display = 'none';
            }
        }
    }
}

// Initialize navigation when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.topNav = new TopNavigation();
    
    // Example: Update badge counts (can be called from other scripts)
    // window.topNav.updateBadge('meetings-badge', 5);
    // window.topNav.setRecordingStatus(true);
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TopNavigation;
}
