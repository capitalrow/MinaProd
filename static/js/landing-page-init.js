/**
 * Landing Page Initialization
 * Ensures marketing landing page content is visible and animated properly
 */

(function() {
  'use strict';
  
  function initLandingPage() {
    // Ensure all fade-in elements are visible immediately
    // This prevents blank page if animations don't trigger
    const fadeElements = document.querySelectorAll('.landing-page .fade-in');
    
    if (fadeElements.length === 0) {
      return; // Not on landing page
    }
    
    // Force visibility for landing page elements
    // The CSS animations should handle the transition, but this is a safety net
    fadeElements.forEach((element, index) => {
      // Ensure element starts visible
      element.style.opacity = '0';
      element.style.transform = 'translateY(30px)';
      
      // Trigger animation with slight delay for stagger effect
      setTimeout(() => {
        element.style.transition = 'opacity 0.8s ease-out, transform 0.8s ease-out';
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
      }, 100 + (index * 100));
    });
    
    console.log(`[Landing Page] Initialized ${fadeElements.length} fade-in elements`);
  }
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLandingPage);
  } else {
    initLandingPage();
  }
})();
