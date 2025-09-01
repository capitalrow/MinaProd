/**
 * 🌉 ENHANCED INTEGRATION BRIDGE
 * Fixes the core integration issues preventing transcription from working
 */

class EnhancedIntegrationBridge {
    constructor() {
        this.initialized = false;
        this.systems = {
            realWhisperIntegration: false,
            performanceIntegration: false,
            pipelinePerformance: false,
            comprehensiveQA: false,
            robustnessEnhancements: false,
            uiAccessibility: false
        };
        
        this.initializationPromise = null;
        this.healthCheckInterval = null;
        
        console.log('🌉 Enhanced Integration Bridge starting...');
    }
    
    /**
     * Initialize all systems with proper dependency management
     */
    async initialize() {
        if (this.initializationPromise) {
            return this.initializationPromise;
        }
        
        this.initializationPromise = this._doInitialize();
        return this.initializationPromise;
    }
    
    async _doInitialize() {
        console.log('🔄 Starting system initialization...');
        
        try {
            // Phase 1: Initialize core systems
            await this.initializeRealWhisperIntegration();
            
            // Phase 2: Initialize performance monitoring
            await this.initializePerformanceMonitoring();
            
            // Phase 3: Initialize QA pipeline
            await this.initializeQAPipeline();
            
            // Phase 4: Initialize robustness features
            await this.initializeRobustnessEnhancements();
            
            // Phase 5: Initialize accessibility features
            await this.initializeUIAccessibility();
            
            // Start health monitoring
            this.startHealthMonitoring();
            
            this.initialized = true;
            console.log('✅ All systems initialized successfully');
            
            return { success: true, systems: this.systems };
            
        } catch (error) {
            console.error('❌ System initialization failed:', error);
            return { success: false, error: error.message, systems: this.systems };
        }
    }
    
    /**
     * Initialize RealWhisperIntegration with proper error handling
     */
    async initializeRealWhisperIntegration() {
        try {
            console.log('🎤 Initializing RealWhisperIntegration...');
            
            // Wait for RealWhisperIntegration class to be available
            let attempts = 0;
            while (typeof RealWhisperIntegration === 'undefined' && attempts < 10) {
                console.log(`⏳ Waiting for RealWhisperIntegration class... (attempt ${attempts + 1}/10)`);
                await new Promise(resolve => setTimeout(resolve, 500));
                attempts++;
            }
            
            if (typeof RealWhisperIntegration === 'undefined') {
                throw new Error('RealWhisperIntegration class not loaded after 10 attempts');
            }
            
            // Create instance if not exists
            if (!window.realWhisperIntegration) {
                window.realWhisperIntegration = new RealWhisperIntegration();
                console.log('✅ RealWhisperIntegration instance created');
            }
            
            // Configure correct endpoints
            if (window.realWhisperIntegration) {
                window.realWhisperIntegration.httpEndpoint = '/api/transcribe-audio';
                window.realWhisperIntegration.streamingEndpoint = '/api/transcribe-audio';
                
                this.systems.realWhisperIntegration = true;
                console.log('✅ RealWhisperIntegration initialized with correct endpoints');
            } else {
                throw new Error('Failed to create RealWhisperIntegration instance');
            }
            
        } catch (error) {
            console.error('❌ RealWhisperIntegration initialization failed:', error);
            this.systems.realWhisperIntegration = false;
        }
    }
    
    /**
     * Initialize performance monitoring systems
     */
    async initializePerformanceMonitoring() {
        try {
            console.log('📊 Initializing performance monitoring...');
            
            // Check performance integration bridge
            if (window.performanceIntegrationBridge) {
                this.systems.performanceIntegration = true;
                console.log('✅ Performance Integration Bridge available');
            } else if (typeof PerformanceIntegrationBridge !== 'undefined') {
                window.performanceIntegrationBridge = new PerformanceIntegrationBridge();
                this.systems.performanceIntegration = true;
                console.log('✅ Performance Integration Bridge created');
            }
            
            // Check pipeline performance
            if (window.pipelinePerformance) {
                this.systems.pipelinePerformance = true;
                console.log('✅ Pipeline Performance available');
            } else if (typeof PipelinePerformanceIntegration !== 'undefined') {
                window.pipelinePerformance = new PipelinePerformanceIntegration();
                this.systems.pipelinePerformance = true;
                console.log('✅ Pipeline Performance created');
            }
            
            // Test profiler endpoint
            try {
                const response = await fetch('/api/profiler/status');
                if (response.ok) {
                    console.log('✅ Profiler endpoint accessible');
                } else {
                    console.warn('⚠️ Profiler endpoint returned:', response.status);
                }
            } catch (error) {
                console.warn('⚠️ Profiler endpoint not accessible:', error.message);
            }
            
        } catch (error) {
            console.error('❌ Performance monitoring initialization failed:', error);
        }
    }
    
    /**
     * Initialize QA pipeline
     */
    async initializeQAPipeline() {
        try {
            console.log('🔬 Initializing QA pipeline...');
            
            // Check if QA pipeline exists
            if (window.comprehensiveQA) {
                this.systems.comprehensiveQA = true;
                console.log('✅ Comprehensive QA available');
            } else if (typeof ComprehensiveQAPipeline !== 'undefined') {
                // Create instance if class exists but instance doesn't
                window.comprehensiveQA = new ComprehensiveQAPipeline();
                this.systems.comprehensiveQA = true;
                console.log('✅ Comprehensive QA initialized');
            } else {
                console.warn('⚠️ Comprehensive QA not available');
                this.systems.comprehensiveQA = false;
            }
            
        } catch (error) {
            console.error('❌ QA pipeline initialization failed:', error);
            this.systems.comprehensiveQA = false;
        }
    }
    
    /**
     * Initialize robustness enhancements
     */
    async initializeRobustnessEnhancements() {
        try {
            console.log('🛡️ Initializing robustness enhancements...');
            
            if (window.robustnessEnhancements) {
                this.systems.robustnessEnhancements = true;
                console.log('✅ Robustness enhancements available');
            } else if (typeof RobustnessEnhancements !== 'undefined') {
                window.robustnessEnhancements = new RobustnessEnhancements();
                this.systems.robustnessEnhancements = true;
                console.log('✅ Robustness enhancements initialized');
            } else {
                console.warn('⚠️ Robustness enhancements not available');
                this.systems.robustnessEnhancements = false;
            }
            
        } catch (error) {
            console.error('❌ Robustness enhancements initialization failed:', error);
            this.systems.robustnessEnhancements = false;
        }
    }
    
    /**
     * Initialize UI accessibility features
     */
    async initializeUIAccessibility() {
        try {
            console.log('♿ Initializing UI accessibility...');
            
            if (window.uiAccessibility) {
                // Initialize accessibility features
                if (typeof window.uiAccessibility.initialize === 'function') {
                    window.uiAccessibility.initialize();
                }
                this.systems.uiAccessibility = true;
                console.log('✅ UI accessibility available');
            } else if (typeof UIAccessibilityEnhancements !== 'undefined') {
                window.uiAccessibility = new UIAccessibilityEnhancements();
                window.uiAccessibility.initialize();
                this.systems.uiAccessibility = true;
                console.log('✅ UI accessibility initialized');
            } else {
                console.warn('⚠️ UI accessibility not available');
                this.systems.uiAccessibility = false;
            }
            
        } catch (error) {
            console.error('❌ UI accessibility initialization failed:', error);
            this.systems.uiAccessibility = false;
        }
    }
    
    /**
     * Start continuous health monitoring
     */
    startHealthMonitoring() {
        // Update system status every 3 seconds
        this.healthCheckInterval = setInterval(() => {
            this.updateSystemHealth();
        }, 3000);
        
        console.log('🔍 Health monitoring started');
    }
    
    /**
     * Update system health indicators in UI
     */
    async updateSystemHealth() {
        try {
            // Update microphone status
            const micStatus = document.getElementById('micStatus');
            if (micStatus) {
                const hasPermission = await this.checkMicrophonePermission();
                micStatus.className = hasPermission ? 'badge bg-success' : 'badge bg-warning';
                micStatus.innerHTML = hasPermission ? 
                    '<i class="bi bi-mic"></i> Microphone: Ready' : 
                    '<i class="bi bi-mic-mute"></i> Microphone: Permission Required';
            }
            
            // Update connection status
            const wsStatus = document.getElementById('wsStatus');
            if (wsStatus) {
                const isConnected = this.systems.realWhisperIntegration;
                wsStatus.className = isConnected ? 'badge bg-success' : 'badge bg-danger';
                wsStatus.innerHTML = isConnected ? 
                    '<i class="bi bi-wifi"></i> Connection: Ready' : 
                    '<i class="bi bi-wifi-off"></i> Connection: Disconnected';
            }
            
            // Update transcription status
            const transcriptionStatus = document.getElementById('transcriptionStatus');
            if (transcriptionStatus) {
                const isWorking = this.systems.realWhisperIntegration;
                transcriptionStatus.className = isWorking ? 'badge bg-success' : 'badge bg-warning';
                transcriptionStatus.innerHTML = isWorking ? 
                    '<i class="bi bi-cpu"></i> Transcription: Ready' : 
                    '<i class="bi bi-cpu"></i> Transcription: Initializing';
            }
            
            // Update performance status
            const performanceStatus = document.getElementById('performanceStatus');
            if (performanceStatus) {
                const isMonitoring = this.systems.performanceIntegration || this.systems.pipelinePerformance;
                performanceStatus.className = isMonitoring ? 'badge bg-success' : 'badge bg-secondary';
                performanceStatus.innerHTML = isMonitoring ? 
                    '<i class="bi bi-speedometer2"></i> Performance: Monitoring' : 
                    '<i class="bi bi-speedometer2"></i> Performance: Unknown';
            }
            
            // Update main connection status
            const connectionStatus = document.getElementById('connectionStatus');
            if (connectionStatus) {
                const allReady = this.systems.realWhisperIntegration;
                connectionStatus.textContent = allReady ? 'Ready' : 'Connecting...';
            }
            
            const statusIndicator = document.getElementById('statusIndicator');
            if (statusIndicator) {
                const allReady = this.systems.realWhisperIntegration;
                statusIndicator.className = allReady ? 'bi bi-circle-fill text-success' : 'bi bi-circle-fill text-warning';
            }
            
        } catch (error) {
            console.error('Error updating system health:', error);
        }
    }
    
    /**
     * Check microphone permission status
     */
    async checkMicrophonePermission() {
        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                return false;
            }
            
            // Check permission state if available
            if (navigator.permissions) {
                try {
                    const permission = await navigator.permissions.query({ name: 'microphone' });
                    return permission.state === 'granted';
                } catch (error) {
                    // Permission API not available or failed
                }
            }
            
            // Fallback: try to access microphone briefly
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                stream.getTracks().forEach(track => track.stop());
                return true;
            } catch (error) {
                return false;
            }
            
        } catch (error) {
            console.error('Error checking microphone permission:', error);
            return false;
        }
    }
    
    /**
     * Get current system diagnostics
     */
    getDiagnostics() {
        return {
            initialized: this.initialized,
            systems: { ...this.systems },
            timestamp: new Date().toISOString()
        };
    }
    
    /**
     * Force restart of a specific system
     */
    async restartSystem(systemName) {
        console.log(`🔄 Restarting ${systemName}...`);
        
        try {
            switch (systemName) {
                case 'realWhisperIntegration':
                    await this.initializeRealWhisperIntegration();
                    break;
                case 'performanceIntegration':
                    await this.initializePerformanceMonitoring();
                    break;
                case 'comprehensiveQA':
                    await this.initializeQAPipeline();
                    break;
                case 'robustnessEnhancements':
                    await this.initializeRobustnessEnhancements();
                    break;
                case 'uiAccessibility':
                    await this.initializeUIAccessibility();
                    break;
                default:
                    throw new Error(`Unknown system: ${systemName}`);
            }
            
            console.log(`✅ ${systemName} restarted successfully`);
            return true;
            
        } catch (error) {
            console.error(`❌ Failed to restart ${systemName}:`, error);
            return false;
        }
    }
    
    /**
     * Cleanup resources
     */
    cleanup() {
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
            this.healthCheckInterval = null;
        }
        
        console.log('🧹 Enhanced Integration Bridge cleaned up');
    }
}

// Initialize the enhanced integration bridge
window.enhancedIntegrationBridge = new EnhancedIntegrationBridge();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Starting enhanced integration bridge initialization...');
    
    // Wait a bit for all scripts to load
    setTimeout(async () => {
        const result = await window.enhancedIntegrationBridge.initialize();
        
        if (result.success) {
            console.log('✅ All systems ready for transcription');
        } else {
            console.error('❌ System initialization incomplete:', result.error);
            console.warn('⚠️ Some features may not work correctly');
        }
    }, 1000);
});

console.log('✅ Enhanced Integration Bridge loaded');