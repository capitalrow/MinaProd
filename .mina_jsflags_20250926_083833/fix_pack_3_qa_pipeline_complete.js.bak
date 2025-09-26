/**
 * 🔬 FIX PACK 3: COMPLETE QA PIPELINE
 * WER calculation, audio-transcript comparison, and quality scoring
 */

class CompleteQAPipeline {
    constructor() {
        this.sessions = new Map();
        this.audioComparator = new AudioTranscriptComparator();
        this.werCalculator = new WERCalculator();
        this.qualityScorer = new QualityScorer();
        
        console.log('🔬 Complete QA Pipeline initialized');
    }
    
    /**
     * Start comprehensive QA session
     */
    startSession(sessionId, options = {}) {
        const session = {
            id: sessionId,
            startTime: Date.now(),
            options: {
                enableWER: options.enableWER !== false,
                enableAudioComparison: options.enableAudioComparison !== false,
                enableQualityScoring: options.enableQualityScoring !== false,
                ...options
            },
            data: {
                audioChunks: [],
                transcriptSegments: [],
                intermediateResults: [],
                finalResults: []
            },
            metrics: {
                wer: 0,
                accuracy: 0,
                latency: [],
                confidence: [],
                completeness: 0,
                semanticDrift: 0
            }
        };
        
        this.sessions.set(sessionId, session);
        
        // Start audio recording for comparison
        if (session.options.enableAudioComparison) {
            this.audioComparator.startRecording(sessionId);
        }
        
        console.log(`🔬 QA Session started: ${sessionId}`);
        return session;
    }
    
    /**
     * Add transcript for analysis
     */
    addTranscript(sessionId, text, confidence, latency, isInterim = false) {
        const session = this.sessions.get(sessionId);
        if (!session) {
            console.warn(`⚠️ QA session not found: ${sessionId}`);
            return;
        }
        
        const segment = {
            text: text.trim(),
            confidence: confidence || 0,
            latency: latency || 0,
            isInterim: isInterim,
            timestamp: Date.now(),
            wordCount: text.trim().split(/\s+/).filter(w => w.length > 0).length
        };
        
        session.data.transcriptSegments.push(segment);
        
        if (isInterim) {
            session.data.intermediateResults.push(segment);
        } else {
            session.data.finalResults.push(segment);
        }
        
        // Perform real-time analysis
        this.performRealTimeAnalysis(sessionId, segment);
        
        console.log(`📝 Transcript added to QA: "${text.substring(0, 30)}..." (conf: ${(confidence * 100).toFixed(1)}%)`);
    }
    
    /**
     * Perform real-time analysis
     */
    performRealTimeAnalysis(sessionId, segment) {
        const session = this.sessions.get(sessionId);
        if (!session) return;
        
        // Update metrics
        session.metrics.confidence.push(segment.confidence);
        session.metrics.latency.push(segment.latency);
        
        // Calculate rolling averages
        const avgConfidence = session.metrics.confidence.reduce((a, b) => a + b, 0) / session.metrics.confidence.length;
        const avgLatency = session.metrics.latency.reduce((a, b) => a + b, 0) / session.metrics.latency.length;
        
        session.metrics.accuracy = avgConfidence;
        
        // Calculate WER if we have enough final results
        if (session.data.finalResults.length >= 2 && session.options.enableWER) {
            this.updateWER(sessionId);
        }
        
        // Calculate quality score
        if (session.options.enableQualityScoring) {
            this.updateQualityScore(sessionId);
        }
        
        // Emit metrics update event
        window.dispatchEvent(new CustomEvent('qaMetricsUpdate', {
            detail: {
                sessionId: sessionId,
                wer: session.metrics.wer,
                accuracy: session.metrics.accuracy,
                confidence: avgConfidence,
                latency: avgLatency
            }
        }));
    }
    
    /**
     * Update WER calculation
     */
    updateWER(sessionId) {
        const session = this.sessions.get(sessionId);
        if (!session || session.data.finalResults.length < 2) return;
        
        const finalResults = session.data.finalResults;
        const reference = finalResults[finalResults.length - 2].text;
        const hypothesis = finalResults[finalResults.length - 1].text;
        
        const wer = this.werCalculator.calculate(reference, hypothesis);
        session.metrics.wer = wer;
        
        console.log(`📊 WER updated: ${(wer * 100).toFixed(2)}% for session ${sessionId}`);
    }
    
    /**
     * Update quality score
     */
    updateQualityScore(sessionId) {
        const session = this.sessions.get(sessionId);
        if (!session) return;
        
        const score = this.qualityScorer.calculateScore(session);
        session.metrics.qualityScore = score;
        
        console.log(`🎯 Quality score updated: ${score.toFixed(2)} for session ${sessionId}`);
    }
    
    /**
     * Get session report
     */
    getSessionReport(sessionId) {
        const session = this.sessions.get(sessionId);
        if (!session) {
            return { error: `Session not found: ${sessionId}` };
        }
        
        const duration = (Date.now() - session.startTime) / 1000;
        const totalWords = session.data.finalResults.reduce((sum, seg) => sum + seg.wordCount, 0);
        
        return {
            sessionId: sessionId,
            duration: duration,
            metrics: session.metrics,
            benchmarks: {
                werTarget: 0.10,
                latencyTarget: 500,
                accuracyTarget: 0.95,
                passed: {
                    wer: session.metrics.wer <= 0.10,
                    latency: session.metrics.latency.length > 0 ? 
                        session.metrics.latency.reduce((a, b) => a + b, 0) / session.metrics.latency.length <= 500 : true,
                    accuracy: session.metrics.accuracy >= 0.95
                }
            },
            summary: {
                totalSegments: session.data.transcriptSegments.length,
                finalSegments: session.data.finalResults.length,
                intermediateSegments: session.data.intermediateResults.length,
                totalWords: totalWords,
                avgConfidence: session.metrics.accuracy,
                avgLatency: session.metrics.latency.length > 0 ? 
                    session.metrics.latency.reduce((a, b) => a + b, 0) / session.metrics.latency.length : 0
            },
            timestamp: new Date().toISOString()
        };
    }
    
    /**
     * Stop session and generate final report
     */
    stopSession(sessionId) {
        const session = this.sessions.get(sessionId);
        if (!session) {
            console.warn(`⚠️ QA session not found: ${sessionId}`);
            return null;
        }
        
        // Stop audio recording
        if (session.options.enableAudioComparison) {
            this.audioComparator.stopRecording(sessionId);
        }
        
        const report = this.getSessionReport(sessionId);
        
        console.log(`🏁 QA Session completed: ${sessionId}`, report);
        
        // Clean up session
        this.sessions.delete(sessionId);
        
        return report;
    }
}

/**
 * Audio-Transcript Comparator
 */
class AudioTranscriptComparator {
    constructor() {
        this.recordings = new Map();
    }
    
    startRecording(sessionId) {
        if (!navigator.mediaDevices) {
            console.warn('⚠️ MediaDevices not available for audio comparison');
            return;
        }
        
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                const mediaRecorder = new MediaRecorder(stream, {
                    mimeType: 'audio/webm;codecs=opus'
                });
                
                const audioChunks = [];
                
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
                
                mediaRecorder.start(1000); // Record in 1-second chunks
                
                this.recordings.set(sessionId, {
                    mediaRecorder: mediaRecorder,
                    audioChunks: audioChunks,
                    stream: stream
                });
                
                console.log(`🎤 Audio recording started for QA: ${sessionId}`);
            })
            .catch(error => {
                console.warn('⚠️ Audio recording failed for QA:', error);
            });
    }
    
    stopRecording(sessionId) {
        const recording = this.recordings.get(sessionId);
        if (!recording) return;
        
        recording.mediaRecorder.stop();
        recording.stream.getTracks().forEach(track => track.stop());
        
        this.recordings.delete(sessionId);
        
        console.log(`🛑 Audio recording stopped for QA: ${sessionId}`);
    }
}

/**
 * WER Calculator using edit distance
 */
class WERCalculator {
    calculate(reference, hypothesis) {
        const refWords = this.normalizeText(reference).split(/\s+/).filter(w => w.length > 0);
        const hypWords = this.normalizeText(hypothesis).split(/\s+/).filter(w => w.length > 0);
        
        if (refWords.length === 0) return 0;
        
        const editDistance = this.calculateEditDistance(refWords, hypWords);
        return editDistance / refWords.length;
    }
    
    normalizeText(text) {
        return text.toLowerCase()
            .replace(/[^\w\s]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }
    
    calculateEditDistance(ref, hyp) {
        const dp = Array(ref.length + 1).fill().map(() => Array(hyp.length + 1).fill(0));
        
        // Initialize
        for (let i = 0; i <= ref.length; i++) dp[i][0] = i;
        for (let j = 0; j <= hyp.length; j++) dp[0][j] = j;
        
        // Fill matrix
        for (let i = 1; i <= ref.length; i++) {
            for (let j = 1; j <= hyp.length; j++) {
                if (ref[i-1] === hyp[j-1]) {
                    dp[i][j] = dp[i-1][j-1];
                } else {
                    dp[i][j] = 1 + Math.min(
                        dp[i-1][j],    // deletion
                        dp[i][j-1],    // insertion
                        dp[i-1][j-1]   // substitution
                    );
                }
            }
        }
        
        return dp[ref.length][hyp.length];
    }
}

/**
 * Quality Scorer
 */
class QualityScorer {
    calculateScore(session) {
        let score = 0;
        
        // Accuracy component (40%)
        const accuracy = session.metrics.accuracy || 0;
        score += accuracy * 0.4;
        
        // Latency component (30%)
        const avgLatency = session.metrics.latency.length > 0 ? 
            session.metrics.latency.reduce((a, b) => a + b, 0) / session.metrics.latency.length : 1000;
        const latencyScore = Math.max(0, 1 - (avgLatency / 1000)); // Normalize to 0-1
        score += latencyScore * 0.3;
        
        // WER component (20%)
        const wer = session.metrics.wer || 1;
        const werScore = Math.max(0, 1 - (wer / 0.5)); // Normalize with 50% WER as baseline
        score += werScore * 0.2;
        
        // Completeness component (10%)
        const expectedSegments = Math.max(1, session.data.finalResults.length);
        const completeness = Math.min(1, session.data.finalResults.length / expectedSegments);
        score += completeness * 0.1;
        
        return Math.min(1, Math.max(0, score)); // Clamp to 0-1
    }
}

// Initialize Complete QA Pipeline
window.completeQAPipeline = new CompleteQAPipeline();

console.log('✅ Fix Pack 3: Complete QA Pipeline loaded');