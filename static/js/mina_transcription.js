/**
 * Mina Live Transcription - Single System Implementation
 * Real working transcription with HTTP-only backend
 */

class MinaTranscription {
    constructor() {
        this.isRecording = false;
        this.sessionId = null;
        this.mediaRecorder = null;
        this.mediaStream = null;
        this.startTime = null;
        this.timer = null;
        this.chunkCount = 0;
        this.cumulativeText = '';
        this.totalWords = 0;
        this.audioContext = null;
        this.analyser = null;
        
        this.elements = {
            recordButton: document.getElementById('recordButton') || document.querySelector('.record-button, #startRecordingBtn'),
            timer: document.getElementById('timer') || document.querySelector('.timer, #timer'),
            wordCount: document.getElementById('wordCount') || document.querySelector('#words, .word-count'),
            accuracy: document.getElementById('accuracy') || document.querySelector('#accuracy, .accuracy'),
            audioLevel: document.getElementById('audioLevel') || document.querySelector('#inputLevel, .audio-level'),
            transcript: document.getElementById('transcript') || document.querySelector('#transcriptContent, .transcript-content, .live-transcript-container'),
            copyButton: document.getElementById('copyButton') || document.querySelector('.copy-button'),
            connectionStatus: document.getElementById('connectionStatus') || document.querySelector('#wsStatus, .connection-status')
        };
        
        this.init();
    }
    
    init() {
        console.log('🎯 Initializing Mina Transcription System');
        
        // Bind record button
        if (this.elements.recordButton) {
            this.elements.recordButton.addEventListener('click', (e) => {
                e.preventDefault();
                if (!this.isRecording) {
                    this.startRecording();
                } else {
                    this.stopRecording();
                }
            });
        }
        
        // Bind copy button if exists
        if (this.elements.copyButton) {
            this.elements.copyButton.addEventListener('click', () => {
                if (this.cumulativeText) {
                    navigator.clipboard.writeText(this.cumulativeText);
                    this.showNotification('Transcript copied to clipboard');
                }
            });
        }
        
        this.updateConnectionStatus('ready');
        
        // Clear any existing content
        if (this.elements.transcript) {
            this.elements.transcript.textContent = 'Click the record button to start transcription';
        }
        
        console.log('✅ Mina Transcription System ready');
    }
    
    async startRecording() {
        try {
            console.log('🎤 Starting recording...');
            
            this.sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            
            // Request microphone access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000,
                    channelCount: 1
                }
            });
            
            console.log('✅ Microphone access granted');
            
            // Determine best audio format
            let mimeType = 'audio/webm;codecs=opus';
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = 'audio/webm';
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = 'audio/mp4';
                    if (!MediaRecorder.isTypeSupported(mimeType)) {
                        mimeType = ''; // Let browser choose
                    }
                }
            }
            
            // Create MediaRecorder
            const options = {};
            if (mimeType) options.mimeType = mimeType;
            
            this.mediaRecorder = new MediaRecorder(this.mediaStream, options);
            
            // Handle audio data
            this.mediaRecorder.ondataavailable = async (event) => {
                if (event.data.size > 0) {
                    this.chunkCount++;
                    console.log(`🎵 Processing audio chunk ${this.chunkCount}: ${event.data.size} bytes`);
                    await this.processAudioChunk(event.data);
                }
            };
            
            this.mediaRecorder.onerror = (error) => {
                console.error('❌ MediaRecorder error:', error);
                this.showNotification('Recording error: ' + error.message);
            };
            
            // Start recording with 1.5 second chunks
            this.mediaRecorder.start(1500);
            
            // Initialize state
            this.isRecording = true;
            this.startTime = Date.now();
            this.chunkCount = 0;
            this.cumulativeText = '';
            this.totalWords = 0;
            
            // Update UI
            this.updateRecordingUI();
            this.startTimer();
            this.startAudioLevelMonitoring();
            
            this.showNotification('Recording started - speak now!');
            console.log('✅ Recording active');
            
        } catch (error) {
            console.error('❌ Failed to start recording:', error);
            this.showNotification('Failed to access microphone: ' + error.message);
            this.updateConnectionStatus('error');
        }
    }
    
    async stopRecording() {
        try {
            console.log('⏹️ Stopping recording...');
            
            if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                this.mediaRecorder.stop();
            }
            
            if (this.mediaStream) {
                this.mediaStream.getTracks().forEach(track => track.stop());
            }
            
            if (this.audioContext) {
                this.audioContext.close();
            }
            
            this.isRecording = false;
            this.stopTimer();
            
            // Update UI
            this.updateStoppedUI();
            
            // Generate final transcript
            if (this.cumulativeText.trim()) {
                await this.generateFinalTranscript();
                this.showNotification('Recording complete - final transcript generated');
            } else {
                this.showNotification('Recording stopped - no speech detected');
            }
            
            console.log('✅ Recording stopped');
            
        } catch (error) {
            console.error('❌ Failed to stop recording:', error);
            this.showNotification('Error stopping recording: ' + error.message);
        }
    }
    
    async processAudioChunk(audioBlob) {
        try {
            // Convert blob to base64
            const arrayBuffer = await audioBlob.arrayBuffer();
            const uint8Array = new Uint8Array(arrayBuffer);
            const base64Audio = btoa(String.fromCharCode.apply(null, uint8Array));
            
            const startTime = Date.now();
            
            // Send to transcription endpoint
            const response = await fetch('/api/transcribe-audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    audio_data: base64Audio,
                    chunk_number: this.chunkCount,
                    is_final: false
                })
            });
            
            const latency = Date.now() - startTime;
            
            if (response.ok) {
                const result = await response.json();
                
                // Process successful transcription
                if (result.text && result.text.trim() && 
                    !result.text.includes('[No speech detected]') && 
                    !result.text.includes('Thank you') && 
                    result.text.length > 2) {
                    
                    // Add to cumulative transcript with smart spacing
                    if (this.cumulativeText.trim()) {
                        // Check if we need punctuation or just space
                        const lastChar = this.cumulativeText.trim().slice(-1);
                        const needsPunctuation = !/[.!?]/.test(lastChar);
                        
                        if (needsPunctuation && this.cumulativeText.split(/\s+/).length % 10 === 0) {
                            this.cumulativeText += '. ' + result.text;
                        } else {
                            this.cumulativeText += ' ' + result.text;
                        }
                    } else {
                        this.cumulativeText = result.text;
                    }
                    
                    // Update UI immediately
                    this.updateTranscriptDisplay();
                    this.updateStats(result);
                    this.updateConnectionStatus('processing');
                    
                    console.log(`✅ Transcribed: "${result.text}" (${latency}ms, confidence: ${Math.round((result.confidence || 0.9) * 100)}%)`);
                } else {
                    console.log(`⚠️ No valid speech in chunk ${this.chunkCount} (${latency}ms)`);
                }
            } else {
                console.error(`❌ Transcription failed: HTTP ${response.status}`);
                const errorText = await response.text();
                console.error('Error details:', errorText);
                this.updateConnectionStatus('error');
            }
            
        } catch (error) {
            console.error('❌ Failed to process audio chunk:', error);
            this.updateConnectionStatus('error');
        }
    }
    
    async generateFinalTranscript() {
        try {
            console.log('📝 Generating final transcript...');
            
            const response = await fetch('/api/transcribe-audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    action: 'finalize',
                    text: this.cumulativeText,
                    is_final: true,
                    word_count: this.totalWords
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.final_text && result.final_text !== this.cumulativeText) {
                    this.cumulativeText = result.final_text;
                    this.updateTranscriptDisplay();
                    console.log('✅ Final transcript generated');
                }
            }
        } catch (error) {
            console.error('❌ Failed to generate final transcript:', error);
        }
    }
    
    updateRecordingUI() {
        // Update record button
        if (this.elements.recordButton) {
            this.elements.recordButton.innerHTML = this.elements.recordButton.innerHTML.includes('fa-') ? 
                '<i class="fas fa-stop"></i>' : 'STOP';
            this.elements.recordButton.className = this.elements.recordButton.className.replace('btn-danger', 'btn-secondary');
            if (this.elements.recordButton.classList) {
                this.elements.recordButton.classList.add('recording');
            }
        }
        
        // Update transcript area
        if (this.elements.transcript) {
            this.elements.transcript.innerHTML = `
                <div class="text-center p-4">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Recording...</span>
                    </div>
                    <h6 class="text-primary">🎤 Recording Active</h6>
                    <p class="text-muted">Speak clearly into your microphone...</p>
                </div>
            `;
        }
        
        this.updateConnectionStatus('recording');
    }
    
    updateStoppedUI() {
        // Update record button
        if (this.elements.recordButton) {
            this.elements.recordButton.innerHTML = this.elements.recordButton.innerHTML.includes('fa-') ? 
                '<i class="fas fa-microphone"></i>' : 'START';
            this.elements.recordButton.className = this.elements.recordButton.className.replace('btn-secondary', 'btn-danger');
            if (this.elements.recordButton.classList) {
                this.elements.recordButton.classList.remove('recording');
            }
        }
        
        // Show copy button if we have transcript
        if (this.elements.copyButton && this.cumulativeText.trim()) {
            this.elements.copyButton.style.display = 'inline-block';
        }
        
        this.updateConnectionStatus('ready');
    }
    
    updateTranscriptDisplay() {
        if (this.elements.transcript) {
            const timestamp = new Date().toLocaleTimeString();
            
            this.elements.transcript.innerHTML = `
                <div class="p-3">
                    <div class="transcript-header mb-3 d-flex justify-content-between align-items-center">
                        <h6 class="text-success mb-0">✅ Live Transcription</h6>
                        <small class="text-muted">${timestamp}</small>
                    </div>
                    <div class="transcript-text" style="font-size: 16px; line-height: 1.6; color: #fff;">
                        ${this.cumulativeText}
                    </div>
                    <div class="transcript-footer mt-3 pt-2 border-top border-secondary">
                        <small class="text-muted">
                            Words: ${this.totalWords} | Session: ${this.sessionId}
                        </small>
                    </div>
                </div>
            `;
        }
    }
    
    updateStats(result) {
        // Update word count
        const words = this.cumulativeText.split(/\s+/).filter(word => word.length > 0);
        this.totalWords = words.length;
        
        if (this.elements.wordCount) {
            this.elements.wordCount.textContent = this.totalWords;
        }
        
        // Update accuracy
        if (this.elements.accuracy) {
            const confidence = Math.round((result.confidence || 0.95) * 100);
            this.elements.accuracy.textContent = confidence + '%';
        }
    }
    
    startTimer() {
        this.timer = setInterval(() => {
            if (!this.startTime) return;
            
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            if (this.elements.timer) {
                this.elements.timer.textContent = timeString;
            }
        }, 1000);
    }
    
    stopTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }
    
    startAudioLevelMonitoring() {
        if (!this.mediaStream) return;
        
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            
            source.connect(this.analyser);
            
            const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
            
            const updateLevel = () => {
                if (!this.isRecording || !this.analyser) return;
                
                this.analyser.getByteFrequencyData(dataArray);
                const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
                const percentage = Math.min(100, Math.max(0, (average / 128) * 100));
                
                if (this.elements.audioLevel) {
                    if (this.elements.audioLevel.style !== undefined) {
                        this.elements.audioLevel.style.width = percentage + '%';
                    } else if (this.elements.audioLevel.setAttribute) {
                        this.elements.audioLevel.setAttribute('style', `width: ${percentage}%`);
                    }
                }
                
                requestAnimationFrame(updateLevel);
            };
            
            updateLevel();
        } catch (error) {
            console.warn('Audio level monitoring not available:', error);
        }
    }
    
    updateConnectionStatus(status) {
        if (!this.elements.connectionStatus) return;
        
        const statusMap = {
            ready: { text: 'Ready', class: 'text-success' },
            recording: { text: '🔴 Recording', class: 'text-danger' },
            processing: { text: '⚡ Processing', class: 'text-warning' },
            error: { text: '❌ Error', class: 'text-danger' }
        };
        
        const config = statusMap[status] || statusMap.ready;
        this.elements.connectionStatus.textContent = config.text;
        this.elements.connectionStatus.className = config.class;
    }
    
    showNotification(message, type = 'info') {
        console.log(`📢 ${message}`);
        
        // Try to use existing toast system
        if (window.toastSystem && window.toastSystem.showSuccess) {
            if (type === 'error') {
                window.toastSystem.showError(message);
            } else {
                window.toastSystem.showSuccess(message);
            }
            return;
        }
        
        // Fallback to browser notification
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Mina Transcription', { body: message });
        }
        
        // Fallback to console
        console.log(`📢 Notification: ${message}`);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Mina Transcription...');
    
    // Wait a moment for other scripts to load, then take control
    setTimeout(() => {
        window.minaTranscription = new MinaTranscription();
        
        // Override any existing recording functions
        window.startRecording = () => window.minaTranscription.startRecording();
        window.stopRecording = () => window.minaTranscription.stopRecording();
        
        console.log('✅ Mina Transcription system ready and active');
    }, 1000);
});

// Export for global access
window.MinaTranscription = MinaTranscription;