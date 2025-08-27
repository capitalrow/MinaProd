"""
Mobile-Specific E2E Testing
Testing mobile browser behavior, touch interactions, and mobile-specific features
"""
import pytest
import asyncio
from playwright.async_api import Page, expect

@pytest.mark.mobile
class TestMobileBasicFunctionality:
    """Test basic functionality on mobile devices."""
    
    async def test_mobile_page_loading(self, mobile_page: Page):
        """Test page loading on mobile viewport."""
        page = mobile_page
        
        await page.goto('http://localhost:5000/live')
        
        # Verify mobile-optimized loading
        await expect(page).to_have_title('Live Transcription - Mina')
        
        # Check viewport meta tag is working
        viewport_content = await page.get_attribute('meta[name="viewport"]', 'content')
        assert 'width=device-width' in viewport_content, "Should have responsive viewport"
        
        # Essential mobile elements should be visible
        await expect(page.locator('#recordButton')).to_be_visible()
        await expect(page.locator('#transcript')).to_be_visible()
        await expect(page.locator('#timer')).to_be_visible()
        await expect(page.locator('#wordCount')).to_be_visible()
        
        print("Mobile page loading test passed")
    
    async def test_touch_interactions(self, mobile_page: Page):
        """Test touch-specific interactions."""
        page = mobile_page
        
        await page.goto('http://localhost:5000/live')
        
        # Test touch targets are appropriate size (minimum 44px)
        record_button = page.locator('#recordButton')
        button_box = await record_button.bounding_box()
        
        assert button_box['width'] >= 44, f"Record button width {button_box['width']}px < 44px minimum"
        assert button_box['height'] >= 44, f"Record button height {button_box['height']}px < 44px minimum"
        
        # Test touch interaction
        await record_button.tap()  # Use tap() instead of click() for mobile
        await page.wait_for_timeout(2000)
        
        # Check for visual feedback
        button_classes = await record_button.get_attribute('class')
        print(f"Button classes after tap: {button_classes}")
        
        # Stop recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.tap()
        else:
            await record_button.tap()
        
        print("Touch interaction test completed")
    
    async def test_mobile_orientation_changes(self, mobile_page: Page):
        """Test behavior during orientation changes."""
        page = mobile_page
        
        await page.goto('http://localhost:5000/live')
        
        # Start in portrait
        portrait_viewport = {'width': 375, 'height': 667}
        await page.set_viewport_size(portrait_viewport)
        
        # Start recording
        await page.locator('#recordButton').tap()
        await page.wait_for_timeout(2000)
        
        initial_timer = await page.locator('#timer').text_content()
        
        # Switch to landscape
        landscape_viewport = {'width': 667, 'height': 375}
        await page.set_viewport_size(landscape_viewport)
        await page.wait_for_timeout(1000)
        
        # Check if recording continued
        await expect(page.locator('#recordButton')).to_be_visible()
        await expect(page.locator('#transcript')).to_be_visible()
        
        landscape_timer = await page.locator('#timer').text_content()
        
        # Switch back to portrait
        await page.set_viewport_size(portrait_viewport)
        await page.wait_for_timeout(1000)
        
        final_timer = await page.locator('#timer').text_content()
        
        print(f"Orientation test - Portrait: {initial_timer}, Landscape: {landscape_timer}, Final: {final_timer}")
        
        # Recording should continue through orientation changes
        assert final_timer != '00:00', "Recording should continue through orientation changes"
        
        # Stop recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.tap()
        else:
            await page.locator('#recordButton').tap()
    
    async def test_mobile_microphone_permission(self, mobile_page: Page):
        """Test microphone permission flow on mobile."""
        page = mobile_page
        
        await page.goto('http://localhost:5000/live')
        
        # Monitor console for permission-related messages
        console_messages = []
        page.on('console', lambda msg: console_messages.append(msg.text))
        
        # Attempt to start recording
        await page.locator('#recordButton').tap()
        await page.wait_for_timeout(3000)
        
        # Check for permission-related console messages
        permission_messages = [msg for msg in console_messages if 'permission' in msg.lower() or 'microphone' in msg.lower()]
        
        print(f"Permission-related console messages: {permission_messages}")
        
        # UI should handle permission state appropriately
        await expect(page.locator('#recordButton')).to_be_visible()
        
        # Clean up
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.tap()

@pytest.mark.mobile
class TestMobileSpecificScenarios:
    """Test mobile-specific usage scenarios."""
    
    async def test_mobile_background_recording(self, mobile_page: Page):
        """Test recording behavior when app goes to background."""
        page = mobile_page
        
        await page.goto('http://localhost:5000/live')
        
        # Start recording
        await page.locator('#recordButton').tap()
        await page.wait_for_timeout(2000)
        
        initial_timer = await page.locator('#timer').text_content()
        
        # Simulate app going to background
        await page.evaluate('''
            // Simulate visibility change (app backgrounded)
            Object.defineProperty(document, 'hidden', {value: true, configurable: true});
            document.dispatchEvent(new Event('visibilitychange'));
            
            // Simulate page freeze (mobile browsers often freeze background tabs)
            window.dispatchEvent(new Event('freeze'));
        ''')
        
        await page.wait_for_timeout(3000)
        
        # Simulate app coming back to foreground
        await page.evaluate('''
            Object.defineProperty(document, 'hidden', {value: false, configurable: true});
            document.dispatchEvent(new Event('visibilitychange'));
            window.dispatchEvent(new Event('resume'));
        ''')
        
        await page.wait_for_timeout(1000)
        
        # Check if recording state is maintained
        current_timer = await page.locator('#timer').text_content()
        
        print(f"Background test - Initial: {initial_timer}, After background: {current_timer}")
        
        # Stop recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.tap()
        else:
            await page.locator('#recordButton').tap()
    
    async def test_mobile_scroll_behavior(self, mobile_page: Page):
        """Test scroll behavior during recording."""
        page = mobile_page
        
        await page.goto('http://localhost:5000/live')
        
        # Start recording
        await page.locator('#recordButton').tap()
        await page.wait_for_timeout(1000)
        
        # Simulate scrolling (which might trigger mobile browser behaviors)
        await page.evaluate('''
            window.scrollTo(0, 100);
        ''')
        await page.wait_for_timeout(500)
        
        await page.evaluate('''
            window.scrollTo(0, 0);
        ''')
        await page.wait_for_timeout(500)
        
        # Recording should continue normally
        timer_value = await page.locator('#timer').text_content()
        assert timer_value != '00:00', "Recording should continue during scroll"
        
        # UI elements should remain accessible
        await expect(page.locator('#recordButton')).to_be_visible()
        
        # Stop recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.tap()
        else:
            await page.locator('#recordButton').tap()
    
    async def test_mobile_keyboard_appearance(self, mobile_page: Page):
        """Test behavior when mobile keyboard appears."""
        page = mobile_page
        
        await page.goto('http://localhost:5000/live')
        
        # If there are any input fields, focus them to trigger keyboard
        input_fields = await page.locator('input, textarea').all()
        
        if input_fields:
            # Start recording first
            await page.locator('#recordButton').tap()
            await page.wait_for_timeout(1000)
            
            # Focus input field (would trigger mobile keyboard)
            await input_fields[0].focus()
            await page.wait_for_timeout(1000)
            
            # Check if recording UI is still accessible
            record_button_visible = await page.locator('#recordButton').is_visible()
            transcript_visible = await page.locator('#transcript').is_visible()
            
            print(f"With keyboard - Record button visible: {record_button_visible}, Transcript visible: {transcript_visible}")
            
            # Blur input to hide keyboard
            await input_fields[0].blur()
            await page.wait_for_timeout(500)
            
            # Stop recording
            stop_button = page.locator('#stopButton')
            if await stop_button.is_visible():
                await stop_button.tap()
            else:
                await page.locator('#recordButton').tap()
        else:
            print("No input fields found - skipping keyboard test")
    
    async def test_mobile_network_switching(self, mobile_page: Page):
        """Test behavior during mobile network changes."""
        page = mobile_page
        
        await page.goto('http://localhost:5000/live')
        
        # Start recording
        await page.locator('#recordButton').tap()
        await page.wait_for_timeout(2000)
        
        # Simulate network quality changes (common on mobile)
        # First simulate slow network
        await page.route('**/*', lambda route: self._simulate_mobile_network_delay(route, 800))
        await page.wait_for_timeout(2000)
        
        # Then simulate network recovery
        await page.unroute('**/*')
        await page.wait_for_timeout(1000)
        
        # Recording should handle network changes gracefully
        timer_value = await page.locator('#timer').text_content()
        assert timer_value != '00:00', "Recording should handle network changes"
        
        # Stop recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.tap()
        else:
            await page.locator('#recordButton').tap()
        
        print(f"Mobile network switching test - Final timer: {timer_value}")
    
    async def _simulate_mobile_network_delay(self, route, delay_ms):
        """Helper to simulate mobile network delays."""
        await asyncio.sleep(delay_ms / 1000)
        await route.continue_()

@pytest.mark.mobile
class TestMobileBrowserSpecific:
    """Test mobile browser specific behaviors."""
    
    async def test_ios_safari_specific(self, page: Page):
        """Test iOS Safari specific behaviors."""
        # Create iOS Safari context
        context = await page.context.browser.new_context(
            **page.context.browser.devices['iPhone 13'],
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
        )
        
        ios_page = await context.new_page()
        
        try:
            await ios_page.goto('http://localhost:5000/live')
            
            # iOS Safari specific checks
            # Check viewport handling
            await expect(ios_page.locator('#recordButton')).to_be_visible()
            
            # Test touch interaction
            await ios_page.locator('#recordButton').tap()
            await ios_page.wait_for_timeout(2000)
            
            # Check for iOS-specific issues
            console_errors = []
            ios_page.on('pageerror', lambda err: console_errors.append(str(err)))
            
            await ios_page.wait_for_timeout(3000)
            
            # Should not have iOS-specific errors
            ios_specific_errors = [err for err in console_errors if 'webkit' in err.lower() or 'safari' in err.lower()]
            assert len(ios_specific_errors) == 0, f"iOS Safari errors: {ios_specific_errors}"
            
            # Stop recording
            stop_button = ios_page.locator('#stopButton')
            if await stop_button.is_visible():
                await stop_button.tap()
            else:
                await ios_page.locator('#recordButton').tap()
            
            print("iOS Safari test completed")
            
        finally:
            await context.close()
    
    async def test_android_chrome_specific(self, page: Page):
        """Test Android Chrome specific behaviors."""
        # Create Android Chrome context
        context = await page.context.browser.new_context(
            **page.context.browser.devices['Pixel 5'],
            user_agent='Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36'
        )
        
        android_page = await context.new_page()
        
        try:
            await android_page.goto('http://localhost:5000/live')
            
            # Android Chrome specific checks
            await expect(android_page.locator('#recordButton')).to_be_visible()
            
            # Test touch interaction
            await android_page.locator('#recordButton').tap()
            await android_page.wait_for_timeout(2000)
            
            # Check for Android-specific issues
            console_errors = []
            android_page.on('pageerror', lambda err: console_errors.append(str(err)))
            
            await android_page.wait_for_timeout(3000)
            
            # Should handle Android Chrome behavior properly
            android_specific_errors = [err for err in console_errors if 'chrome' in err.lower() and 'android' in err.lower()]
            assert len(android_specific_errors) == 0, f"Android Chrome errors: {android_specific_errors}"
            
            # Stop recording
            stop_button = android_page.locator('#stopButton')
            if await stop_button.is_visible():
                await stop_button.tap()
            else:
                await android_page.locator('#recordButton').tap()
            
            print("Android Chrome test completed")
            
        finally:
            await context.close()
    
    async def test_mobile_performance_monitoring(self, mobile_page: Page):
        """Monitor performance metrics on mobile."""
        page = mobile_page
        
        await page.goto('http://localhost:5000/live')
        
        # Start performance monitoring
        await page.evaluate('''
            window.performanceData = {
                loadStart: performance.now(),
                interactions: [],
                memoryUsage: performance.memory ? performance.memory.usedJSHeapSize : 0
            };
        ''')
        
        # Perform typical mobile interactions
        await page.locator('#recordButton').tap()
        
        await page.evaluate('''
            window.performanceData.interactions.push({
                action: 'record_start',
                timestamp: performance.now()
            });
        ''')
        
        await page.wait_for_timeout(5000)
        
        # Stop recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.tap()
        else:
            await page.locator('#recordButton').tap()
        
        await page.evaluate('''
            window.performanceData.interactions.push({
                action: 'record_stop',
                timestamp: performance.now()
            });
            window.performanceData.endMemory = performance.memory ? performance.memory.usedJSHeapSize : 0;
        ''')
        
        # Get performance data
        perf_data = await page.evaluate('window.performanceData')
        
        print(f"Mobile performance data: {perf_data}")
        
        # Basic performance assertions
        if perf_data.get('interactions'):
            total_interaction_time = perf_data['interactions'][-1]['timestamp'] - perf_data['interactions'][0]['timestamp']
            assert total_interaction_time > 0, "Should track interaction timing"
            print(f"Total interaction time: {total_interaction_time:.2f}ms")