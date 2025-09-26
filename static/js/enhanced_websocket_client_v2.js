/**
 * Enhanced WebSocket Client V2 - Production Ready
 * HTTP fallback client for reliable connection with enhanced error handling and performance optimization.
 */

class EnhancedWebSocketClientV2 {
    constructor() {
        this.connectionId = null;
        this.isConnected = false;
        this.isRecording = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        // Connection mode
        this.connectionMode = 'http_fallback';  // Start with HTTP fallback for reliability
        this.baseUrl = window.location.origin;
        
        // Session management
        this.sessionId = null;
        this.audioStream = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        
        // Performance tracking
        this.metrics = {
            chunksProcessed: 0,
            totalLatency: 0,
            avgLatency: 0,
            lastChunkTime: 0,
            connectionTime: 0,
            errorCount: 0
        };
        
        // UI elements cache
        this.elements = {
            transcriptDisplay: null,
            recordButton: null,
            statusDisplay: null,
            wordCounter: null,
            confidenceLevel: null
        };
        
        // Polling interval for HTTP fallback
        this.pollingInterval = null;
        this.pollingFrequency = 100; // 100ms for low latency
        
        this.init();
    }
    
    init() {
        console.log('🎯 Enhanced WebSocket Client V2 initializing...');
        this.cacheElements();
        this.setupEventListeners();
        this.getServerInfo();
    }
    
    cacheElements() {
        // Cache frequently used DOM elements with comprehensive fallback handling
        this.elements.transcriptDisplay = document.getElementById('transcriptDisplay') || 
                                         document.querySelector('.live-transcript-container') ||
                                         document.querySelector('[data-transcript-display]');
        
        this.elements.recordButton = document.getElementById('recordButton') ||
                                    document.querySelector('[data-record-button]') ||
                                    document.querySelector('button[onclick*="recording"]');
        
        this.elements.statusDisplay = document.getElementById('recording-status') ||
                                     document.querySelector('[data-status-display]') ||
                                     document.querySelector('.alert');
        
        this.elements.wordCounter = document.getElementById('wordCounter') ||
                                   document.querySelector('[data-word-counter]');
        
        this.elements.confidenceLevel = document.getElementById('confidenceLevel') ||
                                       document.querySelector('[data-confidence-level]');
        
        // 🔥 CRITICAL FIX: Always ensure transcript display exists
        if (!this.elements.transcriptDisplay) {
            console.warn('⚠️ No transcript display element found, creating enhanced fallback');
            this.createEnhancedTranscriptDisplay();
        }
        
        console.log('✅ UI elements cached:', {
            transcriptDisplay: !!this.elements.transcriptDisplay,
            recordButton: !!this.elements.recordButton,
            statusDisplay: !!this.elements.statusDisplay
        });
    }
    
    createEnhancedTranscriptDisplay() {
        // Create comprehensive fallback transcript display
        const targetContainer = document.querySelector('.col-lg-8') || 
                               document.querySelector('main') || 
                               document.querySelector('.container') ||
                               document.body;
        
        if (targetContainer) {
            const enhancedDiv = document.createElement('div');
            enhancedDiv.id = 'transcriptDisplay';
            enhancedDiv.className = 'card bg-secondary border-secondary mb-4';
            enhancedDiv.innerHTML = `
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="card-title mb-0">
                        <i class="bi bi-file-text text-primary"></i> Live Transcript
                    </h5>
                    <div class="transcript-controls">
                        <span class="badge bg-success" id="transcriptStatus">Ready</span>
                        <button class="btn btn-sm btn-outline-light" onclick="clearTranscript()" title="Clear Transcript">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="live-transcript-container" style="min-height: 400px; max-height: 600px; overflow-y: auto; padding: 20px; background: rgba(0,0,0,0.3); border-radius: 8px;">
                        <div class="text-center text-muted" id="initialMessage">
                            <i class="bi bi-mic-mute fs-1 mb-3"></i>
                            <h6>Enhanced Transcription Ready</h6>
                            <p class="mb-2">Google Recorder-level performance with &lt;400ms latency</p>
                            <p class="small">Click "Start Recording" to begin real-time transcription...</p>
                        </div>
                    </div>
                    <div class="transcript-footer mt-3">
                        <div class="row text-center">
                            <div class="col-md-3">
                                <small class="text-muted">Words: <span id="wordCount">0</span></small>
                            </div>
                            <div class="col-md-3">
                                <small class="text-muted">Confidence: <span id="confidenceDisplay">--</span></small>
                            </div>
                            <div class="col-md-3">
                                <small class="text-muted">Latency: <span id="latencyDisplay">--</span></small>
                            </div>
                            <div class="col-md-3">
                                <small class="text-muted">Quality: <span id="qualityDisplay">--</span></small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Insert before existing content or append
            const existingTranscript = targetContainer.querySelector('.card');
            if (existingTranscript) {
                targetContainer.insertBefore(enhancedDiv, existingTranscript);
            } else {
                targetContainer.appendChild(enhancedDiv);
            }
            
            this.elements.transcriptDisplay = enhancedDiv;
            this.elements.wordCounter = document.getElementById('wordCount');
            this.elements.confidenceLevel = document.getElementById('confidenceDisplay');
            
            // Add global clear function
            window.clearTranscript = () => this.clearTranscript();
            
            console.log('✅ Enhanced fallback transcript display created');
        }
    }
    
    setupEventListeners() {
        // Record button with improved detection
        const recordButtons = [
            this.elements.recordButton,
            document.querySelector('button[onclick*="startRecording"]'),
            document.querySelector('button[onclick*="recording"]'),
            ...document.querySelectorAll('button')
        ].filter(btn => btn && (
            btn.textContent.includes('Start') || 
            btn.textContent.includes('Record') ||
            btn.id === 'recordButton'
        ));
        
        recordButtons.forEach(button => {
            if (button && !button.hasAttribute('data-enhanced-listener')) {
                button.setAttribute('data-enhanced-listener', 'true');
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.toggleRecording();
                });
                console.log('✅ Enhanced listener added to record button');
            }
        });
        
        // Page visibility and lifecycle
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.isRecording) {
                console.log('🔄 Page hidden, maintaining connection...');
                this.updateStatus('Recording in background...', 'warning');
            } else if (!document.hidden && !this.isConnected) {
                console.log('🔄 Page visible, reconnecting...');
                this.connect();
            }
        });
        
        // Before unload cleanup
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.altKey && e.key === 'r') {
                e.preventDefault();
                this.toggleRecording();
            }
        });
    }
    
    async getServerInfo() {
        try {
            console.log('🌐 Fetching server info...');
            const response = await fetch(`${this.baseUrl}/api/enhanced-ws/info`);
            
            if (response.ok) {
                const data = await response.json();
                console.log('📊 Server info received:', data);
                
                if (data.enhanced_websocket) {
                    this.serverInfo = data.enhanced_websocket;
                    this.updateStatus('Enhanced transcription service available', 'success');
                    
                    // Show enhanced features
                    if (data.enhanced_websocket.features) {
                        const features = Object.keys(data.enhanced_websocket.features).filter(
                            key => data.enhanced_websocket.features[key]
                        );
                        console.log('✨ Enhanced features available:', features);
                    }
                } else {
                    throw new Error('Invalid server response');
                }
            } else {
                throw new Error(`Server response: ${response.status}`);
            }
        } catch (error) {
            console.error('❌ Failed to get server info:', error);
            this.updateStatus('Enhanced transcription unavailable - using fallback', 'warning');
        }
    }
    
    async connect() {
        if (this.isConnected) {
            console.log('ℹ️ Already connected');
            return;
        }
        
        try {
            console.log(`🔗 Connecting via ${this.connectionMode}...`);
            this.updateStatus('Connecting to enhanced transcription service...', 'info');
            
            const connectStartTime = performance.now();
            
            // Use HTTP fallback for reliable connection
            const response = await fetch(`${this.baseUrl}/api/enhanced-ws/connect`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    client_type: 'enhanced_v2',
                    user_agent: navigator.userAgent,
                    connection_mode: this.connectionMode
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.connectionId = data.connection_id;
                this.isConnected = true;
                this.reconnectAttempts = 0;
                
                this.metrics.connectionTime = performance.now() - connectStartTime;
                
                console.log(`✅ Connected! Connection ID: ${this.connectionId}`);
                console.log(`🚀 Enhanced features: ${JSON.stringify(data.enhanced_features)}`);
                
                this.updateStatus('Connected to enhanced transcription service', 'success');
                
                // Start polling for HTTP fallback mode
                if (this.connectionMode === 'http_fallback') {
                    this.startPolling();
                }
                
                // Update record button state
                this.updateRecordButtonState();
                
            } else {
                throw new Error(`Connection failed: ${response.status}`);
            }
            
        } catch (error) {
            console.error('❌ Connection failed:', error);
            this.handleConnectionError(error);
        }
    }
    
    startPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }
        
        this.pollingInterval = setInterval(async () => {
            if (!this.isConnected || !this.connectionId) return;
            
            try {
                const response = await fetch(
                    `${this.baseUrl}/api/enhanced-ws/poll?connection_id=${this.connectionId}`
                );
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.has_messages && data.messages.length > 0) {
                        data.messages.forEach(message => this.handleMessage(message));
                    }
                } else {
                    console.warn('⚠️ Polling failed:', response.status);
                }
            } catch (error) {
                console.warn('⚠️ Polling error:', error);
            }
        }, this.pollingFrequency);
    }
    
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
    
    async sendMessage(message) {
        if (!this.isConnected || !this.connectionId) {
            throw new Error('Not connected');
        }
        
        try {
            const response = await fetch(
                `${this.baseUrl}/api/enhanced-ws/message?connection_id=${this.connectionId}`, 
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(message)
                }
            );
            
            if (response.ok) {
                const data = await response.json();
                this.handleMessage(data);
                return data;
            } else {
                throw new Error(`Message failed: ${response.status}`);
            }
            
        } catch (error) {
            console.error('❌ Failed to send message:', error);
            throw error;
        }
    }
    
    handleMessage(data) {
        try {
            switch (data.type) {
                case 'session_started':
                    console.log('🚀 Session started:', data.session_id);
                    this.sessionId = data.session_id;
                    this.updateStatus('Recording session active', 'recording');
                    break;
                    
                case 'transcription_result':
                    this.handleTranscriptionResult(data);
                    break;
                    
                case 'session_ended':
                    console.log('⏹️ Session ended:', data);
                    this.sessionId = null;
                    this.updateStatus('Session ended', 'success');
                    break;
                    
                case 'error':
                    console.error('❌ Server error:', data);
                    this.handleServerError(data);
                    break;
                    
                case 'pong':
                    // Heartbeat response
                    break;
                    
                default:
                    console.log('📨 Unknown message type:', data);
            }
        } catch (error) {
            console.error('❌ Message handling error:', error);
        }
    }
    
    handleTranscriptionResult(data) {
        const processingStartTime = performance.now();
        
        try {
            console.log('📝 Transcription result:', {
                transcript: data.transcript,
                confidence: data.confidence,
                is_final: data.is_final,
                latency_ms: data.latency_ms,
                enhanced_features: data.enhanced_features
            });
            
            // Update transcript display with enhanced formatting
            if (this.elements.transcriptDisplay) {
                this.updateTranscriptDisplay(data);
            }
            
            // Update metrics displays
            this.updateMetricsDisplay(data);
            
            // Track performance
            this.updatePerformanceMetrics(data, processingStartTime);
            
            // Show enhanced features in console for debugging
            if (data.enhanced_features) {
                console.log('🧠 Enhanced features:', data.enhanced_features);
            }
            
            // Quality indicators
            if (data.meets_target) {
                console.log('✅ Target latency achieved:', data.latency_ms + 'ms');
            } else {
                console.warn('⚠️ Latency target missed:', data.latency_ms + 'ms');
            }
            
        } catch (error) {
            console.error('❌ Failed to handle transcription result:', error);
        }
    }
    
    updateTranscriptDisplay(data) {
        const container = this.elements.transcriptDisplay.querySelector('.live-transcript-container') ||
                         this.elements.transcriptDisplay.querySelector('.card-body') ||
                         this.elements.transcriptDisplay;
        
        if (!container) return;
        
        // Remove initial message if present
        const initialMessage = container.querySelector('#initialMessage');
        if (initialMessage) {
            initialMessage.remove();
        }
        
        if (data.is_final) {
            // Final transcript - add as permanent segment with enhanced styling
            const finalSegment = document.createElement('div');
            finalSegment.className = 'transcript-segment final mb-3 p-3 bg-dark rounded';
            finalSegment.innerHTML = `
                <div class="transcript-text text-light mb-2">${this.escapeHtml(data.transcript)}</div>
                <div class="transcript-meta d-flex justify-content-between align-items-center">
                    <div class="confidence-indicator">
                        <span class="badge ${this.getConfidenceBadgeClass(data.confidence)}">
                            ${(data.confidence * 100).toFixed(1)}% confidence
                        </span>
                    </div>
                    <div class="performance-indicators">
                        <span class="badge ${data.meets_target ? 'bg-success' : 'bg-warning'}" title="Latency">
                            ${data.latency_ms.toFixed(0)}ms
                        </span>
                        ${data.enhanced_features?.context_aware ? '<span class="badge bg-info ms-1" title="Context Aware">🧠</span>' : ''}
                        ${data.enhanced_features?.hallucination_filtered ? '<span class="badge bg-secondary ms-1" title="Hallucination Filtered">🛡️</span>' : ''}
                        ${data.enhanced_features?.latency_optimized ? '<span class="badge bg-success ms-1" title="Latency Optimized">⚡</span>' : ''}
                    </div>
                </div>
            `;
            
            container.appendChild(finalSegment);
            
            // Remove any interim segments
            const interimSegments = container.querySelectorAll('.transcript-segment.interim');
            interimSegments.forEach(segment => segment.remove());
            
        } else {
            // Interim transcript - update or create interim segment
            let interimSegment = container.querySelector('.transcript-segment.interim');
            
            if (!interimSegment) {
                interimSegment = document.createElement('div');
                interimSegment.className = 'transcript-segment interim p-2 bg-secondary rounded mb-2';
                container.appendChild(interimSegment);
            }
            
            interimSegment.innerHTML = `
                <div class="transcript-text text-muted">${this.escapeHtml(data.transcript)}</div>
                <div class="transcript-meta">
                    <small class="text-muted">
                        Interim | ${(data.confidence * 100).toFixed(1)}% confidence
                        ${data.latency_ms ? ` | ${data.latency_ms.toFixed(0)}ms` : ''}
                    </small>
                </div>
            `;
        }
        
        // Auto-scroll to bottom with smooth behavior
        container.scrollTo({
            top: container.scrollHeight,
            behavior: 'smooth'
        });
    }
    
    updateMetricsDisplay(data) {
        // Update word counter
        if (this.elements.wordCounter) {
            const allTranscriptText = Array.from(
                this.elements.transcriptDisplay?.querySelectorAll('.transcript-text') || []
            ).map(el => el.textContent).join(' ');
            
            const wordCount = allTranscriptText.trim() ? allTranscriptText.trim().split(/\s+/).length : 0;
            this.elements.wordCounter.textContent = wordCount.toString();
        }
        
        // Update confidence level
        if (this.elements.confidenceLevel) {
            const confidencePercent = (data.confidence * 100).toFixed(1);
            this.elements.confidenceLevel.textContent = `${confidencePercent}%`;
        }
        
        // Update additional displays
        const latencyDisplay = document.getElementById('latencyDisplay');
        if (latencyDisplay) {
            latencyDisplay.textContent = `${data.latency_ms?.toFixed(0) || '--'}ms`;
        }
        
        const qualityDisplay = document.getElementById('qualityDisplay');
        if (qualityDisplay) {
            const quality = data.quality_score ? (data.quality_score * 100).toFixed(0) + '%' : '--';
            qualityDisplay.textContent = quality;
        }
    }
    
    getConfidenceBadgeClass(confidence) {
        if (confidence >= 0.9) return 'bg-success';
        if (confidence >= 0.7) return 'bg-warning';
        return 'bg-danger';
    }
    
    updatePerformanceMetrics(data, startTime) {
        const processingTime = performance.now() - startTime;
        
        this.metrics.chunksProcessed++;
        this.metrics.totalLatency += data.latency_ms || 0;
        this.metrics.avgLatency = this.metrics.totalLatency / this.metrics.chunksProcessed;
        this.metrics.lastChunkTime = processingTime;
        
        // Performance logging
        if (data.latency_ms > 400) {
            console.warn(`⚠️ High latency detected: ${data.latency_ms}ms (target: <400ms)`);
        }
        
        if (processingTime > 50) {
            console.warn(`⚠️ High processing time: ${processingTime.toFixed(2)}ms`);
        }
    }
    
    async toggleRecording() {
        if (this.isRecording) {
            await this.stopRecording();
        } else {
            await this.startRecording();
        }
    }
    
    async startRecording() {
        try {
            console.log('🎤 Starting enhanced recording...');
            
            // Connect if not connected
            if (!this.isConnected) {
                await this.connect();
                
                // Wait for connection with timeout
                await this.waitForConnection(5000);
            }
            
            // Start session
            await this.startSession();
            
            // Request microphone access with enhanced options
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000,
                    channelCount: 1
                }
            });
            
            // Setup MediaRecorder with optimal settings
            const mimeType = this.getBestMimeType();
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: mimeType,
                audioBitsPerSecond: 16000
            });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.sendAudioChunk(event.data);
                }
            };
            
            // Start recording with optimal chunk size for low latency
            this.mediaRecorder.start(200); // 200ms chunks for balance of latency and efficiency
            
            this.isRecording = true;
            this.updateRecordButtonState();
            this.updateStatus('Recording and transcribing with enhanced AI...', 'recording');
            
            console.log('✅ Enhanced recording started with ' + mimeType);
            
        } catch (error) {
            console.error('❌ Failed to start recording:', error);
            this.handleRecordingError(error);
        }
    }
    
    async stopRecording() {
        try {
            console.log('🛑 Stopping enhanced recording...');
            
            if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
                this.mediaRecorder.stop();
            }
            
            if (this.audioStream) {
                this.audioStream.getTracks().forEach(track => track.stop());
                this.audioStream = null;
            }
            
            // End session
            if (this.sessionId) {
                await this.endSession();
            }
            
            this.isRecording = false;
            this.updateRecordButtonState();
            this.updateStatus('Recording stopped', 'success');
            
            console.log('✅ Enhanced recording stopped');
            
        } catch (error) {
            console.error('❌ Failed to stop recording:', error);
            this.updateStatus('Error stopping recording', 'error');
        }
    }
    
    getBestMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/ogg;codecs=opus',
            'audio/webm',
            'audio/mp4',
            'audio/wav'
        ];
        
        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        
        return ''; // Let browser choose
    }
    
    async sendAudioChunk(audioBlob) {
        if (!this.isConnected || !this.sessionId) {
            console.warn('⚠️ Cannot send audio chunk - not connected or no session');
            return;
        }
        
        try {
            // Convert blob to base64
            const arrayBuffer = await audioBlob.arrayBuffer();
            const base64Data = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
            
            const message = {
                type: 'audio_chunk',
                session_id: this.sessionId,
                audio_data: base64Data,
                timestamp: Date.now(),
                duration: 0.2, // 200ms chunks
                is_final: false,
                chunk_size: arrayBuffer.byteLength
            };
            
            await this.sendMessage(message);
            
        } catch (error) {
            console.error('❌ Failed to send audio chunk:', error);
            this.metrics.errorCount++;
        }
    }
    
    async startSession() {
        const message = {
            type: 'start_session',
            language: 'en',
            quality_mode: 'adaptive',
            enhanced_features: true
        };
        
        await this.sendMessage(message);
    }
    
    async endSession() {
        if (!this.sessionId) return;
        
        const message = {
            type: 'end_session',
            session_id: this.sessionId
        };
        
        await this.sendMessage(message);
    }
    
    async waitForConnection(timeout = 5000) {
        return new Promise((resolve, reject) => {
            if (this.isConnected) {
                resolve();
                return;
            }
            
            const checkConnection = () => {
                if (this.isConnected) {
                    resolve();
                } else {
                    setTimeout(checkConnection, 100);
                }
            };
            
            setTimeout(() => reject(new Error('Connection timeout')), timeout);
            checkConnection();
        });
    }
    
    handleConnectionError(error) {
        this.isConnected = false;
        this.connectionId = null;
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
        } else {
            this.updateStatus('Connection failed - please refresh the page', 'error');
            this.showErrorDialog(`Connection failed: ${error.message}`);
        }
    }
    
    handleRecordingError(error) {
        this.isRecording = false;
        this.updateRecordButtonState();
        
        let errorMessage = 'Failed to start recording';
        let recovery = 'Please try again';
        
        if (error.name === 'NotAllowedError') {
            errorMessage = 'Microphone access denied';
            recovery = 'Please allow microphone access and try again';
        } else if (error.name === 'NotFoundError') {
            errorMessage = 'No microphone found';
            recovery = 'Please check your microphone connection';
        } else if (error.message.includes('Connection')) {
            errorMessage = 'Connection to transcription service failed';
            recovery = 'Please check your internet connection';
        }
        
        this.updateStatus(`${errorMessage}: ${recovery}`, 'error');
        this.showErrorDialog(`${errorMessage}. ${recovery}`);
    }
    
    handleServerError(data) {
        this.metrics.errorCount++;
        
        const errorMessage = data.message || 'Unknown server error';
        console.error('❌ Server error:', errorMessage);
        
        this.updateStatus(`Server error: ${errorMessage}`, 'error');
        
        // Handle specific error types
        switch (data.error_type) {
            case 'session_start_failed':
                this.isRecording = false;
                this.updateRecordButtonState();
                break;
                
            case 'transcription_failed':
                console.warn('⚠️ Transcription failed for chunk, continuing...');
                break;
                
            case 'no_active_session':
                if (this.isRecording) {
                    console.log('🔄 Restarting session...');
                    this.startSession();
                }
                break;
        }
    }
    
    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`🔄 Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
        this.updateStatus(
            `Reconnecting in ${Math.ceil(delay/1000)}s... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`, 
            'warning'
        );
        
        setTimeout(() => {
            if (!this.isConnected) {
                this.connect();
            }
        }, delay);
    }
    
    updateRecordButtonState() {
        const buttons = [
            this.elements.recordButton,
            ...document.querySelectorAll('button[data-enhanced-listener="true"]')
        ].filter(btn => btn);
        
        buttons.forEach(button => {
            const icon = button.querySelector('i');
            const text = button.querySelector('span') || button;
            
            if (this.isRecording) {
                button.className = 'btn btn-danger btn-lg';
                if (icon) icon.className = 'bi bi-stop-fill';
                if (text && text !== button) text.textContent = 'Stop Recording';
                else if (text === button) text.innerHTML = '<i class="bi bi-stop-fill"></i> Stop Recording';
            } else {
                button.className = 'btn btn-primary btn-lg';
                if (icon) icon.className = 'bi bi-mic';
                if (text && text !== button) text.textContent = 'Start Recording';
                else if (text === button) text.innerHTML = '<i class="bi bi-mic"></i> Start Recording';
            }
        });
    }
    
    updateStatus(message, type = 'info') {
        console.log(`📱 Status: ${message} (${type})`);
        
        if (this.elements.statusDisplay) {
            const icon = this.elements.statusDisplay.querySelector('i');
            const text = this.elements.statusDisplay.querySelector('span') || 
                        this.elements.statusDisplay.querySelector('.alert-content') ||
                        this.elements.statusDisplay;
            
            // Update classes
            this.elements.statusDisplay.className = `alert mb-3 alert-${this.getAlertClass(type)}`;
            
            // Update icon
            if (icon) {
                icon.className = `bi ${this.getStatusIcon(type)}`;
            }
            
            // Update text
            if (text && text !== this.elements.statusDisplay) {
                text.textContent = message;
            } else {
                this.elements.statusDisplay.innerHTML = `
                    <i class="bi ${this.getStatusIcon(type)}"></i>
                    <span class="ms-2">${message}</span>
                `;
            }
        } else {
            // Create status display if it doesn't exist
            this.createStatusDisplay(message, type);
        }
        
        // Update page title for background indication
        if (type === 'recording') {
            document.title = '🔴 Recording - Mina Live Transcription';
        } else {
            document.title = 'Mina Live Transcription';
        }
    }
    
    createStatusDisplay(message, type) {
        const container = document.querySelector('.recording-controls') || 
                         document.querySelector('.container') ||
                         document.body;
        
        if (container) {
            const statusDiv = document.createElement('div');
            statusDiv.id = 'recording-status';
            statusDiv.className = `alert mb-3 alert-${this.getAlertClass(type)}`;
            statusDiv.innerHTML = `
                <i class="bi ${this.getStatusIcon(type)}"></i>
                <span class="ms-2">${message}</span>
            `;
            
            container.insertBefore(statusDiv, container.firstChild);
            this.elements.statusDisplay = statusDiv;
        }
    }
    
    getAlertClass(type) {
        switch (type) {
            case 'success': return 'success';
            case 'error': return 'danger';
            case 'warning': return 'warning';
            case 'recording': return 'primary';
            case 'info': return 'info';
            default: return 'secondary';
        }
    }
    
    getStatusIcon(type) {
        switch (type) {
            case 'success': return 'bi-check-circle-fill text-success';
            case 'error': return 'bi-exclamation-triangle-fill text-danger';
            case 'warning': return 'bi-exclamation-circle-fill text-warning';
            case 'recording': return 'bi-record-circle-fill text-primary';
            case 'info': return 'bi-info-circle-fill text-info';
            default: return 'bi-circle-fill text-secondary';
        }
    }
    
    showErrorDialog(message) {
        // Enhanced error dialog with better UX
        if (window.confirm) {
            const retry = confirm(`Transcription Error: ${message}\n\nWould you like to try again?`);
            if (retry) {
                setTimeout(() => {
                    this.reconnectAttempts = 0;
                    this.connect();
                }, 1000);
            }
        } else {
            console.error('Error dialog:', message);
        }
    }
    
    clearTranscript() {
        if (this.elements.transcriptDisplay) {
            const container = this.elements.transcriptDisplay.querySelector('.live-transcript-container') ||
                             this.elements.transcriptDisplay.querySelector('.card-body') ||
                             this.elements.transcriptDisplay;
            
            if (container) {
                container.innerHTML = `
                    <div class="text-center text-muted" id="initialMessage">
                        <i class="bi bi-mic-mute fs-1 mb-3"></i>
                        <h6>Transcript Cleared</h6>
                        <p class="mb-2">Ready for new transcription</p>
                        <p class="small">Click "Start Recording" to begin...</p>
                    </div>
                `;
                
                // Reset word counter
                if (this.elements.wordCounter) {
                    this.elements.wordCounter.textContent = '0';
                }
                
                console.log('✅ Transcript cleared');
            }
        }
    }
    
    cleanup() {
        console.log('🧹 Cleaning up enhanced WebSocket client...');
        
        if (this.isRecording) {
            this.stopRecording();
        }
        
        this.stopPolling();
        
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
        }
        
        this.isConnected = false;
        this.connectionId = null;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getMetrics() {
        return {
            ...this.metrics,
            isConnected: this.isConnected,
            isRecording: this.isRecording,
            sessionId: this.sessionId,
            connectionMode: this.connectionMode,
            pollingActive: !!this.pollingInterval
        };
    }
}

// Initialize enhanced WebSocket client V2 when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎯 Initializing Enhanced WebSocket Client V2...');
    window.enhancedWebSocketClient = new EnhancedWebSocketClientV2();
    
    // Global access for debugging and testing
    window.getEnhancedMetrics = () => window.enhancedWebSocketClient.getMetrics();
    window.clearTranscript = () => window.enhancedWebSocketClient.clearTranscript();
    window.toggleRecording = () => window.enhancedWebSocketClient.toggleRecording();
    
    console.log('✅ Enhanced WebSocket Client V2 ready');
});

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
