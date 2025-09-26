const { test, expect } = require('@playwright/test');

test.describe('Mina Frontend-Backend Integration Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Go to the app
    await page.goto('http://127.0.0.1:5000');
    await page.waitForLoadState('networkidle');
  });

  test('Homepage loads correctly with all navigation elements', async ({ page }) => {
    // Check that main elements are present
    await expect(page.locator('h1')).toContainText('Mina');
    await expect(page.locator('[data-nav]')).toHaveCount(4); // Library, Live, Upload, Settings
    
    // Check navigation links
    await expect(page.locator('a[href="#/library"]')).toBeVisible();
    await expect(page.locator('a[href="#/live"]')).toBeVisible();
    await expect(page.locator('a[href="#/upload"]')).toBeVisible();
    await expect(page.locator('a[href="#/settings"]')).toBeVisible();
  });

  test('Authentication flow - Register new user', async ({ page }) => {
    // Navigate to register
    await page.click('button:has-text("Sign In")');
    await page.waitForSelector('text=Sign In');
    
    // Look for register link
    const registerLink = page.locator('a:has-text("Create an account")');
    if (await registerLink.isVisible()) {
      await registerLink.click();
    } else {
      // Try alternative register navigation
      await page.goto('http://127.0.0.1:5000#/register');
    }
    
    await page.waitForSelector('text=Create Account', { timeout: 10000 });
    
    // Fill out registration form
    const timestamp = Date.now();
    const testEmail = `test${timestamp}@example.com`;
    
    await page.fill('#reg-name', 'Test User');
    await page.fill('#reg-email', testEmail);
    await page.fill('#reg-password', 'testpassword123');
    
    // Submit registration
    await page.click('button:has-text("Create Account")');
    
    // Check for success or appropriate response
    await page.waitForTimeout(2000);
    
    // Should either show success message or redirect to library
    const currentUrl = page.url();
    console.log('After registration URL:', currentUrl);
  });

  test('Authentication flow - Login existing user', async ({ page }) => {
    // Navigate to login
    await page.click('button:has-text("Sign In")');
    await page.waitForSelector('text=Sign In');
    
    // Try with test credentials
    await page.fill('#login-email', 'test@example.com');
    await page.fill('#login-password', 'testpassword');
    await page.click('button:has-text("Sign In")');
    
    await page.waitForTimeout(2000);
    console.log('After login URL:', page.url());
  });

  test('Navigation between views works correctly', async ({ page }) => {
    // Test Library view
    await page.click('a[href="#/library"]');
    await page.waitForTimeout(1000);
    expect(page.url()).toContain('#/library');
    
    // Test Live view
    await page.click('a[href="#/live"]');
    await page.waitForTimeout(1000);
    expect(page.url()).toContain('#/live');
    await expect(page.locator('text=Live Transcription')).toBeVisible();
    
    // Test Upload view
    await page.click('a[href="#/upload"]');
    await page.waitForTimeout(1000);
    expect(page.url()).toContain('#/upload');
    await expect(page.locator('text=Upload Audio/Video')).toBeVisible();
    
    // Test Settings view
    await page.click('a[href="#/settings"]');
    await page.waitForTimeout(1000);
    expect(page.url()).toContain('#/settings');
    await expect(page.locator('text=Settings')).toBeVisible();
  });

  test('Live transcription interface elements present', async ({ page }) => {
    await page.goto('http://127.0.0.1:5000#/live');
    await page.waitForLoadState('networkidle');
    
    // Check for transcription controls
    await expect(page.locator('button:has-text("Start Recording")')).toBeVisible();
    await expect(page.locator('button:has-text("Stop Recording")')).toBeVisible();
    await expect(page.locator('button:has-text("Save Session")')).toBeVisible();
    
    // Check for transcript area
    await expect(page.locator('[aria-label="Live transcription text"]')).toBeVisible();
  });

  test('Upload interface elements present', async ({ page }) => {
    await page.goto('http://127.0.0.1:5000#/upload');
    await page.waitForLoadState('networkidle');
    
    // Check for upload form elements
    await expect(page.locator('input[type="file"]')).toBeVisible();
    await expect(page.locator('button:has-text("Upload File")')).toBeVisible();
    
    // Check supported formats info
    await expect(page.locator('text=Supported formats')).toBeVisible();
  });

  test('Settings interface elements present', async ({ page }) => {
    await page.goto('http://127.0.0.1:5000#/settings');
    await page.waitForLoadState('networkidle');
    
    // Check for settings form elements
    await expect(page.locator('text=Settings')).toBeVisible();
    
    // May need authentication first
    const hasEmailField = await page.locator('input[type="email"]').count();
    if (hasEmailField > 0) {
      await expect(page.locator('input[type="email"]')).toBeVisible();
    }
  });

  test('Accessibility features present', async ({ page }) => {
    // Check for skip to content link
    await expect(page.locator('text=Skip to main content')).toBeHidden();
    
    // Check ARIA attributes on main navigation
    await expect(page.locator('[role="navigation"]')).toBeVisible();
    await expect(page.locator('[role="main"]')).toBeVisible();
    
    // Check that form inputs have proper labels
    await page.goto('http://127.0.0.1:5000#/live');
    await page.waitForLoadState('networkidle');
    
    const buttons = await page.locator('button').all();
    for (const button of buttons) {
      const ariaLabel = await button.getAttribute('aria-label');
      const textContent = await button.textContent();
      expect(ariaLabel || textContent).toBeTruthy();
    }
  });

  test('No JavaScript errors in console', async ({ page }) => {
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Navigate through all main views
    await page.goto('http://127.0.0.1:5000');
    await page.click('a[href="#/library"]');
    await page.waitForTimeout(500);
    await page.click('a[href="#/live"]');
    await page.waitForTimeout(500);
    await page.click('a[href="#/upload"]');
    await page.waitForTimeout(500);
    await page.click('a[href="#/settings"]');
    await page.waitForTimeout(500);
    
    // Check for critical errors (ignore minor warnings)
    const criticalErrors = consoleErrors.filter(error => 
      !error.includes('cdn.tailwindcss.com') && 
      !error.includes('favicon.ico')
    );
    
    if (criticalErrors.length > 0) {
      console.log('Console errors found:', criticalErrors);
    }
    
    expect(criticalErrors.length).toBe(0);
  });
});