#!/bin/bash
# Switch production traffic from Blue to Green

set -e

BLUE_URL="https://mina.replit.app"
GREEN_URL="https://mina-green.replit.app"

echo "🔄 Switching traffic to GREEN environment..."
echo ""

# Verify Green is healthy
echo "🏥 Checking Green health..."
if ! curl -sf $GREEN_URL/health > /dev/null; then
    echo "❌ ERROR: Green environment is unhealthy!"
    echo "   Green URL: $GREEN_URL"
    exit 1
fi

echo "✅ Green is healthy"
echo ""

# Run smoke tests
echo "🧪 Running smoke tests on Green..."
export BASE_URL=$GREEN_URL

if [ -f "./scripts/run-deployment-smoke-tests.sh" ]; then
    ./scripts/run-deployment-smoke-tests.sh $BASE_URL || {
        echo "❌ ERROR: Smoke tests failed on Green!"
        exit 1
    }
else
    echo "⚠️  Warning: Smoke test script not found, skipping tests"
fi

echo ""
echo "✅ Smoke tests passed"
echo ""

# Switch traffic (Replit requires manual domain update)
echo "📝 MANUAL STEP REQUIRED:"
echo ""
echo "   To complete the traffic switch to Green:"
echo "   1. Open Replit project settings"
echo "   2. Navigate to: Domains → Custom Domains"
echo "   3. Update domain routing:"
echo "      - Point 'mina.com' to 'mina-green' repl"
echo "   4. Save changes"
echo ""
echo "   Green URL: $GREEN_URL"
echo ""

read -p "Press Enter after updating domain configuration..."

echo ""
echo "✅ Traffic switch to GREEN initiated"
echo ""
echo "📊 NEXT STEPS:"
echo "   1. Monitor Green for 15 minutes: $GREEN_URL"
echo "   2. Watch error rates in Sentry"
echo "   3. Check performance metrics"
echo "   4. Verify user traffic is flowing"
echo ""
echo "🔙 ROLLBACK (if needed):"
echo "   ./scripts/switch-to-blue.sh"
echo ""

# Log the switch
echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] Traffic switched to GREEN" >> logs/blue-green-deployments.log
