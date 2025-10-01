"""
WCAG 2.1 AA Compliance Tests
Tests key pages for accessibility violations using axe-core.
"""
import pytest
from playwright.sync_api import Page

@pytest.mark.e2e
def test_home_page_accessibility(page: Page, axe_builder, assert_no_violations, save_accessibility_report):
    """Test home page for accessibility violations."""
    page.goto('http://localhost:5000/')
    page.wait_for_load_state('networkidle')
    
    results = axe_builder()
    save_accessibility_report('home_page', results)
    
    # Allow specific violations if needed (remove this list for strict checking)
    # allowed_rules = ['color-contrast']
    assert_no_violations(results)

@pytest.mark.e2e
def test_login_page_accessibility(page: Page, axe_builder, assert_no_violations, save_accessibility_report):
    """Test login page for accessibility violations."""
    page.goto('http://localhost:5000/auth/login')
    page.wait_for_load_state('networkidle')
    
    results = axe_builder()
    save_accessibility_report('login_page', results)
    assert_no_violations(results)

@pytest.mark.e2e
def test_public_pages_accessibility(page: Page, axe_builder, assert_no_violations, save_accessibility_report):
    """Test main public pages for accessibility violations."""
    # Test multiple public routes
    public_routes = [
        ('/live', 'live_session'),
        ('/auth/register', 'register'),
    ]
    
    for route, name in public_routes:
        page.goto(f'http://localhost:5000{route}')
        page.wait_for_load_state('networkidle')
        
        results = axe_builder()
        save_accessibility_report(name, results)
        assert_no_violations(results)

@pytest.mark.e2e
def test_keyboard_navigation(page: Page):
    """Test that all interactive elements are keyboard accessible."""
    page.goto('http://localhost:5000/')
    page.wait_for_load_state('networkidle')
    
    # Test Tab navigation
    focusable_elements = page.locator('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])').all()
    
    # Ensure there are focusable elements
    assert len(focusable_elements) > 0, "No focusable elements found on page"
    
    # Test first element can receive focus
    if focusable_elements:
        first_element = focusable_elements[0]
        first_element.focus()
        is_focused = first_element.evaluate('el => el === document.activeElement')
        assert is_focused, "First element should be focusable"

@pytest.mark.e2e
def test_aria_labels_present(page: Page):
    """Test that interactive elements have proper ARIA labels."""
    page.goto('http://localhost:5000/')
    page.wait_for_load_state('networkidle')
    
    # Check buttons without visible text have aria-label
    buttons = page.locator('button').all()
    
    for button in buttons:
        text = button.inner_text()
        if not text.strip():
            # Button has no visible text, should have aria-label
            aria_label = button.get_attribute('aria-label')
            assert aria_label, f"Button without text must have aria-label: {button.inner_html()}"

@pytest.mark.e2e  
def test_form_labels_associated(page: Page):
    """Test that form inputs have associated labels."""
    page.goto('http://localhost:5000/auth/login')
    page.wait_for_load_state('networkidle')
    
    # Get all inputs
    inputs = page.locator('input[type="text"], input[type="email"], input[type="password"]').all()
    
    for input_element in inputs:
        input_id = input_element.get_attribute('id')
        aria_label = input_element.get_attribute('aria-label')
        aria_labelledby = input_element.get_attribute('aria-labelledby')
        
        # Input should have either: id with associated label, aria-label, or aria-labelledby
        if input_id:
            label_count = page.locator(f'label[for="{input_id}"]').count()
            has_label = label_count > 0
        else:
            has_label = False
        
        assert has_label or aria_label or aria_labelledby, \
            f"Input must have associated label: {input_element.get_attribute('name')}"
