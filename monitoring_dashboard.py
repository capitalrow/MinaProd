"""
🔧 PRODUCTION MONITORING DASHBOARD
Real-time metrics collection and visualization for Mina scaling journey
"""

import time
import json
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from flask import Blueprint, jsonify, render_template_string, request
from services.health_monitor import get_health_monitor

# Create monitoring blueprint
monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

@dataclass
class ScalingMetrics:
    """Real-time scaling metrics for decision making"""
    timestamp: float
    active_sessions: int
    memory_usage_mb: float
    memory_growth_rate: float  # MB/minute
    cpu_usage_percent: float
    transcription_latency_ms: float
    websocket_connections: int
    database_connections: int
    api_error_rate: float
    cost_per_hour: float = 0.0
    user_satisfaction_score: float = 0.0

class ProductionMonitor:
    """
    Production monitoring system for Mina scaling strategy
    Implements the monitoring framework from COMPREHENSIVE_SCALING_PLAN.md
    """
    
    def __init__(self):
        self.metrics_history = deque(maxlen=1440)  # 24 hours of minute-by-minute data
        self.scaling_alerts = deque(maxlen=100)
        self.decision_log = deque(maxlen=50)
        self.lock = threading.RLock()
        
        # Phase tracking
        self.current_phase = 1
        self.phase_start_time = time.time()
        
        # Scaling thresholds from the plan
        self.phase_thresholds = {
            1: {  # Phase 1: 10-50 users
                "max_concurrent_sessions": 50,
                "max_memory_growth": 10.0,  # MB/hour
                "max_latency_ms": 400,
                "max_cost_per_user": 15.0,
                "target_uptime": 99.0
            },
            2: {  # Phase 2: 50-200 users
                "max_concurrent_sessions": 200,
                "max_memory_growth": 15.0,
                "max_latency_ms": 500,
                "max_cost_per_user": 9.0,
                "target_uptime": 99.9
            },
            3: {  # Phase 3: 500+ users
                "max_concurrent_sessions": 500,
                "max_memory_growth": 20.0,
                "max_latency_ms": 400,
                "max_cost_per_user": 2.4,
                "target_uptime": 99.95
            }
        }
        
        # Real-time counters
        self.session_counter = 0
        self.total_requests = 0
        self.error_counter = 0
        self.start_time = time.time()
        
    def collect_metrics(self) -> ScalingMetrics:
        """Collect current metrics for scaling analysis"""
        health_monitor = get_health_monitor()
        current_health = health_monitor.get_current_health()
        
        # Get memory growth rate from health monitor
        memory_growth_history = health_monitor.get_metric_history('memory_growth_rate', 60)
        avg_memory_growth = 0.0
        if memory_growth_history:
            avg_memory_growth = sum(m.value for m in memory_growth_history) / len(memory_growth_history)
        
        # Calculate API error rate
        error_rate = (self.error_counter / max(self.total_requests, 1)) * 100
        
        # Create metrics snapshot
        metrics = ScalingMetrics(
            timestamp=time.time(),
            active_sessions=getattr(current_health, 'active_sessions', 0),
            memory_usage_mb=getattr(current_health, 'memory_usage', 0) * 1024,  # Convert GB to MB
            memory_growth_rate=avg_memory_growth,
            cpu_usage_percent=getattr(current_health, 'cpu_usage', 0),
            transcription_latency_ms=getattr(current_health, 'api_response_time', 0),
            websocket_connections=self.session_counter,
            database_connections=5,  # Placeholder - would integrate with actual DB metrics
            api_error_rate=error_rate,
            cost_per_hour=self._estimate_current_cost(),
            user_satisfaction_score=self._calculate_satisfaction_score()
        )
        
        with self.lock:
            self.metrics_history.append(metrics)
            
        return metrics
    
    def _estimate_current_cost(self) -> float:
        """Estimate current hourly cost based on usage"""
        # Simple cost model based on active sessions
        # This would integrate with actual cloud billing APIs in production
        base_cost = 0.50  # Base infrastructure cost per hour
        session_cost = self.session_counter * 0.10  # $0.10 per active session per hour
        return base_cost + session_cost
    
    def _calculate_satisfaction_score(self) -> float:
        """Calculate user satisfaction based on performance metrics"""
        health_monitor = get_health_monitor()
        
        # Get recent performance metrics
        latency_history = health_monitor.get_metric_history('api_response_time', 30)
        error_history = health_monitor.get_metric_history('error_rate', 30)
        
        # Calculate satisfaction score (0-5 scale)
        score = 5.0
        
        # Reduce score based on latency
        if latency_history:
            avg_latency = sum(m.value for m in latency_history) / len(latency_history)
            if avg_latency > 1000:  # >1 second
                score -= 2.0
            elif avg_latency > 500:  # >500ms
                score -= 1.0
            elif avg_latency > 200:  # >200ms
                score -= 0.5
        
        # Reduce score based on errors
        if error_history:
            avg_errors = sum(m.value for m in error_history) / len(error_history)
            if avg_errors > 5:  # >5% error rate
                score -= 2.0
            elif avg_errors > 1:  # >1% error rate
                score -= 1.0
        
        return max(0.0, min(5.0, score))
    
    def check_scaling_triggers(self, metrics: ScalingMetrics) -> List[Dict]:
        """Check if scaling actions are needed based on current metrics"""
        alerts = []
        current_thresholds = self.phase_thresholds[self.current_phase]
        
        # Check session capacity
        if metrics.active_sessions > current_thresholds["max_concurrent_sessions"] * 0.8:
            alerts.append({
                "type": "scaling_warning",
                "metric": "active_sessions",
                "current": metrics.active_sessions,
                "threshold": current_thresholds["max_concurrent_sessions"],
                "recommendation": "Consider scaling to next phase",
                "urgency": "medium"
            })
        
        # Check memory growth
        if metrics.memory_growth_rate > current_thresholds["max_memory_growth"]:
            alerts.append({
                "type": "memory_leak",
                "metric": "memory_growth_rate",
                "current": metrics.memory_growth_rate,
                "threshold": current_thresholds["max_memory_growth"],
                "recommendation": "Investigate memory leaks immediately",
                "urgency": "high"
            })
        
        # Check latency
        if metrics.transcription_latency_ms > current_thresholds["max_latency_ms"]:
            alerts.append({
                "type": "performance_degradation",
                "metric": "transcription_latency",
                "current": metrics.transcription_latency_ms,
                "threshold": current_thresholds["max_latency_ms"],
                "recommendation": "Optimize processing pipeline or scale infrastructure",
                "urgency": "medium"
            })
        
        # Check cost efficiency
        current_cost_per_user = metrics.cost_per_hour / max(metrics.active_sessions, 1)
        if current_cost_per_user > current_thresholds["max_cost_per_user"]:
            alerts.append({
                "type": "cost_efficiency",
                "metric": "cost_per_user",
                "current": current_cost_per_user,
                "threshold": current_thresholds["max_cost_per_user"],
                "recommendation": "Optimize resource usage or implement cost controls",
                "urgency": "medium"
            })
        
        # Store alerts
        with self.lock:
            for alert in alerts:
                alert["timestamp"] = time.time()
                self.scaling_alerts.append(alert)
        
        return alerts
    
    def evaluate_phase_transition(self) -> Optional[Dict]:
        """Evaluate if it's time to transition to the next phase"""
        if len(self.metrics_history) < 60:  # Need at least 1 hour of data
            return None
        
        # Get recent metrics (last hour)
        recent_metrics = list(self.metrics_history)[-60:]
        avg_sessions = sum(m.active_sessions for m in recent_metrics) / len(recent_metrics)
        
        current_thresholds = self.phase_thresholds[self.current_phase]
        
        # Check if consistently hitting capacity
        if avg_sessions > current_thresholds["max_concurrent_sessions"] * 0.7:
            time_in_phase = (time.time() - self.phase_start_time) / (24 * 3600)  # days
            
            if time_in_phase > 14:  # At least 2 weeks in current phase
                next_phase = self.current_phase + 1
                if next_phase <= 3:
                    recommendation = {
                        "action": "phase_transition",
                        "from_phase": self.current_phase,
                        "to_phase": next_phase,
                        "reason": f"Sustained {avg_sessions:.1f} avg sessions for {time_in_phase:.1f} days",
                        "timestamp": time.time(),
                        "readiness_checklist": self._get_phase_readiness_checklist(next_phase)
                    }
                    
                    with self.lock:
                        self.decision_log.append(recommendation)
                    
                    return recommendation
        
        return None
    
    def _get_phase_readiness_checklist(self, phase: int) -> List[str]:
        """Get readiness checklist for next phase"""
        checklists = {
            2: [
                "Sustained >40 concurrent users for 2 weeks",
                "<2% error rate maintained under load", 
                "User satisfaction score >4.0/5",
                "Technical debt backlog manageable",
                "Team capacity for optimization improvements"
            ],
            3: [
                "Sustained >150 concurrent users for 4 weeks",
                "Revenue model validated (if applicable)",
                "Market demand confirmed for enterprise features",
                "Technical architecture tested at 500+ users",
                "Competitive positioning requires advanced features"
            ]
        }
        return checklists.get(phase, [])
    
    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data"""
        current_metrics = self.collect_metrics()
        alerts = self.check_scaling_triggers(current_metrics)
        phase_recommendation = self.evaluate_phase_transition()
        
        # Calculate trends
        if len(self.metrics_history) >= 2:
            prev_metrics = self.metrics_history[-2]
            trends = {
                "sessions_trend": current_metrics.active_sessions - prev_metrics.active_sessions,
                "memory_trend": current_metrics.memory_usage_mb - prev_metrics.memory_usage_mb,
                "latency_trend": current_metrics.transcription_latency_ms - prev_metrics.transcription_latency_ms,
                "cost_trend": current_metrics.cost_per_hour - prev_metrics.cost_per_hour
            }
        else:
            trends = {"sessions_trend": 0, "memory_trend": 0, "latency_trend": 0, "cost_trend": 0}
        
        return {
            "current_metrics": asdict(current_metrics),
            "current_phase": self.current_phase,
            "phase_thresholds": self.phase_thresholds[self.current_phase],
            "active_alerts": alerts,
            "trends": trends,
            "phase_recommendation": phase_recommendation,
            "uptime_hours": (time.time() - self.start_time) / 3600,
            "total_requests": self.total_requests,
            "success_rate": ((self.total_requests - self.error_counter) / max(self.total_requests, 1)) * 100
        }

# Global monitoring instance
production_monitor = ProductionMonitor()

@monitoring_bp.route('/dashboard')
def dashboard():
    """Production monitoring dashboard"""
    return render_template_string(DASHBOARD_HTML)

@monitoring_bp.route('/api/metrics')
def api_metrics():
    """API endpoint for real-time metrics"""
    return jsonify(production_monitor.get_dashboard_data())

@monitoring_bp.route('/api/metrics/history')
def api_metrics_history():
    """API endpoint for metrics history"""
    hours = int(request.args.get('hours', 24))
    cutoff_time = time.time() - (hours * 3600)
    
    with production_monitor.lock:
        history = [
            asdict(m) for m in production_monitor.metrics_history 
            if m.timestamp >= cutoff_time
        ]
    
    return jsonify({"history": history, "hours": hours})

@monitoring_bp.route('/api/alerts')
def api_alerts():
    """API endpoint for scaling alerts"""
    hours = int(request.args.get('hours', 24))
    cutoff_time = time.time() - (hours * 3600)
    
    with production_monitor.lock:
        alerts = [
            alert for alert in production_monitor.scaling_alerts 
            if alert["timestamp"] >= cutoff_time
        ]
    
    return jsonify({"alerts": alerts, "count": len(alerts)})

# Dashboard HTML template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Mina Production Monitoring</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #3498db; }
        .metric-label { color: #7f8c8d; margin-top: 5px; }
        .alert { padding: 15px; margin: 10px 0; border-radius: 5px; }
        .alert-high { background: #e74c3c; color: white; }
        .alert-medium { background: #f39c12; color: white; }
        .alert-low { background: #f1c40f; color: #2c3e50; }
        .phase-indicator { background: #27ae60; color: white; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .chart-container { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .status-healthy { color: #27ae60; }
        .status-warning { color: #f39c12; }
        .status-critical { color: #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Mina Production Monitoring Dashboard</h1>
            <p>Real-time scaling metrics and phase transition monitoring</p>
        </div>
        
        <div id="phase-indicator" class="phase-indicator">
            Loading...
        </div>
        
        <div class="metrics-grid" id="metrics-grid">
            <!-- Metrics will be populated by JavaScript -->
        </div>
        
        <div id="alerts-container">
            <!-- Alerts will be populated by JavaScript -->
        </div>
        
        <div class="chart-container">
            <h3>Active Sessions Over Time</h3>
            <canvas id="sessionsChart" width="400" height="200"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>Memory Usage Trend</h3>
            <canvas id="memoryChart" width="400" height="200"></canvas>
        </div>
    </div>

    <script>
        let sessionsChart, memoryChart;
        
        function initCharts() {
            const sessionsCtx = document.getElementById('sessionsChart').getContext('2d');
            sessionsChart = new Chart(sessionsCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Active Sessions',
                        data: [],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
            
            const memoryCtx = document.getElementById('memoryChart').getContext('2d');
            memoryChart = new Chart(memoryCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Memory Usage (MB)',
                        data: [],
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: false }
                    }
                }
            });
        }
        
        function updateDashboard() {
            fetch('/monitoring/api/metrics')
                .then(response => response.json())
                .then(data => {
                    updateMetrics(data);
                    updateAlerts(data.active_alerts);
                    updatePhaseIndicator(data);
                })
                .catch(error => console.error('Error fetching metrics:', error));
        }
        
        function updateMetrics(data) {
            const metrics = data.current_metrics;
            const trends = data.trends;
            
            const metricsGrid = document.getElementById('metrics-grid');
            metricsGrid.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value">${metrics.active_sessions}</div>
                    <div class="metric-label">Active Sessions</div>
                    <div class="metric-label">${trends.sessions_trend >= 0 ? '↗' : '↘'} ${Math.abs(trends.sessions_trend)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${metrics.memory_usage_mb.toFixed(1)}</div>
                    <div class="metric-label">Memory Usage (MB)</div>
                    <div class="metric-label">Growth: ${metrics.memory_growth_rate.toFixed(2)} MB/min</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${metrics.transcription_latency_ms.toFixed(0)}</div>
                    <div class="metric-label">Latency (ms)</div>
                    <div class="metric-label">${trends.latency_trend >= 0 ? '↗' : '↘'} ${Math.abs(trends.latency_trend).toFixed(0)}ms</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${metrics.cpu_usage_percent.toFixed(1)}%</div>
                    <div class="metric-label">CPU Usage</div>
                    <div class="metric-label">System Load</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">$${metrics.cost_per_hour.toFixed(2)}</div>
                    <div class="metric-label">Cost per Hour</div>
                    <div class="metric-label">${trends.cost_trend >= 0 ? '↗' : '↘'} $${Math.abs(trends.cost_trend).toFixed(2)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.success_rate.toFixed(1)}%</div>
                    <div class="metric-label">Success Rate</div>
                    <div class="metric-label">${data.total_requests} total requests</div>
                </div>
            `;
        }
        
        function updateAlerts(alerts) {
            const alertsContainer = document.getElementById('alerts-container');
            
            if (alerts.length === 0) {
                alertsContainer.innerHTML = '<div style="background: #2ecc71; color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">✅ All systems healthy - no alerts</div>';
                return;
            }
            
            let alertsHtml = '<h3>🚨 Active Alerts</h3>';
            alerts.forEach(alert => {
                const urgencyClass = `alert-${alert.urgency}`;
                alertsHtml += `
                    <div class="alert ${urgencyClass}">
                        <strong>${alert.type.replace('_', ' ').toUpperCase()}</strong><br>
                        ${alert.recommendation}<br>
                        <small>Current: ${alert.current} | Threshold: ${alert.threshold}</small>
                    </div>
                `;
            });
            
            alertsContainer.innerHTML = alertsHtml;
        }
        
        function updatePhaseIndicator(data) {
            const phaseIndicator = document.getElementById('phase-indicator');
            const threshold = data.phase_thresholds;
            
            let phaseHtml = `
                <h3>📈 Phase ${data.current_phase} - Scaling Journey</h3>
                <p>Target: ${threshold.max_concurrent_sessions} concurrent sessions | 
                   Max latency: ${threshold.max_latency_ms}ms | 
                   Uptime: ${data.uptime_hours.toFixed(1)} hours</p>
            `;
            
            if (data.phase_recommendation) {
                phaseHtml += `
                    <div style="background: #f39c12; padding: 10px; border-radius: 5px; margin-top: 10px;">
                        <strong>🎯 Phase Transition Recommended:</strong> 
                        Phase ${data.phase_recommendation.from_phase} → Phase ${data.phase_recommendation.to_phase}<br>
                        <small>${data.phase_recommendation.reason}</small>
                    </div>
                `;
            }
            
            phaseIndicator.innerHTML = phaseHtml;
        }
        
        // Initialize dashboard
        initCharts();
        updateDashboard();
        
        // Update every 30 seconds
        setInterval(updateDashboard, 30000);
    </script>
</body>
</html>
"""

def get_production_monitor():
    """Get the global production monitor instance"""
    return production_monitor