/**
 * CRITICAL TRANSCRIPT DISPLAY FIX
 * Connects transcription results to frontend display
 */

class TranscriptDisplayFix {
    constructor() {
        this.transcriptContainer = null;
        this.segmentCount = 0;
        this.cumulativeText = '';
        this.isInitialized = false;
    }
    
    initialize() {
        console.log('🔧 Initializing Transcript Display Fix');
        
        // Find the transcript container
        this.transcriptContainer = document.getElementById('transcriptContainer') ||
                                 document.getElementById('transcript') ||
                                 document.querySelector('.transcript-content') ||
                                 document.querySelector('.transcription-container');
        
        if (this.transcriptContainer) {
            console.log('✅ Transcript container found:', this.transcriptContainer.id || this.transcriptContainer.className);
            this.setupContainer();
            this.isInitialized = true;
            return true;
        } else {
            console.error('❌ No transcript container found');
            return false;
        }
    }
    
    setupContainer() {
        // Clear any empty state
        const emptyState = this.transcriptContainer.querySelector('.transcript-empty');
        if (emptyState) {
            emptyState.style.display = 'none';
        }
        
        // Add ready message
        this.showReadyMessage();
    }
    
    showReadyMessage() {
        this.transcriptContainer.innerHTML = `
            <div class="transcript-segment ready-state">
                <div class="transcript-header">
                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                    <span class="confidence confidence-high">Ready</span>
                </div>
                <div class="text-content">🎙️ Ready for transcription. Click record to begin.</div>
            </div>
        `;
    }
    
    displayTranscriptionResult(result) {
        if (!this.isInitialized) {
            console.warn('⚠️ Transcript display not initialized');
            return false;
        }
        
        console.log('📝 Displaying transcription:', result.text);
        
        // Remove ready message on first transcription
        if (this.segmentCount === 0) {
            this.clearReadyMessage();
        }
        
        // Create new segment
        this.createTranscriptSegment(result);
        
        // Update cumulative text
        if (result.is_final && result.text && result.text.trim()) {
            this.cumulativeText += result.text + ' ';
        }
        
        this.segmentCount++;
        return true;
    }
    
    clearReadyMessage() {
        const readyState = this.transcriptContainer.querySelector('.ready-state');
        if (readyState) {
            readyState.remove();
        }
    }
    
    createTranscriptSegment(result) {
        const segmentId = `segment-${this.segmentCount}`;
        const confidence = Math.round((result.confidence || 0.9) * 100);
        const timestamp = new Date().toLocaleTimeString();
        const isFinal = result.is_final || false;
        
        // Create segment element
        const segmentElement = document.createElement('div');
        segmentElement.id = segmentId;
        segmentElement.className = `transcript-segment ${isFinal ? 'final' : 'interim'}`;
        
        // Add content
        segmentElement.innerHTML = `
            <div class="transcript-header">
                <span class="timestamp">${timestamp}</span>
                <span class="confidence confidence-${confidence >= 80 ? 'high' : confidence >= 60 ? 'medium' : 'low'}">
                    ${confidence}%
                </span>
                ${!isFinal ? '<span class="status-badge interim">Live</span>' : '<span class="status-badge final">Final</span>'}
            </div>
            <div class="text-content">${result.text}</div>
        `;
        
        // Handle interim vs final results
        if (!isFinal) {
            // Replace any existing interim segment
            const existingInterim = this.transcriptContainer.querySelector('.transcript-segment.interim');
            if (existingInterim) {
                existingInterim.replaceWith(segmentElement);
            } else {
                this.transcriptContainer.appendChild(segmentElement);
            }
        } else {
            // Remove interim and add final
            const existingInterim = this.transcriptContainer.querySelector('.transcript-segment.interim');
            if (existingInterim) {
                existingInterim.remove();
            }
            this.transcriptContainer.appendChild(segmentElement);
        }
        
        // Auto-scroll to bottom
        this.transcriptContainer.scrollTop = this.transcriptContainer.scrollHeight;
        
        console.log(`✅ Segment ${segmentId} displayed: "${result.text}" (${confidence}%, ${isFinal ? 'final' : 'interim'})`);
    }
    
    updateLiveTranscriptElements(result) {
        // Update other live transcript elements on the page
        const liveSelectors = [
            '.live-transcript',
            '[data-transcript="live"]',
            '#liveTranscript',
            '.transcript-live'
        ];
        
        liveSelectors.forEach(selector => {
            try {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    if (el) {
                        el.textContent = result.text;
                        el.classList.toggle('interim', !result.is_final);
                        el.classList.toggle('final', result.is_final);
                    }
                });
            } catch (error) {
                // Silent continue
            }
        });
    }
    
    clear() {
        if (this.transcriptContainer) {
            this.showReadyMessage();
        }
        this.segmentCount = 0;
        this.cumulativeText = '';
    }
    
    getCumulativeText() {
        return this.cumulativeText.trim();
    }
    
    getSegmentCount() {
        return this.segmentCount;
    }
}

// Global instance
window.transcriptDisplayFix = new TranscriptDisplayFix();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const success = window.transcriptDisplayFix.initialize();
    if (success) {
        console.log('✅ Transcript Display Fix ready');
    } else {
        console.error('❌ Transcript Display Fix failed to initialize');
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TranscriptDisplayFix };
}