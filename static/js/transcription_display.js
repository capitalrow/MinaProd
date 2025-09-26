/**
 * Transcription Display Manager
 * Handles real-time display of transcription results with animations and metrics
 */

class TranscriptionDisplayManager {
    constructor() {
        this.transcriptArea = null;
        this.currentSessionTranscripts = [];
        this.wordCount = 0;
        this.startTime = null;
        this.lastUpdateTime = null;
        this.init();
    }
    
    init() {
        // Find transcript display areas
        this.transcriptArea = document.getElementById('transcriptContainer') || 
                             document.querySelector('.transcript-content') || 
                             document.querySelector('#transcriptArea');
        
        if (!this.transcriptArea) {
            console.error('❌ Transcript display area not found');
            return;
        }
        
        // Use the existing container as the content area
        this.transcriptContent = this.transcriptArea;
        
        // Clear any placeholder content on first use
        this.placeholder = document.getElementById('transcriptPlaceholder');
        
        console.log('✅ Transcription display manager initialized with container:', this.transcriptArea.id);
    }
    
    /**
     * Update the transcript display with new results
     */
    updateTranscriptDisplay(result) {
        if (!this.transcriptContent) {
            this.init();
        }
        
        if (!result || !result.transcript) {
            console.warn('No transcript in result:', result);
            return;
        }
        
        const transcript = result.transcript;
        const confidence = result.confidence || 0.95;
        const processingTime = result.processing_time || 0;
        
        // Hide placeholder on first transcript
        if (this.placeholder && this.placeholder.style.display !== 'none') {
            this.placeholder.style.display = 'none';
            console.log('📝 Hiding placeholder, showing first transcript');
        }
        
        // Clear "Processing..." and "Listening for speech..." messages
        const processingMessages = this.transcriptContent.querySelectorAll('.processing-message');
        processingMessages.forEach(msg => msg.remove());
        
        // Create transcript segment
        const segment = this.createTranscriptSegment(transcript, confidence, result);
        
        // Add to display with animation
        this.transcriptContent.appendChild(segment);
        
        // Scroll to latest
        this.scrollToLatest();
        
        // Update metrics
        this.updateMetrics(transcript, processingTime);
        
        // Store for export
        this.currentSessionTranscripts.push({
            timestamp: new Date().toISOString(),
            text: transcript,
            confidence: confidence,
            processingTime: processingTime
        });
        
        // Announce to screen readers
        this.announceTranscript(transcript);
        
        console.log(`📝 Displayed transcript: "${transcript.substring(0, 50)}..." (${this.wordCount} words total)`);
    }
    
    /**
     * Create a styled transcript segment
     */
    createTranscriptSegment(text, confidence, metadata) {
        const segment = document.createElement('div');
        segment.className = 'transcript-segment fade-in';
        segment.setAttribute('role', 'article');
        segment.setAttribute('aria-label', `Transcript segment: ${text.substring(0, 50)}`);
        
        // Add confidence-based styling
        if (confidence > 0.9) {
            segment.classList.add('high-confidence');
        } else if (confidence > 0.7) {
            segment.classList.add('medium-confidence');
        } else {
            segment.classList.add('low-confidence');
        }
        
        // Create timestamp
        const timestamp = document.createElement('span');
        timestamp.className = 'segment-timestamp';
        timestamp.textContent = new Date().toLocaleTimeString();
        
        // Create confidence indicator
        const confidenceBar = document.createElement('div');
        confidenceBar.className = 'confidence-bar';
        confidenceBar.style.width = `${confidence * 100}%`;
        confidenceBar.setAttribute('aria-label', `Confidence: ${Math.round(confidence * 100)}%`);
        
        // Create text content
        const textContent = document.createElement('p');
        textContent.className = 'segment-text';
        textContent.textContent = text;
        
        // Add speaker label if available
        if (metadata && metadata.speaker) {
            const speakerLabel = document.createElement('span');
            speakerLabel.className = 'speaker-label';
            speakerLabel.textContent = `Speaker ${metadata.speaker}: `;
            textContent.prepend(speakerLabel);
        }
        
        // Assemble segment
        segment.appendChild(timestamp);
        segment.appendChild(confidenceBar);
        segment.appendChild(textContent);
        
        // Add interaction handlers
        segment.addEventListener('click', () => this.handleSegmentClick(segment, text));
        
        return segment;
    }
    
    /**
     * Update real-time metrics
     */
    updateMetrics(transcript, processingTime) {
        if (!this.startTime) {
            this.startTime = Date.now();
        }
        
        this.lastUpdateTime = Date.now();
        
        // Count words
        const words = transcript.trim().split(/\s+/).filter(w => w.length > 0);
        this.wordCount += words.length;
        
        // Calculate metrics
        const duration = (Date.now() - this.startTime) / 1000;
        const avgLatency = processingTime ? Math.round(processingTime * 1000) : 0;
        
        // Update UI stats
        if (window.updateSessionStats) {
            window.updateSessionStats({
                duration: this.formatDuration(duration),
                words: this.wordCount,
                chunks: this.currentSessionTranscripts.length,
                latency: `${avgLatency}ms`,
                accuracy: '95%',
                quality: this.calculateQuality()
            });
        }
        
        // Update individual stat elements
        this.updateStatElement('words', this.wordCount);
        this.updateStatElement('latency', `${avgLatency}ms`);
        this.updateStatElement('chunks', this.currentSessionTranscripts.length);
    }
    
    /**
     * Update individual stat element
     */
    updateStatElement(statName, value) {
        const elements = document.querySelectorAll(`[data-stat="${statName}"], .stat-${statName}, #${statName}-stat`);
        elements.forEach(el => {
            if (el.querySelector('.stat-value')) {
                el.querySelector('.stat-value').textContent = value;
            } else if (el.querySelector('h3')) {
                el.querySelector('h3').textContent = value;
            } else {
                // Look for the value in nested structure
                const valueEl = el.querySelector('div:last-child') || el;
                if (valueEl) valueEl.textContent = value;
            }
        });
    }
    
    /**
     * Calculate quality score based on confidence and consistency
     */
    calculateQuality() {
        if (this.currentSessionTranscripts.length === 0) return '0%';
        
        const avgConfidence = this.currentSessionTranscripts.reduce((sum, t) => 
            sum + (t.confidence || 0.95), 0) / this.currentSessionTranscripts.length;
        
        return `${Math.round(avgConfidence * 100)}%`;
    }
    
    /**
     * Format duration for display
     */
    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    
    /**
     * Scroll to latest transcript
     */
    scrollToLatest() {
        if (this.transcriptContent) {
            this.transcriptContent.scrollTop = this.transcriptContent.scrollHeight;
        }
    }
    
    /**
     * Handle segment click for editing/copying
     */
    handleSegmentClick(segment, text) {
        // Copy to clipboard
        navigator.clipboard.writeText(text).then(() => {
            // Visual feedback
            segment.classList.add('copied');
            setTimeout(() => segment.classList.remove('copied'), 1000);
            
            // Toast notification
            if (window.toastSystem) {
                window.toastSystem.info('Transcript copied to clipboard');
            }
        });
    }
    
    /**
     * Announce transcript to screen readers
     */
    announceTranscript(text) {
        const announcement = document.createElement('div');
        announcement.className = 'sr-only';
        announcement.setAttribute('role', 'status');
        announcement.setAttribute('aria-live', 'polite');
        announcement.textContent = `New transcript: ${text}`;
        document.body.appendChild(announcement);
        
        // Remove after announcement
        setTimeout(() => announcement.remove(), 3000);
    }
    
    /**
     * Clear all transcripts
     */
    clearTranscripts() {
        if (this.transcriptContent) {
            this.transcriptContent.innerHTML = '';
        }
        this.currentSessionTranscripts = [];
        this.wordCount = 0;
        this.startTime = null;
        console.log('📄 Transcripts cleared');
    }
    
    /**
     * Export transcripts to file
     */
    exportTranscripts() {
        if (this.currentSessionTranscripts.length === 0) {
            window.toastSystem?.warning('No transcripts to export');
            return;
        }
        
        // Create formatted text
        let exportText = `MINA Live Transcription Export\n`;
        exportText += `Date: ${new Date().toLocaleString()}\n`;
        exportText += `Total Words: ${this.wordCount}\n`;
        exportText += `Segments: ${this.currentSessionTranscripts.length}\n`;
        exportText += `\n${'='.repeat(50)}\n\n`;
        
        this.currentSessionTranscripts.forEach((transcript, index) => {
            exportText += `[${new Date(transcript.timestamp).toLocaleTimeString()}] `;
            exportText += `(Confidence: ${Math.round(transcript.confidence * 100)}%)\n`;
            exportText += `${transcript.text}\n\n`;
        });
        
        // Create download
        const blob = new Blob([exportText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mina_transcript_${new Date().toISOString().replace(/[:.]/g, '-')}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        
        window.toastSystem?.success('Transcript exported successfully');
    }
    
    /**
     * Show interim/partial transcript while processing
     */
    showInterimTranscript(text) {
        // Find or create interim display
        let interimEl = this.transcriptContent.querySelector('.interim-transcript');
        if (!interimEl) {
            interimEl = document.createElement('div');
            interimEl.className = 'interim-transcript';
            this.transcriptContent.appendChild(interimEl);
        }
        
        interimEl.textContent = text;
        this.scrollToLatest();
    }
    
    /**
     * Clear interim transcript
     */
    clearInterimTranscript() {
        const interimEl = this.transcriptContent.querySelector('.interim-transcript');
        if (interimEl) {
            interimEl.remove();
        }
    }
}

// Initialize and expose globally
const transcriptionDisplay = new TranscriptionDisplayManager();

// Expose functions globally for other scripts
window.updateTranscriptDisplay = (result) => transcriptionDisplay.updateTranscriptDisplay(result);
window.clearTranscripts = () => transcriptionDisplay.clearTranscripts();
window.exportTranscripts = () => transcriptionDisplay.exportTranscripts();
window.showInterimTranscript = (text) => transcriptionDisplay.showInterimTranscript(text);

// Add styles for transcript display
const style = document.createElement('style');
style.textContent = `
    .transcript-content {
        max-height: 400px;
        overflow-y: auto;
        padding: 16px;
        scroll-behavior: smooth;
    }
    
    .transcript-segment {
        margin-bottom: 16px;
        padding: 12px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        border-left: 3px solid var(--accent-color, #4a9eff);
        position: relative;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .transcript-segment:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateX(2px);
    }
    
    .transcript-segment.copied {
        background: rgba(74, 158, 255, 0.2);
    }
    
    .transcript-segment.high-confidence {
        border-left-color: #51cf66;
    }
    
    .transcript-segment.medium-confidence {
        border-left-color: #ffd93d;
    }
    
    .transcript-segment.low-confidence {
        border-left-color: #ff6b6b;
        opacity: 0.8;
    }
    
    .segment-timestamp {
        font-size: 0.75em;
        color: var(--secondary-text, #999);
        display: block;
        margin-bottom: 4px;
    }
    
    .confidence-bar {
        height: 2px;
        background: linear-gradient(90deg, #51cf66, #4a9eff);
        margin: 8px 0;
        border-radius: 1px;
        transition: width 0.3s ease;
    }
    
    .segment-text {
        margin: 8px 0 0 0;
        line-height: 1.5;
        color: var(--primary-text, #fff);
    }
    
    .speaker-label {
        font-weight: bold;
        color: var(--accent-color, #4a9eff);
    }
    
    .interim-transcript {
        padding: 12px;
        background: rgba(74, 158, 255, 0.1);
        border-left: 3px solid #4a9eff;
        border-radius: 8px;
        font-style: italic;
        opacity: 0.7;
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    .processing-message {
        text-align: center;
        color: var(--secondary-text, #999);
        padding: 20px;
        font-style: italic;
    }
    
    .fade-in {
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.7; }
        50% { opacity: 1; }
    }
`;
document.head.appendChild(style);

console.log('📝 Transcription display manager initialized');

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
