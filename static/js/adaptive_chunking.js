/**
 * 🎯 ADAPTIVE CHUNKING SYSTEM
 * Dynamically adjusts chunk sizes based on speech patterns and content
 */

class AdaptiveChunking {
    constructor() {
        this.chunkSizeMs = 1000; // Base chunk size in milliseconds
        this.minChunkSize = 500;
        this.maxChunkSize = 3000;
        
        // Adaptive parameters
        this.speechRate = 150; // Words per minute (average)
        this.pauseDetectionThreshold = 0.5; // Seconds of silence
        this.complexityFactor = 1.0;
        
        // Speech pattern analysis
        this.recentSpeechPatterns = [];
        this.patternHistorySize = 10;
        
        // Content analysis
        this.contentComplexity = 0.5; // 0-1 scale
        this.languageComplexity = 0.5;
        
        this.statistics = {
            totalChunks: 0,
            averageChunkSize: 0,
            adaptationEvents: 0,
            performanceGains: 0
        };
        
        console.log('🎯 Adaptive Chunking System initialized');
    }
    
    /**
     * Analyze speech pattern and determine optimal chunk size
     */
    analyzeAndAdaptChunkSize(audioData, speechMetrics = {}) {
        const analysis = this.analyzeSpeechPattern(audioData, speechMetrics);
        const optimalSize = this.calculateOptimalChunkSize(analysis);
        
        // Update chunk size if significantly different
        const sizeDifference = Math.abs(optimalSize - this.chunkSizeMs) / this.chunkSizeMs;
        if (sizeDifference > 0.2) { // 20% threshold for change
            this.adaptChunkSize(optimalSize);
            this.statistics.adaptationEvents++;
        }
        
        this.updateSpeechPatternHistory(analysis);
        this.statistics.totalChunks++;
        
        return {
            recommendedChunkSize: this.chunkSizeMs,
            analysis: analysis,
            adaptationReason: this.getAdaptationReason(analysis)
        };
    }
    
    /**
     * Analyze current speech pattern
     */
    analyzeSpeechPattern(audioData, speechMetrics) {
        const energyProfile = this.calculateEnergyProfile(audioData);
        const speechDensity = this.calculateSpeechDensity(energyProfile);
        const pausePattern = this.detectPausePattern(energyProfile);
        const complexity = this.estimateContentComplexity(speechMetrics);
        
        return {
            speechDensity: speechDensity,
            pauseFrequency: pausePattern.frequency,
            averagePauseLength: pausePattern.averageLength,
            energyVariation: this.calculateEnergyVariation(energyProfile),
            contentComplexity: complexity,
            speechRate: this.estimateSpeechRate(speechMetrics),
            timestamp: Date.now()
        };
    }
    
    /**
     * Calculate energy profile of audio data
     */
    calculateEnergyProfile(audioData) {
        if (!audioData || audioData.length === 0) return [];\n        \n        const windowSize = Math.floor(audioData.length / 20); // 20 windows\n        const energyProfile = [];\n        \n        for (let i = 0; i < audioData.length; i += windowSize) {\n            const window = audioData.slice(i, i + windowSize);\n            const energy = this.calculateRMS(window);\n            energyProfile.push(energy);\n        }\n        \n        return energyProfile;\n    }\n    \n    /**\n     * Calculate RMS energy for a window\n     */\n    calculateRMS(window) {\n        if (window.length === 0) return 0;\n        \n        let sum = 0;\n        for (let i = 0; i < window.length; i++) {\n            sum += window[i] * window[i];\n        }\n        return Math.sqrt(sum / window.length);\n    }\n    \n    /**\n     * Calculate speech density (ratio of speech to silence)\n     */\n    calculateSpeechDensity(energyProfile) {\n        const speechThreshold = 0.02;\n        const speechWindows = energyProfile.filter(energy => energy > speechThreshold).length;\n        return energyProfile.length > 0 ? speechWindows / energyProfile.length : 0;\n    }\n    \n    /**\n     * Detect pause patterns in speech\n     */\n    detectPausePattern(energyProfile) {\n        const silenceThreshold = 0.01;\n        const pauses = [];\n        let pauseStart = -1;\n        \n        for (let i = 0; i < energyProfile.length; i++) {\n            if (energyProfile[i] < silenceThreshold) {\n                if (pauseStart === -1) pauseStart = i;\n            } else {\n                if (pauseStart !== -1) {\n                    pauses.push(i - pauseStart);\n                    pauseStart = -1;\n                }\n            }\n        }\n        \n        return {\n            frequency: pauses.length,\n            averageLength: pauses.length > 0 ? pauses.reduce((sum, len) => sum + len, 0) / pauses.length : 0,\n            totalPauses: pauses.length\n        };\n    }\n    \n    /**\n     * Calculate energy variation (indicator of speech dynamics)\n     */\n    calculateEnergyVariation(energyProfile) {\n        if (energyProfile.length < 2) return 0;\n        \n        const mean = energyProfile.reduce((sum, val) => sum + val, 0) / energyProfile.length;\n        const variance = energyProfile.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / energyProfile.length;\n        \n        return Math.sqrt(variance);\n    }\n    \n    /**\n     * Estimate content complexity based on speech metrics\n     */\n    estimateContentComplexity(speechMetrics) {\n        let complexity = 0.5; // Base complexity\n        \n        // Adjust based on confidence (lower confidence = higher complexity)\n        if (speechMetrics.confidence !== undefined) {\n            complexity += (1 - speechMetrics.confidence) * 0.3;\n        }\n        \n        // Adjust based on processing time\n        if (speechMetrics.processingTime !== undefined) {\n            const normalizedTime = Math.min(1.0, speechMetrics.processingTime / 2000); // Normalize to 2s\n            complexity += normalizedTime * 0.2;\n        }\n        \n        // Adjust based on text length vs audio duration\n        if (speechMetrics.textLength && speechMetrics.audioDuration) {\n            const wordsPerSecond = (speechMetrics.textLength / 5) / (speechMetrics.audioDuration / 1000);\n            if (wordsPerSecond > 3) complexity += 0.2; // Fast speech\n            if (wordsPerSecond < 1) complexity += 0.1; // Slow/careful speech\n        }\n        \n        return Math.min(1.0, Math.max(0.0, complexity));\n    }\n    \n    /**\n     * Estimate speech rate from metrics\n     */\n    estimateSpeechRate(speechMetrics) {\n        if (speechMetrics.textLength && speechMetrics.audioDuration) {\n            const wordsEstimate = speechMetrics.textLength / 5; // ~5 chars per word\n            const durationMinutes = speechMetrics.audioDuration / 60000;\n            return durationMinutes > 0 ? wordsEstimate / durationMinutes : this.speechRate;\n        }\n        return this.speechRate;\n    }\n    \n    /**\n     * Calculate optimal chunk size based on analysis\n     */\n    calculateOptimalChunkSize(analysis) {\n        let optimalSize = this.chunkSizeMs;\n        \n        // Adjust for speech density\n        if (analysis.speechDensity > 0.8) {\n            // High speech density = smaller chunks for better real-time response\n            optimalSize *= 0.8;\n        } else if (analysis.speechDensity < 0.3) {\n            // Low speech density = larger chunks to reduce API calls\n            optimalSize *= 1.3;\n        }\n        \n        // Adjust for pause patterns\n        if (analysis.pauseFrequency > 5) {\n            // Frequent pauses = smaller chunks to capture natural breaks\n            optimalSize *= 0.9;\n        } else if (analysis.pauseFrequency < 2) {\n            // Few pauses = larger chunks for efficiency\n            optimalSize *= 1.2;\n        }\n        \n        // Adjust for content complexity\n        if (analysis.contentComplexity > 0.7) {\n            // High complexity = smaller chunks for better accuracy\n            optimalSize *= 0.85;\n        } else if (analysis.contentComplexity < 0.3) {\n            // Low complexity = larger chunks for efficiency\n            optimalSize *= 1.15;\n        }\n        \n        // Adjust for speech rate\n        if (analysis.speechRate > 180) {\n            // Fast speech = smaller chunks\n            optimalSize *= 0.9;\n        } else if (analysis.speechRate < 120) {\n            // Slow speech = larger chunks\n            optimalSize *= 1.1;\n        }\n        \n        // Apply bounds\n        return Math.max(this.minChunkSize, Math.min(this.maxChunkSize, optimalSize));\n    }\n    \n    /**\n     * Adapt chunk size with smoothing\n     */\n    adaptChunkSize(targetSize) {\n        // Smooth transition to avoid sudden changes\n        const smoothingFactor = 0.3;\n        this.chunkSizeMs = this.chunkSizeMs * (1 - smoothingFactor) + targetSize * smoothingFactor;\n        \n        // Update statistics\n        this.updateAverageChunkSize();\n        \n        console.log(`🎯 Chunk size adapted to ${Math.round(this.chunkSizeMs)}ms`);\n    }\n    \n    /**\n     * Update speech pattern history\n     */\n    updateSpeechPatternHistory(analysis) {\n        this.recentSpeechPatterns.push(analysis);\n        \n        // Keep only recent patterns\n        if (this.recentSpeechPatterns.length > this.patternHistorySize) {\n            this.recentSpeechPatterns.shift();\n        }\n        \n        // Update running averages\n        this.updateRunningAverages();\n    }\n    \n    /**\n     * Update running averages from pattern history\n     */\n    updateRunningAverages() {\n        if (this.recentSpeechPatterns.length === 0) return;\n        \n        const patterns = this.recentSpeechPatterns;\n        this.speechRate = patterns.reduce((sum, p) => sum + p.speechRate, 0) / patterns.length;\n        this.contentComplexity = patterns.reduce((sum, p) => sum + p.contentComplexity, 0) / patterns.length;\n    }\n    \n    /**\n     * Update average chunk size statistic\n     */\n    updateAverageChunkSize() {\n        if (this.statistics.totalChunks === 0) {\n            this.statistics.averageChunkSize = this.chunkSizeMs;\n        } else {\n            const total = this.statistics.averageChunkSize * (this.statistics.totalChunks - 1) + this.chunkSizeMs;\n            this.statistics.averageChunkSize = total / this.statistics.totalChunks;\n        }\n    }\n    \n    /**\n     * Get reason for adaptation\n     */\n    getAdaptationReason(analysis) {\n        const reasons = [];\n        \n        if (analysis.speechDensity > 0.8) reasons.push('high speech density');\n        if (analysis.speechDensity < 0.3) reasons.push('low speech density');\n        if (analysis.contentComplexity > 0.7) reasons.push('high complexity');\n        if (analysis.contentComplexity < 0.3) reasons.push('low complexity');\n        if (analysis.pauseFrequency > 5) reasons.push('frequent pauses');\n        if (analysis.speechRate > 180) reasons.push('fast speech');\n        if (analysis.speechRate < 120) reasons.push('slow speech');\n        \n        return reasons.join(', ') || 'optimization';\n    }\n    \n    /**\n     * Get current chunk size recommendation\n     */\n    getCurrentChunkSize() {\n        return Math.round(this.chunkSizeMs);\n    }\n    \n    /**\n     * Get adaptation statistics\n     */\n    getStatistics() {\n        const recentPatterns = this.recentSpeechPatterns.slice(-5); // Last 5 patterns\n        \n        return {\n            ...this.statistics,\n            currentChunkSize: Math.round(this.chunkSizeMs),\n            averageSpeechRate: Math.round(this.speechRate),\n            averageComplexity: Math.round(this.contentComplexity * 100) / 100,\n            recentAdaptations: recentPatterns.length,\n            adaptationRate: this.statistics.totalChunks > 0 \n                ? (this.statistics.adaptationEvents / this.statistics.totalChunks) * 100 \n                : 0\n        };\n    }\n    \n    /**\n     * Reset adaptation system\n     */\n    reset() {\n        this.chunkSizeMs = 1000;\n        this.recentSpeechPatterns = [];\n        this.speechRate = 150;\n        this.contentComplexity = 0.5;\n        \n        console.log('🎯 Adaptive chunking system reset');\n    }\n    \n    /**\n     * Configure adaptation parameters\n     */\n    configure(options = {}) {\n        if (options.minChunkSize !== undefined) {\n            this.minChunkSize = options.minChunkSize;\n        }\n        if (options.maxChunkSize !== undefined) {\n            this.maxChunkSize = options.maxChunkSize;\n        }\n        if (options.baseChunkSize !== undefined) {\n            this.chunkSizeMs = options.baseChunkSize;\n        }\n        \n        console.log('🎯 Adaptive chunking configuration updated:', options);\n    }\n}\n\n// Initialize global adaptive chunking system\nwindow.adaptiveChunking = new AdaptiveChunking();\n\nconsole.log('✅ Adaptive Chunking System loaded');"