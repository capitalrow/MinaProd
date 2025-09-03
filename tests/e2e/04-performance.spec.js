/**
 * MINA E2E Tests - Performance and Load Testing
 * Tests system performance under various load conditions
 */

const { test, expect } = require('@playwright/test');
const { MinaTestUtils } = require('../setup/test-utils');

test.describe('Performance and Load Testing', () => {
  let utils;

  test.beforeEach(async ({ page }) => {
    utils = new MinaTestUtils(page);
  });

  test('should measure page load performance', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/live');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // Capture detailed performance metrics
    const metrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      const resources = performance.getEntriesByType('resource');
      
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
        loadComplete: navigation.loadEventEnd - navigation.fetchStart,
        firstPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-paint')?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-contentful-paint')?.startTime || 0,
        resourceCount: resources.length,
        totalResourceSize: resources.reduce((size, resource) => size + (resource.transferSize || 0), 0),
        largestResource: Math.max(...resources.map(r => r.transferSize || 0)),
        slowestResource: Math.max(...resources.map(r => r.duration || 0))
      };
    });
    
    // Performance assertions
    expect(loadTime).toBeLessThan(5000); // Page should load within 5 seconds
    expect(metrics.domContentLoaded).toBeLessThan(3000); // DOM ready within 3 seconds
    expect(metrics.firstContentfulPaint).toBeLessThan(2000); // FCP within 2 seconds
    expect(metrics.totalResourceSize).toBeLessThan(5 * 1024 * 1024); // Total resources under 5MB
    
    console.log(`✅ Page Load Performance:`);
    console.log(`📊 Total Load Time: ${loadTime}ms`);
    console.log(`📊 DOM Content Loaded: ${metrics.domContentLoaded}ms`);
    console.log(`📊 First Contentful Paint: ${metrics.firstContentfulPaint}ms`);
    console.log(`📊 Resource Count: ${metrics.resourceCount}`);
    console.log(`📊 Total Resource Size: ${(metrics.totalResourceSize / 1024).toFixed(1)}KB`);
  });

  test('should handle multiple concurrent transcription sessions', async ({ page, browser }) => {
    const sessionCount = 5;
    const contexts = [];
    const pages = [];
    const sessions = [];
    
    try {
      console.log(`🚀 Starting ${sessionCount} concurrent sessions...`);
      
      // Create multiple browser contexts
      for (let i = 0; i < sessionCount; i++) {
        const context = await browser.newContext({ permissions: ['microphone'] });
        const userPage = await context.newPage();
        
        contexts.push(context);
        pages.push(userPage);
        
        // Setup each session
        const sessionUtils = new MinaTestUtils(userPage);
        await sessionUtils.navigateToLive();
        await sessionUtils.simulateAudioInput();
      }
      
      const startTime = Date.now();
      
      // Start all sessions simultaneously
      const sessionPromises = pages.map(async (userPage, index) => {
        const sessionUtils = new MinaTestUtils(userPage);
        const session = await sessionUtils.createSession({
          title: `Concurrent Session ${index + 1}`
        });
        sessions.push(session);
        
        // Start recording
        await sessionUtils.clickRecordButton();
        
        console.log(`✅ Session ${index + 1} started`);
        return session;
      });
      
      await Promise.all(sessionPromises);
      
      const setupTime = Date.now() - startTime;
      console.log(`⏱️ All sessions started in ${setupTime}ms`);
      
      // Let sessions run for a period
      await page.waitForTimeout(5000);
      
      // Check server performance during load
      const healthResponse = await page.request.get('/health/detailed');
      expect(healthResponse.status()).toBe(200);
      
      const health = await healthResponse.json();
      console.log(`💓 Server health during load:`, health.status);
      
      // Stop all sessions
      const stopTime = Date.now();
      const stopPromises = pages.map(async (userPage, index) => {
        const sessionUtils = new MinaTestUtils(userPage);
        await sessionUtils.clickRecordButton(); // Stop recording
        
        if (sessions[index]) {
          await sessionUtils.endSession(sessions[index].session_id);
        }
        
        console.log(`⏹️ Session ${index + 1} stopped`);
      });
      
      await Promise.all(stopPromises);
      
      const stopDuration = Date.now() - stopTime;
      console.log(`⏱️ All sessions stopped in ${stopDuration}ms`);
      
      console.log(`✅ Concurrent sessions test completed successfully`);
      
    } finally {
      // Cleanup
      for (const context of contexts) {
        await context.close();
      }
    }
  });

  test('should measure transcription latency', async ({ page }) => {
    await utils.navigateToLive();
    await utils.grantMicrophonePermissions();
    await utils.simulateAudioInput();
    
    // Monitor network requests for transcription
    const transcriptionRequests = [];
    
    page.on('request', request => {
      if (request.url().includes('/api/transcribe')) {
        transcriptionRequests.push({
          url: request.url(),
          startTime: Date.now()
        });
      }
    });
    
    page.on('response', response => {
      if (response.url().includes('/api/transcribe')) {
        const request = transcriptionRequests.find(r => r.url === response.url());
        if (request) {
          request.endTime = Date.now();
          request.latency = request.endTime - request.startTime;
          request.status = response.status();
        }
      }
    });
    
    // Start recording and measure
    const recordingStart = Date.now();
    await utils.clickRecordButton();
    
    // Wait for transcription activity
    await page.waitForTimeout(10000);
    
    // Analyze latency results
    const completedRequests = transcriptionRequests.filter(r => r.latency);
    
    if (completedRequests.length > 0) {
      const avgLatency = completedRequests.reduce((sum, req) => sum + req.latency, 0) / completedRequests.length;
      const maxLatency = Math.max(...completedRequests.map(req => req.latency));
      const minLatency = Math.min(...completedRequests.map(req => req.latency));
      
      // Performance targets
      expect(avgLatency).toBeLessThan(2000); // Average under 2 seconds
      expect(maxLatency).toBeLessThan(5000); // Max under 5 seconds
      
      console.log(`✅ Transcription Latency Metrics:`);
      console.log(`📊 Requests processed: ${completedRequests.length}`);
      console.log(`📊 Average latency: ${avgLatency.toFixed(0)}ms`);
      console.log(`📊 Min latency: ${minLatency}ms`);
      console.log(`📊 Max latency: ${maxLatency}ms`);
    } else {
      console.log('⚠️ No transcription requests completed during test period');
    }
    
    // Stop recording
    await utils.clickRecordButton();
  });

  test('should monitor memory usage during recording', async ({ page }) => {
    await utils.navigateToLive();
    await utils.grantMicrophonePermissions();
    await utils.simulateAudioInput();
    
    // Baseline memory
    const baselineMetrics = await utils.capturePerformanceMetrics();
    
    // Start recording
    await utils.clickRecordButton();
    
    const memorySnapshots = [];
    const monitoringDuration = 15000; // 15 seconds
    const snapshotInterval = 3000; // Every 3 seconds
    
    for (let i = 0; i < monitoringDuration / snapshotInterval; i++) {
      await page.waitForTimeout(snapshotInterval);
      
      const metrics = await utils.capturePerformanceMetrics();
      memorySnapshots.push({
        timestamp: Date.now(),
        memory: metrics.memory,
        resourceCount: metrics.resourceCount
      });
      
      console.log(`📊 Memory snapshot ${i + 1}: ${metrics.memory ? (metrics.memory.used / 1024 / 1024).toFixed(1) + 'MB' : 'N/A'}`);
    }
    
    // Stop recording
    await utils.clickRecordButton();
    
    // Analyze memory trends
    if (memorySnapshots.length > 0 && memorySnapshots[0].memory) {
      const memoryUsages = memorySnapshots.map(s => s.memory.used);
      const maxMemory = Math.max(...memoryUsages);
      const minMemory = Math.min(...memoryUsages);
      const memoryGrowth = memoryUsages[memoryUsages.length - 1] - memoryUsages[0];
      
      // Memory growth should be reasonable
      expect(memoryGrowth).toBeLessThan(50 * 1024 * 1024); // Less than 50MB growth
      expect(maxMemory).toBeLessThan(200 * 1024 * 1024); // Less than 200MB total
      
      console.log(`✅ Memory Usage Analysis:`);
      console.log(`📊 Baseline: ${(baselineMetrics.memory?.used / 1024 / 1024).toFixed(1)}MB`);
      console.log(`📊 Min during recording: ${(minMemory / 1024 / 1024).toFixed(1)}MB`);
      console.log(`📊 Max during recording: ${(maxMemory / 1024 / 1024).toFixed(1)}MB`);
      console.log(`📊 Net growth: ${(memoryGrowth / 1024 / 1024).toFixed(1)}MB`);
    }
  });

  test('should test application under CPU stress', async ({ page }) => {
    await utils.navigateToLive();
    await utils.grantMicrophonePermissions();
    
    // Create CPU intensive operations
    await page.evaluate(() => {
      // Simulate CPU load
      window.cpuStressInterval = setInterval(() => {
        const start = Date.now();
        while (Date.now() - start < 100) {
          // CPU intensive calculation
          Math.random() * Math.random();
        }
      }, 200);
    });
    
    const stressStart = Date.now();
    
    // Try to use the application under stress
    await utils.simulateAudioInput();
    await utils.clickRecordButton();
    
    // Measure responsiveness under stress
    const interactionTimes = [];
    
    for (let i = 0; i < 5; i++) {
      const startTime = Date.now();
      
      // Perform UI interaction
      await page.locator('#diagnosticsBtn').click({ timeout: 5000 });
      
      const endTime = Date.now();
      interactionTimes.push(endTime - startTime);
      
      await page.waitForTimeout(1000);
    }
    
    // Stop recording and stress
    await utils.clickRecordButton();
    
    await page.evaluate(() => {
      if (window.cpuStressInterval) {
        clearInterval(window.cpuStressInterval);
      }
    });
    
    const stressDuration = Date.now() - stressStart;
    const avgInteractionTime = interactionTimes.reduce((sum, time) => sum + time, 0) / interactionTimes.length;
    
    // UI should remain responsive even under stress
    expect(avgInteractionTime).toBeLessThan(3000); // Average interaction under 3 seconds
    
    console.log(`✅ CPU Stress Test Completed:`);
    console.log(`📊 Stress duration: ${stressDuration}ms`);
    console.log(`📊 Average interaction time: ${avgInteractionTime.toFixed(0)}ms`);
    console.log(`📊 Interaction times: ${interactionTimes.map(t => t + 'ms').join(', ')}`);
  });

  test('should measure WebSocket performance', async ({ page }) => {
    await utils.navigateToLive();
    await utils.grantMicrophonePermissions();
    
    // Monitor WebSocket messages
    const wsMessages = [];
    let wsConnected = false;
    
    page.on('websocket', ws => {
      console.log('🔌 WebSocket connection detected');
      wsConnected = true;
      
      ws.on('framereceived', event => {
        wsMessages.push({
          type: 'received',
          timestamp: Date.now(),
          data: event.payload
        });
      });
      
      ws.on('framesent', event => {
        wsMessages.push({
          type: 'sent',
          timestamp: Date.now(),
          data: event.payload
        });
      });
    });
    
    await utils.simulateAudioInput();
    await utils.clickRecordButton();
    
    // Wait for WebSocket activity
    await page.waitForTimeout(10000);
    
    await utils.clickRecordButton(); // Stop
    
    if (wsConnected && wsMessages.length > 0) {
      const messageIntervals = [];
      for (let i = 1; i < wsMessages.length; i++) {
        const interval = wsMessages[i].timestamp - wsMessages[i-1].timestamp;
        messageIntervals.push(interval);
      }
      
      const avgInterval = messageIntervals.reduce((sum, interval) => sum + interval, 0) / messageIntervals.length;
      
      console.log(`✅ WebSocket Performance:`);
      console.log(`📊 Messages exchanged: ${wsMessages.length}`);
      console.log(`📊 Average message interval: ${avgInterval.toFixed(0)}ms`);
      
      // WebSocket should be responsive
      expect(avgInterval).toBeLessThan(5000); // Average interval under 5 seconds
    } else {
      console.log('⚠️ No WebSocket activity detected');
    }
  });

  test('should test rapid session creation and cleanup', async ({ page }) => {
    const sessionCount = 10;
    const sessions = [];
    
    console.log(`🚀 Creating ${sessionCount} sessions rapidly...`);
    
    const creationStart = Date.now();
    
    // Create sessions rapidly
    for (let i = 0; i < sessionCount; i++) {
      const session = await utils.createSession({
        title: `Rapid Session ${i + 1}`,
        language: 'en'
      });
      
      sessions.push(session);
      
      // Small delay to avoid overwhelming
      await page.waitForTimeout(100);
    }
    
    const creationTime = Date.now() - creationStart;
    
    console.log(`✅ Created ${sessions.length} sessions in ${creationTime}ms`);
    
    // Clean up sessions rapidly
    const cleanupStart = Date.now();
    
    const cleanupPromises = sessions.map(async (session, index) => {
      try {
        await utils.endSession(session.session_id);
        console.log(`🧹 Session ${index + 1} cleaned up`);
      } catch (error) {
        console.warn(`⚠️ Session ${index + 1} cleanup failed:`, error.message);
      }
    });
    
    await Promise.all(cleanupPromises);
    
    const cleanupTime = Date.now() - cleanupStart;
    
    console.log(`✅ Cleaned up sessions in ${cleanupTime}ms`);
    
    // Performance expectations
    expect(creationTime).toBeLessThan(sessionCount * 1000); // Under 1 second per session
    expect(cleanupTime).toBeLessThan(sessionCount * 500); // Under 0.5 seconds per cleanup
    
    console.log(`📊 Average creation time: ${(creationTime / sessionCount).toFixed(0)}ms per session`);
    console.log(`📊 Average cleanup time: ${(cleanupTime / sessionCount).toFixed(0)}ms per session`);
  });
});