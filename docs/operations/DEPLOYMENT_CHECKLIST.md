# Deployment Checklist

## Overview

This comprehensive checklist ensures safe, reliable deployments to production. **All items must be checked before deploying.**

## Pre-Deployment Checklist

### Code Quality & Testing

#### Required Checks ✅

- [ ] **All tests passing**
  ```bash
  pytest
  # Verify: 100% pass rate, 0 failures
  ```

- [ ] **Coverage meets 80% threshold**
  ```bash
  pytest --cov=. --cov-report=term-missing
  # Verify: Total coverage >= 80%
  ```

- [ ] **No linting errors**
  ```bash
  ruff check .
  black --check .
  # Verify: 0 errors
  ```

- [ ] **No security vulnerabilities**
  ```bash
  safety check
  bandit -r . -x ./tests
  # Verify: 0 critical/high issues
  ```

- [ ] **CI/CD pipeline passing**
  - GitHub Actions: All jobs green ✅
  - No failing workflows
  - All required checks completed

#### Code Review

- [ ] **PR approved by at least 2 reviewers**
- [ ] **No unresolved comments**
- [ ] **Architectural changes reviewed by tech lead**
- [ ] **Security-sensitive code reviewed by security champion**

### Database Migrations

#### Migration Safety ✅

- [ ] **Migration tested locally**
  ```bash
  flask db upgrade
  # Verify: Migration applies cleanly
  pytest tests/integration/test_database_operations.py
  # Verify: Tests pass after migration
  ```

- [ ] **Migration tested in staging**
  - Applied to staging environment
  - Application tested after migration
  - Rollback tested successfully

- [ ] **Data migration reviewed**
  - Large table migrations split into steps
  - Zero-downtime approach confirmed
  - Data loss risk assessed

- [ ] **Database backup taken**
  ```bash
  pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
  gpg --symmetric --cipher-algo AES256 backup_*.sql
  # Verify: Backup created and encrypted
  ```

- [ ] **Rollback plan documented**
  - Downgrade command tested
  - Restore-from-backup procedure ready
  - RTO/RPO targets defined

### Performance & Load

#### Performance Verification ✅

- [ ] **Load testing completed**
  ```bash
  cd tests/k6
  ./run-all-tests.sh
  # Verify: All SLOs met
  ```

- [ ] **Lighthouse scores >90**
  - Performance: >90
  - Accessibility: >90
  - Best Practices: >90
  - SEO: >90

- [ ] **Key metrics within targets**
  - API p95 response time: <500ms
  - Page load time: <2s
  - Error rate: <1%
  - WebSocket latency: <400ms

- [ ] **No N+1 queries introduced**
  ```bash
  # Check query count in logs
  pytest tests/integration/ --log-cli-level=DEBUG | grep "SELECT"
  ```

### Security Review

#### Security Checks ✅

- [ ] **No hardcoded secrets**
  ```bash
  git diff main | grep -i "password\|secret\|api_key\|token"
  # Verify: No sensitive data exposed
  ```

- [ ] **Secrets rotation completed (if applicable)**
  - Old API keys marked for deletion
  - New keys configured in production
  - Rotation schedule updated

- [ ] **CORS configuration reviewed**
  - No wildcard origins in production
  - Only approved domains whitelisted

- [ ] **Input validation added**
  - SQL injection prevention verified
  - XSS protection confirmed
  - Path traversal blocked

- [ ] **Rate limiting configured**
  - API endpoints protected
  - Limits appropriate for traffic
  - Bypass for trusted clients

- [ ] **Security headers configured**
  - CSP with nonces
  - HSTS enabled
  - X-Frame-Options set
  - X-Content-Type-Options set

### Accessibility

#### WCAG 2.1 AA Compliance ✅

- [ ] **Axe-core tests passing**
  ```bash
  pytest tests/accessibility/ -v
  # Verify: 0 violations
  ```

- [ ] **Keyboard navigation tested**
  - Tab order logical
  - Focus indicators visible
  - No keyboard traps

- [ ] **Screen reader tested (if UI changes)**
  - ARIA labels present
  - Semantic HTML used
  - Form labels associated

- [ ] **Color contrast meets AA standards**
  - Text: 4.5:1 minimum
  - Large text: 3:1 minimum
  - Interactive elements: 3:1 minimum

### Feature Flags & Config

#### Configuration Management ✅

- [ ] **Environment variables verified**
  - Production config matches .env.example
  - No development values in production
  - All required secrets present

- [ ] **Feature flags configured**
  - New features behind flags (if applicable)
  - Rollback plan via flags documented
  - Default state verified

- [ ] **Third-party integrations tested**
  - OpenAI API connectivity verified
  - Redis connection established
  - Database pool healthy

### Documentation

#### Required Documentation ✅

- [ ] **CHANGELOG.md updated**
  - Version number incremented
  - Features listed
  - Bug fixes documented
  - Breaking changes highlighted

- [ ] **API documentation updated** (if API changes)
  - OpenAPI spec updated
  - Example requests/responses added
  - Breaking changes documented

- [ ] **User-facing documentation updated** (if applicable)
  - Help articles updated
  - Screenshots refreshed
  - FAQs updated

- [ ] **Internal runbook updated** (if new features)
  - Troubleshooting steps added
  - Monitoring alerts documented
  - On-call procedures updated

### Monitoring & Observability

#### Monitoring Setup ✅

- [ ] **Sentry configured**
  - Error tracking enabled
  - Release tagged in Sentry
  - Source maps uploaded (if applicable)

- [ ] **Structured logging verified**
  - Log levels appropriate
  - Sensitive data not logged
  - Request IDs present

- [ ] **Metrics dashboards ready**
  - Key metrics defined
  - Alerts configured
  - Thresholds set

- [ ] **Health checks passing**
  ```bash
  curl https://mina.replit.app/health
  # Verify: {"status": "healthy"}
  ```

### Stakeholder Communication

#### Notifications ✅

- [ ] **Deployment window scheduled**
  - Team notified in #deployments
  - Users notified (if downtime expected)
  - Support team briefed

- [ ] **Rollback contacts identified**
  - On-call engineer available
  - Escalation path defined
  - Emergency contacts confirmed

- [ ] **Release notes prepared**
  - User-facing changes listed
  - Known issues documented
  - Workarounds provided

## Deployment Execution

### Step-by-Step Deployment

#### 1. Final Verification (5 min)

- [ ] Re-run all tests locally
  ```bash
  pytest
  ruff check .
  black --check .
  ```

- [ ] Verify branch is up-to-date
  ```bash
  git fetch origin
  git status
  # Verify: "Your branch is up to date"
  ```

- [ ] Check production health
  ```bash
  curl https://mina.replit.app/health
  # Baseline: Current error rate, response times
  ```

#### 2. Database Migration (if applicable) (10 min)

- [ ] Take database backup
  ```bash
  pg_dump $DATABASE_URL > backup_pre_deploy_$(date +%Y%m%d_%H%M%S).sql
  ```

- [ ] Apply migration
  ```bash
  flask db upgrade
  ```

- [ ] Verify migration
  ```bash
  flask db current
  # Verify: Expected revision ID
  ```

- [ ] Test application with new schema
  ```bash
  pytest tests/integration/test_database_operations.py -v
  ```

#### 3. Deploy Application (5 min)

- [ ] Merge to main branch
  ```bash
  git checkout main
  git merge feature-branch --no-ff
  git push origin main
  ```

- [ ] Tag release
  ```bash
  git tag -a v1.2.3 -m "Release v1.2.3: Brief description"
  git push origin v1.2.3
  ```

- [ ] Deploy to production
  ```bash
  # In Replit: Push triggers auto-deployment
  # Or manual deployment:
  # gunicorn --bind 0.0.0.0:5000 --workers 2 --worker-class eventlet main:app
  ```

- [ ] Wait for deployment completion
  - Monitor workflow logs
  - Watch for startup errors

#### 4. Smoke Testing (5 min)

- [ ] Run deployment smoke tests
  ```bash
  pytest tests/e2e/test_01_smoke_tests.py -v
  ```

- [ ] Verify critical paths
  - [ ] Homepage loads
  - [ ] User can login
  - [ ] Live transcription works
  - [ ] API endpoints respond

- [ ] Check error rates
  ```bash
  # Check Sentry dashboard
  # Verify: Error rate <1%
  ```

#### 5. Monitoring (ongoing)

- [ ] Watch logs for 15 minutes
  ```bash
  # Monitor for errors, warnings
  tail -f logs/application.log
  ```

- [ ] Check key metrics
  - Response times stable
  - Error rate normal
  - CPU/memory normal
  - Database connections healthy

- [ ] Monitor user reports
  - Check #support channel
  - Check error tracking
  - Watch for anomalies

## Post-Deployment Checklist

### Immediate Verification (< 30 min)

- [ ] **All smoke tests passing**
  ```bash
  pytest tests/e2e/test_01_smoke_tests.py -v
  # Verify: 100% pass rate
  ```

- [ ] **Error rate normal**
  - Sentry: <1% error rate
  - Logs: No critical errors
  - APM: Response times normal

- [ ] **User traffic normal**
  - Active users count expected
  - No sudden drop-offs
  - Engagement metrics stable

- [ ] **Database healthy**
  ```bash
  psql $DATABASE_URL -c "SELECT 1;"
  # Verify: Connection successful
  ```

### Follow-Up (< 24 hours)

- [ ] **Performance metrics reviewed**
  - Lighthouse scores maintained
  - API response times <500ms
  - Page load times <2s

- [ ] **User feedback collected**
  - Support tickets reviewed
  - User sentiment checked
  - No spike in complaints

- [ ] **Team debriefed**
  - Deployment retrospective scheduled
  - Learnings documented
  - Process improvements identified

### Documentation Updates

- [ ] **Update deployment log**
  ```markdown
  ## Deployment Log: v1.2.3 (2025-10-02)
  
  - **Deployed by**: engineer@mina.com
  - **Duration**: 25 minutes
  - **Issues**: None
  - **Rollback**: Not required
  - **Notes**: Smooth deployment, all checks passed
  ```

- [ ] **Update runbook** (if new procedures)
- [ ] **Update architecture docs** (if architecture changed)
- [ ] **Close deployment ticket**

## Rollback Procedures

### When to Rollback

Rollback immediately if:

- **P0**: Complete service outage
- **P1**: Error rate >5%
- **P1**: Response time degradation >50%
- **P1**: Data loss or corruption detected
- **P2**: Critical feature broken (assess impact first)

### Rollback Steps

See: [docs/operations/ROLLBACK_PROCEDURES.md](./ROLLBACK_PROCEDURES.md)

Quick rollback:
```bash
# Use Replit Checkpoints (fastest)
# Replit UI: History → Checkpoints → Restore to last good state

# Or git revert
git revert HEAD
git push origin main

# Or database rollback
flask db downgrade
```

## Deployment Types

### Standard Deployment (Default)

- Normal business hours (10am-4pm PST)
- Low-risk changes
- Full testing completed
- This checklist applies

### Hotfix Deployment

- Urgent bug fix or security patch
- Out-of-hours permitted
- **Abbreviated checklist**:
  - [ ] Tests passing
  - [ ] Security review completed
  - [ ] Rollback plan ready
  - [ ] On-call engineer notified
- Full post-deployment verification required

### Emergency Rollback

- Immediate production issue
- Skip pre-deployment checks
- **Focus on**:
  - [ ] Identify last known good version
  - [ ] Execute rollback (< 5 min)
  - [ ] Verify service restored
  - [ ] Create incident report
- Post-rollback: Full RCA required

## Environment-Specific Notes

### Staging Environment (T0.11)

- Can skip some checks (e.g., user notifications)
- Used for final pre-production verification
- Should mirror production setup

### Production Environment

- **All** checklist items required
- No exceptions without CTO approval
- Deployment window scheduled

## Tools & Resources

### Deployment Commands

```bash
# Run full pre-deployment checks
./scripts/pre-deploy-checks.sh

# Deploy to production
./scripts/deploy-production.sh

# Run smoke tests
pytest tests/e2e/test_01_smoke_tests.py -v

# Check deployment status
./scripts/check-deployment-status.sh
```

### Monitoring Dashboards

- **Sentry**: https://sentry.io/mina
- **BetterStack**: https://betterstack.com (when implemented)
- **Replit Console**: https://replit.com/console
- **GitHub Actions**: https://github.com/mina/actions

### Documentation

- [Rollback Procedures](./ROLLBACK_PROCEDURES.md)
- [On-Call Runbook](./ON_CALL_RUNBOOK.md) (T0.30)
- [Database Migrations](../database-migrations.md)
- [Testing Standards](../testing/TESTING_STANDARDS.md)

## Contacts

- **On-Call Engineer**: See rotation in PagerDuty
- **Escalation**: engineering-lead@mina.com
- **Emergency**: #incidents Slack channel

## Checklist Versions

- **v1.0** (2025-10-02): Initial version
- Created as part of T0.15 (Create deployment checklist)
- Covers pre-deployment, deployment, and post-deployment steps
- Includes rollback procedures and emergency protocols

---

**IMPORTANT**: This checklist is mandatory for all production deployments. Bypassing items requires written approval from CTO.
