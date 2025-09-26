/**
 * ENTERPRISE-GRADE CONVERSATION TRANSCRIPT SYSTEM
 * Google Recorder-level conversation flow with accessibility & mobile optimization
 */

class EnhancedConversationTranscript {
    constructor() {
        this.transcriptContainer = null;
        this.segmentCount = 0;
        this.cumulativeText = '';
        this.isInitialized = false;
        
        // Enhanced conversation features
        this.conversations = new Map(); // Track different speakers/segments
        this.currentConversationId = 'main';
        this.currentSpeaker = 'Speaker';
        this.isTyping = false;
        this.typingTimeout = null;
        this.confidenceThreshold = 0.7;
        
        // Performance optimization
        this.virtualScrollEnabled = false;
        this.maxVisibleSegments = 50;
        this.segmentPool = [];
        
        // Accessibility features
        this.announceNewText = true;
        this.highContrastMode = false;
        this.largeTextMode = false;
        
        // Mobile optimization
        this.touchStartY = 0;
        this.isMobile = window.innerWidth <= 768;
        
        // User preferences
        this.preferences = {
            autoScroll: true,
            showTimestamps: true,
            showConfidence: true,
            fontSize: 16,
            theme: 'dark'
        };
        
        this.loadPreferences();
    }
    
    initialize() {
        console.log('🚀 Initializing Enterprise-Grade Conversation Transcript System');
        
        // Find the transcript container with multiple fallbacks
        this.transcriptContainer = this.findTranscriptContainer();
        
        if (this.transcriptContainer) {
            console.log('✅ Transcript container found:', this.transcriptContainer.id || this.transcriptContainer.className);
            this.setupEnhancedContainer();
            this.setupAccessibility();
            this.setupMobileOptimizations();
            this.setupKeyboardNavigation();
            this.bindEvents();
            this.isInitialized = true;
            
            // Announce readiness to screen readers
            this.announceToScreenReader('Live transcript system ready');
            
            return true;
        } else {
            console.error('❌ No transcript container found');
            this.createFallbackContainer();
            return false;
        }
    }
    
    findTranscriptContainer() {
        const selectors = [
            '#transcriptContainer',
            '#transcript', 
            '.transcript-content',
            '.transcription-container',
            '[data-transcript]',
            '[role="log"]'
        ];
        
        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element) return element;
        }
        
        return null;
    }
    
    createFallbackContainer() {
        console.warn('⚠️ Creating fallback transcript container');
        const container = document.createElement('div');
        container.id = 'transcriptContainer';
        container.className = 'transcript-content fallback-container';
        container.setAttribute('role', 'log');
        container.setAttribute('aria-live', 'polite');
        container.setAttribute('aria-label', 'Live transcription text');
        
        document.body.appendChild(container);
        this.transcriptContainer = container;
        this.setupEnhancedContainer();
    }
    
    setupEnhancedContainer() {
        // Enhanced container setup with accessibility
        this.transcriptContainer.classList.add('enhanced-transcript');
        this.transcriptContainer.setAttribute('tabindex', '0');
        this.transcriptContainer.setAttribute('aria-describedby', 'transcript-help');
        
        // Add conversation container
        this.transcriptContainer.innerHTML = `
            <div class="conversation-container" role="log" aria-live="polite">
                <div class="conversation-welcome" role="status">
                    <div class="welcome-icon">
                        <i class="fas fa-comments" aria-hidden="true"></i>
                    </div>
                    <h3 class="welcome-title">Ready for live transcription</h3>
                    <p class="welcome-description">Click the record button to start your conversation</p>
                    <div class="typing-indicator" style="display: none;" role="status" aria-live="assertive">
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                        <span class="sr-only">Processing speech</span>
                    </div>
                </div>
            </div>
            <div id="transcript-help" class="sr-only">
                Live transcript showing real-time speech recognition. Use arrow keys to navigate, Tab to access controls.
            </div>
        `;
        
        // Apply user preferences
        this.applyPreferences();
        
        // Clear any empty state
        const emptyState = this.transcriptContainer.querySelector('.transcript-empty');
        if (emptyState) {
            emptyState.style.display = 'none';
        }
    }
    
    // Legacy method for backward compatibility
    showReadyMessage() {
        this.setupEnhancedContainer();
    }
    
    displayTranscriptionResult(result) {
        if (!this.isInitialized) {
            console.warn('⚠️ Transcript display not initialized');
            return false;
        }
        
        console.log('💬 Displaying conversation result:', result.text);
        
        // Remove welcome message on first transcription
        if (this.segmentCount === 0) {
            this.clearWelcomeMessage();
        }
        
        // Show typing indicator for interim results
        if (!result.is_final) {
            this.showTypingIndicator();
        } else {
            this.hideTypingIndicator();
        }
        
        // Create or update conversation segment
        this.createConversationSegment(result);
        
        // Update cumulative text for final results
        if (result.is_final && result.text && result.text.trim()) {
            this.cumulativeText += result.text + ' ';
            
            // Announce to screen readers for important text
            if (this.announceNewText && result.confidence > this.confidenceThreshold) {
                this.announceToScreenReader(result.text);
            }
        }
        
        // Auto-scroll if enabled
        if (this.preferences.autoScroll) {
            this.smoothScrollToBottom();
        }
        
        this.segmentCount++;
        return true;
    }
    
    clearWelcomeMessage() {
        const welcomeState = this.transcriptContainer.querySelector('.conversation-welcome');
        if (welcomeState) {
            welcomeState.style.opacity = '0';
            welcomeState.style.transform = 'translateY(-20px)';
            setTimeout(() => welcomeState.remove(), 300);
        }
    }
    
    showTypingIndicator() {
        if (this.isTyping) return;
        
        const indicator = this.transcriptContainer.querySelector('.typing-indicator');
        if (indicator) {
            indicator.style.display = 'flex';
            indicator.setAttribute('aria-live', 'assertive');
            this.isTyping = true;
            
            // Auto-hide after 3 seconds of no activity
            clearTimeout(this.typingTimeout);
            this.typingTimeout = setTimeout(() => {
                this.hideTypingIndicator();
            }, 3000);
        }
    }
    
    hideTypingIndicator() {
        const indicator = this.transcriptContainer.querySelector('.typing-indicator');
        if (indicator) {
            indicator.style.display = 'none';
            indicator.setAttribute('aria-live', 'off');
            this.isTyping = false;
        }
        clearTimeout(this.typingTimeout);
    }
    
    createConversationSegment(result) {
        const segmentId = `conversation-${this.segmentCount}`;
        const confidence = Math.round((result.confidence || 0.9) * 100);
        const timestamp = new Date().toLocaleTimeString();
        const isFinal = result.is_final || false;
        const speaker = result.speaker || this.currentSpeaker;
        
        let conversationContainer = this.transcriptContainer.querySelector('.conversation-container');
        if (!conversationContainer) {
            conversationContainer = document.createElement('div');
            conversationContainer.className = 'conversation-container';
            conversationContainer.setAttribute('role', 'log');
            conversationContainer.setAttribute('aria-live', 'polite');
            this.transcriptContainer.appendChild(conversationContainer);
        }
        
        // Create enhanced conversation bubble
        const segmentElement = document.createElement('div');
        segmentElement.id = segmentId;
        segmentElement.className = `conversation-bubble ${isFinal ? 'final' : 'interim'} confidence-${confidence >= 80 ? 'high' : confidence >= 60 ? 'medium' : 'low'}`;
        segmentElement.setAttribute('role', 'listitem');
        segmentElement.setAttribute('aria-label', `${speaker} said: ${result.text}`);
        
        // Enhanced content with accessibility
        segmentElement.innerHTML = `
            <div class="conversation-meta">
                <div class="speaker-info">
                    <div class="speaker-avatar" aria-hidden="true">
                        <i class="fas fa-user"></i>
                    </div>
                    <span class="speaker-name">${speaker}</span>
                </div>
                ${this.preferences.showTimestamps ? `<span class="conversation-time">${timestamp}</span>` : ''}
            </div>
            <div class="conversation-content">
                <div class="text-content" ${!isFinal ? 'aria-live="polite"' : ''}>
                    ${this.formatText(result.text)}
                </div>
                ${this.preferences.showConfidence ? `
                <div class="confidence-indicator">
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${confidence}%" aria-label="${confidence}% confidence"></div>
                    </div>
                    <span class="confidence-text">${confidence}%</span>
                </div>
                ` : ''}
                <div class="segment-controls" style="opacity: 0; pointer-events: none;">
                    <button class="segment-btn" onclick="this.closest('.enhanced-transcript').transcriptSystem.copySegment('${segmentId}')" aria-label="Copy this text">
                        <i class="fas fa-copy"></i>
                    </button>
                    <button class="segment-btn" onclick="this.closest('.enhanced-transcript').transcriptSystem.highlightSegment('${segmentId}')" aria-label="Highlight this text">
                        <i class="fas fa-highlighter"></i>
                    </button>
                </div>
            </div>
        `;
        
        // Handle interim vs final results with conversation flow
        if (!isFinal) {
            // Update existing interim or create new
            const existingInterim = conversationContainer.querySelector('.conversation-bubble.interim');
            if (existingInterim && existingInterim.dataset.speaker === speaker) {
                // Update the same speaker's interim text
                const textContent = existingInterim.querySelector('.text-content');
                if (textContent) {
                    textContent.innerHTML = this.formatText(result.text);
                    textContent.classList.add('typing-effect');
                }
            } else {
                // Remove any existing interim and add new
                const allInterim = conversationContainer.querySelectorAll('.conversation-bubble.interim');
                allInterim.forEach(el => el.remove());
                
                segmentElement.dataset.speaker = speaker;
                conversationContainer.appendChild(segmentElement);
                
                // Add entrance animation
                segmentElement.style.opacity = '0';
                segmentElement.style.transform = 'translateY(10px)';
                requestAnimationFrame(() => {
                    segmentElement.style.transition = 'all 0.3s ease';
                    segmentElement.style.opacity = '1';
                    segmentElement.style.transform = 'translateY(0)';
                });
            }
        } else {
            // Remove interim and add final with conversation continuity
            const existingInterim = conversationContainer.querySelector('.conversation-bubble.interim');
            if (existingInterim) {
                existingInterim.remove();
            }
            
            conversationContainer.appendChild(segmentElement);
            
            // Add final segment animation
            segmentElement.style.opacity = '0';
            segmentElement.style.transform = 'scale(0.95)';
            requestAnimationFrame(() => {
                segmentElement.style.transition = 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)';
                segmentElement.style.opacity = '1';
                segmentElement.style.transform = 'scale(1)';
                
                // Add completion effect
                setTimeout(() => {
                    segmentElement.classList.add('completed');
                }, 200);
            });
        }
        
        // Performance: Maintain segment limit
        this.maintainSegmentLimit(conversationContainer);
        
        // Add hover effects for desktop
        if (!this.isMobile) {
            this.addHoverEffects(segmentElement);
        }
        
        console.log(`💬 Conversation segment created: "${result.text}" (${confidence}%, ${isFinal ? 'final' : 'interim'})`);
    }
    
    // Accessibility & User Experience Methods
    setupAccessibility() {
        // Enhance container accessibility
        this.transcriptContainer.setAttribute('role', 'main');
        this.transcriptContainer.setAttribute('aria-label', 'Live conversation transcript');
        
        // Add screen reader announcements region
        if (!document.getElementById('aria-announcements')) {
            const announceDiv = document.createElement('div');
            announceDiv.id = 'aria-announcements';
            announceDiv.className = 'sr-only';
            announceDiv.setAttribute('aria-live', 'assertive');
            announceDiv.setAttribute('aria-atomic', 'true');
            document.body.appendChild(announceDiv);
        }
    }
    
    setupMobileOptimizations() {
        if (!this.isMobile) return;
        
        // Add touch event listeners
        this.transcriptContainer.addEventListener('touchstart', (e) => {
            this.touchStartY = e.touches[0].clientY;
        }, { passive: true });
        
        this.transcriptContainer.addEventListener('touchend', (e) => {
            const touchEndY = e.changedTouches[0].clientY;
            const deltaY = this.touchStartY - touchEndY;
            
            // Pull to refresh gesture (pull down 50+ pixels)
            if (deltaY < -50 && this.transcriptContainer.scrollTop === 0) {
                this.refreshTranscript();
            }
        }, { passive: true });
        
        // Optimize for mobile keyboard
        this.transcriptContainer.addEventListener('focus', () => {
            if (window.visualViewport) {
                const viewport = window.visualViewport;
                viewport.addEventListener('resize', this.handleViewportResize.bind(this));
            }
        });
    }
    
    setupKeyboardNavigation() {
        this.transcriptContainer.addEventListener('keydown', (e) => {
            switch (e.key) {
                case 'ArrowUp':
                    e.preventDefault();
                    this.navigateSegments(-1);
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    this.navigateSegments(1);
                    break;
                case 'Home':
                    e.preventDefault();
                    this.scrollToTop();
                    break;
                case 'End':
                    e.preventDefault();
                    this.scrollToBottom();
                    break;
                case 'c':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.copyAllText();
                    }
                    break;
                case 'Escape':
                    this.transcriptContainer.blur();
                    break;
            }
        });
    }
    
    bindEvents() {
        // Window resize handling
        window.addEventListener('resize', this.handleResize.bind(this));
        
        // Visibility change handling
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAnimations();
            } else {
                this.resumeAnimations();
            }
        });
        
        // Save preferences on page unload
        window.addEventListener('beforeunload', () => {
            this.savePreferences();
        });
    }
    
    // Enhanced Utility Methods
    formatText(text) {
        if (!text) return '';
        
        // Enhanced text formatting with punctuation and capitalization
        let formatted = text.trim();
        
        // Capitalize first letter of sentences
        formatted = formatted.replace(/^\w|[.!?]\s+\w/g, (match) => match.toUpperCase());
        
        // Add smart punctuation for common patterns
        formatted = formatted.replace(/(\w)\s+(however|therefore|moreover|furthermore)/gi, '$1. $2');
        formatted = formatted.replace(/(\w)\s+(and then|but then|so then)/gi, '$1, $2');
        
        // Highlight important words
        formatted = formatted.replace(/\b(important|critical|urgent|note|remember)\b/gi, '<strong>$1</strong>');
        
        return formatted;
    }
    
    announceToScreenReader(text) {
        const announceDiv = document.getElementById('aria-announcements');
        if (announceDiv && text && text.trim()) {
            announceDiv.textContent = text;
            
            // Clear after announcement
            setTimeout(() => {
                announceDiv.textContent = '';
            }, 1000);
        }
    }
    
    smoothScrollToBottom() {
        const container = this.transcriptContainer;
        const targetScroll = container.scrollHeight - container.clientHeight;
        
        if (container.scrollTop < targetScroll - 10) {
            container.scrollTo({
                top: targetScroll,
                behavior: 'smooth'
            });
        }
    }
    
    maintainSegmentLimit(container) {
        const segments = container.querySelectorAll('.conversation-bubble');
        if (segments.length > this.maxVisibleSegments) {
            // Remove oldest segments with fade-out animation
            const toRemove = segments.length - this.maxVisibleSegments;
            for (let i = 0; i < toRemove; i++) {
                const segment = segments[i];
                segment.style.opacity = '0';
                segment.style.transform = 'translateX(-20px)';
                setTimeout(() => segment.remove(), 300);
            }
        }
    }
    
    addHoverEffects(element) {
        element.addEventListener('mouseenter', () => {
            const controls = element.querySelector('.segment-controls');
            if (controls) {
                controls.style.opacity = '1';
                controls.style.pointerEvents = 'all';
            }
        });
        
        element.addEventListener('mouseleave', () => {
            const controls = element.querySelector('.segment-controls');
            if (controls) {
                controls.style.opacity = '0';
                controls.style.pointerEvents = 'none';
            }
        });
    }
    
    // User Interaction Methods
    copySegment(segmentId) {
        const segment = document.getElementById(segmentId);
        if (segment) {
            const text = segment.querySelector('.text-content').textContent;
            navigator.clipboard.writeText(text).then(() => {
                this.showNotification('Segment copied to clipboard');
            });
        }
    }
    
    highlightSegment(segmentId) {
        const segment = document.getElementById(segmentId);
        if (segment) {
            segment.classList.toggle('highlighted');
        }
    }
    
    clear() {
        if (this.transcriptContainer) {
            const conversationContainer = this.transcriptContainer.querySelector('.conversation-container');
            if (conversationContainer) {
                conversationContainer.innerHTML = `
                    <div class="conversation-welcome" role="status">
                        <div class="welcome-icon">
                            <i class="fas fa-comments" aria-hidden="true"></i>
                        </div>
                        <h3 class="welcome-title">Ready for live transcription</h3>
                        <p class="welcome-description">Click the record button to start your conversation</p>
                    </div>
                `;
            }
        }
        this.segmentCount = 0;
        this.cumulativeText = '';
        this.conversations.clear();
        
        this.announceToScreenReader('Transcript cleared');
    }
    
    // Performance and Navigation Methods
    navigateSegments(direction) {
        const segments = this.transcriptContainer.querySelectorAll('.conversation-bubble');
        const focusedSegment = document.activeElement;
        const currentIndex = Array.from(segments).indexOf(focusedSegment);
        
        let newIndex = currentIndex + direction;
        newIndex = Math.max(0, Math.min(newIndex, segments.length - 1));
        
        if (segments[newIndex]) {
            segments[newIndex].focus();
            segments[newIndex].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
    
    scrollToTop() {
        this.transcriptContainer.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    scrollToBottom() {
        this.smoothScrollToBottom();
    }
    
    copyAllText() {
        const allText = this.cumulativeText.trim();
        if (allText) {
            navigator.clipboard.writeText(allText).then(() => {
                this.showNotification('All transcript text copied to clipboard');
            });
        }
    }
    
    refreshTranscript() {
        this.showNotification('Refreshing transcript...');
        // Add refresh logic here
    }
    
    handleResize() {
        this.isMobile = window.innerWidth <= 768;
        this.applyPreferences();
    }
    
    handleViewportResize() {
        // Handle mobile keyboard appearance
        const viewport = window.visualViewport;
        if (viewport) {
            this.transcriptContainer.style.height = `${viewport.height - 100}px`;
        }
    }
    
    pauseAnimations() {
        this.transcriptContainer.classList.add('animations-paused');
    }
    
    resumeAnimations() {
        this.transcriptContainer.classList.remove('animations-paused');
    }
    
    showNotification(message) {
        // Simple notification system
        const notification = document.createElement('div');
        notification.className = 'transcript-notification';
        notification.textContent = message;
        notification.setAttribute('role', 'status');
        notification.setAttribute('aria-live', 'polite');
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }
    
    // Preference Management
    loadPreferences() {
        const saved = localStorage.getItem('minaTranscriptPreferences');
        if (saved) {
            try {
                this.preferences = { ...this.preferences, ...JSON.parse(saved) };
            } catch (e) {
                console.warn('Failed to load preferences:', e);
            }
        }
    }
    
    savePreferences() {
        localStorage.setItem('minaTranscriptPreferences', JSON.stringify(this.preferences));
    }
    
    applyPreferences() {
        if (this.transcriptContainer) {
            this.transcriptContainer.style.fontSize = `${this.preferences.fontSize}px`;
            this.transcriptContainer.classList.toggle('high-contrast', this.highContrastMode);
            this.transcriptContainer.classList.toggle('large-text', this.largeTextMode);
        }
    }
    
    // Public API
    getCumulativeText() {
        return this.cumulativeText.trim();
    }
    
    getSegmentCount() {
        return this.segmentCount;
    }
    
    setPreference(key, value) {
        this.preferences[key] = value;
        this.applyPreferences();
        this.savePreferences();
    }
    
    getPreference(key) {
        return this.preferences[key];
    }
}

// Global instance with backward compatibility
window.enhancedConversationTranscript = new EnhancedConversationTranscript();
window.transcriptDisplayFix = window.enhancedConversationTranscript; // Backward compatibility

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const success = window.enhancedConversationTranscript.initialize();
    if (success) {
        console.log('✅ Enhanced Conversation Transcript System ready');
        console.log('🎯 Features: Conversation flow, accessibility, mobile optimization, performance');
        
        // Store reference on container for easy access
        const container = document.querySelector('.enhanced-transcript');
        if (container) {
            container.transcriptSystem = window.enhancedConversationTranscript;
        }
    } else {
        console.error('❌ Enhanced Conversation Transcript System failed to initialize');
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        EnhancedConversationTranscript,
        TranscriptDisplayFix: EnhancedConversationTranscript // Backward compatibility
    };
}

// Global methods for external access
window.transcriptAPI = {
    clear: () => window.enhancedConversationTranscript.clear(),
    getCumulativeText: () => window.enhancedConversationTranscript.getCumulativeText(),
    setPreference: (key, value) => window.enhancedConversationTranscript.setPreference(key, value),
    getPreference: (key) => window.enhancedConversationTranscript.getPreference(key),
    copyAllText: () => window.enhancedConversationTranscript.copyAllText()
};

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
