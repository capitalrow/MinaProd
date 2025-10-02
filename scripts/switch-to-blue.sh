#!/bin/bash
# Rollback: Switch traffic back to Blue

set -e

BLUE_URL="https://mina.replit.app"
GREEN_URL="https://mina-green.replit.app"

echo "🔙 ROLLBACK: Switching traffic to BLUE environment..."
echo ""

# Verify Blue is healthy
echo "🏥 Checking Blue health..."
if ! curl -sf $BLUE_URL/health > /dev/null; then
    echo "⚠️  WARNING: Blue environment may be unhealthy"
    echo "   Blue URL: $BLUE_URL"
    read -p "Continue anyway? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        exit 1
    fi
else
    echo "✅ Blue is healthy"
fi

echo ""

# Switch traffic back
echo "📝 MANUAL STEP REQUIRED:"
echo ""
echo "   To complete the rollback to Blue:"
echo "   1. Open Replit project settings"
echo "   2. Navigate to: Domains → Custom Domains"
echo "   3. Update domain routing:"
echo "      - Point 'mina.com' to 'mina' repl (blue)"
echo "   4. Save changes"
echo ""
echo "   Blue URL: $BLUE_URL"
echo ""

read -p "Press Enter after updating domain configuration..."

echo ""
echo "✅ Traffic switched back to BLUE"
echo ""
echo "📊 NEXT STEPS:"
echo "   1. Verify traffic is flowing to Blue: $BLUE_URL"
echo "   2. Monitor error rates"
echo "   3. Investigate Green issues: $GREEN_URL"
echo "   4. Create incident report"
echo ""

# Log the rollback
echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] ROLLBACK: Traffic switched to BLUE" >> logs/blue-green-deployments.log

# Notify team
echo "📢 IMPORTANT: Notify team in #incidents channel"
echo "   - Rollback executed"
echo "   - Green environment needs investigation"
echo "   - Incident report required"
