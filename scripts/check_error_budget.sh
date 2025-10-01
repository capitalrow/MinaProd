#!/bin/bash
# Check current error budget status for SLO compliance

SERVICE="${1:-web_application}"
SLO_TARGET="${2:-99.9}"
WINDOW_DAYS="${3:-30}"

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Calculate total time in minutes
TOTAL_MINUTES=$((WINDOW_DAYS * 24 * 60))

# Get current availability from logs (last N days)
# This is a simplified calculation - in production, use proper metrics from Sentry/Prometheus
if [[ -f "/var/log/mina/app.log" ]]; then
    AVAILABILITY=$(grep -E "GET|POST" /var/log/mina/app.log | \
      awk '{if ($9 ~ /^[2-3]/) s++; total++} \
      END {if (total>0) print (s/total)*100; else print 99.9}')
else
    # Fallback: Assume healthy if no logs available
    AVAILABILITY=99.9
    echo "Warning: Log file not found, assuming $AVAILABILITY% availability"
fi

# Calculate error budget
ALLOWED_UNAVAILABILITY=$(echo "scale=4; 100 - $SLO_TARGET" | bc)
ERROR_BUDGET_MIN=$(echo "scale=2; $TOTAL_MINUTES * $ALLOWED_UNAVAILABILITY / 100" | bc)

# Calculate actual unavailability
ACTUAL_UNAVAILABILITY=$(echo "scale=4; 100 - $AVAILABILITY" | bc)
USED_BUDGET_MIN=$(echo "scale=2; $TOTAL_MINUTES * $ACTUAL_UNAVAILABILITY / 100" | bc)

# Calculate remaining budget
REMAINING_BUDGET=$(echo "scale=2; $ERROR_BUDGET_MIN - $USED_BUDGET_MIN" | bc)
REMAINING_PCT=$(echo "scale=1; ($REMAINING_BUDGET / $ERROR_BUDGET_MIN) * 100" | bc)

# Determine status
if (( $(echo "$REMAINING_PCT > 50" | bc -l) )); then
    STATUS="✅ HEALTHY"
    COLOR=$GREEN
elif (( $(echo "$REMAINING_PCT > 25" | bc -l) )); then
    STATUS="⚠️ LOW"
    COLOR=$YELLOW
else
    STATUS="🚨 CRITICAL"
    COLOR=$RED
fi

# Output
echo -e "${COLOR}========================================="
echo "Service: $SERVICE"
echo "SLO Target: $SLO_TARGET%"
echo "Current Availability: $AVAILABILITY%"
echo "========================================="
echo "Error Budget (${WINDOW_DAYS}d): $ERROR_BUDGET_MIN minutes"
echo "Used Budget: $USED_BUDGET_MIN minutes"
echo "Remaining Budget: $REMAINING_BUDGET minutes ($REMAINING_PCT%)"
echo "Status: $STATUS"
echo -e "==========================================${NC}"

# Recommendations based on status
if (( $(echo "$REMAINING_PCT < 25" | bc -l) )); then
    echo ""
    echo -e "${RED}🚨 CRITICAL: Error budget nearly exhausted${NC}"
    echo "Actions required:"
    echo "1. Feature freeze - no new deployments"
    echo "2. Focus all engineering on stability"
    echo "3. Mandatory post-mortem for all incidents"
    echo "4. Escalate to CTO/CEO"
elif (( $(echo "$REMAINING_PCT < 50" | bc -l) )); then
    echo ""
    echo -e "${YELLOW}⚠️ WARNING: Error budget running low${NC}"
    echo "Recommended actions:"
    echo "1. Increase change review rigor"
    echo "2. Deploy only during off-peak hours"
    echo "3. Defer non-critical features"
    echo "4. Focus on reliability improvements"
fi

# Exit code based on status
if (( $(echo "$REMAINING_PCT < 25" | bc -l) )); then
    exit 1  # Critical - trigger alerts
elif (( $(echo "$REMAINING_PCT < 50" | bc -l) )); then
    exit 2  # Warning - increased monitoring
else
    exit 0  # Healthy
fi
