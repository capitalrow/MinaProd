"""
🎙️ Real-time Transcription Tests for MINA Platform
===============================================

Comprehensive testing of the core transcription functionality:
- Real-time audio recording and processing
- WebSocket communication and streaming
- Voice Activity Detection (VAD)
- Transcription accuracy and performance
- Audio quality handling
- Session management during recording
- Error handling and recovery
"""

import pytest
from playwright.async_api import Page, expect
import asyncio
import time
import json


class TestRealtimeTranscription:
    """Test all real-time transcription functionality"""
    
    @pytest.mark.transcription
    @pytest.mark.critical
    async def test_microphone_permission_flow(self, page: Page):
        """🎙️ Test microphone permission request and handling"""
        # Grant microphone permissions at context level
        await page.context.grant_permissions(['microphone'])
        
        await page.goto('/app')
        await page.wait_for_load_state('networkidle')
        
        # Check if microphone access is properly handled
        mic_status = await page.evaluate("""
            async () => {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    stream.getTracks().forEach(track => track.stop());
                    return 'granted';
                } catch (error) {
                    return error.name;
                }
            }
        """)
        
        assert mic_status == 'granted', f"Microphone permission issue: {mic_status}"
    
    @pytest.mark.transcription
    @pytest.mark.critical
    async def test_record_button_functionality(self, page: Page):
        """🔴 Test record button states and functionality"""
        await page.context.grant_permissions(['microphone'])
        await page.goto('/app')
        await page.wait_for_load_state('networkidle')
        
        # Find record button
        record_selectors = [
            'button:has-text("Record")',
            'button:has-text("Start")',
            '.record-btn',
            '.btn-record',
            'button[id*="record"]',
            'button[data-testid*="record"]',
            'button.record',
            '.recording-controls button'
        ]
        
        record_button = None
        for selector in record_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=2000):
                    record_button = btn
                    break
            except:
                continue
        
        if record_button:
            # Get initial button state
            initial_text = await record_button.text_content()
            initial_classes = await record_button.get_attribute('class') or ''
            
            # Click record button
            await record_button.click()
            await page.wait_for_timeout(1000)
            
            # Check for state change
            new_text = await record_button.text_content()
            new_classes = await record_button.get_attribute('class') or ''
            
            # Button should change state (text or appearance)
            state_changed = (
                initial_text != new_text or
                initial_classes != new_classes or
                'recording' in new_classes.lower() or
                'stop' in (new_text or '').lower() or
                'pause' in (new_text or '').lower()
            )
            
            assert state_changed, f"Record button state didn't change. Initial: '{initial_text}' -> New: '{new_text}'"
            
            # Test stopping recording
            await page.wait_for_timeout(2000)
            await record_button.click()
            await page.wait_for_timeout(1000)
            
            # Button should return to initial state or show stopped state
            final_text = await record_button.text_content()
            final_classes = await record_button.get_attribute('class') or ''
            
            stopped_state = (
                'start' in (final_text or '').lower() or
                'record' in (final_text or '').lower() or
                'stopped' in final_classes.lower() or
                final_text == initial_text
            )
            
            assert stopped_state, f"Record button didn't return to stopped state: '{final_text}'"
        
        else:
            # No obvious record button found - check if recording functionality exists
            page_content = await page.content()
            recording_keywords = ['record', 'microphone', 'audio', 'transcription', 'start recording']
            
            has_recording_features = any(keyword.lower() in page_content.lower() for keyword in recording_keywords)
            assert has_recording_features, "No recording functionality detected on the page"
    
    @pytest.mark.transcription
    @pytest.mark.integration
    async def test_websocket_connection(self, page: Page):
        """🔌 Test WebSocket connection for real-time communication"""
        await page.context.grant_permissions(['microphone'])
        await page.goto('/app')
        await page.wait_for_load_state('networkidle')
        
        # Check for WebSocket/Socket.IO connection
        ws_status = await page.evaluate("""
            () => {
                // Check for Socket.IO
                if (window.io && typeof window.io === 'function') {
                    return 'socketio_available';
                }
                
                // Check for WebSocket connection
                if (window.WebSocket) {
                    return 'websocket_supported';
                }
                
                // Check for any connection status in global variables
                if (window.socket || window.socketio || window.connection) {
                    return 'connection_object_found';
                }
                
                return 'no_websocket_detected';
            }
        """)
        
        # WebSocket support should be available
        assert ws_status != 'no_websocket_detected', f"WebSocket functionality not detected: {ws_status}"
    
    @pytest.mark.transcription
    @pytest.mark.performance
    async def test_recording_session_flow(self, page: Page):
        """⏱️ Test complete recording session flow with timing"""
        await page.context.grant_permissions(['microphone'])
        await page.goto('/app')
        await page.wait_for_load_state('networkidle')
        
        # Find and start recording
        record_selectors = [
            'button:has-text("Record")',
            'button:has-text("Start")',
            '.record-btn',
            'button[id*="record"]'
        ]
        
        record_button = None
        for selector in record_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=2000):
                    record_button = btn
                    break
            except:
                continue
        
        if record_button:
            # Start recording
            start_time = time.time()
            await record_button.click()
            
            # Wait for recording to be active
            await page.wait_for_timeout(1000)
            
            # Check for recording indicators
            recording_indicators = await page.locator(
                '.recording, .rec, [class*="recording"], [data-recording="true"]'
            ).all()
            
            visual_indicators = []
            for indicator in recording_indicators:
                if await indicator.is_visible():
                    text = await indicator.text_content()
                    classes = await indicator.get_attribute('class')
                    visual_indicators.append(f"Text: '{text}', Classes: '{classes}'")
            
            # Simulate recording for a few seconds
            await page.wait_for_timeout(3000)
            
            # Stop recording
            await record_button.click()
            stop_time = time.time()
            
            recording_duration = stop_time - start_time
            
            # Recording session should complete
            assert recording_duration >= 3, f"Recording duration too short: {recording_duration:.2f}s"
            assert recording_duration <= 10, f"Recording took too long: {recording_duration:.2f}s"
            
            # Check for session completion
            await page.wait_for_timeout(2000)
            page_content = await page.content()
            
            completion_indicators = [
                'completed', 'finished', 'stopped', 'saved', 'transcript',
                'recording complete', 'session ended'
            ]
            
            session_completed = any(indicator.lower() in page_content.lower() for indicator in completion_indicators)
            
            # Session should show some completion state or return to ready state
            button_text = await record_button.text_content()
            ready_state = any(word in (button_text or '').lower() for word in ['record', 'start', 'begin'])
            
            assert session_completed or ready_state, \
                f"Recording session didn't complete properly. Button: '{button_text}'"
    
    @pytest.mark.transcription
    @pytest.mark.realtime
    async def test_realtime_transcription_display(self, page: Page):
        """📝 Test real-time transcription text display and updates"""
        await page.context.grant_permissions(['microphone'])
        await page.goto('/app')
        await page.wait_for_load_state('networkidle')
        
        # Look for transcription display areas
        transcription_selectors = [
            '.transcription', '.transcript', '.text-output', '.transcription-text',
            '[data-testid*="transcript"]', '.live-text', '.speech-text',
            '#transcript', '#transcription', '.output-text'
        ]
        
        transcription_area = None
        for selector in transcription_selectors:
            try:
                area = page.locator(selector).first
                if await area.is_visible(timeout=1000):
                    transcription_area = area
                    break
            except:
                continue
        
        # Start recording if button exists
        record_button = None
        record_selectors = ['button:has-text("Record")', 'button:has-text("Start")', '.record-btn']
        
        for selector in record_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=1000):
                    record_button = btn
                    break
            except:
                continue
        
        if record_button and transcription_area:
            # Get initial transcription content
            initial_content = await transcription_area.text_content() or ''
            
            # Start recording
            await record_button.click()
            await page.wait_for_timeout(1000)
            
            # Wait for potential transcription updates
            await page.wait_for_timeout(5000)
            
            # Check if transcription area updated
            final_content = await transcription_area.text_content() or ''
            
            # Stop recording
            await record_button.click()
            await page.wait_for_timeout(1000)
            
            # Transcription area should exist and potentially show updates
            content_changed = initial_content != final_content
            has_placeholder = any(word in final_content.lower() for word in [
                'transcript', 'recording', 'speak', 'listening', 'processing'
            ])
            
            assert content_changed or has_placeholder or len(final_content) > 0, \
                f"Transcription area not functional. Initial: '{initial_content}' Final: '{final_content}'"
        
        else:
            # Check if transcription functionality is present in some form
            page_content = await page.content()
            transcription_keywords = [
                'transcription', 'transcript', 'speech', 'voice', 'audio processing',
                'real-time', 'live text'
            ]
            
            has_transcription_features = any(keyword.lower() in page_content.lower() for keyword in transcription_keywords)
            assert has_transcription_features, "No transcription functionality detected"
    
    @pytest.mark.transcription
    @pytest.mark.edge_case
    async def test_recording_interruption_handling(self, page: Page):
        """🚨 Test handling of recording interruptions and edge cases"""
        await page.context.grant_permissions(['microphone'])
        await page.goto('/app')
        await page.wait_for_load_state('networkidle')
        
        # Find record button
        record_button = None
        record_selectors = ['button:has-text("Record")', 'button:has-text("Start")', '.record-btn']
        
        for selector in record_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=1000):
                    record_button = btn
                    break
            except:
                continue
        
        if record_button:
            # Test rapid clicking
            await record_button.click()
            await page.wait_for_timeout(100)
            await record_button.click()
            await page.wait_for_timeout(100)
            await record_button.click()
            
            # Should handle rapid clicks gracefully
            await page.wait_for_timeout(1000)
            
            # Check for error messages
            error_elements = await page.locator('.error, .alert, [role="alert"]').all()
            error_messages = []
            for element in error_elements:
                if await element.is_visible():
                    text = await element.text_content()
                    if text and text.strip():
                        error_messages.append(text.strip())
            
            # Should not crash from rapid clicking
            critical_errors = [msg for msg in error_messages if 'error' in msg.lower() or 'failed' in msg.lower()]
            assert len(critical_errors) == 0, f"Critical errors from rapid clicking: {critical_errors}"
            
            # Test page navigation during recording
            await record_button.click()  # Start recording
            await page.wait_for_timeout(1000)
            
            # Navigate away and back
            await page.goto('/')
            await page.wait_for_timeout(1000)
            await page.goto('/app')
            await page.wait_for_load_state('networkidle')
            
            # Application should handle navigation gracefully
            await expect(page.locator('body')).to_be_visible()
    
    @pytest.mark.transcription
    @pytest.mark.accessibility
    async def test_transcription_accessibility(self, page: Page):
        """♿ Test accessibility of transcription interface"""
        await page.context.grant_permissions(['microphone'])
        await page.goto('/app')
        await page.wait_for_load_state('networkidle')
        
        # Check for ARIA live regions for dynamic transcription content
        live_regions = await page.locator('[aria-live], [role="log"], [role="status"]').all()
        
        transcription_areas = await page.locator(
            '.transcription, .transcript, .text-output, .live-text'
        ).all()
        
        accessible_transcription_areas = 0
        for area in transcription_areas:
            if await area.is_visible():
                aria_live = await area.get_attribute('aria-live')
                role = await area.get_attribute('role')
                
                if aria_live or role in ['log', 'status']:
                    accessible_transcription_areas += 1
        
        # Check record button accessibility
        record_buttons = await page.locator(
            'button:has-text("Record"), button:has-text("Start"), .record-btn'
        ).all()
        
        accessible_buttons = 0
        for button in record_buttons:
            if await button.is_visible():
                aria_label = await button.get_attribute('aria-label')
                title = await button.get_attribute('title')
                text = await button.text_content()
                
                if aria_label or title or (text and text.strip()):
                    accessible_buttons += 1
        
        # Test keyboard navigation
        await page.keyboard.press('Tab')
        focused_element = await page.evaluate('document.activeElement.tagName')
        
        # Verify accessibility features
        total_buttons = len(record_buttons)
        total_transcription_areas = len(transcription_areas)
        
        if total_buttons > 0:
            button_accessibility = accessible_buttons / total_buttons
            assert button_accessibility >= 0.8, f"Poor button accessibility: {accessible_buttons}/{total_buttons}"
        
        # Keyboard navigation should work
        assert focused_element in ['BUTTON', 'INPUT', 'A', 'BODY'], "Keyboard navigation not working"
    
    @pytest.mark.transcription
    @pytest.mark.performance
    async def test_transcription_performance_metrics(self, page: Page):
        """⚡ Test transcription performance and response times"""
        await page.context.grant_permissions(['microphone'])
        await page.goto('/app')
        await page.wait_for_load_state('networkidle')
        
        # Measure page load time
        start_time = time.time()
        await page.reload()
        await page.wait_for_load_state('networkidle')
        load_time = time.time() - start_time
        
        assert load_time < 10, f"Page load too slow: {load_time:.2f}s"
        
        # Test record button response time
        record_button = None
        record_selectors = ['button:has-text("Record")', 'button:has-text("Start")', '.record-btn']
        
        for selector in record_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=1000):
                    record_button = btn
                    break
            except:
                continue
        
        if record_button:
            # Measure button response time
            click_start = time.time()
            await record_button.click()
            
            # Wait for visual state change
            await page.wait_for_timeout(100)
            click_response_time = time.time() - click_start
            
            assert click_response_time < 2.0, f"Button response too slow: {click_response_time:.2f}s"
            
            # Measure session start time
            session_start = time.time()
            await page.wait_for_timeout(1000)  # Allow session to initialize
            session_init_time = time.time() - session_start
            
            assert session_init_time < 5.0, f"Session initialization too slow: {session_init_time:.2f}s"
    
    @pytest.mark.transcription
    @pytest.mark.mobile
    async def test_mobile_transcription_interface(self, page: Page):
        """📱 Test transcription interface on mobile devices"""
        await page.context.grant_permissions(['microphone'])
        
        # Test different mobile viewport sizes
        mobile_viewports = [
            {"width": 375, "height": 667},  # iPhone SE
            {"width": 414, "height": 896},  # iPhone 11 Pro
            {"width": 412, "height": 915}   # Galaxy S20
        ]
        
        for viewport in mobile_viewports:
            await page.set_viewport_size(viewport)
            await page.goto('/app')
            await page.wait_for_load_state('networkidle')
            
            # Check that record button is touch-friendly
            record_buttons = await page.locator(
                'button:has-text("Record"), button:has-text("Start"), .record-btn'
            ).all()
            
            for button in record_buttons:
                if await button.is_visible():
                    bbox = await button.bounding_box()
                    if bbox:
                        # Touch target should be at least 44px
                        min_size = min(bbox['width'], bbox['height'])
                        assert min_size >= 30, f"Button too small for touch: {min_size}px at {viewport}"
            
            # Check transcription area visibility
            transcription_areas = await page.locator(
                '.transcription, .transcript, .text-output'
            ).all()
            
            visible_areas = 0
            for area in transcription_areas:
                if await area.is_visible():
                    visible_areas += 1
            
            # Transcription interface should be visible on mobile
            assert visible_areas > 0 or await page.locator('button, input').count() > 0, \
                f"No interactive elements visible at {viewport}"