/* =============================================== */
/* PREMIUM INTERACTION SYSTEM                    */
/* =============================================== */

class PremiumInteractions {
    constructor() {
        this.init();
    }

    init() {
        this.setupStatCounters();
        this.setupButtonEffects();
        this.setupCardInteractions();
        this.setupLiveIndicators();
        this.setupProgressiveLoading();
        
        console.log('🎯 Premium Interactions initialized');
    }

    // Animated stat counters
    setupStatCounters() {
        const statValues = document.querySelectorAll('.stat-value');
        
        statValues.forEach(stat => {
            const finalValue = stat.textContent;
            const isPercentage = finalValue.includes('%');
            const numericValue = parseInt(finalValue.replace(/[^\d]/g, ''));
            
            if (numericValue > 0) {
                this.animateCounter(stat, 0, numericValue, isPercentage ? '%' : '');
            }
        });
    }

    animateCounter(element, start, end, suffix = '') {
        const duration = 2000;
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function for smooth animation
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const current = Math.round(start + (end - start) * easeOutQuart);
            
            element.textContent = current + suffix;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    // Enhanced button interactions
    setupButtonEffects() {
        const buttons = document.querySelectorAll('.btn');
        
        buttons.forEach(button => {
            button.addEventListener('mouseenter', this.createRippleEffect.bind(this));
            button.addEventListener('click', this.createClickEffect.bind(this));
        });
    }

    createRippleEffect(e) {
        const button = e.currentTarget;
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
        
        setTimeout(() => ripple.remove(), 600);
    }

    createClickEffect(e) {
        const button = e.currentTarget;
        button.style.transform = 'scale(0.95)';
        setTimeout(() => {
            button.style.transform = '';
        }, 150);
    }

    // Enhanced card interactions
    setupCardInteractions() {
        const cards = document.querySelectorAll('.stat-card, .content-section');
        
        cards.forEach(card => {
            card.addEventListener('mouseenter', this.enhanceCardHover.bind(this));
            card.addEventListener('mouseleave', this.resetCardHover.bind(this));
        });
    }

    enhanceCardHover(e) {
        const card = e.currentTarget;
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

    resetCardHover(e) {
        const card = e.currentTarget;
        card.style.transform = '';
    }

    // Live status indicators
    setupLiveIndicators() {
        const liveElements = document.querySelectorAll('.status-live');
        
        liveElements.forEach(element => {
            // Add pulsing dot
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
        });
    }

    // Progressive loading animations
    setupProgressiveLoading() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, { threshold: 0.1 });

        // Observe elements that should animate in
        const animatedElements = document.querySelectorAll(
            '.stat-card, .content-section, .dashboard-header'
        );
        
        animatedElements.forEach(el => observer.observe(el));
    }

    // Add sparkle effect to stat values
    addSparkleEffect(element) {
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
        
        setTimeout(() => sparkle.remove(), 1000);
    }
}

// CSS for ripple and sparkle animations
const style = document.createElement('style');
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
    
    .animate-in {
        animation: fadeInUp 0.8s cubic-bezier(0.4, 0, 0.2, 1) both;
    }
`;
document.head.appendChild(style);

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new PremiumInteractions();
    });
} else {
    new PremiumInteractions();
}