#!/usr/bin/env python3
"""
WebSocket Performance Benchmark
Tests real-time transcription WebSocket latency and throughput
"""
import socketio
import time
import statistics
import asyncio
from typing import List

# Configuration
SERVER_URL = 'http://localhost:5000'
TEST_ITERATIONS = 50
CONCURRENT_CONNECTIONS = 10

class WebSocketBenchmark:
    def __init__(self):
        self.connection_times: List[float] = []
        self.message_latencies: List[float] = []
        self.errors = 0
        
    async def test_connection_latency(self):
        """Measure WebSocket connection establishment time"""
        sio = socketio.AsyncClient(logger=False, engineio_logger=False)
        
        start = time.time()
        try:
            await asyncio.wait_for(sio.connect(SERVER_URL), timeout=10.0)
            connection_time = (time.time() - start) * 1000  # Convert to ms
            self.connection_times.append(connection_time)
            await sio.disconnect()
            return connection_time
        except Exception as e:
            self.errors += 1
            print(f"Connection error: {e}")
            return None
    
    async def test_message_roundtrip(self):
        """Measure message roundtrip latency"""
        sio = socketio.AsyncClient(logger=False, engineio_logger=False)
        latencies = []
        
        try:
            await asyncio.wait_for(sio.connect(SERVER_URL), timeout=10.0)
            
            # Send test messages and measure response time
            for i in range(10):
                start = time.time()
                
                # Emit a ping-like event
                await sio.emit('ping', {'timestamp': start})
                
                # Wait a bit for processing
                await asyncio.sleep(0.1)
                
                latency = (time.time() - start) * 1000
                latencies.append(latency)
            
            await sio.disconnect()
            return latencies
        except Exception as e:
            self.errors += 1
            print(f"Message test error: {e}")
            return []
    
    async def run_connection_test(self, iterations: int):
        """Run connection latency test"""
        print(f"\n🔌 Testing WebSocket Connection Latency ({iterations} connections)...")
        
        for i in range(iterations):
            if i % 10 == 0 and i > 0:
                print(f"  Progress: {i}/{iterations}")
            await self.test_connection_latency()
            await asyncio.sleep(0.1)  # Small delay between tests
    
    async def run_concurrent_test(self, connections: int):
        """Test concurrent connections"""
        print(f"\n⚡ Testing Concurrent Connections ({connections} simultaneous)...")
        
        tasks = []
        start = time.time()
        
        for _ in range(connections):
            tasks.append(self.test_connection_latency())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start
        
        successful = sum(1 for r in results if r is not None and not isinstance(r, Exception))
        print(f"  Completed {successful}/{connections} connections in {duration:.2f}s")
    
    def print_results(self):
        """Print benchmark results"""
        print("\n" + "="*60)
        print("📊 WebSocket Performance Benchmark Results")
        print("="*60)
        
        if self.connection_times:
            conn_times = self.connection_times
            print(f"\n🔌 Connection Latency ({len(conn_times)} samples):")
            print(f"   Average:  {statistics.mean(conn_times):.2f} ms")
            print(f"   P50:      {statistics.median(conn_times):.2f} ms")
            print(f"   P95:      {statistics.quantiles(conn_times, n=20)[18]:.2f} ms" if len(conn_times) >= 20 else f"   P95:      N/A (need 20+ samples)")
            print(f"   Min:      {min(conn_times):.2f} ms")
            print(f"   Max:      {max(conn_times):.2f} ms")
            
            # SLO Compliance Check
            p50 = statistics.median(conn_times)
            p95 = statistics.quantiles(conn_times, n=20)[18] if len(conn_times) >= 20 else max(conn_times)
            
            print(f"\n✅ SLO Compliance:")
            print(f"   P50 < 2000ms: {'✅ PASS' if p50 < 2000 else '❌ FAIL'} ({p50:.2f}ms)")
            print(f"   P95 < 5000ms: {'✅ PASS' if p95 < 5000 else '❌ FAIL'} ({p95:.2f}ms)")
        
        if self.errors > 0:
            print(f"\n⚠️  Errors: {self.errors}")
        
        print("\n" + "="*60)

async def main():
    benchmark = WebSocketBenchmark()
    
    print("🚀 Mina WebSocket Performance Benchmark")
    print(f"Server: {SERVER_URL}")
    
    # Run tests
    await benchmark.run_connection_test(TEST_ITERATIONS)
    await benchmark.run_concurrent_test(CONCURRENT_CONNECTIONS)
    
    # Print results
    benchmark.print_results()

if __name__ == '__main__':
    asyncio.run(main())
