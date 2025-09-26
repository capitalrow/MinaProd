/**
 * INTEGRATION BRIDGE
 * Connects all enhanced systems together for seamless operation
 */

class IntegrationBridge {
    constructor() {
        this.systems = {
            status: window.statusManager,
            metrics: window.metricsManager,
            audio: window.audioValidator,
            transcript: window.transcriptManager
        };
        
        this.transcriptionSystem = null;
        this.isInitialized = false;
    }
    
    initialize() {
        if (this.isInitialized) return;
        
        console.log('🌉 Initializing Integration Bridge');
        
        // Connect to existing transcription system
        this.connectToTranscriptionSystem();
        
        // Override key methods to integrate enhancements
        this.enhanceExistingSystem();
        
        // Set up event listeners
        this.setupEventListeners();
        
        this.isInitialized = true;
        console.log('✅ Integration Bridge initialized');
    }
    
    connectToTranscriptionSystem() {
        // Try to find existing transcription system
        const possibleSystems = [
            window.fixedTranscription,
            window.minaTranscription,
            window.transcriptionSystem,
            window.FixedMinaTranscription
        ];
        
        for (const system of possibleSystems) {
            if (system && typeof system === 'object') {
                this.transcriptionSystem = system;
                console.log('🔗 Connected to existing transcription system');
                break;
            }
        }
    }
    
    enhanceExistingSystem() {
        if (!this.transcriptionSystem) return;
        
        // Override processAudioChunk method
        const originalProcessAudioChunk = this.transcriptionSystem.processAudioChunk;
        if (originalProcessAudioChunk) {
            this.transcriptionSystem.processAudioChunk = async (audioBlob) => {
                return this.enhancedProcessAudioChunk(audioBlob, originalProcessAudioChunk);
            };
        }
        
        // Override updateUI method
        const originalUpdateUI = this.transcriptionSystem.updateUI;
        if (originalUpdateUI) {
            this.transcriptionSystem.updateUI = (result) => {
                this.enhancedUpdateUI(result, originalUpdateUI);
            };
        }
        
        // Override handleTranscriptionResult method
        const originalHandleResult = this.transcriptionSystem.handleTranscriptionResult;
        if (originalHandleResult) {
            this.transcriptionSystem.handleTranscriptionResult = (result) => {
                this.enhancedHandleTranscriptionResult(result, originalHandleResult);
            };
        }
        
        console.log('🔧 Enhanced existing transcription system');
    }
    
    async enhancedProcessAudioChunk(audioBlob, originalMethod) {
        try {
            // Clear any error states
            this.systems.status.updateStatus('processing', 'Audio chunk processing');
            
            // Validate audio with our enhanced validator
            const validation = this.systems.audio.validateAudioBlob(audioBlob);
            
            if (!validation.isValid) {
                console.warn('⚠️ Audio validation failed:', validation.issues);
                this.systems.status.updateStatus('error', 'Audio quality issue');
                return;
            }
            
            // Call original method
            const result = await originalMethod.call(this.transcriptionSystem, audioBlob);
            
            // Update status on success
            this.systems.status.updateStatus('transcribing', 'Processing complete');
            
            return result;
            
        } catch (error) {
            console.error('❌ Enhanced processing error:', error);
            this.systems.status.updateStatus('error', error.message);
            throw error;
        }
    }
    
    enhancedUpdateUI(result, originalMethod) {
        try {
            // Update metrics with our enhanced manager
            if (this.systems.metrics) {
                this.systems.metrics.updateFromResult(result);
            }
            
            // Call original method if it exists
            if (originalMethod) {
                originalMethod.call(this.transcriptionSystem, result);
            }
            
            // Clear any error states on successful UI update
            this.systems.status.updateStatus('ready', 'UI updated');
            
        } catch (error) {
            console.error('❌ Enhanced UI update error:', error);
            this.systems.status.updateStatus('error', 'UI update failed');
        }
    }
    
    enhancedHandleTranscriptionResult(result, originalMethod) {
        try {
            // Use our enhanced transcript manager
            if (result.text && this.systems.transcript) {
                const added = this.systems.transcript.addTranscript(
                    result.text, 
                    result.confidence || 0.9
                );
                
                if (added) {
                    console.log('📝 Transcript added via enhanced manager');
                } else {
                    console.log('🔄 Transcript filtered (duplicate or invalid)');
                }
            }
            
            // Call original method if it exists
            if (originalMethod) {
                originalMethod.call(this.transcriptionSystem, result);
            }
            
            // Update status
            this.systems.status.updateStatus('ready', 'Transcription processed');
            
        } catch (error) {
            console.error('❌ Enhanced transcription handling error:', error);
            this.systems.status.updateStatus('error', 'Transcription handling failed');
        }
    }
    
    setupEventListeners() {
        // Listen for recording state changes
        document.addEventListener('recordingStateChange', (event) => {
            const { state, context } = event.detail;
            this.systems.status.updateStatus(state, context);
        });
        
        // Listen for metrics updates
        document.addEventListener('metricsUpdate', (event) => {
            const { metrics } = event.detail;
            Object.keys(metrics).forEach(key => {
                this.systems.metrics.updateMetric(key, metrics[key]);
            });
        });
        
        // Listen for transcription events
        document.addEventListener('transcriptionReceived', (event) => {
            const { text, confidence } = event.detail;
            this.systems.transcript.addTranscript(text, confidence);
        });
        
        console.log('👂 Event listeners set up');
    }
    
    // Public API methods
    updateChunkCount(count) {
        this.systems.metrics.updateMetric('chunks', count);
    }
    
    updateLatency(latencyMs) {
        this.systems.metrics.updateMetric('latency', latencyMs);
    }
    
    updateQuality(qualityPercentage) {
        this.systems.metrics.updateMetric('quality', qualityPercentage);
    }
    
    updateAccuracy(accuracyPercentage) {
        this.systems.metrics.updateMetric('accuracy', accuracyPercentage);
    }
    
    updateWordCount(count) {
        this.systems.metrics.updateMetric('words', count);
    }
    
    showStatus(status, context = '') {
        this.systems.status.updateStatus(status, context);
    }
    
    resetAll() {
        this.systems.metrics.resetMetrics();
        this.systems.transcript.clearTranscripts();
        this.systems.status.updateStatus('ready', 'System reset');
    }
    
    // Health check
    performHealthCheck() {
        const health = {
            status: 'healthy',
            systems: {},
            issues: []
        };
        
        // Check each system
        Object.keys(this.systems).forEach(systemName => {
            const system = this.systems[systemName];
            if (system && typeof system === 'object') {
                health.systems[systemName] = 'active';
            } else {
                health.systems[systemName] = 'inactive';
                health.issues.push(`${systemName} system not available`);
            }
        });
        
        // Check transcription system
        if (this.transcriptionSystem) {
            health.systems.transcription = 'connected';
        } else {
            health.systems.transcription = 'disconnected';
            health.issues.push('Transcription system not connected');
        }
        
        // Overall status
        if (health.issues.length > 0) {
            health.status = 'degraded';
        }
        
        return health;
    }
}

// Initialize bridge when DOM is ready
let integrationBridge = null;

document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for other systems to initialize
    setTimeout(() => {
        integrationBridge = new IntegrationBridge();
        integrationBridge.initialize();
        
        // Make available globally for debugging
        window.integrationBridge = integrationBridge;
        
        // Perform initial health check
        const health = integrationBridge.performHealthCheck();
        console.log('🏥 Integration Bridge Health Check:', health);
        
    }, 1000);
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { IntegrationBridge };
}

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
