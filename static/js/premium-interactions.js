/* =============================================== */
/* PREMIUM INTERACTION SYSTEM - MEMORY SAFE      */
/* Emergency Fix: Singleton + Proper Cleanup     */
/* =============================================== */

(function() {
    'use strict';
    
    // Singleton guard - prevent multiple initializations
    if (window.__premiumInteractionsInitialized) {
        return;
    }
    
    class PremiumInteractions {
        constructor() {
            this.observers = [];
            this.listeners = new Map();
            this.styleId = 'premium-interactions-styles';
            this.animationFrames = new Set();
            this.timeouts = new Set();
            this.isDestroyed = false;
            
            // Only initialize if not already initialized
            if (!document.body.hasAttribute('data-premium-init')) {
                this.initializeIdempotent();
            }
        }
        
        initializeIdempotent() {
            // Mark as initialized to prevent duplicate initialization
            document.body.setAttribute('data-premium-init', 'true');
            
            // Setup with proper cleanup patterns
            this.setupStyles();
            this.setupEventDelegation();
            this.setupIntersectionObserver();
            this.setupLiveIndicators();
            this.setupCleanupListeners();
            
            console.log('🎯 Premium Interactions initialized (singleton)');
        }
        
        // Setup styles once with proper ID checking
        setupStyles() {
            if (document.getElementById(this.styleId)) return;
            
            const style = document.createElement('style');
            style.id = this.styleId;
            style.textContent = `
                @keyframes ripple {
                    to {
                        width: 200px;
                        height: 200px;
                        opacity: 0;
                    }
                }
                
                @keyframes sparkle {
                    0% {
                        opacity: 0;
                        transform: translateY(0) rotate(0deg);
                    }
                    50% {
                        opacity: 1;
                    }
                    100% {
                        opacity: 0;
                        transform: translateY(-20px) rotate(180deg);
                    }
                }
                
                @keyframes fadeInUp {
                    0% {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    100% {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                
                @keyframes pulse {
                    0%, 100% {
                        opacity: 1;
                    }
                    50% {
                        opacity: 0.5;
                    }
                }
                
                .animate-in {
                    animation: fadeInUp 0.8s cubic-bezier(0.4, 0, 0.2, 1) both;
                }
            `;
            document.head.appendChild(style);
        }
        
        // Use event delegation instead of individual listeners
        setupEventDelegation() {
            const clickHandler = (e) => {
                if (this.isDestroyed) return;
                
                if (e.target.matches('.btn') || e.target.closest('.btn')) {
                    this.handleButtonClick(e);
                }
            };
            
            const mouseEnterHandler = (e) => {
                if (this.isDestroyed) return;
                
                if (e.target.matches('.btn') || e.target.closest('.btn')) {
                    this.handleButtonHover(e);
                } else if (e.target.matches('.stat-card, .content-section') || e.target.closest('.stat-card, .content-section')) {
                    this.handleCardHover(e);
                }
            };
            
            const mouseLeaveHandler = (e) => {
                if (this.isDestroyed) return;
                
                if (e.target.matches('.stat-card, .content-section') || e.target.closest('.stat-card, .content-section')) {
                    this.handleCardLeave(e);
                }
            };
            
            document.addEventListener('click', clickHandler);
            document.addEventListener('mouseenter', mouseEnterHandler, true);
            document.addEventListener('mouseleave', mouseLeaveHandler, true);
            
            // Store handlers for cleanup
            this.listeners.set('click', clickHandler);
            this.listeners.set('mouseenter', mouseEnterHandler);
            this.listeners.set('mouseleave', mouseLeaveHandler);
        }
        
        // Setup intersection observer with proper cleanup
        setupIntersectionObserver() {
            const observer = new IntersectionObserver((entries) => {
                if (this.isDestroyed) return;
                
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate-in');
                    }
                });
            }, { threshold: 0.1 });
            
            // Observe elements that should animate in
            const animatedElements = document.querySelectorAll(
                '.stat-card:not([data-observed]), .content-section:not([data-observed]), .dashboard-header:not([data-observed])'
            );
            
            animatedElements.forEach(el => {
                observer.observe(el);
                el.setAttribute('data-observed', 'true');
            });
            
            this.observers.push(observer);
        }
        
        // Setup live indicators idempotently
        setupLiveIndicators() {
            const liveElements = document.querySelectorAll('.status-live:not([data-live-enhanced])');
            
            liveElements.forEach(element => {
                // Check if dot already exists
                if (element.querySelector('.live-dot')) return;
                
                const dot = document.createElement('span');
                dot.className = 'live-dot';
                dot.style.cssText = `
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    background: #10b981;
                    border-radius: 50%;
                    margin-right: 6px;
                    animation: pulse 2s infinite;
                `;
                
                element.insertBefore(dot, element.firstChild);
                element.setAttribute('data-live-enhanced', 'true');
            });
        }
        
        // Event handlers with proper cleanup
        handleButtonClick(e) {
            const button = e.target.closest('.btn');
            if (!button) return;
            
            button.style.transform = 'scale(0.95)';
            const timeout = setTimeout(() => {
                if (!this.isDestroyed) {
                    button.style.transform = '';
                }
            }, 150);
            this.timeouts.add(timeout);
        }
        
        handleButtonHover(e) {
            const button = e.target.closest('.btn');
            if (!button) return;
            
            this.createRippleEffect(e, button);
        }
        
        createRippleEffect(e, button) {
            const rect = button.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.className = 'ripple-effect';
            ripple.style.cssText = `
                position: absolute;
                left: ${x}px;
                top: ${y}px;
                width: 0;
                height: 0;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.3);
                transform: translate(-50%, -50%);
                animation: ripple 0.6s ease-out;
                pointer-events: none;
                z-index: 10;
            `;
            
            button.style.position = 'relative';
            button.appendChild(ripple);
            
            const timeout = setTimeout(() => {
                if (ripple.parentNode) {
                    ripple.remove();
                }
            }, 600);
            this.timeouts.add(timeout);
        }
        
        handleCardHover(e) {
            const card = e.target.closest('.stat-card, .content-section');
            if (!card) return;
            
            const rect = card.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            const mouseX = e.clientX;
            const mouseY = e.clientY;
            
            const rotateX = (mouseY - centerY) / 10;
            const rotateY = (centerX - mouseX) / 10;
            
            card.style.transform = `
                translateY(-8px) 
                scale(1.02) 
                rotateX(${rotateX}deg) 
                rotateY(${rotateY}deg)
                perspective(1000px)
            `;
        }
        
        handleCardLeave(e) {
            const card = e.target.closest('.stat-card, .content-section');
            if (!card) return;
            
            card.style.transform = '';
        }
        
        // Animate stat counters with cleanup
        animateStatCounters() {
            const statValues = document.querySelectorAll('.stat-value:not([data-animated])');
            
            statValues.forEach(stat => {
                const finalValue = stat.textContent;
                const isPercentage = finalValue.includes('%');
                const numericValue = parseInt(finalValue.replace(/[^\d]/g, ''));
                
                if (numericValue > 0) {
                    this.animateCounter(stat, 0, numericValue, isPercentage ? '%' : '');
                    stat.setAttribute('data-animated', 'true');
                }
            });
        }
        
        animateCounter(element, start, end, suffix = '') {
            const duration = 2000;
            const startTime = performance.now();
            
            const animate = (currentTime) => {
                if (this.isDestroyed) return;
                
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                const easeOutQuart = 1 - Math.pow(1 - progress, 4);
                const current = Math.round(start + (end - start) * easeOutQuart);
                
                element.textContent = current + suffix;
                
                if (progress < 1) {
                    const frameId = requestAnimationFrame(animate);
                    this.animationFrames.add(frameId);
                } else {
                    this.addSparkleEffect(element);
                }
            };
            
            const frameId = requestAnimationFrame(animate);
            this.animationFrames.add(frameId);
        }
        
        addSparkleEffect(element) {
            if (this.isDestroyed) return;
            
            const sparkle = document.createElement('span');
            sparkle.innerHTML = '✨';
            sparkle.style.cssText = `
                position: absolute;
                font-size: 20px;
                animation: sparkle 1s ease-out forwards;
                pointer-events: none;
            `;
            
            element.style.position = 'relative';
            element.appendChild(sparkle);
            
            const timeout = setTimeout(() => {
                if (sparkle.parentNode) {
                    sparkle.remove();
                }
            }, 1000);
            this.timeouts.add(timeout);
        }
        
        // Setup cleanup listeners
        setupCleanupListeners() {
            const cleanup = () => this.destroy();
            
            window.addEventListener('beforeunload', cleanup);
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    this.pauseAnimations();
                } else {
                    this.resumeAnimations();
                }
            });
        }
        
        pauseAnimations() {
            // Pause heavy animations when page is hidden
            const elements = document.querySelectorAll('.animate-in');
            elements.forEach(el => {
                el.style.animationPlayState = 'paused';
            });
        }
        
        resumeAnimations() {
            // Resume animations when page is visible
            const elements = document.querySelectorAll('.animate-in');
            elements.forEach(el => {
                el.style.animationPlayState = 'running';
            });
        }
        
        // Comprehensive cleanup method
        destroy() {
            if (this.isDestroyed) return;
            this.isDestroyed = true;
            
            // Clear all observers
            this.observers.forEach(observer => observer.disconnect());
            this.observers.length = 0;
            
            // Remove all event listeners
            this.listeners.forEach((handler, event) => {
                document.removeEventListener(event, handler, event === 'mouseenter' || event === 'mouseleave');
            });
            this.listeners.clear();
            
            // Cancel all animation frames
            this.animationFrames.forEach(frameId => cancelAnimationFrame(frameId));
            this.animationFrames.clear();
            
            // Clear all timeouts
            this.timeouts.forEach(timeoutId => clearTimeout(timeoutId));
            this.timeouts.clear();
            
            // Remove styles
            const styleEl = document.getElementById(this.styleId);
            if (styleEl) styleEl.remove();
            
            // Reset body attribute
            document.body.removeAttribute('data-premium-init');
            
            console.log('🧹 Premium Interactions cleaned up');
        }
        
        // Initialize stat counters if needed
        initializeCounters() {
            this.animateStatCounters();
        }
    }
    
    // Create singleton instance
    let premiumInteractions = null;
    
    function initialize() {
        if (!premiumInteractions) {
            premiumInteractions = new PremiumInteractions();
            window.__premiumInteractions = premiumInteractions;
            
            // Initialize counters after a brief delay to ensure DOM is ready
            setTimeout(() => {
                if (premiumInteractions && !premiumInteractions.isDestroyed) {
                    premiumInteractions.initializeCounters();
                }
            }, 100);
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
    // Mark as initialized globally
    window.__premiumInteractionsInitialized = true;
    
})();