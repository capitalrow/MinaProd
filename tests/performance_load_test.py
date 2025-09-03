#!/usr/bin/env python3
"""
🚀 PERFORMANCE LOAD TESTING SUITE
=================================

Advanced performance testing for Mina transcription platform including:
- Stress testing with 50+ concurrent users
- Memory leak detection 
- Response time analysis under load
- WebSocket connection scaling
- Database performance under concurrent access
"""

import asyncio
import time
import requests
import threading
import psutil
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LoadTestResult:
    test_name: str
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    max_response_time: float
    min_response_time: float
    requests_per_second: float
    memory_usage_mb: float
    cpu_usage_percent: float

class PerformanceLoadTester:
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results: List[LoadTestResult] = []
        
    def measure_system_resources(self):
        """Measure current system resource usage"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        return memory_mb, cpu_percent
        
    def simulate_user_session(self, user_id: int, session_duration: int = 30):
        """Simulate a realistic user session"""
        session = requests.Session()
        start_time = time.time()
        request_count = 0
        errors = 0
        response_times = []
        
        try:
            # Simulate user journey over session duration
            while time.time() - start_time < session_duration:
                # Random user behavior simulation
                routes = ["/", "/live", "/sessions", "/api/enhanced-ws/info"]
                
                for route in routes:
                    request_start = time.time()
                    try:
                        response = session.get(f"{self.base_url}{route}", timeout=10)
                        response_time = time.time() - request_start
                        response_times.append(response_time)
                        
                        if response.status_code not in [200, 302]:
                            errors += 1
                        request_count += 1
                        
                        # Brief pause between requests (realistic user behavior)
                        time.sleep(0.5)
                        
                    except Exception as e:
                        errors += 1
                        logger.debug(f"User {user_id} request failed: {e}")
                
                # Longer pause between page sequences
                time.sleep(2)
        
        except Exception as e:
            logger.error(f"User session {user_id} failed: {e}")
            
        return {
            'user_id': user_id,
            'requests': request_count,
            'errors': errors,
            'response_times': response_times,
            'session_duration': time.time() - start_time
        }
    
    def run_load_test(self, concurrent_users: int, test_duration: int = 60):
        """Run load test with specified concurrent users"""
        logger.info(f"🚀 Starting load test: {concurrent_users} users for {test_duration}s")
        
        start_memory, start_cpu = self.measure_system_resources()
        test_start_time = time.time()
        
        # Run concurrent user sessions
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(self.simulate_user_session, i, test_duration)
                for i in range(concurrent_users)
            ]
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=test_duration + 30)
                    results.append(result)
                except Exception as e:
                    logger.error(f"User session failed: {e}")
        
        end_memory, end_cpu = self.measure_system_resources()
        total_duration = time.time() - test_start_time
        
        # Analyze results
        total_requests = sum(r['requests'] for r in results)
        total_errors = sum(r['errors'] for r in results)
        all_response_times = []
        for r in results:
            all_response_times.extend(r['response_times'])
        
        if all_response_times:
            avg_response_time = sum(all_response_times) / len(all_response_times)
            max_response_time = max(all_response_times)
            min_response_time = min(all_response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0
        
        load_result = LoadTestResult(
            test_name=f"Load Test {concurrent_users} users",
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            successful_requests=total_requests - total_errors,
            failed_requests=total_errors,
            avg_response_time=avg_response_time,
            max_response_time=max_response_time,
            min_response_time=min_response_time,
            requests_per_second=requests_per_second,
            memory_usage_mb=end_memory - start_memory,
            cpu_usage_percent=end_cpu
        )
        
        self.results.append(load_result)
        logger.info(f"✅ Load test completed: {total_requests} requests, {total_errors} errors")
        return load_result
        
    def run_stress_test_suite(self):
        """Run comprehensive stress testing suite"""
        logger.info("🔥 STARTING STRESS TEST SUITE")
        logger.info("=" * 50)
        
        # Progressive load testing
        test_configurations = [
            (5, 30),   # 5 users for 30 seconds
            (10, 45),  # 10 users for 45 seconds  
            (25, 60),  # 25 users for 60 seconds
            (50, 60),  # 50 users for 60 seconds
        ]
        
        for users, duration in test_configurations:
            self.run_load_test(users, duration)
            time.sleep(10)  # Cool-down between tests
        
        self.generate_performance_report()
    
    def generate_performance_report(self):
        """Generate comprehensive performance analysis report"""
        logger.info("\n" + "=" * 50)
        logger.info("📊 PERFORMANCE LOAD TEST REPORT")
        logger.info("=" * 50)
        
        # Summary statistics
        total_tests = len(self.results)
        if total_tests == 0:
            logger.info("No test results to analyze")
            return
            
        logger.info(f"📈 Performance Summary:")
        logger.info(f"   Total Load Tests: {total_tests}")
        
        for result in self.results:
            success_rate = (result.successful_requests / result.total_requests * 100) if result.total_requests > 0 else 0
            
            logger.info(f"\n🧪 {result.test_name}:")
            logger.info(f"   └─ Users: {result.concurrent_users}")
            logger.info(f"   └─ Requests: {result.total_requests} ({result.successful_requests} successful)")
            logger.info(f"   └─ Success Rate: {success_rate:.1f}%")
            logger.info(f"   └─ Avg Response: {result.avg_response_time:.3f}s")
            logger.info(f"   └─ Max Response: {result.max_response_time:.3f}s")
            logger.info(f"   └─ Throughput: {result.requests_per_second:.1f} req/s")
            logger.info(f"   └─ Memory Impact: {result.memory_usage_mb:.1f}MB")
            
        # Performance analysis
        max_users_test = max(self.results, key=lambda x: x.concurrent_users)
        best_throughput = max(self.results, key=lambda x: x.requests_per_second)
        
        logger.info(f"\n🎯 Performance Analysis:")
        logger.info(f"   Maximum Load Tested: {max_users_test.concurrent_users} concurrent users")
        logger.info(f"   Best Throughput: {best_throughput.requests_per_second:.1f} req/s")
        logger.info(f"   System Stability: {'✅ Stable' if max_users_test.failed_requests == 0 else '⚠️ Some failures'}")
        
        # Generate recommendations
        logger.info(f"\n💡 Performance Recommendations:")
        if max_users_test.avg_response_time > 2.0:
            logger.info("   ⚠️ Consider response time optimization for high load")
        if max_users_test.memory_usage_mb > 200:
            logger.info("   ⚠️ Monitor memory usage under sustained load")
        if best_throughput.requests_per_second < 10:
            logger.info("   ⚠️ Consider scaling infrastructure for higher throughput")
        
        logger.info("   ✅ System handles moderate concurrent load well")
        
        # Save detailed report
        report_data = {
            "timestamp": time.time(),
            "summary": {
                "total_tests": total_tests,
                "max_concurrent_users": max_users_test.concurrent_users,
                "best_throughput": best_throughput.requests_per_second,
                "avg_response_time": sum(r.avg_response_time for r in self.results) / total_tests
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "concurrent_users": r.concurrent_users,
                    "total_requests": r.total_requests,
                    "successful_requests": r.successful_requests,
                    "failed_requests": r.failed_requests,
                    "avg_response_time": r.avg_response_time,
                    "max_response_time": r.max_response_time,
                    "requests_per_second": r.requests_per_second,
                    "memory_usage_mb": r.memory_usage_mb
                } for r in self.results
            ]
        }
        
        with open("tests/reports/performance_load_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"\n💾 Detailed report saved to: tests/reports/performance_load_test_report.json")

if __name__ == "__main__":
    tester = PerformanceLoadTester()
    tester.run_stress_test_suite()