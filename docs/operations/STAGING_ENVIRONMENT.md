# Staging Environment Setup

## Overview

The staging environment is a production-like environment used for final validation before deploying to production. It mirrors production configuration while using separate infrastructure to prevent any impact on live users.

## Environment Configuration

### Replit Setup

**Staging Repl** (Separate from Production):
- **URL**: `https://mina-staging.replit.app`
- **Branch**: `staging` (dedicated branch)
- **Database**: Separate Neon PostgreSQL database
- **Redis**: Separate Redis instance (or disabled for staging)

### Environment Variables

**Staging-Specific Variables** (`.env.staging`):

```bash
# Application
FLASK_ENV=staging
DEBUG=True
SECRET_KEY=staging-secret-key-different-from-prod

# Database
DATABASE_URL=postgresql://staging_user:staging_pass@staging-db.neon.tech/mina_staging

# External Services (Staging/Test Keys)
OPENAI_API_KEY=sk-staging-key-here
REDIS_URL=redis://staging-redis:6379

# Feature Flags
ENABLE_DEBUG_TOOLBAR=true
ENABLE_VERBOSE_LOGGING=true
ALLOW_TEST_USERS=true

# URLs
FRONTEND_URL=https://mina-staging.replit.app
API_BASE_URL=https://mina-staging.replit.app/api

# Third-party (Staging)
SENTRY_DSN=https://staging-dsn@sentry.io/staging
SENTRY_ENVIRONMENT=staging
```

### Workflow Configuration

**Staging Workflow** (`gunicorn-staging.sh`):
```bash
#!/bin/bash
# Staging deployment script

export FLASK_ENV=staging
export DATABASE_URL=$STAGING_DATABASE_URL

# Run with 2 workers (production uses 2+)
gunicorn --bind 0.0.0.0:5000 \
  --workers 2 \
  --worker-class eventlet \
  --timeout 120 \
  --reload \
  --access-logfile - \
  --error-logfile - \
  main:app
```

## Database Setup

### Create Staging Database

**Using Neon** (Recommended):
1. Create separate Neon project: "mina-staging"
2. Copy connection string to `STAGING_DATABASE_URL`
3. Run migrations:
   ```bash
   export DATABASE_URL=$STAGING_DATABASE_URL
   flask db upgrade
   ```

**Seed with Production-Like Data**:
```bash
# Seed staging database
python scripts/seed_staging_db.py

# Or restore from sanitized production backup
pg_dump $PRODUCTION_DATABASE_URL | \
  sed 's/user@example.com/user+staging@example.com/g' | \
  psql $STAGING_DATABASE_URL
```

### Data Sanitization

**IMPORTANT**: Never use real user data in staging

**Sanitization Script** (`scripts/sanitize_staging_data.py`):
```python
#!/usr/bin/env python3
"""
Sanitize production data for staging use.
"""
from app import app, db
from models import User
import os

def sanitize_staging_data():
    """Replace sensitive data with fake data."""
    with app.app_context():
        # Anonymize emails
        users = User.query.all()
        for user in users:
            user.email = f"user{user.id}+staging@example.com"
            user.username = f"staging_user_{user.id}"
        
        db.session.commit()
        print(f"Sanitized {len(users)} users")

if __name__ == '__main__':
    if os.environ.get('FLASK_ENV') != 'staging':
        print("ERROR: Only run in staging environment!")
        exit(1)
    
    sanitize_staging_data()
```

## Deployment Process

### Automated Staging Deployment

**GitHub Actions Workflow** (`.github/workflows/deploy-staging.yml`):
```yaml
name: Deploy to Staging

on:
  push:
    branches: [staging]
  workflow_dispatch:

env:
  PYTHON_VERSION: '3.11'

jobs:
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run tests
        env:
          DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
          FLASK_ENV: staging
        run: |
          pytest tests/unit/ tests/integration/ -v
      
      - name: Deploy to Replit Staging
        env:
          REPLIT_TOKEN: ${{ secrets.REPLIT_STAGING_TOKEN }}
        run: |
          # Trigger Replit staging deployment
          curl -X POST https://api.replit.com/v1/deploy \
            -H "Authorization: Bearer $REPLIT_TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"repl": "mina-staging", "branch": "staging"}'
      
      - name: Run smoke tests
        run: |
          sleep 30  # Wait for deployment
          pytest tests/e2e/test_01_smoke_tests.py -v \
            --base-url=https://mina-staging.replit.app
      
      - name: Notify team
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Staging deployment ${{ job.status }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Staging Deployment*\nStatus: ${{ job.status }}\nCommit: ${{ github.sha }}\nURL: https://mina-staging.replit.app"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Manual Staging Deployment

```bash
# 1. Switch to staging branch
git checkout staging

# 2. Merge latest changes
git merge main

# 3. Run tests
export FLASK_ENV=staging
export DATABASE_URL=$STAGING_DATABASE_URL
pytest tests/unit/ tests/integration/ -v

# 4. Deploy to Replit
git push origin staging
# Replit auto-deploys on push

# 5. Run smoke tests
pytest tests/e2e/test_01_smoke_tests.py -v --base-url=https://mina-staging.replit.app

# 6. Verify deployment
curl https://mina-staging.replit.app/health
```

## Testing in Staging

### Pre-Production Validation

**Required Tests Before Production**:
1. **Smoke Tests**: All critical paths working
2. **Migration Tests**: Database migrations apply cleanly
3. **Performance Tests**: Meets SLO targets
4. **Security Tests**: No new vulnerabilities
5. **Integration Tests**: External services working

**Validation Checklist**:
- [ ] Application starts without errors
- [ ] Database migrations applied successfully
- [ ] All API endpoints returning expected responses
- [ ] WebSocket connections working
- [ ] Real-time transcription functional
- [ ] AI summary generation working
- [ ] Authentication flow working
- [ ] No errors in Sentry (staging environment)
- [ ] Performance within SLO targets
- [ ] Accessibility tests passing

### Load Testing in Staging

```bash
# Run k6 load tests against staging
cd tests/k6
export BASE_URL=https://mina-staging.replit.app
./run-all-tests.sh

# Check results
cat results/*/metrics.json
```

## Promotion to Production

### Staging-to-Production Workflow

**After successful staging validation**:

```bash
# 1. Tag staging release
git checkout staging
git tag -a v1.2.3-staging -m "Staging release v1.2.3"
git push origin v1.2.3-staging

# 2. Merge to main (production)
git checkout main
git merge staging --no-ff
git push origin main

# 3. Tag production release
git tag -a v1.2.3 -m "Production release v1.2.3"
git push origin v1.2.3

# 4. Deploy to production
# (Triggers production deployment workflow)
```

**Automated Promotion** (GitHub Actions):
```yaml
# .github/workflows/promote-to-production.yml
name: Promote to Production

on:
  workflow_dispatch:
    inputs:
      staging_tag:
        description: 'Staging tag to promote (e.g., v1.2.3-staging)'
        required: true

jobs:
  promote:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Verify staging tag
        run: |
          git fetch --tags
          git tag | grep ${{ github.event.inputs.staging_tag }}
      
      - name: Merge to main
        run: |
          git checkout main
          git merge ${{ github.event.inputs.staging_tag }} --no-ff
          git push origin main
      
      - name: Create production tag
        run: |
          VERSION=$(echo ${{ github.event.inputs.staging_tag }} | sed 's/-staging//')
          git tag -a $VERSION -m "Production release $VERSION"
          git push origin $VERSION
```

## Differences from Production

### What's the Same
- Code (same branch after merge)
- Database schema
- Environment structure
- Dependencies

### What's Different
- **Data**: Sanitized/fake data, not real users
- **Scale**: Smaller database, fewer resources
- **Monitoring**: Separate Sentry project
- **Secrets**: Test API keys, not production
- **URL**: `mina-staging.replit.app` vs `mina.replit.app`
- **Strictness**: More verbose logging, debug enabled

## Maintenance

### Regular Tasks

**Daily**:
- [ ] Sync staging database with production (sanitized)
- [ ] Check for stuck processes
- [ ] Verify external service connectivity

**Weekly**:
- [ ] Review staging logs for errors
- [ ] Update staging dependencies
- [ ] Test latest migrations

**Monthly**:
- [ ] Full staging environment rebuild
- [ ] Rotate staging API keys
- [ ] Review staging costs

### Troubleshooting

**Common Issues**:

1. **Staging database out of sync**
   ```bash
   # Refresh from production (sanitized)
   pg_dump $PRODUCTION_DATABASE_URL > prod_backup.sql
   python scripts/sanitize_staging_data.py prod_backup.sql > staging_data.sql
   psql $STAGING_DATABASE_URL < staging_data.sql
   ```

2. **Staging deployment failing**
   ```bash
   # Check Replit logs
   # Verify environment variables
   # Ensure staging branch is up to date
   ```

3. **Tests failing in staging but passing locally**
   ```bash
   # Check environment differences
   # Verify staging database state
   # Check external service connectivity
   ```

## Access & Permissions

### Team Access

- **Developers**: Full access to staging
- **QA**: Read access, can run tests
- **Stakeholders**: View-only access

### Credentials

Stored in:
- **GitHub Secrets**: `STAGING_DATABASE_URL`, `REPLIT_STAGING_TOKEN`
- **Replit Secrets**: Staging environment variables
- **1Password** (Team Vault): Staging credentials

## Monitoring

### Staging Monitoring

- **Sentry**: Separate staging project
- **Logs**: CloudWatch or Replit logs
- **Uptime**: Optional (BetterStack staging monitor)
- **Alerts**: Slack `#staging-alerts` channel (non-critical)

### Metrics

Track staging-specific metrics:
- Deployment frequency
- Test pass rate
- Time to promote to production
- Staging environment health

## Cost Management

### Resource Optimization

Staging uses fewer resources than production:
- **Database**: Smaller instance (1/4 production size)
- **Compute**: 2 workers vs 4+ in production
- **Storage**: 7-day retention vs 30-day in production
- **Monitoring**: Basic vs comprehensive

**Estimated Monthly Cost**: ~30% of production costs

## Documentation

### Related Docs

- [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md)
- [Rollback Procedures](./ROLLBACK_PROCEDURES.md)
- [Database Migrations](../database-migrations.md)
- [Testing Standards](../testing/TESTING_STANDARDS.md)

## Version History

- **v1.0** (2025-10-02): Initial staging environment documentation
- Created as part of T0.11 (Create staging environment)
- Covers setup, deployment, testing, and promotion workflows
