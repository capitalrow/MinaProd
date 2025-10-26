/**
 * Enhanced Live Recording Client
 * Features: Real-time waveform, multi-speaker display, WebSocket streaming
 */

class LiveRecordingClient {
  constructor() {
    // State
    this.state = 'idle'; // idle, ready, recording, processing
    this.sessionExternalId = null;
    this.mediaRecorder = null;
    this.audioStream = null;
    this.audioContext = null;
    this.analyser = null;
    this.socket = null;
    this.recordingStartTime = null;
    this.timerInterval = null;
    
    // Multi-speaker transcript state
    this.currentSpeaker = null;
    this.segments = [];
    
    // Waveform visualization
    this.waveformBars = [];
    this.animationFrameId = null;
    
    // DOM elements
    this.elements = {
      status: document.getElementById('recorder-status'),
      statusText: document.getElementById('status-text'),
      statusDot: document.querySelector('.status-dot'),
      recordButton: document.getElementById('record-button'),
      pauseButton: document.getElementById('pause-button'),
      stopButton: document.getElementById('stop-button'),
      timer: document.getElementById('recording-time'),
      waveformContainer: document.getElementById('waveform-container'),
      transcriptContent: document.getElementById('transcript-content'),
      sessionId: document.getElementById('session-id-value'),
      wordsSpoken: document.getElementById('words-spoken-value'),
      speakersDetected: document.getElementById('speakers-detected-value')
    };
    
    this.init();
  }
  
  init() {
    console.log('🎙️ Initializing Live Recording Client...');
    this.setupSocketIO();
    this.setupEventListeners();
    this.setupWaveform();
    this.setState('ready');
  }
  
  setupSocketIO() {
    // Connect to the correct namespace
    this.socket = io('/live-transcription', {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      timeout: 20000
    });
    
    this.socket.on('connect', () => {
      console.log('✅ Socket connected');
      this.setState('ready');
    });
    
    this.socket.on('disconnect', () => {
      console.log('❌ Socket disconnected');
      if (this.state === 'recording') {
        this.showError('Connection lost. Attempting to reconnect...');
      }
    });
    
    this.socket.on('connected', (data) => {
      console.log('📡 Connected to live transcription:', data);
    });
    
    this.socket.on('record_start', (data) => {
      console.log('🎬 Recording started:', data);
      if (data.session) {
        this.sessionExternalId = data.session.external_id;
        if (this.elements.sessionId) {
          this.elements.sessionId.textContent = data.session.external_id;
        }
      }
    });
    
    // Multi-speaker transcript events
    this.socket.on('transcript_partial', (data) => {
      this.handleTranscriptUpdate(data, false);
    });
    
    this.socket.on('transcript_segment', (data) => {
      this.handleTranscriptUpdate(data, true);
    });
    
    this.socket.on('session_finalized', (data) => {
      console.log('✅ Session finalized:', data);
      this.handleRecordingComplete();
    });
    
    this.socket.on('error', (data) => {
      console.error('❌ Socket error:', data);
      this.showError(data.message || 'An error occurred');
    });
  }
  
  setupEventListeners() {
    if (this.elements.recordButton) {
      this.elements.recordButton.addEventListener('click', () => this.startRecording());
    }
    
    if (this.elements.pauseButton) {
      this.elements.pauseButton.addEventListener('click', () => this.pauseRecording());
    }
    
    if (this.elements.stopButton) {
      this.elements.stopButton.addEventListener('click', () => this.stopRecording());
    }
  }
  
  setupWaveform() {
    if (!this.elements.waveformContainer) return;
    
    // Create 40 waveform bars
    const waveformEl = document.createElement('div');
    waveformEl.className = 'waveform';
    
    for (let i = 0; i < 40; i++) {
      const bar = document.createElement('div');
      bar.className = 'waveform-bar';
      bar.style.height = '20px';
      waveformEl.appendChild(bar);
      this.waveformBars.push(bar);
    }
    
    this.elements.waveformContainer.innerHTML = '';
    this.elements.waveformContainer.appendChild(waveformEl);
  }
  
  async startRecording() {
    try {
      this.setState('initializing');
      
      // Request microphone access
      this.audioStream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      
      // Setup audio context for waveform
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = this.audioContext.createMediaStreamSource(this.audioStream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      source.connect(this.analyser);
      
      // Start waveform animation
      this.startWaveformAnimation();
      
      // Setup MediaRecorder with best available format
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        const alternatives = ['audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus'];
        mimeType = alternatives.find(type => MediaRecorder.isTypeSupported(type)) || '';
      }
      
      const options = mimeType ? { mimeType } : {};
      this.mediaRecorder = new MediaRecorder(this.audioStream, options);
      
      // Start session on server
      this.socket.emit('start_session', {
        title: `Meeting - ${new Date().toLocaleString()}`,
        locale: 'en',
        device_info: navigator.userAgent
      });
      
      // Handle audio chunks
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.sendAudioChunk(event.data);
        }
      };
      
      // Start recording with 1-second chunks for real-time processing
      this.mediaRecorder.start(1000);
      this.recordingStartTime = Date.now();
      this.startTimer();
      this.setState('recording');
      
      console.log('🎙️ Recording started');
      
    } catch (error) {
      console.error('❌ Failed to start recording:', error);
      this.showError('Failed to access microphone. Please check permissions.');
      this.setState('ready');
    }
  }
  
  pauseRecording() {
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.pause();
      this.stopTimer();
      this.setState('paused');
    } else if (this.mediaRecorder && this.mediaRecorder.state === 'paused') {
      this.mediaRecorder.resume();
      this.startTimer();
      this.setState('recording');
    }
  }
  
  stopRecording() {
    if (!this.mediaRecorder) return;
    
    this.setState('processing');
    
    // Stop media recorder
    if (this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }
    
    // Stop audio stream
    if (this.audioStream) {
      this.audioStream.getTracks().forEach(track => track.stop());
    }
    
    // Stop waveform
    this.stopWaveformAnimation();
    
    // Stop timer
    this.stopTimer();
    
    // Finalize session on server
    this.socket.emit('end_session', {});
    
    console.log('🛑 Recording stopped');
  }
  
  async sendAudioChunk(blob) {
    try {
      const arrayBuffer = await blob.arrayBuffer();
      this.socket.emit('audio_data', {
        data: arrayBuffer,
        mimeType: this.mediaRecorder.mimeType
      });
    } catch (error) {
      console.error('❌ Failed to send audio chunk:', error);
    }
  }
  
  handleTranscriptUpdate(data, isFinal) {
    const { text, speaker, timestamp, speaker_id } = data;
    
    if (!text || text.trim() === '') return;
    
    // Check if speaker changed or if this is final
    if (isFinal || this.currentSpeaker !== speaker_id) {
      // Create new segment
      this.addTranscriptSegment({
        speaker: speaker || `Speaker ${speaker_id || 1}`,
        speaker_id: speaker_id || 1,
        text: text.trim(),
        timestamp: timestamp || new Date().toISOString(),
        isFinal: isFinal
      });
      
      this.currentSpeaker = speaker_id;
    } else {
      // Update current segment
      this.updateLastSegment(text.trim());
    }
    
    // Update word count
    this.updateMetrics();
  }
  
  addTranscriptSegment(segment) {
    this.segments.push(segment);
    
    const segmentEl = document.createElement('div');
    segmentEl.className = `transcript-segment ${segment.isFinal ? '' : 'interim'}`;
    segmentEl.dataset.speakerId = segment.speaker_id;
    
    // Speaker label with color coding
    const speakerEl = document.createElement('div');
    speakerEl.className = 'transcript-speaker';
    speakerEl.style.color = this.getSpeakerColor(segment.speaker_id);
    speakerEl.textContent = segment.speaker;
    
    // Transcript text
    const textEl = document.createElement('div');
    textEl.className = 'transcript-text';
    textEl.textContent = segment.text;
    
    // Timestamp
    const timestampEl = document.createElement('div');
    timestampEl.className = 'transcript-timestamp';
    timestampEl.textContent = this.formatTimestamp(segment.timestamp);
    
    // Interim indicator
    if (!segment.isFinal) {
      const indicator = document.createElement('span');
      indicator.className = 'interim-indicator';
      indicator.textContent = '●';
      textEl.appendChild(indicator);
    }
    
    segmentEl.appendChild(speakerEl);
    segmentEl.appendChild(textEl);
    segmentEl.appendChild(timestampEl);
    
    if (this.elements.transcriptContent) {
      this.elements.transcriptContent.appendChild(segmentEl);
      // Auto-scroll to bottom
      segmentEl.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }
  
  updateLastSegment(text) {
    if (this.segments.length === 0) return;
    
    const lastSegment = this.segments[this.segments.length - 1];
    lastSegment.text = text;
    
    const segmentEls = this.elements.transcriptContent?.querySelectorAll('.transcript-segment');
    if (segmentEls && segmentEls.length > 0) {
      const lastEl = segmentEls[segmentEls.length - 1];
      const textEl = lastEl.querySelector('.transcript-text');
      if (textEl) {
        textEl.textContent = text;
        
        // Add interim indicator
        const indicator = document.createElement('span');
        indicator.className = 'interim-indicator';
        indicator.textContent = '●';
        textEl.appendChild(indicator);
      }
    }
  }
  
  getSpeakerColor(speakerId) {
    const colors = [
      '#667eea', // Speaker 1 - Purple
      '#f093fb', // Speaker 2 - Pink
      '#4facfe', // Speaker 3 - Blue
      '#43e97b', // Speaker 4 - Green
      '#fa709a', // Speaker 5 - Rose
      '#feca57', // Speaker 6 - Yellow
    ];
    return colors[(speakerId - 1) % colors.length];
  }
  
  formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  }
  
  updateMetrics() {
    // Count words
    const totalWords = this.segments.reduce((sum, seg) => {
      return sum + seg.text.split(/\s+/).filter(w => w.length > 0).length;
    }, 0);
    
    // Count unique speakers
    const uniqueSpeakers = new Set(this.segments.map(seg => seg.speaker_id));
    
    if (this.elements.wordsSpoken) {
      this.elements.wordsSpoken.textContent = totalWords;
    }
    
    if (this.elements.speakersDetected) {
      this.elements.speakersDetected.textContent = uniqueSpeakers.size;
    }
  }
  
  startWaveformAnimation() {
    if (!this.analyser) return;
    
    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const animate = () => {
      this.animationFrameId = requestAnimationFrame(animate);
      
      this.analyser.getByteFrequencyData(dataArray);
      
      // Update each bar with audio data
      this.waveformBars.forEach((bar, i) => {
        const index = Math.floor(i * bufferLength / this.waveformBars.length);
        const value = dataArray[index];
        const height = Math.max(20, (value / 255) * 100);
        bar.style.height = `${height}px`;
      });
      
      // Add active state if audio detected
      const avgVolume = dataArray.reduce((a, b) => a + b) / bufferLength;
      if (avgVolume > 10) {
        this.elements.waveformContainer?.classList.add('active');
      } else {
        this.elements.waveformContainer?.classList.remove('active');
      }
    };
    
    animate();
  }
  
  stopWaveformAnimation() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    
    // Reset bars
    this.waveformBars.forEach(bar => {
      bar.style.height = '20px';
    });
    
    this.elements.waveformContainer?.classList.remove('active');
  }
  
  startTimer() {
    this.timerInterval = setInterval(() => {
      const elapsed = Date.now() - this.recordingStartTime;
      const hours = Math.floor(elapsed / 3600000);
      const minutes = Math.floor((elapsed % 3600000) / 60000);
      const seconds = Math.floor((elapsed % 60000) / 1000);
      
      const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      
      if (this.elements.timer) {
        this.elements.timer.textContent = timeString;
      }
    }, 1000);
  }
  
  stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }
  
  setState(newState) {
    this.state = newState;
    
    // Update status UI
    const statusMap = {
      idle: { text: 'Initializing...', class: '' },
      ready: { text: 'Ready to Record', class: '' },
      initializing: { text: 'Starting...', class: '' },
      recording: { text: 'Recording', class: 'recording' },
      paused: { text: 'Paused', class: 'paused' },
      processing: { text: 'Processing...', class: 'processing' }
    };
    
    const status = statusMap[newState] || statusMap.idle;
    
    if (this.elements.status) {
      this.elements.status.className = `recorder-status ${status.class}`;
    }
    
    if (this.elements.statusText) {
      this.elements.statusText.textContent = status.text;
    }
    
    // Update button states
    if (this.elements.recordButton) {
      this.elements.recordButton.disabled = newState !== 'ready';
      this.elements.recordButton.classList.toggle('recording', newState === 'recording');
    }
    
    if (this.elements.pauseButton) {
      this.elements.pauseButton.disabled = !['recording', 'paused'].includes(newState);
    }
    
    if (this.elements.stopButton) {
      this.elements.stopButton.disabled = !['recording', 'paused'].includes(newState);
    }
  }
  
  handleRecordingComplete() {
    if (!this.sessionExternalId) {
      console.warn('⚠️ No session ID, redirecting to dashboard');
      setTimeout(() => window.location.href = '/dashboard', 2000);
      return;
    }
    
    // Show processing overlay
    this.showProcessingOverlay();
    
    // Redirect to session detail page after 2 seconds
    setTimeout(() => {
      window.location.href = `/sessions/${this.sessionExternalId}`;
    }, 2000);
  }
  
  showProcessingOverlay() {
    // Create overlay if it doesn't exist
    let overlay = document.getElementById('processing-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'processing-overlay';
      overlay.className = 'processing-overlay';
      overlay.innerHTML = `
        <div class="processing-content">
          <div class="spinner"></div>
          <h2>Processing Your Recording...</h2>
          <p>Generating transcript, summary, and insights</p>
        </div>
      `;
      document.body.appendChild(overlay);
    }
    overlay.style.display = 'flex';
  }
  
  showError(message) {
    // Simple toast notification
    const toast = document.createElement('div');
    toast.className = 'toast error';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.classList.add('fadeout');
      setTimeout(() => toast.remove(), 300);
    }, 5000);
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.liveRecorder = new LiveRecordingClient();
  });
} else {
  window.liveRecorder = new LiveRecordingClient();
}
