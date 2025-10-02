# SLO/SLI Metrics Definition

## Overview

This document defines Service Level Indicators (SLIs) and Service Level Objectives (SLOs) for the Mina platform. These metrics form the foundation of our reliability engineering, monitoring, and incident response.

## Terminology

- **SLI (Service Level Indicator)**: A quantitative measure of service quality
- **SLO (Service Level Objective)**: Target value or range for an SLI
- **SLA (Service Level Agreement)**: Formal commitment to customers (typically SLO - 1%)
- **Error Budget**: Allowed failure rate before violating SLO (100% - SLO%)

## Core Platform SLOs

### 1. Availability

**Definition**: Percentage of time the service is operational and accessible

| Metric | SLI | SLO Target | Measurement Period | Error Budget |
|--------|-----|------------|-------------------|--------------|
| **Service Uptime** | % of successful health checks | ≥ 99.9% | 30 days | 43.2 min/month |
| **API Availability** | % of non-5xx responses | ≥ 99.5% | 7 days | 50.4 min/week |
| **WebSocket Availability** | % of successful connections | ≥ 99.5% | 7 days | 50.4 min/week |

**Measurement**:
```python
# Health check success rate
sli_uptime = (successful_health_checks / total_health_checks) * 100

# API availability
sli_api = ((total_requests - error_5xx) / total_requests) * 100

# WebSocket availability
sli_ws = (successful_ws_connections / total_ws_attempts) * 100
```

**Alerting**:
- **Warning**: SLI < 99.9% (within 1 hour window)
- **Critical**: SLI < 99.5% (P1 incident)
- **Page On-Call**: SLI < 99% (P0 incident)

### 2. Latency

**Definition**: Time to complete requests

| Endpoint Type | SLI | SLO Target (p95) | SLO Target (p99) | Measurement |
|--------------|-----|------------------|------------------|-------------|
| **API Read** | Request duration | ≤ 500ms | ≤ 1000ms | Per request |
| **API Write** | Request duration | ≤ 1000ms | ≤ 2000ms | Per request |
| **Page Load** | Time to Interactive | ≤ 2000ms | ≤ 3000ms | Real User Monitoring |
| **WebSocket** | End-to-end transcription | ≤ 400ms | ≤ 800ms | Audio → text latency |

**Measurement**:
```python
# API latency (p95)
sli_api_latency_p95 = percentile(request_durations, 0.95)

# Page load (p95)
sli_page_load_p95 = percentile(time_to_interactive, 0.95)

# WebSocket latency (p95)
sli_ws_latency_p95 = percentile(audio_to_text_latency, 0.95)
```

**Alerting**:
- **Warning**: p95 latency > SLO for 5 minutes
- **Critical**: p95 latency > SLO * 1.5 for 2 minutes
- **Page On-Call**: p99 latency > SLO * 2 for 1 minute

### 3. Error Rate

**Definition**: Percentage of failed requests

| Error Type | SLI | SLO Target | Measurement Period |
|-----------|-----|------------|-------------------|
| **4xx Client Errors** | % of requests | ≤ 5% | 1 hour |
| **5xx Server Errors** | % of requests | ≤ 1% | 1 hour |
| **Transcription Errors** | % of sessions | ≤ 2% | 1 day |
| **Database Errors** | % of queries | ≤ 0.5% | 1 hour |

**Measurement**:
```python
# Server error rate
sli_error_rate = (error_5xx_count / total_requests) * 100

# Transcription error rate
sli_transcription_errors = (failed_sessions / total_sessions) * 100

# Database error rate
sli_db_errors = (failed_queries / total_queries) * 100
```

**Alerting**:
- **Warning**: Error rate > 1% for 5 minutes
- **Critical**: Error rate > 3% for 2 minutes (P1)
- **Page On-Call**: Error rate > 5% for 1 minute (P0)

### 4. Data Durability

**Definition**: Data loss prevention and backup integrity

| Metric | SLI | SLO Target | Measurement |
|--------|-----|------------|-------------|
| **Data Loss** | % of data preserved | ≥ 99.99% | Monthly |
| **Backup Success** | % of successful backups | ≥ 100% | Daily |
| **Backup Recovery** | % of successful restores | ≥ 100% | Test monthly |

**Measurement**:
```python
# Backup success rate
sli_backup = (successful_backups / total_backup_attempts) * 100

# Recovery success rate  
sli_recovery = (successful_recoveries / total_recovery_tests) * 100
```

**Alerting**:
- **Critical**: Any backup failure (P1)
- **Page On-Call**: Data loss detected (P0)
- **Warning**: Recovery test failure

## Feature-Specific SLOs

### Real-Time Transcription

| Metric | SLI | SLO Target | Notes |
|--------|-----|------------|-------|
| **Transcription Accuracy** | Word Error Rate (WER) | ≤ 10% | Measured on test dataset |
| **Speaker Diarization** | Diarization Error Rate | ≤ 15% | Multi-speaker sessions |
| **Language Detection** | Detection accuracy | ≥ 95% | Auto-detected languages |
| **VAD Accuracy** | Voice activity detection | ≥ 90% | Speech vs silence |

**Measurement**:
```python
# Word Error Rate
wer = (substitutions + deletions + insertions) / total_words * 100

# Diarization Error Rate
der = (speaker_confusion + false_alarms + missed_speech) / total_speech_time * 100
```

### AI Summary Generation

| Metric | SLI | SLO Target | Notes |
|--------|-----|------------|-------|
| **Summary Generation** | Success rate | ≥ 98% | Per session |
| **Summary Latency** | Generation time | ≤ 5s (p95) | After session end |
| **Summary Quality** | User satisfaction | ≥ 4.0/5.0 | User ratings |

### User Authentication

| Metric | SLI | SLO Target | Notes |
|--------|-----|------------|-------|
| **Login Success** | Non-credential-error rate | ≥ 99.5% | Excludes wrong password |
| **Login Latency** | Time to authenticate | ≤ 500ms (p95) | JWT generation |
| **Session Validity** | Invalid session rate | ≤ 0.1% | Unexpected logouts |

## Business Metrics (SLIs)

### User Engagement

| Metric | SLI | Target | Notes |
|--------|-----|--------|-------|
| **Daily Active Users (DAU)** | Count | Growth > 0% MoM | Leading indicator |
| **Session Duration** | Median minutes | ≥ 10 min | Engagement depth |
| **Activation Rate** | % completing first session | ≥ 70% | Onboarding quality |
| **Retention (7-day)** | % returning users | ≥ 40% | Product stickiness |

### Product Performance

| Metric | SLI | Target | Notes |
|--------|-----|--------|-------|
| **Transcription Volume** | Sessions/day | Growth > 0% MoM | Core usage |
| **Average Session Length** | Minutes | ≥ 15 min | Meeting duration proxy |
| **Tasks Created** | Tasks/session | ≥ 2 | Action item extraction |
| **Export Usage** | % sessions exported | ≥ 30% | Value realization |

## Monitoring Implementation

### Data Collection

**Sources**:
1. **Application Metrics**: Gunicorn, Flask middleware
2. **Database Metrics**: PostgreSQL statistics
3. **External Services**: OpenAI API metrics, Redis metrics
4. **Real User Monitoring**: Lighthouse CI, browser performance API
5. **Error Tracking**: Sentry
6. **Uptime Monitoring**: BetterStack (T0.26)

**Collection Frequency**:
- **Real-time**: Health checks (30s interval)
- **Near real-time**: Error rates, latency (1 min aggregation)
- **Periodic**: Transcription quality (hourly aggregation)
- **Batch**: Business metrics (daily aggregation)

### Instrumentation

**Code Example**:
```python
# services/metrics.py
import time
from functools import wraps

class Metrics:
    @staticmethod
    def track_latency(operation_name):
        """Decorator to track operation latency."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    success = True
                    return result
                except Exception as e:
                    success = False
                    raise e
                finally:
                    duration = time.time() - start_time
                    Metrics.record_latency(operation_name, duration)
                    Metrics.record_success(operation_name, success)
            return wrapper
        return decorator
    
    @staticmethod
    def record_latency(operation, duration_ms):
        """Record latency metric."""
        # Send to metrics backend (e.g., Prometheus, Datadog)
        logger.info(f"metric.latency.{operation}", extra={
            "metric_type": "latency",
            "operation": operation,
            "duration_ms": duration_ms
        })
    
    @staticmethod
    def record_success(operation, success):
        """Record success/failure metric."""
        logger.info(f"metric.success.{operation}", extra={
            "metric_type": "success",
            "operation": operation,
            "success": success
        })

# Usage in code
@Metrics.track_latency("api.sessions.create")
def create_session(user_id, title):
    # Implementation
    pass
```

### Dashboard Design

**Required Dashboards**:

1. **Platform Health** (T0.27)
   - Uptime: 99.9% SLO gauge
   - Error rate: 1% SLO gauge
   - Latency (p95, p99): Timeseries
   - Active users: Current count

2. **Real-Time Transcription**
   - WebSocket connections: Current count
   - Transcription latency: p95 timeseries
   - Error rate: Last hour
   - OpenAI API status: Health

3. **Database Performance**
   - Query latency: p95 timeseries
   - Connection pool: Usage gauge
   - Slow queries: Count per hour
   - Replication lag: Milliseconds

4. **Business Metrics**
   - DAU/WAU/MAU: Timeseries
   - Activation rate: % gauge
   - Retention cohorts: Heatmap
   - Revenue (when applicable): Timeseries

## Alert Routing

### Severity Levels

**P0 (Critical - Page On-Call)**:
- Service unavailable (uptime < 99%)
- Data loss detected
- Error rate > 5%
- Security breach detected

**Response**: Immediate (< 5 min)

**P1 (High - Notify On-Call)**:
- SLO violation imminent (error budget < 10%)
- Latency degradation > 50%
- Backup failure
- Error rate > 3%

**Response**: < 30 min during business hours

**P2 (Medium - Create Ticket)**:
- SLO warning (error budget < 25%)
- Non-critical feature degraded
- Performance below target

**Response**: Next business day

**P3 (Low - Dashboard Only)**:
- Informational alerts
- Approaching thresholds
- Capacity planning warnings

**Response**: Reviewed weekly

### Alert Examples

```yaml
# alert-rules.yml
groups:
  - name: availability
    interval: 30s
    rules:
      - alert: ServiceDown
        expr: up{job="mina-api"} == 0
        for: 1m
        labels:
          severity: P0
        annotations:
          summary: "Mina API is down"
          description: "Service has been down for 1 minute"
          
      - alert: HighErrorRate
        expr: (sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) > 0.03
        for: 2m
        labels:
          severity: P1
        annotations:
          summary: "High 5xx error rate"
          description: "Error rate is {{ $value | humanizePercentage }}"
  
  - name: latency
    interval: 1m
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: P2
        annotations:
          summary: "API latency p95 > 500ms"
          description: "p95 latency is {{ $value }}s"
```

## Error Budget Management

### Error Budget Calculation

```python
# Monthly error budget for 99.9% SLO
uptime_target = 0.999
downtime_allowed = (1 - uptime_target) * 30 * 24 * 60  # minutes/month
# = 43.2 minutes per month

# Current error budget remaining
current_uptime = 0.9995  # 99.95%
error_budget_used = (1 - current_uptime) / (1 - uptime_target)
# = 0.5 (50% of error budget consumed)
error_budget_remaining = 1 - error_budget_used  # 50%
```

### Error Budget Policies

**Error Budget > 50%**: 
- Proceed with feature development
- Normal deployment cadence
- Accept reasonable risks

**Error Budget 25-50%**:
- Increase caution in deployments
- Require extra testing
- Consider freezing non-critical features

**Error Budget < 25%**:
- Feature freeze (reliability work only)
- Mandatory postmortems for all incidents
- Increased on-call staffing
- Executive visibility

**Error Budget < 10%**:
- Full deployment freeze
- War room activated
- All hands on reliability
- Customer communication

## Continuous Improvement

### Review Cadence

- **Daily**: Check dashboard, triage alerts
- **Weekly**: Review error budget, discuss trends
- **Monthly**: SLO compliance report, adjust targets
- **Quarterly**: Comprehensive SLO review, business alignment

### SLO Refinement

**When to Adjust SLOs**:
- Consistently exceeding targets (make stricter)
- Consistently missing targets (make realistic)
- Business priorities change
- New features require different standards
- User expectations evolve

**Process**:
1. Propose change with data justification
2. Engineering lead approval required
3. Update this document
4. Communicate to team
5. Update monitoring/alerting
6. Track compliance for 30 days

## Resources

- **Monitoring Dashboard**: (to be created in T0.27)
- **On-Call Runbook**: docs/operations/ON_CALL_RUNBOOK.md (T0.30)
- **Incident Response**: docs/security/PG-1-IMPLEMENTATION-SUMMARY.md
- **Performance Benchmarks**: docs/performance/PG-2-PERFORMANCE-BASELINE.md

## References

- [Google SRE Book - SLIs, SLOs, SLAs](https://sre.google/sre-book/service-level-objectives/)
- [Atlassian SLO Guide](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli)
- [Error Budget Policies](https://sre.google/workbook/error-budget-policy/)

## Version History

- **v1.0** (2025-10-02): Initial SLO/SLI definitions
- Created as part of T0.29 (Define SLO/SLI metrics)
- Covers availability, latency, error rates, data durability
- Includes feature-specific and business metrics
- Defines alert routing and error budget policies
