/**
 * ADAPTIVE ML CORRECTION ENGINE
 * Advanced machine learning-based text correction and prediction
 */

class AdaptiveMLCorrectionEngine {
    constructor() {
        this.isActive = false;
        this.learningModel = {
            wordPairs: new Map(),
            contextPatterns: new Map(),
            userVocabulary: new Set(),
            correctionHistory: [],
            confidenceThresholds: new Map()
        };
        
        this.predictionEngine = {
            ngramModel: new Map(),
            wordFrequency: new Map(),
            contextPredictions: new Map(),
            sentencePatterns: new Map()
        };
        
        this.adaptiveSettings = {
            learningRate: 0.1,
            predictionDepth: 3,
            contextWindow: 5,
            confidenceThreshold: 0.75,
            adaptationSpeed: 'medium'
        };
        
        this.performanceMetrics = {
            correctionsApplied: 0,
            predictionAccuracy: 0,
            learningEfficiency: 0,
            adaptationSuccess: 0
        };
        
        this.initializeBaseLexicon();
    }
    
    initialize() {
        console.log('🧠 Initializing Adaptive ML Correction Engine');
        
        this.loadUserPreferences();
        this.buildInitialModels();
        this.setupContinuousLearning();
        this.isActive = true;
        
        console.log('✅ ML correction engine active');
        return true;
    }
    
    initializeBaseLexicon() {
        // Common word corrections and patterns
        const commonCorrections = [
            ['gonna', 'going to'], ['wanna', 'want to'], ['gotta', 'got to'],
            ['shoulda', 'should have'], ['coulda', 'could have'], ['woulda', 'would have'],
            ['cant', "can't"], ['dont', "don't"], ['wont', "won't"],
            ['im', "I'm"], ['youre', "you're"], ['theyre', "they're"],
            ['its', "it's"], ['hes', "he's"], ['shes', "she's"],
            ['whats', "what's"], ['thats', "that's"], ['wheres', "where's"]
        ];
        
        commonCorrections.forEach(([incorrect, correct]) => {
            this.learningModel.wordPairs.set(incorrect.toLowerCase(), correct);
        });
        
        // Technical vocabulary for transcription contexts
        const techVocab = [
            'transcription', 'accuracy', 'latency', 'optimization', 'enhancement',
            'algorithm', 'processing', 'bandwidth', 'throughput', 'performance',
            'implementation', 'configuration', 'parameters', 'metrics', 'analytics'
        ];
        
        techVocab.forEach(word => {
            this.learningModel.userVocabulary.add(word.toLowerCase());
            this.predictionEngine.wordFrequency.set(word.toLowerCase(), 1.0);
        });
    }
    
    loadUserPreferences() {
        // Load stored learning data from localStorage
        try {
            const stored = localStorage.getItem('mina_ml_corrections');
            if (stored) {
                const data = JSON.parse(stored);
                
                // Restore word pairs
                if (data.wordPairs) {
                    Object.entries(data.wordPairs).forEach(([key, value]) => {
                        this.learningModel.wordPairs.set(key, value);
                    });
                }
                
                // Restore vocabulary
                if (data.userVocabulary) {
                    data.userVocabulary.forEach(word => {
                        this.learningModel.userVocabulary.add(word);
                    });
                }
                
                // Restore word frequencies
                if (data.wordFrequency) {
                    Object.entries(data.wordFrequency).forEach(([key, value]) => {
                        this.predictionEngine.wordFrequency.set(key, value);
                    });
                }
                
                console.log('📚 Loaded ML learning data from storage');
            }
        } catch (error) {
            console.warn('⚠️ Could not load ML data:', error);
        }
    }
    
    buildInitialModels() {
        // Build n-gram models for prediction
        this.buildNgramModel();
        
        // Initialize context patterns
        this.initializeContextPatterns();
        
        // Set up confidence thresholds
        this.calibrateConfidenceThresholds();
    }
    
    buildNgramModel() {
        // Build bigram and trigram models from common English patterns
        const commonBigrams = [
            ['i', 'am'], ['you', 'are'], ['he', 'is'], ['she', 'is'], ['it', 'is'],
            ['we', 'are'], ['they', 'are'], ['i', 'have'], ['you', 'have'],
            ['going', 'to'], ['want', 'to'], ['need', 'to'], ['have', 'to'],
            ['like', 'to'], ['used', 'to'], ['able', 'to'], ['try', 'to']
        ];
        
        commonBigrams.forEach(([first, second]) => {
            const key = `${first}|${second}`;
            this.predictionEngine.ngramModel.set(key, 1.0);
        });
        
        const commonTrigrams = [
            ['i', 'am', 'going'], ['you', 'are', 'going'], ['i', 'want', 'to'],
            ['i', 'need', 'to'], ['i', 'have', 'to'], ['we', 'need', 'to'],
            ['going', 'to', 'be'], ['want', 'to', 'be'], ['have', 'to', 'be']
        ];
        
        commonTrigrams.forEach(([first, second, third]) => {
            const key = `${first}|${second}|${third}`;
            this.predictionEngine.ngramModel.set(key, 1.5);
        });
    }
    
    initializeContextPatterns() {
        // Common sentence patterns and structures
        const patterns = [
            { pattern: /^(what|where|when|who|how)/, completion: '?' },
            { pattern: /^(yes|no|okay|sure|absolutely)$/, completion: '.' },
            { pattern: /(thank\s+you|thanks)/, completion: '.' },
            { pattern: /(please|could\s+you)/, completion: '?' },
            { pattern: /(i\s+think|i\s+believe)/, followUp: ['that', 'we', 'it'] }
        ];
        
        patterns.forEach((pattern, index) => {
            this.learningModel.contextPatterns.set(`pattern_${index}`, pattern);
        });
    }
    
    calibrateConfidenceThresholds() {
        // Set confidence thresholds for different types of corrections
        this.learningModel.confidenceThresholds.set('word_replacement', 0.8);
        this.learningModel.confidenceThresholds.set('punctuation', 0.7);
        this.learningModel.confidenceThresholds.set('capitalization', 0.9);
        this.learningModel.confidenceThresholds.set('grammar', 0.75);
        this.learningModel.confidenceThresholds.set('prediction', 0.6);
    }
    
    setupContinuousLearning() {
        // Learn from each transcription result
        window.addEventListener('transcriptionResult', (event) => {
            if (this.isActive) {
                this.learnFromTranscription(event.detail);
            }
        });
        
        // Periodic model optimization
        this.optimizationInterval = setInterval(() => {
            this.optimizeModels();
            this.saveUserPreferences();
        }, 30000); // Every 30 seconds
    }
    
    processTranscription(transcriptionResult) {
        if (!this.isActive) return transcriptionResult;
        
        console.log('🧠 Applying ML corrections to:', transcriptionResult.text);
        
        let correctedText = transcriptionResult.text;
        let confidenceAdjustment = 0;
        const appliedCorrections = [];
        
        // Step 1: Word-level corrections
        const wordCorrections = this.applyWordCorrections(correctedText);
        correctedText = wordCorrections.text;
        appliedCorrections.push(...wordCorrections.corrections);
        
        // Step 2: Context-based improvements
        const contextCorrections = this.applyContextCorrections(correctedText);
        correctedText = contextCorrections.text;
        appliedCorrections.push(...contextCorrections.corrections);
        
        // Step 3: Predictive text completion
        const predictions = this.applyPredictiveCorrections(correctedText, transcriptionResult.is_final);
        correctedText = predictions.text;
        appliedCorrections.push(...predictions.corrections);
        
        // Step 4: Grammar and punctuation enhancement
        const grammarCorrections = this.applyGrammarCorrections(correctedText);
        correctedText = grammarCorrections.text;
        appliedCorrections.push(...grammarCorrections.corrections);
        
        // Calculate confidence adjustment
        confidenceAdjustment = this.calculateConfidenceAdjustment(appliedCorrections, transcriptionResult.confidence);
        
        // Create enhanced result
        const enhancedResult = {
            ...transcriptionResult,
            text: correctedText,
            original_text: transcriptionResult.text,
            confidence: Math.min(1.0, (transcriptionResult.confidence || 0.9) + confidenceAdjustment),
            ml_corrections: appliedCorrections,
            ml_confidence_boost: confidenceAdjustment,
            ml_processed: true
        };
        
        // Learn from this correction
        this.learnFromCorrection(transcriptionResult, enhancedResult);
        
        // Update metrics
        this.updatePerformanceMetrics(appliedCorrections);
        
        console.log(`🎯 ML enhanced: "${transcriptionResult.text}" → "${correctedText}" (+${appliedCorrections.length} corrections)`);
        
        return enhancedResult;
    }
    
    applyWordCorrections(text) {
        const words = text.split(/\s+/);
        const corrections = [];
        
        const correctedWords = words.map((word, index) => {
            const cleanWord = word.toLowerCase().replace(/[.,!?]/g, '');
            
            // Check for direct word replacements
            if (this.learningModel.wordPairs.has(cleanWord)) {
                const replacement = this.learningModel.wordPairs.get(cleanWord);
                corrections.push({
                    type: 'word_replacement',
                    original: word,
                    corrected: replacement,
                    position: index,
                    confidence: 0.9
                });
                return word.replace(new RegExp(cleanWord, 'i'), replacement);
            }
            
            // Check for vocabulary suggestions
            const suggestion = this.findVocabularySuggestion(cleanWord);
            if (suggestion && suggestion !== cleanWord) {
                corrections.push({
                    type: 'vocabulary_suggestion',
                    original: word,
                    corrected: suggestion,
                    position: index,
                    confidence: 0.7
                });
                return word.replace(new RegExp(cleanWord, 'i'), suggestion);
            }
            
            return word;
        });
        
        return {
            text: correctedWords.join(' '),
            corrections: corrections
        };
    }
    
    findVocabularySuggestion(word) {
        // Find closest match in user vocabulary using edit distance
        let bestMatch = word;
        let minDistance = Infinity;
        
        for (const vocabWord of this.learningModel.userVocabulary) {
            const distance = this.calculateEditDistance(word, vocabWord);
            if (distance < minDistance && distance <= 2 && distance > 0) {
                minDistance = distance;
                bestMatch = vocabWord;
            }
        }
        
        return minDistance <= 2 ? bestMatch : word;
    }
    
    calculateEditDistance(str1, str2) {
        // Levenshtein distance algorithm
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
    
    applyContextCorrections(text) {
        const corrections = [];
        let correctedText = text;
        
        // Apply context patterns
        for (const [patternId, pattern] of this.learningModel.contextPatterns) {
            if (pattern.pattern.test(text)) {
                if (pattern.completion && !text.match(/[.!?]$/)) {
                    correctedText += pattern.completion;
                    corrections.push({
                        type: 'punctuation',
                        original: text,
                        corrected: correctedText,
                        reason: `Applied pattern: ${patternId}`,
                        confidence: 0.8
                    });
                }
            }
        }
        
        return {
            text: correctedText,
            corrections: corrections
        };
    }
    
    applyPredictiveCorrections(text, isFinal) {
        const corrections = [];
        let correctedText = text;
        
        if (!isFinal) {
            // For interim results, predict likely next words
            const words = text.trim().split(/\s+/);
            const lastWords = words.slice(-2); // Last 2 words for bigram prediction
            
            if (lastWords.length >= 2) {
                const bigramKey = `${lastWords[0].toLowerCase()}|${lastWords[1].toLowerCase()}`;
                const prediction = this.predictNextWord(bigramKey);
                
                if (prediction) {
                    corrections.push({
                        type: 'prediction',
                        original: text,
                        suggestion: prediction,
                        confidence: 0.6
                    });
                }
            }
        }
        
        return {
            text: correctedText,
            corrections: corrections
        };
    }
    
    predictNextWord(bigramKey) {
        // Find potential next words from n-gram model
        const candidates = [];
        
        for (const [ngramKey, frequency] of this.predictionEngine.ngramModel) {
            if (ngramKey.startsWith(bigramKey + '|')) {
                const nextWord = ngramKey.split('|').pop();
                candidates.push({ word: nextWord, frequency: frequency });
            }
        }
        
        // Return most frequent candidate
        if (candidates.length > 0) {
            candidates.sort((a, b) => b.frequency - a.frequency);
            return candidates[0].word;
        }
        
        return null;
    }
    
    applyGrammarCorrections(text) {
        const corrections = [];
        let correctedText = text;
        
        // Common grammar corrections
        const grammarRules = [
            { pattern: /\bi\b(?!\s+am|\s+have|\s+will)/gi, replacement: 'I', type: 'capitalization' },
            { pattern: /\s+([.,!?])/g, replacement: '$1', type: 'spacing' },
            { pattern: /([.,!?])([a-z])/g, replacement: '$1 $2', type: 'spacing' },
            { pattern: /\s{2,}/g, replacement: ' ', type: 'spacing' }
        ];
        
        grammarRules.forEach((rule, index) => {
            const before = correctedText;
            correctedText = correctedText.replace(rule.pattern, rule.replacement);
            
            if (before !== correctedText) {
                corrections.push({
                    type: rule.type,
                    original: before,
                    corrected: correctedText,
                    rule: `grammar_rule_${index}`,
                    confidence: 0.85
                });
            }
        });
        
        return {
            text: correctedText,
            corrections: corrections
        };
    }
    
    calculateConfidenceAdjustment(corrections, originalConfidence) {
        if (corrections.length === 0) return 0;
        
        // Calculate weighted confidence boost based on correction types
        let boost = 0;
        
        corrections.forEach(correction => {
            switch (correction.type) {
                case 'word_replacement':
                    boost += 0.05;
                    break;
                case 'vocabulary_suggestion':
                    boost += 0.03;
                    break;
                case 'punctuation':
                    boost += 0.02;
                    break;
                case 'grammar':
                    boost += 0.04;
                    break;
                case 'capitalization':
                    boost += 0.01;
                    break;
            }
        });
        
        // Diminishing returns for many corrections
        return Math.min(boost, 0.15);
    }
    
    learnFromTranscription(transcriptionData) {
        if (!transcriptionData.text) return;
        
        const words = transcriptionData.text.toLowerCase().split(/\s+/);
        
        // Update word frequencies
        words.forEach(word => {
            const cleanWord = word.replace(/[.,!?]/g, '');
            if (cleanWord.length > 2) {
                const current = this.predictionEngine.wordFrequency.get(cleanWord) || 0;
                this.predictionEngine.wordFrequency.set(cleanWord, current + 0.1);
                this.learningModel.userVocabulary.add(cleanWord);
            }
        });
        
        // Update n-gram model
        for (let i = 0; i < words.length - 1; i++) {
            const bigram = `${words[i]}|${words[i + 1]}`;
            const current = this.predictionEngine.ngramModel.get(bigram) || 0;
            this.predictionEngine.ngramModel.set(bigram, current + 0.1);
        }
        
        // Learn trigrams
        for (let i = 0; i < words.length - 2; i++) {
            const trigram = `${words[i]}|${words[i + 1]}|${words[i + 2]}`;
            const current = this.predictionEngine.ngramModel.get(trigram) || 0;
            this.predictionEngine.ngramModel.set(trigram, current + 0.1);
        }
    }
    
    learnFromCorrection(original, corrected) {
        // Learn from successful corrections
        if (original.text !== corrected.text) {
            this.learningModel.correctionHistory.push({
                timestamp: Date.now(),
                original: original.text,
                corrected: corrected.text,
                corrections: corrected.ml_corrections || []
            });
            
            // Keep history bounded
            if (this.learningModel.correctionHistory.length > 100) {
                this.learningModel.correctionHistory.shift();
            }
        }
    }
    
    optimizeModels() {
        // Decay old frequencies to adapt to new patterns
        const decayFactor = 0.99;
        
        for (const [key, value] of this.predictionEngine.wordFrequency) {
            this.predictionEngine.wordFrequency.set(key, value * decayFactor);
        }
        
        for (const [key, value] of this.predictionEngine.ngramModel) {
            this.predictionEngine.ngramModel.set(key, value * decayFactor);
        }
        
        // Remove very low frequency items
        for (const [key, value] of this.predictionEngine.wordFrequency) {
            if (value < 0.01) {
                this.predictionEngine.wordFrequency.delete(key);
            }
        }
        
        for (const [key, value] of this.predictionEngine.ngramModel) {
            if (value < 0.01) {
                this.predictionEngine.ngramModel.delete(key);
            }
        }
    }
    
    updatePerformanceMetrics(corrections) {
        this.performanceMetrics.correctionsApplied += corrections.length;
        
        // Calculate running averages
        const totalSessions = this.learningModel.correctionHistory.length || 1;
        this.performanceMetrics.learningEfficiency = 
            this.performanceMetrics.correctionsApplied / totalSessions;
    }
    
    saveUserPreferences() {
        try {
            const data = {
                wordPairs: Object.fromEntries(this.learningModel.wordPairs),
                userVocabulary: Array.from(this.learningModel.userVocabulary),
                wordFrequency: Object.fromEntries(this.predictionEngine.wordFrequency),
                ngramModel: Object.fromEntries(this.predictionEngine.ngramModel),
                timestamp: Date.now()
            };
            
            localStorage.setItem('mina_ml_corrections', JSON.stringify(data));
        } catch (error) {
            console.warn('⚠️ Could not save ML data:', error);
        }
    }
    
    getPerformanceReport() {
        return {
            ...this.performanceMetrics,
            vocabularySize: this.learningModel.userVocabulary.size,
            ngramPatterns: this.predictionEngine.ngramModel.size,
            correctionHistory: this.learningModel.correctionHistory.length,
            adaptiveSettings: this.adaptiveSettings
        };
    }
    
    stop() {
        this.isActive = false;
        
        if (this.optimizationInterval) {
            clearInterval(this.optimizationInterval);
        }
        
        this.saveUserPreferences();
        console.log('🛑 Adaptive ML correction engine stopped');
    }
}

// Export for global use
window.AdaptiveMLCorrectionEngine = AdaptiveMLCorrectionEngine;