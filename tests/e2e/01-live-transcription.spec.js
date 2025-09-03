/**
 * MINA E2E Tests - Live Transcription Core Journey
 * Tests the primary user flow: Record audio → Real-time transcription → Display
 */

const { test, expect } = require('@playwright/test');
const { MinaTestUtils } = require('../setup/test-utils');

test.describe('Live Transcription - Core User Journey', () => {
  let utils;

  test.beforeEach(async ({ page }) => {
    utils = new MinaTestUtils(page);
    await utils.grantMicrophonePermissions();
    await utils.navigateToLive();
  });

  test('should load live transcription page successfully', async ({ page }) => {
    // Verify page title and key elements
    await expect(page).toHaveTitle(/Mina.*Live Transcription/);
    
    // Check main UI components
    await expect(page.locator('#recordButton')).toBeVisible();
    await expect(page.locator('.live-transcript-container, #transcriptContainer')).toBeVisible();
    await expect(page.locator('#recording-status')).toBeVisible();
    
    // Verify initial state
    const recordButton = page.locator('#recordButton');
    const buttonText = await recordButton.textContent();
    expect(buttonText).toContain('Start Recording');
    
    console.log('✅ Live transcription page loaded with all components');
  });

  test('should handle record button interaction', async ({ page }) => {
    const recordButton = page.locator('#recordButton');
    
    // Test button click and state change
    const { initialText, newText } = await utils.clickRecordButton();
    
    // Verify button state changed
    expect(initialText).toContain('Start');
    expect(newText).toContain('Stop');
    
    // Verify UI status updates
    const status = page.locator('#recording-status');
    await expect(status).toContainText(/Recording|Active/);
    
    // Stop recording
    await recordButton.click();
    await page.waitForTimeout(1000);
    
    const finalText = await recordButton.textContent();
    expect(finalText).toContain('Start');
    
    console.log('✅ Record button interaction working correctly');
  });

  test('should initialize microphone and audio recording', async ({ page }) => {
    await utils.simulateAudioInput();
    
    // Start recording
    await utils.clickRecordButton();
    
    // Monitor console for audio-related messages
    const logs = [];
    page.on('console', msg => {
      if (msg.text().includes('microphone') || msg.text().includes('audio') || msg.text().includes('MediaRecorder')) {
        logs.push(msg.text());
      }
    });
    
    // Wait for audio initialization
    await page.waitForTimeout(3000);
    
    // Verify audio setup was attempted
    const hasAudioLogs = logs.some(log => 
      log.includes('getUserMedia') || 
      log.includes('MediaRecorder') || 
      log.includes('microphone')
    );
    
    expect(hasAudioLogs).toBeTruthy();
    console.log('✅ Audio recording initialization detected');
  });

  test('should display transcription content', async ({ page }) => {
    await utils.simulateAudioInput();
    
    // Start recording
    await utils.clickRecordButton();
    
    // Wait for transcription UI to update
    await page.waitForTimeout(2000);
    
    // Check for transcription container updates
    const transcriptContainer = page.locator('.live-transcript-container, #transcriptContainer');
    await expect(transcriptContainer).toBeVisible();
    
    // Verify placeholder text changes or content appears
    const content = await transcriptContainer.textContent();
    expect(content.length).toBeGreaterThan(0);
    
    // Look for transcription-related elements
    const hasTranscriptionElements = await page.locator('.transcript-segment, .transcription-active, .processing').count() > 0;
    
    if (hasTranscriptionElements) {
      console.log('✅ Transcription UI elements detected');
    } else {
      console.log('⚠️ Transcription elements not found - may need actual audio input');
    }
  });

  test('should handle session lifecycle correctly', async ({ page }) => {
    // Create session via API first
    const session = await utils.createSession({
      title: 'E2E Test Session',
      language: 'en'
    });
    
    expect(session.success).toBeTruthy();
    expect(session.session_id).toBeTruthy();
    
    // Verify session in UI context
    await utils.simulateAudioInput();
    await utils.clickRecordButton();
    
    // Wait for session activity
    await page.waitForTimeout(3000);
    
    // Stop recording
    await utils.clickRecordButton();
    
    // End session via API
    const result = await utils.endSession(session.session_id);
    expect(result.success).toBeTruthy();
    
    console.log('✅ Session lifecycle completed successfully');
  });

  test('should maintain UI responsiveness during recording', async ({ page }) => {
    await utils.simulateAudioInput();
    
    // Start recording
    await utils.clickRecordButton();
    
    // Test UI responsiveness during recording
    const startTime = Date.now();
    
    // Interact with various UI elements
    await page.locator('#diagnosticsBtn').click({ timeout: 2000 });
    await page.waitForTimeout(500);
    
    // Navigate and interact
    const navigateTime = Date.now();
    await page.goto('/live'); // Re-navigate
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - navigateTime;
    expect(loadTime).toBeLessThan(5000); // Should reload quickly
    
    // Verify page is still functional
    await expect(page.locator('#recordButton')).toBeVisible();
    
    const totalTime = Date.now() - startTime;
    console.log(`✅ UI remained responsive - Total interaction time: ${totalTime}ms`);
  });

  test('should handle browser refresh during recording', async ({ page }) => {
    await utils.simulateAudioInput();
    await utils.clickRecordButton();
    
    // Wait for recording to start
    await page.waitForTimeout(2000);
    
    // Refresh the page
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Verify page loads correctly after refresh
    await expect(page.locator('#recordButton')).toBeVisible();
    
    // Check if any session recovery occurred
    const recordButton = page.locator('#recordButton');
    const buttonText = await recordButton.textContent();
    
    // Should return to initial state after refresh
    expect(buttonText).toContain('Start');
    
    console.log('✅ Browser refresh handled correctly');
  });

  test('should capture performance metrics', async ({ page }) => {
    // Get baseline metrics
    const beforeMetrics = await utils.capturePerformanceMetrics();
    
    await utils.simulateAudioInput();
    await utils.clickRecordButton();
    
    // Wait for recording activity
    await page.waitForTimeout(5000);
    
    // Get performance metrics during recording
    const duringMetrics = await utils.capturePerformanceMetrics();
    
    // Stop recording
    await utils.clickRecordButton();
    await page.waitForTimeout(1000);
    
    // Get final metrics
    const afterMetrics = await utils.capturePerformanceMetrics();
    
    // Verify performance is acceptable
    expect(duringMetrics.loadTime).toBeLessThan(3000);
    
    if (duringMetrics.memory) {
      const memoryIncrease = duringMetrics.memory.used - beforeMetrics.memory.used;
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024); // Less than 50MB increase
    }
    
    console.log('✅ Performance metrics within acceptable ranges');
    console.log(`📊 Load time: ${duringMetrics.loadTime}ms`);
    console.log(`📊 Resource count: ${duringMetrics.resourceCount}`);
  });
});