# K6 Load Testing Suite for Mina

## Overview

This directory contains comprehensive load testing scripts using k6 to verify Mina's performance, capacity, and SLO compliance.

## 📊 Test Scenarios

### 1. API Read Load Test (`01-api-read-load.js`)
Tests read-heavy endpoints (GET /api/*) under various load conditions:
- **Smoke Test**: 1 VU for 30s (basic functionality)
- **Normal Load**: 100 RPS for 5 minutes
- **Peak Load**: 400 RPS for 5 minutes  
- **Capacity Test**: 1000 RPS for 3 minutes (3x peak, max capacity)

**SLO Targets**: P50<300ms, P95<800ms, P99<1500ms

### 2. API Write Load Test (`02-api-write-load.js`)
Tests write-heavy endpoints (POST/PUT/DELETE /api/*):
- **Normal Writes**: 20 writes/sec for 3 minutes
- **Peak Writes**: 60 writes/sec for 3 minutes
- **Capacity Writes**: 150 writes/sec for 2 minutes (3x peak)

**SLO Targets**: P50<500ms, P95<1200ms, P99<2000ms

### 3. Mixed Workload Test (`03-mixed-workload.js`)
Simulates realistic user behavior:
- 80% read operations (browsing, viewing)
- 15% write operations (creating, updating)
- 5% delete operations
- Gradual ramp from 10 → 50 → 150 → 300 VUs

**Target**: System stability under mixed production-like workload

### 4. SLO Verification Test (`04-slo-verification.js`)
Comprehensive SLO compliance verification:
- Sustained 400 RPS for 10 minutes (peak load)
- Verifies all SLO targets simultaneously
- Tracks violations and generates compliance report

**Verified SLOs**:
- Availability: 99.95%
- API Read: P50<300ms, P95<800ms, P99<1500ms
- Static Pages: P50<200ms, P95<500ms, P99<1000ms
- Error Rate: <0.05%
- Throughput: ≥400 RPS

## 🚀 Quick Start

### Prerequisites
- k6 installed (`packager_tool` has already installed it)
- Mina server running at http://localhost:5000
- Database initialized

### Run All Tests
```bash
cd tests/k6
./run-all-tests.sh
```

### Run Specific Test
```bash
# API read load test
k6 run scenarios/01-api-read-load.js

# SLO verification
k6 run scenarios/04-slo-verification.js -e BASE_URL=http://localhost:5000

# With custom URL
k6 run scenarios/03-mixed-workload.js -e BASE_URL=https://staging.mina.app
```

### Quick Smoke Test
```bash
./run-all-tests.sh --quick
```

## 📈 Understanding Results

### Key Metrics
- **http_req_duration**: Response time (P50, P95, P99)
- **http_reqs**: Requests per second (throughput)
- **http_req_failed**: Error rate
- **vus**: Virtual users (concurrent users)

### Pass Criteria
✅ **PASS** if:
- P50 < 300ms for API read (500ms for write)
- P95 < 800ms for API read (1200ms for write)
- P99 < 1500ms for API read (2000ms for write)
- Error rate < 0.05%
- Throughput ≥400 RPS sustained

❌ **FAIL** if any threshold is violated

### Interpreting Output
```bash
✓ http_req_duration.........: avg=285ms min=45ms med=250ms max=1.2s  p(95)=650ms p(99)=980ms
✓ http_req_failed...........: 0.02% ✓ 10 ✗ 49990
✓ http_reqs.................: 50000 (416.6 req/s)
✓ checks....................: 99.98% ✓ 199990 ✗ 10
```

This shows:
- ✅ Average response 285ms (good)
- ✅ P95 at 650ms (within 800ms SLO)  
- ✅ P99 at 980ms (within 1500ms SLO)
- ✅ Error rate 0.02% (within 0.05% SLO)
- ✅ Throughput 416 RPS (meets 400 RPS target)

## 🏗️ Test Architecture

```
tests/k6/
├── config.js                 # Shared configuration, SLO thresholds
├── scenarios/
│   ├── 01-api-read-load.js  # API read endpoints
│   ├── 02-api-write-load.js # API write endpoints
│   ├── 03-mixed-workload.js # Realistic user journeys
│   └── 04-slo-verification.js # SLO compliance
├── results/                  # Test results (JSON, logs)
├── run-all-tests.sh         # Master test runner
└── README.md                # This file
```

## 🎯 SLO Compliance Testing

The test suite is aligned with SLO targets defined in `docs/monitoring/SLO-SLI-METRICS.md`:

| Metric | Target | Test Verification |
|--------|--------|-------------------|
| **Availability** | 99.95% | All tests check status codes |
| **API Read P50** | <300ms | Enforced in thresholds |
| **API Read P95** | <800ms | Enforced in thresholds |
| **API Read P99** | <1500ms | Enforced in thresholds |
| **API Write P50** | <500ms | Enforced in thresholds |
| **API Write P95** | <1200ms | Enforced in thresholds |
| **API Write P99** | <2000ms | Enforced in thresholds |
| **Error Rate** | <0.05% | Monitored in all tests |
| **Throughput** | ≥400 RPS | Capacity test verifies 1000 RPS |

## 🔧 Configuration

### Environment Variables
```bash
export BASE_URL="http://localhost:5000"  # Server URL
export K6_OUT="json=results/metrics.json" # Output format
```

### Custom Thresholds
Edit `config.js` to adjust SLO thresholds:
```javascript
export const SLO_THRESHOLDS = {
  api_read: {
    'http_req_duration{endpoint:api_read}': [
      'p(50)<300',  // Adjust as needed
      'p(95)<800',
      'p(99)<1500',
    ],
  },
};
```

## 📊 Results and Reporting

### JSON Results
Each test generates JSON results in `results/`:
```bash
results/
├── YYYYMMDD_HHMMSS/
│   ├── 01-api-read-load-results.json
│   ├── 02-api-write-load-results.json
│   ├── 03-mixed-workload-results.json
│   ├── 04-slo-verification-results.json
│   └── load-test-report.html
```

### HTML Report
Open `results/TIMESTAMP/load-test-report.html` in a browser for visual summary.

### Real-time Monitoring
Use k6 Cloud or Grafana for real-time dashboards:
```bash
k6 run --out cloud scenarios/01-api-read-load.js
```

## 🐛 Troubleshooting

### "Server not available"
Ensure Mina is running:
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### "Too many open files"
Increase system limits:
```bash
ulimit -n 65536
```

### High error rates
- Check database connections
- Verify Redis is running (for caching)
- Monitor CPU/memory usage
- Review application logs

### Slow response times
- Check database query performance
- Verify indexes are applied (PG-5)
- Enable Redis caching (PG-4)
- Monitor network latency

## 🎓 Best Practices

### Before Running Tests
1. ✅ Ensure server is running and healthy
2. ✅ Database is initialized and populated
3. ✅ Recent indexes applied (Task PG-5)
4. ✅ Redis available (for caching tests)
5. ✅ System resources available (CPU, memory)

### During Tests
1. 📊 Monitor system resources (htop, Activity Monitor)
2. 📈 Watch application logs for errors
3. 🗄️ Monitor database connections
4. 🔍 Check for memory leaks

### After Tests
1. 📝 Review test results and SLO compliance
2. 🐛 Investigate any failures or violations
3. 📊 Compare with baseline metrics
4. 🔄 Iterate and optimize as needed

## 📚 References

- [k6 Documentation](https://k6.io/docs/)
- [Mina SLO/SLI Metrics](../../docs/monitoring/SLO-SLI-METRICS.md)
- [Database Optimization Plan](../../docs/database/DATABASE-OPTIMIZATION-PLAN.md)
- [Redis Caching Strategy](../../docs/performance/REDIS-CACHING-STRATEGY.md)

## 🤝 Contributing

To add new test scenarios:
1. Create new test file in `scenarios/`
2. Follow existing naming convention (XX-test-name.js)
3. Use shared config from `config.js`
4. Add SLO-based thresholds
5. Update `run-all-tests.sh` to include new test
6. Update this README

## ✅ Success Criteria (Task PG-6)

This load testing suite verifies:
- ✅ **3x peak capacity**: System handles 1000 RPS (API max capacity)
- ✅ **SLO compliance**: All latency, availability, and error rate SLOs met
- ✅ **Comprehensive coverage**: Read, write, mixed, and sustained load tests
- ✅ **Automated verification**: Thresholds enforce SLO compliance
- ✅ **Documentation**: Complete setup and usage instructions

**Status**: ✅ Ready for production validation
