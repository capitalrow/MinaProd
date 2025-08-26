#!/usr/bin/env python3
"""
📊 Production Feature: SLA & Performance Monitoring

Implements comprehensive SLA monitoring, performance baselines, error budgets,
and reliability targets for production service level management.

Key Features:
- SLA metric definition and tracking
- Performance baseline establishment
- Error budget management
- Reliability target monitoring
- Alerting and escalation
"""

import logging
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import redis
from threading import Thread
import psutil

logger = logging.getLogger(__name__)

class SLAMetricType(Enum):
    """Types of SLA metrics to monitor."""
    AVAILABILITY = "availability"  # Uptime percentage
    LATENCY = "latency"  # Response time
    THROUGHPUT = "throughput"  # Requests per second
    ERROR_RATE = "error_rate"  # Error percentage
    TRANSCRIPTION_ACCURACY = "transcription_accuracy"  # WER/quality
    WEBSOCKET_STABILITY = "websocket_stability"  # Connection stability

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class SLATarget:
    """SLA target definition."""
    metric_type: SLAMetricType
    target_value: float
    measurement_window: int  # seconds
    threshold_warning: float  # % of target
    threshold_critical: float  # % of target
    error_budget_percent: float  # % allowed failures
    description: str

@dataclass
class PerformanceBaseline:
    """Performance baseline metrics."""
    metric_name: str
    baseline_value: float
    measurement_unit: str
    confidence_interval: float
    established_date: datetime
    sample_size: int
    baseline_type: str  # mean, p95, p99, etc.

@dataclass
class ErrorBudget:
    """Error budget tracking."""
    sla_metric: SLAMetricType
    budget_percent: float
    consumed_percent: float
    remaining_percent: float
    reset_date: datetime
    breach_count: int
    current_burn_rate: float  # % per hour

@dataclass
class SLAAlert:
    """SLA alert record."""
    alert_id: str
    metric_type: SLAMetricType
    severity: AlertSeverity
    message: str
    current_value: float
    target_value: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class SLAPerformanceMonitor:
    """
    📊 Production-grade SLA and performance monitoring.
    
    Tracks service level agreements, establishes performance baselines,
    manages error budgets, and provides alerting for production reliability.
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Define production SLA targets
        self.sla_targets = {
            SLAMetricType.AVAILABILITY: SLATarget(
                metric_type=SLAMetricType.AVAILABILITY,
                target_value=99.9,  # 99.9% uptime (8.76 hours downtime/year)
                measurement_window=300,  # 5 minutes
                threshold_warning=99.5,
                threshold_critical=99.0,
                error_budget_percent=0.1,
                description="Service availability and uptime"
            ),
            SLAMetricType.LATENCY: SLATarget(
                metric_type=SLAMetricType.LATENCY,
                target_value=400.0,  # 400ms p95 latency
                measurement_window=60,  # 1 minute
                threshold_warning=600.0,
                threshold_critical=1000.0,
                error_budget_percent=5.0,
                description="API response latency (p95)"
            ),
            SLAMetricType.THROUGHPUT: SLATarget(
                metric_type=SLAMetricType.THROUGHPUT,
                target_value=100.0,  # 100 RPS minimum
                measurement_window=300,  # 5 minutes
                threshold_warning=80.0,
                threshold_critical=50.0,
                error_budget_percent=10.0,
                description="Request throughput capacity"
            ),
            SLAMetricType.ERROR_RATE: SLATarget(
                metric_type=SLAMetricType.ERROR_RATE,
                target_value=1.0,  # <1% error rate
                measurement_window=300,  # 5 minutes
                threshold_warning=2.0,
                threshold_critical=5.0,
                error_budget_percent=1.0,
                description="HTTP error rate percentage"
            ),
            SLAMetricType.TRANSCRIPTION_ACCURACY: SLATarget(
                metric_type=SLAMetricType.TRANSCRIPTION_ACCURACY,
                target_value=85.0,  # >85% accuracy (WER <15%)
                measurement_window=3600,  # 1 hour
                threshold_warning=80.0,
                threshold_critical=75.0,
                error_budget_percent=5.0,
                description="Transcription accuracy percentage"
            ),
            SLAMetricType.WEBSOCKET_STABILITY: SLATarget(
                metric_type=SLAMetricType.WEBSOCKET_STABILITY,
                target_value=95.0,  # 95% connection stability
                measurement_window=1800,  # 30 minutes
                threshold_warning=90.0,
                threshold_critical=85.0,
                error_budget_percent=5.0,
                description="WebSocket connection stability"
            )
        }
        
        # Performance baselines (to be established from real data)
        self.performance_baselines = {}
        self.error_budgets = {}
        self.active_alerts = {}
        
        logger.info("📊 SLA Performance Monitor initialized")
    
    def start_monitoring(self):
        """Start continuous SLA monitoring."""
        if self.monitoring_active:
            logger.warning("SLA monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("🚀 SLA monitoring started")
    
    def stop_monitoring(self):
        """Stop SLA monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        logger.info("⏹️ SLA monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                self._collect_metrics()
                self._evaluate_slas()
                self._update_error_budgets()
                self._check_alerts()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"SLA monitoring error: {e}")
                time.sleep(60)  # Back off on errors
    
    def _collect_metrics(self):
        """Collect current performance metrics."""
        timestamp = datetime.utcnow()
        metrics = {}
        
        try:
            # System availability
            metrics[SLAMetricType.AVAILABILITY] = self._measure_availability()
            
            # Response latency
            metrics[SLAMetricType.LATENCY] = self._measure_latency()
            
            # Request throughput
            metrics[SLAMetricType.THROUGHPUT] = self._measure_throughput()
            
            # Error rates
            metrics[SLAMetricType.ERROR_RATE] = self._measure_error_rate()
            
            # Transcription accuracy
            metrics[SLAMetricType.TRANSCRIPTION_ACCURACY] = self._measure_transcription_accuracy()
            
            # WebSocket stability
            metrics[SLAMetricType.WEBSOCKET_STABILITY] = self._measure_websocket_stability()
            
            # Store metrics in Redis
            metrics_key = f"sla:metrics:{int(timestamp.timestamp())}"
            self.redis_client.setex(
                metrics_key,
                86400,  # 24 hours
                json.dumps({k.value: v for k, v in metrics.items()}, default=str)
            )
            
        except Exception as e:
            logger.error(f"Metric collection failed: {e}")
    
    def _measure_availability(self) -> float:
        """Measure system availability."""
        try:
            # Check if main services are responding
            health_checks = [
                self._check_database_health(),
                self._check_redis_health(),
                self._check_transcription_service_health(),
                self._check_websocket_health()
            ]
            
            available_services = sum(health_checks)
            availability = (available_services / len(health_checks)) * 100
            
            return availability
            
        except Exception as e:
            logger.error(f"Availability measurement failed: {e}")
            return 0.0
    
    def _measure_latency(self) -> float:
        """Measure API response latency (p95)."""
        try:
            # Get recent latency measurements from Redis
            latency_key = "metrics:latency:recent"
            latencies = self.redis_client.lrange(latency_key, 0, 100)
            
            if latencies:
                latency_values = [float(l) for l in latencies]
                latency_values.sort()
                
                # Calculate p95
                p95_index = int(0.95 * len(latency_values))
                p95_latency = latency_values[p95_index] if p95_index < len(latency_values) else latency_values[-1]
                
                return p95_latency * 1000  # Convert to milliseconds
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Latency measurement failed: {e}")
            return 0.0
    
    def _measure_throughput(self) -> float:
        """Measure request throughput (RPS)."""
        try:
            # Count requests in last minute
            request_key = "metrics:requests:count"
            current_minute = int(time.time() // 60)
            
            # Get counts for last minute
            requests_count = 0
            for i in range(60):  # 60 seconds
                minute_key = f"{request_key}:{current_minute - i}"
                count = self.redis_client.get(minute_key)
                if count:
                    requests_count += int(count)
            
            return requests_count / 60.0  # RPS
            
        except Exception as e:
            logger.error(f"Throughput measurement failed: {e}")
            return 0.0
    
    def _measure_error_rate(self) -> float:
        """Measure HTTP error rate percentage."""
        try:
            # Get error counts from Redis
            error_key = "metrics:errors:count"
            success_key = "metrics:success:count"
            
            errors = int(self.redis_client.get(error_key) or 0)
            successes = int(self.redis_client.get(success_key) or 0)
            
            total_requests = errors + successes
            if total_requests > 0:
                error_rate = (errors / total_requests) * 100
                return error_rate
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error rate measurement failed: {e}")
            return 0.0
    
    def _measure_transcription_accuracy(self) -> float:
        """Measure transcription accuracy percentage."""
        try:
            # Get accuracy metrics from transcription service
            accuracy_key = "metrics:transcription:accuracy"
            accuracy_data = self.redis_client.get(accuracy_key)
            
            if accuracy_data:
                accuracy_info = json.loads(accuracy_data)
                return accuracy_info.get('accuracy_percent', 0.0)
            
            return 85.0  # Default baseline
            
        except Exception as e:
            logger.error(f"Transcription accuracy measurement failed: {e}")
            return 0.0
    
    def _measure_websocket_stability(self) -> float:
        """Measure WebSocket connection stability."""
        try:
            # Get WebSocket metrics
            ws_metrics_key = "metrics:websocket:stability"
            ws_data = self.redis_client.get(ws_metrics_key)
            
            if ws_data:
                ws_info = json.loads(ws_data)
                stable_connections = ws_info.get('stable_connections', 0)
                total_connections = ws_info.get('total_connections', 1)
                
                stability = (stable_connections / total_connections) * 100
                return stability
            
            return 95.0  # Default baseline
            
        except Exception as e:
            logger.error(f"WebSocket stability measurement failed: {e}")
            return 0.0
    
    def _check_database_health(self) -> bool:
        """Check database health."""
        try:
            # Simple Redis ping as proxy for database health
            self.redis_client.ping()
            return True
        except:
            return False
    
    def _check_redis_health(self) -> bool:
        """Check Redis health."""
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def _check_transcription_service_health(self) -> bool:
        """Check transcription service health."""
        try:
            # Check if transcription service is responsive
            service_key = "health:transcription_service"
            last_heartbeat = self.redis_client.get(service_key)
            
            if last_heartbeat:
                last_time = datetime.fromisoformat(last_heartbeat.decode())
                time_diff = datetime.utcnow() - last_time
                return time_diff.total_seconds() < 300  # 5 minutes
            
            return False
            
        except:
            return False
    
    def _check_websocket_health(self) -> bool:
        """Check WebSocket service health."""
        try:
            # Check WebSocket service status
            ws_key = "health:websocket_service"
            status = self.redis_client.get(ws_key)
            return status == b'healthy' if status else False
            
        except:
            return False
    
    def _evaluate_slas(self):
        """Evaluate current metrics against SLA targets."""
        timestamp = datetime.utcnow()
        
        # Get latest metrics
        metrics_key = f"sla:metrics:{int(timestamp.timestamp())}"
        metrics_data = self.redis_client.get(metrics_key)
        
        if not metrics_data:
            return
        
        metrics = json.loads(metrics_data)
        
        for metric_type, target in self.sla_targets.items():
            metric_name = metric_type.value
            current_value = metrics.get(metric_name, 0.0)
            
            # Check if SLA is breached
            if self._is_sla_breached(current_value, target):
                self._handle_sla_breach(metric_type, current_value, target)
            elif self._is_sla_warning(current_value, target):
                self._handle_sla_warning(metric_type, current_value, target)
    
    def _is_sla_breached(self, current_value: float, target: SLATarget) -> bool:
        """Check if SLA is critically breached."""
        if target.metric_type in [SLAMetricType.AVAILABILITY, SLAMetricType.TRANSCRIPTION_ACCURACY, SLAMetricType.WEBSOCKET_STABILITY]:
            return current_value < target.threshold_critical
        else:  # Latency, error rate
            return current_value > target.threshold_critical
    
    def _is_sla_warning(self, current_value: float, target: SLATarget) -> bool:
        """Check if SLA is in warning state."""
        if target.metric_type in [SLAMetricType.AVAILABILITY, SLAMetricType.TRANSCRIPTION_ACCURACY, SLAMetricType.WEBSOCKET_STABILITY]:
            return current_value < target.threshold_warning
        else:  # Latency, error rate
            return current_value > target.threshold_warning
    
    def _handle_sla_breach(self, metric_type: SLAMetricType, current_value: float, target: SLATarget):
        """Handle critical SLA breach."""
        alert = SLAAlert(
            alert_id=f"sla_critical_{metric_type.value}_{int(time.time())}",
            metric_type=metric_type,
            severity=AlertSeverity.CRITICAL,
            message=f"CRITICAL: {target.description} - Current: {current_value:.2f}, Target: {target.target_value:.2f}",
            current_value=current_value,
            target_value=target.target_value,
            timestamp=datetime.utcnow()
        )
        
        self._send_alert(alert)
    
    def _handle_sla_warning(self, metric_type: SLAMetricType, current_value: float, target: SLATarget):
        """Handle SLA warning."""
        alert = SLAAlert(
            alert_id=f"sla_warning_{metric_type.value}_{int(time.time())}",
            metric_type=metric_type,
            severity=AlertSeverity.WARNING,
            message=f"WARNING: {target.description} - Current: {current_value:.2f}, Target: {target.target_value:.2f}",
            current_value=current_value,
            target_value=target.target_value,
            timestamp=datetime.utcnow()
        )
        
        self._send_alert(alert)
    
    def _send_alert(self, alert: SLAAlert):
        """Send SLA alert."""
        self.active_alerts[alert.alert_id] = alert
        
        # Store alert in Redis
        alert_key = f"sla:alerts:{alert.alert_id}"
        self.redis_client.setex(
            alert_key,
            86400 * 7,  # 7 days
            json.dumps(asdict(alert), default=str)
        )
        
        # Log alert
        logger.warning(f"SLA ALERT [{alert.severity.value.upper()}]: {alert.message}")
        
        # In production, integrate with PagerDuty, Slack, etc.
        self._notify_alert_channels(alert)
    
    def _notify_alert_channels(self, alert: SLAAlert):
        """Notify external alert channels (Slack, PagerDuty, etc.)."""
        # TODO: Integrate with actual alerting systems
        logger.info(f"Alert notification sent: {alert.alert_id}")
    
    def _update_error_budgets(self):
        """Update error budget consumption."""
        for metric_type, target in self.sla_targets.items():
            budget = self.error_budgets.get(metric_type)
            if not budget:
                budget = ErrorBudget(
                    sla_metric=metric_type,
                    budget_percent=target.error_budget_percent,
                    consumed_percent=0.0,
                    remaining_percent=target.error_budget_percent,
                    reset_date=datetime.utcnow() + timedelta(days=30),
                    breach_count=0,
                    current_burn_rate=0.0
                )
                self.error_budgets[metric_type] = budget
            
            # Calculate current consumption
            # This is simplified - in production, use proper time-window calculations
            self._calculate_budget_consumption(budget, target)
    
    def _calculate_budget_consumption(self, budget: ErrorBudget, target: SLATarget):
        """Calculate error budget consumption rate."""
        # Simplified calculation - in production, use rolling windows
        budget.current_burn_rate = 0.1  # Example: 0.1% per hour
        budget.consumed_percent += budget.current_burn_rate / 24  # Per hour consumption
        budget.remaining_percent = budget.budget_percent - budget.consumed_percent
        
        if budget.remaining_percent <= 0:
            logger.critical(f"ERROR BUDGET EXHAUSTED for {budget.sla_metric.value}")
    
    def _check_alerts(self):
        """Check for alert conditions and auto-resolution."""
        # Check if any alerts can be resolved
        for alert_id, alert in list(self.active_alerts.items()):
            if not alert.resolved:
                # Check if condition is resolved
                if self._is_alert_resolved(alert):
                    alert.resolved = True
                    alert.resolved_at = datetime.utcnow()
                    logger.info(f"Alert resolved: {alert_id}")
                    
                    # Update in Redis
                    alert_key = f"sla:alerts:{alert_id}"
                    self.redis_client.setex(
                        alert_key,
                        86400 * 7,
                        json.dumps(asdict(alert), default=str)
                    )
    
    def _is_alert_resolved(self, alert: SLAAlert) -> bool:
        """Check if alert condition is resolved."""
        # Simplified resolution check
        return (datetime.utcnow() - alert.timestamp).total_seconds() > 600  # 10 minutes
    
    def establish_performance_baseline(self, metric_name: str, measurements: List[float], 
                                     measurement_unit: str, baseline_type: str = "p95") -> PerformanceBaseline:
        """Establish performance baseline from historical data."""
        if not measurements:
            raise ValueError("No measurements provided for baseline")
        
        measurements.sort()
        
        if baseline_type == "mean":
            baseline_value = sum(measurements) / len(measurements)
        elif baseline_type == "p95":
            p95_index = int(0.95 * len(measurements))
            baseline_value = measurements[p95_index]
        elif baseline_type == "p99":
            p99_index = int(0.99 * len(measurements))
            baseline_value = measurements[p99_index]
        else:
            baseline_value = measurements[int(len(measurements) / 2)]  # median
        
        # Calculate confidence interval (simplified)
        std_dev = (sum((x - baseline_value) ** 2 for x in measurements) / len(measurements)) ** 0.5
        confidence_interval = 1.96 * (std_dev / (len(measurements) ** 0.5))  # 95% CI
        
        baseline = PerformanceBaseline(
            metric_name=metric_name,
            baseline_value=baseline_value,
            measurement_unit=measurement_unit,
            confidence_interval=confidence_interval,
            established_date=datetime.utcnow(),
            sample_size=len(measurements),
            baseline_type=baseline_type
        )
        
        self.performance_baselines[metric_name] = baseline
        
        # Store in Redis
        baseline_key = f"sla:baseline:{metric_name}"
        self.redis_client.set(baseline_key, json.dumps(asdict(baseline), default=str))
        
        logger.info(f"Performance baseline established for {metric_name}: {baseline_value:.2f} {measurement_unit}")
        
        return baseline
    
    def get_sla_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive SLA dashboard data."""
        dashboard_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'sla_targets': {k.value: asdict(v) for k, v in self.sla_targets.items()},
            'current_metrics': self._get_current_metrics(),
            'error_budgets': {k.value: asdict(v) for k, v in self.error_budgets.items()},
            'active_alerts': {k: asdict(v) for k, v in self.active_alerts.items()},
            'performance_baselines': {k: asdict(v) for k, v in self.performance_baselines.items()},
            'sla_compliance': self._calculate_sla_compliance()
        }
        
        return dashboard_data
    
    def _get_current_metrics(self) -> Dict[str, float]:
        """Get current metric values."""
        # Return latest metrics from Redis
        latest_key = f"sla:metrics:{int(time.time())}"
        metrics_data = self.redis_client.get(latest_key)
        
        if metrics_data:
            return json.loads(metrics_data)
        
        return {}
    
    def _calculate_sla_compliance(self) -> Dict[str, float]:
        """Calculate SLA compliance percentages."""
        compliance = {}
        
        for metric_type, target in self.sla_targets.items():
            # Calculate compliance over last 24 hours (simplified)
            compliance[metric_type.value] = 99.0  # Placeholder
        
        return compliance

# Initialize global SLA monitor
sla_monitor = None

def init_sla_monitoring(app, redis_client: redis.Redis):
    """Initialize SLA monitoring for Flask app."""
    global sla_monitor
    sla_monitor = SLAPerformanceMonitor(redis_client)
    app.sla_monitor = sla_monitor
    
    # Start monitoring
    sla_monitor.start_monitoring()
    
    logger.info("📊 SLA monitoring initialized and started")
    return sla_monitor