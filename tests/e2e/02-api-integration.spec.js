/**
 * MINA E2E Tests - API Integration
 * Tests all critical API endpoints and data flows
 */

const { test, expect } = require('@playwright/test');
const { MinaTestUtils } = require('../setup/test-utils');

test.describe('API Integration Tests', () => {
  let utils;

  test.beforeEach(async ({ page }) => {
    utils = new MinaTestUtils(page);
    await utils.checkHealth();
  });

  test('should validate health endpoints', async ({ page }) => {
    // Test basic health endpoint
    const response = await page.request.get('/health');
    expect(response.status()).toBe(200);
    
    const health = await response.json();
    expect(health.status).toBe('healthy');
    
    // Test detailed health endpoint
    const detailedResponse = await page.request.get('/health/detailed');
    expect(detailedResponse.status()).toBe(200);
    
    const detailedHealth = await detailedResponse.json();
    expect(detailedHealth.database).toBeDefined();
    expect(detailedHealth.transcription_service).toBeDefined();
    
    console.log('✅ Health endpoints responding correctly');
  });

  test('should handle session CRUD operations', async ({ page }) => {
    // Create session
    const createResponse = await page.request.post('/api/sessions', {
      data: {
        title: 'API Test Session',
        language: 'en',
        enable_speaker_detection: true
      }
    });
    
    expect(createResponse.status()).toBe(201);
    const session = await createResponse.json();
    expect(session.success).toBeTruthy();
    expect(session.session_id).toBeTruthy();
    
    const sessionId = session.session_id;
    
    // Read session
    const getResponse = await page.request.get(`/api/sessions/${sessionId}`);
    expect(getResponse.status()).toBe(200);
    
    const sessionData = await getResponse.json();
    expect(sessionData.title).toBe('API Test Session');
    expect(sessionData.language).toBe('en');
    
    // Update session (end it)
    const endResponse = await page.request.post(`/api/sessions/${sessionId}/end`);
    expect(endResponse.status()).toBe(200);
    
    const endResult = await endResponse.json();
    expect(endResult.success).toBeTruthy();
    
    console.log('✅ Session CRUD operations working correctly');
  });

  test('should handle transcription API endpoint', async ({ page }) => {
    // Create minimal audio data for testing
    const audioBlob = Buffer.from('mock audio data').toString('base64');
    
    const response = await page.request.post('/api/transcribe-audio', {
      form: {
        'audio_data': audioBlob,
        'session_id': 'test_session',
        'chunk_id': '1'
      }
    });
    
    // Should get a response (success or appropriate error)
    expect([200, 400, 422]).toContain(response.status());
    
    const result = await response.json();
    expect(result).toHaveProperty('success');
    
    if (result.success) {
      expect(result).toHaveProperty('transcript');
      console.log('✅ Transcription API endpoint responded successfully');
    } else {
      expect(result).toHaveProperty('error');
      console.log('⚠️ Transcription API returned expected error:', result.error);
    }
  });

  test('should handle session segments API', async ({ page }) => {
    // Create a session first
    const session = await utils.createSession({
      title: 'Segments Test Session'
    });
    
    const sessionId = session.session_id;
    
    // Get segments (should be empty initially)
    const segmentsResponse = await page.request.get(`/api/sessions/${sessionId}/segments`);
    expect(segmentsResponse.status()).toBe(200);
    
    const segments = await segmentsResponse.json();
    expect(segments.session_id).toBe(sessionId);
    expect(Array.isArray(segments.segments)).toBeTruthy();
    
    // Test pagination parameters
    const paginatedResponse = await page.request.get(`/api/sessions/${sessionId}/segments?limit=10&offset=0`);
    expect(paginatedResponse.status()).toBe(200);
    
    const paginatedSegments = await paginatedResponse.json();
    expect(paginatedSegments.session_id).toBe(sessionId);
    
    console.log('✅ Session segments API working correctly');
  });

  test('should handle export functionality', async ({ page }) => {
    // Create a session
    const session = await utils.createSession({
      title: 'Export Test Session'
    });
    
    const sessionId = session.session_id;
    
    // Test JSON export
    const jsonResponse = await page.request.get(`/api/sessions/${sessionId}/export?format=json`);
    expect(jsonResponse.status()).toBe(200);
    
    const jsonData = await jsonResponse.json();
    expect(jsonData.session).toBeDefined();
    expect(jsonData.segments).toBeDefined();
    
    // Test TXT export
    const txtResponse = await page.request.get(`/api/sessions/${sessionId}/export?format=txt`);
    expect(txtResponse.status()).toBe(200);
    
    const txtContent = await txtResponse.text();
    expect(typeof txtContent).toBe('string');
    
    console.log('✅ Export functionality working correctly');
  });

  test('should validate API error handling', async ({ page }) => {
    // Test non-existent session
    const invalidSessionResponse = await page.request.get('/api/sessions/invalid-session-id');
    expect(invalidSessionResponse.status()).toBe(404);
    
    // Test invalid endpoint
    const invalidEndpointResponse = await page.request.get('/api/invalid-endpoint');
    expect(invalidEndpointResponse.status()).toBe(404);
    
    // Test malformed request
    const malformedResponse = await page.request.post('/api/sessions', {
      data: 'invalid json data'
    });
    expect([400, 422]).toContain(malformedResponse.status());
    
    console.log('✅ API error handling working correctly');
  });

  test('should handle concurrent API requests', async ({ page }) => {
    const concurrentRequests = 5;
    const sessionPromises = [];
    
    // Create multiple sessions concurrently
    for (let i = 0; i < concurrentRequests; i++) {
      const promise = page.request.post('/api/sessions', {
        data: {
          title: `Concurrent Session ${i}`,
          language: 'en'
        }
      });
      sessionPromises.push(promise);
    }
    
    const responses = await Promise.all(sessionPromises);
    
    // All requests should succeed
    responses.forEach((response, index) => {
      expect(response.status()).toBe(201);
      console.log(`✅ Concurrent request ${index + 1} succeeded`);
    });
    
    console.log('✅ Concurrent API requests handled correctly');
  });

  test('should validate API response times', async ({ page }) => {
    const startTime = Date.now();
    
    // Test critical endpoints for response time
    const healthResponse = await page.request.get('/health');
    const healthTime = Date.now() - startTime;
    
    expect(healthResponse.status()).toBe(200);
    expect(healthTime).toBeLessThan(2000); // Less than 2 seconds
    
    const sessionStartTime = Date.now();
    const sessionResponse = await page.request.post('/api/sessions', {
      data: {
        title: 'Performance Test Session',
        language: 'en'
      }
    });
    const sessionTime = Date.now() - sessionStartTime;
    
    expect(sessionResponse.status()).toBe(201);
    expect(sessionTime).toBeLessThan(3000); // Less than 3 seconds
    
    console.log(`✅ API response times acceptable - Health: ${healthTime}ms, Session: ${sessionTime}ms`);
  });

  test('should handle authentication and authorization', async ({ page }) => {
    // Test endpoints that might require authentication
    const protectedEndpoints = [
      '/api/monitoring/dashboard',
      '/api/profiler/status',
      '/internal/metrics/health'
    ];
    
    for (const endpoint of protectedEndpoints) {
      const response = await page.request.get(endpoint);
      
      // Should either work (200) or require auth (401/403) or not exist (404)
      expect([200, 401, 403, 404]).toContain(response.status());
      
      if (response.status() === 401 || response.status() === 403) {
        console.log(`🔒 ${endpoint} requires authentication (${response.status()})`);
      } else if (response.status() === 200) {
        console.log(`✅ ${endpoint} accessible (${response.status()})`);
      } else {
        console.log(`⚠️ ${endpoint} not found (${response.status()})`);
      }
    }
  });
});