#!/usr/bin/env python3
"""
E2E Test Runner with comprehensive reporting
"""
import subprocess
import sys
import time
import json
from pathlib import Path
from datetime import datetime

def run_e2e_tests():
    """Run the complete E2E test suite."""
    print("🚀 MINA E2E TEST SUITE")
    print("=" * 50)
    
    # Ensure results directory exists
    results_dir = Path('tests/results')
    results_dir.mkdir(exist_ok=True)
    (results_dir / 'screenshots').mkdir(exist_ok=True)
    (results_dir / 'videos').mkdir(exist_ok=True)
    
    # Test configuration
    test_start_time = datetime.now()
    
    # Test suites to run
    test_suites = [
        {
            'name': 'Smoke Tests',
            'module': 'tests/e2e/test_01_smoke_tests.py',
            'markers': 'smoke',
            'timeout': 300  # 5 minutes
        },
        {
            'name': 'Critical User Journeys',
            'module': 'tests/e2e/test_02_critical_user_journeys.py', 
            'markers': 'critical',
            'timeout': 600  # 10 minutes
        },
        {
            'name': 'Edge Cases',
            'module': 'tests/e2e/test_03_edge_cases.py',
            'markers': 'edge_case',
            'timeout': 900  # 15 minutes
        },
        {
            'name': 'Mobile Testing',
            'module': 'tests/e2e/test_04_mobile_testing.py',
            'markers': 'mobile',
            'timeout': 600  # 10 minutes
        },
        {
            'name': 'Accessibility Testing',
            'module': 'tests/e2e/test_05_accessibility.py',
            'markers': 'accessibility',
            'timeout': 400  # 7 minutes
        }
    ]
    
    # Results tracking
    suite_results = []
    overall_start_time = time.time()
    
    print(f"📋 Running {len(test_suites)} test suites...")
    print(f"📅 Started at: {test_start_time.isoformat()}")
    print()
    
    # Run each test suite
    for i, suite in enumerate(test_suites):
        print(f"🧪 [{i+1}/{len(test_suites)}] Running {suite['name']}...")
        
        suite_start_time = time.time()
        
        # Prepare pytest command
        cmd = [
            'python', '-m', 'pytest',
            suite['module'],
            '-v',
            '--tb=short',
            '--html=tests/results/e2e_report.html',
            '--self-contained-html',
            f'--timeout={suite["timeout"]}',
            '--capture=no',
            '--asyncio-mode=auto'
        ]
        
        # Add marker filter if specified
        if suite.get('markers'):
            cmd.extend(['-m', suite['markers']])
        
        try:
            # Run the test suite
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=suite['timeout']
            )
            
            suite_end_time = time.time()
            suite_duration = suite_end_time - suite_start_time
            
            # Parse results
            suite_result = {
                'name': suite['name'],
                'module': suite['module'],
                'duration_seconds': round(suite_duration, 2),
                'exit_code': result.returncode,
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'timestamp': datetime.now().isoformat()
            }
            
            suite_results.append(suite_result)
            
            # Print results
            if suite_result['success']:
                print(f"  ✅ {suite['name']} - PASSED ({suite_duration:.1f}s)")
            else:
                print(f"  ❌ {suite['name']} - FAILED ({suite_duration:.1f}s)")
                print(f"     Exit code: {result.returncode}")
                
                # Print error summary
                if result.stderr:
                    error_lines = result.stderr.split('\n')[:5]  # First 5 lines
                    for line in error_lines:
                        if line.strip():
                            print(f"     {line}")
            
        except subprocess.TimeoutExpired:
            print(f"  ⏰ {suite['name']} - TIMEOUT ({suite['timeout']}s)")
            
            suite_results.append({
                'name': suite['name'],
                'module': suite['module'],
                'duration_seconds': suite['timeout'],
                'exit_code': -1,
                'success': False,
                'error': 'Timeout exceeded',
                'timestamp': datetime.now().isoformat()
            })
        
        except Exception as e:
            print(f"  💥 {suite['name']} - ERROR: {e}")
            
            suite_results.append({
                'name': suite['name'],
                'module': suite['module'],
                'duration_seconds': 0,
                'exit_code': -2,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        print()
    
    # Calculate overall results
    overall_end_time = time.time()
    overall_duration = overall_end_time - overall_start_time
    
    successful_suites = sum(1 for r in suite_results if r['success'])
    total_suites = len(suite_results)
    
    # Generate comprehensive report
    final_report = {
        'test_session': {
            'start_time': test_start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_seconds': round(overall_duration, 2),
            'total_suites': total_suites,
            'successful_suites': successful_suites,
            'failed_suites': total_suites - successful_suites,
            'success_rate': round((successful_suites / total_suites) * 100, 1)
        },
        'suite_results': suite_results,
        'environment': {
            'python_version': sys.version,
            'platform': sys.platform,
            'working_directory': str(Path.cwd())
        },
        'recommendations': generate_recommendations(suite_results)
    }
    
    # Save detailed report
    report_file = results_dir / 'e2e_test_report.json'
    with open(report_file, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    # Print summary
    print("=" * 50)
    print("E2E TEST SUITE SUMMARY")
    print("=" * 50)
    print(f"📊 Overall Results:")
    print(f"   Total Suites: {total_suites}")
    print(f"   Successful: {successful_suites}")
    print(f"   Failed: {total_suites - successful_suites}")
    print(f"   Success Rate: {final_report['test_session']['success_rate']}%")
    print(f"   Total Duration: {overall_duration:.1f}s")
    print()
    
    print(f"📋 Suite Breakdown:")
    for result in suite_results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"   {result['name']}: {status} ({result['duration_seconds']}s)")
    print()
    
    print(f"💡 Recommendations:")
    for rec in final_report['recommendations']:
        print(f"   • {rec}")
    print()
    
    print(f"📄 Detailed report saved to: {report_file}")
    
    # Return success/failure based on critical tests
    critical_suites = ['Smoke Tests', 'Critical User Journeys']
    critical_failures = [r for r in suite_results 
                        if r['name'] in critical_suites and not r['success']]
    
    if critical_failures:
        print("❌ CRITICAL TESTS FAILED - E2E suite failed")
        return False
    else:
        print("✅ CRITICAL TESTS PASSED - E2E suite successful")
        return True

def generate_recommendations(suite_results):
    """Generate recommendations based on test results."""
    recommendations = []
    
    failed_suites = [r for r in suite_results if not r['success']]
    
    if not failed_suites:
        recommendations.append("All test suites passed - system is ready for production")
        return recommendations
    
    for failed in failed_suites:
        if 'timeout' in failed.get('error', '').lower():
            recommendations.append(f"Optimize performance in {failed['name']} - tests are timing out")
        elif failed['name'] == 'Smoke Tests':
            recommendations.append("CRITICAL: Basic functionality failing - fix core features before proceeding")
        elif failed['name'] == 'Critical User Journeys':
            recommendations.append("CRITICAL: Core user flows broken - fix primary use cases")
        elif failed['name'] == 'Mobile Testing':
            recommendations.append("Mobile experience needs improvement - fix responsive design issues")
        elif failed['name'] == 'Accessibility Testing':
            recommendations.append("Accessibility compliance issues - implement WCAG 2.1 AA fixes")
        elif failed['name'] == 'Edge Cases':
            recommendations.append("System robustness needs improvement - fix error handling")
    
    return recommendations

if __name__ == "__main__":
    success = run_e2e_tests()
    sys.exit(0 if success else 1)