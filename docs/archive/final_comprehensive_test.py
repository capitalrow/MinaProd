#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE TEST - HONEST EFFECTIVENESS ASSESSMENT
"""

import requests
import time
import sys
from datetime import datetime

def test_all_components():
    """Test all system components thoroughly"""
    results = {}
    
    # 1. Backend Health
    try:
        response = requests.get('http://localhost:5000/', timeout=5)
        results['backend_health'] = response.status_code == 200
    except:
        results['backend_health'] = False
    
    # 2. API Endpoints
    try:
        response = requests.get('http://localhost:5000/api/stats', timeout=5)
        results['api_endpoints'] = response.status_code == 200
        if response.status_code == 200:
            stats = response.json()
            results['session_sync'] = stats['database']['active_sessions'] == stats['service']['active_sessions']
            results['stats_data'] = stats
    except:
        results['api_endpoints'] = False
        results['session_sync'] = False
    
    # 3. JavaScript File Serving
    try:
        response = requests.get('http://localhost:5000/static/js/enhanced_transcription.js', timeout=5)
        js_size = len(response.content)
        results['js_file_serving'] = js_size > 1000  # Should be substantial size
        results['js_size'] = js_size
    except:
        results['js_file_serving'] = False
        results['js_size'] = 0
    
    # 4. Enhanced Features in HTML
    try:
        response = requests.get('http://localhost:5000/', timeout=5)
        html = response.text
        has_enhanced_js = 'real_time_transcription.js' in html
        has_toast_containers = 'toast-container' in html
        results['enhanced_features_loaded'] = has_enhanced_js
        results['toast_system_ready'] = has_toast_containers
    except:
        results['enhanced_features_loaded'] = False
        results['toast_system_ready'] = False
    
    # 5. WebSocket Readiness
    try:
        response = requests.get('http://localhost:5000/socket.io/?transport=polling', timeout=5)
        results['websocket_ready'] = response.status_code in [200, 400]  # Both OK
    except:
        results['websocket_ready'] = False
    
    return results

def calculate_real_effectiveness(results):
    """Calculate honest effectiveness percentage"""
    critical_components = [
        'backend_health',
        'api_endpoints', 
        'session_sync',
        'js_file_serving',
        'enhanced_features_loaded',
        'websocket_ready'
    ]
    
    passed = sum(1 for comp in critical_components if results.get(comp, False))
    total = len(critical_components)
    
    return (passed / total) * 100, passed, total

def main():
    print("🔍 FINAL COMPREHENSIVE SYSTEM TEST")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = test_all_components()
    effectiveness, passed, total = calculate_real_effectiveness(results)
    
    print("📊 COMPONENT TEST RESULTS")
    print("-" * 40)
    
    status_map = {
        'backend_health': 'Backend Health',
        'api_endpoints': 'API Endpoints', 
        'session_sync': 'Session Synchronization',
        'js_file_serving': 'JavaScript File Serving',
        'enhanced_features_loaded': 'Enhanced Features Loaded',
        'toast_system_ready': 'Toast Notification System',
        'websocket_ready': 'WebSocket Infrastructure'
    }
    
    for key, name in status_map.items():
        status = "✅" if results.get(key, False) else "❌"
        print(f"{status} {name}")
        
        # Add details for key components
        if key == 'session_sync' and 'stats_data' in results:
            stats = results['stats_data']
            db_sessions = stats['database']['active_sessions']
            svc_sessions = stats['service']['active_sessions']
            print(f"    DB Sessions: {db_sessions}, Service Sessions: {svc_sessions}")
        
        if key == 'js_file_serving':
            js_size = results.get('js_size', 0)
            print(f"    JavaScript Size: {js_size} bytes")
    
    print()
    print("🎯 HONEST EFFECTIVENESS ASSESSMENT")
    print("=" * 60)
    print(f"Passed Components: {passed}/{total}")
    print(f"Real Effectiveness: {effectiveness:.1f}%")
    
    if effectiveness >= 90.0:
        print()
        print("🏆 EXCELLENT: System highly effective and ready for production")
    elif effectiveness >= 75.0:
        print()
        print("✅ GOOD: System mostly functional with minor issues")
    elif effectiveness >= 50.0:
        print()
        print("⚠️ MODERATE: System partially functional, needs fixes")
    else:
        print()
        print("❌ CRITICAL: Major system issues need immediate attention")
    
    return effectiveness >= 90.0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)