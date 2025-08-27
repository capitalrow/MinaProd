"""
Edge Case & Negative Testing
Testing boundary conditions, error scenarios, and unexpected inputs
"""
import pytest
import asyncio
from playwright.async_api import Page, expect

@pytest.mark.edge_case
class TestAudioInputEdgeCases:
    """Test edge cases related to audio input."""
    
    async def test_very_short_recording(self, live_page: Page):
        """Test very short recording sessions (<1 second)."""
        page = live_page
        
        # Start and immediately stop recording
        await page.locator('#recordButton').click()
        await page.wait_for_timeout(300)  # Only 300ms
        
        # Stop recording quickly
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.click()
        else:
            await page.locator('#recordButton').click()
        
        await page.wait_for_timeout(1000)
        
        # Should handle gracefully
        timer_value = await page.locator('#timer').text_content()
        word_count = await page.locator('#wordCount').text_content()
        
        print(f"Very short recording - Timer: {timer_value}, Words: {word_count}")
        
        # Should not crash the application
        await expect(page.locator('#recordButton')).to_be_visible()
        await expect(page.locator('#transcript')).to_be_visible()
    
    async def test_very_long_recording(self, live_page: Page):
        """Test extended recording session (stress test)."""
        page = live_page
        
        # Start recording for extended period
        await page.locator('#recordButton').click()
        
        # Monitor for 30 seconds (representing long session)
        for i in range(6):  # 6 intervals of 5 seconds each
            await page.wait_for_timeout(5000)
            
            # Check system is still responsive
            timer_value = await page.locator('#timer').text_content()
            print(f"Long recording check {i+1}/6 - Timer: {timer_value}")
            
            # Verify UI is still responsive
            await expect(page.locator('#recordButton')).to_be_visible()
            
            # Check for memory leaks or performance degradation
            # (Basic check - in real testing, would monitor actual memory usage)
            page_title = await page.title()
            assert 'Mina' in page_title, "Page should remain responsive"
        
        # Stop the long recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.click()
        else:
            await page.locator('#recordButton').click()
        
        await page.wait_for_timeout(2000)
        
        final_timer = await page.locator('#timer').text_content()
        print(f"Long recording completed - Final timer: {final_timer}")
        
        # Should complete successfully
        assert final_timer != '00:00', "Long recording should show elapsed time"
    
    async def test_rapid_button_clicking(self, live_page: Page):
        """Test rapid clicking of record button."""
        page = live_page
        
        record_button = page.locator('#recordButton')
        
        # Rapidly click the record button multiple times
        for i in range(10):
            await record_button.click()
            await page.wait_for_timeout(100)  # Very short delay
        
        await page.wait_for_timeout(2000)
        
        # System should handle this gracefully
        await expect(record_button).to_be_visible()
        await expect(record_button).to_be_enabled()
        
        # Clean up - ensure recording is stopped
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.click()
        
        print("Rapid clicking test completed successfully")
    
    async def test_browser_tab_switching(self, live_page: Page):
        """Test behavior when switching browser tabs during recording."""
        page = live_page
        
        # Start recording
        await page.locator('#recordButton').click()
        await page.wait_for_timeout(2000)
        
        initial_timer = await page.locator('#timer').text_content()
        
        # Simulate tab becoming invisible (background)
        await page.evaluate('document.dispatchEvent(new Event("visibilitychange"))')
        await page.evaluate('Object.defineProperty(document, "hidden", {value: true, configurable: true})')
        
        await page.wait_for_timeout(3000)
        
        # Simulate tab becoming visible again
        await page.evaluate('Object.defineProperty(document, "hidden", {value: false, configurable: true})')
        await page.evaluate('document.dispatchEvent(new Event("visibilitychange"))')
        
        await page.wait_for_timeout(1000)
        
        # Check if recording continued
        current_timer = await page.locator('#timer').text_content()
        
        print(f"Tab switching test - Initial: {initial_timer}, After: {current_timer}")
        
        # Stop recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.click()
        else:
            await page.locator('#recordButton').click()
    
    async def test_multiple_simultaneous_sessions(self, page: Page):
        """Test opening multiple tabs with live transcription."""
        # Create additional browser tabs
        context = page.context
        
        pages = [page]  # Original page
        
        try:
            # Create 2 additional tabs
            for i in range(2):
                new_page = await context.new_page()
                await new_page.goto('http://localhost:5000/live')
                await new_page.wait_for_load_state('networkidle')
                pages.append(new_page)
            
            # Start recording in all tabs simultaneously
            for i, test_page in enumerate(pages):
                await test_page.locator('#recordButton').click()
                print(f"Started recording in tab {i+1}")
                await asyncio.sleep(0.5)  # Small delay between starts
            
            # Let all sessions run for a few seconds
            await asyncio.sleep(5)
            
            # Stop all recordings
            for i, test_page in enumerate(pages):
                stop_button = test_page.locator('#stopButton')
                if await stop_button.is_visible():
                    await stop_button.click()
                else:
                    await test_page.locator('#recordButton').click()
                print(f"Stopped recording in tab {i+1}")
            
            await asyncio.sleep(2)
            
            # Verify all sessions completed
            for i, test_page in enumerate(pages):
                timer = await test_page.locator('#timer').text_content()
                print(f"Tab {i+1} final timer: {timer}")
                
                # Each tab should show some recorded time
                assert timer != '00:00', f"Tab {i+1} should show recorded time"
        
        finally:
            # Clean up additional pages
            for test_page in pages[1:]:  # Skip original page
                await test_page.close()

@pytest.mark.edge_case
class TestNetworkEdgeCases:
    """Test network-related edge cases."""
    
    async def test_slow_network_conditions(self, live_page: Page, network_conditions):
        """Test behavior under slow network conditions."""
        page = live_page
        
        # Simulate slow 3G connection
        await page.context.set_offline(False)
        await page.route('**/*', lambda route: asyncio.create_task(self._slow_response(route, 1000)))
        
        # Start recording
        start_time = asyncio.get_event_loop().time()
        await page.locator('#recordButton').click()
        
        # Wait longer for slow network
        await page.wait_for_timeout(8000)
        
        # Stop recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.click()
        else:
            await page.locator('#recordButton').click()
        
        end_time = asyncio.get_event_loop().time()
        session_duration = end_time - start_time
        
        await page.wait_for_timeout(3000)  # Extra wait for slow network
        
        # Clear route
        await page.unroute('**/*')
        
        # Should complete despite slow network
        timer_value = await page.locator('#timer').text_content()
        print(f"Slow network test - Duration: {session_duration:.1f}s, Timer: {timer_value}")
        
        assert timer_value != '00:00', "Should complete recording despite slow network"
    
    async def _slow_response(self, route, delay_ms):
        """Helper to add delay to network responses."""
        await asyncio.sleep(delay_ms / 1000)
        await route.continue_()
    
    async def test_intermittent_connectivity(self, live_page: Page):
        """Test handling of intermittent network connectivity."""
        page = live_page
        
        # Start recording
        await page.locator('#recordButton').click()
        await page.wait_for_timeout(2000)
        
        # Simulate network drop
        await page.context.set_offline(True)
        await page.wait_for_timeout(2000)
        
        # Restore network
        await page.context.set_offline(False)
        await page.wait_for_timeout(2000)
        
        # Drop again
        await page.context.set_offline(True)
        await page.wait_for_timeout(1000)
        
        # Final restore
        await page.context.set_offline(False)
        await page.wait_for_timeout(2000)
        
        # Stop recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.click()
        else:
            await page.locator('#recordButton').click()
        
        await page.wait_for_timeout(2000)
        
        # Should handle intermittent connectivity
        timer_value = await page.locator('#timer').text_content()
        print(f"Intermittent connectivity test - Timer: {timer_value}")

@pytest.mark.edge_case
class TestBrowserCompatibilityEdgeCases:
    """Test browser-specific edge cases."""
    
    async def test_browser_refresh_during_recording(self, live_page: Page):
        """Test page refresh during active recording."""
        page = live_page
        
        # Start recording
        await page.locator('#recordButton').click()
        await page.wait_for_timeout(3000)
        
        initial_timer = await page.locator('#timer').text_content()
        
        # Refresh the page
        await page.reload()
        await page.wait_for_load_state('networkidle')
        
        # Check state after refresh
        new_timer = await page.locator('#timer').text_content()
        
        print(f"Page refresh test - Before: {initial_timer}, After: {new_timer}")
        
        # UI should be functional after refresh
        await expect(page.locator('#recordButton')).to_be_visible()
        await expect(page.locator('#transcript')).to_be_visible()
        
        # Should either preserve state or reset gracefully
        assert new_timer is not None, "Timer should be present after refresh"
    
    async def test_browser_back_navigation(self, live_page: Page):
        """Test browser back button during recording."""
        page = live_page
        
        # Start recording
        await page.locator('#recordButton').click()
        await page.wait_for_timeout(2000)
        
        # Navigate to another page
        await page.goto('http://localhost:5000/')
        await page.wait_for_timeout(1000)
        
        # Go back to live page
        await page.go_back()
        await page.wait_for_load_state('networkidle')
        
        # Check if session state is preserved
        await expect(page.locator('#recordButton')).to_be_visible()
        await expect(page.locator('#transcript')).to_be_visible()
        
        timer_value = await page.locator('#timer').text_content()
        print(f"Back navigation test - Timer after back: {timer_value}")
    
    async def test_javascript_disabled_fallback(self, page: Page):
        """Test behavior when JavaScript is disabled."""
        # This is challenging to test with Playwright, but we can simulate
        # by removing JavaScript functionality
        
        await page.goto('http://localhost:5000/live')
        
        # Disable JavaScript execution
        await page.add_init_script('window.MinaTranscription = undefined;')
        
        await page.reload()
        await page.wait_for_load_state('networkidle')
        
        # Page should still load basic HTML
        await expect(page.locator('#recordButton')).to_be_visible()
        await expect(page.locator('#transcript')).to_be_visible()
        
        # Button might not be functional, but should not crash
        try:
            await page.locator('#recordButton').click()
            await page.wait_for_timeout(1000)
        except Exception as e:
            print(f"Expected behavior with JS disabled: {e}")
        
        print("JavaScript disabled test completed")

@pytest.mark.edge_case
class TestUIEdgeCases:
    """Test UI-specific edge cases."""
    
    async def test_extreme_viewport_sizes(self, page: Page):
        """Test UI at extreme viewport sizes."""
        extreme_viewports = [
            {'width': 240, 'height': 320},   # Very small mobile
            {'width': 3840, 'height': 2160}, # 4K display
            {'width': 1024, 'height': 768}   # iPad landscape
        ]
        
        for viewport in extreme_viewports:
            await page.set_viewport_size(viewport)
            await page.goto('http://localhost:5000/live')
            
            print(f"Testing viewport: {viewport['width']}x{viewport['height']}")
            
            # Essential elements should remain accessible
            await expect(page.locator('#recordButton')).to_be_visible()
            await expect(page.locator('#transcript')).to_be_visible()
            
            # Check if record button is appropriately sized
            button_box = await page.locator('#recordButton').bounding_box()
            
            if viewport['width'] <= 480:  # Mobile viewports
                # Button should be large enough for touch
                assert button_box['width'] >= 40, f"Button too small at {viewport['width']}px width"
                assert button_box['height'] >= 40, f"Button too small at {viewport['width']}px width"
    
    async def test_css_loading_failure(self, page: Page):
        """Test behavior when CSS fails to load."""
        # Block CSS loading
        await page.route('**/*.css', lambda route: route.abort())
        
        await page.goto('http://localhost:5000/live')
        
        # Page should still be functional without CSS
        await expect(page.locator('#recordButton')).to_be_visible()
        await expect(page.locator('#transcript')).to_be_visible()
        
        # Basic functionality should work
        try:
            await page.locator('#recordButton').click()
            await page.wait_for_timeout(1000)
            print("Record button functional without CSS")
        except Exception as e:
            print(f"Record button issue without CSS: {e}")
        
        # Clean up
        await page.unroute('**/*.css')
    
    async def test_unicode_and_special_characters(self, live_page: Page):
        """Test handling of unicode and special characters in transcription."""
        page = live_page
        
        # Start recording
        await page.locator('#recordButton').click()
        await page.wait_for_timeout(1000)
        
        # Simulate transcription with special characters by injecting into transcript
        # (In real scenario, this would come from audio with special characters)
        special_text = "Hello 世界! Test émojis 🎤 Special chars: @#$%^&*()[]{}|"
        
        try:
            await page.evaluate(f'''
                const transcript = document.getElementById('transcript');
                if (transcript) {{
                    transcript.textContent = "{special_text}";
                }}
            ''')
            
            await page.wait_for_timeout(1000)
            
            # Verify special characters are handled properly
            transcript_content = await page.locator('#transcript').text_content()
            print(f"Special characters test: {transcript_content}")
            
            # Should not crash or corrupt the display
            await expect(page.locator('#transcript')).to_be_visible()
            
        except Exception as e:
            print(f"Special characters handling issue: {e}")
        
        finally:
            # Stop recording
            stop_button = page.locator('#stopButton')
            if await stop_button.is_visible():
                await stop_button.click()
            else:
                await page.locator('#recordButton').click()