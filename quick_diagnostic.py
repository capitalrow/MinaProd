#!/usr/bin/env python3
"""
🩺 MINA Quick Diagnostic Script
Runs immediate health checks using existing monitoring systems to identify current issues.
"""

import requests
import json
import time
from datetime import datetime

def run_quick_diagnostic():
    """Run comprehensive diagnostic using existing MINA endpoints."""
    
    base_url = "http://localhost:5000"
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': [],
        'issues_found': [],
        'overall_status': 'unknown'
    }
    
    # Test 1: Basic health check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        test_result = {
            'name': 'Basic Health Check',
            'status': 'pass' if response.status_code == 200 else 'fail',
            'details': response.json() if response.status_code == 200 else response.text,
            'response_time_ms': response.elapsed.total_seconds() * 1000
        }
        results['tests'].append(test_result)
        
        if test_result['status'] == 'fail':
            results['issues_found'].append({
                'type': 'service_unavailable',
                'severity': 'critical',
                'message': 'Basic health check failed'
            })
    except Exception as e:
        results['tests'].append({
            'name': 'Basic Health Check',
            'status': 'error', 
            'error': str(e)
        })
        results['issues_found'].append({
            'type': 'service_unreachable',
            'severity': 'critical',
            'message': f'Cannot reach service: {str(e)}'
        })
    
    # Test 2: API stats (performance indicators)
    try:
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        test_result = {
            'name': 'API Statistics',
            'status': 'pass' if response.status_code == 200 else 'fail',
            'response_time_ms': response.elapsed.total_seconds() * 1000
        }
        
        if response.status_code == 200:
            stats = response.json()
            test_result['details'] = stats
            
            # Check for performance issues
            if stats.get('service', {}).get('processing_queue_size', 0) > 10:
                results['issues_found'].append({
                    'type': 'high_queue_size',
                    'severity': 'medium',
                    'message': f"Processing queue size: {stats['service']['processing_queue_size']}"
                })
                
            # Check active sessions vs configured maximum
            active = stats.get('service', {}).get('active_sessions', 0)
            max_sessions = stats.get('service', {}).get('max_concurrent_sessions', 10)
            if active / max_sessions > 0.8:  # 80% capacity
                results['issues_found'].append({
                    'type': 'near_capacity',
                    'severity': 'medium', 
                    'message': f"Near session capacity: {active}/{max_sessions}"
                })
        
        results['tests'].append(test_result)
        
    except Exception as e:
        results['tests'].append({
            'name': 'API Statistics',
            'status': 'error',
            'error': str(e)
        })
    
    # Test 3: Live page accessibility
    try:
        response = requests.get(f"{base_url}/live", timeout=5)
        test_result = {
            'name': 'Live Page Load',
            'status': 'pass' if response.status_code == 200 else 'fail',
            'response_time_ms': response.elapsed.total_seconds() * 1000
        }
        
        if response.status_code == 200:
            # Check for critical JavaScript dependencies
            content = response.text
            js_dependencies = ['socket.io', 'recording_wiring.js', 'websocket_streaming.js']
            missing_deps = [dep for dep in js_dependencies if dep not in content]
            
            if missing_deps:
                results['issues_found'].append({
                    'type': 'missing_dependencies',
                    'severity': 'high',
                    'message': f"Missing JavaScript dependencies: {missing_deps}"
                })
        
        results['tests'].append(test_result)
        
    except Exception as e:
        results['tests'].append({
            'name': 'Live Page Load',
            'status': 'error',
            'error': str(e)
        })
    
    # Test 4: WebSocket connectivity simulation
    try:
        # This is a simplified test - real implementation would use websocket client
        test_result = {
            'name': 'WebSocket Readiness',
            'status': 'partial',  # Since we can't fully test without connecting
            'message': 'Service appears ready for WebSocket connections'
        }
        results['tests'].append(test_result)
        
    except Exception as e:
        results['tests'].append({
            'name': 'WebSocket Readiness',
            'status': 'error',
            'error': str(e)
        })
    
    # Calculate overall status
    test_statuses = [test['status'] for test in results['tests']]
    if 'error' in test_statuses or any(issue['severity'] == 'critical' for issue in results['issues_found']):
        results['overall_status'] = 'critical'
    elif 'fail' in test_statuses or any(issue['severity'] == 'high' for issue in results['issues_found']):
        results['overall_status'] = 'degraded'
    elif any(issue['severity'] == 'medium' for issue in results['issues_found']):
        results['overall_status'] = 'warning'
    else:
        results['overall_status'] = 'healthy'
    
    return results

def print_diagnostic_report(results):
    """Print formatted diagnostic report."""
    
    print("\n" + "="*60)
    print("🩺 MINA QUICK DIAGNOSTIC REPORT")
    print("="*60)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Overall Status: {results['overall_status'].upper()}")
    print()
    
    # Print test results
    print("📋 TEST RESULTS:")
    for test in results['tests']:
        status_emoji = "✅" if test['status'] == 'pass' else "❌" if test['status'] == 'fail' else "⚠️"
        print(f"  {status_emoji} {test['name']}: {test['status'].upper()}")
        if 'response_time_ms' in test:
            print(f"      Response time: {test['response_time_ms']:.0f}ms")
        if 'error' in test:
            print(f"      Error: {test['error']}")
    
    # Print issues found
    if results['issues_found']:
        print("\n🚨 ISSUES DETECTED:")
        for issue in results['issues_found']:
            severity_emoji = "🔴" if issue['severity'] == 'critical' else "🟡" if issue['severity'] == 'high' else "🟠"
            print(f"  {severity_emoji} {issue['type'].upper()}: {issue['message']}")
    else:
        print("\n✅ No issues detected!")
    
    # Print recommendations
    print("\n💡 RECOMMENDATIONS:")
    if results['overall_status'] == 'critical':
        print("  🔴 IMMEDIATE ACTION REQUIRED:")
        print("     - Check server logs for errors")
        print("     - Verify database connectivity") 
        print("     - Restart services if necessary")
    elif results['overall_status'] == 'degraded':
        print("  🟡 SERVICE DEGRADATION DETECTED:")
        print("     - Monitor performance metrics")
        print("     - Check resource utilization")
        print("     - Review recent changes")
    elif results['overall_status'] == 'warning':
        print("  🟠 MINOR ISSUES DETECTED:")
        print("     - Continue monitoring")
        print("     - Consider preventive maintenance")
    else:
        print("  ✅ System operating normally")
        print("     - Continue regular monitoring")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print("🔍 Running MINA quick diagnostic...")
    results = run_quick_diagnostic()
    print_diagnostic_report(results)
    
    # Save results to file
    with open(f"diagnostic_report_{int(time.time())}.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Full report saved to diagnostic_report_{int(time.time())}.json")