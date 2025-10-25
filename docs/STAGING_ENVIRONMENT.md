# Staging Environment Setup Guide

## Overview

The staging environment is a production-like environment used to test changes before deploying to production. It should mirror production configuration as closely as possible while remaining completely isolated.

**Critical Principle**: Staging and production must NEVER share resources (databases, Redis, S3 buckets, API keys).

## Quick Start

### 1. Create Local Staging Configuration

```bash
# Copy staging template
cp .env.staging .env.staging.local

# Edit and fill in real values
nano .env.staging.local
```

### 2. Critical Values to Set

**Must Change (Security Critical):**
```bash
SECRET_KEY=<generate_with: python -c "import secrets; print(secrets.token_hex(32))">
SESSION_SECRET=<generate_with: python -c "import secrets; print(secrets.token_hex(32))">
DATABASE_URL=postgresql://user:pass@staging-db.host:5432/mina_staging
```

**Should Change (Isolation Critical):**
```bash
REDIS_URL=redis://staging-redis:6379/0
OPENAI_API_KEY=sk-staging-...
AWS_S3_BUCKET=mina-audio-staging
SHARE_BASE_URL=https://mina-staging.replit.app
```

### 3. Launch Staging Server

```bash
# Load staging environment
export $(cat .env.staging.local | grep -v '^#' | xargs)

# Verify environment
echo $ENVIRONMENT  # Should output: staging

# Run database migrations
flask db upgrade

# Start server
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## Environment Architecture

### Isolation Boundaries

| Resource          | Production                     | Staging                           | Isolated? |
|-------------------|--------------------------------|-----------------------------------|-----------|
| Database          | `mina_production`              | `mina_staging`                    | ✅ Yes     |
| Redis             | `redis.prod:6379/0`            | `redis.staging:6379/0`            | ✅ Yes     |
| S3 Bucket         | `mina-audio-production`        | `mina-audio-staging`              | ✅ Yes     |
| OpenAI API Key    | Production key (org billing)   | Staging key (separate billing)    | ✅ Yes     |
| Sentry Project    | `mina-production`              | `mina-staging` or disabled        | ✅ Yes     |
| Slack Channel     | `#mina-alerts`                 | `#mina-staging-alerts`            | ✅ Yes     |
| Email Service     | Production SendGrid            | Staging SendGrid or disabled      | ✅ Yes     |
| Share Links       | `mina.app`                     | `mina-staging.replit.app`         | ✅ Yes     |

### Database Setup Options

#### Option 1: Separate Postgres Instance (Recommended)

```bash
# Neon/Supabase: Create separate staging project
DATABASE_URL=postgresql://user:pass@staging.region.neon.tech:5432/mina_staging
```

**Pros:**
- Complete isolation (can't accidentally connect to production)
- Independent scaling and performance tuning
- Can reset/wipe staging without affecting production

**Cons:**
- Costs money (separate instance)
- Requires managing two database instances

#### Option 2: Same Instance, Different Database

```bash
# Same Postgres server, different database name
DATABASE_URL=postgresql://user:pass@shared.postgres.host:5432/mina_staging
```

**Pros:**
- Cost-efficient (reuses existing Postgres instance)
- Simpler infrastructure management

**Cons:**
- Risk of connecting to wrong database (typo in .env)
- Shared resource contention

#### Option 3: Same Database, Different Schema (Not Recommended)

```bash
# Same database, different schema
DATABASE_URL=postgresql://user:pass@prod.host:5432/mina?options=-c search_path=staging
```

**Pros:**
- Minimal cost

**Cons:**
- ❌ High risk of data crossover
- ❌ Difficult to enforce isolation
- ❌ Not recommended for production systems

### Redis Setup Options

#### Option 1: Separate Redis Instance (Recommended)

```bash
# Upstash: Create separate staging database
REDIS_URL=rediss://default:pass@staging-redis.upstash.io:6379
```

#### Option 2: Same Redis, Different DB Number

```bash
# Production uses db 0, staging uses db 1
REDIS_URL=redis://shared-redis.host:6379/1
```

**Warning**: This shares the same Redis instance, so memory limits and eviction policies affect both environments.

## Testing the Staging Environment

### 1. Verify Isolation

```bash
# Check environment variable
curl http://staging-server:5000/api/version
# Should include: "environment": "staging"

# Check database (should be empty or have staging data only)
psql $DATABASE_URL -c "SELECT COUNT(*) FROM sessions;"

# Check Redis (should not see production keys)
redis-cli -u $REDIS_URL KEYS "*"
```

### 2. Test Deployment Flow

```bash
# 1. Deploy code to staging
git push staging main

# 2. Run migrations
flask db upgrade

# 3. Test new features
curl http://staging-server:5000/api/meetings
# ... manual testing in browser ...

# 4. Check logs for errors
tail -f logs/staging.log

# 5. If successful, deploy to production
git push production main
```

### 3. Data Refresh from Production (Optional)

**Warning**: Only do this if staging data is stale and you need realistic test data.

```bash
# 1. Take production snapshot
pg_dump $PRODUCTION_DATABASE_URL > prod_snapshot.sql

# 2. Restore to staging (THIS WILL WIPE STAGING DATA!)
psql $STAGING_DATABASE_URL < prod_snapshot.sql

# 3. Anonymize sensitive data
psql $STAGING_DATABASE_URL -c "
  UPDATE users SET 
    email = 'staging_' || id || '@example.com',
    password_hash = 'invalid_hash';
"
```

## Environment-Specific Behavior

### Feature Flags in Staging

Staging should test new features before production:

```python
# In routes or services
from services.feature_flags import is_enabled

if is_enabled('new_ai_insights', default=False):
    # Enable by default in staging, require flag in production
    use_new_ai_insights()
```

### Logging in Staging

Staging uses the same JSON logging as production for realistic testing:

```bash
JSON_LOGS=true
LOG_LEVEL=INFO  # Same as production
```

### Rate Limiting in Staging

Staging has more relaxed limits to allow testing:

```bash
# Production: 100/min, 1000/hour
# Staging: 200/min, 2000/hour (2x higher)
RATE_LIMIT_PER_MINUTE=200
RATE_LIMIT_PER_HOUR=2000
```

## Deployment Process

### Full Staging → Production Flow

```bash
# 1. Merge PR to main branch
git checkout main && git pull

# 2. Deploy to staging first
git push staging main

# 3. Run staging migrations
heroku run flask db upgrade --app mina-staging

# 4. Test in staging environment
./scripts/smoke_test.sh https://mina-staging.replit.app

# 5. If tests pass, deploy to production
git push production main

# 6. Run production migrations (with backup!)
heroku run flask db upgrade --app mina-production

# 7. Verify production health
./scripts/smoke_test.sh https://mina.app

# 8. Monitor error rates in Sentry
open https://sentry.io/organizations/mina/projects/mina-production/
```

## Safety Checklist

Before deploying to staging, verify:

- [ ] `ENVIRONMENT=staging` in .env.staging.local
- [ ] `DATABASE_URL` points to staging database (not production!)
- [ ] `REDIS_URL` points to staging Redis (not production!)
- [ ] `SHARE_BASE_URL` uses staging domain
- [ ] `SENTRY_ENVIRONMENT=staging` (separate error tracking)
- [ ] Email service disabled or uses staging SendGrid account
- [ ] Slack uses `#mina-staging-alerts` channel (not production)
- [ ] S3 bucket is `mina-audio-staging` (not production)
- [ ] OpenAI API key is staging-specific (separate billing)
- [ ] `.env.staging.local` is in .gitignore (never committed!)

## Troubleshooting

### Problem: Staging connects to production database

**Symptom**: Seeing production data in staging, or staging writes appear in production

**Solution**:
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Should NOT contain production domain/database name
# If it does, fix .env.staging.local and restart
```

### Problem: Feature flag changes affect production

**Symptom**: Toggling staging feature flags changes production behavior

**Solution**:
```bash
# Check Redis connection
redis-cli -u $REDIS_URL INFO server

# Should connect to staging Redis, not production
# Verify REDIS_URL in .env.staging.local
```

### Problem: Staging emails sent to real users

**Symptom**: Users receive test emails from staging

**Solution**:
```bash
# Disable email in staging
SENDGRID_API_KEY=

# Or use staging-specific SendGrid with catch-all redirect
```

## Advanced: Blue/Green Staging

For zero-downtime staging tests:

```bash
# Deploy to staging-blue
git push staging-blue main

# Test staging-blue
./scripts/smoke_test.sh https://staging-blue.mina.app

# If successful, swap traffic to staging-blue
# (Now staging-blue becomes new "staging")

# Deploy next change to staging-green
git push staging-green main
```

This allows testing without disrupting ongoing staging QA.

## See Also

- [Deployment Playbook](./DEPLOYMENT_PLAYBOOK.md) - Full production deployment process
- [Migrations Guide](./MIGRATIONS_GUIDE.md) - Database migration best practices
- [Feature Flags](../services/feature_flags.py) - Feature flag service documentation
