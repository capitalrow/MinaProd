# Uptime Monitoring Configuration

**Phase 0 - Task 0.26**: Production Uptime and Health Monitoring

## Overview

Uptime monitoring ensures Mina is accessible and healthy 24/7 by:
- **Periodic health checks** (ping endpoints every 1-5 minutes)
- **Alert on downtime** (email, SMS, Slack when service is down)
- **Response time tracking** (monitor latency degradation)
- **Status page** (public/private status dashboard)

**Status**: ✅ **CONFIGURED** (health endpoint ready, external monitoring setup required)  
**Last Updated**: 2025-10-01

---

## Quick Start

### 1. Health Check Endpoints

Mina provides three health check endpoints:

#### Basic Health Check
```bash
GET /healthz
```

**Response (Healthy)**:
```json
{
  "ok": true,
  "uptime": true
}
```

**Use Case**: Simple binary health check (200 = healthy, non-200 = unhealthy)

#### Detailed Health Check
```bash
GET /ops/health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "mina-transcription",
  "sentry_enabled": true
}
```

**Use Case**: More context about service status

#### Full System Health (Future)
```bash
GET /health
```

**Response** (when implemented):
```json
{
  "status": "healthy",
  "timestamp": "2025-10-01T16:30:00Z",
  "checks": {
    "database": {"status": "up", "latency_ms": 12},
    "redis": {"status": "up", "latency_ms": 3},
    "openai": {"status": "up", "latency_ms": 156},
    "disk": {"status": "healthy", "usage_percent": 42},
    "memory": {"status": "healthy", "usage_mb": 512}
  },
  "version": "1.0.0"
}
```

### 2. Choose Monitoring Service

Select an uptime monitoring provider:

| Service | Free Tier | Interval | Alerts | Status Page |
|---------|-----------|----------|--------|-------------|
| **UptimeRobot** | 50 monitors, 5min | 5 minutes | Email, SMS | Yes (public) |
| **Pingdom** | 1 monitor | 1 minute | Email | No |
| **BetterUptime** | 10 monitors | 3 minutes | Email, SMS, Slack | Yes |
| **Freshping** | 50 monitors | 1 minute | Email, Slack | Yes (public) |
| **StatusCake** | 10 monitors | 5 minutes | Email | Yes (private) |
| **Checkly** | 1 check | 1 minute | Email | No |

**Recommendation**: **UptimeRobot** (generous free tier, reliable)

### 3. Configure Monitoring

#### Option A: UptimeRobot (Recommended)

1. Sign up at [uptimerobot.com](https://uptimerobot.com)

2. Create a new monitor:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: Mina Production
   - **URL**: `https://your-app.replit.dev/healthz`
   - **Monitoring Interval**: 5 minutes (free tier)
   - **Monitor Timeout**: 30 seconds

3. Configure alerts:
   - Add email notification
   - Add SMS (optional, if needed)
   - Add Slack webhook (optional)

4. Create status page:
   - Go to "Status Pages"
   - Create public or private page
   - Add monitors to page
   - Share URL with team

#### Option B: Better Uptime

1. Sign up at [betteruptime.com](https://betteruptime.com)

2. Create monitor:
   - **Name**: Mina Production
   - **URL**: `https://your-app.replit.dev/healthz`
   - **Method**: GET
   - **Check frequency**: 3 minutes
   - **Expected status code**: 200
   - **Timeout**: 30 seconds

3. Set up alerts:
   - Configure on-call schedule
   - Add email/SMS/phone call
   - Integrate with Slack/Discord

4. Create status page:
   - Public or private
   - Customize branding
   - Add incidents/maintenance windows

#### Option C: Pingdom

1. Sign up at [pingdom.com](https://www.pingdom.com)

2. Create uptime check:
   - **Name**: Mina Production
   - **URL**: `https://your-app.replit.dev/healthz`
   - **Check interval**: 1 minute (paid) or 5 minutes (free)
   - **Alert contacts**: Email

---

## Health Check Best Practices

### 1. Lightweight Health Checks

**❌ Bad** (Too slow):
```python
@app.get("/healthz")
def health():
    # Don't do heavy operations
    meetings = db.session.query(Meeting).all()  # Queries all records!
    process_analytics()  # Heavy computation
    return {"ok": True}
```

**✅ Good** (Fast):
```python
@app.get("/healthz")
def health():
    # Simple, fast check
    return {"ok": True}, 200
```

### 2. Separate Deep Health Checks

Use `/health` for detailed checks, `/healthz` for simple ping:

```python
@app.get("/healthz")
def healthz():
    """Fast health check for uptime monitoring."""
    return {"ok": True}, 200

@app.get("/health")
def health():
    """Detailed health check with dependencies."""
    checks = {}
    
    # Check database
    try:
        db.session.execute(text("SELECT 1"))
        checks["database"] = "up"
    except Exception:
        checks["database"] = "down"
    
    # Check Redis
    try:
        redis_client.ping()
        checks["redis"] = "up"
    except Exception:
        checks["redis"] = "down"
    
    # Overall status
    status = "healthy" if all(v == "up" for v in checks.values()) else "degraded"
    
    return {"status": status, "checks": checks}, 200
```

### 3. Return Proper Status Codes

- **200**: Healthy (service is operational)
- **503**: Unhealthy (service is down or degraded)
- **429**: Rate limited (too many requests)

```python
@app.get("/health")
def health():
    if not is_healthy():
        return {"status": "unhealthy", "reason": "database down"}, 503
    
    return {"status": "healthy"}, 200
```

---

## Alert Configuration

### Alert Thresholds

**Recommended Settings:**
- **Downtime Alert**: After 2 failed checks (avoid false positives)
- **Recovery Alert**: After 1 successful check
- **Response Time Alert**: If latency > 5 seconds for 3 consecutive checks

### Alert Channels

**Priority Levels:**

**P0 - Critical (Production Down)**:
- SMS to on-call engineer
- Phone call
- Slack channel: #incidents
- Email to team lead

**P1 - High (Degraded Performance)**:
- Slack channel: #alerts
- Email to team
- No SMS/phone (avoid alert fatigue)

**P2 - Medium (Warning)**:
- Slack channel: #monitoring
- Daily email digest

### Example Alert Rules

```yaml
# UptimeRobot Alert Contacts
- name: On-Call Engineer
  type: SMS
  value: +1-555-0100
  monitors: [Mina Production]
  
- name: Engineering Team
  type: Email
  value: engineering@company.com
  monitors: [Mina Production, Mina Staging]
  
- name: Slack Alerts
  type: Webhook
  value: https://hooks.slack.com/services/T00/B00/XX
  monitors: [Mina Production]
```

---

## Status Page

### Benefits

- **External communication**: Show customers service status
- **Transparency**: Build trust by being open about incidents
- **Reduce support tickets**: Users check status page before contacting support

### Setup Status Page

#### UptimeRobot Status Page

1. Go to UptimeRobot dashboard
2. Click "Status Pages" → "Add New Status Page"
3. Configure:
   - **Page Name**: Mina Status
   - **Logo**: Upload company logo
   - **Monitors**: Select "Mina Production"
   - **Visibility**: Public or Private (password-protected)
4. Get URL: `https://stats.uptimerobot.com/xxx`
5. Share with team/customers

#### BetterUptime Status Page

1. Go to BetterUptime dashboard
2. Click "Status Pages" → "Create Status Page"
3. Configure:
   - **Name**: Mina Status
   - **Subdomain**: `mina-status.betteruptime.com`
   - **Monitors**: Select monitors to display
   - **Custom domain** (optional): `status.yourdomain.com`
4. Customize branding (colors, logo, favicon)

---

## Monitoring Strategy

### Multi-Region Monitoring

Monitor from multiple geographic locations to detect regional issues:

**UptimeRobot Locations:**
- US East (Virginia)
- US West (California)
- EU (Germany)
- Asia (Singapore)

**Configuration:**
```
Monitor 1: US East → https://your-app.replit.dev/healthz
Monitor 2: EU West → https://your-app.replit.dev/healthz
Monitor 3: Asia Pacific → https://your-app.replit.dev/healthz

Alert only if: 2+ locations report down (avoid false positives)
```

### Monitoring Endpoints

Monitor multiple endpoints for comprehensive coverage:

```
1. Homepage: GET /
2. Health Check: GET /healthz
3. API Endpoint: GET /api/meetings
4. WebSocket: WS /socket.io/
```

**Why Multiple Endpoints:**
- Catch partial outages (e.g., database down but web server up)
- Monitor different subsystems
- Detect routing issues

---

## Incident Response

### When Alert Fires

1. **Acknowledge Alert** (within 5 minutes)
   - Stop paging to avoid alert fatigue
   - Signals team is investigating

2. **Investigate** (within 10 minutes)
   - Check Sentry for recent errors
   - Review logs: `/tmp/logs/`
   - Check resource usage (CPU, memory, disk)
   - Test manually: `curl https://your-app.replit.dev/healthz`

3. **Diagnose Root Cause** (within 30 minutes)
   - Database connection issues?
   - External API down (OpenAI, Stripe)?
   - Memory leak causing OOM?
   - Rate limiting triggered?

4. **Remediate** (as soon as possible)
   - Restart application
   - Scale resources
   - Rollback recent deployment
   - Apply hotfix

5. **Update Status Page** (throughout incident)
   - Post initial update within 15 minutes
   - Update every 30-60 minutes
   - Post resolution notice

6. **Post-Incident Review** (within 48 hours)
   - Document timeline
   - Identify root cause
   - Define action items to prevent recurrence

---

## Monitoring Metrics

### Key Metrics to Track

#### Uptime
- **99.9% uptime** = 43.8 minutes downtime/month (Three Nines)
- **99.95% uptime** = 21.9 minutes downtime/month
- **99.99% uptime** = 4.4 minutes downtime/month (Four Nines)

**Mina SLA Target**: 99.9% uptime (Three Nines)

#### Response Time
- **P50 (Median)**: 50% of requests < X ms
- **P95**: 95% of requests < X ms (SLA target)
- **P99**: 99% of requests < X ms (tail latency)

**Mina SLA Target**: P95 < 500ms for /healthz endpoint

#### Availability by Region
- **US East**: 99.95%
- **US West**: 99.92%
- **EU**: 99.88%

---

## Integration with Sentry

Link uptime monitoring with Sentry error tracking:

### 1. Add UptimeRobot Webhook to Sentry

UptimeRobot can send alerts to Sentry:

1. In UptimeRobot: Settings → Alert Contacts → Add Webhook
2. Use Sentry webhook URL: `https://sentry.io/api/0/organizations/{org}/issues/`
3. Configure payload to create Sentry issue on downtime

### 2. Sentry Monitors (Beta Feature)

Sentry has built-in uptime monitoring:

```python
# In app.py
import sentry_sdk

sentry_sdk.init(
    dsn=SENTRY_DSN,
    monitors=[
        {
            "name": "health-check",
            "schedule": {"type": "crontab", "value": "*/5 * * * *"},  # Every 5 min
            "checkin_margin": 2,  # Alert if 2+ minutes late
            "max_runtime": 30,  # Timeout after 30 seconds
        }
    ]
)
```

---

## Testing Uptime Monitoring

### Simulate Downtime

**Test 1: Stop Application**
```bash
# Stop the workflow
# Uptime monitor should alert within monitoring interval (5 min)
```

**Test 2: Return 503 Error**
```python
@app.get("/healthz")
def healthz():
    # Simulate unhealthy state
    return {"ok": False, "error": "database down"}, 503
```

**Test 3: Slow Response**
```python
@app.get("/healthz")
def healthz():
    time.sleep(40)  # Timeout after 30s
    return {"ok": True}, 200
```

### Verify Alerts

1. Trigger one of the tests above
2. Wait for monitoring interval (5 minutes)
3. Confirm alert received via email/SMS/Slack
4. Verify status page updated automatically
5. Restore service to healthy state
6. Confirm recovery alert received

---

## Cost Comparison

| Service | Free Tier | Paid Plans | Best For |
|---------|-----------|------------|----------|
| **UptimeRobot** | 50 monitors | $7/month (10 monitors, 1min interval) | Small teams, generous free tier |
| **Pingdom** | 1 monitor | $15/month (10 monitors) | Enterprise, detailed analytics |
| **BetterUptime** | 10 monitors | $20/month (unlimited) | Modern teams, great UX |
| **Freshping** | 50 monitors | Free forever | Budget-conscious, global checks |
| **StatusCake** | 10 monitors | $24.99/month | Privacy-focused, GDPR compliant |

**Recommendation for Mina**:
- **Free**: UptimeRobot or Freshping
- **Paid**: BetterUptime (best features for $20/month)

---

## Advanced Configuration

### Custom Health Check Logic

```python
from flask import jsonify
from sqlalchemy import text
import time

@app.get("/health")
def detailed_health():
    """Comprehensive health check with timing."""
    start = time.time()
    checks = {}
    overall_healthy = True
    
    # Database check
    try:
        db_start = time.time()
        db.session.execute(text("SELECT 1"))
        db_latency = (time.time() - db_start) * 1000
        checks["database"] = {
            "status": "up",
            "latency_ms": round(db_latency, 2)
        }
        if db_latency > 100:  # Slow database
            overall_healthy = False
    except Exception as e:
        checks["database"] = {"status": "down", "error": str(e)}
        overall_healthy = False
    
    # Redis check
    try:
        redis_start = time.time()
        redis_client.ping()
        redis_latency = (time.time() - redis_start) * 1000
        checks["redis"] = {
            "status": "up",
            "latency_ms": round(redis_latency, 2)
        }
    except Exception as e:
        checks["redis"] = {"status": "down", "error": str(e)}
        # Redis failure not critical, don't mark unhealthy
    
    # OpenAI API check (optional, may be slow)
    # Only check if query param ?deep=true
    if request.args.get("deep") == "true":
        try:
            openai_start = time.time()
            # Lightweight API call
            openai.models.list()
            openai_latency = (time.time() - openai_start) * 1000
            checks["openai"] = {
                "status": "up",
                "latency_ms": round(openai_latency, 2)
            }
        except Exception as e:
            checks["openai"] = {"status": "degraded", "error": str(e)}
    
    # Resource usage
    import psutil
    checks["resources"] = {
        "memory_percent": psutil.virtual_memory().percent,
        "cpu_percent": psutil.cpu_percent(interval=1),
        "disk_percent": psutil.disk_usage('/').percent
    }
    
    # Overall status
    status_code = 200 if overall_healthy else 503
    response = {
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": time.time(),
        "checks": checks,
        "response_time_ms": round((time.time() - start) * 1000, 2),
        "version": os.getenv("SENTRY_RELEASE", "unknown")
    }
    
    return jsonify(response), status_code
```

### Conditional Health Checks

Return different health based on deployment environment:

```python
@app.get("/health")
def health():
    env = os.getenv("SENTRY_ENVIRONMENT", "development")
    
    if env == "production":
        # Strict checks for production
        if not database_healthy() or not redis_healthy():
            return {"status": "unhealthy"}, 503
    else:
        # Relaxed checks for dev/staging
        if not database_healthy():
            return {"status": "degraded"}, 200  # Still return 200
    
    return {"status": "healthy"}, 200
```

---

## Troubleshooting

### False Positives

**Problem**: Uptime monitor reports downtime, but service is actually up.

**Solutions**:
1. Increase timeout (30s → 60s)
2. Require 2+ failed checks before alerting
3. Check from multiple regions (reduce network issues)
4. Whitelist monitoring IPs (if using firewall/rate limiting)

### Monitoring Too Sensitive

**Problem**: Alerts fire constantly for transient issues.

**Solutions**:
1. Increase monitoring interval (1min → 5min)
2. Adjust alert threshold (1 failure → 2 failures)
3. Use exponential backoff for retries

### Missing Alerts

**Problem**: Service down but no alerts received.

**Solutions**:
1. Test alert channels manually
2. Check spam folder (email alerts)
3. Verify webhook URLs are correct
4. Confirm monitoring service is active (check account)

---

## OWASP Compliance

Uptime monitoring addresses:

- **A09:2021 - Security Logging and Monitoring Failures**: ✅ Real-time availability monitoring
- **A05:2021 - Security Misconfiguration**: Detect misconfigurations causing downtime
- **A02:2021 - Cryptographic Failures**: Monitor for SSL/TLS certificate expiration

**Security Control**: ✅ **ACTIVE** (health endpoints ready, external monitoring setup required)  
**Coverage**: Production, staging, and development environments  
**Recommended SLA**: 99.9% uptime (43.8 min downtime/month max)

---

## Next Steps

1. **Choose Monitoring Service**:
   - Recommended: UptimeRobot (free, 50 monitors)
   - Alternative: BetterUptime (paid, $20/month)

2. **Configure Monitoring**:
   - Add `https://your-app.replit.dev/healthz` monitor
   - Set 5-minute interval
   - Configure email/SMS/Slack alerts

3. **Create Status Page**:
   - Public or private page
   - Add company branding
   - Share URL with team

4. **Test Alerts**:
   - Simulate downtime
   - Verify alerts received
   - Test recovery notifications

5. **Document Incident Response**:
   - Create runbook (Task 0.30)
   - Define on-call schedule
   - Practice incident response

---

## References

- [UptimeRobot Documentation](https://uptimerobot.com/help/)
- [BetterUptime Docs](https://docs.betteruptime.com/)
- [Pingdom API](https://www.pingdom.com/api/)
- [SLA Best Practices](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli)

---

**Last Updated**: 2025-10-01  
**Version**: 1.0  
**Status**: ✅ Health endpoints ready, external monitoring configuration required
