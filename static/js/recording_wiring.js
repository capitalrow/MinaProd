// 🔥 INT-LIVE-I2: Enhanced WebAudio RMS Recording Implementation
// Drop-in replacement with real-time RMS calculation and proper socket handling

(() => {
  let socket;
  let CURRENT_SESSION_ID = null;

  // Media capture
  let mediaStream;
  let mediaRecorder;
  let chunks = []; // raw WebM/Opus blobs before upload

  // WebAudio RMS
  let audioCtx;
  let sourceNode;
  let analyser;
  let timeData;
  let rafId = null;
  let lastRms = 0;

  // UI elements (lazy getters for safety)
  const startBtn = () => document.getElementById('startRecordingBtn');
  const stopBtn = () => document.getElementById('stopRecordingBtn');
  const wsStatus = () => document.getElementById('wsStatus');
  const micStatus = () => document.getElementById('micStatus');
  const inputLevel = () => document.getElementById('inputLevel');

  // --- Enhanced Socket Management with Reliability -----------------------------------------------------------
  
  // Connection health monitoring state
  let connectionHealth = {
    isConnected: false,
    lastHeartbeat: Date.now(),
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    heartbeatInterval: null
  };
  
  function initSocket() {
    if (socket && socket.connected) return;
    
    console.log('🔥 ENHANCED: Initializing socket with reliability features...');
    socket = io({ 
      transports: ['websocket', 'polling'],
      forceNew: false,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      randomizationFactor: 0.5,
      timeout: 20000
    });
    
    setupConnectionHealthMonitoring();

    socket.on('connect', () => {
      console.log('✅ Socket connected - Enhanced reliability active');
      connectionHealth.isConnected = true;
      connectionHealth.reconnectAttempts = 0;
      connectionHealth.lastHeartbeat = Date.now();
      
      if (wsStatus()) {
        wsStatus().textContent = 'Connected';
        wsStatus().className = 'status-indicator connected';
      }
      
      // Show success message briefly
      showNotification('Connected to Mina transcription service', 'success', 2000);
      
      // Auto-join session if we have one
      if (CURRENT_SESSION_ID) {
        console.log(`🔄 Auto-joining session: ${CURRENT_SESSION_ID}`);
        socket.emit('join_session', { session_id: CURRENT_SESSION_ID });
      }
    });

    socket.on('disconnect', (reason) => {
      console.log(`❌ Socket disconnected: ${reason}`);
      connectionHealth.isConnected = false;
      
      if (wsStatus()) {
        wsStatus().textContent = `Disconnected (${reason})`;
        wsStatus().className = 'status-indicator disconnected';
      }
      
      // Show appropriate user message
      if (reason === 'io server disconnect') {
        showNotification('Connection closed by server. Please refresh the page.', 'error', 5000);
      } else {
        showNotification('Connection lost. Attempting to reconnect...', 'warning', 3000);
      }
    });

    socket.on('error', (error) => {
      console.error('🚨 Socket error:', error);
      if (wsStatus()) {
        wsStatus().textContent = `Error: ${error}`;
        wsStatus().className = 'status-indicator error';
      }
      
      showNotification(`Connection error: ${error}`, 'error', 4000);
    });
    
    socket.on('reconnect', (attemptNumber) => {
      console.log(`🔄 Reconnected after ${attemptNumber} attempts`);
      connectionHealth.isConnected = true;
      connectionHealth.reconnectAttempts = 0;
      
      showNotification('Reconnected successfully!', 'success', 2000);
    });
    
    // 🔥 CRITICAL FIX: Add transcription event listeners
    socket.on('interim_transcript', (data) => {
      console.log('📝 Interim transcript received:', data.text);
      updateTranscriptionUI(data, false);
    });
    
    socket.on('final_transcript', (data) => {
      console.log('✅ Final transcript received:', data.text);
      updateTranscriptionUI(data, true);
    });
    
    socket.on('audio_received', (data) => {
      console.log('🎵 Audio chunk acknowledged:', data.chunk_id, 'Processing time:', data.processing_time_ms + 'ms');
    });
    
    socket.on('error', (errorData) => {
      console.error('🚨 Server error:', errorData);
      if (errorData.code === 'PROCESSING_TIMEOUT') {
        showError('Audio processing timeout. Please check your connection.');
      } else if (errorData.code === 'PROCESSING_ERROR') {
        showError('Audio processing failed. Please try again.');
      }
    });
    
    socket.on('reconnect', (attemptNumber) => {
      console.log(`🔄 Reconnected after ${attemptNumber} attempts`);
      connectionHealth.reconnectAttempts = attemptNumber;
      showNotification(`Reconnected successfully!`, 'success', 2000);
    });
    
    socket.on('reconnect_error', (error) => {
      console.error('🔄❌ Reconnection failed:', error);
      connectionHealth.reconnectAttempts++;
      
      if (connectionHealth.reconnectAttempts >= connectionHealth.maxReconnectAttempts) {
        showNotification('Unable to reconnect. Please refresh the page.', 'error', 10000);
      } else {
        showNotification(`Reconnecting... (${connectionHealth.reconnectAttempts}/${connectionHealth.maxReconnectAttempts})`, 'warning', 2000);
      }
    });

    // --- Transcription Event Handlers ---
    socket.on('interim_transcript', (payload) => {
      console.log('📝 Interim transcript:', payload.text?.substring(0, 50) + '...');
      
      const interimDiv = document.getElementById('interimText');
      if (interimDiv && payload.text) {
        interimDiv.textContent = payload.text;
        interimDiv.style.display = 'block';
        
        // Add confidence styling
        if (payload.avg_confidence !== undefined) {
          const conf = payload.avg_confidence;
          if (conf > 0.7) {
            interimDiv.className = 'transcription-segment interim confidence-high';
          } else if (conf > 0.5) {
            interimDiv.className = 'transcription-segment interim confidence-medium';
          } else {
            interimDiv.className = 'transcription-segment interim confidence-low';
          }
        }
      }
    });

    socket.on('final_transcript', (payload) => {
      console.log('✅ Final transcript:', payload.text?.substring(0, 50) + '...');
      
      // Clear interim display
      const interimDiv = document.getElementById('interimText');
      if (interimDiv) {
        interimDiv.style.display = 'none';
        interimDiv.textContent = '';
      }
      
      // Add to final transcript display
      const finalDiv = document.getElementById('finalText');
      if (finalDiv && payload.text) {
        const text = payload.text.trim();
        if (text) {
          // Create a new segment element
          const segmentDiv = document.createElement('div');
          segmentDiv.className = 'transcription-segment final';
          segmentDiv.textContent = (finalDiv.textContent ? ' ' : '') + text;
          
          // Add confidence indicator
          if (payload.avg_confidence !== undefined) {
            const confBar = document.createElement('div');
            confBar.className = 'confidence-indicator';
            const confLevel = document.createElement('div');
            confLevel.className = `confidence-bar ${payload.avg_confidence > 0.7 ? 'confidence-high' : 
                                                   payload.avg_confidence > 0.5 ? 'confidence-medium' : 'confidence-low'}`;
            confLevel.style.width = `${Math.round(payload.avg_confidence * 100)}%`;
            confBar.appendChild(confLevel);
            segmentDiv.appendChild(confBar);
          }
          
          finalDiv.appendChild(segmentDiv);
          
          // Auto-scroll if enabled
          const autoScroll = document.getElementById('autoScroll');
          if (autoScroll && autoScroll.checked) {
            segmentDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
          }
        }
      }
    });

    // Session management events
    socket.on('session_created', (data) => {
      console.log('🆕 Session created:', data.session_id);
      CURRENT_SESSION_ID = data.session_id;
      socket.emit('join_session', { session_id: CURRENT_SESSION_ID });
    });

    socket.on('joined_session', (data) => {
      console.log('✅ Joined session:', data.session_id);
    });

    // Audio processing feedback
    socket.on('audio_received', (data) => {
      // Update input level from server acknowledgment if no client RMS
      if (!lastRms && data.input_level) {
        updateInputLevel(data.input_level);
      }
    });

    socket.on('processing_error', (data) => {
      console.error('🚨 Processing error:', data.error);
      showError(`Processing error: ${data.error}`);
    });
  }
  
  // --- Connection Health Monitoring ---
  function setupConnectionHealthMonitoring() {
    // Start heartbeat monitoring every 30 seconds
    if (connectionHealth.heartbeatInterval) {
      clearInterval(connectionHealth.heartbeatInterval);
    }
    
    connectionHealth.heartbeatInterval = setInterval(() => {
      if (socket && socket.connected) {
        connectionHealth.lastHeartbeat = Date.now();
        socket.emit('heartbeat', { timestamp: connectionHealth.lastHeartbeat });
      } else {
        // Connection appears down, check for stale connection
        const timeSinceLastHeartbeat = Date.now() - connectionHealth.lastHeartbeat;
        if (timeSinceLastHeartbeat > 45000) { // 45 seconds without heartbeat
          console.warn('⚠️ Stale connection detected, forcing reconnect...');
          if (socket) {
            socket.disconnect();
            socket.connect();
          }
        }
      }
    }, 30000);
  }

  // --- Accessibility and Keyboard Navigation Enhancement ---
  function initAccessibilityFeatures() {
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // Focus management
    setupFocusManagement();
    
    // Screen reader announcements
    setupScreenReaderAnnouncements();
    
    // Mobile accessibility
    setupMobileAccessibility();
    
    console.log('🔧 Accessibility features initialized');
  }
  
  function handleKeyboardShortcuts(event) {
    // Only handle shortcuts when not in input fields
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') return;
    
    if (event.ctrlKey) {
      switch(event.key.toLowerCase()) {
        case 'r':
          event.preventDefault();
          if (startBtn() && !startBtn().disabled) {
            startBtn().click();
            announceToScreenReader('Recording started via keyboard shortcut');
          }
          break;
        case 's':
          event.preventDefault();
          if (stopBtn() && !stopBtn().disabled) {
            stopBtn().click();
            announceToScreenReader('Recording stopped via keyboard shortcut');
          }
          break;
        case 'delete':
          event.preventDefault();
          const clearBtn = document.getElementById('clearTranscription');
          if (clearBtn) {
            clearBtn.click();
            announceToScreenReader('Transcription cleared via keyboard shortcut');
          }
          break;
        case 'e':
          event.preventDefault();
          const exportBtn = document.getElementById('exportTranscription');
          if (exportBtn) {
            exportBtn.click();
            announceToScreenReader('Transcription export started via keyboard shortcut');
          }
          break;
      }
    }
    
    // Escape key to clear focus
    if (event.key === 'Escape') {
      document.activeElement.blur();
      announceToScreenReader('Focus cleared');
    }
  }
  
  function setupFocusManagement() {
    // Enhanced focus indicators for keyboard navigation
    const focusableElements = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    
    document.querySelectorAll(focusableElements).forEach(element => {
      element.addEventListener('focus', (e) => {
        e.target.style.outline = '3px solid #007bff';
        e.target.style.outlineOffset = '2px';
      });
      
      element.addEventListener('blur', (e) => {
        e.target.style.outline = '';
        e.target.style.outlineOffset = '';
      });
    });
  }
  
  function setupScreenReaderAnnouncements() {
    // Create announcement functions for screen readers
    window.announceToScreenReader = function(message, priority = 'polite') {
      const announcer = priority === 'assertive' ? 
        document.getElementById('sr-announcements') : 
        document.getElementById('sr-status');
      
      if (announcer) {
        announcer.textContent = message;
        // Clear after announcement
        setTimeout(() => {
          announcer.textContent = '';
        }, 1000);
      }
    };
    
    // Announce connection status changes
    const originalWSStatus = wsStatus;
    if (originalWSStatus) {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'childList' || mutation.type === 'characterData') {
            const newStatus = mutation.target.textContent;
            if (newStatus.includes('Connected')) {
              announceToScreenReader('WebSocket connection established', 'assertive');
            } else if (newStatus.includes('Disconnected')) {
              announceToScreenReader('WebSocket connection lost', 'assertive');
            }
          }
        });
      });
      
      observer.observe(originalWSStatus(), { childList: true, characterData: true, subtree: true });
    }
  }
  
  function setupMobileAccessibility() {
    // iOS audio context handling
    if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
      // Ensure audio context is resumed on first user interaction
      const resumeAudioContext = () => {
        if (audioCtx && audioCtx.state === 'suspended') {
          audioCtx.resume().then(() => {
            console.log('📱 iOS: AudioContext resumed');
            announceToScreenReader('Audio system ready for iOS');
          });
        }
      };
      
      document.addEventListener('touchstart', resumeAudioContext, { once: true });
      document.addEventListener('click', resumeAudioContext, { once: true });
    }
    
    // Android Chrome permission handling
    if (/Android/.test(navigator.userAgent) && /Chrome/.test(navigator.userAgent)) {
      // Enhanced permission request with user guidance
      const originalGetUserMedia = navigator.mediaDevices.getUserMedia;
      navigator.mediaDevices.getUserMedia = function(constraints) {
        announceToScreenReader('Requesting microphone access for Android Chrome');
        return originalGetUserMedia.call(this, constraints);
      };
    }
    
    // Touch-friendly enhancements
    document.querySelectorAll('.btn').forEach(button => {
      button.addEventListener('touchstart', (e) => {
        // Add visual feedback for touch
        e.target.style.transform = 'scale(0.95)';
      }, { passive: true });
      
      button.addEventListener('touchend', (e) => {
        setTimeout(() => {
          e.target.style.transform = '';
        }, 150);
      }, { passive: true });
    });
    
    // Prevent zoom on form inputs for iOS
    if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
      document.querySelectorAll('input, select, textarea').forEach(input => {
        if (input.style.fontSize.length === 0) {
          input.style.fontSize = '16px';
        }
      });
    }
  }

  // --- Enhanced User Notifications ---
  function showNotification(message, type = 'info', duration = 3000) {
    // Remove any existing notifications
    const existingNotification = document.querySelector('.notification-popup');
    if (existingNotification) {
      existingNotification.remove();
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification-popup ${type}`;
    notification.innerHTML = `
      <div class="notification-content">
        <span class="notification-icon">${getNotificationIcon(type)}</span>
        <span class="notification-message">${message}</span>
        <button class="notification-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
      </div>
    `;
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Auto-hide after duration
    setTimeout(() => {
      if (notification.parentElement) {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
      }
    }, duration);
  }
  
  function getNotificationIcon(type) {
    const icons = {
      success: '✅',
      error: '❌', 
      warning: '⚠️',
      info: 'ℹ️'
    };
    return icons[type] || icons.info;
  }

  // --- Enhanced Error Handling ---
  function showError(message, details = '') {
    console.error('🚨 Enhanced Error Display:', message, details);
    
    // Update any error display elements
    const errorDiv = document.getElementById('errorDisplay');
    if (errorDiv) {
      errorDiv.innerHTML = `
        <div class="error-content">
          <h4>⚠️ Processing Error</h4>
          <p><strong>Issue:</strong> ${message}</p>
          ${details ? `<p class="error-details">${details}</p>` : ''}
          <div class="error-actions">
            <button onclick="location.reload()" class="btn btn-primary btn-sm">Refresh Page</button>
            <button onclick="this.parentElement.parentElement.parentElement.style.display='none'" class="btn btn-secondary btn-sm">Dismiss</button>
          </div>
        </div>
      `;
      errorDiv.style.display = 'block';
    }
    
    // Also show as notification
    showNotification(`Error: ${message}`, 'error', 5000);
    
    // Announce error to screen readers
    announceToScreenReader(`Error occurred: ${message}`, 'assertive');
  }

  // --- WebAudio RMS Processing ---
  function startRmsLoop() {
    if (!analyser || !timeData) return;
    
    const tick = () => {
      analyser.getFloatTimeDomainData(timeData);
      
      // Compute RMS in PCM domain (real-time signal analysis)
      let sum = 0;
      for (let i = 0; i < timeData.length; i++) {
        const v = timeData[i];
        sum += v * v;
      }
      lastRms = Math.sqrt(sum / timeData.length) || 0;

      // Update UI meter
      updateInputLevel(lastRms);
      
      rafId = requestAnimationFrame(tick);
    };
    rafId = requestAnimationFrame(tick);
  }

  function stopRmsLoop() {
    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
    lastRms = 0;
    updateInputLevel(0);
  }

  function updateInputLevel(level) {
    const levelElement = inputLevel();
    if (levelElement) {
      const pct = Math.min(1, level * 4); // Scale up visually
      levelElement.textContent = `${Math.round(pct * 100)}%`;
    }

    // Update visual meter if present
    const meter = document.getElementById('levelMeter');
    if (meter) {
      meter.style.width = `${Math.round(pct * 100)}%`;
      meter.setAttribute('aria-valuenow', String(pct));
    }
  }

  // --- Recording Controls ---
  async function startRecording() {
    try {
      console.log('🎤 Starting recording with WebAudio RMS...');
      
      // Ensure socket connection
      initSocket();
      if (!socket || !socket.connected) {
        console.warn('⚠️ Socket not connected, waiting...');
        if (wsStatus()) wsStatus().textContent = 'Connecting...';
        
        // Wait for connection with timeout
        await new Promise((resolve, reject) => {
          const timeout = setTimeout(() => reject(new Error('Connection timeout')), 5000);
          socket.once('connect', () => {
            clearTimeout(timeout);
            resolve();
          });
        });
      }

      // 🔥 CRITICAL FIX: Create session before recording
      await createSessionAndWait();

      // Request microphone access
      console.log('🎤 Requesting microphone access...');
      
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            sampleRate: 16000
          }
        });
        
        console.log('✅ Microphone access granted');
        
      } catch (permissionError) {
        // 🔥 ENHANCED: Comprehensive microphone permission error handling
        console.error('🚨 Microphone access error:', permissionError);
        
        let errorMessage = 'Unable to access microphone';
        let actionText = 'Try Again';
        
        if (permissionError.name === 'NotAllowedError') {
          errorMessage = 'Microphone access denied. Please allow microphone access and try again.';
          actionText = 'Check Permissions';
        } else if (permissionError.name === 'NotFoundError') {
          errorMessage = 'No microphone found. Please connect a microphone and try again.';
          actionText = 'Check Device';
        } else if (permissionError.name === 'NotReadableError') {
          errorMessage = 'Microphone is being used by another application. Please close other apps using the microphone.';
          actionText = 'Check Apps';
        }
        
        showError(errorMessage, {
          action: actionText,
          callback: () => {
            // 🔥 ENHANCED: Provide specific help based on error type
            if (permissionError.name === 'NotAllowedError') {
              window.open('https://support.google.com/chrome/answer/2693767', '_blank');
            }
          }
        });
        
        // Update UI state
        updateConnectionStatus('error', 'Microphone access denied');
        return;
      }
      
      if (micStatus()) micStatus().textContent = 'Recording...';

      // Set up WebAudio pipeline for real-time RMS
      console.log('🔊 Setting up WebAudio RMS pipeline...');
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      sourceNode = audioCtx.createMediaStreamSource(mediaStream);
      analyser = audioCtx.createAnalyser();
      
      // Configure analyser for responsive RMS
      analyser.fftSize = 1024; // Balance between responsiveness and accuracy
      analyser.smoothingTimeConstant = 0.3; // Some smoothing but still responsive
      
      timeData = new Float32Array(analyser.fftSize);
      sourceNode.connect(analyser);
      
      // Start RMS monitoring
      startRmsLoop();

      // Set up MediaRecorder for audio transmission
      console.log('🎵 Setting up MediaRecorder...');
      const mimeCandidates = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus', 
        'audio/ogg'
      ];
      
      const mimeType = mimeCandidates.find(t => MediaRecorder.isTypeSupported(t)) || '';
      console.log(`📦 Using MIME type: ${mimeType || 'default'}`);
      
      const options = mimeType ? { mimeType } : {};
      mediaRecorder = new MediaRecorder(mediaStream, options);

      mediaRecorder.ondataavailable = async (e) => {
        if (!e.data || !e.data.size || !socket || !socket.connected) {
          console.warn('⚠️ Skipping audio chunk - no data or connection issue');
          return;
        }
        
        if (!CURRENT_SESSION_ID) {
          console.warn('⚠️ Skipping audio chunk - no active session');
          return;
        }
        
        try {
          // Convert to ArrayBuffer and then base64
          const arrayBuf = await e.data.arrayBuffer();
          const base64Data = arrayBufferToBase64(arrayBuf);
          
          // Emit with real-time RMS data
          socket.emit('audio_chunk', {
            session_id: CURRENT_SESSION_ID,
            is_final_chunk: false,  // 🔥 INT-LIVE-I2: Proper default
            audio_data_b64: base64Data,
            mime_type: mediaRecorder.mimeType || mimeType || 'audio/webm',
            rms: lastRms,  // 🔥 Real client-side RMS
            ts_client: Date.now()
          });
          
          console.log(`📤 Sent audio chunk: ${arrayBuf.byteLength} bytes, RMS: ${lastRms.toFixed(3)}`);
        
        } catch (error) {
          console.error('🚨 Error sending audio chunk:', {
            error: error.message,
            stack: error.stack,
            sessionId: CURRENT_SESSION_ID,
            chunkSize: arrayBuf.byteLength,
            timestamp: Date.now(),
            rms: lastRms,
            vadResult: vadResult,
            mimeType: mediaRecorder.mimeType || mimeType || 'audio/webm'
          });
          
          // Increment error counter for monitoring
          if (!window.MINA_ERROR_STATS) {
            window.MINA_ERROR_STATS = { audio_send_errors: 0, connection_errors: 0, processing_errors: 0 };
          }
          window.MINA_ERROR_STATS.audio_send_errors += 1;
          
          // Show user-friendly error if too many failures
          if (window.MINA_ERROR_STATS.audio_send_errors > 5) {
            showError('Connection issues detected. Please check your internet connection and try again.');
          }
        }
      };

      mediaRecorder.onstart = () => {
        console.log('✅ MediaRecorder started');
        if (startBtn()) startBtn().disabled = true;
        if (stopBtn()) stopBtn().disabled = false;
      };

      mediaRecorder.onstop = () => {
        console.log('⏹️ MediaRecorder stopped');
        if (startBtn()) startBtn().disabled = false;
        if (stopBtn()) stopBtn().disabled = true;
      };

      mediaRecorder.onerror = (e) => {
        console.error('🚨 MediaRecorder error:', e);
        showError('Recording error occurred');
      };

      // Start recording with optimized chunk timing
      // 300ms gives ~3-4 chunks/sec for good interim cadence
      mediaRecorder.start(300);
      
      console.log('🎯 Recording started successfully');

    } catch (err) {
      console.error('🚨 Start recording error:', err);
      
      let message = 'Recording failed';
      if (err.name === 'NotAllowedError') {
        message = 'Microphone access denied. Please allow microphone permissions.';
      } else if (err.name === 'NotFoundError') {
        message = 'No microphone found. Please connect a microphone.';
      } else if (err.message === 'Connection timeout') {
        message = 'Connection timeout. Please check your internet connection.';
      }
      
      if (micStatus()) micStatus().textContent = message;
      showError(message);
      
      // Clean up on error
      cleanup();
    }
  }

  function stopRecording() {
    try {
      console.log('⏹️ Stopping recording...');
      
      // Stop MediaRecorder
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
      }
      
      // Send final signal to trigger server-side finalization
      if (socket && socket.connected && CURRENT_SESSION_ID) {
        console.log('📤 Sending finalization signal...');
        socket.emit('audio_chunk', {
          session_id: CURRENT_SESSION_ID,
          is_final_chunk: true,  // 🔥 Critical: trigger finalization
          audio_data_b64: null,  // No audio data, just signal
          mime_type: null,
          rms: 0,
          ts_client: Date.now()
        });
      }
      
      cleanup();
      
      if (micStatus()) micStatus().textContent = 'Stopped';
      console.log('✅ Recording stopped successfully');
      
    } catch (e) {
      console.error('🚨 Stop recording error:', e);
      cleanup(); // Ensure cleanup even on error
    }
  }

  function cleanup() {
    // Stop RMS monitoring
    stopRmsLoop();
    
    // Clean up WebAudio
    if (sourceNode) {
      sourceNode.disconnect();
      sourceNode = null;
    }
    if (audioCtx) {
      audioCtx.close();
      audioCtx = null;
    }
    
    // Clean up media stream
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop());
      mediaStream = null;
    }
    
    // Reset UI
    if (startBtn()) startBtn().disabled = false;
    if (stopBtn()) stopBtn().disabled = true;
    
    analyser = null;
    timeData = null;
    mediaRecorder = null;
  }

  // --- Utility Functions ---
  function arrayBufferToBase64(buffer) {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  function showError(message) {
    console.error('🚨 Error:', message);
    
    // Try to show in UI if toast system exists
    if (window.ToastNotificationSystem) {
      new ToastNotificationSystem().showError(message);
    } else {
      // Fallback to alert
      alert(message);
    }
  }

  // 🔥 CRITICAL FIX: Session creation with proper async handling
  function createSessionAndWait() {
    return new Promise((resolve, reject) => {
      if (CURRENT_SESSION_ID) {
        console.log('📋 Using existing session:', CURRENT_SESSION_ID);
        resolve();
        return;
      }
      
      if (!socket || !socket.connected) {
        reject(new Error('Socket not connected'));
        return;
      }
      
      // Listen for session creation response
      const sessionCreatedHandler = (data) => {
        console.log('🆕 Session created successfully:', data.session_id);
        CURRENT_SESSION_ID = data.session_id;
        
        // 🔥 CRITICAL FIX: Join session room immediately after creation
        console.log('🏠 Joining session room:', data.session_id);
        socket.emit('join_session', { session_id: data.session_id });
        
        // Listen for room join confirmation
        const roomJoinedHandler = (joinData) => {
          console.log('✅ Successfully joined session room:', joinData.session_id);
          socket.off('joined_session', roomJoinedHandler);
        };
        
        socket.once('joined_session', roomJoinedHandler);
        
        socket.off('session_created', sessionCreatedHandler);
        socket.off('error', errorHandler);
        resolve();
      };
      
      const errorHandler = (error) => {
        console.error('🚨 Session creation failed:', error);
        socket.off('session_created', sessionCreatedHandler);
        socket.off('error', errorHandler);
        reject(new Error(`Session creation failed: ${error.message || 'Unknown error'}`));
      };
      
      // Set up listeners
      socket.once('session_created', sessionCreatedHandler);
      socket.once('error', errorHandler);
      
      // Request session creation
      console.log('📋 Creating new session...');
      socket.emit('create_session', {
        title: `Live Session ${new Date().toISOString()}`,
        language: document.getElementById('sessionLanguage')?.value || 'en'
      });
      
      // Timeout after 10 seconds
      setTimeout(() => {
        socket.off('session_created', sessionCreatedHandler);
        socket.off('error', errorHandler);
        reject(new Error('Session creation timeout'));
      }, 10000);
    });
  }

  // Legacy function for compatibility
  function createSession() {
    createSessionAndWait().catch(error => {
      console.error('🚨 Session creation failed:', error);
      showError(`Session creation failed: ${error.message}`);
    });
  }

  // --- Event Binding ---
  function bindEvents() {
    if (window._minaRecordingBound) {
      console.log('⚠️ Recording events already bound, skipping...');
      return;
    }
    
    console.log('🔗 Binding recording UI events...');
    
    const start = startBtn();
    const stop = stopBtn();
    
    if (start) {
      start.addEventListener('click', async () => {
        // 🔥 CRITICAL FIX: Proper async session creation
        try {
          await startRecording(); // Session creation is now handled inside startRecording
        } catch (error) {
          console.error('🚨 Failed to start recording:', error);
          if (micStatus()) micStatus().textContent = 'Error';
          showError(`Failed to start recording: ${error.message}`);
        }
      });
    }
    
    if (stop) {
      stop.addEventListener('click', stopRecording);
    }
    
    // Clear transcription button
    const clearBtn = document.getElementById('clearTranscription');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        const finalDiv = document.getElementById('finalText');
        const interimDiv = document.getElementById('interimText');
        if (finalDiv) finalDiv.innerHTML = '';
        if (interimDiv) {
          interimDiv.textContent = '';
          interimDiv.style.display = 'none';
        }
        console.log('🗑️ Transcription cleared');
      });
    }
    
    window._minaRecordingBound = true;
    console.log('✅ Recording events bound successfully');
  }

  // --- Initialization ---
  function initialize() {
    console.log('🚀 INT-LIVE-I2: Initializing enhanced recording system...');
    
    // Initialize socket connection
    initSocket();
    
    // Bind UI events once DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        bindEvents();
        initAccessibilityFeatures();
        // Announce application ready to screen readers after initialization
        setTimeout(() => {
          if (typeof announceToScreenReader === 'function') {
            announceToScreenReader('Mina live transcription application ready. Press Ctrl+R to start recording.', 'polite');
          }
        }, 1500);
      });
    } else {
      bindEvents();
      initAccessibilityFeatures();
      // Announce application ready to screen readers after initialization
      setTimeout(() => {
        if (typeof announceToScreenReader === 'function') {
          announceToScreenReader('Mina live transcription application ready. Press Ctrl+R to start recording.', 'polite');
        }
      }, 1500);
    }
    
    console.log('🔧 ENHANCED: Accessibility-enabled recording system initialized');
  }

  // --- Transcription UI Updates -------------------------------------------------------------------------------
  
  function updateTranscriptionUI(data, isFinal) {
    const container = document.querySelector('#transcriptionContainer, [data-transcription-container]');
    if (!container) {
      console.warn('⚠️ Transcription container not found');
      return;
    }
    
    if (isFinal) {
      // Remove any interim text
      const interimElements = container.querySelectorAll('.interim-transcript');
      interimElements.forEach(el => el.remove());
      
      // Add final transcript segment
      const finalElement = document.createElement('div');
      finalElement.className = 'transcription-segment final-transcript mb-2';
      finalElement.innerHTML = `
        <div class="segment-content">${data.text}</div>
        <div class="segment-meta text-muted small">
          <span class="confidence">Confidence: ${Math.round((data.avg_confidence || data.confidence || 0) * 100)}%</span>
          <span class="timestamp ms-2">${new Date().toLocaleTimeString()}</span>
        </div>
      `;
      container.appendChild(finalElement);
      
      // Update "Ready to transcribe" message
      const readyMessage = container.querySelector('.text-center');
      if (readyMessage && readyMessage.textContent.includes('Ready to transcribe')) {
        readyMessage.style.display = 'none';
      }
    } else {
      // Update or add interim transcript
      let interimElement = container.querySelector('.interim-transcript');
      if (!interimElement) {
        interimElement = document.createElement('div');
        interimElement.className = 'transcription-segment interim-transcript mb-2';
        container.appendChild(interimElement);
      }
      interimElement.innerHTML = `
        <div class="segment-content text-primary">${data.text}</div>
        <div class="segment-meta text-muted small">
          <span class="confidence">Confidence: ${Math.round((data.avg_confidence || data.confidence || 0) * 100)}%</span>
          <span class="status ms-2">Interim</span>
        </div>
      `;
      
      // Hide "Ready to transcribe" message
      const readyMessage = container.querySelector('.text-center');
      if (readyMessage && readyMessage.textContent.includes('Ready to transcribe')) {
        readyMessage.style.display = 'none';
      }
    }
    
    // Auto-scroll if enabled
    const autoScroll = document.getElementById('autoScroll');
    if (autoScroll && autoScroll.checked) {
      container.scrollTop = container.scrollHeight;
    }
    
    // Update stats
    updateTranscriptionStats(data, isFinal);
  }
  
  function updateTranscriptionStats(data, isFinal) {
    if (isFinal) {
      // Update segment count
      const segmentCount = document.querySelector('[data-segments-count]');
      if (segmentCount) {
        const current = parseInt(segmentCount.textContent.replace('Segments: ', '')) || 0;
        segmentCount.textContent = `Segments: ${current + 1}`;
      }
      
      // Update confidence
      const avgConfidence = document.querySelector('[data-avg-confidence]');
      if (avgConfidence && data.avg_confidence) {
        avgConfidence.textContent = `Avg. Confidence: ${Math.round(data.avg_confidence * 100)}%`;
      }
      
      // Update last update time
      const lastUpdate = document.querySelector('[data-last-update]');
      if (lastUpdate) {
        lastUpdate.textContent = `Last Update: ${new Date().toLocaleTimeString()}`;
      }
    }
  }

  // Auto-initialize
  initialize();

})();