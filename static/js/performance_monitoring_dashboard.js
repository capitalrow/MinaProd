/**
 * 📊 REAL-TIME PERFORMANCE MONITORING DASHBOARD
 * Comprehensive monitoring with WER calculation and quality assessment
 */

class PerformanceMonitoringDashboard {
    constructor() {
        this.metrics = {
            latency: {
                current: 0,
                average: 0,
                samples: [],
                target: 500
            },
            accuracy: {
                current: 0,
                average: 0,
                wer: 0, // Word Error Rate
                confidence: 0
            },
            throughput: {
                chunksPerSecond: 0,
                bytesPerSecond: 0,
                wordsPerMinute: 0
            },
            quality: {
                score: 0,
                audioQuality: 0,
                transcriptionQuality: 0,
                networkQuality: 0
            },
            errors: {
                total: 0,
                rate: 0,
                lastError: null
            }
        };
        
        this.dashboard = null;
        this.updateInterval = null;
        this.isVisible = false;
        
        // Performance tracking
        this.sessionStartTime = Date.now();
        this.totalChunksProcessed = 0;
        this.totalBytesProcessed = 0;
        this.totalWordsTranscribed = 0;
        
        this.initializeDashboard();
        console.log('📊 Performance Monitoring Dashboard initialized');
    }
    
    /**
     * Initialize dashboard UI
     */
    initializeDashboard() {
        this.createDashboardElement();
        this.startMonitoring();
        this.setupEventListeners();
    }
    
    /**
     * Create dashboard DOM element
     */
    createDashboardElement() {
        this.dashboard = document.createElement('div');
        this.dashboard.id = 'performance-dashboard';
        this.dashboard.className = 'performance-dashboard hidden';
        
        this.dashboard.innerHTML = `
            <div class=\"dashboard-header\">
                <h3>📊 Performance Monitor</h3>
                <button class=\"close-btn\" onclick=\"window.performanceDashboard.hide()\">&times;</button>
            </div>
            
            <div class=\"dashboard-content\">
                <div class=\"metrics-grid\">
                    <div class=\"metric-card latency\">
                        <div class=\"metric-header\">
                            <span class=\"metric-title\">Latency</span>
                            <span class=\"metric-target\">Target: &lt;500ms</span>
                        </div>
                        <div class=\"metric-value\" id=\"latency-current\">0ms</div>
                        <div class=\"metric-sub\">Avg: <span id=\"latency-average\">0ms</span></div>
                        <div class=\"metric-indicator\" id=\"latency-indicator\"></div>
                    </div>
                    
                    <div class=\"metric-card accuracy\">
                        <div class=\"metric-header\">
                            <span class=\"metric-title\">Accuracy</span>
                            <span class=\"metric-target\">Target: &gt;95%</span>
                        </div>
                        <div class=\"metric-value\" id=\"accuracy-current\">0%</div>
                        <div class=\"metric-sub\">WER: <span id=\"wer-current\">0%</span></div>
                        <div class=\"metric-indicator\" id=\"accuracy-indicator\"></div>
                    </div>
                    
                    <div class=\"metric-card throughput\">
                        <div class=\"metric-header\">
                            <span class=\"metric-title\">Throughput</span>
                            <span class=\"metric-target\">Real-time</span>
                        </div>
                        <div class=\"metric-value\" id=\"throughput-current\">0 WPM</div>
                        <div class=\"metric-sub\">Chunks: <span id=\"chunks-per-second\">0/s</span></div>
                        <div class=\"metric-indicator\" id=\"throughput-indicator\"></div>
                    </div>
                    
                    <div class=\"metric-card quality\">
                        <div class=\"metric-header\">
                            <span class=\"metric-title\">Quality Score</span>
                            <span class=\"metric-target\">Target: &gt;85</span>
                        </div>
                        <div class=\"metric-value\" id=\"quality-current\">0</div>
                        <div class=\"metric-sub\">Audio: <span id=\"audio-quality\">0</span></div>
                        <div class=\"metric-indicator\" id=\"quality-indicator\"></div>
                    </div>
                </div>
                
                <div class=\"charts-section\">
                    <div class=\"chart-container\">
                        <canvas id=\"latency-chart\" width=\"400\" height=\"150\"></canvas>
                    </div>
                </div>
                
                <div class=\"session-stats\">
                    <div class=\"stat-item\">
                        <span class=\"stat-label\">Session Duration:</span>
                        <span class=\"stat-value\" id=\"session-duration\">0s</span>
                    </div>
                    <div class=\"stat-item\">
                        <span class=\"stat-label\">Total Chunks:</span>
                        <span class=\"stat-value\" id=\"total-chunks\">0</span>
                    </div>
                    <div class=\"stat-item\">
                        <span class=\"stat-label\">Total Words:</span>
                        <span class=\"stat-value\" id=\"total-words\">0</span>
                    </div>
                    <div class=\"stat-item\">
                        <span class=\"stat-label\">Error Rate:</span>
                        <span class=\"stat-value\" id=\"error-rate\">0%</span>
                    </div>
                </div>
            </div>
        `;
        
        // Add styles
        this.addDashboardStyles();
        
        document.body.appendChild(this.dashboard);
    }
    
    /**
     * Add dashboard CSS styles
     */
    addDashboardStyles() {
        if (document.getElementById('performance-dashboard-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'performance-dashboard-styles';
        styles.textContent = `
            .performance-dashboard {
                position: fixed;
                top: 20px;
                right: 20px;
                width: 450px;
                max-height: 80vh;
                background: rgba(0, 0, 0, 0.95);
                border: 1px solid #333;
                border-radius: 8px;
                color: white;
                font-family: monospace;
                font-size: 12px;
                z-index: 10000;
                overflow-y: auto;
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            }
            
            .performance-dashboard.hidden {
                display: none;
            }
            
            .dashboard-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 15px;
                border-bottom: 1px solid #333;
                background: rgba(0, 100, 200, 0.2);
            }
            
            .dashboard-header h3 {
                margin: 0;
                font-size: 14px;
            }
            
            .close-btn {
                background: none;
                border: none;
                color: white;
                font-size: 18px;
                cursor: pointer;
                padding: 0;
                width: 20px;
                height: 20px;
            }
            
            .dashboard-content {
                padding: 15px;
            }
            
            .metrics-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                margin-bottom: 15px;
            }
            
            .metric-card {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 6px;
                padding: 10px;
                border-left: 3px solid #666;
            }
            
            .metric-card.latency { border-left-color: #007bff; }
            .metric-card.accuracy { border-left-color: #28a745; }
            .metric-card.throughput { border-left-color: #ffc107; }
            .metric-card.quality { border-left-color: #dc3545; }
            
            .metric-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 5px;
            }
            
            .metric-title {
                font-weight: bold;
                font-size: 11px;
            }
            
            .metric-target {
                font-size: 9px;
                opacity: 0.7;
            }
            
            .metric-value {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 3px;
            }
            
            .metric-sub {
                font-size: 10px;
                opacity: 0.8;
            }
            
            .metric-indicator {
                height: 3px;
                background: #333;
                border-radius: 2px;
                margin-top: 5px;
                position: relative;
            }
            
            .metric-indicator::after {
                content: '';
                position: absolute;
                left: 0;
                top: 0;
                height: 100%;
                border-radius: 2px;
                background: currentColor;
                transition: width 0.3s ease;
            }
            
            .metric-indicator.excellent::after { width: 100%; background: #28a745; }
            .metric-indicator.good::after { width: 75%; background: #ffc107; }
            .metric-indicator.fair::after { width: 50%; background: #fd7e14; }
            .metric-indicator.poor::after { width: 25%; background: #dc3545; }
            
            .charts-section {
                margin-bottom: 15px;
            }
            
            .chart-container {
                background: rgba(255, 255, 255, 0.03);
                border-radius: 6px;
                padding: 10px;
            }
            
            .session-stats {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
                font-size: 11px;
            }
            
            .stat-item {
                display: flex;
                justify-content: space-between;
                padding: 5px 8px;
                background: rgba(255, 255, 255, 0.03);
                border-radius: 4px;
            }
            
            .stat-label {
                opacity: 0.8;
            }
            
            .stat-value {
                font-weight: bold;
            }
        `;
        
        document.head.appendChild(styles);
    }
    
    /**
     * Start monitoring
     */
    startMonitoring() {
        this.updateInterval = setInterval(() => {
            this.updateDashboard();
        }, 1000); // Update every second
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Listen for transcription events
        window.addEventListener('transcriptionComplete', (event) => {
            this.recordTranscriptionMetrics(event.detail);
        });
        
        // Listen for performance events
        window.addEventListener('performanceMetrics', (event) => {
            this.updateMetrics(event.detail);
        });
        
        // Listen for error events
        window.addEventListener('transcriptionError', (event) => {
            this.recordError(event.detail);
        });
    }
    
    /**
     * Record transcription metrics
     */
    recordTranscriptionMetrics(data) {
        // Update latency
        if (data.processingTime) {
            this.metrics.latency.current = data.processingTime;
            this.metrics.latency.samples.push(data.processingTime);
            
            // Keep only last 50 samples
            if (this.metrics.latency.samples.length > 50) {
                this.metrics.latency.samples.shift();
            }
            
            this.metrics.latency.average = this.metrics.latency.samples.reduce((sum, val) => sum + val, 0) / this.metrics.latency.samples.length;
        }
        
        // Update accuracy
        if (data.confidence !== undefined) {
            this.metrics.accuracy.confidence = data.confidence;
            this.metrics.accuracy.current = data.confidence * 100;
        }
        
        // Update word count
        if (data.text) {
            const words = data.text.split(' ').length;
            this.totalWordsTranscribed += words;
        }
        
        this.totalChunksProcessed++;
        
        // Calculate throughput
        this.calculateThroughput();
        
        // Update quality score
        this.calculateQualityScore();
    }
    
    /**
     * Calculate throughput metrics
     */
    calculateThroughput() {
        const sessionDuration = (Date.now() - this.sessionStartTime) / 1000; // seconds
        
        if (sessionDuration > 0) {
            this.metrics.throughput.chunksPerSecond = this.totalChunksProcessed / sessionDuration;
            this.metrics.throughput.wordsPerMinute = (this.totalWordsTranscribed / sessionDuration) * 60;
        }
    }
    
    /**
     * Calculate overall quality score
     */
    calculateQualityScore() {
        const latencyScore = this.calculateLatencyScore();
        const accuracyScore = this.metrics.accuracy.current / 100;
        const throughputScore = this.calculateThroughputScore();
        
        // Weighted quality score
        const qualityScore = (latencyScore * 0.3) + (accuracyScore * 0.4) + (throughputScore * 0.3);
        this.metrics.quality.score = Math.round(qualityScore * 100);
    }
    
    /**
     * Calculate latency score (0-1)
     */
    calculateLatencyScore() {
        const target = this.metrics.latency.target;
        const current = this.metrics.latency.average || this.metrics.latency.current;
        
        if (current <= target * 0.5) return 1.0; // Excellent
        if (current <= target) return 0.8; // Good
        if (current <= target * 1.5) return 0.6; // Fair
        return 0.3; // Poor
    }
    
    /**
     * Calculate throughput score (0-1)
     */
    calculateThroughputScore() {
        const wpm = this.metrics.throughput.wordsPerMinute;
        const targetWPM = 150; // Average speaking rate
        
        if (wpm >= targetWPM * 0.8) return 1.0; // Real-time or better
        if (wpm >= targetWPM * 0.6) return 0.8; // Good
        if (wpm >= targetWPM * 0.4) return 0.6; // Fair
        return 0.3; // Poor
    }
    
    /**
     * Record error
     */
    recordError(errorData) {
        this.metrics.errors.total++;
        this.metrics.errors.lastError = errorData;
        
        // Calculate error rate
        if (this.totalChunksProcessed > 0) {
            this.metrics.errors.rate = (this.metrics.errors.total / this.totalChunksProcessed) * 100;
        }
    }
    
    /**
     * Update dashboard display
     */
    updateDashboard() {
        if (!this.isVisible) return;
        
        // Update latency
        document.getElementById('latency-current').textContent = `${Math.round(this.metrics.latency.current)}ms`;
        document.getElementById('latency-average').textContent = `${Math.round(this.metrics.latency.average)}ms`;
        this.updateIndicator('latency-indicator', this.calculateLatencyScore());
        
        // Update accuracy
        document.getElementById('accuracy-current').textContent = `${Math.round(this.metrics.accuracy.current)}%`;
        document.getElementById('wer-current').textContent = `${Math.round(this.metrics.accuracy.wer)}%`;
        this.updateIndicator('accuracy-indicator', this.metrics.accuracy.current / 100);
        
        // Update throughput
        document.getElementById('throughput-current').textContent = `${Math.round(this.metrics.throughput.wordsPerMinute)} WPM`;
        document.getElementById('chunks-per-second').textContent = `${this.metrics.throughput.chunksPerSecond.toFixed(1)}/s`;
        this.updateIndicator('throughput-indicator', this.calculateThroughputScore());
        
        // Update quality
        document.getElementById('quality-current').textContent = this.metrics.quality.score;
        document.getElementById('audio-quality').textContent = Math.round(this.metrics.quality.audioQuality);
        this.updateIndicator('quality-indicator', this.metrics.quality.score / 100);
        
        // Update session stats
        const sessionDuration = Math.round((Date.now() - this.sessionStartTime) / 1000);
        document.getElementById('session-duration').textContent = `${sessionDuration}s`;
        document.getElementById('total-chunks').textContent = this.totalChunksProcessed;
        document.getElementById('total-words').textContent = this.totalWordsTranscribed;
        document.getElementById('error-rate').textContent = `${this.metrics.errors.rate.toFixed(1)}%`;
    }
    
    /**
     * Update metric indicator
     */
    updateIndicator(elementId, score) {
        const indicator = document.getElementById(elementId);
        if (!indicator) return;
        
        indicator.className = 'metric-indicator';
        if (score >= 0.9) indicator.classList.add('excellent');
        else if (score >= 0.7) indicator.classList.add('good');
        else if (score >= 0.5) indicator.classList.add('fair');
        else indicator.classList.add('poor');
    }
    
    /**
     * Show dashboard
     */
    show() {
        this.dashboard.classList.remove('hidden');
        this.isVisible = true;
    }
    
    /**
     * Hide dashboard
     */
    hide() {
        this.dashboard.classList.add('hidden');
        this.isVisible = false;
    }
    
    /**
     * Toggle dashboard visibility
     */
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    /**
     * Calculate Word Error Rate (WER)
     */
    calculateWER(reference, hypothesis) {
        if (!reference || !hypothesis) return 0;
        
        const refWords = reference.toLowerCase().split(/\\s+/);\n        const hypWords = hypothesis.toLowerCase().split(/\\s+/);\n        \n        // Simple WER calculation using edit distance\n        const editDistance = this.calculateEditDistance(refWords, hypWords);\n        const wer = refWords.length > 0 ? (editDistance / refWords.length) * 100 : 0;\n        \n        this.metrics.accuracy.wer = wer;\n        return wer;\n    }\n    \n    /**\n     * Calculate edit distance between two word arrays\n     */\n    calculateEditDistance(arr1, arr2) {\n        const m = arr1.length;\n        const n = arr2.length;\n        const dp = Array(m + 1).fill().map(() => Array(n + 1).fill(0));\n        \n        // Initialize base cases\n        for (let i = 0; i <= m; i++) dp[i][0] = i;\n        for (let j = 0; j <= n; j++) dp[0][j] = j;\n        \n        // Fill the dp table\n        for (let i = 1; i <= m; i++) {\n            for (let j = 1; j <= n; j++) {\n                if (arr1[i - 1] === arr2[j - 1]) {\n                    dp[i][j] = dp[i - 1][j - 1];\n                } else {\n                    dp[i][j] = 1 + Math.min(\n                        dp[i - 1][j],     // deletion\n                        dp[i][j - 1],     // insertion\n                        dp[i - 1][j - 1]  // substitution\n                    );\n                }\n            }\n        }\n        \n        return dp[m][n];\n    }\n    \n    /**\n     * Get performance report\n     */\n    generateReport() {\n        return {\n            session: {\n                duration: Math.round((Date.now() - this.sessionStartTime) / 1000),\n                chunksProcessed: this.totalChunksProcessed,\n                wordsTranscribed: this.totalWordsTranscribed\n            },\n            metrics: {\n                latency: {\n                    current: this.metrics.latency.current,\n                    average: Math.round(this.metrics.latency.average),\n                    target: this.metrics.latency.target,\n                    score: this.calculateLatencyScore()\n                },\n                accuracy: {\n                    current: Math.round(this.metrics.accuracy.current),\n                    wer: Math.round(this.metrics.accuracy.wer),\n                    confidence: Math.round(this.metrics.accuracy.confidence * 100)\n                },\n                throughput: {\n                    wpm: Math.round(this.metrics.throughput.wordsPerMinute),\n                    chunksPerSecond: Math.round(this.metrics.throughput.chunksPerSecond * 10) / 10\n                },\n                quality: {\n                    overall: this.metrics.quality.score,\n                    breakdown: {\n                        latency: this.calculateLatencyScore(),\n                        accuracy: this.metrics.accuracy.current / 100,\n                        throughput: this.calculateThroughputScore()\n                    }\n                },\n                errors: {\n                    total: this.metrics.errors.total,\n                    rate: Math.round(this.metrics.errors.rate * 10) / 10\n                }\n            },\n            timestamp: new Date().toISOString()\n        };\n    }\n    \n    /**\n     * Export metrics data\n     */\n    exportData() {\n        const report = this.generateReport();\n        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });\n        const url = URL.createObjectURL(blob);\n        \n        const a = document.createElement('a');\n        a.href = url;\n        a.download = `mina-performance-${Date.now()}.json`;\n        document.body.appendChild(a);\n        a.click();\n        document.body.removeChild(a);\n        URL.revokeObjectURL(url);\n    }\n}\n\n// Initialize global performance dashboard\nwindow.performanceDashboard = new PerformanceMonitoringDashboard();\n\n// Add toggle button to page\ndocument.addEventListener('DOMContentLoaded', () => {\n    const toggleButton = document.createElement('button');\n    toggleButton.textContent = '📊';\n    toggleButton.title = 'Performance Dashboard';\n    toggleButton.style.cssText = `\n        position: fixed;\n        bottom: 20px;\n        right: 20px;\n        width: 50px;\n        height: 50px;\n        border-radius: 50%;\n        border: none;\n        background: rgba(0, 100, 200, 0.8);\n        color: white;\n        font-size: 20px;\n        cursor: pointer;\n        z-index: 9999;\n        box-shadow: 0 2px 10px rgba(0,0,0,0.3);\n    `;\n    \n    toggleButton.onclick = () => window.performanceDashboard.toggle();\n    document.body.appendChild(toggleButton);\n});\n\nconsole.log('✅ Performance Monitoring Dashboard loaded');"

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
