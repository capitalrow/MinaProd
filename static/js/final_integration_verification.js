/**
 * 🔍 FINAL INTEGRATION VERIFICATION
 * Verifies all performance optimizations are properly connected and working
 */

class FinalIntegrationVerification {
    constructor() {
        this.verificationResults = {};
        this.systemsChecked = [];
        
        console.log('🔍 Final Integration Verification starting...');
    }
    
    /**
     * Run comprehensive verification of all integrated systems
     */
    async runFullVerification() {
        console.log('🔍 Running comprehensive system verification...');
        
        try {
            // Verify core performance systems
            await this.verifyVADOptimization();
            await this.verifyAdaptiveChunking();
            await this.verifyBinaryWebSocket();
            
            // Verify monitoring and QA systems
            await this.verifyPerformanceMonitoring();
            await this.verifyAutomatedQA();
            
            // Verify mobile optimizations
            await this.verifyMobileOptimization();
            
            // Verify integration bridge
            await this.verifyIntegrationBridge();
            
            // Verify WER calculator
            await this.verifyWERCalculator();
            
            // Generate final report
            const report = this.generateVerificationReport();
            this.displayVerificationResults(report);
            
            return report;
            
        } catch (error) {
            console.error('❌ Verification failed:', error);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Verify VAD Optimization system
     */
    async verifyVADOptimization() {
        const systemName = 'VAD Optimization';
        const results = {
            systemAvailable: !!window.vadOptimization,
            configurable: false,
            functional: false,
            apiReduction: 0
        };
        
        if (window.vadOptimization) {
            try {
                // Test configuration
                window.vadOptimization.configure({
                    silenceThreshold: 0.01,
                    speechThreshold: 0.03
                });
                results.configurable = true;
                
                // Test functionality with dummy data
                const dummyAudio = new Float32Array(1000).fill(0.05); // Simulate speech
                const vadResult = window.vadOptimization.analyzeAudioChunk(dummyAudio);
                results.functional = vadResult && typeof vadResult.vadState === 'string';
                
                // Get statistics
                const stats = window.vadOptimization.getStatistics();
                results.apiReduction = stats.apiCallReduction || 0;
                
            } catch (error) {
                console.error(`❌ ${systemName} verification error:`, error);
            }
        }
        
        this.verificationResults[systemName] = results;
        this.systemsChecked.push(systemName);
        
        const status = results.systemAvailable && results.configurable && results.functional ? '✅' : '❌';
        console.log(`${status} ${systemName}: Available=${results.systemAvailable}, Functional=${results.functional}`);
    }
    
    /**
     * Verify Adaptive Chunking system
     */
    async verifyAdaptiveChunking() {
        const systemName = 'Adaptive Chunking';
        const results = {
            systemAvailable: !!window.adaptiveChunking,
            configurable: false,
            functional: false,
            adaptationEvents: 0
        };
        
        if (window.adaptiveChunking) {
            try {
                // Test configuration
                window.adaptiveChunking.configure({
                    minChunkSize: 1000,
                    maxChunkSize: 3000
                });
                results.configurable = true;
                
                // Test functionality with dummy data
                const dummyAudio = new Float32Array(2000).fill(0.03); // Simulate audio
                const chunkResult = window.adaptiveChunking.analyzeAndAdaptChunkSize(dummyAudio, {
                    confidence: 0.8,
                    processingTime: 150
                });
                results.functional = chunkResult && typeof chunkResult.recommendedChunkSize === 'number';
                
                // Get statistics
                const stats = window.adaptiveChunking.getStatistics();
                results.adaptationEvents = stats.adaptationEvents || 0;
                
            } catch (error) {
                console.error(`❌ ${systemName} verification error:`, error);
            }
        }
        
        this.verificationResults[systemName] = results;
        this.systemsChecked.push(systemName);
        
        const status = results.systemAvailable && results.configurable && results.functional ? '✅' : '❌';
        console.log(`${status} ${systemName}: Available=${results.systemAvailable}, Functional=${results.functional}`);
    }
    
    /**
     * Verify Binary WebSocket system
     */
    async verifyBinaryWebSocket() {
        const systemName = 'Binary WebSocket';
        const results = {
            systemAvailable: !!window.binaryWebSocket,
            configurable: false,
            connectionReady: false,
            messageHandling: false
        };
        
        if (window.binaryWebSocket) {
            try {
                // Test basic functionality
                results.configurable = typeof window.binaryWebSocket.setSessionId === 'function';
                results.connectionReady = typeof window.binaryWebSocket.connect === 'function';
                results.messageHandling = typeof window.binaryWebSocket.sendBinaryAudio === 'function';
                
            } catch (error) {
                console.error(`❌ ${systemName} verification error:`, error);
            }
        }
        
        this.verificationResults[systemName] = results;
        this.systemsChecked.push(systemName);
        
        const status = results.systemAvailable && results.configurable && results.connectionReady ? '✅' : '❌';
        console.log(`${status} ${systemName}: Available=${results.systemAvailable}, Ready=${results.connectionReady}`);
    }
    
    /**
     * Verify Performance Monitoring system
     */
    async verifyPerformanceMonitoring() {
        const systemName = 'Performance Monitoring';
        const results = {
            systemAvailable: !!window.performanceDashboard,
            dashboardReady: false,
            metricsRecording: false,
            reportGeneration: false
        };
        
        if (window.performanceDashboard) {
            try {
                // Test dashboard functionality
                results.dashboardReady = typeof window.performanceDashboard.toggle === 'function';
                results.metricsRecording = typeof window.performanceDashboard.recordTranscriptionMetrics === 'function';
                results.reportGeneration = typeof window.performanceDashboard.generateReport === 'function';
                
                // Test metrics recording
                window.performanceDashboard.recordTranscriptionMetrics({
                    processingTime: 200,
                    confidence: 0.9,
                    text: 'Test verification'
                });
                
            } catch (error) {
                console.error(`❌ ${systemName} verification error:`, error);
            }
        }
        
        this.verificationResults[systemName] = results;
        this.systemsChecked.push(systemName);
        
        const status = results.systemAvailable && results.dashboardReady && results.metricsRecording ? '✅' : '❌';
        console.log(`${status} ${systemName}: Available=${results.systemAvailable}, Recording=${results.metricsRecording}`);
    }
    
    /**
     * Verify Automated QA system
     */
    async verifyAutomatedQA() {
        const systemName = 'Automated QA';
        const results = {
            systemAvailable: !!window.automatedQA,
            sessionManagement: false,
            qualityAnalysis: false,
            reporting: false
        };
        
        if (window.automatedQA) {
            try {
                // Test session management
                const testSessionId = 'verification_test';
                window.automatedQA.startQASession(testSessionId);
                results.sessionManagement = window.automatedQA.qaSession?.id === testSessionId;
                
                // Test quality analysis
                window.automatedQA.addTranscriptSegment('Test transcript', 0.9, 150);
                results.qualityAnalysis = window.automatedQA.transcriptBuffer.length > 0;
                
                // Test reporting
                results.reporting = typeof window.automatedQA.getStatistics === 'function';
                
                // Clean up
                window.automatedQA.endQASession();
                
            } catch (error) {
                console.error(`❌ ${systemName} verification error:`, error);
            }
        }
        
        this.verificationResults[systemName] = results;
        this.systemsChecked.push(systemName);
        
        const status = results.systemAvailable && results.sessionManagement && results.qualityAnalysis ? '✅' : '❌';
        console.log(`${status} ${systemName}: Available=${results.systemAvailable}, Analysis=${results.qualityAnalysis}`);
    }
    
    /**
     * Verify Mobile Optimization system
     */
    async verifyMobileOptimization() {
        const systemName = 'Mobile Optimization';
        const results = {
            systemAvailable: !!window.mobileOptimizer,
            deviceDetection: false,
            performanceManagement: false,
            batteryOptimization: false
        };
        
        if (window.mobileOptimizer) {
            try {
                // Test device detection
                results.deviceDetection = typeof window.mobileOptimizer.isMobile === 'boolean';
                
                // Test performance management
                results.performanceManagement = typeof window.mobileOptimizer.setPerformanceLevel === 'function';
                
                // Test battery optimization features
                results.batteryOptimization = typeof window.mobileOptimizer.getStatistics === 'function';
                
            } catch (error) {
                console.error(`❌ ${systemName} verification error:`, error);
            }
        }
        
        this.verificationResults[systemName] = results;
        this.systemsChecked.push(systemName);
        
        const status = results.systemAvailable && results.deviceDetection && results.performanceManagement ? '✅' : '❌';
        console.log(`${status} ${systemName}: Available=${results.systemAvailable}, Mobile=${results.deviceDetection}`);
    }
    
    /**
     * Verify Integration Bridge system
     */
    async verifyIntegrationBridge() {
        const systemName = 'Integration Bridge';
        const results = {
            systemAvailable: !!window.performanceIntegrationBridge,
            integrated: false,
            realWhisperConnection: false,
            patchedMethods: 0
        };
        
        if (window.performanceIntegrationBridge) {
            try {
                // Test integration status
                const status = window.performanceIntegrationBridge.getStatus();
                results.integrated = status.integrated;
                results.realWhisperConnection = status.realWhisperIntegration;
                results.patchedMethods = status.patchedMethods.length;
                
            } catch (error) {
                console.error(`❌ ${systemName} verification error:`, error);
            }
        }
        
        this.verificationResults[systemName] = results;
        this.systemsChecked.push(systemName);
        
        const status = results.systemAvailable && results.integrated ? '✅' : '❌';
        console.log(`${status} ${systemName}: Available=${results.systemAvailable}, Integrated=${results.integrated}`);
    }
    
    /**
     * Verify WER Calculator system
     */
    async verifyWERCalculator() {
        const systemName = 'WER Calculator';
        const results = {
            systemAvailable: !!window.realTimeWERCalculator,
            werCalculation: false,
            analysisGeneration: false,
            dataExport: false
        };
        
        if (window.realTimeWERCalculator) {
            try {
                // Test WER calculation
                const testWER = window.realTimeWERCalculator.calculateWEREstimate('Test transcript', 0.9);
                results.werCalculation = typeof testWER === 'number';
                
                // Test analysis generation
                const analysis = window.realTimeWERCalculator.getDetailedAnalysis();
                results.analysisGeneration = analysis && typeof analysis.wer === 'number';
                
                // Test data export
                results.dataExport = typeof window.realTimeWERCalculator.exportData === 'function';
                
            } catch (error) {
                console.error(`❌ ${systemName} verification error:`, error);
            }
        }
        
        this.verificationResults[systemName] = results;
        this.systemsChecked.push(systemName);
        
        const status = results.systemAvailable && results.werCalculation && results.analysisGeneration ? '✅' : '❌';
        console.log(`${status} ${systemName}: Available=${results.systemAvailable}, Calculating=${results.werCalculation}`);
    }
    
    /**
     * Generate comprehensive verification report
     */
    generateVerificationReport() {
        const totalSystems = this.systemsChecked.length;
        let fullyFunctional = 0;
        let partiallyFunctional = 0;
        let nonFunctional = 0;
        
        const systemDetails = [];
        
        for (const [systemName, results] of Object.entries(this.verificationResults)) {
            const functionalAspects = Object.values(results).filter(v => v === true).length;
            const totalAspects = Object.values(results).length;
            const functionalPercentage = (functionalAspects / totalAspects) * 100;
            
            let status;
            if (functionalPercentage >= 80) {
                status = 'Fully Functional';
                fullyFunctional++;
            } else if (functionalPercentage >= 50) {
                status = 'Partially Functional';
                partiallyFunctional++;
            } else {
                status = 'Non-Functional';
                nonFunctional++;
            }
            
            systemDetails.push({
                name: systemName,
                status: status,
                functionality: functionalPercentage,
                details: results
            });
        }
        
        const overallHealth = (fullyFunctional / totalSystems) * 100;
        
        return {
            timestamp: new Date().toISOString(),
            overallHealth: Math.round(overallHealth),
            totalSystems: totalSystems,
            systemStats: {
                fullyFunctional: fullyFunctional,
                partiallyFunctional: partiallyFunctional,
                nonFunctional: nonFunctional
            },
            systemDetails: systemDetails,
            gapsIdentified: this.identifyRemainingGaps(),
            recommendations: this.generateRecommendations()
        };
    }
    
    /**
     * Identify remaining gaps in the system
     */
    identifyRemainingGaps() {
        const gaps = [];
        
        for (const [systemName, results] of Object.entries(this.verificationResults)) {
            if (!results.systemAvailable) {
                gaps.push(`${systemName} system is not available`);
                continue;
            }
            
            const failedAspects = Object.entries(results)
                .filter(([key, value]) => value === false)
                .map(([key]) => key);
                
            if (failedAspects.length > 0) {
                gaps.push(`${systemName}: ${failedAspects.join(', ')} not working`);
            }
        }
        
        // Check for integration gaps
        if (!window.realWhisperIntegration) {
            gaps.push('RealWhisperIntegration not available - optimizations may not be connected');
        }
        
        if (window.performanceIntegrationBridge && !window.performanceIntegrationBridge.isIntegrated) {
            gaps.push('Performance systems not fully integrated with transcription pipeline');
        }
        
        return gaps;
    }
    
    /**
     * Generate recommendations for fixing gaps
     */
    generateRecommendations() {
        const recommendations = [];\n        const gaps = this.identifyRemainingGaps();\n        \n        if (gaps.length === 0) {\n            recommendations.push('All systems are functioning correctly - no immediate action required');\n            recommendations.push('Monitor performance metrics during actual usage');\n            recommendations.push('Run periodic verification checks');\n        } else {\n            recommendations.push('Fix identified gaps to achieve target performance');\n            \n            if (gaps.some(gap => gap.includes('not available'))) {\n                recommendations.push('Ensure all JavaScript files are loaded correctly');\n                recommendations.push('Check for JavaScript errors in browser console');\n            }\n            \n            if (gaps.some(gap => gap.includes('integration'))) {\n                recommendations.push('Verify RealWhisperIntegration is loaded before optimization systems');\n                recommendations.push('Check integration bridge configuration');\n            }\n            \n            if (gaps.some(gap => gap.includes('functional'))) {\n                recommendations.push('Test individual system components for proper functionality');\n                recommendations.push('Review system configuration and initialization order');\n            }\n        }\n        \n        return recommendations;\n    }\n    \n    /**\n     * Display verification results\n     */\n    displayVerificationResults(report) {\n        console.log('\\n📊 FINAL INTEGRATION VERIFICATION REPORT');\n        console.log('='.repeat(50));\n        console.log(`Overall System Health: ${report.overallHealth}%`);\n        console.log(`Total Systems Checked: ${report.totalSystems}`);\n        console.log(`✅ Fully Functional: ${report.systemStats.fullyFunctional}`);\n        console.log(`⚠️ Partially Functional: ${report.systemStats.partiallyFunctional}`);\n        console.log(`❌ Non-Functional: ${report.systemStats.nonFunctional}`);\n        \n        console.log('\\n📋 System Details:');\n        for (const system of report.systemDetails) {\n            const icon = system.functionality >= 80 ? '✅' : system.functionality >= 50 ? '⚠️' : '❌';\n            console.log(`${icon} ${system.name}: ${system.status} (${system.functionality.toFixed(0)}%)`);\n        }\n        \n        if (report.gapsIdentified.length > 0) {\n            console.log('\\n🔍 Identified Gaps:');\n            report.gapsIdentified.forEach(gap => console.log(`• ${gap}`));\n        }\n        \n        console.log('\\n💡 Recommendations:');\n        report.recommendations.forEach(rec => console.log(`• ${rec}`));\n        \n        console.log('\\n' + '='.repeat(50));\n        \n        // Show summary notification if available\n        if (window.showNotification) {\n            const statusType = report.overallHealth >= 80 ? 'success' : \n                              report.overallHealth >= 50 ? 'warning' : 'error';\n            \n            window.showNotification(\n                'System Verification Complete',\n                `Overall Health: ${report.overallHealth}% (${report.systemStats.fullyFunctional}/${report.totalSystems} systems fully functional)`,\n                statusType\n            );\n        }\n    }\n    \n    /**\n     * Export verification report\n     */\n    exportReport() {\n        const report = this.generateVerificationReport();\n        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });\n        const url = URL.createObjectURL(blob);\n        \n        const a = document.createElement('a');\n        a.href = url;\n        a.download = `mina-verification-report-${Date.now()}.json`;\n        document.body.appendChild(a);\n        a.click();\n        document.body.removeChild(a);\n        URL.revokeObjectURL(url);\n        \n        return report;\n    }\n}\n\n// Initialize verification system\nwindow.integrationVerification = new FinalIntegrationVerification();\n\n// Auto-run verification after all systems are loaded\nwindow.addEventListener('load', () => {\n    // Delay to ensure all systems are initialized\n    setTimeout(() => {\n        window.integrationVerification.runFullVerification();\n    }, 3000);\n});\n\nconsole.log('✅ Final Integration Verification loaded');"