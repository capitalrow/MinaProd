"""
Pytest configuration for MINA E2E tests
"""

import pytest
import os
import sys
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright

# Add the project root to Python path so tests can import application modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Register custom pytest marks
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "smoke: Basic smoke tests")
    config.addinivalue_line("markers", "critical: Critical functionality tests")
    config.addinivalue_line("markers", "auth: Authentication related tests")
    config.addinivalue_line("markers", "transcription: Transcription functionality tests") 
    config.addinivalue_line("markers", "edge_case: Edge case and boundary tests")
    config.addinivalue_line("markers", "performance: Performance testing")
    config.addinivalue_line("markers", "accessibility: Accessibility compliance tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "mobile: Mobile device tests")
    config.addinivalue_line("markers", "comprehensive: Full end-to-end tests")
    config.addinivalue_line("markers", "validation: Form and input validation tests")
    config.addinivalue_line("markers", "security: Security testing")
    config.addinivalue_line("markers", "browser: Cross-browser compatibility tests")
    config.addinivalue_line("markers", "realtime: Real-time functionality tests")

def pytest_sessionstart(session):
    """Setup session - install Playwright browsers if needed"""
    try:
        # Check if browsers are available
        result = subprocess.run([sys.executable, "-m", "playwright", "install", "--help"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            # Install browsers with dependencies
            print("🔧 Installing Playwright browsers...")
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)
            print("✅ Playwright setup complete")
    except Exception as e:
        print(f"⚠️ Could not setup Playwright: {e}")

@pytest.fixture(scope="session")
def base_url():
    """Base URL for testing"""
    return os.getenv("BASE_URL", "http://localhost:5000")

@pytest.fixture(scope="session")
async def browser_context(base_url):
    """Create browser context with proper base URL"""
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                base_url=base_url,
                viewport={"width": 1280, "height": 720},
                permissions=["microphone"],
                ignore_https_errors=True
            )
            yield context
            await context.close()
            await browser.close()
        except Exception as e:
            pytest.skip(f"Browser not available: {e}")

@pytest.fixture
async def page(browser_context):
    """Create page with proper context"""
    try:
        page = await browser_context.new_page()
        
        # Add axe-core for accessibility testing
        await page.add_script_tag(url="https://unpkg.com/axe-core@4.7.0/axe.min.js")
        
        yield page
        await page.close()
    except Exception as e:
        pytest.skip(f"Page not available: {e}")