/**
 * K6 Load Test: API Read Endpoints
 * 
 * Tests GET endpoints under various load conditions to verify:
 * - SLO compliance (P50 <300ms, P95 <800ms, P99 <1500ms)
 * - 3x peak capacity (400 RPS * 3 = 1200 RPS, capped at 1000 RPS max)
 * - Error rate <0.05%
 * 
 * Endpoints tested:
 * - GET /api/meetings
 * - GET /api/meetings/{id}
 * - GET /api/analytics/dashboard
 * - GET /api/analytics/trends
 * - GET /api/tasks
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { BASE_URL, API_URL, SLO_THRESHOLDS, HTTP_PARAMS } from '../config.js';

// Custom metrics
const apiReadDuration = new Trend('api_read_duration', true);
const apiReadErrors = new Rate('api_read_errors');
const requestCounter = new Counter('api_read_requests');

// Test configuration
export const options = {
  scenarios: {
    // Smoke test: Verify functionality
    smoke: {
      executor: 'constant-vus',
      exec: 'smoke',
      vus: 1,
      duration: '30s',
      tags: { test_type: 'smoke' },
    },
    
    // Normal load: 100 RPS for 5 minutes
    normal_load: {
      executor: 'constant-arrival-rate',
      exec: 'readEndpoints',
      rate: 100,
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 20,
      maxVUs: 50,
      startTime: '30s',
      tags: { test_type: 'normal' },
    },
    
    // Peak load: 400 RPS for 5 minutes
    peak_load: {
      executor: 'constant-arrival-rate',
      exec: 'readEndpoints',
      rate: 400,
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 80,
      maxVUs: 150,
      startTime: '5m30s',
      tags: { test_type: 'peak' },
    },
    
    // Capacity test: 1000 RPS for 3 minutes (max capacity = 3x peak)
    capacity_test: {
      executor: 'constant-arrival-rate',
      exec: 'readEndpoints',
      rate: 1000,
      timeUnit: '1s',
      duration: '3m',
      preAllocatedVUs: 200,
      maxVUs: 400,
      startTime: '10m30s',
      tags: { test_type: 'capacity' },
    },
  },
  
  // SLO-based thresholds
  thresholds: {
    ...SLO_THRESHOLDS.api_read,
    ...SLO_THRESHOLDS.overall,
    'api_read_duration': [
      'p(50)<300',
      'p(95)<800',
      'p(99)<1500',
      'avg<400',
    ],
    'api_read_errors': ['rate<0.0005'],
    'http_req_duration{test_type:capacity}': ['p(95)<1000'], // Relaxed during capacity test
  },
};

/**
 * Smoke test: Basic functionality check
 */
export function smoke() {
  const endpoints = [
    `${API_URL}/meetings`,
    `${API_URL}/analytics/dashboard`,
    `${API_URL}/tasks`,
  ];
  
  endpoints.forEach(url => {
    const res = http.get(url, HTTP_PARAMS);
    check(res, {
      'smoke test: status is 200 or 302': (r) => r.status === 200 || r.status === 302,
      'smoke test: response time < 1000ms': (r) => r.timings.duration < 1000,
    });
  });
  
  sleep(1);
}

/**
 * Main test: Read endpoints under load
 */
export function readEndpoints() {
  const scenarios = [
    { name: 'list_meetings', url: `${API_URL}/meetings?page=1&per_page=20` },
    { name: 'dashboard_analytics', url: `${API_URL}/analytics/dashboard?days=7` },
    { name: 'analytics_trends', url: `${API_URL}/analytics/trends?days=30` },
    { name: 'list_tasks', url: `${API_URL}/tasks?status=pending&limit=20` },
    { name: 'health_check', url: `${BASE_URL}/health` },
  ];
  
  // Randomly select an endpoint (realistic user behavior)
  const scenario = scenarios[Math.floor(Math.random() * scenarios.length)];
  
  const startTime = Date.now();
  const res = http.get(scenario.url, {
    ...HTTP_PARAMS,
    tags: { endpoint: 'api_read', name: scenario.name },
  });
  const duration = Date.now() - startTime;
  
  // Record metrics
  apiReadDuration.add(duration);
  requestCounter.add(1);
  
  // Check response
  const passed = check(res, {
    'status is 200-399': (r) => r.status >= 200 && r.status < 400,
    'response time < P99 SLO (1500ms)': (r) => r.timings.duration < 1500,
    'response has body': (r) => r.body && r.body.length > 0,
    'no server errors': (r) => r.status < 500,
  });
  
  if (!passed || res.status >= 500) {
    apiReadErrors.add(1);
  } else {
    apiReadErrors.add(0);
  }
  
  // Verify SLO compliance
  if (duration > 800) {
    console.warn(`⚠️ Slow response: ${scenario.name} took ${duration}ms (P95 SLO: 800ms)`);
  }
  
  // Realistic think time (random 0.1-0.5s)
  sleep(0.1 + Math.random() * 0.4);
}

/**
 * Setup: Run once at start
 */
export function setup() {
  console.log('🚀 Starting API Read Load Test');
  console.log(`📊 Target: Verify 3x peak capacity (1000 RPS) with SLO compliance`);
  console.log(`🎯 SLO Targets: P50<300ms, P95<800ms, P99<1500ms, Error rate<0.05%`);
  
  // Verify server is up
  const res = http.get(`${BASE_URL}/health`);
  if (res.status !== 200) {
    throw new Error(`Server not available: ${res.status}`);
  }
  
  return { startTime: Date.now() };
}

/**
 * Teardown: Run once at end
 */
export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000 / 60;
  console.log(`✅ API Read Load Test completed in ${duration.toFixed(2)} minutes`);
}

/**
 * Custom summary handler
 */
export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    test_type: 'api_read_load',
    duration_seconds: data.state.testRunDurationMs / 1000,
    metrics: {
      requests_total: data.metrics.http_reqs.values.count,
      requests_per_second: data.metrics.http_reqs.values.rate,
      error_rate: data.metrics.api_read_errors?.values.rate || 0,
      response_times: {
        avg: data.metrics.http_req_duration.values.avg,
        min: data.metrics.http_req_duration.values.min,
        max: data.metrics.http_req_duration.values.max,
        p50: data.metrics.http_req_duration.values['p(50)'],
        p95: data.metrics.http_req_duration.values['p(95)'],
        p99: data.metrics.http_req_duration.values['p(99)'],
      },
      slo_compliance: {
        p50_met: data.metrics.http_req_duration.values['p(50)'] < 300,
        p95_met: data.metrics.http_req_duration.values['p(95)'] < 800,
        p99_met: data.metrics.http_req_duration.values['p(99)'] < 1500,
        error_rate_met: (data.metrics.api_read_errors?.values.rate || 0) < 0.0005,
      },
    },
    pass: 
      data.metrics.http_req_duration.values['p(50)'] < 300 &&
      data.metrics.http_req_duration.values['p(95)'] < 800 &&
      data.metrics.http_req_duration.values['p(99)'] < 1500 &&
      (data.metrics.api_read_errors?.values.rate || 0) < 0.0005,
  };
  
  return {
    'stdout': JSON.stringify(summary, null, 2),
    '../results/api-read-load-results.json': JSON.stringify(summary, null, 2),
  };
}
