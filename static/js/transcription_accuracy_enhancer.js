/**
 * TRANSCRIPTION ACCURACY ENHANCER
 * Advanced post-processing for maximum text accuracy and completeness
 */

class TranscriptionAccuracyEnhancer {
    constructor() {
        this.contextBuffer = [];
        this.wordConfidenceThreshold = 0.7;
        this.sentenceBuffer = '';
        this.languageModel = null;
        this.commonCorrections = new Map();
        this.setupCommonCorrections();
        this.confidenceHistory = [];
    }
    
    setupCommonCorrections() {
        // Common speech-to-text corrections
        this.commonCorrections.set('there', ['their', 'they\'re']);
        this.commonCorrections.set('your', ['you\'re']);
        this.commonCorrections.set('its', ['it\'s']);
        this.commonCorrections.set('to', ['too', 'two']);
        this.commonCorrections.set('by', ['bye', 'buy']);
        this.commonCorrections.set('right', ['write', 'rite']);
        this.commonCorrections.set('no', ['know']);
        this.commonCorrections.set('for', ['four']);
        this.commonCorrections.set('one', ['won']);
        this.commonCorrections.set('sea', ['see']);
        this.commonCorrections.set('meat', ['meet']);
        this.commonCorrections.set('peace', ['piece']);
    }
    
    enhanceTranscription(rawResult) {
        console.log('🔍 Enhancing transcription:', rawResult.text);
        
        if (!rawResult.text || !rawResult.text.trim()) {
            return rawResult;
        }
        
        let enhancedText = rawResult.text;
        let enhancedConfidence = rawResult.confidence || 0.9;
        
        // Step 1: Context-aware corrections
        enhancedText = this.applyContextCorrections(enhancedText);
        
        // Step 2: Grammar and punctuation improvements
        enhancedText = this.improveGrammarAndPunctuation(enhancedText);
        
        // Step 3: Word-level confidence analysis
        const wordAnalysis = this.analyzeWordConfidence(enhancedText, rawResult.confidence);
        
        // Step 4: Sentence completion
        enhancedText = this.completeSentence(enhancedText, rawResult.is_final);
        
        // Step 5: Final quality assessment
        enhancedConfidence = this.calculateEnhancedConfidence(enhancedText, rawResult.confidence, wordAnalysis);
        
        const enhancedResult = {
            ...rawResult,
            text: enhancedText,
            confidence: enhancedConfidence,
            original_text: rawResult.text,
            enhancement_applied: true,
            word_analysis: wordAnalysis,
            quality_score: this.calculateQualityScore(enhancedText, enhancedConfidence)
        };
        
        // Update context buffer
        this.updateContextBuffer(enhancedResult);
        
        console.log(`✅ Enhanced: "${rawResult.text}" → "${enhancedText}" (${Math.round(enhancedConfidence * 100)}%)`);
        
        return enhancedResult;
    }
    
    applyContextCorrections(text) {
        // Use context from previous transcriptions
        let correctedText = text;
        
        // Apply common corrections based on context
        const words = text.split(' ');
        const correctedWords = words.map((word, index) => {
            const cleanWord = word.toLowerCase().replace(/[.,!?]/g, '');
            
            if (this.commonCorrections.has(cleanWord)) {
                const alternatives = this.commonCorrections.get(cleanWord);
                const bestAlternative = this.selectBestAlternative(cleanWord, alternatives, words, index);
                
                if (bestAlternative) {
                    return word.replace(new RegExp(cleanWord, 'i'), bestAlternative);
                }
            }
            
            return word;
        });
        
        return correctedWords.join(' ');
    }
    
    selectBestAlternative(word, alternatives, words, index) {
        // Simple context-based selection
        const prevWord = index > 0 ? words[index - 1].toLowerCase() : '';
        const nextWord = index < words.length - 1 ? words[index + 1].toLowerCase() : '';
        
        // Basic rules for common corrections
        if (word === 'to' && (nextWord === 'much' || nextWord === 'many')) {
            return 'too';
        }
        
        if (word === 'your' && (nextWord === 'going' || nextWord === 'welcome')) {
            return 'you\'re';
        }
        
        if (word === 'there' && (prevWord === 'over' || nextWord === 'is' || nextWord === 'are')) {
            return 'their';
        }
        
        // If no context match, keep original
        return null;
    }
    
    improveGrammarAndPunctuation(text) {
        let improvedText = text;
        
        // Add periods at sentence endings
        improvedText = improvedText.replace(/\b(yes|no|okay|alright|sure)\b$/i, '$1.');
        
        // Fix common punctuation issues
        improvedText = improvedText.replace(/\s+([.,!?])/g, '$1');
        improvedText = improvedText.replace(/([.,!?])\s*([a-z])/g, '$1 $2');
        
        // Capitalize sentence beginnings
        improvedText = improvedText.replace(/(^|[.!?]\s+)([a-z])/g, (match, p1, p2) => {
            return p1 + p2.toUpperCase();
        });
        
        // Fix common speech patterns
        improvedText = improvedText.replace(/\buh\b/gi, '');
        improvedText = improvedText.replace(/\bum\b/gi, '');
        improvedText = improvedText.replace(/\s+/g, ' ');
        improvedText = improvedText.trim();
        
        return improvedText;
    }
    
    analyzeWordConfidence(text, overallConfidence) {
        const words = text.split(' ');
        const analysis = {
            totalWords: words.length,
            highConfidenceWords: 0,
            mediumConfidenceWords: 0,
            lowConfidenceWords: 0,
            suspiciousWords: []
        };
        
        words.forEach((word, index) => {
            const wordConfidence = this.estimateWordConfidence(word, overallConfidence);
            
            if (wordConfidence > 0.8) {
                analysis.highConfidenceWords++;
            } else if (wordConfidence > 0.6) {
                analysis.mediumConfidenceWords++;
            } else {
                analysis.lowConfidenceWords++;
                analysis.suspiciousWords.push({ word, index, confidence: wordConfidence });
            }
        });
        
        return analysis;
    }
    
    estimateWordConfidence(word, baseConfidence) {
        // Estimate individual word confidence based on various factors
        let confidence = baseConfidence;
        
        // Length factor - very short words often misrecognized
        if (word.length <= 2) {
            confidence *= 0.8;
        }
        
        // Common words are more reliable
        const commonWords = ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'];
        
        if (commonWords.includes(word.toLowerCase())) {
            confidence *= 1.1;
        }
        
        // Numbers and digits are typically accurate
        if (/\d/.test(word)) {
            confidence *= 1.2;
        }
        
        // Proper nouns (capitalized) can be less reliable
        if (/^[A-Z][a-z]+$/.test(word)) {
            confidence *= 0.9;
        }
        
        return Math.min(confidence, 1.0);
    }
    
    completeSentence(text, isFinal) {
        // Add to sentence buffer for incomplete sentences
        this.sentenceBuffer += text + ' ';
        
        if (isFinal) {
            const completedSentence = this.finalizeSentence(this.sentenceBuffer.trim());
            this.sentenceBuffer = '';
            return completedSentence;
        }
        
        return text;
    }
    
    finalizeSentence(sentence) {
        // Ensure sentence has proper ending punctuation
        if (sentence && !sentence.match(/[.!?]$/)) {
            // Determine appropriate ending based on content
            if (sentence.toLowerCase().includes('what') || 
                sentence.toLowerCase().includes('who') || 
                sentence.toLowerCase().includes('when') || 
                sentence.toLowerCase().includes('where') || 
                sentence.toLowerCase().includes('how')) {
                sentence += '?';
            } else if (sentence.toLowerCase().includes('!') || 
                      sentence.toLowerCase().includes('wow') || 
                      sentence.toLowerCase().includes('amazing')) {
                sentence += '!';
            } else {
                sentence += '.';
            }
        }
        
        return sentence;
    }
    
    calculateEnhancedConfidence(text, originalConfidence, wordAnalysis) {
        let enhancedConfidence = originalConfidence;
        
        // Boost confidence for well-formed sentences
        if (text.match(/^[A-Z].*[.!?]$/)) {
            enhancedConfidence *= 1.1;
        }
        
        // Reduce confidence if many suspicious words
        const suspiciousRatio = wordAnalysis.suspiciousWords.length / wordAnalysis.totalWords;
        if (suspiciousRatio > 0.3) {
            enhancedConfidence *= 0.9;
        }
        
        // Boost confidence for high-confidence words
        const highConfidenceRatio = wordAnalysis.highConfidenceWords / wordAnalysis.totalWords;
        enhancedConfidence *= (0.8 + 0.4 * highConfidenceRatio);
        
        return Math.min(Math.max(enhancedConfidence, 0.1), 1.0);
    }
    
    calculateQualityScore(text, confidence) {
        // Comprehensive quality assessment
        let score = 0;
        
        // Length factor (reasonable sentences score higher)
        const wordCount = text.split(' ').length;
        const lengthScore = Math.min(wordCount / 10, 1.0) * 0.2;
        
        // Grammar score (proper capitalization and punctuation)
        const grammarScore = this.assessGrammarQuality(text) * 0.2;
        
        // Confidence score
        const confidenceScore = confidence * 0.4;
        
        // Completeness score (complete sentences)
        const completenessScore = text.match(/[.!?]$/) ? 0.2 : 0.1;
        
        score = lengthScore + grammarScore + confidenceScore + completenessScore;
        
        return Math.round(score * 100);
    }
    
    assessGrammarQuality(text) {
        let score = 0.5; // Base score
        
        // Check for proper capitalization
        if (/^[A-Z]/.test(text)) score += 0.2;
        
        // Check for proper punctuation
        if (/[.!?]$/.test(text)) score += 0.2;
        
        // Check for reasonable word spacing
        if (!/\s{2,}/.test(text)) score += 0.1;
        
        return Math.min(score, 1.0);
    }
    
    updateContextBuffer(result) {
        this.contextBuffer.push({
            text: result.text,
            confidence: result.confidence,
            timestamp: Date.now()
        });
        
        // Keep only recent context (last 10 results)
        if (this.contextBuffer.length > 10) {
            this.contextBuffer.shift();
        }
        
        // Update confidence history
        this.confidenceHistory.push(result.confidence);
        if (this.confidenceHistory.length > 20) {
            this.confidenceHistory.shift();
        }
    }
    
    getContextSummary() {
        return {
            recentTranscriptions: this.contextBuffer.slice(-5),
            averageConfidence: this.confidenceHistory.reduce((a, b) => a + b, 0) / this.confidenceHistory.length,
            totalWords: this.contextBuffer.reduce((total, item) => total + item.text.split(' ').length, 0)
        };
    }
    
    reset() {
        this.contextBuffer = [];
        this.sentenceBuffer = '';
        this.confidenceHistory = [];
        console.log('🔄 Transcription accuracy enhancer reset');
    }
}

// Export for global use
window.TranscriptionAccuracyEnhancer = TranscriptionAccuracyEnhancer;

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
