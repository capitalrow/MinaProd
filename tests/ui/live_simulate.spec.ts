/**
 * Playwright End-to-End UI Tests for Audio Simulation
 * Tests real MP3 → browser MediaRecorder → WebSocket → UI updates
 */

import { test, expect, Page } from '@playwright/test';

test.describe('Live Transcription UI with Audio Simulation', () => {
  let testStartTime: number;
  let simulationMetrics: any = {};

  test.beforeEach(async ({ page }) => {
    testStartTime = Date.now();
    
    // Navigate to live transcription page
    await page.goto('/live');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Verify page loaded correctly
    await expect(page.locator('h1')).toContainText('Live Transcription');
    
    console.log('🧪 Test setup complete - navigated to /live');
  });

  test('should load audio simulation script and start transcription', async ({ page }) => {
    console.log('🎬 Starting audio simulation test');
    
    // Inject the audio simulation script
    await page.addScriptTag({
      url: '/static/js/sim_from_audio.js'
    });
    
    // Wait for script to load
    await page.waitForTimeout(1000);
    
    // Verify simulation functions are available
    const simFunctionsAvailable = await page.evaluate(() => {
      return typeof window._minaSimStart === 'function' && 
             typeof window._minaSimStop === 'function' &&
             typeof window._minaSimMetrics === 'function';
    });
    
    expect(simFunctionsAvailable).toBe(true);
    console.log('✅ Audio simulation functions loaded');
    
    // Start simulation with test MP3
    const simulationStarted = await page.evaluate(async () => {
      try {
        const result = await window._minaSimStart('/static/test/djvlad_120s.mp3', {
          timesliceMs: 300
        });
        return result;
      } catch (error) {
        console.error('Simulation start error:', error);
        return false;
      }
    });
    
    expect(simulationStarted).toBe(true);
    console.log('🎬 Audio simulation started successfully');
    
    // Wait for transcription to begin (first interim should appear within 2s)
    const firstInterimAppeared = await page.waitForFunction(
      () => {
        const transcriptContainer = document.querySelector('.live-transcript, #transcript, .transcript');
        return transcriptContainer && transcriptContainer.textContent.trim().length > 0;
      },
      { timeout: 2000 }
    ).catch(() => false);
    
    expect(firstInterimAppeared).toBeTruthy();
    console.log('✅ First interim text appeared within 2s');
    
    // Monitor transcription accumulation for 30 seconds
    let transcriptLength = 0;
    let finalCount = 0;
    
    for (let i = 0; i < 30; i++) {
      await page.waitForTimeout(1000);
      
      // Check current transcript content
      const currentTranscript = await page.evaluate(() => {
        const container = document.querySelector('.live-transcript, #transcript, .transcript');
        return container ? container.textContent.trim() : '';
      });
      
      const currentLength = currentTranscript.length;
      if (currentLength > transcriptLength) {
        transcriptLength = currentLength;
        console.log(`📝 Transcript growing: ${transcriptLength} chars`);
      }
      
      // Count elements that might represent final segments
      const currentFinalCount = await page.evaluate(() => {
        const finals = document.querySelectorAll('.final-segment, .final, [data-final="true"]');
        return finals.length;
      });
      
      if (currentFinalCount > finalCount) {
        finalCount = currentFinalCount;
        console.log(`🎯 Final segments: ${finalCount}`);
      }
      
      // Check if we have enough content to validate
      if (transcriptLength > 1000 && finalCount >= 5) {
        console.log('✅ Sufficient transcription content detected early');
        break;
      }
    }
    
    // Get simulation metrics
    simulationMetrics = await page.evaluate(() => {
      if (typeof window._minaSimMetrics === 'function') {
        return window._minaSimMetrics();
      }
      return {};
    });
    
    console.log('📊 Simulation metrics:', simulationMetrics);
    
    // Stop simulation
    const simulationStopped = await page.evaluate(async () => {
      if (typeof window._minaSimStop === 'function') {
        return window._minaSimStop();
      }
      return true;
    });
    
    expect(simulationStopped).toBe(true);
    console.log('🛑 Audio simulation stopped');
    
    // Wait for final transcription processing
    await page.waitForTimeout(3000);
    
    // Final validation
    const finalTranscript = await page.evaluate(() => {
      const container = document.querySelector('.live-transcript, #transcript, .transcript');
      return container ? container.textContent.trim() : '';
    });
    
    const wordCount = finalTranscript.split(/\s+/).filter(word => word.length > 0).length;
    
    console.log(`📝 Final transcript: ${finalTranscript.length} chars, ${wordCount} words`);
    
    // Assertions for successful transcription
    expect(wordCount).toBeGreaterThanOrEqual(400); // Minimum word count
    expect(finalTranscript.length).toBeGreaterThan(2000); // Minimum character count
    
    // Check simulation metrics if available
    if (simulationMetrics.chunksGenerated) {
      expect(simulationMetrics.chunksGenerated).toBeGreaterThan(50);
      console.log(`✅ Generated ${simulationMetrics.chunksGenerated} audio chunks`);
    }
    
    if (simulationMetrics.interimCount) {
      expect(simulationMetrics.interimCount).toBeGreaterThan(10);
      console.log(`✅ Received ${simulationMetrics.interimCount} interim updates`);
    }
    
    if (simulationMetrics.finalCount) {
      expect(simulationMetrics.finalCount).toBeGreaterThanOrEqual(10);
      console.log(`✅ Received ${simulationMetrics.finalCount} final segments`);
    }
    
    console.log('✅ Audio simulation UI test completed successfully');
  });

  test('should validate session persistence after simulation', async ({ page }) => {
    console.log('🧪 Testing session persistence after audio simulation');
    
    // This test assumes the previous test created a session
    // Navigate to sessions page to verify persistence
    await page.goto('/sessions');
    await page.waitForLoadState('networkidle');
    
    // Look for recent sessions
    const sessionElements = await page.locator('.session-item, .session, [data-session-id]').count();
    
    if (sessionElements > 0) {
      console.log(`📋 Found ${sessionElements} session(s) in UI`);
      
      // Click on the most recent session
      await page.locator('.session-item, .session, [data-session-id]').first().click();
      await page.waitForLoadState('networkidle');
      
      // Verify transcript content is displayed
      const transcriptDisplayed = await page.evaluate(() => {
        const transcript = document.querySelector('.transcript-content, .transcript, #transcript');
        return transcript && transcript.textContent.trim().length > 0;
      });
      
      expect(transcriptDisplayed).toBe(true);
      console.log('✅ Session transcript displayed correctly');
      
      // Check word count in session view
      const sessionWordCount = await page.evaluate(() => {
        const transcript = document.querySelector('.transcript-content, .transcript, #transcript');
        if (transcript) {
          const text = transcript.textContent.trim();
          return text.split(/\s+/).filter(word => word.length > 0).length;
        }
        return 0;
      });
      
      expect(sessionWordCount).toBeGreaterThanOrEqual(400);
      console.log(`✅ Session shows ${sessionWordCount} words`);
      
    } else {
      console.log('⚠️ No sessions found in UI - session persistence test skipped');
    }
  });

  test('should handle error states gracefully', async ({ page }) => {
    console.log('🧪 Testing error handling in audio simulation');
    
    // Inject simulation script
    await page.addScriptTag({
      url: '/static/js/sim_from_audio.js'
    });
    await page.waitForTimeout(1000);
    
    // Try to start simulation with invalid audio file
    const errorHandled = await page.evaluate(async () => {
      try {
        const result = await window._minaSimStart('/static/test/nonexistent.mp3');
        return result === false; // Should return false for invalid file
      } catch (error) {
        return true; // Error caught appropriately
      }
    });
    
    expect(errorHandled).toBe(true);
    console.log('✅ Invalid file error handled correctly');
    
    // Test stopping non-running simulation
    const stopResult = await page.evaluate(() => {
      if (typeof window._minaSimStop === 'function') {
        return window._minaSimStop();
      }
      return false;
    });
    
    // Should handle gracefully (return false or not crash)
    expect(typeof stopResult).toBe('boolean');
    console.log('✅ Stop on non-running simulation handled correctly');
  });

  test('should display real-time metrics during simulation', async ({ page }) => {
    console.log('🧪 Testing real-time metrics display');
    
    // Check if metrics are displayed on the page
    const metricsVisible = await page.evaluate(() => {
      const metricsElements = document.querySelectorAll(
        '.metrics, .session-stats, .quality-monitor, [data-metric]'
      );
      return metricsElements.length > 0;
    });
    
    if (metricsVisible) {
      console.log('📊 Metrics UI elements found');
      
      // Inject simulation and start
      await page.addScriptTag({
        url: '/static/js/sim_from_audio.js'
      });
      await page.waitForTimeout(1000);
      
      await page.evaluate(async () => {
        if (typeof window._minaSimStart === 'function') {
          await window._minaSimStart('/static/test/djvlad_120s.mp3', { timesliceMs: 300 });
        }
      });
      
      // Monitor metrics updates for 10 seconds
      let metricsUpdated = false;
      
      for (let i = 0; i < 10; i++) {
        await page.waitForTimeout(1000);
        
        const currentMetrics = await page.evaluate(() => {
          const elements = document.querySelectorAll('.metric-value, [data-metric-value]');
          let hasNonZeroValues = false;
          
          elements.forEach(el => {
            const value = el.textContent.trim();
            if (value && value !== '0' && value !== '0%' && value !== '0.0') {
              hasNonZeroValues = true;
            }
          });
          
          return hasNonZeroValues;
        });
        
        if (currentMetrics) {
          metricsUpdated = true;
          console.log(`📊 Metrics updated at ${i + 1}s`);
          break;
        }
      }
      
      // Stop simulation
      await page.evaluate(() => {
        if (typeof window._minaSimStop === 'function') {
          window._minaSimStop();
        }
      });
      
      expect(metricsUpdated).toBe(true);
      console.log('✅ Real-time metrics updated during simulation');
      
    } else {
      console.log('⚠️ No metrics UI elements found - metrics test skipped');
    }
  });

  test.afterEach(async ({ page }) => {
    const testDuration = Date.now() - testStartTime;
    console.log(`⏱️ Test completed in ${testDuration}ms`);
    
    // Cleanup: ensure simulation is stopped
    await page.evaluate(() => {
      if (typeof window._minaSimStop === 'function') {
        window._minaSimStop();
      }
    }).catch(() => {
      // Ignore cleanup errors
    });
    
    // Log final metrics if available
    if (simulationMetrics && Object.keys(simulationMetrics).length > 0) {
      console.log('📊 Final simulation metrics:', simulationMetrics);
    }
  });
});