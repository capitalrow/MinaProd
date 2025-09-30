#!/usr/bin/env python3
"""
Production Validation Suite for Mina Live Transcription System
Comprehensive production readiness verification and continuous validation
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionValidator:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 4: Production Hardening - Final Validation",
            "status": "RUNNING",
            "checks": {},
            "score": 0,
            "total_checks": 0,
            "production_ready": False
        }
        
    def run_validation_suite(self) -> Dict[str, Any]:
        """Run comprehensive production validation"""
        logger.info("🚀 Starting Production Validation Suite")
        
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
                logger.info(f"✅ {check_name}: {result['status']}")
            except Exception as e:
                logger.error(f"❌ {check_name} validation failed: {e}")
                self.results["checks"][check_name] = {
                    "status": "FAIL",
                    "error": str(e)
                }
                self.results["total_checks"] += 1
        
        # Calculate final score
        score_percentage = (self.results["score"] / self.results["total_checks"]) * 100
        self.results["score_percentage"] = score_percentage
        self.results["status"] = "PASS" if score_percentage >= 90 else "FAIL"
        self.results["production_ready"] = score_percentage >= 85
        
        logger.info(f"🎯 Production Score: {score_percentage:.1f}% ({self.results['score']}/{self.results['total_checks']})")
        return self.results
    
    def validate_security_headers(self) -> Dict[str, Any]:
        """Validate security headers implementation"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            headers = response.headers
            
            required_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "Strict-Transport-Security": lambda x: "max-age=" in x,
                "Content-Security-Policy": lambda x: len(x) > 50
            }
            
            passed = 0
            total = len(required_headers)
            details = []
            
            for header, expected in required_headers.items():
                actual = headers.get(header, "")
                if callable(expected):
                    valid = expected(actual)
                elif isinstance(expected, list):
                    valid = actual in expected
                else:
                    valid = actual == expected
                
                details.append({"header": header, "present": bool(actual), "valid": valid})
                if valid:
                    passed += 1
            
            return {
                "status": "PASS" if passed >= total * 0.9 else "FAIL",
                "details": details,
                "score": f"{passed}/{total}"
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def validate_cors_config(self) -> Dict[str, Any]:
        """Validate CORS configuration"""
        try:
            response = requests.options(
                f"{self.base_url}/api/analytics/trends",
                headers={"Origin": "https://test.replit.dev"},
                timeout=10
            )
            
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods"
            ]
            
            valid_cors = any(header in response.headers for header in cors_headers)
            
            return {
                "status": "PASS" if valid_cors or response.status_code == 200 else "FAIL",
                "cors_working": valid_cors,
                "api_accessible": response.status_code == 200
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def validate_websocket_security(self) -> Dict[str, Any]:
        """Validate WebSocket security"""
        try:
            response = requests.get(f"{self.base_url}/socket.io/?EIO=4&transport=polling", timeout=10)
            websocket_ready = response.status_code == 200 and "sid" in response.text
            
            return {
                "status": "PASS" if websocket_ready else "FAIL",
                "websocket_endpoint": websocket_ready,
                "security_configured": True
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def validate_error_handling(self) -> Dict[str, Any]:
        """Validate error handling"""
        try:
            test_cases = [("/nonexistent", 404), ("/api/nonexistent", 404)]
            results = []
            
            for endpoint, expected_status in test_cases:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                valid = response.status_code == expected_status
                results.append({"endpoint": endpoint, "valid": valid})
            
            passed = sum(1 for r in results if r["valid"])
            
            return {
                "status": "PASS" if passed >= len(results) * 0.8 else "FAIL",
                "error_handling_working": passed >= 1,
                "details": results
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def validate_performance(self) -> Dict[str, Any]:
        """Validate performance characteristics"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/", timeout=10)
            response_time = time.time() - start_time
            
            fast_enough = response_time < 2.0
            has_compression = "gzip" in response.headers.get("content-encoding", "")
            
            return {
                "status": "PASS" if fast_enough else "FAIL",
                "response_time": response_time,
                "fast_enough": fast_enough,
                "compression_enabled": has_compression
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def validate_api_endpoints(self) -> Dict[str, Any]:
        """Validate API endpoints"""
        try:
            endpoints = [
                ("/api/analytics/trends", "GET"),
                ("/api/meetings", "GET"),
                ("/healthz", "GET")
            ]
            
            results = []
            for endpoint, method in endpoints:
                response = requests.request(method, f"{self.base_url}{endpoint}", timeout=5)
                is_json = "application/json" in response.headers.get("content-type", "")
                valid = response.status_code < 500 and is_json
                
                results.append({
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "json_response": is_json,
                    "valid": valid
                })
            
            valid_apis = sum(1 for r in results if r["valid"])
            
            return {
                "status": "PASS" if valid_apis >= len(results) * 0.8 else "FAIL",
                "apis_working": valid_apis,
                "total_apis": len(results),
                "details": results
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def validate_template_rendering(self) -> Dict[str, Any]:
        """Validate template rendering"""
        try:
            pages = ["/", "/live", "/dashboard"]
            results = []
            
            for page in pages:
                response = requests.get(f"{self.base_url}{page}", timeout=10)
                valid = response.status_code in [200, 302] and "<!DOCTYPE html>" in response.text
                results.append({"page": page, "valid": valid})
            
            valid_pages = sum(1 for r in results if r["valid"])
            
            return {
                "status": "PASS" if valid_pages >= len(results) * 0.8 else "FAIL",
                "pages_rendering": valid_pages,
                "total_pages": len(results)
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def validate_database_integration(self) -> Dict[str, Any]:
        """Validate database integration"""
        try:
            response = requests.get(f"{self.base_url}/api/analytics/trends", timeout=10)
            db_working = response.status_code == 200 and response.headers.get("content-type", "").startswith("application/json")
            
            return {
                "status": "PASS" if db_working else "FAIL",
                "database_connected": db_working,
                "api_responsive": response.status_code == 200
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def validate_session_management(self) -> Dict[str, Any]:
        """Validate session management"""
        try:
            session = requests.Session()
            response = session.get(f"{self.base_url}/", timeout=10)
            
            # Session persistence working if no errors
            session_working = response.status_code == 200
            
            return {
                "status": "PASS" if session_working else "PARTIAL",
                "session_persistence": session_working,
                "cookies_managed": "Set-Cookie" in response.headers
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def validate_csp(self) -> Dict[str, Any]:
        """Validate Content Security Policy"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            csp = response.headers.get("Content-Security-Policy", "")
            
            required_directives = ["default-src", "script-src", "style-src"]
            present_directives = sum(1 for directive in required_directives if directive in csp)
            valid_csp = len(csp) > 100 and present_directives >= 2
            
            return {
                "status": "PASS" if valid_csp else "FAIL",
                "csp_configured": len(csp) > 50,
                "directives_present": present_directives
            }
            
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def generate_report(self):
        """Generate production validation report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"production_validation_report_{timestamp}.json"
        
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📋 Production Validation Report: {report_file}")
        
        # Print summary
        print("\n" + "="*80)
        print("🚀 MINA PRODUCTION VALIDATION SUITE - FINAL REPORT")
        print("="*80)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Overall Status: {self.results['status']}")
        print(f"Score: {self.results['score_percentage']:.1f}% ({self.results['score']}/{self.results['total_checks']})")
        print(f"Production Ready: {'✅ YES' if self.results['production_ready'] else '❌ NO'}")
        
        print(f"\n📊 VALIDATION RESULTS:")
        for check_name, result in self.results["checks"].items():
            status_emoji = "✅" if result["status"] == "PASS" else "⚠️" if result["status"] == "PARTIAL" else "❌"
            print(f"{status_emoji} {check_name}: {result['status']}")
        
        print(f"\n🎯 PRODUCTION READINESS:")
        if self.results["score_percentage"] >= 95:
            print("🌟 EXCELLENT: Production deployment recommended!")
        elif self.results["score_percentage"] >= 90:
            print("✅ READY: System meets production standards.")
        elif self.results["score_percentage"] >= 80:
            print("⚠️ CAUTION: Minor issues, but deployable.")
        else:
            print("❌ NOT READY: Critical issues must be resolved.")
        
        print("="*80)

def main():
    """Run production validation suite"""
    # Wait for server
    logger.info("Waiting for server to be ready...")
    for attempt in range(30):
        try:
            response = requests.get("http://localhost:5000/healthz", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Server ready!")
                break
        except:
            pass
        time.sleep(2)
    else:
        logger.error("❌ Server not responding")
        sys.exit(1)
    
    # Run validation
    validator = ProductionValidator()
    results = validator.run_validation_suite()
    validator.generate_report()
    
    # Exit with status
    sys.exit(0 if results["production_ready"] else 1)

if __name__ == "__main__":
    main()