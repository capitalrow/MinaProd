/**
 * 🎯 INTERIM TRANSCRIPTION: Real-time transcription results during recording
 * Provides immediate feedback and progressive transcript building
 */

class InterimTranscriptionManager {
    constructor() {
        this.interimText = '';
        this.finalText = '';
        this.currentChunk = 0;
        this.isProcessing = false;
        this.lastUpdateTime = 0;
        this.transcriptDisplay = null;
        
        this.initializeDisplay();
        console.log('✅ Interim Transcription Manager initialized');
    }
    
    initializeDisplay() {
        // Find or create transcript display area
        this.transcriptDisplay = document.getElementById('transcript-display');
        if (!this.transcriptDisplay) {
            // Create transcript display if it doesn't exist
            const container = document.querySelector('.live-transcript-container') || document.body;
            this.transcriptDisplay = document.createElement('div');
            this.transcriptDisplay.id = 'transcript-display';
            this.transcriptDisplay.className = 'transcript-display';
            this.transcriptDisplay.innerHTML = `
                <div class="transcript-header">
                    <h3>Live Transcript</h3>
                    <div class="transcript-status">Ready</div>
                </div>
                <div class="transcript-content">
                    <div class="final-transcript" id="final-transcript"></div>
                    <div class="interim-transcript" id="interim-transcript"></div>
                </div>
            `;
            container.appendChild(this.transcriptDisplay);
        }
    }
    
    /**
     * Process interim transcription chunk
     */
    async processInterimChunk(audioBlob, chunkNumber) {
        if (this.isProcessing) {
            console.log(`⏳ Still processing chunk ${this.currentChunk}, queuing chunk ${chunkNumber}`);
            return;
        }
        
        this.isProcessing = true;
        this.currentChunk = chunkNumber;
        this.updateStatus('processing');
        
        try {
            console.log(`🎙️ Processing interim chunk ${chunkNumber}: ${audioBlob.size} bytes`);
            
            const formData = new FormData();
            formData.append('audio', audioBlob, `interim_${chunkNumber}.webm`);
            formData.append('session_id', window.currentSessionId || `session_${Date.now()}`);
            formData.append('chunk_id', chunkNumber.toString());
            formData.append('is_interim', 'true');
            
            const response = await fetch('/api/transcribe-audio', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                
                if (result.success && result.transcript) {
                    this.addInterimText(result.transcript, chunkNumber);
                    this.updateMetrics({
                        latency: Math.round(result.processing_time) + 'ms',
                        confidence: Math.round(result.confidence * 100) + '%',
                        words: result.word_count || result.transcript.split(' ').length
                    });
                } else {
                    console.log(`ℹ️ Interim chunk ${chunkNumber}: No speech detected`);
                }
            } else {
                console.warn(`⚠️ Interim chunk ${chunkNumber} failed: ${response.status}`);
            }
            
        } catch (error) {
            console.error(`❌ Interim processing error for chunk ${chunkNumber}:`, error);
            this.showError('Interim processing error', error.message);
        } finally {
            this.isProcessing = false;
            this.updateStatus('ready');
        }
    }
    
    /**
     * Add interim text to display
     */
    addInterimText(text, chunkNumber) {
        if (!text || !text.trim()) return;
        
        const cleanText = text.trim();
        const timestamp = new Date().toLocaleTimeString();
        
        // Update interim display
        const interimDiv = document.getElementById('interim-transcript');
        if (interimDiv) {
            interimDiv.innerHTML = `
                <div class="interim-chunk" data-chunk="${chunkNumber}">
                    <span class="interim-text">${cleanText}</span>
                    <small class="interim-timestamp">${timestamp}</small>
                </div>
            `;
            
            // Add fade-in animation
            interimDiv.style.opacity = '0';
            setTimeout(() => {
                interimDiv.style.transition = 'opacity 0.3s ease';
                interimDiv.style.opacity = '1';
            }, 10);
        }
        
        // Update cumulative transcript
        this.interimText += cleanText + ' ';
        
        // Update word count in real-time
        this.updateLiveStats();
        
        console.log(`✅ Interim text added (chunk ${chunkNumber}): "${cleanText}"`);
    }
    
    /**
     * Finalize current interim text
     */
    finalizeText() {
        if (this.interimText.trim()) {
            this.finalText += this.interimText;
            
            // Move interim to final display
            const finalDiv = document.getElementById('final-transcript');
            if (finalDiv) {
                const finalParagraph = document.createElement('p');
                finalParagraph.className = 'final-paragraph';
                finalParagraph.textContent = this.interimText.trim();
                finalDiv.appendChild(finalParagraph);
                
                // Highlight the final text briefly
                finalParagraph.style.backgroundColor = '#4CAF50';
                finalParagraph.style.color = '#ffffff';
                setTimeout(() => {
                    finalParagraph.style.backgroundColor = '';
                    finalParagraph.style.color = '';
                }, 2000);
            }
            
            // Clear interim
            this.interimText = '';
            const interimDiv = document.getElementById('interim-transcript');
            if (interimDiv) {
                interimDiv.innerHTML = '<div class="interim-placeholder">Listening...</div>';
            }
            
            console.log(`✅ Text finalized: ${this.finalText.length} characters total`);
        }
    }
    
    /**
     * Update transcription status
     */
    updateStatus(status) {
        const statusDiv = document.querySelector('.transcript-status');
        if (statusDiv) {
            const statusMap = {
                'ready': { text: 'Ready', class: 'status-ready' },
                'processing': { text: 'Processing...', class: 'status-processing' },
                'error': { text: 'Error', class: 'status-error' }
            };
            
            const statusInfo = statusMap[status] || statusMap['ready'];
            statusDiv.textContent = statusInfo.text;
            statusDiv.className = `transcript-status ${statusInfo.class}`;
        }
        
        this.lastUpdateTime = Date.now();
    }
    
    /**
     * Update live statistics during recording
     */
    updateLiveStats() {
        const totalWords = (this.finalText + ' ' + this.interimText).split(' ').filter(w => w.length > 0).length;
        const recordingTime = (Date.now() - (window.recordingStartTime || Date.now())) / 1000;
        
        // Update stats cards if they exist
        const updateStatCard = (id, value) => {
            const element = document.querySelector(`[data-stat="${id}"] .stat-value`);
            if (element) element.textContent = value;
        };
        
        updateStatCard('words', totalWords);
        updateStatCard('duration', this.formatTime(recordingTime));
        
        // Update WPM if recording for more than 10 seconds
        if (recordingTime > 10) {
            const wpm = Math.round((totalWords / recordingTime) * 60);
            updateStatCard('wpm', wpm);
        }
    }
    
    /**
     * Update performance metrics
     */
    updateMetrics(metrics) {
        const updateStatCard = (id, value) => {
            const element = document.querySelector(`[data-stat="${id}"] .stat-value`);
            if (element) element.textContent = value;
        };
        
        if (metrics.latency) updateStatCard('latency', metrics.latency);
        if (metrics.confidence) updateStatCard('accuracy', metrics.confidence);
        if (metrics.words) updateStatCard('chunks', this.currentChunk);
    }
    
    /**
     * Show error message
     */
    showError(title, message) {
        this.updateStatus('error');
        
        if (window.toastSystem) {
            window.toastSystem.error(`${title}: ${message}`);
        } else {
            console.error(`${title}: ${message}`);
        }
    }
    
    /**
     * Format time as MM:SS
     */
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    
    /**
     * Clear all transcription data
     */
    clear() {
        this.interimText = '';
        this.finalText = '';
        this.currentChunk = 0;
        
        const finalDiv = document.getElementById('final-transcript');
        if (finalDiv) finalDiv.innerHTML = '';
        
        const interimDiv = document.getElementById('interim-transcript');
        if (interimDiv) interimDiv.innerHTML = '<div class="interim-placeholder">Ready to transcribe...</div>';
        
        this.updateStatus('ready');
        console.log('🧹 Interim transcription cleared');
    }
    
    /**
     * Get complete transcript
     */
    getCompleteTranscript() {
        return (this.finalText + ' ' + this.interimText).trim();
    }
}

// Initialize global interim transcription manager
window.interimTranscription = new InterimTranscriptionManager();

console.log('✅ Interim transcription system loaded');

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
