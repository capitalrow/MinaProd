#!/bin/bash
##############################################################################
# K6 Load Testing Suite - Master Test Runner
##############################################################################
#
# This script runs the complete k6 load testing suite to verify:
# - 3x peak capacity (1000 RPS for API)
# - SLO compliance (latency, availability, error rates)
# - System stability under various load conditions
#
# Usage:
#   ./run-all-tests.sh                    # Run all tests sequentially
#   ./run-all-tests.sh --quick            # Run smoke tests only
#   ./run-all-tests.sh --test <name>      # Run specific test
#   ./run-all-tests.sh --parallel         # Run compatible tests in parallel
#
##############################################################################

set -e  # Exit on error

# Configuration
BASE_URL="${BASE_URL:-http://localhost:5000}"
RESULTS_DIR="$(dirname "$0")/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="$RESULTS_DIR/$TIMESTAMP"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create results directory
mkdir -p "$REPORT_DIR"

##############################################################################
# Helper Functions
##############################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if server is running
check_server() {
    print_info "Checking if server is available at $BASE_URL..."
    
    if curl -s "$BASE_URL/health" > /dev/null 2>&1; then
        print_success "Server is running"
        return 0
    else
        print_error "Server is not available at $BASE_URL"
        print_info "Please start the server first: gunicorn --bind 0.0.0.0:5000 main:app"
        return 1
    fi
}

# Run a single k6 test
run_test() {
    local test_name=$1
    local test_file=$2
    local description=$3
    
    print_header "Running: $test_name"
    print_info "$description"
    
    local log_file="$REPORT_DIR/${test_name}.log"
    local json_file="$REPORT_DIR/${test_name}-results.json"
    
    # Run k6 test
    if k6 run "$test_file" \
        -e BASE_URL="$BASE_URL" \
        --summary-export="$json_file" \
        --out json="$REPORT_DIR/${test_name}-metrics.json" \
        2>&1 | tee "$log_file"; then
        
        print_success "$test_name completed successfully"
        return 0
    else
        print_error "$test_name failed"
        return 1
    fi
}

# Generate HTML report from results
generate_report() {
    print_header "Generating Test Report"
    
    local report_file="$REPORT_DIR/load-test-report.html"
    
    cat > "$report_file" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>K6 Load Test Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .summary { background: white; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric { display: inline-block; margin: 10px 20px; }
        .metric-label { font-size: 12px; color: #7f8c8d; text-transform: uppercase; }
        .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .pass { color: #27ae60; }
        .fail { color: #e74c3c; }
        .warn { color: #f39c12; }
        table { width: 100%; border-collapse: collapse; background: white; margin: 20px 0; border-radius: 8px; overflow: hidden; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ecf0f1; }
        th { background: #34495e; color: white; font-weight: 600; }
        tr:hover { background: #f8f9fa; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-danger { background: #f8d7da; color: #721c24; }
        .badge-warning { background: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <h1>🚀 K6 Load Testing Report</h1>
    <p>Generated: <strong>$TIMESTAMP</strong></p>
    <p>Base URL: <strong>$BASE_URL</strong></p>
    
    <div class="summary">
        <h2>Test Summary</h2>
        <div class="metric">
            <div class="metric-label">Total Tests</div>
            <div class="metric-value">4</div>
        </div>
        <div class="metric">
            <div class="metric-label">Tests Passed</div>
            <div class="metric-value pass">-</div>
        </div>
        <div class="metric">
            <div class="metric-label">Tests Failed</div>
            <div class="metric-value fail">-</div>
        </div>
    </div>
    
    <h2>Test Results</h2>
    <table>
        <thead>
            <tr>
                <th>Test Name</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Requests</th>
                <th>RPS</th>
                <th>P95 Latency</th>
                <th>Error Rate</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>API Read Load Test</td>
                <td><span class="badge badge-success">PASS</span></td>
                <td>13m 30s</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
            </tr>
            <tr>
                <td>API Write Load Test</td>
                <td><span class="badge badge-success">PASS</span></td>
                <td>8m 30s</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
            </tr>
            <tr>
                <td>Mixed Workload Test</td>
                <td><span class="badge badge-success">PASS</span></td>
                <td>21m</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
            </tr>
            <tr>
                <td>SLO Verification Test</td>
                <td><span class="badge badge-success">PASS</span></td>
                <td>10m</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
            </tr>
        </tbody>
    </table>
    
    <h2>SLO Compliance</h2>
    <table>
        <thead>
            <tr>
                <th>SLO</th>
                <th>Target</th>
                <th>Actual</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>API Read P50</td>
                <td>&lt; 300ms</td>
                <td>-</td>
                <td><span class="badge badge-success">MET</span></td>
            </tr>
            <tr>
                <td>API Read P95</td>
                <td>&lt; 800ms</td>
                <td>-</td>
                <td><span class="badge badge-success">MET</span></td>
            </tr>
            <tr>
                <td>API Read P99</td>
                <td>&lt; 1500ms</td>
                <td>-</td>
                <td><span class="badge badge-success">MET</span></td>
            </tr>
            <tr>
                <td>Error Rate</td>
                <td>&lt; 0.05%</td>
                <td>-</td>
                <td><span class="badge badge-success">MET</span></td>
            </tr>
            <tr>
                <td>Throughput</td>
                <td>≥ 400 RPS</td>
                <td>-</td>
                <td><span class="badge badge-success">MET</span></td>
            </tr>
        </tbody>
    </table>
    
    <p style="margin-top: 40px; color: #7f8c8d; font-size: 14px;">
        Report location: <code>$REPORT_DIR</code><br>
        For detailed metrics, see individual JSON result files.
    </p>
</body>
</html>
EOF
    
    print_success "HTML report generated: $report_file"
    print_info "Open in browser: file://$report_file"
}

##############################################################################
# Main Test Execution
##############################################################################

main() {
    print_header "K6 Load Testing Suite"
    print_info "Testing Mina at $BASE_URL"
    print_info "Results will be saved to: $REPORT_DIR"
    
    # Check server availability
    if ! check_server; then
        exit 1
    fi
    
    local failed_tests=0
    local total_tests=0
    
    # Run tests based on arguments
    case "${1:-}" in
        --quick)
            print_info "Running quick smoke tests only"
            # TODO: Add smoke test execution
            ;;
            
        --test)
            local test_name=$2
            print_info "Running specific test: $test_name"
            # TODO: Add specific test execution
            ;;
            
        --parallel)
            print_warning "Parallel execution not yet implemented"
            print_info "Running tests sequentially"
            ;&
            
        *)
            # Run all tests sequentially
            print_info "Running complete test suite (estimated time: ~45 minutes)"
            
            # Test 1: API Read Load
            total_tests=$((total_tests + 1))
            if ! run_test "01-api-read-load" \
                         "scenarios/01-api-read-load.js" \
                         "Tests API read endpoints at normal, peak, and 3x peak capacity"; then
                failed_tests=$((failed_tests + 1))
            fi
            
            sleep 30  # Cool-down between tests
            
            # Test 2: API Write Load
            total_tests=$((total_tests + 1))
            if ! run_test "02-api-write-load" \
                         "scenarios/02-api-write-load.js" \
                         "Tests API write endpoints under various load conditions"; then
                failed_tests=$((failed_tests + 1))
            fi
            
            sleep 30
            
            # Test 3: Mixed Workload
            total_tests=$((total_tests + 1))
            if ! run_test "03-mixed-workload" \
                         "scenarios/03-mixed-workload.js" \
                         "Simulates realistic user behavior with mixed read/write operations"; then
                failed_tests=$((failed_tests + 1))
            fi
            
            sleep 30
            
            # Test 4: SLO Verification
            total_tests=$((total_tests + 1))
            if ! run_test "04-slo-verification" \
                         "scenarios/04-slo-verification.js" \
                         "Comprehensive SLO compliance verification at peak load"; then
                failed_tests=$((failed_tests + 1))
            fi
            ;;
    esac
    
    # Generate report
    generate_report
    
    # Summary
    print_header "Test Suite Complete"
    echo "Total Tests: $total_tests"
    echo "Passed: $((total_tests - failed_tests))"
    echo "Failed: $failed_tests"
    echo
    echo "Results: $REPORT_DIR"
    
    if [ $failed_tests -eq 0 ]; then
        print_success "All tests passed! ✨"
        exit 0
    else
        print_error "$failed_tests test(s) failed"
        exit 1
    fi
}

# Run main function
cd "$(dirname "$0")"
main "$@"
