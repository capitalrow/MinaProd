"""
Performance and Load Testing
Tests system performance under various load conditions
"""

import pytest
import asyncio
import time
from playwright.async_api import Page, Browser, expect
import statistics


class TestPerformanceLoad:
    """Test system performance and load handling"""
    
    @pytest.mark.asyncio
    async def test_single_user_performance_baseline(self, live_page: Page):
        """Establish performance baseline for single user"""
        
        metrics = []
        
        for i in range(5):
            start_time = time.time()
            
            # Measure page load time
            await live_page.reload()
            await live_page.wait_for_load_state('networkidle')
            load_time = time.time() - start_time
            
            # Measure recording start time
            start_time = time.time()
            await live_page.locator('#recordButton').click()
            await expect(live_page.locator('#recordButton')).to_have_class(re.compile(r'.*recording.*'))
            recording_start_time = time.time() - start_time
            
            # Measure recording stop time
            await asyncio.sleep(2)
            start_time = time.time()
            await live_page.locator('#recordButton').click()
            await expect(live_page.locator('#recordButton')).not_to_have_class(re.compile(r'.*recording.*'))
            recording_stop_time = time.time() - start_time
            
            metrics.append({
                'iteration': i + 1,
                'load_time': load_time,
                'recording_start_time': recording_start_time,
                'recording_stop_time': recording_stop_time
            })
            
            await asyncio.sleep(1)  # Brief pause between iterations
        
        # Analyze baseline performance
        avg_load_time = statistics.mean(m['load_time'] for m in metrics)
        avg_start_time = statistics.mean(m['recording_start_time'] for m in metrics)
        avg_stop_time = statistics.mean(m['recording_stop_time'] for m in metrics)
        
        # Performance assertions
        assert avg_load_time < 3.0, f"Average load time too slow: {avg_load_time:.2f}s"
        assert avg_start_time < 1.0, f"Recording start too slow: {avg_start_time:.2f}s"
        assert avg_stop_time < 2.0, f"Recording stop too slow: {avg_stop_time:.2f}s"
        
        print(f"Performance Baseline - Load: {avg_load_time:.2f}s, Start: {avg_start_time:.2f}s, Stop: {avg_stop_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_memory_usage_over_time(self, live_page: Page):
        """Test memory usage stability over extended use"""
        
        memory_samples = []
        
        # Initial memory reading
        initial_memory = await live_page.evaluate("""
            () => performance.memory ? {
                used: performance.memory.usedJSHeapSize,
                total: performance.memory.totalJSHeapSize,
                limit: performance.memory.jsHeapSizeLimit
            } : null
        """)
        
        if initial_memory:
            memory_samples.append(initial_memory['used'])
        
        # Perform 10 recording cycles
        for i in range(10):
            await live_page.locator('#recordButton').click()
            await asyncio.sleep(3)
            await live_page.locator('#recordButton').click()
            await asyncio.sleep(1)
            
            # Sample memory every 2 cycles
            if i % 2 == 0:
                memory = await live_page.evaluate("() => performance.memory ? performance.memory.usedJSHeapSize : 0")
                if memory > 0:
                    memory_samples.append(memory)
        
        # Analyze memory usage
        if len(memory_samples) > 1:
            memory_growth = memory_samples[-1] - memory_samples[0]
            max_memory = max(memory_samples)
            
            # Memory should not grow excessively (allow 30MB growth)
            assert memory_growth < 30_000_000, f"Excessive memory growth: {memory_growth / 1_000_000:.1f}MB"
            assert max_memory < 200_000_000, f"Peak memory too high: {max_memory / 1_000_000:.1f}MB"
            
            print(f"Memory Usage - Growth: {memory_growth / 1_000_000:.1f}MB, Peak: {max_memory / 1_000_000:.1f}MB")
    
    @pytest.mark.asyncio
    async def test_concurrent_users_simulation(self, browser: Browser):
        """Simulate multiple concurrent users (limited by single process)"""
        
        num_concurrent = 5  # Limited for single-process testing
        contexts = []
        pages = []
        
        try:
            # Create multiple browser contexts
            for i in range(num_concurrent):
                context = await browser.new_context(
                    permissions=['microphone'],
                    viewport={'width': 1920, 'height': 1080}
                )
                page = await context.new_page()
                contexts.append(context)
                pages.append(page)
            
            # Load application in all contexts simultaneously
            start_time = time.time()
            load_tasks = [page.goto('http://localhost:5000/live') for page in pages]
            await asyncio.gather(*load_tasks)
            
            # Wait for all pages to be ready
            ready_tasks = [page.wait_for_load_state('networkidle') for page in pages]
            await asyncio.gather(*ready_tasks, return_exceptions=True)
            load_time = time.time() - start_time
            
            print(f"Concurrent load time for {num_concurrent} users: {load_time:.2f}s")
            
            # Start recording on all pages simultaneously
            start_time = time.time()
            start_tasks = [page.locator('#recordButton').click() for page in pages]
            await asyncio.gather(*start_tasks, return_exceptions=True)
            concurrent_start_time = time.time() - start_time
            
            # Let them record for a bit
            await asyncio.sleep(3)
            
            # Stop recording on all pages
            start_time = time.time()
            stop_tasks = [page.locator('#recordButton').click() for page in pages]
            await asyncio.gather(*stop_tasks, return_exceptions=True)
            concurrent_stop_time = time.time() - start_time
            
            # Performance assertions for concurrent usage
            assert load_time < 10.0, f"Concurrent load too slow: {load_time:.2f}s"
            assert concurrent_start_time < 3.0, f"Concurrent start too slow: {concurrent_start_time:.2f}s"
            assert concurrent_stop_time < 5.0, f"Concurrent stop too slow: {concurrent_stop_time:.2f}s"
            
            print(f"Concurrent Performance - Start: {concurrent_start_time:.2f}s, Stop: {concurrent_stop_time:.2f}s")
            
        finally:
            # Clean up all contexts
            for context in contexts:
                await context.close()
    
    @pytest.mark.asyncio
    async def test_ui_responsiveness_under_load(self, live_page: Page):
        """Test UI responsiveness during intensive operations"""
        
        response_times = []
        
        # Start a recording session
        await live_page.locator('#recordButton').click()
        
        # Test UI responsiveness every 500ms during recording
        for i in range(10):
            start_time = time.time()
            
            # Test timer element responsiveness
            timer_text = await live_page.locator('#timer').text_content()
            
            # Test transcript area responsiveness
            await live_page.locator('#transcript').click()
            
            # Test metrics update
            word_count = await live_page.locator('#wordCount').text_content()
            
            response_time = time.time() - start_time
            response_times.append(response_time)
            
            await asyncio.sleep(0.5)
        
        # Stop recording
        await live_page.locator('#recordButton').click()
        
        # Analyze responsiveness
        avg_response = statistics.mean(response_times)
        max_response = max(response_times)
        
        # UI should remain responsive (under 100ms for these operations)
        assert avg_response < 0.1, f"UI too slow on average: {avg_response * 1000:.1f}ms"
        assert max_response < 0.5, f"UI had slow response: {max_response * 1000:.1f}ms"
        
        print(f"UI Responsiveness - Avg: {avg_response * 1000:.1f}ms, Max: {max_response * 1000:.1f}ms")
    
    @pytest.mark.asyncio
    async def test_network_request_performance(self, live_page: Page):
        """Test network request performance and optimization"""
        
        network_logs = []
        
        # Monitor network requests
        live_page.on('request', lambda request: network_logs.append({
            'url': request.url,
            'method': request.method,
            'timestamp': time.time()
        }))
        
        responses = []
        live_page.on('response', lambda response: responses.append({
            'url': response.url,
            'status': response.status,
            'timing': response.request.timing,
            'timestamp': time.time()
        }))
        
        # Perform recording operation
        await live_page.locator('#recordButton').click()
        await asyncio.sleep(5)
        await live_page.locator('#recordButton').click()
        
        # Wait for any pending requests
        await asyncio.sleep(2)
        
        # Analyze network performance
        transcription_requests = [r for r in network_logs if 'transcribe' in r['url'] or 'audio' in r['url']]
        transcription_responses = [r for r in responses if 'transcribe' in r['url'] or 'audio' in r['url']]
        
        if transcription_responses:
            response_times = [r['timing']['responseEnd'] - r['timing']['requestStart'] 
                            for r in transcription_responses if r['timing']]
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                assert avg_response_time < 5000, f"Network requests too slow: {avg_response_time:.1f}ms"
                
                print(f"Network Performance - Avg Response: {avg_response_time:.1f}ms")
        
        print(f"Network Activity - {len(network_logs)} requests, {len(responses)} responses")
    
    @pytest.mark.asyncio
    async def test_cpu_intensive_operations(self, live_page: Page):
        """Test performance during CPU-intensive operations"""
        
        # Enable performance monitoring
        await live_page.evaluate("""
            window.performanceMetrics = {
                start: performance.now(),
                entries: [],
                observer: null
            };
            
            // Monitor long tasks
            if ('PerformanceObserver' in window) {
                window.performanceMetrics.observer = new PerformanceObserver((list) => {
                    list.getEntries().forEach(entry => {
                        if (entry.duration > 50) { // Tasks longer than 50ms
                            window.performanceMetrics.entries.push({
                                name: entry.name,
                                duration: entry.duration,
                                startTime: entry.startTime
                            });
                        }
                    });
                });
                
                try {
                    window.performanceMetrics.observer.observe({entryTypes: ['longtask']});
                } catch(e) {
                    console.log('Long task monitoring not supported');
                }
            }
        """)
        
        # Perform intensive recording session
        await live_page.locator('#recordButton').click()
        
        # Simulate intensive usage
        for i in range(6):  # 30 seconds of recording in 5-second chunks
            await asyncio.sleep(5)
            
            # Check for long tasks
            long_tasks = await live_page.evaluate("() => window.performanceMetrics.entries.length")
            if long_tasks > 10:
                print(f"Warning: {long_tasks} long tasks detected")
        
        await live_page.locator('#recordButton').click()
        
        # Analyze performance metrics
        metrics = await live_page.evaluate("""
            () => ({
                longTasks: window.performanceMetrics.entries,
                totalDuration: performance.now() - window.performanceMetrics.start
            })
        """)
        
        # Check for performance issues
        long_tasks = metrics['longTasks']
        if len(long_tasks) > 0:
            avg_task_duration = statistics.mean(task['duration'] for task in long_tasks)
            max_task_duration = max(task['duration'] for task in long_tasks)
            
            # Long tasks should be minimized
            assert len(long_tasks) < 20, f"Too many long tasks: {len(long_tasks)}"
            assert max_task_duration < 500, f"Task too long: {max_task_duration:.1f}ms"
            
            print(f"Long Tasks - Count: {len(long_tasks)}, Avg: {avg_task_duration:.1f}ms, Max: {max_task_duration:.1f}ms")
    
    @pytest.mark.asyncio
    async def test_data_throughput_performance(self, live_page: Page):
        """Test data processing throughput"""
        
        # Monitor data processing
        processing_stats = []
        
        # Hook into console messages to track processing
        def track_processing(msg):
            if 'processing' in msg.text.lower() or 'chunk' in msg.text.lower():
                processing_stats.append({
                    'message': msg.text,
                    'timestamp': time.time(),
                    'type': msg.type
                })
        
        live_page.on('console', track_processing)
        
        start_time = time.time()
        
        # Start recording
        await live_page.locator('#recordButton').click()
        
        # Record for 15 seconds to generate significant data
        await asyncio.sleep(15)
        
        # Stop recording
        await live_page.locator('#recordButton').click()
        
        total_time = time.time() - start_time
        
        # Analyze throughput
        chunks_processed = len([s for s in processing_stats if 'chunk' in s['message'].lower()])
        if chunks_processed > 0:
            throughput = chunks_processed / total_time
            print(f"Data Throughput - {chunks_processed} chunks in {total_time:.1f}s ({throughput:.1f} chunks/sec)")
            
            # Should process at least 1 chunk per 5 seconds
            assert throughput > 0.2, f"Throughput too low: {throughput:.2f} chunks/sec"
    
    @pytest.mark.asyncio
    async def test_browser_resource_limits(self, live_page: Page):
        """Test behavior approaching browser resource limits"""
        
        # Get initial resource usage
        initial_resources = await live_page.evaluate("""
            () => ({
                memory: performance.memory ? performance.memory.usedJSHeapSize : 0,
                timing: performance.timing ? performance.timing.loadEventEnd - performance.timing.navigationStart : 0,
                resources: performance.getEntriesByType('resource').length
            })
        """)
        
        # Perform resource-intensive operations
        for i in range(15):  # Extended test
            await live_page.locator('#recordButton').click()
            await asyncio.sleep(2)
            await live_page.locator('#recordButton').click()
            
            if i % 5 == 0:  # Check resources every 5 cycles
                resources = await live_page.evaluate("""
                    () => ({
                        memory: performance.memory ? performance.memory.usedJSHeapSize : 0,
                        resources: performance.getEntriesByType('resource').length,
                        errors: window.errorCount || 0
                    })
                """)
                
                # Check we're not hitting critical limits
                if resources['memory'] > 500_000_000:  # 500MB
                    print(f"Warning: High memory usage {resources['memory'] / 1_000_000:.1f}MB")
        
        # Final resource check
        final_resources = await live_page.evaluate("""
            () => ({
                memory: performance.memory ? performance.memory.usedJSHeapSize : 0,
                resources: performance.getEntriesByType('resource').length
            })
        """)
        
        # Should not have crashed or become unresponsive
        is_responsive = await live_page.locator('#recordButton').is_visible()
        assert is_responsive, "Application became unresponsive under resource stress"
        
        print(f"Resource Usage - Initial: {initial_resources['memory'] / 1_000_000:.1f}MB, Final: {final_resources['memory'] / 1_000_000:.1f}MB")


import re  # Add regex import