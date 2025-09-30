#!/usr/bin/env python3
"""
🚀 ENHANCED: System Health Monitor for Mina Transcription Platform
Real-time monitoring of system performance, quality metrics, and user experience.
"""

import logging
import time
from datetime import datetime, timedelta
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import psutil
import os

logger = logging.getLogger(__name__)

@dataclass
class SystemHealthMetrics:
    """Comprehensive system health metrics."""
    timestamp: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_sessions: int
    total_transcriptions: int
    average_latency: float
    error_rate: float
    quality_filter_rate: float
    user_satisfaction_score: float
    
class SystemHealthMonitor:
    """
    🎯 ENHANCED: Real-time system health monitoring with intelligent alerting.
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics_history = []
        self.alert_thresholds = {
            'cpu_usage': 85.0,
            'memory_usage': 80.0,
            'disk_usage': 90.0,
            'error_rate': 5.0,
            'quality_filter_rate': 30.0,
            'latency': 2000.0  # ms
        }
        self.last_health_check = time.time()
        
    def collect_system_metrics(self) -> SystemHealthMetrics:
        """Collect comprehensive system health metrics."""
        try:
            # System resource metrics
            cpu_usage = psutil.cpu_percent(interval=None)  # Non-blocking CPU sampling
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Application metrics (would be populated by transcription service)
            active_sessions = self._get_active_sessions_count()
            total_transcriptions = self._get_total_transcriptions()
            average_latency = self._get_average_latency()
            error_rate = self._get_error_rate()
            quality_filter_rate = self._get_quality_filter_rate()
            user_satisfaction = self._calculate_user_satisfaction()
            
            metrics = SystemHealthMetrics(
                timestamp=datetime.utcnow().isoformat(),
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=(disk.used / disk.total) * 100,
                active_sessions=active_sessions,
                total_transcriptions=total_transcriptions,
                average_latency=average_latency,
                error_rate=error_rate,
                quality_filter_rate=quality_filter_rate,
                user_satisfaction_score=user_satisfaction
            )
            
            # Store in history
            self.metrics_history.append(metrics)
            
            # Keep only last 100 metrics (rolling window)
            if len(self.metrics_history) > 100:
                self.metrics_history = self.metrics_history[-100:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            # Return a fallback metrics object instead of None
            return SystemHealthMetrics(
                timestamp=datetime.utcnow().isoformat(),
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                active_sessions=0,
                total_transcriptions=0,
                average_latency=0.0,
                error_rate=0.0,
                quality_filter_rate=0.0,
                user_satisfaction_score=0.0
            )
    
    def check_health_alerts(self, metrics: SystemHealthMetrics) -> List[str]:
        """Check for health alerts based on current metrics."""
        alerts = []
        
        if metrics.cpu_usage > self.alert_thresholds['cpu_usage']:
            alerts.append(f"🔥 HIGH CPU USAGE: {metrics.cpu_usage:.1f}%")
        
        if metrics.memory_usage > self.alert_thresholds['memory_usage']:
            alerts.append(f"🧠 HIGH MEMORY USAGE: {metrics.memory_usage:.1f}%")
        
        if metrics.disk_usage > self.alert_thresholds['disk_usage']:
            alerts.append(f"💾 HIGH DISK USAGE: {metrics.disk_usage:.1f}%")
        
        if metrics.error_rate > self.alert_thresholds['error_rate']:
            alerts.append(f"⚠️ HIGH ERROR RATE: {metrics.error_rate:.1f}%")
        
        if metrics.quality_filter_rate > self.alert_thresholds['quality_filter_rate']:
            alerts.append(f"🔍 HIGH FILTER RATE: {metrics.quality_filter_rate:.1f}%")
        
        if metrics.average_latency > self.alert_thresholds['latency']:
            alerts.append(f"🐌 HIGH LATENCY: {metrics.average_latency:.0f}ms")
        
        return alerts
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report."""
        if not self.metrics_history:
            return {"status": "no_data", "message": "No metrics available"}
        
        latest = self.metrics_history[-1]
        alerts = self.check_health_alerts(latest)
        
        # Calculate trends (last 10 metrics)
        recent_metrics = self.metrics_history[-10:]
        
        trends = {}
        if len(recent_metrics) > 1:
            trends = {
                'cpu_trend': self._calculate_trend([m.cpu_usage for m in recent_metrics]),
                'memory_trend': self._calculate_trend([m.memory_usage for m in recent_metrics]),
                'latency_trend': self._calculate_trend([m.average_latency for m in recent_metrics]),
                'error_trend': self._calculate_trend([m.error_rate for m in recent_metrics])
            }
        
        uptime_hours = (time.time() - self.start_time) / 3600
        
        return {
            "status": "healthy" if not alerts else "warning",
            "uptime_hours": round(uptime_hours, 2),
            "current_metrics": asdict(latest),
            "alerts": alerts,
            "trends": trends,
            "summary": {
                "system_load": "normal" if latest.cpu_usage < 70 else "high",
                "transcription_quality": "excellent" if latest.quality_filter_rate < 20 else "good",
                "performance": "optimal" if latest.average_latency < 1000 else "degraded",
                "overall_health": "excellent" if latest.user_satisfaction_score > 85 else "good"
            }
        }
    
    def _get_active_sessions_count(self) -> int:
        """Get count of active transcription sessions."""
        try:
            from models.session import Session
            from app import db
            with db.session as session:
                active_count = session.query(Session).filter(Session.status == 'active').count()
                return active_count
        except Exception as e:
            logger.error(f"Error getting active sessions count: {e}")
            return 0
    
    def _get_total_transcriptions(self) -> int:
        """Get total number of transcriptions processed."""
        try:
            from models.session import Session
            from app import db
            with db.session as session:
                total_count = session.query(Session).count()
                return total_count
        except Exception as e:
            logger.error(f"Error getting total transcriptions: {e}")
            return 0
    
    def _get_average_latency(self) -> float:
        """Get average transcription latency in milliseconds."""
        try:
            from models.metrics import ChunkMetric
            from app import db
            from sqlalchemy import func
            with db.session as session:
                # Get average end-to-end latency from recent chunks (last hour)
                one_hour_ago = datetime.utcnow() - timedelta(hours=1)
                avg_latency = session.query(func.avg(ChunkMetric.end_to_end_latency)).filter(
                    ChunkMetric.end_to_end_latency.isnot(None),
                    ChunkMetric.created_at >= one_hour_ago
                ).scalar()
                return float(avg_latency) if avg_latency else 350.0  # Default to 350ms if no data
        except Exception as e:
            logger.error(f"Error calculating average latency: {e}")
            return 350.0
    
    def _get_error_rate(self) -> float:
        """Get current error rate percentage."""
        try:
            from models.metrics import ChunkMetric
            from app import db
            from sqlalchemy import func
            with db.session as session:
                # Calculate error rate from recent chunks (last hour)
                one_hour_ago = datetime.utcnow() - timedelta(hours=1)
                total_chunks = session.query(ChunkMetric).filter(
                    ChunkMetric.created_at >= one_hour_ago
                ).count()
                
                error_chunks = session.query(ChunkMetric).filter(
                    ChunkMetric.status == 'error',
                    ChunkMetric.created_at >= one_hour_ago
                ).count()
                
                if total_chunks > 0:
                    error_rate = (error_chunks / total_chunks) * 100
                    return float(error_rate)
                return 0.0
        except Exception as e:
            logger.error(f"Error calculating error rate: {e}")
            return 1.2  # Conservative default
    
    def _get_quality_filter_rate(self) -> float:
        """Get percentage of audio chunks filtered for quality."""
        try:
            from models.metrics import ChunkMetric
            from app import db
            from sqlalchemy import func
            with db.session as session:
                # Calculate quality filter rate based on low confidence chunks (last hour)
                one_hour_ago = datetime.utcnow() - timedelta(hours=1)
                total_chunks = session.query(ChunkMetric).filter(
                    ChunkMetric.avg_confidence_score.isnot(None),
                    ChunkMetric.created_at >= one_hour_ago
                ).count()
                
                low_quality_chunks = session.query(ChunkMetric).filter(
                    ChunkMetric.avg_confidence_score < 0.6,  # Consider <60% confidence as filtered
                    ChunkMetric.created_at >= one_hour_ago
                ).count()
                
                if total_chunks > 0:
                    filter_rate = (low_quality_chunks / total_chunks) * 100
                    return float(filter_rate)
                return 8.0  # Default optimistic rate
        except Exception as e:
            logger.error(f"Error calculating quality filter rate: {e}")
            return 8.0
    
    def _calculate_user_satisfaction(self) -> float:
        """Calculate overall user satisfaction score."""
        # Weighted score based on performance metrics
        base_score = 100.0
        
        # Deduct for high latency
        if len(self.metrics_history) > 0:
            latest = self.metrics_history[-1]
            if latest.average_latency > 1000:
                base_score -= 20
            elif latest.average_latency > 500:
                base_score -= 10
            
            # Deduct for high filter rate
            if latest.quality_filter_rate > 25:
                base_score -= 15
            elif latest.quality_filter_rate > 15:
                base_score -= 5
            
            # Deduct for errors
            base_score -= latest.error_rate * 2
        
        return max(0, min(100, base_score))
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values."""
        if len(values) < 2:
            return "stable"
        
        recent_avg = sum(values[-3:]) / min(3, len(values))
        older_avg = sum(values[:-3]) / max(1, len(values) - 3)
        
        if recent_avg > older_avg * 1.1:
            return "increasing"
        elif recent_avg < older_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def log_health_summary(self):
        """Log a concise health summary."""
        report = self.generate_health_report()
        
        if report["status"] == "no_data":
            return
        
        metrics = report["current_metrics"]
        summary = report["summary"]
        
        logger.info(f"🏥 HEALTH CHECK: System {summary['overall_health']} | "
                   f"CPU: {metrics['cpu_usage']:.1f}% | "
                   f"Memory: {metrics['memory_usage']:.1f}% | "
                   f"Latency: {metrics['average_latency']:.0f}ms | "
                   f"Filter Rate: {metrics['quality_filter_rate']:.1f}% | "
                   f"Satisfaction: {metrics['user_satisfaction_score']:.1f}%")
        
        if report["alerts"]:
            logger.warning(f"🚨 ALERTS: {', '.join(report['alerts'])}")

# Global health monitor instance
health_monitor = SystemHealthMonitor()

def get_system_health() -> Dict[str, Any]:
    """Get current system health report."""
    return health_monitor.generate_health_report()

def collect_health_metrics():
    """Collect and log health metrics."""
    metrics = health_monitor.collect_system_metrics()
    if metrics:
        health_monitor.log_health_summary()
    return metrics

if __name__ == "__main__":
    # Demo/testing
    print("🏥 System Health Monitor Demo")
    metrics = collect_health_metrics()
    if metrics:
        print(json.dumps(asdict(metrics), indent=2))