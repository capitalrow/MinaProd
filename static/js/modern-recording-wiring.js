// Modern Recording Wiring with Enhanced State Management
// Enterprise-grade JavaScript for production deployment

(() => {
  'use strict';

  // ============================================================================
  // APPLICATION STATE MANAGEMENT
  // ============================================================================
  
  class MinaState extends EventTarget {
    constructor() {
      super();
      this.state = {
        socket: null,
        sessionId: String(Date.now()),
        stream: null,
        mediaRecorder: null,
        audioContext: null,
        analyser: null,
        isRecording: false,
        isConnected: false,
        theme: this.getInitialTheme(),
        sessionStartTime: null,
        interimText: '',
        finalText: '',
        debugLogs: []
      };
    }

    getInitialTheme() {
      const stored = localStorage.getItem('mina-theme');
      if (stored) return stored;
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    setState(updates) {
      const oldState = { ...this.state };
      this.state = { ...this.state, ...updates };
      this.dispatchEvent(new CustomEvent('statechange', { 
        detail: { oldState, newState: this.state, updates } 
      }));
    }

    getState() {
      return { ...this.state };
    }
  }

  // ============================================================================
  // GLOBAL APPLICATION INSTANCE
  // ============================================================================
  
  const appState = new MinaState();
  
  // ============================================================================
  // DOM UTILITIES & HELPERS
  // ============================================================================
  
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => document.querySelectorAll(selector);
  
  const logger = {
    log: (...args) => {
      const message = args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
      ).join(' ');
      
      console.log('[mina]', message);
      
      // Add to state
      const logs = appState.getState().debugLogs;
      appState.setState({
        debugLogs: [...logs, { timestamp: Date.now(), message }].slice(-50) // Keep last 50 logs
      });
      
      // Update UI
      const debugConsoleElement = $('#debugConsole');
      if (debugConsoleElement) {
        const div = document.createElement('div');
        div.className = 'mina-console__line';
        div.textContent = message;
        debugConsoleElement.appendChild(div);
        debugConsoleElement.scrollTop = debugConsoleElement.scrollHeight;
      }

      // Update live region for screen readers
      const liveRegion = $('#liveRegion');
      if (liveRegion && (message.includes('connected') || message.includes('error'))) {
        liveRegion.textContent = message;
      }
    }
  };

  // ============================================================================
  // THEME MANAGEMENT
  // ============================================================================
  
  class ThemeManager {
    constructor() {
      this.init();
    }

    init() {
      const toggle = $('#themeToggle');
      const icon = $('#themeIcon');
      
      if (toggle && icon) {
        toggle.addEventListener('click', () => this.toggleTheme());
        this.updateUI();
      }

      // Listen for system theme changes
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('mina-theme')) {
          appState.setState({ theme: e.matches ? 'dark' : 'light' });
        }
      });

      // Listen to state changes
      appState.addEventListener('statechange', (e) => {
        if (e.detail.updates.theme) {
          this.updateUI();
        }
      });
    }

    toggleTheme() {
      const currentTheme = appState.getState().theme;
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      appState.setState({ theme: newTheme });
      localStorage.setItem('mina-theme', newTheme);
    }

    updateUI() {
      const theme = appState.getState().theme;
      const html = document.documentElement;
      const icon = $('#themeIcon');
      
      if (html) {
        html.setAttribute('data-bs-theme', theme);
        html.setAttribute('data-theme', theme);
      }
      
      if (icon) {
        // Update icon with smooth transition
        icon.style.transform = 'scale(0)';
        setTimeout(() => {
          icon.setAttribute('data-feather', theme === 'light' ? 'moon' : 'sun');
          if (typeof feather !== 'undefined') {
            feather.replace();
          }
          icon.style.transform = 'scale(1)';
        }, 150);
      }
    }
  }

  // ============================================================================
  // NOTIFICATION SYSTEM
  // ============================================================================
  
  class NotificationManager {
    constructor() {
      this.toastElement = $('#notificationToast');
      this.toastMessage = $('#toastMessage');
      this.toast = null;
      this.fallbackContainer = null;
      this.initializeToast();
    }

    initializeToast() {
      if (typeof bootstrap !== 'undefined' && this.toastElement) {
        try {
          this.toast = new bootstrap.Toast(this.toastElement);
          logger.log('[NotificationManager] Bootstrap Toast initialized');
        } catch (error) {
          logger.log('[NotificationManager] Bootstrap Toast initialization failed:', error);
          this.createFallbackSystem();
        }
      } else {
        logger.log('[NotificationManager] Bootstrap not available, using fallback notifications');
        this.createFallbackSystem();
      }
    }

    createFallbackSystem() {
      // Create fallback notification container if it doesn't exist
      if (!this.fallbackContainer) {
        this.fallbackContainer = document.createElement('div');
        this.fallbackContainer.className = 'mina-fallback-notifications';
        this.fallbackContainer.style.cssText = `
          position: fixed;
          top: 20px;
          right: 20px;
          z-index: 9999;
          max-width: 350px;
        `;
        document.body.appendChild(this.fallbackContainer);
        
        // Add fallback notification styles
        const style = document.createElement('style');
        style.textContent = `
          .mina-fallback-notification {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease-out;
            position: relative;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          }
          .mina-fallback-notification--success { border-left: 4px solid #198754; }
          .mina-fallback-notification--danger { border-left: 4px solid #dc3545; }
          .mina-fallback-notification--warning { border-left: 4px solid #fd7e14; }
          .mina-fallback-notification--info { border-left: 4px solid #0d6efd; }
          @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
          }
          @media (max-width: 576px) {
            .mina-fallback-notifications {
              top: 10px;
              right: 10px;
              left: 10px;
              max-width: none;
            }
          }
        `;
        document.head.appendChild(style);
      }
    }

    show(message, type = 'info') {
      // Try Bootstrap Toast first
      if (this.toast && this.toastMessage) {
        try {
          this.toastMessage.textContent = message;
          this.toastElement.className = `toast border-${type}`;
          this.toast.show();
          logger.log(`[Toast] ${message}`);
          return;
        } catch (error) {
          logger.log('[NotificationManager] Toast failed, using fallback:', error);
        }
      }
      
      // Fallback notification system
      this.showFallback(message, type);
    }

    showFallback(message, type) {
      if (!this.fallbackContainer) {
        this.createFallbackSystem();
      }
      
      const notification = document.createElement('div');
      notification.className = `mina-fallback-notification mina-fallback-notification--${type}`;
      notification.innerHTML = `
        <div style="font-weight: 500; color: #333; font-size: 14px;">
          ${this.getTypeIcon(type)} ${message}
        </div>
      `;
      
      this.fallbackContainer.appendChild(notification);
      
      // Auto-remove after 5 seconds
      setTimeout(() => {
        if (notification.parentNode) {
          notification.style.animation = 'slideIn 0.3s ease-out reverse';
          setTimeout(() => {
            notification.remove();
          }, 300);
        }
      }, 5000);
      
      logger.log(`[Fallback] ${message}`);
    }

    getTypeIcon(type) {
      const icons = {
        success: '✅',
        danger: '❌',
        warning: '⚠️',
        info: 'ℹ️'
      };
      return icons[type] || icons.info;
    }

    success(message) {
      this.show(message, 'success');
    }

    error(message) {
      this.show(message, 'danger');
    }

    warning(message) {
      this.show(message, 'warning');
    }

    info(message) {
      this.show(message, 'info');
    }
  }

  // ============================================================================
  // SOCKET MANAGEMENT
  // ============================================================================
  
  class SocketManager {
    constructor() {
      this.reconnectAttempts = 0;
      this.maxReconnectAttempts = 10;
      this.reconnectDelay = 1000;
    }

    connect() {
      if (appState.getState().socket?.connected) return;

      const socket = io(window.location.origin, {
        path: '/socket.io',
        transports: ['polling'],
        upgrade: false,
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: this.reconnectDelay,
        timeout: 10000,
      });

      this.setupEventHandlers(socket);
      appState.setState({ socket });
    }

    setupEventHandlers(socket) {
      socket.on('connect', () => {
        appState.setState({ isConnected: true });
        this.reconnectAttempts = 0;
        logger.log(`Socket connected ID: ${socket.id}, Transport: ${socket.io.engine.transport.name}`);
        socket.emit('join_session', { session_id: appState.getState().sessionId });
        notifications.success('Connected to transcription service');
      });

      socket.on('disconnect', (reason) => {
        appState.setState({ isConnected: false });
        logger.log(`Socket disconnected: ${reason}`);
        notifications.warning('Connection lost - attempting to reconnect...');
      });

      socket.on('connect_error', (error) => {
        logger.log(`Connection error: ${error?.message || error}`);
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          notifications.error('Unable to connect to transcription service');
        }
        this.reconnectAttempts++;
      });

      socket.on('server_hello', (data) => {
        logger.log('Server hello:', data);
      });

      socket.on('error', (error) => {
        logger.log('Socket error:', error);
        notifications.error('Transcription service error');
      });

      socket.on('socket_error', (error) => {
        logger.log('Transcription error:', error);
        notifications.error('Transcription processing error');
      });

      socket.on('interim_transcript', (data) => {
        const text = data?.text || '';
        appState.setState({ interimText: text });
      });

      socket.on('final_transcript', (data) => {
        const text = (data?.text || '').trim();
        if (text) {
          const currentFinal = appState.getState().finalText;
          const newFinal = currentFinal ? `${currentFinal} ${text}` : text;
          appState.setState({ 
            finalText: newFinal,
            interimText: '' 
          });
          logger.log(`Final transcript: "${text}"`);
        }
      });
    }
  }

  // ============================================================================
  // AUDIO MANAGEMENT
  // ============================================================================
  
  class AudioManager {
    constructor() {
      this.animationFrameId = null;
    }

    async startRecording() {
      try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            sampleRate: 44100
          } 
        });

        // Setup audio visualization
        this.setupAudioVisualization(stream);

        // Create MediaRecorder
        const mediaRecorder = this.createMediaRecorder(stream);

        appState.setState({ 
          stream, 
          mediaRecorder, 
          isRecording: true,
          sessionStartTime: Date.now()
        });

        mediaRecorder.start(1200); // 1.2 second chunks for balanced latency/cost
        logger.log('Recording started successfully');
        notifications.success('Recording started');

      } catch (error) {
        logger.log('Failed to start recording:', error.message);
        notifications.error(`Recording failed: ${error.message}`);
        throw error;
      }
    }

    setupAudioVisualization(stream) {
      try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(stream);
        const analyser = audioContext.createAnalyser();
        
        analyser.fftSize = 512;
        source.connect(analyser);

        appState.setState({ audioContext, analyser });
        this.startVisualization(analyser);

      } catch (error) {
        logger.log('Audio visualization setup failed:', error.message);
      }
    }

    startVisualization(analyser) {
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const waveform = $('#audioWaveform');

      const animate = () => {
        if (!appState.getState().isRecording) return;

        analyser.getByteTimeDomainData(dataArray);
        
        // Calculate RMS level
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          const value = (dataArray[i] - 128) / 128;
          sum += value * value;
        }
        
        const rms = Math.sqrt(sum / dataArray.length);
        const percentage = Math.min(100, Math.max(0, rms * 300)); // Amplify for visibility
        
        if (waveform) {
          waveform.style.width = `${percentage}%`;
        }

        this.animationFrameId = requestAnimationFrame(animate);
      };

      animate();
    }

    createMediaRecorder(stream) {
      // Determine the best supported format
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        if (MediaRecorder.isTypeSupported('audio/webm')) {
          mimeType = 'audio/webm';
        } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
          mimeType = 'audio/ogg;codecs=opus';
        } else {
          mimeType = ''; // Let browser decide
        }
      }

      const mediaRecorder = new MediaRecorder(stream, { 
        mimeType, 
        audioBitsPerSecond: 128000 
      });

      mediaRecorder.ondataavailable = async (event) => {
        if (!event.data || event.data.size === 0) return;

        try {
          // Convert to base64
          const buffer = await event.data.arrayBuffer();
          const base64 = btoa(String.fromCharCode(...new Uint8Array(buffer)));
          
          // Send to server
          const socket = appState.getState().socket;
          if (socket && socket.connected) {
            socket.emit('audio_chunk', {
              session_id: appState.getState().sessionId,
              audio_data_b64: base64,
              mime: event.data.type || mimeType,
              duration_ms: 1200
            });
          }
        } catch (error) {
          logger.log('Error processing audio chunk:', error.message);
        }
      };

      mediaRecorder.onstop = () => {
        this.stopVisualization();
        
        // Send finalization request
        const socket = appState.getState().socket;
        if (socket && socket.connected) {
          socket.emit('finalize_session', { 
            session_id: appState.getState().sessionId, 
            mime: mediaRecorder.mimeType || mimeType 
          });
        }

        // Clean up stream
        const stream = appState.getState().stream;
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
        }

        appState.setState({ 
          stream: null, 
          mediaRecorder: null, 
          isRecording: false 
        });

        logger.log('Recording stopped');
        notifications.success('Recording stopped - processing final transcript...');
      };

      return mediaRecorder;
    }

    stopRecording() {
      const { mediaRecorder } = appState.getState();
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
      }
    }

    stopVisualization() {
      if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId);
        this.animationFrameId = null;
      }

      const { audioContext } = appState.getState();
      if (audioContext) {
        audioContext.close().catch(() => {});
      }

      const waveform = $('#audioWaveform');
      if (waveform) {
        waveform.style.width = '0%';
      }

      appState.setState({ audioContext: null, analyser: null });
    }
  }

  // ============================================================================
  // UI CONTROLLER
  // ============================================================================
  
  class UIController {
    constructor() {
      this.sessionTimer = null;
      this.init();
    }

    init() {
      this.bindEvents();
      this.bindStateChanges();
      this.updateSessionInfo();
    }

    bindEvents() {
      // Recording controls
      $('#startRecordingBtn')?.addEventListener('click', () => this.handleStartRecording());
      $('#stopRecordingBtn')?.addEventListener('click', () => this.handleStopRecording());
      $('#clearBtn')?.addEventListener('click', () => this.handleClearTranscripts());
      $('#clearLogBtn')?.addEventListener('click', () => this.handleClearLog());
      $('#copyBtn')?.addEventListener('click', () => this.handleCopyTranscript());

      // Keyboard shortcuts
      document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
    }

    bindStateChanges() {
      appState.addEventListener('statechange', (e) => {
        const { updates } = e.detail;
        
        if ('isConnected' in updates) this.updateConnectionStatus();
        if ('isRecording' in updates) this.updateRecordingStatus();
        if ('interimText' in updates) this.updateInterimText();
        if ('finalText' in updates) this.updateFinalText();
        if ('sessionStartTime' in updates) this.updateSessionTimer();
      });
    }

    async handleStartRecording() {
      const { isRecording, socket } = appState.getState();
      
      if (isRecording) return;
      
      if (!socket || !socket.connected) {
        notifications.warning('Connecting to transcription service...');
        socketManager.connect();
        return;
      }

      try {
        await audioManager.startRecording();
      } catch (error) {
        // Error already handled in AudioManager
      }
    }

    handleStopRecording() {
      audioManager.stopRecording();
    }

    handleClearTranscripts() {
      appState.setState({ interimText: '', finalText: '' });
      notifications.success('Transcripts cleared');
    }

    handleClearLog() {
      appState.setState({ debugLogs: [] });
      const debugConsoleElement = $('#debugConsole');
      if (debugConsoleElement) debugConsoleElement.innerHTML = '';
    }

    async handleCopyTranscript() {
      const { finalText } = appState.getState();
      if (!finalText) {
        notifications.warning('No final transcript to copy');
        return;
      }

      try {
        await navigator.clipboard.writeText(finalText);
        notifications.success('Transcript copied to clipboard');
      } catch (error) {
        notifications.error('Failed to copy transcript');
      }
    }

    handleKeyboardShortcuts(event) {
      // Space bar: Toggle recording (when not in an input)
      if (event.code === 'Space' && !['INPUT', 'TEXTAREA'].includes(event.target.tagName)) {
        event.preventDefault();
        const { isRecording } = appState.getState();
        if (isRecording) {
          this.handleStopRecording();
        } else {
          this.handleStartRecording();
        }
      }

      // Escape: Stop recording
      if (event.code === 'Escape') {
        this.handleStopRecording();
      }

      // Ctrl/Cmd + K: Clear transcripts
      if ((event.ctrlKey || event.metaKey) && event.code === 'KeyK') {
        event.preventDefault();
        this.handleClearTranscripts();
      }
    }

    updateConnectionStatus() {
      const { isConnected } = appState.getState();
      const status = $('#wsStatus');
      const indicator = status?.querySelector('.mina-pill__indicator');
      
      if (status) {
        status.className = `mina-pill ${isConnected ? 'mina-pill--success' : 'mina-pill--warning'}`;
        status.innerHTML = `
          <span class="mina-pill__indicator"></span>
          ${isConnected ? 'Connected' : 'Disconnected'}
        `;
      }
    }

    updateRecordingStatus() {
      const { isRecording } = appState.getState();
      const startBtn = $('#startRecordingBtn');
      const stopBtn = $('#stopRecordingBtn');
      const micStatus = $('#micStatus');
      
      if (startBtn) startBtn.disabled = isRecording;
      if (stopBtn) stopBtn.disabled = !isRecording;
      
      if (micStatus) {
        micStatus.className = `mina-pill ${isRecording ? 'mina-pill--danger' : 'mina-pill--success'}`;
        micStatus.innerHTML = `
          <i data-feather="${isRecording ? 'mic' : 'mic-off'}" class="me-1"></i>
          ${isRecording ? 'Recording...' : 'Ready'}
        `;
        if (typeof feather !== 'undefined') {
          feather.replace();
        }
      }

      // Update session timer
      if (isRecording && !this.sessionTimer) {
        this.startSessionTimer();
      } else if (!isRecording && this.sessionTimer) {
        this.stopSessionTimer();
      }
    }

    updateInterimText() {
      const { interimText } = appState.getState();
      const element = $('#interimText');
      if (element) {
        element.textContent = interimText || '';
      }
    }

    updateFinalText() {
      const { finalText } = appState.getState();
      const element = $('#finalText');
      if (element) {
        element.textContent = finalText || '';
      }
    }

    updateSessionInfo() {
      const { sessionId } = appState.getState();
      const sessionIdElement = $('#sessionId');
      if (sessionIdElement) {
        sessionIdElement.textContent = sessionId;
      }
    }

    startSessionTimer() {
      const { sessionStartTime } = appState.getState();
      if (!sessionStartTime) return;

      this.sessionTimer = setInterval(() => {
        const elapsed = Date.now() - sessionStartTime;
        const minutes = Math.floor(elapsed / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        const duration = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        const durationElement = $('#sessionDuration');
        if (durationElement) {
          durationElement.textContent = duration;
        }
      }, 1000);
    }

    stopSessionTimer() {
      if (this.sessionTimer) {
        clearInterval(this.sessionTimer);
        this.sessionTimer = null;
      }
    }

    updateSessionTimer() {
      const { sessionStartTime } = appState.getState();
      if (sessionStartTime) {
        this.startSessionTimer();
      } else {
        this.stopSessionTimer();
      }
    }
  }

  // ============================================================================
  // APPLICATION INITIALIZATION
  // ============================================================================
  
  // Global instances
  const themeManager = new ThemeManager();
  const notifications = new NotificationManager();
  const socketManager = new SocketManager();
  const audioManager = new AudioManager();
  const uiController = new UIController();

  // Initialize application
  document.addEventListener('DOMContentLoaded', () => {
    logger.log('Mina application initialized');
    
    // Connect to WebSocket early
    socketManager.connect();
    
    // Initialize theme
    themeManager.updateUI();
    
    // Show welcome message
    setTimeout(() => {
      notifications.success('Mina is ready for real-time transcription');
    }, 1000);
  });

  // Global error handling
  window.addEventListener('error', (event) => {
    logger.log('Global error:', event.error?.message || event.message);
    notifications.error('An unexpected error occurred');
  });

  window.addEventListener('unhandledrejection', (event) => {
    logger.log('Unhandled promise rejection:', event.reason);
    notifications.error('An unexpected error occurred');
  });

  // Expose state for debugging (development only)
  if (typeof window !== 'undefined') {
    window.minaDebug = {
      getState: () => appState.getState(),
      logger,
      notifications,
      socketManager,
      audioManager
    };
  }

})();