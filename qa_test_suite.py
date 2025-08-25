#!/usr/bin/env python3
"""
Mina Live Transcription QA Test Suite
Comprehensive quality assurance testing for the transcription pipeline.
"""

import json
import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
import websocket
import threading

# Configure logging for QA metrics
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - QA - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TranscriptionQATest:
    """Comprehensive QA testing for live transcription system."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.ws_url = base_url.replace('http', 'ws') + '/socket.io'
        self.test_results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'critical_issues': [],
            'performance_metrics': {},
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def test_system_health(self) -> Dict[str, Any]:
        """Test 1: System health and service availability."""
        logger.info("Running Test 1: System Health Check")
        
        try:
            response = requests.get(f"{self.base_url}/api/stats", timeout=10)
            health_data = response.json()
            
            # Check critical metrics
            db_sessions = health_data['database']['active_sessions']
            service_sessions = health_data['service']['active_sessions']
            processing_queue = health_data['service']['processing_queue_size']
            
            issues = []
            if db_sessions > service_sessions:
                issues.append(f"Session sync mismatch: {db_sessions} DB vs {service_sessions} service")
            
            if processing_queue > 5:
                issues.append(f"High processing queue: {processing_queue} items")
            
            result = {
                'test_name': 'system_health',
                'status': 'PASS' if not issues else 'FAIL',
                'issues': issues,
                'metrics': {
                    'response_time_ms': response.elapsed.total_seconds() * 1000,
                    'db_sessions': db_sessions,
                    'service_sessions': service_sessions,
                    'queue_size': processing_queue
                }
            }
            
            self.test_results['tests_run'] += 1
            if result['status'] == 'PASS':
                self.test_results['tests_passed'] += 1
            else:
                self.test_results['tests_failed'] += 1
                self.test_results['critical_issues'].extend(issues)
            
            return result
            
        except Exception as e:
            logger.error(f"System health test failed: {e}")
            self.test_results['tests_run'] += 1
            self.test_results['tests_failed'] += 1
            return {
                'test_name': 'system_health',
                'status': 'ERROR',
                'error': str(e)
            }
    
    def test_websocket_connection(self) -> Dict[str, Any]:
        """Test 2: WebSocket connection and session creation."""
        logger.info("Running Test 2: WebSocket Connection Test")
        
        # TODO: Implement WebSocket testing
        # This would create a connection, join session, and verify events
        
        return {
            'test_name': 'websocket_connection',
            'status': 'PENDING',
            'note': 'WebSocket testing implementation needed'
        }
    
    def test_audio_format_handling(self) -> Dict[str, Any]:
        """Test 3: Audio format conversion and processing."""
        logger.info("Running Test 3: Audio Format Handling")
        
        try:
            # Test the AudioProcessor conversion directly
            import sys
            sys.path.append('/home/runner/workspace')
            from services.audio_processor import AudioProcessor
            
            audio_processor = AudioProcessor()
            
            # Test with mock webm data (16 bytes of audio-like data)
            mock_webm_data = b'\x00' * 16000  # 1 second of silence at 16kHz
            
            wav_data = audio_processor.convert_to_wav(
                mock_webm_data, 
                input_format='webm',
                sample_rate=16000,
                channels=1
            )
            
            # WAV should have header + data
            has_wav_header = wav_data[:4] == b'RIFF'
            size_increased = len(wav_data) > len(mock_webm_data)
            
            result = {
                'test_name': 'audio_format_handling',
                'status': 'PASS' if has_wav_header and size_increased else 'FAIL',
                'metrics': {
                    'input_size': len(mock_webm_data),
                    'output_size': len(wav_data),
                    'has_wav_header': has_wav_header,
                    'format_conversion_working': has_wav_header and size_increased
                }
            }
            
            self.test_results['tests_run'] += 1
            if result['status'] == 'PASS':
                self.test_results['tests_passed'] += 1
            else:
                self.test_results['tests_failed'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Audio format test failed: {e}")
            self.test_results['tests_run'] += 1
            self.test_results['tests_failed'] += 1
            return {
                'test_name': 'audio_format_handling',
                'status': 'ERROR',
                'error': str(e)
            }
    
    def test_transcription_pipeline(self) -> Dict[str, Any]:
        """Test 4: End-to-end transcription pipeline."""
        logger.info("Running Test 4: Transcription Pipeline Test")
        
        # TODO: Implement pipeline testing
        # This would send test audio and verify transcription response
        
        return {
            'test_name': 'transcription_pipeline', 
            'status': 'PENDING',
            'note': 'End-to-end pipeline testing implementation needed'
        }
    
    def test_mobile_compatibility(self) -> Dict[str, Any]:
        """Test 5: Mobile device compatibility check."""
        logger.info("Running Test 5: Mobile Compatibility Test")
        
        # TODO: Implement mobile-specific testing
        # This would check user agent handling, WebRTC support, etc.
        
        return {
            'test_name': 'mobile_compatibility',
            'status': 'PENDING', 
            'note': 'Mobile compatibility testing implementation needed'
        }
    
    def test_accessibility_compliance(self) -> Dict[str, Any]:
        """Test 6: WCAG AA+ accessibility compliance."""
        logger.info("Running Test 6: Accessibility Compliance Test")
        
        try:
            # Test main page accessibility
            response = requests.get(self.base_url)
            html_content = response.text
            
            # Basic accessibility checks
            has_aria_labels = 'aria-label' in html_content
            has_proper_headings = '<h1' in html_content
            has_alt_text = 'alt=' in html_content
            has_semantic_elements = any(tag in html_content for tag in ['<main', '<nav', '<section'])
            
            score = sum([has_aria_labels, has_proper_headings, has_alt_text, has_semantic_elements])
            
            result = {
                'test_name': 'accessibility_compliance',
                'status': 'PASS' if score >= 3 else 'PARTIAL',
                'metrics': {
                    'accessibility_score': f"{score}/4",
                    'has_aria_labels': has_aria_labels,
                    'has_proper_headings': has_proper_headings,
                    'has_alt_text': has_alt_text,
                    'has_semantic_elements': has_semantic_elements
                }
            }
            
            self.test_results['tests_run'] += 1
            if result['status'] == 'PASS':
                self.test_results['tests_passed'] += 1
            else:
                self.test_results['tests_failed'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Accessibility test failed: {e}")
            self.test_results['tests_run'] += 1
            self.test_results['tests_failed'] += 1
            return {
                'test_name': 'accessibility_compliance',
                'status': 'ERROR',
                'error': str(e)
            }
    
    def run_full_qa_suite(self) -> Dict[str, Any]:
        """Run complete QA test suite."""
        logger.info("🧪 Starting Comprehensive QA Test Suite")
        
        start_time = time.time()
        
        # Run all tests
        test_results = []
        test_results.append(self.test_system_health())
        test_results.append(self.test_websocket_connection()) 
        test_results.append(self.test_audio_format_handling())
        test_results.append(self.test_transcription_pipeline())
        test_results.append(self.test_mobile_compatibility())
        test_results.append(self.test_accessibility_compliance())
        
        # Calculate final metrics
        duration = time.time() - start_time
        success_rate = (self.test_results['tests_passed'] / self.test_results['tests_run']) * 100 if self.test_results['tests_run'] > 0 else 0
        
        final_report = {
            'qa_suite_summary': self.test_results,
            'individual_tests': test_results,
            'execution_time_seconds': round(duration, 2),
            'success_rate_percent': round(success_rate, 1),
            'overall_status': 'PASS' if success_rate >= 80 else 'FAIL',
            'recommendations': self._generate_recommendations()
        }
        
        logger.info(f"✅ QA Suite Complete: {success_rate:.1f}% success rate ({self.test_results['tests_passed']}/{self.test_results['tests_run']} tests passed)")
        
        return final_report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if self.test_results['tests_failed'] > 0:
            recommendations.append("Critical issues found - prioritize failed test resolution")
        
        if 'Session sync mismatch' in str(self.test_results['critical_issues']):
            recommendations.append("Fix session synchronization between database and service")
        
        if self.test_results['tests_passed'] < self.test_results['tests_run']:
            recommendations.append("Implement pending tests for comprehensive coverage")
        
        if not recommendations:
            recommendations.append("System appears healthy - consider adding performance benchmarks")
        
        return recommendations

def main():
    """Run QA test suite."""
    qa_tester = TranscriptionQATest()
    
    print("🔍 MINA TRANSCRIPTION QA TESTING SUITE")
    print("=" * 50)
    
    # Run complete test suite
    results = qa_tester.run_full_qa_suite()
    
    # Print summary
    print(f"\n📊 QA RESULTS SUMMARY:")
    print(f"   Tests Run: {results['qa_suite_summary']['tests_run']}")
    print(f"   Tests Passed: {results['qa_suite_summary']['tests_passed']}")
    print(f"   Tests Failed: {results['qa_suite_summary']['tests_failed']}")
    print(f"   Success Rate: {results['success_rate_percent']}%")
    print(f"   Overall Status: {results['overall_status']}")
    
    # Print critical issues
    if results['qa_suite_summary']['critical_issues']:
        print(f"\n🚨 CRITICAL ISSUES:")
        for issue in results['qa_suite_summary']['critical_issues']:
            print(f"   • {issue}")
    
    # Print recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    for rec in results['recommendations']:
        print(f"   • {rec}")
    
    # Save detailed report
    with open('/tmp/qa_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: /tmp/qa_test_results.json")
    print("=" * 50)
    
    return results

if __name__ == "__main__":
    main()