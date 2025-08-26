"""
Production monitoring and alerting system for Mina
"""
import os
import time
import psutil
import logging
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ProductionMonitor:
    """Production monitoring system for health checks and alerting."""
    
    def __init__(self):
        self.metrics_history = []
        self.alert_thresholds = {
            'cpu_percent': 85.0,
            'memory_percent': 90.0,
            'disk_percent': 95.0,
            'response_time_ms': 5000,
            'error_rate_percent': 5.0
        }
        
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'timestamp': time.time(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'memory_available_mb': memory.available / 1024 / 1024,
                'disk_free_gb': disk.free / 1024 / 1024 / 1024
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def check_application_health(self) -> Dict[str, Any]:
        """Check application health endpoints."""
        try:
            # Check main health endpoint
            start_time = time.time()
            response = requests.get('http://localhost:5000/api/health', timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            health_status = {
                'health_endpoint_status': response.status_code,
                'response_time_ms': response_time,
                'timestamp': time.time()
            }
            
            if response.status_code == 200:
                health_data = response.json()
                health_status.update(health_data)
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error checking application health: {e}")
            return {
                'health_endpoint_status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }
    
    def check_alerts(self, metrics: Dict[str, Any]) -> list:
        """Check if any metrics exceed alert thresholds."""
        alerts = []
        
        for metric, threshold in self.alert_thresholds.items():
            if metric in metrics and metrics[metric] > threshold:
                alerts.append({
                    'metric': metric,
                    'value': metrics[metric],
                    'threshold': threshold,
                    'severity': 'critical' if metrics[metric] > threshold * 1.1 else 'warning',
                    'timestamp': time.time()
                })
        
        return alerts
    
    def send_alert(self, alert: Dict[str, Any]):
        """Send alert notification (implement webhook/email here)."""
        webhook_url = os.getenv('ALERT_WEBHOOK_URL')
        if webhook_url:
            try:
                requests.post(webhook_url, json=alert, timeout=5)
                logger.info(f"Alert sent: {alert}")
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")
        else:
            logger.warning(f"Alert triggered but no webhook configured: {alert}")
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle."""
        # Collect metrics
        system_metrics = self.collect_system_metrics()
        app_health = self.check_application_health()
        
        combined_metrics = {**system_metrics, **app_health}
        
        # Check for alerts
        alerts = self.check_alerts(combined_metrics)
        
        # Send alerts if any
        for alert in alerts:
            self.send_alert(alert)
        
        # Store metrics
        self.metrics_history.append(combined_metrics)
        
        # Keep only last 1000 metrics (about 8 hours if run every 30s)
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        return combined_metrics, alerts

if __name__ == "__main__":
    # Run monitoring in standalone mode
    monitor = ProductionMonitor()
    
    while True:
        try:
            metrics, alerts = monitor.run_monitoring_cycle()
            print(f"Monitoring cycle completed: {len(alerts)} alerts")
            time.sleep(30)  # Run every 30 seconds
        except KeyboardInterrupt:
            print("Monitoring stopped")
            break
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            time.sleep(60)  # Wait longer on error