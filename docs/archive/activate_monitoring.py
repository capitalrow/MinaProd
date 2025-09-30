#!/usr/bin/env python3
"""
🔧 MINA Monitoring Activation Script
Activates and integrates existing monitoring systems for proactive issue detection.
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import existing MINA monitoring services
from services.performance_monitor import PerformanceMonitor
from services.qa_pipeline import QAPipeline  
from services.confidence_scoring import ConfidenceService
from services.incident_response import IncidentResponseManager
from services.websocket_reliability import get_reliability_manager

logger = logging.getLogger(__name__)

class MinaMonitoringDashboard:
    """Integrates all existing monitoring systems into a unified dashboard."""
    
    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.qa_pipeline = QAPipeline()
        self.confidence_service = ConfidenceService()
        self.incident_manager = IncidentResponseManager()
        self.reliability_manager = get_reliability_manager()
        
        # Alert thresholds (configurable)
        self.thresholds = {
            'session_creation_timeout_rate': 0.05,  # 5% failure rate triggers alert
            'websocket_disconnection_rate': 0.10,   # 10% disconnection rate
            'average_latency_ms': 2000,              # 2 second latency threshold
            'confidence_score_minimum': 0.60,       # 60% minimum confidence
            'promise_timeout_rate': 0.03             # 3% promise timeout rate
        }
        
        # Issue detection state
        self.detected_issues = []
        self.last_check = datetime.now()
        
    def collect_real_time_metrics(self) -> Dict[str, Any]:
        """Collect metrics from all existing monitoring systems."""
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system_health': {},
            'performance': {},
            'quality': {},
            'connectivity': {},
            'issues': []
        }
        
        try:
            # Performance metrics (from existing performance_monitor.py)
            if hasattr(self.performance_monitor, 'get_current_metrics'):
                perf_data = self.performance_monitor.get_current_metrics()
                metrics['performance'] = {
                    'average_latency_ms': perf_data.get('avg_latency', 0),
                    'queue_depth': perf_data.get('queue_depth', 0),
                    'cpu_usage': perf_data.get('cpu_usage', 0),
                    'memory_usage_mb': perf_data.get('memory_usage', 0),
                    'active_sessions': perf_data.get('active_sessions', 0)
                }
                
            # Quality metrics (from existing qa_pipeline.py)
            if hasattr(self.qa_pipeline, 'get_quality_summary'):
                quality_data = self.qa_pipeline.get_quality_summary()
                metrics['quality'] = {
                    'average_wer': quality_data.get('wer_score', 0),
                    'duplicate_rate': quality_data.get('duplicate_rate', 0),
                    'confidence_distribution': quality_data.get('confidence_dist', [])
                }
                
            # Connectivity metrics (from existing websocket_reliability.py)
            if self.reliability_manager:
                conn_data = self.reliability_manager.get_connection_stats()
                metrics['connectivity'] = {
                    'total_connections': conn_data.get('total_connections', 0),
                    'active_connections': conn_data.get('active_connections', 0),
                    'failed_connections': conn_data.get('failed_connections', 0),
                    'reconnection_rate': conn_data.get('reconnection_rate', 0)
                }
                
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            metrics['issues'].append({
                'type': 'monitoring_error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
        return metrics
    
    def detect_issues(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Proactive issue detection using existing monitoring data."""
        
        issues = []
        
        # Session creation timeout detection
        if metrics['performance'].get('average_latency_ms', 0) > self.thresholds['average_latency_ms']:
            issues.append({
                'type': 'high_latency',
                'severity': 'high',
                'message': f"Average latency {metrics['performance']['average_latency_ms']}ms exceeds {self.thresholds['average_latency_ms']}ms threshold",
                'recommendation': 'Check server resources and database connectivity'
            })
            
        # WebSocket disconnection rate
        conn_metrics = metrics['connectivity']
        if conn_metrics.get('total_connections', 0) > 0:
            disconnection_rate = conn_metrics.get('failed_connections', 0) / conn_metrics['total_connections']
            if disconnection_rate > self.thresholds['websocket_disconnection_rate']:
                issues.append({
                    'type': 'websocket_instability', 
                    'severity': 'medium',
                    'message': f"WebSocket disconnection rate {disconnection_rate:.2%} exceeds {self.thresholds['websocket_disconnection_rate']:.2%}",
                    'recommendation': 'Check network stability and server load'
                })
                
        # Quality degradation detection
        quality_metrics = metrics['quality']
        if quality_metrics.get('average_wer', 0) > 0.3:  # 30% word error rate
            issues.append({
                'type': 'quality_degradation',
                'severity': 'medium', 
                'message': f"Word Error Rate {quality_metrics['average_wer']:.2%} indicates transcription quality issues",
                'recommendation': 'Check audio quality and model performance'
            })
            
        return issues
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report using existing systems."""
        
        metrics = self.collect_real_time_metrics()
        issues = self.detect_issues(metrics)
        
        # Calculate overall health score
        health_score = 100
        for issue in issues:
            if issue['severity'] == 'critical':
                health_score -= 30
            elif issue['severity'] == 'high':
                health_score -= 20
            elif issue['severity'] == 'medium':
                health_score -= 10
            else:
                health_score -= 5
                
        health_score = max(0, health_score)
        
        report = {
            'overall_health': {
                'score': health_score,
                'status': 'healthy' if health_score >= 80 else 'degraded' if health_score >= 60 else 'unhealthy',
                'last_updated': datetime.now().isoformat()
            },
            'metrics': metrics,
            'issues': issues,
            'recommendations': self._generate_recommendations(issues)
        }
        
        return report
    
    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations based on detected issues."""
        
        recommendations = []
        
        issue_types = [issue['type'] for issue in issues]
        
        if 'high_latency' in issue_types:
            recommendations.append("Scale up server resources or optimize database queries")
            
        if 'websocket_instability' in issue_types:
            recommendations.append("Implement more aggressive WebSocket reconnection strategy")
            
        if 'quality_degradation' in issue_types:
            recommendations.append("Review audio input quality and consider model retraining")
            
        if not recommendations:
            recommendations.append("System operating normally - continue monitoring")
            
        return recommendations

def setup_monitoring_endpoints():
    """Set up monitoring endpoints that integrate existing systems."""
    
    from flask import Blueprint, jsonify
    from app import app
    
    monitor_bp = Blueprint('monitoring', __name__)
    dashboard = MinaMonitoringDashboard()
    
    @monitor_bp.route('/api/monitoring/health')
    def health_report():
        """Enhanced health endpoint using existing monitoring systems."""
        try:
            report = dashboard.generate_health_report()
            return jsonify(report), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    @monitor_bp.route('/api/monitoring/metrics') 
    def current_metrics():
        """Real-time metrics from existing monitoring systems."""
        try:
            metrics = dashboard.collect_real_time_metrics()
            return jsonify(metrics), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    @monitor_bp.route('/api/monitoring/issues')
    def current_issues():
        """Current issues detected by monitoring systems."""
        try:
            metrics = dashboard.collect_real_time_metrics()
            issues = dashboard.detect_issues(metrics)
            return jsonify({'issues': issues}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    app.register_blueprint(monitor_bp)
    logger.info("Monitoring endpoints registered successfully")

def start_continuous_monitoring():
    """Start continuous monitoring using existing systems."""
    
    dashboard = MinaMonitoringDashboard()
    
    def monitoring_loop():
        while True:
            try:
                report = dashboard.generate_health_report()
                
                # Log critical issues immediately
                critical_issues = [i for i in report['issues'] if i['severity'] == 'critical']
                if critical_issues:
                    logger.critical(f"CRITICAL ISSUES DETECTED: {critical_issues}")
                    
                # Log health score changes
                health_score = report['overall_health']['score']
                if health_score < 80:
                    logger.warning(f"Health score degraded to {health_score}%")
                    
                # Sleep for monitoring interval
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(30)  # Retry in 30 seconds on error
    
    import threading
    monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
    monitoring_thread.start()
    logger.info("Continuous monitoring started")

if __name__ == "__main__":
    # Activate monitoring systems
    print("🔧 Activating MINA monitoring systems...")
    
    # Set up endpoints
    setup_monitoring_endpoints()
    
    # Start continuous monitoring  
    start_continuous_monitoring()
    
    print("✅ MINA monitoring systems activated!")
    print("📊 Access monitoring at:")
    print("  - Health Report: /api/monitoring/health")
    print("  - Real-time Metrics: /api/monitoring/metrics") 
    print("  - Current Issues: /api/monitoring/issues")