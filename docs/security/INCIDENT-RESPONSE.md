# Security Incident Response Plan
**Mina - Enterprise-Grade Incident Management**

## Overview

This document defines procedures for detecting, responding to, and recovering from security incidents. All team members must be familiar with these protocols to ensure rapid, effective response.

**Status:** ✅ Production-ready  
**Compliance:** SOC 2, ISO 27001, GDPR, HIPAA  
**Last Updated:** October 2025  
**Review Frequency:** Quarterly

---

## Incident Classification

### 🔴 P0 - Critical (Immediate Response)

**Response Time:** < 15 minutes  
**Examples:**
- Active data breach or exfiltration
- Ransomware attack in progress
- Production system completely down
- Credentials leaked publicly (GitHub, Pastebin, etc.)
- Zero-day exploit being actively exploited
- Customer PII/PHI exposure confirmed

**Actions:**
1. Activate incident commander immediately
2. Notify CEO, CTO, legal team
3. Begin containment within 15 minutes
4. Document every action in incident log

---

### 🟠 P1 - High (Urgent Response)

**Response Time:** < 1 hour  
**Examples:**
- Suspicious admin access detected
- Multiple failed authentication attempts (possible brute force)
- Unauthorized database access
- DDoS attack affecting service
- Vulnerability scanner detected in logs
- API key rotation overdue >7 days

**Actions:**
1. Assign incident lead
2. Notify security team and engineering lead
3. Begin investigation within 1 hour
4. Implement temporary mitigations

---

### 🟡 P2 - Medium (Standard Response)

**Response Time:** < 4 hours  
**Examples:**
- Malware detected on employee workstation
- Phishing email reported by user
- Minor service degradation
- Non-critical vulnerability discovered
- Unusual traffic patterns detected
- Session anomaly detected

**Actions:**
1. Log incident in tracking system
2. Assign to security team member
3. Investigate within 4 hours
4. Schedule remediation

---

### 🟢 P3 - Low (Routine Response)

**Response Time:** < 24 hours  
**Examples:**
- Security scan finding (non-exploitable)
- Outdated library with no known CVE
- Policy violation (minor)
- False positive alert
- Security awareness training reminder

**Actions:**
1. Create ticket in issue tracker
2. Review during next security sync
3. Address during regular sprint

---

## Incident Response Lifecycle

### Phase 1: Detection & Analysis

**Detection Sources:**
- Sentry error tracking (SENTRY_DSN)
- Uptime monitoring (BetterStack)
- Failed login alerts (auth logs)
- Rate limit violations (middleware/limits.py)
- Database anomaly detection
- User reports (support tickets)
- Security scans (OWASP ZAP, automated)

**Initial Analysis:**
```bash
# 1. Check recent logs
tail -n 500 /var/log/mina/app.log | grep -i "error\|unauthorized\|403\|401"

# 2. Review Sentry for errors
# https://sentry.io/organizations/mina/issues/

# 3. Check database for suspicious queries
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# 4. Review auth logs
grep "login" /var/log/mina/app.log | tail -n 100

# 5. Check rate limit violations
grep "Rate limit exceeded" /var/log/mina/app.log | tail -n 50
```

**Indicators of Compromise (IOCs):**
- Unexpected outbound connections
- Database queries at unusual hours
- Multiple failed auth from same IP
- Large data exports (>1GB)
- Modified system files
- Disabled security controls
- New admin users created

---

### Phase 2: Containment

**Immediate Containment (< 15 minutes for P0):**

```bash
# 1. Block malicious IP immediately
# Option A: Via Python console (security_config.py has block_ip method)
python3 -c "
from app import app
from security_config import SecurityConfig
with app.app_context():
    sec = SecurityConfig(app)
    sec.block_ip('MALICIOUS_IP', 'Active attack - Incident #123')
"

# Option B: Via upstream firewall/WAF (Cloudflare, Replit config)
# Or implement /ops/block-ip endpoint in routes/ops.py

# 2. Disable compromised user account
psql $DATABASE_URL -c "UPDATE users SET is_active = false WHERE id = 'USER_ID';"

# 3. Rotate compromised credentials IMMEDIATELY
./scripts/rotate_secrets.sh SESSION_SECRET
./scripts/rotate_secrets.sh API_SECRET_KEY

# 4. Enable emergency rate limiting (more strict)
# Update middleware/limits.py:
# 'api': {'requests': 10, 'window': 300}  # 10 req/5min (emergency mode)

# 5. Take database backup before any remediation
pg_dump $DATABASE_URL > /backups/incident_$(date +%Y%m%d_%H%M%S).sql
```

**Short-term Containment (< 1 hour for P1):**

```bash
# 1. Enable maintenance mode
# Set MAINTENANCE_MODE=true in Replit Secrets
# Application detects this and returns 503 for all requests
# (Implement via before_request hook in app.py if not yet added)

# 2. Isolate affected services
# If database compromised: Create read-only replica, point app there
# If API compromised: Disable API endpoints temporarily

# 3. Preserve evidence
# Copy logs before rotation
cp /var/log/mina/app.log /evidence/incident_logs_$(date +%Y%m%d_%H%M%S).log

# 4. Notify affected users (if data exposed)
# See "Communication Protocols" section below
```

---

### Phase 3: Eradication

**Remove Threat:**

```bash
# 1. Patch vulnerabilities
# Update dependencies
pip install --upgrade $(pip list --outdated | awk 'NR>2 {print $1}')
npm update

# 2. Remove malicious code/backdoors
# Review recent git commits
git log --since="2 days ago" --all --oneline
git diff HEAD~10 HEAD  # Review last 10 commits

# 3. Reset all compromised accounts
# Force password reset for affected users
psql $DATABASE_URL -c "UPDATE users SET password_must_change = true WHERE id IN (...);"

# 4. Revoke all active sessions
psql $DATABASE_URL -c "DELETE FROM sessions WHERE user_id IN (...);"

# 5. Clean up malicious database entries
# Review and remove injected data
psql $DATABASE_URL -c "DELETE FROM suspicious_table WHERE created_at > '2025-10-01 12:00:00';"
```

**Harden Systems:**

```bash
# 1. Update CSP headers (if XSS involved)
# Edit middleware/csp.py to stricter policy

# 2. Enable additional monitoring
# Add Sentry breadcrumbs for sensitive operations
# Update routes/auth.py to log all auth events

# 3. Implement additional controls
# Add IP allowlist for admin panel
# Require 2FA for admin accounts (future enhancement)

# 4. Apply security patches
# Check for Flask, SQLAlchemy, etc. security updates
pip install --upgrade flask flask-sqlalchemy flask-wtf
```

---

### Phase 4: Recovery

**Restore Normal Operations:**

```bash
# 1. Verify threat eliminated
# Run security scan
python scripts/security_audit.py

# 2. Restore from backup (if needed)
# Restore database to last known good state
pg_restore -d $DATABASE_URL /backups/pre_incident_backup.sql

# 3. Gradually restore services
# Disable maintenance mode
unset MAINTENANCE_MODE

# 4. Monitor closely for 24-48 hours
# Watch for recurrence
tail -f /var/log/mina/app.log | grep -i "error\|unauthorized"

# 5. Validate all systems functioning
curl https://your-app.replit.app/ops/health
# Check all endpoints return 200
```

**Post-Recovery Validation:**
- [ ] All services responding normally
- [ ] No unauthorized access detected (24h monitoring)
- [ ] Backups verified and current
- [ ] Credentials rotated and verified
- [ ] Monitoring alerts functioning
- [ ] Users can access their accounts
- [ ] Data integrity confirmed

---

### Phase 5: Post-Incident Analysis

**Incident Report Template:**

```markdown
# Security Incident Report

## Incident Summary
- **Incident ID:** INC-2025-001
- **Date/Time:** 2025-10-01 14:30 UTC
- **Severity:** P0 / P1 / P2 / P3
- **Status:** Resolved / In Progress / Monitoring

## Timeline
- **14:30** - Incident detected (source: Sentry alert)
- **14:35** - Incident commander assigned
- **14:40** - Containment began
- **15:00** - Threat contained
- **16:00** - Eradication complete
- **17:00** - Services restored
- **18:00** - Post-incident review scheduled

## Impact Assessment
- **Users Affected:** 150 users (5% of total)
- **Data Exposed:** Email addresses (no passwords/PII)
- **Downtime:** 30 minutes (14:45-15:15 UTC)
- **Financial Impact:** $500 (estimated)
- **Regulatory:** GDPR notification required (>250 users)

## Root Cause
SQL injection vulnerability in /api/meetings search endpoint
- **CVE:** N/A (custom code vulnerability)
- **Introduced:** Commit abc123 (2025-09-28)
- **Exploited:** 2025-10-01 14:30 UTC

## Actions Taken
1. Blocked attacker IP: 192.0.2.100
2. Patched SQL injection vulnerability
3. Rotated database credentials
4. Notified affected users
5. Implemented parameterized queries

## Lessons Learned
### What Went Well
- Detection within 5 minutes (Sentry alert)
- Containment within 10 minutes
- Clear communication with team

### What Needs Improvement
- Parameterized queries not enforced in code review
- No automated security testing for SQL injection
- Incident response playbook not readily accessible

## Preventive Measures
- [ ] Implement SQLAlchemy ORM (no raw SQL)
- [ ] Add SAST (Static Application Security Testing)
- [ ] Security code review checklist
- [ ] Quarterly security training for developers
- [ ] Automated SQL injection testing in CI/CD

## Follow-up Actions
- [ ] Update incident response plan (Owner: Security Team, Due: 2025-10-15)
- [ ] Implement automated security scanning (Owner: DevOps, Due: 2025-10-20)
- [ ] Conduct security training (Owner: HR, Due: 2025-11-01)
- [ ] Review similar code patterns (Owner: Engineering, Due: 2025-10-10)
```

---

## Communication Protocols

### Internal Communication

**Incident Commander:**
- Primary: John Doe (john@mina.com, +1-555-0100)
- Backup: Jane Smith (jane@mina.com, +1-555-0101)

**Escalation Path:**
1. Security Team Lead → CTO → CEO
2. For legal issues: → General Counsel
3. For PR issues: → Communications Director

**Communication Channels:**
- **P0/P1:** Dedicated Slack channel `#incident-response-YYYYMMDD`
- **P2/P3:** `#security` Slack channel
- **War Room:** Zoom link: https://zoom.us/j/incident-room

**Status Updates:**
- P0: Every 30 minutes
- P1: Every 2 hours
- P2: Daily
- P3: As needed

---

### External Communication

**Customer Notification (Data Breach):**

**Template: Immediate Notification (<24h)**
```
Subject: Important Security Notice - Mina Account

Dear [User],

We are writing to inform you of a security incident that may have affected your Mina account.

What Happened:
On [DATE], we detected unauthorized access to our systems. We immediately 
contained the incident and have taken steps to prevent future occurrences.

What Information Was Involved:
[Specific data types: email, name, etc. - be specific and honest]

What We're Doing:
- Patched the vulnerability
- Rotated all security credentials
- Enhanced monitoring
- Working with security experts

What You Should Do:
- Change your password immediately: [LINK]
- Enable two-factor authentication (when available)
- Monitor your account for suspicious activity
- Be cautious of phishing attempts

We sincerely apologize for this incident and any inconvenience caused.

For questions: security@mina.com or visit [HELP CENTER LINK]

Sincerely,
Mina Security Team
```

**Regulatory Notifications:**

**GDPR (EU) - Within 72 hours:**
- Notify supervisory authority (Data Protection Commission)
- Include: nature of breach, categories of data, number affected
- Contact: https://edpb.europa.eu/

**CCPA (California) - Without unreasonable delay:**
- Notify affected California residents
- Offer 12 months free credit monitoring if SSN exposed

**HIPAA (Healthcare) - Within 60 days:**
- Notify HHS if >500 individuals affected
- Contact: https://ocrportal.hhs.gov/

---

## Incident Response Tools

### Detection Tools

```bash
# Check for suspicious processes
ps aux | grep -v "^root\|^runner" | grep -E "nc|ncat|bash -i"

# Check for unusual network connections
netstat -tunap | grep ESTABLISHED

# Check for modified system files
find /app -type f -mtime -1  # Files modified in last 24h

# Check for large file transfers
du -sh /app/* | sort -hr | head -10

# Check for crypto mining (high CPU)
top -b -n 1 | head -15
```

### Forensic Collection

```bash
# Collect system information
cat > /evidence/system_info_$(date +%Y%m%d_%H%M%S).txt <<EOF
Date: $(date)
Hostname: $(hostname)
Kernel: $(uname -a)
Users: $(who)
Processes: $(ps aux | wc -l)
Network: $(netstat -tunap | wc -l)
EOF

# Collect logs
tar -czf /evidence/logs_$(date +%Y%m%d_%H%M%S).tar.gz \
  /var/log/mina/ \
  /var/log/nginx/ \
  /var/log/auth.log

# Collect database metadata
psql $DATABASE_URL -c "\dt" > /evidence/db_tables_$(date +%Y%m%d_%H%M%S).txt
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity;" > /evidence/db_activity_$(date +%Y%m%d_%H%M%S).txt

# Memory dump (if available)
# gcore $(pgrep python)  # Requires gdb
```

### Recovery Scripts

```bash
# Emergency lockdown script
cat > /scripts/emergency_lockdown.sh <<'EOF'
#!/bin/bash
# Emergency lockdown - Use only in P0 incidents

echo "🚨 EMERGENCY LOCKDOWN ACTIVATED"

# 1. Block all non-admin IPs (emergency mode)
iptables -A INPUT -p tcp --dport 5000 -j DROP
iptables -I INPUT -p tcp -s ADMIN_IP --dport 5000 -j ACCEPT

# 2. Disable all API endpoints
export API_DISABLED=true

# 3. Force logout all users
psql $DATABASE_URL -c "DELETE FROM sessions;"

# 4. Rotate all credentials
./scripts/rotate_secrets.sh SESSION_SECRET
./scripts/rotate_secrets.sh API_SECRET_KEY

# 5. Enable maximum logging
export LOG_LEVEL=DEBUG
export JSON_LOGS=true

echo "✅ Lockdown complete. Incident response activated."
EOF

chmod +x /scripts/emergency_lockdown.sh
```

---

## Incident Response Checklist

### P0 Incident Checklist

- [ ] **0-5min:** Verify incident is P0 severity
- [ ] **0-5min:** Activate incident commander
- [ ] **0-5min:** Create incident Slack channel
- [ ] **0-10min:** Notify CEO, CTO, Legal
- [ ] **0-15min:** Begin containment (block IPs, disable accounts)
- [ ] **0-30min:** Preserve evidence (logs, database)
- [ ] **0-30min:** Take system snapshots/backups
- [ ] **1hr:** Complete threat containment
- [ ] **2hr:** Begin eradication (patch, remove malware)
- [ ] **4hr:** Restore services (gradual rollout)
- [ ] **24hr:** Notify affected users (if data breach)
- [ ] **72hr:** Regulatory notification (GDPR, if applicable)
- [ ] **1 week:** Post-incident report published
- [ ] **2 weeks:** Preventive measures implemented

### Evidence Preservation

- [ ] Stop log rotation immediately
- [ ] Copy all relevant logs to `/evidence/`
- [ ] Take database snapshot
- [ ] Capture network traffic (if possible)
- [ ] Screenshot attacker activity
- [ ] Document all actions in incident log
- [ ] Chain of custody maintained
- [ ] Do NOT reboot affected systems (preserves memory)

---

## Tabletop Exercises

**Schedule:** Quarterly  
**Participants:** Security team, engineering leads, executives

**Scenario 1: Ransomware Attack**
- Database encrypted, ransom note displayed
- Practice: Restore from backup, notify authorities
- Goal: < 4 hour recovery time

**Scenario 2: Insider Threat**
- Employee downloads customer database
- Practice: Revoke access, forensic investigation
- Goal: Detect within 24 hours

**Scenario 3: API Key Leak**
- OpenAI API key posted to GitHub
- Practice: Emergency rotation, usage audit
- Goal: Rotate within 1 hour

**Scenario 4: DDoS Attack**
- Service unavailable, rate limits exceeded
- Practice: Enable DDoS protection, scale infrastructure
- Goal: Restore service within 30 minutes

---

## Contact Information

### Internal Contacts

| Role | Name | Email | Phone | Backup |
|------|------|-------|-------|--------|
| Incident Commander | John Doe | john@mina.com | +1-555-0100 | Jane Smith |
| Security Lead | Jane Smith | jane@mina.com | +1-555-0101 | Bob Johnson |
| CTO | Bob Johnson | bob@mina.com | +1-555-0102 | CEO |
| CEO | Alice Williams | alice@mina.com | +1-555-0103 | Board Chair |
| Legal Counsel | David Lee | david@legalfirm.com | +1-555-0104 | Outside Counsel |
| PR Director | Sarah Chen | sarah@mina.com | +1-555-0105 | CEO |

### External Contacts

| Service | Contact | Purpose |
|---------|---------|---------|
| **Incident Response Partner** | CrowdStrike | +1-855-980-1347 | Forensics, malware analysis |
| **Legal (Data Breach)** | Morrison Foerster | +1-415-268-7000 | Regulatory compliance |
| **FBI Cyber Division** | IC3.gov | https://www.ic3.gov/ | Criminal investigation |
| **Cloud Provider (Replit)** | Replit Support | support@replit.com | Infrastructure issues |
| **Database (Neon)** | Neon Support | support@neon.tech | Database compromise |
| **Monitoring (Sentry)** | Sentry Support | support@sentry.io | Detection issues |

### Regulatory Authorities

| Region | Authority | Notification Requirement |
|--------|-----------|-------------------------|
| **EU** | Data Protection Commission | 72 hours (GDPR) |
| **California** | Attorney General | Without unreasonable delay (CCPA) |
| **Healthcare** | HHS OCR | 60 days if >500 affected (HIPAA) |
| **Financial** | FinCEN | Immediately (if applicable) |

---

## Metrics and KPIs

**Track for Each Incident:**
- Time to detect (TTD)
- Time to contain (TTC)
- Time to eradicate (TTE)
- Time to recover (TTR)
- Mean time to resolution (MTTR)
- Number of users affected
- Data volume exposed (GB)
- Financial impact ($)
- Regulatory fines ($)

**Target SLAs:**
- P0: TTD < 15min, TTC < 1hr, MTTR < 4hr
- P1: TTD < 1hr, TTC < 4hr, MTTR < 24hr
- P2: TTD < 4hr, TTC < 24hr, MTTR < 1 week
- P3: TTD < 24hr, MTTR < 2 weeks

**Monthly Report:**
- Total incidents by severity
- Average MTTR by severity
- Top attack vectors
- Repeat incidents (same root cause)
- Preventive measures implemented

---

## Legal and Compliance

### Data Breach Notification Laws

**United States:**
- All 50 states have data breach notification laws
- Notification required "without unreasonable delay"
- Must include: what happened, what data, what to do

**European Union (GDPR):**
- Notify supervisory authority within 72 hours
- Notify affected individuals "without undue delay"
- Fines up to 4% of global revenue or €20M

**California (CCPA):**
- Notify affected California residents
- Attorney General if >500 residents
- Offer credit monitoring if SSN exposed

### Evidence Handling

**Chain of Custody:**
1. Document who collected evidence
2. Document when evidence was collected
3. Document where evidence is stored
4. Document who accessed evidence
5. Maintain cryptographic hashes (SHA-256)

**Legal Hold:**
- Preserve all evidence if litigation expected
- Do NOT delete logs, backups, or communications
- Consult legal counsel before any data destruction

---

## Appendix

### A. Incident Response Runbook (Quick Reference)

**P0 Incident - First 15 Minutes:**
```bash
# 1. Assess and confirm P0 severity
# 2. Activate incident commander: Call +1-555-0100
# 3. Create Slack channel: #incident-response-YYYYMMDD
# 4. Block attacker (use security_config.py or upstream WAF)
# 5. Disable compromised accounts:
psql $DATABASE_URL -c "UPDATE users SET is_active=false WHERE id IN (...);"
# 6. Rotate credentials:
./scripts/rotate_secrets.sh SESSION_SECRET
./scripts/rotate_secrets.sh API_SECRET_KEY
# 7. Preserve evidence:
cp /var/log/mina/app.log /evidence/incident_$(date +%Y%m%d_%H%M%S).log
# 8. Notify: CEO, CTO, Legal
```

### B. Post-Incident Improvement Tracker

| Incident ID | Date | Root Cause | Preventive Measure | Status | Owner |
|-------------|------|------------|-------------------|--------|-------|
| INC-001 | 2025-09-15 | SQL Injection | Implement ORM only | ✅ Done | Engineering |
| INC-002 | 2025-09-20 | Weak password | Enforce password policy | ✅ Done | Security |
| INC-003 | 2025-09-25 | Leaked API key | Automated secret scanning | 🔄 In Progress | DevOps |

### C. Security Incident Log (Confidential)

**Location:** `docs/security/.incident_log` (encrypted)

```
# Security Incident Log - CONFIDENTIAL
# Format: YYYY-MM-DD | Incident ID | Severity | Description | Status | Impact

2025-10-01 | INC-2025-001 | P1 | SQL injection in /api/meetings | Resolved | 150 users
2025-09-28 | INC-2025-002 | P2 | Failed auth spike from 192.0.2.5 | Resolved | 0 users
2025-09-25 | INC-2025-003 | P3 | Outdated library (non-exploitable) | Resolved | 0 users
```

---

**Document Owner:** Mina Security Team  
**Last Reviewed:** October 2025  
**Next Review:** January 2026  
**Status:** Production-ready ✅

**For Emergencies:** Call Incident Commander at +1-555-0100
