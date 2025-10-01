# API Key Rotation Schedule
**Mina - Secure Credential Lifecycle Management**

## Overview

API key rotation is a critical security practice that reduces the impact of credential compromise. This document defines rotation schedules, procedures, and automation for all API keys and secrets used in Mina.

**Status:** ✅ Production-ready  
**Compliance:** SOC 2, ISO 27001, PCI DSS 4.0  
**Last Updated:** October 2025

---

## Initial Setup

**Before using the rotation system, set up the backup encryption passphrase:**

```bash
# 1. Generate a strong backup passphrase
GPG_BACKUP_PASSPHRASE=$(openssl rand -base64 32)
echo "Backup passphrase: $GPG_BACKUP_PASSPHRASE"

# 2. Add to Replit Secrets
# In Replit: Tools → Secrets → Add Secret
# Key: GPG_BACKUP_PASSPHRASE
# Value: [paste the generated passphrase]

# 3. Verify it's set
echo $GPG_BACKUP_PASSPHRASE
# Should show the passphrase (only in your secure terminal)

# 4. IMPORTANT: Store backup passphrase securely
# Save in password manager or encrypted vault for emergency recovery
```

**⚠️ Critical:** Without `GPG_BACKUP_PASSPHRASE`, the rotation script will refuse to backup secrets (fail-safe behavior).

---

## Rotation Schedule

### 🔴 Critical Secrets (30-Day Rotation)

**SESSION_SECRET** - Flask session encryption key
- **Rotation Frequency:** Every 30 days
- **Impact:** All active sessions invalidated on rotation
- **Procedure:** [SESSION_SECRET Rotation](#session_secret-rotation)
- **Next Rotation:** 2025-11-01

**API_SECRET_KEY** - Internal API authentication
- **Rotation Frequency:** Every 30 days
- **Impact:** API clients must update credentials
- **Procedure:** [API Key Rotation](#api-key-rotation)
- **Next Rotation:** 2025-11-01

### 🟡 High-Priority Secrets (90-Day Rotation)

**OPENAI_API_KEY** - OpenAI API access
- **Rotation Frequency:** Every 90 days
- **Impact:** Transcription services temporarily unavailable during rotation
- **Procedure:** [Third-Party API Key Rotation](#third-party-api-key-rotation)
- **Next Rotation:** 2025-12-30

**DATABASE_URL** - PostgreSQL connection
- **Rotation Frequency:** Every 90 days (password rotation)
- **Impact:** 10-second downtime during connection pool refresh
- **Procedure:** [Database Credential Rotation](#database-credential-rotation)
- **Next Rotation:** 2025-12-30

### 🟢 Standard Secrets (Annual Rotation)

**SENTRY_DSN** - Error tracking endpoint
- **Rotation Frequency:** Annually or on suspected compromise
- **Impact:** Error tracking briefly interrupted
- **Procedure:** [Sentry DSN Rotation](#sentry-dsn-rotation)
- **Next Rotation:** 2026-10-01

**REDIS_URL** - Cache/session store (if used)
- **Rotation Frequency:** Annually
- **Impact:** Cache cleared, sessions reset
- **Procedure:** [Redis Credential Rotation](#redis-credential-rotation)
- **Next Rotation:** 2026-10-01

### ⚪ Non-Rotating Secrets

**JWT signing keys** - Managed by Flask-Login (session-based, no JWT yet)
**OAuth client secrets** - Managed by OAuth providers (rotate on provider dashboard)

---

## Rotation Procedures

### SESSION_SECRET Rotation

**Purpose:** Invalidate all existing sessions and prevent session fixation attacks.

**Pre-Rotation Checklist:**
- [ ] Ensure `GPG_BACKUP_PASSPHRASE` is set in Replit Secrets (required for encrypted backups)
- [ ] Schedule maintenance window (5min)
- [ ] Notify users 24h in advance
- [ ] Verify session persistence is working

**Rotation Steps:**

```bash
# 1. Generate new secret (32 bytes, base64-encoded)
NEW_SECRET=$(openssl rand -base64 32)
echo "New SESSION_SECRET: $NEW_SECRET"

# 2. Update environment variable (Replit Secrets)
# In Replit: Tools → Secrets → SESSION_SECRET → Update value
# Or via CLI:
# replit secrets set SESSION_SECRET="$NEW_SECRET"

# 3. Restart application
# Replit auto-restarts on secret change
# Or manually: gunicorn restart

# 4. Verify new secret is active
curl -v https://your-app.replit.app/auth/login 2>&1 | grep -i "set-cookie"
# Should show new session cookies

# 5. Store old secret securely (emergency rollback)
echo "$OLD_SECRET" | gpg --encrypt > session_secret_backup_$(date +%Y%m%d).gpg
```

**Post-Rotation Verification:**
- [ ] Login works correctly
- [ ] New sessions created successfully
- [ ] Old sessions invalidated
- [ ] No 500 errors in logs
- [ ] Update rotation tracker: `docs/security/.rotation_log`

**Rollback Procedure:**
```bash
# If issues detected within 15 minutes:
replit secrets set SESSION_SECRET="$OLD_SECRET"
# Application auto-restarts with old secret
```

**Impact:** All users logged out, must re-authenticate.

---

### API Key Rotation

**Purpose:** Rotate internal API keys used for service-to-service authentication.

**Rotation Steps:**

```bash
# 1. Generate new API key
NEW_API_KEY=$(openssl rand -hex 32)
echo "New API_SECRET_KEY: $NEW_API_KEY"

# 2. Dual-key period: Add new key while keeping old key active
# The app already supports dual-key via environment variables
# No code changes needed - security_config.py checks both keys automatically

# 3. Update environment with new key (keep old key for transition)
replit secrets set API_SECRET_KEY="$NEW_API_KEY"
replit secrets set API_SECRET_KEY_OLD="$OLD_API_KEY"

# 4. Wait 24-48h for clients to migrate to new key
# Monitor logs for "Request authenticated with OLD API key" messages

# 5. Remove old key after transition period
replit secrets delete API_SECRET_KEY_OLD
# App automatically stops accepting old key once removed

# 6. Verify only new key accepted
curl -H "X-API-Key: $OLD_API_KEY" https://your-app.replit.app/api/health
# Should return 401 Unauthorized
```

**Post-Rotation Checklist:**
- [ ] New key works for all API clients
- [ ] Old key rejected after transition period
- [ ] No 401 errors in production logs
- [ ] Update API documentation with new key format

---

### Third-Party API Key Rotation

**Purpose:** Rotate credentials for external services (OpenAI, Sentry, etc.)

**OpenAI API Key Rotation:**

```bash
# 1. Generate new key in OpenAI dashboard
# https://platform.openai.com/api-keys
# Create key → "Mina Production - 2025-10" → Copy key

# 2. Test new key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $NEW_OPENAI_KEY" | jq .

# 3. Update Replit secret
replit secrets set OPENAI_API_KEY="$NEW_OPENAI_KEY"

# 4. Verify transcription still works
# Test in app: Start recording → Check transcription appears

# 5. Revoke old key in OpenAI dashboard
# https://platform.openai.com/api-keys → Select old key → Revoke

# 6. Monitor for usage spikes (potential compromise)
```

**Sentry DSN Rotation:**

```bash
# 1. Generate new DSN in Sentry
# Sentry → Settings → Client Keys (DSN) → Create new key

# 2. Update environment
replit secrets set SENTRY_DSN="$NEW_SENTRY_DSN"

# 3. Verify errors still reported
# Trigger test error: /ops/test-error

# 4. Revoke old DSN in Sentry dashboard
# Sentry → Settings → Client Keys (DSN) → Delete old key
```

---

### Database Credential Rotation

**Purpose:** Rotate PostgreSQL password without downtime.

**Rotation Steps (Neon/Replit Database):**

```bash
# 1. Get current DATABASE_URL
echo $DATABASE_URL
# postgres://user:oldpass@host:5432/dbname

# 2. Change password in Neon/Replit dashboard
# Neon: Dashboard → Select database → Settings → Reset password
# Replit: Database pane → Settings → Reset credentials

# 3. Get new DATABASE_URL
NEW_DB_URL="postgres://user:newpass@host:5432/dbname"

# 4. Update environment variable
replit secrets set DATABASE_URL="$NEW_DB_URL"

# 5. Application auto-restarts with new credentials
# Connection pool drains old connections, creates new ones

# 6. Verify database connectivity
curl https://your-app.replit.app/ops/health | jq .database
# Should show "status": "healthy"

# 7. Old password no longer works (automatic revocation)
```

**Zero-Downtime Rotation (Advanced):**

```python
# For high-availability deployments, use connection failover:

# 1. Configure dual database URLs during rotation
PRIMARY_DB = os.getenv("DATABASE_URL")
FALLBACK_DB = os.getenv("DATABASE_URL_NEW")

# 2. Connection pool with automatic failover
engine = create_engine(PRIMARY_DB, pool_pre_ping=True)
# pool_pre_ping=True validates connections before use

# 3. Gradual migration: New connections use new URL
# Old connections drain naturally over 60 seconds
```

---

### Redis Credential Rotation

**Purpose:** Rotate Redis password (if using managed Redis).

**Rotation Steps:**

```bash
# 1. Generate new Redis URL with new password
# Redis provider dashboard → Reset password

# 2. Update environment
replit secrets set REDIS_URL="$NEW_REDIS_URL"

# 3. Application restart clears cache, reconnects
# Note: All cached data lost (acceptable for cache)

# 4. Verify Redis connectivity
redis-cli -u "$NEW_REDIS_URL" PING
# Should return PONG

# 5. Old password revoked automatically
```

---

## Emergency Rotation

**When to Perform Emergency Rotation:**

🚨 **IMMEDIATE** (within 1 hour):
- Secret leaked in git commit
- Secret leaked in logs/error messages
- Secret exposed in public forum/screenshot
- Suspected compromise (unauthorized API usage)
- Employee offboarding (had access to secrets)

⚠️ **URGENT** (within 24 hours):
- Audit finding (secret stored insecurely)
- Third-party data breach (provider compromised)
- Compliance requirement (audit mandated rotation)

**Emergency Rotation Process:**

```bash
# 1. Identify compromised secret
COMPROMISED_SECRET="SESSION_SECRET"  # Example

# 2. Generate replacement immediately
NEW_VALUE=$(openssl rand -base64 32)

# 3. Rotate without warning (security takes precedence)
replit secrets set $COMPROMISED_SECRET="$NEW_VALUE"

# 4. Revoke old secret in provider dashboard (if applicable)
# OpenAI: Revoke key
# Sentry: Delete DSN
# Database: Reset password

# 5. Audit git history for leaked secret
git log -p -S "$OLD_VALUE" --all
# If found: git filter-repo, force push, contact GitHub support

# 6. Monitor for unusual activity
# Check logs for unauthorized access attempts
# Review Sentry errors for authentication failures

# 7. Document incident in security log
echo "$(date): Emergency rotation of $COMPROMISED_SECRET - Reason: [compromise details]" >> docs/security/.incident_log

# 8. Notify security team and stakeholders
```

---

## Automation

### Automated Rotation Script

**Location:** `scripts/rotate_secrets.sh`

**Usage:**
```bash
# Check rotation status (shows overdue/upcoming rotations)
./scripts/rotate_secrets.sh

# Rotate a specific secret (generates new value, backs up old one)
./scripts/rotate_secrets.sh SESSION_SECRET

# Verify rotation after applying new secret in Replit
./scripts/rotate_secrets.sh SESSION_SECRET --verify

# Show secret value (use with caution)
./scripts/rotate_secrets.sh SESSION_SECRET --show
```

**Prerequisites:**
- GPG installed: `gnupg` package
- `GPG_BACKUP_PASSPHRASE` set in Replit Secrets (for encrypted backups)

**Features:**
- ✅ Generates cryptographically secure new values
- ✅ GPG AES256-encrypted backups (requires GPG_BACKUP_PASSPHRASE)
- ✅ Never prints secrets by default (secure temp files)
- ✅ Verification-based logging (prevents false audit trail)
- ✅ Fail-safe: Refuses to backup without proper encryption

**Automated Rotation Schedule (Cron):**

```bash
# Add to crontab for automated rotation
# crontab -e

# Rotate SESSION_SECRET on 1st of every month at 2 AM
0 2 1 * * /app/scripts/rotate_secrets.sh SESSION_SECRET >> /var/log/rotation.log 2>&1

# Rotate API_SECRET_KEY on 1st of every month at 3 AM
0 3 1 * * /app/scripts/rotate_secrets.sh API_SECRET_KEY >> /var/log/rotation.log 2>&1

# Check for upcoming rotations (weekly reminder)
0 9 * * 1 /app/scripts/check_rotation_due.sh
```

### Rotation Monitoring

**Metrics to Track:**
- Days since last rotation (per secret)
- Rotation success/failure rate
- Time to complete rotation
- Number of failed auth attempts post-rotation

**Alerting:**

```python
# In monitoring system (Sentry/Grafana)

# Alert if rotation overdue
if days_since_rotation("SESSION_SECRET") > 35:
    alert("SESSION_SECRET rotation overdue by 5 days")

# Alert if rotation failed
if rotation_status != "success":
    alert("Secret rotation failed - manual intervention required")

# Alert on auth spike post-rotation (potential compromise)
if auth_failures_last_hour > 100:
    alert("High auth failure rate - verify rotation completed correctly")
```

---

## Rotation Tracker

**Location:** `docs/security/.rotation_log`

```
# Secret Rotation Log
# Format: YYYY-MM-DD | Secret Name | Rotated By | Next Rotation | Notes

2025-10-01 | SESSION_SECRET | admin | 2025-11-01 | Initial setup
2025-10-01 | API_SECRET_KEY | admin | 2025-11-01 | Initial setup
2025-10-01 | OPENAI_API_KEY | admin | 2025-12-30 | Production key
2025-10-01 | DATABASE_URL | admin | 2025-12-30 | Neon password rotation
2025-10-01 | SENTRY_DSN | admin | 2026-10-01 | Annual rotation scheduled
```

**Upcoming Rotations:**

| Secret | Last Rotated | Next Rotation | Days Remaining | Priority |
|--------|--------------|---------------|----------------|----------|
| SESSION_SECRET | 2025-10-01 | 2025-11-01 | 31 | 🔴 Critical |
| API_SECRET_KEY | 2025-10-01 | 2025-11-01 | 31 | 🔴 Critical |
| OPENAI_API_KEY | 2025-10-01 | 2025-12-30 | 90 | 🟡 High |
| DATABASE_URL | 2025-10-01 | 2025-12-30 | 90 | 🟡 High |
| SENTRY_DSN | 2025-10-01 | 2026-10-01 | 365 | 🟢 Standard |

---

## Best Practices

### ✅ DO
- **Rotate on schedule** - Don't skip rotations
- **Document every rotation** - Update `.rotation_log`
- **Test before production** - Verify new secrets in staging
- **Use strong generation** - `openssl rand -base64 32` minimum
- **Backup old secrets** - Encrypted, for emergency rollback
- **Monitor post-rotation** - Check logs for auth failures
- **Automate when possible** - Reduce human error

### ❌ DON'T
- **Don't hardcode secrets** - Always use environment variables
- **Don't commit secrets** - Use `.gitignore`, scan with git-secrets
- **Don't share secrets** - Use secret managers, not Slack/email
- **Don't skip backups** - Old secrets needed for rollback
- **Don't rotate without testing** - Test new secret before revoking old
- **Don't forget to revoke** - Old secrets must be deactivated
- **Don't ignore alerts** - Overdue rotations are security risks

---

## Compliance Requirements

### SOC 2 Type II
- **Control:** Cryptographic keys rotated quarterly (90 days)
- **Evidence:** Rotation logs, automated rotation scripts
- **Audit:** `.rotation_log` reviewed by auditors

### ISO 27001
- **Control:** A.10.1.2 - Key management
- **Requirement:** Documented rotation procedures
- **Evidence:** This document + rotation logs

### PCI DSS 4.0
- **Requirement 3.6.4:** Cryptographic keys must be rotated periodically
- **Frequency:** At least annually (we exceed with 30-90 day rotation)
- **Evidence:** Rotation logs, automated scripts

### GDPR (if applicable)
- **Article 32:** Technical measures to ensure security
- **Rotation reduces risk:** Compromised keys have limited lifetime
- **Data protection:** Encrypted data remains secure post-rotation

---

## Incident Response

### If Secret Compromised

**Detection Signals:**
- Unexpected API usage spike
- Failed auth attempts from unknown IPs
- Third-party breach notification
- Git commit contains secret
- Employee reports potential exposure

**Response Steps:**

1. **Assess Scope** (5 min)
   - Which secret(s) compromised?
   - When was exposure?
   - Who has access?

2. **Immediate Rotation** (15 min)
   - Follow [Emergency Rotation](#emergency-rotation)
   - No maintenance window - rotate immediately

3. **Revoke Old Secret** (5 min)
   - Provider dashboard: Revoke/delete old key
   - Verify old key no longer works

4. **Audit Usage** (30 min)
   - Review logs for unauthorized access
   - Check for data exfiltration
   - Identify affected users/data

5. **Notification** (as required)
   - Internal: Security team, management
   - External: Affected users (if data breach)
   - Regulatory: GDPR/HIPAA reporting (if applicable)

6. **Post-Incident** (24 hours)
   - Document incident in `.incident_log`
   - Root cause analysis
   - Implement preventive measures
   - Update rotation procedures if needed

---

## Tools and Resources

### Secret Generation
```bash
# Strong random string (32 bytes)
openssl rand -base64 32

# Hex string (64 characters)
openssl rand -hex 32

# UUID (for API keys)
uuidgen

# Password-like (with special chars)
pwgen -s 32 1
```

### Secret Scanning
```bash
# Scan git history for secrets
git-secrets --scan-history

# Scan codebase with truffleHog
trufflehog filesystem . --json

# GitHub secret scanning (automatic)
# Enabled in repository settings
```

### Secret Storage
- **Development:** Replit Secrets (encrypted at rest)
- **Production:** AWS Secrets Manager, Azure Key Vault, HashiCorp Vault
- **Backup:** GPG-encrypted files, offline storage

### Monitoring Integrations
- **Sentry:** Secret rotation events as breadcrumbs
- **Grafana:** Days-since-rotation dashboard
- **Slack:** Rotation reminders and alerts

---

## FAQ

**Q: What happens to active users when SESSION_SECRET rotates?**  
A: All users are logged out and must re-authenticate. Schedule rotation during low-traffic hours.

**Q: Can I extend rotation intervals?**  
A: Not recommended. 30/90-day intervals balance security and convenience. Shortening is better than lengthening.

**Q: What if rotation fails mid-process?**  
A: Use backed-up old secret to rollback. Fix issue, retry rotation. Document in `.incident_log`.

**Q: How do I rotate secrets without downtime?**  
A: Use dual-key periods: Keep old key active while introducing new key, transition over 24h.

**Q: Do I need to rotate DATABASE_URL if password unchanged?**  
A: No. Only rotate when password changes or on schedule. Connection string format changes don't require rotation.

**Q: Should I rotate secrets if employee leaves?**  
A: Yes, emergency rotation within 24h if employee had secret access.

---

## References

- **NIST SP 800-57:** Cryptographic Key Management
- **OWASP Key Management Cheat Sheet:** https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html
- **AWS Secrets Manager Best Practices:** https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html
- **CIS Controls v8:** Control 3.11 - Encrypt Sensitive Data

---

**Last Reviewed:** October 2025  
**Next Review:** January 2026  
**Owner:** Mina Security Team  
**Status:** Production-ready ✅
