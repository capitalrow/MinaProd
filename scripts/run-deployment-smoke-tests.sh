#!/bin/bash
# Run deployment smoke tests
# Usage: ./scripts/run-deployment-smoke-tests.sh [base_url]

set -e

BASE_URL=${1:-"http://localhost:5000"}
TIMEOUT=${2:-300}  # 5 minute timeout

echo "🚀 Running deployment smoke tests against: $BASE_URL"
echo "⏱️  Timeout: ${TIMEOUT}s"
echo ""

# Wait for service to be ready
echo "⏳ Waiting for service to be ready..."
end_time=$((SECONDS + 60))

while [ $SECONDS -lt $end_time ]; do
    if curl -s -f -m 5 "$BASE_URL/health" > /dev/null 2>&1; then
        echo "✅ Service is ready!"
        break
    fi
    echo "   Still waiting... (${SECONDS}s elapsed)"
    sleep 5
done

if [ $SECONDS -ge $end_time ]; then
    echo "❌ ERROR: Service did not become ready within 60 seconds"
    exit 1
fi

echo ""
echo "🧪 Running smoke tests..."
echo ""

# Run smoke tests
export BASE_URL=$BASE_URL
pytest tests/deployment/test_smoke_deployment.py \
    -v \
    -m smoke \
    --tb=short \
    --timeout=$TIMEOUT \
    -x \
    --color=yes

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✅ All deployment smoke tests passed!"
    echo ""
    echo "📊 Deployment Summary:"
    echo "   URL: $BASE_URL"
    echo "   Status: ✅ HEALTHY"
    echo "   Tests: ✅ PASSED"
else
    echo "❌ Deployment smoke tests FAILED!"
    echo ""
    echo "📊 Deployment Summary:"
    echo "   URL: $BASE_URL"
    echo "   Status: ❌ UNHEALTHY"
    echo "   Tests: ❌ FAILED"
    echo ""
    echo "🔍 Troubleshooting steps:"
    echo "   1. Check application logs"
    echo "   2. Verify environment variables"
    echo "   3. Check database connectivity"
    echo "   4. Review recent deployments"
    echo ""
    echo "📖 See: docs/operations/ROLLBACK_PROCEDURES.md"
fi

exit $exit_code
