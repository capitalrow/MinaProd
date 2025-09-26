/**
 * 🔍 PIPELINE DIAGNOSTICS: Real-time monitoring and debugging
 * Tracks audio → API → UI pipeline performance
 */

class PipelineDiagnostics {
    constructor() {
        this.metrics = {
            chunksCollected: 0,
            chunksProcessed: 0,
            apiCalls: 0,
            apiSuccesses: 0,
            apiFailures: 0,
            totalAudioSize: 0,
            sessionStart: Date.now(),
            lastActivity: Date.now()
        };
        
        this.logs = [];
        this.maxLogs = 100;
        
        this.initializeMonitoring();
        console.log('🔍 Pipeline Diagnostics initialized');
    }
    
    initializeMonitoring() {
        // Hook into audio chunk collection
        if (window.audioChunkHandler) {
            const originalCollect = window.audioChunkHandler.collectChunk;
            window.audioChunkHandler.collectChunk = (chunk) => {
                this.trackChunkCollection(chunk);
                return originalCollect.call(window.audioChunkHandler, chunk);
            };
        }
        
        // Hook into API calls
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            if (args[0].includes('/api/transcribe')) {
                this.trackAPICall(args[0]);
            }
            
            try {
                const response = await originalFetch(...args);
                if (args[0].includes('/api/transcribe')) {
                    this.trackAPIResponse(response.ok);
                }
                return response;
            } catch (error) {
                if (args[0].includes('/api/transcribe')) {
                    this.trackAPIResponse(false, error);
                }
                throw error;
            }
        };
        
        // Update dashboard every 2 seconds
        setInterval(() => this.updateDashboard(), 2000);
    }
    
    trackChunkCollection(chunk) {\n        this.metrics.chunksCollected++;\n        this.metrics.totalAudioSize += chunk.size;\n        this.metrics.lastActivity = Date.now();\n        \n        this.addLog('chunk_collected', {\n            size: chunk.size,\n            total: this.metrics.chunksCollected\n        });\n    }\n    \n    trackChunkProcessing() {\n        this.metrics.chunksProcessed++;\n        this.addLog('chunk_processed', {\n            processed: this.metrics.chunksProcessed\n        });\n    }\n    \n    trackAPICall(url) {\n        this.metrics.apiCalls++;\n        this.metrics.lastActivity = Date.now();\n        this.addLog('api_call', { url });\n    }\n    \n    trackAPIResponse(success, error = null) {\n        if (success) {\n            this.metrics.apiSuccesses++;\n            this.addLog('api_success', {});\n        } else {\n            this.metrics.apiFailures++;\n            this.addLog('api_failure', { error: error?.message });\n        }\n    }\n    \n    addLog(type, data) {\n        const log = {\n            timestamp: Date.now(),\n            type,\n            data\n        };\n        \n        this.logs.push(log);\n        if (this.logs.length > this.maxLogs) {\n            this.logs.shift();\n        }\n    }\n    \n    updateDashboard() {\n        const dashboardElement = this.getDashboardElement();\n        if (!dashboardElement) return;\n        \n        const uptimeMs = Date.now() - this.metrics.sessionStart;\n        const uptimeSeconds = Math.floor(uptimeMs / 1000);\n        const timeSinceActivity = Date.now() - this.metrics.lastActivity;\n        \n        const successRate = this.metrics.apiCalls > 0 ? \n            Math.round((this.metrics.apiSuccesses / this.metrics.apiCalls) * 100) : 0;\n        \n        dashboardElement.innerHTML = `\n            <div class=\"pipeline-dashboard\">\n                <h4>🔍 Pipeline Status</h4>\n                <div class=\"metrics-grid\">\n                    <div class=\"metric\">\n                        <span class=\"label\">Audio Chunks</span>\n                        <span class=\"value\">${this.metrics.chunksCollected}</span>\n                    </div>\n                    <div class=\"metric\">\n                        <span class=\"label\">API Calls</span>\n                        <span class=\"value\">${this.metrics.apiCalls}</span>\n                    </div>\n                    <div class=\"metric\">\n                        <span class=\"label\">Success Rate</span>\n                        <span class=\"value ${successRate > 80 ? 'good' : successRate > 50 ? 'warning' : 'error'}\">${successRate}%</span>\n                    </div>\n                    <div class=\"metric\">\n                        <span class=\"label\">Audio Size</span>\n                        <span class=\"value\">${this.formatBytes(this.metrics.totalAudioSize)}</span>\n                    </div>\n                    <div class=\"metric\">\n                        <span class=\"label\">Uptime</span>\n                        <span class=\"value\">${this.formatTime(uptimeSeconds)}</span>\n                    </div>\n                    <div class=\"metric\">\n                        <span class=\"label\">Last Activity</span>\n                        <span class=\"value ${timeSinceActivity > 5000 ? 'warning' : 'good'}\">${this.formatTime(Math.floor(timeSinceActivity / 1000))} ago</span>\n                    </div>\n                </div>\n                \n                <div class=\"recent-logs\">\n                    <h5>Recent Activity</h5>\n                    <div class=\"log-entries\">\n                        ${this.logs.slice(-5).map(log => `\n                            <div class=\"log-entry ${log.type}\">\n                                <span class=\"time\">${new Date(log.timestamp).toLocaleTimeString()}</span>\n                                <span class=\"type\">${log.type}</span>\n                                <span class=\"data\">${JSON.stringify(log.data)}</span>\n                            </div>\n                        `).join('')}\n                    </div>\n                </div>\n                \n                <div class=\"pipeline-flow\">\n                    <div class=\"flow-step ${this.metrics.chunksCollected > 0 ? 'active' : ''}\">\n                        📦 Audio Collection\n                    </div>\n                    <div class=\"flow-arrow\">→</div>\n                    <div class=\"flow-step ${this.metrics.apiCalls > 0 ? 'active' : ''}\">\n                        🔄 API Processing\n                    </div>\n                    <div class=\"flow-arrow\">→</div>\n                    <div class=\"flow-step ${this.metrics.apiSuccesses > 0 ? 'active' : ''}\">\n                        📝 UI Display\n                    </div>\n                </div>\n            </div>\n        `;\n    }\n    \n    getDashboardElement() {\n        let dashboard = document.getElementById('pipeline-diagnostics');\n        if (!dashboard) {\n            dashboard = document.createElement('div');\n            dashboard.id = 'pipeline-diagnostics';\n            dashboard.style.cssText = `\n                position: fixed;\n                top: 10px;\n                right: 10px;\n                background: rgba(0, 0, 0, 0.9);\n                color: white;\n                padding: 15px;\n                border-radius: 8px;\n                font-family: monospace;\n                font-size: 12px;\n                z-index: 10000;\n                max-width: 300px;\n                box-shadow: 0 4px 8px rgba(0,0,0,0.3);\n            `;\n            \n            // Add CSS for dashboard\n            const style = document.createElement('style');\n            style.textContent = `\n                .pipeline-dashboard .metrics-grid {\n                    display: grid;\n                    grid-template-columns: 1fr 1fr;\n                    gap: 8px;\n                    margin: 10px 0;\n                }\n                .pipeline-dashboard .metric {\n                    display: flex;\n                    justify-content: space-between;\n                    padding: 4px;\n                    background: rgba(255,255,255,0.1);\n                    border-radius: 4px;\n                }\n                .pipeline-dashboard .value.good { color: #4CAF50; }\n                .pipeline-dashboard .value.warning { color: #FF9800; }\n                .pipeline-dashboard .value.error { color: #F44336; }\n                .pipeline-dashboard .log-entries {\n                    max-height: 100px;\n                    overflow-y: auto;\n                }\n                .pipeline-dashboard .log-entry {\n                    font-size: 10px;\n                    margin: 2px 0;\n                    padding: 2px;\n                    background: rgba(255,255,255,0.05);\n                }\n                .pipeline-dashboard .pipeline-flow {\n                    display: flex;\n                    align-items: center;\n                    margin-top: 10px;\n                    font-size: 10px;\n                }\n                .pipeline-dashboard .flow-step {\n                    padding: 4px 8px;\n                    border-radius: 4px;\n                    background: rgba(255,255,255,0.1);\n                }\n                .pipeline-dashboard .flow-step.active {\n                    background: rgba(76, 175, 80, 0.3);\n                }\n                .pipeline-dashboard .flow-arrow {\n                    margin: 0 5px;\n                }\n            `;\n            document.head.appendChild(style);\n            \n            document.body.appendChild(dashboard);\n        }\n        return dashboard;\n    }\n    \n    formatBytes(bytes) {\n        if (bytes === 0) return '0 B';\n        const k = 1024;\n        const sizes = ['B', 'KB', 'MB', 'GB'];\n        const i = Math.floor(Math.log(bytes) / Math.log(k));\n        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];\n    }\n    \n    formatTime(seconds) {\n        if (seconds < 60) return `${seconds}s`;\n        const minutes = Math.floor(seconds / 60);\n        const remainingSeconds = seconds % 60;\n        return `${minutes}m ${remainingSeconds}s`;\n    }\n    \n    getReport() {\n        return {\n            metrics: this.metrics,\n            logs: this.logs,\n            timestamp: Date.now()\n        };\n    }\n    \n    reset() {\n        this.metrics = {\n            chunksCollected: 0,\n            chunksProcessed: 0,\n            apiCalls: 0,\n            apiSuccesses: 0,\n            apiFailures: 0,\n            totalAudioSize: 0,\n            sessionStart: Date.now(),\n            lastActivity: Date.now()\n        };\n        this.logs = [];\n        console.log('🔄 Pipeline diagnostics reset');\n    }\n}\n\n// Initialize global diagnostics\nwindow.pipelineDiagnostics = new PipelineDiagnostics();\n\nconsole.log('✅ Pipeline diagnostics system loaded');

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
