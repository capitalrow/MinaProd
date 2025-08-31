/**
 * Real Whisper API Integration for Main Live Transcription Page
 * Replaces Socket.IO with direct WebSocket connection to real Whisper transcription
 */

class RealWhisperIntegration {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.isRecording = false;
        this.sessionId = null;
        this.mediaRecorder = null;
        this.mediaStream = null;
        this.connectionAttempts = 0;
        this.maxConnectionAttempts = 3;
        
        // Real-time transcription state
        this.transcriptionBuffer = [];
        this.cumulativeTranscript = '';  // For building progressive transcript
        this.chunkCount = 0;  // Track number of chunks processed
        this.processingFeedback = false;
        
        console.log('Real Whisper Integration initialized');
    }
    
    async sendAudioDataHTTP(audioBlob) {
        // Send audio data to transcription service via HTTP POST
        if (!this.httpEndpoint) {
            console.error('❌ HTTP endpoint not configured');
            return;
        }
        
        try {
            console.log(`📤 Uploading audio chunk ${this.chunkCount}: ${audioBlob.size} bytes`);
            
            // Create FormData for HTTP upload
            const formData = new FormData();
            formData.append('audio', audioBlob, `chunk_${this.chunkCount}.webm`);
            formData.append('session_id', this.sessionId || 'default');
            formData.append('chunk_id', this.chunkCount.toString());
            formData.append('timestamp', Date.now().toString());
            
            // Send HTTP POST request with timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000);
            
            const response = await fetch(this.httpEndpoint, {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                console.log(`✅ Chunk ${this.chunkCount} transcribed: "${result.transcript}"`);
                
                // Display the transcript in real-time
                this.displayTranscript(result.transcript, result.segments || [], this.chunkCount);
                
                // Process transcription result
                this.handleHTTPTranscriptionResult(result);
                
                // Update performance metrics
                this.updatePerformanceMetrics({
                    processing_time: result.processing_time,
                    segment_count: result.segment_count,
                    confidence: result.segments?.[0]?.confidence || 0
                });
                
                return result;
                
            } else {
                throw new Error(result.error || 'Transcription failed');
            }
            
        } catch (error) {
            if (error.name === 'AbortError') {
                console.error(`❌ Chunk ${this.chunkCount} timeout after 10 seconds`);
                this.showTranscriptionError('Transcription timeout - please try again');
            } else {
                console.error(`❌ Chunk ${this.chunkCount} failed:`, error);
                this.showTranscriptionError(`Transcription failed: ${error.message}`);
            }
            
            // Update error statistics
            this.updateErrorStats(error);
            throw error;
        }
    }
    
    handleHTTPTranscriptionResult(result) {
        // Process transcription result from HTTP endpoint
        if (!result.transcript || !result.transcript.trim()) {
            console.log('⚠️ Empty transcript received');
            return;
        }
        
        // Add to cumulative transcript
        const newText = result.transcript.trim();
        this.cumulativeTranscript += newText + ' ';
        
        // Update transcript display in real-time
        this.updateTranscriptDisplay(newText, result.segments || []);
        
        // Update session statistics
        this.updateSessionStats({
            wordCount: this.cumulativeTranscript.split(' ').filter(w => w.length > 0).length,
            duration: result.audio_duration || 0,
            accuracy: result.segments?.[0]?.confidence || 0,
            chunks: this.chunkCount,
            latency: result.processing_time || 0
        });
        
        console.log(`📝 Updated transcript: ${this.cumulativeTranscript.length} characters total`);
    }
    
    updateTranscriptDisplay(newText, segments) {
        // Update the live transcript area with new transcription
        const transcriptArea = document.getElementById('transcriptContainer') || 
                              document.getElementById('transcriptArea') ||
                              document.querySelector('.transcript-content');
        if (!transcriptArea) {
            console.warn('⚠️ Transcript area not found');
            return;
        }
        
        // Remove placeholder if present
        const placeholder = transcriptArea.querySelector('.transcript-placeholder');
        if (placeholder) {
            placeholder.remove();
        }
        
        // Create new segment element with better styling
        const segmentDiv = document.createElement('div');
        segmentDiv.className = 'transcript-segment mb-2 p-2 border-start border-3 border-info';
        segmentDiv.style.animation = 'fadeIn 0.3s ease-in';
        
        const timestamp = new Date().toLocaleTimeString();
        segmentDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <span class="segment-text flex-grow-1">${this.escapeHtml(newText)}</span>
                <small class="segment-time text-muted ms-2">${timestamp}</small>
            </div>
        `;
        
        // Add confidence indicator if available
        if (segments && segments.length > 0 && segments[0].confidence !== undefined) {
            const confidence = Math.abs(segments[0].confidence);
            const confidencePercent = Math.round((1 - confidence) * 100);
            
            // Update confidence score display
            const confidenceScore = document.getElementById('confidenceScore');
            if (confidenceScore) {
                confidenceScore.textContent = `${confidencePercent}%`;
            }
            
            // Add visual confidence indicator
            if (confidence < 0.5) {
                segmentDiv.classList.add('border-success');
            } else if (confidence < 1.0) {
                segmentDiv.classList.add('border-warning');
            } else {
                segmentDiv.classList.add('border-danger');
            }
        }
        
        // Add to transcript area
        transcriptArea.appendChild(segmentDiv);
        
        // Auto-scroll to bottom for real-time updates
        transcriptArea.scrollTop = transcriptArea.scrollHeight;
        
        // Update statistics
        const wordCount = newText.split(' ').filter(w => w.length > 0).length;
        const wordsElement = document.getElementById('wordsCount');
        if (wordsElement) {
            const currentCount = parseInt(wordsElement.textContent) || 0;
            wordsElement.textContent = currentCount + wordCount;
        }
        
        // Update chunks processed
        const chunksElement = document.getElementById('chunksProcessed');
        if (chunksElement) {
            chunksElement.textContent = this.chunkCount;
        }
        
        // Announce to screen readers
        this.announceTranscript(newText);
        
        console.log(`📝 Displayed transcript: ${newText.substring(0, 50)}...`);
    }
    
    announceTranscript(text) {
        // Announce new transcript to screen readers
        let liveRegion = document.getElementById('transcriptLiveRegion');
        if (!liveRegion) {
            // Create live region for screen reader announcements
            liveRegion = document.createElement('div');
            liveRegion.id = 'transcriptLiveRegion';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'false');
            liveRegion.className = 'sr-only';
            document.body.appendChild(liveRegion);
        }
        
        // Announce new transcript text
        liveRegion.textContent = `New transcript: ${text}`;
    }
    
    escapeHtml(text) {
        // Escape HTML characters for safe display
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    updateSessionStats(stats) {
        // Update session statistics in the UI
        try {
            // Update word count
            const wordCountElement = document.getElementById('wordCount');
            if (wordCountElement && stats.wordCount !== undefined) {
                wordCountElement.textContent = stats.wordCount;
            }
            
            // Update duration
            const sessionTimeElement = document.getElementById('sessionTime');
            if (sessionTimeElement && stats.duration !== undefined) {
                const minutes = Math.floor(stats.duration / 60);
                const seconds = Math.floor(stats.duration % 60);
                sessionTimeElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
            
            // Update confidence/accuracy
            const confidenceElement = document.getElementById('confidenceScore');
            if (confidenceElement && stats.accuracy !== undefined) {
                confidenceElement.textContent = `${Math.round(stats.accuracy * 100)}%`;
            }
            
            // Update chunk count
            const chunksElement = document.getElementById('chunks');
            if (chunksElement && stats.chunks !== undefined) {
                chunksElement.textContent = stats.chunks;
            }
            
            // Update latency
            const latencyElement = document.getElementById('latency');
            if (latencyElement && stats.latency !== undefined) {
                latencyElement.textContent = `${Math.round(stats.latency * 1000)}ms`;
            }
            
        } catch (error) {
            console.warn('⚠️ Failed to update session stats:', error);
        }
    }
    
    updatePerformanceMetrics(metrics) {
        // Update real-time performance metrics
        try {
            // Update quality score
            const qualityElement = document.getElementById('quality');
            if (qualityElement && metrics.confidence !== undefined) {
                qualityElement.textContent = `${Math.round(Math.abs(metrics.confidence) * 100)}%`;
            }
            
            // Update processing time
            const latencyElement = document.getElementById('latency');
            if (latencyElement && metrics.processing_time !== undefined) {
                latencyElement.textContent = `${Math.round(metrics.processing_time * 1000)}ms`;
            }
            
            console.log(`📊 Performance updated: ${Math.round(metrics.processing_time * 1000)}ms latency`);
            
        } catch (error) {
            console.warn('⚠️ Failed to update performance metrics:', error);
        }
    }
    
    showTranscriptionError(message) {
        // Display user-friendly transcription error
        console.error('🚨 Transcription Error:', message);
        
        // Update status indicators
        const statusText = document.getElementById('statusText');
        const statusDot = document.getElementById('statusDot');
        
        if (statusText) {
            statusText.textContent = 'Error';
        }
        
        if (statusDot) {
            statusDot.className = 'status-dot error';
        }
        
        // Show error notification
        const header = document.querySelector('.app-header .header-content');
        if (header) {
            // Remove existing errors
            const existing = header.querySelector('.transcription-error');
            if (existing) existing.remove();
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'transcription-error alert alert-danger mt-2';
            errorDiv.setAttribute('role', 'alert');
            errorDiv.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="fas fa-exclamation-triangle me-2" aria-hidden="true"></i>
                    <span class="flex-grow-1">${message}</span>
                    <button type="button" class="btn-close" aria-label="Close error message" onclick="this.parentElement.parentElement.remove()"></button>
                </div>
            `;
            header.appendChild(errorDiv);
            
            // Auto-remove after 10 seconds
            setTimeout(() => {
                if (errorDiv.parentElement) {
                    errorDiv.remove();
                }
            }, 10000);
        }
        
        // Announce error to screen readers
        this.announceError(message);
    }
    
    announceError(message) {
        // Announce error to screen readers
        let errorRegion = document.getElementById('errorLiveRegion');
        if (!errorRegion) {
            errorRegion = document.createElement('div');
            errorRegion.id = 'errorLiveRegion';
            errorRegion.setAttribute('aria-live', 'assertive');
            errorRegion.setAttribute('aria-atomic', 'true');
            errorRegion.className = 'sr-only';
            document.body.appendChild(errorRegion);
        }
        
        errorRegion.textContent = `Error: ${message}`;
    }
    
    updateErrorStats(error) {
        // Track error statistics for monitoring
        // Simple error counting for now
        if (!this.errorCount) this.errorCount = 0;
        this.errorCount++;
        
        console.warn(`⚠️ Error count: ${this.errorCount}`);
    }
    
    showChunkProcessingFeedback(chunkNumber, chunkSize) {
        // Update chunk processing feedback in the UI
        try {
            const chunksElement = document.getElementById('chunks');
            if (chunksElement) {
                chunksElement.textContent = chunkNumber;
            }
            
            // Update processing indicator
            const processingElement = document.getElementById('currentProcessing');
            if (processingElement) {
                processingElement.style.display = 'block';
                const processingText = processingElement.querySelector('#processingText');
                if (processingText) {
                    processingText.textContent = `Processing chunk ${chunkNumber} (${Math.round(chunkSize/1024)}KB)...`;
                }
            }
            
            console.log(`📊 Chunk ${chunkNumber} feedback updated in UI`);
        } catch (error) {
            console.warn('⚠️ Failed to update chunk feedback:', error);
        }
    }
    
    clearTranscriptArea() {
        // Clear the transcript area and reset placeholders
        try {
            const transcriptArea = document.getElementById('transcriptArea') || 
                                 document.querySelector('.transcript-container') ||
                                 document.querySelector('.complete-transcript-display');
            
            if (transcriptArea) {
                // Remove all transcript segments but keep structure
                const segments = transcriptArea.querySelectorAll('.transcript-segment');
                segments.forEach(segment => segment.remove());
                
                console.log('🧹 Transcript area cleared');
            }
        } catch (error) {
            console.warn('⚠️ Failed to clear transcript area:', error);
        }
    }
    
    showTranscriptionActive() {
        // Update UI to show active transcription state
        try {
            // Update status indicators
            const statusText = document.getElementById('statusText');
            const statusDot = document.getElementById('statusDot');
            
            if (statusText) {
                statusText.textContent = 'Recording...';
            }
            
            if (statusDot) {
                statusDot.className = 'status-dot recording';
            }
            
            // Show processing indicator
            const currentProcessing = document.getElementById('currentProcessing');
            if (currentProcessing) {
                currentProcessing.style.display = 'block';
            }
            
            console.log('🎤 Active transcription state displayed');
        } catch (error) {
            console.warn('⚠️ Failed to update active status:', error);
        }
    }
    
    async stopTranscription() {
        // Stop audio recording and transcription
        try {
            console.log('🛑 Stopping HTTP transcription...');
            
            if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
                this.mediaRecorder.stop();
                console.log('📹 MediaRecorder stopped');
            }
            
            if (this.mediaStream) {
                this.mediaStream.getTracks().forEach(track => track.stop());
                console.log('🎤 Media stream stopped');
            }
            
            // Update UI state
            const statusText = document.getElementById('statusText');
            const statusDot = document.getElementById('statusDot');
            
            if (statusText) {
                statusText.textContent = 'Ready';
            }
            
            if (statusDot) {
                statusDot.className = 'status-dot ready';
            }
            
            // Hide processing indicator
            const currentProcessing = document.getElementById('currentProcessing');
            if (currentProcessing) {
                currentProcessing.style.display = 'none';
            }
            
            console.log('✅ HTTP transcription stopped successfully');
            return true;
            
        } catch (error) {
            console.error('❌ Failed to stop transcription:', error);
            throw error;
        }
    }
    
    async initializeConnection() {
        try {
            console.log('🔗 Initializing real-time transcription connection...');
            
            // MANUAL MONITORING RECOMMENDATION #1: Smart port detection with fallback
            // Try multiple ports to find working Enhanced WebSocket server
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.hostname;
            // CRITICAL FIX: Use same host as web page, not localhost
            const portsToTry = ['8774', '8775', '8776', '8773'];  // Try alternatives first
            
            console.log(`🔍 Connecting to host: ${host} (not localhost)`);
            
            // CRITICAL FIX: Skip WebSocket, use HTTP-based transcription directly
            console.log('🌐 Switching to HTTP-based transcription for maximum reliability');
            
            // Test basic connectivity to Flask server
            const baseUrl = `${window.location.protocol}//${window.location.host}`;
            console.log(`🔍 Testing Flask server connectivity: ${baseUrl}`);
            
            try {
                const response = await fetch(`${baseUrl}/health`);
                if (response.ok) {
                    console.log('✅ Flask server connectivity verified');
                } else {
                    console.warn('⚠️ Flask server responding but may have issues');
                }
            } catch (error) {
                console.error('❌ Flask server connectivity failed:', error);
                throw new Error('Cannot connect to transcription service');
            }
            
            // Initialize HTTP-based transcription mode
            this.useHttpMode = true;
            this.httpEndpoint = `${baseUrl}/api/transcribe`;
            console.log(`📡 HTTP transcription endpoint: ${this.httpEndpoint}`);
            
            // CRITICAL FIX: HTTP mode setup, no WebSocket handlers needed
            this.isConnected = true;
            this.connectionAttempts = 0;
            console.log('✅ HTTP transcription mode ready');
            
            // Update UI with connection status
            if (window.professionalRecorder) {
                window.professionalRecorder.updateConnectionStatus('connected');
            }
            
            // Show success notification
            if (window.toastSystem) {
                window.toastSystem.showSuccess('🔗 HTTP transcription service ready');
            }
            
            // Message handler will be set up after connection handshake
            
            this.socket.onclose = () => {
                this.isConnected = false;
                console.log('🔌 Real-time transcription disconnected');
                this.handleReconnection();
                
                // Update UI
                if (window.professionalRecorder) {
                    window.professionalRecorder.updateConnectionStatus('disconnected');
                }
            };
            
            this.socket.onerror = (error) => {
                console.error('❌ Enhanced WebSocket connection error:', error);
                this.handleConnectionError(error);
                
                // Show error notification
                if (window.toastSystem) {
                    window.toastSystem.showError('❌ Connection failed - retrying...');
                }
            };
            
            // Enhanced WebSocket connection with message handling
            return new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Enhanced WebSocket connection timeout after 10 seconds'));
                }, 10000);
                
                this.socket.onopen = () => {
                    console.log('🔗 Enhanced WebSocket connection opened, waiting for server handshake...');
                    // Don't resolve immediately, wait for server welcome message
                };
                
                this.socket.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log('📨 Server message:', data);
                        
                        if (data.type === 'connected') {
                            clearTimeout(timeout);
                            this.isConnected = true;
                            this.connectionAttempts = 0;
                            console.log('✅ Enhanced WebSocket Server handshake complete:', data.server);
                            resolve();
                        } else {
                            // Handle other message types during connection
                            this.handleTranscriptionMessage(data);
                        }
                    } catch (e) {
                        console.warn('📨 Non-JSON message during connection:', event.data);
                    }
                };
                
                this.socket.onerror = (error) => {
                    clearTimeout(timeout);
                    console.error('❌ Enhanced WebSocket connection error:', error);
                    reject(new Error(`Enhanced WebSocket connection failed: ${error.message || error}`));
                };
            });
            
            // Set up message handler for ongoing communication
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleTranscriptionMessage(data);
                } catch (e) {
                    console.warn('📨 Non-JSON message received:', event.data);
                }
            };
            
        } catch (error) {
            console.error('Failed to initialize connection:', error);
            throw error;
        }
    }
    
    // Enhanced WebSocket client with proper session management
    
    async startTranscription(sessionId) {
        try {
            console.log('🎯 STARTING HTTP TRANSCRIPTION');
            
            // Initialize HTTP-based transcription mode
            if (!this.isConnected) {
                await this.initializeConnection();
            }
            
            this.sessionId = sessionId || `session_${Date.now()}`;
            
            // CRITICAL: Reset cumulative transcript for new recording
            this.cumulativeTranscript = '';
            this.chunkCount = 0;
            this.transcriptionBuffer = [];
            console.log('🎯 RESET: Starting fresh HTTP transcription session');
            
            // CRITICAL: Clear the transcript area and show active status
            this.clearTranscriptArea();
            this.showTranscriptionActive();
            
            // Initialize audio recording for HTTP upload
            await this.initializeAudioRecordingHTTP();
            
            console.log('✅ HTTP-based transcription started');
            return true;
            
        } catch (error) {
            console.error('Failed to start transcription:', error);
            throw error;
        }
    }
    
    clearTranscriptArea() {
        const transcriptContainer = document.querySelector('.live-transcript-container') ||
                                  document.getElementById('transcript') || 
                                  document.getElementById('transcriptContent') ||
                                  document.querySelector('.transcript-content');
                                  
        if (transcriptContainer) {
            transcriptContainer.innerHTML = '';
            console.log('🧹 Transcript area cleared');
        }
    }
    
    showTranscriptionActive() {
        const transcriptContainer = document.querySelector('.live-transcript-container') ||
                                  document.getElementById('transcript') || 
                                  document.getElementById('transcriptContent') ||
                                  document.querySelector('.transcript-content');
                                  
        if (transcriptContainer) {
            transcriptContainer.innerHTML = `
                <div class="transcription-active p-3 text-center">
                    <div class="spinner-border text-success mb-2" role="status">
                        <span class="visually-hidden">Processing...</span>
                    </div>
                    <h6 class="text-success">🎤 Live Transcription Active</h6>
                    <p class="text-muted mb-0">Listening for speech...</p>
                </div>
            `;
            console.log('🎤 Showing active transcription status');
        }
    }
    
    async initializeAudioRecordingHTTP() {
        try {
            // Get microphone access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000
                }
            });
            
            // Set up MediaRecorder for high-quality audio
            const options = {
                mimeType: 'audio/webm;codecs=opus',
                audioBitsPerSecond: 128000
            };
            
            // Fallback for browsers that don't support webm/opus
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                options.mimeType = 'audio/webm';
            }
            
            this.mediaRecorder = new MediaRecorder(this.mediaStream, options);
            
            // CRITICAL FIX: Handle audio data via HTTP upload
            this.mediaRecorder.ondataavailable = async (event) => {
                if (event.data.size > 0) {
                    this.chunkCount++;
                    
                    console.log(`📦 Collected chunk ${this.chunkCount}: ${event.data.size} bytes`);
                    
                    // DISABLED: Automatic chunk sending - now handled by audio_chunk_handler.js
                    // The audio_chunk_handler will collect all chunks and send complete audio
                    // when recording stops, providing better compatibility with OpenAI API
                    
                    // try {
                    //     // Send audio data via HTTP POST
                    //     await this.sendAudioDataHTTP(event.data);
                    //     
                    //     // Show chunk processing feedback in UI
                    //     this.showChunkProcessingFeedback(this.chunkCount, event.data.size);
                    //     
                    //     // Update UI with audio transmission feedback
                    //     if (this.chunkCount % 2 === 0 && window.toastSystem) {
                    //         window.toastSystem.showInfo(`🎵 Processing chunk ${this.chunkCount}...`);
                    //     }
                    // } catch (error) {
                    //     console.error(`❌ Failed to process chunk ${this.chunkCount}:`, error);
                    // }
                } else {
                    console.warn('⚠️ Cannot send audio: WebSocket not ready or no data');
                }
            };
            
            // Start recording with 1-second chunks for optimal accuracy
            this.mediaRecorder.start(1000);
            this.isRecording = true;
            
            console.log('🎤 Audio recording initialized');
            console.log('✅ Real Whisper Integration: MediaRecorder active, ready for transcription');
            
        } catch (error) {
            console.error('Failed to initialize audio recording:', error);
            throw error;
        }
    }
    
    handleTranscriptionMessage(data) {
        console.log('📨 Enhanced WebSocket message:', data);
        
        switch (data.type) {
            case 'connected':
                console.log('🔗 Enhanced WebSocket Server handshake complete:', data.message);
                break;
                
            case 'session_joined':
                console.log('📝 Session joined successfully:', data.session_id);
                if (window.toastSystem) {
                    window.toastSystem.showSuccess(`Session ${data.session_id} ready for transcription`);
                }
                break;
                
            case 'transcription_result':
                this.handleTranscriptionResult(data);
                break;
                
            case 'error':
                console.error('❌ Enhanced WebSocket Server error:', data.message);
                if (window.toastSystem) {
                    window.toastSystem.showError(`Server Error: ${data.message}`);
                }
                break;
                
            default:
                console.log('📨 Unknown message type:', data.type);
        }
    }
    
    handleTranscriptionResult(data) {
        const timestamp = new Date().toLocaleTimeString();
        const confidence = Math.round(data.confidence * 100);
        const latency = Date.now() - (data.timestamp || Date.now());
        
        // INDUSTRY STANDARD: Update performance metrics
        if (window.performanceMonitor && window.performanceMonitor.isActive) {
            window.performanceMonitor.segmentCount++;
            window.performanceMonitor.latencies.push(latency);
            window.performanceMonitor.confidenceScores.push(confidence / 100);
            
            if (data.text) {
                const wordCount = data.text.split(' ').filter(word => word.length > 0).length;
                window.performanceMonitor.wordCount += wordCount;
            }
        }
        
        // Handle different types of responses
        if (data.processing) {
            // Show processing feedback immediately
            this.displayProcessingFeedback(data.text);
        } else if (data.text && data.text.trim() && data.text !== "[No speech detected]") {
            // CRITICAL: Build cumulative transcript for progressive display
            this.buildCumulativeTranscript({
                text: data.text,
                confidence: confidence,
                is_final: data.is_final,
                timestamp: timestamp,
                latency: latency
            });
        }
        
        console.log(`📝 Transcription: "${data.text}" (${confidence}% confidence, ${latency}ms latency)`);
    }
    
    buildCumulativeTranscript(result) {
        // Initialize cumulative transcript if not exists
        if (!this.cumulativeTranscript) {
            this.cumulativeTranscript = '';
        }
        
        // Add interim results to build progressive transcript
        if (!result.is_final) {
            // For interim results, append to cumulative transcript
            const newText = result.text.trim();
            if (newText && !this.cumulativeTranscript.includes(newText)) {
                this.cumulativeTranscript += (this.cumulativeTranscript ? ' ' : '') + newText;
                console.log(`📝 INTERIM: "${this.cumulativeTranscript}"`);
            }
        } else {
            // For final results, ensure it's included in cumulative
            const finalText = result.text.trim();
            if (finalText && !this.cumulativeTranscript.includes(finalText)) {
                this.cumulativeTranscript += (this.cumulativeTranscript ? ' ' : '') + finalText;
                console.log(`📝 FINAL: "${this.cumulativeTranscript}"`);
            }
        }
        
        // Update UI with progressive transcript
        this.displayProgressiveTranscript({
            text: this.cumulativeTranscript,
            confidence: result.confidence,
            is_final: result.is_final,
            timestamp: result.timestamp,
            latency: result.latency
        });
    }
    
    displayProgressiveTranscript(result) {
        // ENHANCED: Find transcript container with multiple fallbacks
        const transcriptContainer = document.querySelector('.live-transcript-container') ||
                                  document.getElementById('transcript') || 
                                  document.getElementById('transcriptContent') ||
                                  document.querySelector('.transcript-content') ||
                                  document.querySelector('.transcription-container');
                                  
        if (transcriptContainer) {
            // Remove placeholder if exists
            const placeholder = transcriptContainer.querySelector('.text-muted');
            if (placeholder && placeholder.textContent.includes('Ready to record')) {
                placeholder.remove();
            }
            
            // ENHANCED: Clean scrollable interface with full complete text
            transcriptContainer.innerHTML = '';
            
            // Create enhanced main transcript element
            const mainTranscriptElement = document.createElement('div');
            mainTranscriptElement.className = 'enhanced-transcript-display';
            mainTranscriptElement.innerHTML = `
                <div class="transcript-header d-flex justify-content-between align-items-center mb-3">
                    <h6 class="text-light mb-0 d-flex align-items-center">
                        <span class="status-indicator ${result.is_final ? 'text-success' : 'text-warning'}">
                            ${result.is_final ? '✅' : '🎤'}
                        </span>
                        <span class="ms-2">Live Transcription</span>
                    </h6>
                    <div class="transcript-stats d-flex flex-column text-end">
                        <small class="text-muted">Chunk: ${this.chunkCount}</small>
                        <small class="text-muted">Words: ${result.text.split(' ').length}</small>
                        <small class="text-muted">Total: ${this.cumulativeTranscript.split(' ').length} words</small>
                    </div>
                </div>
                
                <div class="clean-scrollable-transcript-container p-4 bg-dark border rounded" 
                     style="max-height: 400px; overflow-y: auto; scroll-behavior: smooth;">
                    
                    <div class="complete-transcribed-text">
                        <div class="full-transcript-text ${result.is_final ? 'text-success fw-bold' : 'text-light'}" 
                             style="line-height: 1.6; font-size: 1.1rem; white-space: pre-wrap;">
                            ${this.cumulativeTranscript || result.text}
                        </div>
                        
                        ${!result.is_final ? `
                        <div class="current-processing mt-3 p-2 bg-warning bg-opacity-10 border-start border-warning">
                            <small class="text-warning d-flex align-items-center">
                                <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                                Processing: "${result.text}"
                            </small>
                        </div>
                        ` : ''}
                    </div>
                    
                    <div class="transcript-metadata mt-3 pt-3 border-top border-secondary">
                        <div class="row g-2">
                            <div class="col-md-6">
                                <small class="text-muted d-block">
                                    <strong>Timestamp:</strong> ${result.timestamp || new Date().toLocaleTimeString()}
                                </small>
                                <small class="text-muted d-block">
                                    <strong>Confidence:</strong> <span class="text-${result.confidence > 80 ? 'success' : result.confidence > 60 ? 'warning' : 'danger'}">${result.confidence}%</span>
                                </small>
                            </div>
                            <div class="col-md-6">
                                <small class="text-muted d-block">
                                    <strong>Latency:</strong> ${result.latency ? `${result.latency}ms` : 'N/A'}
                                </small>
                                <small class="text-muted d-block">
                                    <strong>Status:</strong> <span class="text-${result.is_final ? 'success' : 'warning'}">${result.is_final ? 'FINAL' : 'INTERIM'}</span>
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            transcriptContainer.appendChild(mainTranscriptElement);
            
            // ENHANCED: Smooth scrolling to bottom with animation
            const scrollContainer = mainTranscriptElement.querySelector('.clean-scrollable-transcript-container');
            if (scrollContainer) {
                scrollContainer.scrollTop = scrollContainer.scrollHeight;
            }
            transcriptContainer.scrollTop = transcriptContainer.scrollHeight;
            
            // Store for final transcript generation
            this.transcriptionBuffer.push(result);
            
            // ENHANCED: Update real performance metrics
            this.updateRealTimeMetrics(result);
            
            // Trigger segment update event
            window.dispatchEvent(new CustomEvent('transcriptionSegment', {
                detail: result
            }));
        }
    }
    
    updateRealTimeMetrics(result) {
        // CRITICAL FIX: Connect to actual backend performance data
        try {
            // Update latency metrics with real data
            const latencyElement = document.querySelector('#latencyMs') || 
                                 document.querySelector('.latency-value') ||
                                 document.querySelector('[data-metric="latency"]');
            if (latencyElement && result.latency) {
                latencyElement.textContent = `${result.latency}ms`;
                latencyElement.className = `metric-value ${result.latency < 500 ? 'text-success' : result.latency < 1000 ? 'text-warning' : 'text-danger'}`;
            }
            
            // Update quality score with real confidence data
            const qualityElement = document.querySelector('#qualityScore') || 
                                 document.querySelector('.quality-value') ||
                                 document.querySelector('[data-metric="quality"]');
            if (qualityElement) {
                qualityElement.textContent = `${result.confidence}%`;
                qualityElement.className = `metric-value ${result.confidence > 80 ? 'text-success' : result.confidence > 60 ? 'text-warning' : 'text-danger'}`;
            }
            
            // Update chunk processing success rate
            const successRateElement = document.querySelector('#successRate') ||
                                     document.querySelector('.success-rate-value') ||
                                     document.querySelector('[data-metric="success-rate"]');
            if (successRateElement) {
                const successRate = Math.round((this.chunkCount > 0 ? (this.transcriptionBuffer.length / this.chunkCount) * 100 : 100));
                successRateElement.textContent = `${successRate}%`;
                successRateElement.className = `metric-value ${successRate > 90 ? 'text-success' : successRate > 70 ? 'text-warning' : 'text-danger'}`;
            }
            
            // Update performance monitor if available
            if (window.performanceMonitor) {
                window.performanceMonitor.updateMetrics({
                    latency: result.latency,
                    confidence: result.confidence,
                    wordCount: result.text.split(' ').filter(w => w.length > 0).length,
                    chunkNumber: this.chunkCount,
                    successRate: Math.round((this.chunkCount > 0 ? (this.transcriptionBuffer.length / this.chunkCount) * 100 : 100))
                });
            }
            
        } catch (error) {
            console.warn('⚠️ Failed to update real-time metrics:', error);
        }
    }
    
    showChunkProcessingFeedback(chunkNumber, chunkSize) {
        // Show processing feedback for each chunk
        const statusElement = document.querySelector('#connectionStatus') || 
                             document.querySelector('.connection-status') ||
                             document.querySelector('#wsStatus');
                             
        if (statusElement) {
            statusElement.innerHTML = `
                <span class="text-warning">
                    🎵 Processing chunk ${chunkNumber} (${chunkSize} bytes)...
                </span>
            `;
            
            // Clear after 2 seconds
            setTimeout(() => {
                if (statusElement) {
                    statusElement.innerHTML = '<span class="text-success">🔗 Connected & Recording</span>';
                }
            }, 2000);
        }
    }
    
    displayProcessingFeedback(text) {
        // Add processing feedback to main transcript
        const transcriptContainer = document.getElementById('transcript') || 
                                  document.getElementById('transcriptContent') ||
                                  document.querySelector('.transcript-content');
                                  
        if (transcriptContainer) {
            const processingElement = document.createElement('div');
            processingElement.className = 'transcript-segment processing';
            processingElement.innerHTML = `
                <span class="timestamp">[${new Date().toLocaleTimeString()}]</span>
                <span class="processing-text">${text}</span>
            `;
            
            transcriptContainer.appendChild(processingElement);
            transcriptContainer.scrollTop = transcriptContainer.scrollHeight;
            
            // Remove processing feedback after a short delay
            setTimeout(() => {
                if (processingElement.parentNode) {
                    processingElement.remove();
                }
            }, 2000);
        }
    }
    
    displayTranscriptionResult(result) {
        // INDUSTRY STANDARD: Separate interim and final transcript handling
        if (result.is_final) {
            // Store final transcripts for GPT-4 refinement
            if (window.finalTranscripts) {
                window.finalTranscripts.push({
                    text: result.text,
                    confidence: result.confidence,
                    timestamp: result.timestamp
                });
                console.log(`📄 Final transcript segment stored: "${result.text}"`);
            }
        } else {
            // Store interim transcripts for real-time display
            if (window.interimTranscripts) {
                window.interimTranscripts.push({
                    text: result.text,
                    confidence: result.confidence,
                    timestamp: result.timestamp
                });
            }
        }
        
        // Display transcription in UI
        const transcriptContainer = document.querySelector('.live-transcript-container') ||
                                  document.getElementById('transcript') || 
                                  document.getElementById('transcriptContent') ||
                                  document.querySelector('.transcript-content');
                                  
        if (transcriptContainer) {
            // Remove "Ready to record" placeholder if it exists
            const placeholder = transcriptContainer.querySelector('.text-muted');
            if (placeholder && placeholder.textContent.includes('Ready to record')) {
                placeholder.remove();
            }
            
            const segmentElement = document.createElement('div');
            segmentElement.className = `transcript-segment ${result.is_final ? 'final' : 'interim'} mb-2 fade-in`;
            segmentElement.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="transcript-text">
                        <small class="text-muted">[${result.timestamp}]</small>
                        <span class="ms-2 ${result.is_final ? 'text-light fw-bold' : 'text-warning'}">${result.text}</span>
                    </div>
                    <small class="text-muted">${result.confidence}%</small>
                </div>
            `;
            
            transcriptContainer.appendChild(segmentElement);
            transcriptContainer.scrollTop = transcriptContainer.scrollHeight;
            
            // Update word count in the stats
            const wordCountElement = document.querySelector('.metric-value');
            if (wordCountElement && wordCountElement.textContent === '0') {
                const words = result.text.split(' ').filter(word => word.length > 0).length;
                wordCountElement.textContent = words;
            }
        }
        
        // Add to transcription buffer
        this.transcriptionBuffer.push(result);
        
        // Trigger segment update event for other components
        window.dispatchEvent(new CustomEvent('transcriptionSegment', {
            detail: result
        }));
    }
    
    // MANUAL MONITORING RECOMMENDATION #5: Enhanced connection error handling
    handleConnectionError(error) {
        console.error('❌ Connection error:', error);
        
        // Update UI immediately
        if (window.professionalRecorder) {
            window.professionalRecorder.updateConnectionStatus('error');
        }
        
        if (this.connectionAttempts < this.maxConnectionAttempts) {
            this.connectionAttempts++;
            const delay = Math.pow(2, this.connectionAttempts) * 1000; // Exponential backoff
            console.log(`🔄 Retrying connection (attempt ${this.connectionAttempts}/${this.maxConnectionAttempts}) in ${delay}ms`);
            
            // Show retry notification
            if (window.toastSystem) {
                window.toastSystem.showWarning(`🔄 Retrying connection... (${this.connectionAttempts}/${this.maxConnectionAttempts})`);
            }
            
            setTimeout(() => this.initializeConnection(), delay);
        } else {
            console.error('❌ Max connection attempts reached - connection failed permanently');
            
            // Show failure notification
            if (window.toastSystem) {
                window.toastSystem.showError('❌ Connection failed after multiple attempts');
            }
            
            // Update UI to show connection failure
            if (window.professionalRecorder) {
                window.professionalRecorder.updateConnectionStatus('failed');
            }
        }
        
        // Also use enhanced error handler if available
        if (window.enhancedErrorHandler) {
            window.enhancedErrorHandler.handleError(error, 'Socket.IO', () => {
                this.attemptReconnection();
            });
        }
    }
    
    handleReconnection() {
        if (this.connectionAttempts < this.maxConnectionAttempts) {
            this.connectionAttempts++;
            console.log(`🔄 Attempting reconnection (${this.connectionAttempts}/${this.maxConnectionAttempts})`);
            
            setTimeout(() => {
                this.initializeConnection().catch(error => {
                    console.error('Reconnection failed:', error);
                });
            }, 2000 * this.connectionAttempts);
        } else {
            console.error('❌ Max reconnection attempts reached');
        }
    }
    
    stopTranscription() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
        }
        
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
        
        console.log('⏹️ Transcription stopped');
    }
    
    disconnect() {
        this.stopTranscription();
        
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        
        this.isConnected = false;
        console.log('🔌 Disconnected from real-time transcription');
    }
}

// Initialize global instance and professional recorder replacement
window.realWhisperIntegration = new RealWhisperIntegration();

// Professional Recorder replacement for compatibility
class ProfessionalRecorder {
    constructor() {
        this.isRecording = false;
        this.sessionId = null;
        console.log('✅ Professional Recorder initialized with Real Whisper integration');
    }
    
    async startRecording() {
        try {
            this.sessionId = `live_${Date.now()}`;
            await window.realWhisperIntegration.startTranscription(this.sessionId);
            this.isRecording = true;
            console.log('✅ Recording started with Real Whisper API');
            return { success: true, sessionId: this.sessionId };
        } catch (error) {
            console.error('❌ Failed to start recording:', error);
            return { success: false, error: error.message };
        }
    }
    
    stopRecording() {
        window.realWhisperIntegration.stopTranscription();
        this.isRecording = false;
        console.log('⏹️ Recording stopped');
        return { success: true };
    }
    
    updateConnectionStatus(status) {
        const wsStatus = document.querySelector('#wsStatus');
        if (wsStatus) {
            wsStatus.textContent = status === 'connected' ? 'Connected' : 'Disconnected';
            wsStatus.className = `status-indicator ${status}`;
        }
    }
    
    updateTranscriptionStats(stats) {
        // Update UI with transcription statistics
        console.log('📊 Transcription stats:', stats);
    }
}

// Initialize professional recorder replacement
window.professionalRecorder = new ProfessionalRecorder();

// Add CSS for processing feedback
const style = document.createElement('style');
style.textContent = `
    .transcript-segment.processing .processing-text {
        color: #ffc107;
        font-style: italic;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .transcript-segment.final .text {
        color: #28a745;
        font-weight: bold;
    }
    
    .transcript-segment.interim .text {
        color: #17a2b8;
        font-style: italic;
    }
    
    .transcript-segment .confidence {
        font-size: 0.8em;
        color: #6c757d;
        margin-left: 0.5em;
    }
`;
document.head.appendChild(style);

// Initialize Real Whisper Integration globally
window.realWhisperIntegration = new RealWhisperIntegration();

// CRITICAL FIX: Button Event Binding for Real Whisper Integration
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 CRITICAL FIX: Binding Real Whisper Integration to UI buttons');
    
    // Find the recording buttons
    const startBtn = document.getElementById('startRecordingBtn') || 
                    document.querySelector('.start-recording-btn') ||
                    document.querySelector('[data-action="start"]');
                    
    const stopBtn = document.getElementById('stopRecordingBtn') || 
                   document.querySelector('.stop-recording-btn') ||
                   document.querySelector('[data-action="stop"]');
    
    if (!startBtn || !stopBtn) {
        console.error('❌ CRITICAL: Recording buttons not found in DOM');
        return;
    }
    
    console.log('✅ Found recording buttons:', startBtn, stopBtn);
    
    // EXCLUSIVE Real Whisper Integration button handlers
    startBtn.addEventListener('click', async function(event) {
        event.preventDefault();
        event.stopImmediatePropagation();
        
        console.log('🎯 EXCLUSIVE Real Whisper Integration handling start button');
        
        try {
            // Disable button to prevent double-clicks
            startBtn.disabled = true;
            startBtn.textContent = 'Connecting...';
            
            // Update UI immediately
            if (window.toastSystem) {
                window.toastSystem.showInfo('🔗 Connecting to real-time transcription...');
            }
            
            // Generate session ID
            const sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(7)}`;
            
            // Start Real Whisper Integration transcription
            await window.realWhisperIntegration.startTranscription(sessionId);
            
            // Update button states
            startBtn.style.display = 'none';
            stopBtn.style.display = 'inline-block';
            stopBtn.disabled = false;
            
            // Start performance monitoring
            if (window.performanceMonitor) {
                window.performanceMonitor.startMonitoring();
            }
            
            console.log('✅ Real Whisper Integration started successfully');
            
            if (window.toastSystem) {
                window.toastSystem.showSuccess('🎤 Live transcription started!');
            }
            
        } catch (error) {
            console.error('❌ Real Whisper Integration start failed:', error);
            
            // Reset button state on error
            startBtn.disabled = false;
            startBtn.textContent = 'Start Recording';
            
            if (window.toastSystem) {
                window.toastSystem.showError(`❌ Failed to start: ${error.message}`);
            }
        }
    });
    
    stopBtn.addEventListener('click', async function(event) {
        event.preventDefault();
        event.stopImmediatePropagation();
        
        console.log('🎯 EXCLUSIVE Real Whisper Integration handling stop button');
        
        try {
            // Disable button
            stopBtn.disabled = true;
            stopBtn.textContent = 'Stopping...';
            
            // Update UI
            if (window.toastSystem) {
                window.toastSystem.showInfo('🛑 Stopping transcription...');
            }
            
            // Stop Real Whisper Integration
            await window.realWhisperIntegration.stopTranscription();
            
            // Update button states
            stopBtn.style.display = 'none';
            startBtn.style.display = 'inline-block';
            startBtn.disabled = false;
            startBtn.textContent = 'Start Recording';
            
            // Stop performance monitoring
            if (window.performanceMonitor) {
                window.performanceMonitor.stopMonitoring();
            }
            
            console.log('✅ Real Whisper Integration stopped successfully');
            
            if (window.toastSystem) {
                window.toastSystem.showSuccess('✅ Recording stopped - processing final transcript...');
            }
            
            // TODO: Generate final transcript here
            
        } catch (error) {
            console.error('❌ Real Whisper Integration stop failed:', error);
            
            // Reset button state on error
            stopBtn.disabled = false;
            stopBtn.textContent = 'Stop Recording';
            
            if (window.toastSystem) {
                window.toastSystem.showError(`❌ Failed to stop: ${error.message}`);
            }
        }
    });
    
    console.log('🎯 CRITICAL FIX COMPLETE: Real Whisper Integration bound to buttons');
});

console.log('Real Whisper Integration loaded successfully');