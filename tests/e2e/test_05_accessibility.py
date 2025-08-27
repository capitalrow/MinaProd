"""
Accessibility Testing (WCAG 2.1 AA+ Compliance)
Testing keyboard navigation, screen readers, and accessibility features
"""
import pytest
import asyncio
from playwright.async_api import Page, expect

@pytest.mark.accessibility
class TestKeyboardNavigation:
    """Test keyboard navigation and shortcuts."""
    
    async def test_tab_navigation_flow(self, live_page: Page):
        """Test complete keyboard navigation flow."""
        page = live_page
        
        # Start at the beginning of the page
        await page.keyboard.press('Home')
        
        # Tab through all interactive elements
        focusable_elements = []
        
        for i in range(20):  # Maximum 20 tab stops
            await page.keyboard.press('Tab')
            
            # Get currently focused element
            focused_element = await page.evaluate('''
                document.activeElement ? {
                    tagName: document.activeElement.tagName,
                    id: document.activeElement.id,
                    className: document.activeElement.className,
                    ariaLabel: document.activeElement.getAttribute('aria-label'),
                    type: document.activeElement.type
                } : null
            ''')
            
            if focused_element and focused_element not in focusable_elements:
                focusable_elements.append(focused_element)
                print(f"Tab stop {i+1}: {focused_element}")
        
        # Should have focused on record button at some point
        record_button_focused = any(elem['id'] == 'recordButton' for elem in focusable_elements)
        assert record_button_focused, "Record button should be reachable via keyboard"
        
        # Should have proper focus indicators
        await page.keyboard.press('Tab')  # Focus on record button
        
        # Take screenshot to verify focus indicator
        await page.screenshot(path='tests/results/screenshots/keyboard_focus.png')
        
        print(f"Found {len(focusable_elements)} focusable elements")
    
    async def test_keyboard_shortcuts(self, live_page: Page):
        """Test keyboard shortcuts for common actions."""
        page = live_page
        
        # Test Space bar to start/stop recording
        await page.focus('body')  # Ensure body has focus
        await page.keyboard.press('Space')
        await page.wait_for_timeout(2000)
        
        # Check if recording started
        timer_value = await page.locator('#timer').text_content()
        print(f"After Space press - Timer: {timer_value}")
        
        # Test Escape to stop recording
        await page.keyboard.press('Escape')
        await page.wait_for_timeout(1000)
        
        # Should handle keyboard shortcuts gracefully
        await expect(page.locator('#recordButton')).to_be_visible()
        
        print("Keyboard shortcuts test completed")
    
    async def test_focus_management(self, live_page: Page):
        """Test focus management during dynamic content changes."""
        page = live_page
        
        # Focus on record button
        await page.locator('#recordButton').focus()
        
        # Verify focus is visible
        focused_element_id = await page.evaluate('document.activeElement?.id')
        assert focused_element_id == 'recordButton', "Record button should be focused"
        
        # Start recording and check focus management
        await page.keyboard.press('Enter')  # Activate button with keyboard
        await page.wait_for_timeout(1000)
        
        # Focus should remain on a reasonable element
        current_focus = await page.evaluate('''
            document.activeElement ? {
                id: document.activeElement.id,
                tagName: document.activeElement.tagName
            } : null
        ''')
        
        print(f"Focus after recording start: {current_focus}")
        
        # Focus should not be lost to document body
        assert current_focus and current_focus['tagName'] != 'BODY', "Focus should be managed properly"
        
        # Stop recording
        await page.keyboard.press('Escape')
    
    async def test_skip_links(self, live_page: Page):
        """Test skip links for keyboard users."""
        page = live_page
        
        # Tab to first element (should be skip link if implemented)
        await page.keyboard.press('Tab')
        
        focused_element = await page.evaluate('''
            document.activeElement ? {
                textContent: document.activeElement.textContent,
                href: document.activeElement.href,
                className: document.activeElement.className
            } : null
        ''')
        
        print(f"First tab stop: {focused_element}")
        
        # Look for skip link patterns
        if focused_element and ('skip' in focused_element.get('textContent', '').lower()):
            print("Skip link found")
            
            # Activate skip link
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(500)
            
            # Should jump to main content
            new_focus = await page.evaluate('document.activeElement?.id')
            print(f"Focus after skip link: {new_focus}")
        else:
            print("No skip link detected - this is a recommendation for improvement")

@pytest.mark.accessibility
class TestScreenReaderSupport:
    """Test screen reader support and ARIA attributes."""
    
    async def test_aria_live_regions(self, live_page: Page):
        """Test ARIA live regions for dynamic content."""
        page = live_page
        
        # Check transcript area has aria-live
        transcript_aria = await page.get_attribute('#transcript', 'aria-live')
        assert transcript_aria == 'polite', f"Transcript should have aria-live='polite', got {transcript_aria}"
        
        # Check for aria-atomic if present
        transcript_atomic = await page.get_attribute('#transcript', 'aria-atomic')
        print(f"Transcript aria-atomic: {transcript_atomic}")
        
        # Start recording to test live region updates
        await page.locator('#recordButton').click()
        await page.wait_for_timeout(3000)
        
        # Simulate transcript update and verify it's announced
        await page.evaluate('''
            const transcript = document.getElementById('transcript');
            if (transcript) {
                transcript.textContent = 'Test transcription update for screen reader';
            }
        ''')
        
        await page.wait_for_timeout(1000)
        
        # Stop recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.click()
        else:
            await page.locator('#recordButton').click()
        
        print("ARIA live regions test completed")
    
    async def test_button_labeling(self, live_page: Page):
        """Test button labeling for screen readers."""
        page = live_page
        
        # Check record button has proper labeling
        record_button = page.locator('#recordButton')
        
        # Check for aria-label
        aria_label = await record_button.get_attribute('aria-label')
        
        # Check for title attribute as fallback
        title = await record_button.get_attribute('title')
        
        # Check button text content
        text_content = await record_button.text_content()
        
        print(f"Record button - aria-label: {aria_label}, title: {title}, text: {text_content}")
        
        # Should have some form of accessible label
        has_label = aria_label or title or (text_content and text_content.strip())
        assert has_label, "Record button should have accessible label"
        
        # Check other interactive elements
        interactive_selectors = [
            '#pauseButton',
            '#stopButton', 
            '#copyButton',
            '#downloadButton'
        ]
        
        for selector in interactive_selectors:
            element = page.locator(selector)
            
            if await element.count() > 0 and await element.is_visible():
                elem_aria_label = await element.get_attribute('aria-label')
                elem_title = await element.get_attribute('title')
                elem_text = await element.text_content()
                
                elem_has_label = elem_aria_label or elem_title or (elem_text and elem_text.strip())
                
                print(f"{selector} - aria-label: {elem_aria_label}, title: {elem_title}, text: {elem_text}")
                
                if not elem_has_label:
                    print(f"WARNING: {selector} may need better labeling")
    
    async def test_form_labeling(self, live_page: Page):
        """Test form element labeling."""
        page = live_page
        
        # Find all input elements
        inputs = await page.locator('input, select, textarea').all()
        
        for i, input_elem in enumerate(inputs):
            input_id = await input_elem.get_attribute('id')
            input_type = await input_elem.get_attribute('type')
            aria_label = await input_elem.get_attribute('aria-label')
            aria_labelledby = await input_elem.get_attribute('aria-labelledby')
            
            print(f"Input {i+1}: id={input_id}, type={input_type}, aria-label={aria_label}")
            
            # Check for associated label
            if input_id:
                label_exists = await page.locator(f'label[for="{input_id}"]').count() > 0
                if not label_exists and not aria_label and not aria_labelledby:
                    print(f"WARNING: Input {input_id} may need better labeling")
    
    async def test_heading_structure(self, live_page: Page):
        """Test proper heading structure."""
        page = live_page
        
        # Get all headings
        headings = await page.evaluate('''
            Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6')).map(h => ({
                level: parseInt(h.tagName.charAt(1)),
                text: h.textContent.trim(),
                id: h.id
            }))
        ''')
        
        print(f"Found headings: {headings}")
        
        # Should have at least one h1
        h1_headings = [h for h in headings if h['level'] == 1]
        assert len(h1_headings) >= 1, "Page should have at least one H1 heading"
        
        # Check heading hierarchy (no skipping levels)
        if len(headings) > 1:
            for i in range(1, len(headings)):
                current_level = headings[i]['level']
                previous_level = headings[i-1]['level']
                
                level_jump = current_level - previous_level
                if level_jump > 1:
                    print(f"WARNING: Heading level jump from H{previous_level} to H{current_level}")
    
    async def test_color_contrast(self, live_page: Page):
        """Test color contrast ratios."""
        page = live_page
        
        # Get computed styles for key elements
        contrast_tests = [
            {'selector': '#recordButton', 'description': 'Record button'},
            {'selector': '#transcript', 'description': 'Transcript area'},
            {'selector': '#timer', 'description': 'Timer display'},
            {'selector': '#wordCount', 'description': 'Word count'},
            {'selector': 'body', 'description': 'Page background'}
        ]
        
        for test in contrast_tests:
            try:
                styles = await page.evaluate(f'''
                    const element = document.querySelector('{test["selector"]}');
                    if (element) {{
                        const computed = getComputedStyle(element);
                        return {{
                            color: computed.color,
                            backgroundColor: computed.backgroundColor,
                            fontSize: computed.fontSize
                        }};
                    }}
                    return null;
                ''')
                
                print(f"{test['description']}: {styles}")
                
                # Note: Actual contrast ratio calculation would require
                # parsing RGB values and applying WCAG formula
                # This is a basic check for visibility
                
            except Exception as e:
                print(f"Could not check contrast for {test['selector']}: {e}")

@pytest.mark.accessibility  
class TestAccessibilityFeatures:
    """Test specific accessibility features."""
    
    async def test_reduced_motion_support(self, live_page: Page):
        """Test support for users who prefer reduced motion."""
        page = live_page
        
        # Set prefers-reduced-motion
        await page.emulate_media(media=[{'name': 'prefers-reduced-motion', 'value': 'reduce'}])
        
        await page.reload()
        await page.wait_for_load_state('networkidle')
        
        # Start recording to check animations
        await page.locator('#recordButton').click()
        await page.wait_for_timeout(1000)
        
        # Check if animations are reduced/disabled
        # (This would require checking CSS animations)
        button_styles = await page.evaluate('''
            const button = document.getElementById('recordButton');
            if (button) {
                const computed = getComputedStyle(button);
                return {
                    animationDuration: computed.animationDuration,
                    transitionDuration: computed.transitionDuration
                };
            }
            return null;
        ''')
        
        print(f"Reduced motion - Button animations: {button_styles}")
        
        # Stop recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.click()
        else:
            await page.locator('#recordButton').click()
    
    async def test_high_contrast_mode(self, live_page: Page):
        """Test high contrast mode support."""
        page = live_page
        
        # Simulate high contrast mode
        await page.emulate_media(media=[{'name': 'prefers-contrast', 'value': 'high'}])
        
        await page.reload()
        await page.wait_for_load_state('networkidle')
        
        # Check if high contrast styles are applied
        # (This would require checking specific CSS)
        
        # At minimum, elements should remain visible and functional
        await expect(page.locator('#recordButton')).to_be_visible()
        await expect(page.locator('#transcript')).to_be_visible()
        
        # Test functionality in high contrast
        await page.locator('#recordButton').click()
        await page.wait_for_timeout(1000)
        
        # Should still be functional
        timer_value = await page.locator('#timer').text_content()
        print(f"High contrast mode - Timer: {timer_value}")
        
        # Stop recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.click()
        else:
            await page.locator('#recordButton').click()
    
    async def test_zoom_support(self, live_page: Page):
        """Test zoom support up to 200%."""
        page = live_page
        
        zoom_levels = [100, 150, 200]
        
        for zoom in zoom_levels:
            # Set zoom level
            await page.set_viewport_size({
                'width': int(1920 / (zoom / 100)),
                'height': int(1080 / (zoom / 100))
            })
            
            await page.evaluate(f'document.body.style.zoom = "{zoom}%"')
            await page.wait_for_timeout(500)
            
            print(f"Testing at {zoom}% zoom")
            
            # Essential elements should remain visible and functional
            await expect(page.locator('#recordButton')).to_be_visible()
            await expect(page.locator('#transcript')).to_be_visible()
            
            # Check if text is still readable (not cut off)
            record_button_box = await page.locator('#recordButton').bounding_box()
            transcript_box = await page.locator('#transcript').bounding_box()
            
            assert record_button_box['width'] > 0, f"Record button should be visible at {zoom}%"
            assert transcript_box['width'] > 0, f"Transcript should be visible at {zoom}%"
            
            print(f"Zoom {zoom}% - Elements remain accessible")
        
        # Reset zoom
        await page.evaluate('document.body.style.zoom = "100%"')
    
    async def test_screen_reader_announcements(self, live_page: Page):
        """Test proper screen reader announcements."""
        page = live_page
        
        # Look for ARIA live regions and announcement areas
        announcement_areas = await page.evaluate('''
            Array.from(document.querySelectorAll('[aria-live], [role="alert"], [role="status"]')).map(elem => ({
                tagName: elem.tagName,
                id: elem.id,
                className: elem.className,
                ariaLive: elem.getAttribute('aria-live'),
                role: elem.getAttribute('role'),
                textContent: elem.textContent.slice(0, 50)
            }))
        ''')
        
        print(f"Screen reader announcement areas: {announcement_areas}")
        
        # Should have at least one announcement mechanism
        assert len(announcement_areas) > 0, "Should have ARIA live regions for announcements"
        
        # Start recording to test announcements
        await page.locator('#recordButton').click()
        await page.wait_for_timeout(2000)
        
        # Check if status changes are announced
        # (In real testing, this would be verified with actual screen readers)
        
        # Stop recording
        stop_button = page.locator('#stopButton')
        if await stop_button.is_visible():
            await stop_button.click()
        else:
            await page.locator('#recordButton').click()
        
        print("Screen reader announcements test completed")