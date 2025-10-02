#!/bin/bash
# Automated blue-green deployment

set -e

BLUE_URL="https://mina.replit.app"
GREEN_URL="https://mina-green.replit.app"

echo "🚀 Blue-Green Deployment Starting..."
echo ""
echo "   Blue (current):  $BLUE_URL"
echo "   Green (new):     $GREEN_URL"
echo ""

# Step 1: Verify Green environment exists
echo "📋 Step 1: Verifying Green environment..."
if ! curl -sf $GREEN_URL/health > /dev/null 2>&1; then
    echo "⚠️  Green environment not accessible"
    echo "   Ensure 'mina-green' Repl exists and is running"
    exit 1
fi
echo "✅ Green environment exists"
echo ""

# Step 2: Deploy to Green
echo "📦 Step 2: Deploying new version to Green..."
if [ -d ".git" ]; then
    git remote add green https://github.com/mina/mina-green.git 2>/dev/null || true
    echo "   Pushing to green remote..."
    # In practice, this would trigger Repl deployment
    echo "   ℹ️  Manual: Update mina-green Repl with latest code"
else
    echo "   ⚠️  Not a git repository"
fi
echo ""

# Step 3: Run database migrations
echo "🗃️  Step 3: Running database migrations..."
if [ -n "$DATABASE_URL" ]; then
    echo "   Running: flask db upgrade"
    flask db upgrade || {
        echo "❌ Database migration failed"
        exit 1
    }
    echo "✅ Migrations complete"
else
    echo "   ⚠️  DATABASE_URL not set, skipping migrations"
fi
echo ""

# Step 4: Wait for Green deployment
echo "⏳ Step 4: Waiting for Green deployment (30s)..."
sleep 30
echo ""

# Step 5: Health check
echo "🏥 Step 5: Health check on Green..."
if ! curl -sf $GREEN_URL/health > /dev/null; then
    echo "❌ Green deployment failed health check"
    exit 1
fi
echo "✅ Green is healthy"
echo ""

# Step 6: Smoke tests
echo "🧪 Step 6: Running smoke tests on Green..."
export BASE_URL=$GREEN_URL
if [ -f "./scripts/run-deployment-smoke-tests.sh" ]; then
    ./scripts/run-deployment-smoke-tests.sh $BASE_URL || {
        echo "❌ Smoke tests failed"
        exit 1
    }
else
    echo "⚠️  Smoke test script not found"
    echo "   Manually verify: $GREEN_URL"
fi
echo ""

# Step 7: Manual approval
echo "✅ Green environment is ready!"
echo ""
echo "📊 Review Green environment:"
echo "   URL: $GREEN_URL"
echo "   - Test critical user flows"
echo "   - Verify recent changes"
echo "   - Check performance metrics"
echo ""

read -p "Proceed with traffic switch? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled by user"
    echo "   Green environment remains available for testing"
    exit 1
fi

echo ""

# Step 8: Switch traffic
echo "🔄 Step 8: Switching traffic to Green..."
./scripts/switch-to-green.sh

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo ""
echo "📊 Current Status:"
echo "   🟢 Green: ACTIVE (serving production traffic)"
echo "   🔵 Blue:  STANDBY (available for rollback)"
echo ""
echo "📈 Monitoring (next 15 minutes):"
echo "   - Error rates should remain < 1%"
echo "   - Response times should remain < 500ms"
echo "   - No spike in Sentry errors"
echo ""
echo "🔙 Rollback if needed:"
echo "   ./scripts/switch-to-blue.sh"
echo ""

# Log successful deployment
echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] Blue-Green deployment completed successfully" >> logs/blue-green-deployments.log
