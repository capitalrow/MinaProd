#!/usr/bin/env python3
"""
Production Hardening Final - Phase 4 Complete System Verification
Comprehensive production readiness validation for Mina transcription system
"""

import os
import sys
import json
import time
import logging
import requests
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionHardeningValidator:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 4: Production Hardening Final",
            "status": "RUNNING",
            "checks": {},
            "score": 0,
            "total_checks": 0
        }
        
    def run_all_validations(self) -> Dict[str, Any]:
        """Run comprehensive production validation suite"""
        logger.info("🚀 Starting Production Hardening Final Validation")
        
        validations = [
            ("Security Headers", self.validate_security_headers),
            ("CORS Configuration", self.validate_cors_config),
            ("WebSocket Security", self.validate_websocket_security),
            ("Error Handling", self.validate_error_handling),
            ("Performance", self.validate_performance),
            ("API Endpoints", self.validate_api_endpoints),
            ("Template Rendering", self.validate_template_rendering),
            ("Database Integration", self.validate_database_integration),
            ("Session Management", self.validate_session_management),
            ("Content Security Policy", self.validate_csp),
        ]
        
        for check_name, validation_func in validations:
            logger.info(f"Running {check_name} validation...")
            try:
                result = validation_func()
                self.results["checks"][check_name] = result
                self.results["total_checks"] += 1
                if result["status"] == "PASS":
                    self.results["score"] += 1
            except Exception as e:
                logger.error(f"❌ {check_name} validation failed: {e}")
                self.results["checks"][check_name] = {
                    "status": "FAIL",
                    "error": str(e),
                    "details": []
                }
                self.results["total_checks"] += 1
        
        # Calculate final score
        score_percentage = (self.results["score"] / self.results["total_checks"]) * 100
        self.results["score_percentage"] = score_percentage
        self.results["status"] = "PASS" if score_percentage >= 90 else "FAIL"
        
        logger.info(f"🎯 Production Hardening Score: {score_percentage:.1f}% ({self.results['score']}/{self.results['total_checks']})")
        return self.results
    
    def validate_security_headers(self) -> Dict[str, Any]:
        """Validate comprehensive security headers"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            headers = response.headers
            
            required_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": lambda x: "max-age=" in x and "includeSubDomains" in x,
                "Referrer-Policy": ["strict-origin-when-cross-origin", "strict-origin"],
                "Content-Security-Policy": lambda x: len(x) > 50  # Has substantial CSP
            }
            
            results = []
            passed = 0
            total = len(required_headers)
            
            for header, expected in required_headers.items():
                actual = headers.get(header, "")
                if callable(expected):
                    valid = expected(actual)
                elif isinstance(expected, list):
                    valid = actual in expected
                else:
                    valid = actual == expected
                
                results.append({
                    "header": header,
                    "expected": str(expected),
                    "actual": actual,
                    "valid": valid
                })
                if valid:
                    passed += 1
            
            return {
                "status": "PASS" if passed >= total * 0.9 else "FAIL",
                "passed": passed,
                "total": total,
                "details": results
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e), "details": []}
    
    def validate_cors_config(self) -> Dict[str, Any]:
        """Validate CORS configuration"""
        try:
            # Test preflight request
            response = requests.options(
                f"{self.base_url}/api/analytics/trends",
                headers={
                    "Origin": "https://test.replit.dev",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Content-Type"
                },
                timeout=10
            )
            
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers"
            ]
            
            results = []
            for header in cors_headers:
                value = response.headers.get(header, "")
                results.append({
                    "header": header,
                    "present": bool(value),
                    "value": value
                })
            
            valid_cors = all(r["present"] for r in results)
            
            return {
                "status": "PASS" if valid_cors else "FAIL",
                "details": results
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e), "details": []}
    
    def validate_websocket_security(self) -> Dict[str, Any]:
        """Validate WebSocket security configuration"""
        try:
            # Check if Socket.IO endpoint responds appropriately
            response = requests.get(f"{self.base_url}/socket.io/?EIO=4&transport=polling", timeout=10)
            
            # Socket.IO should respond with proper session info
            valid_response = response.status_code == 200 and "sid" in response.text
            
            return {
                "status": "PASS" if valid_response else "FAIL",
                "details": [
                    {
                        "check": "Socket.IO endpoint accessibility",
                        "status_code": response.status_code,
                        "valid": valid_response
                    }
                ]
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e), "details": []}
    
    def validate_error_handling(self) -> Dict[str, Any]:
        """Validate error handling"""
        try:
            test_cases = [
                ("/nonexistent", 404),
                ("/api/nonexistent", 404),
            ]
            
            results = []
            for endpoint, expected_status in test_cases:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                    results.append({
                        "endpoint": endpoint,
                        "expected": expected_status,
                        "actual": response.status_code,
                        "valid": response.status_code == expected_status,
                        "has_json": "application/json" in response.headers.get("content-type", "")
                    })
                except Exception as e:
                    results.append({
                        "endpoint": endpoint,
                        "error": str(e),
                        "valid": False
                    })
            
            passed = sum(1 for r in results if r.get("valid", False))
            
            return {
                "status": "PASS" if passed >= len(results) * 0.8 else "FAIL",
                "passed": passed,
                "total": len(results),
                "details": results
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e), "details": []}
    
    def validate_performance(self) -> Dict[str, Any]:
        """Validate performance characteristics"""
        try:
            # Test response times
            endpoints = ["/", "/live", "/dashboard"]
            results = []
            
            for endpoint in endpoints:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                results.append({
                    "endpoint": endpoint,
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "fast_enough": response_time < 2.0,  # Less than 2 seconds
                    "has_compression": "gzip" in response.headers.get("content-encoding", "")
                })
            
            fast_responses = sum(1 for r in results if r["fast_enough"])
            
            return {
                "status": "PASS" if fast_responses >= len(results) * 0.8 else "FAIL",
                "fast_responses": fast_responses,
                "total_endpoints": len(results),
                "details": results
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e), "details": []}
    
    def validate_api_endpoints(self) -> Dict[str, Any]:
        """Validate critical API endpoints"""
        try:
            api_endpoints = [
                ("/api/analytics/trends", "GET"),
                ("/api/meetings", "GET"),
                ("/healthz", "GET"),
            ]
            
            results = []
            for endpoint, method in api_endpoints:
                try:
                    response = requests.request(method, f"{self.base_url}{endpoint}", timeout=5)
                    is_json = "application/json" in response.headers.get("content-type", "")
                    
                    results.append({
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": response.status_code,
                        "is_json": is_json,
                        "valid": response.status_code < 500 and is_json
                    })
                except Exception as e:
                    results.append({
                        "endpoint": endpoint,
                        "method": method,
                        "error": str(e),
                        "valid": False
                    })
            
            valid_apis = sum(1 for r in results if r.get("valid", False))
            
            return {
                "status": "PASS" if valid_apis >= len(results) * 0.8 else "FAIL",
                "valid_apis": valid_apis,
                "total_apis": len(results),
                "details": results
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e), "details": []}
    
    def validate_template_rendering(self) -> Dict[str, Any]:
        """Validate template rendering consistency"""
        try:
            template_pages = [
                "/",
                "/live", 
                "/dashboard",
                "/dashboard/meetings",
                "/dashboard/analytics",
                "/dashboard/tasks"
            ]
            
            results = []
            for page in template_pages:
                try:
                    response = requests.get(f"{self.base_url}{page}", timeout=10)
                    content = response.text
                    
                    # Check for unified template elements
                    has_sidebar = "sidebar" in content or "nav" in content
                    has_mina_logo = "Mina" in content
                    has_proper_html = "<!DOCTYPE html>" in content
                    
                    results.append({
                        "page": page,
                        "status_code": response.status_code,
                        "has_sidebar": has_sidebar,
                        "has_mina_logo": has_mina_logo,
                        "has_proper_html": has_proper_html,
                        "valid": response.status_code == 200 and has_proper_html
                    })
                    
                except Exception as e:
                    results.append({
                        "page": page,
                        "error": str(e),
                        "valid": False
                    })
            
            valid_pages = sum(1 for r in results if r.get("valid", False))
            
            return {
                "status": "PASS" if valid_pages >= len(results) * 0.9 else "FAIL",
                "valid_pages": valid_pages,
                "total_pages": len(results),
                "details": results
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e), "details": []}
    
    def validate_database_integration(self) -> Dict[str, Any]:
        """Validate database integration"""
        try:
            # Test basic database connectivity through API
            response = requests.get(f"{self.base_url}/api/analytics/trends", timeout=10)
            
            db_connected = response.status_code == 200
            has_data_structure = isinstance(response.json(), dict) if db_connected else False
            
            return {
                "status": "PASS" if db_connected else "FAIL",
                "details": [
                    {
                        "check": "Database API response",
                        "connected": db_connected,
                        "has_data_structure": has_data_structure,
                        "status_code": response.status_code
                    }
                ]
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e), "details": []}
    
    def validate_session_management(self) -> Dict[str, Any]:
        """Validate session management"""
        try:
            session = requests.Session()
            
            # Test session persistence
            response1 = session.get(f"{self.base_url}/", timeout=10)
            response2 = session.get(f"{self.base_url}/dashboard", timeout=10)
            
            # Check for secure cookie settings in headers
            set_cookie = response1.headers.get("Set-Cookie", "")
            has_secure_cookies = "HttpOnly" in set_cookie or "Secure" in set_cookie
            
            return {
                "status": "PASS" if has_secure_cookies else "PARTIAL",
                "details": [
                    {
                        "check": "Session persistence",
                        "first_response": response1.status_code,
                        "second_response": response2.status_code,
                        "has_secure_cookies": has_secure_cookies
                    }
                ]
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e), "details": []}
    
    def validate_csp(self) -> Dict[str, Any]:
        """Validate Content Security Policy"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            csp = response.headers.get("Content-Security-Policy", "")
            
            # Check for essential CSP directives
            required_directives = [
                "default-src",
                "script-src", 
                "style-src",
                "connect-src",
                "img-src"
            ]
            
            results = []
            for directive in required_directives:
                present = directive in csp
                results.append({
                    "directive": directive,
                    "present": present
                })
            
            valid_csp = len(csp) > 100 and all(r["present"] for r in results)
            
            return {
                "status": "PASS" if valid_csp else "FAIL",
                "csp_length": len(csp),
                "details": results
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e), "details": []}
    
    def generate_report(self) -> None:
        """Generate comprehensive production readiness report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"production_hardening_final_report_{timestamp}.json"
        
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📋 Production Hardening Final Report saved to: {report_file}")
        
        # Print summary
        print("\n" + "="*80)
        print("🚀 PRODUCTION HARDENING FINAL - PHASE 4 COMPLETE")
        print("="*80)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Overall Status: {self.results['status']}")
        print(f"Score: {self.results['score_percentage']:.1f}% ({self.results['score']}/{self.results['total_checks']})")
        print("\n📊 CHECK RESULTS:")
        
        for check_name, result in self.results["checks"].items():
            status_emoji = "✅" if result["status"] == "PASS" else "⚠️" if result["status"] == "PARTIAL" else "❌"
            print(f"{status_emoji} {check_name}: {result['status']}")
        
        print("\n🎯 PRODUCTION READINESS ASSESSMENT:")
        if self.results["score_percentage"] >= 95:
            print("🌟 EXCELLENT: System is production-ready with exceptional quality!")
        elif self.results["score_percentage"] >= 90:
            print("✅ GOOD: System is production-ready with minor areas for improvement.")
        elif self.results["score_percentage"] >= 80:
            print("⚠️ ACCEPTABLE: System can go to production with some risks.")
        else:
            print("❌ NEEDS WORK: System requires additional hardening before production.")
        
        print("="*80)

def main():
    """Run production hardening final validation"""
    validator = ProductionHardeningValidator()
    
    # Wait for server to be ready
    logger.info("Waiting for server to be ready...")
    for attempt in range(30):
        try:
            response = requests.get("http://localhost:5000/healthz", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Server is ready!")
                break
        except:
            pass
        time.sleep(2)
    else:
        logger.error("❌ Server not responding after 60 seconds")
        sys.exit(1)
    
    # Run comprehensive validation
    results = validator.run_all_validations()
    validator.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if results["status"] == "PASS" else 1)

if __name__ == "__main__":
    main()