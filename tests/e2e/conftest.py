"""
E2E Test Configuration
Playwright-based end-to-end tests that use the actual database
"""
import pytest
import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def browser():
    """Launch browser for E2E tests."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()

@pytest.fixture(scope="function")
async def page(browser: Browser):
    """Create a new page for each test."""
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        permissions=["microphone"]  # Grant microphone permission
    )
    page = await context.new_page()
    yield page
    await page.close()
    await context.close()

@pytest.fixture(scope="function")
async def live_page(page: Page):
    """Navigate to live transcription page."""
    await page.goto('http://localhost:5000/live')
    await page.wait_for_load_state('networkidle')
    yield page

@pytest.fixture(scope="function")
def performance_monitor():
    """Provide performance monitoring dictionary."""
    return {}

@pytest.fixture(scope="function")
def mock_whisper_api(mocker):
    """Mock Whisper API for testing without actual transcription."""
    # This can be expanded to mock OpenAI/Whisper calls if needed
    return mocker

@pytest.fixture(scope="function")
def seed_test_session():
    """Seed a test session with segments for deterministic testing."""
    import os
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker
    from datetime import datetime
    import uuid
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL or DATABASE_URL.startswith('sqlite'):
        yield None
        return
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()
    
    try:
        from models.session import Session as SessionModel
        from models.segment import Segment
        
        # Create test session
        test_session = SessionModel(
            external_id=str(uuid.uuid4()),
            title="E2E Test Session",
            status="active",
            locale="en-US"
        )
        db_session.add(test_session)
        db_session.flush()  # Get the ID
        
        # Create test segments
        for i in range(3):
            segment = Segment(
                session_id=test_session.id,
                kind="final",
                text=f"Test transcript segment {i+1}",
                avg_confidence=0.95,
            )
            db_session.add(segment)
        
        db_session.commit()
        
        yield test_session
        
        # Cleanup after test
        for segment in test_session.segments:
            db_session.delete(segment)
        db_session.delete(test_session)
        db_session.commit()
        
    except Exception as e:
        db_session.rollback()
        print(f"Error seeding test session: {e}")
        yield None
    finally:
        db_session.close()
