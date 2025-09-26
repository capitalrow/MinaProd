/**
 * MINA MOBILE GESTURE SYSTEM
 * Touch-optimized interactions with haptic feedback and accessibility support
 */

class MobileGestureSystem {
  constructor() {
    this.isMobile = this.detectMobile();
    this.gestures = {
      swipeLeft: { threshold: 100, callback: null },
      swipeRight: { threshold: 100, callback: null },
      swipeUp: { threshold: 80, callback: null },
      swipeDown: { threshold: 80, callback: null },
      longPress: { duration: 800, callback: null },
      doubleTap: { maxDelay: 300, callback: null }
    };
    
    this.touchState = {
      startX: 0,
      startY: 0,
      startTime: 0,
      isLongPress: false,
      longPressTimer: null,
      lastTapTime: 0,
      tapCount: 0
    };
    
    this.hapticSupported = 'vibrate' in navigator;
    this.hapticEnabled = this.loadHapticPreference();
    
    if (this.isMobile) {
      this.init();
    }
  }

  init() {
    this.createMobileUI();
    this.bindGestureEvents();
    this.setupAccessibility();
    this.initializeDefaultGestures();
    
    console.log('📱 Mobile gesture system initialized');
  }

  detectMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
           (navigator.maxTouchPoints && navigator.maxTouchPoints > 2);
  }

  createMobileUI() {
    // Create mobile recording panel
    const mobilePanel = document.createElement('div');
    mobilePanel.className = 'mobile-recording-panel safe-area-inset-bottom';
    mobilePanel.id = 'mobileRecordingPanel';
    
    mobilePanel.innerHTML = `
      <div class="mobile-recording-controls">
        <button class="mobile-action-btn btn btn-outline-light" 
                id="mobileSettingsBtn"
                aria-label="Recording settings">
          <i class="fas fa-cog"></i>
        </button>
        
        <button class="mobile-record-btn btn btn-success" 
                id="mobileRecordBtn"
                aria-label="Start recording">
          <i class="fas fa-microphone"></i>
        </button>
        
        <button class="mobile-action-btn btn btn-outline-light" 
                id="mobileTranscriptBtn"
                aria-label="View transcription">
          <i class="fas fa-file-text"></i>
        </button>
      </div>
      
      <div class="mobile-gesture-hints mt-2">
        <small class="text-muted text-center d-block">
          Swipe ← Stop • Swipe → Start • Swipe ↑ Settings
        </small>
      </div>
    `;
    
    document.body.appendChild(mobilePanel);
    
    // Create gesture feedback overlay
    const feedbackOverlay = document.createElement('div');
    feedbackOverlay.className = 'swipe-feedback';
    feedbackOverlay.id = 'swipeFeedback';
    document.body.appendChild(feedbackOverlay);
    
    // Show mobile panel when recording controls are visible
    this.showMobilePanelWhenNeeded();
  }

  showMobilePanelWhenNeeded() {
    const observer = new MutationObserver(() => {
      const recordingSection = document.getElementById('recording-controls');
      const mobilePanel = document.getElementById('mobileRecordingPanel');
      
      if (recordingSection && mobilePanel) {
        const isVisible = recordingSection.offsetParent !== safeGet(window, "initialValue", null);
        mobilePanel.classList.toggle('active', isVisible);
      }
    });
    
    observer.observe(document.body, { 
      childList: true, 
      subtree: true, 
      attributes: true,
      attributeFilter: ['style', 'class']
    });
  }

  bindGestureEvents() {
    const gestureZone = document.body;
    
    gestureZone.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: false });
    gestureZone.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
    gestureZone.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: false });
    gestureZone.addEventListener('touchcancel', (e) => this.handleTouchCancel(e), { passive: false });
    
    // Prevent default touch behaviors on recording controls
    const recordingControls = document.getElementById('recording-controls');
    if (recordingControls) {
      recordingControls.classList.add('swipe-zone');
    }
    
    // Bind mobile button events
    this.bindMobileButtons();
  }

  bindMobileButtons() {
    document.getElementById('mobileRecordBtn')?.addEventListener('click', (e) => {
      this.triggerHapticFeedback('medium');
      this.handleRecordingToggle();
    });
    
    document.getElementById('mobileSettingsBtn')?.addEventListener('click', (e) => {
      this.triggerHapticFeedback('light');
      this.showMobileSettings();
    });
    
    document.getElementById('mobileTranscriptBtn')?.addEventListener('click', (e) => {
      this.triggerHapticFeedback('light');
      this.showMobileTranscript();
    });
  }

  handleTouchStart(e) {
    // Skip if touching form elements or buttons
    if (e.target.matches('input, textarea, select, button, [role="button"]')) {
      return;
    }
    
    const touch = e.touches[0];
    this.touchState.startX = touch.clientX;
    this.touchState.startY = touch.clientY;
    this.touchState.startTime = Date.now();
    this.touchState.isLongPress = false;
    
    // Start long press timer
    this.touchState.longPressTimer = setTimeout(() => {
      this.touchState.isLongPress = true;
      this.handleLongPress(e);
    }, this.gestures.longPress.duration);
  }

  handleTouchMove(e) {
    // Cancel long press on move
    if (this.touchState.longPressTimer) {
      clearTimeout(this.touchState.longPressTimer);
      this.touchState.longPressTimer = safeGet(window, "initialValue", null);
    }
    
    const touch = e.touches[0];
    const deltaX = touch.clientX - this.touchState.startX;
    const deltaY = touch.clientY - this.touchState.startY;
    
    // Show swipe indicators
    this.showSwipeIndicator(deltaX, deltaY);
  }

  handleTouchEnd(e) {
    if (this.touchState.longPressTimer) {
      clearTimeout(this.touchState.longPressTimer);
    }
    
    // Skip if it was a long press
    if (this.touchState.isLongPress) {
      this.hideSwipeIndicator();
      return;
    }
    
    const touch = e.changedTouches[0];
    const deltaX = touch.clientX - this.touchState.startX;
    const deltaY = touch.clientY - this.touchState.startY;
    const deltaTime = Date.now() - this.touchState.startTime;
    
    this.hideSwipeIndicator();
    
    // Detect gestures
    const swipeDetected = this.detectSwipe(deltaX, deltaY, deltaTime);
    
    if (!swipeDetected) {
      this.handleTap(e);
    }
  }

  handleTouchCancel(e) {
    if (this.touchState.longPressTimer) {
      clearTimeout(this.touchState.longPressTimer);
    }
    this.hideSwipeIndicator();
  }

  detectSwipe(deltaX, deltaY, deltaTime) {
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);
    
    // Must be within reasonable time and distance
    if (deltaTime > 800) return false;
    
    // Horizontal swipes
    if (absX > this.gestures.swipeLeft.threshold && absX > absY) {
      if (deltaX > 0) {
        this.handleSwipeRight();
      } else {
        this.handleSwipeLeft();
      }
      return true;
    }
    
    // Vertical swipes
    if (absY > this.gestures.swipeUp.threshold && absY > absX) {
      if (deltaY > 0) {
        this.handleSwipeDown();
      } else {
        this.handleSwipeUp();
      }
      return true;
    }
    
    return false;
  }

  handleTap(e) {
    const now = Date.now();
    this.touchState.tapCount++;
    
    if (this.touchState.tapCount === 1) {
      // Wait for potential second tap
      setTimeout(() => {
        if (this.touchState.tapCount === 1) {
          // Single tap
          this.handleSingleTap(e);
        } else if (this.touchState.tapCount === 2) {
          // Double tap
          this.handleDoubleTap(e);
        }
        this.touchState.tapCount = 0;
      }, this.gestures.doubleTap.maxDelay);
    }
    
    this.touchState.lastTapTime = now;
  }

  // Gesture handlers
  handleSwipeLeft() {
    this.triggerHapticFeedback('medium');
    this.showSwipeFeedback('← Stop Recording');
    
    if (this.gestures.swipeLeft.callback) {
      this.gestures.swipeLeft.callback();
    } else {
      // Default: stop recording
      const stopBtn = document.getElementById('stopRecordingBtn');
      if (stopBtn && !stopBtn.disabled) {
        stopBtn.click();
      }
    }
  }

  handleSwipeRight() {
    this.triggerHapticFeedback('medium');
    this.showSwipeFeedback('→ Start Recording');
    
    if (this.gestures.swipeRight.callback) {
      this.gestures.swipeRight.callback();
    } else {
      // Default: start recording
      const startBtn = document.getElementById('startRecordingBtn');
      if (startBtn && !startBtn.disabled) {
        startBtn.click();
      }
    }
  }

  handleSwipeUp() {
    this.triggerHapticFeedback('light');
    this.showSwipeFeedback('↑ Settings');
    
    if (this.gestures.swipeUp.callback) {
      this.gestures.swipeUp.callback();
    } else {
      // Default: show settings
      this.showMobileSettings();
    }
  }

  handleSwipeDown() {
    this.triggerHapticFeedback('light');
    this.showSwipeFeedback('↓ Hide Panel');
    
    if (this.gestures.swipeDown.callback) {
      this.gestures.swipeDown.callback();
    } else {
      // Default: minimize mobile panel
      this.toggleMobilePanel(false);
    }
  }

  handleLongPress(e) {
    this.triggerHapticFeedback('heavy');
    
    if (this.gestures.longPress.callback) {
      this.gestures.longPress.callback(e);
    } else {
      // Default: show context menu
      this.showContextMenu(e);
    }
  }

  handleSingleTap(e) {
    // Default single tap behavior (if needed)
  }

  handleDoubleTap(e) {
    this.triggerHapticFeedback('medium');
    
    if (this.gestures.doubleTap.callback) {
      this.gestures.doubleTap.callback(e);
    } else {
      // Default: toggle recording state
      this.handleRecordingToggle();
    }
  }

  // UI feedback methods
  showSwipeIndicator(deltaX, deltaY) {
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);
    
    let text = '';
    if (absX > 50 && absX > absY) {
      text = deltaX > 0 ? '→ Start' : '← Stop';
    } else if (absY > 50 && absY > absX) {
      text = deltaY > 0 ? '↓ Hide' : '↑ Settings';
    }
    
    if (text) {
      const indicator = document.querySelector('.swipe-indicator') || 
                       this.createSwipeIndicator();
      indicator.textContent = text;
      indicator.classList.add('show');
    }
  }

  createSwipeIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'swipe-indicator';
    document.body.appendChild(indicator);
    return indicator;
  }

  hideSwipeIndicator() {
    const indicator = document.querySelector('.swipe-indicator');
    if (indicator) {
      indicator.classList.remove('show');
    }
  }

  showSwipeFeedback(message) {
    const feedback = document.getElementById('swipeFeedback');
    if (feedback) {
      feedback.textContent = message;
      feedback.classList.add('show');
      
      setTimeout(() => {
        feedback.classList.remove('show');
      }, 1500);
    }
  }

  triggerHapticFeedback(intensity = 'medium') {
    if (!this.hapticSupported || !this.hapticEnabled) return;
    
    const patterns = {
      light: [10],
      medium: [20],
      heavy: [30],
      success: [10, 10, 10],
      issue: [50, 20, 50]
    };
    
    const pattern = patterns[intensity] || patterns.medium;
    navigator.vibrate(pattern);
  }

  // Action handlers
  handleRecordingToggle() {
    const recordingState = window.recordingStates?.getCurrentState() || 'idle';
    
    switch(recordingState) {
      case 'idle':
      case 'ready':
        const startBtn = document.getElementById('startRecordingBtn');
        if (startBtn && !startBtn.disabled) {
          startBtn.click();
          this.updateMobileRecordButton('recording');
        }
        break;
        
      case 'recording':
        const stopBtn = document.getElementById('stopRecordingBtn');
        if (stopBtn && !stopBtn.disabled) {
          stopBtn.click();
          this.updateMobileRecordButton('idle');
        }
        break;
        
      case 'paused':
        const resumeBtn = document.getElementById('resumeRecordingBtn');
        if (resumeBtn) {
          resumeBtn.click();
          this.updateMobileRecordButton('recording');
        }
        break;
    }
  }

  updateMobileRecordButton(state) {
    const btn = document.getElementById('mobileRecordBtn');
    if (!btn) return;
    
    const icon = btn.querySelector('i');
    
    switch(state) {
      case 'recording':
        btn.className = 'mobile-record-btn btn btn-danger recording';
        icon.className = 'fas fa-stop';
        btn.setAttribute('aria-label', 'Stop recording');
        break;
        
      case 'paused':
        btn.className = 'mobile-record-btn btn btn-warning';
        icon.className = 'fas fa-play';
        btn.setAttribute('aria-label', 'Resume recording');
        break;
        
      default:
        btn.className = 'mobile-record-btn btn btn-success';
        icon.className = 'fas fa-microphone';
        btn.setAttribute('aria-label', 'Start recording');
    }
  }

  showMobileSettings() {
    // Show settings modal or panel
    const settingsModal = document.querySelector('#sessionConfigModal');
    if (settingsModal) {
      new bootstrap.Modal(settingsModal).show();
    } else {
      // Show quick settings
      this.showQuickSettings();
    }
  }

  showQuickSettings() {
    const quickSettingsHTML = `
      <div class="modal fade" id="mobileQuickSettings" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">
                <i class="fas fa-mobile-alt me-2"></i>
                Quick Settings
              </h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div class="mb-3">
                <div class="form-check form-switch">
                  <input class="form-check-input" type="checkbox" id="mobileHaptic" ${this.hapticEnabled ? 'checked' : ''}>
                  <label class="form-check-label" for="mobileHaptic">
                    Haptic Feedback
                  </label>
                </div>
              </div>
              
              <div class="mb-3">
                <div class="form-check form-switch">
                  <input class="form-check-input" type="checkbox" id="mobileGestures" checked>
                  <label class="form-check-label" for="mobileGestures">
                    Gesture Controls
                  </label>
                </div>
              </div>
              
              <div class="mb-3">
                <label class="form-label">Swipe Sensitivity</label>
                <input type="range" class="form-range" min="50" max="200" value="100" id="swipeSensitivity">
              </div>
              
              <div class="alert alert-info">
                <small>
                  <strong>Gestures:</strong><br>
                  Swipe left: Stop • Swipe right: Start<br>
                  Swipe up: Settings • Double tap: Toggle recording
                </small>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-primary" onclick="window.mobileGestures.saveQuickSettings()" data-bs-dismiss="modal">
                Save
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
    
    // Remove existing modal
    const existing = document.getElementById('mobileQuickSettings');
    if (existing) existing.remove();
    
    document.body.insertAdjacentHTML('beforeend', quickSettingsHTML);
    new bootstrap.Modal(document.getElementById('mobileQuickSettings')).show();
  }

  saveQuickSettings() {
    const hapticEnabled = document.getElementById('mobileHaptic')?.checked || false;
    const gesturesEnabled = document.getElementById('mobileGestures')?.checked || false;
    const sensitivity = document.getElementById('swipeSensitivity')?.value || 100;
    
    this.hapticEnabled = hapticEnabled;
    this.updateSwipeSensitivity(sensitivity);
    
    localStorage.setItem('minaHapticEnabled', hapticEnabled.toString());
    localStorage.setItem('minaGesturesEnabled', gesturesEnabled.toString());
    localStorage.setItem('minaSwipeSensitivity', sensitivity);
    
    if (window.intelligentNotifications) {
      window.intelligentNotifications.show('success', '📱 Mobile settings saved!', { duration: 2000 });
    }
  }

  showMobileTranscript() {
    // Scroll to transcription container
    const transcriptContainer = document.getElementById('transcriptionContainer');
    if (transcriptContainer) {
      transcriptContainer.scrollIntoView({ behavior: 'smooth' });
    }
  }

  showContextMenu(e) {
    const contextMenuHTML = `
      <div class="mobile-context-menu" id="mobileContextMenu" style="
        position: fixed;
        top: ${e.touches[0].clientY}px;
        left: ${e.touches[0].clientX}px;
        z-index: 1300;
        background: rgba(33, 37, 41, 0.95);
        border-radius: 8px;
        padding: 8px;
        backdrop-filter: blur(10px);
      ">
        <button class="btn btn-sm btn-outline-light d-block w-100 mb-2" onclick="window.mobileGestures.quickAction('start')">
          <i class="fas fa-play me-2"></i>Start Recording
        </button>
        <button class="btn btn-sm btn-outline-light d-block w-100 mb-2" onclick="window.mobileGestures.quickAction('settings')">
          <i class="fas fa-cog me-2"></i>Settings
        </button>
        <button class="btn btn-sm btn-outline-light d-block w-100" onclick="window.mobileGestures.quickAction('export')">
          <i class="fas fa-download me-2"></i>Export
        </button>
      </div>
    `;
    
    // Remove existing menu
    const existing = document.getElementById('mobileContextMenu');
    if (existing) existing.remove();
    
    document.body.insertAdjacentHTML('beforeend', contextMenuHTML);
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
      const menu = document.getElementById('mobileContextMenu');
      if (menu) menu.remove();
    }, 3000);
  }

  quickAction(action) {
    // Remove context menu
    const menu = document.getElementById('mobileContextMenu');
    if (menu) menu.remove();
    
    this.triggerHapticFeedback('medium');
    
    switch(action) {
      case 'start':
        this.handleRecordingToggle();
        break;
      case 'settings':
        this.showMobileSettings();
        break;
      case 'export':
        if (window.exportTranscription) {
          window.exportTranscription();
        }
        break;
    }
  }

  setupAccessibility() {
    // Add mobile-specific accessibility enhancements
    document.body.setAttribute('data-mobile-gestures', 'enabled');
    
    // Announce gesture capabilities to screen readers
    if (window.announceToScreenReader) {
      setTimeout(() => {
        announceToScreenReader('Mobile gestures enabled: swipe left to stop, right to start, up for settings', 'polite');
      }, 2000);
    }
  }

  initializeDefaultGestures() {
    // Set up default gesture callbacks
    this.gestures.swipeLeft.callback = () => this.handleSwipeLeft();
    this.gestures.swipeRight.callback = () => this.handleSwipeRight();
    this.gestures.swipeUp.callback = () => this.handleSwipeUp();
    this.gestures.swipeDown.callback = () => this.handleSwipeDown();
    this.gestures.longPress.callback = (e) => this.handleLongPress(e);
    this.gestures.doubleTap.callback = () => this.handleDoubleTap();
  }

  updateSwipeSensitivity(sensitivity) {
    const factor = sensitivity / 100;
    this.gestures.swipeLeft.threshold = 100 * factor;
    this.gestures.swipeRight.threshold = 100 * factor;
    this.gestures.swipeUp.threshold = 80 * factor;
    this.gestures.swipeDown.threshold = 80 * factor;
  }

  toggleMobilePanel(show) {
    const panel = document.getElementById('mobileRecordingPanel');
    if (panel) {
      panel.classList.toggle('active', show);
    }
  }

  loadHapticPreference() {
    return localStorage.getItem('minaHapticEnabled') !== 'false';
  }

  // Public API methods
  setGestureCallback(gestureType, callback) {
    if (this.gestures[gestureType]) {
      this.gestures[gestureType].callback = callback;
    }
  }

  enableHaptic() {
    this.hapticEnabled = true;
    localStorage.setItem('minaHapticEnabled', 'true');
  }

  disableHaptic() {
    this.hapticEnabled = false;
    localStorage.setItem('minaHapticEnabled', 'false');
  }
}

// Initialize mobile gesture system
window.mobileGestures = new MobileGestureSystem();

// Integration with recording states
document.addEventListener('DOMContentLoaded', () => {
  // Listen for recording state changes to update mobile UI
  if (window.recordingStates) {
    const originalSetState = window.recordingStates.setState;
    window.recordingStates.setState = function(state, details) {
      originalSetState.call(this, state, details);
      
      // Update mobile button
      if (window.mobileGestures && window.mobileGestures.isMobile) {
        window.mobileGestures.updateMobileRecordButton(state);
      }
    };
  }
});

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
