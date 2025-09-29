/**
 * ENHANCED TRANSCRIPTION CLIENT
 * Comprehensive and extensive frontend transcription processing with advanced features:
 * - Real-time audio processing with quality monitoring
 * - Adaptive buffering and intelligent chunk management  
 * - Context-aware transcription display with confidence indicators
 * - Advanced error handling and recovery mechanisms
 * - Performance monitoring and analytics
 */

class EnhancedTranscriptionClient {
    constructor(options = {}) {
        // Enhanced configuration
        this.config = {
            socketNamespace: '/transcription',
            audioConstraints: {
                audio: {
                    sampleRate: 48000,
                    channelCount: 1,
                    autoGainControl: true,
                    noiseSuppression: true,
                    echoCancellation: true,
                    ...options.audioConstraints
                }
            },
            recordingOptions: {
                mimeType: 'audio/webm;codecs=opus',
                audioBitsPerSecond: 128000,
                timeslice: 1000  // 1 second chunks for optimal processing
            },
            qualityThresholds: {
                confidence: 0.7,
                minimumWords: 2,
                maxRetries: 3
            },
            processingOptions: {
                enableRealTimeProcessing: true,
                enableContextAwareness: true,
                qualityMode: 'balanced',  // high, balanced, fast
                confidenceThreshold: 0.7,
                audioEnhancement: true
            },
            ui: {
                enableVisualIndicators: true,
                showConfidenceScores: true,
                showProcessingMetrics: true,
                enableAnimations: true
            },
            ...options
        };

        // Enhanced state management
        this.state = {
            isRecording: false,
            isConnected: false,
            hasEnhancedSession: false,
            mediaRecorder: null,
            mediaStream: null,
            socket: null,
            sessionId: null,
            enhancedSessionId: null,
            
            // Processing state
            processingQuality: 1.0,
            consecutiveFailures: 0,
            adaptiveInterval: 2000,
            
            // Audio analysis
            audioAnalyzer: null,
            audioContext: null,
            audioLevel: 0,
            speechDetected: false,
            
            // Transcription state
            interimTranscript: '',
            finalTranscript: '',
            currentSegments: [],
            processingHistory: [],
            
            // UI state
            isProcessing: false,
            lastUpdateTime: 0,
            performanceMetrics: {}
        };

        // Enhanced callbacks
        this.callbacks = {
            onConnect: options.onConnect || this._defaultOnConnect.bind(this),
            onDisconnect: options.onDisconnect || this._defaultOnDisconnect.bind(this),
            onSessionStart: options.onSessionStart || this._defaultOnSessionStart.bind(this),
            onTranscriptUpdate: options.onTranscriptUpdate || this._defaultOnTranscriptUpdate.bind(this),
            onEnhancedResult: options.onEnhancedResult || this._defaultOnEnhancedResult.bind(this),
            onProcessingMetrics: options.onProcessingMetrics || this._defaultOnProcessingMetrics.bind(this),
            onError: options.onError || this._defaultOnError.bind(this),
            onQualityChange: options.onQualityChange || this._defaultOnQualityChange.bind(this),
            onBackpressure: options.onBackpressure || this._defaultOnBackpressure.bind(this)
        };

        // Initialize enhanced components
        this._initializeSocket();
        this._initializeUI();
        this._initializeAnalytics();
    }

    /**
     * Initialize enhanced WebSocket connection with comprehensive event handling
     */
    _initializeSocket() {
        try {
            this.state.socket = io(this.config.socketNamespace, {
                path: '/socket.io',
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionAttempts: Infinity,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                timeout: 20000,
                upgrade: true
            });

            // Enhanced connection events
            this.state.socket.on('connect', () => {
                console.log('🔌 Enhanced transcription client connected');
                this.state.isConnected = true;
                this.callbacks.onConnect();
            });

            this.state.socket.on('disconnect', () => {
                console.log('🔌 Enhanced transcription client disconnected');
                this.state.isConnected = false;
                this.state.hasEnhancedSession = false;
                this.callbacks.onDisconnect();
            });

            // Enhanced status events
            this.state.socket.on('enhanced_status', (data) => {
                console.log('📊 Enhanced connection status:', data);
                if (data.features) {
                    this._updateCapabilities(data.features);
                }
            });

            // Enhanced session events
            this.state.socket.on('enhanced_session_started', (data) => {
                console.log('🚀 Enhanced session started:', data);
                this.state.hasEnhancedSession = true;
                this.state.enhancedSessionId = data.session_id;
                this.callbacks.onSessionStart(data);
            });

            // Enhanced transcription results
            this.state.socket.on('enhanced_transcription_result', (data) => {
                console.log('🎯 Enhanced result received:', data);
                this._processEnhancedResult(data);
            });

            // Legacy compatibility
            this.state.socket.on('transcription_result', (data) => {
                this._processLegacyResult(data);
            });

            // Enhanced processing metrics
            this.state.socket.on('enhanced_processing_metrics', (data) => {
                this._updateProcessingMetrics(data);
            });

            // Enhanced error handling
            this.state.socket.on('enhanced_error', (data) => {
                console.error('❌ Enhanced transcription error:', data);
                this.callbacks.onError(data);
            });

            // Enhanced backpressure warnings
            this.state.socket.on('enhanced_backpressure_warning', (data) => {
                console.warn('⚠️ Enhanced backpressure warning:', data);
                this.callbacks.onBackpressure(data);
                this._handleBackpressure(data);
            });

            // Enhanced session metrics
            this.state.socket.on('enhanced_session_metrics', (data) => {
                this._updateSessionMetrics(data);
            });

            // Enhanced ingestion status
            this.state.socket.on('enhanced_ingestion_status', (data) => {
                this._updateIngestionStatus(data);
            });

        } catch (error) {
            console.error('❌ Socket initialization failed:', error);
            this.callbacks.onError({ message: `Socket initialization failed: ${error.message}` });
        }
    }

    /**
     * Initialize enhanced UI components and visual indicators
     */
    _initializeUI() {
        if (!this.config.ui.enableVisualIndicators) return;

        // Create enhanced UI elements
        this._createAudioLevelIndicator();
        this._createProcessingIndicator();
        this._createQualityIndicator();
        this._createMetricsDisplay();
    }

    /**
     * Initialize comprehensive analytics and monitoring
     */
    _initializeAnalytics() {
        // Performance monitoring
        this.analytics = {
            startTime: null,
            totalAudioProcessed: 0,
            totalTranscriptionTime: 0,
            qualityHistory: [],
            errorHistory: [],
            latencyHistory: []
        };

        // Start periodic analytics collection
        setInterval(() => {
            this._collectAnalytics();
        }, 5000);
    }

    /**
     * Start enhanced recording with comprehensive audio processing
     */
    async startRecording() {
        try {
            console.log('🎤 Starting enhanced recording...');

            if (this.state.isRecording) {
                console.warn('⚠️ Recording already in progress');
                return false;
            }

            // Get enhanced media stream
            this.state.mediaStream = await navigator.mediaDevices.getUserMedia(
                this.config.audioConstraints
            );

            // Initialize enhanced audio analysis
            await this._initializeAudioAnalysis();

            // Enhanced MediaRecorder with iOS Safari fallback
            const recordingOptions = { ...this.config.recordingOptions };
            
            // Check MIME type support with comprehensive fallbacks
            if (!MediaRecorder.isTypeSupported(recordingOptions.mimeType)) {
                if (MediaRecorder.isTypeSupported('audio/webm')) {
                    recordingOptions.mimeType = 'audio/webm';
                } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
                    recordingOptions.mimeType = 'audio/mp4'; // iOS Safari primary
                } else if (MediaRecorder.isTypeSupported('audio/aac')) {
                    recordingOptions.mimeType = 'audio/aac'; // iOS Safari secondary
                } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
                    recordingOptions.mimeType = 'audio/ogg;codecs=opus';
                } else if (MediaRecorder.isTypeSupported('audio/wav')) {
                    recordingOptions.mimeType = 'audio/wav'; // Universal fallback
                } else {
                    delete recordingOptions.mimeType; // Let browser decide
                }
                console.log(`🎙️ Enhanced client using fallback MIME: ${recordingOptions.mimeType || 'browser default'}`);
            }
            
            this.state.mediaRecorder = new MediaRecorder(
                this.state.mediaStream,
                recordingOptions
            );

            // Enhanced event handlers
            this.state.mediaRecorder.ondataavailable = (event) => {
                this._handleEnhancedAudioData(event);
            };

            this.state.mediaRecorder.onerror = (event) => {
                console.error('❌ MediaRecorder error:', event);
                this.callbacks.onError({ message: `MediaRecorder error: ${event.error}` });
            };

            this.state.mediaRecorder.onstart = () => {
                console.log('🎵 Enhanced recording started');
                this.state.isRecording = true;
                this._updateUI('recording');
            };

            this.state.mediaRecorder.onstop = () => {
                console.log('⏹️ Enhanced recording stopped');
                this.state.isRecording = false;
                this._updateUI('stopped');
            };

            // Start enhanced session
            if (!this.state.hasEnhancedSession) {
                await this._startEnhancedSession();
            }

            // Start recording with enhanced chunking
            this.state.mediaRecorder.start(this.config.recordingOptions.timeslice);
            this.analytics.startTime = Date.now();

            return true;

        } catch (error) {
            console.error('❌ Enhanced recording start failed:', error);
            this.callbacks.onError({ message: `Failed to start recording: ${error.message}` });
            return false;
        }
    }

    /**
     * Stop enhanced recording with graceful cleanup
     */
    async stopRecording() {
        try {
            console.log('⏹️ Stopping enhanced recording...');

            if (!this.state.isRecording) {
                console.warn('⚠️ No recording in progress');
                return false;
            }

            // Stop MediaRecorder
            if (this.state.mediaRecorder && this.state.mediaRecorder.state !== 'inactive') {
                this.state.mediaRecorder.stop();
            }

            // Stop media stream
            if (this.state.mediaStream) {
                this.state.mediaStream.getTracks().forEach(track => track.stop());
                this.state.mediaStream = null;
            }

            // Cleanup audio analysis
            if (this.state.audioContext) {
                await this.state.audioContext.close();
                this.state.audioContext = null;
            }

            // Update analytics
            if (this.analytics.startTime) {
                const sessionDuration = Date.now() - this.analytics.startTime;
                this.analytics.totalRecordingTime = sessionDuration;
            }

            this._updateUI('stopped');
            return true;

        } catch (error) {
            console.error('❌ Enhanced recording stop failed:', error);
            this.callbacks.onError({ message: `Failed to stop recording: ${error.message}` });
            return false;
        }
    }

    /**
     * Start enhanced transcription session with advanced configuration
     */
    async _startEnhancedSession() {
        return new Promise((resolve, reject) => {
            if (!this.state.isConnected) {
                reject(new Error('Not connected to transcription service'));
                return;
            }

            const sessionConfig = {
                ...this.config.processingOptions,
                language: 'en',
                client_capabilities: {
                    enhanced_ui: this.config.ui.enableVisualIndicators,
                    real_time_metrics: this.config.ui.showProcessingMetrics,
                    audio_analysis: true
                }
            };

            // Set up one-time listener for session start
            const onSessionStart = (data) => {
                this.state.socket.off('enhanced_session_started', onSessionStart);
                resolve(data);
            };

            const onError = (error) => {
                this.state.socket.off('enhanced_error', onError);
                reject(new Error(error.message || 'Session start failed'));
            };

            this.state.socket.on('enhanced_session_started', onSessionStart);
            this.state.socket.on('enhanced_error', onError);

            // Start enhanced session
            this.state.socket.emit('start_enhanced_session', sessionConfig);

            // Timeout after 10 seconds
            setTimeout(() => {
                this.state.socket.off('enhanced_session_started', onSessionStart);
                this.state.socket.off('enhanced_error', onError);
                reject(new Error('Session start timeout'));
            }, 10000);
        });
    }

    /**
     * Initialize enhanced audio analysis with real-time monitoring
     */
    async _initializeAudioAnalysis() {
        try {
            this.state.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const analyser = this.state.audioContext.createAnalyser();
            
            analyser.fftSize = 256;
            analyser.smoothingTimeConstant = 0.3;
            
            const source = this.state.audioContext.createMediaStreamSource(this.state.mediaStream);
            source.connect(analyser);
            
            this.state.audioAnalyzer = analyser;
            
            // Start real-time audio level monitoring
            this._startAudioLevelMonitoring();
            
        } catch (error) {
            console.warn('⚠️ Audio analysis initialization failed:', error);
        }
    }

    /**
     * Start real-time audio level monitoring for quality assessment
     */
    _startAudioLevelMonitoring() {
        if (!this.state.audioAnalyzer) return;

        const bufferLength = this.state.audioAnalyzer.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const monitor = () => {
            if (!this.state.isRecording) return;

            this.state.audioAnalyzer.getByteFrequencyData(dataArray);
            
            // Calculate audio level
            const average = dataArray.reduce((sum, value) => sum + value, 0) / bufferLength;
            this.state.audioLevel = average / 255.0;
            
            // Detect speech activity (simple threshold-based)
            this.state.speechDetected = this.state.audioLevel > 0.1;
            
            // Update UI indicators
            this._updateAudioIndicators();
            
            // Continue monitoring
            if (this.state.isRecording) {
                requestAnimationFrame(monitor);
            }
        };

        requestAnimationFrame(monitor);
    }

    /**
     * Handle enhanced audio data with comprehensive processing
     */
    _handleEnhancedAudioData(event) {
        if (!event.data || event.data.size === 0) return;

        try {
            const audioBlob = event.data;
            const audioSize = audioBlob.size;
            
            // Update analytics
            this.analytics.totalAudioProcessed += audioSize;
            
            // Convert to ArrayBuffer and then to base64
            const reader = new FileReader();
            reader.onloadend = () => {
                const arrayBuffer = reader.result;
                const uint8Array = new Uint8Array(arrayBuffer);
                const base64Audio = btoa(String.fromCharCode.apply(null, uint8Array));
                
                // Create enhanced audio data packet
                const enhancedAudioData = {
                    audioData: base64Audio,
                    mimeType: audioBlob.type || 'audio/webm',
                    metadata: {
                        size: audioSize,
                        timestamp: Date.now(),
                        sampleRate: this.config.audioConstraints.audio.sampleRate,
                        channels: this.config.audioConstraints.audio.channelCount,
                        audioLevel: this.state.audioLevel,
                        speechDetected: this.state.speechDetected,
                        processingQuality: this.state.processingQuality
                    },
                    qualityIndicators: {
                        audioLevel: this.state.audioLevel,
                        speechActivity: this.state.speechDetected,
                        consecutiveFailures: this.state.consecutiveFailures
                    }
                };

                // Send enhanced audio data
                this.state.socket.emit('enhanced_audio_data', enhancedAudioData);
                
                // Update processing state
                this.state.isProcessing = true;
                this._updateProcessingIndicator(true);
                
            };

            reader.onerror = (error) => {
                console.error('❌ Audio data reading failed:', error);
                this.callbacks.onError({ message: `Audio data reading failed: ${error}` });
            };

            reader.readAsArrayBuffer(audioBlob);

        } catch (error) {
            console.error('❌ Enhanced audio data handling failed:', error);
            this.callbacks.onError({ message: `Audio data handling failed: ${error.message}` });
        }
    }

    /**
     * Process enhanced transcription result with comprehensive analysis
     */
    _processEnhancedResult(data) {
        try {
            // Update processing state
            this.state.isProcessing = false;
            this.state.lastUpdateTime = Date.now();
            
            // Update transcription state
            if (data.is_final) {
                this.state.finalTranscript += ' ' + data.transcript;
                this.state.interimTranscript = '';
            } else {
                this.state.interimTranscript = data.transcript;
            }

            // Update processing history
            this.state.processingHistory.push({
                text: data.transcript,
                confidence: data.confidence,
                is_final: data.is_final,
                timestamp: data.timestamp,
                latency: data.latency_ms,
                quality_indicators: data.quality_indicators
            });

            // Limit history size
            if (this.state.processingHistory.length > 100) {
                this.state.processingHistory = this.state.processingHistory.slice(-50);
            }

            // Update analytics
            this.analytics.latencyHistory.push(data.latency_ms);
            this.analytics.qualityHistory.push(data.confidence);
            
            if (this.analytics.latencyHistory.length > 50) {
                this.analytics.latencyHistory = this.analytics.latencyHistory.slice(-25);
            }
            
            if (this.analytics.qualityHistory.length > 50) {
                this.analytics.qualityHistory = this.analytics.qualityHistory.slice(-25);
            }

            // Update consecutive failures
            if (data.confidence < this.config.qualityThresholds.confidence) {
                this.state.consecutiveFailures++;
            } else {
                this.state.consecutiveFailures = 0;
            }

            // Update processing quality
            this._updateProcessingQuality(data);

            // Update UI
            this._updateTranscriptionDisplay(data);
            this._updateProcessingIndicator(false);
            
            // Call enhanced callback
            this.callbacks.onEnhancedResult(data);

        } catch (error) {
            console.error('❌ Enhanced result processing failed:', error);
            this.callbacks.onError({ message: `Result processing failed: ${error.message}` });
        }
    }

    /**
     * Process legacy transcription result for compatibility
     */
    _processLegacyResult(data) {
        // Convert legacy format to enhanced format
        const enhancedData = {
            transcript: data.transcript,
            confidence: data.confidence || 0.9,
            is_final: data.is_final || false,
            latency_ms: data.latency_ms || 0,
            quality_indicators: {
                confidence_score: data.confidence || 0.9
            },
            timestamp: Date.now()
        };
        
        this._processEnhancedResult(enhancedData);
    }

    // Default callback implementations
    _defaultOnConnect() {
        console.log('✅ Enhanced transcription client connected');
    }

    _defaultOnDisconnect() {
        console.log('🔌 Enhanced transcription client disconnected');
    }

    _defaultOnSessionStart(data) {
        console.log('🚀 Enhanced transcription session started:', data);
    }

    _defaultOnTranscriptUpdate(data) {
        console.log('📝 Transcript updated:', data);
    }

    _defaultOnEnhancedResult(data) {
        console.log('🎯 Enhanced result received:', data);
    }

    _defaultOnProcessingMetrics(data) {
        console.log('📊 Processing metrics:', data);
    }

    _defaultOnError(error) {
        console.error('❌ Enhanced transcription error:', error);
    }

    _defaultOnQualityChange(quality) {
        console.log('📊 Processing quality changed:', quality);
    }

    _defaultOnBackpressure(data) {
        console.warn('⚠️ Enhanced backpressure detected:', data);
    }

    // UI update methods (to be implemented based on specific UI requirements)
    _createAudioLevelIndicator() {
        // Implementation depends on specific UI framework
    }

    _createProcessingIndicator() {
        // Implementation depends on specific UI framework
    }

    _createQualityIndicator() {
        // Implementation depends on specific UI framework
    }

    _createMetricsDisplay() {
        // Implementation depends on specific UI framework
    }

    _updateUI(state) {
        // Implementation depends on specific UI framework
    }

    _updateAudioIndicators() {
        // Implementation depends on specific UI framework
    }

    _updateTranscriptionDisplay(data) {
        // Implementation depends on specific UI framework
    }

    _updateProcessingIndicator(isProcessing) {
        // Implementation depends on specific UI framework
    }

    _updateCapabilities(features) {
        console.log('🔧 Server capabilities updated:', features);
    }

    _updateProcessingMetrics(data) {
        this.state.performanceMetrics = data;
        this.callbacks.onProcessingMetrics(data);
    }

    _updateSessionMetrics(data) {
        console.log('📊 Session metrics updated:', data);
    }

    _updateIngestionStatus(data) {
        console.log('📥 Ingestion status:', data);
    }

    _updateProcessingQuality(data) {
        const newQuality = data.quality_indicators?.processing_quality || 
                          (data.confidence > 0.8 ? 1.0 : data.confidence);
        
        this.state.processingQuality = newQuality;
        this.callbacks.onQualityChange(newQuality);
    }

    _handleBackpressure(data) {
        // Implement backpressure handling (reduce send rate, etc.)
        if (data.severity === 'critical') {
            // Temporarily stop sending audio data
            if (this.state.mediaRecorder && this.state.mediaRecorder.state === 'recording') {
                this.state.mediaRecorder.pause();
                
                // Resume after a delay
                setTimeout(() => {
                    if (this.state.mediaRecorder && this.state.mediaRecorder.state === 'paused') {
                        this.state.mediaRecorder.resume();
                    }
                }, 2000);
            }
        }
    }

    _collectAnalytics() {
        if (this.analytics.startTime) {
            const now = Date.now();
            const sessionDuration = now - this.analytics.startTime;
            
            const analytics = {
                sessionDuration,
                totalAudioProcessed: this.analytics.totalAudioProcessed,
                averageLatency: this._calculateAverage(this.analytics.latencyHistory),
                averageQuality: this._calculateAverage(this.analytics.qualityHistory),
                consecutiveFailures: this.state.consecutiveFailures,
                processingQuality: this.state.processingQuality
            };

            console.log('📊 Analytics update:', analytics);
        }
    }

    _calculateAverage(array) {
        if (array.length === 0) return 0;
        return array.reduce((sum, val) => sum + val, 0) / array.length;
    }

    // Public API methods
    getState() {
        return { ...this.state };
    }

    getAnalytics() {
        return { ...this.analytics };
    }

    getProcessingHistory() {
        return [...this.state.processingHistory];
    }

    async requestSessionMetrics() {
        if (this.state.socket && this.state.isConnected) {
            this.state.socket.emit('get_enhanced_session_metrics');
        }
    }
}

// Export for use in other modules
window.EnhancedTranscriptionClient = EnhancedTranscriptionClient;