# Blue-Green Deployment Strategy

## Overview

Blue-green deployment is a release strategy that reduces downtime and risk by running two identical production environments (Blue and Green). Only one environment serves live traffic at a time, while the other is idle or used for testing the next release.

## Architecture

### Environment Setup

**Blue Environment** (Current Production):
- URL: `https://mina.replit.app` (primary)
- Database: Production PostgreSQL
- Status: **Active** (serving live traffic)

**Green Environment** (Next Release):
- URL: `https://mina-green.replit.app` (secondary)
- Database: Same production PostgreSQL (shared)
- Status: **Standby** (ready for deployment)

### Traffic Routing

**Using Replit Custom Domains** or **Load Balancer**:
```
User Request
    ↓
DNS/Load Balancer (mina.com)
    ↓
    ├─→ Blue Environment (active)
    └─→ Green Environment (standby)
```

**Switch traffic** by updating DNS or load balancer configuration.

## Deployment Process

### Step-by-Step Blue-Green Deployment

#### Phase 1: Pre-Deployment (Green Environment)

```bash
# 1. Ensure Green environment exists
# Replit: Create "mina-green" repl (clone of "mina")

# 2. Deploy new version to Green
git checkout main
git pull origin main

# Push to green environment
git remote add green https://github.com/mina/mina-green.git
git push green main

# 3. Run database migrations (safe, idempotent)
export DATABASE_URL=$PRODUCTION_DATABASE_URL
flask db upgrade
# Note: Both Blue and Green share same DB, migrations are safe
```

#### Phase 2: Testing Green Environment

```bash
# 4. Run smoke tests against Green
export BASE_URL=https://mina-green.replit.app
./scripts/run-deployment-smoke-tests.sh $BASE_URL

# 5. Manual verification
# Visit: https://mina-green.replit.app
# Verify critical flows work

# 6. Load test Green (optional)
cd tests/k6
export BASE_URL=https://mina-green.replit.app
./run-all-tests.sh
```

#### Phase 3: Traffic Switch

```bash
# 7. Switch traffic from Blue to Green
# Method 1: Update Replit custom domain
# In Replit UI: Settings → Domains → Point mina.com to mina-green

# Method 2: Update DNS (if using external DNS)
# Update A record: mina.com → [Green IP]

# Method 3: Update Load Balancer
./scripts/switch-to-green.sh

# 8. Monitor Green environment
# Watch metrics, logs, error rates for 15 minutes
```

#### Phase 4: Rollback (If Needed)

```bash
# 9. Immediate rollback if issues detected
./scripts/switch-to-blue.sh

# Or manual:
# Replit UI: Point mina.com back to mina (blue)
# Or DNS: Update A record back to Blue IP

# 10. Investigate and fix
# Green remains available for debugging
```

#### Phase 5: Cleanup (After Success)

```bash
# 11. After 24 hours of stable Green operation:
# - Update Blue environment to match Green
# - Blue becomes the new standby
# - Green is now production

# 12. Next deployment will deploy to Blue
# Then switch traffic Blue ← Green
```

## Implementation Scripts

### Traffic Switch Script

**`scripts/switch-to-green.sh`**:
```bash
#!/bin/bash
# Switch production traffic from Blue to Green

set -e

echo "🔄 Switching traffic to GREEN environment..."

# Verify Green is healthy
echo "🏥 Checking Green health..."
curl -f https://mina-green.replit.app/health || {
    echo "❌ Green environment is unhealthy!"
    exit 1
}

# Run smoke tests
echo "🧪 Running smoke tests on Green..."
export BASE_URL=https://mina-green.replit.app
./scripts/run-deployment-smoke-tests.sh $BASE_URL || {
    echo "❌ Smoke tests failed on Green!"
    exit 1
}

# Switch traffic (choose one method)

# Method 1: Replit Custom Domain (manual in UI)
echo "📝 Manual step required:"
echo "   1. Go to Replit project settings"
echo "   2. Navigate to Domains"
echo "   3. Point mina.com to mina-green repl"
echo ""
read -p "Press Enter after updating domain..."

# Method 2: Update environment variable flag
# export ACTIVE_ENVIRONMENT=green
# Restart load balancer

echo "✅ Traffic switched to GREEN"
echo "📊 Monitor: https://mina-green.replit.app"
echo "🔙 Rollback: ./scripts/switch-to-blue.sh"
```

**`scripts/switch-to-blue.sh`**:
```bash
#!/bin/bash
# Rollback: Switch traffic back to Blue

set -e

echo "🔙 ROLLBACK: Switching traffic to BLUE environment..."

# Verify Blue is healthy
echo "🏥 Checking Blue health..."
curl -f https://mina.replit.app/health || {
    echo "⚠️  Warning: Blue environment may be unhealthy"
}

# Switch traffic back
echo "📝 Manual step required:"
echo "   1. Go to Replit project settings"
echo "   2. Navigate to Domains"
echo "   3. Point mina.com to mina (blue) repl"
echo ""
read -p "Press Enter after updating domain..."

echo "✅ Traffic switched back to BLUE"
echo "📊 Monitor: https://mina.replit.app"
```

### Deployment Automation

**`scripts/blue-green-deploy.sh`**:
```bash
#!/bin/bash
# Automated blue-green deployment

set -e

BLUE_URL="https://mina.replit.app"
GREEN_URL="https://mina-green.replit.app"

echo "🚀 Blue-Green Deployment Starting..."
echo ""

# Step 1: Deploy to Green
echo "📦 Step 1: Deploying to Green environment..."
git push green main
sleep 30  # Wait for deployment

# Step 2: Run migrations
echo "🗃️  Step 2: Running database migrations..."
export DATABASE_URL=$PRODUCTION_DATABASE_URL
flask db upgrade

# Step 3: Health check
echo "🏥 Step 3: Health check on Green..."
curl -f $GREEN_URL/health || {
    echo "❌ Green deployment failed health check"
    exit 1
}

# Step 4: Smoke tests
echo "🧪 Step 4: Running smoke tests..."
export BASE_URL=$GREEN_URL
./scripts/run-deployment-smoke-tests.sh $BASE_URL || {
    echo "❌ Smoke tests failed"
    exit 1
}

# Step 5: Manual approval
echo ""
echo "✅ Green environment is ready!"
echo "📊 Review Green: $GREEN_URL"
echo ""
read -p "Proceed with traffic switch? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Step 6: Switch traffic
echo "🔄 Step 6: Switching traffic to Green..."
./scripts/switch-to-green.sh

echo ""
echo "✅ Deployment complete!"
echo "🟢 Green is now serving production traffic"
echo "🔵 Blue is now standby"
echo ""
echo "📊 Monitor for 15 minutes: $GREEN_URL"
echo "🔙 Rollback if needed: ./scripts/switch-to-blue.sh"
```

## Database Considerations

### Shared Database Strategy

**Both Blue and Green share the same production database**:

**Pros**:
- No data sync needed
- Instant traffic switch
- Consistent data across environments

**Cons**:
- Database migrations affect both environments
- Schema must be backward compatible

### Migration Best Practices

**Backward Compatible Migrations**:

1. **Adding Columns** (Safe):
   ```python
   # Safe: Add nullable column
   op.add_column('users', sa.Column('new_field', sa.String(100), nullable=True))
   ```

2. **Removing Columns** (Requires 2 deployments):
   ```python
   # Deployment 1: Stop using column in code
   # (Deploy to Green, switch traffic)
   
   # Deployment 2: Drop column
   op.drop_column('users', 'old_field')
   ```

3. **Renaming Columns** (Requires 3 deployments):
   ```python
   # Deployment 1: Add new column, copy data
   op.add_column('users', sa.Column('new_name', sa.String(100)))
   op.execute("UPDATE users SET new_name = old_name")
   
   # Deployment 2: Update code to use new column
   
   # Deployment 3: Drop old column
   op.drop_column('users', 'old_name')
   ```

### Database Migration Checklist

- [ ] Migration is backward compatible
- [ ] Tested on staging with production-like data
- [ ] Rollback plan documented
- [ ] Both Blue and Green can run with new schema
- [ ] No data loss risk

## Monitoring During Deployment

### Key Metrics to Watch

**During Traffic Switch** (first 15 minutes):

1. **Error Rate**:
   ```bash
   # Should remain < 1%
   # Alert if > 3%
   ```

2. **Response Time**:
   ```bash
   # p95 should remain < 500ms
   # Alert if > 1000ms
   ```

3. **Active Users**:
   ```bash
   # Should not drop suddenly
   # Alert if drops > 20%
   ```

4. **Database Connections**:
   ```bash
   # Monitor connection pool
   # Both Blue and Green share pool
   ```

### Monitoring Dashboards

**Create dedicated dashboard** showing:
- Blue environment metrics
- Green environment metrics
- Database metrics (shared)
- Traffic distribution

## Rollback Procedure

### When to Rollback

**Immediate rollback if**:
- Error rate > 5%
- Response time > 2x normal
- Database errors detected
- Critical feature broken

### Rollback Steps

```bash
# 1. Execute rollback
./scripts/switch-to-blue.sh

# 2. Verify Blue is serving traffic
curl https://mina.com/health

# 3. Monitor metrics
# Verify error rate drops
# Verify response times normalize

# 4. Investigate Green
# Green remains available for debugging
# Fix issues before next attempt

# 5. Document incident
# Create incident report
# Update deployment procedures
```

### Rollback Time

**Target RTO**: < 5 minutes
- Traffic switch: < 1 minute
- Verification: < 2 minutes
- Monitoring: < 2 minutes

## Advantages of Blue-Green

1. **Zero Downtime**: Instant traffic switch
2. **Easy Rollback**: Switch back to Blue if issues
3. **Testing in Production**: Test Green with production data
4. **Reduced Risk**: Old version (Blue) ready as fallback

## Limitations & Considerations

1. **Resource Cost**: Requires 2x infrastructure
2. **Database Complexity**: Shared DB requires compatible schemas
3. **State Management**: User sessions may be lost on switch
4. **Configuration Sync**: Ensure both environments have same config

## Alternatives Considered

### Canary Deployment
- **Pros**: Gradual rollout, less risk
- **Cons**: More complex, requires load balancer
- **When to use**: For very high-risk changes

### Rolling Deployment
- **Pros**: No extra infrastructure needed
- **Cons**: Longer deployment, potential downtime
- **When to use**: For low-risk changes

### Blue-Green (Current Choice)
- **Pros**: Simple, fast rollback, zero downtime
- **Cons**: 2x infrastructure cost
- **Why chosen**: Best balance for Mina

## Future Enhancements

### Automated Traffic Switching

**Using Cloudflare Workers** or **AWS Route53**:
```javascript
// Automated health-based switching
if (greenHealth.status === 'healthy') {
    route.to('green')
} else {
    route.to('blue')
}
```

### Progressive Traffic Migration

**Gradual switch** (10% → 50% → 100%):
```bash
# Route 10% traffic to Green
./scripts/route-traffic.sh green 10

# Monitor for 5 minutes

# Route 50% traffic to Green
./scripts/route-traffic.sh green 50

# Monitor for 5 minutes

# Route 100% traffic to Green
./scripts/route-traffic.sh green 100
```

## Checklist

### Pre-Deployment
- [ ] Green environment exists and is updated
- [ ] Database migrations are backward compatible
- [ ] Smoke tests pass on Green
- [ ] Rollback script tested
- [ ] Team notified

### During Deployment
- [ ] Deploy to Green
- [ ] Run migrations
- [ ] Smoke tests pass
- [ ] Manual verification complete
- [ ] Switch traffic to Green

### Post-Deployment
- [ ] Monitor metrics for 15 minutes
- [ ] No error rate spike
- [ ] No performance degradation
- [ ] Document deployment
- [ ] Update Blue as new standby

## Resources

- [Rollback Procedures](./ROLLBACK_PROCEDURES.md)
- [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md)
- [Staging Environment](./STAGING_ENVIRONMENT.md)
- [Martin Fowler - BlueGreenDeployment](https://martinfowler.com/bliki/BlueGreenDeployment.html)

## Version History

- **v1.0** (2025-10-02): Initial blue-green deployment strategy
- Created as part of T0.13 (Implement blue-green deployment)
- Covers architecture, process, scripts, database strategy, monitoring
