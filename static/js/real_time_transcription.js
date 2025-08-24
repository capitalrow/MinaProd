/**
 * Real-time Transcription Application
 * Main application logic for live audio transcription with WebSocket communication
 */

class RealTimeTranscription {
    constructor() {
        this.socket = null;
        this.audioProcessor = null;
        this.websocketStreaming = null;
        this.isRecording = false;
        this.isPaused = false;
        this.sessionId = null;
        this.sessionStartTime = null;
        this.currentSessionConfig = this.getDefaultConfig();
        
        // Statistics
        this.stats = {
            segmentCount: 0,
            totalConfidence: 0,
            speakingTime: 0,
            lastUpdate: null
        };
        
        // DOM elements
        this.elements = {};
        
        // Initialize
        this.initializeElements();
        this.initializeSocket();
        this.initializeAudioProcessor();
        this.setupEventListeners();
        this.updateUI();
        
        console.log('RealTimeTranscription initialized');
    }
    
    getDefaultConfig() {
        return {
            title: 'Live Session',
            description: '',
            language: 'en',
            vadSensitivity: 0.5,
            minConfidence: 0.7,
            enableSpeakerDetection: true,
            enableSentimentAnalysis: false,
            enableRealtime: true,
            enableWordTimestamps: true
        };
    }
    
    initializeElements() {
        this.elements = {
            // Status elements
            connectionStatus: document.getElementById('connectionStatus'),
            connectionText: document.getElementById('connectionText'),
            micStatus: document.getElementById('micStatus'),
            languageStatus: document.getElementById('languageStatus'),
            sessionTime: document.getElementById('sessionTime'),
            
            // Control buttons
            startButton: document.getElementById('startButton'),
            pauseButton: document.getElementById('pauseButton'),
            stopButton: document.getElementById('stopButton'),
            
            // Transcription display
            transcriptionContainer: document.getElementById('transcriptionContainer'),
            clearTranscription: document.getElementById('clearTranscription'),
            exportTranscription: document.getElementById('exportTranscription'),
            
            // Audio visualizer
            audioVisualizer: document.getElementById('audioVisualizer'),
            waveContainer: document.getElementById('waveContainer'),
            inputLevel: document.getElementById('inputLevel'),
            vadStatus: document.getElementById('vadStatus'),
            
            // Statistics
            segmentCount: document.getElementById('segmentCount'),
            avgConfidence: document.getElementById('avgConfidence'),
            speakingTime: document.getElementById('speakingTime'),
            lastUpdate: document.getElementById('lastUpdate'),
            
            // Configuration
            autoScroll: document.getElementById('autoScroll'),
            showInterim: document.getElementById('showInterim'),
            
            // Modal elements
            sessionTitle: document.getElementById('sessionTitle'),
            sessionLanguage: document.getElementById('sessionLanguage'),
            sessionDescription: document.getElementById('sessionDescription'),
            vadSensitivityConfig: document.getElementById('vadSensitivityConfig'),
            minConfidenceConfig: document.getElementById('minConfidenceConfig'),
            vadSensitivityValue: document.getElementById('vadSensitivityValue'),
            minConfidenceValue: document.getElementById('minConfidenceValue'),
            enableSpeakerDetectionConfig: document.getElementById('enableSpeakerDetectionConfig'),
            enableSentimentAnalysisConfig: document.getElementById('enableSentimentAnalysisConfig'),
            enableRealtimeConfig: document.getElementById('enableRealtimeConfig'),
            enableWordTimestampsConfig: document.getElementById('enableWordTimestampsConfig'),
            applyConfig: document.getElementById('applyConfig')
        };
    }
    
    initializeSocket() {
        if (!window.io) {
            console.error('Socket.IO not loaded');
            this.updateConnectionStatus('error', 'Socket.IO not available');
            return;
        }
        
        this.socket = io({
            transports: ['websocket', 'polling'],
            upgrade: true,
            rememberUpgrade: true
        });
        
        // Socket event handlers
        this.socket.on('connect', () => {
            console.log('Socket connected');
            this.updateConnectionStatus('connected', 'Connected to server');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Socket disconnected');
            this.updateConnectionStatus('disconnected', 'Disconnected from server');
        });
        
        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            this.updateConnectionStatus('error', `Error: ${error.message || error}`);
        });
        
        this.socket.on('session_joined', (data) => {
            console.log('Session joined:', data);
            this.sessionId = data.session_id;
            this.updateConnectionStatus('connected', `Session: ${this.sessionId}`);
        });
        
        this.socket.on('transcription_result', (data) => {
            this.handleTranscriptionResult(data);
        });
        
        this.socket.on('interim_result', (data) => {
            this.handleInterimResult(data);
        });
        
        this.socket.on('transcription_started', (data) => {
            console.log('Transcription started:', data);
        });
        
        this.socket.on('transcription_stopped', (data) => {
            console.log('Transcription stopped:', data);
        });
        
        this.socket.on('processing_error', (data) => {
            console.error('Processing error:', data);
            this.showError(`Processing error: ${data.error}`);
        });
    }
    
    initializeAudioProcessor() {
        if (window.VADProcessorAdvanced) {
            this.audioProcessor = new VADProcessorAdvanced({
                sampleRate: 16000,
                vadSensitivity: this.currentSessionConfig.vadSensitivity
            });
            
            this.audioProcessor.onAudioLevel = (level) => {
                this.updateAudioLevel(level);
            };
            
            this.audioProcessor.onVADResult = (result) => {
                this.updateVADStatus(result);
            };
            
            this.audioProcessor.onAudioChunk = (audioData, timestamp) => {
                this.sendAudioChunk(audioData, timestamp);
            };
        }
        
        if (window.WebSocketStreaming) {
            this.websocketStreaming = new WebSocketStreaming({
                socket: this.socket,
                chunkDuration: 1000, // 1 second chunks
                enableVAD: true
            });
        }
        
        this.initializeAudioVisualizer();
    }
    
    initializeAudioVisualizer() {
        const waveContainer = this.elements.waveContainer;
        if (!waveContainer) return;
        
        // Create wave bars
        waveContainer.innerHTML = '';
        for (let i = 0; i < 32; i++) {
            const bar = document.createElement('div');
            bar.className = 'wave-bar';
            bar.style.height = '10px';
            waveContainer.appendChild(bar);
        }
        
        this.waveBars = waveContainer.querySelectorAll('.wave-bar');
    }
    
    setupEventListeners() {
        // Control buttons
        this.elements.startButton?.addEventListener('click', () => this.startRecording());
        this.elements.pauseButton?.addEventListener('click', () => this.pauseRecording());
        this.elements.stopButton?.addEventListener('click', () => this.stopRecording());
        
        // Transcription controls
        this.elements.clearTranscription?.addEventListener('click', () => this.clearTranscription());
        this.elements.exportTranscription?.addEventListener('click', () => this.exportTranscription());
        
        // Configuration modal
        this.elements.vadSensitivityConfig?.addEventListener('input', (e) => {
            this.elements.vadSensitivityValue.textContent = e.target.value;
        });
        
        this.elements.minConfidenceConfig?.addEventListener('input', (e) => {
            this.elements.minConfidenceValue.textContent = e.target.value;
        });
        
        this.elements.applyConfig?.addEventListener('click', () => this.applyConfiguration());
        
        // Load saved configuration
        this.loadConfiguration();
        
        // Auto-save configuration
        const configInputs = [
            'vadSensitivityConfig', 'minConfidenceConfig', 'enableSpeakerDetectionConfig',
            'enableSentimentAnalysisConfig', 'enableRealtimeConfig', 'enableWordTimestampsConfig'
        ];
        
        configInputs.forEach(id => {
            this.elements[id]?.addEventListener('change', () => {
                this.saveConfiguration();
            });
        });
        
        // Session timer
        setInterval(() => this.updateSessionTimer(), 1000);
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'r':
                        e.preventDefault();
                        if (!this.isRecording) this.startRecording();
                        break;
                    case 'p':
                        e.preventDefault();
                        if (this.isRecording) this.pauseRecording();
                        break;
                    case 's':
                        e.preventDefault();
                        if (this.isRecording) this.stopRecording();
                        break;
                    case 'e':
                        e.preventDefault();
                        this.exportTranscription();
                        break;
                }
            }
        });
    }
    
    async startRecording() {
        try {
            console.log('Starting recording...');
            
            // Create session
            await this.createSession();
            
            // Initialize audio processing
            if (this.audioProcessor) {
                await this.audioProcessor.initialize();
            }
            
            // Start audio capture
            if (this.websocketStreaming) {
                await this.websocketStreaming.startStreaming();
            }
            
            // Join session
            if (this.socket && this.sessionId) {
                this.socket.emit('join_session', { session_id: this.sessionId });
                this.socket.emit('start_transcription', { session_id: this.sessionId });
            }
            
            this.isRecording = true;
            this.isPaused = false;
            this.sessionStartTime = Date.now();
            
            this.updateUI();
            this.updateMicrophoneStatus('Recording');
            
            console.log('Recording started successfully');
            
        } catch (error) {
            console.error('Failed to start recording:', error);
            this.showError(`Failed to start recording: ${error.message}`);
        }
    }
    
    pauseRecording() {
        if (!this.isRecording || this.isPaused) return;
        
        this.isPaused = true;
        
        if (this.websocketStreaming) {
            this.websocketStreaming.pauseStreaming();
        }
        
        this.updateUI();
        this.updateMicrophoneStatus('Paused');
        console.log('Recording paused');
    }
    
    async stopRecording() {
        if (!this.isRecording) return;
        
        try {
            // Stop audio processing
            if (this.websocketStreaming) {
                await this.websocketStreaming.stopStreaming();
            }
            
            if (this.audioProcessor) {
                this.audioProcessor.cleanup();
            }
            
            // End session
            if (this.socket && this.sessionId) {
                this.socket.emit('stop_transcription', { session_id: this.sessionId });
                this.socket.emit('leave_session', { session_id: this.sessionId });
            }
            
            this.isRecording = false;
            this.isPaused = false;
            
            this.updateUI();
            this.updateMicrophoneStatus('Stopped');
            
            console.log('Recording stopped');
            
        } catch (error) {
            console.error('Error stopping recording:', error);
            this.showError(`Error stopping recording: ${error.message}`);
        }
    }
    
    async createSession() {
        try {
            const response = await fetch('/api/sessions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.currentSessionConfig)
            });
            
            if (!response.ok) {
                throw new Error(`Failed to create session: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.sessionId = data.session_id;
            
            console.log('Session created:', this.sessionId);
            
        } catch (error) {
            console.error('Failed to create session:', error);
            throw error;
        }
    }
    
    handleTranscriptionResult(data) {
        if (!this.elements.showInterim?.checked && !data.is_final) return;
        
        this.addTranscriptionSegment({
            text: data.text,
            confidence: data.confidence,
            isFinal: data.is_final,
            timestamp: data.timestamp,
            speaker: data.speaker || 'Speaker 1',
            words: data.words || []
        });
        
        // Update statistics
        if (data.is_final) {
            this.stats.segmentCount++;
            this.stats.totalConfidence += data.confidence;
        }
        
        this.stats.lastUpdate = new Date();
        this.updateStatistics();
    }
    
    handleInterimResult(data) {
        if (!this.elements.showInterim?.checked) return;
        
        // Update VAD status
        if (data.vad) {
            this.updateVADStatus(data.vad);
        }
        
        // Show interim transcription
        if (data.transcription) {
            this.addTranscriptionSegment({
                text: data.transcription.text,
                confidence: data.transcription.confidence,
                isFinal: false,
                timestamp: data.timestamp,
                speaker: 'Speaker 1'
            });
        }
    }
    
    addTranscriptionSegment(segment) {
        const container = this.elements.transcriptionContainer;
        if (!container) return;
        
        // Remove placeholder if exists
        const placeholder = container.querySelector('.text-center');
        if (placeholder) {
            placeholder.remove();
        }
        
        // Create segment element
        const segmentElement = document.createElement('div');
        segmentElement.className = `transcription-segment ${segment.isFinal ? 'final' : 'interim'}`;
        
        // Speaker label
        const speakerLabel = document.createElement('div');
        speakerLabel.className = `speaker-label ${this.getSpeakerClass(segment.speaker)}`;
        speakerLabel.textContent = segment.speaker;
        
        // Text content
        const textContent = document.createElement('div');
        textContent.className = 'segment-text';
        textContent.textContent = segment.text;
        
        // Confidence indicator
        const confidenceIndicator = document.createElement('div');
        confidenceIndicator.className = 'confidence-indicator';
        
        const confidenceBar = document.createElement('div');
        confidenceBar.className = `confidence-bar ${this.getConfidenceClass(segment.confidence)}`;
        confidenceBar.style.width = `${segment.confidence * 100}%`;
        
        confidenceIndicator.appendChild(confidenceBar);
        
        // Timestamp
        const timestamp = document.createElement('small');
        timestamp.className = 'text-muted timestamp';
        timestamp.textContent = new Date(segment.timestamp).toLocaleTimeString();
        
        // Assemble segment
        segmentElement.appendChild(speakerLabel);
        segmentElement.appendChild(textContent);
        segmentElement.appendChild(confidenceIndicator);
        segmentElement.appendChild(timestamp);
        
        // Add to container
        if (!segment.isFinal) {
            // Replace existing interim segment
            const existingInterim = container.querySelector('.transcription-segment.interim');
            if (existingInterim) {
                existingInterim.replaceWith(segmentElement);
            } else {
                container.appendChild(segmentElement);
            }
        } else {
            // Remove interim and add final
            const existingInterim = container.querySelector('.transcription-segment.interim');
            if (existingInterim) {
                existingInterim.remove();
            }
            container.appendChild(segmentElement);
        }
        
        // Auto-scroll
        if (this.elements.autoScroll?.checked) {
            container.scrollTop = container.scrollHeight;
        }
    }
    
    getSpeakerClass(speaker) {
        const speakerNumber = speaker.match(/\d+/)?.[0] || '1';
        return `speaker-${speakerNumber}`;
    }
    
    getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'confidence-high';
        if (confidence >= 0.6) return 'confidence-medium';
        return 'confidence-low';
    }
    
    sendAudioChunk(audioData, timestamp) {
        if (!this.socket || !this.sessionId || this.isPaused) return;
        
        // Convert audio data to base64 for transmission
        const base64Audio = this.audioDataToBase64(audioData);
        
        this.socket.emit('audio_chunk', {
            session_id: this.sessionId,
            audio_data: base64Audio,
            timestamp: timestamp
        });
    }
    
    audioDataToBase64(audioData) {
        // Convert Float32Array to Int16Array
        const int16Array = new Int16Array(audioData.length);
        for (let i = 0; i < audioData.length; i++) {
            int16Array[i] = Math.max(-32768, Math.min(32767, audioData[i] * 32768));
        }
        
        // Convert to base64
        const uint8Array = new Uint8Array(int16Array.buffer);
        return btoa(String.fromCharCode(...uint8Array));
    }
    
    updateAudioLevel(level) {
        if (this.elements.inputLevel) {
            this.elements.inputLevel.textContent = `${Math.round(level * 100)}%`;
        }
        
        // Update visualizer
        if (this.waveBars) {
            this.waveBars.forEach((bar, index) => {
                const height = Math.max(5, level * 50 * (1 + Math.sin(Date.now() * 0.01 + index) * 0.5));
                bar.style.height = `${height}px`;
                bar.style.setProperty('--wave-height', level);
                
                if (level > 0.1) {
                    bar.classList.add('active');
                } else {
                    bar.classList.remove('active');
                }
            });
        }
    }
    
    updateVADStatus(vadResult) {
        const vadStatus = this.elements.vadStatus;
        if (!vadStatus) return;
        
        if (vadResult.is_speech || vadResult.isSpeech) {
            vadStatus.textContent = 'Speaking';
            vadStatus.className = 'text-success';
        } else {
            vadStatus.textContent = 'Silence';
            vadStatus.className = 'text-muted';
        }
    }
    
    updateConnectionStatus(status, message) {
        const statusElement = this.elements.connectionStatus;
        const textElement = this.elements.connectionText;
        
        if (statusElement) {
            statusElement.className = `status-indicator status-${status}`;
        }
        
        if (textElement) {
            textElement.textContent = message;
        }
    }
    
    updateMicrophoneStatus(status) {
        if (this.elements.micStatus) {
            this.elements.micStatus.textContent = status;
        }
    }
    
    updateSessionTimer() {
        if (!this.sessionStartTime || !this.isRecording) return;
        
        const elapsed = Math.floor((Date.now() - this.sessionStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        
        if (this.elements.sessionTime) {
            this.elements.sessionTime.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
        
        if (this.isRecording && !this.isPaused) {
            this.stats.speakingTime = elapsed;
            this.updateStatistics();
        }
    }
    
    updateStatistics() {
        if (this.elements.segmentCount) {
            this.elements.segmentCount.textContent = this.stats.segmentCount;
        }
        
        if (this.elements.avgConfidence) {
            const avgConf = this.stats.segmentCount > 0 
                ? (this.stats.totalConfidence / this.stats.segmentCount * 100)
                : 0;
            this.elements.avgConfidence.textContent = `${Math.round(avgConf)}%`;
        }
        
        if (this.elements.speakingTime) {
            this.elements.speakingTime.textContent = `${this.stats.speakingTime}s`;
        }
        
        if (this.elements.lastUpdate && this.stats.lastUpdate) {
            this.elements.lastUpdate.textContent = this.stats.lastUpdate.toLocaleTimeString();
        }
    }
    
    updateUI() {
        const startBtn = this.elements.startButton;
        const pauseBtn = this.elements.pauseButton;
        const stopBtn = this.elements.stopButton;
        
        if (startBtn) {
            startBtn.disabled = this.isRecording;
            if (this.isRecording) {
                startBtn.classList.add('recording');
            } else {
                startBtn.classList.remove('recording');
            }
        }
        
        if (pauseBtn) {
            pauseBtn.disabled = !this.isRecording;
        }
        
        if (stopBtn) {
            stopBtn.disabled = !this.isRecording;
        }
    }
    
    clearTranscription() {
        const container = this.elements.transcriptionContainer;
        if (!container) return;
        
        container.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-microphone-slash fa-3x mb-3"></i>
                <h5>Transcription cleared</h5>
                <p>Start recording to see new transcription</p>
            </div>
        `;
        
        // Reset statistics
        this.stats = {
            segmentCount: 0,
            totalConfidence: 0,
            speakingTime: 0,
            lastUpdate: null
        };
        
        this.updateStatistics();
    }
    
    exportTranscription() {
        const container = this.elements.transcriptionContainer;
        if (!container) return;
        
        const segments = container.querySelectorAll('.transcription-segment.final');
        if (segments.length === 0) {
            this.showError('No transcription data to export');
            return;
        }
        
        let text = `Transcription Export - ${new Date().toLocaleString()}\n`;
        text += `Session: ${this.sessionId || 'Unknown'}\n`;
        text += `Segments: ${segments.length}\n\n`;
        
        segments.forEach((segment, index) => {
            const speaker = segment.querySelector('.speaker-label')?.textContent || 'Unknown';
            const content = segment.querySelector('.segment-text')?.textContent || '';
            const timestamp = segment.querySelector('.timestamp')?.textContent || '';
            
            text += `[${timestamp}] ${speaker}: ${content}\n`;
        });
        
        // Download as text file
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `transcription_${this.sessionId || 'export'}_${Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
    }
    
    loadConfiguration() {
        const saved = localStorage.getItem('minaTranscriptionConfig');
        if (saved) {
            try {
                this.currentSessionConfig = { ...this.currentSessionConfig, ...JSON.parse(saved) };
                this.updateConfigurationUI();
            } catch (error) {
                console.error('Failed to load configuration:', error);
            }
        }
    }
    
    saveConfiguration() {
        try {
            localStorage.setItem('minaTranscriptionConfig', JSON.stringify(this.currentSessionConfig));
        } catch (error) {
            console.error('Failed to save configuration:', error);
        }
    }
    
    updateConfigurationUI() {
        const config = this.currentSessionConfig;
        
        if (this.elements.sessionTitle) this.elements.sessionTitle.value = config.title;
        if (this.elements.sessionLanguage) this.elements.sessionLanguage.value = config.language;
        if (this.elements.sessionDescription) this.elements.sessionDescription.value = config.description;
        if (this.elements.vadSensitivityConfig) this.elements.vadSensitivityConfig.value = config.vadSensitivity;
        if (this.elements.minConfidenceConfig) this.elements.minConfidenceConfig.value = config.minConfidence;
        if (this.elements.enableSpeakerDetectionConfig) this.elements.enableSpeakerDetectionConfig.checked = config.enableSpeakerDetection;
        if (this.elements.enableSentimentAnalysisConfig) this.elements.enableSentimentAnalysisConfig.checked = config.enableSentimentAnalysis;
        if (this.elements.enableRealtimeConfig) this.elements.enableRealtimeConfig.checked = config.enableRealtime;
        if (this.elements.enableWordTimestampsConfig) this.elements.enableWordTimestampsConfig.checked = config.enableWordTimestamps;
        
        // Update value displays
        if (this.elements.vadSensitivityValue) this.elements.vadSensitivityValue.textContent = config.vadSensitivity;
        if (this.elements.minConfidenceValue) this.elements.minConfidenceValue.textContent = config.minConfidence;
        if (this.elements.languageStatus) this.elements.languageStatus.textContent = config.language;
    }
    
    applyConfiguration() {
        // Gather configuration from form
        this.currentSessionConfig = {
            title: this.elements.sessionTitle?.value || 'Live Session',
            description: this.elements.sessionDescription?.value || '',
            language: this.elements.sessionLanguage?.value || 'en',
            vadSensitivity: parseFloat(this.elements.vadSensitivityConfig?.value || 0.5),
            minConfidence: parseFloat(this.elements.minConfidenceConfig?.value || 0.7),
            enableSpeakerDetection: this.elements.enableSpeakerDetectionConfig?.checked || false,
            enableSentimentAnalysis: this.elements.enableSentimentAnalysisConfig?.checked || false,
            enableRealtime: this.elements.enableRealtimeConfig?.checked || true,
            enableWordTimestamps: this.elements.enableWordTimestampsConfig?.checked || true
        };
        
        // Update audio processor configuration
        if (this.audioProcessor) {
            this.audioProcessor.updateConfig({
                vadSensitivity: this.currentSessionConfig.vadSensitivity
            });
        }
        
        // Update UI
        this.updateConfigurationUI();
        this.saveConfiguration();
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('sessionConfigModal'));
        if (modal) modal.hide();
        
        // Show success message
        this.showSuccess('Configuration applied successfully');
        
        console.log('Configuration applied:', this.currentSessionConfig);
    }
    
    showError(message) {
        this.showAlert(message, 'danger');
    }
    
    showSuccess(message) {
        this.showAlert(message, 'success');
    }
    
    showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('main');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.minaTranscription = new RealTimeTranscription();
});

// Export for use in other modules
window.RealTimeTranscription = RealTimeTranscription;
