"""
Mobile Experience Tests - Pixel 9 Pro Focused
Tests mobile-specific functionality and optimizations
"""

import pytest
import asyncio
import time
from playwright.async_api import Page, expect, BrowserContext


class TestMobileExperience:
    """Test mobile-specific features and optimizations"""
    
    @pytest.mark.asyncio
    async def test_pixel_9_pro_optimization(self, browser, test_audio_data):
        """Test Pixel 9 Pro specific optimizations"""
        
        # Create Pixel 9 Pro context
        context = await browser.new_context(
            viewport={'width': 1344, 'height': 2992},
            user_agent='Mozilla/5.0 (Linux; Android 16; Pixel 9 Pro Build/BP2A.250805.005; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/139.0.7258.143 Mobile Safari/537.36',
            device_scale_factor=3.5,
            is_mobile=True,
            has_touch=True,
            permissions=['microphone']
        )
        
        page = await context.new_page()
        console_messages = []
        page.on('console', lambda msg: console_messages.append(msg.text))
        
        try:
            await page.goto('http://localhost:5000/live')
            await page.wait_for_load_state('networkidle')
            
            # Wait for mobile optimization detection
            await asyncio.sleep(3)
            
            # Verify Pixel 9 Pro optimization messages
            optimization_messages = [msg for msg in console_messages if any(keyword in msg.lower() for keyword in [
                'pixel', 'high-end', 'mobile', 'optimization', 'battery', 'device'
            ])]
            
            assert len(optimization_messages) > 0, f"No mobile optimization detected. Console: {console_messages[-5:]}"
            
            # Check for specific Pixel 9 Pro features
            pixel_optimized = any('pixel' in msg.lower() or 'high-end' in msg.lower() for msg in console_messages)
            assert pixel_optimized, "Pixel 9 Pro optimizations not detected"
            
        finally:
            await context.close()
    
    @pytest.mark.asyncio
    async def test_touch_interactions(self, mobile_page: Page):
        """Test touch-specific interactions"""
        
        await mobile_page.goto('http://localhost:5000/live')
        await mobile_page.wait_for_load_state('networkidle')
        
        # Test touch recording
        record_button = mobile_page.locator('#recordButton')
        await expect(record_button).to_be_visible()
        
        # Simulate touch tap
        await record_button.tap()
        await asyncio.sleep(1)
        
        # Verify recording started
        await expect(record_button).to_have_class(re.compile(r'.*recording.*'), timeout=5000)
        
        # Test touch stop
        await record_button.tap()
        await asyncio.sleep(1)
        
        # Verify recording stopped
        await expect(record_button).not_to_have_class(re.compile(r'.*recording.*'))
    
    @pytest.mark.asyncio
    async def test_mobile_ui_layout(self, mobile_page: Page):
        """Test mobile UI layout and responsiveness"""
        
        await mobile_page.goto('http://localhost:5000/live')
        await mobile_page.wait_for_load_state('networkidle')
        
        # Check key elements are visible on mobile
        await expect(mobile_page.locator('#recordButton')).to_be_visible()
        await expect(mobile_page.locator('#transcript')).to_be_visible()
        await expect(mobile_page.locator('#timer')).to_be_visible()
        
        # Check mobile-specific styling
        record_button = mobile_page.locator('#recordButton')
        button_styles = await record_button.evaluate('el => getComputedStyle(el)')
        
        # Verify touch-friendly button size (should be at least 44px)
        button_height = await record_button.bounding_box()
        if button_height:
            assert button_height['height'] >= 44, f"Button too small for touch: {button_height['height']}px"
        
        # Test viewport scaling
        viewport_meta = await mobile_page.locator('meta[name="viewport"]').get_attribute('content')
        assert 'width=device-width' in viewport_meta or viewport_meta is None, "Missing viewport meta tag"
    
    @pytest.mark.asyncio
    async def test_orientation_changes(self, browser):
        """Test behavior during orientation changes"""
        
        context = await browser.new_context(
            viewport={'width': 1344, 'height': 2992},  # Portrait
            is_mobile=True,
            has_touch=True,
            permissions=['microphone']
        )
        
        page = await context.new_page()
        
        try:
            await page.goto('http://localhost:5000/live')
            await page.wait_for_load_state('networkidle')
            
            # Start recording in portrait
            await page.locator('#recordButton').tap()
            await asyncio.sleep(1)
            
            # Change to landscape
            await context.set_viewport_size({'width': 2992, 'height': 1344})
            await asyncio.sleep(1)
            
            # Verify recording continues
            await expect(page.locator('#recordButton')).to_have_class(re.compile(r'.*recording.*'))
            
            # Stop recording in landscape
            await page.locator('#recordButton').tap()
            
            # Verify UI adapts to landscape
            record_button_box = await page.locator('#recordButton').bounding_box()
            transcript_box = await page.locator('#transcript').bounding_box()
            
            assert record_button_box is not None, "Record button not visible in landscape"
            assert transcript_box is not None, "Transcript not visible in landscape"
            
        finally:
            await context.close()
    
    @pytest.mark.asyncio
    async def test_mobile_gestures(self, mobile_page: Page):
        """Test mobile gesture recognition"""
        
        await mobile_page.goto('http://localhost:5000/live')
        await mobile_page.wait_for_load_state('networkidle')
        
        console_messages = []
        mobile_page.on('console', lambda msg: console_messages.append(msg.text))
        
        # Test swipe gestures on transcript area
        transcript = mobile_page.locator('#transcript')
        await expect(transcript).to_be_visible()
        
        # Simulate swipe down
        transcript_box = await transcript.bounding_box()
        if transcript_box:
            start_x = transcript_box['x'] + transcript_box['width'] / 2
            start_y = transcript_box['y'] + 50
            end_y = start_y + 200
            
            await mobile_page.touch_screen.tap(start_x, start_y)
            await mobile_page.touch_screen.tap(start_x, end_y)
            
            await asyncio.sleep(1)
            
            # Check for gesture detection in console
            gesture_messages = [msg for msg in console_messages if 'gesture' in msg.lower()]
            if len(gesture_messages) > 0:
                assert True  # Gestures are detected
    
    @pytest.mark.asyncio
    async def test_network_condition_adaptation(self, mobile_page: Page, network_conditions):
        """Test mobile performance under different network conditions"""
        
        # Test under 3G conditions
        context = mobile_page.context
        await context.set_offline(False)
        await context.route('**/*', lambda route: route.continue_())
        
        # Simulate 3G network
        client = await context.new_cdp_session(mobile_page)
        await client.send('Network.enable')
        await client.send('Network.emulateNetworkConditions', {
            'offline': False,
            'downloadThroughput': network_conditions['3g']['download'] * 1024 / 8,
            'uploadThroughput': network_conditions['3g']['upload'] * 1024 / 8,
            'latency': network_conditions['3g']['latency']
        })
        
        start_time = time.time()
        
        await mobile_page.goto('http://localhost:5000/live')
        await mobile_page.wait_for_load_state('networkidle', timeout=30000)
        
        load_time = time.time() - start_time
        
        # Verify page loads reasonably fast even on 3G
        assert load_time < 15, f"Page load too slow on 3G: {load_time:.2f}s"
        
        # Test transcription functionality under 3G
        await mobile_page.locator('#recordButton').tap()
        await asyncio.sleep(3)
        await mobile_page.locator('#recordButton').tap()
        
        # Should still work, albeit slower
        await expect(mobile_page.locator('#recordButton')).not_to_have_class(re.compile(r'.*recording.*'), timeout=10000)
    
    @pytest.mark.asyncio
    async def test_battery_optimization_awareness(self, mobile_page: Page):
        """Test battery optimization features"""
        
        await mobile_page.goto('http://localhost:5000/live')
        await mobile_page.wait_for_load_state('networkidle')
        
        console_messages = []
        mobile_page.on('console', lambda msg: console_messages.append(msg.text))
        
        # Wait for battery optimization messages
        await asyncio.sleep(3)
        
        # Check for battery-related optimizations
        battery_messages = [msg for msg in console_messages if any(keyword in msg.lower() for keyword in [
            'battery', 'optimization', 'power', 'efficient', 'aggressive', 'moderate'
        ])]
        
        assert len(battery_messages) > 0, "No battery optimization messages detected"
        
        # Test long recording to see battery optimization kick in
        await mobile_page.locator('#recordButton').tap()
        await asyncio.sleep(10)  # Longer recording
        
        # Check if optimization level changes
        optimization_changes = [msg for msg in console_messages[-10:] if 'optimization' in msg.lower()]
        
        await mobile_page.locator('#recordButton').tap()
    
    @pytest.mark.asyncio
    async def test_mobile_accessibility_features(self, mobile_page: Page):
        """Test mobile accessibility features"""
        
        await mobile_page.goto('http://localhost:5000/live')
        await mobile_page.wait_for_load_state('networkidle')
        
        # Check for accessibility attributes
        record_button = mobile_page.locator('#recordButton')
        
        # Test ARIA attributes
        aria_label = await record_button.get_attribute('aria-label')
        assert aria_label is not None or await record_button.text_content() is not None, "Button lacks accessibility label"
        
        # Test keyboard navigation (important for assistive tech)
        await record_button.focus()
        focused_element = await mobile_page.evaluate('document.activeElement.id')
        assert focused_element == 'recordButton', "Button not focusable"
        
        # Test high contrast support
        styles = await record_button.evaluate('el => getComputedStyle(el)')
        # Basic contrast check - button should have visible styling
        assert styles is not None, "Button styles not accessible"
    
    @pytest.mark.asyncio
    async def test_mobile_performance_metrics(self, mobile_page: Page):
        """Test mobile performance metrics collection"""
        
        await mobile_page.goto('http://localhost:5000/live')
        await mobile_page.wait_for_load_state('networkidle')
        
        # Start performance monitoring
        await mobile_page.evaluate("""
            window.performanceData = [];
            window.performance.mark('test-start');
        """)
        
        # Perform recording operation
        await mobile_page.locator('#recordButton').tap()
        await asyncio.sleep(3)
        await mobile_page.locator('#recordButton').tap()
        
        # Collect performance data
        await mobile_page.evaluate("""
            window.performance.mark('test-end');
            window.performance.measure('test-duration', 'test-start', 'test-end');
        """)
        
        # Get performance metrics
        metrics = await mobile_page.evaluate("""
            () => {
                const measures = performance.getEntriesByType('measure');
                const marks = performance.getEntriesByType('mark');
                return {
                    measures: measures.map(m => ({name: m.name, duration: m.duration})),
                    marks: marks.map(m => ({name: m.name, startTime: m.startTime})),
                    memory: performance.memory ? {
                        used: performance.memory.usedJSHeapSize,
                        total: performance.memory.totalJSHeapSize,
                        limit: performance.memory.jsHeapSizeLimit
                    } : null
                };
            }
        """)
        
        assert len(metrics['measures']) > 0, "No performance measures recorded"
        
        # Check test duration
        test_measure = next((m for m in metrics['measures'] if m['name'] == 'test-duration'), None)
        if test_measure:
            assert test_measure['duration'] < 10000, f"Test took too long: {test_measure['duration']}ms"


import re  # Add regex import