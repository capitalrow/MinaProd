/**
 * Premium Hamburger Menu - Crown+ Edition
 * GSAP-powered mobile navigation with glassmorphism
 */

class HamburgerMenu {
  constructor() {
    this.button = document.getElementById('mobile-menu-button');
    this.menu = null;
    this.backdrop = null;
    this.isOpen = false;
    this.animating = false;
    
    if (!this.button) return;
    
    this.init();
  }
  
  init() {
    this.createMenuStructure();
    this.attachEventListeners();
    this.setupAccessibility();
  }
  
  createMenuStructure() {
    // Create glassmorphism backdrop
    this.backdrop = document.createElement('div');
    this.backdrop.className = 'hamburger-backdrop';
    this.backdrop.setAttribute('aria-hidden', 'true');
    document.body.appendChild(this.backdrop);
    
    // Create mobile menu drawer
    this.menu = document.createElement('div');
    this.menu.className = 'hamburger-menu';
    this.menu.setAttribute('role', 'dialog');
    this.menu.setAttribute('aria-label', 'Mobile navigation');
    this.menu.setAttribute('aria-modal', 'true');
    
    // Clone navbar menu items
    const navbarMenu = document.querySelector('.navbar-menu');
    if (navbarMenu) {
      const menuContent = document.createElement('div');
      menuContent.className = 'hamburger-menu-content';
      
      // Add header
      const header = document.createElement('div');
      header.className = 'hamburger-menu-header';
      header.innerHTML = `
        <div class="hamburger-menu-brand">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <rect width="32" height="32" rx="8" fill="url(#logo-gradient-mobile)"/>
            <path d="M8 12L16 8L24 12V20L16 24L8 20V12Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <defs>
              <linearGradient id="logo-gradient-mobile" x1="0" y1="0" x2="32" y2="32">
                <stop offset="0%" stop-color="#6366f1"/>
                <stop offset="100%" stop-color="#8b5cf6"/>
              </linearGradient>
            </defs>
          </svg>
          <span class="hamburger-menu-title">Mina</span>
        </div>
        <button class="hamburger-menu-close" id="hamburger-close" aria-label="Close menu">
          <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      `;
      menuContent.appendChild(header);
      
      // Add navigation items
      const nav = document.createElement('nav');
      nav.className = 'hamburger-menu-nav';
      nav.setAttribute('role', 'navigation');
      nav.setAttribute('aria-label', 'Mobile menu items');
      
      const links = navbarMenu.querySelectorAll('.navbar-link');
      links.forEach((link, index) => {
        const menuItem = document.createElement('a');
        menuItem.href = link.href;
        menuItem.className = 'hamburger-menu-item';
        menuItem.textContent = link.textContent;
        menuItem.style.setProperty('--stagger-index', index);
        nav.appendChild(menuItem);
      });
      
      menuContent.appendChild(nav);
      
      // Add actions section if present
      const actions = navbarMenu.querySelector('.navbar-actions');
      if (actions) {
        const actionsSection = document.createElement('div');
        actionsSection.className = 'hamburger-menu-actions';
        actionsSection.innerHTML = actions.innerHTML;
        menuContent.appendChild(actionsSection);
      }
      
      this.menu.appendChild(menuContent);
    }
    
    document.body.appendChild(this.menu);
    
    // Set initial state (hidden)
    gsap.set(this.backdrop, { opacity: 0, pointerEvents: 'none' });
    gsap.set(this.menu, { x: '100%' });
  }
  
  attachEventListeners() {
    // Open menu
    this.button.addEventListener('click', () => this.toggle());
    
    // Close on backdrop click
    this.backdrop.addEventListener('click', () => this.close());
    
    // Close button
    const closeButton = document.getElementById('hamburger-close');
    if (closeButton) {
      closeButton.addEventListener('click', () => this.close());
    }
    
    // Close menu when clicking a link
    const menuItems = this.menu.querySelectorAll('.hamburger-menu-item');
    menuItems.forEach(item => {
      item.addEventListener('click', () => {
        setTimeout(() => this.close(), 200);
      });
    });
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });
    
    // Handle resize
    window.addEventListener('resize', () => {
      if (window.innerWidth > 768 && this.isOpen) {
        this.close(false); // Close without animation on resize
      }
    });
  }
  
  setupAccessibility() {
    // Trap focus within menu when open
    this.menu.addEventListener('keydown', (e) => {
      if (!this.isOpen) return;
      
      if (e.key === 'Tab') {
        const focusableElements = this.menu.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    });
  }
  
  toggle() {
    if (this.animating) return;
    
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }
  
  open() {
    if (this.animating || this.isOpen) return;
    
    this.animating = true;
    this.isOpen = true;
    
    // Update ARIA
    this.button.setAttribute('aria-expanded', 'true');
    this.backdrop.setAttribute('aria-hidden', 'false');
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    // Animate hamburger icon to X
    this.animateHamburgerIcon(true);
    
    // Animation timeline
    const tl = gsap.timeline({
      onComplete: () => {
        this.animating = false;
        // Focus first menu item
        const firstItem = this.menu.querySelector('.hamburger-menu-item');
        if (firstItem) firstItem.focus();
      }
    });
    
    // Backdrop fade in
    tl.to(this.backdrop, {
      opacity: 1,
      pointerEvents: 'auto',
      duration: 0.3,
      ease: 'power2.out'
    });
    
    // Menu slide in
    tl.to(this.menu, {
      x: '0%',
      duration: 0.4,
      ease: 'power3.out'
    }, '-=0.2');
    
    // Stagger menu items
    const items = this.menu.querySelectorAll('.hamburger-menu-item');
    tl.from(items, {
      x: 40,
      opacity: 0,
      stagger: 0.05,
      duration: 0.3,
      ease: 'power2.out'
    }, '-=0.2');
  }
  
  close(animated = true) {
    if (this.animating || !this.isOpen) return;
    
    this.animating = true;
    this.isOpen = false;
    
    // Update ARIA
    this.button.setAttribute('aria-expanded', 'false');
    this.backdrop.setAttribute('aria-hidden', 'true');
    
    // Restore body scroll
    document.body.style.overflow = '';
    
    // Animate hamburger icon back
    this.animateHamburgerIcon(false);
    
    if (!animated) {
      gsap.set(this.backdrop, { opacity: 0, pointerEvents: 'none' });
      gsap.set(this.menu, { x: '100%' });
      this.animating = false;
      return;
    }
    
    // Animation timeline
    const tl = gsap.timeline({
      onComplete: () => {
        this.animating = false;
        this.button.focus();
      }
    });
    
    // Menu slide out
    tl.to(this.menu, {
      x: '100%',
      duration: 0.3,
      ease: 'power3.in'
    });
    
    // Backdrop fade out
    tl.to(this.backdrop, {
      opacity: 0,
      pointerEvents: 'none',
      duration: 0.2,
      ease: 'power2.in'
    }, '-=0.1');
  }
  
  animateHamburgerIcon(toX) {
    const icon = this.button.querySelector('svg');
    if (!icon) return;
    
    const paths = icon.querySelectorAll('path');
    if (paths.length === 0) return;
    
    if (toX) {
      // Transform to X
      gsap.to(paths[0], {
        attr: { d: 'M6 6l12 12' },
        duration: 0.3,
        ease: 'power2.inOut'
      });
      gsap.to(paths[1], {
        opacity: 0,
        duration: 0.2
      });
      gsap.to(paths[2], {
        attr: { d: 'M18 6L6 18' },
        duration: 0.3,
        ease: 'power2.inOut'
      });
    } else {
      // Transform back to hamburger
      gsap.to(paths[0], {
        attr: { d: 'M4 6h16' },
        duration: 0.3,
        ease: 'power2.inOut'
      });
      gsap.to(paths[1], {
        opacity: 1,
        duration: 0.2
      });
      gsap.to(paths[2], {
        attr: { d: 'M4 18h16' },
        duration: 0.3,
        ease: 'power2.inOut'
      });
    }
  }
}

// Initialize when DOM is ready and GSAP is loaded
function initHamburgerMenu() {
  if (typeof gsap === 'undefined') {
    console.warn('[Hamburger Menu] GSAP not loaded, using fallback');
    return;
  }
  
  new HamburgerMenu();
}

// Auto-initialize
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initHamburgerMenu);
} else {
  initHamburgerMenu();
}
