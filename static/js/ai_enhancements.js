/**
 * 🚀 ADVANCED AI COMPONENTS FOR MINA TRANSCRIPTION
 * Industry-leading enhancements for Google-quality performance
 */

class PunctuationEngine {
    constructor() {
        this.patterns = {
            question: /\b(what|how|when|where|why|who|which|can|could|would|should|do|does|did|is|are|was|were)\b/i,
            statement: /\b(i|you|we|they|he|she|it|this|that|these|those)\b.*\b(said|think|believe|know|want|need|like|have|had|will|would|should|could)\b/i,
            exclamation: /\b(wow|great|amazing|wonderful|terrible|awful|fantastic|incredible|unbelievable)\b/i
        };
        this.contextBuffer = '';
    }
    
    addSmartPunctuation(text, confidence) {
        if (!text || confidence < 0.6) return text;
        
        let enhanced = text;
        
        // Smart capitalization
        if (this.contextBuffer === '' || this.contextBuffer.endsWith('.') || this.contextBuffer.endsWith('!') || this.contextBuffer.endsWith('?')) {
            enhanced = enhanced.charAt(0).toUpperCase() + enhanced.slice(1);
        }
        
        // Add ending punctuation based on context
        if (!enhanced.match(/[.!?]$/)) {
            if (this.patterns.question.test(enhanced)) {
                enhanced += '?';
            } else if (this.patterns.exclamation.test(enhanced)) {
                enhanced += '!';
            } else if (this.patterns.statement.test(enhanced)) {
                enhanced += '.';
            }
        }
        
        this.contextBuffer = enhanced;
        return enhanced;
    }
    
    formatOpening(text) {
        return text.charAt(0).toUpperCase() + text.slice(1);
    }
    
    reset() {
        this.contextBuffer = '';
    }
}

class ContextualMemory {
    constructor() {
        this.history = [];
        this.topics = new Set();
        this.speakerPatterns = [];
        this.maxHistory = 50;
    }
    
    processText(newText, existingText) {
        // Store context
        this.history.push({
            text: newText,
            timestamp: Date.now(),
            context: existingText
        });
        
        // Trim history
        if (this.history.length > this.maxHistory) {
            this.history = this.history.slice(-this.maxHistory);
        }
        
        // Extract topics and patterns
        this.extractTopics(newText);
        
        // Return contextually enhanced text
        return this.applyContextualEnhancements(newText, existingText);
    }
    
    extractTopics(text) {
        const words = text.toLowerCase().split(/\s+/);
        const significantWords = words.filter(word => 
            word.length > 3 && 
            !['that', 'this', 'they', 'them', 'with', 'have', 'been', 'will', 'would', 'could', 'should'].includes(word)
        );
        significantWords.forEach(word => this.topics.add(word));
    }
    
    applyContextualEnhancements(newText, existingText) {
        // Apply topic-based corrections
        let enhanced = newText;
        
        // Context-aware word corrections
        if (existingText.includes('meeting') && enhanced.includes('minute')) {
            enhanced = enhanced.replace(/minute/g, 'minutes');
        }
        
        return enhanced;
    }
    
    reset() {
        this.history = [];
        this.topics.clear();
        this.speakerPatterns = [];
    }
}

class AdaptiveQuality {
    constructor() {
        this.errorHistory = [];
        this.successRate = 1.0;
        this.adaptiveSettings = {
            chunkSize: 4000,
            confidenceThreshold: 0.3,
            retryAttempts: 3
        };
    }
    
    handleProcessingError(error, audioBlob) {
        this.errorHistory.push({
            error: error.message,
            timestamp: Date.now(),
            audioSize: audioBlob ? audioBlob.size : 0
        });
        
        // Calculate success rate
        const recentErrors = this.errorHistory.filter(e => Date.now() - e.timestamp < 60000);
        this.successRate = Math.max(0.1, 1.0 - (recentErrors.length / 10));
        
        // Adaptive recovery strategy
        if (error.message.includes('network') || error.message.includes('timeout')) {
            return {
                shouldRetry: true,
                strategy: 'network_retry',
                retryDelay: Math.min(1000 * Math.pow(2, recentErrors.length), 8000)
            };
        }
        
        if (error.message.includes('audio') && audioBlob && audioBlob.size < 1000) {
            return {
                shouldRetry: false,
                strategy: 'skip_small_chunk'
            };
        }
        
        return {
            shouldRetry: recentErrors.length < this.adaptiveSettings.retryAttempts,
            strategy: 'general_retry',
            retryDelay: 2000
        };
    }
    
    getQualityMetrics() {
        return {
            successRate: this.successRate,
            errorCount: this.errorHistory.length,
            adaptiveScore: this.successRate * 100
        };
    }
}

class StreamingOptimizer {
    constructor() {
        this.performanceHistory = [];
        this.optimalChunkSize = 4000;
        this.networkQuality = 1.0;
    }
    
    calculateOptimalChunkSize() {
        // Adaptive based on performance
        if (this.performanceHistory.length === 0) {
            return this.optimalChunkSize;
        }
        
        const avgLatency = this.performanceHistory.reduce((sum, p) => sum + p.latency, 0) / this.performanceHistory.length;
        
        // Adjust chunk size based on latency
        if (avgLatency > 3000) {
            this.optimalChunkSize = Math.max(2000, this.optimalChunkSize - 500);
        } else if (avgLatency < 1000) {
            this.optimalChunkSize = Math.min(6000, this.optimalChunkSize + 500);
        }
        
        return this.optimalChunkSize;
    }
    
    recordPerformance(latency, success) {
        this.performanceHistory.push({
            latency,
            success,
            timestamp: Date.now()
        });
        
        // Keep only recent performance data
        if (this.performanceHistory.length > 20) {
            this.performanceHistory = this.performanceHistory.slice(-20);
        }
    }
}

// Advanced methods for transcription class
window.MinaAIEnhancements = {
    calculateSemanticSimilarity: function(text1, text2) {
        if (!text1 || !text2) return 0;
        
        const words1 = new Set(text1.toLowerCase().split(/\s+/));
        const words2 = new Set(text2.toLowerCase().split(/\s+/));
        
        const intersection = new Set([...words1].filter(x => words2.has(x)));
        const union = new Set([...words1, ...words2]);
        
        return intersection.size / union.size;
    },
    
    buildIntelligentContinuation: function(existing, newText) {
        // Smart text continuation with overlap detection
        const existingWords = existing.toLowerCase().split(/\s+/);
        const newWords = newText.toLowerCase().split(/\s+/);
        
        // Find overlap
        let overlap = 0;
        for (let i = 1; i <= Math.min(3, existingWords.length, newWords.length); i++) {
            const existingEnd = existingWords.slice(-i).join(' ');
            const newStart = newWords.slice(0, i).join(' ');
            if (existingEnd === newStart) {
                overlap = i;
            }
        }
        
        if (overlap > 0) {
            const remainingNew = newWords.slice(overlap).join(' ');
            return existing + (remainingNew ? ' ' + remainingNew : '');
        } else {
            const needsSpace = !existing.endsWith(' ') && !existing.endsWith('.') && !existing.endsWith('!') && !existing.endsWith('?');
            return existing + (needsSpace ? ' ' : '') + newText;
        }
    },
    
    analyzeTranscriptQuality: function(cumulativeText, confidenceHistory) {
        const words = cumulativeText.split(/\s+/).filter(word => word.length > 0);
        const sentences = cumulativeText.split(/[.!?]+/).filter(s => s.trim().length > 0);
        
        const avgWordsPerSentence = sentences.length > 0 ? words.length / sentences.length : 0;
        const hasProperPunctuation = /[.!?]$/.test(cumulativeText.trim());
        
        let qualityScore = 0.5; // Base score
        
        // Quality factors
        if (avgWordsPerSentence >= 3) qualityScore += 0.2;
        if (hasProperPunctuation) qualityScore += 0.1;
        if (words.length >= 5) qualityScore += 0.1;
        if (confidenceHistory && confidenceHistory.length > 0) {
            const avgConfidence = confidenceHistory.reduce((sum, c) => sum + c, 0) / confidenceHistory.length;
            qualityScore += (avgConfidence - 0.5) * 0.2;
        }
        
        return {
            wordCount: words.length,
            sentenceCount: sentences.length,
            avgWordsPerSentence,
            qualityScore: Math.min(1.0, qualityScore),
            hasProperPunctuation
        };
    }
};

console.log('🚀 Advanced AI Components loaded successfully!');

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
