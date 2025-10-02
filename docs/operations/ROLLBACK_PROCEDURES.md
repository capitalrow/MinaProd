# Rollback Procedures

## Overview

This document outlines comprehensive rollback procedures for the Mina platform, covering application deployments, database migrations, and disaster recovery scenarios. All procedures are designed to minimize downtime and data loss.

## Table of Contents

1. [Application Rollback](#application-rollback)
2. [Database Migration Rollback](#database-migration-rollback)
3. [Configuration Rollback](#configuration-rollback)
4. [Emergency Procedures](#emergency-procedures)
5. [Verification Steps](#verification-steps)
6. [Post-Rollback Actions](#post-rollback-actions)

## Application Rollback

### Replit Deployment Rollback

**Scenario**: Production application deployment fails or causes issues

**Steps**:
1. **Immediate Response** (< 5 minutes)
   ```bash
   # Stop current deployment
   # In Replit: Stop the "Start application" workflow
   
   # Check git history
   git log --oneline -10
   
   # Identify last known good commit
   git show <commit-hash>
   ```

2. **Rollback to Previous Version**
   ```bash
   # Option 1: Rollback to specific commit
   git revert <bad-commit-hash>
   git push origin main
   
   # Option 2: Hard reset (use with caution)
   git reset --hard <good-commit-hash>
   git push origin main --force
   
   # Option 3: Use Replit Checkpoints (RECOMMENDED)
   # Use the Replit UI to restore to a previous checkpoint
   # This rolls back code, database, and environment together
   ```

3. **Restart Application**
   ```bash
   # In Replit: Restart the "Start application" workflow
   # Or manually:
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

### Blue-Green Deployment Rollback

**When Available** (T0.13 implementation pending)

**Steps**:
1. **Switch Traffic** (< 1 minute)
   ```bash
   # Switch load balancer to green (previous) environment
   ./scripts/switch-to-green.sh
   ```

2. **Verify**
   ```bash
   # Check health endpoint
   curl https://mina.replit.app/health
   
   # Verify metrics
   # Check Sentry, uptime monitors
   ```

3. **Decommission Blue** (after verification)
   ```bash
   # Keep blue environment for 24 hours
   # Then decommission
   ./scripts/decommission-blue.sh
   ```

## Database Migration Rollback

### Alembic Migration Rollback

**Scenario**: Database migration causes issues or data corruption

**Prerequisites**:
- Always test migrations in staging first
- Always backup database before migration
- Document migration dependencies

**Steps**:

1. **Check Current Migration State**
   ```bash
   # Show current revision
   flask db current
   
   # Show migration history
   flask db history
   ```

2. **Rollback Single Migration**
   ```bash
   # Downgrade by 1 step
   flask db downgrade -1
   
   # Or downgrade to specific revision
   flask db downgrade <revision-id>
   
   # Example:
   flask db downgrade 6f9f2dd343f5
   ```

3. **Rollback Multiple Migrations**
   ```bash
   # Rollback to base (DANGER: removes all migrations)
   flask db downgrade base
   
   # Rollback to specific point in history
   flask db downgrade <earlier-revision-id>
   ```

4. **Verify Database State**
   ```bash
   # Check tables
   flask db current
   
   # Verify data integrity
   python scripts/verify_db_integrity.py
   
   # Check application
   pytest tests/integration/test_database_operations.py -v
   ```

### Database Restore from Backup

**Scenario**: Migration rollback fails or data corruption detected

**RPO (Recovery Point Objective)**: < 5 minutes (based on backup frequency)  
**RTO (Recovery Time Objective)**: < 30 minutes (based on database size)

**Steps**:

1. **Stop Application** (prevent writes during restore)
   ```bash
   # Stop workflows in Replit
   # Or kill gunicorn process
   pkill -f gunicorn
   ```

2. **Identify Backup**
   ```bash
   # List available backups
   ls -lah backups/postgres/
   
   # Choose most recent pre-migration backup
   # Example: backup_20251002_120000.sql.gpg
   ```

3. **Restore Database**
   ```bash
   # Decrypt backup
   gpg --decrypt backups/postgres/backup_20251002_120000.sql.gpg > restore.sql
   
   # Drop existing database (CAREFUL!)
   dropdb mina_production
   
   # Create fresh database
   createdb mina_production
   
   # Restore from backup
   psql mina_production < restore.sql
   
   # Clean up
   rm restore.sql
   ```

4. **Verify Restore**
   ```bash
   # Check table count
   psql mina_production -c "\dt"
   
   # Check row counts
   psql mina_production -c "SELECT 'users' as table, COUNT(*) FROM users
   UNION ALL SELECT 'sessions', COUNT(*) FROM sessions
   UNION ALL SELECT 'segments', COUNT(*) FROM segments;"
   
   # Run integrity checks
   python scripts/verify_db_integrity.py
   ```

5. **Restart Application**
   ```bash
   # Restart workflows
   # Or manually start
   gunicorn --bind 0.0.0.0:5000 --workers 2 --worker-class eventlet main:app
   ```

## Configuration Rollback

### Environment Variables Rollback

**Scenario**: Bad configuration deployed

**Steps**:

1. **Identify Previous Configuration**
   ```bash
   # Check git history
   git log -- .env.example
   git diff HEAD~1:.env.example .env.example
   ```

2. **Restore Configuration**
   ```bash
   # Using Replit Secrets UI
   # Manually revert changed secrets
   
   # Or using script (if available)
   ./scripts/restore-secrets.sh <backup-file>
   ```

3. **Restart Application**
   ```bash
   # Restart to pick up new config
   # In Replit: Restart workflow
   ```

### Feature Flag Rollback

**Scenario**: Feature flag causes issues

**Steps**:

1. **Disable Feature**
   ```python
   # In Python console or admin panel
   from app import app, db
   from models import FeatureFlag
   
   with app.app_context():
       flag = FeatureFlag.query.filter_by(name='problematic_feature').first()
       flag.enabled = False
       db.session.commit()
   ```

2. **Verify**
   ```bash
   # Check application behavior
   pytest tests/integration/ -k "test_feature"
   
   # Monitor logs
   tail -f logs/application.log
   ```

## Emergency Procedures

### Critical Incident Response

**Severity Levels**:
- **P0 (Critical)**: Complete service outage, data loss
- **P1 (High)**: Partial outage, degraded performance >20%
- **P2 (Medium)**: Minor issues, workarounds available
- **P3 (Low)**: Cosmetic issues, no user impact

**P0 Incident Rollback** (< 5 min RTO):

1. **Immediate Actions**
   ```bash
   # Stop application
   pkill -f gunicorn
   
   # Use Replit Checkpoint rollback (fastest)
   # This rolls back code + database + environment together
   # Access via Replit UI: History → Checkpoints → Restore
   ```

2. **Notify Stakeholders**
   ```bash
   # Post incident update
   # Slack: #incidents channel
   # Status page: update.mina.com
   ```

3. **Verify Recovery**
   ```bash
   # Run smoke tests
   pytest tests/e2e/test_01_smoke_tests.py -v
   
   # Check health
   curl https://mina.replit.app/health
   ```

### Partial Rollback (Selective Features)

**Scenario**: Only specific feature needs rollback

**Steps**:

1. **Identify Feature Code**
   ```bash
   # Find commits for feature
   git log --grep="FEATURE-123" --oneline
   ```

2. **Revert Specific Commits**
   ```bash
   # Revert individual commits
   git revert <commit-hash-1> <commit-hash-2>
   git push origin main
   ```

3. **Deploy**
   ```bash
   # Deploy will pick up reverted changes
   # Monitor deployment
   ```

## Verification Steps

After any rollback, **always verify**:

### 1. Application Health
```bash
# Health endpoint
curl https://mina.replit.app/health
# Expected: {"status": "healthy"}

# Smoke tests
pytest tests/e2e/test_01_smoke_tests.py -v
```

### 2. Database Integrity
```bash
# Check connections
psql $DATABASE_URL -c "SELECT 1;"

# Verify key tables
python scripts/verify_db_integrity.py

# Check migration state
flask db current
```

### 3. Critical User Flows
```bash
# Run critical path tests
pytest tests/e2e/test_02_critical_user_journeys.py -v

# Manual verification
# - User can login
# - User can create session
# - Real-time transcription works
```

### 4. Monitoring & Alerts
```bash
# Check Sentry for errors
# https://sentry.io/mina/dashboard

# Check uptime monitors
# BetterStack dashboard

# Verify metrics
# Error rate < 1%
# Response time < 500ms
# Uptime > 99.9%
```

## Post-Rollback Actions

### 1. Incident Documentation (Required)
```markdown
# Create incident report
File: docs/incidents/YYYY-MM-DD-incident-name.md

## Incident Summary
- **Date**: 2025-10-02
- **Severity**: P1
- **Duration**: 15 minutes
- **Impact**: 20% of users affected

## Timeline
- 14:00 - Deployment started
- 14:05 - Errors detected in Sentry
- 14:08 - Rollback initiated
- 14:15 - Service restored

## Root Cause
- Bad database migration
- Missing index caused query timeout

## Resolution
- Rolled back migration using `flask db downgrade -1`
- Restored from backup (unnecessary, rollback worked)

## Action Items
- [ ] Add migration testing to CI/CD
- [ ] Improve staging environment parity
- [ ] Update rollback runbook with learnings

## Prevention
- Always test migrations in staging first
- Add query performance tests
```

### 2. Root Cause Analysis (Within 24 hours)

Required for P0/P1 incidents:
- Identify root cause
- Document timeline
- Create action items
- Assign owners
- Set deadlines

### 3. Process Improvements

Update documentation:
- [ ] Update this rollback guide with learnings
- [ ] Update deployment checklist
- [ ] Update testing requirements
- [ ] Share incident report with team

### 4. Preventive Measures

Implement safeguards:
- Add tests to prevent recurrence
- Improve monitoring/alerting
- Update CI/CD pipeline
- Schedule training if needed

## Rollback Decision Tree

```
Incident Detected
├─ Is service down?
│  ├─ YES → P0: Immediate Replit Checkpoint Rollback (RTO: <5min)
│  └─ NO → Continue assessment
│
├─ Is performance degraded >20%?
│  ├─ YES → P1: Rollback to previous deployment (RTO: <15min)
│  └─ NO → Continue assessment
│
├─ Is it a database issue?
│  ├─ YES → Database Migration Rollback
│  │  ├─ Single migration: flask db downgrade -1
│  │  └─ If failed: Restore from backup
│  └─ NO → Continue assessment
│
├─ Is it a configuration issue?
│  ├─ YES → Restore previous configuration
│  └─ NO → Continue assessment
│
├─ Is it a specific feature?
│  ├─ YES → Selective rollback (revert commits)
│  └─ NO → Full rollback recommended
│
└─ Minor issue? → Monitor, create bug ticket, fix forward
```

## Testing Rollback Procedures

**IMPORTANT**: Test rollback procedures regularly in staging!

### Monthly Rollback Drill

1. **Schedule** (first Monday of month)
2. **Scope**: Full application + database rollback in staging
3. **Steps**:
   ```bash
   # Deploy intentionally bad code to staging
   git checkout staging
   git merge feature/rollback-drill-bad-code
   git push
   
   # Wait for deployment
   # Verify issues
   # Execute rollback procedure
   # Document time taken
   # Note any issues
   ```

4. **Metrics**:
   - Rollback time (target: <15 min)
   - Data loss (target: 0)
   - Success rate (target: 100%)

## Contacts

**On-Call Rotation**: See `docs/operations/ON_CALL.md`

**Escalation Path**:
1. On-call engineer (primary)
2. Engineering lead
3. CTO

**Emergency Contacts**:
- Slack: #incidents
- PagerDuty: incidents@mina.pagerduty.com
- Phone: See internal wiki

## Resources

- [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md) (T0.15)
- [Database Migrations Guide](../database-migrations.md)
- [On-Call Runbook](./ON_CALL_RUNBOOK.md) (T0.30)
- [Incident Response Guide](../security/PG-1-IMPLEMENTATION-SUMMARY.md)
- [Disaster Recovery Plan](../resilience/DISASTER_RECOVERY_PLAN.md)

## Version History

- **v1.0** (2025-10-02): Initial version
- Created as part of T0.12 (Document rollback procedures)
- Covers application, database, configuration rollbacks
- Includes emergency procedures and verification steps
