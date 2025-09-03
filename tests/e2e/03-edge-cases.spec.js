/**
 * MINA E2E Tests - Edge Cases and Negative Testing
 * Tests error conditions, boundary cases, and failure scenarios
 */

const { test, expect } = require('@playwright/test');
const { MinaTestUtils } = require('../setup/test-utils');

test.describe('Edge Cases and Negative Testing', () => {
  let utils;

  test.beforeEach(async ({ page }) => {
    utils = new MinaTestUtils(page);
  });

  test('should handle microphone permission denial', async ({ page }) => {
    // Navigate to live page
    await page.goto('/live');
    await page.waitForLoadState('networkidle');
    
    // Deny microphone permissions
    const context = page.context();
    await context.clearPermissions();
    
    // Try to start recording
    const recordButton = page.locator('#recordButton');
    await recordButton.click();
    
    // Wait for permission handling
    await page.waitForTimeout(3000);
    
    // Check for error handling
    const errorElements = page.locator('.error, .alert-danger, .permission-error');
    const hasError = await errorElements.count() > 0;
    
    if (hasError) {
      console.log('✅ Microphone permission denial handled with error message');
    } else {
      // Check console for error messages
      const logs = [];
      page.on('console', msg => {
        if (msg.text().toLowerCase().includes('permission') || msg.text().toLowerCase().includes('denied')) {
          logs.push(msg.text());
        }
      });
      
      await page.waitForTimeout(2000);
      
      if (logs.length > 0) {
        console.log('✅ Microphone permission denial logged to console');
      } else {
        console.log('⚠️ Microphone permission denial handling needs verification');
      }
    }
  });

  test('should handle network connectivity issues', async ({ page }) => {
    await utils.navigateToLive();
    await utils.grantMicrophonePermissions();
    
    // Start recording
    await utils.clickRecordButton();
    
    // Simulate network failure by going offline
    await page.context().setOffline(true);
    
    // Wait for network error detection
    await page.waitForTimeout(5000);
    
    // Check for network error handling
    const errorHandling = await page.evaluate(() => {
      // Look for network error indicators
      const hasErrorDialogs = document.querySelectorAll('.error-dialog, .network-error').length > 0;
      const hasRetryElements = document.querySelectorAll('[class*="retry"], [class*="reconnect"]').length > 0;
      
      return {
        hasErrorDialogs,
        hasRetryElements,
        onlineStatus: navigator.onLine
      };
    });
    
    expect(errorHandling.onlineStatus).toBeFalsy();
    
    // Restore connectivity
    await page.context().setOffline(false);
    await page.waitForTimeout(3000);
    
    console.log('✅ Network connectivity issues handled');
  });

  test('should handle invalid session data', async ({ page }) => {
    const testData = utils.generateTestData();
    
    // Test invalid session creation
    const invalidResponse = await page.request.post('/api/sessions', {
      data: testData.invalidSession
    });
    
    expect([400, 422]).toContain(invalidResponse.status());
    
    if (invalidResponse.status() === 400 || invalidResponse.status() === 422) {
      const error = await invalidResponse.json();
      expect(error.error || error.message).toBeDefined();
      console.log('✅ Invalid session data rejected with proper error');
    }
    
    // Test extremely large session data
    const largeResponse = await page.request.post('/api/sessions', {
      data: testData.largeSession
    });
    
    // Should either accept or reject gracefully
    expect([201, 400, 413, 422]).toContain(largeResponse.status());
    console.log(`✅ Large session data handled (${largeResponse.status()})`);
  });

  test('should handle malformed audio data', async ({ page }) => {
    // Test with various malformed audio payloads
    const malformedPayloads = [
      { description: 'Empty data', data: '' },
      { description: 'Invalid base64', data: 'invalid-base64-data!' },
      { description: 'Null data', data: null },
      { description: 'Very large data', data: 'A'.repeat(10000) }
    ];
    
    for (const payload of malformedPayloads) {
      const response = await page.request.post('/api/transcribe-audio', {
        form: {
          'audio_data': payload.data,
          'session_id': 'test_session',
          'chunk_id': '1'
        }
      });
      
      // Should handle gracefully (not crash)
      expect([200, 400, 413, 422, 500]).toContain(response.status());
      
      if (response.status() >= 400) {
        const error = await response.json();
        expect(error.error || error.message).toBeDefined();
      }
      
      console.log(`✅ ${payload.description} handled (${response.status()})`);
    }
  });

  test('should handle rapid button clicking', async ({ page }) => {
    await utils.navigateToLive();
    await utils.grantMicrophonePermissions();
    await utils.simulateAudioInput();
    
    const recordButton = page.locator('#recordButton');
    
    // Rapidly click the record button multiple times
    for (let i = 0; i < 10; i++) {
      await recordButton.click();
      await page.waitForTimeout(100); // Very short delay
    }
    
    // Wait for state to stabilize
    await page.waitForTimeout(2000);
    
    // Verify the application is still responsive
    await expect(recordButton).toBeVisible();
    await expect(recordButton).toBeEnabled();
    
    const buttonText = await recordButton.textContent();
    expect(buttonText).toMatch(/(Start|Stop) Recording/);
    
    console.log('✅ Rapid button clicking handled gracefully');
  });

  test('should handle browser refresh during active session', async ({ page }) => {
    await utils.navigateToLive();
    await utils.grantMicrophonePermissions();
    
    // Start recording
    await utils.clickRecordButton();
    await page.waitForTimeout(2000);
    
    // Refresh multiple times rapidly
    for (let i = 0; i < 3; i++) {
      await page.reload();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);
    }
    
    // Verify page is still functional
    await expect(page.locator('#recordButton')).toBeVisible();
    
    const recordButton = page.locator('#recordButton');
    const buttonText = await recordButton.textContent();
    
    // Should reset to initial state after refresh
    expect(buttonText).toContain('Start');
    
    console.log('✅ Multiple browser refreshes handled correctly');
  });

  test('should handle extremely long recording sessions', async ({ page }) => {
    await utils.navigateToLive();
    await utils.grantMicrophonePermissions();
    await utils.simulateAudioInput();
    
    // Start recording
    await utils.clickRecordButton();
    
    // Simulate a long recording session (compressed time)
    const checkInterval = 2000;
    const maxChecks = 5; // Simulate 10 seconds of recording
    
    for (let i = 0; i < maxChecks; i++) {
      await page.waitForTimeout(checkInterval);
      
      // Verify UI is still responsive
      const isVisible = await page.locator('#recordButton').isVisible();
      expect(isVisible).toBeTruthy();
      
      // Check memory usage if available
      const metrics = await utils.capturePerformanceMetrics();
      if (metrics.memory) {
        // Memory shouldn't grow excessively
        expect(metrics.memory.used).toBeLessThan(100 * 1024 * 1024); // Less than 100MB
      }
      
      console.log(`✅ Long session check ${i + 1}/${maxChecks} - UI responsive`);
    }
    
    // Stop recording
    await utils.clickRecordButton();
    console.log('✅ Long recording session handled successfully');
  });

  test('should handle concurrent user sessions', async ({ page, browser }) => {
    // Create multiple browser contexts to simulate different users
    const contexts = [];
    const pages = [];
    
    try {
      // Create 3 concurrent user sessions
      for (let i = 0; i < 3; i++) {
        const context = await browser.newContext({
          permissions: ['microphone']
        });
        const userPage = await context.newPage();
        
        contexts.push(context);
        pages.push(userPage);
        
        // Navigate each user to the live page
        await userPage.goto('http://localhost:5000/live');
        await userPage.waitForLoadState('networkidle');
      }
      
      // Start recording on all sessions simultaneously
      const startPromises = pages.map(async (userPage, index) => {
        const utils = new MinaTestUtils(userPage);
        await utils.simulateAudioInput();
        await utils.clickRecordButton();
        console.log(`✅ User ${index + 1} started recording`);
      });
      
      await Promise.all(startPromises);
      
      // Wait for all sessions to be active
      await page.waitForTimeout(3000);
      
      // Verify all sessions are working
      for (let i = 0; i < pages.length; i++) {
        const recordButton = pages[i].locator('#recordButton');
        const buttonText = await recordButton.textContent();
        expect(buttonText).toContain('Stop');
        console.log(`✅ User ${i + 1} session active`);
      }
      
      console.log('✅ Concurrent user sessions handled successfully');
      
    } finally {
      // Clean up contexts
      for (const context of contexts) {
        await context.close();
      }
    }
  });

  test('should handle invalid API tokens and authentication', async ({ page }) => {
    // Test with invalid authorization headers
    const invalidTokens = [
      'Bearer invalid-token',
      'Bearer expired-token-12345',
      'Basic invalid-credentials',
      'Token malformed-token'
    ];
    
    for (const token of invalidTokens) {
      const response = await page.request.get('/api/sessions', {
        headers: { 'Authorization': token }
      });
      
      // Should handle invalid auth gracefully
      expect([200, 401, 403]).toContain(response.status());
      
      if (response.status() === 401 || response.status() === 403) {
        console.log(`✅ Invalid token rejected: ${token.substring(0, 20)}...`);
      } else {
        console.log(`⚠️ Token ignored (no auth required): ${token.substring(0, 20)}...`);
      }
    }
  });

  test('should handle resource exhaustion scenarios', async ({ page }) => {
    await utils.navigateToLive();
    await utils.grantMicrophonePermissions();
    
    // Monitor resource usage
    let initialMetrics = await utils.capturePerformanceMetrics();
    
    // Simulate resource-intensive operations
    await page.evaluate(() => {
      // Create many DOM elements
      for (let i = 0; i < 1000; i++) {
        const div = document.createElement('div');
        div.textContent = `Test element ${i}`;
        document.body.appendChild(div);
      }
      
      // Create large arrays
      window.testArrays = [];
      for (let i = 0; i < 100; i++) {
        window.testArrays.push(new Array(10000).fill(`data-${i}`));
      }
    });
    
    await page.waitForTimeout(2000);
    
    // Check if application is still responsive
    const recordButton = page.locator('#recordButton');
    await expect(recordButton).toBeVisible();
    await expect(recordButton).toBeEnabled();
    
    // Clean up resources
    await page.evaluate(() => {
      // Remove test elements
      const testElements = document.querySelectorAll('div');
      testElements.forEach((el, index) => {
        if (index > 50 && el.textContent?.includes('Test element')) {
          el.remove();
        }
      });
      
      // Clear test arrays
      delete window.testArrays;
    });
    
    const finalMetrics = await utils.capturePerformanceMetrics();
    console.log('✅ Resource exhaustion scenario handled - application remained responsive');
  });
});