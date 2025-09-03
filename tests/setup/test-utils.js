/**
 * MINA E2E Test Utilities
 * Shared functions and helpers for all test suites
 */

const { expect } = require('@playwright/test');

class MinaTestUtils {
  constructor(page) {
    this.page = page;
    this.baseURL = 'http://localhost:5000';
  }

  /**
   * Navigate to the live transcription page and wait for it to load
   */
  async navigateToLive() {
    await this.page.goto('/live');
    await this.page.waitForLoadState('networkidle');
    
    // Wait for critical elements to be visible
    await expect(this.page.locator('#recordButton')).toBeVisible();
    await expect(this.page.locator('.live-transcript-container, #transcriptContainer')).toBeVisible();
    
    console.log('✅ Live transcription page loaded');
  }

  /**
   * Grant microphone permissions for audio testing
   */
  async grantMicrophonePermissions() {
    const context = this.page.context();
    await context.grantPermissions(['microphone']);
    console.log('✅ Microphone permissions granted');
  }

  /**
   * Click the record button and verify state change
   */
  async clickRecordButton() {
    const recordButton = this.page.locator('#recordButton');
    await expect(recordButton).toBeVisible();
    
    const initialText = await recordButton.textContent();
    console.log(`🎤 Record button initial state: ${initialText}`);
    
    await recordButton.click();
    
    // Wait for state change with timeout
    await this.page.waitForTimeout(2000);
    
    const newText = await recordButton.textContent();
    console.log(`🎤 Record button new state: ${newText}`);
    
    return { initialText, newText };
  }

  /**
   * Wait for transcription to appear in the UI
   */
  async waitForTranscription(timeout = 10000) {
    const transcriptContainer = this.page.locator('.live-transcript-container, #transcriptContainer, .transcript-content');
    
    // Wait for transcription content to appear
    await expect(transcriptContainer).toBeVisible();
    
    // Wait for actual transcription text (not just placeholder)
    await this.page.waitForFunction(() => {
      const container = document.querySelector('.live-transcript-container, #transcriptContainer, .transcript-content');
      const text = container?.textContent || '';
      return text.length > 50 && !text.includes('Click "Start Recording"');
    }, { timeout });
    
    const transcriptText = await transcriptContainer.textContent();
    console.log(`📝 Transcription detected: ${transcriptText.substring(0, 100)}...`);
    
    return transcriptText;
  }

  /**
   * Create a new session via API
   */
  async createSession(sessionData = {}) {
    const defaultData = {
      title: `Test Session ${Date.now()}`,
      language: 'en',
      enable_speaker_detection: true
    };
    
    const response = await this.page.request.post('/api/sessions', {
      data: { ...defaultData, ...sessionData },
      headers: { 'Content-Type': 'application/json' }
    });
    
    expect(response.status()).toBe(201);
    const session = await response.json();
    
    console.log(`✅ Session created: ${session.session_id}`);
    return session;
  }

  /**
   * Get session details via API
   */
  async getSession(sessionId) {
    const response = await this.page.request.get(`/api/sessions/${sessionId}`);
    expect(response.status()).toBe(200);
    
    const session = await response.json();
    console.log(`📊 Session retrieved: ${sessionId}`);
    
    return session;
  }

  /**
   * End a session via API
   */
  async endSession(sessionId) {
    const response = await this.page.request.post(`/api/sessions/${sessionId}/end`);
    expect(response.status()).toBe(200);
    
    const result = await response.json();
    console.log(`🏁 Session ended: ${sessionId}`);
    
    return result;
  }

  /**
   * Simulate microphone input with fake audio data
   */
  async simulateAudioInput() {
    // Inject JavaScript to simulate MediaRecorder functionality
    await this.page.addInitScript(() => {
      // Mock MediaRecorder for testing
      window.MockMediaRecorder = class {
        constructor(stream, options) {
          this.stream = stream;
          this.options = options;
          this.state = 'inactive';
          this.ondataavailable = null;
          this.onstop = null;
          this.onerror = null;
        }
        
        start(timeslice) {
          this.state = 'recording';
          console.log('🎤 Mock MediaRecorder started');
          
          // Simulate audio data chunks
          setTimeout(() => {
            if (this.ondataavailable) {
              const mockBlob = new Blob(['mock audio data'], { type: 'audio/webm' });
              this.ondataavailable({ data: mockBlob });
            }
          }, 1000);
        }
        
        stop() {
          this.state = 'inactive';
          if (this.onstop) {
            this.onstop();
          }
          console.log('⏹️ Mock MediaRecorder stopped');
        }
      };
      
      // Mock getUserMedia
      navigator.mediaDevices.getUserMedia = async () => {
        console.log('🎤 Mock getUserMedia called');
        return new MediaStream();
      };
    });
    
    console.log('🎭 Audio input simulation configured');
  }

  /**
   * Wait for WebSocket connection to be established
   */
  async waitForWebSocketConnection() {
    await this.page.waitForFunction(() => {
      return window.socket && window.socket.connected;
    }, { timeout: 15000 });
    
    console.log('🔌 WebSocket connection established');
  }

  /**
   * Monitor network requests for API calls
   */
  async monitorNetworkRequests() {
    const requests = [];
    
    this.page.on('request', request => {
      if (request.url().includes('/api/')) {
        requests.push({
          url: request.url(),
          method: request.method(),
          timestamp: new Date().toISOString()
        });
      }
    });
    
    this.page.on('response', response => {
      if (response.url().includes('/api/')) {
        const request = requests.find(r => r.url === response.url());
        if (request) {
          request.status = response.status();
          request.responseTime = Date.now();
        }
      }
    });
    
    return requests;
  }

  /**
   * Check application health
   */
  async checkHealth() {
    const response = await this.page.request.get('/health');
    expect(response.status()).toBe(200);
    
    const health = await response.json();
    console.log('💓 Health check:', health.status);
    
    return health;
  }

  /**
   * Capture performance metrics
   */
  async capturePerformanceMetrics() {
    const metrics = await this.page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      const resources = performance.getEntriesByType('resource');
      
      return {
        loadTime: navigation.loadEventEnd - navigation.fetchStart,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
        resourceCount: resources.length,
        memory: performance.memory ? {
          used: performance.memory.usedJSHeapSize,
          total: performance.memory.totalJSHeapSize,
          limit: performance.memory.jsHeapSizeLimit
        } : null
      };
    });
    
    console.log('📊 Performance metrics captured:', metrics);
    return metrics;
  }

  /**
   * Generate test data for various scenarios
   */
  generateTestData() {
    return {
      validSession: {
        title: 'Valid Test Session',
        language: 'en',
        enable_speaker_detection: true
      },
      invalidSession: {
        title: '', // Empty title
        language: 'invalid-lang',
        enable_speaker_detection: 'not-boolean'
      },
      largeSession: {
        title: 'A'.repeat(1000), // Very long title
        language: 'en',
        description: 'B'.repeat(5000) // Large description
      }
    };
  }
}

module.exports = { MinaTestUtils };