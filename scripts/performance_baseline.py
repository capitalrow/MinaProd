"""
Performance Baseline Script for Mina Application
Measures response times, memory, throughput, and database performance
"""

import time
import requests
import psutil
import statistics
from typing import Dict, List, Tuple
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PerformanceBaseline:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results = {}
        
    def measure_endpoint(self, name: str, path: str, method: str = "GET", iterations: int = 10) -> Dict:
        """Measure endpoint performance"""
        response_times = []
        status_codes = []
        
        print(f"Testing {name}...")
        
        for i in range(iterations):
            start = time.time()
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{path}", timeout=10)
                else:
                    response = requests.post(f"{self.base_url}{path}", timeout=10)
                
                elapsed = (time.time() - start) * 1000  # Convert to ms
                status_codes.append(response.status_code)
                
                # Only count as success if 2xx status code
                if 200 <= response.status_code < 300:
                    response_times.append(elapsed)
                else:
                    print(f"  Non-2xx status on iteration {i+1}: {response.status_code}")
            except Exception as e:
                print(f"  Error on iteration {i+1}: {e}")
                status_codes.append(0)
        
        valid_times = [t for t in response_times if t > 0]
        
        if valid_times:
            return {
                "name": name,
                "path": path,
                "iterations": iterations,
                "success_rate": (len(valid_times) / iterations) * 100,
                "avg_response_time_ms": statistics.mean(valid_times),
                "min_response_time_ms": min(valid_times),
                "max_response_time_ms": max(valid_times),
                "p50_response_time_ms": statistics.median(valid_times),
                "p95_response_time_ms": statistics.quantiles(valid_times, n=20)[18] if len(valid_times) >= 20 else max(valid_times),
                "status_codes": list(set(status_codes))
            }
        else:
            return {"name": name, "error": "All requests failed"}
    
    def measure_memory(self) -> Dict:
        """Measure current memory usage"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent()
        }
    
    def measure_system_resources(self) -> Dict:
        """Measure system-wide resources"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_total_gb": memory.total / 1024 / 1024 / 1024,
            "memory_available_gb": memory.available / 1024 / 1024 / 1024,
            "memory_used_percent": memory.percent,
            "disk_total_gb": disk.total / 1024 / 1024 / 1024,
            "disk_used_percent": disk.percent
        }
    
    def run_baseline(self):
        """Run complete performance baseline"""
        print("=" * 60)
        print("MINA PERFORMANCE BASELINE")
        print("=" * 60)
        print()
        
        # Test key endpoints
        endpoints = [
            ("Dashboard", "/dashboard/", "GET"),
            ("API Analytics", "/api/analytics/trends?days=30", "GET"),
            ("API Meetings", "/api/meetings?limit=5", "GET"),
            ("Health Check", "/health", "GET"),
        ]
        
        endpoint_results = []
        for name, path, method in endpoints:
            result = self.measure_endpoint(name, path, method, iterations=10)
            endpoint_results.append(result)
            time.sleep(0.5)  # Brief pause between tests
        
        # Measure resources
        memory = self.measure_memory()
        system = self.measure_system_resources()
        
        # Print results
        print("\n" + "=" * 60)
        print("ENDPOINT PERFORMANCE RESULTS")
        print("=" * 60)
        
        for result in endpoint_results:
            if "error" not in result:
                print(f"\n{result['name']} ({result['path']})")
                print(f"  Success Rate: {result['success_rate']:.1f}%")
                print(f"  Avg Response Time: {result['avg_response_time_ms']:.2f} ms")
                print(f"  Min/Max: {result['min_response_time_ms']:.2f} / {result['max_response_time_ms']:.2f} ms")
                print(f"  P50: {result['p50_response_time_ms']:.2f} ms")
                print(f"  P95: {result['p95_response_time_ms']:.2f} ms")
                print(f"  Status Codes: {result['status_codes']}")
            else:
                print(f"\n{result['name']}: {result['error']}")
        
        print("\n" + "=" * 60)
        print("MEMORY USAGE")
        print("=" * 60)
        print(f"  RSS: {memory['rss_mb']:.2f} MB")
        print(f"  VMS: {memory['vms_mb']:.2f} MB")
        print(f"  Percent: {memory['percent']:.2f}%")
        
        print("\n" + "=" * 60)
        print("SYSTEM RESOURCES")
        print("=" * 60)
        print(f"  CPU Usage: {system['cpu_percent']:.1f}%")
        print(f"  Memory: {system['memory_used_percent']:.1f}% used")
        print(f"  Memory Available: {system['memory_available_gb']:.2f} GB")
        print(f"  Disk: {system['disk_used_percent']:.1f}% used")
        
        print("\n" + "=" * 60)
        print("BASELINE SUMMARY")
        print("=" * 60)
        
        # Calculate averages
        successful_endpoints = [r for r in endpoint_results if "error" not in r and r.get("success_rate", 0) > 0]
        if successful_endpoints:
            avg_response = statistics.mean([r["avg_response_time_ms"] for r in successful_endpoints])
            max_response = max([r["max_response_time_ms"] for r in successful_endpoints])
            print(f"  Average Response Time: {avg_response:.2f} ms")
            print(f"  Maximum Response Time: {max_response:.2f} ms")
            print(f"  Endpoints Tested: {len(successful_endpoints)}")
            print(f"  Overall Success Rate: {statistics.mean([r['success_rate'] for r in successful_endpoints]):.1f}%")
        
        print(f"  Memory Footprint: {memory['rss_mb']:.2f} MB")
        print(f"  CPU Usage: {system['cpu_percent']:.1f}%")
        print()
        
        # Store results
        self.results = {
            "endpoints": endpoint_results,
            "memory": memory,
            "system": system,
            "timestamp": time.time()
        }
        
        return self.results

if __name__ == "__main__":
    baseline = PerformanceBaseline()
    baseline.run_baseline()
