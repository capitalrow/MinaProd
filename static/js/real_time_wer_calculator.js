/**
 * 📊 REAL-TIME WER CALCULATOR
 * Calculates Word Error Rate without reference text using confidence-based estimation
 */

class RealTimeWERCalculator {
    constructor() {
        this.transcriptHistory = [];
        this.confidenceThreshold = 0.7;
        this.maxHistorySize = 50;
        this.werEstimate = 0;
        
        // Patterns that indicate potential errors
        this.errorPatterns = [
            /\b(you|uh|um)\b/gi,           // Common misrecognitions
            /\b(\w+)\s+\1\b/gi,            // Word repetitions
            /\b[a-z]\b/gi,                 // Single letter words (often errors)
            /[^\w\s.,!?]/gi,               // Unusual characters
            /\b\w{1,2}\b.*\b\w{1,2}\b/gi  // Multiple very short words
        ];
        
        // Language model for plausibility checking
        this.commonWords = new Set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i',
            'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        ]);
        
        console.log('📊 Real-time WER Calculator initialized');
    }
    
    /**
     * Calculate WER estimate for a transcript segment
     */
    calculateWEREstimate(transcript, confidence = null, metadata = {}) {
        if (!transcript || typeof transcript !== 'string') {
            return 0;
        }
        
        const segment = {
            text: transcript.trim(),
            confidence: confidence,
            timestamp: Date.now(),
            metadata: metadata
        };
        
        // Add to history
        this.transcriptHistory.push(segment);
        
        // Maintain history size
        if (this.transcriptHistory.length > this.maxHistorySize) {
            this.transcriptHistory.shift();
        }
        
        // Calculate WER estimate
        const werEstimate = this.estimateWER(segment);
        
        // Update running average
        this.updateRunningWER(werEstimate);
        
        console.log(`📊 WER Estimate: ${werEstimate.toFixed(1)}% for "${transcript.substring(0, 30)}..."`);
        
        return werEstimate;
    }
    
    /**
     * Estimate WER using multiple heuristic methods
     */
    estimateWER(segment) {
        const scores = [];
        
        // Method 1: Confidence-based estimation
        scores.push(this.confidenceBasedWER(segment));
        
        // Method 2: Pattern-based error detection
        scores.push(this.patternBasedWER(segment));
        
        // Method 3: Language model plausibility
        scores.push(this.plausibilityBasedWER(segment));
        
        // Method 4: Consistency with recent transcripts
        scores.push(this.consistencyBasedWER(segment));
        
        // Method 5: Length and complexity analysis
        scores.push(this.complexityBasedWER(segment));
        
        // Weighted average of all methods
        const weights = [0.3, 0.2, 0.2, 0.15, 0.15];
        const weightedScore = scores.reduce((sum, score, i) => sum + (score * weights[i]), 0);
        
        return Math.max(0, Math.min(100, weightedScore));
    }
    
    /**
     * Method 1: Confidence-based WER estimation
     */
    confidenceBasedWER(segment) {
        if (!segment.confidence) {
            return 15; // Default moderate error rate
        }
        
        // Convert confidence to error rate
        // High confidence (>0.9) -> Low WER (<5%)
        // Medium confidence (0.7-0.9) -> Medium WER (5-15%)
        // Low confidence (<0.7) -> High WER (>15%)
        
        if (segment.confidence > 0.9) {
            return 2 + (1 - segment.confidence) * 30; // 2-5%
        } else if (segment.confidence > 0.7) {
            return 5 + (0.9 - segment.confidence) * 50; // 5-15%
        } else {
            return 15 + (0.7 - segment.confidence) * 50; // 15-50%
        }
    }
    
    /**
     * Method 2: Pattern-based error detection
     */
    patternBasedWER(segment) {
        const text = segment.text.toLowerCase();
        let errorIndicators = 0;
        let totalWords = text.split(/\\s+/).length;
        
        if (totalWords === 0) return 100; // Empty transcript
        
        // Check for error patterns
        for (const pattern of this.errorPatterns) {\n            const matches = text.match(pattern);\n            if (matches) {\n                errorIndicators += matches.length;\n            }\n        }\n        \n        // Check for very short or very long words (often misrecognitions)\n        const words = text.split(/\\s+/);\n        const unusualWords = words.filter(word => {\n            const cleanWord = word.replace(/[^a-z]/g, '');\n            return cleanWord.length === 1 || cleanWord.length > 12;\n        });\n        \n        errorIndicators += unusualWords.length;\n        \n        // Convert to percentage\n        const errorRate = (errorIndicators / totalWords) * 100;\n        return Math.min(50, errorRate); // Cap at 50%\n    }\n    \n    /**\n     * Method 3: Language model plausibility\n     */\n    plausibilityBasedWER(segment) {\n        const text = segment.text.toLowerCase();\n        const words = text.split(/\\s+/).filter(word => word.length > 0);\n        \n        if (words.length === 0) return 100;\n        \n        let implausibleWords = 0;\n        \n        for (const word of words) {\n            const cleanWord = word.replace(/[^a-z]/g, '');\n            \n            // Check if word is in common words or looks like a real word\n            if (!this.commonWords.has(cleanWord)) {\n                // Basic heuristics for real words\n                if (!this.looksLikeRealWord(cleanWord)) {\n                    implausibleWords++;\n                }\n            }\n        }\n        \n        const implausibilityRate = (implausibleWords / words.length) * 100;\n        return Math.min(40, implausibilityRate); // Cap at 40%\n    }\n    \n    /**\n     * Check if a word looks like a real English word\n     */\n    looksLikeRealWord(word) {\n        if (word.length < 2) return false;\n        \n        // Check for reasonable vowel/consonant distribution\n        const vowels = (word.match(/[aeiou]/g) || []).length;\n        const consonants = word.length - vowels;\n        \n        if (vowels === 0 && word.length > 3) return false; // No vowels in long word\n        if (vowels / word.length > 0.8) return false; // Too many vowels\n        \n        // Check for repeated character patterns that are unlikely\n        if (/([a-z])\\1{3,}/.test(word)) return false; // 4+ repeated chars\n        \n        return true;\n    }\n    \n    /**\n     * Method 4: Consistency with recent transcripts\n     */\n    consistencyBasedWER(segment) {\n        if (this.transcriptHistory.length < 3) {\n            return 10; // Default when insufficient history\n        }\n        \n        const recentSegments = this.transcriptHistory.slice(-5); // Last 5 segments\n        let inconsistencyScore = 0;\n        \n        // Check for sudden changes in transcript characteristics\n        const currentWords = segment.text.split(/\\s+/).length;\n        const avgRecentWords = recentSegments.reduce((sum, seg) => {\n            return sum + seg.text.split(/\\s+/).length;\n        }, 0) / recentSegments.length;\n        \n        // Sudden length changes might indicate errors\n        if (Math.abs(currentWords - avgRecentWords) > avgRecentWords * 0.5) {\n            inconsistencyScore += 10;\n        }\n        \n        // Check for style consistency (capitalization, punctuation)\n        const hasCapitalization = /[A-Z]/.test(segment.text);\n        const hasPunctuation = /[.,!?]/.test(segment.text);\n        \n        const recentCapitalization = recentSegments.filter(seg => /[A-Z]/.test(seg.text)).length / recentSegments.length;\n        const recentPunctuation = recentSegments.filter(seg => /[.,!?]/.test(seg.text)).length / recentSegments.length;\n        \n        if ((hasCapitalization && recentCapitalization < 0.3) || (!hasCapitalization && recentCapitalization > 0.7)) {\n            inconsistencyScore += 5;\n        }\n        \n        if ((hasPunctuation && recentPunctuation < 0.3) || (!hasPunctuation && recentPunctuation > 0.7)) {\n            inconsistencyScore += 5;\n        }\n        \n        return Math.min(25, inconsistencyScore);\n    }\n    \n    /**\n     * Method 5: Complexity and length analysis\n     */\n    complexityBasedWER(segment) {\n        const text = segment.text;\n        const words = text.split(/\\s+/);\n        let complexityScore = 0;\n        \n        // Very short transcripts are often errors or incomplete\n        if (text.length < 3) {\n            complexityScore += 30;\n        } else if (text.length < 10) {\n            complexityScore += 15;\n        }\n        \n        // Single word repetitions often indicate errors\n        if (words.length === 1 && this.transcriptHistory.length > 0) {\n            const lastSegment = this.transcriptHistory[this.transcriptHistory.length - 1];\n            if (lastSegment.text.toLowerCase() === text.toLowerCase()) {\n                complexityScore += 25;\n            }\n        }\n        \n        // Check for unusual character-to-word ratio\n        if (words.length > 0) {\n            const avgWordLength = text.replace(/\\s/g, '').length / words.length;\n            if (avgWordLength < 2 || avgWordLength > 15) {\n                complexityScore += 10;\n            }\n        }\n        \n        return Math.min(40, complexityScore);\n    }\n    \n    /**\n     * Update running WER average\n     */\n    updateRunningWER(newWER) {\n        if (this.transcriptHistory.length === 1) {\n            this.werEstimate = newWER;\n        } else {\n            // Exponential moving average with alpha = 0.3\n            this.werEstimate = this.werEstimate * 0.7 + newWER * 0.3;\n        }\n    }\n    \n    /**\n     * Get current WER estimate\n     */\n    getCurrentWER() {\n        return Math.round(this.werEstimate * 10) / 10; // Round to 1 decimal\n    }\n    \n    /**\n     * Get detailed WER analysis\n     */\n    getDetailedAnalysis() {\n        if (this.transcriptHistory.length === 0) {\n            return {\n                wer: 0,\n                confidence: 'No data',\n                segments: 0,\n                avgConfidence: 0,\n                qualityIndicators: []\n            };\n        }\n        \n        const recentSegments = this.transcriptHistory.slice(-10);\n        const avgConfidence = recentSegments.reduce((sum, seg) => {\n            return sum + (seg.confidence || 0.5);\n        }, 0) / recentSegments.length;\n        \n        const qualityIndicators = [];\n        \n        if (this.werEstimate <= 5) {\n            qualityIndicators.push('Excellent quality transcription');\n        } else if (this.werEstimate <= 10) {\n            qualityIndicators.push('High quality transcription');\n        } else if (this.werEstimate <= 20) {\n            qualityIndicators.push('Moderate quality - some errors expected');\n        } else {\n            qualityIndicators.push('Lower quality - consider audio improvements');\n        }\n        \n        if (avgConfidence > 0.9) {\n            qualityIndicators.push('High confidence from recognition engine');\n        } else if (avgConfidence < 0.7) {\n            qualityIndicators.push('Low confidence - check audio quality');\n        }\n        \n        return {\n            wer: this.getCurrentWER(),\n            confidence: avgConfidence,\n            segments: this.transcriptHistory.length,\n            avgConfidence: Math.round(avgConfidence * 100),\n            qualityIndicators: qualityIndicators\n        };\n    }\n    \n    /**\n     * Reset WER calculator\n     */\n    reset() {\n        this.transcriptHistory = [];\n        this.werEstimate = 0;\n        console.log('📊 WER Calculator reset');\n    }\n    \n    /**\n     * Export analysis data\n     */\n    exportData() {\n        return {\n            transcriptHistory: this.transcriptHistory,\n            currentWER: this.getCurrentWER(),\n            analysis: this.getDetailedAnalysis(),\n            timestamp: new Date().toISOString()\n        };\n    }\n}\n\n// Initialize global WER calculator\nwindow.realTimeWERCalculator = new RealTimeWERCalculator();\n\nconsole.log('✅ Real-time WER Calculator loaded');"

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
