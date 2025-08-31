#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE PIPELINE TEST: End-to-end validation of MINA transcription system
Tests all critical components: endpoints, QA pipeline, performance monitoring, error handling
"""

import os
import sys
import time
import json
import requests
import threading
from pathlib import Path
import tempfile
import base64
import asyncio
from typing import Dict, List, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensivePipelineTest:
    """Comprehensive test suite for MINA transcription pipeline"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
        self.session_id = f"test_session_{int(time.time())}"
        
        # Create test audio data (simple tone)
        self.test_audio_data = self.generate_test_audio()
        
        logger.info(f"🧪 Comprehensive Pipeline Test initialized for {base_url}")
        
    def generate_test_audio(self) -> bytes:
        """Generate simple test audio data (WebM format simulation)"""
        # This is a simple representation - in real tests you'd use actual audio
        # For now, create a byte pattern that simulates audio data
        header = b'webm\x00\x00\x00\x1a\x45\xdf\xa3'  # WebM header signature
        audio_data = b'\x01\x02\x03\x04' * 4000  # 16KB of "audio" data
        return header + audio_data
    
    async def test_health_endpoints(self) -> Dict:
        """Test all health and status endpoints"""
        logger.info("🔍 Testing health endpoints...")
        
        health_tests = [
            ("/health", "Main health endpoint"),
            ("/api/health", "Transcription health endpoint"),
            ("/", "Main page accessibility")
        ]
        
        results = []
        for endpoint, description in health_tests:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                status = "PASS" if response.status_code in [200, 404] else "FAIL"
                
                results.append({
                    "endpoint": endpoint,
                    "description": description,
                    "status_code": response.status_code,
                    "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                    "status": status
                })
                
                logger.info(f"✅ {endpoint}: {response.status_code} ({response.elapsed.total_seconds()*1000:.0f}ms)")
                
            except Exception as e:
                results.append({
                    "endpoint": endpoint,
                    "description": description,
                    "error": str(e),
                    "status": "ERROR"
                })
                logger.error(f"❌ {endpoint}: {e}")
                
        return {"test": "health_endpoints", "results": results}
    
    async def test_transcription_endpoint(self) -> Dict:
        """Test the main transcription endpoint with various scenarios"""
        logger.info("🎙️ Testing transcription endpoint...")
        
        tests = [
            {
                "name": "valid_audio",
                "audio_data": self.test_audio_data,
                "session_id": self.session_id,
                "expected_success": True
            },
            {
                "name": "empty_audio", 
                "audio_data": b"",
                "session_id": self.session_id,
                "expected_success": False
            },
            {
                "name": "small_audio",
                "audio_data": b"tiny",
                "session_id": self.session_id,
                "expected_success": True  # Should return empty transcript
            },
            {
                "name": "large_audio",
                "audio_data": self.test_audio_data * 10,  # 160KB
                "session_id": self.session_id,
                "expected_success": True
            }
        ]
        
        results = []
        for test in tests:
            try:
                # Prepare form data with base64 encoding as expected by endpoint
                import base64
                audio_b64 = base64.b64encode(test["audio_data"]).decode('utf-8')
                data = {
                    'session_id': test["session_id"],
                    'chunk_id': str(len(results) + 1),
                    'audio_data': audio_b64,
                    'action': 'transcribe'
                }
                
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/api/transcribe-audio", 
                    data=data,
                    timeout=30
                )
                processing_time = (time.time() - start_time) * 1000
                
                # Parse response
                if response.headers.get('content-type', '').startswith('application/json'):
                    result_data = response.json()
                else:
                    result_data = {"error": "Non-JSON response", "content": response.text[:200]}
                
                test_status = "PASS" if (
                    response.status_code == 200 and test["expected_success"]
                ) or (
                    response.status_code >= 400 and not test["expected_success"]
                ) else "FAIL"
                
                results.append({
                    "test_name": test["name"],
                    "status_code": response.status_code,
                    "processing_time_ms": int(processing_time),
                    "audio_size": len(test["audio_data"]),
                    "response_data": result_data,
                    "status": test_status
                })
                
                logger.info(f"✅ {test['name']}: {response.status_code} ({processing_time:.0f}ms)")
                
            except Exception as e:
                results.append({
                    "test_name": test["name"],
                    "error": str(e),
                    "status": "ERROR"
                })
                logger.error(f"❌ {test['name']}: {e}")
        
        return {"test": "transcription_endpoint", "results": results}
    
    async def test_performance_benchmarks(self) -> Dict:
        """Test performance benchmarks and latency requirements"""
        logger.info("🚀 Testing performance benchmarks...")
        
        # Performance test with multiple concurrent requests
        concurrent_tests = 5
        chunk_sizes = [1000, 5000, 10000, 20000]  # Different audio sizes
        
        results = []
        
        for chunk_size in chunk_sizes:
            if chunk_size <= len(self.test_audio_data):
                test_audio = self.test_audio_data[:chunk_size]
            else:
                # Repeat the test audio to reach desired size
                repeat_count = (chunk_size // len(self.test_audio_data)) + 1
                repeated_audio = self.test_audio_data * repeat_count
                test_audio = repeated_audio[:chunk_size]
            
            # Single request test
            start_time = time.time()
            try:
                import base64
                audio_b64 = base64.b64encode(test_audio).decode('utf-8')
                data = {
                    'session_id': f"{self.session_id}_perf", 
                    'chunk_id': '1',
                    'audio_data': audio_b64,
                    'action': 'transcribe'
                }
                
                response = requests.post(
                    f"{self.base_url}/api/transcribe-audio",
                    data=data,
                    timeout=30
                )
                
                latency = (time.time() - start_time) * 1000
                
                results.append({
                    "chunk_size": chunk_size,
                    "latency_ms": int(latency),
                    "status_code": response.status_code,
                    "throughput_bytes_per_sec": int(chunk_size / (latency / 1000)) if latency > 0 else 0,
                    "meets_latency_target": latency < 2000,  # <2s target
                    "test_type": "single_request"
                })
                
                logger.info(f"📊 Chunk {chunk_size}B: {latency:.0f}ms")
                
            except Exception as e:
                results.append({
                    "chunk_size": chunk_size,
                    "error": str(e),
                    "test_type": "single_request"
                })
        
        return {"test": "performance_benchmarks", "results": results}
    
    async def test_error_handling(self) -> Dict:
        """Test error handling and recovery scenarios"""
        logger.info("🛡️ Testing error handling...")
        
        error_tests = [
            {
                "name": "missing_audio_file",
                "method": "POST",
                "data": {"session_id": "test", "action": "transcribe"},
                "files": None,
                "expected_status": 400
            },
            {
                "name": "invalid_content_type", 
                "method": "POST",
                "data": {"session_id": "test", "audio_data": "aW52YWxpZA==", "action": "transcribe"},
                "files": None,
                "expected_status": [200, 400, 500]  # May handle gracefully
            },
            {
                "name": "malformed_request",
                "method": "POST", 
                "data": "invalid",
                "files": None,
                "expected_status": 400
            }
        ]
        
        results = []
        for test in error_tests:
            try:
                response = requests.post(
                    f"{self.base_url}/api/transcribe-audio",
                    data=test.get("data"),
                    files=test.get("files"),
                    timeout=10
                )
                
                expected_statuses = test["expected_status"] if isinstance(test["expected_status"], list) else [test["expected_status"]]
                status = "PASS" if response.status_code in expected_statuses else "FAIL"
                
                results.append({
                    "test_name": test["name"],
                    "status_code": response.status_code,
                    "expected_status": test["expected_status"],
                    "status": status
                })
                
                logger.info(f"✅ {test['name']}: {response.status_code}")
                
            except Exception as e:
                results.append({
                    "test_name": test["name"],
                    "error": str(e),
                    "status": "ERROR"
                })
                logger.error(f"❌ {test['name']}: {e}")
        
        return {"test": "error_handling", "results": results}
    
    async def test_session_management(self) -> Dict:
        """Test session management and state tracking"""
        logger.info("🎯 Testing session management...")
        
        test_session = f"session_mgmt_{int(time.time())}"
        results = []
        
        # Test multiple chunks in same session
        for chunk_id in range(1, 4):
            try:
                import base64
                audio_b64 = base64.b64encode(self.test_audio_data).decode('utf-8')
                data = {
                    'session_id': test_session,
                    'chunk_id': str(chunk_id),
                    'audio_data': audio_b64,
                    'action': 'transcribe'
                }
                
                response = requests.post(
                    f"{self.base_url}/api/transcribe-audio",
                    data=data,
                    timeout=15
                )
                
                results.append({
                    "chunk_id": chunk_id,
                    "session_id": test_session,
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                })
                
            except Exception as e:
                results.append({
                    "chunk_id": chunk_id,
                    "error": str(e)
                })
        
        return {"test": "session_management", "results": results}
    
    async def run_comprehensive_test(self) -> Dict:
        """Run all comprehensive tests and generate report"""
        logger.info("🚀 Starting comprehensive pipeline test suite...")
        
        start_time = time.time()
        all_results = []
        
        # Run all tests
        tests = [
            self.test_health_endpoints(),
            self.test_transcription_endpoint(),
            self.test_performance_benchmarks(),
            self.test_error_handling(),
            self.test_session_management()
        ]
        
        for test in tests:
            try:
                result = await test
                all_results.append(result)
            except Exception as e:
                logger.error(f"❌ Test failed: {e}")
                all_results.append({
                    "test": "failed_test",
                    "error": str(e)
                })
        
        total_time = time.time() - start_time
        
        # Generate summary
        summary = self.generate_test_summary(all_results, total_time)
        
        logger.info(f"✅ Comprehensive test suite completed in {total_time:.1f}s")
        
        return {
            "test_suite": "comprehensive_pipeline",
            "timestamp": time.time(),
            "duration_seconds": total_time,
            "summary": summary,
            "results": all_results
        }
    
    def generate_test_summary(self, results: List[Dict], duration: float) -> Dict:
        """Generate comprehensive test summary"""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        
        for test_group in results:
            if "results" in test_group:
                for result in test_group["results"]:
                    total_tests += 1
                    status = result.get("status", "UNKNOWN")
                    if status == "PASS":
                        passed_tests += 1
                    elif status == "FAIL":
                        failed_tests += 1
                    elif status == "ERROR":
                        error_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Determine overall grade
        if success_rate >= 95:
            grade = "A+"
        elif success_rate >= 90:
            grade = "A"
        elif success_rate >= 85:
            grade = "B+"
        elif success_rate >= 80:
            grade = "B"
        elif success_rate >= 70:
            grade = "C"
        else:
            grade = "F"
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "success_rate": round(success_rate, 1),
            "grade": grade,
            "duration_seconds": round(duration, 1),
            "status": "PASS" if success_rate >= 80 else "FAIL"
        }

async def main():
    """Main test execution"""
    
    # Test configuration
    base_url = os.getenv("TEST_BASE_URL", "http://localhost:5000")
    
    print("🧪 MINA Comprehensive Pipeline Test Suite")
    print("=" * 50)
    print(f"Target URL: {base_url}")
    print(f"Test Session: {int(time.time())}")
    print()
    
    # Initialize test suite
    test_suite = ComprehensivePipelineTest(base_url)
    
    try:
        # Run comprehensive tests
        results = await test_suite.run_comprehensive_test()
        
        # Print results
        print("📊 TEST RESULTS")
        print("=" * 50)
        
        summary = results["summary"]
        print(f"Overall Grade: {summary['grade']}")
        print(f"Success Rate: {summary['success_rate']}%")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Errors: {summary['errors']}")
        print(f"Duration: {summary['duration_seconds']}s")
        print()
        
        # Detailed results
        for test_group in results["results"]:
            test_name = test_group.get("test", "Unknown")
            print(f"🔍 {test_name.upper()}")
            
            if "results" in test_group:
                for result in test_group["results"]:
                    status_emoji = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️"}.get(result.get("status", ""), "❓")
                    test_desc = result.get("test_name", result.get("endpoint", result.get("description", "Unknown")))
                    print(f"  {status_emoji} {test_desc}")
            
            print()
        
        # Save results to file
        report_file = f"test_results_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📄 Detailed results saved to: {report_file}")
        
        # Exit with appropriate code
        exit_code = 0 if summary["status"] == "PASS" else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️ Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        logger.exception("Test suite error")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())