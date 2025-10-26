/**
 * Enhanced Page Transitions - GSAP + View Transitions API
 * Premium navigation with skeleton screens and smooth GSAP animations
 */

class EnhancedPageTransitions extends PageTransitionManager {
  constructor() {
    super();
    this.skeletonEnabled = true;
    this.gsapAvailable = typeof gsap !== 'undefined';
    
    if (!this.gsapAvailable) {
      console.warn('[Page Transitions] GSAP not available, using fallback');
    }
  }
  
  async performViewTransition(url) {
    if (!this.gsapAvailable) {
      return super.performViewTransition(url);
    }
    
    // Show skeleton screen
    this.showSkeletonScreen();
    
    const transition = document.startViewTransition(async () => {
      await this.updatePage(url);
    });
    
    await transition.ready;
    
    // Animate content in with GSAP
    this.animateContentIn();
    
    await transition.finished;
    
    this.hideSkeletonScreen();
    
    return transition.finished;
  }
  
  async performFallbackTransition(url) {
    if (!this.gsapAvailable) {
      return super.performFallbackTransition(url);
    }
    
    // GSAP-powered fallback
    this.showSkeletonScreen();
    
    // Fade out current content - only if it exists
    const mainContent = document.querySelector('#main-content');
    if (mainContent) {
      await gsap.to('#main-content', {
        opacity: 0,
        y: -20,
        duration: 0.2,
        ease: 'power2.in'
      });
    }
    
    // Update page content
    await this.updatePage(url);
    
    // Animate new content in
    await this.animateContentIn();
    
    this.hideSkeletonScreen();
  }
  
  animateContentIn() {
    if (!this.gsapAvailable) return Promise.resolve();
    
    const main = document.querySelector('#main-content');
    if (!main) return Promise.resolve();
    
    // Reset position
    gsap.set(main, { opacity: 0, y: 20 });
    
    // Fade in main content
    const tl = gsap.timeline();
    
    tl.to(main, {
      opacity: 1,
      y: 0,
      duration: 0.4,
      ease: 'power3.out'
    });
    
    // Stagger in cards and sections - only if they exist
    const cards = Array.from(main.querySelectorAll('.card, .card-glass, .metric-card'));
    if (cards && cards.length > 0) {
      tl.from(cards, {
        opacity: 0,
        y: 30,
        stagger: 0.05,
        duration: 0.4,
        ease: 'power2.out'
      }, '-=0.3');
    }
    
    // Animate page title - only if it exists
    const pageTitle = main.querySelector('h1, .page-title');
    if (pageTitle) {
      tl.from(pageTitle, {
        opacity: 0,
        x: -20,
        duration: 0.5,
        ease: 'power3.out'
      }, '-=0.4');
    }
    
    return tl.then();
  }
  
  showSkeletonScreen() {
    if (!this.skeletonEnabled) return;
    
    const skeleton = document.createElement('div');
    skeleton.className = 'skeleton-screen';
    skeleton.innerHTML = `
      <div class="skeleton-container">
        <div class="skeleton-header">
          <div class="skeleton-title"></div>
          <div class="skeleton-subtitle"></div>
        </div>
        <div class="skeleton-grid">
          <div class="skeleton-card"></div>
          <div class="skeleton-card"></div>
          <div class="skeleton-card"></div>
          <div class="skeleton-card"></div>
        </div>
      </div>
    `;
    
    document.body.appendChild(skeleton);
    
    if (this.gsapAvailable) {
      gsap.from(skeleton, {
        opacity: 0,
        duration: 0.2,
        ease: 'power2.out'
      });
    }
  }
  
  hideSkeletonScreen() {
    const skeleton = document.querySelector('.skeleton-screen');
    if (!skeleton) return;
    
    if (this.gsapAvailable) {
      gsap.to(skeleton, {
        opacity: 0,
        duration: 0.3,
        ease: 'power2.in',
        onComplete: () => skeleton.remove()
      });
    } else {
      skeleton.remove();
    }
  }
  
  showLoadingState() {
    document.documentElement.classList.add('page-loading');
    
    const loader = document.createElement('div');
    loader.className = 'page-transition-loader';
    loader.innerHTML = `<div class="loader-bar"></div>`;
    document.body.appendChild(loader);
    
    if (this.gsapAvailable) {
      const bar = loader.querySelector('.loader-bar');
      gsap.fromTo(bar, 
        { width: '0%' },
        { width: '100%', duration: 0.5, ease: 'power2.out' }
      );
    }
  }
}

// Enhanced CSS for skeleton screens
const enhancedStyles = `
/* Skeleton Screen Styles */
.skeleton-screen {
  position: fixed;
  inset: 0;
  background: var(--color-bg-base);
  z-index: var(--z-modal);
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.skeleton-container {
  width: 100%;
  max-width: var(--container-max-width);
  padding: var(--space-8);
}

.skeleton-header {
  margin-bottom: var(--space-8);
}

.skeleton-title {
  width: 40%;
  height: 48px;
  background: var(--glass-bg);
  border-radius: var(--radius-xl);
  margin-bottom: var(--space-4);
  position: relative;
  overflow: hidden;
}

.skeleton-subtitle {
  width: 30%;
  height: 24px;
  background: var(--glass-bg);
  border-radius: var(--radius-lg);
  position: relative;
  overflow: hidden;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-6);
}

.skeleton-card {
  height: 200px;
  background: var(--glass-bg);
  border-radius: var(--radius-2xl);
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

/* Shimmer animation */
.skeleton-title::before,
.skeleton-subtitle::before,
.skeleton-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.1),
    transparent
  );
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
}

/* Enhanced loading bar */
.page-transition-loader {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: var(--z-tooltip);
  background: transparent;
}

.loader-bar {
  height: 100%;
  background: var(--gradient-primary);
  width: 0%;
  box-shadow: 0 0 10px var(--color-primary);
  border-radius: 0 var(--radius-full) var(--radius-full) 0;
}

/* Mobile optimizations */
@media (max-width: 768px) {
  .skeleton-grid {
    grid-template-columns: 1fr;
  }
  
  .skeleton-title {
    width: 60%;
  }
  
  .skeleton-subtitle {
    width: 45%;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .skeleton-title::before,
  .skeleton-subtitle::before,
  .skeleton-card::before {
    animation: none !important;
  }
}
`;

// Inject enhanced styles
const enhancedStyleSheet = document.createElement('style');
enhancedStyleSheet.textContent = enhancedStyles;
document.head.appendChild(enhancedStyleSheet);

// Only initialize if GSAP is available and this hasn't been initialized yet
if (typeof gsap !== 'undefined' && !window.pageTransitionsInitialized) {
  window.pageTransitionsInitialized = true;
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      new EnhancedPageTransitions();
    });
  } else {
    new EnhancedPageTransitions();
  }
}

window.EnhancedPageTransitions = EnhancedPageTransitions;
