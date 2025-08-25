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

  // --- Socket Management -----------------------------------------------------------
  function initSocket() {
    if (socket && socket.connected) return;
    
    console.log('🔥 INT-LIVE-I2: Initializing socket with proper event handlers...');
    socket = io({ 
      transports: ['websocket', 'polling'],
      forceNew: false,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    });

    socket.on('connect', () => {
      console.log('✅ Socket connected');
      if (wsStatus()) wsStatus().textContent = 'Connected';
      
      // Auto-join session if we have one
      if (CURRENT_SESSION_ID) {
        console.log(`🔄 Auto-joining session: ${CURRENT_SESSION_ID}`);
        socket.emit('join_session', { session_id: CURRENT_SESSION_ID });
      }
    });

    socket.on('disconnect', () => {
      console.log('❌ Socket disconnected');
      if (wsStatus()) wsStatus().textContent = 'Disconnected';
    });

    socket.on('error', (error) => {
      console.error('🚨 Socket error:', error);
      if (wsStatus()) wsStatus().textContent = 'Error';
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

      // Request microphone access
      console.log('🎤 Requesting microphone access...');
      mediaStream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        }
      });
      
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
        if (!e.data || !e.data.size || !socket || !socket.connected) return;
        
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
          console.error('🚨 Error sending audio chunk:', error);
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

  function createSession() {
    if (!socket || !socket.connected) {
      console.warn('⚠️ Cannot create session - socket not connected');
      return;
    }
    
    console.log('🆕 Creating new session...');
    socket.emit('create_session', {
      title: 'Live Recording Session',
      language: document.getElementById('sessionLanguage')?.value || 'en'
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
      start.addEventListener('click', () => {
        // Create session first if needed
        if (!CURRENT_SESSION_ID) {
          createSession();
          // Wait a moment for session creation, then start
          setTimeout(startRecording, 500);
        } else {
          startRecording();
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
      document.addEventListener('DOMContentLoaded', bindEvents);
    } else {
      bindEvents();
    }
    
    console.log('✅ Recording system initialized');
  }

  // Auto-initialize
  initialize();

})();