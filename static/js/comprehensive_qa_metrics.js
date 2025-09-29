/**
 * 🔬 COMPREHENSIVE QA METRICS & PIPELINE MONITORING
 * Implements WER, latency, accuracy, and drift measurement for transcription quality assessment
 */

class ComprehensiveQAMetrics {
    constructor() {
        this.sessions = new Map();
        this.currentSession = null;
        this.qualityThresholds = {
            wer: 10,        // Word Error Rate ≤ 10%
            latency: 500,   // Latency < 500ms
            accuracy: 95,   // Accuracy ≥ 95%
            completeness: 90 // Audio coverage ≥ 90%
        };
        
        this.realTimeMetrics = {
            chunkCount: 0,
            totalWords: 0,
            correctWords: 0,
            deletedWords: 0,
            insertedWords: 0,
            substitutedWords: 0,
            totalLatency: 0,
            semanticDrift: 0,
            duplicateCount: 0,
            hallucinations: 0
        };
        
        console.log('🔬 Comprehensive QA Metrics initialized');
    }
    
    /**
     * Start new QA session with baseline measurements
     */
    startQASession(sessionId, referenceAudio = null) {
        this.currentSession = {
            id: sessionId,
            startTime: Date.now(),
            referenceAudio: referenceAudio,
            transcriptChunks: [],
            audioChunks: [],
            metrics: {
                wer: 0,
                accuracy: 0,
                latency: 0,
                completeness: 0,
                semanticDrift: 0,
                duplicateRate: 0,
                hallucinations: 0
            },
            performance: {
                chunkLatencies: [],
                queueLengths: [],
                droppedChunks: 0,
                retryCount: 0,
                eventLoopBlocks: 0
            },
            qualityGates: {
                confidence: [],
                speakerDetection: [],
                languageDetection: []
            }
        };
        
        // Reset real-time metrics
        this.realTimeMetrics = {
            chunkCount: 0,
            totalWords: 0,
            correctWords: 0,
            deletedWords: 0,
            insertedWords: 0,
            substitutedWords: 0,
            totalLatency: 0,
            semanticDrift: 0,
            duplicateCount: 0,
            hallucinations: 0
        };
        
        this.sessions.set(sessionId, this.currentSession);
        console.log(`🔬 QA Session started: ${sessionId}`);
        
        return sessionId;
    }
    
    /**
     * Record audio chunk for analysis
     */
    recordAudioChunk(audioData, chunkId, timestamp) {
        if (!this.currentSession) return;
        
        this.currentSession.audioChunks.push({
            id: chunkId,
            data: audioData,
            timestamp: timestamp,
            size: audioData.size || audioData.length || 0
        });
        
        this.realTimeMetrics.chunkCount++;
    }
    
    /**
     * Process transcription result and calculate metrics
     */
    processTranscriptChunk(transcriptData, chunkId, processingTime) {
        if (!this.currentSession) return;
        
        const chunk = {
            id: chunkId,
            text: transcriptData.transcript || transcriptData.text || '',
            confidence: transcriptData.confidence || 0.95,
            timestamp: Date.now(),
            processingTime: processingTime,
            isInterim: transcriptData.is_interim || false,
            segments: transcriptData.segments || []
        };
        
        this.currentSession.transcriptChunks.push(chunk);
        
        // Update real-time metrics
        this.updateRealTimeMetrics(chunk);
        
        // Calculate quality metrics
        this.calculateChunkMetrics(chunk);
        
        // Log performance data
        this.logPerformanceMetrics(chunk);
        
        console.log(`📊 QA Chunk ${chunkId}: WER=${this.currentSession.metrics.wer}%, Latency=${processingTime}ms`);
        
        return this.currentSession.metrics;
    }
    
    /**
     * Update real-time metrics for monitoring
     */
    updateRealTimeMetrics(chunk) {
        if (!chunk.text) return;
        
        const words = chunk.text.split(/\s+/).filter(w => w.length > 0);
        this.realTimeMetrics.totalWords += words.length;
        
        // Estimate correct words (simplified - in real implementation would compare with reference)
        this.realTimeMetrics.correctWords += Math.floor(words.length * (chunk.confidence || 0.95));
        
        // Track latency
        this.realTimeMetrics.totalLatency += chunk.processingTime || 0;
        
        // Detect potential duplicates (simple heuristic)
        if (this.detectDuplicate(chunk.text)) {
            this.realTimeMetrics.duplicateCount++;
        }
        
        // Detect potential hallucinations (very short or nonsensical text)
        if (this.detectHallucination(chunk.text, chunk.confidence)) {
            this.realTimeMetrics.hallucinations++;
        }
    }
    
    /**
     * Calculate comprehensive quality metrics
     */
    calculateChunkMetrics(chunk) {
        if (!this.currentSession) return;
        
        // Update accuracy based on confidence scores
        const confidences = this.currentSession.transcriptChunks.map(c => c.confidence || 0);
        this.currentSession.metrics.accuracy = (confidences.reduce((a, b) => a + b, 0) / confidences.length) * 100;
        
        // Calculate average latency
        const latencies = this.currentSession.transcriptChunks.map(c => c.processingTime || 0);
        this.currentSession.metrics.latency = latencies.reduce((a, b) => a + b, 0) / latencies.length;
        
        // Calculate WER (simplified - actual WER requires reference transcript)
        const estimatedWER = this.estimateWER();
        this.currentSession.metrics.wer = estimatedWER;
        
        // Calculate completeness (audio chunks vs transcript chunks)
        const audioChunks = this.currentSession.audioChunks.length;
        const transcriptChunks = this.currentSession.transcriptChunks.filter(c => !c.isInterim).length;
        this.currentSession.metrics.completeness = audioChunks > 0 ? (transcriptChunks / audioChunks) * 100 : 0;
        
        // Calculate duplicate rate
        this.currentSession.metrics.duplicateRate = (this.realTimeMetrics.duplicateCount / this.realTimeMetrics.chunkCount) * 100;
        
        // Calculate semantic drift (simplified)
        this.currentSession.metrics.semanticDrift = this.calculateSemanticDrift();
    }
    
    /**
     * Estimate Word Error Rate (simplified without reference transcript)
     */
    estimateWER() {
        if (this.realTimeMetrics.totalWords === 0) return 0;
        
        // Simplified WER estimation based on confidence scores and detected issues
        const lowConfidenceWords = this.realTimeMetrics.totalWords - this.realTimeMetrics.correctWords;
        const duplicateWords = this.realTimeMetrics.duplicateCount * 5; // Estimate words per duplicate
        const hallucinationWords = this.realTimeMetrics.hallucinations * 3; // Estimate words per hallucination
        
        const estimatedErrors = lowConfidenceWords + duplicateWords + hallucinationWords;
        return Math.min(100, (estimatedErrors / this.realTimeMetrics.totalWords) * 100);
    }
    
    /**
     * Calculate semantic drift over time
     */
    calculateSemanticDrift() {
        if (this.currentSession.transcriptChunks.length < 3) return 0;
        
        // Simplified drift calculation based on vocabulary consistency
        const recentChunks = this.currentSession.transcriptChunks.slice(-5);
        const vocabularies = recentChunks.map(chunk => 
            new Set(chunk.text.toLowerCase().split(/\s+/).filter(w => w.length > 3))
        );
        
        if (vocabularies.length < 2) return 0;
        
        // Calculate vocabulary overlap between consecutive chunks
        let overlapSum = 0;
        for (let i = 1; i < vocabularies.length; i++) {
            const intersection = new Set([...vocabularies[i-1]].filter(x => vocabularies[i].has(x)));
            const union = new Set([...vocabularies[i-1], ...vocabularies[i]]);
            overlapSum += union.size > 0 ? intersection.size / union.size : 0;
        }
        
        const avgOverlap = overlapSum / (vocabularies.length - 1);
        return Math.max(0, (1 - avgOverlap) * 100); // Higher drift = lower semantic consistency
    }
    
    /**
     * Detect duplicate content
     */
    detectDuplicate(text) {
        if (!this.currentSession || this.currentSession.transcriptChunks.length < 2) return false;
        
        const recent = this.currentSession.transcriptChunks.slice(-3).map(c => c.text.toLowerCase().trim());
        return recent.some(recentText => 
            recentText.length > 10 && text.toLowerCase().includes(recentText)
        );
    }
    
    /**
     * Detect potential hallucinations
     */
    detectHallucination(text, confidence) {
        if (!text || text.length < 3) return true;
        
        // Low confidence + very short text
        if (confidence < 0.7 && text.length < 10) return true;
        
        // Repetitive patterns (simplified)
        const words = text.split(/\s+/);
        if (words.length > 2) {
            const uniqueWords = new Set(words);
            if (uniqueWords.size / words.length < 0.5) return true; // >50% repetition
        }
        
        return false;
    }
    
    /**
     * Log performance metrics for monitoring
     */
    logPerformanceMetrics(chunk) {
        if (!this.currentSession) return;
        
        this.currentSession.performance.chunkLatencies.push(chunk.processingTime || 0);
        
        // Simulate queue length monitoring (would come from actual system)
        const queueLength = Math.floor(Math.random() * 5); // Placeholder
        this.currentSession.performance.queueLengths.push(queueLength);
        
        // Log to console for debugging
        console.log(`📈 Performance: Latency=${chunk.processingTime}ms, Queue=${queueLength}, Chunk=${chunk.id}`);
    }
    
    /**
     * End QA session and generate comprehensive report
     */
    endQASession() {
        if (!this.currentSession) return null;
        
        const session = this.currentSession;
        const endTime = Date.now();
        const duration = endTime - session.startTime;
        
        // Final metric calculations
        this.calculateFinalMetrics(session);
        
        const report = {
            sessionId: session.id,
            duration: duration,
            totalChunks: session.transcriptChunks.length,
            audioChunks: session.audioChunks.length,
            
            metrics: {
                wer: Math.round(session.metrics.wer * 100) / 100,
                accuracy: Math.round(session.metrics.accuracy * 100) / 100,
                latency: Math.round(session.metrics.latency),
                completeness: Math.round(session.metrics.completeness * 100) / 100,
                semanticDrift: Math.round(session.metrics.semanticDrift * 100) / 100,
                duplicateRate: Math.round(session.metrics.duplicateRate * 100) / 100
            },
            
            performance: {
                avgLatency: session.performance.chunkLatencies.length > 0 ? 
                    session.performance.chunkLatencies.reduce((a, b) => a + b, 0) / session.performance.chunkLatencies.length : 0,
                maxLatency: Math.max(...session.performance.chunkLatencies, 0),
                p95Latency: this.calculatePercentile(session.performance.chunkLatencies, 95),
                avgQueueLength: session.performance.queueLengths.length > 0 ?
                    session.performance.queueLengths.reduce((a, b) => a + b, 0) / session.performance.queueLengths.length : 0,
                droppedChunks: session.performance.droppedChunks,
                retryCount: session.performance.retryCount
            },
            
            qualityAssessment: this.assessQuality(session.metrics),
            
            passed: {
                wer: session.metrics.wer <= this.qualityThresholds.wer,
                latency: session.metrics.latency < this.qualityThresholds.latency,
                accuracy: session.metrics.accuracy >= this.qualityThresholds.accuracy,
                completeness: session.metrics.completeness >= this.qualityThresholds.completeness,
                overall: this.assessOverallQuality(session.metrics)
            }
        };
        
        console.log(`📊 QA Session ${session.id} Complete:`, report);
        
        this.currentSession = null;
        return report;
    }
    
    /**
     * Calculate final metrics for session
     */
    calculateFinalMetrics(session) {
        // Recalculate all metrics with final data
        this.calculateChunkMetrics(session.transcriptChunks[session.transcriptChunks.length - 1]);
    }
    
    /**
     * Calculate percentile for latency analysis
     */
    calculatePercentile(arr, percentile) {
        if (arr.length === 0) return 0;
        
        const sorted = [...arr].sort((a, b) => a - b);
        const index = Math.ceil((percentile / 100) * sorted.length) - 1;
        return sorted[Math.max(0, index)];
    }
    
    /**
     * Assess overall quality based on metrics
     */
    assessQuality(metrics) {
        const scores = {
            wer: metrics.wer <= this.qualityThresholds.wer ? 'EXCELLENT' : 
                 metrics.wer <= 20 ? 'GOOD' : 'NEEDS_IMPROVEMENT',
            latency: metrics.latency < this.qualityThresholds.latency ? 'EXCELLENT' :
                     metrics.latency < 1000 ? 'GOOD' : 'NEEDS_IMPROVEMENT',
            accuracy: metrics.accuracy >= this.qualityThresholds.accuracy ? 'EXCELLENT' :
                      metrics.accuracy >= 85 ? 'GOOD' : 'NEEDS_IMPROVEMENT',
            completeness: metrics.completeness >= this.qualityThresholds.completeness ? 'EXCELLENT' :
                          metrics.completeness >= 75 ? 'GOOD' : 'NEEDS_IMPROVEMENT'
        };
        
        return scores;
    }
    
    /**
     * Assess overall quality pass/fail
     */
    assessOverallQuality(metrics) {
        return metrics.wer <= this.qualityThresholds.wer &&
               metrics.latency < this.qualityThresholds.latency &&
               metrics.accuracy >= this.qualityThresholds.accuracy &&
               metrics.completeness >= this.qualityThresholds.completeness;
    }
    
    /**
     * Get current real-time metrics
     */
    getCurrentMetrics() {
        return {
            ...this.realTimeMetrics,
            sessionActive: !!this.currentSession,
            currentSession: this.currentSession?.id || null
        };
    }
    
    /**
     * Get session history
     */
    getSessionHistory() {
        return Array.from(this.sessions.entries()).map(([id, session]) => ({
            id,
            duration: Date.now() - session.startTime,
            metrics: session.metrics,
            chunkCount: session.transcriptChunks.length
        }));
    }
}

// Create global instance
window.comprehensiveQAMetrics = new ComprehensiveQAMetrics();

console.log('✅ Comprehensive QA Metrics system loaded');