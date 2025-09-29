/**
 * REAL-TIME QUALITY MONITOR
 * Comprehensive monitoring and adaptive optimization dashboard
 */

class RealTimeQualityMonitor {
    constructor() {
        this.isMonitoring = false;
        this.metrics = {
            audio: {
                quality: 0,
                snr: 0,
                volume: 0,
                clarity: 0,
                stability: 0
            },
            transcription: {
                accuracy: 0,
                confidence: 0,
                latency: 0,
                completeness: 0,
                errorRate: 0
            },
            system: {
                cpuUsage: 0,
                memoryUsage: 0,
                networkLatency: 0,
                throughput: 0,
                queueLength: 0
            },
            performance: {
                endToEndLatency: 0,
                chunkProcessingTime: 0,
                enhancementTime: 0,
                displayTime: 0
            }
        };
        
        this.history = {
            audio: [],
            transcription: [],
            system: [],
            performance: []
        };
        
        this.thresholds = {
            audio: { excellent: 85, good: 70, poor: 50 },
            transcription: { excellent: 95, good: 85, poor: 70 },
            system: { excellent: 30, good: 60, poor: 85 },
            performance: { excellent: 400, good: 1000, poor: 2000 }
        };
        
        this.alerts = [];
        this.optimizationSuggestions = [];
    }
    
    initialize() {
        console.log('📊 Initializing Real-Time Quality Monitor');
        
        this.setupEventListeners();
        this.createMonitoringDashboard();
        this.startMonitoring();
        
        console.log('✅ Quality monitoring active');
        return true;
    }
    
    setupEventListeners() {
        // Listen for quality updates from various sources
        window.addEventListener('audioQualityUpdate', (event) => {
            this.updateAudioMetrics(event.detail);
        });
        
        window.addEventListener('transcriptionResult', (event) => {
            this.updateTranscriptionMetrics(event.detail);
        });
        
        window.addEventListener('systemPerformanceUpdate', (event) => {
            this.updateSystemMetrics(event.detail);
        });
        
        window.addEventListener('enhancementMetricsUpdate', (event) => {
            this.updatePerformanceMetrics(event.detail);
        });
        
        window.addEventListener('chunkingMetricsUpdate', (event) => {
            this.updateChunkingMetrics(event.detail);
        });
    }
    
    createMonitoringDashboard() {
        // Find or create monitoring container
        let dashboardContainer = document.getElementById('qualityDashboard');
        
        if (!dashboardContainer) {
            // Create dashboard if it doesn't exist
            dashboardContainer = document.createElement('div');
            dashboardContainer.id = 'qualityDashboard';
            dashboardContainer.className = 'quality-dashboard';
            dashboardContainer.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                width: 300px;
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 15px;
                border-radius: 8px;
                font-family: 'Segoe UI', monospace;
                font-size: 12px;
                z-index: 10000;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                max-height: 80vh;
                overflow-y: auto;
                display: none;
            `;
            
            document.body.appendChild(dashboardContainer);
        }
        
        // Create dashboard content
        dashboardContainer.innerHTML = `
            <div class="dashboard-header">
                <h3 style="margin: 0 0 10px 0; color: #00ff88;">🌟 MINA Quality Monitor</h3>
                <button id="toggleDashboard" style="float: right; background: none; border: 1px solid #333; color: white; padding: 2px 8px; border-radius: 4px; cursor: pointer;">Hide</button>
            </div>
            
            <div class="metrics-section">
                <div class="metric-group">
                    <h4 style="color: #00bfff; margin: 10px 0 5px 0;">🔊 Audio Quality</h4>
                    <div class="metric-row">
                        <span>Overall:</span>
                        <span id="audioQualityOverall" class="metric-value">0%</span>
                    </div>
                    <div class="metric-row">
                        <span>SNR:</span>
                        <span id="audioSNR" class="metric-value">0.0</span>
                    </div>
                    <div class="metric-row">
                        <span>Volume:</span>
                        <span id="audioVolume" class="metric-value">0%</span>
                    </div>
                    <div class="metric-row">
                        <span>Clarity:</span>
                        <span id="audioClarity" class="metric-value">0%</span>
                    </div>
                </div>
                
                <div class="metric-group">
                    <h4 style="color: #ff6b35; margin: 10px 0 5px 0;">🎯 Transcription</h4>
                    <div class="metric-row">
                        <span>Accuracy:</span>
                        <span id="transcriptionAccuracy" class="metric-value">0%</span>
                    </div>
                    <div class="metric-row">
                        <span>Confidence:</span>
                        <span id="transcriptionConfidence" class="metric-value">0%</span>
                    </div>
                    <div class="metric-row">
                        <span>Latency:</span>
                        <span id="transcriptionLatency" class="metric-value">0ms</span>
                    </div>
                    <div class="metric-row">
                        <span>Error Rate:</span>
                        <span id="transcriptionErrorRate" class="metric-value">0%</span>
                    </div>
                </div>
                
                <div class="metric-group">
                    <h4 style="color: #9d4edd; margin: 10px 0 5px 0;">⚡ System Performance</h4>
                    <div class="metric-row">
                        <span>Memory:</span>
                        <span id="systemMemory" class="metric-value">0%</span>
                    </div>
                    <div class="metric-row">
                        <span>Network:</span>
                        <span id="systemNetwork" class="metric-value">0ms</span>
                    </div>
                    <div class="metric-row">
                        <span>Queue:</span>
                        <span id="systemQueue" class="metric-value">0</span>
                    </div>
                    <div class="metric-row">
                        <span>Throughput:</span>
                        <span id="systemThroughput" class="metric-value">0 KB/s</span>
                    </div>
                </div>
                
                <div class="metric-group">
                    <h4 style="color: #ffd23f; margin: 10px 0 5px 0;">🚀 Enhancements</h4>
                    <div class="metric-row">
                        <span>Audio Boost:</span>
                        <span id="enhancementAudio" class="metric-value">+0%</span>
                    </div>
                    <div class="metric-row">
                        <span>Accuracy Boost:</span>
                        <span id="enhancementAccuracy" class="metric-value">+0%</span>
                    </div>
                    <div class="metric-row">
                        <span>Latency Reduction:</span>
                        <span id="enhancementLatency" class="metric-value">+0%</span>
                    </div>
                </div>
            </div>
            
            <div class="alerts-section" id="alertsSection" style="margin-top: 15px;">
                <h4 style="color: #ff4757; margin: 10px 0 5px 0;">⚠️ Alerts</h4>
                <div id="alertsList" style="font-size: 11px;"></div>
            </div>
            
            <div class="recommendations-section" id="recommendationsSection" style="margin-top: 15px;">
                <h4 style="color: #2ed573; margin: 10px 0 5px 0;">💡 Optimizations</h4>
                <div id="recommendationsList" style="font-size: 11px;"></div>
            </div>
        `;
        
        // Add CSS for metric rows
        const style = document.createElement('style');
        style.textContent = `
            .metric-row {
                display: flex;
                justify-content: space-between;
                margin: 3px 0;
                padding: 2px 0;
            }
            .metric-value {
                font-weight: bold;
                color: #00ff88;
            }
            .metric-value.warning {
                color: #ffd23f !important;
            }
            .metric-value.error {
                color: #ff4757 !important;
            }
            .quality-dashboard::-webkit-scrollbar {
                width: 6px;
            }
            .quality-dashboard::-webkit-scrollbar-track {
                background: rgba(255, 255, 255, 0.1);
            }
            .quality-dashboard::-webkit-scrollbar-thumb {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 3px;
            }
        `;
        document.head.appendChild(style);
        
        // Setup toggle functionality
        document.getElementById('toggleDashboard').addEventListener('click', () => {
            this.toggleDashboard();
        });
        
        this.dashboardContainer = dashboardContainer;
    }
    
    startMonitoring() {
        this.isMonitoring = true;
        
        // Update dashboard every 500ms
        this.monitoringInterval = setInterval(() => {
            this.updateDashboard();
            this.analyzePerformance();
            this.generateOptimizationSuggestions();
        }, 500);
        
        // Show dashboard initially
        this.showDashboard();
    }
    
    updateAudioMetrics(audioData) {
        this.metrics.audio = {
            quality: audioData.overallScore || 0,
            snr: audioData.snr || 0,
            volume: (audioData.volume || 0) * 100,
            clarity: (audioData.clarity || 0) * 100,
            stability: (audioData.stability || 0) * 100
        };
        
        // Add to history
        this.history.audio.push({
            timestamp: Date.now(),
            ...this.metrics.audio
        });
        
        // Keep history bounded
        if (this.history.audio.length > 100) {
            this.history.audio.shift();
        }
    }
    
    updateTranscriptionMetrics(transcriptionData) {
        this.metrics.transcription = {
            accuracy: (transcriptionData.confidence || 0.9) * 100,
            confidence: (transcriptionData.confidence || 0.9) * 100,
            latency: transcriptionData.latency_ms || 0,
            completeness: transcriptionData.quality_score || 0,
            errorRate: Math.max(0, 100 - ((transcriptionData.confidence || 0.9) * 100))
        };
        
        // Add to history
        this.history.transcription.push({
            timestamp: Date.now(),
            ...this.metrics.transcription
        });
        
        if (this.history.transcription.length > 100) {
            this.history.transcription.shift();
        }
    }
    
    updateSystemMetrics(systemData) {
        this.metrics.system = {
            cpuUsage: systemData.cpuUsage || 0,
            memoryUsage: (systemData.memoryUsage || 0) * 100,
            networkLatency: systemData.networkDelay || 0,
            throughput: systemData.throughput || 0,
            queueLength: systemData.queueLength || 0
        };
        
        this.history.system.push({
            timestamp: Date.now(),
            ...this.metrics.system
        });
        
        if (this.history.system.length > 100) {
            this.history.system.shift();
        }
    }
    
    updatePerformanceMetrics(performanceData) {
        this.metrics.performance = {
            endToEndLatency: performanceData.endToEndLatency || 0,
            chunkProcessingTime: performanceData.chunkProcessingTime || 0,
            enhancementTime: performanceData.enhancementTime || 0,
            displayTime: performanceData.displayTime || 0
        };
    }
    
    updateChunkingMetrics(chunkingData) {
        // Update system throughput based on chunking
        this.metrics.system.throughput = chunkingData.avgChunkSize || 0;
    }
    
    updateDashboard() {
        if (!this.dashboardContainer || !this.isMonitoring) return;
        
        // Update audio metrics
        this.updateElement('audioQualityOverall', `${Math.round(this.metrics.audio.quality)}%`, this.metrics.audio.quality);
        this.updateElement('audioSNR', this.metrics.audio.snr.toFixed(1), this.metrics.audio.snr * 20);
        this.updateElement('audioVolume', `${Math.round(this.metrics.audio.volume)}%`, this.metrics.audio.volume);
        this.updateElement('audioClarity', `${Math.round(this.metrics.audio.clarity)}%`, this.metrics.audio.clarity);
        
        // Update transcription metrics
        this.updateElement('transcriptionAccuracy', `${Math.round(this.metrics.transcription.accuracy)}%`, this.metrics.transcription.accuracy);
        this.updateElement('transcriptionConfidence', `${Math.round(this.metrics.transcription.confidence)}%`, this.metrics.transcription.confidence);
        this.updateElement('transcriptionLatency', `${Math.round(this.metrics.transcription.latency)}ms`, 100 - (this.metrics.transcription.latency / 20));
        this.updateElement('transcriptionErrorRate', `${Math.round(this.metrics.transcription.errorRate)}%`, 100 - this.metrics.transcription.errorRate);
        
        // Update system metrics
        this.updateElement('systemMemory', `${Math.round(this.metrics.system.memoryUsage)}%`, 100 - this.metrics.system.memoryUsage);
        this.updateElement('systemNetwork', `${Math.round(this.metrics.system.networkLatency)}ms`, 100 - (this.metrics.system.networkLatency / 10));
        this.updateElement('systemQueue', this.metrics.system.queueLength.toString(), 100 - (this.metrics.system.queueLength * 10));
        this.updateElement('systemThroughput', `${(this.metrics.system.throughput / 1024).toFixed(1)} KB/s`, this.metrics.system.throughput / 10);
        
        // Update enhancement metrics (if available)
        if (window.enhancedSystemIntegration) {
            const enhMetrics = window.enhancedSystemIntegration.enhancementMetrics || {};
            this.updateElement('enhancementAudio', `+${Math.round(enhMetrics.audioQuality || 0)}%`, enhMetrics.audioQuality || 0);
            this.updateElement('enhancementAccuracy', `+${Math.round(enhMetrics.accuracyBoost || 0)}%`, enhMetrics.accuracyBoost || 0);
            this.updateElement('enhancementLatency', `+${Math.round(enhMetrics.latencyReduction || 0)}%`, enhMetrics.latencyReduction || 0);
        }
        
        // Update alerts and recommendations
        this.updateAlerts();
        this.updateRecommendations();
    }
    
    updateElement(elementId, value, score) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.textContent = value;
        
        // Apply color coding based on score
        element.className = 'metric-value';
        if (score < 40) {
            element.classList.add('error');
        } else if (score < 70) {
            element.classList.add('warning');
        }
    }
    
    analyzePerformance() {
        this.alerts = [];
        
        // Audio quality alerts
        if (this.metrics.audio.quality < this.thresholds.audio.poor) {
            this.alerts.push({
                type: 'warning',
                message: `Low audio quality (${Math.round(this.metrics.audio.quality)}%)`
            });
        }
        
        if (this.metrics.audio.snr < 2.0) {
            this.alerts.push({
                type: 'error',
                message: `Poor signal-to-noise ratio (${this.metrics.audio.snr.toFixed(1)})`
            });
        }
        
        // Transcription alerts
        if (this.metrics.transcription.latency > this.thresholds.performance.poor) {
            this.alerts.push({
                type: 'error',
                message: `High latency (${Math.round(this.metrics.transcription.latency)}ms)`
            });
        }
        
        if (this.metrics.transcription.accuracy < this.thresholds.transcription.poor) {
            this.alerts.push({
                type: 'warning',
                message: `Low accuracy (${Math.round(this.metrics.transcription.accuracy)}%)`
            });
        }
        
        // System alerts
        if (this.metrics.system.memoryUsage > 85) {
            this.alerts.push({
                type: 'warning',
                message: `High memory usage (${Math.round(this.metrics.system.memoryUsage)}%)`
            });
        }
        
        if (this.metrics.system.queueLength > 5) {
            this.alerts.push({
                type: 'error',
                message: `Processing queue backing up (${this.metrics.system.queueLength} items)`
            });
        }
    }
    
    generateOptimizationSuggestions() {
        this.optimizationSuggestions = [];
        
        // Audio optimization suggestions
        if (this.metrics.audio.quality < 70) {
            this.optimizationSuggestions.push('Consider improving microphone positioning or reducing background noise');
        }
        
        // Performance optimization suggestions
        if (this.metrics.transcription.latency > 1000) {
            this.optimizationSuggestions.push('Enable adaptive chunking to reduce latency');
        }
        
        if (this.metrics.system.memoryUsage > 75) {
            this.optimizationSuggestions.push('Reduce buffer sizes to conserve memory');
        }
        
        // Enhancement suggestions
        if (this.metrics.transcription.accuracy < 85) {
            this.optimizationSuggestions.push('Enable accuracy enhancer for better text quality');
        }
    }
    
    updateAlerts() {
        const alertsList = document.getElementById('alertsList');
        if (!alertsList) return;
        
        if (this.alerts.length === 0) {
            alertsList.innerHTML = '<div style="color: #2ed573;">✅ All systems optimal</div>';
        } else {
            alertsList.innerHTML = this.alerts.map(alert => 
                `<div style="color: ${alert.type === 'error' ? '#ff4757' : '#ffd23f'}; margin: 2px 0;">
                    ${alert.type === 'error' ? '🔴' : '🟡'} ${alert.message}
                </div>`
            ).join('');
        }
    }
    
    updateRecommendations() {
        const recommendationsList = document.getElementById('recommendationsList');
        if (!recommendationsList) return;
        
        if (this.optimizationSuggestions.length === 0) {
            recommendationsList.innerHTML = '<div style="color: #2ed573;">🎯 System running optimally</div>';
        } else {
            recommendationsList.innerHTML = this.optimizationSuggestions.map(suggestion => 
                `<div style="color: #2ed573; margin: 2px 0;">💡 ${suggestion}</div>`
            ).slice(0, 3).join(''); // Show top 3 suggestions
        }
    }
    
    showDashboard() {
        if (this.dashboardContainer) {
            this.dashboardContainer.style.display = 'block';
        }
    }
    
    hideDashboard() {
        if (this.dashboardContainer) {
            this.dashboardContainer.style.display = 'none';
        }
    }
    
    toggleDashboard() {
        if (this.dashboardContainer) {
            const isVisible = this.dashboardContainer.style.display !== 'none';
            if (isVisible) {
                this.hideDashboard();
                document.getElementById('toggleDashboard').textContent = 'Show';
            } else {
                this.showDashboard();
                document.getElementById('toggleDashboard').textContent = 'Hide';
            }
        }
    }
    
    getPerformanceReport() {
        const report = {
            currentMetrics: { ...this.metrics },
            alerts: this.alerts,
            suggestions: this.optimizationSuggestions,
            history: {
                audioQuality: this.calculateAverageFromHistory('audio', 'quality'),
                transcriptionAccuracy: this.calculateAverageFromHistory('transcription', 'accuracy'),
                averageLatency: this.calculateAverageFromHistory('transcription', 'latency'),
                systemLoad: this.calculateAverageFromHistory('system', 'memoryUsage')
            }
        };
        
        return report;
    }
    
    calculateAverageFromHistory(category, metric) {
        const history = this.history[category];
        if (!history || history.length === 0) return 0;
        
        const recent = history.slice(-20); // Last 20 measurements
        return recent.reduce((sum, item) => sum + (item[metric] || 0), 0) / recent.length;
    }
    
    stop() {
        this.isMonitoring = false;
        
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
        }
        
        this.hideDashboard();
        console.log('🛑 Real-time quality monitor stopped');
    }
}

// Initialize global quality monitor
window.realTimeQualityMonitor = new RealTimeQualityMonitor();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.realTimeQualityMonitor.initialize();
    console.log('📊 Real-Time Quality Monitor initialized');
});