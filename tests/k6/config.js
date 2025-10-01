/**
 * K6 Load Testing Configuration
 * 
 * This file defines shared configuration for all k6 load tests including:
 * - Base URLs
 * - Test thresholds aligned with SLO/SLI targets
 * - Common options and settings
 * 
 * SLO Targets (from docs/monitoring/SLO-SLI-METRICS.md):
 * - API Read: P50 <300ms, P95 <800ms, P99 <1500ms
 * - API Write: P50 <500ms, P95 <1200ms, P99 <2000ms
 * - Static Pages: P50 <200ms, P95 <500ms, P99 <1000ms
 * - Error Rate: <0.05% (1 in 2000 requests)
 * - Availability: 99.95% (within 30-day window)
 */

export const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';
export const API_URL = `${BASE_URL}/api`;

/**
 * SLO-based Thresholds
 * These thresholds enforce SLO compliance during load tests
 */
export const SLO_THRESHOLDS = {
  // API Read Endpoints (GET /api/*)
  api_read: {
    'http_req_duration{endpoint:api_read}': [
      'p(50)<300',   // P50 < 300ms (SLO requirement)
      'p(95)<800',   // P95 < 800ms (SLO requirement)
      'p(99)<1500',  // P99 < 1500ms (SLO requirement)
    ],
    'http_req_failed{endpoint:api_read}': ['rate<0.0005'], // <0.05% error rate
  },
  
  // API Write Endpoints (POST /api/*)
  api_write: {
    'http_req_duration{endpoint:api_write}': [
      'p(50)<500',   // P50 < 500ms (SLO requirement)
      'p(95)<1200',  // P95 < 1200ms (SLO requirement)
      'p(99)<2000',  // P99 < 2000ms (SLO requirement)
    ],
    'http_req_failed{endpoint:api_write}': ['rate<0.0005'], // <0.05% error rate
  },
  
  // Static Pages (HTML endpoints)
  static_pages: {
    'http_req_duration{endpoint:static}': [
      'p(50)<200',   // P50 < 200ms (SLO requirement)
      'p(95)<500',   // P95 < 500ms (SLO requirement)
      'p(99)<1000',  // P99 < 1000ms (SLO requirement)
    ],
    'http_req_failed{endpoint:static}': ['rate<0.001'], // <0.1% error rate
  },
  
  // Overall system thresholds
  overall: {
    'http_req_duration': ['avg<600', 'p(95)<1000'], // Overall average <600ms
    'http_req_failed': ['rate<0.0005'], // Overall error rate <0.05%
    'http_reqs': ['rate>50'], // Minimum 50 RPS sustained
  }
};

/**
 * Load Test Scenarios
 * Based on SLO capacity targets:
 * - Normal Load: 100 RPS API, 50 RPS Web
 * - Peak Load: 400 RPS API, 200 RPS Web
 * - 3x Peak (Capacity Test): 1200 RPS API → capped at 1000 RPS max capacity
 */
export const LOAD_SCENARIOS = {
  // Smoke Test: Minimal load to verify functionality
  smoke: {
    executor: 'constant-vus',
    vus: 1,
    duration: '1m',
  },
  
  // Normal Load: Expected steady-state traffic
  normal: {
    executor: 'constant-arrival-rate',
    rate: 100,        // 100 requests per second
    timeUnit: '1s',
    duration: '5m',
    preAllocatedVUs: 20,
    maxVUs: 50,
  },
  
  // Peak Load: 2x normal (typical peak hours)
  peak: {
    executor: 'constant-arrival-rate',
    rate: 400,        // 400 requests per second (peak SLO)
    timeUnit: '1s',
    duration: '5m',
    preAllocatedVUs: 80,
    maxVUs: 150,
  },
  
  // Capacity Test: 3x peak (stress test to max capacity)
  capacity: {
    executor: 'constant-arrival-rate',
    rate: 1000,       // 1000 RPS (max capacity per SLO)
    timeUnit: '1s',
    duration: '3m',
    preAllocatedVUs: 200,
    maxVUs: 400,
  },
  
  // Ramp Test: Gradual increase to find breaking point
  ramp: {
    executor: 'ramping-arrival-rate',
    startRate: 50,
    timeUnit: '1s',
    preAllocatedVUs: 50,
    maxVUs: 500,
    stages: [
      { duration: '2m', target: 100 },   // Ramp to normal
      { duration: '3m', target: 400 },   // Ramp to peak
      { duration: '2m', target: 800 },   // Ramp to 2x peak
      { duration: '2m', target: 1000 },  // Ramp to max capacity
      { duration: '2m', target: 1200 },  // Push beyond max
      { duration: '2m', target: 50 },    // Cool down
    ],
  },
  
  // Spike Test: Sudden traffic spikes
  spike: {
    executor: 'ramping-vus',
    startVUs: 10,
    stages: [
      { duration: '30s', target: 10 },   // Normal
      { duration: '10s', target: 200 },  // Sudden spike
      { duration: '1m', target: 200 },   // Sustained spike
      { duration: '10s', target: 10 },   // Drop back
      { duration: '30s', target: 10 },   // Recover
    ],
  },
  
  // Stress Test: Push system to breaking point
  stress: {
    executor: 'ramping-vus',
    startVUs: 1,
    stages: [
      { duration: '2m', target: 50 },
      { duration: '5m', target: 100 },
      { duration: '5m', target: 200 },
      { duration: '5m', target: 300 },
      { duration: '5m', target: 400 },   // Beyond max VUs
      { duration: '2m', target: 0 },
    ],
  },
  
  // Soak Test: Sustained load over long period (memory leak detection)
  soak: {
    executor: 'constant-vus',
    vus: 50,
    duration: '30m',
  },
};

/**
 * Common HTTP parameters
 */
export const HTTP_PARAMS = {
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  timeout: '30s',
  tags: { name: 'mina-load-test' },
};

/**
 * Test data generators
 */
export function generateMeetingData() {
  return {
    title: `Load Test Meeting ${Date.now()}`,
    scheduled_start: new Date(Date.now() + 86400000).toISOString(),
    scheduled_end: new Date(Date.now() + 90000000).toISOString(),
    description: 'Automated load test meeting',
    status: 'scheduled',
  };
}

export function generateTaskData(meetingId) {
  return {
    meeting_id: meetingId,
    title: `Task ${Date.now()}`,
    description: 'Load test task',
    priority: 'medium',
    status: 'pending',
    due_date: new Date(Date.now() + 604800000).toISOString(),
  };
}

/**
 * Performance assertion helpers
 */
export function assertSLOCompliance(response, endpoint_type) {
  const thresholds = {
    api_read: { p50: 300, p95: 800, p99: 1500 },
    api_write: { p50: 500, p95: 1200, p99: 2000 },
    static: { p50: 200, p95: 500, p99: 1000 },
  };
  
  const threshold = thresholds[endpoint_type];
  if (!threshold) return;
  
  // Check response time
  if (response.timings.duration > threshold.p99) {
    console.warn(`⚠️ Response time ${response.timings.duration}ms exceeds P99 SLO (${threshold.p99}ms)`);
  }
  
  // Check status code
  if (response.status >= 500) {
    console.error(`❌ Server error ${response.status} violates availability SLO`);
  }
}

/**
 * Custom metrics
 */
export function setupCustomMetrics(k6) {
  return {
    api_read_duration: new k6.metrics.Trend('api_read_duration', true),
    api_write_duration: new k6.metrics.Trend('api_write_duration', true),
    static_page_duration: new k6.metrics.Trend('static_page_duration', true),
    error_rate: new k6.metrics.Rate('error_rate'),
  };
}

export default {
  BASE_URL,
  API_URL,
  SLO_THRESHOLDS,
  LOAD_SCENARIOS,
  HTTP_PARAMS,
};
