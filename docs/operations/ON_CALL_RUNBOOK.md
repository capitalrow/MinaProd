# On-Call Runbook

## Overview

This runbook provides comprehensive guidance for on-call engineers responding to Mina platform incidents. It covers common scenarios, troubleshooting procedures, escalation paths, and recovery steps.

## Table of Contents

1. [On-Call Responsibilities](#on-call-responsibilities)
2. [Alert Response](#alert-response)
3. [Common Incident Scenarios](#common-incident-scenarios)
4. [Troubleshooting Procedures](#troubleshooting-procedures)
5. [Escalation](#escalation)
6. [Post-Incident](#post-incident)
7. [Tools & Access](#tools--access)

## On-Call Responsibilities

### Primary Duties

- **Respond to alerts** within SLO targets (P0: <5min, P1: <30min)
- **Investigate incidents** using monitoring and logging tools
- **Mitigate issues** to restore service (not necessarily fix root cause)
- **Communicate status** to stakeholders
- **Document incidents** for post-incident review
- **Escalate** when needed

### Shift Expectations

- **Availability**: Respond within target times
- **Equipment**: Laptop with stable internet, phone for PagerDuty
- **Preparation**: Review this runbook before shift
- **Handoff**: Brief incoming on-call engineer

### Rotation Schedule

See PagerDuty rotation or internal wiki for current schedule.

## Alert Response

### Alert Triage Process

```
Alert Received
    ↓
1. Acknowledge (stop alarm)
    ↓
2. Assess Severity
    ↓
3. Check Dashboard
    ↓
4. Review Recent Deployments
    ↓
5. Investigate Logs
    ↓
6. Determine Action
    ├─ Rollback
    ├─ Hotfix
    ├─ Escalate
    └─ Monitor
```

### Severity Assessment

**P0 (Critical)**:
- Complete service outage
- Data loss or corruption
- Security breach
- Error rate > 5%

**Action**: Immediately page entire team, declare incident

**P1 (High)**:
- Partial service degradation
- Error rate 3-5%
- Performance degradation >50%
- Backup failure

**Action**: Investigate immediately, escalate if unresolved in 30min

**P2 (Medium)**:
- Minor feature degradation
- Error rate 1-3%
- Performance degradation 20-50%

**Action**: Investigate during business hours

**P3 (Low)**:
- Informational alerts
- Capacity warnings

**Action**: Create ticket, review weekly

### Initial Response Checklist

- [ ] **Acknowledge alert** in PagerDuty (stop noise)
- [ ] **Check status page**: Are others reporting issues?
- [ ] **Review dashboard**: Confirm impact scope
- [ ] **Check recent deployments**: Was there a recent change?
- [ ] **Post to #incidents**: "Investigating alert: [name]"
- [ ] **Start incident timer**: Note start time

## Common Incident Scenarios

### 1. Service Down (P0)

**Symptoms**:
- Health check failing
- All requests timing out
- Uptime monitor alerting

**Quick Checks**:
```bash
# Check if service is running
curl https://mina.replit.app/health
# Expected: {"status": "healthy"}

# Check Replit console
# Verify workflow is running

# Check logs
tail -f /tmp/logs/Start_application_*.log | grep -i "error\|exception"
```

**Common Causes**:
1. **Application crash**: Check logs for unhandled exceptions
2. **Database connection failure**: Check DATABASE_URL connectivity
3. **Out of memory**: Check resource usage
4. **Bad deployment**: Recent code change broke startup

**Resolution**:
```bash
# Option 1: Restart application
# In Replit: Restart "Start application" workflow

# Option 2: Rollback to last known good version
# See: docs/operations/ROLLBACK_PROCEDURES.md
# Use Replit Checkpoints (fastest)

# Option 3: Emergency hotfix
git revert <bad-commit>
git push origin main
```

**Escalation Trigger**: Service not restored within 15 minutes

### 2. High Error Rate (P1)

**Symptoms**:
- 5xx error rate > 3%
- Sentry showing spike in errors
- User complaints

**Quick Checks**:
```bash
# Check error types in Sentry
# Look for common error message
# Identify affected endpoints

# Check recent deployments
git log --oneline -10

# Check external service status
# OpenAI API status
# Database connectivity
```

**Common Causes**:
1. **OpenAI API degradation**: Check OpenAI status page
2. **Database query timeout**: Check slow query log
3. **Bad code deployment**: Recent bug introduced
4. **Rate limiting hit**: Too many requests to external API

**Resolution**:
```bash
# If external service issue
# Implement circuit breaker or fallback

# If database issue
# Identify and kill long-running queries
psql $DATABASE_URL -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query_start < NOW() - INTERVAL '5 minutes';"

# If code issue
# Rollback deployment
```

**Escalation Trigger**: Error rate not decreasing after 30 minutes

### 3. Slow Performance (P1)

**Symptoms**:
- p95 latency > 1000ms
- Users complaining about slowness
- Timeouts increasing

**Quick Checks**:
```bash
# Check database connection pool
psql $DATABASE_URL -c "SELECT count(*) as total, state FROM pg_stat_activity GROUP BY state;"

# Check slow queries
psql $DATABASE_URL -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check CPU/memory usage
# In Replit console

# Check external API latency
# OpenAI response times
```

**Common Causes**:
1. **Database N+1 queries**: Missing index or eager loading
2. **Memory leak**: Gradual memory increase
3. **External API slowdown**: OpenAI latency spike
4. **Too many concurrent requests**: Need to scale workers

**Resolution**:
```bash
# Add database index (if identified)
# See docs/performance/PG-10 for index strategy

# Restart application (clears memory leak)
# In Replit: Restart workflow

# Increase worker count (if needed)
# Edit: gunicorn --workers 4 (from 2)

# Implement caching for expensive operations
```

**Escalation Trigger**: Latency not improving after 1 hour

### 4. Database Connection Failure (P0/P1)

**Symptoms**:
- "OperationalError: could not connect to server"
- All database queries failing
- Connection pool exhausted

**Quick Checks**:
```bash
# Test database connectivity
psql $DATABASE_URL -c "SELECT 1;"

# Check connection pool status
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Check for long-running transactions
psql $DATABASE_URL -c "SELECT pid, usename, state, query_start, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY query_start;"
```

**Common Causes**:
1. **Connection pool exhausted**: Too many connections
2. **Database server down**: Neon infrastructure issue
3. **Network issue**: Connectivity problem
4. **Long-running transaction**: Blocking other connections

**Resolution**:
```bash
# Kill idle connections
psql $DATABASE_URL -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < NOW() - INTERVAL '10 minutes';"

# Restart application (reset connection pool)

# Contact Neon support (if database server issue)

# Check DATABASE_URL is correct
echo $DATABASE_URL | head -c 50
```

**Escalation Trigger**: Database inaccessible for > 5 minutes (P0)

### 5. WebSocket Connection Failures (P1)

**Symptoms**:
- "WebSocket connection failed"
- Users can't start live transcription
- Socket.IO errors in logs

**Quick Checks**:
```bash
# Check WebSocket logs
grep -i "websocket\|socket.io" /tmp/logs/Start_application_*.log | tail -20

# Check Redis connectivity (if using Redis adapter)
redis-cli ping
# Expected: PONG

# Check CORS configuration
# Verify allowed origins

# Test WebSocket connection
# Open live page, check browser console
```

**Common Causes**:
1. **CORS misconfiguration**: Origin not allowed
2. **Redis connection failure**: Socket.IO adapter down
3. **Worker crash**: Eventlet worker died
4. **Too many concurrent connections**: Worker limit reached

**Resolution**:
```bash
# Check CORS settings
# See: app.py socketio initialization

# Restart Redis (if issue)
# Or use in-memory fallback

# Restart application
# In Replit: Restart workflow

# Increase worker count if needed
gunicorn --workers 2 --worker-class eventlet main:app
```

**Escalation Trigger**: Issue persists after restart

### 6. OpenAI API Failure (P1)

**Symptoms**:
- Transcription requests failing
- "OpenAI API error" in logs
- Summary generation broken

**Quick Checks**:
```bash
# Check OpenAI status
# Visit: https://status.openai.com

# Check API key validity
echo $OPENAI_API_KEY | head -c 20
# Should start with "sk-"

# Check rate limits in logs
grep -i "rate_limit\|quota" logs/application.log

# Test API manually
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Common Causes**:
1. **OpenAI service degradation**: External service issue
2. **Rate limit exceeded**: Too many requests
3. **Invalid API key**: Key expired or revoked
4. **Quota exceeded**: Billing issue

**Resolution**:
```bash
# If OpenAI outage
# Implement graceful degradation
# Queue requests for retry

# If rate limit
# Implement exponential backoff
# Reduce concurrent requests

# If API key issue
# Rotate API key
# Update OPENAI_API_KEY secret

# If quota issue
# Contact billing
# Temporarily pause non-critical usage
```

**Escalation Trigger**: OpenAI outage > 1 hour

### 7. Backup Failure (P1)

**Symptoms**:
- "Backup failed" alert
- No recent backup file
- gpg encryption error

**Quick Checks**:
```bash
# Check backup directory
ls -lah backups/postgres/ | tail -10

# Check disk space
df -h

# Check backup script logs
cat logs/backup.log | tail -50

# Verify database accessibility
psql $DATABASE_URL -c "SELECT 1;"
```

**Common Causes**:
1. **Disk space full**: No room for backup file
2. **Database timeout**: Backup taking too long
3. **Permission issue**: Can't write to backup directory
4. **GPG key issue**: Encryption failing

**Resolution**:
```bash
# Clean up old backups (if disk full)
find backups/postgres/ -mtime +30 -delete

# Run manual backup
pg_dump $DATABASE_URL > backup_manual_$(date +%Y%m%d_%H%M%S).sql

# Encrypt backup
gpg --symmetric --cipher-algo AES256 backup_manual_*.sql

# Verify backup integrity
psql test_db < backup_manual_*.sql
```

**Escalation Trigger**: Backup failure 2 days in a row

## Troubleshooting Procedures

### Check Application Health

```bash
# Health endpoint
curl https://mina.replit.app/health

# Detailed health check (if available)
curl https://mina.replit.app/health/detailed

# Check all critical services
./scripts/health-check.sh
```

### Review Logs

```bash
# Application logs (latest)
tail -f /tmp/logs/Start_application_*.log

# Search for errors
grep -i "error\|exception\|fatal" /tmp/logs/Start_application_*.log | tail -50

# Filter by time (last 1 hour)
grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')" /tmp/logs/Start_application_*.log

# Check Sentry dashboard
# Visit: https://sentry.io/mina
```

### Database Diagnostics

```bash
# Check connections
psql $DATABASE_URL -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Top slow queries
psql $DATABASE_URL -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Check table sizes
psql $DATABASE_URL -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;"

# Check for locks
psql $DATABASE_URL -c "SELECT pid, usename, pg_blocking_pids(pid) as blocked_by, query FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0;"
```

### Performance Metrics

```bash
# Check current load
# In Replit console: CPU/memory usage

# API response times (from logs)
grep "request_duration" logs/application.log | awk '{sum+=$NF; count++} END {print "Avg:", sum/count}'

# Error rate (last hour)
total=$(grep "HTTP" logs/application.log | wc -l)
errors=$(grep "HTTP.*5[0-9][0-9]" logs/application.log | wc -l)
echo "Error rate: $(echo "scale=2; $errors/$total*100" | bc)%"
```

## Escalation

### When to Escalate

**Immediate Escalation (P0)**:
- Service down > 15 minutes
- Data loss detected
- Security breach suspected
- Unsure how to proceed

**Standard Escalation (P1)**:
- Issue unresolved after 30 minutes
- Multiple systems affected
- Need domain expertise
- Approaching SLO violation

### Escalation Path

```
On-Call Engineer
    ↓ (if > 30 min or P0)
Engineering Lead
    ↓ (if > 1 hour or critical)
CTO
    ↓ (if business impact)
CEO
```

### Escalation Contacts

- **Engineering Lead**: lead@mina.com, Slack @eng-lead
- **CTO**: cto@mina.com, Phone: (see internal wiki)
- **Database Admin**: dba@mina.com
- **Security**: security@mina.com

### How to Escalate

1. **Post in #incidents**: "@eng-lead Need escalation on [incident]"
2. **Call if urgent**: Use PagerDuty escalation policy
3. **Provide context**:
   - What's broken
   - What you've tried
   - Current impact
   - Time since start

## Post-Incident

### Immediate Actions

- [ ] **Verify resolution**: Confirm all systems healthy
- [ ] **Update status**: Post "Incident resolved" in #incidents
- [ ] **Document timeline**: Note key events
- [ ] **Preserve logs**: Save relevant logs for analysis
- [ ] **Thank responders**: Acknowledge help

### Incident Report (Within 24 hours)

Create incident report in `docs/incidents/YYYY-MM-DD-incident-name.md`:

```markdown
# Incident Report: [Title]

## Summary
- **Date**: 2025-10-02
- **Duration**: 45 minutes
- **Severity**: P1
- **Impact**: 15% of users affected
- **Root Cause**: Database migration timeout

## Timeline
- 14:00 - Alert triggered (high error rate)
- 14:05 - On-call acknowledged, started investigation
- 14:15 - Identified database migration as cause
- 14:20 - Rolled back migration
- 14:30 - Service restored
- 14:45 - Verified all systems healthy

## Impact
- Users: 500 active users saw errors
- Revenue: Minimal (no payment failures)
- Data: No data loss

## Root Cause
Database migration added index on large table without proper batching, causing table lock and query timeouts.

## Resolution
1. Rolled back migration using `flask db downgrade`
2. Recreated migration with CONCURRENTLY option
3. Re-applied migration successfully

## Lessons Learned
- Always test migrations on staging first with production-sized data
- Use CONCURRENTLY for index creation on large tables
- Add migration duration estimates to checklist

## Action Items
- [ ] Update migration guide with CONCURRENTLY examples (owner: @engineer, due: 2025-10-05)
- [ ] Add staging data seeding script (owner: @dba, due: 2025-10-10)
- [ ] Create migration review checklist (owner: @lead, due: 2025-10-08)

## Prevention
- All migrations now require staging test with >10k rows
- Added pre-deployment checklist item for migration duration
- Configured alert for migration duration > 5min
```

### Postmortem (For P0/P1)

Schedule blameless postmortem within 3 business days:
- 30-60 minute meeting
- Review timeline
- Discuss root cause
- Identify improvements
- Assign action items

## Tools & Access

### Required Access

- **Replit Account**: Full access to project
- **GitHub**: Write access to repository
- **Sentry**: Admin access
- **PagerDuty**: On-call schedule management
- **Slack**: #incidents, #engineering channels
- **Database**: Production read/write access

### Monitoring Tools

- **Sentry**: https://sentry.io/mina (error tracking)
- **Replit Console**: https://replit.com/console (logs, resources)
- **GitHub Actions**: https://github.com/mina/actions (CI/CD)
- **BetterStack** (when configured): Uptime monitoring

### Common Commands

```bash
# Restart application
# In Replit: Restart "Start application" workflow

# Check logs
tail -f /tmp/logs/Start_application_*.log

# Database access
psql $DATABASE_URL

# Run tests
pytest tests/e2e/test_01_smoke_tests.py -v

# Deploy rollback
# See: docs/operations/ROLLBACK_PROCEDURES.md

# Health check
curl https://mina.replit.app/health
```

### Runbook Scripts

```bash
# Quick health check
./scripts/health-check.sh

# Database diagnostics
./scripts/db-diagnostics.sh

# Performance check
./scripts/performance-check.sh

# Emergency rollback
./scripts/emergency-rollback.sh
```

## Shift Handoff

### Before Your Shift

- [ ] Review recent incidents
- [ ] Check current alerts
- [ ] Read this runbook
- [ ] Test PagerDuty connectivity
- [ ] Verify access to all tools

### During Handoff

Incoming on-call should brief outgoing on:
- **Active incidents**: Ongoing issues
- **Watch items**: Potential problems
- **Recent changes**: Deployments, config updates
- **Known issues**: Expected alerts
- **Planned work**: Scheduled maintenance

### After Your Shift

- [ ] Document all incidents
- [ ] Update runbook with learnings
- [ ] File action items from incidents
- [ ] Brief incoming on-call

## FAQs

**Q: What if I don't know how to fix an issue?**  
A: Escalate immediately. It's better to escalate early than struggle for hours.

**Q: Can I deploy fixes while on-call?**  
A: For hotfixes (P0/P1), yes. Follow abbreviated deployment checklist. For non-urgent fixes, wait until business hours.

**Q: What if I make things worse?**  
A: Rollback immediately. Document what happened. Learn from it. No blame.

**Q: Should I wake people up?**  
A: For P0 incidents only. Use PagerDuty escalation policy.

**Q: What if multiple alerts fire at once?**  
A: Triage by severity. Address P0 first, delegate P1 to team if available.

## Resources

- [Rollback Procedures](./ROLLBACK_PROCEDURES.md)
- [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md)
- [SLO/SLI Metrics](../monitoring/SLO_SLI_METRICS.md)
- [Database Migrations](../database-migrations.md)
- [Security Incident Response](../security/PG-1-IMPLEMENTATION-SUMMARY.md)

## Version History

- **v1.0** (2025-10-02): Initial on-call runbook
- Created as part of T0.30 (Create on-call runbook)
- Covers common incidents, troubleshooting, escalation
- Includes severity levels, response procedures, tools & access

---

**Remember**: Your goal is to restore service quickly, not necessarily to find and fix the root cause. Mitigate first, investigate later.
