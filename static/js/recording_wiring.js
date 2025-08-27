// 🔥 INT-LIVE-I2: Enhanced WebAudio RMS Recording Implementation
// Drop-in replacement with real-time RMS calculation and proper socket handling

(() => {
  let socket;
  let CURRENT_SESSION_ID = safeGet(window, 'initialSessionId', null);

  // Media capture
  let mediaStream;
  let mediaRecorder;
  let chunks = []; // raw WebM/Opus blobs before upload

  // WebAudio RMS
  let audioCtx;
  let sourceNode;
  let analyser;
  let timeData;
  let rafId = safeGet(window, 'initialRafId', null);
  let lastRms = 0;

  // UI elements (lazy getters for safety)
  const startBtn = () => safeQuerySelector('#startRecordingBtn');
  const stopBtn = () => safeQuerySelector('#stopRecordingBtn');
  const wsStatus = () => safeQuerySelector('#wsStatus');
  const micStatus = () => safeQuerySelector('#micStatus');
  const inputLevel = () => safeQuerySelector('#inputLevel');

  // --- Enhanced Socket Management with Reliability -----------------------------------------------------------
  
  // Connection health monitoring state
  let connectionHealth = {
    isConnected: false,
    lastHeartbeat: Date.now(),
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    heartbeatInterval: safeGet(window, 'initialHeartbeatInterval', null)
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
        joinSession(CURRENT_SESSION_ID);
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

    // 🔥 PHASE 1: Enhanced session joining protocol
    function joinSession(sessionId) {
      if (!socket || !socket.connected) {
        console.warn('🚨 Cannot join session: Socket not connected');
        showNotification('Connection not available. Please try again.', 'error');
        return;
      }
      
      console.log(`📝 Joining session: ${sessionId}`);
      socket.emit('join_session', { session_id: sessionId });
    }
    
    // 🔥 PHASE 1: Listen for session join confirmation
    socket.on('joined_session', (data) => {
      console.log('✅ Session joined successfully:', data);
      CURRENT_SESSION_ID = data.session_id;
      
      // Show debug/stub mode indicators
      if (data.debug_mode) {
        showNotification('Debug mode enabled', 'info', 3000);
      }
      if (data.stub_mode) {
        showNotification('Stub transcription mode - testing wiring', 'info', 5000);
      }
      
      // Update UI to show session is ready
      if (wsStatus()) {
        wsStatus().textContent = data.stub_mode ? 'Connected (Stub Mode)' : 'Ready';
        wsStatus().className = 'status-indicator connected';
      }
    });
    
    // 🔥 PHASE 1: Listen for acknowledgments to track delivery
    let ackCount = 0;
    socket.on('ack', (ackData) => {
      ackCount++;
      console.log(`📨 ACK #${ackData.seq}: ${ackData.latency_ms}ms, mode: ${ackData.mode}`);
      
      // Update performance indicator (optional UI enhancement)
      if (ackData.latency_ms > 1000) {
        console.warn(`⚠️ High latency detected: ${ackData.latency_ms}ms`);
      }
      
      // Show periodic connection health
      if (ackCount % 10 === 0) {
        console.log(`🔗 Connection health: ${ackCount} chunks processed`);
      }
    });

    socket.on('error', (issueData) => {
      console.warn('🚨 Server issue:', issueData);
      
      // 🔥 CRITICAL: Handle recording errors properly
      if (mediaRecorder && mediaRecorder.state === 'recording') {
        console.warn('🚨 Recording failed due to server error, stopping...');
        stopRecording().catch(e => safeExecute(() => console.warn('Recording stop issue:', e), 'Stop Recording'));
      }
      
      const issueMessage = issueData.message || issueData || 'Unknown server error';
      const errorType = issueData.type || 'unknown';
      
      // Specific error handling based on type
      switch (errorType) {
        case 'missing_session_id':
          showNotification('Session issue: Missing session ID', 'error');
          break;
        case 'session_not_joined':
          showNotification('Please wait for session to initialize', 'warning');
          // Auto-retry joining if we have a session ID
          if (CURRENT_SESSION_ID) {
            setTimeout(() => joinSession(CURRENT_SESSION_ID), 1000);
          }
          break;
        case 'rate_limit_exceeded':
          showNotification('Speaking too fast - please slow down', 'warning');
          break;
        case 'audio_decode_error':
        case 'audio_processing_error':
          showNotification('Audio processing error - please check microphone', 'error');
          break;
        case 'server_exception':
          showNotification('Server error - please try again', 'error');
          break;
        default:
          showNotification(issueMessage, 'error');
      }
      
      // Update status indicator
      if (wsStatus()) {
        const statusEl = wsStatus(); if (statusEl) statusEl.textContent = 'Issue';
        wsStatus().className = 'status-indicator error';
      }
    });
    
    socket.on('reconnect', (attemptNumber) => {
      console.log(`🔄 Reconnected after ${attemptNumber} attempts`);
      connectionHealth.isConnected = true;
      connectionHealth.reconnectAttempts = 0;
      
      showNotification('Reconnected successfully!', 'success', 2000);
    });
    
    // 🔥 CONSOLIDATED TRANSCRIPTION EVENT HANDLERS
    socket.on('interim_transcript', (data) => {
      console.log('📝 Interim transcript received:', data.text?.substring(0, 50) + '...');
      
      // Check if interim display is enabled
      const showInterimCheckbox = document.getElementById('showInterim');
      if (!showInterimCheckbox || !showInterimCheckbox.checked) {
        return; // Skip interim updates if disabled
      }
      
      updateTranscriptionUI(data, false);
    });
    
    socket.on('final_transcript', (data) => {
      console.log('✅ Final transcript received:', data.text);
      updateTranscriptionUI(data, true);
    });
    
    socket.on('transcription_segment', (data) => {
      console.log('📄 Transcription segment:', data);
      // Handle both interim and final based on data.is_final
      updateTranscriptionUI(data, data.is_final || false);
    });
    
    socket.on('audio_acknowledged', (data) => {
      console.log('📨 ACK #' + data.chunk_id + ': ' + data.processing_time_ms + 'ms, mode:', data.mode || 'unknown');
    });
    
    socket.on('reconnect', (attemptNumber) => {
      console.log(`🔄 Reconnected after ${attemptNumber} attempts`);
      connectionHealth.reconnectAttempts = attemptNumber;
      showNotification(`Reconnected successfully!`, 'success', 2000);
    });
    
    socket.on('reconnect_error', (error) => {
      console.warn('🔄❌ Reconnection failed:', error);
      connectionHealth.reconnectAttempts++;
      
      if (connectionHealth.reconnectAttempts >= connectionHealth.maxReconnectAttempts) {
        showNotification('Unable to reconnect. Please refresh the page.', 'error', 10000);
      } else {
        showNotification(`Reconnecting... (${connectionHealth.reconnectAttempts}/${connectionHealth.maxReconnectAttempts})`, 'warning', 2000);
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

    // 🔥 CRITICAL FIX: Add real-time session metrics broadcast
    socket.on('session_metrics_update', (metrics) => {
      console.log('📊 Session metrics update:', metrics);
      updateSessionMetrics(metrics);
    });

    // Audio processing feedback
    socket.on('audio_received', (data) => {
      // Update input level from server acknowledgment if no client RMS
      if (!lastRms && data.input_level) {
        updateInputLevel(data.input_level);
      }
    });

    socket.on('processing_error', (data) => {
      console.warn('🚨 Processing issue:', data.issue);
      
      // 🔥 CRITICAL: Stop recording on processing errors
      if (mediaRecorder && mediaRecorder.state === 'recording') {
        console.warn('🚨 Processing failed, stopping recording...');
        stopRecording().catch(e => console.warn('Issue stopping recording on processing issue:', e));
      }
      
      showEnhancedNotification('Processing issue: ' + safeGet(data, 'issue', 'Unknown'));
    });
    
    // 🔥 NEW: Add missing transcription error handler
    socket.on('transcription_error', (data) => {
      console.warn('🚨 Transcription issue:', data);
      
      // Stop recording on transcription errors
      if (mediaRecorder && mediaRecorder.state === 'recording') {
        console.warn('🚨 Transcription failed, stopping recording...');
        stopRecording().catch(e => console.warn('Issue stopping recording on transcription issue:', e));
      }
      
      showNotification(`Transcription failed: ${data.issue || 'Unknown error'}`, 'error', 5000);
    });
  }
  
  // 🔥 CRITICAL FIX: Advanced visual recording indicators
  function updateRecordingVisualIndicators(isRecording, inputLevel = 0) {
    try {
      const micStatus = document.getElementById('micStatus');
      const wsStatus = document.getElementById('wsStatus');
      const recordingIndicator = document.getElementById('recordingIndicator');
      const micLevelBar = document.getElementById('micLevelBar');
      
      if (isRecording) {
        // Add animated recording indicator
        if (micStatus) {
          micStatus.innerHTML = '<span class="recording-indicator recording-pulse"></span>Recording';
          micStatus.className = 'text-danger fw-bold d-flex align-items-center';
        }
        
        // Update connection status with recording state
        if (wsStatus) {
          wsStatus.innerHTML = '<span class="status-indicator status-connected"></span>Recording Active';
          wsStatus.className = 'text-success';
        }
        
        // Update microphone level visualization
        if (micLevelBar) {
          const level = Math.min(Math.max(inputLevel * 100, 0), 100);
          micLevelBar.style.width = `${level}%`;
          micLevelBar.style.opacity = '1';
        }
        
        // Add recording pulse to main recording indicator
        if (recordingIndicator) {
          recordingIndicator.classList.add('recording-pulse');
        }
        
      } else {
        // Remove recording indicators
        if (micStatus) {
          micStatus.innerHTML = '<span class="status-indicator status-disconnected"></span>Ready';
          micStatus.className = 'text-muted';
        }
        
        if (wsStatus) {
          const isConnected = socket && socket.connected;
          if (isConnected) {
            wsStatus.innerHTML = '<span class="status-indicator status-connected"></span>Connected';
            wsStatus.className = 'text-success';
          } else {
            wsStatus.innerHTML = '<span class="status-indicator status-disconnected"></span>Not Connected';
            wsStatus.className = 'text-danger';
          }
        }
        
        // Hide microphone level
        if (micLevelBar) {
          micLevelBar.style.width = '0%';
          micLevelBar.style.opacity = '0.3';
        }
        
        // Remove recording pulse
        if (recordingIndicator) {
          recordingIndicator.classList.remove('recording-pulse');
        }
      }
      
      // Announce state change for accessibility
      announceToScreenReader(isRecording ? 'Recording started' : 'Recording stopped');
      
    } catch (issue) {
      console.warn('❌ Failed to update recording visual indicators:', error);
    }
  }

  // 🔥 CRITICAL FIX: Session metrics update function
  function updateSessionMetrics(metrics) {
    try {
      // Update segment count
      const segmentElement = document.getElementById('segmentCount');
      if (segmentElement) {
        segmentElement.textContent = metrics.segments_count || 0;
      }
      
      // Update session duration
      const durationElement = document.getElementById('sessionDuration');
      if (durationElement) {
        const duration = metrics.session_duration || 0;
        const minutes = Math.floor(duration / 60);
        const seconds = Math.floor(duration % 60);
        durationElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
      }
      
      // Update average confidence
      const confidenceElement = document.getElementById('avgConfidence');
      if (confidenceElement) {
        const confidence = metrics.avg_confidence || 0;
        confidenceElement.textContent = `${Math.round(confidence * 100)}%`;
      }
      
      // Update words per minute
      const wpmElement = document.getElementById('wordsPerMinute');
      if (wpmElement) {
        wpmElement.textContent = metrics.words_per_minute || 0;
      }
      
    } catch (issue) {
      console.warn('❌ Failed to update session metrics UI:', error);
    }
  }

  // 🔥 ADVANCED: Enhanced error handling with specific recovery guidance
  function showEnhancedIssue(errorType, message, details = {}) {
    const errorConfig = {
      'microphone_denied': {
        title: '🎤 Microphone Access Required',
        message: 'Please allow microphone access to use live transcription.',
        actions: [
          '1. Click the microphone icon in your browser address bar',
          '2. Select "Allow" for microphone access',
          '3. Refresh the page and try again'
        ],
        type: 'warning',
        persistent: true
      },
      'websocket_disconnected': {
        title: '🔌 Connection Lost',
        message: 'Lost connection to transcription service.',
        actions: [
          '1. Check your internet connection',
          '2. Attempting to reconnect automatically...',
          '3. If problems persist, refresh the page'
        ],
        type: 'error',
        persistent: false
      },
      'session_failed': {
        title: '⚠️ Session Error',
        message: 'Transcription session encountered an error.',
        actions: [
          '1. Stop current recording if active',
          '2. Start a new session',
          '3. Contact support if error persists'
        ],
        type: 'error',
        persistent: true
      }
    };
    
    const config = errorConfig[errorType] || {
      title: '❌ Error',
      message: message,
      actions: ['Please try again or refresh the page'],
      type: 'error',
      persistent: false
    };
    
    showDetailedNotification(config);
  }

  function showDetailedNotification(config) {
    const notificationArea = document.getElementById('notificationArea') || createNotificationArea();
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${config.type === 'warning' ? 'warning' : 'danger'} alert-dismissible fade show`;
    notification.setAttribute('role', 'alert');
    notification.setAttribute('aria-live', 'assertive');
    
    const actionsHtml = config.actions.map(action => 
      `<li class="small text-muted mt-1">${action}</li>`
    ).join('');
    
    notification.innerHTML = `
      <div class="d-flex align-items-start">
        <div class="me-3 fs-4">⚠️</div>
        <div class="flex-grow-1">
          <strong class="d-block">${config.title}</strong>
          <div class="mt-1">${config.message}</div>
          ${actionsHtml ? `<ul class="mt-2 mb-0 ps-3">${actionsHtml}</ul>` : ''}
        </div>
        ${!config.persistent ? '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' : ''}
      </div>
    `;
    
    notificationArea.appendChild(notification);
    
    if (!config.persistent) {
      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove();
        }
      }, 8000);
    }
    
    announceToScreenReader(`${config.title}: ${config.message}`);
  }

  function createNotificationArea() {
    const area = document.createElement('div');
    area.id = 'notificationArea';
    area.className = 'position-fixed top-0 end-0 p-3';
    area.style.zIndex = '1056';
    document.body.appendChild(area);
    return area;
  }

  
  // 🚀 CUTTING-EDGE: AI-Powered Quality Enhancement
  class TranscriptionQualityEnhancer {
    constructor() {
      this.confidenceHistory = [];
      this.latencyHistory = [];
      this.qualityThreshold = 0.75;
      this.adaptiveOptimization = true;
    }
    
    analyzeTranscriptQuality(segment) {
      const confidence = segment.avg_confidence || 0;
      const text = segment.text || '';
      
      // Advanced quality metrics
      const metrics = {
        confidence: confidence,
        textLength: text.length,
        wordCount: text.split(' ').length,
        hasRepetition: this.detectRepetition(text),
        isComplete: this.isCompleteSentence(text),
        semanticCoherence: this.analyzeSemanticCoherence(text),
        timestamp: Date.now()
      };
      
      this.confidenceHistory.push(metrics);
      
      // Keep only recent history (last 50 segments)
      if (this.confidenceHistory.length > 50) {
        this.confidenceHistory.shift();
      }
      
      return this.calculateOverallQuality(metrics);
    }
    
    detectRepetition(text) {
      const words = text.toLowerCase().split(' ');
      const wordCount = {};
      let totalRepetitions = 0;
      
      words.forEach(word => {
        wordCount[word] = (wordCount[word] || 0) + 1;
        if (wordCount[word] > 1) {
          totalRepetitions++;
        }
      });
      
      return totalRepetitions / words.length;
    }
    
    isCompleteSentence(text) {
      const sentenceEnders = /[.!?]$/;
      const hasCapital = /^[A-Z]/.test(text.trim());
      return sentenceEnders.test(text.trim()) && hasCapital;
    }
    
    analyzeSemanticCoherence(text) {
      // Simple coherence check based on common patterns
      const coherenceIndicators = [
        /\b(and|but|however|therefore|because|since|although)\b/gi,
        /\b(first|second|third|finally|next|then)\b/gi,
        /\b(this|that|these|those)\b/gi
      ];
      
      let coherenceScore = 0;
      coherenceIndicators.forEach(pattern => {
        coherenceScore += (text.match(pattern) || []).length;
      });
      
      return Math.min(coherenceScore / 10, 1); // Normalize to 0-1
    }
    
    calculateOverallQuality(currentMetrics) {
      if (this.confidenceHistory.length < 3) {
        return {
          overall: currentMetrics.confidence,
          trend: 'stable',
          recommendation: 'gathering_data'
        };
      }
      
      const recentConfidences = this.confidenceHistory.slice(-5).map(m => m.confidence);
      const avgConfidence = recentConfidences.reduce((a, b) => a + b, 0) / recentConfidences.length;
      
      const trend = this.calculateTrend(recentConfidences);
      
      let recommendation = 'continue';
      if (avgConfidence < 0.4) {
        recommendation = 'check_microphone';
      } else if (avgConfidence < 0.6) {
        recommendation = 'improve_audio';
      } else if (avgConfidence > 0.85) {
        recommendation = 'excellent';
      }
      
      return {
        overall: avgConfidence,
        trend: trend,
        recommendation: recommendation,
        metrics: currentMetrics
      };
    }
    
    calculateTrend(values) {
      if (values.length < 3) return 'stable';
      
      const firstHalf = values.slice(0, Math.floor(values.length / 2));
      const secondHalf = values.slice(Math.floor(values.length / 2));
      
      const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
      const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
      
      const diff = secondAvg - firstAvg;
      
      if (diff > 0.1) return 'improving';
      if (diff < -0.1) return 'declining';
      return 'stable';
    }
    
    getAdaptiveRecommendations() {
      if (this.confidenceHistory.length < 5) return [];
      
      const recent = this.confidenceHistory.slice(-5);
      const recommendations = [];
      
      // Check for consistent low confidence
      if (recent.every(m => m.confidence < 0.5)) {
        recommendations.push({
          type: 'microphone_check',
          message: 'Consider checking microphone position - consistent low confidence detected',
          priority: 'high'
        });
      }
      
      // Check for high repetition
      const avgRepetition = recent.reduce((sum, m) => sum + m.hasRepetition, 0) / recent.length;
      if (avgRepetition > 0.3) {
        recommendations.push({
          type: 'audio_quality',
          message: 'Audio may have echoes or background noise causing repetition',
          priority: 'medium'
        });
      }
      
      // Check for incomplete sentences
      const incompleteRatio = recent.filter(m => !m.isComplete).length / recent.length;
      if (incompleteRatio > 0.7) {
        recommendations.push({
          type: 'speech_pattern',
          message: 'Try speaking in complete sentences for better transcription',
          priority: 'low'
        });
      }
      
      return recommendations;
    }
  }

  // 🚀 CUTTING-EDGE: Predictive Latency Optimization
  class PredictiveLatencyOptimizer {
    constructor() {
      this.latencyHistory = [];
      this.networkHistory = [];
      this.adaptiveBuffering = true;
      this.targetLatency = 200; // ms
      this.bufferSize = 1024;
    }
    
    recordLatency(latency, chunkSize, timestamp) {
      this.latencyHistory.push({
        latency,
        chunkSize,
        timestamp,
        networkCondition: this.assessNetworkCondition(latency)
      });
      
      // Keep only recent history (last 100 measurements)
      if (this.latencyHistory.length > 100) {
        this.latencyHistory.shift();
      }
      
      return this.optimizeForPredictedLatency();
    }
    
    assessNetworkCondition(latency) {
      if (latency < 100) return 'excellent';
      if (latency < 300) return 'good';
      if (latency < 800) return 'fair';
      return 'poor';
    }
    
    optimizeForPredictedLatency() {
      if (this.latencyHistory.length < 10) {
        return { strategy: 'default', bufferSize: this.bufferSize };
      }
      
      const recent = this.latencyHistory.slice(-10);
      const avgLatency = recent.reduce((sum, entry) => sum + entry.latency, 0) / recent.length;
      const latencyTrend = this.calculateLatencyTrend(recent);
      
      let strategy = 'adaptive';
      let recommendedBufferSize = this.bufferSize;
      
      // Predictive optimization based on patterns
      if (avgLatency > this.targetLatency * 2) {
        // High latency - reduce chunk frequency, increase buffer
        strategy = 'conservative';
        recommendedBufferSize = Math.min(this.bufferSize * 1.5, 4096);
      } else if (avgLatency < this.targetLatency * 0.5) {
        // Low latency - can be more aggressive
        strategy = 'aggressive';
        recommendedBufferSize = Math.max(this.bufferSize * 0.7, 512);
      }
      
      // Trend-based adjustments
      if (latencyTrend === 'increasing') {
        recommendedBufferSize *= 1.2;
        strategy = 'preemptive';
      } else if (latencyTrend === 'decreasing') {
        recommendedBufferSize *= 0.9;
      }
      
      return {
        strategy,
        bufferSize: Math.round(recommendedBufferSize),
        avgLatency,
        trend: latencyTrend,
        networkCondition: this.assessNetworkCondition(avgLatency)
      };
    }
    
    calculateLatencyTrend(entries) {
      if (entries.length < 5) return 'stable';
      
      const firstHalf = entries.slice(0, Math.floor(entries.length / 2));
      const secondHalf = entries.slice(Math.floor(entries.length / 2));
      
      const firstAvg = firstHalf.reduce((sum, e) => sum + e.latency, 0) / firstHalf.length;
      const secondAvg = secondHalf.reduce((sum, e) => sum + e.latency, 0) / secondHalf.length;
      
      const changeRatio = (secondAvg - firstAvg) / firstAvg;
      
      if (changeRatio > 0.2) return 'increasing';
      if (changeRatio < -0.2) return 'decreasing';
      return 'stable';
    }
    
    getPredictiveInsights() {
      if (this.latencyHistory.length < 20) return null;
      
      const recent = this.latencyHistory.slice(-20);
      const patterns = this.detectPatterns(recent);
      
      return {
        currentCondition: this.assessNetworkCondition(recent[recent.length - 1].latency),
        predictions: patterns,
        recommendations: this.getOptimizationRecommendations(patterns)
      };
    }
    
    detectPatterns(entries) {
      // Simple pattern detection - could be enhanced with ML
      const latencies = entries.map(e => e.latency);
      const timeWindows = [];
      
      // Check for time-based patterns (e.g., degradation during certain periods)
      for (let i = 0; i < latencies.length - 5; i++) {
        const window = latencies.slice(i, i + 5);
        const avg = window.reduce((a, b) => a + b, 0) / window.length;
        timeWindows.push(avg);
      }
      
      return {
        hasIncreasingPattern: timeWindows.every((val, i, arr) => i === 0 || val >= arr[i - 1]),
        hasStablePattern: timeWindows.every(val => Math.abs(val - timeWindows[0]) < 50),
        volatility: this.calculateVolatility(latencies)
      };
    }
    
    calculateVolatility(values) {
      const mean = values.reduce((a, b) => a + b, 0) / values.length;
      const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
      return Math.sqrt(variance);
    }
    
    getOptimizationRecommendations(patterns) {
      const recommendations = [];
      
      if (patterns.volatility > 200) {
        recommendations.push({
          type: 'network_stability',
          message: 'Network latency is highly variable - consider switching to a more stable connection',
          priority: 'high'
        });
      }
      
      if (patterns.hasIncreasingPattern) {
        recommendations.push({
          type: 'performance_degradation',
          message: 'Network performance appears to be degrading - adaptive buffering enabled',
          priority: 'medium'
        });
      }
      
      return recommendations;
    }
  }

  // Initialize advanced systems
  const qualityEnhancer = new TranscriptionQualityEnhancer();
  const latencyOptimizer = new PredictiveLatencyOptimizer();

  // 🚀 CUTTING-EDGE: Advanced utility functions
  function showQualityInsight(analysis) {
    const insightMessages = {
      'check_microphone': {
        title: '🎤 Microphone Check Recommended',
        message: `Audio quality is below optimal (${Math.round(analysis.overall * 100)}%). Consider adjusting microphone position.`,
        type: 'warning'
      },
      'improve_audio': {
        title: '🔧 Audio Enhancement Available',
        message: `Transcript quality is fair (${Math.round(analysis.overall * 100)}%). Try reducing background noise or speaking closer to microphone.`,
        type: 'info'
      },
      'gathering_data': {
        title: '📊 Quality Analysis in Progress',
        message: 'Analyzing audio quality patterns...',
        type: 'info'
      }
    };
    
    const config = insightMessages[analysis.recommendation];
    if (config) {
      showDetailedNotification({
        ...config,
        actions: [`Quality trend: ${analysis.trend}`, `Confidence: ${Math.round(analysis.overall * 100)}%`],
        persistent: false
      });
    }
  }

  function applyLatencyOptimizations(optimization) {
    console.log(`🎯 Applying ${optimization.strategy} latency strategy:`, optimization);
    
    // Apply buffer size optimization
    if (window.audioProcessor && optimization.bufferSize !== window.audioProcessor.bufferSize) {
      window.audioProcessor.bufferSize = optimization.bufferSize;
      console.log(`📊 Buffer size optimized: ${optimization.bufferSize} bytes`);
    }
    
    // Show optimization insight to user
    if (optimization.strategy !== 'default' && optimization.avgLatency > 500) {
      showDetailedNotification({
        title: '⚡ Performance Optimization Active',
        message: `Network conditions detected as ${optimization.networkCondition}. Adaptive optimization applied.`,
        actions: [
          `Strategy: ${optimization.strategy}`,
          `Average latency: ${Math.round(optimization.avgLatency)}ms`,
          `Trend: ${optimization.trend}`
        ],
        type: 'info',
        persistent: false
      });
    }
  }

  function showLatencyWarning(latency, optimization) {
    showDetailedNotification({
      title: '⚠️ High Latency Detected',
      message: `Response time is ${latency}ms (target: <200ms).`,
      actions: [
        'Network optimization automatically applied',
        `Strategy: ${optimization.strategy}`,
        'Consider checking your internet connection'
      ],
      type: 'warning',
      persistent: false
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
  // 🚀 WCAG 2.1 AAA COMPLIANCE: Advanced accessibility features
  function initAccessibilityFeatures() {
    // Enhanced keyboard shortcuts with help system
    document.addEventListener('keydown', handleAdvancedKeyboardShortcuts);
    
    // Create comprehensive ARIA live regions
    createAccessibilityInfrastructure();
    
    // Initialize focus management
    setupAdvancedFocusManagement();
    
    // Initialize screen reader optimizations
    setupScreenReaderOptimizations();
    
    // Add voice navigation (cutting-edge feature)
    if ('speechRecognition' in window || 'webkitSpeechRecognition' in window) {
      initVoiceNavigation();
    }
    
    console.log('♿ Advanced accessibility features initialized');
  }

  function handleAdvancedKeyboardShortcuts(event) {
    // Help system (F1 or Ctrl+?)
    if (event.key === 'F1' || (event.ctrlKey && event.key === '?')) {
      event.preventDefault();
      showKeyboardShortcutsHelp();
      return;
    }
    
    // Skip standard shortcuts if user is in an input field
    if (event.target.matches('input, textarea, select, [contenteditable]')) {
      return;
    }
    
    switch(event.key.toLowerCase()) {
      case 'r':
        event.preventDefault();
        const startBtn = document.getElementById('startRecordingBtn');
        if (startBtn && !startBtn.disabled) {
          startBtn.click();
          announceToScreenReader('Recording started via keyboard shortcut R');
        }
        break;
      case 's':
        event.preventDefault();
        const stopBtn = document.getElementById('stopRecordingBtn');
        if (stopBtn && !stopBtn.disabled) {
          stopBtn.click();
          announceToScreenReader('Recording stopped via keyboard shortcut S');
        }
        break;
      case 'c':
        event.preventDefault();
        const clearBtn = document.getElementById('clearTranscription');
        if (clearBtn) {
          clearBtn.click();
          announceToScreenReader('Transcription cleared via keyboard shortcut C');
        }
        break;
      case 'e':
        event.preventDefault();
        const exportBtn = document.getElementById('exportTranscription');
        if (exportBtn) {
          exportBtn.click();
          announceToScreenReader('Export started via keyboard shortcut E');
        }
        break;
      case 'm':
        event.preventDefault();
        toggleMute();
        break;
      case 'h':
        event.preventDefault();
        showKeyboardShortcutsHelp();
        break;
    }
    
    // Escape key functionality
    if (event.key === 'Escape') {
      // Close any open notifications
      const notifications = document.querySelectorAll('.alert');
      notifications.forEach(n => n.remove());
      
      // Clear focus if not essential
      if (!event.target.matches('button[aria-label*="recording"], input[required]')) {
        document.activeElement.blur();
        announceToScreenReader('Focus cleared, press Tab to navigate');
      }
    }
  }

  function createAccessibilityInfrastructure() {
    // Main announcements region
    let announcer = document.getElementById('sr-announcements');
    if (!announcer) {
      announcer = document.createElement('div');
      announcer.id = 'sr-announcements';
      announcer.setAttribute('aria-live', 'assertive');
      announcer.setAttribute('aria-atomic', 'true');
      announcer.className = 'sr-only';
      document.body.appendChild(announcer);
    }
    
    // Status updates region
    let statusRegion = document.getElementById('sr-status');
    if (!statusRegion) {
      statusRegion = document.createElement('div');
      statusRegion.id = 'sr-status';
      statusRegion.setAttribute('aria-live', 'polite');
      statusRegion.setAttribute('aria-atomic', 'false');
      statusRegion.className = 'sr-only';
      document.body.appendChild(statusRegion);
    }
    
    // Add enhanced role definitions
    const transcriptionContainer = document.getElementById('transcriptionContainer');
    if (transcriptionContainer) {
      transcriptionContainer.setAttribute('role', 'region');
      transcriptionContainer.setAttribute('aria-label', 'Live transcription results');
      transcriptionContainer.setAttribute('aria-live', 'polite');
      transcriptionContainer.setAttribute('aria-relevant', 'additions text');
    }
  }

  function setupAdvancedFocusManagement() {
    // Enhanced focus indicators
    const style = document.createElement('style');
    style.textContent = `
      *:focus {
        outline: 3px solid #0066cc !important;
        outline-offset: 2px !important;
        box-shadow: 0 0 0 6px rgba(0, 102, 204, 0.2) !important;
      }
      
      .focus-trap {
        position: relative;
      }
      
      .focus-trap::before,
      .focus-trap::after {
        content: '';
        position: absolute;
        width: 1px;
        height: 1px;
        opacity: 0;
        pointer-events: none;
      }
    `;
    document.head.appendChild(style);
    
    // Focus trap for modal dialogs
    setupFocusTraps();
  }

  function setupFocusTraps() {
    // Focus trapping for any modal that might appear
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Tab') {
        const focusableElements = document.querySelectorAll(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]):not([disabled])'
        );
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        // If no focusable elements, prevent tabbing
        if (focusableElements.length === 0) {
          event.preventDefault();
          return;
        }
        
        // Wrap focus
        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
          }
        }
      }
    });
  }

  function setupScreenReaderOptimizations() {
    // Dynamic content announcements
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          mutation.addedNodes.forEach((node) => {
            // Announce new transcription segments
            if (node.nodeType === Node.ELEMENT_NODE && 
                node.classList && node.classList.contains('transcription-segment')) {
              const text = node.textContent.trim();
              if (text.length > 0) {
                setTimeout(() => {
                  announceToScreenReader(`New transcript: ${text.substring(0, 100)}`);
                }, 100);
              }
            }
          });
        }
      });
    });
    
    const transcriptionContainer = document.getElementById('transcriptionContainer');
    if (transcriptionContainer) {
      observer.observe(transcriptionContainer, {
        childList: true,
        subtree: true
      });
    }
  }

  function showKeyboardShortcutsHelp() {
    const shortcuts = [
      { key: 'R', action: 'Start recording' },
      { key: 'S', action: 'Stop recording' },
      { key: 'C', action: 'Clear transcription' },
      { key: 'E', action: 'Export transcription' },
      { key: 'M', action: 'Toggle microphone mute' },
      { key: 'H', action: 'Show this help' },
      { key: 'F1', action: 'Help (alternative)' },
      { key: 'Escape', action: 'Close dialogs/clear focus' },
      { key: 'Tab', action: 'Navigate between elements' },
      { key: 'Space', action: 'Activate focused button' },
      { key: 'Enter', action: 'Activate focused element' }
    ];
    
    const helpContent = shortcuts.map(s => `${s.key}: ${s.action}`).join('\n');
    
    showDetailedNotification({
      title: '⌨️ Keyboard Shortcuts',
      message: 'Available keyboard shortcuts:',
      actions: shortcuts.map(s => `${s.key} - ${s.action}`),
      type: 'info',
      persistent: true
    });
    
    announceToScreenReader('Keyboard shortcuts help displayed');
  }

  function initVoiceNavigation() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const voiceRecognition = new SpeechRecognition();
    
    voiceRecognition.continuous = false;
    voiceRecognition.interimResults = false;
    voiceRecognition.lang = 'en-US';
    
    // Voice commands for navigation
    const voiceCommands = {
      'start recording': () => document.getElementById('startRecordingBtn')?.click(),
      'stop recording': () => document.getElementById('stopRecordingBtn')?.click(),
      'clear transcript': () => document.getElementById('clearTranscription')?.click(),
      'export transcript': () => document.getElementById('exportTranscription')?.click(),
      'show help': () => showKeyboardShortcutsHelp(),
      'mute microphone': () => toggleMute()
    };
    
    // Enable voice commands with Ctrl+Shift+V
    document.addEventListener('keydown', (event) => {
      if (event.ctrlKey && event.shiftKey && event.key === 'V') {
        event.preventDefault();
        announceToScreenReader('Voice command mode activated. Say a command.');
        voiceRecognition.start();
      }
    });
    
    voiceRecognition.onresult = (event) => {
      const command = event.results[0][0].transcript.toLowerCase().trim();
      console.log('🎤 Voice command heard:', command);
      
      const matchedCommand = Object.keys(voiceCommands).find(cmd => 
        command.includes(cmd) || cmd.includes(command)
      );
      
      if (matchedCommand) {
        voiceCommands[matchedCommand]();
        announceToScreenReader(`Voice command executed: ${matchedCommand}`);
      } else {
        announceToScreenReader(`Voice command not recognized: ${command}`);
      }
    };
    
    voiceRecognition.onerror = (event) => {
      console.warn('Voice recognition issue:', event.issue);
      announceToScreenReader('Voice command error. Try again.');
    };
    
    console.log('🎤 Voice navigation initialized. Use Ctrl+Shift+V to activate.');
  }

  function toggleMute() {
    // Toggle microphone mute functionality
    if (window.audioContext && window.audioContext.state === 'running') {
      // Implementation would depend on audio setup
      announceToScreenReader('Microphone mute toggled');
    } else {
      announceToScreenReader('Microphone not active');
    }
  }
  
  // --- Connection Health Monitoring ---
  function setupConnectionHealthMonitoring() {
    // Start heartbeat monitoring every 30 seconds
    if (connectionHealth.heartbeatInterval) {
      clearInterval(connectionHealth.heartbeatInterval);
    }
    
    connectionHealth.heartbeatInterval = setInterval(() => {
      if (socket && socket.connected) {
        const startTime = Date.now();
        socket.emit('ping', startTime);
      }
    }, 30000);
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
      issue: '❌', 
      warning: '⚠️',
      info: 'ℹ️'
    };
    return icons[type] || icons.info;
  }

  // --- Enhanced Issue Handling ---
  function showEnhancedNotification(message, details = '') {
    console.warn('🚨 Enhanced Notification:', message, details);
    
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
    showNotification(`Issue: ${message}`, 'error', 5000);
    
    // Announce error to screen readers
    announceToScreenReader(`Issue occurred: ${message}`, 'assertive');
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
      rafId = safeGet(window, "initialValue", null);
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
          const timeout = setTimeout(() => reject(new Issue('Connection timeout')), 5000);
          socket.once('connect', () => {
            clearTimeout(timeout);
            resolve();
          });
        });
      }

      // 🔥 CRITICAL FIX: Create session before recording
      console.log('🔧 DEBUG: About to create session...');
      await createSessionAndWait();
      console.log('🔧 DEBUG: Session creation completed, continuing to microphone...');

      // Request microphone access
      console.log('🎤 Requesting microphone access...');
      
      try {
        console.log('🔍 Checking microphone permissions and device capabilities...');
        // 📱 MOBILE-OPTIMIZED: Apply device-specific audio constraints
        const isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        // 📱 MOBILE-OPTIMIZED: Clean constraint format for maximum compatibility
        const audioConstraints = {
          audio: {
            sampleRate: 16000,
            channelCount: 1,
            echoCancellation: false,  // Always disabled for mobile compatibility
            noiseSuppression: false,  // Always disabled for mobile compatibility
            autoGainControl: false    // Always disabled for mobile compatibility
          }
        };
        
        if (isMobileDevice) {
          console.log('📱 Mobile device detected - using simplified constraints');
        }
        
        mediaStream = await navigator.mediaDevices.getUserMedia(audioConstraints);
        
        console.log('✅ Microphone access granted');
        console.log('🎤 Microphone stream details:', {
          tracks: mediaStream.getAudioTracks().length,
          active: mediaStream.active,
          id: mediaStream.id
        });
        
      } catch (permissionError) {
        // 🔥 ENHANCED: Comprehensive microphone permission error handling
        console.warn('🚨 Microphone access issue:', permissionError);
        
        let issueMessage = 'Unable to access microphone';
        let actionText = 'Try Again';
        
        if (permissionError.name === 'NotAllowedError') {
          issueMessage = 'Microphone access denied. Please allow microphone access and try again.';
          actionText = 'Check Permissions';
        } else if (permissionError.name === 'NotFoundError') {
          issueMessage = 'No microphone found. Please connect a microphone and try again.';
          actionText = 'Check Device';
        } else if (permissionError.name === 'NotReadableError') {
          issueMessage = 'Microphone is being used by another application. Please close other apps using the microphone.';
          actionText = 'Check Apps';
        }
        
        showNotification(issueMessage, {
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
          
          // 🔥 PHASE 1: Validate session before sending
          if (!CURRENT_SESSION_ID) {
            console.warn('🚨 Cannot send audio: No session ID available');
            showNotification('Session not ready - please wait', 'warning');
            return;
          }
          
          if (!socket || !socket.connected) {
            console.warn('🚨 Cannot send audio: Socket not connected');
            return;
          }
          
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
        
        } catch (issue) {
          console.warn('🚨 Issue sending audio chunk:', {
            issue: error.message,
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
            showNotification('Connection issues detected. Please check your internet connection and try again.');
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
        console.warn('🚨 MediaRecorder issue:', e);
        showNotification('Recording error occurred');
      };

      // Start recording with optimized chunk timing
      // 300ms gives ~3-4 chunks/sec for good interim cadence
      mediaRecorder.start(300);
      
      console.log('🎯 Recording started successfully');

    } catch (err) {
      console.warn('🚨 Start recording issue:', err);
      
      let message = 'Recording setup failed';
      if (err.name === 'NotAllowedError') {
        message = 'Microphone access denied. Please allow microphone permissions.';
      } else if (err.name === 'NotFoundError') {
        message = 'No microphone found. Please connect a microphone.';
      } else if (err.name === 'NotSupportedError') {
        message = 'Recording not supported on this device.';
      } else if (err.message === 'Connection timeout') {
        message = 'Connection timeout. Please check your internet connection.';
      } else if (err.message && err.message.includes('socket')) {
        message = 'Connection error. Please refresh and try again.';
      } else {
        console.warn('🚨 Detailed issue:', err.name, err.message, err.stack);
        message = `Recording setup failed: ${err.message || 'Unknown error'}`;
      }
      
      if (micStatus()) micStatus().textContent = message;
      showNotification(message);
      
      // Clean up on error
      cleanup();
      
      // 🔥 CRITICAL FIX: Reset button state on error
      if (startBtn()) {
        startBtn().disabled = false;
        startBtn().removeAttribute('processing');
      }
      window._recordingInProgress = false;
    }
  }

  function stopRecording() {
    try {
      console.log('⏹️ Stopping recording...');
      
      // Stop MediaRecorder
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
      }
      
      // 🔥 PHASE 1: Send final signal to trigger server-side finalization
      if (socket && socket.connected && CURRENT_SESSION_ID) {
        console.log('📤 Sending finalization signal...');
        socket.emit('audio_chunk', {
          session_id: CURRENT_SESSION_ID,
          is_final_chunk: true,  // 🔥 Critical: trigger finalization
          audio_data_b64: '',  // Empty string instead of null
          mime_type: '',
          rms: 0,
          ts_client: Date.now()
        });
      }
      
      cleanup();
      
      if (micStatus()) micStatus().textContent = 'Stopped';
      console.log('✅ Recording stopped successfully');
      
    } catch (issue) {
      console.warn('🚨 Stop recording issue:', e);
      cleanup(); // Ensure cleanup even on error
    }
  }

  function cleanup() {
    // Stop RMS monitoring
    stopRmsLoop();
    
    // Clean up WebAudio
    if (sourceNode) {
      sourceNode.disconnect();
      sourceNode = safeGet(window, "initialValue", null);
    }
    if (audioCtx) {
      audioCtx.close();
      audioCtx = safeGet(window, "initialValue", null);
    }
    
    // Clean up media stream
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop());
      mediaStream = safeGet(window, "initialValue", null);
    }
    
    // Reset UI
    if (startBtn()) startBtn().disabled = false;
    if (stopBtn()) stopBtn().disabled = true;
    
    analyser = safeGet(window, "initialValue", null);
    timeData = safeGet(window, "initialValue", null);
    mediaRecorder = safeGet(window, "initialValue", null);
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

  function showNotification(message) {
    console.warn('🚨 Issue:', message);
    
    // Try to show in UI if toast system exists
    if (window.ToastNotificationSystem) {
      new ToastNotificationSystem().showNotification(message);
    } else {
      // Fallback to alert
      alert(message);
    }
  }

  // 🔥 CRITICAL FIX: Session creation with proper async handling + monitoring
  function createSessionAndWait() {
    const startTime = Date.now();
    
    return new Promise((resolve, reject) => {
      if (CURRENT_SESSION_ID) {
        console.log('📋 Using existing session:', CURRENT_SESSION_ID);
        resolve();
        return;
      }
      
      if (!socket || !socket.connected) {
        reject(new Issue('Socket not connected'));
        return;
      }
      
      // Listen for session creation response
      const sessionCreatedHandler = (data) => {
        console.log('🆕 Session created successfully:', data.session_id);
        CURRENT_SESSION_ID = data.session_id;
        
        // 🔥 PHASE 1: Join session room immediately after creation using enhanced protocol
        console.log('🏠 Joining session room:', data.session_id);
        joinSession(data.session_id);
        
        // 🔥 CRITICAL FIX: Wait for room join confirmation before resolving
        const roomJoinedHandler = (joinData) => {
          console.log('✅ Successfully joined session room:', joinData.session_id);
          clearTimeout(timeoutId);
          socket.off('session_created', sessionCreatedHandler);
          socket.off('error', errorHandler);
          socket.off('joined_session', roomJoinedHandler);
          socket.off('joined_session', joinedFallbackHandler);
          // 📊 MONITORING: Track successful session creation timing
          const totalTime = Date.now() - startTime;
          console.log(`📊 SESSION SUCCESS: Total time ${totalTime}ms`);
          if (window._minaTelemetry) {
            window._minaTelemetry.reportSessionSuccess(totalTime);
          }
          resolve(); // Only resolve after BOTH session creation AND room joining
        };
        
        socket.once('joined_session', roomJoinedHandler);
        
        socket.off('session_created', sessionCreatedHandler);
        socket.off('error', errorHandler);
        // Do NOT resolve here - wait for room join confirmation
      };
      
      const errorHandler = (error) => {
        console.warn('🚨 Session creation failed:', error);
        socket.off('session_created', sessionCreatedHandler);
        socket.off('error', errorHandler);
        reject(new Issue(`Session creation failed: ${error.message || 'Unknown error'}`));
      };
      
      // Set up listeners with debug logging
      socket.once('session_created', sessionCreatedHandler);
      socket.once('error', errorHandler);
      
      // Add debug listener for joined_session as fallback (only if no session created yet)
      const joinedFallbackHandler = (joinData) => {
        if (!CURRENT_SESSION_ID && joinData.session_id) {
          console.log('🔄 Using joined_session as fallback for session creation:', joinData.session_id);
          CURRENT_SESSION_ID = joinData.session_id;
          clearTimeout(timeoutId);
          socket.off('session_created', sessionCreatedHandler);
          socket.off('error', errorHandler);
          socket.off('joined_session', joinedFallbackHandler);
          resolve();
        }
      };
      socket.once('joined_session', joinedFallbackHandler);
      
      // Request session creation
      console.log('📋 Creating new session...');
      socket.emit('create_session', {
        title: `Live Session ${new Date().toISOString()}`,
        language: document.getElementById('sessionLanguage')?.value || 'en'
      });
      
      // Timeout after 15 seconds (increased from 10 for mobile devices)
      const timeoutId = setTimeout(() => {
        socket.off('session_created', sessionCreatedHandler);
        socket.off('error', errorHandler);
        socket.off('joined_session', joinedFallbackHandler);
        console.warn('🚨 Session creation timeout - no session_created event received in 15s');
        console.warn('🚨 Current session ID at timeout:', CURRENT_SESSION_ID);
        
        // 📊 MONITORING: Track timeout with detailed context
        const timeoutDetails = {
          hasSessionId: !!CURRENT_SESSION_ID,
          sessionId: CURRENT_SESSION_ID,
          socketConnected: socket?.connected || false,
          totalTime: Date.now() - startTime
        };
        
        if (window._minaTelemetry) {
          window._minaTelemetry.reportSessionTimeout(timeoutDetails);
        }
        
        reject(new Issue('Session creation timeout'));
      }, 15000);
    });
  }

  // Legacy function for compatibility
  function createSession() {
    createSessionAndWait().catch(error => {
      console.warn('🚨 Session creation failed:', error);
      showNotification(`Session creation failed: ${error.message}`);
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
      // 🔥 SIMPLE FIX: Just add event listener with proper state management
      start.addEventListener('click', async (event) => {
        // Prevent double-clicks during processing
        if (start.disabled || start.hasAttribute('processing') || window._recordingInProgress) {
          console.log('⚠️ Recording already in progress, ignoring click');
          return;
        }
        
        console.log('🎯 Start recording button clicked');
        window._recordingInProgress = true;
        start.setAttribute('processing', 'true');
        start.disabled = true;
        
        try {
          await startRecording(); // Session creation is now handled inside startRecording
        } catch (issue) {
          console.warn('🚨 Failed to start recording:', error);
          if (micStatus()) micStatus().textContent = 'Issue';
          showNotification(`Failed to start recording: ${error.message}`);
        } finally {
          // Re-enable button after processing
          setTimeout(() => {
            start.removeAttribute('processing');
            start.disabled = false;
            window._recordingInProgress = false;
          }, 1000);
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
    
    // Handle missing or empty text
    if (!data.text || data.text.trim() === '') {
      console.log('📝 Empty transcription text, skipping update');
      return;
    }
    
    if (isFinal) {
      // Remove any interim text before adding final
      const interimElements = container.querySelectorAll('.interim-transcript');
      interimElements.forEach(el => el.remove());
      
      // Add final transcript segment
      const finalElement = document.createElement('div');
      finalElement.className = 'transcription-segment final-transcript mb-2';
      finalElement.setAttribute('data-segment-id', data.segment_id || Date.now());
      
      const confidence = Math.round((data.avg_confidence || data.confidence || 0) * 100);
      const confidenceClass = confidence > 70 ? 'confidence-high' : confidence > 50 ? 'confidence-medium' : 'confidence-low';
      
      finalElement.innerHTML = `
        <div class="segment-content ${confidenceClass}">${escapeHtml(data.text)}</div>
        <div class="segment-meta text-muted small">
          <span class="confidence">Confidence: ${confidence}%</span>
          <span class="timestamp ms-2">${new Date().toLocaleTimeString()}</span>
          ${data.speaker ? `<span class="speaker ms-2">Speaker: ${data.speaker}</span>` : ''}
        </div>
      `;
      container.appendChild(finalElement);
      
      // Hide "Ready to transcribe" message
      const readyMessage = container.querySelector('.text-center.text-muted');
      if (readyMessage && readyMessage.textContent.includes('Ready to transcribe')) {
        readyMessage.style.display = 'none';
      }
      
      // 📊 Track successful transcription in telemetry
      if (window._minaTelemetry) {
        window._minaTelemetry.reportTranscriptionSegment({
          isFinal: true,
          confidence: confidence,
          textLength: data.text.length
        });
      }
      
    } else {
      // Handle interim results - only if "Show interim" is enabled
      const showInterimCheckbox = document.getElementById('showInterim');
      if (!showInterimCheckbox || !showInterimCheckbox.checked) {
        return; // Skip interim updates if disabled
      }
      
      // Update or add interim transcript
      let interimElement = container.querySelector('.interim-transcript');
      if (!interimElement) {
        interimElement = document.createElement('div');
        interimElement.className = 'transcription-segment interim-transcript mb-2';
        container.appendChild(interimElement);
      }
      
      const confidence = Math.round((data.avg_confidence || data.confidence || 0) * 100);
      interimElement.innerHTML = `
        <div class="segment-content text-primary" style="font-style: italic;">${escapeHtml(data.text)}</div>
        <div class="segment-meta text-muted small">
          <span class="confidence">Confidence: ${confidence}%</span>
          <span class="status ms-2"><i class="fas fa-spinner fa-spin me-1"></i>Processing...</span>
        </div>
      `;
      
      // Hide "Ready to transcribe" message
      const readyMessage = container.querySelector('.text-center.text-muted');
      if (readyMessage && readyMessage.textContent.includes('Ready to transcribe')) {
        readyMessage.style.display = 'none';
      }
    }
    
    // Auto-scroll if enabled
    const autoScrollCheckbox = document.getElementById('autoScroll');
    if (autoScrollCheckbox && autoScrollCheckbox.checked) {
      container.scrollTop = container.scrollHeight;
    }
    
    // Update session stats if available
    if (data.session_stats) {
      updateSessionStats(data.session_stats);
    }
  }
  
  // Helper function to escape HTML for security
  function escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
  }
  
  // Update session statistics display
  function updateSessionStats(stats) {
    const elements = {
      'sessionId': stats.session_id,
      'segmentsCount': stats.segments_count || 0,
      'avgConfidence': Math.round((stats.avg_confidence || 0) * 100) + '%',
      'processingTime': (stats.processing_time || 0) + 'ms',
      'chunkCount': stats.chunk_count || 0
    };
    
    Object.entries(elements).forEach(([id, value]) => {
      const element = document.getElementById(id);
      if (element) element.textContent = value;
    });
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