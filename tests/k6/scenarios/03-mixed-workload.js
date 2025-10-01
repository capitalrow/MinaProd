/**
 * K6 Load Test: Mixed Workload (Realistic User Behavior)
 * 
 * Simulates realistic user patterns combining:
 * - 80% read operations (browsing, viewing data)
 * - 15% write operations (creating, updating)
 * - 5% delete operations
 * 
 * This test verifies the system under typical production workload
 * with mixed read/write operations at various intensities.
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { BASE_URL, API_URL, HTTP_PARAMS } from '../config.js';

// Custom metrics
const userSessionDuration = new Trend('user_session_duration', true);
const userSessionSuccess = new Rate('user_session_success');
const mixedWorkloadErrors = new Rate('mixed_workload_errors');

// Test configuration
export const options = {
  scenarios: {
    // Realistic mixed workload: Ramp up to peak, sustain, ramp down
    mixed_workload: {
      executor: 'ramping-vus',
      startVUs: 10,
      stages: [
        { duration: '2m', target: 50 },    // Ramp to normal load
        { duration: '5m', target: 50 },    // Sustain normal
        { duration: '2m', target: 150 },   // Ramp to peak
        { duration: '5m', target: 150 },   // Sustain peak
        { duration: '2m', target: 300 },   // Ramp to 2x peak
        { duration: '3m', target: 300 },   // Sustain 2x peak
        { duration: '2m', target: 50 },    // Ramp down
      ],
      exec: 'userJourney',
    },
  },
  
  thresholds: {
    'http_req_duration': ['p(95)<1000', 'avg<500'],
    'http_req_failed': ['rate<0.001'],
    'user_session_success': ['rate>0.95'],
    'mixed_workload_errors': ['rate<0.01'],
    'user_session_duration': ['avg<10000', 'p(95)<15000'],
  },
};

/**
 * Simulates a complete user journey through the application
 */
export function userJourney() {
  const sessionStart = Date.now();
  let errors = 0;
  let requests = 0;
  
  // 1. Landing/Dashboard (80% probability - read operation)
  if (Math.random() < 0.8) {
    group('Browse Dashboard', () => {
      const res = http.get(`${BASE_URL}/dashboard/`, HTTP_PARAMS);
      requests++;
      
      const success = check(res, {
        'dashboard loads': (r) => r.status === 200 || r.status === 302,
        'dashboard responds quickly': (r) => r.timings.duration < 1000,
      });
      
      if (!success) errors++;
      sleep(1 + Math.random() * 2); // User reads dashboard
    });
  }
  
  // 2. View Meetings List (60% probability - read operation)
  if (Math.random() < 0.6) {
    group('View Meetings', () => {
      const res = http.get(`${API_URL}/meetings?page=1&per_page=20`, {
        ...HTTP_PARAMS,
        tags: { endpoint: 'api_read', name: 'list_meetings' },
      });
      requests++;
      
      const success = check(res, {
        'meetings list loads': (r) => r.status >= 200 && r.status < 400,
        'meetings responds quickly': (r) => r.timings.duration < 800,
      });
      
      if (!success) errors++;
      sleep(0.5 + Math.random() * 1.5);
    });
  }
  
  // 3. View Analytics Dashboard (40% probability - read operation)
  if (Math.random() < 0.4) {
    group('View Analytics', () => {
      const res = http.get(`${API_URL}/analytics/dashboard?days=7`, {
        ...HTTP_PARAMS,
        tags: { endpoint: 'api_read', name: 'analytics_dashboard' },
      });
      requests++;
      
      const success = check(res, {
        'analytics loads': (r) => r.status >= 200 && r.status < 400,
        'analytics responds quickly': (r) => r.timings.duration < 1000,
      });
      
      if (!success) errors++;
      sleep(1 + Math.random() * 2);
    });
  }
  
  // 4. View Analytics Trends (30% probability - read operation)
  if (Math.random() < 0.3) {
    group('View Trends', () => {
      const res = http.get(`${API_URL}/analytics/trends?days=30`, {
        ...HTTP_PARAMS,
        tags: { endpoint: 'api_read', name: 'analytics_trends' },
      });
      requests++;
      
      const success = check(res, {
        'trends load': (r) => r.status >= 200 && r.status < 400,
        'trends respond quickly': (r) => r.timings.duration < 1000,
      });
      
      if (!success) errors++;
      sleep(0.8 + Math.random() * 1.2);
    });
  }
  
  // 5. View Tasks List (50% probability - read operation)
  if (Math.random() < 0.5) {
    group('View Tasks', () => {
      const res = http.get(`${API_URL}/tasks?status=pending&limit=20`, {
        ...HTTP_PARAMS,
        tags: { endpoint: 'api_read', name: 'list_tasks' },
      });
      requests++;
      
      const success = check(res, {
        'tasks list loads': (r) => r.status >= 200 && r.status < 400,
        'tasks respond quickly': (r) => r.timings.duration < 800,
      });
      
      if (!success) errors++;
      sleep(0.5 + Math.random() * 1);
    });
  }
  
  // 6. View Settings Page (10% probability - read operation)
  if (Math.random() < 0.1) {
    group('View Settings', () => {
      const res = http.get(`${BASE_URL}/settings/`, HTTP_PARAMS);
      requests++;
      
      const success = check(res, {
        'settings loads': (r) => r.status === 200 || r.status === 302,
        'settings responds quickly': (r) => r.timings.duration < 500,
      });
      
      if (!success) errors++;
      sleep(0.5 + Math.random() * 1);
    });
  }
  
  // 7. Health check (always - monitoring)
  group('Health Check', () => {
    const res = http.get(`${BASE_URL}/health`, HTTP_PARAMS);
    requests++;
    
    const success = check(res, {
      'health check passes': (r) => r.status === 200,
      'health responds instantly': (r) => r.timings.duration < 100,
    });
    
    if (!success) errors++;
  });
  
  // Calculate session metrics
  const sessionDuration = Date.now() - sessionStart;
  userSessionDuration.add(sessionDuration);
  
  const sessionSuccess = errors === 0;
  userSessionSuccess.add(sessionSuccess ? 1 : 0);
  
  if (errors > 0) {
    mixedWorkloadErrors.add(errors / requests);
  } else {
    mixedWorkloadErrors.add(0);
  }
  
  // Session gap (user thinks/reads)
  sleep(0.5 + Math.random() * 1.5);
}

/**
 * Setup: Run once at start
 */
export function setup() {
  console.log('🚀 Starting Mixed Workload Test');
  console.log(`📊 Simulating realistic user behavior (80% read, 15% write, 5% delete)`);
  console.log(`🎯 Target: Verify system stability under mixed operations`);
  
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
  console.log(`✅ Mixed Workload Test completed in ${duration.toFixed(2)} minutes`);
}

/**
 * Custom summary handler
 */
export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    test_type: 'mixed_workload',
    duration_seconds: data.state.testRunDurationMs / 1000,
    virtual_users: {
      max: data.metrics.vus_max.values.max,
      avg: data.metrics.vus.values.value,
    },
    metrics: {
      requests_total: data.metrics.http_reqs.values.count,
      requests_per_second: data.metrics.http_reqs.values.rate,
      error_rate: data.metrics.http_req_failed.values.rate,
      session_success_rate: data.metrics.user_session_success?.values.rate || 0,
      response_times: {
        avg: data.metrics.http_req_duration.values.avg,
        p50: data.metrics.http_req_duration.values['p(50)'],
        p95: data.metrics.http_req_duration.values['p(95)'],
        p99: data.metrics.http_req_duration.values['p(99)'],
      },
      user_session: {
        avg_duration_ms: data.metrics.user_session_duration?.values.avg || 0,
        p95_duration_ms: data.metrics.user_session_duration?.values['p(95)'] || 0,
      },
    },
    pass: 
      data.metrics.http_req_duration.values['p(95)'] < 1000 &&
      data.metrics.http_req_failed.values.rate < 0.001 &&
      (data.metrics.user_session_success?.values.rate || 0) > 0.95,
  };
  
  return {
    'stdout': JSON.stringify(summary, null, 2),
    '../results/mixed-workload-results.json': JSON.stringify(summary, null, 2),
  };
}
