/**
 * 🔗 STREAMING INTEGRATION
 * Integration layer between the streaming audio client and existing UI
 */

class StreamingIntegration {
    constructor() {
        this.streamingClient = null;
        this.isInitialized = false;
        this.currentTranscript = '';
        this.sessionMetrics = {};
        
        console.log('🔗 StreamingIntegration initialized');
    }
    
    async initialize() {
        if (this.isInitialized) return;
        
        try {
            // Initialize streaming client
            this.streamingClient = new window.StreamingAudioClient({
                sampleRate: 16000,
                channels: 1,
                chunkDurationMs: 300,
                overlapMs: 50,
                vadThreshold: 0.01,
                maxRetries: 3
            });
            
            this.isInitialized = true;
            console.log('✅ Streaming integration initialized');
            
        } catch (error) {
            console.error('❌ Failed to initialize streaming integration:', error);
            throw error;
        }
    }
    
    async startTranscription() {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }
            
            // Clear previous transcript
            this.currentTranscript = '';
            this.updateTranscriptDisplay('');
            
            // Update UI state
            this.updateUIState('starting');
            
            // Start streaming transcription
            await this.streamingClient.startRecording(
                (result) => this.handleTranscriptionResult(result),
                (error) => this.handleTranscriptionError(error),
                (status) => this.handleStatusChange(status)
            );
            
            // Start polling for results
            this.streamingClient.pollForResults();
            
            console.log('✅ Streaming transcription started');
            
        } catch (error) {
            console.error('❌ Failed to start streaming transcription:', error);
            this.handleTranscriptionError(error);
        }
    }
    
    async stopTranscription() {
        try {
            if (!this.streamingClient) return;
            
            const analytics = await this.streamingClient.stopRecording();
            this.sessionMetrics = { ...analytics, ...this.streamingClient.getMetrics() };
            
            this.updateUIState('stopped');
            
            console.log('✅ Streaming transcription stopped');
            console.log('📊 Session metrics:', this.sessionMetrics);
            
            return this.sessionMetrics;
            
        } catch (error) {
            console.error('❌ Failed to stop streaming transcription:', error);
            throw error;
        }
    }
    
    handleTranscriptionResult(result) {
        try {
            // Update transcript display
            if (result.text) {
                if (result.isFinal) {
                    // Add final text to transcript
                    this.currentTranscript += result.text + ' ';
                    this.updateTranscriptDisplay(this.currentTranscript);
                    
                    // Update word count
                    this.updateWordCount(this.currentTranscript.split(' ').length);
                    
                } else {
                    // Show interim text without adding to final transcript
                    this.updateTranscriptDisplay(this.currentTranscript + result.text);
                }
                
                // Update confidence display
                if (result.confidence !== undefined) {
                    this.updateConfidenceDisplay(result.confidence);
                }
                
                console.log('📝 Transcription result:', {
                    text: result.text.substring(0, 50) + '...',
                    confidence: result.confidence,
                    isFinal: result.isFinal
                });
            }
            
        } catch (error) {
            console.error('❌ Error handling transcription result:', error);
        }
    }
    
    handleTranscriptionError(error) {
        console.error('❌ Transcription error:', error);
        
        // Update UI to show error state
        this.updateUIState('error');
        
        // Show user-friendly error message
        this.showErrorMessage('Transcription error occurred. Please try again.');
        
        // Try to recover or stop
        if (this.streamingClient) {
            this.streamingClient.stopRecording().catch(console.error);
        }
    }
    
    handleStatusChange(status) {
        console.log('📊 Status change:', status);
        this.updateUIState(status);
        
        switch (status) {
            case 'recording':
                this.showSuccessMessage('Recording started successfully');
                break;
            case 'stopped':
                this.showInfoMessage('Recording stopped');
                break;
        }
    }
    
    updateTranscriptDisplay(text) {
        const transcriptDisplay = document.getElementById('transcriptDisplay') ||
                                document.querySelector('.live-transcript-container');
        
        if (transcriptDisplay) {
            if (text.trim()) {
                transcriptDisplay.innerHTML = `
                    <div class="transcript-text">
                        <p class="mb-2">${this.escapeHtml(text)}</p>
                    </div>
                `;
            } else {
                transcriptDisplay.innerHTML = `
                    <div class="text-muted text-center">
                        <i class="bi bi-mic"></i>
                        <p>Listening for speech...</p>
                    </div>
                `;
            }
        }
    }
    
    updateWordCount(count) {
        const wordCounter = document.getElementById('wordCounter');
        if (wordCounter) {
            wordCounter.textContent = count.toString();
        }
    }
    
    updateConfidenceDisplay(confidence) {
        const confidenceElement = document.getElementById('confidenceLevel');
        if (confidenceElement) {
            const percentage = Math.round(confidence * 100);
            confidenceElement.textContent = `${percentage}%`;
            
            // Update confidence color based on level
            confidenceElement.className = 'badge ' + this.getConfidenceClass(confidence);
        }
    }
    
    getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'bg-success';
        if (confidence >= 0.6) return 'bg-warning';
        return 'bg-danger';
    }
    
    updateUIState(state) {
        const body = document.body;
        const startButton = document.getElementById('startButton');
        const stopButton = document.getElementById('stopButton');
        
        // Remove all existing UI state classes
        body.classList.remove('ui-state-idle', 'ui-state-recording', 'ui-state-processing', 'ui-state-error');
        
        switch (state) {
            case 'starting':
            case 'recording':
                body.classList.add('ui-state-recording');
                if (startButton) startButton.disabled = true;
                if (stopButton) stopButton.disabled = false;
                break;
                
            case 'stopped':
            case 'idle':
                body.classList.add('ui-state-idle');
                if (startButton) startButton.disabled = false;
                if (stopButton) stopButton.disabled = true;
                break;
                
            case 'error':
                body.classList.add('ui-state-error');
                if (startButton) startButton.disabled = false;
                if (stopButton) stopButton.disabled = true;
                break;
        }
    }
    
    showSuccessMessage(message) {
        this.showNotification(message, 'success');
    }
    
    showInfoMessage(message) {
        this.showNotification(message, 'info');
    }
    
    showErrorMessage(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type = 'info') {
        // Create notification element if it doesn't exist
        let notificationContainer = document.getElementById('notification-container');
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.id = 'notification-container';
            notificationContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(notificationContainer);
        }
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${this.getBootstrapAlertClass(type)} alert-dismissible fade show`;
        notification.innerHTML = `
            <strong>${this.getNotificationTitle(type)}</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        notificationContainer.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    getBootstrapAlertClass(type) {
        const mapping = {
            'success': 'success',
            'info': 'info',
            'warning': 'warning',
            'error': 'danger'
        };
        return mapping[type] || 'info';
    }
    
    getNotificationTitle(type) {
        const mapping = {
            'success': 'Success!',
            'info': 'Info:',
            'warning': 'Warning:',
            'error': 'Error!'
        };
        return mapping[type] || 'Info:';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getMetrics() {
        return {
            ...this.sessionMetrics,
            streamingClient: this.streamingClient?.getMetrics(),
            currentTranscriptLength: this.currentTranscript.length,
            isRecording: this.streamingClient?.isRecording || false
        };
    }
}

// Initialize global streaming integration
window.streamingIntegration = new StreamingIntegration();

// Update existing button handlers to use streaming integration
document.addEventListener('DOMContentLoaded', function() {
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    
    if (startButton) {
        startButton.addEventListener('click', async () => {
            try {
                await window.streamingIntegration.startTranscription();
            } catch (error) {
                console.error('❌ Failed to start transcription:', error);
            }
        });
    }
    
    if (stopButton) {
        stopButton.addEventListener('click', async () => {
            try {
                await window.streamingIntegration.stopTranscription();
            } catch (error) {
                console.error('❌ Failed to stop transcription:', error);
            }
        });
    }
    
    console.log('✅ Streaming integration UI handlers attached');
});

console.log('🔗 Streaming integration module loaded');