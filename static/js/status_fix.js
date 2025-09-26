/**
 * CRITICAL STATUS DISPLAY FIX
 * Addresses the "Ready Ready", "Recording Recording", "Error Error" duplication issues
 */

class StatusDisplayFixer {
    constructor() {
        this.isActive = false;
        this.fixInterval = null;
        this.lastFixTime = 0;
        this.fixCount = 0;
    }
    
    initialize() {
        console.log('🔧 Initializing Status Display Fixer');
        this.startContinuousFixing();
    }
    
    startContinuousFixing() {
        if (this.isActive) return;
        
        this.isActive = true;
        
        // Fix immediately
        this.fixAllStatusDisplays();
        
        // Set up continuous monitoring and fixing
        this.fixInterval = setInterval(() => {
            this.fixAllStatusDisplays();
        }, 500); // Check every 500ms
        
        // Also fix on DOM mutations
        this.observeStatusChanges();
        
        console.log('✅ Status Display Fixer active');
    }
    
    fixAllStatusDisplays() {
        const now = Date.now();
        if (now - this.lastFixTime < 100) return; // Throttle fixes
        
        let fixesApplied = 0;
        
        // Find all potential status elements
        const selectors = [
            '[class*="status"]',
            '[id*="status"]', 
            '.system-status',
            '.recording-status',
            '.connection-status',
            '.transcription-status',
            '[data-status]',
            '.status-indicator',
            '.status-text',
            '.state-display'
        ];
        
        selectors.forEach(selector => {
            try {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    const fixed = this.fixDuplicateText(el);
                    if (fixed) {
                        fixesApplied++;
                    }
                });
            } catch (error) {
                // Silently continue if selector fails
            }
        });
        
        // Also check common text patterns across the page
        this.fixCommonTextPatterns();
        
        if (fixesApplied > 0) {
            this.fixCount += fixesApplied;
            console.log(`🔧 Applied ${fixesApplied} status fixes (total: ${this.fixCount})`);
        }
        
        this.lastFixTime = now;
    }
    
    fixDuplicateText(element) {
        if (!element || !element.textContent) return false;
        
        const originalText = element.textContent.trim();
        if (!originalText) return false;
        
        // Define all duplicate patterns to fix
        const duplicatePatterns = [
            { pattern: /Ready\s+Ready/gi, replacement: 'Ready' },
            { pattern: /Recording\s+Recording/gi, replacement: 'Recording' },
            { pattern: /Error\s+Error/gi, replacement: 'Error' },
            { pattern: /Processing\s+Processing/gi, replacement: 'Processing' },
            { pattern: /Connecting\s+Connecting/gi, replacement: 'Connecting' },
            { pattern: /Connected\s+Connected/gi, replacement: 'Connected' },
            { pattern: /Transcribing\s+Transcribing/gi, replacement: 'Transcribing' },
            { pattern: /Waiting\s+Waiting/gi, replacement: 'Waiting' },
            { pattern: /Loading\s+Loading/gi, replacement: 'Loading' },
            { pattern: /Failed\s+Failed/gi, replacement: 'Failed' },
            { pattern: /Success\s+Success/gi, replacement: 'Success' },
            { pattern: /Stopped\s+Stopped/gi, replacement: 'Stopped' }
        ];
        
        let fixedText = originalText;
        let wasFixed = false;
        
        duplicatePatterns.forEach(({ pattern, replacement }) => {
            const newText = fixedText.replace(pattern, replacement);
            if (newText !== fixedText) {
                fixedText = newText;
                wasFixed = true;
            }
        });
        
        if (wasFixed) {
            // Update the element's content
            if (element.textContent !== fixedText) {
                element.textContent = fixedText;
                console.log(`🔧 Status fix: "${originalText}" → "${fixedText}"`);
                return true;
            }
        }
        
        return false;
    }
    
    fixCommonTextPatterns() {
        // Look for text nodes that might contain duplicate patterns
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: (node) => {
                    const text = node.textContent.trim();
                    return text && (
                        text.includes(' Ready') ||
                        text.includes(' Recording') ||
                        text.includes(' Error') ||
                        text.includes(' Processing')
                    ) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
                }
            }
        );
        
        const textNodes = [];
        let node;
        while (node = walker.nextNode()) {
            textNodes.push(node);
        }
        
        textNodes.forEach(textNode => {
            const originalText = textNode.textContent;
            const fixedText = this.fixTextContent(originalText);
            
            if (fixedText !== originalText) {
                textNode.textContent = fixedText;
                console.log(`🔧 Text node fix: "${originalText}" → "${fixedText}"`);
            }
        });
    }
    
    fixTextContent(text) {
        return text
            .replace(/Ready\s+Ready/gi, 'Ready')
            .replace(/Recording\s+Recording/gi, 'Recording')
            .replace(/Error\s+Error/gi, 'Error')
            .replace(/Processing\s+Processing/gi, 'Processing')
            .replace(/Connecting\s+Connecting/gi, 'Connecting')
            .replace(/Connected\s+Connected/gi, 'Connected')
            .replace(/Transcribing\s+Transcribing/gi, 'Transcribing');
    }
    
    observeStatusChanges() {
        // Set up mutation observer to catch dynamic status changes
        const observer = new MutationObserver((mutations) => {
            let shouldFix = false;
            
            mutations.forEach(mutation => {
                if (mutation.type === 'childList' || mutation.type === 'characterData') {
                    shouldFix = true;
                }
            });
            
            if (shouldFix) {
                // Delay the fix slightly to let all changes settle
                setTimeout(() => {
                    this.fixAllStatusDisplays();
                }, 50);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });
        
        console.log('👁️ Status change observer active');
    }
    
    stop() {
        this.isActive = false;
        if (this.fixInterval) {
            clearInterval(this.fixInterval);
            this.fixInterval = null;
        }
        console.log('🛑 Status Display Fixer stopped');
    }
    
    // Public method to manually trigger a fix
    fixNow() {
        this.fixAllStatusDisplays();
    }
    
    // Get statistics
    getStats() {
        return {
            isActive: this.isActive,
            totalFixes: this.fixCount,
            lastFixTime: this.lastFixTime
        };
    }
}

// Initialize the fixer when DOM is ready
let statusFixer = null;

document.addEventListener('DOMContentLoaded', function() {
    statusFixer = new StatusDisplayFixer();
    statusFixer.initialize();
    
    // Make available globally for debugging
    window.statusFixer = statusFixer;
});

// Also initialize immediately if DOM is already ready
if (document.readyState === 'loading') {
    // DOM is still loading, wait for DOMContentLoaded
} else {
    // DOM is already ready
    if (!statusFixer) {
        statusFixer = new StatusDisplayFixer();
        statusFixer.initialize();
        window.statusFixer = statusFixer;
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { StatusDisplayFixer };
}

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
