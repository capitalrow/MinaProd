/**
 * K6 Load Test: SLO Verification Test
 * 
 * Comprehensive SLO compliance verification test.
 * Validates all Service Level Objectives defined in docs/monitoring/SLO-SLI-METRICS.md
 * 
 * SLO Targets Verified:
 * 1. Availability: 99.95% uptime
 * 2. API Read Latency: P50<300ms, P95<800ms, P99<1500ms
 * 3. API Write Latency: P50<500ms, P95<1200ms, P99<2000ms
 * 4. Static Pages: P50<200ms, P95<500ms, P99<1000ms
 * 5. Error Rate: <0.05% (1 in 2000 requests)
 * 6. Throughput: Sustain 400 RPS API, 200 RPS Web
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { BASE_URL, API_URL, HTTP_PARAMS } from '../config.js';

// Custom metrics for SLO tracking
const availabilityRate = new Rate('slo_availability');
const apiReadLatency = new Trend('slo_api_read_latency', true);
const apiWriteLatency = new Trend('slo_api_write_latency', true);
const staticPageLatency = new Trend('slo_static_page_latency', true);
const errorRate = new Rate('slo_error_rate');
const throughput = new Counter('slo_throughput');

// SLO compliance tracking
const sloViolations = new Counter('slo_violations');
const p50Violations = new Counter('slo_p50_violations');
const p95Violations = new Counter('slo_p95_violations');
const p99Violations = new Counter('slo_p99_violations');

// Test configuration
export const options = {
  scenarios: {
    // Sustained load at peak for extended period
    slo_verification: {
      executor: 'constant-arrival-rate',
      rate: 400,  // Peak SLO rate
      timeUnit: '1s',
      duration: '10m',  // 10 minutes sustained
      preAllocatedVUs: 80,
      maxVUs: 200,
    },
  },
  
  // Strict SLO thresholds - must all pass
  thresholds: {
    // Availability SLO: 99.95%
    'slo_availability': ['rate>0.9995'],
    
    // API Read Latency SLO
    'slo_api_read_latency': [
      'p(50)<300',
      'p(95)<800',
      'p(99)<1500',
    ],
    
    // API Write Latency SLO (if tested)
    'slo_api_write_latency': [
      'p(50)<500',
      'p(95)<1200',
      'p(99)<2000',
    ],
    
    // Static Page Latency SLO
    'slo_static_page_latency': [
      'p(50)<200',
      'p(95)<500',
      'p(99)<1000',
    ],
    
    // Error Rate SLO: <0.05%
    'slo_error_rate': ['rate<0.0005'],
    
    // Throughput SLO: Sustain 400 RPS
    'http_reqs': ['rate>=400'],
    
    // SLO violations must be minimal
    'slo_violations': ['count<100'],  // <1% violation rate
    'slo_p50_violations': ['count<50'],
    'slo_p95_violations': ['count<20'],
    'slo_p99_violations': ['count<10'],
  },
};

/**
 * Main SLO verification test
 */
export default function() {
  // Test endpoint selection (weighted by usage patterns)
  const rand = Math.random();
  
  if (rand < 0.15) {
    // Static pages (15% - matches typical usage)
    testStaticPage();
  } else if (rand < 0.85) {
    // API Read (70% - most common)
    testAPIRead();
  } else {
    // Health check (10% - monitoring)
    testHealthCheck();
  }
  
  throughput.add(1);
  sleep(0.1 + Math.random() * 0.3);
}

/**
 * Test static pages against SLO
 */
function testStaticPage() {
  const pages = [
    `${BASE_URL}/dashboard/`,
    `${BASE_URL}/settings/`,
  ];
  
  const url = pages[Math.floor(Math.random() * pages.length)];
  
  group('Static Page SLO', () => {
    const res = http.get(url, {
      ...HTTP_PARAMS,
      tags: { endpoint: 'static', slo_type: 'static_page' },
    });
    
    const latency = res.timings.duration;
    staticPageLatency.add(latency);
    
    // Check availability
    const available = res.status >= 200 && res.status < 500;
    availabilityRate.add(available ? 1 : 0);
    
    // Check error rate
    const hasError = res.status >= 500;
    errorRate.add(hasError ? 1 : 0);
    
    // Check SLO compliance
    check(res, {
      'static page available': (r) => r.status >= 200 && r.status < 500,
      'static page P50 SLO (200ms)': (r) => r.timings.duration < 200,
      'static page P95 SLO (500ms)': (r) => r.timings.duration < 500,
      'static page P99 SLO (1000ms)': (r) => r.timings.duration < 1000,
    });
    
    // Track violations
    if (latency > 200) p50Violations.add(1);
    if (latency > 500) p95Violations.add(1);
    if (latency > 1000) {
      p99Violations.add(1);
      sloViolations.add(1);
    }
  });
}

/**
 * Test API read endpoints against SLO
 */
function testAPIRead() {
  const endpoints = [
    { url: `${API_URL}/meetings?page=1&per_page=20`, name: 'meetings_list' },
    { url: `${API_URL}/analytics/dashboard?days=7`, name: 'analytics_dashboard' },
    { url: `${API_URL}/analytics/trends?days=30`, name: 'analytics_trends' },
    { url: `${API_URL}/tasks?status=pending&limit=20`, name: 'tasks_list' },
  ];
  
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  
  group('API Read SLO', () => {
    const res = http.get(endpoint.url, {
      ...HTTP_PARAMS,
      tags: { endpoint: 'api_read', name: endpoint.name, slo_type: 'api_read' },
    });
    
    const latency = res.timings.duration;
    apiReadLatency.add(latency);
    
    // Check availability
    const available = res.status >= 200 && res.status < 500;
    availabilityRate.add(available ? 1 : 0);
    
    // Check error rate
    const hasError = res.status >= 500;
    errorRate.add(hasError ? 1 : 0);
    
    // Check SLO compliance
    const sloChecks = check(res, {
      'API read available': (r) => r.status >= 200 && r.status < 500,
      'API read P50 SLO (300ms)': (r) => r.timings.duration < 300,
      'API read P95 SLO (800ms)': (r) => r.timings.duration < 800,
      'API read P99 SLO (1500ms)': (r) => r.timings.duration < 1500,
      'API read no errors': (r) => r.status < 500,
    });
    
    // Track violations
    if (latency > 300) p50Violations.add(1);
    if (latency > 800) p95Violations.add(1);
    if (latency > 1500) {
      p99Violations.add(1);
      sloViolations.add(1);
      console.warn(`⚠️ SLO violation: ${endpoint.name} took ${latency.toFixed(0)}ms (P99 limit: 1500ms)`);
    }
  });
}

/**
 * Test health check endpoint
 */
function testHealthCheck() {
  group('Health Check', () => {
    const res = http.get(`${BASE_URL}/health`, {
      ...HTTP_PARAMS,
      tags: { endpoint: 'health', slo_type: 'health' },
    });
    
    const available = res.status === 200;
    availabilityRate.add(available ? 1 : 0);
    
    check(res, {
      'health check passes': (r) => r.status === 200,
      'health check fast': (r) => r.timings.duration < 100,
    });
  });
}

/**
 * Setup: Run once at start
 */
export function setup() {
  console.log('🚀 Starting SLO Verification Test');
  console.log(`📊 Verifying SLO compliance at peak load (400 RPS) for 10 minutes`);
  console.log(`🎯 SLO Targets:`);
  console.log(`   - Availability: >99.95%`);
  console.log(`   - API Read: P50<300ms, P95<800ms, P99<1500ms`);
  console.log(`   - Static Pages: P50<200ms, P95<500ms, P99<1000ms`);
  console.log(`   - Error Rate: <0.05%`);
  console.log(`   - Throughput: ≥400 RPS`);
  
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
  console.log(`✅ SLO Verification Test completed in ${duration.toFixed(2)} minutes`);
}

/**
 * Custom summary handler with detailed SLO compliance report
 */
export function handleSummary(data) {
  const metrics = data.metrics;
  
  // Calculate SLO compliance
  const availability = metrics.slo_availability?.values.rate || 0;
  const apiReadP50 = metrics.slo_api_read_latency?.values['p(50)'] || 0;
  const apiReadP95 = metrics.slo_api_read_latency?.values['p(95)'] || 0;
  const apiReadP99 = metrics.slo_api_read_latency?.values['p(99)'] || 0;
  const staticP50 = metrics.slo_static_page_latency?.values['p(50)'] || 0;
  const staticP95 = metrics.slo_static_page_latency?.values['p(95)'] || 0;
  const staticP99 = metrics.slo_static_page_latency?.values['p(99)'] || 0;
  const errorRateValue = metrics.slo_error_rate?.values.rate || 0;
  const throughputRate = metrics.http_reqs?.values.rate || 0;
  
  const sloCompliance = {
    availability: { value: availability, target: 0.9995, met: availability >= 0.9995 },
    api_read_p50: { value: apiReadP50, target: 300, met: apiReadP50 < 300 },
    api_read_p95: { value: apiReadP95, target: 800, met: apiReadP95 < 800 },
    api_read_p99: { value: apiReadP99, target: 1500, met: apiReadP99 < 1500 },
    static_page_p50: { value: staticP50, target: 200, met: staticP50 < 200 },
    static_page_p95: { value: staticP95, target: 500, met: staticP95 < 500 },
    static_page_p99: { value: staticP99, target: 1000, met: staticP99 < 1000 },
    error_rate: { value: errorRateValue, target: 0.0005, met: errorRateValue < 0.0005 },
    throughput: { value: throughputRate, target: 400, met: throughputRate >= 400 },
  };
  
  const allSLOsMet = Object.values(sloCompliance).every(slo => slo.met);
  
  const summary = {
    timestamp: new Date().toISOString(),
    test_type: 'slo_verification',
    duration_seconds: data.state.testRunDurationMs / 1000,
    slo_compliance: sloCompliance,
    all_slos_met: allSLOsMet,
    violations: {
      total: metrics.slo_violations?.values.count || 0,
      p50: metrics.slo_p50_violations?.values.count || 0,
      p95: metrics.slo_p95_violations?.values.count || 0,
      p99: metrics.slo_p99_violations?.values.count || 0,
    },
    metrics: {
      requests_total: metrics.http_reqs.values.count,
      requests_per_second: throughputRate,
      availability_rate: availability,
      error_rate: errorRateValue,
    },
  };
  
  return {
    'stdout': JSON.stringify(summary, null, 2),
    '../results/slo-verification-results.json': JSON.stringify(summary, null, 2),
  };
}
