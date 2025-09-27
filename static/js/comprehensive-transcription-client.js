/**
 * COMPREHENSIVE TRANSCRIPTION CLIENT
 * Unified client integrating all enhanced transcription features including:
 * - Advanced audio processing and visualization
 * - Multi-speaker diarization
 * - Real-time punctuation
 * - Enhanced session management
 * - Performance monitoring
 */

class ComprehensiveTranscriptionClient {
    constructor(options = {}) {
        this.options = {
            socketUrl: '',
            enableVisualizer: true,
            enableSpeakerDiarization: true,
            enablePunctuation: true,
            enableSessionPersistence: true,
            audioConstraints: {
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            },
            chunkDuration: 1500, // ms
            ...options
        };

        // Core components
        this.socket = null;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.visualizer = null;
        
        // Session management
        this.sessionId = null;
        this.clientId = this._generateClientId();
        this.isRecording = false;
        
        // Audio processing
        this.audioChunks = [];
        this.recordingStartTime = null;
        
        // Real-time transcription
        this.transcriptionBuffer = [];
        this.currentTranscript = '';
        this.speakers = new Map();
        
        // Performance monitoring
        this.metrics = {
            audioChunksProcessed: 0,
            transcriptionRequests: 0,
            averageLatency: 0,
            errorCount: 0,
            sessionStartTime: null
        };
        
        // Event callbacks
        this.callbacks = {
            onTranscriptionResult: () => {},
            onSpeakerDetected: () => {},
            onSessionUpdate: () => {},
            onError: () => {},
            onMetricsUpdate: () => {}
        };
        
        this._initializeSocket();
        console.log('🚀 Comprehensive Transcription Client initialized');
    }

    _generateClientId() {
        return 'client_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }

    _initializeSocket() {
        try {
            this.socket = io(this.options.socketUrl);
            
            this.socket.on('connect', () => {
                console.log('✅ Connected to comprehensive transcription server');
                this._emit_callback('onSessionUpdate', { status: 'connected' });
            });

            this.socket.on('disconnect', () => {
                console.log('🔌 Disconnected from transcription server');
                this._emit_callback('onSessionUpdate', { status: 'disconnected' });
            });

            this.socket.on('comprehensive_transcription_result', (result) => {
                this._handleTranscriptionResult(result);
            });

            this.socket.on('joined_comprehensive_session', (data) => {
                console.log('🎯 Joined comprehensive session:', data.session_id);
                this._emit_callback('onSessionUpdate', { 
                    status: 'session_joined', 
                    sessionId: data.session_id 
                });
            });

            this.socket.on('error', (error) => {
                console.error('❌ Socket error:', error);
                this.metrics.errorCount++;
                this._emit_callback('onError', error);
            });

        } catch (error) {
            console.error('❌ Socket initialization failed:', error);
            this._emit_callback('onError', { message: 'Socket initialization failed' });
        }
    }

    async createSession(sessionName = '', language = 'en') {
        try {
            const response = await fetch('/api/transcription/comprehensive/session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_name: sessionName,
                    language: language,
                    client_id: this.clientId
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.sessionId = data.session_id;
                this.metrics.sessionStartTime = Date.now();
                
                // Join WebSocket session
                this.socket.emit('join_comprehensive_session', {
                    session_id: this.sessionId,
                    client_id: this.clientId
                });
                
                console.log('🆕 Created comprehensive session:', this.sessionId);
                this._emit_callback('onSessionUpdate', { 
                    status: 'session_created', 
                    sessionId: this.sessionId 
                });
                
                return this.sessionId;
            } else {
                throw new Error(data.error || 'Failed to create session');
            }
            
        } catch (error) {
            console.error('❌ Session creation failed:', error);
            this._emit_callback('onError', { message: 'Session creation failed: ' + error.message });
            throw error;
        }
    }

    async startRecording() {
        try {
            if (this.isRecording) {
                console.warn('⚠️ Recording already in progress');
                return;
            }

            if (!this.sessionId) {
                await this.createSession();
            }

            // Get audio stream
            this.audioStream = await navigator.mediaDevices.getUserMedia(this.options.audioConstraints);
            
            // Initialize visualizer if enabled
            if (this.options.enableVisualizer) {
                await this._initializeVisualizer();
            }
            
            // Setup MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this._processAudioChunk(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this._handleRecordingStop();
            };
            
            // Start recording
            this.recordingStartTime = Date.now();
            this.mediaRecorder.start(this.options.chunkDuration);
            this.isRecording = true;
            
            console.log('🎤 Comprehensive recording started');
            this._emit_callback('onSessionUpdate', { 
                status: 'recording_started',
                sessionId: this.sessionId
            });
            
        } catch (error) {
            console.error('❌ Recording start failed:', error);
            this._emit_callback('onError', { message: 'Recording start failed: ' + error.message });
            throw error;
        }
    }

    async stopRecording() {
        try {
            if (!this.isRecording) {
                console.warn('⚠️ No recording in progress');
                return;
            }

            this.isRecording = false;
            
            if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
                this.mediaRecorder.stop();
            }
            
            if (this.audioStream) {
                this.audioStream.getTracks().forEach(track => track.stop());
                this.audioStream = null;
            }
            
            if (this.visualizer) {
                this.visualizer.stop();
            }
            
            // Send final processing request
            if (this.audioChunks.length > 0) {
                await this._sendFinalChunk();
            }
            
            console.log('⏹️ Comprehensive recording stopped');
            this._emit_callback('onSessionUpdate', { 
                status: 'recording_stopped',
                sessionId: this.sessionId,
                metrics: this._getSessionMetrics()
            });
            
        } catch (error) {
            console.error('❌ Recording stop failed:', error);
            this._emit_callback('onError', { message: 'Recording stop failed: ' + error.message });
        }
    }

    async _initializeVisualizer() {
        try {
            const canvasElement = document.querySelector('#audio-visualizer');
            if (!canvasElement) {
                console.warn('⚠️ Audio visualizer canvas not found');
                return;
            }

            this.visualizer = new AdvancedAudioVisualizer('audio-visualizer', {
                onAudioMetrics: (metrics) => {
                    this._emit_callback('onMetricsUpdate', { audioMetrics: metrics });
                },
                onVoiceActivity: (isActive, metrics) => {
                    this._emit_callback('onSessionUpdate', { 
                        status: 'voice_activity', 
                        isActive: isActive,
                        metrics: metrics
                    });
                },
                onSpeakerChange: (speakers) => {
                    this._emit_callback('onSpeakerDetected', { activeSpeakers: speakers });
                }
            });

            if (this.visualizer.connectAudioSource(this.audioStream)) {
                this.visualizer.start();
                console.log('🎨 Audio visualizer initialized');
            }

        } catch (error) {
            console.error('❌ Visualizer initialization failed:', error);
        }
    }

    async _processAudioChunk(audioBlob) {
        try {
            const startTime = performance.now();
            
            // Convert blob to base64
            const base64Audio = await this._blobToBase64(audioBlob);
            
            // Send to comprehensive processing pipeline
            this.socket.emit('comprehensive_audio_data', {
                session_id: this.sessionId,
                client_id: this.clientId,
                audio_data: base64Audio,
                is_final: false,
                chunk_index: this.metrics.audioChunksProcessed,
                timestamp: Date.now()
            });
            
            this.metrics.audioChunksProcessed++;
            this.metrics.transcriptionRequests++;
            
            // Store for potential final processing
            this.audioChunks.push({
                blob: audioBlob,
                timestamp: Date.now(),
                processingTime: performance.now() - startTime
            });
            
            // Keep only recent chunks to manage memory
            if (this.audioChunks.length > 10) {
                this.audioChunks = this.audioChunks.slice(-5);
            }
            
        } catch (error) {
            console.error('❌ Audio chunk processing failed:', error);
            this.metrics.errorCount++;
            this._emit_callback('onError', { message: 'Audio processing failed' });
        }
    }

    async _sendFinalChunk() {
        try {
            if (this.audioChunks.length === 0) return;
            
            // Use the last chunk for final processing
            const finalChunk = this.audioChunks[this.audioChunks.length - 1];
            const base64Audio = await this._blobToBase64(finalChunk.blob);
            
            this.socket.emit('comprehensive_audio_data', {
                session_id: this.sessionId,
                client_id: this.clientId,
                audio_data: base64Audio,
                is_final: true,
                chunk_index: this.metrics.audioChunksProcessed,
                timestamp: Date.now()
            });
            
            console.log('📤 Final audio chunk sent for processing');
            
        } catch (error) {
            console.error('❌ Final chunk processing failed:', error);
        }
    }

    _handleTranscriptionResult(result) {
        try {
            const processingTime = performance.now();
            
            // Update metrics
            this._updateLatencyMetrics(result.processing_info?.processing_time_ms || 0);
            
            // Process speaker information
            if (result.speaker_info && this.options.enableSpeakerDiarization) {
                this._updateSpeakerInfo(result.speaker_info);
            }
            
            // Update transcript
            if (result.text) {
                this._updateTranscript(result);
            }
            
            // Emit callbacks
            this._emit_callback('onTranscriptionResult', {
                text: result.text,
                confidence: result.confidence,
                isFinal: result.is_final,
                speakerInfo: result.speaker_info,
                audioMetrics: result.audio_metrics,
                processingInfo: result.processing_info
            });
            
            this._emit_callback('onMetricsUpdate', {
                systemMetrics: result.system_metrics,
                processingMetrics: this._getSessionMetrics()
            });
            
            console.log('📝 Transcription result processed:', {
                text: result.text?.substring(0, 50) + (result.text?.length > 50 ? '...' : ''),
                speaker: result.speaker_info?.speaker_id,
                confidence: result.confidence,
                quality: result.quality_score
            });
            
        } catch (error) {
            console.error('❌ Transcription result handling failed:', error);
            this._emit_callback('onError', { message: 'Result processing failed' });
        }
    }

    _updateSpeakerInfo(speakerInfo) {
        try {
            const speakerId = speakerInfo.speaker_id;
            
            if (!this.speakers.has(speakerId)) {
                this.speakers.set(speakerId, {
                    id: speakerId,
                    confidence: speakerInfo.speaker_confidence,
                    firstSeen: Date.now(),
                    lastSeen: Date.now(),
                    segmentCount: 0
                });
                
                this._emit_callback('onSpeakerDetected', {
                    type: 'new_speaker',
                    speakerId: speakerId,
                    speakerInfo: speakerInfo
                });
            } else {
                const speaker = this.speakers.get(speakerId);
                speaker.confidence = speakerInfo.speaker_confidence;
                speaker.lastSeen = Date.now();
                speaker.segmentCount++;
            }
            
            // Update visualizer if available
            if (this.visualizer && this.options.enableSpeakerDiarization) {
                const activeSpeakers = Array.from(this.speakers.keys())
                    .filter(id => Date.now() - this.speakers.get(id).lastSeen < 10000); // Active in last 10s
                this.visualizer.updateSpeakerActivity(activeSpeakers);
            }
            
        } catch (error) {
            console.error('❌ Speaker info update failed:', error);
        }
    }

    _updateTranscript(result) {
        try {
            // Add to transcription buffer
            this.transcriptionBuffer.push({
                text: result.text,
                speaker: result.speaker_info?.speaker_id || 'unknown',
                timestamp: Date.now(),
                confidence: result.confidence,
                isFinal: result.is_final
            });
            
            // Keep buffer manageable
            if (this.transcriptionBuffer.length > 100) {
                this.transcriptionBuffer = this.transcriptionBuffer.slice(-50);
            }
            
            // Update current transcript
            if (result.is_final) {
                this.currentTranscript += result.text + ' ';
            }
            
        } catch (error) {
            console.error('❌ Transcript update failed:', error);
        }
    }

    _updateLatencyMetrics(processingTimeMs) {
        try {
            const currentAvg = this.metrics.averageLatency;
            const alpha = 0.1; // Smoothing factor
            
            this.metrics.averageLatency = alpha * processingTimeMs + (1 - alpha) * currentAvg;
            
        } catch (error) {
            console.error('❌ Latency metrics update failed:', error);
        }
    }

    _getSessionMetrics() {
        return {
            ...this.metrics,
            sessionDuration: this.metrics.sessionStartTime ? 
                Date.now() - this.metrics.sessionStartTime : 0,
            transcriptLength: this.currentTranscript.length,
            speakerCount: this.speakers.size,
            errorRate: this.metrics.errorCount / Math.max(1, this.metrics.transcriptionRequests)
        };
    }

    async _blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    _handleRecordingStop() {
        console.log('🎤 MediaRecorder stopped');
        this.isRecording = false;
    }

    _emit_callback(callbackName, data) {
        try {
            if (typeof this.callbacks[callbackName] === 'function') {
                this.callbacks[callbackName](data);
            }
        } catch (error) {
            console.error(`❌ Callback ${callbackName} failed:`, error);
        }
    }

    // Public API methods
    on(event, callback) {
        if (this.callbacks.hasOwnProperty('on' + event.charAt(0).toUpperCase() + event.slice(1))) {
            this.callbacks['on' + event.charAt(0).toUpperCase() + event.slice(1)] = callback;
        } else {
            console.warn(`⚠️ Unknown event: ${event}`);
        }
    }

    async getSessionAnalytics() {
        try {
            if (!this.sessionId) {
                throw new Error('No active session');
            }

            const response = await fetch(`/api/transcription/comprehensive/session/${this.sessionId}`);
            const data = await response.json();
            
            if (data.success) {
                return data.session_analytics;
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('❌ Analytics retrieval failed:', error);
            throw error;
        }
    }

    async exportSession(format = 'json') {
        try {
            if (!this.sessionId) {
                throw new Error('No active session');
            }

            const response = await fetch(`/api/transcription/comprehensive/session/${this.sessionId}/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ format: format })
            });

            if (response.ok) {
                const blob = await response.blob();
                
                // Create download link
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `session_${this.sessionId}.${format}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                console.log(`📄 Session exported as ${format}`);
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Export failed');
            }
            
        } catch (error) {
            console.error('❌ Session export failed:', error);
            throw error;
        }
    }

    getTranscript() {
        return this.currentTranscript;
    }

    getTranscriptionBuffer() {
        return [...this.transcriptionBuffer];
    }

    getSpeakers() {
        return new Map(this.speakers);
    }

    getMetrics() {
        return this._getSessionMetrics();
    }

    disconnect() {
        try {
            if (this.isRecording) {
                this.stopRecording();
            }
            
            if (this.socket) {
                this.socket.emit('leave_comprehensive_session', {
                    session_id: this.sessionId,
                    client_id: this.clientId
                });
                this.socket.disconnect();
            }
            
            console.log('🔌 Comprehensive transcription client disconnected');
            
        } catch (error) {
            console.error('❌ Disconnect failed:', error);
        }
    }
}

// Export for use in other modules
window.ComprehensiveTranscriptionClient = ComprehensiveTranscriptionClient;