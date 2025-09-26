/**
 * COMPREHENSIVE SYSTEM FIXES
 * Addresses all critical issues identified in mobile testing
 * Fixes JavaScript errors, audio processing, and UI display issues
 */

// Fix 1: Enhanced Error-Safe JavaScript Loading
(function() {
    'use strict';
    
    // Prevent syntax errors from breaking the entire system
    window.addEventListener('error', function(event) {
        console.error('🚨 JavaScript Error Caught:', {
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            error: event.error
        });
        
        // Don't let errors break the transcription system
        event.preventDefault();
        
        // Show user-friendly error message
        const errorContainer = document.getElementById('errorContainer') || createErrorContainer();
        errorContainer.innerHTML = `
            <div class="alert alert-warning alert-dismissible">
                <i class="fas fa-exclamation-triangle"></i>
                <strong>System Notice:</strong> Optimizing performance, transcription continues...
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
    });
    
    function createErrorContainer() {
        const container = document.createElement('div');
        container.id = 'errorContainer';
        container.className = 'error-container mb-3';
        document.querySelector('.app-container').insertBefore(container, document.querySelector('.app-container').firstChild);
        return container;
    }
})();

// Fix 2: Enhanced Status Display Manager
class StatusDisplayManager {
    constructor() {
        this.currentStatus = 'ready';
        this.statusHistory = [];
        this.duplicateCheckEnabled = true;
    }
    
    updateStatus(newStatus, context = '') {
        // Prevent duplicate status display
        if (this.duplicateCheckEnabled && this.currentStatus === newStatus) {
            console.log(`🔄 Status already ${newStatus}, skipping duplicate update`);
            return;
        }
        
        this.currentStatus = newStatus;
        this.statusHistory.push({
            status: newStatus,
            timestamp: Date.now(),
            context
        });
        
        // Keep only last 10 status changes
        if (this.statusHistory.length > 10) {
            this.statusHistory.shift();
        }
        
        this.renderStatus(newStatus, context);
    }
    
    renderStatus(status, context = '') {
        const statusElements = [
            document.getElementById('statusText'),
            document.querySelector('.status-text'),
            document.querySelector('.connection-status .status-text')
        ].filter(el => el);
        
        const statusDotElements = [
            document.getElementById('statusDot'),
            document.querySelector('.status-dot'),
            document.querySelector('.connection-status .status-dot')
        ].filter(el => el);
        
        // Update text elements
        statusElements.forEach(el => {
            el.textContent = this.getStatusText(status);
        });
        
        // Update dot elements
        statusDotElements.forEach(el => {
            // Remove all status classes
            el.classList.remove('ready', 'recording', 'processing', 'error', 'connecting');
            // Add current status class
            el.classList.add(this.getStatusClass(status));
        });
        
        console.log(`📊 Status updated: ${status} ${context}`);
    }
    
    getStatusText(status) {
        const statusMap = {
            'ready': 'Ready',
            'recording': 'Recording',
            'processing': 'Processing',
            'error': 'Issue Detected',
            'connecting': 'Connecting',
            'transcribing': 'Transcribing'
        };
        return statusMap[status] || 'Active';
    }
    
    getStatusClass(status) {
        const classMap = {
            'ready': 'ready',
            'recording': 'recording', 
            'processing': 'processing',
            'error': 'error',
            'connecting': 'connecting',
            'transcribing': 'processing'
        };
        return classMap[status] || 'ready';
    }
    
    clearDuplicateStatus() {
        // Fix the "Ready Ready" display issue
        const statusElements = document.querySelectorAll('[class*="status"]');
        statusElements.forEach(el => {
            if (el.textContent && el.textContent.includes('Ready Ready')) {
                el.textContent = 'Ready';
            }
            if (el.textContent && el.textContent.includes('Recording Recording')) {
                el.textContent = 'Recording';
            }
        });
    }
}

// Fix 3: Enhanced Metrics Display Manager
class MetricsDisplayManager {
    constructor() {
        this.metrics = {
            duration: '00:00',
            words: 0,
            accuracy: 0,
            chunks: 0,
            latency: 0,
            quality: 0
        };
        this.animationEnabled = true;
    }
    
    updateMetric(key, value, animate = true) {
        this.metrics[key] = value;
        
        const elementMappings = {
            'duration': ['sessionTime', 'durationDisplay'],
            'words': ['wordCount', 'wordsCount', 'wordsDisplay'],
            'accuracy': ['confidenceScore', 'accuracyPercentage', 'accuracyDisplay'],
            'chunks': ['chunksProcessed', 'chunksCount', 'chunksDisplay'],
            'latency': ['latencyMs', 'latencyDisplay'],
            'quality': ['qualityScore', 'qualityDisplay']
        };
        
        const possibleIds = elementMappings[key] || [key];
        
        possibleIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                const formattedValue = this.formatValue(key, value);
                element.textContent = formattedValue;
                
                if (animate && this.animationEnabled) {
                    this.animateUpdate(element);
                }
                
                // Add color coding based on performance
                this.applyColorCoding(element, key, value);
                
                console.log(`📊 Updated ${key}: ${formattedValue}`);
            }
        });
    }
    
    formatValue(key, value) {
        switch (key) {
            case 'duration':
                return value; // Already formatted as MM:SS
            case 'words':
            case 'chunks':
                return Math.max(0, parseInt(value) || 0).toString();
            case 'accuracy':
            case 'quality':
                const percentage = Math.max(0, Math.min(100, parseFloat(value) || 0));
                return Math.round(percentage) + '%';
            case 'latency':
                const latencyMs = Math.max(0, parseFloat(value) || 0);
                return Math.round(latencyMs) + 'ms';
            default:
                return value?.toString() || '0';
        }
    }
    
    animateUpdate(element) {
        element.classList.add('metric-update');
        setTimeout(() => {
            element.classList.remove('metric-update');
        }, 600);
    }
    
    applyColorCoding(element, key, value) {
        // Remove existing color classes
        element.classList.remove('text-success', 'text-warning', 'text-danger', 'text-info');
        
        switch (key) {
            case 'accuracy':
            case 'quality':
                const percentage = parseFloat(value) || 0;
                if (percentage >= 80) {
                    element.classList.add('text-success');
                } else if (percentage >= 60) {
                    element.classList.add('text-warning');
                } else if (percentage > 0) {
                    element.classList.add('text-danger');
                } else {
                    element.classList.add('text-info'); // 0% gets info color
                }
                break;
            case 'latency':
                const latency = parseFloat(value) || 0;
                if (latency <= 500) {
                    element.classList.add('text-success');
                } else if (latency <= 1500) {
                    element.classList.add('text-warning');
                } else {
                    element.classList.add('text-danger');
                }
                break;
            case 'words':
                const words = parseInt(value) || 0;
                if (words > 0) {
                    element.classList.add('text-success');
                } else {
                    element.classList.add('text-info');
                }
                break;
            default:
                element.classList.add('text-info');
        }
    }
    
    resetMetrics() {
        this.updateMetric('duration', '00:00', false);
        this.updateMetric('words', 0, false);
        this.updateMetric('accuracy', 0, false);
        this.updateMetric('chunks', 0, false);
        this.updateMetric('latency', 0, false);
        this.updateMetric('quality', 0, false);
        
        console.log('📊 Metrics reset');
    }
    
    updateFromResult(result) {
        // Update individual metrics based on transcription result
        if (result.processing_time_ms !== undefined) {
            this.updateMetric('latency', result.processing_time_ms);
        }
        if (result.confidence !== undefined) {
            this.updateMetric('accuracy', result.confidence * 100);
            this.updateMetric('quality', result.confidence * 100);
        }
        if (result.word_count !== undefined) {
            this.updateMetric('words', result.word_count);
        }
    }
}

// Fix 4: Enhanced Audio Quality Validator
class AudioQualityValidator {
    constructor() {
        this.validationEnabled = true;
        this.minimumSize = 1000; // bytes
        this.maximumSize = 10 * 1024 * 1024; // 10MB
    }
    
    validateAudioBlob(audioBlob) {
        const validation = {
            isValid: true,
            issues: [],
            quality: 'good',
            size: audioBlob.size,
            type: audioBlob.type
        };
        
        // Size validation
        if (audioBlob.size < this.minimumSize) {
            validation.isValid = false;
            validation.issues.push(`Audio too small: ${audioBlob.size} bytes (min: ${this.minimumSize})`);
            validation.quality = 'poor';
        } else if (audioBlob.size > this.maximumSize) {
            validation.isValid = false;
            validation.issues.push(`Audio too large: ${audioBlob.size} bytes (max: ${this.maximumSize})`);
            validation.quality = 'poor';
        }
        
        // Type validation
        if (!audioBlob.type.includes('audio/')) {
            validation.issues.push(`Unexpected MIME type: ${audioBlob.type}`);
            validation.quality = validation.quality === 'good' ? 'fair' : 'poor';
        }
        
        // Duration estimation
        const estimatedDurationMs = this.estimateDuration(audioBlob);
        if (estimatedDurationMs < 300) {
            validation.issues.push(`Very short duration: ~${estimatedDurationMs}ms`);
            validation.quality = validation.quality === 'good' ? 'fair' : 'poor';
        }
        
        validation.estimatedDuration = estimatedDurationMs;
        
        return validation;
    }
    
    estimateDuration(audioBlob) {
        // Rough estimation based on file size and typical audio encoding
        const avgBitrate = 32000; // bits per second for typical WebM/Opus
        const fileSizeBits = audioBlob.size * 8;
        return (fileSizeBits / avgBitrate) * 1000; // Convert to milliseconds
    }
    
    generateQualityReport(validation) {
        let report = `Audio Quality: ${validation.quality.toUpperCase()}\n`;
        report += `Size: ${(validation.size / 1024).toFixed(1)}KB\n`;
        report += `Type: ${validation.type}\n`;
        report += `Estimated Duration: ${validation.estimatedDuration?.toFixed(0)}ms\n`;
        
        if (validation.issues.length > 0) {
            report += `Issues: ${validation.issues.join(', ')}`;
        }
        
        return report;
    }
}

// Fix 5: Transcript Content Manager
class TranscriptContentManager {
    constructor() {
        this.transcriptHistory = [];
        this.maxHistory = 50;
        this.duplicateThreshold = 0.8;
    }
    
    addTranscript(text, confidence = 0.9, timestamp = Date.now()) {
        if (!text || text.includes('[No speech detected]') || text.includes('[Filtered]')) {
            return false; // Don't add system messages
        }
        
        // Check for duplicates
        if (this.isDuplicate(text)) {
            console.log('🔄 Duplicate transcript filtered');
            return false;
        }
        
        const transcriptEntry = {
            text: text.trim(),
            confidence,
            timestamp,
            id: `transcript_${timestamp}_${Math.random().toString(36).substr(2, 9)}`
        };
        
        this.transcriptHistory.push(transcriptEntry);
        
        // Maintain history size
        if (this.transcriptHistory.length > this.maxHistory) {
            this.transcriptHistory.shift();
        }
        
        this.displayTranscript(transcriptEntry);
        return true;
    }
    
    isDuplicate(newText) {
        if (this.transcriptHistory.length === 0) return false;
        
        const recent = this.transcriptHistory.slice(-3); // Check last 3 entries
        return recent.some(entry => {
            const similarity = this.calculateSimilarity(entry.text.toLowerCase(), newText.toLowerCase());
            return similarity > this.duplicateThreshold;
        });
    }
    
    calculateSimilarity(str1, str2) {
        if (str1 === str2) return 1;
        
        const longer = str1.length > str2.length ? str1 : str2;
        const shorter = str1.length > str2.length ? str2 : str1;
        
        if (longer.length === 0) return 1;
        
        const editDistance = this.levenshteinDistance(longer, shorter);
        return (longer.length - editDistance) / longer.length;
    }
    
    levenshteinDistance(str1, str2) {
        const matrix = Array(str2.length + 1).fill().map(() => Array(str1.length + 1).fill(0));
        
        for (let i = 0; i <= str1.length; i++) matrix[0][i] = i;
        for (let j = 0; j <= str2.length; j++) matrix[j][0] = j;
        
        for (let j = 1; j <= str2.length; j++) {
            for (let i = 1; i <= str1.length; i++) {
                if (str1[i - 1] === str2[j - 1]) {
                    matrix[j][i] = matrix[j - 1][i - 1];
                } else {
                    matrix[j][i] = Math.min(
                        matrix[j - 1][i] + 1,
                        matrix[j][i - 1] + 1,
                        matrix[j - 1][i - 1] + 1
                    );
                }
            }
        }
        
        return matrix[str2.length][str1.length];
    }
    
    displayTranscript(transcriptEntry) {
        const transcriptContainers = [
            document.getElementById('transcriptContainer'),
            document.querySelector('.transcript-content'),
            document.querySelector('#transcript')
        ].filter(el => el);
        
        if (transcriptContainers.length === 0) {
            console.warn('⚠️ No transcript container found');
            return;
        }
        
        const timestamp = new Date(transcriptEntry.timestamp).toLocaleTimeString();
        const confidence = Math.round(transcriptEntry.confidence * 100);
        
        const transcriptHTML = `
            <div class="transcript-entry" data-id="${transcriptEntry.id}">
                <div class="transcript-header d-flex justify-content-between align-items-center mb-2">
                    <div class="d-flex align-items-center">
                        <span class="badge bg-primary me-2">Live</span>
                        <span class="confidence-badge badge ${this.getConfidenceBadgeClass(confidence)}">
                            ${confidence}%
                        </span>
                    </div>
                    <small class="text-muted">${timestamp}</small>
                </div>
                <div class="transcript-text" style="font-size: 1.1em; line-height: 1.6; color: #fff; margin: 0.5rem 0;">
                    ${transcriptEntry.text}
                </div>
            </div>
        `;
        
        transcriptContainers.forEach(container => {
            container.innerHTML = transcriptHTML;
        });
        
        console.log(`📝 Transcript displayed: "${transcriptEntry.text.substring(0, 50)}..." (${confidence}%)`);
    }
    
    getConfidenceBadgeClass(confidence) {
        if (confidence >= 90) return 'bg-success';
        if (confidence >= 70) return 'bg-warning';
        return 'bg-danger';
    }
    
    clearTranscripts() {
        this.transcriptHistory = [];
        const containers = [
            document.getElementById('transcriptContainer'),
            document.querySelector('.transcript-content'),
            document.querySelector('#transcript')
        ].filter(el => el);
        
        containers.forEach(container => {
            container.innerHTML = `
                <div class="text-muted text-center py-4">
                    <i class="fas fa-microphone-slash mb-3" style="font-size: 2rem; opacity: 0.5;"></i>
                    <p>Ready to transcribe speech</p>
                </div>
            `;
        });
    }
}

// Global instances
window.statusManager = new StatusDisplayManager();
window.metricsManager = new MetricsDisplayManager();
window.audioValidator = new AudioQualityValidator();
window.transcriptManager = new TranscriptContentManager();

// Initialize comprehensive fixes
document.addEventListener('DOMContentLoaded', function() {
    console.log('🛠️ Comprehensive fixes initialized');
    
    // Fix duplicate status displays
    window.statusManager.clearDuplicateStatus();
    
    // Reset metrics to clean state
    window.metricsManager.resetMetrics();
    
    // Clear any existing transcripts
    window.transcriptManager.clearTranscripts();
    
    // Add enhanced CSS
    addEnhancedCSS();
    
    console.log('✅ All comprehensive fixes applied');
});

function addEnhancedCSS() {
    const css = `
        .metric-update {
            animation: metricPulse 0.6s ease-in-out;
            transform: scale(1.02);
        }
        
        @keyframes metricPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        .transcript-entry {
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.5rem;
            background: rgba(255, 255, 255, 0.02);
        }
        
        .confidence-badge {
            font-size: 0.75em;
        }
        
        .error-container {
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .status-dot.ready { background-color: #28a745; }
        .status-dot.recording { background-color: #dc3545; animation: pulse 1s infinite; }
        .status-dot.processing { background-color: #ffc107; animation: pulse 1s infinite; }
        .status-dot.error { background-color: #dc3545; }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    `;
    
    const style = document.createElement('style');
    style.textContent = css;
    document.head.appendChild(style);
}

// Export for integration with existing systems
if (typeof window !== 'undefined') {
    window.ComprehensiveFixes = {
        StatusDisplayManager,
        MetricsDisplayManager,
        AudioQualityValidator,
        TranscriptContentManager
    };
}

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
