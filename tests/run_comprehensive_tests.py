#!/usr/bin/env python3
"""
🧪 Quick Test Execution Script for MINA E2E Tests
============================================

Simple script to run comprehensive E2E tests with proper setup.
Handles dependencies and provides clear output.
"""

import subprocess
import sys
import os
import time
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Check Python dependencies
    try:
        import pytest
        import playwright
        print("✅ Python dependencies available")
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        print("Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "playwright", "pytest-html", "pytest-json-report", "pytest-timeout"], check=True)
    
    # Check Playwright browsers
    try:
        result = subprocess.run(["npx", "playwright", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Playwright available")
        else:
            print("❌ Playwright not found, installing...")
            subprocess.run(["npm", "install", "@playwright/test"], check=True)
            subprocess.run(["npx", "playwright", "install"], check=True)
    except FileNotFoundError:
        print("❌ Node.js/npm not found. Please install Node.js first.")
        return False
    
    return True


def check_server():
    """Check if MINA server is running"""
    print("🌐 Checking MINA server...")
    
    try:
        import requests
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            print("✅ MINA server is running")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach server: {e}")
        print("Please ensure MINA is running on http://localhost:5000")
        return False


def run_smoke_tests():
    """Run quick smoke tests to validate basic functionality"""
    print("\n🔥 Running smoke tests...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/e2e/test_comprehensive_e2e.py::TestComprehensiveE2E::test_01_homepage_loads_successfully",
        "tests/e2e/test_comprehensive_e2e.py::TestComprehensiveE2E::test_02_navigation_elements_present",
        "-v", "--tb=short", "--timeout=30"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Smoke tests passed")
        return True
    else:
        print("❌ Smoke tests failed")
        print("STDOUT:", result.stdout[-500:])  # Last 500 chars
        print("STDERR:", result.stderr[-500:])
        return False


def run_critical_tests():
    """Run critical user journey tests"""
    print("\n🎯 Running critical user journey tests...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/e2e/",
        "-m", "critical",
        "-v", "--tb=short", "--timeout=60",
        "--html=tests/results/critical_tests_report.html",
        "--self-contained-html"
    ]
    
    # Create results directory
    os.makedirs("tests/results", exist_ok=True)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"Exit code: {result.returncode}")
    if result.stdout:
        print("Test output:")
        print(result.stdout[-1000:])  # Last 1000 chars
    
    return result.returncode == 0


def run_full_suite():
    """Run the complete comprehensive test suite"""
    print("\n🚀 Running full comprehensive test suite...")
    
    # Install Playwright dependencies first
    try:
        print("Installing Playwright browsers...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)
    except Exception as e:
        print(f"Warning: Could not install browsers: {e}")
    
    # Run all comprehensive tests
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/e2e/",
        "-v", "--tb=short", "--timeout=120",
        "--html=tests/results/comprehensive_report.html",
        "--self-contained-html",
        f"--base-url=http://localhost:5000"
    ]
    
    # Create results directory
    os.makedirs("tests/results", exist_ok=True)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"Exit code: {result.returncode}")
    if result.stdout:
        print("Test output:")
        print(result.stdout[-1500:])  # Last 1500 chars
    
    return result.returncode == 0


def main():
    """Main execution function"""
    print("🧪 MINA Comprehensive E2E Test Execution")
    print("="*50)
    
    start_time = time.time()
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        return 1
    
    # Check server
    if not check_server():
        print("❌ Server check failed")
        return 1
    
    # Run tests based on argument
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        success = run_smoke_tests()
    elif len(sys.argv) > 1 and sys.argv[1] == "critical":
        success = run_critical_tests()
    elif len(sys.argv) > 1 and sys.argv[1] == "full":
        success = run_full_suite()
    else:
        # Default: run critical tests
        print("Running critical tests (use 'smoke', 'critical', or 'full' as argument)")
        success = run_critical_tests()
    
    # Summary
    execution_time = time.time() - start_time
    print(f"\n⏱️ Total execution time: {execution_time:.1f}s")
    
    if success:
        print("🎉 Test execution completed successfully!")
        return 0
    else:
        print("💔 Some tests failed - check the output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())