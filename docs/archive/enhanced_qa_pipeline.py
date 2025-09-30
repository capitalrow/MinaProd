#!/usr/bin/env python3
"""
🎯 ENHANCED QA PIPELINE - Real Audio Testing for A++ Grade
Tests with actual WAV audio data and comprehensive validation
"""

import os
import json
import time
import logging
import tempfile
import subprocess
import base64
import requests
import struct
import math
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedQAResult:
    """Enhanced QA test result with detailed metrics"""
    test_name: str
    status: str  # pass, fail, warning
    score: float  # 0.0 to 1.0
    details: Dict
    execution_time_ms: float
    error_message: Optional[str] = None

class AudioTestGenerator:
    """Generate realistic test audio for comprehensive testing"""
    
    @staticmethod
    def create_wav_audio(frequency: float = 440.0, duration: float = 2.0, 
                        sample_rate: int = 16000, amplitude: float = 0.5) -> bytes:
        """Create a proper WAV file with sine wave audio"""
        samples = []
        for i in range(int(sample_rate * duration)):
            t = float(i) / sample_rate
            sample = int(32767 * amplitude * math.sin(2 * math.pi * frequency * t))
            samples.append(max(-32767, min(32767, sample)))
        
        # Create WAV header
        wav_data = b'RIFF'
        wav_data += struct.pack('<I', 36 + len(samples) * 2)
        wav_data += b'WAVE'
        wav_data += b'fmt '
        wav_data += struct.pack('<I', 16)  # Subchunk size
        wav_data += struct.pack('<H', 1)   # Audio format (PCM)
        wav_data += struct.pack('<H', 1)   # Number of channels (mono)
        wav_data += struct.pack('<I', sample_rate)
        wav_data += struct.pack('<I', sample_rate * 2)  # Byte rate
        wav_data += struct.pack('<H', 2)   # Block align
        wav_data += struct.pack('<H', 16)  # Bits per sample
        wav_data += b'data'
        wav_data += struct.pack('<I', len(samples) * 2)
        
        for sample in samples:
            wav_data += struct.pack('<h', sample)
        
        return wav_data
    
    @staticmethod
    def create_speech_like_wav(words: List[str], sample_rate: int = 16000) -> bytes:
        """Create speech-like audio pattern for testing"""
        total_duration = len(words) * 0.8 + 0.5  # 0.8s per word + 0.5s silence
        samples = []
        
        for i, word in enumerate(words):
            word_start_time = i * 0.8
            
            # Create word-like audio (multiple harmonics)
            for j in range(int(sample_rate * 0.6)):  # 0.6s of audio per word
                t = word_start_time + (float(j) / sample_rate)
                
                # Fundamental frequency varies by word position
                fundamental = 120 + (i * 15) + (len(word) * 5)
                
                # Create complex waveform with harmonics
                sample = 0.0
                sample += 0.4 * math.sin(2 * math.pi * fundamental * t)
                sample += 0.3 * math.sin(2 * math.pi * fundamental * 2 * t)
                sample += 0.2 * math.sin(2 * math.pi * fundamental * 3 * t)
                sample += 0.1 * math.sin(2 * math.pi * fundamental * 4 * t)
                
                # Add some noise for realism
                import random
                sample += 0.05 * (random.random() - 0.5)
                
                # Convert to 16-bit integer
                int_sample = int(16000 * sample)
                samples.append(max(-32767, min(32767, int_sample)))
            
            # Add silence between words
            for j in range(int(sample_rate * 0.2)):
                samples.append(0)
        
        # Create WAV header
        wav_data = b'RIFF'
        wav_data += struct.pack('<I', 36 + len(samples) * 2)
        wav_data += b'WAVE'
        wav_data += b'fmt '
        wav_data += struct.pack('<I', 16)
        wav_data += struct.pack('<H', 1)
        wav_data += struct.pack('<H', 1)
        wav_data += struct.pack('<I', sample_rate)
        wav_data += struct.pack('<I', sample_rate * 2)
        wav_data += struct.pack('<H', 2)
        wav_data += struct.pack('<H', 16)
        wav_data += b'data'
        wav_data += struct.pack('<I', len(samples) * 2)
        
        for sample in samples:
            wav_data += struct.pack('<h', sample)
        
        return wav_data

class EnhancedMinaQAPipeline:
    """Enhanced QA pipeline with real audio testing for A++ grade assessment"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.transcription_url = f"{base_url}/api/transcribe-audio"
        self.test_results = []
        self.audio_generator = AudioTestGenerator()
        
    def run_comprehensive_qa(self) -> Dict:
        """Run enhanced QA pipeline with real audio testing"""
        logger.info("🎯 Starting ENHANCED QA Pipeline for A++ Grade Assessment")
        
        start_time = time.time()
        qa_results = {
            'timestamp': datetime.now().isoformat(),
            'pipeline_version': 'Enhanced_v2.0',
            'test_categories': {}
        }
        
        # Test Category 1: Real Audio Processing (CRITICAL)
        qa_results['test_categories']['real_audio_processing'] = self.test_real_audio_processing()
        
        # Test Category 2: Error Handling Validation (CRITICAL)  
        qa_results['test_categories']['error_handling_validation'] = self.test_enhanced_error_handling()
        
        # Test Category 3: Performance Benchmarks (HIGH)
        qa_results['test_categories']['performance_benchmarks'] = self.test_realistic_performance()
        
        # Test Category 4: Quality Validation (HIGH)
        qa_results['test_categories']['quality_validation'] = self.test_quality_metrics()
        
        # Test Category 5: Edge Case Handling (MEDIUM)
        qa_results['test_categories']['edge_case_handling'] = self.test_edge_cases()
        
        # Test Category 6: Integration Testing (MEDIUM)
        qa_results['test_categories']['integration_testing'] = self.test_system_integration()
        
        # Calculate overall assessment
        qa_results['execution_time_s'] = time.time() - start_time
        qa_results['overall_assessment'] = self.calculate_enhanced_assessment(qa_results['test_categories'])
        
        return qa_results
    
    def test_real_audio_processing(self) -> Dict:
        """Test with realistic audio data"""
        logger.info("🎵 Testing Real Audio Processing")
        
        test_cases = [
            {
                'name': 'high_quality_wav',
                'audio_generator': lambda: self.audio_generator.create_wav_audio(440.0, 2.0, 16000, 0.7),
                'expected_success': True,
                'min_confidence': 0.5
            },
            {
                'name': 'speech_pattern_wav', 
                'audio_generator': lambda: self.audio_generator.create_speech_like_wav(['hello', 'world', 'test']),
                'expected_success': True,
                'min_confidence': 0.3
            },
            {
                'name': 'low_amplitude_wav',
                'audio_generator': lambda: self.audio_generator.create_wav_audio(220.0, 1.5, 16000, 0.2),
                'expected_success': True,
                'min_confidence': 0.2
            },
            {
                'name': 'long_duration_wav',
                'audio_generator': lambda: self.audio_generator.create_wav_audio(880.0, 4.0, 16000, 0.6),
                'expected_success': True,
                'min_confidence': 0.4
            }
        ]
        
        results = {
            'test_name': 'Real Audio Processing',
            'test_cases': [],
            'summary': {'passed': 0, 'failed': 0, 'total': len(test_cases)}
        }
        
        for case in test_cases:
            case_start = time.time()
            try:
                # Generate real audio
                audio_data = case['audio_generator']()
                logger.info(f"Generated {case['name']}: {len(audio_data)} bytes")
                
                # Test transcription
                session_id = f"enhanced_qa_{case['name']}_{int(time.time())}"
                result = self.send_transcription_request(session_id, audio_data)
                
                execution_time = (time.time() - case_start) * 1000
                
                if result['success']:
                    transcription = result['data']
                    confidence = transcription.get('confidence', 0.0)
                    text = transcription.get('text', '')
                    
                    # Enhanced validation
                    passed = (
                        confidence >= case['min_confidence'] and
                        len(text.strip()) > 0 and
                        transcription.get('status') == 'success'
                    )
                    
                    case_result = {
                        'name': case['name'],
                        'status': 'pass' if passed else 'fail',
                        'score': confidence,
                        'details': {
                            'transcription': text,
                            'confidence': confidence,
                            'audio_size_bytes': len(audio_data),
                            'processing_time_ms': execution_time,
                            'expected_success': case['expected_success'],
                            'min_confidence_met': confidence >= case['min_confidence']
                        }
                    }
                    
                    if passed:
                        results['summary']['passed'] += 1
                    else:
                        results['summary']['failed'] += 1
                else:
                    case_result = {
                        'name': case['name'],
                        'status': 'fail',
                        'score': 0.0,
                        'details': {
                            'error': result.get('error', 'Unknown error'),
                            'audio_size_bytes': len(audio_data),
                            'processing_time_ms': execution_time
                        }
                    }
                    results['summary']['failed'] += 1
                    
            except Exception as e:
                case_result = {
                    'name': case['name'],
                    'status': 'fail',
                    'score': 0.0,
                    'details': {'exception': str(e)}
                }
                results['summary']['failed'] += 1
            
            results['test_cases'].append(case_result)
        
        # Calculate category score
        results['category_score'] = results['summary']['passed'] / results['summary']['total']
        results['status'] = 'pass' if results['category_score'] >= 0.8 else 'fail'
        
        return results
    
    def test_enhanced_error_handling(self) -> Dict:
        """Test proper error handling and validation"""
        logger.info("🚨 Testing Enhanced Error Handling")
        
        error_test_cases = [
            {
                'name': 'empty_audio',
                'audio_data': b'',
                'expected_error': True,
                'expected_status_code': 400
            },
            {
                'name': 'tiny_audio',
                'audio_data': b'tiny',
                'expected_error': True,
                'expected_status_code': 400
            },
            {
                'name': 'corrupt_wav_header',
                'audio_data': b'RIFF\\x00\\x00\\x00\\x00WAVEfmt invalid_data',
                'expected_error': True,
                'expected_status_code': 400
            },
            {
                'name': 'oversized_audio',
                'audio_data': b'x' * (50 * 1024 * 1024),  # 50MB
                'expected_error': True,
                'expected_status_code': 400
            }
        ]
        
        results = {
            'test_name': 'Enhanced Error Handling',
            'test_cases': [],
            'summary': {'passed': 0, 'failed': 0, 'total': len(error_test_cases)}
        }
        
        for case in error_test_cases:
            try:
                session_id = f"error_test_{case['name']}"
                result = self.send_transcription_request(session_id, case['audio_data'])
                
                # Check if error handling worked correctly
                got_error = not result['success']
                expected_error = case['expected_error']
                
                passed = got_error == expected_error
                
                if got_error and 'status_code' in result:
                    # Check status code if available
                    status_code_correct = result['status_code'] == case.get('expected_status_code', 400)
                    passed = passed and status_code_correct
                
                case_result = {
                    'name': case['name'],
                    'status': 'pass' if passed else 'fail',
                    'score': 1.0 if passed else 0.0,
                    'details': {
                        'expected_error': expected_error,
                        'got_error': got_error,
                        'audio_size_bytes': len(case['audio_data']),
                        'response': result
                    }
                }
                
                if passed:
                    results['summary']['passed'] += 1
                else:
                    results['summary']['failed'] += 1
                    
            except Exception as e:
                case_result = {
                    'name': case['name'],
                    'status': 'fail',
                    'score': 0.0,
                    'details': {'exception': str(e)}
                }
                results['summary']['failed'] += 1
            
            results['test_cases'].append(case_result)
        
        results['category_score'] = results['summary']['passed'] / results['summary']['total']
        results['status'] = 'pass' if results['category_score'] >= 0.75 else 'fail'
        
        return results
    
    def test_realistic_performance(self) -> Dict:
        """Test performance with realistic audio loads"""
        logger.info("⚡ Testing Realistic Performance")
        
        # Create various audio sizes for testing
        test_audio_sizes = [
            ('small_1s', 1.0),
            ('medium_2s', 2.0), 
            ('large_5s', 5.0)
        ]
        
        results = {
            'test_name': 'Realistic Performance',
            'latency_tests': [],
            'summary': {'passed': 0, 'failed': 0, 'total': len(test_audio_sizes)}
        }
        
        for size_name, duration in test_audio_sizes:
            # Generate realistic audio
            audio_data = self.audio_generator.create_wav_audio(440.0, duration, 16000, 0.6)
            
            # Run multiple iterations for accurate measurement
            latencies = []
            successes = 0
            
            for i in range(3):  # 3 iterations per size
                start_time = time.time()
                session_id = f"perf_test_{size_name}_{i}"
                result = self.send_transcription_request(session_id, audio_data)
                
                latency_ms = (time.time() - start_time) * 1000
                latencies.append(latency_ms)
                
                if result['success']:
                    successes += 1
            
            # Calculate metrics
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            success_rate = successes / len(latencies)
            
            # Performance thresholds (realistic for production)
            latency_threshold = duration * 2000  # 2x real-time
            passed = avg_latency < latency_threshold and success_rate >= 0.8
            
            test_result = {
                'audio_size': size_name,
                'duration_s': duration,
                'audio_bytes': len(audio_data),
                'avg_latency_ms': avg_latency,
                'max_latency_ms': max_latency,
                'success_rate': success_rate,
                'threshold_ms': latency_threshold,
                'passed': passed
            }
            
            results['latency_tests'].append(test_result)
            
            if passed:
                results['summary']['passed'] += 1
            else:
                results['summary']['failed'] += 1
        
        results['category_score'] = results['summary']['passed'] / results['summary']['total']
        results['status'] = 'pass' if results['category_score'] >= 0.8 else 'fail'
        
        return results
    
    def test_quality_metrics(self) -> Dict:
        """Test transcription quality and accuracy"""
        logger.info("🎯 Testing Quality Metrics")
        
        # Test with known audio patterns
        quality_tests = [
            {
                'name': 'pure_tone_440hz',
                'audio_gen': lambda: self.audio_generator.create_wav_audio(440.0, 2.0),
                'min_confidence': 0.3
            },
            {
                'name': 'speech_pattern',
                'audio_gen': lambda: self.audio_generator.create_speech_like_wav(['test', 'quality']),
                'min_confidence': 0.2
            }
        ]
        
        results = {
            'test_name': 'Quality Metrics',
            'quality_tests': [],
            'summary': {'passed': 0, 'failed': 0, 'total': len(quality_tests)}
        }
        
        for test in quality_tests:
            audio_data = test['audio_gen']()
            session_id = f"quality_test_{test['name']}"
            result = self.send_transcription_request(session_id, audio_data)
            
            if result['success']:
                data = result['data']
                confidence = data.get('confidence', 0.0)
                text = data.get('text', '')
                
                passed = (
                    confidence >= test['min_confidence'] and
                    len(text.strip()) > 0
                )
                
                test_result = {
                    'name': test['name'],
                    'passed': passed,
                    'confidence': confidence,
                    'text_length': len(text),
                    'transcription': text
                }
                
                if passed:
                    results['summary']['passed'] += 1
                else:
                    results['summary']['failed'] += 1
            else:
                test_result = {
                    'name': test['name'],
                    'passed': False,
                    'error': result.get('error')
                }
                results['summary']['failed'] += 1
            
            results['quality_tests'].append(test_result)
        
        results['category_score'] = results['summary']['passed'] / results['summary']['total']
        results['status'] = 'pass' if results['category_score'] >= 0.7 else 'fail'
        
        return results
    
    def test_edge_cases(self) -> Dict:
        """Test edge cases and boundary conditions"""
        logger.info("🔬 Testing Edge Cases")
        
        edge_cases = [
            {
                'name': 'minimum_valid_wav',
                'audio_gen': lambda: self.audio_generator.create_wav_audio(440.0, 0.2),  # 200ms
                'should_succeed': True
            },
            {
                'name': 'high_frequency',
                'audio_gen': lambda: self.audio_generator.create_wav_audio(8000.0, 1.0),  # 8kHz
                'should_succeed': True
            }
        ]
        
        results = {
            'test_name': 'Edge Cases',
            'edge_tests': [],
            'summary': {'passed': 0, 'failed': 0, 'total': len(edge_cases)}
        }
        
        for case in edge_cases:
            audio_data = case['audio_gen']()
            session_id = f"edge_test_{case['name']}"
            result = self.send_transcription_request(session_id, audio_data)
            
            success = result['success']
            expected_success = case['should_succeed']
            passed = success == expected_success
            
            test_result = {
                'name': case['name'],
                'passed': passed,
                'expected_success': expected_success,
                'actual_success': success,
                'audio_size_bytes': len(audio_data)
            }
            
            if passed:
                results['summary']['passed'] += 1
            else:
                results['summary']['failed'] += 1
            
            results['edge_tests'].append(test_result)
        
        results['category_score'] = results['summary']['passed'] / results['summary']['total']
        results['status'] = 'pass' if results['category_score'] >= 0.8 else 'fail'
        
        return results
    
    def test_system_integration(self) -> Dict:
        """Test overall system integration"""
        logger.info("🔗 Testing System Integration")
        
        # Test API availability and basic functionality
        integration_tests = [
            {
                'name': 'api_availability',
                'test_func': self.test_api_availability
            },
            {
                'name': 'session_handling',
                'test_func': self.test_session_handling
            }
        ]
        
        results = {
            'test_name': 'System Integration',
            'integration_tests': [],
            'summary': {'passed': 0, 'failed': 0, 'total': len(integration_tests)}
        }
        
        for test in integration_tests:
            try:
                passed = test['test_func']()
                test_result = {
                    'name': test['name'],
                    'passed': passed
                }
                
                if passed:
                    results['summary']['passed'] += 1
                else:
                    results['summary']['failed'] += 1
                    
            except Exception as e:
                test_result = {
                    'name': test['name'],
                    'passed': False,
                    'error': str(e)
                }
                results['summary']['failed'] += 1
            
            results['integration_tests'].append(test_result)
        
        results['category_score'] = results['summary']['passed'] / results['summary']['total']
        results['status'] = 'pass' if results['category_score'] >= 0.8 else 'fail'
        
        return results
    
    def test_api_availability(self) -> bool:
        """Test if API is available and responding"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_session_handling(self) -> bool:
        """Test session management"""
        try:
            # Test multiple sessions
            audio_data = self.audio_generator.create_wav_audio(440.0, 1.0)
            
            sessions = ['session_1', 'session_2', 'session_3']
            results = []
            
            for session_id in sessions:
                result = self.send_transcription_request(session_id, audio_data)
                results.append(result['success'])
            
            return all(results)  # All sessions should succeed
        except:
            return False
    
    def send_transcription_request(self, session_id: str, audio_data: bytes) -> Dict:
        """Send transcription request with enhanced error handling"""
        try:
            b64_audio = base64.b64encode(audio_data).decode('utf-8')
            
            response = requests.post(
                self.transcription_url,
                json={
                    'session_id': session_id,
                    'audio_data': b64_audio,
                    'chunk_number': 1,
                    'is_final': False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'error': response.text,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_enhanced_assessment(self, test_categories: Dict) -> Dict:
        """Calculate enhanced overall assessment for A++ grading"""
        
        # Weighted scoring for different test categories
        category_weights = {
            'real_audio_processing': 0.35,      # Most critical
            'error_handling_validation': 0.20,   # Critical for production
            'performance_benchmarks': 0.20,      # High importance
            'quality_validation': 0.15,          # High importance
            'edge_case_handling': 0.05,          # Medium importance
            'integration_testing': 0.05          # Medium importance
        }
        
        weighted_scores = []
        category_details = {}
        critical_failures = []
        
        for category_name, results in test_categories.items():
            score = results.get('category_score', 0.0)
            weight = category_weights.get(category_name, 0.1)
            weighted_score = score * weight
            weighted_scores.append(weighted_score)
            
            category_details[category_name] = {
                'score': score,
                'weight': weight,
                'weighted_score': weighted_score,
                'status': results.get('status', 'unknown'),
                'passed_tests': results.get('summary', {}).get('passed', 0),
                'total_tests': results.get('summary', {}).get('total', 0)
            }
            
            # Track critical failures
            if score < 0.8 and weight >= 0.2:  # High-weight categories with low scores
                critical_failures.append(category_name)
        
        # Calculate overall score
        overall_score = sum(weighted_scores)
        overall_percentage = overall_score * 100
        
        # Determine grade based on enhanced criteria
        if critical_failures:
            grade = 'D'  # Any critical system failure = D
            recommendation = f"CRITICAL FAILURES: {', '.join(critical_failures)} must be fixed"
        elif overall_percentage >= 95:
            grade = 'A++'
            recommendation = "EXCELLENT: System exceeds production requirements"
        elif overall_percentage >= 90:
            grade = 'A+'
            recommendation = "VERY GOOD: System meets production requirements with minor improvements"
        elif overall_percentage >= 85:
            grade = 'A'
            recommendation = "GOOD: System functional but needs optimization"
        elif overall_percentage >= 80:
            grade = 'B+'
            recommendation = "ABOVE AVERAGE: System working but improvements needed"
        elif overall_percentage >= 70:
            grade = 'B'
            recommendation = "AVERAGE: System has moderate issues"
        elif overall_percentage >= 60:
            grade = 'C'
            recommendation = "BELOW AVERAGE: System has significant issues"
        else:
            grade = 'F'
            recommendation = "FAILING: System needs major repairs"
        
        # Generate specific action items
        action_items = []
        
        for category_name, details in category_details.items():
            if details['score'] < 0.8:
                if category_name == 'real_audio_processing':
                    action_items.append("CRITICAL: Fix audio processing pipeline for real audio data")
                elif category_name == 'error_handling_validation':
                    action_items.append("CRITICAL: Implement proper input validation and error responses")
                elif category_name == 'performance_benchmarks':
                    action_items.append("HIGH: Optimize processing latency and throughput")
                elif category_name == 'quality_validation':
                    action_items.append("HIGH: Improve transcription confidence and accuracy")
                else:
                    action_items.append(f"MEDIUM: Address issues in {category_name}")
        
        if not action_items:
            action_items.append("System performing excellently - continue monitoring")
        
        return {
            'overall_grade': grade,
            'overall_score': overall_score,
            'overall_percentage': overall_percentage,
            'category_breakdown': category_details,
            'critical_failures': critical_failures,
            'recommendation': recommendation,
            'action_items': action_items,
            'grade_threshold_met': {
                'A++': overall_percentage >= 95,
                'A+': overall_percentage >= 90,
                'A': overall_percentage >= 85,
                'pass': overall_percentage >= 70
            }
        }

if __name__ == "__main__":
    qa_pipeline = EnhancedMinaQAPipeline()
    results = qa_pipeline.run_comprehensive_qa()
    
    print("\n🎯 ENHANCED MINA QA PIPELINE RESULTS")
    print("=" * 60)
    
    assessment = results['overall_assessment']
    print(f"OVERALL GRADE: {assessment['overall_grade']}")
    print(f"OVERALL SCORE: {assessment['overall_percentage']:.1f}%")
    print(f"RECOMMENDATION: {assessment['recommendation']}")
    print("\nACTION ITEMS:")
    for item in assessment['action_items']:
        print(f"  • {item}")
    
    print(f"\nDetailed results saved to enhanced_qa_results.json")
    with open('enhanced_qa_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)