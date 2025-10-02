"""
Visual regression tests using Playwright screenshot comparison.
These tests capture screenshots and compare them against baseline images.
"""
import pytest
from playwright.async_api import Page, expect


@pytest.mark.visual
class TestVisualRegression:
    """Visual regression tests for UI consistency."""
    
    async def test_homepage_visual(self, page: Page):
        """Test homepage visual appearance."""
        await page.goto('http://localhost:5000/')
        await page.wait_for_load_state('networkidle')
        
        await expect(page).to_have_screenshot('homepage.png', full_page=True)
    
    async def test_live_page_visual(self, page: Page):
        """Test live transcription page visual appearance."""
        await page.goto('http://localhost:5000/live')
        await page.wait_for_load_state('networkidle')
        
        await expect(page).to_have_screenshot('live-page.png', full_page=True)
    
    async def test_live_page_recording_state_visual(self, page: Page):
        """Test live page in recording state."""
        await page.goto('http://localhost:5000/live')
        await page.wait_for_load_state('networkidle')
        
        record_button = page.locator('#recordButton')
        await record_button.click()
        await page.wait_for_timeout(500)
        
        await expect(page).to_have_screenshot('live-page-recording.png', full_page=True)
    
    async def test_dashboard_visual(self, page: Page):
        """Test dashboard visual appearance."""
        await page.goto('http://localhost:5000/dashboard')
        await page.wait_for_load_state('networkidle')
        
        await expect(page).to_have_screenshot('dashboard.png', full_page=True)
    
    async def test_navigation_component_visual(self, page: Page):
        """Test navigation component visual consistency."""
        await page.goto('http://localhost:5000/')
        await page.wait_for_load_state('networkidle')
        
        nav = page.locator('nav')
        await expect(nav).to_have_screenshot('navigation.png')
    
    async def test_footer_component_visual(self, page: Page):
        """Test footer component visual consistency."""
        await page.goto('http://localhost:5000/')
        await page.wait_for_load_state('networkidle')
        
        footer = page.locator('footer')
        if await footer.count() > 0:
            await expect(footer).to_have_screenshot('footer.png')
    
    async def test_mobile_homepage_visual(self, page: Page):
        """Test mobile homepage visual appearance."""
        await page.set_viewport_size({'width': 375, 'height': 667})
        await page.goto('http://localhost:5000/')
        await page.wait_for_load_state('networkidle')
        
        await expect(page).to_have_screenshot('mobile-homepage.png', full_page=True)
    
    async def test_mobile_live_page_visual(self, page: Page):
        """Test mobile live page visual appearance."""
        await page.set_viewport_size({'width': 375, 'height': 667})
        await page.goto('http://localhost:5000/live')
        await page.wait_for_load_state('networkidle')
        
        await expect(page).to_have_screenshot('mobile-live-page.png', full_page=True)
    
    async def test_dark_theme_visual(self, page: Page):
        """Test dark theme visual consistency."""
        await page.goto('http://localhost:5000/')
        await page.wait_for_load_state('networkidle')
        
        theme_toggle = page.locator('[data-theme-toggle]')
        if await theme_toggle.count() > 0:
            await theme_toggle.click()
            await page.wait_for_timeout(300)
            await expect(page).to_have_screenshot('homepage-dark.png', full_page=True)
    
    async def test_high_contrast_mode_visual(self, page: Page):
        """Test high contrast mode visual appearance."""
        await page.goto('http://localhost:5000/')
        await page.wait_for_load_state('networkidle')
        
        contrast_toggle = page.locator('[data-contrast-toggle]')
        if await contrast_toggle.count() > 0:
            await contrast_toggle.click()
            await page.wait_for_timeout(300)
            await expect(page).to_have_screenshot('homepage-high-contrast.png', full_page=True)
