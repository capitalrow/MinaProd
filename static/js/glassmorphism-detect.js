/**
 * Glassmorphism Feature Detection
 * Adds .glass-supported class to <html> if backdrop-filter is supported
 * Crown+ Premium - Mobile Compatibility Layer
 */

(function() {
  'use strict';
  
  /**
   * Test if backdrop-filter is supported
   */
  function supportsBackdropFilter() {
    // Test various prefixes
    const testElement = document.createElement('div');
    const prefixes = ['', '-webkit-', '-moz-', '-ms-', '-o-'];
    
    for (const prefix of prefixes) {
      const property = prefix + 'backdrop-filter';
      testElement.style[property] = 'blur(2px)';
      
      if (testElement.style[property]) {
        return true;
      }
    }
    
    // CSS.supports API fallback
    if (typeof CSS !== 'undefined' && CSS.supports) {
      return (
        CSS.supports('backdrop-filter', 'blur(2px)') ||
        CSS.supports('-webkit-backdrop-filter', 'blur(2px)')
      );
    }
    
    return false;
  }
  
  /**
   * Initialize feature detection
   */
  function init() {
    const html = document.documentElement;
    
    if (supportsBackdropFilter()) {
      html.classList.add('glass-supported');
      
      // Store in sessionStorage for future checks
      try {
        sessionStorage.setItem('glassSupported', 'true');
      } catch (e) {
        // Ignore storage errors
      }
      
      console.log('[Glassmorphism] ✓ Backdrop filter supported');
    } else {
      html.classList.add('glass-not-supported');
      
      try {
        sessionStorage.setItem('glassSupported', 'false');
      } catch (e) {
        // Ignore storage errors
      }
      
      console.log('[Glassmorphism] ✗ Backdrop filter not supported - using fallback');
    }
    
    // Detect performance preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const prefersReducedTransparency = window.matchMedia('(prefers-reduced-transparency: reduce)').matches;
    
    if (prefersReducedMotion) {
      html.classList.add('reduced-motion');
      console.log('[Accessibility] Reduced motion detected');
    }
    
    if (prefersReducedTransparency) {
      html.classList.add('reduced-transparency');
      console.log('[Accessibility] Reduced transparency detected');
    }
    
    // Detect touch capability
    const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    if (hasTouch) {
      html.classList.add('touch-device');
    } else {
      html.classList.add('no-touch');
    }
    
    // Detect mobile
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    if (isMobile) {
      html.classList.add('mobile-device');
    }
  }
  
  // Run immediately if DOM is ready, otherwise wait
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
