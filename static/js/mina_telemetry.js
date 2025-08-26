/**
 * 📊 MINA Telemetry - Client-side monitoring and issue detection
 * Integrates with existing server-side monitoring systems
 */

class MinaTelemetry {
  constructor() {
    this.sessionMetrics = [];
    this.errorPatterns = [];
    this.performanceBaseline = {
      sessionCreationTimeMs: 3000,  // Expected max time
      socketConnectionTimeMs: 2000,
      audioChunkIntervalMs: 200
    };
    
    console.log('📊 MINA Telemetry initialized');
  }
  
  reportSessionSuccess(totalTimeMs) {
    const metric = {
      type: 'session_success',
      totalTimeMs,
      timestamp: Date.now(),
      wasSlowSession: totalTimeMs > this.performanceBaseline.sessionCreationTimeMs
    };
    
    this.sessionMetrics.push(metric);
    
    // Alert on slow session creation
    if (metric.wasSlowSession) {
      console.warn(`⚠️ Slow session creation: ${totalTimeMs}ms (expected <${this.performanceBaseline.sessionCreationTimeMs}ms)`);
      this.sendTelemetry('slow_session_creation', metric);
    }
    
    // Keep only last 50 metrics
    if (this.sessionMetrics.length > 50) {
      this.sessionMetrics = this.sessionMetrics.slice(-50);
    }
  }
  
  reportSessionTimeout(details) {
    const errorMetric = {
      type: 'session_timeout',
      details,
      timestamp: Date.now(),
      pattern: this.analyzeTimeoutPattern(details)
    };
    
    this.errorPatterns.push(errorMetric);
    
    console.error('🚨 Session timeout tracked:', errorMetric);
    this.sendTelemetry('session_timeout', errorMetric);
    
    // Detect timeout patterns
    this.detectTimeoutPatterns();
  }
  
  reportWebSocketIssue(eventType, details) {
    const wsMetric = {
      type: 'websocket_issue',
      eventType,
      details,
      timestamp: Date.now()
    };
    
    console.warn('📡 WebSocket issue tracked:', wsMetric);
    this.sendTelemetry('websocket_issue', wsMetric);
  }
  
  analyzeTimeoutPattern(details) {
    // Analyze timeout context to identify patterns
    if (details.hasSessionId && !details.socketConnected) {
      return 'socket_disconnected_after_session_created';
    } else if (!details.hasSessionId && details.socketConnected) {
      return 'session_creation_failed_with_connected_socket';
    } else if (!details.socketConnected) {
      return 'socket_connection_lost';
    } else {
      return 'promise_resolution_timeout';
    }
  }
  
  detectTimeoutPatterns() {
    // Look for recurring timeout patterns in last 10 attempts
    const recentTimeouts = this.errorPatterns
      .filter(e => e.type === 'session_timeout')
      .slice(-10);
      
    if (recentTimeouts.length >= 3) {
      const patterns = recentTimeouts.map(t => t.pattern);
      const mostCommon = this.getMostCommonPattern(patterns);
      
      if (mostCommon.count >= 2) {
        console.error(`🔴 PATTERN DETECTED: ${mostCommon.pattern} (${mostCommon.count} times)`);
        this.sendTelemetry('timeout_pattern_detected', {
          pattern: mostCommon.pattern,
          occurrences: mostCommon.count,
          recentTimeouts: recentTimeouts.length
        });
      }
    }
  }
  
  getMostCommonPattern(patterns) {
    const counts = {};
    patterns.forEach(p => counts[p] = (counts[p] || 0) + 1);
    
    const entries = Object.entries(counts);
    const [pattern, count] = entries.reduce((max, current) => 
      current[1] > max[1] ? current : max, ['', 0]);
      
    return { pattern, count };
  }
  
  sendTelemetry(eventType, data) {
    // Send to monitoring endpoint (non-blocking)
    try {
      fetch('/api/telemetry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_type: eventType,
          data,
          user_agent: navigator.userAgent,
          url: window.location.href,
          timestamp: Date.now()
        })
      }).catch(e => {
        // Silently fail - don't interfere with main app
        console.debug('Telemetry send failed (non-critical):', e.message);
      });
    } catch (e) {
      // Silently fail
      console.debug('Telemetry error (non-critical):', e.message);
    }
  }
  
  getHealthSummary() {
    const recentSessions = this.sessionMetrics.slice(-10);
    const recentErrors = this.errorPatterns.slice(-10);
    
    return {
      recentSessionSuccessRate: recentSessions.length / (recentSessions.length + recentErrors.length),
      averageSessionTime: recentSessions.reduce((sum, s) => sum + s.totalTimeMs, 0) / recentSessions.length || 0,
      recentErrorTypes: recentErrors.map(e => e.type),
      slowSessionCount: recentSessions.filter(s => s.wasSlowSession).length
    };
  }
}

// Initialize global telemetry
window._minaTelemetry = new MinaTelemetry();

// Integrate with existing WebSocket monitoring
if (typeof socket !== 'undefined') {
  socket.on('disconnect', (reason) => {
    window._minaTelemetry.reportWebSocketIssue('disconnect', { reason });
  });
  
  socket.on('connect_error', (error) => {
    window._minaTelemetry.reportWebSocketIssue('connect_error', { error: error.message });
  });
}