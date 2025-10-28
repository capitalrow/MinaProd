/**
 * CROWN⁴ Performance Monitor UI
 * 
 * Floating debug panel showing real-time CROWN⁴ compliance metrics.
 * Toggle with Ctrl+Shift+P (Performance)
 */

class CROWNPerformanceMonitor {
    constructor(telemetry) {
        this.telemetry = telemetry;
        this.panel = null;
        this.isVisible = false;
        this.updateInterval = null;
        
        this.init();
    }
    
    init() {
        // Create panel HTML
        this.createPanel();
        
        // Set up keyboard shortcut (Ctrl+Shift+P)
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'P') {
                e.preventDefault();
                this.toggle();
            }
        });
        
        console.log('📊 CROWN⁴ Performance Monitor initialized (Ctrl+Shift+P to toggle)');
    }
    
    createPanel() {
        // Create panel container
        this.panel = document.createElement('div');
        this.panel.id = 'crown-performance-monitor';
        this.panel.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 360px;
            max-height: 80vh;
            overflow-y: auto;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            z-index: 10000;
            display: none;
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
            font-size: 13px;
            color: #e2e8f0;
        `;
        
        // Panel content
        this.panel.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #818cf8;">
                    📊 CROWN⁴ Metrics
                </h3>
                <button id="crown-monitor-close" style="
                    background: none;
                    border: none;
                    color: #94a3b8;
                    cursor: pointer;
                    font-size: 20px;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                ">&times;</button>
            </div>
            
            <div id="crown-metrics-container">
                <!-- Metrics will be injected here -->
            </div>
            
            <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(148, 163, 184, 0.2); font-size: 11px; color: #64748b;">
                Press Ctrl+Shift+P to toggle • Auto-refresh: 2s
            </div>
        `;
        
        document.body.appendChild(this.panel);
        
        // Close button handler
        document.getElementById('crown-monitor-close').addEventListener('click', () => {
            this.hide();
        });
    }
    
    show() {
        this.isVisible = true;
        this.panel.style.display = 'block';
        this.update();
        
        // Start auto-refresh
        this.updateInterval = setInterval(() => this.update(), 2000);
    }
    
    hide() {
        this.isVisible = false;
        this.panel.style.display = 'none';
        
        // Stop auto-refresh
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    update() {
        if (!this.telemetry) return;
        
        const summary = this.telemetry.getSummary();
        const container = document.getElementById('crown-metrics-container');
        
        container.innerHTML = `
            <!-- Bootstrap Performance -->
            <div class="crown-metric-section">
                <div class="crown-metric-header">
                    <span class="crown-metric-icon">${summary.bootstrap.status === 'pass' ? '✅' : '⚠️'}</span>
                    <span class="crown-metric-title">Bootstrap Time</span>
                </div>
                <div class="crown-metric-value" style="color: ${summary.bootstrap.status === 'pass' ? '#10b981' : '#f59e0b'};">
                    ${summary.bootstrap.time?.toFixed(0) || 'N/A'} ms
                </div>
                <div class="crown-metric-target">Target: &lt;${summary.bootstrap.target} ms</div>
                <div class="crown-progress-bar">
                    <div class="crown-progress-fill" style="
                        width: ${Math.min(100, (summary.bootstrap.time / summary.bootstrap.target) * 100)}%;
                        background: ${summary.bootstrap.status === 'pass' ? '#10b981' : '#f59e0b'};
                    "></div>
                </div>
            </div>
            
            <!-- Event Propagation -->
            <div class="crown-metric-section">
                <div class="crown-metric-header">
                    <span class="crown-metric-icon">${summary.propagation.status === 'pass' ? '✅' : '⚠️'}</span>
                    <span class="crown-metric-title">Event Propagation (P95)</span>
                </div>
                <div class="crown-metric-value" style="color: ${summary.propagation.status === 'pass' ? '#10b981' : '#f59e0b'};">
                    ${summary.propagation.p95.toFixed(0)} ms
                </div>
                <div class="crown-metric-target">
                    Avg: ${summary.propagation.avg.toFixed(0)} ms | Target: &lt;${summary.propagation.target} ms
                </div>
                <div class="crown-metric-target" style="margin-top: 4px;">
                    Events tracked: ${summary.propagation.count}
                </div>
                <div class="crown-progress-bar">
                    <div class="crown-progress-fill" style="
                        width: ${Math.min(100, (summary.propagation.p95 / summary.propagation.target) * 100)}%;
                        background: ${summary.propagation.status === 'pass' ? '#10b981' : '#f59e0b'};
                    "></div>
                </div>
            </div>
            
            <!-- Cache Hit Ratio -->
            <div class="crown-metric-section">
                <div class="crown-metric-header">
                    <span class="crown-metric-icon">${summary.cache.status === 'pass' ? '✅' : '⚠️'}</span>
                    <span class="crown-metric-title">Cache Hit Ratio</span>
                </div>
                <div class="crown-metric-value" style="color: ${summary.cache.status === 'pass' ? '#10b981' : '#f59e0b'};">
                    ${(summary.cache.hitRatio * 100).toFixed(1)}%
                </div>
                <div class="crown-metric-target">
                    Hits: ${summary.cache.hits} | Misses: ${summary.cache.misses}
                </div>
                <div class="crown-metric-target">Target: &gt;=${(summary.cache.target * 100).toFixed(0)}%</div>
                <div class="crown-progress-bar">
                    <div class="crown-progress-fill" style="
                        width: ${summary.cache.hitRatio * 100}%;
                        background: ${summary.cache.status === 'pass' ? '#10b981' : '#f59e0b'};
                    "></div>
                </div>
            </div>
            
            <!-- Sequence Integrity -->
            <div class="crown-metric-section">
                <div class="crown-metric-header">
                    <span class="crown-metric-icon">${summary.sequence.status === 'pass' ? '✅' : '❌'}</span>
                    <span class="crown-metric-title">Sequence Integrity</span>
                </div>
                <div class="crown-metric-value" style="color: ${summary.sequence.status === 'pass' ? '#10b981' : '#ef4444'};">
                    ${summary.sequence.totalLag === 0 ? 'Perfect' : `${summary.sequence.lagCount} gaps`}
                </div>
                <div class="crown-metric-target">
                    Total lag: ${summary.sequence.totalLag} events
                </div>
                <div class="crown-metric-target">Target: Zero desync</div>
            </div>
            
            <!-- Offline Queue -->
            <div class="crown-metric-section" style="border-bottom: none;">
                <div class="crown-metric-header">
                    <span class="crown-metric-icon">📦</span>
                    <span class="crown-metric-title">Offline Queue</span>
                </div>
                <div class="crown-metric-value" style="color: ${summary.offline.queueDepth === 0 ? '#10b981' : '#f59e0b'};">
                    ${summary.offline.queueDepth} operations
                </div>
                <div class="crown-metric-target">
                    Pending mutations awaiting sync
                </div>
            </div>
            
            <style>
                .crown-metric-section {
                    padding: 16px 0;
                    border-bottom: 1px solid rgba(148, 163, 184, 0.1);
                }
                
                .crown-metric-header {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin-bottom: 8px;
                }
                
                .crown-metric-icon {
                    font-size: 16px;
                }
                
                .crown-metric-title {
                    font-weight: 600;
                    color: #cbd5e1;
                    font-size: 13px;
                }
                
                .crown-metric-value {
                    font-size: 28px;
                    font-weight: 700;
                    margin-bottom: 4px;
                    font-family: 'SF Mono', 'Monaco', monospace;
                }
                
                .crown-metric-target {
                    font-size: 11px;
                    color: #64748b;
                }
                
                .crown-progress-bar {
                    height: 4px;
                    background: rgba(148, 163, 184, 0.1);
                    border-radius: 2px;
                    margin-top: 8px;
                    overflow: hidden;
                }
                
                .crown-progress-fill {
                    height: 100%;
                    transition: width 0.3s ease, background 0.3s ease;
                }
            </style>
        `;
    }
}

// Make globally available
window.CROWNPerformanceMonitor = CROWNPerformanceMonitor;
