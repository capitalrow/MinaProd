#!/usr/bin/env python3
"""
Mina Live Transcription Pipeline Diagnostics & QA Suite
Comprehensive performance profiling and quality assurance testing.
"""

import asyncio
import json
import logging
import time
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import requests
import websocket
import threading

# Configure logging for QA metrics
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - QA - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class LatencyMetrics:
    """Audio processing latency measurements."""
    chunk_to_server: float = 0.0
    vad_processing: float = 0.0
    whisper_api_call: float = 0.0
    result_to_ui: float = 0.0
    total_pipeline: float = 0.0

@dataclass
class QualityMetrics:
    """Transcription quality metrics."""
    word_error_rate: float = 0.0
    dropped_chunks: int = 0
    duplicate_segments: int = 0
    interim_to_final_ratio: float = 0.0
    confidence_distribution: List[float] = None
    hallucinations: int = 0

@dataclass  
class SystemMetrics:
    """System performance metrics."""
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    active_connections: int = 0
    queue_length: int = 0
    error_rate: float = 0.0

class PipelineDiagnostics:
    """Comprehensive pipeline testing and profiling."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.ws_url = base_url.replace('http', 'ws') + '/socket.io'
        self.metrics_log = []
        self.test_session_id = None
        
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive system health check."""
        try:
            response = requests.get(f"{self.base_url}/api/stats", timeout=5)
            health_data = response.json()
            
            # Check critical services
            health_report = {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'database': health_data.get('database', {}),
                'service': health_data.get('service', {}),
                'critical_issues': []
            }
            
            # Detect critical issues
            db_data = health_data.get('database', {})
            service_data = health_data.get('service', {})
            
            if db_data.get('active_sessions', 0) > service_data.get('active_sessions', 0):
                health_report['critical_issues'].append({
                    'issue': 'SESSION_SYNC_MISMATCH',
                    'description': f"Database has {db_data.get('active_sessions')} sessions but service has {service_data.get('active_sessions')}",
                    'severity': 'HIGH'
                })
                
            if service_data.get('processing_queue_size', 0) > 10:
                health_report['critical_issues'].append({
                    'issue': 'HIGH_QUEUE_LENGTH',
                    'description': f"Processing queue has {service_data.get('processing_queue_size')} items",
                    'severity': 'MEDIUM'
                })
            
            logger.info(f"Health check completed: {len(health_report['critical_issues'])} issues found")
            return health_report
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': 'error',
                'error': str(e),
                'critical_issues': [{'issue': 'HEALTH_CHECK_FAILED', 'severity': 'CRITICAL'}]
            }

    def profile_latency(self, session_id: str, duration_seconds: int = 30) -> LatencyMetrics:
        """Profile end-to-end pipeline latency."""
        latencies = []
        start_time = time.time()
        
        # TODO: Implement WebSocket latency testing
        # This would involve:
        # 1. Send audio chunk
        # 2. Measure time to VAD result
        # 3. Measure time to Whisper response
        # 4. Measure time to UI update
        
        # For now, return mock data structure
        return LatencyMetrics(
            chunk_to_server=50.0,  # ms
            vad_processing=10.0,
            whisper_api_call=800.0,
            result_to_ui=20.0,
            total_pipeline=880.0
        )

    def measure_quality(self, reference_audio_path: str, session_id: str) -> QualityMetrics:
        """Compare transcription output against reference."""
        # TODO: Implement comprehensive quality analysis
        # This would involve:
        # 1. Load reference transcript
        # 2. Compare with live transcript
        # 3. Calculate WER, duplicates, etc.
        
        return QualityMetrics(
            word_error_rate=0.15,  # 15% WER
            dropped_chunks=2,
            duplicate_segments=0,
            interim_to_final_ratio=0.8,
            confidence_distribution=[0.6, 0.7, 0.8, 0.9, 0.95],
            hallucinations=1
        )

    def stress_test(self, concurrent_sessions: int = 5, duration_minutes: int = 5) -> Dict[str, Any]:
        """Perform stress testing with multiple concurrent sessions."""
        logger.info(f"Starting stress test: {concurrent_sessions} sessions for {duration_minutes} minutes")
        
        results = {
            'start_time': datetime.utcnow().isoformat(),
            'concurrent_sessions': concurrent_sessions,
            'duration_minutes': duration_minutes,
            'sessions_created': 0,
            'sessions_failed': 0,
            'average_latency': 0.0,
            'error_rate': 0.0,
            'peak_memory_mb': 0.0,
            'issues': []
        }
        
        # TODO: Implement actual stress testing
        # This would involve creating multiple WebSocket connections
        # and sending concurrent audio streams
        
        return results

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report."""
        logger.info("Generating comprehensive pipeline report...")
        
        health = self.health_check()
        # latency = self.profile_latency("test-session", 30)
        # quality = self.measure_quality("test-audio.wav", "test-session")  
        # stress = self.stress_test(3, 2)
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'pipeline_version': '1.0.0',
            'health_check': health,
            'recommendations': [],
            'action_items': []
        }
        
        # Generate recommendations based on health check
        for issue in health.get('critical_issues', []):
            if issue['issue'] == 'SESSION_SYNC_MISMATCH':
                report['recommendations'].append({
                    'priority': 'HIGH',
                    'category': 'SESSION_MANAGEMENT',
                    'description': 'Fix session synchronization between database and service',
                    'estimated_effort': '2-4 hours'
                })
                
        if not health.get('critical_issues'):
            report['recommendations'].append({
                'priority': 'LOW', 
                'category': 'MONITORING',
                'description': 'System appears healthy - add proactive monitoring',
                'estimated_effort': '1-2 hours'
            })
        
        return report

def main():
    """Run comprehensive pipeline diagnostics."""
    diagnostics = PipelineDiagnostics()
    
    print("🔍 MINA PIPELINE DIAGNOSTICS STARTING...")
    print("=" * 50)
    
    # Run diagnostics
    report = diagnostics.generate_report()
    
    # Print summary
    print(f"\n📊 HEALTH STATUS: {report['health_check']['overall_status'].upper()}")
    print(f"⚠️  CRITICAL ISSUES: {len(report['health_check']['critical_issues'])}")
    print(f"💡 RECOMMENDATIONS: {len(report['recommendations'])}")
    
    # Print critical issues
    for issue in report['health_check']['critical_issues']:
        print(f"   🚨 {issue['issue']}: {issue['description']} ({issue['severity']})")
    
    # Print recommendations  
    for rec in report['recommendations']:
        print(f"   ✅ {rec['category']}: {rec['description']} ({rec['priority']})")
    
    # Save full report
    with open('/tmp/mina_diagnostics_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to: /tmp/mina_diagnostics_report.json")
    print("=" * 50)
    
    return report

if __name__ == "__main__":
    main()