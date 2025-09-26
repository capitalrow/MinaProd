#!/usr/bin/env python3
"""
Debug authentication issues with cookie handling
"""

import requests
import json
import time
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:5000"

def test_auth_debug():
    print("🔍 DEBUGGING AUTHENTICATION ISSUES")
    print("=" * 60)
    
    session = requests.Session()
    timestamp = int(time.time())
    test_email = f"debug{timestamp}@example.com"
    test_password = "debugpass123"
    test_name = "Debug User"
    
    # Step 1: Register user
    print("\n1. REGISTRATION")
    register_response = session.post(
        urljoin(BASE_URL, "/auth/register"),
        json={'email': test_email, 'password': test_password, 'name': test_name},
        timeout=10
    )
    print(f"Status: {register_response.status_code}")
    print(f"Response: {register_response.text}")
    print(f"Set-Cookie headers: {register_response.headers.get('Set-Cookie', 'None')}")
    print(f"Session cookies after register: {dict(session.cookies)}")
    
    # Step 2: Login user  
    print("\n2. LOGIN")
    login_response = session.post(
        urljoin(BASE_URL, "/auth/login"),
        json={'email': test_email, 'password': test_password},
        timeout=10
    )
    print(f"Status: {login_response.status_code}")
    print(f"Response: {login_response.text}")
    print(f"Set-Cookie headers: {login_response.headers.get('Set-Cookie', 'None')}")
    print(f"Session cookies after login: {dict(session.cookies)}")
    
    # Step 3: Check /auth/me 
    print("\n3. CHECK SESSION")
    me_response = session.get(urljoin(BASE_URL, "/auth/me"), timeout=10)
    print(f"Status: {me_response.status_code}")
    print(f"Response: {me_response.text}")
    print(f"Request cookies sent: {dict(session.cookies)}")
    
    # Step 4: Try password change
    print("\n4. PASSWORD CHANGE ATTEMPT")
    change_response = session.post(
        urljoin(BASE_URL, "/auth/change-password"),
        json={'current_password': test_password, 'new_password': 'newpass456'},
        timeout=10
    )
    print(f"Status: {change_response.status_code}")
    print(f"Response: {change_response.text}")
    print(f"Request cookies sent: {dict(session.cookies)}")
    
    # Step 5: Manual cookie test
    print("\n5. MANUAL COOKIE TEST")
    if session.cookies:
        # Try manually setting the cookie header
        headers = {}
        for name, value in session.cookies.items():
            headers['Cookie'] = f"{name}={value}"
            
        manual_me = requests.get(
            urljoin(BASE_URL, "/auth/me"),
            headers=headers,
            timeout=10
        )
        print(f"Manual /auth/me status: {manual_me.status_code}")
        print(f"Manual /auth/me response: {manual_me.text}")
        
        manual_change = requests.post(
            urljoin(BASE_URL, "/auth/change-password"),
            json={'current_password': test_password, 'new_password': 'newpass456'},
            headers=headers,
            timeout=10
        )
        print(f"Manual password change status: {manual_change.status_code}")
        print(f"Manual password change response: {manual_change.text}")

if __name__ == "__main__":
    test_auth_debug()