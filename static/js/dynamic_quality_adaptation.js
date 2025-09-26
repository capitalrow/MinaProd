/**
 * DYNAMIC QUALITY ADAPTATION ENGINE
 * Real-time quality optimization based on environmental conditions
 */

class DynamicQualityAdaptation {
    constructor() {
        this.isActive = false;
        this.environmentalProfiles = new Map();
        this.adaptationHistory = [];
        this.currentProfile = 'balanced';
        
        this.qualityMetrics = {
            audioClarity: 0,
            backgroundNoise: 0,
            speechConsistency: 0,
            transcriptionAccuracy: 0,
            systemPerformance: 0
        };
        
        this.adaptationProfiles = {
            'silent_environment': {
                name: 'Silent Environment',
                audioSettings: {
                    noiseSuppression: false,
                    echoCancellation: true,
                    autoGainControl: false,
                    sensitivity: 'high'
                },
                processingSettings: {
                    chunkSize: 3000,
                    qualityPriority: 'accuracy',
                    enhancementLevel: 'maximum'
                },
                transcriptionSettings: {
                    confidenceThreshold: 0.8,
                    grammarCorrection: true,
                    contextAnalysis: 'deep'
                }
            },
            
            'noisy_environment': {
                name: 'Noisy Environment',
                audioSettings: {
                    noiseSuppression: true,
                    echoCancellation: true,
                    autoGainControl: true,
                    sensitivity: 'medium'
                },
                processingSettings: {
                    chunkSize: 2000,
                    qualityPriority: 'noise_reduction',
                    enhancementLevel: 'aggressive'
                },
                transcriptionSettings: {
                    confidenceThreshold: 0.7,
                    grammarCorrection: true,
                    contextAnalysis: 'enhanced'
                }
            },
            
            'mobile_device': {
                name: 'Mobile Optimized',
                audioSettings: {
                    noiseSuppression: true,
                    echoCancellation: true,
                    autoGainControl: true,
                    sensitivity: 'adaptive'
                },
                processingSettings: {
                    chunkSize: 1500,
                    qualityPriority: 'performance',
                    enhancementLevel: 'balanced'
                },
                transcriptionSettings: {
                    confidenceThreshold: 0.75,
                    grammarCorrection: true,
                    contextAnalysis: 'standard'
                }
            },
            
            'presentation_mode': {
                name: 'Presentation Mode',
                audioSettings: {
                    noiseSuppression: false,
                    echoCancellation: false,
                    autoGainControl: false,
                    sensitivity: 'high'
                },
                processingSettings: {
                    chunkSize: 4000,
                    qualityPriority: 'completeness',
                    enhancementLevel: 'maximum'
                },
                transcriptionSettings: {
                    confidenceThreshold: 0.85,
                    grammarCorrection: true,
                    contextAnalysis: 'comprehensive'
                }
            },
            
            'interview_mode': {
                name: 'Interview Mode',
                audioSettings: {
                    noiseSuppression: true,
                    echoCancellation: true,
                    autoGainControl: true,
                    sensitivity: 'high'
                },
                processingSettings: {
                    chunkSize: 2500,
                    qualityPriority: 'speaker_clarity',
                    enhancementLevel: 'enhanced'
                },
                transcriptionSettings: {
                    confidenceThreshold: 0.8,
                    grammarCorrection: true,
                    contextAnalysis: 'conversational'
                }
            },
            
            'low_bandwidth': {
                name: 'Low Bandwidth',
                audioSettings: {
                    noiseSuppression: false,
                    echoCancellation: false,
                    autoGainControl: true,
                    sensitivity: 'medium'
                },
                processingSettings: {
                    chunkSize: 1000,
                    qualityPriority: 'speed',
                    enhancementLevel: 'minimal'
                },
                transcriptionSettings: {
                    confidenceThreshold: 0.6,
                    grammarCorrection: false,
                    contextAnalysis: 'basic'
                }
            }
        };
        
        this.adaptationTriggers = {
            environment: {
                noiseLevel: 0.3,
                speechClarityThreshold: 0.7,
                backgroundNoiseThreshold: 0.4
            },
            performance: {
                latencyThreshold: 1000,
                accuracyThreshold: 0.8,
                resourceUsageThreshold: 0.8
            },
            network: {
                bandwidthThreshold: 100, // KB/s
                latencyThreshold: 300,   // ms
                stabilityThreshold: 0.7
            }
        };
        
        this.setupEnvironmentalDetection();
    }
    
    initialize() {
        console.log('🎭 Initializing Dynamic Quality Adaptation');
        
        this.detectInitialEnvironment();
        this.startEnvironmentalMonitoring();
        this.setupAdaptationEngine();
        this.isActive = true;
        
        console.log('✅ Dynamic quality adaptation active');
        return true;
    }
    
    setupEnvironmentalDetection() {
        // Environmental detection algorithms
        this.detectionAlgorithms = {
            noiseLevel: this.detectNoiseLevel.bind(this),
            speechPattern: this.detectSpeechPattern.bind(this),
            deviceType: this.detectDeviceType.bind(this),
            networkCondition: this.detectNetworkCondition.bind(this),
            usageContext: this.detectUsageContext.bind(this)
        };
    }
    
    detectInitialEnvironment() {
        // Perform initial environment detection
        const environment = {
            deviceType: this.detectDeviceType(),
            networkCondition: this.detectNetworkCondition(),
            estimatedNoiseLevel: 0.5, // Will be updated with actual audio
            usageContext: 'general'
        };
        
        // Select initial profile based on detection
        this.currentProfile = this.selectOptimalProfile(environment);
        this.applyProfile(this.currentProfile);
        
        console.log(`🎯 Initial profile selected: ${this.adaptationProfiles[this.currentProfile].name}`);
    }
    
    startEnvironmentalMonitoring() {
        // Monitor environment every 2 seconds
        this.monitoringInterval = setInterval(() => {
            this.analyzeCurrentEnvironment();
            this.evaluateAdaptationNeed();
        }, 2000);
        
        // Listen for audio quality updates
        window.addEventListener('audioQualityUpdate', (event) => {
            this.processAudioQualityData(event.detail);
        });
        
        // Listen for transcription results
        window.addEventListener('transcriptionResult', (event) => {
            this.processTranscriptionQuality(event.detail);
        });
        
        // Listen for performance metrics
        window.addEventListener('systemPerformanceUpdate', (event) => {
            this.processPerformanceData(event.detail);
        });
    }
    
    analyzeCurrentEnvironment() {
        const currentEnvironment = {
            noiseLevel: this.qualityMetrics.backgroundNoise,
            speechClarity: this.qualityMetrics.audioClarity / 100,
            transcriptionAccuracy: this.qualityMetrics.transcriptionAccuracy / 100,
            systemLoad: this.qualityMetrics.systemPerformance / 100,
            networkStability: this.detectNetworkStability(),
            deviceType: this.detectDeviceType()
        };
        
        // Update environmental profile
        this.updateEnvironmentalProfile(currentEnvironment);
        
        // Check if adaptation is needed
        const optimalProfile = this.selectOptimalProfile(currentEnvironment);
        if (optimalProfile !== this.currentProfile) {
            this.considerProfileSwitch(optimalProfile, currentEnvironment);
        }
    }
    
    detectNoiseLevel() {
        // Analyze background noise from audio quality metrics
        if (window.enhancedSystemIntegration?.audioOptimizer) {
            const quality = window.enhancedSystemIntegration.audioOptimizer.getQualityMetrics();
            if (quality && quality.snr) {
                // Convert SNR to noise level (inverted)
                return Math.max(0, 1 - (quality.snr / 10));
            }
        }
        return 0.5; // Default moderate noise level
    }
    
    detectSpeechPattern() {
        // Analyze speech patterns from chunking data
        const patterns = {
            continuous: false,
            sporadic: false,
            consistent: false,
            variable: false
        };
        
        if (window.intelligentChunkingOptimizer) {
            const report = window.intelligentChunkingOptimizer.getOptimizationReport();
            if (report && report.speechDetectionRate) {
                if (report.speechDetectionRate > 80) {
                    patterns.continuous = true;
                    patterns.consistent = true;
                } else if (report.speechDetectionRate < 40) {
                    patterns.sporadic = true;
                } else {
                    patterns.variable = true;
                }
            }
        }
        
        return patterns;
    }
    
    detectDeviceType() {
        // Detect device type from user agent and capabilities
        const ua = navigator.userAgent.toLowerCase();
        
        if (/mobile|android|iphone|ipad|tablet/.test(ua)) {
            return 'mobile';
        } else if (/tablet|ipad/.test(ua)) {
            return 'tablet';
        } else {
            return 'desktop';
        }
    }
    
    detectNetworkCondition() {
        // Analyze network performance
        if (navigator.connection) {
            const connection = navigator.connection;
            
            if (connection.effectiveType === '4g' && connection.downlink > 2) {
                return 'high_bandwidth';
            } else if (connection.effectiveType === '3g' || connection.downlink < 1) {
                return 'low_bandwidth';
            } else {
                return 'medium_bandwidth';
            }
        }
        
        // Fallback to latency-based detection
        if (window.predictiveLatencyOptimizer) {
            const report = window.predictiveLatencyOptimizer.getOptimizationReport();
            if (report && report.recentLatencyTrend) {
                if (report.recentLatencyTrend < 200) {
                    return 'high_bandwidth';
                } else if (report.recentLatencyTrend > 800) {
                    return 'low_bandwidth';
                } else {
                    return 'medium_bandwidth';
                }
            }
        }
        
        return 'medium_bandwidth';
    }
    
    detectNetworkStability() {
        // Calculate network stability based on latency variance
        if (window.predictiveLatencyOptimizer && window.predictiveLatencyOptimizer.latencyHistory.length > 5) {
            const recent = window.predictiveLatencyOptimizer.latencyHistory.slice(-10);
            const networkLatencies = recent.map(d => d.network);
            
            const mean = networkLatencies.reduce((a, b) => a + b, 0) / networkLatencies.length;
            const variance = networkLatencies.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / networkLatencies.length;
            const stabilityScore = Math.max(0, 1 - (Math.sqrt(variance) / mean));
            
            return stabilityScore;
        }
        
        return 0.8; // Default good stability
    }
    
    detectUsageContext() {
        // Detect usage context from speech patterns and timing
        const speechPatterns = this.detectSpeechPattern();
        const currentHour = new Date().getHours();
        
        if (speechPatterns.continuous && speechPatterns.consistent) {
            if (currentHour >= 9 && currentHour <= 17) {
                return 'presentation_mode';
            } else {
                return 'interview_mode';
            }
        } else if (speechPatterns.sporadic) {
            return 'casual_use';
        }
        
        return 'general';
    }
    
    selectOptimalProfile(environment) {
        let bestProfile = 'balanced';
        let bestScore = 0;
        
        // Score each profile based on environment
        for (const [profileName, profile] of Object.entries(this.adaptationProfiles)) {
            const score = this.calculateProfileScore(profile, environment);
            
            if (score > bestScore) {
                bestScore = score;
                bestProfile = profileName;
            }
        }
        
        return bestProfile;
    }
    
    calculateProfileScore(profile, environment) {
        let score = 0;
        
        // Device type compatibility
        if (environment.deviceType === 'mobile' && profile.name.includes('Mobile')) {
            score += 30;
        }
        
        // Network condition compatibility
        if (environment.networkStability < 0.5 && profile.name.includes('Low Bandwidth')) {
            score += 25;
        }
        
        // Noise level compatibility
        if (environment.noiseLevel > 0.6 && profile.name.includes('Noisy')) {
            score += 20;
        } else if (environment.noiseLevel < 0.2 && profile.name.includes('Silent')) {
            score += 20;
        }
        
        // Performance requirements
        if (environment.systemLoad > 0.8 && profile.processingSettings.qualityPriority === 'speed') {
            score += 15;
        }
        
        // Transcription accuracy considerations
        if (environment.transcriptionAccuracy < 0.7 && profile.transcriptionSettings.enhancementLevel === 'maximum') {
            score += 10;
        }
        
        return score;
    }
    
    considerProfileSwitch(newProfile, environment) {
        const switchThreshold = 20; // Minimum score difference to switch
        const currentScore = this.calculateProfileScore(this.adaptationProfiles[this.currentProfile], environment);
        const newScore = this.calculateProfileScore(this.adaptationProfiles[newProfile], environment);
        
        if (newScore - currentScore >= switchThreshold) {
            this.switchToProfile(newProfile, `Environmental change detected`);
        }
    }
    
    switchToProfile(profileName, reason) {
        if (profileName === this.currentProfile) return;
        
        console.log(`🔄 Switching to profile: ${this.adaptationProfiles[profileName].name} (${reason})`);
        
        // Record adaptation
        this.adaptationHistory.push({
            timestamp: Date.now(),
            fromProfile: this.currentProfile,
            toProfile: profileName,
            reason: reason,
            environment: { ...this.qualityMetrics }
        });
        
        // Apply new profile
        this.currentProfile = profileName;
        this.applyProfile(profileName);
        
        // Broadcast profile change
        this.broadcastProfileChange(profileName, reason);
    }
    
    applyProfile(profileName) {
        const profile = this.adaptationProfiles[profileName];
        if (!profile) return;
        
        console.log(`🎭 Applying profile: ${profile.name}`);
        
        // Apply audio settings
        this.applyAudioSettings(profile.audioSettings);
        
        // Apply processing settings
        this.applyProcessingSettings(profile.processingSettings);
        
        // Apply transcription settings
        this.applyTranscriptionSettings(profile.transcriptionSettings);
    }
    
    applyAudioSettings(audioSettings) {
        // Apply to audio quality optimizer
        if (window.enhancedSystemIntegration?.audioOptimizer) {
            const optimizer = window.enhancedSystemIntegration.audioOptimizer;
            
            if (optimizer.filters) {
                // Adjust noise gate based on noise suppression setting
                if (audioSettings.noiseSuppression && optimizer.filters.noiseGate) {
                    optimizer.filters.noiseGate.gain.setValueAtTime(0.7, optimizer.audioContext.currentTime);
                } else if (optimizer.filters.noiseGate) {
                    optimizer.filters.noiseGate.gain.setValueAtTime(1.0, optimizer.audioContext.currentTime);
                }
                
                // Adjust compression based on auto gain control
                if (audioSettings.autoGainControl && optimizer.filters.compressor) {
                    optimizer.filters.compressor.ratio.setValueAtTime(4, optimizer.audioContext.currentTime);
                    optimizer.filters.compressor.threshold.setValueAtTime(-20, optimizer.audioContext.currentTime);
                } else if (optimizer.filters.compressor) {
                    optimizer.filters.compressor.ratio.setValueAtTime(2, optimizer.audioContext.currentTime);
                    optimizer.filters.compressor.threshold.setValueAtTime(-24, optimizer.audioContext.currentTime);
                }
            }
        }
    }
    
    applyProcessingSettings(processingSettings) {
        // Apply to performance optimizer
        if (window.performanceOptimizer) {
            const optimizer = window.performanceOptimizer;
            
            // Set chunk size
            optimizer.optimizations.chunkSize = processingSettings.chunkSize;
            
            // Adjust concurrency based on quality priority
            if (processingSettings.qualityPriority === 'speed') {
                optimizer.optimizations.maxConcurrent = Math.min(optimizer.optimizations.maxConcurrent + 1, 4);
            } else if (processingSettings.qualityPriority === 'accuracy') {
                optimizer.optimizations.maxConcurrent = Math.max(optimizer.optimizations.maxConcurrent - 1, 1);
            }
        }
        
        // Apply to intelligent chunking
        if (window.intelligentChunkingOptimizer) {
            const chunking = window.intelligentChunkingOptimizer;
            
            if (processingSettings.qualityPriority === 'completeness') {
                chunking.speechPatterns.optimalChunkDuration = processingSettings.chunkSize;
                chunking.speechPatterns.maxChunkDuration = processingSettings.chunkSize * 1.5;
            }
        }
    }
    
    applyTranscriptionSettings(transcriptionSettings) {
        // Apply to accuracy enhancer
        if (window.transcriptionAccuracyEnhancer) {
            const enhancer = window.transcriptionAccuracyEnhancer;
            
            // Set confidence threshold
            enhancer.wordConfidenceThreshold = transcriptionSettings.confidenceThreshold;
        }
        
        // Apply to ML correction engine
        if (window.adaptiveMLCorrectionEngine) {
            const mlEngine = window.adaptiveMLCorrectionEngine;
            
            // Adjust learning rate based on context analysis level
            if (transcriptionSettings.contextAnalysis === 'deep') {
                mlEngine.adaptiveSettings.learningRate = 0.15;
                mlEngine.adaptiveSettings.contextWindow = 7;
            } else if (transcriptionSettings.contextAnalysis === 'basic') {
                mlEngine.adaptiveSettings.learningRate = 0.05;
                mlEngine.adaptiveSettings.contextWindow = 3;
            } else {
                mlEngine.adaptiveSettings.learningRate = 0.1;
                mlEngine.adaptiveSettings.contextWindow = 5;
            }
        }
    }
    
    processAudioQualityData(audioData) {
        // Update quality metrics from audio data
        this.qualityMetrics.audioClarity = audioData.overallScore || 0;
        this.qualityMetrics.backgroundNoise = this.detectNoiseLevel();
        this.qualityMetrics.speechConsistency = audioData.stability * 100 || 0;
    }
    
    processTranscriptionQuality(transcriptionData) {
        // Update transcription quality metrics
        this.qualityMetrics.transcriptionAccuracy = (transcriptionData.confidence || 0.9) * 100;
    }
    
    processPerformanceData(performanceData) {
        // Update system performance metrics
        this.qualityMetrics.systemPerformance = 100 - ((performanceData.memoryUsage || 0.5) * 100);
    }
    
    updateEnvironmentalProfile(environment) {
        const profileKey = `${environment.deviceType}_${Math.round(environment.noiseLevel * 10)}_${Math.round(environment.networkStability * 10)}`;
        
        this.environmentalProfiles.set(profileKey, {
            timestamp: Date.now(),
            environment: environment,
            profile: this.currentProfile,
            performance: { ...this.qualityMetrics }
        });
        
        // Keep profiles bounded
        if (this.environmentalProfiles.size > 50) {
            const oldest = Array.from(this.environmentalProfiles.keys())[0];
            this.environmentalProfiles.delete(oldest);
        }
    }
    
    evaluateAdaptationNeed() {
        // Check if current performance is degrading
        const performanceScore = (
            this.qualityMetrics.audioClarity +
            this.qualityMetrics.transcriptionAccuracy +
            this.qualityMetrics.systemPerformance
        ) / 3;
        
        if (performanceScore < 60) {
            // Performance is poor, consider emergency adaptation
            this.triggerEmergencyAdaptation();
        }
    }
    
    triggerEmergencyAdaptation() {
        console.log('🚨 Triggering emergency quality adaptation');
        
        // Switch to low bandwidth profile for emergency performance
        if (this.currentProfile !== 'low_bandwidth') {
            this.switchToProfile('low_bandwidth', 'Emergency performance adaptation');
        }
    }
    
    broadcastProfileChange(profileName, reason) {
        const event = new CustomEvent('qualityProfileChanged', {
            detail: {
                profileName: profileName,
                profileData: this.adaptationProfiles[profileName],
                reason: reason,
                qualityMetrics: this.qualityMetrics
            }
        });
        
        window.dispatchEvent(event);
    }
    
    getAdaptationReport() {
        return {
            currentProfile: {
                name: this.currentProfile,
                displayName: this.adaptationProfiles[this.currentProfile].name
            },
            qualityMetrics: this.qualityMetrics,
            adaptationHistory: this.adaptationHistory.slice(-10),
            environmentalProfiles: this.environmentalProfiles.size,
            availableProfiles: Object.keys(this.adaptationProfiles)
        };
    }
    
    stop() {
        this.isActive = false;
        
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
        }
        
        console.log('🛑 Dynamic quality adaptation stopped');
    }
}

// Export for global use
window.DynamicQualityAdaptation = DynamicQualityAdaptation;

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
