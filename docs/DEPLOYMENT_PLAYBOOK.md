# Blue/Green Deployment Playbook

## Overview
This playbook documents the step-by-step process for deploying Mina using a blue/green deployment strategy, ensuring zero-downtime releases with instant rollback capabilities.

## Table of Contents
1. [Strategy Overview](#strategy-overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Health Check Validation](#health-check-validation)
5. [Traffic Switching](#traffic-switching)
6. [Rollback Procedures](#rollback-procedures)
7. [Post-Deployment Tasks](#post-deployment-tasks)
8. [Emergency Procedures](#emergency-procedures)

---

## Strategy Overview

### What is Blue/Green Deployment?
Blue/green deployment runs two identical production environments:
- **Blue Environment**: Currently serving live traffic
- **Green Environment**: New version being prepared for deployment

**Benefits:**
- Zero downtime deployments
- Instant rollback capability (switch traffic back)
- Full smoke testing in production-like environment
- Minimal risk to users

### Mina-Specific Considerations
1. **WebSocket Connections**: Active transcription sessions must be drained before switching
2. **Database Migrations**: Run migrations before traffic switch, designed to be forward+backward compatible
3. **Redis State**: Shared between environments for feature flags and cache
4. **Audio Buffers**: In-memory buffers must complete before server shutdown

---

## Pre-Deployment Checklist

### 1. Code Freeze & Review
- [ ] All PRs merged to `main` branch
- [ ] CI/CD pipeline passed (tests, linting, security scans)
- [ ] Database migrations reviewed and tested in staging
- [ ] Feature flags configured for new features (disabled by default)
- [ ] Release notes drafted
- [ ] Stakeholders notified of deployment window

### 2. Environment Verification
```bash
# Verify staging environment is healthy
curl https://mina-staging.replit.app/api/health
# Expected: {"status": "healthy", "version": "v2.5.0"}

# Verify database connectivity
psql $DATABASE_URL -c "SELECT version();"

# Verify Redis connectivity
redis-cli -u $REDIS_URL ping
# Expected: PONG
```

### 3. Backup Critical Data
```bash
# Backup production database (point-in-time recovery available for last 7 days)
pg_dump $PRODUCTION_DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup integrity
pg_restore --list backup_*.sql | head -10

# Upload backup to S3 (optional, Replit auto-backups daily)
aws s3 cp backup_*.sql s3://mina-backups/$(date +%Y%m%d)/
```

### 4. Smoke Test Suite
```bash
# Run full regression test suite
pytest tests/smoke/ -v --html=report.html

# Expected: All tests pass
# ✅ test_transcription_pipeline PASSED
# ✅ test_session_finalization PASSED  
# ✅ test_websocket_reconnection PASSED
# ✅ test_ai_insights_generation PASSED
```

---

## Step-by-Step Deployment

### Phase 1: Prepare Green Environment (15 minutes)

#### 1.1 Deploy New Code to Green
```bash
# Tag the release
git tag -a v2.5.0 -m "Release v2.5.0: Audio replay + transcript editing"
git push origin v2.5.0

# Deploy to green environment
replit deployments create \
  --name mina-green \
  --version v2.5.0 \
  --env production

# Wait for deployment to complete
replit deployments logs mina-green --follow
```

#### 1.2 Run Database Migrations
```bash
# CRITICAL: Always test migrations in staging FIRST, never downgrade in production!

# Step 1: Test migration in staging environment
export DATABASE_URL=$STAGING_DATABASE_URL
flask db upgrade
flask db current  # Verify migration applied

# Test rollback capability in staging
flask db downgrade -1
flask db upgrade  # Re-apply to confirm reversibility

# Step 2: Apply to production (green environment only)
replit ssh mina-green
export DATABASE_URL=$PRODUCTION_DATABASE_URL

# Run migration (forward-only, never downgrade in production!)
flask db upgrade

# Verify migration applied
flask db current
# Expected: 1a2b3c4d5e6f (head)

# DO NOT run downgrade on production database - rollback must happen in staging only!
```

#### 1.3 Warm Up Green Environment
```bash
# Start services
replit deployments start mina-green

# Warm up Python imports and models
curl https://mina-green.replit.app/api/health

# Pre-compile templates
curl https://mina-green.replit.app/live

# Prime Redis cache with feature flags
curl https://mina-green.replit.app/api/flags
```

### Phase 2: Health Check Validation (10 minutes)

#### 2.1 Application Health Checks
```bash
# Health endpoint check
curl https://mina-green.replit.app/api/health
# Expected: {"status": "healthy", "version": "v2.5.0", "uptime_seconds": 45}

# Database connectivity check
curl https://mina-green.replit.app/api/health/db
# Expected: {"status": "connected", "latency_ms": 12}

# Redis connectivity check
curl https://mina-green.replit.app/api/health/redis
# Expected: {"status": "connected", "latency_ms": 3}

# AI service check
curl https://mina-green.replit.app/api/health/openai
# Expected: {"status": "available", "model": "gpt-4o"}
```

#### 2.2 WebSocket Health Check
```bash
# Test WebSocket connection
wscat -c wss://mina-green.replit.app/socket.io/?transport=websocket

# Send ping event
> {"type": "ping"}

# Expected response within 2s:
< {"type": "pong", "timestamp": 1698123456789}
```

#### 2.3 Critical Path Smoke Tests
```bash
# Test transcription pipeline (using test audio file)
curl -X POST https://mina-green.replit.app/api/sessions \
  -H "Authorization: Bearer $TEST_TOKEN" \
  -d '{"title": "Smoke Test Session"}'
# Expected: {"session_id": 12345, "status": "active"}

# Test segment creation
curl -X POST https://mina-green.replit.app/api/sessions/12345/segments \
  -H "Authorization: Bearer $TEST_TOKEN" \
  -d '{"text": "Test transcription", "speaker": "Speaker 1"}'
# Expected: {"segment_id": 67890, "status": "created"}

# Test session finalization
curl -X POST https://mina-green.replit.app/api/sessions/12345/finalize \
  -H "Authorization: Bearer $TEST_TOKEN"
# Expected: {"status": "finalized", "summary_generated": true}

# Cleanup test session
curl -X DELETE https://mina-green.replit.app/api/sessions/12345 \
  -H "Authorization: Bearer $TEST_TOKEN"
```

#### 2.4 Performance Validation
```bash
# Load test with 100 concurrent users (5 minute duration)
artillery run deployment/load-test.yml \
  --target https://mina-green.replit.app

# Expected metrics:
# - P95 response time < 500ms
# - P99 response time < 1000ms
# - Error rate < 0.1%
# - WebSocket connection success rate > 99.9%
```

### Phase 3: Traffic Switching (5 minutes)

#### 3.1 Drain Blue Environment Connections
```bash
# Enable connection draining (30s grace period)
# IMPORTANT: Admin must be authenticated via Flask-Login before running this command

# Option A: Use admin CLI tool (recommended)
./scripts/admin_drain.sh mina-blue

# Option B: Manual curl with authenticated session cookie
# First, login to get session cookie
SESSION_COOKIE=$(curl -X POST https://mina-blue.replit.app/api/auth/login \
  -d "username=$ADMIN_USER&password=$ADMIN_PASS" \
  -c - | grep session | awk '{print $7}')

# Then call drain endpoint with authenticated session
curl -X POST https://mina-blue.replit.app/admin/drain \
  -b "session=$SESSION_COOKIE"

# Monitor active connections
watch -n 1 'curl -s https://mina-blue.replit.app/api/metrics/connections'

# Wait for connections to drain to 0
# Active WebSocket connections: 247 → 156 → 78 → 23 → 5 → 0
```

#### 3.2 Switch Traffic (Load Balancer)
```bash
# Option A: Replit Deployments (automatic)
replit deployments switch \
  --from mina-blue \
  --to mina-green \
  --confirm

# Option B: Manual (nginx/HAProxy config update)
# Edit load balancer config
upstream mina_backend {
    # server mina-blue.replit.app:443;  # OLD - commented out
    server mina-green.replit.app:443;    # NEW - active
}

# Reload load balancer (zero downtime)
nginx -t && nginx -s reload
# OR
haproxy -f /etc/haproxy/haproxy.cfg -c && systemctl reload haproxy
```

#### 3.3 Verify Traffic Shift
```bash
# Check traffic distribution
curl https://mina.production.com/api/health
# Expected: {"version": "v2.5.0", "environment": "green"}

# Monitor logs for new requests
replit deployments logs mina-green --follow | grep "REQUEST"

# Expected: Requests flowing to green environment
# [2025-10-25 10:15:23] REQUEST GET /api/sessions user_id=12345
# [2025-10-25 10:15:24] REQUEST POST /api/sessions/67890/segments
```

### Phase 4: Post-Switch Monitoring (15 minutes)

#### 4.1 Monitor Error Rates
```bash
# Watch error logs
replit deployments logs mina-green --filter ERROR --follow

# Check error rate metrics
curl https://mina-green.replit.app/api/metrics/errors
# Expected: error_rate_5min < 0.1%

# Monitor Sentry for exceptions
open https://sentry.io/organizations/mina/issues/?query=is:unresolved+environment:production
```

#### 4.2 Monitor Performance
```bash
# Response time percentiles
curl https://mina-green.replit.app/api/metrics/performance
# Expected:
# {
#   "p50_ms": 87,
#   "p95_ms": 245,
#   "p99_ms": 512,
#   "requests_per_second": 342
# }

# WebSocket connection success rate
curl https://mina-green.replit.app/api/metrics/websockets
# Expected: connection_success_rate > 99%
```

#### 4.3 Monitor Business Metrics
```bash
# Active sessions count
curl https://mina-green.replit.app/api/metrics/sessions/active
# Expected: Similar to pre-deployment baseline

# Transcription completion rate
curl https://mina-green.replit.app/api/metrics/transcriptions/completion_rate
# Expected: > 98% (should not drop post-deployment)

# AI insights generation rate
curl https://mina-green.replit.app/api/metrics/ai/insights_success_rate
# Expected: > 95%
```

---

## Health Check Validation

### Automated Health Checks
Create `/api/health` endpoint that validates all critical dependencies:

```python
# routes/health.py
@app.route('/api/health')
def health_check():
    """
    Comprehensive health check for blue/green deployment validation.
    Returns 200 if all systems operational, 503 otherwise.
    """
    checks = {
        'database': check_database_health(),
        'redis': check_redis_health(),
        'openai': check_openai_health(),
        'websockets': check_websocket_health(),
        'disk_space': check_disk_space()
    }
    
    all_healthy = all(check['status'] == 'healthy' for check in checks.values())
    status_code = 200 if all_healthy else 503
    
    return jsonify({
        'status': 'healthy' if all_healthy else 'degraded',
        'version': os.getenv('APP_VERSION', 'unknown'),
        'environment': os.getenv('ENVIRONMENT', 'production'),
        'checks': checks,
        'uptime_seconds': time.time() - app.start_time
    }), status_code

def check_database_health():
    try:
        start = time.time()
        db.session.execute('SELECT 1')
        latency_ms = (time.time() - start) * 1000
        return {'status': 'healthy', 'latency_ms': round(latency_ms, 2)}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}
```

### Load Balancer Health Check Configuration
```nginx
# nginx.conf
upstream mina_green {
    server mina-green.replit.app:443;
    
    # Health check every 5 seconds
    health_check interval=5s fails=2 passes=2 uri=/api/health;
    
    # Mark server down after 2 consecutive failures
    # Mark server up after 2 consecutive successes
}
```

---

## Traffic Switching

### Strategy 1: Instant Switch (Recommended)
- **When**: Low-risk deployments, feature flags protect new code
- **How**: Update load balancer config to point to green
- **Rollback Time**: < 30 seconds

```bash
# Instant switch command
./scripts/switch_traffic.sh blue green --instant
```

### Strategy 2: Gradual Canary Rollout
- **When**: High-risk deployments, major version changes
- **How**: Gradually increase traffic to green (10% → 25% → 50% → 100%)
- **Rollback Time**: < 2 minutes

```bash
# Canary deployment (10% traffic to green)
./scripts/switch_traffic.sh blue green --canary 10

# Wait 10 minutes, monitor metrics
# If healthy, increase to 25%
./scripts/switch_traffic.sh blue green --canary 25

# Continue until 100%
```

### Strategy 3: A/B Test (Specific Users)
- **When**: Testing new features with beta users
- **How**: Route specific user IDs to green environment
- **Rollback Time**: < 1 minute

```nginx
# nginx config for user-based routing
map $http_x_user_id $backend {
    ~^(12345|67890|11111)$ mina-green;  # Beta users
    default mina-blue;                   # Everyone else
}
```

---

## Rollback Procedures

### Scenario 1: Critical Bug Detected (Immediate Rollback)

**Trigger Conditions:**
- Error rate spikes above 5%
- Database connection failures
- AI service completely down
- User-reported critical functionality broken

**Rollback Steps (< 2 minutes):**

```bash
# 1. Immediately switch traffic back to blue
replit deployments switch --from mina-green --to mina-blue --emergency

# 2. Verify traffic switched
curl https://mina.production.com/api/health
# Expected: {"version": "v2.4.5", "environment": "blue"}

# 3. Disable new feature flags (if needed)
curl -X POST https://mina.production.com/admin/flags \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"key": "enable_audio_replay", "enabled": false}'

# 4. Investigate issue in green environment
replit deployments logs mina-green --filter ERROR --since 10m

# 5. Notify stakeholders
./scripts/notify_rollback.sh "Critical bug in v2.5.0 - rolled back to v2.4.5"
```

### Scenario 2: Performance Degradation (Gradual Rollback)

**Trigger Conditions:**
- P95 response time increased by > 50%
- Database query latency > 500ms
- WebSocket connection success rate < 95%

**Rollback Steps (< 5 minutes):**

```bash
# 1. Reduce traffic to green (canary rollback)
./scripts/switch_traffic.sh green blue --canary 75  # Blue gets 75%

# 2. Monitor if performance improves
watch -n 5 'curl https://mina.production.com/api/metrics/performance'

# 3. If performance doesn't improve, full rollback
./scripts/switch_traffic.sh green blue --instant

# 4. Scale blue environment if needed
replit deployments scale mina-blue --instances 4
```

### Scenario 3: Database Migration Issue

**Trigger Conditions:**
- Migration failed halfway
- Data integrity issues detected
- Foreign key constraints violated

**CRITICAL RULE: NEVER downgrade production database! Always roll forward or restore from backup.**

**Rollback Steps:**

```bash
# 1. Immediately switch traffic back to blue (old code that works with current schema)
replit deployments switch --to mina-blue --emergency

# 2. Verify blue environment is serving traffic
curl https://mina.production.com/api/health
# Expected: {"version": "v2.4.5", "environment": "blue"}

# 3. Assess damage in green environment (read-only investigation)
replit ssh mina-green
flask db current  # Check which migration is active

# 4. If data corruption detected, restore from point-in-time backup
# IMPORTANT: Do this in a separate restoration environment, NOT on production
pg_dump $PRODUCTION_DATABASE_URL > pre_restore_backup_$(date +%Y%m%d_%H%M%S).sql

# Restore to last known good state (5 minutes before migration)
pg_restore --clean --if-exists backup_20251025_095500.sql

# 5. Verify data integrity after restore
./scripts/verify_data_integrity.sh

# 6. DO NOT rollback migration - instead, create a forward-fix migration
# Example: If migration added a problematic column, create new migration to modify it
flask db revision -m "Fix migration 1a2b3c - adjust column constraints"

# Edit the new migration to fix the issue (e.g., make column nullable, fix default value)
# vim migrations/versions/2b3c4d5e6f7g_fix_migration.py

# 7. Test fix in staging FIRST
export DATABASE_URL=$STAGING_DATABASE_URL
flask db upgrade  # Apply the fix migration
# Run integration tests to verify fix works

# 8. Apply fix to production once verified in staging
export DATABASE_URL=$PRODUCTION_DATABASE_URL  
flask db upgrade

# 9. Redeploy green with fixed migrations
replit deployments create --version v2.5.1-hotfix

# 10. Post-mortem analysis
./scripts/analyze_migration_failure.sh --include-timeline
```

**Alternative: If corruption is severe and restore is complex**

```bash
# 1. Keep blue serving traffic (it's compatible with current schema)
# Blue stays active while you prepare a fix

# 2. Create a hotfix migration that makes the schema compatible with BOTH versions
# This is called a "compatible schema migration"

# Example: If new migration added NOT NULL constraint that broke blue
# Create a migration that makes the column NULLABLE first
flask db revision -m "Hotfix - make column nullable for compatibility"

# 3. Apply hotfix migration to production
flask db upgrade

# 4. Now blue and green can both work with the schema
# Redeploy green with the corrected migration sequence

# 5. Switch traffic to green once verified
```

---

## Post-Deployment Tasks

### Immediate (Within 1 hour)
- [ ] Monitor error rates for first hour (should stabilize < 0.1%)
- [ ] Verify all background jobs running (AI insights, task extraction)
- [ ] Confirm WebSocket connections stable
- [ ] Check Sentry for new exception types
- [ ] Review performance metrics vs. baseline

### Short-term (Within 24 hours)
- [ ] Gradually enable new feature flags (10% → 25% → 50% → 100%)
- [ ] Monitor user feedback channels (support tickets, Slack)
- [ ] Review database query performance (identify slow queries)
- [ ] Analyze user session recordings (identify UX issues)
- [ ] Decommission blue environment (keep for 7 days as backup)

### Long-term (Within 1 week)
- [ ] Post-deployment retrospective meeting
- [ ] Update deployment playbook with lessons learned
- [ ] Optimize any performance bottlenecks discovered
- [ ] Archive deployment artifacts (logs, metrics, backups)
- [ ] Document any manual interventions required

---

## Emergency Procedures

### Total System Failure

**If both blue and green environments are down:**

```bash
# 1. Check Replit status page
open https://status.replit.com

# 2. Restore from last known good backup
replit deployments create --from-backup mina-backup-20251024

# 3. Restore database to last checkpoint
pg_restore --clean backup_latest.sql

# 4. Start emergency hotline
./scripts/emergency_hotline.sh --activate

# 5. Communicate with users
echo "Service temporarily unavailable. Estimated restoration: 15 minutes" \
  | ./scripts/update_status_page.sh
```

### Data Corruption Detected

```bash
# 1. Immediately take affected tables offline
psql $DATABASE_URL -c "REVOKE ALL ON TABLE sessions FROM PUBLIC;"

# 2. Identify corruption extent
./scripts/analyze_data_corruption.sh

# 3. Restore from point-in-time backup
pg_restore --table sessions backup_20251025_095000.sql

# 4. Verify data integrity
./scripts/verify_data_integrity.sh

# 5. Re-enable access
psql $DATABASE_URL -c "GRANT ALL ON TABLE sessions TO app_user;"
```

### Security Incident

```bash
# 1. Activate incident response team
./scripts/security_incident.sh --severity critical

# 2. Rotate all credentials immediately
./scripts/rotate_secrets.sh --all --force

# 3. Review access logs for breach
./scripts/audit_access_logs.sh --since "2 hours ago"

# 4. Patch vulnerability in emergency hotfix
git checkout -b hotfix/security-patch
# ... make fixes ...
git push && ./scripts/emergency_deploy.sh

# 5. Notify affected users (GDPR compliance)
./scripts/notify_users.sh --template security_breach
```

---

## Appendix: Helper Scripts

### scripts/switch_traffic.sh
```bash
#!/bin/bash
# Usage: ./switch_traffic.sh [from] [to] [--instant|--canary PERCENT]

FROM_ENV=$1
TO_ENV=$2
STRATEGY=${3:-"--instant"}
CANARY_PERCENT=${4:-100}

echo "Switching traffic from $FROM_ENV to $TO_ENV ($STRATEGY)"

if [ "$STRATEGY" == "--instant" ]; then
    replit deployments switch --from $FROM_ENV --to $TO_ENV --confirm
elif [ "$STRATEGY" == "--canary" ]; then
    # Update load balancer weights
    nginx_update_weights $TO_ENV $CANARY_PERCENT
fi

echo "✅ Traffic switched successfully"
```

### scripts/health_check_loop.sh
```bash
#!/bin/bash
# Continuously monitor health endpoint

ENVIRONMENT=$1
INTERVAL=${2:-5}

while true; do
    RESPONSE=$(curl -s https://mina-$ENVIRONMENT.replit.app/api/health)
    STATUS=$(echo $RESPONSE | jq -r '.status')
    
    if [ "$STATUS" != "healthy" ]; then
        echo "❌ UNHEALTHY: $RESPONSE"
        # Send alert
        ./scripts/send_alert.sh "Environment $ENVIRONMENT is unhealthy"
    else
        echo "✅ HEALTHY: $ENVIRONMENT"
    fi
    
    sleep $INTERVAL
done
```

---

## Checklist Summary

### Pre-Deployment
- [ ] Code freeze & CI passed
- [ ] Database backup created
- [ ] Smoke tests passed
- [ ] Stakeholders notified

### Deployment
- [ ] Green environment deployed
- [ ] Database migrations applied
- [ ] Health checks passed
- [ ] Traffic switched to green
- [ ] Monitoring active

### Post-Deployment
- [ ] Error rates normal
- [ ] Performance metrics stable
- [ ] Feature flags enabled
- [ ] Blue environment decommissioned (after 7 days)
- [ ] Retrospective completed

---

**Last Updated:** October 2025  
**Version:** 1.0  
**Owner:** Mina DevOps Team
