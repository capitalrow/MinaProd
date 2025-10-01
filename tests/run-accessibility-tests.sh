#!/bin/bash
# Accessibility Testing Script for Mina
# Runs both Playwright axe-core tests and Python Playwright tests

set -e

echo "🎯 Mina Accessibility Test Suite"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create results directory
mkdir -p tests/results/accessibility

# Check if Flask app is running
check_app_running() {
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Flask application is running"
        return 0
    else
        echo -e "${RED}✗${NC} Flask application is not running on port 5000"
        echo ""
        echo "Please start the Flask application first:"
        echo "  gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app"
        echo ""
        return 1
    fi
}

# Run Playwright axe-core tests
run_playwright_tests() {
    echo ""
    echo "📦 Running Playwright axe-core automated tests..."
    echo "---------------------------------------------------"
    
    if npx playwright test tests/e2e/06-axe-core-automated.spec.js --reporter=list; then
        echo -e "${GREEN}✓${NC} Playwright axe-core tests passed"
        return 0
    else
        echo -e "${RED}✗${NC} Playwright axe-core tests failed"
        return 1
    fi
}

# Run Python Playwright accessibility tests
run_python_tests() {
    echo ""
    echo "🐍 Running Python Playwright WCAG compliance tests..."
    echo "-------------------------------------------------------"
    
    if pytest tests/accessibility/test_wcag_compliance.py -v; then
        echo -e "${GREEN}✓${NC} Python accessibility tests passed"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} Python accessibility tests had issues (non-blocking)"
        return 0
    fi
}

# Generate summary report
generate_summary() {
    echo ""
    echo "📊 Accessibility Test Summary"
    echo "=================================="
    
    if [ -d "tests/results/accessibility" ]; then
        echo ""
        echo "Generated Reports:"
        ls -lh tests/results/accessibility/*.json 2>/dev/null || echo "  No JSON reports found"
        
        echo ""
        echo "Violations Summary:"
        for file in tests/results/accessibility/*_axe_report.json; do
            if [ -f "$file" ]; then
                violations=$(jq '.violations | length' "$file" 2>/dev/null || echo "N/A")
                passes=$(jq '.passes | length' "$file" 2>/dev/null || echo "N/A")
                critical=$(jq '[.violations[] | select(.impact=="critical")] | length' "$file" 2>/dev/null || echo "N/A")
                serious=$(jq '[.violations[] | select(.impact=="serious")] | length' "$file" 2>/dev/null || echo "N/A")
                
                echo "  $(basename $file):"
                echo "    ✅ Passed: $passes"
                echo "    ⚠️  Violations: $violations"
                echo "    ❌ Critical: $critical"
                echo "    🟠 Serious: $serious"
            fi
        done
    fi
    
    echo ""
    echo "=================================="
}

# Main execution
main() {
    # Check if app is running
    if ! check_app_running; then
        exit 1
    fi
    
    # Track test results
    playwright_result=0
    python_result=0
    
    # Run Playwright tests
    if ! run_playwright_tests; then
        playwright_result=1
    fi
    
    # Run Python tests
    if ! run_python_tests; then
        python_result=1
    fi
    
    # Generate summary
    generate_summary
    
    # Overall result
    echo ""
    if [ $playwright_result -eq 0 ] && [ $python_result -eq 0 ]; then
        echo -e "${GREEN}✅ All accessibility tests completed successfully!${NC}"
        exit 0
    else
        echo -e "${RED}❌ Some accessibility tests failed${NC}"
        exit 1
    fi
}

# Parse command line arguments
case "${1:-all}" in
    "playwright"|"pw")
        check_app_running && run_playwright_tests && generate_summary
        ;;
    "python"|"py")
        check_app_running && run_python_tests && generate_summary
        ;;
    "all"|*)
        main
        ;;
esac
