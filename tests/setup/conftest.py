"""
Pytest configuration and fixtures for E2E testing
"""
import pytest
import asyncio
import json
import time
import os
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import Dict, Generator, AsyncGenerator

# Test configuration
BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
BROWSER_TIMEOUT = 30000  # 30 seconds
TEST_RESULTS_DIR = Path('tests/results')
SCREENSHOTS_DIR = TEST_RESULTS_DIR / 'screenshots'
VIDEOS_DIR = TEST_RESULTS_DIR / 'videos'

# Create directories
TEST_RESULTS_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)
VIDEOS_DIR.mkdir(exist_ok=True)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def playwright():
    """Start Playwright for the test session."""
    async with async_playwright() as p:
        yield p

@pytest.fixture(scope="session") 
async def browser(playwright):
    """Launch browser for the test session."""
    browser = await playwright.chromium.launch(
        headless=HEADLESS,
        args=[
            '--use-fake-ui-for-media-stream',  # Auto-grant microphone permission
            '--use-fake-device-for-media-stream',
            '--allow-running-insecure-content',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor'
        ]
    )
    yield browser
    await browser.close()

@pytest.fixture(scope="function")
async def context(browser: Browser):
    """Create a new browser context for each test."""
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        permissions=['microphone'],
        record_video_dir=str(VIDEOS_DIR) if not HEADLESS else None
    )
    yield context
    await context.close()

@pytest.fixture(scope="function")
async def page(context: BrowserContext):
    """Create a new page for each test."""
    page = await context.new_page()
    
    # Set longer timeout for network requests
    page.set_default_timeout(BROWSER_TIMEOUT)
    
    # Add console logging
    page.on('console', lambda msg: print(f'CONSOLE: {msg.text}'))
    page.on('pageerror', lambda err: print(f'PAGE ERROR: {err}'))
    
    yield page

@pytest.fixture(scope="function")
async def mobile_context(browser: Browser):
    """Create mobile browser context."""
    context = await browser.new_context(
        **playwright.devices['iPhone 13'],
        permissions=['microphone']
    )
    yield context
    await context.close()

@pytest.fixture(scope="function") 
async def mobile_page(mobile_context: BrowserContext):
    """Create mobile page."""
    page = await mobile_context.new_page()
    page.set_default_timeout(BROWSER_TIMEOUT)
    
    # Mobile-specific console logging
    page.on('console', lambda msg: print(f'MOBILE CONSOLE: {msg.text}'))
    page.on('pageerror', lambda err: print(f'MOBILE PAGE ERROR: {err}'))
    
    yield page

@pytest.fixture(scope="function")
def test_audio_data():
    """Provide test audio data for testing."""
    return {
        'clear_speech': {
            'file': 'tests/data/clear_speech.wav',
            'expected_text': 'hello world this is a test',
            'duration_seconds': 5
        },
        'noisy_audio': {
            'file': 'tests/data/noisy_audio.wav', 
            'expected_text': 'background noise test',
            'duration_seconds': 3
        },
        'silence': {
            'file': 'tests/data/silence.wav',
            'expected_text': '',
            'duration_seconds': 2
        }
    }

@pytest.fixture(scope="function")
def network_conditions():
    """Network condition presets for testing."""
    return {
        'fast': {'download': 50000, 'upload': 50000, 'latency': 20},
        '3g': {'download': 1600, 'upload': 750, 'latency': 300},
        'slow_3g': {'download': 500, 'upload': 500, 'latency': 2000},
        'offline': {'download': 0, 'upload': 0, 'latency': 0}
    }

@pytest.fixture(scope="function")
async def live_page(page: Page):
    """Navigate to live transcription page and ensure it's ready."""
    await page.goto(f'{BASE_URL}/live')
    
    # Wait for page to be fully loaded
    await page.wait_for_load_state('networkidle')
    
    # Verify key elements are present
    await page.wait_for_selector('#recordButton', timeout=10000)
    await page.wait_for_selector('#transcript', timeout=10000)
    
    yield page

@pytest.fixture(scope="function")
def screenshot_on_failure(request, page: Page):
    """Take screenshot on test failure."""
    yield
    if request.node.rep_call.failed:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = SCREENSHOTS_DIR / f'failure_{request.node.name}_{timestamp}.png'
        asyncio.create_task(page.screenshot(path=screenshot_path, full_page=True))

@pytest.fixture(scope="session")
def test_session_data():
    """Store data across the test session."""
    return {
        'start_time': datetime.now(),
        'test_results': [],
        'performance_metrics': []
    }

@pytest.fixture(scope="function")
def performance_monitor():
    """Monitor performance metrics during tests."""
    start_time = time.time()
    metrics = {
        'start_time': start_time,
        'network_requests': [],
        'console_errors': [],
        'performance_entries': []
    }
    
    yield metrics
    
    metrics['end_time'] = time.time()
    metrics['duration'] = metrics['end_time'] - start_time

# Pytest hooks for enhanced reporting
def pytest_runtest_makereport(item, call):
    """Make test results available to fixtures."""
    if "tmp_path" in item.fixturenames:
        return
    if call.when == "call":
        setattr(item, "rep_" + call.when, call)

@pytest.fixture(autouse=True)
def test_metadata(request):
    """Add metadata to each test."""
    request.node.user_properties.append(("start_time", datetime.now().isoformat()))
    yield
    request.node.user_properties.append(("end_time", datetime.now().isoformat()))

# Mock data fixtures
@pytest.fixture(scope="session")
def mock_api_responses():
    """Mock API responses for testing."""
    return {
        'transcription_success': {
            'status': 'success',
            'text': 'This is a test transcription',
            'confidence': 0.95,
            'word_count': 5,
            'session_id': 'test_session_123'
        },
        'transcription_error': {
            'status': 'error',
            'error': 'Transcription service unavailable',
            'code': 'SERVICE_UNAVAILABLE'
        },
        'rate_limit': {
            'status': 'error', 
            'error': 'Rate limit exceeded',
            'code': 'RATE_LIMIT_EXCEEDED',
            'retry_after': 60
        }
    }

@pytest.fixture(scope="function")
async def mock_whisper_api(page: Page, mock_api_responses):
    """Mock the Whisper API for controlled testing."""
    await page.route('**/api/transcribe-audio', lambda route: route.fulfill(
        json=mock_api_responses['transcription_success'],
        status=200,
        headers={'Content-Type': 'application/json'}
    ))
    yield
    await page.unroute('**/api/transcribe-audio')