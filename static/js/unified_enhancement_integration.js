/**
 * Unified Enhancement Integration - Safe integration of all improvement systems
 * Prevents infinite recursion and ensures all systems work together properly
 */

class UnifiedEnhancementIntegration {
    constructor() {
        this.enhancementSystems = new Map();
        this.isInitialized = false;
        this.originalSetState = null;
        this.isProcessingStateChange = false;
        
        console.info('🔗 Unified enhancement integration initialized');
    }
    
    registerSystem(name, system, startMethod, endMethod) {
        /*Register an enhancement system with the unified integration./*
        this.enhancementSystems.set(name, {
            system: system,
            startMethod: startMethod,
            endMethod: endMethod,
            isActive: false
        });
        
        console.info(`📝 Registered enhancement system: ${name}`);
    }
    
    initialize() {
        /*Initialize the unified integration system./*
        if (this.isInitialized) return;
        
        // Wait for recordingStates to be available
        if (!window.recordingStates || !window.recordingStates.setState) {
            setTimeout(() => this.initialize(), 100);
            return;
        }
        
        // Store the original setState function
        this.originalSetState = window.recordingStates.setState.bind(window.recordingStates);
        
        // Replace with our unified handler
        window.recordingStates.setState = (state, details) => {
            this.handleStateChange(state, details);
        };
        
        this.isInitialized = true;
        console.info('✅ Unified enhancement integration active');
    }
    
    handleStateChange(state, details) {
        /*Handle recording state changes for all systems./*
        // Prevent infinite recursion
        if (this.isProcessingStateChange) {
            return;
        }
        
        this.isProcessingStateChange = true;
        
        try {
            // Call the original setState first
            if (this.originalSetState) {
                this.originalSetState(state, details);
            }
            
            // Handle state changes for all systems
            if (state === 'recording') {
                this.startAllSystems(details);
            } else if (state === 'complete' || state === 'idle') {
                this.endAllSystems();
            }
            
        } catch (error) {
            console.error('State change handling error:', error);
        } finally {
            this.isProcessingStateChange = false;
        }
    }
    
    startAllSystems(details) {
        /*Start all registered enhancement systems./*
        const sessionId = details?.sessionId || `session_${Date.now()}`;
        
        console.info(`🚀 Starting all enhancement systems for session: ${sessionId}`);
        
        this.enhancementSystems.forEach((systemInfo, name) => {
            try {
                if (!systemInfo.isActive && systemInfo.system && systemInfo.startMethod) {
                    systemInfo.system[systemInfo.startMethod](sessionId);
                    systemInfo.isActive = true;
                    console.info(`✅ Started ${name}`);
                }
            } catch (error) {
                console.error(`Failed to start ${name}:`, error);
            }
        });
    }
    
    endAllSystems() {
        /*End all registered enhancement systems./*
        console.info('🏁 Ending all enhancement systems');
        
        this.enhancementSystems.forEach((systemInfo, name) => {
            try {
                if (systemInfo.isActive && systemInfo.system && systemInfo.endMethod) {
                    const report = systemInfo.system[systemInfo.endMethod]();
                    systemInfo.isActive = false;
                    console.info(`📊 ${name} final report:`, report);
                }
            } catch (error) {
                console.error(`Failed to end ${name}:`, error);
            }
        });
    }
    
    getSystemStatus() {
        /*Get status of all enhancement systems./*
        const status = {};
        this.enhancementSystems.forEach((systemInfo, name) => {
            status[name] = {
                registered: true,
                active: systemInfo.isActive,
                available: systemInfo.system !== null
            };
        });
        return status;
    }
}

// Create global unified integration instance
window.unifiedEnhancementIntegration = new UnifiedEnhancementIntegration();

// Auto-register systems when they become available
function registerEnhancementSystems() {
    const integration = window.unifiedEnhancementIntegration;
    
    // Register Live Monitoring Client
    if (window.liveMonitoringClient) {
        integration.registerSystem(
            'liveMonitoring',
            window.liveMonitoringClient,
            'startMonitoring',
            'endMonitoring'
        );
    }
    
    // Register Continuous Improvement Client
    if (window.continuousImprovementClient) {
        integration.registerSystem(
            'continuousImprovement',
            window.continuousImprovementClient,
            'startContinuousImprovement',
            'endContinuousImprovement'
        );
    }
    
    // Register Predictive Performance Client
    if (window.predictivePerformanceClient) {
        integration.registerSystem(
            'predictivePerformance',
            window.predictivePerformanceClient,
            'startPredictiveOptimization',
            'endPredictiveOptimization'
        );
    }
    
    // Register Comprehensive Testing Client
    if (window.comprehensiveTestingClient) {
        integration.registerSystem(
            'comprehensiveTesting',
            window.comprehensiveTestingClient,
            'startComprehensiveTesting',
            'endComprehensiveTesting'
        );
    }
    
    // Register Automatic Session Testing
    if (window.automaticSessionTesting) {
        integration.registerSystem(
            'automaticTesting',
            window.automaticSessionTesting,
            'startTesting',
            'endTesting'
        );
    }
    
    // Initialize the integration
    integration.initialize();
}

// Register systems when DOM is ready and all scripts are loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(registerEnhancementSystems, 500);
    });
} else {
    setTimeout(registerEnhancementSystems, 500);
}

console.info('🔗 Unified enhancement integration ready');