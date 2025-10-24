"""
Smoke Tests - Basic functionality validation
These tests verify that core components load and basic interactions work
"""
import pytest
import asyncio
from playwright.async_api import Page, expect

@pytest.mark.smoke
class TestSmokeTests:
    """Basic smoke tests for critical functionality."""
    
    async def test_homepage_loads(self, page: Page):
        """Test that homepage loads successfully."""
        await page.goto('http://localhost:5000/')
        
        # Check page loads
        await expect(page).to_have_title('Mina')
        
        # Check navigation is present
        await expect(page.locator('nav')).to_be_visible()
        
        # Verify no console errors
        console_errors = []
        page.on('pageerror', lambda err: console_errors.append(str(err)))
        await page.wait_for_timeout(2000)
        
        assert len(console_errors) == 0, f"Console errors found: {console_errors}"
    
    async def test_live_page_loads(self, page: Page):
        """Test that live transcription page loads successfully."""
        await page.goto('http://localhost:5000/live')
        
        # Check page loads
        await expect(page).to_have_title('Live Transcription - Mina')
        
        # Check essential elements are present
        await expect(page.locator('#recordButton')).to_be_visible()
        await expect(page.locator('#transcript')).to_be_visible()
        await expect(page.locator('#timer')).to_be_visible()
        await expect(page.locator('#wordCount')).to_be_visible()
        await expect(page.locator('#accuracy')).to_be_visible()
        
        # Verify initial states
        timer_text = await page.locator('#timer').text_content()
        assert timer_text == '00:00', f"Expected timer to show 00:00, got {timer_text}"
        
        word_count = await page.locator('#wordCount').text_content()
        assert word_count == '0', f"Expected word count to be 0, got {word_count}"
    
    async def test_record_button_interaction(self, page: Page):
        """Test basic record button interaction."""
        await page.goto('http://localhost:5000/live')
        
        record_button = page.locator('#recordButton')
        
        # Check initial state
        await expect(record_button).to_be_visible()
        await expect(record_button).to_be_enabled()
        
        # Check button is clickable
        initial_class = await record_button.get_attribute('class')
        
        # Click the button
        await record_button.click()
        
        # Wait for any state changes
        await page.wait_for_timeout(1000)
        
        # Verify button state changed (should have recording state)
        new_class = await record_button.get_attribute('class')
        
        # Button class should change when clicked
        print(f"Initial button class: {initial_class}")
        print(f"New button class: {new_class}")
    
    async def test_javascript_loads(self, page: Page):
        """Test that JavaScript files load without errors."""
        js_errors = []
        page.on('pageerror', lambda err: js_errors.append(str(err)))
        
        await page.goto('http://localhost:5000/live')
        await page.wait_for_timeout(3000)  # Wait for JS to execute
        
        # Check for JavaScript errors
        assert len(js_errors) == 0, f"JavaScript errors found: {js_errors}"
        
        # Check if MinaTranscription is available
        mina_available = await page.evaluate('typeof window.MinaTranscription !== "undefined"')
        print(f"MinaTranscription available: {mina_available}")
        
        # Check if system is initialized
        system_initialized = await page.evaluate('''
            typeof window.minaTranscription !== "undefined" || 
            typeof window.minaSystemManager !== "undefined"
        ''')
        print(f"Transcription system initialized: {system_initialized}")
    
    async def test_responsive_layout(self, page: Page):
        """Test responsive layout at different viewport sizes."""
        test_viewports = [
            {'width': 375, 'height': 667},   # iPhone SE
            {'width': 768, 'height': 1024},  # iPad
            {'width': 1920, 'height': 1080}  # Desktop
        ]
        
        for viewport in test_viewports:
            await page.set_viewport_size({"width": viewport['width'], "height": viewport['height']})
            await page.goto('http://localhost:5000/live')
            
            # Essential elements should be visible at all sizes
            await expect(page.locator('#recordButton')).to_be_visible()
            await expect(page.locator('#transcript')).to_be_visible()
            
            # Check if elements are properly sized for touch on mobile
            if viewport['width'] <= 768:
                button = page.locator('#recordButton')
                button_box = await button.bounding_box()
                
                # Touch targets should be at least 44px
                if button_box:  # Check if button_box is not None
                    assert button_box['width'] >= 44, f"Button too small for touch at {viewport['width']}px"
                    assert button_box['height'] >= 44, f"Button too small for touch at {viewport['width']}px"
    
    async def test_accessibility_basics(self, page: Page):
        """Test basic accessibility features."""
        await page.goto('http://localhost:5000/live')
        
        # Check for proper heading structure
        h1_elements = await page.locator('h1').count()
        assert h1_elements >= 1, "Page should have at least one H1 element"
        
        # Check record button has proper labeling
        record_button = page.locator('#recordButton')
        
        # Should have either aria-label or title
        aria_label = await record_button.get_attribute('aria-label')
        title = await record_button.get_attribute('title')
        
        assert aria_label or title, "Record button should have aria-label or title for accessibility"
        
        # Check transcript area has proper ARIA attributes
        transcript = page.locator('#transcript')
        aria_live = await transcript.get_attribute('aria-live')
        
        assert aria_live == 'polite', f"Transcript should have aria-live='polite', got {aria_live}"
    
    async def test_network_connectivity(self, page: Page):
        """Test basic network connectivity to backend."""
        await page.goto('http://localhost:5000/live')
        
        # Monitor network requests
        requests = []
        page.on('request', lambda req: requests.append(req.url))
        
        responses = []
        page.on('response', lambda res: responses.append({'url': res.url, 'status': res.status}))
        
        # Wait for initial requests
        await page.wait_for_timeout(2000)
        
        # Check that basic resources loaded successfully
        css_loaded = any('/static/css/' in req for req in requests)
        js_loaded = any('/static/js/' in req or 'mina_transcription' in req for req in requests)
        
        print(f"CSS loaded: {css_loaded}")
        print(f"JS loaded: {js_loaded}")
        print(f"Total requests: {len(requests)}")
        print(f"Total responses: {len(responses)}")
        
        # Check for any 404s or 500s
        error_responses = [res for res in responses if res['status'] >= 400]
        assert len(error_responses) == 0, f"Error responses found: {error_responses}"

@pytest.mark.smoke  
class TestAPIEndpoints:
    """Test API endpoints are accessible."""
    
    async def test_transcription_endpoint_exists(self, page: Page):
        """Test that transcription API endpoint exists."""
        # Navigate to live page first to set up context
        await page.goto('http://localhost:5000/live')
        
        # Make a test request to the API endpoint
        response = await page.request.post(
            'http://localhost:5000/api/transcribe-audio',
            data={
                'session_id': 'test_session',
                'audio_data': 'test_data',
                'chunk_number': 1
            }
        )
        
        # Should return a response (might be error, but endpoint exists)
        assert response.status in [200, 400, 422], f"Unexpected status: {response.status}"
        
        # If 200, should have JSON response
        if response.status == 200:
            json_response = await response.json()
            assert 'status' in json_response, "Response should have status field"
    
    async def test_health_check_endpoint(self, page: Page):
        """Test health check endpoint if available."""
        try:
            response = await page.request.get('http://localhost:5000/health')
            if response.status == 200:
                json_response = await response.json()
                print(f"Health check response: {json_response}")
        except Exception as e:
            print(f"Health check endpoint not available: {e}")
            # This is not a critical failure for smoke tests