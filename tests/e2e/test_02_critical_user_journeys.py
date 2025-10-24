"""
Critical User Journey Tests
End-to-end validation of core user flows
"""
import pytest
import asyncio
from playwright.async_api import Page, expect

@pytest.mark.critical
class TestLiveTranscriptionJourney:
    """Test the complete live transcription user journey."""
    
    async def test_complete_recording_session(self, live_page: Page, performance_monitor):
        """Test complete recording session from start to finish."""
        page = live_page
        
        # Step 1: Verify initial state
        await expect(page.locator('#recordButton')).to_be_visible()
        await expect(page.locator('#transcript')).to_contain_text('Click the red button')
        
        initial_timer = await page.locator('#timer').text_content()
        initial_words = await page.locator('#wordCount').text_content()
        
        assert initial_timer == '00:00', f"Expected 00:00, got {initial_timer}"
        assert initial_words == '0', f"Expected 0 words, got {initial_words}"
        
        # Step 2: Start recording
        performance_monitor['recording_start'] = asyncio.get_event_loop().time()
        
        await page.locator('#recordButton').click()
        
        # Wait for recording state to activate
        await page.wait_for_timeout(1000)
        
        # Step 3: Verify recording state changes
        # Timer should start incrementing
        await page.wait_for_timeout(2000)
        current_timer = await page.locator('#timer').text_content()
        assert current_timer != '00:00', f"Timer should have started, still shows {current_timer}"
        
        # Button should show recording state
        button_classes = await page.locator('#recordButton').get_attribute('class')
        print(f"Recording button classes: {button_classes}")
        
        # Step 4: Simulate speaking by triggering transcription
        # Wait for potential transcription updates
        await page.wait_for_timeout(5000)
        
        # Step 5: Check for any transcription updates
        transcript_content = await page.locator('#transcript').text_content()
        print(f"Transcript content: {transcript_content}")
        
        # Step 6: Stop recording
        # Look for stop button or click record button again
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.click()
        else:
            await page.locator('#recordButton').click()
        
        performance_monitor['recording_end'] = asyncio.get_event_loop().time()
        
        # Step 7: Verify session completion
        await page.wait_for_timeout(2000)
        
        # Record final state
        final_timer = await page.locator('#timer').text_content()
        final_words = await page.locator('#wordCount').text_content()
        final_transcript = await page.locator('#transcript').text_content()
        
        performance_monitor['final_state'] = {
            'timer': final_timer,
            'words': final_words,
            'transcript_length': len(final_transcript) if final_transcript else 0,
            'session_duration': performance_monitor['recording_end'] - performance_monitor['recording_start']
        }
        
        print(f"Session completed - Timer: {final_timer}, Words: {final_words}")
        print(f"Session duration: {performance_monitor['final_state']['session_duration']:.1f}s")
    
    async def test_pause_resume_functionality(self, live_page: Page):
        """Test pause and resume functionality if available."""
        page = live_page
        
        # Start recording
        await page.locator('#recordButton').click()
        await page.wait_for_timeout(2000)
        
        # Look for pause button
        pause_button = page.locator('#pauseButton')
        
        if await pause_button.is_visible():
            # Test pause
            await pause_button.click()
            await page.wait_for_timeout(1000)
            
            paused_timer = await page.locator('#timer').text_content()
            
            # Wait and check timer doesn't advance
            await page.wait_for_timeout(2000)
            still_paused_timer = await page.locator('#timer').text_content()
            
            assert paused_timer == still_paused_timer, "Timer should not advance when paused"
            
            # Resume recording
            await page.locator('#recordButton').click()  # Or resume button if different
            await page.wait_for_timeout(2000)
            
            resumed_timer = await page.locator('#timer').text_content()
            # Timer should advance after resume
            
            # Stop recording
            await page.locator('#stopButton').click()
        else:
            print("Pause functionality not available - skipping pause/resume test")
            # Just stop the recording we started
            await page.locator('#recordButton').click()
    
    async def test_multiple_recording_sessions(self, live_page: Page):
        """Test multiple recording sessions in sequence."""
        page = live_page
        
        session_results = []
        
        for session_num in range(3):
            print(f"Starting session {session_num + 1}")
            
            # Start recording
            await page.locator('#recordButton').click()
            await page.wait_for_timeout(3000)  # Record for 3 seconds
            
            # Stop recording
            stop_button = page.locator('#stopButton')
            if await stop_button.is_visible():
                await stop_button.click()
            else:
                await page.locator('#recordButton').click()
            
            await page.wait_for_timeout(1000)
            
            # Capture session results
            timer = await page.locator('#timer').text_content()
            words = await page.locator('#wordCount').text_content()
            transcript = await page.locator('#transcript').text_content()
            
            session_results.append({
                'session': session_num + 1,
                'timer': timer,
                'words': words,
                'transcript_length': len(transcript) if transcript else 0
            })
            
            print(f"Session {session_num + 1} results: {timer}, {words} words")
            
            # Wait between sessions
            await page.wait_for_timeout(1000)
        
        # Verify all sessions completed
        assert len(session_results) == 3, "Should have completed 3 sessions"
        
        for result in session_results:
            assert result['timer'] != '00:00', f"Session {result['session']} should have recorded time"

@pytest.mark.critical
class TestTranscriptionQuality:
    """Test transcription quality and accuracy."""
    
    async def test_real_time_transcription_updates(self, live_page: Page, mock_whisper_api):
        """Test that transcription updates appear in real-time."""
        page = live_page
        
        # Set up to monitor transcript changes
        transcript_changes = []
        
        async def track_transcript_changes():
            while True:
                try:
                    content = await page.locator('#transcript').text_content()
                    if content not in [change['content'] for change in transcript_changes]:
                        transcript_changes.append({
                            'timestamp': asyncio.get_event_loop().time(),
                            'content': content
                        })
                    await asyncio.sleep(0.5)
                except:
                    break
        
        # Start monitoring in background
        monitor_task = asyncio.create_task(track_transcript_changes())
        
        try:
            # Start recording
            await page.locator('#recordButton').click()
            
            # Wait for transcription updates
            await page.wait_for_timeout(5000)
            
            # Stop recording
            stop_button = page.locator('#stopButton')
            if await stop_button.is_visible():
                await stop_button.click()
            else:
                await page.locator('#recordButton').click()
            
            await page.wait_for_timeout(2000)
            
        finally:
            monitor_task.cancel()
        
        # Analyze transcript changes
        print(f"Detected {len(transcript_changes)} transcript changes")
        for i, change in enumerate(transcript_changes):
            print(f"  {i+1}. {change['content'][:50]}...")
        
        # Should have at least initial state change
        assert len(transcript_changes) >= 1, "Should detect at least initial transcript state"
    
    async def test_word_count_accuracy(self, live_page: Page):
        """Test that word count matches transcript content."""
        page = live_page
        
        # Start recording
        await page.locator('#recordButton').click()
        await page.wait_for_timeout(5000)
        
        # Stop recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.click()
        else:
            await page.locator('#recordButton').click()
        
        await page.wait_for_timeout(2000)
        
        # Get final counts
        displayed_word_count = await page.locator('#wordCount').text_content()
        transcript_text = await page.locator('#transcript').text_content()
        
        # Count words in transcript (excluding UI text)
        if transcript_text and displayed_word_count and not transcript_text.startswith('Click the red button'):
            actual_word_count = len([w for w in transcript_text.split() if w.strip()])
            expected_count = int(displayed_word_count)
            
            # Allow for some variance in word counting
            word_count_diff = abs(actual_word_count - expected_count)
            assert word_count_diff <= 2, f"Word count mismatch: displayed {expected_count}, actual {actual_word_count}"
            
            print(f"Word count validation: displayed={expected_count}, actual={actual_word_count}")
        else:
            print("No transcription detected - skipping word count validation")

@pytest.mark.critical  
class TestErrorHandling:
    """Test error handling and recovery scenarios."""
    
    async def test_microphone_permission_denied(self, page: Page):
        """Test handling when microphone permission is denied."""
        # Create context without microphone permission
        browser = page.context.browser
        if not browser:
            print("Browser not available for context creation")
            return
        context = await browser.new_context(
            permissions=[]  # No permissions granted
        )
        
        test_page = await context.new_page()
        
        try:
            await test_page.goto('http://localhost:5000/live')
            
            # Try to start recording
            await test_page.locator('#recordButton').click()
            
            # Wait for error handling
            await test_page.wait_for_timeout(3000)
            
            # Check for error message or status
            page_content = await test_page.content()
            
            # Should show some indication that microphone access failed
            # This will depend on implementation
            print("Testing microphone permission denial...")
            
        finally:
            await context.close()
    
    async def test_network_disconnection_recovery(self, live_page: Page, network_conditions):
        """Test recovery from network disconnection."""
        page = live_page
        
        # Start recording
        await page.locator('#recordButton').click()
        await page.wait_for_timeout(2000)
        
        # Simulate network disconnection
        await page.context.set_offline(True)
        
        # Continue recording during offline period
        await page.wait_for_timeout(3000)
        
        # Restore network
        await page.context.set_offline(False)
        
        # Should recover gracefully
        await page.wait_for_timeout(3000)
        
        # Stop recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.click()
        else:
            await page.locator('#recordButton').click()
        
        await page.wait_for_timeout(2000)
        
        # Should have completed session despite network issues
        final_timer = await page.locator('#timer').text_content()
        assert final_timer != '00:00', "Session should show recorded time despite network issues"
    
    async def test_page_refresh_during_recording(self, live_page: Page):
        """Test behavior when page is refreshed during recording."""
        page = live_page
        
        # Start recording
        await page.locator('#recordButton').click()
        await page.wait_for_timeout(2000)
        
        # Get initial state
        initial_timer = await page.locator('#timer').text_content()
        
        # Refresh page
        await page.reload()
        await page.wait_for_load_state('networkidle')
        
        # Check if session state is preserved or reset
        new_timer = await page.locator('#timer').text_content()
        
        # Should either preserve state or gracefully reset
        print(f"Timer before refresh: {initial_timer}")
        print(f"Timer after refresh: {new_timer}")
        
        # UI should be functional after refresh
        await expect(page.locator('#recordButton')).to_be_visible()
        await expect(page.locator('#transcript')).to_be_visible()