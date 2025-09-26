/**
 * Modern UI Interactions & Micro-animations
 * Enhances user experience with smooth interactions and visual feedback
 */

class ModernUIInteractions {
    constructor() {
        this.observers = new Map();
        this.isInitialized = false;
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        console.log('🎨 Initializing modern UI interactions...');
        
        this.setupScrollEffects();
        this.setupHoverEffects();
        this.setupClickEffects();
        this.setupNavigationEffects();
        this.setupFormInteractions();
        this.setupToastSystem();
        this.setupLoadingStates();
        this.setupProgressIndicators();
        this.setupParallaxEffects();
        
        this.isInitialized = true;
        console.log('✅ Modern UI interactions initialized');
    }
    
    setupScrollEffects() {
        // Navbar scroll effect
        const navbar = document.querySelector('.mina-navbar');
        if (navbar) {
            let lastScrollY = window.scrollY;
            
            const handleScroll = () => {
                const currentScrollY = window.scrollY;
                
                if (currentScrollY > 50) {
                    navbar.classList.add('mina-navbar-scrolled');
                } else {
                    navbar.classList.remove('mina-navbar-scrolled');
                }
                
                // Hide/show navbar on scroll
                if (currentScrollY > lastScrollY && currentScrollY > 100) {
                    navbar.style.transform = 'translateY(-100%)';
                } else {
                    navbar.style.transform = 'translateY(0)';
                }
                
                lastScrollY = currentScrollY;
            };
            
            window.addEventListener('scroll', this.throttle(handleScroll, 16));
        }
        
        // Parallax scroll effects
        this.setupParallaxScrolling();
        
        // Reveal animations on scroll
        this.setupScrollRevealAnimations();
    }
    
    setupParallaxScrolling() {
        const parallaxElements = document.querySelectorAll('[data-parallax]');
        
        if (parallaxElements.length === 0) return;
        
        const handleParallax = () => {
            const scrolled = window.pageYOffset;
            
            parallaxElements.forEach(element => {
                const rate = scrolled * -0.5;
                element.style.transform = `translateY(${rate}px)`;
            });
        };
        
        window.addEventListener('scroll', this.throttle(handleParallax, 16));
    }
    
    setupScrollRevealAnimations() {
        // Create intersection observer for reveal animations
        const revealObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('mina-revealed');
                    revealObserver.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        // Add reveal animation styles
        this.addRevealStyles();
        
        // Observe elements for reveal animations
        const revealElements = document.querySelectorAll('.mina-card, .mina-stat-card, .mina-metric-card');
        revealElements.forEach(element => {
            element.classList.add('mina-reveal');
            revealObserver.observe(element);
        });
        
        this.observers.set('reveal', revealObserver);
    }
    
    addRevealStyles() {
        if (document.getElementById('reveal-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'reveal-styles';
        styles.textContent = `
            .mina-reveal {
                opacity: 0;
                transform: translateY(30px);
                transition: opacity 0.6s ease, transform 0.6s ease;
            }
            
            .mina-revealed {
                opacity: 1;
                transform: translateY(0);
            }
            
            .mina-reveal:nth-child(2) { transition-delay: 0.1s; }
            .mina-reveal:nth-child(3) { transition-delay: 0.2s; }
            .mina-reveal:nth-child(4) { transition-delay: 0.3s; }
            .mina-reveal:nth-child(5) { transition-delay: 0.4s; }
            .mina-reveal:nth-child(6) { transition-delay: 0.5s; }
        `;
        document.head.appendChild(styles);
    }
    
    setupHoverEffects() {
        // Enhanced card hover effects
        const cards = document.querySelectorAll('.mina-card, .mina-stat-card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', this.handleCardHover);
            card.addEventListener('mouseleave', this.handleCardLeave);
        });
        
        // Button hover effects
        const buttons = document.querySelectorAll('.mina-btn');
        buttons.forEach(button => {
            this.addButtonRippleEffect(button);
        });
        
        // Interactive elements glow effect
        this.setupGlowEffects();
    }
    
    handleCardHover(event) {
        const card = event.currentTarget;
        const rect = card.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        // Create glow effect at cursor position
        const glow = document.createElement('div');
        glow.style.cssText = `
            position: absolute;
            top: ${y}px;
            left: ${x}px;
            width: 100px;
            height: 100px;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.2) 0%, transparent 70%);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            pointer-events: none;
            z-index: 1;
        `;
        
        card.style.position = 'relative';
        card.appendChild(glow);
        
        // Remove glow after animation
        setTimeout(() => {
            if (glow.parentNode) {
                glow.remove();
            }
        }, 1000);
    }
    
    handleCardLeave(event) {
        // Additional leave effects can be added here
    }
    
    setupGlowEffects() {
        const glowElements = document.querySelectorAll('[data-glow]');
        
        glowElements.forEach(element => {
            element.addEventListener('mousemove', (e) => {
                const rect = element.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / rect.width) * 100;
                const y = ((e.clientY - rect.top) / rect.height) * 100;
                
                element.style.background = `
                    radial-gradient(circle at ${x}% ${y}%, 
                    rgba(59, 130, 246, 0.1) 0%, 
                    transparent 50%),
                    ${element.dataset.originalBackground || 'var(--mina-neutral-0)'}
                `;
            });
            
            element.addEventListener('mouseleave', () => {
                element.style.background = element.dataset.originalBackground || 'var(--mina-neutral-0)';
            });
        });
    }
    
    addButtonRippleEffect(button) {
        button.addEventListener('click', (e) => {
            const rect = button.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                top: ${y}px;
                left: ${x}px;
                width: 0;
                height: 0;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.6);
                transform: translate(-50%, -50%);
                animation: mina-ripple 0.6s linear;
                pointer-events: none;
                z-index: 1;
            `;
            
            button.style.position = 'relative';
            button.style.overflow = 'hidden';
            button.appendChild(ripple);
            
            // Add ripple animation if not exists
            if (!document.getElementById('ripple-styles')) {
                const rippleStyles = document.createElement('style');
                rippleStyles.id = 'ripple-styles';
                rippleStyles.textContent = `
                    @keyframes mina-ripple {
                        to {
                            width: 300px;
                            height: 300px;
                            opacity: 0;
                        }
                    }
                `;
                document.head.appendChild(rippleStyles);
            }
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    }
    
    setupClickEffects() {
        // Smooth scroll for anchor links
        const anchorLinks = document.querySelectorAll('a[href^="#"]');
        anchorLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(link.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
        
        // Click feedback for interactive elements
        const interactive = document.querySelectorAll('.mina-btn, .mina-card-interactive');
        interactive.forEach(element => {
            element.addEventListener('mousedown', () => {
                element.style.transform = 'scale(0.98)';
            });
            
            element.addEventListener('mouseup', () => {
                element.style.transform = '';
            });
            
            element.addEventListener('mouseleave', () => {
                element.style.transform = '';
            });
        });
    }
    
    setupNavigationEffects() {
        // Mobile navigation toggle
        const navToggle = document.querySelector('.mina-navbar-toggle');
        const navMenu = document.querySelector('.mina-navbar-nav');
        
        if (navToggle && navMenu) {
            navToggle.addEventListener('click', () => {
                navToggle.classList.toggle('active');
                navMenu.classList.toggle('active');
                
                // Prevent body scroll when menu is open
                document.body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
            });
            
            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                    navToggle.classList.remove('active');
                    navMenu.classList.remove('active');
                    document.body.style.overflow = '';
                }
            });
        }
        
        // Active navigation highlighting
        this.updateActiveNavigation();
    }
    
    updateActiveNavigation() {
        const navLinks = document.querySelectorAll('.mina-navbar-nav-link');
        const currentPath = window.location.pathname;
        
        navLinks.forEach(link => {
            const linkPath = new URL(link.href).pathname;
            if (linkPath === currentPath || (currentPath !== '/' && linkPath.includes(currentPath))) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }
    
    setupFormInteractions() {
        // Enhanced form focus effects
        const inputs = document.querySelectorAll('.mina-input, input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('focus', () => {
                input.closest('.mina-form-group')?.classList.add('focused');
            });
            
            input.addEventListener('blur', () => {
                input.closest('.mina-form-group')?.classList.remove('focused');
            });
            
            // Real-time validation feedback
            input.addEventListener('input', () => {
                this.validateField(input);
            });
        });
        
        // Add floating label effects
        this.setupFloatingLabels();
    }
    
    setupFloatingLabels() {
        const formGroups = document.querySelectorAll('.mina-form-group');
        
        formGroups.forEach(group => {
            const input = group.querySelector('input, textarea, select');
            const label = group.querySelector('.mina-label');
            
            if (input && label && !group.classList.contains('floating-setup')) {
                group.classList.add('floating-setup');
                
                const checkFloat = () => {
                    if (input.value || input === document.activeElement) {
                        label.classList.add('floating');
                    } else {
                        label.classList.remove('floating');
                    }
                };
                
                input.addEventListener('focus', checkFloat);
                input.addEventListener('blur', checkFloat);
                input.addEventListener('input', checkFloat);
                
                // Initial check
                checkFloat();
            }
        });
        
        // Add floating label styles
        if (!document.getElementById('floating-label-styles')) {
            const styles = document.createElement('style');
            styles.id = 'floating-label-styles';
            styles.textContent = `
                .mina-form-group.floating-setup {
                    position: relative;
                    margin-top: 1.5rem;
                }
                
                .mina-form-group.floating-setup .mina-label {
                    position: absolute;
                    top: 50%;
                    left: 1rem;
                    transform: translateY(-50%);
                    transition: all 0.2s ease;
                    background: var(--mina-neutral-0);
                    padding: 0 0.5rem;
                    pointer-events: none;
                }
                
                .mina-form-group.floating-setup .mina-label.floating {
                    top: 0;
                    transform: translateY(-50%);
                    font-size: 0.75rem;
                    color: var(--mina-primary-600);
                }
                
                .mina-form-group.focused .mina-label {
                    color: var(--mina-primary-600);
                }
            `;
            document.head.appendChild(styles);
        }
    }
    
    validateField(input) {
        // Basic validation feedback
        const formGroup = input.closest('.mina-form-group');
        if (!formGroup) return;
        
        // Remove previous validation classes
        input.classList.remove('mina-input-error', 'mina-input-success');
        
        // Basic validation rules
        let isValid = true;
        
        if (input.required && !input.value.trim()) {
            isValid = false;
        }
        
        if (input.type === 'email' && input.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            isValid = emailRegex.test(input.value);
        }
        
        // Apply validation styling
        if (input.value.trim()) {
            input.classList.add(isValid ? 'mina-input-success' : 'mina-input-error');
        }
    }
    
    setupToastSystem() {
        // Create toast container if it doesn't exist
        if (!document.querySelector('.mina-toast-container')) {
            const container = document.createElement('div');
            container.className = 'mina-toast-container';
            document.body.appendChild(container);
        }
        
        // Global toast function
        window.showToast = (message, type = 'info', title = '', duration = 5000) => {
            this.showToast(message, type, title, duration);
        };
    }
    
    showToast(message, type = 'info', title = '', duration = 5000) {
        const container = document.querySelector('.mina-toast-container');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `mina-toast mina-toast-${type}`;
        
        const icons = {
            success: 'bi-check-circle-fill',
            error: 'bi-x-circle-fill',
            warning: 'bi-exclamation-triangle-fill',
            info: 'bi-info-circle-fill'
        };
        
        toast.innerHTML = `
            <div class="mina-toast-icon">
                <i class="bi ${icons[type] || icons.info}"></i>
            </div>
            <div class="mina-toast-content">
                ${title ? `<div class="mina-toast-title">${title}</div>` : ''}
                <div class="mina-toast-message">${message}</div>
            </div>
            <button class="mina-toast-close" aria-label="Close notification">
                <i class="bi bi-x"></i>
            </button>
            <div class="mina-toast-progress"></div>
        `;
        
        // Add event listeners
        const closeBtn = toast.querySelector('.mina-toast-close');
        closeBtn.addEventListener('click', () => this.removeToast(toast));
        
        container.appendChild(toast);
        
        // Auto-remove after duration
        setTimeout(() => {
            this.removeToast(toast);
        }, duration);
    }
    
    removeToast(toast) {
        toast.classList.add('removing');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }
    
    setupLoadingStates() {
        // Add loading states to buttons and forms
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn) {
                    this.setLoadingState(submitBtn, true);
                }
            });
        });
        
        // Global loading state functions
        window.setLoadingState = (element, loading) => this.setLoadingState(element, loading);
    }
    
    setLoadingState(element, loading) {
        if (loading) {
            element.disabled = true;
            element.dataset.originalText = element.textContent;
            element.innerHTML = '<span class="mina-spinner"></span> Loading...';
            element.classList.add('loading');
        } else {
            element.disabled = false;
            element.textContent = element.dataset.originalText || 'Submit';
            element.classList.remove('loading');
            delete element.dataset.originalText;
        }
    }
    
    setupProgressIndicators() {
        // Animated progress bars
        const progressBars = document.querySelectorAll('[data-progress]');
        
        const progressObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const bar = entry.target;
                    const progress = bar.dataset.progress;
                    
                    bar.style.width = '0%';
                    setTimeout(() => {
                        bar.style.transition = 'width 1s ease-out';
                        bar.style.width = progress + '%';
                    }, 100);
                    
                    progressObserver.unobserve(bar);
                }
            });
        });
        
        progressBars.forEach(bar => {
            progressObserver.observe(bar);
        });
        
        this.observers.set('progress', progressObserver);
    }
    
    setupParallaxEffects() {
        // Smooth parallax scrolling for hero sections
        const heroElements = document.querySelectorAll('.mina-hero');
        
        heroElements.forEach(hero => {
            const handleParallax = () => {
                const scrolled = window.pageYOffset;
                const rate = scrolled * -0.2;
                
                hero.style.transform = `translateY(${rate}px)`;
            };
            
            window.addEventListener('scroll', this.throttle(handleParallax, 16));
        });
    }
    
    // Utility functions
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    debounce(func, delay) {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }
    
    // Public API
    addRevealAnimation(element) {
        element.classList.add('mina-reveal');
        this.observers.get('reveal')?.observe(element);
    }
    
    removeAllToasts() {
        const toasts = document.querySelectorAll('.mina-toast');
        toasts.forEach(toast => this.removeToast(toast));
    }
    
    updateProgress(element, progress) {
        element.style.width = Math.min(100, Math.max(0, progress)) + '%';
    }
    
    destroy() {
        // Clean up observers
        this.observers.forEach(observer => observer.disconnect());
        this.observers.clear();
        
        // Remove event listeners
        window.removeEventListener('scroll', this.handleScroll);
        
        this.isInitialized = false;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎨 Initializing modern UI interactions...');
    window.modernUI = new ModernUIInteractions();
    
    // Global access for debugging
    window.getUIInteractions = () => window.modernUI;
    
    console.log('✅ Modern UI interactions ready');
});

// Update navigation on page changes (for SPAs)
window.addEventListener('popstate', () => {
    if (window.modernUI) {
        window.modernUI.updateActiveNavigation();
    }
});