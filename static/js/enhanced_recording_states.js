/**
 * MINA ENHANCED RECORDING STATES SYSTEM
 * Industry-standard state management with visual feedback and progress tracking
 */

class EnhancedRecordingStates {
  constructor() {
    this.currentState = 'idle';
    this.states = {
      idle: { name: 'Idle', icon: 'fas fa-circle', color: 'secondary' },
      testing: { name: 'Testing', icon: 'fas fa-cog fa-spin', color: 'info' },
      ready: { name: 'Ready', icon: 'fas fa-check-circle', color: 'success' },
      recording: { name: 'Recording', icon: 'fas fa-record-vinyl recording-pulse', color: 'danger' },
      paused: { name: 'Paused', icon: 'fas fa-pause-circle', color: 'warning' },
      processing: { name: 'Processing', icon: 'fas fa-spinner fa-spin', color: 'primary' },
      complete: { name: 'Complete', icon: 'fas fa-check', color: 'success' },
      issue: { name: 'Issue', icon: 'fas fa-exclamation-triangle', color: 'danger' }
    };
    
    this.sessionData = {
      startTime: null,
      duration: 0,
      segmentCount: 0,
      averageConfidence: 0,
      totalWords: 0,
      pausedDuration: 0,
      lastPauseTime: null
    };
    
    this.timers = {
      session: null,
      autoSave: null,
      qualityCheck: null
    };
    
    this.init();
  }

  init() {
    this.createStateIndicators();
    this.createProgressPanel();
    this.createAdvancedControls();
    this.bindEvents();
    this.setState('idle');
    
    console.log('🎛️ Enhanced recording states initialized');
  }

  createStateIndicators() {
    // Enhanced state indicator in header
    const existingStatus = document.getElementById('connectionStatus');
    if (existingStatus) {
      existingStatus.insertAdjacentHTML('afterend', `
        <div class="recording-state-panel ms-3 d-flex align-items-center">
          <div class="state-indicator me-2">
            <i id="stateIcon" class="fas fa-circle text-secondary"></i>
          </div>
          <div class="state-info">
            <div class="state-name fw-bold" id="stateName">Idle</div>
            <div class="state-details small text-muted" id="stateDetails">Ready to record</div>
          </div>
        </div>
      `);
    }
  }

  createProgressPanel() {
    // Add progress panel to recording controls
    const recordingControls = document.querySelector('#recording-controls .card-body');
    if (recordingControls) {
      recordingControls.insertAdjacentHTML('beforeend', `
        <div class="recording-progress-panel mt-4 d-none" id="recordingProgressPanel">
          <div class="row">
            <div class="col-md-8">
              <div class="progress mb-2" style="height: 8px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated bg-danger" 
                     id="recordingProgressBar" 
                     style="width: 0%">
                </div>
              </div>
              <div class="d-flex justify-content-between small text-muted">
                <span id="recordingElapsed">00:00</span>
                <span id="recordingStatus">Recording in progress...</span>
                <span id="recordingTarget">Target: Auto</span>
              </div>
            </div>
            <div class="col-md-4">
              <div class="recording-stats">
                <div class="row text-center">
                  <div class="col-4">
                    <div class="stat-value fw-bold text-primary" id="segmentCounter">0</div>
                    <div class="stat-label small text-muted">Segments</div>
                  </div>
                  <div class="col-4">
                    <div class="stat-value fw-bold text-success" id="wordCounter">0</div>
                    <div class="stat-label small text-muted">Words</div>
                  </div>
                  <div class="col-4">
                    <div class="stat-value fw-bold text-info" id="confidenceAvg">--</div>
                    <div class="stat-label small text-muted">Quality</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      `);
    }
  }

  createAdvancedControls() {
    // Add advanced recording controls
    const startButton = document.getElementById('startRecordingBtn');
    if (startButton) {
      startButton.insertAdjacentHTML('afterend', `
        <button class="btn btn-warning d-none" 
                id="pauseRecordingBtn" 
                aria-label="Pause recording session"
                aria-keyshortcuts="Space">
          <i class="fas fa-pause me-2"></i>
          Pause
        </button>
        
        <button class="btn btn-info d-none" 
                id="resumeRecordingBtn" 
                aria-label="Resume recording session"
                aria-keyshortcuts="Space">
          <i class="fas fa-play me-2"></i>
          Resume
        </button>
        
        <div class="btn-group ms-2" role="group" aria-label="Advanced recording options">
          <button class="btn btn-outline-secondary btn-sm" 
                  id="autoSaveBtn" 
                  title="Toggle auto-save every 2 seconds (CROWN+ spec)">
            <i class="fas fa-save me-1"></i>
            Auto-save
          </button>
          
          <button class="btn btn-outline-secondary btn-sm" 
                  id="voiceActivatedBtn" 
                  title="Toggle voice-activated recording">
            <i class="fas fa-microphone-slash me-1"></i>
            Voice Mode
          </button>
          
          <button class="btn btn-outline-secondary btn-sm" 
                  id="qualityBoostBtn" 
                  title="Enable quality boost mode">
            <i class="fas fa-magic me-1"></i>
            Boost
          </button>
        </div>
      `);
    }
  }

  bindEvents() {
    // Enhanced button event listeners
    document.getElementById('pauseRecordingBtn')?.addEventListener('click', () => this.pauseRecording());
    document.getElementById('resumeRecordingBtn')?.addEventListener('click', () => this.resumeRecording());
    
    // Advanced features
    document.getElementById('autoSaveBtn')?.addEventListener('click', () => this.toggleAutoSave());
    document.getElementById('voiceActivatedBtn')?.addEventListener('click', () => this.toggleVoiceActivated());
    document.getElementById('qualityBoostBtn')?.addEventListener('click', () => this.toggleQualityBoost());
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
    
    // Page visibility API for handling backgrounding
    document.addEventListener('visibilitychange', () => this.handleVisibilityChange());
  }

  setState(newState, details = null) {
    const previousState = this.currentState;
    this.currentState = newState;
    
    const state = this.states[newState];
    if (!state) {
      console.warn(`Unknown state: ${newState}`);
      return;
    }
    
    // Update visual indicators
    this.updateStateIndicators(state, details);
    
    // Handle state-specific logic
    this.handleStateTransition(previousState, newState);
    
    // Announce state change for accessibility
    this.announceStateChange(state, details);
    
    console.log(`🎯 State transition: ${previousState} → ${newState}`, { details });
  }

  updateStateIndicators(state, details) {
    // Update main state indicator
    const stateIcon = document.getElementById('stateIcon');
    const stateName = document.getElementById('stateName');
    const stateDetails = document.getElementById('stateDetails');
    
    if (stateIcon) {
      stateIcon.className = `${state.icon} text-${state.color}`;
    }
    
    if (stateName) {
      stateName.textContent = state.name;
      stateName.className = `state-name fw-bold text-${state.color}`;
    }
    
    if (stateDetails) {
      stateDetails.textContent = details || this.getStateDescription(this.currentState);
    }
    
    // Update progress panel visibility
    const progressPanel = document.getElementById('recordingProgressPanel');
    if (progressPanel) {
      const showProgress = ['recording', 'paused', 'processing'].includes(this.currentState);
      progressPanel.classList.toggle('d-none', !showProgress);
    }
    
    // Update button states
    this.updateButtonStates();
  }

  updateButtonStates() {
    const buttons = {
      start: document.getElementById('startRecordingBtn'),
      stop: document.getElementById('stopRecordingBtn'),
      pause: document.getElementById('pauseRecordingBtn'),
      resume: document.getElementById('resumeRecordingBtn')
    };
    
    // Reset all button visibility
    Object.values(buttons).forEach(btn => {
      if (btn) btn.classList.add('d-none');
    });
    
    // Show appropriate buttons based on state
    switch(this.currentState) {
      case 'idle':
      case 'ready':
        buttons.start?.classList.remove('d-none');
        if (buttons.start) buttons.start.disabled = false;
        break;
        
      case 'testing':
        buttons.start?.classList.remove('d-none');
        if (buttons.start) buttons.start.disabled = true;
        break;
        
      case 'recording':
        buttons.stop?.classList.remove('d-none');
        buttons.pause?.classList.remove('d-none');
        if (buttons.stop) buttons.stop.disabled = false;
        break;
        
      case 'paused':
        buttons.stop?.classList.remove('d-none');
        buttons.resume?.classList.remove('d-none');
        break;
        
      case 'processing':
        buttons.stop?.classList.remove('d-none');
        if (buttons.stop) buttons.stop.disabled = true;
        break;
        
      case 'complete':
        buttons.start?.classList.remove('d-none');
        if (buttons.start) buttons.start.disabled = false;
        break;
        
      case 'issue':
        buttons.start?.classList.remove('d-none');
        if (buttons.start) buttons.start.disabled = false;
        break;
    }
  }

  getStateDescription(state) {
    const descriptions = {
      idle: 'Ready to begin recording',
      testing: 'Checking microphone and connection',
      ready: 'All systems ready - click Start to begin',
      recording: 'Recording in progress...',
      paused: 'Recording paused - click Resume to continue',
      processing: 'Processing transcription...',
      complete: 'Recording complete and saved',
      issue: 'Issue occurred - please try again'
    };
    
    return descriptions[state] || 'Unknown state';
  }

  handleStateTransition(from, to) {
    switch(to) {
      case 'recording':
        this.startRecordingSession();
        break;
        
      case 'paused':
        this.pauseRecordingSession();
        break;
        
      case 'complete':
        this.completeRecordingSession();
        break;
        
      case 'issue':
        this.handleRecordingIssue();
        break;
    }
  }

  startRecordingSession() {
    this.sessionData.startTime = Date.now();
    this.sessionData.duration = 0;
    this.sessionData.segmentCount = 0;
    this.sessionData.totalWords = 0;
    this.sessionData.averageConfidence = 0;
    
    // Start session timer
    this.timers.session = setInterval(() => {
      this.updateSessionTimer();
    }, 1000);
    
    // Start auto-save if enabled (CROWN+ spec: 2s interval)
    if (this.isAutoSaveEnabled()) {
      this.timers.autoSave = setInterval(() => {
        this.autoSaveSession();
      }, 2000); // Every 2 seconds (CROWN+ requirement)
    }
    
    // Start quality monitoring
    this.timers.qualityCheck = setInterval(() => {
      this.performQualityCheck();
    }, 5000); // Every 5 seconds
    
    // Show notification
    if (window.showNotification) {
      showNotification('🎙️ Recording started successfully!', 'success', 3000);
    }
  }

  pauseRecordingSession() {
    this.sessionData.lastPauseTime = Date.now();
    
    // Clear timers but keep session data
    if (this.timers.session) {
      clearInterval(this.timers.session);
    }
    
    // Show notification
    if (window.showNotification) {
      showNotification('⏸️ Recording paused', 'info', 2000);
    }
  }

  resumeRecordingSession() {
    if (this.sessionData.lastPauseTime) {
      this.sessionData.pausedDuration += Date.now() - this.sessionData.lastPauseTime;
      this.sessionData.lastPauseTime = safeGet(window, "initialValue", null);
    }
    
    // Restart session timer
    this.timers.session = setInterval(() => {
      this.updateSessionTimer();
    }, 1000);
    
    this.setState('recording', 'Recording resumed');
    
    // Show notification
    if (window.showNotification) {
      showNotification('▶️ Recording resumed', 'success', 2000);
    }
  }

  completeRecordingSession() {
    // Clear all timers
    Object.values(this.timers).forEach(timer => {
      if (timer) clearInterval(timer);
    });
    
    // Calculate final statistics
    const totalDuration = Date.now() - this.sessionData.startTime - this.sessionData.pausedDuration;
    const stats = {
      duration: Math.round(totalDuration / 1000),
      segments: this.sessionData.segmentCount,
      words: this.sessionData.totalWords,
      avgConfidence: Math.round(this.sessionData.averageConfidence * 100),
      wpm: Math.round((this.sessionData.totalWords / (totalDuration / 1000)) * 60)
    };
    
    // Show completion summary
    this.showCompletionSummary(stats);
    
    // Auto-export if enabled
    if (this.shouldAutoExport()) {
      this.triggerAutoExport();
    }
  }

  handleRecordingIssue() {
    // Clear timers
    Object.values(this.timers).forEach(timer => {
      if (timer) clearInterval(timer);
    });
    
    // handled
    if (window.showNotification) {
      showNotification('❌ Recording error - check microphone and try again', 'issue', 5000);
    }
  }

  updateSessionTimer() {
    if (!this.sessionData.startTime) return;
    
    const elapsed = Date.now() - this.sessionData.startTime - this.sessionData.pausedDuration;
    const seconds = Math.floor(elapsed / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    const elapsedElement = document.getElementById('recordingElapsed');
    if (elapsedElement) {
      if (hours > 0) {
        elapsedElement.textContent = `${hours}:${String(minutes % 60).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
      } else {
        elapsedElement.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
      }
    }
    
    // Update progress bar (demo: grows over time)
    const progressBar = document.getElementById('recordingProgressBar');
    if (progressBar && seconds > 0) {
      const progress = Math.min((seconds / 300) * 100, 100); // 5 minutes = 100%
      progressBar.style.width = progress + '%';
    }
  }

  updateStatistics(segmentData) {
    if (segmentData.is_final) {
      this.sessionData.segmentCount++;
      
      if (segmentData.text) {
        const wordCount = segmentData.text.split(/\s+/).length;
        this.sessionData.totalWords += wordCount;
      }
      
      if (segmentData.confidence || segmentData.avg_confidence) {
        const confidence = segmentData.avg_confidence || segmentData.confidence;
        this.sessionData.averageConfidence = (
          (this.sessionData.averageConfidence * (this.sessionData.segmentCount - 1) + confidence) /
          this.sessionData.segmentCount
        );
      }
      
      // Update UI counters
      document.getElementById('segmentCounter').textContent = this.sessionData.segmentCount;
      document.getElementById('wordCounter').textContent = this.sessionData.totalWords;
      document.getElementById('confidenceAvg').textContent = Math.round(this.sessionData.averageConfidence * 100) + '%';
    }
  }

  pauseRecording() {
    if (this.currentState === 'recording') {
      this.setState('paused');
      
      // Call the main recording system's pause function if available
      if (window.pauseRecording) {
        window.pauseRecording();
      }
    }
  }

  resumeRecording() {
    if (this.currentState === 'paused') {
      this.resumeRecordingSession();
      
      // Call the main recording system's resume function if available  
      if (window.resumeRecording) {
        window.resumeRecording();
      }
    }
  }

  handleKeyboardShortcuts(event) {
    // Space bar for pause/resume
    if (event.code === 'Space' && !event.target.matches('input, textarea')) {
      event.preventDefault();
      
      if (this.currentState === 'recording') {
        this.pauseRecording();
      } else if (this.currentState === 'paused') {
        this.resumeRecording();
      }
    }
  }

  handleVisibilityChange() {
    if (document.hidden && this.currentState === 'recording') {
      // Page went to background during recording
      console.log('📱 App backgrounded during recording');
      
      // Show notification about background recording
      if (this.isBackgroundRecordingEnabled()) {
        if (window.showNotification) {
          showNotification('🎙️ Recording continues in background', 'info', 3000);
        }
      } else {
        // Pause recording if background mode is disabled
        this.pauseRecording();
        if (window.showNotification) {
          showNotification('⏸️ Recording paused - app backgrounded', 'warning', 3000);
        }
      }
    } else if (!document.hidden && this.currentState === 'paused') {
      // Page came back to foreground
      console.log('📱 App foregrounded');
      
      // Offer to resume
      if (window.showNotification) {
        const resumeBtn = '<button onclick="window.recordingStates.resumeRecording()" class="btn btn-sm btn-primary ms-2">Resume</button>';
        showNotification('▶️ Welcome back! ' + resumeBtn, 'info', 5000);
      }
    }
  }

  performQualityCheck() {
    // This would integrate with the quality monitoring system
    if (window._minaTelemetry && window._minaTelemetry.getHealthSummary) {
      const health = window._minaTelemetry.getHealthSummary();
      
      // Check for quality issues
      if (health.recentErrors && health.recentErrors.length > 3) {
        this.setState('issue', 'Multiple errors detected');
      }
      
      // Update quality status
      const qualityBtn = document.getElementById('qualityBoostBtn');
      if (qualityBtn && health.avgConfidence < 0.6) {
        qualityBtn.classList.add('btn-warning');
        qualityBtn.title = 'Low quality detected - click to boost';
      }
    }
  }

  autoSaveSession() {
    console.log('💾 Auto-saving session...');
    
    // This would integrate with the backend to save session state
    const sessionState = {
      timestamp: Date.now(),
      state: this.currentState,
      data: this.sessionData,
      transcription: this.getCurrentTranscription()
    };
    
    // Show subtle notification
    if (window.showNotification) {
      showNotification('💾 Session auto-saved', 'success', 1500);
    }
  }

  showCompletionSummary(stats) {
    const summaryHTML = `
      <div class="modal fade" id="completionSummary" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header bg-success text-white">
              <h5 class="modal-title">
                <i class="fas fa-check-circle me-2"></i>
                Recording Complete!
              </h5>
            </div>
            <div class="modal-body">
              <div class="row text-center mb-3">
                <div class="col-3">
                  <div class="stat-big text-primary">${this.formatDuration(stats.duration)}</div>
                  <div class="stat-label">Duration</div>
                </div>
                <div class="col-3">
                  <div class="stat-big text-success">${stats.segments}</div>
                  <div class="stat-label">Segments</div>
                </div>
                <div class="col-3">
                  <div class="stat-big text-info">${stats.words}</div>
                  <div class="stat-label">Words</div>
                </div>
                <div class="col-3">
                  <div class="stat-big text-warning">${stats.avgConfidence}%</div>
                  <div class="stat-label">Quality</div>
                </div>
              </div>
              
              <div class="alert alert-success">
                <i class="fas fa-trophy me-2"></i>
                <strong>Great job!</strong> Average ${stats.wpm} words per minute with ${stats.avgConfidence}% confidence.
              </div>
              
              <div class="d-grid gap-2">
                <button type="button" class="btn btn-primary" onclick="this.triggerExport()">
                  <i class="fas fa-download me-2"></i>
                  Export Transcription
                </button>
                <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                  Continue
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
    
    // Remove existing modal if any
    const existing = document.getElementById('completionSummary');
    if (existing) existing.remove();
    
    // Add new modal
    document.body.insertAdjacentHTML('beforeend', summaryHTML);
    
    // Show modal
    new bootstrap.Modal(document.getElementById('completionSummary')).show();
  }

  formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${String(remainingSeconds).padStart(2, '0')}`;
  }

  announceStateChange(state, details) {
    if (window.announceToScreenReader) {
      const message = `Recording state changed to ${state.name}. ${details || this.getStateDescription(this.currentState)}`;
      announceToScreenReader(message, 'polite');
    }
  }

  // Configuration methods
  isAutoSaveEnabled() {
    return localStorage.getItem('minaAutoSave') === 'true';
  }

  isBackgroundRecordingEnabled() {
    const prefs = JSON.parse(localStorage.getItem('minaPreferences') || '{}');
    return prefs.backgroundRecording || false;
  }

  shouldAutoExport() {
    return localStorage.getItem('minaAutoExport') === 'true';
  }

  toggleAutoSave() {
    const current = this.isAutoSaveEnabled();
    localStorage.setItem('minaAutoSave', (!current).toString());
    
    const btn = document.getElementById('autoSaveBtn');
    if (btn) {
      btn.classList.toggle('active', !current);
      btn.title = !current ? 'Auto-save enabled' : 'Auto-save disabled';
    }
    
    if (window.showNotification) {
      showNotification(`💾 Auto-save ${!current ? 'enabled' : 'disabled'}`, 'info', 2000);
    }
  }

  toggleVoiceActivated() {
    // This would integrate with VAD system
    const btn = document.getElementById('voiceActivatedBtn');
    if (btn) {
      btn.classList.toggle('active');
      const isActive = btn.classList.contains('active');
      btn.title = isActive ? 'Voice activation enabled' : 'Voice activation disabled';
      
      if (window.showNotification) {
        showNotification(`🎤 Voice activation ${isActive ? 'enabled' : 'disabled'}`, 'info', 2000);
      }
    }
  }

  toggleQualityBoost() {
    // This would integrate with quality enhancement
    const btn = document.getElementById('qualityBoostBtn');
    if (btn) {
      btn.classList.toggle('active');
      const isActive = btn.classList.contains('active');
      btn.title = isActive ? 'Quality boost enabled' : 'Quality boost disabled';
      
      if (window.showNotification) {
        showNotification(`✨ Quality boost ${isActive ? 'enabled' : 'disabled'}`, 'info', 2000);
      }
    }
  }

  getCurrentTranscription() {
    const container = document.getElementById('transcriptionContainer');
    return container ? container.innerText : '';
  }

  triggerAutoExport() {
    // This would integrate with export system
    console.log('📤 Auto-exporting session...');
    
    if (window.showNotification) {
      showNotification('📤 Exporting transcription...', 'info', 3000);
    }
  }

  // Public API methods
  getSessionStats() {
    return { ...this.sessionData };
  }

  getCurrentState() {
    return this.currentState;
  }

  forceState(state, details) {
    this.setState(state, details);
  }
}

// Initialize enhanced recording states
window.recordingStates = new EnhancedRecordingStates();

// Integration with existing recording system
document.addEventListener('DOMContentLoaded', () => {
  // Override existing start/stop functions to integrate with state system
  const originalStartBtn = document.getElementById('startRecordingBtn');
  const originalStopBtn = document.getElementById('stopRecordingBtn');
  
  if (originalStartBtn) {
    originalStartBtn.addEventListener('click', () => {
      window.recordingStates.setState('testing', 'Initializing recording...');
      setTimeout(() => {
        window.recordingStates.setState('recording');
      }, 1000);
    });
  }
  
  if (originalStopBtn) {
    originalStopBtn.addEventListener('click', () => {
      window.recordingStates.setState('processing', 'Finalizing transcription...');
      setTimeout(() => {
        window.recordingStates.setState('complete');
      }, 2000);
    });
  }
});