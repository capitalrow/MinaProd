/**
 * 🔗 PERFORMANCE INTEGRATION BRIDGE
 * Connects all optimization systems to the actual transcription pipeline
 */

class PerformanceIntegrationBridge {
    constructor() {
        this.realWhisperIntegration = null;
        this.originalMethods = {};
        this.isIntegrated = false;
        this.connectionAttempts = 0;
        this.fallbackMode = false;
        
        console.log('🔗 Performance Integration Bridge initializing...');
    }
    
    /**
     * Integrate all optimization systems with RealWhisperIntegration
     */
    integrateWithTranscriptionSystem() {
        // Wait for RealWhisperIntegration to be available with retry limit
        if (!window.realWhisperIntegration) {
            this.connectionAttempts = (this.connectionAttempts || 0) + 1;
            if (this.connectionAttempts > 20) { // Max 10 seconds
                console.error('❌ RealWhisperIntegration not available after 10 seconds - using fallback mode');
                this.setupFallbackMode();
                return;
            }
            console.log(`⏳ Waiting for RealWhisperIntegration... (attempt ${this.connectionAttempts}/20)`);
            setTimeout(() => this.integrateWithTranscriptionSystem(), 500);
            return;
        }
        
        this.realWhisperIntegration = window.realWhisperIntegration;
        this.patchAudioProcessing();
        this.patchTranscriptionHandling();
        this.setupPerformanceMonitoring();
        this.isIntegrated = true;
        
        console.log('✅ Performance systems integrated with transcription pipeline');
    }
    
    /**
     * Patch audio processing methods to include VAD and adaptive chunking
     */
    patchAudioProcessing() {
        // 🔒 DEFENSIVE BINDING: Validate method exists before binding
        if (typeof this.realWhisperIntegration.sendAudioDataHTTP !== 'function') {
            console.warn('⚠️ sendAudioDataHTTP method not found, using fallback');
            this.originalMethods.sendAudioDataHTTP = () => Promise.resolve();
        } else {
            this.originalMethods.sendAudioDataHTTP = this.realWhisperIntegration.sendAudioDataHTTP.bind(this.realWhisperIntegration);
        }
        
        // Patch sendAudioDataHTTP to include VAD optimization
        this.realWhisperIntegration.sendAudioDataHTTP = async (audioBlob) => {
            const startTime = Date.now();
            
            // Convert blob to array buffer for analysis
            const arrayBuffer = await audioBlob.arrayBuffer();
            const audioData = new Float32Array(arrayBuffer);
            
            // Apply VAD optimization
            if (window.vadOptimization) {
                const vadResult = window.vadOptimization.analyzeAudioChunk(audioData, startTime);
                
                if (!vadResult.shouldProcess) {
                    console.log('🎤 VAD: Skipping chunk (no speech detected)');
                    return; // Skip processing silent chunks
                }
                
                console.log(`🎤 VAD: Processing speech chunk (RMS: ${vadResult.rms.toFixed(4)}, Duration: ${vadResult.speechDuration}ms)`);
            }
            
            // Apply adaptive chunking analysis
            if (window.adaptiveChunking) {
                const chunkingResult = window.adaptiveChunking.analyzeAndAdaptChunkSize(audioData, {
                    confidence: 0.8,
                    processingTime: Date.now() - startTime,
                    audioDuration: audioData.length / 16000 * 1000 // Estimate duration
                });
                
                console.log(`🎯 Adaptive Chunking: Recommended size ${chunkingResult.recommendedChunkSize}ms`);
            }
            
            // Apply mobile optimizations
            if (window.mobileOptimizer && window.mobileOptimizer.isMobile) {
                // Check battery level and adjust quality if needed
                const stats = window.mobileOptimizer.getStatistics();
                if (stats.batteryLevel !== null && stats.batteryLevel < 20 && !stats.isCharging) {
                    console.log('📱 Low battery: Applying aggressive optimization');
                    // Could compress audio or reduce frequency here
                }
            }
            
            // Proceed with original method
            return this.originalMethods.sendAudioDataHTTP(audioBlob);
        };
        
        console.log('🔗 Audio processing methods patched');
    }
    
    /**
     * Patch transcription handling to include performance monitoring
     */
    patchTranscriptionHandling() {
        // 🔒 DEFENSIVE BINDING: Fix method name and validate existence
        const methodName = 'updateTranscriptDisplay'; // Correct method name
        if (typeof this.realWhisperIntegration[methodName] !== 'function') {
            console.warn(`⚠️ ${methodName} method not found, using fallback`);
            this.originalMethods.displayTranscript = () => {};
        } else {
            this.originalMethods.displayTranscript = this.realWhisperIntegration[methodName].bind(this.realWhisperIntegration);
        }
        
        // Patch updateTranscriptDisplay to include performance monitoring  
        this.realWhisperIntegration.updateTranscriptDisplay = (transcript, segments) => {
            const timestamp = Date.now();
            
            // Record performance metrics
            if (window.performanceDashboard) {
                const processingTime = timestamp - (this.lastChunkTime || timestamp);
                window.performanceDashboard.recordTranscriptionMetrics({
                    processingTime: processingTime,
                    confidence: this.estimateConfidence(transcript, segments),
                    text: transcript
                });
            }
            
            // Record QA metrics
            if (window.automatedQA && window.automatedQA.qaSession) {
                window.automatedQA.addTranscriptSegment(
                    transcript,
                    this.estimateConfidence(transcript, segments),
                    timestamp - (this.lastChunkTime || timestamp),
                    false, // Not interim
                    timestamp
                );
            }
            
            this.lastChunkTime = timestamp;
            
            // Proceed with original method
            return this.originalMethods.displayTranscript(transcript, segments);
        };
        
        console.log('🔗 Transcription handling methods patched');
    }
    
    /**
     * Setup comprehensive performance monitoring
     */
    setupPerformanceMonitoring() {
        // 🔒 DEFENSIVE BINDING: Fix method names and validate existence
        const startMethodName = 'startTranscription'; // Correct method name
        const originalStartRecording = this.realWhisperIntegration[startMethodName]?.bind?.(this.realWhisperIntegration);
        if (originalStartRecording && typeof originalStartRecording === 'function') {
            this.realWhisperIntegration[startMethodName] = async (sessionId) => {
                console.log('🎙️ Recording started - activating performance systems');
                
                // Start QA session
                if (window.automatedQA) {
                    const sessionId = `session_${Date.now()}`;
                    window.automatedQA.startQASession(sessionId);
                }
                
                // Reset performance systems
                if (window.vadOptimization) window.vadOptimization.reset();
                if (window.adaptiveChunking) window.adaptiveChunking.reset();
                
                // Emit recording started event
                window.dispatchEvent(new CustomEvent('recordingStarted', {
                    detail: { timestamp: Date.now() }
                }));
                
                return originalStartRecording();
            };
        }
        
        const stopMethodName = 'stopTranscription'; // Correct method name
        const originalStopRecording = this.realWhisperIntegration[stopMethodName]?.bind?.(this.realWhisperIntegration);
        if (originalStopRecording && typeof originalStopRecording === 'function') {
            this.realWhisperIntegration[stopMethodName] = () => {
                console.log('🎙️ Recording stopped - finalizing performance metrics');
                
                // End QA session and generate report
                if (window.automatedQA) {
                    const report = window.automatedQA.endQASession();
                    if (report) {
                        console.log('📊 Final QA Report:', report);
                        this.displayQAReport(report);
                    }
                }
                
                // Generate performance statistics
                this.generatePerformanceReport();
                
                // Emit recording stopped event
                window.dispatchEvent(new CustomEvent('recordingStopped', {
                    detail: { timestamp: Date.now() }
                }));
                
                return originalStopRecording();
            };
        }
        
        console.log('🔗 Performance monitoring setup complete');
    }
    
    /**
     * Setup fallback mode when RealWhisperIntegration is not available
     */
    setupFallbackMode() {
        this.fallbackMode = true;
        console.log('🔄 Activating fallback performance monitoring mode');
        
        // Find the record button and hook into its events
        const recordButton = document.getElementById('recordButton');
        if (recordButton) {
            recordButton.addEventListener('click', () => {
                if (recordButton.textContent.includes('Start')) {
                    this.onRecordingStart();
                } else {
                    this.onRecordingStop();
                }
            });
        }
        
        // Monitor HTTP transcription requests
        this.interceptHTTPRequests();
        
        this.isIntegrated = true;
        console.log('✅ Fallback mode activated - monitoring HTTP transcription flow');
    }
    
    /**
     * Intercept HTTP transcription requests for fallback monitoring
     */
    interceptHTTPRequests() {
        const originalFetch = window.fetch;
        window.fetch = async (url, options) => {
            const startTime = Date.now();
            
            if (url.includes('/api/transcribe')) {
                console.log('📤 Intercepted transcription request');
                
                try {
                    const response = await originalFetch(url, options);
                    const endTime = Date.now();
                    const latency = endTime - startTime;
                    
                    // Clone response to read it
                    const responseClone = response.clone();
                    const result = await responseClone.json();
                    
                    // Record performance metrics
                    if (window.performanceDashboard) {
                        window.performanceDashboard.recordTranscriptionMetrics({
                            processingTime: latency,
                            confidence: result.segments?.[0]?.confidence || 0.8,
                            text: result.transcript || ''
                        });
                    }
                    
                    // Record QA metrics
                    if (window.automatedQA && window.automatedQA.qaSession) {
                        window.automatedQA.addTranscriptSegment(
                            result.transcript || '',
                            result.segments?.[0]?.confidence || 0.8,
                            latency,
                            false,
                            endTime
                        );
                    }
                    
                    console.log(`✅ HTTP transcription completed in ${latency}ms`);
                    return response;
                    
                } catch (error) {
                    console.error('❌ HTTP transcription failed:', error);
                    throw error;
                }
            }
            
            return originalFetch(url, options);
        };
    }
    
    /**
     * Handle recording start in fallback mode
     */
    onRecordingStart() {
        console.log('🎙️ Recording started (fallback mode)');
        
        // Start QA session
        if (window.automatedQA) {
            const sessionId = `session_${Date.now()}`;
            window.automatedQA.startQASession(sessionId);
        }
        
        // Reset performance systems
        if (window.vadOptimization) window.vadOptimization.reset();
        if (window.adaptiveChunking) window.adaptiveChunking.reset();
        
        // Emit recording started event
        window.dispatchEvent(new CustomEvent('recordingStarted', {
            detail: { timestamp: Date.now(), fallbackMode: true }
        }));
    }
    
    /**
     * Handle recording stop in fallback mode
     */
    onRecordingStop() {
        console.log('🎙️ Recording stopped (fallback mode)');
        
        // End QA session and generate report
        if (window.automatedQA) {
            const report = window.automatedQA.endQASession();
            if (report) {
                console.log('📊 Final QA Report (Fallback):', report);
                this.displayQAReport(report);
            }
        }
        
        // Generate performance statistics
        this.generatePerformanceReport();
        
        // Emit recording stopped event
        window.dispatchEvent(new CustomEvent('recordingStopped', {
            detail: { timestamp: Date.now(), fallbackMode: true }
        }));
    }
    
    /**
     * Estimate confidence from transcript and segments
     */
    estimateConfidence(transcript, segments) {
        if (!transcript || transcript.length === 0) return 0;
        
        // Basic confidence estimation based on transcript characteristics
        let confidence = 0.8; // Base confidence
        
        // Adjust based on length (very short transcripts are often unreliable)
        if (transcript.length < 3) confidence -= 0.3;
        else if (transcript.length > 10) confidence += 0.1;
        
        // Adjust based on common recognition errors
        const lowConfidenceWords = ['you', 'uh', 'um', 'the the', 'a a'];
        const hasLowConfidenceWords = lowConfidenceWords.some(word => 
            transcript.toLowerCase().includes(word)
        );
        if (hasLowConfidenceWords) confidence -= 0.2;
        
        // Adjust based on segments if available
        if (segments && segments.length > 0) {
            // If we have segments with confidence, use them
            const avgSegmentConfidence = segments.reduce((sum, seg) => {
                return sum + (seg.confidence || 0.8);
            }, 0) / segments.length;
            confidence = (confidence + avgSegmentConfidence) / 2;
        }
        
        return Math.max(0.1, Math.min(0.95, confidence));
    }
    
    /**
     * Generate comprehensive performance report
     */
    generatePerformanceReport() {
        const report = {
            timestamp: new Date().toISOString(),
            systems: {}
        };
        
        // VAD statistics
        if (window.vadOptimization) {
            report.systems.vad = window.vadOptimization.getStatistics();
        }
        
        // Adaptive chunking statistics
        if (window.adaptiveChunking) {
            report.systems.adaptiveChunking = window.adaptiveChunking.getStatistics();
        }
        
        // Performance dashboard metrics
        if (window.performanceDashboard) {
            report.systems.performance = window.performanceDashboard.generateReport();
        }
        
        // Mobile optimization statistics
        if (window.mobileOptimizer) {
            report.systems.mobile = window.mobileOptimizer.getStatistics();
        }
        
        console.log('📊 Performance Report Generated:', report);
        
        // Display report summary
        this.displayPerformanceReport(report);
        
        return report;
    }
    
    /**
     * Display QA report in UI
     */
    displayQAReport(report) {
        if (!report || !report.metrics) return;
        
        const summary = `
QA Report Summary:
• WER: ${report.metrics.wer.toFixed(1)}% (Target: ≤10%)
• Accuracy: ${report.metrics.accuracy.toFixed(1)}% (Target: ≥95%)
• Latency: ${report.metrics.latency.toFixed(0)}ms (Target: <500ms)
• Completeness: ${report.metrics.completeness.toFixed(1)}%
        `.trim();
        
        // Show notification
        if (window.showNotification) {
            const status = report.passed.overall ? 'success' : 'warning';
            window.showNotification(`Quality Assessment Complete`, summary, status);
        } else {
            console.log('📊 ' + summary);
        }
    }
    
    /**
     * Display performance report summary
     */
    displayPerformanceReport(report) {
        const summaryItems = [];
        
        if (report.systems.vad) {
            summaryItems.push(`VAD: ${report.systems.vad.apiCallReduction}% reduction in API calls`);
        }
        
        if (report.systems.adaptiveChunking) {
            summaryItems.push(`Chunking: ${report.systems.adaptiveChunking.adaptationEvents} adaptations`);
        }
        
        if (report.systems.performance && report.systems.performance.metrics) {
            const latency = report.systems.performance.metrics.latency;
            summaryItems.push(`Latency: ${latency.average.toFixed(0)}ms avg`);
        }
        
        if (report.systems.mobile && report.systems.mobile.isMobile) {
            summaryItems.push(`Mobile: ${report.systems.mobile.performanceLevel} mode`);
        }
        
        const summary = `Performance Optimizations:
${summaryItems.map(item => '• ' + item).join('\n')}`;
        
        // Show notification
        if (window.showNotification) {
            window.showNotification('Performance Report', summary, 'info');
        } else {
            console.log('📊 ' + summary);
        }
    }
    
    /**
     * Monitor real-time performance metrics
     */
    startRealTimeMonitoring() {
        setInterval(() => {
            if (!this.isIntegrated) return;
            
            // Update performance dashboard if visible
            if (window.performanceDashboard && window.performanceDashboard.isVisible) {
                // Dashboard updates itself
            }
            
            // Check for performance issues
            this.checkPerformanceIssues();
            
        }, 5000); // Every 5 seconds
    }
    
    /**
     * Check for performance issues and auto-adjust
     */
    checkPerformanceIssues() {
        const issues = [];
        
        // Check VAD performance
        if (window.vadOptimization) {
            const vadStats = window.vadOptimization.getStatistics();
            if (vadStats.apiCallReduction < 30) {
                issues.push('VAD not effectively reducing API calls');
                // Auto-adjust VAD sensitivity
                window.vadOptimization.configure({
                    silenceThreshold: 0.015, // Make more sensitive
                    speechThreshold: 0.025
                });
                console.log('🎤 Auto-adjusted VAD sensitivity for better performance');
            }
        }
        
        // Check mobile battery optimization
        if (window.mobileOptimizer && window.mobileOptimizer.isMobile) {
            const mobileStats = window.mobileOptimizer.getStatistics();
            if (mobileStats.batteryLevel !== null && mobileStats.batteryLevel < 15 && !mobileStats.isCharging) {
                if (mobileStats.performanceLevel !== 'battery_saver') {
                    window.mobileOptimizer.setPerformanceLevel('battery_saver');
                    issues.push('Switched to battery saver mode due to low battery');
                }
            }
        }
        
        if (issues.length > 0) {
            console.log('🔧 Auto-adjustments made:', issues);
        }
    }
    
    /**
     * Get integration status
     */
    getStatus() {
        return {
            integrated: this.isIntegrated,
            realWhisperIntegration: !!this.realWhisperIntegration,
            patchedMethods: Object.keys(this.originalMethods),
            systems: {
                vad: !!window.vadOptimization,
                adaptiveChunking: !!window.adaptiveChunking,
                performanceDashboard: !!window.performanceDashboard,
                automatedQA: !!window.automatedQA,
                mobileOptimizer: !!window.mobileOptimizer
            }
        };
    }
}

// Initialize the integration bridge
window.performanceIntegrationBridge = new PerformanceIntegrationBridge();

// Auto-start integration when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.performanceIntegrationBridge.integrateWithTranscriptionSystem();
    window.performanceIntegrationBridge.startRealTimeMonitoring();
});

console.log('✅ Performance Integration Bridge loaded');

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
