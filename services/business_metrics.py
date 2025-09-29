"""
📊 Business Metrics Tracking
Tracks user engagement, retention, and business KPIs for 100% monitoring coverage.
"""
import logging
import time
import threading
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class UserSession:
    """User session tracking"""
    user_id: str
    session_id: str
    start_time: float
    last_activity: float
    page_views: int = 0
    transcription_minutes: float = 0.0
    features_used: Set[str] = field(default_factory=set)
    export_actions: int = 0
    errors_encountered: int = 0

@dataclass
class BusinessKPIs:
    """Business key performance indicators"""
    daily_active_users: int = 0
    weekly_active_users: int = 0
    monthly_active_users: int = 0
    average_session_duration: float = 0.0
    transcription_volume_minutes: float = 0.0
    feature_adoption_rate: Dict[str, float] = field(default_factory=dict)
    user_retention_rate: float = 0.0
    export_conversion_rate: float = 0.0
    error_impact_rate: float = 0.0
    timestamp: float = field(default_factory=time.time)

class BusinessMetricsTracker:
    """Comprehensive business metrics tracking"""
    
    def __init__(self):
        self.active_sessions: Dict[str, UserSession] = {}
        self.completed_sessions: deque = deque(maxlen=10000)  # Keep last 10k sessions
        self.user_activity: Dict[str, List[float]] = defaultdict(list)  # user_id -> activity timestamps
        self.feature_usage: Dict[str, int] = defaultdict(int)
        self.daily_stats: Dict[str, Dict] = {}  # date -> stats
        self.lock = threading.RLock()
        
        # Business thresholds and targets
        self.targets = {
            'daily_active_users': 50,
            'average_session_duration': 600,  # 10 minutes
            'transcription_volume_daily': 1000,  # 1000 minutes
            'feature_adoption_rate': 0.7,  # 70%
            'user_retention_rate': 0.85,  # 85%
            'export_conversion_rate': 0.3,  # 30%
            'error_impact_rate': 0.05  # 5%
        }
        
        logger.info("📊 Business metrics tracker initialized")
    
    def start_user_session(self, user_id: str, session_id: str):
        """Start tracking user session"""
        
        with self.lock:
            session = UserSession(
                user_id=user_id,
                session_id=session_id,
                start_time=time.time(),
                last_activity=time.time()
            )
            self.active_sessions[session_id] = session
            
            # Track user activity
            self.user_activity[user_id].append(time.time())
            
            logger.debug(f"📊 Started session tracking: {session_id} for user {user_id}")
    
    def end_user_session(self, session_id: str):
        """End user session tracking"""
        with self.lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.last_activity = time.time()
                
                # Move to completed sessions
                self.completed_sessions.append(session)
                del self.active_sessions[session_id]
                
                duration = session.last_activity - session.start_time
                logger.info(f"📊 Ended session: {session_id} (duration: {duration:.1f}s, "
                           f"transcription: {session.transcription_minutes:.1f}min, "
                           f"features: {len(session.features_used)})")
    
    def record_page_view(self, session_id: str, page: str):
        """Record page view"""
        with self.lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.page_views += 1
                session.last_activity = time.time()
    
    def record_transcription_time(self, session_id: str, minutes: float):
        """Record transcription time"""
        with self.lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.transcription_minutes += minutes
                session.last_activity = time.time()
    
    def record_feature_usage(self, session_id: str, feature: str):
        """Record feature usage"""
        with self.lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.features_used.add(feature)
                session.last_activity = time.time()
            
            # Global feature tracking
            self.feature_usage[feature] += 1
    
    def record_export_action(self, session_id: str, export_type: str):
        """Record export action"""
        with self.lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.export_actions += 1
                session.last_activity = time.time()
            
            self.record_feature_usage(session_id, f"export_{export_type}")
    
    def record_error(self, session_id: str, error_type: str):
        """Record user-facing error"""
        with self.lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.errors_encountered += 1
                session.last_activity = time.time()
    
    def calculate_kpis(self) -> BusinessKPIs:
        """Calculate current business KPIs"""
        with self.lock:
            current_time = time.time()
            
            # Calculate DAU, WAU, MAU
            day_ago = current_time - 86400
            week_ago = current_time - 604800
            month_ago = current_time - 2592000
            
            dau = len(set(
                session.user_id for session in self.active_sessions.values()
                if session.start_time >= day_ago
            ) | set(
                session.user_id for session in self.completed_sessions
                if session.start_time >= day_ago
            ))
            
            wau = len(set(
                user_id for user_id, timestamps in self.user_activity.items()
                if any(t >= week_ago for t in timestamps)
            ))
            
            mau = len(set(
                user_id for user_id, timestamps in self.user_activity.items()
                if any(t >= month_ago for t in timestamps)
            ))
            
            # Calculate average session duration
            recent_sessions = [s for s in self.completed_sessions if s.start_time >= day_ago]
            avg_duration = 0.0
            if recent_sessions:
                total_duration = sum(s.last_activity - s.start_time for s in recent_sessions)
                avg_duration = total_duration / len(recent_sessions)
            
            # Calculate transcription volume
            transcription_volume = sum(s.transcription_minutes for s in recent_sessions)
            transcription_volume += sum(s.transcription_minutes for s in self.active_sessions.values())
            
            # Calculate feature adoption rates
            total_sessions = len(recent_sessions) + len(self.active_sessions)
            feature_adoption = {}
            if total_sessions > 0:
                for feature, count in self.feature_usage.items():
                    feature_adoption[feature] = count / total_sessions
            
            # Calculate retention rate (simplified: users who came back in last week)
            retention_rate = 0.0
            if wau > 0:
                returning_users = sum(1 for timestamps in self.user_activity.values() 
                                    if len([t for t in timestamps if t >= week_ago]) > 1)
                retention_rate = returning_users / wau
            
            # Calculate export conversion rate
            export_sessions = sum(1 for s in recent_sessions if s.export_actions > 0)
            export_sessions += sum(1 for s in self.active_sessions.values() if s.export_actions > 0)
            export_conversion = export_sessions / total_sessions if total_sessions > 0 else 0.0
            
            # Calculate error impact rate
            error_sessions = sum(1 for s in recent_sessions if s.errors_encountered > 0)
            error_sessions += sum(1 for s in self.active_sessions.values() if s.errors_encountered > 0)
            error_impact = error_sessions / total_sessions if total_sessions > 0 else 0.0
            
            return BusinessKPIs(
                daily_active_users=dau,
                weekly_active_users=wau,
                monthly_active_users=mau,
                average_session_duration=avg_duration,
                transcription_volume_minutes=transcription_volume,
                feature_adoption_rate=feature_adoption,
                user_retention_rate=retention_rate,
                export_conversion_rate=export_conversion,
                error_impact_rate=error_impact
            )
    
    def get_performance_vs_targets(self) -> Dict[str, Dict]:
        """Compare current performance against targets"""
        kpis = self.calculate_kpis()
        
        performance = {}
        performance['daily_active_users'] = {
            'current': kpis.daily_active_users,
            'target': self.targets['daily_active_users'],
            'status': 'success' if kpis.daily_active_users >= self.targets['daily_active_users'] else 'warning'
        }
        
        performance['average_session_duration'] = {
            'current': kpis.average_session_duration,
            'target': self.targets['average_session_duration'],
            'status': 'success' if kpis.average_session_duration >= self.targets['average_session_duration'] else 'warning'
        }
        
        performance['transcription_volume'] = {
            'current': kpis.transcription_volume_minutes,
            'target': self.targets['transcription_volume_daily'],
            'status': 'success' if kpis.transcription_volume_minutes >= self.targets['transcription_volume_daily'] else 'warning'
        }
        
        performance['user_retention_rate'] = {
            'current': kpis.user_retention_rate,
            'target': self.targets['user_retention_rate'],
            'status': 'success' if kpis.user_retention_rate >= self.targets['user_retention_rate'] else 'warning'
        }
        
        performance['export_conversion_rate'] = {
            'current': kpis.export_conversion_rate,
            'target': self.targets['export_conversion_rate'],
            'status': 'success' if kpis.export_conversion_rate >= self.targets['export_conversion_rate'] else 'warning'
        }
        
        performance['error_impact_rate'] = {
            'current': kpis.error_impact_rate,
            'target': self.targets['error_impact_rate'],
            'status': 'success' if kpis.error_impact_rate <= self.targets['error_impact_rate'] else 'warning'
        }
        
        return performance
    
    def get_summary(self) -> Dict:
        """Get business metrics summary for dashboard"""
        kpis = self.calculate_kpis()
        performance = self.get_performance_vs_targets()
        
        # Calculate overall business health
        success_count = sum(1 for metric in performance.values() if metric['status'] == 'success')
        health_score = (success_count / len(performance)) * 100
        
        status = 'healthy' if health_score >= 80 else ('warning' if health_score >= 60 else 'critical')
        
        return {
            'status': status,
            'health_score': health_score,
            'daily_active_users': kpis.daily_active_users,
            'active_sessions': len(self.active_sessions),
            'transcription_volume_today': kpis.transcription_volume_minutes,
            'top_features': sorted(self.feature_usage.items(), key=lambda x: x[1], reverse=True)[:5],
            'performance_vs_targets': performance
        }

# Global business metrics tracker
_business_metrics = None

def get_business_metrics() -> BusinessMetricsTracker:
    """Get global business metrics tracker"""
    global _business_metrics
    if _business_metrics is None:
        _business_metrics = BusinessMetricsTracker()
    return _business_metrics