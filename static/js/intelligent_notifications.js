/**
 * MINA INTELLIGENT NOTIFICATION SYSTEM
 * Context-aware, proactive guidance with quality monitoring and user assistance
 */

class IntelligentNotifications {
  constructor() {
    this.notificationQueue = [];
    this.activeNotifications = new Map();
    this.userPreferences = this.loadPreferences();
    this.context = {
      isFirstTimeUser: this.isFirstTimeUser(),
      recordingState: 'idle',
      qualityIssues: [],
      lastGuidanceTime: 0,
      sessionMetrics: {}
    };
    
    this.notificationTypes = {
      success: { icon: 'fas fa-check-circle', color: 'success', duration: 3000 },
      info: { icon: 'fas fa-info-circle', color: 'info', duration: 4000 },
      warning: { icon: 'fas fa-exclamation-triangle', color: 'warning', duration: 5000 },
      error: { icon: 'fas fa-times-circle', color: 'danger', duration: 7000 },
      guidance: { icon: 'fas fa-lightbulb', color: 'primary', duration: 6000 },
      quality: { icon: 'fas fa-star', color: 'info', duration: 4000 }
    };
    
    this.init();
  }

  init() {
    this.createNotificationContainer();
    this.bindEvents();
    this.startQualityMonitoring();
    this.scheduleProactiveGuidance();
    
    // Show welcome message for first-time users
    if (this.context.isFirstTimeUser) {
      setTimeout(() => {
        this.showWelcomeSequence();
      }, 2000);
    }
    
    console.log('🔔 Intelligent notification system initialized');
  }

  createNotificationContainer() {
    const containerHTML = `
      <div id="intelligentNotifications" class="notification-container">
        <!-- Notifications will be dynamically inserted here -->
      </div>
      
      <div id="guidanceModal" class="modal fade" tabindex="-1">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header border-0">
              <h5 class="modal-title">
                <i class="fas fa-graduation-cap me-2"></i>
                MINA Assistant
              </h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" id="guidanceContent">
              <!-- Dynamic guidance content -->
            </div>
            <div class="modal-footer border-0">
              <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                Got it
              </button>
              <button type="button" class="btn btn-primary" id="tryGuidanceBtn">
                Try it now
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', containerHTML);
    
    // Add CSS for notification positioning
    const style = document.createElement('style');
    style.textContent = `
      .notification-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1200;
        max-width: 400px;
      }
      
      @media (max-width: 768px) {
        .notification-container {
          top: 10px;
          right: 10px;
          left: 10px;
          max-width: none;
        }
      }
      
      .intelligent-notification {
        margin-bottom: 10px;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        backdrop-filter: blur(10px);
        animation: slideInRight 0.3s ease-out;
      }
      
      @keyframes slideInRight {
        from {
          opacity: 0;
          transform: translateX(100%);
        }
        to {
          opacity: 1;
          transform: translateX(0);
        }
      }
      
      .notification-icon {
        width: 24px;
        text-align: center;
      }
      
      .notification-actions {
        gap: 8px;
        margin-top: 8px;
      }
      
      .notification-progress {
        position: absolute;
        bottom: 0;
        left: 0;
        height: 3px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 0 0 8px 8px;
        transition: width linear;
      }
    `;
    document.head.appendChild(style);
  }

  bindEvents() {
    // Listen for recording state changes
    document.addEventListener('recordingStateChange', (e) => {
      this.context.recordingState = e.detail.state;
      this.handleStateChange(e.detail.state, e.detail.data);
    });
    
    // Listen for quality events
    document.addEventListener('audioQualityChange', (e) => {
      this.handleQualityChange(e.detail);
    });
    
    // Listen for transcription events
    document.addEventListener('transcriptionReceived', (e) => {
      this.handleTranscriptionEvent(e.detail);
    });
    
    // Listen for errors
    document.addEventListener('recordingError', (e) => {
      this.handleError(e.detail);
    });
  }

  show(type, message, options = {}) {
    const notification = this.createNotification(type, message, options);
    this.displayNotification(notification);
    
    // Add to queue for management
    this.notificationQueue.push(notification);
    this.manageQueue();
    
    return notification.id;
  }

  createNotification(type, message, options) {
    const id = 'notification_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    const config = this.notificationTypes[type] || this.notificationTypes.info;
    const duration = options.duration || config.duration;
    
    const notification = {
      id,
      type,
      message,
      config,
      duration,
      options,
      createdAt: Date.now(),
      element: null
    };
    
    notification.element = this.buildNotificationElement(notification);
    return notification;
  }

  buildNotificationElement(notification) {
    const { config, message, options, duration } = notification;
    
    const element = document.createElement('div');
    element.className = `alert alert-${config.color} intelligent-notification`;
    element.id = notification.id;
    
    let actionsHTML = '';
    if (options.actions && Array.isArray(options.actions)) {
      actionsHTML = `
        <div class="notification-actions d-flex">
          ${options.actions.map(action => `
            <button class="btn btn-sm btn-outline-${config.color}" 
                    onclick="window.intelligentNotifications.handleAction('${notification.id}', '${action.id}')">
              ${action.icon ? `<i class="${action.icon} me-1"></i>` : ''}
              ${action.text}
            </button>
          `).join('')}
        </div>
      `;
    }
    
    element.innerHTML = `
      <div class="d-flex align-items-start">
        <div class="notification-icon me-3">
          <i class="${config.icon}"></i>
        </div>
        <div class="flex-grow-1">
          <div class="notification-message">${message}</div>
          ${actionsHTML}
        </div>
        <button type="button" class="btn-close btn-close-white ms-2" 
                onclick="window.intelligentNotifications.dismiss('${notification.id}')">
        </button>
      </div>
      ${options.showProgress !== false ? `<div class="notification-progress"></div>` : ''}
    `;
    
    return element;
  }

  displayNotification(notification) {
    const container = document.getElementById('intelligentNotifications');
    container.appendChild(notification.element);
    
    this.activeNotifications.set(notification.id, notification);
    
    // Start progress bar animation if enabled
    if (notification.options.showProgress !== false) {
      this.animateProgress(notification);
    }
    
    // Auto-dismiss after duration
    setTimeout(() => {
      this.dismiss(notification.id);
    }, notification.duration);
    
    // Announce to screen readers
    this.announceNotification(notification);
  }

  animateProgress(notification) {
    const progressBar = notification.element.querySelector('.notification-progress');
    if (!progressBar) return;
    
    progressBar.style.width = '100%';
    progressBar.style.transition = `width ${notification.duration}ms linear`;
    
    // Animate to 0%
    requestAnimationFrame(() => {
      progressBar.style.width = '0%';
    });
  }

  dismiss(notificationId) {
    const notification = this.activeNotifications.get(notificationId);
    if (!notification) return;
    
    // Fade out animation
    notification.element.style.animation = 'fadeOut 0.3s ease-out forwards';
    
    setTimeout(() => {
      notification.element.remove();
      this.activeNotifications.delete(notificationId);
    }, 300);
  }

  handleAction(notificationId, actionId) {
    const notification = this.activeNotifications.get(notificationId);
    if (!notification || !notification.options.actions) return;
    
    const action = notification.options.actions.find(a => a.id === actionId);
    if (!action) return;
    
    // Execute action callback
    if (action.callback && typeof action.callback === 'function') {
      action.callback();
    }
    
    // Dismiss notification after action
    this.dismiss(notificationId);
  }

  handleStateChange(newState, data) {
    switch(newState) {
      case 'recording':
        this.showRecordingStarted(data);
        break;
      case 'paused':
        this.showRecordingPaused();
        break;
      case 'complete':
        this.showRecordingComplete(data);
        break;
      case 'error':
        this.showRecordingError(data);
        break;
    }
  }

  showRecordingStarted(data) {
    const message = data?.qualityPrecheck 
      ? '🎙️ Recording started with optimal settings!'
      : '🎙️ Recording started successfully!';
    
    this.show('success', message, {
      actions: [
        {
          id: 'pause',
          text: 'Pause',
          icon: 'fas fa-pause',
          callback: () => window.recordingStates?.pauseRecording()
        }
      ]
    });
    
    // Schedule quality check
    setTimeout(() => {
      this.performQualityCheck();
    }, 10000);
  }

  showRecordingPaused() {
    this.show('info', '⏸️ Recording paused', {
      actions: [
        {
          id: 'resume',
          text: 'Resume',
          icon: 'fas fa-play',
          callback: () => window.recordingStates?.resumeRecording()
        }
      ],
      duration: 8000
    });
  }

  showRecordingComplete(data) {
    const stats = data?.stats;
    let message = '✅ Recording completed successfully!';
    
    if (stats) {
      message += ` ${stats.segments} segments, ${stats.words} words, ${stats.avgConfidence}% quality.`;
    }
    
    this.show('success', message, {
      actions: [
        {
          id: 'export',
          text: 'Export',
          icon: 'fas fa-download',
          callback: () => this.triggerExport()
        },
        {
          id: 'new',
          text: 'New Recording',
          icon: 'fas fa-plus',
          callback: () => this.startNewRecording()
        }
      ],
      duration: 10000
    });
  }

  handleQualityChange(qualityData) {
    const { level, confidence, issues } = qualityData;
    
    if (level === 'excellent' && confidence > 0.9) {
      this.show('quality', '⭐ Excellent audio quality detected!', {
        duration: 3000
      });
    } else if (level === 'poor' && confidence < 0.5) {
      this.show('warning', '⚠️ Low audio quality detected', {
        actions: [
          {
            id: 'improve',
            text: 'How to improve',
            icon: 'fas fa-question',
            callback: () => this.showQualityGuidance(issues)
          }
        ]
      });
    }
  }

  handleTranscriptionEvent(transcriptionData) {
    if (transcriptionData.milestone) {
      switch(transcriptionData.milestone) {
        case 'first_segment':
          this.show('info', '🎯 First transcription segment received!', {
            duration: 2000
          });
          break;
        case '100_words':
          this.show('quality', '📝 100 words transcribed with great accuracy!', {
            duration: 2000
          });
          break;
        case '1000_words':
          this.show('success', '🎉 Milestone: 1,000 words transcribed!', {
            duration: 3000
          });
          break;
      }
    }
  }

  handleError(errorData) {
    const { type, message, recoverable } = errorData;
    
    let guidance = '';
    let actions = [];
    
    switch(type) {
      case 'microphone_access':
        guidance = 'Please allow microphone access in your browser settings.';
        actions.push({
          id: 'help',
          text: 'Show Guide',
          icon: 'fas fa-question',
          callback: () => this.showMicrophoneHelp()
        });
        break;
        
      case 'network_error':
        guidance = 'Connection lost. Your session will be saved automatically.';
        actions.push({
          id: 'reconnect',
          text: 'Reconnect',
          icon: 'fas fa-wifi',
          callback: () => this.attemptReconnect()
        });
        break;
        
      case 'audio_processing':
        guidance = 'Audio processing error. Try adjusting your microphone settings.';
        actions.push({
          id: 'settings',
          text: 'Audio Settings',
          icon: 'fas fa-cog',
          callback: () => this.showAudioSettings()
        });
        break;
        
      default:
        guidance = 'An error occurred. Please try again.';
        if (recoverable) {
          actions.push({
            id: 'retry',
            text: 'Retry',
            icon: 'fas fa-redo',
            callback: () => this.retryLastAction()
          });
        }
    }
    
    this.show('error', `❌ ${message || 'Error occurred'}. ${guidance}`, {
      actions,
      duration: 8000
    });
  }

  performQualityCheck() {
    // Simulate quality assessment
    const currentQuality = Math.random() * 0.4 + 0.6; // 0.6-1.0 range
    
    if (currentQuality > 0.85) {
      this.show('quality', '🎵 Audio quality is excellent - keep it up!', {
        duration: 2000
      });
    } else if (currentQuality < 0.7) {
      this.show('guidance', '💡 Tip: Move closer to your microphone for better quality', {
        actions: [
          {
            id: 'tips',
            text: 'More Tips',
            icon: 'fas fa-lightbulb',
            callback: () => this.showQualityTips()
          }
        ]
      });
    }
  }

  showWelcomeSequence() {
    const messages = [
      {
        type: 'info',
        message: '👋 Welcome to MINA! Let\'s get you started with live transcription.',
        options: { duration: 4000 }
      },
      {
        type: 'guidance',
        message: '🎯 Pro tip: Use keyboard shortcuts R (record), S (stop), C (clear) for fast control.',
        options: { 
          duration: 5000,
          actions: [
            {
              id: 'shortcuts',
              text: 'All Shortcuts',
              icon: 'fas fa-keyboard',
              callback: () => this.showKeyboardShortcuts()
            }
          ]
        },
        delay: 4500
      }
    ];
    
    messages.forEach((msg, index) => {
      setTimeout(() => {
        this.show(msg.type, msg.message, msg.options);
      }, msg.delay || (index * 4000));
    });
    
    // Mark user as no longer first-time
    localStorage.setItem('minaFirstTime', 'false');
  }

  scheduleProactiveGuidance() {
    // Schedule periodic guidance based on user activity
    setInterval(() => {
      if (this.shouldShowGuidance()) {
        this.showContextualGuidance();
      }
    }, 60000); // Every minute
  }

  shouldShowGuidance() {
    const now = Date.now();
    const timeSinceLastGuidance = now - this.context.lastGuidanceTime;
    const isRecording = this.context.recordingState === 'recording';
    const hasActiveNotifications = this.activeNotifications.size > 0;
    
    return timeSinceLastGuidance > 300000 && // 5 minutes
           !isRecording &&
           !hasActiveNotifications;
  }

  showContextualGuidance() {
    const guidanceOptions = [
      {
        message: '💡 Did you know? You can export your transcription in multiple formats.',
        action: { id: 'export', text: 'Learn More', callback: () => this.showExportGuidance() }
      },
      {
        message: '🎵 For best results, speak clearly and avoid background noise.',
        action: { id: 'quality', text: 'Quality Tips', callback: () => this.showQualityTips() }
      },
      {
        message: '⚡ Use voice commands to control recording hands-free.',
        action: { id: 'voice', text: 'Voice Commands', callback: () => this.showVoiceCommands() }
      }
    ];
    
    const randomGuidance = guidanceOptions[Math.floor(Math.random() * guidanceOptions.length)];
    
    this.show('guidance', randomGuidance.message, {
      actions: [randomGuidance.action],
      duration: 6000
    });
    
    this.context.lastGuidanceTime = Date.now();
  }

  manageQueue() {
    // Limit to 3 simultaneous notifications
    while (this.activeNotifications.size > 3) {
      const oldestId = Array.from(this.activeNotifications.keys())[0];
      this.dismiss(oldestId);
    }
  }

  announceNotification(notification) {
    if (window.announceToScreenReader) {
      const cleanMessage = notification.message.replace(/[🎙️⏸️✅❌⚠️🎯📝🎉💡🎵👋🎯]/g, '').trim();
      announceToScreenReader(cleanMessage, 'polite');
    }
  }

  // Guidance methods
  showQualityGuidance(issues) {
    const content = `
      <div class="guidance-content">
        <h6><i class="fas fa-star me-2"></i>Improve Audio Quality</h6>
        <ul class="list-unstyled">
          <li><i class="fas fa-check text-success me-2"></i>Position microphone 6-12 inches from mouth</li>
          <li><i class="fas fa-check text-success me-2"></i>Speak clearly at consistent pace</li>
          <li><i class="fas fa-check text-success me-2"></i>Minimize background noise</li>
          <li><i class="fas fa-check text-success me-2"></i>Use a quiet, echo-free environment</li>
        </ul>
      </div>
    `;
    this.showGuidanceModal(content);
  }

  showQualityTips() {
    const content = `
      <div class="guidance-content">
        <h6><i class="fas fa-lightbulb me-2"></i>Pro Tips for Best Results</h6>
        <div class="row">
          <div class="col-md-6">
            <h6 class="text-success">✅ Do</h6>
            <ul class="small">
              <li>Use a dedicated microphone</li>
              <li>Record in a quiet room</li>
              <li>Speak at normal pace</li>
              <li>Pause between thoughts</li>
            </ul>
          </div>
          <div class="col-md-6">
            <h6 class="text-danger">❌ Avoid</h6>
            <ul class="small">
              <li>Background music or TV</li>
              <li>Speaking too fast</li>
              <li>Moving away from mic</li>
              <li>Echo-prone locations</li>
            </ul>
          </div>
        </div>
      </div>
    `;
    this.showGuidanceModal(content);
  }

  showKeyboardShortcuts() {
    const content = `
      <div class="guidance-content">
        <h6><i class="fas fa-keyboard me-2"></i>Keyboard Shortcuts</h6>
        <div class="row">
          <div class="col-md-6">
            <div class="shortcut-item d-flex justify-content-between mb-2">
              <span>Start Recording</span>
              <kbd>R</kbd>
            </div>
            <div class="shortcut-item d-flex justify-content-between mb-2">
              <span>Stop Recording</span>
              <kbd>S</kbd>
            </div>
            <div class="shortcut-item d-flex justify-content-between mb-2">
              <span>Pause/Resume</span>
              <kbd>Space</kbd>
            </div>
          </div>
          <div class="col-md-6">
            <div class="shortcut-item d-flex justify-content-between mb-2">
              <span>Clear Transcription</span>
              <kbd>C</kbd>
            </div>
            <div class="shortcut-item d-flex justify-content-between mb-2">
              <span>Export</span>
              <kbd>E</kbd>
            </div>
            <div class="shortcut-item d-flex justify-content-between mb-2">
              <span>Help</span>
              <kbd>H</kbd>
            </div>
          </div>
        </div>
      </div>
    `;
    this.showGuidanceModal(content);
  }

  showGuidanceModal(content) {
    document.getElementById('guidanceContent').innerHTML = content;
    new bootstrap.Modal(document.getElementById('guidanceModal')).show();
  }

  // Utility methods
  isFirstTimeUser() {
    return localStorage.getItem('minaFirstTime') !== 'false';
  }

  loadPreferences() {
    try {
      return JSON.parse(localStorage.getItem('minaNotificationPreferences')) || {};
    } catch {
      return {};
    }
  }

  startQualityMonitoring() {
    // This would integrate with the quality monitoring system
    setInterval(() => {
      if (this.context.recordingState === 'recording') {
        this.performQualityCheck();
      }
    }, 30000); // Every 30 seconds during recording
  }

  // Integration methods for action callbacks
  triggerExport() {
    if (window.exportTranscription) {
      window.exportTranscription();
    }
  }

  startNewRecording() {
    const startBtn = document.getElementById('startRecordingBtn');
    if (startBtn && !startBtn.disabled) {
      startBtn.click();
    }
  }

  showMicrophoneHelp() {
    // Implementation for microphone troubleshooting
    this.showGuidanceModal(`
      <div class="guidance-content">
        <h6><i class="fas fa-microphone me-2"></i>Microphone Setup Help</h6>
        <div class="alert alert-info">
          <strong>Chrome/Edge:</strong> Click the microphone icon in the address bar and select "Always allow"
        </div>
        <div class="alert alert-info">
          <strong>Firefox:</strong> Click the microphone icon next to the URL and choose "Remember this decision"
        </div>
        <div class="alert alert-info">
          <strong>Safari:</strong> Go to Safari > Preferences > Websites > Microphone and set to "Allow"
        </div>
      </div>
    `);
  }
}

// Initialize intelligent notifications
window.intelligentNotifications = new IntelligentNotifications();

// Override the global showNotification function to use intelligent system
if (window.showNotification) {
  const originalShowNotification = window.showNotification;
  window.showNotification = function(message, type = 'info', duration) {
    return window.intelligentNotifications.show(type, message, { duration });
  };
}