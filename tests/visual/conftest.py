"""
Visual regression test configuration.
"""
import pytest
from playwright.async_api import Page


@pytest.fixture(scope='function')
async def page_with_snapshot_config(page: Page):
    """Configure page for visual regression testing."""
    page.set_default_timeout(30000)
    yield page
