#!/usr/bin/env python3
"""
Backend Performance Profiler for Mina Transcription Pipeline
Measures latency, queue depth, memory usage, and event loop performance
"""

import asyncio
import psutil
import time
import threading
from typing import Dict, List, Any
import json
from datetime import datetime

class BackendProfiler:
    """Profiles backend transcription pipeline performance"""
    
    def __init__(self):
        self.metrics = {
            'start_time': time.time(),
            'chunk_latencies': [],
            'queue_lengths': [],
            'memory_usage': [],
            'cpu_usage': [],
            'event_loop_blocks': [],
            'websocket_metrics': {},
            'api_call_metrics': [],
            'deduplication_stats': {},
            'confidence_filtering': {}
        }
        self.monitoring = False
    
    def start_monitoring(self):
        """Start background monitoring"""
        self.monitoring = True
        
        # Start monitoring threads
        threading.Thread(target=self._monitor_system_resources, daemon=True).start()
        threading.Thread(target=self._monitor_event_loop, daemon=True).start()
        
        print("📊 Backend profiling started...")
    
    def stop_monitoring(self):
        """Stop monitoring and generate report"""
        self.monitoring = False
        time.sleep(1)  # Allow final measurements
        return self.generate_profile_report()
    
    def _monitor_system_resources(self):
        """Monitor CPU and memory usage"""
        while self.monitoring:
            process = psutil.Process()
            
            self.metrics['memory_usage'].append({
                'timestamp': time.time(),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'memory_percent': process.memory_percent(),
                'cpu_percent': process.cpu_percent()
            })
            
            self.metrics['cpu_usage'].append({
                'timestamp': time.time(),
                'cpu_percent': psutil.cpu_percent(),
                'load_avg': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            })
            
            time.sleep(1)
    
    def _monitor_event_loop(self):
        """Monitor event loop blocking"""
        last_time = time.time()
        
        while self.monitoring:
            current_time = time.time()
            loop_time = current_time - last_time
            
            if loop_time > 0.1:  # Block detection threshold
                self.metrics['event_loop_blocks'].append({
                    'timestamp': current_time,
                    'block_duration': loop_time,
                    'severity': 'high' if loop_time > 0.5 else 'medium'
                })
            
            last_time = current_time
            time.sleep(0.01)  # Check every 10ms
    
    def record_chunk_latency(self, session_id: str, chunk_id: int, latency_ms: float):
        """Record audio chunk processing latency"""
        self.metrics['chunk_latencies'].append({
            'timestamp': time.time(),
            'session_id': session_id,
            'chunk_id': chunk_id,
            'latency_ms': latency_ms,
            'category': self._categorize_latency(latency_ms)
        })
    
    def record_queue_length(self, queue_name: str, length: int):
        """Record queue depth"""
        self.metrics['queue_lengths'].append({
            'timestamp': time.time(),
            'queue_name': queue_name,
            'length': length,
            'status': 'normal' if length < 5 else 'high' if length < 10 else 'critical'
        })
    
    def record_api_call(self, api_name: str, duration_ms: float, success: bool, response_size: int = 0):
        """Record API call metrics"""
        self.metrics['api_call_metrics'].append({
            'timestamp': time.time(),
            'api_name': api_name,
            'duration_ms': duration_ms,
            'success': success,
            'response_size': response_size,
            'category': self._categorize_api_performance(duration_ms)
        })
    
    def record_deduplication(self, session_id: str, duplicates_removed: int, total_segments: int):
        """Record deduplication effectiveness"""
        if session_id not in self.metrics['deduplication_stats']:
            self.metrics['deduplication_stats'][session_id] = []
        
        self.metrics['deduplication_stats'][session_id].append({
            'timestamp': time.time(),
            'duplicates_removed': duplicates_removed,
            'total_segments': total_segments,
            'dedup_rate': duplicates_removed / max(total_segments, 1)
        })
    
    def record_confidence_filtering(self, session_id: str, filtered_count: int, total_count: int, avg_confidence: float):
        """Record confidence filtering effectiveness"""
        if session_id not in self.metrics['confidence_filtering']:
            self.metrics['confidence_filtering'][session_id] = []
        
        self.metrics['confidence_filtering'][session_id].append({
            'timestamp': time.time(),
            'filtered_count': filtered_count,
            'total_count': total_count,
            'filter_rate': filtered_count / max(total_count, 1),
            'avg_confidence': avg_confidence
        })
    
    def _categorize_latency(self, latency_ms: float) -> str:
        """Categorize latency performance"""
        if latency_ms < 100:
            return 'excellent'
        elif latency_ms < 300:
            return 'good'
        elif latency_ms < 1000:
            return 'acceptable'
        else:
            return 'poor'
    
    def _categorize_api_performance(self, duration_ms: float) -> str:
        """Categorize API call performance"""
        if duration_ms < 500:
            return 'fast'
        elif duration_ms < 1000:
            return 'moderate'
        elif duration_ms < 2000:
            return 'slow'
        else:
            return 'very_slow'
    
    def generate_profile_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        runtime = time.time() - self.metrics['start_time']
        
        report = {
            'profile_summary': {
                'runtime_seconds': runtime,
                'timestamp': datetime.now().isoformat(),
                'total_chunks_processed': len(self.metrics['chunk_latencies']),
                'total_api_calls': len(self.metrics['api_call_metrics'])
            },
            'latency_analysis': self._analyze_latencies(),
            'resource_analysis': self._analyze_resources(),
            'queue_analysis': self._analyze_queues(),
            'api_performance': self._analyze_api_performance(),
            'event_loop_health': self._analyze_event_loop(),
            'deduplication_effectiveness': self._analyze_deduplication(),
            'confidence_filtering_effectiveness': self._analyze_confidence_filtering(),
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _analyze_latencies(self) -> Dict[str, Any]:
        """Analyze chunk processing latencies"""
        if not self.metrics['chunk_latencies']:
            return {'status': 'no_data'}
        
        latencies = [chunk['latency_ms'] for chunk in self.metrics['chunk_latencies']]
        
        return {
            'total_chunks': len(latencies),
            'avg_latency_ms': sum(latencies) / len(latencies),
            'min_latency_ms': min(latencies),
            'max_latency_ms': max(latencies),
            'p95_latency_ms': sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
            'latency_distribution': {
                'excellent': len([l for l in latencies if l < 100]),
                'good': len([l for l in latencies if 100 <= l < 300]),
                'acceptable': len([l for l in latencies if 300 <= l < 1000]),
                'poor': len([l for l in latencies if l >= 1000])
            }
        }
    
    def _analyze_resources(self) -> Dict[str, Any]:
        """Analyze system resource usage"""
        if not self.metrics['memory_usage']:
            return {'status': 'no_data'}
        
        memory_values = [m['memory_mb'] for m in self.metrics['memory_usage']]
        cpu_values = [c['cpu_percent'] for c in self.metrics['cpu_usage']]
        
        return {
            'memory_analysis': {
                'avg_memory_mb': sum(memory_values) / len(memory_values),
                'max_memory_mb': max(memory_values),
                'memory_trend': 'increasing' if memory_values[-1] > memory_values[0] else 'stable'
            },
            'cpu_analysis': {
                'avg_cpu_percent': sum(cpu_values) / len(cpu_values),
                'max_cpu_percent': max(cpu_values),
                'cpu_spikes': len([c for c in cpu_values if c > 80])
            }
        }
    
    def _analyze_queues(self) -> Dict[str, Any]:
        """Analyze queue depth and performance"""
        if not self.metrics['queue_lengths']:
            return {'status': 'no_data'}
        
        queue_stats = {}
        for queue_entry in self.metrics['queue_lengths']:
            queue_name = queue_entry['queue_name']
            if queue_name not in queue_stats:
                queue_stats[queue_name] = []
            queue_stats[queue_name].append(queue_entry['length'])
        
        analysis = {}
        for queue_name, lengths in queue_stats.items():
            analysis[queue_name] = {
                'avg_length': sum(lengths) / len(lengths),
                'max_length': max(lengths),
                'backlog_events': len([l for l in lengths if l > 5])
            }
        
        return analysis
    
    def _analyze_api_performance(self) -> Dict[str, Any]:
        """Analyze API call performance"""
        if not self.metrics['api_call_metrics']:
            return {'status': 'no_data'}
        
        api_stats = {}
        for call in self.metrics['api_call_metrics']:
            api_name = call['api_name']
            if api_name not in api_stats:
                api_stats[api_name] = {'durations': [], 'successes': 0, 'failures': 0}
            
            api_stats[api_name]['durations'].append(call['duration_ms'])
            if call['success']:
                api_stats[api_name]['successes'] += 1
            else:
                api_stats[api_name]['failures'] += 1
        
        analysis = {}
        for api_name, stats in api_stats.items():
            durations = stats['durations']
            analysis[api_name] = {
                'total_calls': len(durations),
                'success_rate': stats['successes'] / (stats['successes'] + stats['failures']),
                'avg_duration_ms': sum(durations) / len(durations),
                'max_duration_ms': max(durations),
                'p95_duration_ms': sorted(durations)[int(len(durations) * 0.95)] if durations else 0
            }
        
        return analysis
    
    def _analyze_event_loop(self) -> Dict[str, Any]:
        """Analyze event loop blocking"""
        blocks = self.metrics['event_loop_blocks']
        
        if not blocks:
            return {'status': 'healthy', 'total_blocks': 0}
        
        return {
            'total_blocks': len(blocks),
            'max_block_duration': max(block['block_duration'] for block in blocks),
            'avg_block_duration': sum(block['block_duration'] for block in blocks) / len(blocks),
            'severe_blocks': len([b for b in blocks if b['severity'] == 'high']),
            'status': 'unhealthy' if len([b for b in blocks if b['severity'] == 'high']) > 0 else 'degraded'
        }
    
    def _analyze_deduplication(self) -> Dict[str, Any]:
        """Analyze deduplication effectiveness"""
        if not self.metrics['deduplication_stats']:
            return {'status': 'no_data'}
        
        total_duplicates = 0
        total_segments = 0
        
        for session_data in self.metrics['deduplication_stats'].values():
            for entry in session_data:
                total_duplicates += entry['duplicates_removed']
                total_segments += entry['total_segments']
        
        return {
            'total_duplicates_removed': total_duplicates,
            'total_segments_processed': total_segments,
            'overall_dedup_rate': total_duplicates / max(total_segments, 1),
            'effectiveness': 'good' if total_duplicates / max(total_segments, 1) > 0.1 else 'minimal'
        }
    
    def _analyze_confidence_filtering(self) -> Dict[str, Any]:
        """Analyze confidence filtering effectiveness"""
        if not self.metrics['confidence_filtering']:
            return {'status': 'no_data'}
        
        total_filtered = 0
        total_processed = 0
        confidence_sum = 0
        confidence_count = 0
        
        for session_data in self.metrics['confidence_filtering'].values():
            for entry in session_data:
                total_filtered += entry['filtered_count']
                total_processed += entry['total_count']
                confidence_sum += entry['avg_confidence']
                confidence_count += 1
        
        return {
            'total_filtered': total_filtered,
            'total_processed': total_processed,
            'filter_rate': total_filtered / max(total_processed, 1),
            'avg_confidence': confidence_sum / max(confidence_count, 1),
            'effectiveness': 'good' if total_filtered / max(total_processed, 1) < 0.2 else 'aggressive'
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Latency recommendations
        latency_analysis = self._analyze_latencies()
        if latency_analysis.get('max_latency_ms', 0) > 1000:
            recommendations.append("Reduce maximum latency spikes - consider request queuing")
        
        # Resource recommendations
        resource_analysis = self._analyze_resources()
        if resource_analysis.get('cpu_analysis', {}).get('max_cpu_percent', 0) > 80:
            recommendations.append("CPU usage spikes detected - implement load balancing")
        
        # Event loop recommendations
        event_loop_analysis = self._analyze_event_loop()
        if event_loop_analysis.get('severe_blocks', 0) > 0:
            recommendations.append("Event loop blocking detected - move heavy operations to worker threads")
        
        # API recommendations
        api_analysis = self._analyze_api_performance()
        for api_name, stats in api_analysis.items():
            if isinstance(stats, dict) and stats.get('success_rate', 1) < 0.95:
                recommendations.append(f"Improve {api_name} reliability - implement retry logic")
        
        return recommendations

# Example usage function
def profile_transcription_session():
    """Example of how to use the profiler"""
    profiler = BackendProfiler()
    profiler.start_monitoring()
    
    # Simulate some operations
    time.sleep(5)
    
    # Record some sample metrics
    profiler.record_chunk_latency("test_session", 1, 250)
    profiler.record_chunk_latency("test_session", 2, 1200)  # High latency
    profiler.record_api_call("whisper_api", 800, True, 1024)
    profiler.record_queue_length("audio_queue", 3)
    
    # Stop and get report
    report = profiler.stop_monitoring()
    
    print("📊 BACKEND PERFORMANCE REPORT")
    print("="*40)
    print(json.dumps(report, indent=2))
    
    return report

if __name__ == "__main__":
    profile_transcription_session()