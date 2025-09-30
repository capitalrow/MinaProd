#!/usr/bin/env python3
"""
Comprehensive QA Pipeline for Mina Live Transcription System
Measures performance, accuracy, and end-to-end functionality
"""

import json
import time
import requests
import base64
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import threading
import queue
import statistics
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MinaQA')

@dataclass
class TranscriptionMetrics:
    """Comprehensive metrics for transcription quality assessment"""
    session_id: str
    timestamp: str
    
    # Performance Metrics
    total_chunks: int = 0
    successful_chunks: int = 0
    failed_chunks: int = 0
    average_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    
    # Quality Metrics
    total_words: int = 0
    total_characters: int = 0
    interim_updates: int = 0
    final_transcripts: int = 0
    
    # Audio Metrics
    total_audio_duration_s: float = 0.0
    audio_chunks_sent: int = 0
    audio_bytes_processed: int = 0
    
    # Error Tracking
    timeout_errors: int = 0
    network_errors: int = 0
    server_errors: int = 0
    audio_processing_errors: int = 0
    
    # System Resource Metrics
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate chunk processing success rate"""
        if self.total_chunks == 0:
            return 0.0
        return (self.successful_chunks / self.total_chunks) * 100
    
    @property
    def words_per_second(self) -> float:
        """Calculate transcription throughput"""
        if self.total_audio_duration_s == 0:
            return 0.0
        return self.total_words / self.total_audio_duration_s
    
    @property
    def latency_percentile_95(self) -> float:
        """Calculate 95th percentile latency (placeholder)"""
        return self.max_latency_ms * 0.95

class MinaQAPipeline:
    """Comprehensive QA testing pipeline for Mina transcription system"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.transcription_url = f"{base_url}/api/transcribe-audio"
        self.test_results = []
        self.current_metrics = None
        self.latency_measurements = []
        
    def create_test_audio_chunk(self, size_bytes: int = 1024) -> bytes:
        """Create synthetic audio data for testing"""
        # Generate pseudo-audio data (not real audio, but valid for API testing)
        import random
        return bytes([random.randint(0, 255) for _ in range(size_bytes)])
    
    def test_transcription_endpoint(self, audio_data: bytes, session_id: str, chunk_number: int) -> Dict:
        """Test single transcription request and measure performance"""
        start_time = time.time()
        
        try:
            # Encode audio to base64
            b64_audio = base64.b64encode(audio_data).decode('utf-8')
            
            # Prepare request
            payload = {
                'session_id': session_id,
                'audio_data': b64_audio,
                'chunk_number': chunk_number,
                'is_final': False
            }
            
            # Send request
            response = requests.post(
                self.transcription_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            latency = (time.time() - start_time) * 1000  # Convert to milliseconds
            self.latency_measurements.append(latency)
            
            # Parse response
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'latency_ms': latency,
                    'response': result,
                    'status_code': response.status_code,
                    'chunk_number': chunk_number
                }
            else:
                return {
                    'success': False,
                    'latency_ms': latency,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'status_code': response.status_code,
                    'chunk_number': chunk_number
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'latency_ms': (time.time() - start_time) * 1000,
                'error': 'Request timeout',
                'error_type': 'timeout',
                'chunk_number': chunk_number
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'latency_ms': (time.time() - start_time) * 1000,
                'error': str(e),
                'error_type': 'network',
                'chunk_number': chunk_number
            }
        except Exception as e:
            return {
                'success': False,
                'latency_ms': (time.time() - start_time) * 1000,
                'error': str(e),
                'error_type': 'unknown',
                'chunk_number': chunk_number
            }
    
    def test_session_lifecycle(self, session_id: str, num_chunks: int = 10) -> TranscriptionMetrics:
        """Test complete session with multiple chunks and final processing"""
        logger.info(f"🧪 Starting session lifecycle test: {session_id} ({num_chunks} chunks)")
        
        metrics = TranscriptionMetrics(
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
        start_time = time.time()
        
        # Send multiple audio chunks
        for chunk_num in range(1, num_chunks + 1):
            # Create test audio chunk
            audio_chunk = self.create_test_audio_chunk(1024 + (chunk_num * 100))
            
            # Test transcription
            result = self.test_transcription_endpoint(audio_chunk, session_id, chunk_num)
            
            # Update metrics
            metrics.total_chunks += 1
            metrics.audio_chunks_sent += 1
            metrics.audio_bytes_processed += len(audio_chunk)
            
            if result['success']:
                metrics.successful_chunks += 1
                
                # Parse transcription response
                response = result.get('response', {})
                text = response.get('text', '')
                
                if text and not text.startswith('['):
                    # Valid transcription text
                    words = len(text.split())
                    metrics.total_words += words
                    metrics.total_characters += len(text)
                    metrics.interim_updates += 1
                    
                    logger.info(f"✅ Chunk {chunk_num}: '{text}' ({result['latency_ms']:.1f}ms)")
                else:
                    logger.info(f"⚠️ Chunk {chunk_num}: No speech detected ({result['latency_ms']:.1f}ms)")
            else:
                metrics.failed_chunks += 1
                error_type = result.get('error_type', 'unknown')
                
                if error_type == 'timeout':
                    metrics.timeout_errors += 1
                elif error_type == 'network':
                    metrics.network_errors += 1
                else:
                    metrics.server_errors += 1
                
                logger.error(f"❌ Chunk {chunk_num}: {result['error']}")
            
            # Small delay between chunks (simulate real recording)
            time.sleep(0.5)
        
        # Test finalization
        logger.info(f"📝 Testing session finalization...")
        final_result = self.test_finalization(session_id, "Test transcript for finalization")
        
        if final_result['success']:
            metrics.final_transcripts += 1
            logger.info(f"✅ Session finalized successfully")
        else:
            logger.error(f"❌ Session finalization failed: {final_result['error']}")
        
        # Calculate final metrics
        metrics.total_audio_duration_s = time.time() - start_time
        
        if self.latency_measurements:
            metrics.average_latency_ms = statistics.mean(self.latency_measurements)
            metrics.min_latency_ms = min(self.latency_measurements)
            metrics.max_latency_ms = max(self.latency_measurements)
        
        return metrics
    
    def test_finalization(self, session_id: str, cumulative_text: str) -> Dict:
        """Test transcript finalization endpoint"""
        try:
            payload = {
                'session_id': session_id,
                'action': 'finalize',
                'text': cumulative_text,
                'is_final': True
            }
            
            response = requests.post(
                self.transcription_url,
                json=payload,
                timeout=15,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'final_text': result.get('final_text', ''),
                    'status': result.get('status', '')
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_error_conditions(self) -> Dict:
        """Test various error conditions and edge cases"""
        logger.info("🧪 Testing error conditions...")
        
        error_tests = {
            'empty_audio': self.test_empty_audio(),
            'invalid_base64': self.test_invalid_base64(),
            'missing_session_id': self.test_missing_session_id(),
            'oversized_audio': self.test_oversized_audio(),
            'malformed_request': self.test_malformed_request()
        }
        
        return error_tests
    
    def test_empty_audio(self) -> Dict:
        """Test with empty audio data"""
        return self.test_transcription_endpoint(b'', 'test_empty', 1)
    
    def test_invalid_base64(self) -> Dict:
        """Test with invalid base64 audio data"""
        try:
            payload = {
                'session_id': 'test_invalid_b64',
                'audio_data': 'invalid_base64_data!!!',
                'chunk_number': 1
            }
            
            response = requests.post(self.transcription_url, json=payload, timeout=5)
            
            return {
                'success': response.status_code != 200,
                'status_code': response.status_code,
                'expected_error': True
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_missing_session_id(self) -> Dict:
        """Test with missing session ID"""
        try:
            payload = {
                'audio_data': base64.b64encode(b'test').decode(),
                'chunk_number': 1
            }
            
            response = requests.post(self.transcription_url, json=payload, timeout=5)
            
            return {
                'success': True,  # Should handle gracefully
                'status_code': response.status_code,
                'response': response.json() if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_oversized_audio(self) -> Dict:
        """Test with oversized audio chunk"""
        large_audio = self.create_test_audio_chunk(10 * 1024 * 1024)  # 10MB
        return self.test_transcription_endpoint(large_audio, 'test_oversized', 1)
    
    def test_malformed_request(self) -> Dict:
        """Test with malformed JSON request"""
        try:
            response = requests.post(
                self.transcription_url,
                data="invalid json content",
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            return {
                'success': response.status_code != 200,
                'status_code': response.status_code,
                'expected_error': True
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def run_load_test(self, concurrent_sessions: int = 3, chunks_per_session: int = 5) -> List[TranscriptionMetrics]:
        """Run concurrent load test with multiple sessions"""
        logger.info(f"🚀 Starting load test: {concurrent_sessions} concurrent sessions, {chunks_per_session} chunks each")
        
        results = []
        threads = []
        results_queue = queue.Queue()
        
        def session_worker(session_num):
            session_id = f"load_test_session_{session_num}_{int(time.time())}"
            metrics = self.test_session_lifecycle(session_id, chunks_per_session)
            results_queue.put(metrics)
        
        # Start concurrent sessions
        for i in range(concurrent_sessions):
            thread = threading.Thread(target=session_worker, args=(i,))
            thread.start()
            threads.append(thread)
        
        # Wait for all sessions to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        while not results_queue.empty():
            results.append(results_queue.get())
        
        return results
    
    def generate_qa_report(self, metrics_list: List[TranscriptionMetrics], error_tests: Dict) -> Dict:
        """Generate comprehensive QA report"""
        if not metrics_list:
            return {'error': 'No metrics data available'}
        
        # Aggregate metrics
        total_chunks = sum(m.total_chunks for m in metrics_list)
        successful_chunks = sum(m.successful_chunks for m in metrics_list)
        total_words = sum(m.total_words for m in metrics_list)
        total_duration = sum(m.total_audio_duration_s for m in metrics_list)
        
        avg_latencies = [m.average_latency_ms for m in metrics_list if m.average_latency_ms > 0]
        
        report = {
            'test_summary': {
                'total_sessions_tested': len(metrics_list),
                'total_chunks_processed': total_chunks,
                'overall_success_rate': (successful_chunks / total_chunks * 100) if total_chunks > 0 else 0,
                'total_words_transcribed': total_words,
                'total_test_duration_s': total_duration,
                'average_words_per_session': total_words / len(metrics_list) if metrics_list else 0
            },
            'performance_metrics': {
                'average_latency_ms': statistics.mean(avg_latencies) if avg_latencies else 0,
                'median_latency_ms': statistics.median(avg_latencies) if avg_latencies else 0,
                'min_latency_ms': min(avg_latencies) if avg_latencies else 0,
                'max_latency_ms': max(avg_latencies) if avg_latencies else 0,
                'latency_std_dev': statistics.stdev(avg_latencies) if len(avg_latencies) > 1 else 0
            },
            'quality_metrics': {
                'transcription_throughput_wps': total_words / total_duration if total_duration > 0 else 0,
                'average_session_success_rate': statistics.mean([m.success_rate for m in metrics_list]) if metrics_list else 0,
                'interim_to_final_ratio': sum(m.interim_updates for m in metrics_list) / max(sum(m.final_transcripts for m in metrics_list), 1)
            },
            'error_analysis': {
                'timeout_errors': sum(m.timeout_errors for m in metrics_list),
                'network_errors': sum(m.network_errors for m in metrics_list),
                'server_errors': sum(m.server_errors for m in metrics_list),
                'audio_processing_errors': sum(m.audio_processing_errors for m in metrics_list)
            },
            'error_condition_tests': error_tests,
            'individual_session_metrics': [asdict(m) for m in metrics_list],
            'test_timestamp': datetime.now().isoformat(),
            'recommendations': self.generate_recommendations(metrics_list)
        }
        
        return report
    
    def generate_recommendations(self, metrics_list: List[TranscriptionMetrics]) -> List[str]:
        """Generate improvement recommendations based on test results"""
        recommendations = []
        
        if not metrics_list:
            return ['No test data available for analysis']
        
        # Calculate overall metrics
        avg_success_rate = statistics.mean([m.success_rate for m in metrics_list])
        avg_latency = statistics.mean([m.average_latency_ms for m in metrics_list if m.average_latency_ms > 0])
        
        # Performance recommendations
        if avg_latency > 2000:
            recommendations.append(f"HIGH: Average latency ({avg_latency:.1f}ms) exceeds target (<2000ms). Consider optimizing Whisper API calls or implementing caching.")
        
        if avg_success_rate < 95:
            recommendations.append(f"HIGH: Success rate ({avg_success_rate:.1f}%) below target (95%). Investigate error patterns and implement retry mechanisms.")
        
        # Check for error patterns
        total_timeouts = sum(m.timeout_errors for m in metrics_list)
        total_chunks = sum(m.total_chunks for m in metrics_list)
        
        if total_timeouts > 0 and total_chunks > 0:
            timeout_rate = (total_timeouts / total_chunks) * 100
            if timeout_rate > 5:
                recommendations.append(f"MEDIUM: High timeout rate ({timeout_rate:.1f}%). Consider increasing request timeouts or optimizing backend processing.")
        
        # Quality recommendations
        total_words = sum(m.total_words for m in metrics_list)
        if total_words == 0:
            recommendations.append("CRITICAL: No transcribed words detected. Verify audio processing pipeline and Whisper API integration.")
        
        # Add positive feedback
        if avg_success_rate >= 95 and avg_latency <= 2000:
            recommendations.append("EXCELLENT: System meets performance targets. Consider load testing with higher concurrency.")
        
        return recommendations

def main():
    """Run comprehensive QA pipeline"""
    print("🧪 MINA LIVE TRANSCRIPTION QA PIPELINE")
    print("=" * 50)
    
    qa = MinaQAPipeline()
    
    # Test 1: Single session lifecycle
    print("\n📋 Test 1: Single Session Lifecycle")
    session_metrics = qa.test_session_lifecycle("qa_test_single_001", 8)
    
    # Test 2: Error conditions
    print("\n📋 Test 2: Error Condition Testing")
    error_tests = qa.test_error_conditions()
    
    # Test 3: Load testing
    print("\n📋 Test 3: Concurrent Load Testing")
    load_results = qa.run_load_test(concurrent_sessions=2, chunks_per_session=5)
    
    # Combine all metrics
    all_metrics = [session_metrics] + load_results
    
    # Generate comprehensive report
    print("\n📊 Generating QA Report...")
    report = qa.generate_qa_report(all_metrics, error_tests)
    
    # Save report
    with open('qa_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 50)
    print("QA PIPELINE RESULTS SUMMARY")
    print("=" * 50)
    
    summary = report['test_summary']
    performance = report['performance_metrics']
    
    print(f"Sessions Tested: {summary['total_sessions_tested']}")
    print(f"Total Chunks: {summary['total_chunks_processed']}")
    print(f"Success Rate: {summary['overall_success_rate']:.1f}%")
    print(f"Words Transcribed: {summary['total_words_transcribed']}")
    print(f"Average Latency: {performance['average_latency_ms']:.1f}ms")
    
    print(f"\n📝 Recommendations:")
    for rec in report['recommendations']:
        print(f"  • {rec}")
    
    print(f"\n📄 Full report saved to: qa_report.json")
    
    return report

if __name__ == "__main__":
    main()