#!/usr/bin/env python3
"""
Quick Manual Test Runner
Simplified E2E validation for immediate feedback
"""
import requests
import json
import time
from datetime import datetime

def test_application_endpoints():
    """Test basic application endpoints."""
    base_url = "http://localhost:5000"
    
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'tests': []
    }
    
    endpoints_to_test = [
        {'path': '/', 'name': 'Homepage', 'expected_status': 200},
        {'path': '/live', 'name': 'Live Transcription Page', 'expected_status': 200},
        {'path': '/api/stats', 'name': 'Stats API', 'expected_status': 200}
    ]
    
    print("🧪 QUICK E2E VALIDATION")
    print("=" * 40)
    
    for endpoint in endpoints_to_test:
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}{endpoint['path']}", timeout=10)
            end_time = time.time()
            
            duration_ms = round((end_time - start_time) * 1000, 2)
            
            test_result = {
                'name': endpoint['name'],
                'path': endpoint['path'],
                'status_code': response.status_code,
                'expected_status': endpoint['expected_status'],
                'duration_ms': duration_ms,
                'success': response.status_code == endpoint['expected_status'],
                'content_length': len(response.content)
            }
            
            test_results['tests'].append(test_result)
            
            status_icon = "✅" if test_result['success'] else "❌"
            print(f"{status_icon} {endpoint['name']}: {response.status_code} ({duration_ms}ms)")
            
            # Basic content validation
            if endpoint['path'] == '/live' and response.status_code == 200:
                content = response.text
                
                essential_elements = [
                    'recordButton',
                    'transcript',
                    'timer',
                    'wordCount'
                ]
                
                for element in essential_elements:
                    if element in content:
                        print(f"   ✓ {element} element found")
                    else:
                        print(f"   ✗ {element} element missing")
                
                # Check for script loading
                if 'mina_transcription.js' in content:
                    print(f"   ✓ mina_transcription.js script included")
                else:
                    print(f"   ✗ mina_transcription.js script missing")
            
        except requests.exceptions.RequestException as e:
            test_result = {
                'name': endpoint['name'],
                'path': endpoint['path'],
                'success': False,
                'error': str(e),
                'duration_ms': 0
            }
            
            test_results['tests'].append(test_result)
            print(f"❌ {endpoint['name']}: Connection failed - {e}")
    
    # Summary
    successful_tests = sum(1 for test in test_results['tests'] if test.get('success', False))
    total_tests = len(test_results['tests'])
    success_rate = round((successful_tests / total_tests) * 100, 1) if total_tests > 0 else 0
    
    print("\n" + "=" * 40)
    print("QUICK VALIDATION SUMMARY")
    print("=" * 40)
    print(f"✅ Successful: {successful_tests}/{total_tests}")
    print(f"📊 Success Rate: {success_rate}%")
    print(f"🕐 Total Time: {sum(test.get('duration_ms', 0) for test in test_results['tests']):.1f}ms")
    
    # Save results
    with open('tests/results/quick_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    return test_results

def test_transcription_api():
    """Test transcription API endpoint."""
    print("\n🎤 TRANSCRIPTION API TEST")
    print("=" * 40)
    
    api_url = "http://localhost:5000/api/transcribe-audio"
    
    test_data = {
        'session_id': 'test_validation_session',
        'chunk_number': 1,
        'audio_data': 'VGVzdCBhdWRpbyBkYXRh',  # Base64 encoded "Test audio data"
        'action': 'transcribe'
    }
    
    try:
        start_time = time.time()
        response = requests.post(api_url, json=test_data, timeout=30)
        end_time = time.time()
        
        duration_ms = round((end_time - start_time) * 1000, 2)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {duration_ms}ms")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"✅ API Response: {json.dumps(response_data, indent=2)}")
                
                if response_data.get('status') == 'success':
                    print("✅ Transcription API working correctly")
                elif response_data.get('status') == 'error':
                    print(f"⚠️ API returned error: {response_data.get('error', 'Unknown error')}")
                else:
                    print(f"ℹ️ API returned: {response_data}")
                
            except json.JSONDecodeError:
                print("⚠️ API returned non-JSON response")
                print(f"Raw response: {response.text[:200]}")
        
        elif response.status_code == 400:
            print("ℹ️ API rejected request (expected for test data)")
        
        elif response.status_code == 422:
            print("ℹ️ API validation error (expected for test data)")
        
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API connection failed: {e}")
    
    return True

if __name__ == "__main__":
    # Run endpoint tests
    endpoint_results = test_application_endpoints()
    
    # Run API test
    api_results = test_transcription_api()
    
    print("\n🎯 VALIDATION COMPLETE")
    print("For full E2E testing, run: python tests/e2e_runner.py")
    print("For comprehensive analysis, see: tests/overview.md")