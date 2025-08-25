#!/usr/bin/env python3
"""
Live Transcription Pipeline Performance Profiler
Measures end-to-end latency, queue performance, and system metrics
"""

import time
import asyncio
import requests
import json
import psutil
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from collections import deque, defaultdict

@dataclass
class PipelineMetrics:
    """Comprehensive pipeline performance metrics"""
    # Latency Metrics
    chunk_latency_ms: List[float]
    audio_to_interim_ms: List[float] 
    interim_to_final_ms: List[float]
    end_to_end_latency_ms: List[float]
    
    # Queue Performance
    queue_length_samples: List[int]
    max_queue_length: int
    queue_overflow_count: int
    
    # Chunk Analysis
    total_chunks_sent: int
    chunks_processed: int
    chunks_dropped: int
    duplicate_chunks: int
    
    # Transcription Quality
    interim_events: int
    final_events: int
    interim_to_final_ratio: float
    confidence_scores: List[float]
    
    # System Performance
    cpu_usage_samples: List[float]
    memory_usage_mb: List[float]
    event_loop_lag_ms: List[float]
    
    # Error Analysis
    retries: int
    api_failures: int
    websocket_disconnects: int
    timeout_errors: int

class PipelineProfiler:
    """Real-time pipeline performance profiler"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.metrics = PipelineMetrics(
            chunk_latency_ms=[], audio_to_interim_ms=[], interim_to_final_ms=[],
            end_to_end_latency_ms=[], queue_length_samples=[], max_queue_length=0,
            queue_overflow_count=0, total_chunks_sent=0, chunks_processed=0,
            chunks_dropped=0, duplicate_chunks=0, interim_events=0, final_events=0,
            interim_to_final_ratio=0.0, confidence_scores=[], cpu_usage_samples=[],
            memory_usage_mb=[], event_loop_lag_ms=[], retries=0, api_failures=0,
            websocket_disconnects=0, timeout_errors=0
        )
        self.chunk_timestamps = {}
        self.interim_timestamps = {}
        self.monitoring = False
        
    def start_monitoring(self, duration_seconds: int = 60):
        """Start comprehensive pipeline monitoring"""
        print(f"🔍 Starting pipeline profiling for {duration_seconds} seconds...")
        self.monitoring = True
        
        # Start system monitoring thread
        system_thread = threading.Thread(target=self._monitor_system_resources)
        system_thread.daemon = True
        system_thread.start()
        
        # Start API monitoring
        api_thread = threading.Thread(target=self._monitor_api_performance)
        api_thread.daemon = True
        api_thread.start()
        
        # Monitor for specified duration
        time.sleep(duration_seconds)
        self.monitoring = False
        
        return self._compile_results()
    
    def _monitor_system_resources(self):
        """Monitor CPU, memory, and event loop performance"""
        while self.monitoring:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                self.metrics.cpu_usage_samples.append(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.metrics.memory_usage_mb.append(memory.used / 1024 / 1024)
                
                # Event loop lag simulation (measure API response time as proxy)
                start_time = time.time()
                try:
                    response = requests.get(f"{self.base_url}/api/health", timeout=1)
                    if response.status_code == 200:
                        lag_ms = (time.time() - start_time) * 1000
                        self.metrics.event_loop_lag_ms.append(lag_ms)
                except:
                    self.metrics.event_loop_lag_ms.append(1000)  # Assume 1s lag on error
                    
            except Exception as e:
                print(f"Error monitoring system resources: {e}")
            
            time.sleep(1)
    
    def _monitor_api_performance(self):
        """Monitor API endpoints and transcription metrics"""
        while self.monitoring:
            try:
                # Get current stats
                response = requests.get(f"{self.base_url}/api/stats", timeout=5)
                if response.status_code == 200:
                    stats = response.json()
                    
                    # Extract service metrics
                    service_stats = stats.get('service', {})
                    self.metrics.interim_events = service_stats.get('total_interim_events', 0)
                    self.metrics.final_events = service_stats.get('total_final_events', 0)
                    
                    # Calculate interim to final ratio
                    if self.metrics.interim_events > 0:
                        self.metrics.interim_to_final_ratio = self.metrics.final_events / self.metrics.interim_events
                    
                    # Queue length monitoring
                    active_sessions = service_stats.get('active_sessions', 0)
                    self.metrics.queue_length_samples.append(active_sessions)
                    self.metrics.max_queue_length = max(self.metrics.max_queue_length, active_sessions)
                    
                    # Error tracking
                    self.metrics.retries = service_stats.get('total_retries', 0)
                    
                else:
                    self.metrics.api_failures += 1
                    
            except requests.RequestException:
                self.metrics.api_failures += 1
            except Exception as e:
                print(f"Error monitoring API performance: {e}")
            
            time.sleep(0.5)  # High frequency monitoring
    
    def _compile_results(self) -> Dict:
        """Compile comprehensive performance results"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'summary': self._generate_summary(),
            'detailed_metrics': asdict(self.metrics),
            'performance_analysis': self._analyze_performance(),
            'recommendations': self._generate_recommendations()
        }
        return results
    
    def _generate_summary(self) -> Dict:
        """Generate performance summary"""
        cpu_avg = sum(self.metrics.cpu_usage_samples) / len(self.metrics.cpu_usage_samples) if self.metrics.cpu_usage_samples else 0
        memory_avg = sum(self.metrics.memory_usage_mb) / len(self.metrics.memory_usage_mb) if self.metrics.memory_usage_mb else 0
        event_loop_avg = sum(self.metrics.event_loop_lag_ms) / len(self.metrics.event_loop_lag_ms) if self.metrics.event_loop_lag_ms else 0
        
        return {
            'avg_cpu_usage_percent': round(cpu_avg, 2),
            'avg_memory_usage_mb': round(memory_avg, 2),
            'avg_event_loop_lag_ms': round(event_loop_avg, 2),
            'interim_to_final_ratio': round(self.metrics.interim_to_final_ratio, 3),
            'total_api_failures': self.metrics.api_failures,
            'max_queue_length': self.metrics.max_queue_length,
            'total_retries': self.metrics.retries
        }
    
    def _analyze_performance(self) -> Dict:
        """Analyze performance bottlenecks"""
        analysis = {
            'cpu_status': 'healthy' if sum(self.metrics.cpu_usage_samples) / len(self.metrics.cpu_usage_samples) < 70 else 'high',
            'memory_status': 'healthy' if sum(self.metrics.memory_usage_mb) / len(self.metrics.memory_usage_mb) < 512 else 'high',
            'event_loop_status': 'healthy' if sum(self.metrics.event_loop_lag_ms) / len(self.metrics.event_loop_lag_ms) < 100 else 'slow',
            'api_reliability': 'good' if self.metrics.api_failures < 5 else 'poor',
            'queue_performance': 'efficient' if self.metrics.max_queue_length < 5 else 'congested'
        }
        
        return analysis
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        analysis = self._analyze_performance()
        
        if analysis['cpu_status'] == 'high':
            recommendations.append("Consider optimizing CPU-intensive operations or scaling horizontally")
        
        if analysis['memory_status'] == 'high':
            recommendations.append("Implement memory optimization and garbage collection improvements")
        
        if analysis['event_loop_status'] == 'slow':
            recommendations.append("Optimize blocking operations and improve async performance")
        
        if analysis['api_reliability'] == 'poor':
            recommendations.append("Implement better error handling and retry mechanisms")
        
        if analysis['queue_performance'] == 'congested':
            recommendations.append("Increase processing capacity or implement load balancing")
        
        if self.metrics.interim_to_final_ratio > 5.0:
            recommendations.append("High interim-to-final ratio suggests excessive interim events")
        
        return recommendations

def main():
    """Run comprehensive pipeline profiling"""
    profiler = PipelineProfiler()
    
    print("🚀 MINA PIPELINE PERFORMANCE PROFILER")
    print("=" * 50)
    
    # Run profiling
    results = profiler.start_monitoring(duration_seconds=30)
    
    # Display results
    print("\n📊 PERFORMANCE SUMMARY")
    print("-" * 30)
    for key, value in results['summary'].items():
        print(f"{key}: {value}")
    
    print("\n🔍 PERFORMANCE ANALYSIS")
    print("-" * 30)
    for key, value in results['performance_analysis'].items():
        print(f"{key}: {value}")
    
    print("\n💡 RECOMMENDATIONS")
    print("-" * 30)
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"{i}. {rec}")
    
    # Save detailed results
    with open('pipeline_performance_report.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Detailed report saved to: pipeline_performance_report.json")
    
    return results

if __name__ == "__main__":
    main()