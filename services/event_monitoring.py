"""
Production Event Monitoring for CROWN+ Event Sequencing

Provides comprehensive monitoring, logging, and metrics tracking for:
- Event execution timing
- Event success/failure rates
- Dashboard refresh monitoring
- Anomaly detection
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field

from models import db
from models.event_ledger import EventLedger, EventType, EventStatus

logger = logging.getLogger(__name__)


@dataclass
class EventMetrics:
    """Metrics for a specific event type"""
    event_type: str
    total_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    last_execution: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100
    
    @property
    def failure_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return (self.failure_count / self.total_count) * 100


class EventMonitoringService:
    """
    Production monitoring service for CROWN+ event sequencing.
    
    Tracks:
    - Event execution metrics
    - Dashboard refresh monitoring
    - Performance anomalies
    - Error patterns
    """
    
    def __init__(self):
        self.metrics_cache: Dict[str, EventMetrics] = {}
        self.anomaly_threshold_ms = 10000  # Alert if event takes > 10s
        self.refresh_cache_interval = 300  # Refresh cache every 5 minutes
        self.last_cache_refresh = time.time()
    
    def log_dashboard_refresh(self, session_id: str, success: bool, duration_ms: float, metadata: Dict[str, Any] = None):
        """
        Log dashboard refresh event with detailed metrics.
        
        Args:
            session_id: External session identifier
            success: Whether refresh completed successfully
            duration_ms: Time taken to complete refresh
            metadata: Additional context (user count, data size, etc.)
        """
        log_data = {
            'event_type': 'dashboard_refresh',
            'session_id': session_id,
            'success': success,
            'duration_ms': round(duration_ms, 2),
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        if success:
            logger.info(
                f"📊 Dashboard refresh completed for session {session_id} in {duration_ms:.2f}ms",
                extra=log_data
            )
        else:
            logger.error(
                f"❌ Dashboard refresh failed for session {session_id} after {duration_ms:.2f}ms",
                extra=log_data
            )
        
        # Check for performance anomalies
        if duration_ms > self.anomaly_threshold_ms:
            logger.warning(
                f"⚠️ Dashboard refresh anomaly detected: {duration_ms:.2f}ms exceeds threshold {self.anomaly_threshold_ms}ms",
                extra=log_data
            )
    
    def get_event_metrics(self, event_type: str = None, hours: int = 24) -> Dict[str, EventMetrics]:
        """
        Get aggregated metrics for event types.
        
        Args:
            event_type: Specific event type to query (None for all)
            hours: Look back window in hours
            
        Returns:
            Dictionary of event type to metrics
        """
        # Check if cache needs refresh
        if time.time() - self.last_cache_refresh > self.refresh_cache_interval:
            self._refresh_metrics_cache(hours)
        
        if event_type:
            return {event_type: self.metrics_cache.get(event_type, EventMetrics(event_type=event_type))}
        
        return self.metrics_cache.copy()
    
    def _refresh_metrics_cache(self, hours: int = 24):
        """Refresh metrics cache from database"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Query all events within window
        events = EventLedger.query.filter(
            EventLedger.created_at >= cutoff_time
        ).all()
        
        # Aggregate metrics by event type
        metrics_by_type = defaultdict(lambda: {
            'total': 0,
            'success': 0,
            'failure': 0,
            'durations': []
        })
        
        for event in events:
            event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
            metrics = metrics_by_type[event_type_str]
            
            metrics['total'] += 1
            
            if event.status == EventStatus.COMPLETED:
                metrics['success'] += 1
            elif event.status == EventStatus.FAILED:
                metrics['failure'] += 1
            
            # Calculate duration if available
            if event.started_at and event.completed_at:
                duration_ms = (event.completed_at - event.started_at).total_seconds() * 1000
                metrics['durations'].append(duration_ms)
        
        # Convert to EventMetrics objects
        self.metrics_cache.clear()
        for event_type_str, data in metrics_by_type.items():
            durations = data['durations']
            
            self.metrics_cache[event_type_str] = EventMetrics(
                event_type=event_type_str,
                total_count=data['total'],
                success_count=data['success'],
                failure_count=data['failure'],
                avg_duration_ms=sum(durations) / len(durations) if durations else 0,
                min_duration_ms=min(durations) if durations else 0,
                max_duration_ms=max(durations) if durations else 0,
                last_execution=datetime.utcnow()
            )
        
        self.last_cache_refresh = time.time()
        logger.info(f"📊 Metrics cache refreshed: {len(self.metrics_cache)} event types tracked")
    
    def get_dashboard_refresh_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get specific metrics for dashboard_refresh events.
        
        Args:
            hours: Look back window in hours
            
        Returns:
            Detailed dashboard refresh metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Query dashboard_refresh events
        refresh_events = EventLedger.query.filter(
            EventLedger.event_type == EventType.DASHBOARD_REFRESH,
            EventLedger.created_at >= cutoff_time
        ).all()
        
        if not refresh_events:
            return {
                'total_refreshes': 0,
                'success_rate': 0.0,
                'avg_duration_ms': 0.0,
                'anomalies': 0
            }
        
        total = len(refresh_events)
        successful = sum(1 for e in refresh_events if e.status == EventStatus.COMPLETED)
        failed = sum(1 for e in refresh_events if e.status == EventStatus.FAILED)
        
        durations = []
        anomalies = 0
        
        for event in refresh_events:
            if event.started_at and event.completed_at:
                duration_ms = (event.completed_at - event.started_at).total_seconds() * 1000
                durations.append(duration_ms)
                
                if duration_ms > self.anomaly_threshold_ms:
                    anomalies += 1
        
        return {
            'total_refreshes': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0.0,
            'failure_rate': (failed / total * 100) if total > 0 else 0.0,
            'avg_duration_ms': sum(durations) / len(durations) if durations else 0.0,
            'min_duration_ms': min(durations) if durations else 0.0,
            'max_duration_ms': max(durations) if durations else 0.0,
            'anomalies': anomalies,
            'anomaly_rate': (anomalies / total * 100) if total > 0 else 0.0,
            'time_window_hours': hours
        }
    
    def get_pipeline_health_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive health report for entire CROWN+ pipeline.
        
        Returns:
            Health report with metrics for all stages
        """
        metrics = self.get_event_metrics(hours=24)
        dashboard_metrics = self.get_dashboard_refresh_metrics(hours=24)
        
        # Calculate overall pipeline health
        total_pipelines = 0
        successful_pipelines = 0
        
        # A pipeline is successful if it has dashboard_refresh completed
        if EventType.DASHBOARD_REFRESH.value in metrics:
            refresh_metrics = metrics[EventType.DASHBOARD_REFRESH.value]
            total_pipelines = refresh_metrics.total_count
            successful_pipelines = refresh_metrics.success_count
        
        health_score = (successful_pipelines / total_pipelines * 100) if total_pipelines > 0 else 0.0
        
        return {
            'health_score': round(health_score, 2),
            'total_pipelines_24h': total_pipelines,
            'successful_pipelines': successful_pipelines,
            'failed_pipelines': total_pipelines - successful_pipelines,
            'dashboard_refresh_metrics': dashboard_metrics,
            'event_metrics': {k: {
                'total': v.total_count,
                'success_rate': round(v.success_rate, 2),
                'avg_duration_ms': round(v.avg_duration_ms, 2)
            } for k, v in metrics.items()},
            'generated_at': datetime.utcnow().isoformat()
        }


# Global monitoring service instance
event_monitoring_service = EventMonitoringService()


def log_dashboard_refresh_event(session_id: str, success: bool, duration_ms: float, **kwargs):
    """
    Convenience function to log dashboard refresh events.
    
    Usage:
        log_dashboard_refresh_event('session-123', True, 250.5, user_count=5)
    """
    event_monitoring_service.log_dashboard_refresh(session_id, success, duration_ms, metadata=kwargs)


def get_dashboard_metrics(hours: int = 24) -> Dict[str, Any]:
    """
    Convenience function to get dashboard refresh metrics.
    
    Usage:
        metrics = get_dashboard_metrics(hours=12)
    """
    return event_monitoring_service.get_dashboard_refresh_metrics(hours=hours)


def get_pipeline_health() -> Dict[str, Any]:
    """
    Convenience function to get overall pipeline health.
    
    Usage:
        health = get_pipeline_health()
    """
    return event_monitoring_service.get_pipeline_health_report()
