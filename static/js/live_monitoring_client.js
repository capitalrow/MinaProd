/**
 * Live Monitoring Client - Real-time monitoring integration for recording sessions
 * Tracks UI updates, errors, and performance metrics during recording
 */

class LiveMonitoringClient {
    constructor() {
        this.isMonitoring = false;
        this.sessionId = null;
        this.startTime = null;
        this.monitoringInterval = null;
        
        // Metrics tracking
        this.metrics = {
            uiUpdates: 0,
            jsErrors: [],
            connectionEvents: [],
            transcriptionEvents: [],
            performanceData: []
        };
        
        console.info('🔍 Live monitoring client initialized');
    }
    
    startMonitoring(sessionId) {
        """Start comprehensive live monitoring for the session."""
        this.isMonitoring = true;
        this.sessionId = sessionId;
        this.startTime = Date.now();
        
        // Reset metrics
        this.metrics = {
            uiUpdates: 0,
            jsErrors: [],
            connectionEvents: [],
            transcriptionEvents: [],
            performanceData: []
        };
        
        console.info(`🚀 Starting live monitoring for session: ${sessionId}`);
        
        // Start monitoring intervals
        this.startPerformanceMonitoring();
        this.monitorUIUpdates();
        this.monitorTranscriptionDisplay();
        
        // Send monitoring start event
        this.sendMonitoringEvent('monitoring_started', {
            sessionId: sessionId,
            startTime: this.startTime,
            userAgent: navigator.userAgent
        });
        
        return {
            sessionId: this.sessionId,
            status: 'monitoring_active'
        };
    }
    
    startPerformanceMonitoring() {
        """Monitor performance metrics every second."""
        this.monitoringInterval = setInterval(() => {
            if (!this.isMonitoring) return;
            
            const performanceData = {
                timestamp: Date.now(),
                memory: this.getMemoryUsage(),
                timing: this.getPageTiming(),
                domElements: document.querySelectorAll('*').length,
                socketConnected: window.socket ? window.socket.connected : false
            };
            
            this.metrics.performanceData.push(performanceData);
            
            // Send real-time performance update
            this.sendMonitoringEvent('performance_update', performanceData);
            
            // Keep only last 60 entries (1 minute)
            if (this.metrics.performanceData.length > 60) {
                this.metrics.performanceData.shift();
            }
            
        }, 1000);
    }
    
    getMemoryUsage() {
        """Get memory usage information."""
        if (performance.memory) {
            return {
                used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
                limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
            };
        }
        return null;
    }
    
    getPageTiming() {
        """Get page performance timing."""
        const navigation = performance.getEntriesByType('navigation')[0];
        if (navigation) {
            return {
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                responseTime: navigation.responseEnd - navigation.responseStart
            };
        }
        return null;
    }
    
    monitorUIUpdates() {
        """Monitor UI updates and changes."""
        
        // Monitor DOM mutations
        const observer = new MutationObserver((mutations) => {
            if (!this.isMonitoring) return;
            
            mutations.forEach((mutation) => {
                this.metrics.uiUpdates++;
                
                // Track specific UI updates
                if (mutation.target.id) {
                    this.sendMonitoringEvent('ui_update', {
                        elementId: mutation.target.id,
                        type: mutation.type,
                        timestamp: Date.now()
                    });
                }
            });
        });
        
        // Start observing
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class', 'style', 'textContent']
        });
        
        // Monitor specific transcription elements
        this.monitorTranscriptionContainer();
        this.monitorStatusIndicators();
        this.monitorMetricsDisplay();
    }
    
    monitorTranscriptionContainer() {
        """Monitor transcription text display."""
        const transcriptionContainer = document.querySelector('.transcription-text') || 
                                     document.getElementById('transcriptionOutput') ||
                                     document.querySelector('[class*=\"transcript\"]');
        
        if (transcriptionContainer) {
            const observer = new MutationObserver((mutations) => {
                if (!this.isMonitoring) return;
                
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList' || mutation.type === 'characterData') {
                        const newText = transcriptionContainer.textContent || '';
                        
                        this.metrics.transcriptionEvents.push({
                            timestamp: Date.now(),
                            text: newText,
                            textLength: newText.length,
                            wordCount: newText.split(/\s+/).filter(word => word.length > 0).length
                        });
                        
                        this.sendMonitoringEvent('transcription_display_update', {
                            textLength: newText.length,
                            wordCount: newText.split(/\s+/).filter(word => word.length > 0).length,
                            timestamp: Date.now()
                        });
                        
                        console.info(`📝 Transcription display updated: ${newText.length} chars, ${newText.split(/\s+/).filter(word => word.length > 0).length} words`);
                    }
                });
            });
            
            observer.observe(transcriptionContainer, {
                childList: true,
                subtree: true,
                characterData: true
            });
        }
    }
    
    monitorStatusIndicators() {
        """Monitor status indicators (connection, recording, etc.)."""
        const statusElements = [
            document.getElementById('wsStatus'),
            document.getElementById('micStatus'),
            document.getElementById('recordingStatus'),
            document.querySelector('.status-indicator')
        ].filter(Boolean);
        
        statusElements.forEach(element => {
            const observer = new MutationObserver((mutations) => {
                if (!this.isMonitoring) return;
                
                mutations.forEach((mutation) => {
                    this.sendMonitoringEvent('status_indicator_change', {
                        elementId: element.id || element.className,
                        newValue: element.textContent,
                        timestamp: Date.now()
                    });
                });
            });
            
            observer.observe(element, {
                attributes: true,
                childList: true,
                characterData: true
            });
        });
    }
    
    monitorMetricsDisplay() {
        """Monitor metrics display elements."""
        const metricsElements = [
            document.getElementById('segmentCount'),
            document.getElementById('avgConfidence'),
            document.getElementById('sessionDuration'),
            document.getElementById('wordsPerMinute')
        ].filter(Boolean);
        
        metricsElements.forEach(element => {
            const observer = new MutationObserver((mutations) => {
                if (!this.isMonitoring) return;
                
                this.sendMonitoringEvent('metrics_display_update', {
                    elementId: element.id,
                    value: element.textContent,
                    timestamp: Date.now()
                });
            });
            
            observer.observe(element, {
                childList: true,
                characterData: true
            });
        });
    }
    
    monitorTranscriptionDisplay() {
        """Monitor transcription text visibility and performance."""
        
        // Check transcription display performance every 2 seconds
        setInterval(() => {
            if (!this.isMonitoring) return;
            
            const transcriptionElements = document.querySelectorAll('[class*=\"transcript\"], .transcription-text, #transcriptionOutput');
            
            transcriptionElements.forEach(element => {
                const rect = element.getBoundingClientRect();
                const isVisible = rect.top >= 0 && rect.left >= 0 && 
                                rect.bottom <= window.innerHeight && 
                                rect.right <= window.innerWidth;
                
                const text = element.textContent || '';
                
                this.sendMonitoringEvent('transcription_visibility_check', {
                    elementId: element.id || element.className,
                    isVisible: isVisible,
                    textLength: text.length,
                    wordCount: text.split(/\s+/).filter(word => word.length > 0).length,
                    timestamp: Date.now()
                });
            });
            
        }, 2000);
    }
    
    recordConnectionEvent(eventType, isConnected) {
        """Record WebSocket connection event."""
        if (!this.isMonitoring) return;
        
        const event = {
            timestamp: Date.now(),
            eventType: eventType,
            connected: isConnected
        };
        
        this.metrics.connectionEvents.push(event);
        
        this.sendMonitoringEvent('connection_event', event);
        
        console.info(`🔌 Connection event: ${eventType} (connected: ${isConnected})`);
    }
    
    recordJavaScriptError(error, source = '') {
        """Record JavaScript error."""
        if (!this.isMonitoring) return;
        
        const errorData = {
            timestamp: Date.now(),
            message: error.toString(),
            source: source,
            stack: error.stack || ''
        };
        
        this.metrics.jsErrors.push(errorData);
        
        this.sendMonitoringEvent('javascript_error', errorData);
        
        console.warn(`🚨 JS Error recorded: ${error.toString()}`);
    }
    
    sendMonitoringEvent(eventType, data) {
        """Send monitoring event to server."""
        if (window.socket && window.socket.connected) {
            window.socket.emit('live_monitoring_event', {
                sessionId: this.sessionId,
                eventType: eventType,
                data: data,
                timestamp: Date.now()
            });
        }
    }
    
    getCurrentMetrics() {
        """Get current monitoring metrics."""
        if (!this.isMonitoring) return null;
        
        const duration = (Date.now() - this.startTime) / 1000;
        const latestPerformance = this.metrics.performanceData[this.metrics.performanceData.length - 1];
        
        return {
            sessionId: this.sessionId,
            duration: duration,
            uiUpdates: this.metrics.uiUpdates,
            jsErrors: this.metrics.jsErrors.length,
            connectionEvents: this.metrics.connectionEvents.length,
            transcriptionEvents: this.metrics.transcriptionEvents.length,
            currentMemoryMB: latestPerformance?.memory?.used || 0,
            socketConnected: latestPerformance?.socketConnected || false,
            wordsTranscribed: this.getLatestWordCount(),
            status: 'active'
        };
    }
    
    getLatestWordCount() {
        """Get latest word count from transcription events."""
        const latest = this.metrics.transcriptionEvents[this.metrics.transcriptionEvents.length - 1];
        return latest ? latest.wordCount : 0;
    }
    
    endMonitoring() {
        """End monitoring and generate final report."""
        if (!this.isMonitoring) return null;
        
        this.isMonitoring = false;
        
        // Clear intervals
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
        
        const endTime = Date.now();
        const duration = (endTime - this.startTime) / 1000;
        
        const finalReport = {
            sessionId: this.sessionId,
            startTime: this.startTime,
            endTime: endTime,
            duration: duration,
            
            // Summary metrics
            totalUIUpdates: this.metrics.uiUpdates,
            totalJSErrors: this.metrics.jsErrors.length,
            totalConnectionEvents: this.metrics.connectionEvents.length,
            totalTranscriptionEvents: this.metrics.transcriptionEvents.length,
            
            // Performance summary
            avgMemoryMB: this.calculateAverageMemory(),
            peakMemoryMB: this.calculatePeakMemory(),
            
            // Quality metrics
            wordsTranscribed: this.getLatestWordCount(),
            uiUpdatesPerSecond: this.metrics.uiUpdates / duration,
            
            status: 'completed'
        };
        
        // Send final report
        this.sendMonitoringEvent('monitoring_ended', finalReport);
        
        console.info('✅ Live monitoring completed', finalReport);
        
        return finalReport;
    }
    
    calculateAverageMemory() {
        """Calculate average memory usage."""
        const memoryData = this.metrics.performanceData
            .map(data => data.memory?.used)
            .filter(val => val !== undefined);
        
        return memoryData.length > 0 ? 
            memoryData.reduce((sum, val) => sum + val, 0) / memoryData.length : 0;
    }
    
    calculatePeakMemory() {
        """Calculate peak memory usage."""
        const memoryData = this.metrics.performanceData
            .map(data => data.memory?.used)
            .filter(val => val !== undefined);
        
        return memoryData.length > 0 ? Math.max(...memoryData) : 0;
    }
}

// Initialize live monitoring client
window.liveMonitoringClient = new LiveMonitoringClient();

// Integration handled by unified enhancement integration system

// Integrate with WebSocket events
if (window.socket) {
    window.socket.on('connect', () => {
        if (window.liveMonitoringClient) {
            window.liveMonitoringClient.recordConnectionEvent('connect', true);
        }
    });
    
    window.socket.on('disconnect', () => {
        if (window.liveMonitoringClient) {
            window.liveMonitoringClient.recordConnectionEvent('disconnect', false);
        }
    });
    
    window.socket.on('error', (error) => {
        if (window.liveMonitoringClient) {
            window.liveMonitoringClient.recordConnectionEvent('error', false);
        }
    });
}

// Override console.error to capture JS errors
const originalConsoleError = console.error;
console.error = function(...args) {
    if (window.liveMonitoringClient && window.liveMonitoringClient.isMonitoring) {
        window.liveMonitoringClient.recordJavaScriptError(new Error(args.join(' ')), 'console.error');
    }
    originalConsoleError.apply(console, args);
};

// Capture unhandled errors
window.addEventListener('error', (event) => {
    if (window.liveMonitoringClient && window.liveMonitoringClient.isMonitoring) {
        window.liveMonitoringClient.recordJavaScriptError(event.error || new Error(event.message), event.filename);
    }
});

console.info('🔍 Live monitoring client ready - will automatically start with recording sessions');