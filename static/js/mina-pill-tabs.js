/**
 * MINA PILL TABS - Interactive Behavior
 * Handles smooth scrolling, snap points, active states, keyboard navigation
 * Production-ready with accessibility support and touch optimization
 */

(function() {
  'use strict';

  /**
   * PillTabs Class
   * Manages a single pill tabs instance
   */
  class PillTabs {
    constructor(container) {
      this.container = container;
      this.wrapper = container.querySelector('[data-pill-tabs-wrapper]');
      this.scroller = container.querySelector('[data-pill-tabs-scroll]');
      this.tabs = Array.from(container.querySelectorAll('[data-pill-tab]'));
      
      // State
      this.activeTab = container.querySelector('.mina-pill-tab.active');
      this.scrollTimeout = null;
      this.isScrolling = false;
      
      // Bind methods
      this.handleTabClick = this.handleTabClick.bind(this);
      this.handleKeydown = this.handleKeydown.bind(this);
      this.handleScroll = this.handleScroll.bind(this);
      this.updateScrollIndicators = this.updateScrollIndicators.bind(this);
      
      this.init();
    }

    /**
     * Initialize the component
     */
    init() {
      if (!this.scroller || this.tabs.length === 0) return;
      
      // Attach event listeners
      this.attachEvents();
      
      // Initial setup
      this.updateScrollIndicators();
      this.scrollActiveIntoView(false);
      
      // Setup intersection observer for performance
      this.setupIntersectionObserver();
      
      console.log('✨ Pill Tabs initialized:', {
        tabs: this.tabs.length,
        activeTab: this.activeTab?.dataset.pillTab
      });
    }

    /**
     * Attach all event listeners
     */
    attachEvents() {
      // Tab click events
      this.tabs.forEach(tab => {
        tab.addEventListener('click', this.handleTabClick);
      });
      
      // Keyboard navigation
      this.scroller.addEventListener('keydown', this.handleKeydown);
      
      // Scroll events for fade indicators
      this.scroller.addEventListener('scroll', this.handleScroll, { passive: true });
      
      // Window resize for recalculation
      window.addEventListener('resize', () => {
        clearTimeout(this.scrollTimeout);
        this.scrollTimeout = setTimeout(() => {
          this.updateScrollIndicators();
        }, 150);
      }, { passive: true });
    }

    /**
     * Handle tab click
     */
    handleTabClick(e) {
      e.preventDefault();
      
      const clickedTab = e.currentTarget;
      const tabId = clickedTab.dataset.pillTab;
      
      // Don't reactivate already active tab
      if (clickedTab === this.activeTab) {
        return;
      }
      
      // Update active state
      this.setActiveTab(clickedTab);
      
      // Scroll tab into view
      this.scrollActiveIntoView(true);
      
      // Emit custom event for other components to listen
      this.emitTabChange(tabId);
      
      // Update associated content panels
      this.updateContentPanels(tabId);
    }

    /**
     * Set active tab
     */
    setActiveTab(tab) {
      // Remove active state from all tabs
      this.tabs.forEach(t => {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
        t.setAttribute('tabindex', '-1');
      });
      
      // Set active state on clicked tab
      tab.classList.add('active');
      tab.setAttribute('aria-selected', 'true');
      tab.setAttribute('tabindex', '0');
      
      // Update internal reference
      this.activeTab = tab;
    }

    /**
     * Scroll active tab into view
     */
    scrollActiveIntoView(smooth = true) {
      if (!this.activeTab) return;
      
      const scrollerRect = this.scroller.getBoundingClientRect();
      const tabRect = this.activeTab.getBoundingClientRect();
      
      // Calculate optimal scroll position (center the tab if possible)
      const scrollLeft = this.scroller.scrollLeft;
      const targetScroll = scrollLeft + (tabRect.left - scrollerRect.left) - (scrollerRect.width / 2) + (tabRect.width / 2);
      
      // Scroll to position
      this.scroller.scrollTo({
        left: Math.max(0, targetScroll),
        behavior: smooth ? 'smooth' : 'auto'
      });
    }

    /**
     * Handle keyboard navigation
     */
    handleKeydown(e) {
      const currentIndex = this.tabs.indexOf(document.activeElement);
      
      if (currentIndex === -1) return;
      
      let nextIndex = currentIndex;
      
      switch(e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          nextIndex = currentIndex > 0 ? currentIndex - 1 : this.tabs.length - 1;
          break;
        
        case 'ArrowRight':
          e.preventDefault();
          nextIndex = currentIndex < this.tabs.length - 1 ? currentIndex + 1 : 0;
          break;
        
        case 'Home':
          e.preventDefault();
          nextIndex = 0;
          break;
        
        case 'End':
          e.preventDefault();
          nextIndex = this.tabs.length - 1;
          break;
        
        case 'Enter':
        case ' ':
          e.preventDefault();
          this.handleTabClick({ currentTarget: this.tabs[currentIndex], preventDefault: () => {} });
          return;
        
        default:
          return;
      }
      
      // Focus and scroll to next tab
      const nextTab = this.tabs[nextIndex];
      nextTab.focus();
      
      // Scroll into view
      nextTab.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
        inline: 'center'
      });
    }

    /**
     * Handle scroll events
     */
    handleScroll() {
      if (!this.isScrolling) {
        this.isScrolling = true;
      }
      
      clearTimeout(this.scrollTimeout);
      
      this.scrollTimeout = setTimeout(() => {
        this.isScrolling = false;
        this.updateScrollIndicators();
      }, 100);
      
      this.updateScrollIndicators();
    }

    /**
     * Update scroll position indicators (fade edges)
     */
    updateScrollIndicators() {
      if (!this.wrapper || !this.scroller) return;
      
      const scrollLeft = this.scroller.scrollLeft;
      const scrollWidth = this.scroller.scrollWidth;
      const clientWidth = this.scroller.clientWidth;
      const maxScroll = scrollWidth - clientWidth;
      
      // Threshold for showing indicators (5px tolerance)
      const threshold = 5;
      
      // Remove all position classes
      this.wrapper.classList.remove('scroll-start', 'scroll-middle', 'scroll-end');
      
      // Determine scroll position
      if (scrollLeft <= threshold) {
        // At start
        this.wrapper.classList.add('scroll-start');
      } else if (scrollLeft >= maxScroll - threshold) {
        // At end
        this.wrapper.classList.add('scroll-end');
      } else {
        // In middle
        this.wrapper.classList.add('scroll-middle');
      }
    }

    /**
     * Emit custom event when tab changes
     */
    emitTabChange(tabId) {
      const event = new CustomEvent('pill-tab-change', {
        detail: {
          tabId: tabId,
          activeTab: this.activeTab,
          container: this.container
        },
        bubbles: true,
        cancelable: true
      });
      
      this.container.dispatchEvent(event);
    }

    /**
     * Update associated content panels
     */
    updateContentPanels(activeTabId) {
      // Find all panels associated with this tab group
      const dataTarget = this.container.dataset.pillTabs;
      const panels = document.querySelectorAll(`[data-pill-panel-group="${dataTarget}"]`);
      
      panels.forEach(panel => {
        const panelId = panel.dataset.pillPanel;
        
        if (panelId === activeTabId) {
          // Show active panel
          panel.classList.remove('hidden');
          panel.classList.add('active');
          panel.removeAttribute('hidden');
          panel.setAttribute('aria-hidden', 'false');
        } else {
          // Hide inactive panels
          panel.classList.add('hidden');
          panel.classList.remove('active');
          panel.setAttribute('hidden', '');
          panel.setAttribute('aria-hidden', 'true');
        }
      });
    }

    /**
     * Setup intersection observer for lazy loading content
     */
    setupIntersectionObserver() {
      if (!('IntersectionObserver' in window)) return;
      
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            // Tab is visible, can trigger lazy loading if needed
            const tab = entry.target;
            tab.dataset.visible = 'true';
          }
        });
      }, {
        root: this.scroller,
        threshold: 0.5
      });
      
      this.tabs.forEach(tab => observer.observe(tab));
    }

    /**
     * Public method: Programmatically set active tab
     */
    activateTab(tabId) {
      const tab = this.tabs.find(t => t.dataset.pillTab === tabId);
      if (tab) {
        this.setActiveTab(tab);
        this.scrollActiveIntoView(true);
        this.emitTabChange(tabId);
        this.updateContentPanels(tabId);
      }
    }

    /**
     * Public method: Get current active tab
     */
    getActiveTab() {
      return this.activeTab?.dataset.pillTab || null;
    }

    /**
     * Destroy instance and cleanup
     */
    destroy() {
      this.tabs.forEach(tab => {
        tab.removeEventListener('click', this.handleTabClick);
      });
      
      this.scroller.removeEventListener('keydown', this.handleKeydown);
      this.scroller.removeEventListener('scroll', this.handleScroll);
      
      clearTimeout(this.scrollTimeout);
    }
  }

  /**
   * Auto-initialize all pill tabs on page
   */
  function initPillTabs() {
    const containers = document.querySelectorAll('[data-pill-tabs]');
    
    containers.forEach(container => {
      // Avoid double initialization
      if (container._pillTabsInstance) return;
      
      // Create and store instance
      container._pillTabsInstance = new PillTabs(container);
    });
  }

  /**
   * Initialize on DOM ready
   */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPillTabs);
  } else {
    initPillTabs();
  }

  /**
   * Re-initialize on dynamic content load
   */
  document.addEventListener('content-loaded', initPillTabs);

  /**
   * Expose PillTabs class globally for manual initialization
   */
  window.MinaPillTabs = PillTabs;

  console.log('🎯 Mina Pill Tabs module loaded');

})();
