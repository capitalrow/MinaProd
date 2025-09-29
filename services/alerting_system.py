"""
🚨 Production Alerting System
Real-time alerting for 100% monitoring coverage with notification channels.
"""
import logging
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import json

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"

@dataclass
class Alert:
    """Alert definition"""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    source: str
    metric: str
    value: float
    threshold: float
    timestamp: float = field(default_factory=time.time)
    status: AlertStatus = AlertStatus.ACTIVE
    tags: Dict[str, str] = field(default_factory=dict)
    
class AlertingSystem:
    """Production-grade alerting system for comprehensive monitoring"""
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_channels: List[Callable] = []
        self.lock = threading.RLock()
        
        # Alert rules and thresholds
        self.alert_rules = {
            'memory_critical': {
                'metric': 'process_memory_mb',
                'threshold': 800.0,
                'severity': AlertSeverity.CRITICAL,
                'title': 'High Memory Usage',
                'description': 'Process memory usage exceeded critical threshold'
            },
            'memory_growth_rate': {
                'metric': 'memory_growth_rate', 
                'threshold': 25.0,
                'severity': AlertSeverity.WARNING,
                'title': 'Memory Growth Rate High',
                'description': 'Memory growing too fast, possible leak'
            },
            'cpu_critical': {
                'metric': 'cpu_usage',
                'threshold': 90.0,
                'severity': AlertSeverity.CRITICAL,
                'title': 'High CPU Usage',
                'description': 'CPU usage exceeded critical threshold'
            },
            'api_latency_critical': {
                'metric': 'api_response_time',
                'threshold': 10000.0,
                'severity': AlertSeverity.WARNING,
                'title': 'High API Latency',
                'description': 'API response time too slow'
            },
            'error_rate_high': {
                'metric': 'error_rate',
                'threshold': 15.0,
                'severity': AlertSeverity.CRITICAL,
                'title': 'High Error Rate',
                'description': 'Error rate exceeded acceptable threshold'
            },
            'websocket_connections_high': {
                'metric': 'active_websocket_connections',
                'threshold': 200,
                'severity': AlertSeverity.WARNING,
                'title': 'High WebSocket Connections',
                'description': 'Too many concurrent WebSocket connections'
            },
            'openai_api_failures': {
                'metric': 'openai_failure_rate',
                'threshold': 5.0,
                'severity': AlertSeverity.CRITICAL,
                'title': 'OpenAI API Failures',
                'description': 'High failure rate for OpenAI API calls'
            }
        }
        
        logger.info("🚨 Alerting system initialized")
    
    def check_metric(self, metric_name: str, value: float, source: str = "system"):
        """Check metric against alert rules and generate alerts if needed"""
        with self.lock:
            for rule_id, rule in self.alert_rules.items():
                if rule['metric'] == metric_name:
                    if value >= rule['threshold']:
                        alert_id = f"{rule_id}_{source}_{int(time.time())}"
                        
                        # Check if similar alert is already active
                        existing_alert = self._find_active_alert(rule['metric'], source)
                        if existing_alert:
                            continue  # Don't duplicate alerts
                        
                        alert = Alert(
                            id=alert_id,
                            title=rule['title'],
                            description=f"{rule['description']}: {value} >= {rule['threshold']}",
                            severity=rule['severity'],
                            source=source,
                            metric=metric_name,
                            value=value,
                            threshold=rule['threshold'],
                            tags={'rule_id': rule_id}
                        )
                        
                        self._trigger_alert(alert)
                    else:
                        # Check if we should resolve existing alert
                        existing_alert = self._find_active_alert(rule['metric'], source)
                        if existing_alert:
                            self._resolve_alert(existing_alert.id)
    
    def _find_active_alert(self, metric: str, source: str) -> Optional[Alert]:
        """Find active alert for metric and source"""
        for alert in self.active_alerts.values():
            if alert.metric == metric and alert.source == source and alert.status == AlertStatus.ACTIVE:
                return alert
        return None
    
    def _trigger_alert(self, alert: Alert):
        """Trigger new alert"""
        self.active_alerts[alert.id] = alert
        self.alert_history.append(alert)
        
        # Keep history bounded
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        logger.warning(f"🚨 ALERT TRIGGERED: {alert.title} - {alert.description}")
        
        # Send notifications
        self._send_notifications(alert)
    
    def _resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            del self.active_alerts[alert_id]
            
            logger.info(f"✅ ALERT RESOLVED: {alert.title}")
    
    def _send_notifications(self, alert: Alert):
        """Send alert notifications through configured channels"""
        for channel in self.notification_channels:
            try:
                channel(alert)
            except Exception as e:
                logger.error(f"❌ Failed to send alert notification: {e}")
    
    def add_notification_channel(self, channel: Callable):
        """Add notification channel (function that takes Alert)"""
        self.notification_channels.append(channel)
        logger.info(f"📢 Added notification channel: {channel.__name__}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        with self.lock:
            return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get recent alert history"""
        with self.lock:
            return self.alert_history[-limit:]
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].status = AlertStatus.ACKNOWLEDGED
            logger.info(f"✅ ALERT ACKNOWLEDGED: {alert_id}")
    
    def get_alert_summary(self) -> Dict:
        """Get alert summary for dashboard"""
        with self.lock:
            active_count = len(self.active_alerts)
            severity_counts = {}
            for alert in self.active_alerts.values():
                severity = alert.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            return {
                'active_alerts': active_count,
                'severity_breakdown': severity_counts,
                'total_alerts_today': len([a for a in self.alert_history if time.time() - a.timestamp < 86400]),
                'status': 'healthy' if active_count == 0 else ('critical' if severity_counts.get('critical', 0) > 0 else 'warning')
            }

# Global alerting system instance
_alerting_system = None

def get_alerting_system() -> AlertingSystem:
    """Get global alerting system instance"""
    global _alerting_system
    if _alerting_system is None:
        _alerting_system = AlertingSystem()
    return _alerting_system